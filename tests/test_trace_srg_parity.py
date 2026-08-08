"""SRG score-modifier tests: trace() unit coverage + REAL query()/trace() parity.

Production contract (torment_service/fabric.py):

  * ``query()``  applies three SRG post-score multipliers at fabric.py:4332-4352
    and surfaces the decomposition at fabric.py:4490-4504 when ``explain=True``.
  * ``trace()``  applies the same three multipliers at fabric.py:6717-6737 and
    surfaces the same five fields at fabric.py:6813-6827.

  The multipliers are: same-band resonance x1.08, crystal identity x1.05,
  heartbeat class A x1.03.  Both surfaces read their SRG state through the same
  helper, ``fabric._effective_srg_source`` (fabric.py:181), which prefers the
  flattened top-level ``hit["srg"]`` produced by ``MemoryGraph.search``.

  PARITY THEREFORE MEANS BOTH:
    (A) identical multiplicative score modification, and
    (B) identical ``srg_*`` explain fields.
  Both are asserted below.

Why this file changed
---------------------
The previous version claimed query()/trace() parity in its docstring but called
``trace()`` 7 times and ``query()`` 0 times, so it could not observe query() at
all: if query() had stopped applying fabric.py:4332-4352 entirely, every test
still passed.  It also drove ``R_band`` with the strings ``"A"``/``"B"``/``"X"``
while production ``assign_band`` (srg_engine.py:187-199) returns an ``int`` in
``[0, DEFAULT_NUM_BANDS-1]``; because both sides of the ``==`` comparison were
test-supplied, the fixture could not detect an int/str mismatch.

This version keeps every trace-side unit assertion (now with production-real
integer bands) and adds real two-sided parity coverage plus a falsification
test proving the parity assertion catches one-sided divergence.
"""

import os
import shutil
import sys
import tempfile
import unittest
from typing import Any, Dict, Optional

import torment_service.fabric as fabric_mod
from torment_service.fabric import TormentFabric

_WS = "ws"
_AG = "agent"

# Production R_band is an int in [0, DEFAULT_NUM_BANDS-1] (srg_engine.assign_band).
_BAND = 2
_OTHER_BAND = 4

_SRG_EXPLAIN_KEYS = (
    "srg_same_band_bonus",
    "srg_crystal_bonus",
    "srg_heartbeat_bonus",
    "srg_total_multiplier",
    "srg_active_modifiers",
)


