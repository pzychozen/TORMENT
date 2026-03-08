# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
examples/python_client.py

Minimal Torment client (requests-based).
- Creates a workspace + two agents
- Ingests private memories
- Proposes shared canon from both agents
- Processes proposals (promotes to shared canon)
- Runs a query with explainability
- Pulls an inline trace view for one returned memory (if present)

Usage:
  python examples/python_client.py

Config via env:
  TORMENT_URL=http://127.0.0.1:8787
  TORMENT_WORKSPACE=my-ws
"""

from __future__ import annotations

import os
import sys
import json
import time
from typing import Any, Dict, List, Optional

import requests


def _env(name: str, default: str) -> str:
    v = os.environ.get(name, "").strip()
    return v if v else default


BASE_URL = _env("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
WORKSPACE_ID = _env("TORMENT_WORKSPACE", "demo-ws")


class TormentClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.s = requests.Session()

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self.s.post(self._url(path), json=payload, timeout=self.timeout_s)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"POST {path} failed: {r.status_code} {r.text}") from e
        return r.json()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = self.s.get(self._url(path), params=params or {}, timeout=self.timeout_s)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"GET {path} failed: {r.status_code} {r.text}") from e
        return r.json()

    # --- Workspace / agent

    def workspace_create(self, workspace_id: str) -> Dict[str, Any]:
        return self._post("/workspace/create", {"workspace_id": workspace_id})

    def agent_create(
        self,
        workspace_id: str,
        agent_id: str,
        coupling_mode: str = "read_only",
        coupling_strength: float = 0.6,
        domain_pref: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "coupling_mode": coupling_mode,
            "coupling_strength": coupling_strength,
            "domain_pref": domain_pref
            or {"research": 0.3, "engineering": 0.2, "operations": 0.2, "creative": 0.2, "meta": 0.1},
        }
        return self._post("/agent/create", payload)

    # --- Memory

    def ingest(
        self,
        workspace_id: str,
        agent_id: str,
        text: str,
        domain_id: Optional[str] = None,
        mtype: str = "episode",
        confidence: float = 0.7,
        strength: float = 0.75,
        scope: str = "private",  # "private" or "shared"
        supplied_summary: Optional[str] = None,
        supplied_embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "text": text,
            "mtype": mtype,
            "confidence": confidence,
            "strength": strength,
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
        mtype: str = "episode",
        confidence: float = 0.7,
        strength: float = 0.75,
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
        domain_id: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        return self._post(
            "/memory/trace_view",
            {
                "workspace_id": workspace_id,
                "eid": eid,
                "scope": scope,
                "domain_id": domain_id,
                "depth": depth,
                "export": "none",
            },
        )


def pp(title: str, obj: Any) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main() -> int:
    c = TormentClient(BASE_URL)

    # 1) Workspace
    ws = c.workspace_create(WORKSPACE_ID)
    pp("workspace_create", ws)

    # 2) Agents (two agents to satisfy min_distinct_agents=2 for canon promotion)
    a1 = c.agent_create(WORKSPACE_ID, "atlas-01", coupling_mode="read_only")
    a2 = c.agent_create(WORKSPACE_ID, "atlas-02", coupling_mode="read_only")
    pp("agent_create atlas-01", a1)
    pp("agent_create atlas-02", a2)

    # 3) Private ingests
    c.ingest(
        WORKSPACE_ID,
        "atlas-01",
        text="We decided: default domains are research, engineering, operations, creative, meta.",
        domain_id="meta",
    )
    c.ingest(
        WORKSPACE_ID,
        "atlas-02",
        text="Entropy should be monitored; merge suggestions when fragmentation rises.",
        domain_id="research",
    )

    # 4) Propose shared canon (same domain, two agents)
    pr1 = c.propose_share(
        WORKSPACE_ID,
        "atlas-01",
        summary="Torment uses fixed default domains: research, engineering, operations, creative, meta.",
        domain_id="meta",
    )
    pr2 = c.propose_share(
        WORKSPACE_ID,
        "atlas-02",
        summary="Torment uses fixed default domains: research, engineering, operations, creative, meta.",
        domain_id="meta",
    )
    pp("propose_share atlas-01", pr1)
    pp("propose_share atlas-02", pr2)

    # 5) Process proposals (promote to shared canon)
    proc = c.process_proposals(WORKSPACE_ID, domain_id="meta", min_distinct_agents=2)
    pp("process_proposals meta", proc)

    # 6) Query (with explain)
    q = c.query(
        WORKSPACE_ID,
        "atlas-01",
        query="What are the default domains?",
        domain_hint="meta",
        top_k=8,
        explain=True,
        peek_bridges=False,
    )
    pp("query explain", q)

    # 7) Trace view for first hit if available
    hits = q.get("hits") or q.get("results") or []
    if hits:
        hit0 = hits[0]
        eid = hit0.get("eid")
        scope = hit0.get("scope", "private")
        domain_id = hit0.get("domain_id", "meta")
        if isinstance(eid, int):
            tv = c.trace_view(WORKSPACE_ID, eid=eid, scope=scope, domain_id=domain_id, depth=2)
            pp(f"trace_view eid={eid} scope={scope} domain={domain_id}", tv)
        else:
            print("\nNo integer eid on first hit; trace_view skipped.")
    else:
        print("\nNo hits returned; trace_view skipped.")

    print("\n✅ Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())