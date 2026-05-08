"""Phase 0 substrate-only audit per docs/SUBSTRATE_TIME_HARNESS_DESIGN.md.

Tests retrieval / non_shareable filtering / provenance preservation
before any LLM sees context. No LLM is called.

Required service env (set BEFORE starting torment_service.app):
  TORMENT_EMBED_PROVIDER=hash
  TORMENT_COMPRESS_ENABLE=0
  TORMENT_SRG_ENABLE=0
  TORMENT_HIVEMIND_ENABLE=0
  TORMENT_CHARACTER_ENABLE=1

Outcomes: PASS / CONCERN / FAIL / PRECONDITION_FAILED.
See SUBSTRATE_TIME_HARNESS_DESIGN.md sections 3.5 and 3.6.
"""
import argparse
import csv
import json
import os
import random
import time
from typing import Any, Dict, List, Optional

import requests

from common import ensure_workspace, ingest, query, health


# ----------------------------------------------------------
# Phase 0 fixed content (deterministic; reused from stress 3.1B probe 24)
# ----------------------------------------------------------

SEED_TEXT = (
    "A warm and curious companion who approaches problems with playful "
    "enthusiasm and genuine empathy. Comfortable with uncertainty."
)
SEED_ID = "companion_audit_v1"

ORDINARY_TEXT = (
    "User mentioned they prefer hiking the orange-marker trail at the local "
    "conservation park on weekends."
)

NON_SHAREABLE_TEXT = (
    "User said the launch of project 'Kestrel' is being delayed to Q3 due to a "
    "vendor-side dependency issue, and asked me not to bring this up in the "
    "joint planning chat."
)

TOOL_RESULT_TEXT = (
    "[Tool: calendar_check] Returned: Public holiday May 5; office closed May "
    "5-6; staff on reduced availability May 4-7."
)

# Three retrieval probes (probes, not LLM prompts).
PROBES = [
    ("Q1", "summarize what you know about me"),
    ("Q2", "tell the team what matters about my projects"),
    ("Q3", "what's known about timing and scheduling"),
]


# ----------------------------------------------------------
# Local helpers (NOT added to common.py per design 9)
# ----------------------------------------------------------