class _SRGFixtureBase(unittest.TestCase):
    """Shared fixture: real TormentFabric, SRG enabled, env restored on exit."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_trace_srg_")
        # Capture and restore the prior value instead of unconditionally
        # deleting it in tearDown (the old version leaked into later tests).
        self._prev_srg_env = os.environ.get("TORMENT_SRG_ENABLE")
        os.environ["TORMENT_SRG_ENABLE"] = "1"
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace(_WS)
        self.fabric.create_agent(_WS, _AG)

    def tearDown(self):
        if self._prev_srg_env is None:
            os.environ.pop("TORMENT_SRG_ENABLE", None)
        else:
            os.environ["TORMENT_SRG_ENABLE"] = self._prev_srg_env
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # -- helpers ------------------------------------------------------------

    def _ingest_with_srg(self, text, step, srg_payload):
        """Ingest a memory and stamp its entity payload with an SRG state.

        The payload is written where production writes it (``payload["srg"]``),
        so ``MemoryGraph.search`` flattens it to ``hit["srg"]`` exactly as it
        does for an organically built SRG state.
        """
        r = self.fabric.ingest(
            workspace_id=_WS, agent_id=_AG, text=text, step=step,
        )
        eid = r["eid"]
        ak = self.fabric._agent_key(_WS, _AG)
        pg = self.fabric.private_graphs.get(ak)
        self.assertIsNotNone(pg, "private graph must exist after ingest")
        ent = pg.entities.get(int(eid))
        self.assertIsNotNone(ent, "ingested entity must exist")
        ent.payload["srg"] = dict(srg_payload)
        return eid

    def _set_last_band(self, band):
        # Must be set AFTER ingest: ingest overwrites this per-agent entry.
        self.fabric._srg_last_ingest_band_by_agent[(_WS, _AG)] = band

    def _trace_item(self, eid, query_text):
        t = self.fabric.trace(
            workspace_id=_WS, agent_id=_AG, query_text=query_text, eids=[eid],
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1, "trace returned no items")
        return items[0]

    def _query_item(self, eid, query_text) -> Optional[Dict[str, Any]]:
        q = self.fabric.query(
            workspace_id=_WS, agent_id=_AG, query_text=query_text,
            top_k=25, explain=True,
        )
        # query() returns its hit list under "results" (fabric.query).
        for h in q.get("results", []) or []:
            if int(h.get("eid", -1)) == int(eid):
                return h
        return None

    def _require_query_item(self, eid, query_text) -> Dict[str, Any]:
        h = self._query_item(eid, query_text)
        self.assertIsNotNone(
            h, f"query() did not return eid={eid}; parity cannot be evaluated",
        )
        return h

    @staticmethod
    def _srg_explain(item) -> Dict[str, Any]:
        ex = item.get("explain", {}) or {}
        return {k: ex.get(k) for k in _SRG_EXPLAIN_KEYS}


# =========================================================================
# 1. trace()-side unit coverage (preserved from the previous file,
#    with production-real integer R_band values)
# =========================================================================

class TestTraceSRGMultiplierUnits(_SRGFixtureBase):
    """trace() applies each SRG multiplier and reports the decomposition."""

    def test_same_band_bonus(self):
        eid = self._ingest_with_srg(
            "Memory about resonance patterns", step=10,
            srg_payload={"R_band": _BAND, "is_crystal": False, "heartbeat_class": "C"},
        )
        self._set_last_band(_BAND)
        ex = self._srg_explain(self._trace_item(eid, "resonance patterns"))
        self.assertAlmostEqual(ex["srg_same_band_bonus"], 1.08, places=4)
        self.assertAlmostEqual(ex["srg_crystal_bonus"], 1.0, places=4)
        self.assertAlmostEqual(ex["srg_heartbeat_bonus"], 1.0, places=4)
        self.assertAlmostEqual(ex["srg_total_multiplier"], 1.08, places=4)
        self.assertEqual(ex["srg_active_modifiers"], ["same_band"])

    def test_crystal_bonus(self):
        eid = self._ingest_with_srg(
            "Crystal identity memory about self-concept", step=10,
            srg_payload={"R_band": _OTHER_BAND, "is_crystal": True, "heartbeat_class": "C"},
        )
        self._set_last_band(_BAND)  # deliberately NOT the memory's band
        ex = self._srg_explain(self._trace_item(eid, "self-concept"))
        self.assertAlmostEqual(ex["srg_same_band_bonus"], 1.0, places=4)
        self.assertAlmostEqual(ex["srg_crystal_bonus"], 1.05, places=4)
        self.assertAlmostEqual(ex["srg_heartbeat_bonus"], 1.0, places=4)
        self.assertAlmostEqual(ex["srg_total_multiplier"], 1.05, places=4)
        self.assertEqual(ex["srg_active_modifiers"], ["crystal"])

    def test_heartbeat_class_a_bonus(self):
        eid = self._ingest_with_srg(
            "Deep slow heartbeat memory about stability", step=10,
            srg_payload={"R_band": _OTHER_BAND, "is_crystal": False, "heartbeat_class": "A"},
        )
        self._set_last_band(_BAND)
        ex = self._srg_explain(self._trace_item(eid, "stability"))
        self.assertAlmostEqual(ex["srg_same_band_bonus"], 1.0, places=4)
        self.assertAlmostEqual(ex["srg_crystal_bonus"], 1.0, places=4)
        self.assertAlmostEqual(ex["srg_heartbeat_bonus"], 1.03, places=4)
        self.assertAlmostEqual(ex["srg_total_multiplier"], 1.03, places=4)
        self.assertEqual(ex["srg_active_modifiers"], ["heartbeat_a"])

    def test_combined_srg_modifiers(self):
        eid = self._ingest_with_srg(
            "Special memory with all SRG properties", step=10,
            srg_payload={"R_band": _BAND, "is_crystal": True, "heartbeat_class": "A"},
        )
        self._set_last_band(_BAND)

        self.fabric._srg_enable = False
        item_no = self._trace_item(eid, "special memory")
        self.fabric._srg_enable = True
        item_yes = self._trace_item(eid, "special memory")

        expected = 1.08 * 1.05 * 1.03
        ex = self._srg_explain(item_yes)
        self.assertAlmostEqual(ex["srg_total_multiplier"], expected, places=4)
        self.assertEqual(
            ex["srg_active_modifiers"], ["same_band", "crystal", "heartbeat_a"],
            msg="combined active SRG modifiers must use stable order",
        )
        self.assertAlmostEqual(
            item_yes["final_score"], item_no["final_score"] * expected, delta=0.001,
            msg="trace SRG-enabled score should be base x combined multiplier",
        )

    def test_no_srg_neutral_fields(self):
        self.fabric._srg_enable = False
        r = self.fabric.ingest(
            workspace_id=_WS, agent_id=_AG,
            text="Normal memory without SRG data", step=10,
        )
        eid = r["eid"]

        self.fabric._srg_enable = True
        ex = self._srg_explain(self._trace_item(eid, "normal memory"))
        self.assertAlmostEqual(ex["srg_same_band_bonus"], 1.0, places=4)
        self.assertAlmostEqual(ex["srg_crystal_bonus"], 1.0, places=4)
        self.assertAlmostEqual(ex["srg_heartbeat_bonus"], 1.0, places=4)
        self.assertAlmostEqual(ex["srg_total_multiplier"], 1.0, places=4)
        self.assertEqual(ex["srg_active_modifiers"], [])

        # SRG payload present but SRG disabled at read time -> still neutral.
        self.fabric._srg_enable = False
        eid2 = self._ingest_with_srg(
            "Memory with SRG payload but SRG disabled at trace", step=20,
            srg_payload={"R_band": _BAND, "is_crystal": True, "heartbeat_class": "A"},
        )
        self._set_last_band(_BAND)
        ex2 = self._srg_explain(self._trace_item(eid2, "SRG disabled memory"))
        self.assertAlmostEqual(ex2["srg_total_multiplier"], 1.0, places=4)
        self.assertEqual(ex2["srg_active_modifiers"], [])


# =========================================================================
# 2. Production-real band typing
# =========================================================================

class TestSRGBandTypeIsProductionReal(_SRGFixtureBase):
    """assign_band returns int; the same-band comparison must work on ints."""

    def test_assign_band_returns_int_in_range(self):
        from torment_service.srg_engine import DEFAULT_NUM_BANDS, assign_band

        band = assign_band(coherence=0.7, phase_duration=3, character_mode="")
        self.assertIsInstance(band, int)
        self.assertGreaterEqual(band, 0)
        self.assertLess(band, DEFAULT_NUM_BANDS)

    def test_int_band_matches_and_str_band_does_not(self):
        """An int band matches; the stringified form must NOT be treated as equal.

        This is the check the previous string fixtures could not make, because
        both sides of the comparison were test-supplied.
        """
        eid = self._ingest_with_srg(
            "Integer band resonance memory", step=10,
            srg_payload={"R_band": _BAND, "is_crystal": False, "heartbeat_class": "C"},
        )
        self._set_last_band(_BAND)
        ex_int = self._srg_explain(self._trace_item(eid, "integer band resonance"))
        self.assertAlmostEqual(ex_int["srg_same_band_bonus"], 1.08, places=4)

        # Same agent band, but the memory now carries the STRING form.
        ak = self.fabric._agent_key(_WS, _AG)
        ent = self.fabric.private_graphs[ak].entities[int(eid)]
        ent.payload["srg"]["R_band"] = str(_BAND)
        ex_str = self._srg_explain(self._trace_item(eid, "integer band resonance"))
        self.assertAlmostEqual(
            ex_str["srg_same_band_bonus"], 1.0, places=4,
            msg="'2' must not match int 2 — the comparison is type-sensitive",
        )


# =========================================================================
# 3. REAL query()/trace() parity — both surfaces exercised
# =========================================================================

class TestQueryTraceSRGParity(_SRGFixtureBase):
    """Assert (A) equal multiplicative effect and (B) equal explain fields."""

    _TEXT = "shared resonance anchor memory for parity checking"
    _QUERY = "shared resonance anchor parity"

    def _both_surfaces(self, srg_payload, band):
        eid = self._ingest_with_srg(self._TEXT, step=10, srg_payload=srg_payload)
        self._set_last_band(band)
        t_item = self._trace_item(eid, self._QUERY)
        q_item = self._require_query_item(eid, self._QUERY)
        return eid, q_item, t_item

    def test_explain_field_parity_all_three_modifiers(self):
        for label, payload, band, expected in (
            ("same_band", {"R_band": _BAND, "is_crystal": False, "heartbeat_class": "C"}, _BAND, 1.08),
            ("crystal", {"R_band": _OTHER_BAND, "is_crystal": True, "heartbeat_class": "C"}, _BAND, 1.05),
            ("heartbeat_a", {"R_band": _OTHER_BAND, "is_crystal": False, "heartbeat_class": "A"}, _BAND, 1.03),
            ("combined", {"R_band": _BAND, "is_crystal": True, "heartbeat_class": "A"}, _BAND, 1.08 * 1.05 * 1.03),
        ):
            with self.subTest(case=label):
                self.setUp()
                try:
                    _eid, q_item, t_item = self._both_surfaces(payload, band)
                    q_ex, t_ex = self._srg_explain(q_item), self._srg_explain(t_item)
                    self.assertEqual(
                        q_ex, t_ex,
                        msg=f"[{label}] query() and trace() SRG explain fields diverged:"
                            f"\n  query={q_ex}\n  trace={t_ex}",
                    )
                    self.assertAlmostEqual(q_ex["srg_total_multiplier"], expected, places=4)
                finally:
                    self.tearDown()

    def test_multiplicative_effect_parity(self):
        """Both surfaces must scale their own base score by the same factor.

        Compared as a RATIO, because query() and trace() legitimately compute
        different base scores (different lanes / assembly); the SRG contract is
        about the multiplier, not the absolute score.
        """
        payload = {"R_band": _BAND, "is_crystal": True, "heartbeat_class": "A"}
        eid = self._ingest_with_srg(self._TEXT, step=10, srg_payload=payload)
        self._set_last_band(_BAND)

        self.fabric._srg_enable = False
        t_off = self._trace_item(eid, self._QUERY)["final_score"]
        q_off = self._require_query_item(eid, self._QUERY)["final_score"]

        self.fabric._srg_enable = True
        self._set_last_band(_BAND)
        t_on = self._trace_item(eid, self._QUERY)["final_score"]
        q_on = self._require_query_item(eid, self._QUERY)["final_score"]

        expected = 1.08 * 1.05 * 1.03
        self.assertGreater(t_off, 0.0)
        self.assertGreater(q_off, 0.0)
        self.assertAlmostEqual(t_on / t_off, expected, places=4,
                               msg="trace() multiplicative effect")
        self.assertAlmostEqual(q_on / q_off, expected, places=4,
                               msg="query() multiplicative effect")
        self.assertAlmostEqual(t_on / t_off, q_on / q_off, places=6,
                               msg="query() and trace() multiplicative effects diverged")

    def test_neutral_parity_when_no_srg_payload(self):
        # Ingest with SRG OFF so no srg payload is created and no
        # last-ingest band is recorded.  (With SRG on, an organically
        # ingested memory necessarily matches the agent's own last-ingest
        # band, so the x1.08 same-band multiplier fires immediately — that
        # is correct production behaviour, not a neutral case.)
        self.fabric._srg_enable = False
        r = self.fabric.ingest(
            workspace_id=_WS, agent_id=_AG,
            text="plain parity memory with no srg state", step=10,
        )
        eid = r["eid"]
        self.fabric._srg_enable = True
        t_ex = self._srg_explain(self._trace_item(eid, "plain parity memory"))
        q_ex = self._srg_explain(self._require_query_item(eid, "plain parity memory"))
        self.assertEqual(q_ex, t_ex)
        self.assertAlmostEqual(q_ex["srg_total_multiplier"], 1.0, places=4)


# =========================================================================
# 4. Falsification — the parity assertion must CATCH one-sided divergence
# =========================================================================

class TestParityAssertionHasTeeth(_SRGFixtureBase):
    """Break one multiplier on the query side ONLY, with no production edit.

    ``_effective_srg_source`` is the shared read helper both surfaces use.  The
    patch below inspects the immediate caller's function name and strips
    ``is_crystal`` only when the caller is ``query`` (fabric.py:4003), leaving
    ``trace`` (fabric.py:6559) untouched.  Production source is not modified.

    If the parity assertions in TestQueryTraceSRGParity were incapable of
    observing query(), this test could not make them fail.
    """

    def test_query_only_divergence_is_detected(self):
        real_source = fabric_mod._effective_srg_source

        def query_only_broken(hit):
            src = real_source(hit)
            if src is None:
                return None
            caller = sys._getframe(1).f_code.co_name
            if caller == "query":
                broken = dict(src)
                broken.pop("is_crystal", None)   # kills the x1.05 on query only
                return broken
            return src

        eid = self._ingest_with_srg(
            "falsification anchor memory for one sided divergence", step=10,
            srg_payload={"R_band": _BAND, "is_crystal": True, "heartbeat_class": "A"},
        )
        self._set_last_band(_BAND)
        qtext = "falsification anchor divergence"

        # Baseline: unpatched, the two surfaces agree.
        t_ex = self._srg_explain(self._trace_item(eid, qtext))
        q_ex = self._srg_explain(self._require_query_item(eid, qtext))
        self.assertEqual(q_ex, t_ex, "baseline parity must hold before patching")

        fabric_mod._effective_srg_source = query_only_broken
        try:
            t_ex_b = self._srg_explain(self._trace_item(eid, qtext))
            q_ex_b = self._srg_explain(self._require_query_item(eid, qtext))
        finally:
            fabric_mod._effective_srg_source = real_source

        self.assertEqual(t_ex_b["srg_crystal_bonus"], 1.05,
                         "trace side must be unaffected by the query-only break")
        self.assertEqual(q_ex_b["srg_crystal_bonus"], 1.0,
                         "query side must lose the crystal multiplier under the patch")
        self.assertNotEqual(
            q_ex_b, t_ex_b,
            msg="parity comparison FAILED TO DETECT a one-sided query() divergence "
                "— the parity test would be vacuous",
        )


if __name__ == "__main__":
    unittest.main()
