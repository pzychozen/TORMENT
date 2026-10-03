"""R3 — legacy POST /cognition/run must call the CURRENT lane helpers.

Background
----------
`66b5e319` (2026-09-01) changed the lane helper shapes to
``_query_private_lane(ak, workspace_id, query_text, agent_id, top_k, read_model)`` and
``_query_shared_lane(ws, workspace_id, query_text, top_k, domains, read_model, *, ...)``
and routed ``fabric.query()`` through ``_legacy_query_read_model``.  The lane wrappers
built inside the legacy ``/cognition/run`` handler kept the pre-66b5e319 call shape, so
every lane call raised ``TypeError``; the aperture layer swallows lane exceptions, so the
route silently ran cognition with EMPTY private and shared memory on every LEGACY_ACTIVE
root.  Under NATIVE_ACTIVE the route is unclassified and refused 409 by the middleware
before the handler runs, so native deployments were never exposed.

What this file characterizes (legacy-seeded disposable root, hash embedder, auth off):
  * the private wrapper returns exactly what the current private helper returns;
  * the shared wrapper returns the current ``(hits, bridge_peek_domains)`` tuple with the
    handler's existing domain-ranking logic (top-2 router ranking, preference insertion,
    two-domain truncation) and matches the direct helper call;
  * end to end through the real cognition pipeline, lane memories reach the pipeline
    (no swallowed exception) and the response still carries only allowlisted keys;
  * a missing private graph surfaces the same KeyError the helpers raise for
    ``fabric.query()``, and the aperture layer still turns it into an empty lane;
  * native posture refuses POST /cognition/run with 409 BEFORE the legacy handler is
    entered, and the route stays unclassified for native.
No cognition internals, fabric helpers, native classification or storage are touched.
"""
from __future__ import annotations

import importlib
import os
import shutil
import tempfile
import types
import unittest
from typing import Any, Dict, List

WS, AGENT = "wsR3", "agR3"
PRIVATE_TEXTS = [
    "Private memory about quantum fields and lane repair",
    "Private memory about topology of the triad",
    "Private memory about identity seeds",
]
SHARED_TEXT = "Shared memory about collective fields and lane repair"
QUERY = "quantum fields lane repair"


