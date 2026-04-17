#!/usr/bin/env python3
"""
writeback_dryrun_report.py — Dry-run writeback report generator (D4 deliverable)

Runs a set of representative queries through the cognition pipeline with
TORMENT_ARCHIVIST_WRITEBACK=1 and captures proposal counts, guard decisions,
and sample writeback content.

Prerequisites:
    - TORMENT service running on localhost:8787
    - TORMENT_ARCHIVIST_WRITEBACK=1 in the service environment
    - A workspace with character-enabled agents and some ingested memories

Usage:
    python scripts/writeback_dryrun_report.py \\
        --workspace <workspace_id> --agent <agent_id> \\
        [--port 8787] [--queries "query1" "query2" ...]

The script sends each query to /cognition/run, inspects the writeback
in the response, and produces a summary report.

Exit codes:
    0 — report generated (does not imply pass/fail; the operator inspects).
    1 — error communicating with the service.

Reference:
    docs/ARCHIVIST_WRITEBACK_GATE_FRAMING_v2.4.x.md §6.2, §7 D4
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib import request, error
from typing import Any, Dict, List


DEFAULT_QUERIES = [
    "Tell me about yourself.",
    "What do you remember about our last conversation?",
    "How are you feeling today?",
    "What is your purpose?",
    "Describe your identity and values.",
]


def post_json(url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """POST JSON to url and return parsed response."""
    data = json.dumps(body).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        print(f"  HTTP {exc.code}: {body_text[:500]}", file=sys.stderr)
        raise


def run_cognition_query(
    base_url: str,
    workspace_id: str,
    agent_id: str,
    query: str,
) -> Dict[str, Any]:
    """Send a single cognition query and return the full response."""
    url = f"{base_url}/cognition/run"
    body = {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "user_input": query,
        "mode": "auto",
        "priority": "normal",
    }
    return post_json(url, body)


def format_report(
    workspace_id: str,
    agent_id: str,
    results: List[Dict[str, Any]],
) -> str:
    """Format the dry-run results into a human-readable report."""
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append("ARCHIVIST WRITEBACK DRY-RUN REPORT")
    lines.append(f"Workspace: {workspace_id}   Agent: {agent_id}")
    lines.append(f"Queries run: {len(results)}")
    lines.append("=" * 70)
    lines.append("")

    total_proposals = 0
    total_approved = 0
    total_rejected = 0
    total_guard_blocked = 0

    for i, entry in enumerate(results, 1):
        query = entry["query"]
        response = entry.get("response", {})
        wb = response.get("writeback", [])
        pipeline_ok = response.get("ok", False)

        lines.append(f"--- Query {i}: {query!r}")
        lines.append(f"    Pipeline OK: {pipeline_ok}")

        # Diagnostic: role summaries (shows proposal generation per role)
        role_summaries = response.get("role_summaries", [])
        if role_summaries:
            for rs in role_summaries:
                lines.append(
                    f"    Role: {rs.get('role','?'):12s}  "
                    f"confidence={rs.get('confidence',0):.2f}  "
                    f"proposals={rs.get('proposals_count',0)}  "
                    f"summary={rs.get('summary','')[:100]}")
        routing = response.get("routing", {})
        if routing:
            lines.append(
                f"    Routing: aperture={routing.get('effective_aperture','?')}  "
                f"roles={routing.get('roles_activated',[])}  "
                f"drift_check={routing.get('drift_check_required',False)}")

        lines.append(f"    Writeback results: {len(wb)} entries")

        for j, wb_entry in enumerate(wb):
            status = wb_entry.get("status", "unknown")
            proposal_id = wb_entry.get("proposal_id", "?")
            reason = wb_entry.get("rejection_reason", None)
            content = wb_entry.get("content", "")
            summary = wb_entry.get("summary", "")
            domain = wb_entry.get("domain", "")

            total_proposals += 1
            if status == "accepted":
                total_approved += 1
                tag = "ACCEPTED"
            elif status == "guard_rejected":
                total_guard_blocked += 1
                tag = f"GUARD REJECTED ({reason})"
            else:
                total_rejected += 1
                tag = f"REJECTED ({reason or status})"

            lines.append(f"      [{j+1}] {tag}")
            lines.append(f"          proposal_id: {proposal_id}")
            lines.append(f"          domain: {domain}")
            lines.append(f"          summary: {summary[:120]}")
            if content:
                lines.append(f"          content preview: {content[:200]}")

        if not wb:
            lines.append("    (no writeback proposals produced)")
        lines.append("")

    lines.append("=" * 70)
    lines.append("SUMMARY")
    lines.append(f"  Total proposals:      {total_proposals}")
    lines.append(f"  Accepted (ingested):  {total_approved}")
    lines.append(f"  Rejected (archivist): {total_rejected}")
    lines.append(f"  Guard-blocked:        {total_guard_blocked}")
    lines.append("")
    lines.append("Operator action: inspect accepted proposals above for")
    lines.append("content quality, non-degeneracy, and identity safety.")
    lines.append("=" * 70)

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run writeback report (D4 deliverable)")
    parser.add_argument("--workspace", required=True, help="Workspace ID")
    parser.add_argument("--agent", required=True, help="Agent ID")
    parser.add_argument("--port", type=int, default=8787, help="Service port")
    parser.add_argument("--host", default="127.0.0.1", help="Service host")
    parser.add_argument(
        "--queries", nargs="+", default=None,
        help="Custom queries (default: built-in representative set)")
    parser.add_argument(
        "--output", type=str, default=None,
        help="Write report to file (default: stdout)")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    queries = args.queries or DEFAULT_QUERIES

    print(f"Dry-run writeback report")
    print(f"  service: {base_url}")
    print(f"  workspace: {args.workspace}  agent: {args.agent}")
    print(f"  queries: {len(queries)}")
    print()

    # Verify service is up
    try:
        with request.urlopen(f"{base_url}/health", timeout=5) as resp:
            health = json.loads(resp.read().decode("utf-8"))
            print(f"  service health: {health.get('status', 'unknown')}")
    except Exception as exc:
        print(f"error: cannot reach service at {base_url}: {exc}", file=sys.stderr)
        print("  Is the TORMENT service running with TORMENT_ARCHIVIST_WRITEBACK=1?",
              file=sys.stderr)
        return 1

    # Run queries
    results: List[Dict[str, Any]] = []
    for i, query in enumerate(queries, 1):
        print(f"  [{i}/{len(queries)}] {query[:60]}...", end=" ", flush=True)
        try:
            response = run_cognition_query(
                base_url, args.workspace, args.agent, query)
            wb_count = len(response.get("writeback", []))
            print(f"OK ({wb_count} proposals)")
            results.append({"query": query, "response": response})
        except Exception as exc:
            print(f"ERROR: {exc}")
            results.append({"query": query, "error": str(exc)})

    # Generate report
    report = format_report(args.workspace, args.agent, results)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nReport written to {args.output}")
    else:
        print()
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
