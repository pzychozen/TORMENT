# TORMENT Working Notes

> **PARTIALLY SUPERSEDED (2026-04-14).** This file is anchored to the v2.4.3 milestone (2026-04-07). The core doctrine block below is still canonical and load-bearing. The v2.4.3 "Completed" and "Next phase: tool-result lifecycle policy" sections are historical — tool-result ingest, provenance v1, and the step-5/step-6 migration work have all since landed. For the current "what's next" view, see `docs/TORMENT_ROADMAP_NOTES.md`.

**Core doctrine (do not lose this):**

> Tool-result ingest is a memory feature, not a capability feature.

> TORMENT may remember what tools returned before it is ever allowed to decide what tools to run.

> Tool-result lifecycle policy must remain entirely inside the epistemic memory system. It must not imply freshness refresh, background re-query, scheduled updates, or any autonomous external action.

---

## v2.4.3 milestone — Tool-Result Memory Lane (completed 2026-04-07)

Completed:
- Tool-result ingest: Spine-governed write operation, `POST /tool/ingest`, provenance-tagged
- Provenance normalization: collective writes use ProvenanceV1, backward-compat at 3 sites
- Debug endpoint separator fix: `"::"` → `"/"`
- Retrieval semantics:
  - 0.85x tool-result discount (env-configurable)
  - Continuity bonuses excluded for tool-result hits
  - Provenance badge (`provenance_type`, `provenance_tool_name`) on all returned hits
- Tests: 41 passing (ingest + retrieval semantics)
- Docs: README, MCP_CAPABILITY_BOUNDARY, SPINE_CONTRACT, TOOL_RESULT_RETRIEVAL_SEMANTICS

## Next phase: tool-result lifecycle policy

How tool-result memories should behave over time: retention, decay, compression routing, dedup.

Constraints:
- Memory lifecycle only — no execution, no automation
- No freshness refresh, background re-query, scheduled updates
- No autonomous external action of any kind

## Hard boundary (do not cross)

No autonomous tool calls. No scheduling. No polling. No automation. No chained workflows. No internal role-triggered tool usage. Ever, in this phase.
