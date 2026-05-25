#!/usr/bin/env python3
"""
tests/run_assembly_audit_smoke.py — S6 operator-run live verification.

Live smoke for Memory-to-Prompt v0.2 observability lane. Verifies the
end-to-end `/retrieve` audit path against a real running TORMENT
service: real HTTP, real serialization, real persistence, real
/embedder/check identity.

NOT a pytest test. Operator runs directly:

    cd /d C:\\TORMENT\\TORMENT_repo\\TORMENT-fabric_v2\\torment_fabric
    python tests\\run_assembly_audit_smoke.py

Prerequisites:
    - TORMENT service running at http://127.0.0.1:8787 (in a separate
      CMD window):
          cd /d C:\\TORMENT\\TORMENT_repo\\TORMENT-fabric_v2\\torment_fabric
          python -m torment_service
    - Hash embedder (default; no model download required).
    - Disposable workspace (created on first run, re-used on later
      runs; safe to wipe via `rmdir /s /q data\\workspaces\\audit_smoke_v0_2`):
          workspace_id = audit_smoke_v0_2
          agent_id     = smoke_runner

This script writes to a disposable workspace by default. It MUST NOT
be pointed at Ryuki, default, default_st, external_inference_smoke_st,
or any other protected character workspace. A hardcoded denylist
enforces this even when --workspace-id is overridden via CLI.

Doctrine: docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md §§4, 7.4 (Slice S6).
Pattern reference: tests/run_external_inference_smoke.py.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, List

import requests


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Hardcoded protected-workspace denylist. Operator override via
# --workspace-id cannot bypass this. To intentionally point S6 at one
# of these workspaces, edit this list AND document why.
_PROTECTED_WORKSPACES = frozenset({
    "ryuki",
    "default",
    "default_st",
    "external_inference_smoke_st",
})

_DEFAULT_BASE_URL = "http://127.0.0.1:8787"
_DEFAULT_WORKSPACE = "audit_smoke_v0_2"
_DEFAULT_AGENT = "smoke_runner"
_DEFAULT_EXPECTED_PROVIDER = "hash"

# Per Memory-to-Prompt v0.2 §4.2.
_EXPECTED_AUDIT_TOP_LEVEL_KEYS = frozenset({
    "lane_version",
    "timestamp",
    "request",
    "embedder",
    "filter_a",
    "assembly",
    "character",
    "spirit_return_summary",
    "tool_result_summary",
})

# Per Cluster 2 v0.1 §11.3.
_TOOL_RESULT_THREE_MODIFIER = "(low-authority, decay-bounded, tool_result)"

_TOOL_NAME = "audit_smoke:probe"
_AUDIT_KEY = "assembly_audit"
_QUERY_TEXT = "What did we decide about storage?"


# ---------------------------------------------------------------------------
# Findings collector — green / yellow / red
# ---------------------------------------------------------------------------

class FindingsCollector:
    """Collect hard checks (green/red) and soft observations (yellow).

    Exit code is 0 if no reds, else 1. Yellows never fail the run.
    """

    def __init__(self) -> None:
        self.greens: List[str] = []
        self.yellows: List[str] = []
        self.reds: List[str] = []

    def green(self, msg: str) -> None:
        self.greens.append(msg)
        print(f"  [GREEN]  {msg}")

    def yellow(self, msg: str) -> None:
        self.yellows.append(msg)
        print(f"  [YELLOW] {msg}")

    def red(self, msg: str) -> None:
        self.reds.append(msg)
        print(f"  [RED]    {msg}")

    def check(self, condition: bool, green_msg: str, red_msg: str) -> None:
        """Hard check — green on True, red on False."""
        if condition:
            self.green(green_msg)
        else:
            self.red(red_msg)

    def check_soft(self, condition: bool, green_msg: str, yellow_msg: str) -> None:
        """Soft check — green on True, yellow on False (does not fail)."""
        if condition:
            self.green(green_msg)
        else:
            self.yellow(yellow_msg)

    def summary_and_exit_code(self) -> int:
        print()
        print("=" * 64)
        print(f"  GREEN  : {len(self.greens)}")
        print(f"  YELLOW : {len(self.yellows)}")
        print(f"  RED    : {len(self.reds)}")
        print("=" * 64)
        if self.reds:
            print("\nRED FAILURES (block exit):")
            for r in self.reds:
                print(f"  - {r}")
        if self.yellows:
            print("\nYELLOW FINDINGS (non-blocking):")
            for y in self.yellows:
                print(f"  - {y}")
        return 1 if self.reds else 0


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _abort(msg: str, code: int = 2) -> None:
    print(f"\n[ABORT] {msg}", file=sys.stderr)
    sys.exit(code)


def _get(base_url: str, path: str, *, timeout: float = 10.0) -> requests.Response:
    try:
        return requests.get(f"{base_url}{path}", timeout=timeout)
    except requests.exceptions.RequestException as e:
        _abort(f"GET {path} failed: {e}")


def _post(
    base_url: str,
    path: str,
    payload: Dict[str, Any],
    *,
    timeout: float = 30.0,
    expect_status: tuple = (200,),
) -> requests.Response:
    try:
        r = requests.post(f"{base_url}{path}", json=payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        _abort(f"POST {path} failed: {e}")
    if r.status_code not in expect_status:
        _abort(
            f"POST {path} returned {r.status_code}: {r.text[:300]}"
        )
    return r


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def preflight(base_url: str, expected_provider: str) -> Dict[str, Any]:
    """Verify /health and /embedder/check. Returns the embedder check dict."""
    print("[1] Preflight")

    # /health
    r = _get(base_url, "/health")
    if r.status_code != 200:
        _abort(
            f"/health returned {r.status_code}; "
            f"is the service running at {base_url}?"
        )
    print(f"  /health: OK ({r.status_code})")

    # /embedder/check — required to be ok=True and degraded=False
    r = _get(base_url, "/embedder/check")
    if r.status_code != 200:
        _abort(f"/embedder/check returned {r.status_code}: {r.text[:200]}")
    chk = r.json()

    if not chk.get("ok"):
        _abort(
            f"/embedder/check ok={chk.get('ok')!r}, "
            f"error={chk.get('error', '')!r}"
        )
    if chk.get("degraded"):
        _abort(
            f"/embedder/check degraded=True (silent embedder degradation; "
            f"check TORMENT_EMBED_PROVIDER and friends). "
            f"hint={chk.get('hint', '')!r}"
        )

    actual_provider = str(chk.get("provider", ""))
    if actual_provider != expected_provider:
        _abort(
            f"/embedder/check provider={actual_provider!r}; "
            f"expected {expected_provider!r}. If this is intentional, "
            f"re-run with --expected-provider {actual_provider}."
        )

    print(
        f"  /embedder/check: ok=True, degraded=False, "
        f"provider={actual_provider!r}, "
        f"model={chk.get('model', '')!r}, "
        f"dim={chk.get('dim')}"
    )
    return chk


# ---------------------------------------------------------------------------
# Workspace + agent setup (create-or-reuse)
# ---------------------------------------------------------------------------

def setup_workspace_and_agent(
    base_url: str, workspace_id: str, agent_id: str
) -> None:
    print(f"[2] Workspace + agent setup")
    print(f"     workspace_id = {workspace_id}")
    print(f"     agent_id     = {agent_id}")

    # /workspace/create — tolerant of conflict-on-exists
    r = requests.post(
        f"{base_url}/workspace/create",
        json={"workspace_id": workspace_id},
        timeout=10,
    )
    if r.status_code == 200:
        print(f"  workspace created")
    elif r.status_code in (400, 409):
        print(f"  workspace already exists (re-using)")
    else:
        _abort(
            f"/workspace/create returned {r.status_code}: {r.text[:200]}"
        )

    # /agent/create — same tolerance
    r = requests.post(
        f"{base_url}/agent/create",
        json={
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "seed": {
                "coupling_mode": "read_only",
                "coupling_strength": 0.2,
            },
        },
        timeout=10,
    )
    if r.status_code == 200:
        print(f"  agent created")
    elif r.status_code in (400, 409):
        print(f"  agent already exists (re-using)")
    else:
        _abort(f"/agent/create returned {r.status_code}: {r.text[:200]}")


# ---------------------------------------------------------------------------
# Ingest fixtures (three small ingests per S6 plan §4)
# ---------------------------------------------------------------------------

def ingest_fixtures(
    base_url: str, workspace_id: str, agent_id: str
) -> None:
    print("[3] Ingest fixtures")

    # Fixture 1 — user input
    text1 = "We chose summaries plus embeddings for storage."
    r = _post(base_url, "/agent/ingest", {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "text": text1,
        "step": 1,
        "supplied_summary": text1,
        "scope": "private",
    })
    print(f"  ingest 1 (user_input): stored={r.json().get('stored')}")

    # Fixture 2 — user input
    text2 = "Character voice should preserve material meaning."
    r = _post(base_url, "/agent/ingest", {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "text": text2,
        "step": 2,
        "supplied_summary": text2,
        "scope": "private",
    })
    print(f"  ingest 2 (user_input): stored={r.json().get('stored')}")

    # Fixture 3 — tool_result via /tool/ingest
    text3 = "Probe tool output: storage doctrine remains intact."
    r = _post(base_url, "/tool/ingest", {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "text": text3,
        "tool_name": _TOOL_NAME,
        "scope": "private",
    })
    print(
        f"  ingest 3 (tool_result via {_TOOL_NAME!r}): "
        f"stored={r.json().get('stored')}"
    )


# ---------------------------------------------------------------------------
# /retrieve A/B
# ---------------------------------------------------------------------------

def call_retrieve(
    base_url: str,
    workspace_id: str,
    agent_id: str,
    *,
    include_audit: bool,
) -> Dict[str, Any]:
    payload = {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "query": _QUERY_TEXT,
        "profile": "companion",
        "token_budget": 1500,
        "top_k": 5,
        "include_assembly_audit": include_audit,
    }
    r = _post(base_url, "/retrieve", payload)
    return r.json()


# ---------------------------------------------------------------------------
# Verification — audit payload shape per v0.2 §4.2
# ---------------------------------------------------------------------------

def verify_audit(
    audit: Dict[str, Any],
    embedder_check: Dict[str, Any],
    workspace_id: str,
    agent_id: str,
    findings: FindingsCollector,
) -> None:
    print("\n[5] Audit payload verification")

    # Top-level shape — hard
    findings.check(
        set(audit.keys()) == _EXPECTED_AUDIT_TOP_LEVEL_KEYS,
        "audit top-level keys match v0.2 §4.2 schema",
        (
            f"audit top-level keys diverge: "
            f"extra={sorted(set(audit.keys()) - _EXPECTED_AUDIT_TOP_LEVEL_KEYS)}, "
            f"missing={sorted(_EXPECTED_AUDIT_TOP_LEVEL_KEYS - set(audit.keys()))}"
        ),
    )

    # lane_version — hard
    findings.check(
        audit.get("lane_version") == "memory_to_prompt_observability_v0.2",
        "lane_version is memory_to_prompt_observability_v0.2",
        f"lane_version mismatch: got {audit.get('lane_version')!r}",
    )

    # timestamp — hard
    ts = audit.get("timestamp")
    now = int(time.time())
    findings.check(
        isinstance(ts, int) and ts > 1577836800 and ts <= now + 2,
        f"timestamp is int and recent ({ts})",
        f"timestamp invalid: {ts!r} (now={now})",
    )

    # request block — hard
    req = audit.get("request") or {}
    findings.check(
        req.get("workspace_id") == workspace_id,
        f"request.workspace_id matches ({workspace_id})",
        f"request.workspace_id mismatch: got {req.get('workspace_id')!r}",
    )
    findings.check(
        req.get("agent_id") == agent_id,
        f"request.agent_id matches ({agent_id})",
        f"request.agent_id mismatch: got {req.get('agent_id')!r}",
    )
    findings.check(
        req.get("surface") == "llm_context",
        "request.surface is llm_context",
        f"request.surface mismatch: got {req.get('surface')!r}",
    )

    # embedder block — hard (matches /embedder/check)
    emb = audit.get("embedder") or {}
    findings.check(
        emb.get("provider") == embedder_check.get("provider"),
        f"embedder.provider matches /embedder/check ({emb.get('provider')!r})",
        (
            f"embedder.provider mismatch: "
            f"audit={emb.get('provider')!r} vs check={embedder_check.get('provider')!r}"
        ),
    )
    findings.check(
        emb.get("model") == embedder_check.get("model"),
        f"embedder.model matches /embedder/check ({emb.get('model')!r})",
        (
            f"embedder.model mismatch: "
            f"audit={emb.get('model')!r} vs check={embedder_check.get('model')!r}"
        ),
    )
    findings.check(
        emb.get("dim") == embedder_check.get("dim"),
        f"embedder.dim matches /embedder/check ({emb.get('dim')})",
        (
            f"embedder.dim mismatch: "
            f"audit={emb.get('dim')} vs check={embedder_check.get('dim')}"
        ),
    )

    # filter_a block — hard
    fa = audit.get("filter_a") or {}
    findings.check(
        fa.get("archive_filter_applied") is False,
        "filter_a.archive_filter_applied is False (v0.2 §3.2 honest report)",
        (
            f"filter_a.archive_filter_applied unexpected: "
            f"{fa.get('archive_filter_applied')!r} (expected False; if True, "
            f"archive-FILTER-A fix landed without v0.2 doctrine update)"
        ),
    )
    findings.check(
        fa.get("authority_guard_rejected") == 0,
        "filter_a.authority_guard_rejected is 0 (H4d fail-loud)",
        (
            f"filter_a.authority_guard_rejected unexpected: "
            f"{fa.get('authority_guard_rejected')!r} (H4d should fail-loud)"
        ),
    )
    in_count = fa.get("core_hits_in_count", 0)
    out_count = fa.get("core_hits_out_count", 0)
    excluded_count = len(fa.get("excluded") or [])
    findings.check(
        in_count == out_count + excluded_count,
        (
            f"filter_a arithmetic holds "
            f"(in={in_count} == out={out_count} + excluded={excluded_count})"
        ),
        (
            f"filter_a arithmetic violated: "
            f"in={in_count}, out={out_count}, excluded={excluded_count}"
        ),
    )

    # tool_result_summary — hard on three_modifier, soft on count
    trs = audit.get("tool_result_summary") or {}
    findings.check(
        trs.get("three_modifier") == _TOOL_RESULT_THREE_MODIFIER,
        f"tool_result_summary.three_modifier matches Cluster 2 §11.3 verbatim",
        f"tool_result_summary.three_modifier mismatch: got {trs.get('three_modifier')!r}",
    )

    count_in_prompt = int(trs.get("count_in_prompt", 0) or 0)
    findings.check_soft(
        count_in_prompt >= 1,
        (
            f"tool_result_summary.count_in_prompt = {count_in_prompt} "
            f"(tool_result row entered prompt context)"
        ),
        (
            f"tool_result_summary.count_in_prompt = 0 — tool_result row was "
            f"ingested but did not enter prompt context this run (possibly "
            f"outranked or budget-skipped). Lane is wired correctly; "
            f"tool-result surfacing was not exercised by this query/budget."
        ),
    )
    if count_in_prompt >= 1:
        tool_names = trs.get("tool_names") or []
        findings.check(
            _TOOL_NAME in tool_names,
            f"tool_result_summary.tool_names contains {_TOOL_NAME!r}",
            (
                f"tool_result_summary.tool_names missing {_TOOL_NAME!r}: "
                f"got {tool_names!r}"
            ),
        )

    # assembly block — hard on structure
    asm = audit.get("assembly") or {}
    findings.check(
        asm.get("profile_used") == "companion",
        "assembly.profile_used is companion",
        f"assembly.profile_used mismatch: got {asm.get('profile_used')!r}",
    )
    findings.check(
        isinstance(asm.get("blocks"), dict),
        "assembly.blocks is a dict",
        f"assembly.blocks invalid type: {type(asm.get('blocks')).__name__}",
    )
    findings.check(
        isinstance(asm.get("selection_log_enriched"), list),
        "assembly.selection_log_enriched is a list",
        (
            f"assembly.selection_log_enriched invalid type: "
            f"{type(asm.get('selection_log_enriched')).__name__}"
        ),
    )
    findings.check(
        isinstance(asm.get("profile_weights"), dict),
        "assembly.profile_weights is a dict",
        f"assembly.profile_weights invalid: {type(asm.get('profile_weights')).__name__}",
    )

    # spirit_return_summary — soft (zero expected on fresh disposable)
    sr = audit.get("spirit_return_summary") or {}
    findings.check_soft(
        int(sr.get("total", 0) or 0) == 0,
        "spirit_return_summary.total is 0 (expected on fresh disposable workspace)",
        (
            f"spirit_return_summary.total = {sr.get('total')} — unexpected on "
            f"fresh disposable workspace with 3 small ingests; investigate"
        ),
    )

    # character block — hard on types only
    char = audit.get("character") or {}
    findings.check(
        isinstance(char.get("drift_score"), (int, float)),
        f"character.drift_score is numeric ({char.get('drift_score')})",
        f"character.drift_score invalid type: {type(char.get('drift_score')).__name__}",
    )
    findings.check(
        isinstance(char.get("relational_count"), int),
        f"character.relational_count is int ({char.get('relational_count')})",
        f"character.relational_count invalid type: {type(char.get('relational_count')).__name__}",
    )


# ---------------------------------------------------------------------------
# Verification — A/B byte identity (audit-on does not change normal output)
# ---------------------------------------------------------------------------

def verify_ab_byte_identity(
    body_off: Dict[str, Any],
    body_on: Dict[str, Any],
    findings: FindingsCollector,
) -> None:
    print("\n[6] A/B verification (audit-on vs audit-off)")

    extra = set(body_on.keys()) - set(body_off.keys())
    findings.check(
        extra == {_AUDIT_KEY},
        f"audit-on response adds exactly {{'{_AUDIT_KEY}'}}",
        f"audit-on response adds unexpected keys: {sorted(extra)!r}",
    )

    missing = set(body_off.keys()) - set(body_on.keys())
    findings.check(
        not missing,
        "audit-on response does not drop any keys present in audit-off",
        (
            f"audit-on response is missing keys present in audit-off: "
            f"{sorted(missing)!r}"
        ),
    )

    common_keys = (
        "blocks",
        "assembled_text",
        "tokens_used",
        "profile",
        "block_token_counts",
        "token_budget",
        "selection_log",
    )
    for key in common_keys:
        findings.check(
            body_off.get(key) == body_on.get(key),
            f"common key {key!r} byte-identical between audit-off and audit-on",
            f"common key {key!r} diverges between audit-off and audit-on",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description=(
            "S6 live verification for /retrieve include_assembly_audit "
            "(Memory-to-Prompt v0.2 observability lane)."
        )
    )
    p.add_argument("--base-url", default=_DEFAULT_BASE_URL,
                   help=f"TORMENT service URL (default: {_DEFAULT_BASE_URL})")
    p.add_argument(
        "--workspace-id",
        default=_DEFAULT_WORKSPACE,
        help=(
            f"Disposable workspace (default: {_DEFAULT_WORKSPACE}). "
            f"Cannot be a protected name."
        ),
    )
    p.add_argument(
        "--agent-id",
        default=_DEFAULT_AGENT,
        help=f"Smoke agent (default: {_DEFAULT_AGENT})",
    )
    p.add_argument(
        "--expected-provider",
        default=_DEFAULT_EXPECTED_PROVIDER,
        help=(
            f"Expected embedder provider (default: {_DEFAULT_EXPECTED_PROVIDER}). "
            f"If the service is intentionally running ST, pass --expected-provider st."
        ),
    )
    args = p.parse_args()

    # Hardcoded denylist enforcement — cannot be bypassed by --workspace-id.
    if args.workspace_id in _PROTECTED_WORKSPACES:
        _abort(
            f"workspace_id={args.workspace_id!r} is in the protected denylist "
            f"{sorted(_PROTECTED_WORKSPACES)}. This script must not write to "
            f"protected workspaces. Choose a disposable name (or edit the "
            f"_PROTECTED_WORKSPACES constant in this file if the trio has "
            f"explicitly authorized writing to that workspace)."
        )

    print("=" * 64)
    print("  S6 assembly-audit smoke verification")
    print("=" * 64)
    print(f"base_url:          {args.base_url}")
    print(f"workspace:         {args.workspace_id}")
    print(f"agent:             {args.agent_id}")
    print(f"expected provider: {args.expected_provider}")
    print()

    findings = FindingsCollector()

    # 1. Preflight
    embedder_check = preflight(args.base_url, args.expected_provider)
    print()

    # 2. Workspace + agent
    setup_workspace_and_agent(args.base_url, args.workspace_id, args.agent_id)
    print()

    # 3. Ingest
    ingest_fixtures(args.base_url, args.workspace_id, args.agent_id)

    # 4. A/B /retrieve
    print("\n[4] /retrieve A/B")
    body_off = call_retrieve(
        args.base_url, args.workspace_id, args.agent_id, include_audit=False
    )
    print(f"  audit-off keys: {sorted(body_off.keys())}")
    body_on = call_retrieve(
        args.base_url, args.workspace_id, args.agent_id, include_audit=True
    )
    print(f"  audit-on keys:  {sorted(body_on.keys())}")

    if _AUDIT_KEY not in body_on:
        _abort(
            f"audit-on response missing {_AUDIT_KEY!r} key — "
            f"is the service running the S5 wiring commit?"
        )

    audit = body_on[_AUDIT_KEY]

    # 5. Audit payload checks
    embedder_for_audit = {
        "provider": embedder_check.get("provider"),
        "model": embedder_check.get("model"),
        "dim": embedder_check.get("dim"),
    }
    verify_audit(
        audit, embedder_for_audit, args.workspace_id, args.agent_id, findings
    )

    # 6. A/B byte identity
    verify_ab_byte_identity(body_off, body_on, findings)

    # 7. Pretty-print audit payload for operator inspection
    print("\n[7] assembly_audit payload (for inspection):")
    print(json.dumps(audit, indent=2, default=str))

    # 8. Summary + exit code
    exit_code = findings.summary_and_exit_code()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