class TestCognitionRunLegacyLaneCalls(unittest.TestCase):
    def setUp(self):
        from conftest import assert_legacy_mode, existing_legacy_root, safe_run_data_root
        from fastapi.testclient import TestClient

        safe_run_data_root()
        # I11: an empty root is refused (fresh-root-requires-native-genesis); seed a legacy owner.
        self.root = str(existing_legacy_root(tempfile.mkdtemp(prefix="torment_r3_lane_"), WS))
        self._prev = {k: os.environ.get(k) for k in ("TORMENT_DATA_DIR", "TORMENT_AUTH_ENABLE", "TORMENT_EMBED_PROVIDER")}
        os.environ["TORMENT_DATA_DIR"] = self.root
        os.environ["TORMENT_AUTH_ENABLE"] = "0"
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        import torment_service.app as appmod
        self.appmod = importlib.reload(appmod)
        self.client = TestClient(self.appmod.app)
        assert_legacy_mode(self.appmod)
        self.assertEqual(self.client.post("/workspace/create", json={"workspace_id": WS}).status_code, 200)
        self.assertEqual(self.client.post("/agent/create", json={"workspace_id": WS, "agent_id": AGENT}).status_code, 200)
        # Seed through the REST route so every write happens in the app's own thread
        # (the legacy mirror index is thread-affine under TestClient).
        for text in PRIVATE_TEXTS:
            r = self.client.post("/agent/ingest", json={"workspace_id": WS, "agent_id": AGENT, "text": text, "scope": "private"})
            self.assertEqual(r.status_code, 200, r.text)
            self.assertTrue(r.json().get("stored"))
        r = self.client.post("/agent/ingest", json={"workspace_id": WS, "agent_id": AGENT, "text": SHARED_TEXT, "scope": "shared"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json().get("stored"))

    def tearDown(self):
        from conftest import _is_repo_default
        try:
            self.client.close()
        finally:
            try:
                from torment_service.public_runtime import reset_public_runtime_for_test
                reset_public_runtime_for_test(self.root)
            finally:
                for k, v in self._prev.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
                shutil.rmtree(self.root, ignore_errors=True)
                if not _is_repo_default(os.environ.get("TORMENT_DATA_DIR")):
                    importlib.reload(self.appmod)

    # ------------------------------------------------------------------ helpers
    def _capture_lane_provider(self):
        """Run the route with a stand-in pipeline that only records its lane_provider."""
        import cognition.pipeline as pipemod
        captured: Dict[str, Any] = {}
        orig = pipemod.run_cognition_pipeline

        def fake(**kw):
            captured.update(kw)
            return {"ok": True, "task_id": "r3", "final_answer": "captured"}

        pipemod.run_cognition_pipeline = fake
        try:
            resp = self.client.post("/cognition/run", json={"workspace_id": WS, "agent_id": AGENT, "user_input": QUERY})
        finally:
            pipemod.run_cognition_pipeline = orig
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertIn("lane_provider", captured)
        return captured["lane_provider"], resp.json()

    def _read_model(self, ws):
        return self.appmod.fabric._legacy_query_read_model(
            ws, workspace_id=WS, agent_id=AGENT, preferred_private_domain=None,
        )

    # ------------------------------------------------------------------ private lane
    def test_private_wrapper_returns_current_helper_hits(self):
        provider, _ = self._capture_lane_provider()
        hits = provider.private_fn(WS, AGENT, QUERY, 3)  # pre-repair: TypeError (stale call shape)
        self.assertIsInstance(hits, list)
        self.assertTrue(hits, "private lane returned no hits for ingested private memories")
        self.assertTrue(all(isinstance(h, dict) and "eid" in h for h in hits))
        fabric = self.appmod.fabric
        ws = fabric.get_workspace(WS)
        expected = fabric._query_private_lane(
            fabric._agent_key(WS, AGENT), WS, QUERY, AGENT, top_k=3, read_model=self._read_model(ws),
        )
        self.assertEqual(hits, expected)
        self.assertEqual(provider.private_fn(WS, AGENT, QUERY, 0), [])

    # ------------------------------------------------------------------ shared lane
    def test_shared_wrapper_returns_hits_and_bridge_domains_tuple(self):
        provider, _ = self._capture_lane_provider()
        fabric = self.appmod.fabric
        ws = fabric.get_workspace(WS)
        result = provider.shared_fn(WS, AGENT, QUERY, 3, None)  # pre-repair: TypeError (stale call shape)
        self.assertIsInstance(result, tuple)
        hits, bridge_domains = result
        self.assertIsInstance(hits, list)
        self.assertIsInstance(bridge_domains, list)
        self.assertTrue(hits, "shared lane returned no hits for the ingested shared memory")
        # the handler's existing domain-ranking logic, reproduced verbatim
        qemb = fabric.kernel.embedder.embed(QUERY)
        domains = [d.domain_id for d in ws.router.rank_domains(qemb, top_k=2)]
        expected = fabric._query_shared_lane(ws, WS, QUERY, top_k=3, domains=domains, read_model=self._read_model(ws))
        self.assertEqual(result, expected)
        # domain preference: inserted first, de-duplicated, truncated to two
        preferred = domains[-1] if domains else None
        if preferred is not None:
            pref_domains = ([preferred] + [d for d in domains if d != preferred])[:2]
            expected_pref = fabric._query_shared_lane(ws, WS, QUERY, top_k=3, domains=pref_domains, read_model=self._read_model(ws))
            self.assertEqual(provider.shared_fn(WS, AGENT, QUERY, 3, preferred), expected_pref)
        self.assertEqual(provider.shared_fn(WS, AGENT, QUERY, 0, None), ([], []))

    # ------------------------------------------------------------------ end to end
    def test_route_delivers_lane_memories_to_the_real_pipeline_with_allowlisted_response(self):
        import cognition.apertures as apmod
        from torment_service.app import _COGNITION_SAFE_KEYS
        seen: Dict[str, List[Any]] = {"private": [], "shared": [], "errors": []}
        real_provider_cls = apmod.LaneQueryProvider

        def recording(fn, lane):
            def wrapped(*args, **kwargs):
                try:
                    out = fn(*args, **kwargs)
                except Exception as exc:  # the aperture layer would swallow this silently
                    seen["errors"].append(f"{lane}: {type(exc).__name__}: {exc}")
                    raise
                seen[lane].append(out)
                return out
            return wrapped

        class RecordingProvider(real_provider_cls):  # type: ignore[misc,valid-type]
            def __init__(self, private_fn=None, shared_fn=None, deep_fn=None):
                super().__init__(
                    private_fn=recording(private_fn, "private") if private_fn else None,
                    shared_fn=recording(shared_fn, "shared") if shared_fn else None,
                    deep_fn=deep_fn,
                )

        apmod.LaneQueryProvider = RecordingProvider
        try:
            resp = self.client.post("/cognition/run", json={"workspace_id": WS, "agent_id": AGENT, "user_input": QUERY})
        finally:
            apmod.LaneQueryProvider = real_provider_cls
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertTrue(set(body).issubset(set(_COGNITION_SAFE_KEYS)), sorted(body))
        self.assertIs(body.get("ok"), True)
        self.assertEqual(seen["errors"], [], "lane calls raised inside the route (swallowed by the aperture layer)")
        self.assertTrue(seen["private"] and any(seen["private"]), "private lane never delivered hits to the pipeline")
        self.assertTrue(seen["shared"] and any(r[0] for r in seen["shared"]), "shared lane never delivered hits to the pipeline")
        self.assertTrue(all(isinstance(r, tuple) and len(r) == 2 for r in seen["shared"]))

    def test_response_allowlist_pinned(self):
        from torment_service.app import _COGNITION_SAFE_KEYS
        self.assertEqual(_COGNITION_SAFE_KEYS, (
            "ok", "task_id", "final_answer", "merged_findings", "dissent",
            "memory_effects", "drift_report", "governance_rejections", "role_summaries", "routing",
        ))

    # ------------------------------------------------------------------ missing private graph
    def test_missing_private_graph_raises_the_helpers_keyerror_and_aperture_yields_empty_lane(self):
        provider, _ = self._capture_lane_provider()
        with self.assertRaises(KeyError) as excinfo:
            provider.private_fn(WS, "nobody", QUERY, 3)
        self.assertIn("private query lane is unavailable", str(excinfo.exception))
        from cognition.apertures import build_memory_context
        ctx = build_memory_context("broad", WS, "nobody", QUERY, lane_provider=provider)
        self.assertEqual(ctx.private_memories, [])

    # ------------------------------------------------------------------ native posture
    def test_native_posture_refuses_before_the_legacy_handler(self):
        import cognition.pipeline as pipemod
        from torment_service.app import _native_rest_route_is_classified
        self.assertFalse(_native_rest_route_is_classified("POST", "/cognition/run"))
        orig_pipeline = pipemod.run_cognition_pipeline

        def must_not_run(**kw):
            raise AssertionError("legacy handler was entered under native posture")

        pipemod.run_cognition_pipeline = must_not_run
        # the public runtime surface reports native_mode; nothing else is reachable through it
        self.appmod.fabric.runtime = lambda: types.SimpleNamespace(native_mode=True)
        try:
            resp = self.client.post("/cognition/run", json={"workspace_id": WS, "agent_id": AGENT, "user_input": QUERY})
        finally:
            del self.appmod.fabric.runtime  # restore the class method
            pipemod.run_cognition_pipeline = orig_pipeline
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["detail"], "native public route is refused before legacy-memory effect")


if __name__ == "__main__":
    unittest.main()
