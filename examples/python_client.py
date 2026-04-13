#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/python_client.py

Low-level TORMENT API walkthrough (requests-based).

What this example demonstrates:
- health check
- workspace creation
- idempotent agent creation
- private memory ingest
- shared-canon proposal from two agents
- proposal processing / promotion
- query with explainability
- optional trace view for a returned memory

What this example is NOT:
- not a chat client
- not a full character runtime
- not an MCP client

Usage:
    python examples/python_client.py

Config via env:
    TORMENT_URL=http://127.0.0.1:8787
    TORMENT_WORKSPACE=demo-ws
    TORMENT_TOP_K=8

Notes:
- This is a low-level substrate/API example meant to be easy to run.
- It is intentionally deterministic and does not require an LLM API key.
- It uses two demo agents so shared-canon promotion can satisfy
  min_distinct_agents=2.

NEVER hardcode secrets in files.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests


# ---------------------------------------------------------------------------
# Env helpers / config
# ---------------------------------------------------------------------------

def _env(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value if value else default


BASE_URL = _env("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
WORKSPACE_ID = _env("TORMENT_WORKSPACE", "demo-ws")
TOP_K = int(_env("TORMENT_TOP_K", "8"))

DEFAULT_DOMAINS = ["research", "engineering", "operations", "creative", "meta"]


# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def info(msg: str) -> None:
    print(f"  • {msg}")


def success(msg: str) -> None:
    print(f"  ✅ {msg}")


def warning(msg: str) -> None:
    print(f"  ⚠️  {msg}")


def dump_json(label: str, obj: Any) -> None:
    section(label)
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def print_hits(result: Dict[str, Any]) -> None:
    hits = result.get("hits") or result.get("results") or []
    if not hits:
        warning("No hits returned.")
        return

    info(f"{len(hits)} hit(s) returned:")
    for i, hit in enumerate(hits[:TOP_K], 1):
        eid = hit.get("eid", "?")
        scope = hit.get("scope", "?")
        domain = hit.get("domain_id", "?")
        score = hit.get("final_score", hit.get("score", 0.0))
        summary = hit.get("summary", "")
        print(f"    {i}. eid={eid}  score={score:.2f}  scope={scope}  domain={domain}")
        if summary:
            print(f"       {summary[:140]}")


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class TormentClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(self._url(path), json=payload, timeout=self.timeout_s)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"POST {path} failed: {response.status_code} {response.text}"
            ) from e
        return response.json()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self.session.get(self._url(path), params=params or {}, timeout=self.timeout_s)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"GET {path} failed: {response.status_code} {response.text}"
            ) from e
        return response.json()

    # --- Health / workspace / agents -------------------------------------------------

    def health(self) -> Dict[str, Any]:
        return self._get("/health")

    def workspace_create(
        self,
        workspace_id: str,
        domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"workspace_id": workspace_id}
        if domains:
            payload["domains"] = domains
        return self._post("/workspace/create", payload)

    def agent_create(
        self,
        workspace_id: str,
        agent_id: str,
        seed: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Note: the real /agent/create request schema accepts only
        # (workspace_id, agent_id, seed).  Coupling mode, coupling strength,
        # and domain preferences are properties of the seed/overlay — if you
        # want to set them, put them inside `seed`.
        payload: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
        }
        if seed is not None:
            payload["seed"] = seed
        return self._post("/agent/create", payload)

    # --- Memory ----------------------------------------------------------------------

    def ingest(
        self,
        workspace_id: str,
        agent_id: str,
        text: str,
        step: int = 0,
        domain_id: Optional[str] = None,
        scope: str = "private",
        supplied_summary: Optional[str] = None,
        supplied_embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        # Note: the real /agent/ingest request schema accepts
        # (workspace_id, agent_id, text, step, domain_id, scope,
        # supplied_summary, supplied_embedding).  `step` is the deterministic
        # replay counter — pass a monotonic value per agent if you care about
        # reproducible ordering.
        payload: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "text": text,
            "step": step,
            "scope": scope,
        }
        if domain_id:
            payload["domain_id"] = domain_id
        if supplied_summary is not None:
            payload["supplied_summary"] = supplied_summary
        if supplied_embedding is not None:
            payload["supplied_embedding"] = supplied_embedding
        return self._post("/agent/ingest", payload)

    def propose_share(
        self,
        workspace_id: str,
        agent_id: str,
        summary: str,
        domain_id: str,
        mtype: str = "fact",
        confidence: float = 0.6,
        strength: float = 0.6,
        supplied_embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "summary": summary,
            "domain_id": domain_id,
            "mtype": mtype,
            "confidence": confidence,
            "strength": strength,
        }
        if supplied_embedding is not None:
            payload["supplied_embedding"] = supplied_embedding
        return self._post("/agent/propose_share", payload)

    def process_proposals(
        self,
        workspace_id: str,
        domain_id: str,
        min_distinct_agents: int = 2,
        max_to_process: int = 200,
    ) -> Dict[str, Any]:
        return self._post(
            "/workspace/process_proposals",
            {
                "workspace_id": workspace_id,
                "domain_id": domain_id,
                "min_distinct_agents": min_distinct_agents,
                "max_to_process": max_to_process,
            },
        )

    def query(
        self,
        workspace_id: str,
        agent_id: str,
        query: str,
        domain_hint: Optional[str] = None,
        top_k: int = 8,
        explain: bool = True,
        peek_bridges: bool = False,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "query": query,
            "top_k": top_k,
            "explain": explain,
            "peek_bridges": peek_bridges,
        }
        if domain_hint:
            payload["domain_id"] = domain_hint
        return self._post("/agent/query", payload)

    def trace_view(
        self,
        workspace_id: str,
        eid: int,
        scope: str,
        domain_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        depth: int = 2,
        explain: bool = False,
    ) -> Dict[str, Any]:
        # Note: for scope="private" the server needs `agent_id` to locate the
        # memory.  For scope="shared" it needs `domain_id`.  Pass whichever is
        # appropriate for the hit you are tracing.
        payload: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "eid": eid,
            "scope": scope,
            "depth": depth,
            "explain": explain,
        }
        if domain_id is not None:
            payload["domain_id"] = domain_id
        if agent_id is not None:
            payload["agent_id"] = agent_id
        return self._post("/memory/trace_view", payload)


