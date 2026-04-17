# Session Handoff Notes — Phase 2.5 Complete

> **SUPERSEDED (2026-04-14).** This file is a Phase 2.5 snapshot from the pre-v2.4.3 era. The "immediate" items (test suite run, archive docs, clean local data, git commit) are long closed; Phase 2.6/2.7 framing has been absorbed into later work. The canonical handoff and "what's next" view now lives in `docs/TORMENT_ROADMAP_NOTES.md`. Retained here only for historical traceability; do not treat any item below as live state.

## What was done this session

Phase 2.5 stabilization and observability:

1. **Incident log** (`torment_service/incident_log.py`) — ring buffer recording every Spine decision. Wired into all exit paths of `submit_task()`.
2. **Status surface** — `GET /spine/status` (HTTP) and `torment://admin/status` (MCP resource). Shows active agents, recent decisions, blocks, escalations.
3. **MCP Expansion Guide** (`docs/MCP_EXPANSION_GUIDE.md`) — full walkthrough for adding new tools, with worked example, decision matrix, checklist.
4. **Bug fixes** — 4 bugs from first real-host smoke test, all fixed and verified.
5. **Live MCP verification** — full cycle through Claude Desktop including identity-sensitive auto-escalation (fast → full cognition pipeline).

## What needs doing next

### Immediate (before more features)

- **Run test suite** — the incident log integration in spine.py needs test verification. The 70 MCP+Spine tests passed before the incident log was added; they likely still pass but should be confirmed. Bash was unavailable due to disk space when we tried.
- **Archive old docs** — move `MCP_INTEGRATION_AUDIT.md`, `ROADMAP_post_hivemind_milestone.md`, `HIVEMIND_IMPLEMENTATION_PLAN.md`, `MILESTONE_hivemind_v1.md` to `docs/archive/`.
- **Clean local data** — delete `data/`, `data4/`, `__pycache__/`, `outputs/`, `.pytest_cache/`, `torment_stress_harness/outputs/` from the working copy. All are in `.gitignore`.
- **Git commit** — stage new files: `incident_log.py`, `MCP_EXPANSION_GUIDE.md`. Stage modified: `spine.py`, `mcp_server.py`, `app.py`, `fabric.py`. Don't commit `data/` or `__pycache__/`.

### Phase 2.6 — observability (ChatGPT recommended)

- Add incident log tests (test_incident_log.py) — record, query, summary, failure detection
- Test `/spine/status` HTTP endpoint
- Test `torment://admin/status` MCP resource from Claude Desktop
- Consider adding JSONL file persistence for incident log (currently in-memory only; the `file_path` parameter is supported but not configured by default)

### Phase 2.7 — real host hardening (ChatGPT recommended)

- One full Claude Desktop smoke pass with weird inputs
- One pass with missing/incorrect context
- One pass with Tier 2 intentionally blocked
- Verify the status surface actually answers "what just happened?" in practice

### Phase 3 — optional MCP expansion (not yet)

- Guarded Tier 2 support (cognition_run, compression_run, collective_reingest)
- Maybe one prompt resource
- Maybe Streamable HTTP transport later
- Do NOT rush this

## Architecture notes for future Claude sessions

- **MCP is a projection of Spine policy, not a second control plane.** This is the core principle. Don't break it.
- **The completeness rule:** If it mutates state, it needs a Spine operation, decision codes, tests, and an exposure tier.
- **Incident log is in-memory.** It resets on server restart. The `IncidentLog` class supports `file_path` for JSONL persistence but it's not wired up by default. Consider adding env var `TORMENT_MCP_INCIDENT_LOG` to enable.
- **Exposure tiers are code-level policy.** `get_exposed_operations()` generates the MCP surface from the registry. Docs and code can never drift apart.
- **stdout is sacred in MCP.** All logging, all print(), all diagnostics → stderr. This was Bug 1 and it will bite again if anyone adds a print().
- **The full cognition pipeline works.** Identity-sensitive queries auto-escalate from fast to full with the Interpreter/Skeptic/Archivist pipeline. Verified live.

## Files changed this session

New:
- `torment_service/incident_log.py`
- `docs/MCP_EXPANSION_GUIDE.md`
- `docs/SESSION_HANDOFF_NOTES.md`

Modified:
- `torment_service/spine.py` (incident log integration at every exit path)
- `torment_service/mcp_server.py` (admin status resource, stderr logging fix)
- `torment_service/app.py` (/spine/status endpoint)
- `torment_service/fabric.py` (print→stderr fix)
- `docs/MCP_README.md` (Windows setup section, updated defaults)
- `docs/MCP_SMOKE_TEST.md` (created earlier this session chain)
- `docs/SPINE_CONTRACT.md` (created earlier this session chain)
- `tests/test_mcp_server.py` (created earlier, 21 tests)
- `tests/test_spine.py` (expanded, 49 tests)