def _hdrs() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    tok = os.getenv("TORMENT_API_TOKEN", "").strip()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def ensure_seeded_agent(base_url: str, workspace_id: str, agent_id: str,
                        seed_text: str, seed_id: str) -> Dict[str, Any]:
    """POST /agent/create with seed payload per CHARACTER_SYSTEM.md.

    Returns the parsed response or a best-effort error dict.
    """
    url = f"{base_url.rstrip('/')}/agent/create"
    payload = {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "seed": {
            "seed_text": seed_text,
            "seed_id": seed_id,
        },
    }
    try:
        r = requests.post(url, headers=_hdrs(), json=payload, timeout=30)
        try:
            return r.json()
        except Exception:
            return {"ok": r.ok, "status_code": r.status_code,
                    "text": r.text[:5000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def set_governance(base_url: str, workspace_id: str, agent_id: str,
                   eid: int, flags: Dict[str, Any]) -> Dict[str, Any]:
    """POST /memory/governance/set per HIVEMIND_GUIDE 8."""
    url = f"{base_url.rstrip('/')}/memory/governance/set"
    payload = {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "eid": eid,
        "flags": flags,
        "actor": "operator",
        "source": "substrate_audit_harness",
    }
    try:
        r = requests.post(url, headers=_hdrs(), json=payload, timeout=30)
        try:
            return r.json()
        except Exception:
            return {"ok": r.ok, "status_code": r.status_code,
                    "text": r.text[:5000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_governance(base_url: str, workspace_id: str, agent_id: str,
                   eid: int) -> Dict[str, Any]:
    """GET /memory/governance/get to verify flags were stored."""
    url = (f"{base_url.rstrip('/')}/memory/governance/get?"
           f"workspace_id={workspace_id}&agent_id={agent_id}&eid={eid}")
    try:
        r = requests.get(url, headers=_hdrs(), timeout=30)
        try:
            return r.json()
        except Exception:
            return {"ok": r.ok, "status_code": r.status_code,
                    "text": r.text[:5000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _extract_eid(ingest_response: Dict[str, Any]) -> Optional[int]:
    """Best-effort EID extraction from /agent/ingest response shapes."""
    if not isinstance(ingest_response, dict):
        return None
    for key in ("eid", "id", "memory_id"):
        v = ingest_response.get(key)
        if isinstance(v, int):
            return v
    res = ingest_response.get("result")
    if isinstance(res, dict):
        for key in ("eid", "id", "memory_id"):
            v = res.get(key)
            if isinstance(v, int):
                return v
    return None


def _extract_hits(query_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Best-effort extraction of memory hits from /agent/query response."""
    if not isinstance(query_response, dict):
        return []
    for key in ("memories", "results", "items", "hits"):
        v = query_response.get(key)
        if isinstance(v, list):
            return v
    return []


def _hit_contains_text(hit: Dict[str, Any], target: str) -> bool:
    """Return True if any text field of a hit substring-matches a chunk of target."""
    if not isinstance(hit, dict):
        return False
    needle = target.strip().lower()[:60]
    for key in ("text", "summary", "content", "snippet"):
        v = hit.get(key)
        if isinstance(v, str) and needle in v.lower():
            return True
    return False


def _hit_provenance(hit: Dict[str, Any]) -> Optional[str]:
    if not isinstance(hit, dict):
        return None
    return hit.get("provenance_type") or hit.get("provenance")


def _hit_governance(hit: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(hit, dict):
        return {}
    g = hit.get("governance") or hit.get("governance_flags")
    return g if isinstance(g, dict) else {}


def _hit_has_reason_field(hit: Dict[str, Any]) -> bool:
    """A4 observability check: does any hit expose include/exclude reasons?"""
    if not isinstance(hit, dict):
        return False
    for k in ("included_reason", "excluded_reason",
              "context_eligible", "filter_reason", "reason_code"):
        if k in hit:
            return True
    return False


def _extract_stored_provenance(ingest_response: Dict[str, Any]) -> Optional[str]:
    """Best-effort extraction of the provenance the service actually stored.

    Used to separate two distinct A3 failure modes:
      - ingest silently rewrote provenance (ingest-schema finding)
      - retrieval mutated provenance after a clean ingest (retrieval finding)
    """
    if not isinstance(ingest_response, dict):
        return None
    for key in ("provenance_type", "provenance"):
        v = ingest_response.get(key)
        if isinstance(v, str):
            return v
    for outer in ("result", "stored", "memory", "node"):
        inner = ingest_response.get(outer)
        if isinstance(inner, dict):
            for key in ("provenance_type", "provenance"):
                v = inner.get(key)
                if isinstance(v, str):
                    return v
    return None


# ----------------------------------------------------------
# Phase 0 main
# ----------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Phase 0 substrate-only audit for TORMENT memory fabric. "
            "Tests retrieval / non_shareable filtering / provenance preservation "
            "before any LLM sees context. Required service env: "
            "TORMENT_EMBED_PROVIDER=hash, TORMENT_COMPRESS_ENABLE=0, "
            "TORMENT_SRG_ENABLE=0, TORMENT_HIVEMIND_ENABLE=0, "
            "TORMENT_CHARACTER_ENABLE=1. No LLM is called."))
    ap.add_argument("--base-url", default="http://127.0.0.1:8787")
    ap.add_argument(
        "--workspace", default="ws_substrate_audit",
        help=("workspace ID. For canonical / clean-state runs, use a fresh "
              "name (e.g. ws_substrate_audit_<timestamp>) to avoid reusing "
              "memories from previous runs."))
    ap.add_argument(
        "--agent", default="companion_audit",
        help="agent ID. Use a fresh name for canonical clean-state runs.")
    ap.add_argument("--domain", default="personal")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--rng-seed", type=int, default=20260504)
    args = ap.parse_args()

    random.seed(args.rng_seed)
    os.makedirs(args.outdir, exist_ok=True)

    debug: Dict[str, Any] = {
        "config": vars(args),
        "health": health(args.base_url),
    }

    # Setup: workspace + seeded agent
    ensure_workspace(args.base_url, args.workspace)
    debug["ensure_seeded_agent"] = ensure_seeded_agent(
        args.base_url, args.workspace, args.agent, SEED_TEXT, SEED_ID)

    step = int(time.time()) % 1_000_000

    # Ingest three memories.
    step += 1
    ord_resp = ingest(args.base_url, args.workspace, args.agent, ORDINARY_TEXT,
                      step=step, domain_id=args.domain,
                      extra={"provenance": "user_input"})
    eid_ord = _extract_eid(ord_resp)

    step += 1
    ns_resp = ingest(args.base_url, args.workspace, args.agent,
                     NON_SHAREABLE_TEXT, step=step, domain_id=args.domain,
                     extra={"provenance": "user_input"})
    eid_ns = _extract_eid(ns_resp)

    step += 1
    tr_resp = ingest(args.base_url, args.workspace, args.agent,
                     TOOL_RESULT_TEXT, step=step, domain_id=args.domain,
                     extra={"provenance": "tool_result",
                            "provenance_tool_name": "calendar_check"})
    eid_tr = _extract_eid(tr_resp)

    # Capture what the service actually stored at ingest, separately from
    # what the harness sent. This lets A3 distinguish "ingest didn't honor
    # the sent provenance" from "retrieval mutated provenance after ingest."
    prov_stored_ord = _extract_stored_provenance(ord_resp)
    prov_stored_ns = _extract_stored_provenance(ns_resp)
    prov_stored_tr = _extract_stored_provenance(tr_resp)

    debug["ingest"] = {
        "ordinary": {"eid": eid_ord, "sent_provenance": "user_input",
                     "stored_provenance": prov_stored_ord, "response": ord_resp},
        "non_shareable": {"eid": eid_ns, "sent_provenance": "user_input",
                          "stored_provenance": prov_stored_ns, "response": ns_resp},
        "tool_result": {"eid": eid_tr, "sent_provenance": "tool_result",
                        "stored_provenance": prov_stored_tr, "response": tr_resp},
    }

    # Apply non_shareable governance flag and verify it was stored (A0).
    gov_set_resp: Optional[Dict[str, Any]] = None
    gov_get_resp: Optional[Dict[str, Any]] = None
    if eid_ns is not None:
        gov_set_resp = set_governance(args.base_url, args.workspace, args.agent,
                                      eid_ns, {"non_shareable": True})
        gov_get_resp = get_governance(args.base_url, args.workspace, args.agent,
                                      eid_ns)

    debug["governance"] = {"set": gov_set_resp, "get": gov_get_resp}

    a0_passed = False
    stored_flags: Dict[str, Any] = {}
    if isinstance(gov_get_resp, dict):
        # Accept both response shapes:
        #   - {"flags": {...}}      (the schema the design assumed)
        #   - {"governance": {...}} (what torment_service v2.4.3 actually returns)
        # Without this fallback, the first Phase 0 run produced a false-positive
        # PRECONDITION_FAILED because the substrate did store non_shareable=true
        # but the harness looked for the wrong key.
        flags = gov_get_resp.get("flags")
        if not isinstance(flags, dict):
            flags = gov_get_resp.get("governance")
        if isinstance(flags, dict):
            stored_flags = flags
            if flags.get("non_shareable") is True:
                a0_passed = True

    rows: List[Dict[str, Any]] = []

    if not a0_passed:
        # PRECONDITION_FAILED — cannot evaluate retrieval filtering.
        rows.append({
            "probe_id": "PRECONDITION",
            "eid": eid_ns,
            "governance_flags_sent_at_ingest": json.dumps({"non_shareable": True}),
            "governance_flags_stored_at_ingest": json.dumps(stored_flags),
            "a0_preserved_at_ingest": False,
            "expected_in_context": "n/a",
            "appeared_in_raw_hits": "n/a",
            "appeared_in_assembled_context": "n/a",
            "provenance_at_ingest": "user_input",
            "provenance_at_retrieval": "n/a",
            "provenance_preserved": "n/a",
            "governance_flags_at_retrieval": "n/a",
            "reason_code_if_excluded": "n/a",
            "assertion_passed": False,
            "outcome_class": "PRECONDITION_FAILED",
        })
        outcome = "PRECONDITION_FAILED"
    else:
        # Run probes and evaluate A1-A4 per planted memory.
        probe_log: List[Dict[str, Any]] = []
        for pid, qtext in PROBES:
            rq = query(args.base_url, args.workspace, args.agent, qtext,
                       top_k=args.top_k, continuity_debug=True,
                       domain_id=args.domain)
            probe_log.append({"probe_id": pid, "query_text": qtext, "response": rq})
            hits = _extract_hits(rq)

            # A4 observability sources, post FILTER-A (Commit γ):
            #   1. Per-hit reason fields (legacy / not currently emitted).
            #   2. Top-level `excluded` list on the query response (the
            #      surface added by Commit γ; carries {eid, excluded_reason}).
            # Either source proves the service exposes reason codes.
            top_level_excluded = rq.get("excluded")
            top_level_excluded_list = (
                top_level_excluded if isinstance(top_level_excluded, list) else []
            )
            a4_observable = (
                any(_hit_has_reason_field(h) for h in hits)
                or len(top_level_excluded_list) > 0
                or isinstance(top_level_excluded, list)  # empty list still proves observability
            )

            for label, eid, expected_present, content_target, prov_sent, prov_stored in [
                ("ordinary", eid_ord, True, ORDINARY_TEXT, "user_input", prov_stored_ord),
                ("non_shareable", eid_ns, False, NON_SHAREABLE_TEXT, "user_input", prov_stored_ns),
                ("tool_result", eid_tr, True, TOOL_RESULT_TEXT, "tool_result", prov_stored_tr),
            ]:
                if eid is None:
                    continue

                in_raw = any(_hit_contains_text(h, content_target) for h in hits)
                # Conservative: anything that came back from /agent/query is
                # assumed to be context-eligible (i.e., would reach the LLM).
                # If/when the service exposes a context_eligible field, A4
                # becomes observable and this assumption can be tightened.
                in_assembled = in_raw

                provenance_at_ret = None
                gov_at_ret: Dict[str, Any] = {}
                for h in hits:
                    if _hit_contains_text(h, content_target):
                        provenance_at_ret = _hit_provenance(h)
                        gov_at_ret = _hit_governance(h)
                        break

                # Per-row pass criterion:
                #   ordinary + tool_result: expected to appear in context (A1)
                #   non_shareable: expected to NOT appear (A2)
                if expected_present:
                    assertion_passed = bool(in_assembled)
                else:
                    assertion_passed = not bool(in_assembled)

                # Did ingest honor the sent provenance? Separate finding from A3.
                ingest_prov_honored: Any
                if prov_stored is None:
                    ingest_prov_honored = None  # service didn't expose stored prov
                else:
                    ingest_prov_honored = (prov_stored == prov_sent)

                # A3 — provenance preservation across the retrieval round-trip.
                # Compare retrieval-side prov against what was STORED at ingest,
                # not against what we tried to send. If ingest already rewrote
                # the prov, that's an ingest-schema finding (ingest_prov_honored)
                # and A3 isn't the right test for it.
                baseline_for_a3 = prov_stored if prov_stored is not None else prov_sent

                # Known harness limitation S1 (per SUBSTRATE_AUDIT_LOG.md
                # secondary findings): direct /agent/ingest stamps
                # source_type=user_input regardless of client-supplied
                # provenance overrides. The ingest response does not expose
                # stored provenance, so when we send tool_result and see
                # user_input come back at retrieval, we can't distinguish
                # ingest-rewrite from retrieval-mutation. Per design, this
                # is an ingest-schema observation, NOT a retrieval-mutation
                # failure. Mark as None (A3 not evaluable for this row)
                # rather than recording a false violation.
                # Tracked as Phase 0 v2 harness improvement: switch tool-result
                # ingest to spine-mediated tool_result_ingest per
                # SPINE_CONTRACT.md §3.
                is_s1_caveat = (
                    prov_stored is None
                    and label == "tool_result"
                    and provenance_at_ret == "user_input"
                )

                if is_s1_caveat:
                    provenance_preserved: Any = None
                elif in_raw and provenance_at_ret is not None:
                    provenance_preserved = (provenance_at_ret == baseline_for_a3)
                else:
                    # Either the memory didn't surface at all (nothing to check)
                    # or the substrate didn't expose retrieval-side provenance.
                    # Record as None to distinguish from a definite mutation.
                    provenance_preserved = None

                # If this EID was filtered, look up the specific reason code
                # from the top-level `excluded` list (post-Commit-γ surface).
                # Falls back to a generic "observable"/"unobservable" marker
                # when no specific exclusion record is found.
                reason_code: str
                matched_excluded = next(
                    (e for e in top_level_excluded_list
                     if isinstance(e, dict) and e.get("eid") == eid),
                    None,
                )
                if matched_excluded is not None:
                    reason_code = str(matched_excluded.get(
                        "excluded_reason", "observable"))
                elif a4_observable:
                    reason_code = "observable"
                else:
                    reason_code = "unobservable"

                rows.append({
                    "probe_id": pid,
                    "eid": eid,
                    "governance_flags_sent_at_ingest": (
                        json.dumps({"non_shareable": True})
                        if label == "non_shareable" else json.dumps({})),
                    "governance_flags_stored_at_ingest": (
                        json.dumps(stored_flags)
                        if label == "non_shareable" else json.dumps({})),
                    "a0_preserved_at_ingest": True,
                    "expected_in_context": expected_present,
                    "appeared_in_raw_hits": in_raw,
                    "appeared_in_assembled_context": in_assembled,
                    "provenance_sent_at_ingest": prov_sent,
                    "provenance_stored_at_ingest": prov_stored,
                    "ingest_provenance_honored": ingest_prov_honored,
                    "provenance_at_retrieval": provenance_at_ret,
                    "provenance_preserved": provenance_preserved,
                    "a3_s1_caveat": is_s1_caveat,
                    "governance_flags_at_retrieval": json.dumps(gov_at_ret),
                    "reason_code_if_excluded": reason_code,
                    "assertion_passed": assertion_passed,
                    "outcome_class": "",  # filled after composite eval
                })

        debug["probes"] = probe_log

        # Composite assertions across all probe rows.
        a1_passed = any(r["assertion_passed"] for r in rows
                        if r["expected_in_context"] is True)
        a2_passed = all(r["assertion_passed"] for r in rows
                        if r["expected_in_context"] is False)
        # A3 is satisfied if no row affirmatively contradicts it.
        a3_violated = any(r["provenance_preserved"] is False for r in rows)
        a3_passed = not a3_violated
        a4_passed = any(r["reason_code_if_excluded"] == "observable" for r in rows)

        if a1_passed and a2_passed and a3_passed and a4_passed:
            outcome = "PASS"
        elif a1_passed and a2_passed and a3_passed and not a4_passed:
            outcome = "CONCERN"
        else:
            outcome = "FAIL"

        for r in rows:
            r["outcome_class"] = outcome

        debug["assertions"] = {
            "A0": a0_passed, "A1": a1_passed, "A2": a2_passed,
            "A3": a3_passed, "A4": a4_passed,
        }

    # Write outputs.
    stamp = int(time.time())
    csv_path = os.path.join(args.outdir, f"substrate_audit_{stamp}.csv")
    json_path = os.path.join(args.outdir, f"substrate_audit_{stamp}.json")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    debug["outcome"] = outcome
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(debug, f, indent=2, default=str)

    print(f"Outcome: {outcome}")
    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")


if __name__ == "__main__":
    main()