# ---------------------------------------------------------------------------
# Idempotent setup helpers
# ---------------------------------------------------------------------------

def ensure_workspace(
    client: TormentClient,
    workspace_id: str,
    domains: List[str],
) -> None:
    try:
        client.workspace_create(workspace_id, domains=domains)
        success(f"Workspace '{workspace_id}' created.")
    except RuntimeError as e:
        if " 409 " in str(e):
            info(f"Workspace '{workspace_id}' already exists.")
        else:
            raise


def ensure_agent(
    client: TormentClient,
    workspace_id: str,
    agent_id: str,
    seed: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        client.agent_create(
            workspace_id,
            agent_id,
            seed=seed,
        )
        success(f"Agent '{agent_id}' created.")
    except RuntimeError as e:
        if " 409 " in str(e):
            info(f"Agent '{agent_id}' already exists.")
        else:
            raise


# ---------------------------------------------------------------------------
# Main walkthrough
# ---------------------------------------------------------------------------

def main() -> int:
    section("TORMENT low-level API walkthrough")
    info(f"Base URL: {BASE_URL}")
    info(f"Workspace: {WORKSPACE_ID}")
    info(f"Top-K: {TOP_K}")

    client = TormentClient(BASE_URL)

    # 0) Preflight
    section("0) Health check")
    try:
        health = client.health()
        success("TORMENT server is reachable.")
        print(json.dumps(health, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n  TORMENT server not reachable at {BASE_URL}")
        print(f"  Error: {e}")
        print("\n  Start it first, for example:")
        print("    python -m torment_service.app\n")
        return 1

    # 1) Workspace
    section("1) Ensure workspace")
    ensure_workspace(client, WORKSPACE_ID, DEFAULT_DOMAINS)

    # 2) Agents
    section("2) Ensure demo agents")
    agent_a = "demo_researcher"
    agent_b = "demo_operator"
    ensure_agent(
        client,
        WORKSPACE_ID,
        agent_a,
        seed={
            "seed_text": "Demo researcher agent — read-only coupling, exploring the substrate.",
            "coupling_mode": "read_only",
            "coupling_strength": 0.6,
        },
    )
    ensure_agent(
        client,
        WORKSPACE_ID,
        agent_b,
        seed={
            "seed_text": "Demo operator agent — read-only coupling, watching for drift and fragmentation.",
            "coupling_mode": "read_only",
            "coupling_strength": 0.6,
        },
    )

    # 3) Private ingests
    # `step` is the deterministic replay counter — pass a monotonic value per
    # agent so the walkthrough is reproducible.
    section("3) Private memory ingest")
    ingest_a = client.ingest(
        WORKSPACE_ID,
        agent_a,
        text="We decided that TORMENT uses fixed default domains: research, engineering, operations, creative, meta.",
        domain_id="meta",
        step=1,
    )
    ingest_b = client.ingest(
        WORKSPACE_ID,
        agent_b,
        text="Entropy should be monitored, and merge suggestions should be considered when fragmentation rises.",
        domain_id="research",
        step=1,
    )
    success("Private memories ingested.")
    info(f"{agent_a} ingest status recorded.")
    info(f"{agent_b} ingest status recorded.")
    dump_json("ingest demo_researcher", ingest_a)
    dump_json("ingest demo_operator", ingest_b)

    # 4) Shared canon proposals
    section("4) Propose shared canon")
    shared_summary = (
        "TORMENT uses fixed default domains: research, engineering, operations, creative, meta."
    )
    pr1 = client.propose_share(
        WORKSPACE_ID,
        agent_a,
        summary=shared_summary,
        domain_id="meta",
    )
    pr2 = client.propose_share(
        WORKSPACE_ID,
        agent_b,
        summary=shared_summary,
        domain_id="meta",
    )
    success("Both agents proposed shared canon for the same summary.")
    dump_json("propose_share demo_researcher", pr1)
    dump_json("propose_share demo_operator", pr2)

    # 5) Process proposals
    section("5) Process proposals")
    proc = client.process_proposals(
        WORKSPACE_ID,
        domain_id="meta",
        min_distinct_agents=2,
    )
    success("Proposal processing completed.")
    dump_json("process_proposals", proc)

    # 6) Query with explainability
    section("6) Query with explainability")
    query_result = client.query(
        WORKSPACE_ID,
        agent_a,
        query="What are the default domains?",
        domain_hint="meta",
        top_k=TOP_K,
        explain=True,
        peek_bridges=False,
    )
    success("Explain query completed.")
    print_hits(query_result)
    dump_json("query explain", query_result)

    # 7) Optional trace view for first hit
    section("7) Optional trace view")
    hits = query_result.get("hits") or query_result.get("results") or []
    if not hits:
        warning("No hits returned, so trace_view is skipped.")
    else:
        first_hit = hits[0]
        eid = first_hit.get("eid")
        scope = first_hit.get("scope", "private")
        domain_id = first_hit.get("domain_id", "meta")

        if isinstance(eid, int):
            # For private-scope hits, trace_view needs agent_id; for
            # shared-scope hits, it needs domain_id.  Pass the right one.
            if scope == "private":
                trace = client.trace_view(
                    WORKSPACE_ID,
                    eid=eid,
                    scope=scope,
                    agent_id=agent_a,
                    depth=2,
                )
            else:
                trace = client.trace_view(
                    WORKSPACE_ID,
                    eid=eid,
                    scope=scope,
                    domain_id=domain_id,
                    depth=2,
                )
            success(f"Trace view retrieved for eid={eid}.")
            dump_json(f"trace_view eid={eid} scope={scope} domain={domain_id}", trace)
        else:
            warning("First hit does not expose an integer eid, so trace_view is skipped.")

    section("Done")
    success("Low-level API walkthrough completed.")
    info("This example is a substrate smoke test, not a chat runtime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())