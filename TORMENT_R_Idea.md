# TORMENT Roadmap and Research Notes

## Current project state

TORMENT is now a governed memory-and-identity system for persistent AI characters and agents.

It is not an automation engine or autonomous tool runner.
It is strongest as:
- a memory core
- an identity core
- a provenance-aware governed system
- a safe MCP-compatible memory interface

---

## Completed (April 9, 2026)

- Doc audit: all 62 docs deep-verified against codebase, stale values fixed
- Test audit: 10 test files deep-verified, zero stale values
- Bug fix: Spine HTTPException propagation (409 no longer swallowed as 500)
- Bug fix: propose_share KeyError on missing domain (guard + clear error message)
- Character Forge alignment: all generated payloads, endpoints, env vars verified and fixed
- SRG env var wiring: TORMENT_SRG_BANDS, CLASS_A_RATIO, CRYSTAL now configurable
- Test score: 1739 passed, 5 failed (environment-only), 2 skipped
- CodeQL cleanup phases A through E merged
- fabric.py character_name fix: reads character_name from seed dict, falls back to seed_id
- 5 cognition env vars wired into thinking_controller.py (default ON, opt-out via env)
- torment_feedback simplified: memory_ids + bool flags replaces 4 JSON-string arrays
- provencev1 reviewed: healthy, well-tested, no functional issues (cosmetic doc refs only)
- Character creator updated: character_name in payloads, cognition env vars no longer commented out
- Test score: 1721 passed, 2 skipped (environment-only)

---

## Outstanding small fixes

Status update (April 10, 2026):

1. **docs/archive/AGENT_SPINE_PLAN.md references** — 30+ files reference docs/archive/AGENT_SPINE_PLAN.md which is now in docs/archive/. Comments-only, not functional. Low priority.

2. **Unused provenance constants** — SOURCE_MEMORY, SOURCE_DERIVED.derive(), and 3 unused write_path values (reflection_writeback, migration, system_import) are defined but never used in production. Kept for future extensibility.

### Next pick (recommended immediate task)

Do a focused provenance-intent pass on the currently unconnected constants:
- confirm intended semantic role for each constant/value
- document where each should be produced and consumed
- wire the missing paths where intended behavior already exists
- keep constants that represent valid future/interop states (do not delete blindly)

Goal: reduce ambiguity, preserve provenance intent, and connect intended states before broader security hardening.

---

## Active tracks

### 1. Security hardening / bug hunting
- Security hardening
- Bug analysis
- Tightening weak spots
- Making the system less fragile and more runnable

Tools to consider: [Snyk](https://snyk.io/), [Semgrep](https://semgrep.dev/)

### 2. MCP compatibility across hosts
Keep TORMENT MCP support solid for:
- Claude
- Hermes
- clawbot
- other popular MCP-compatible connections

Focus: compatibility, clarity, reliability, developer usability.
Not: lots of new tools, automation, execution expansion.

---

## Deferred tracks

### 3. Path 2: retrieval tuning
- Continuity bonus / recency wall mitigation
- Diversity in top-k retrieval
- Short-path to long-path re-evaluation
- Motif alignment staleness review

This is later tuning, not immediate work.

### 4. Path 1: live / personal layer
- Live agent voice/transcript hardening
- Response feel
- Natural memory use in real interaction
- Making the character experience feel alive

---

## Late roadmap: deep systems research

Look deeply at the libraries TORMENT runs on, especially:
- CPU-side behavior / libraries
- RAM / memory behavior
- Transformer-related layers and dependencies

Possible directions:
- Study what kind of wild research could support them
- Explore whether TORMENT's own math could guide or improve them
- Revisit past research ideas and see if they can inform runtime behavior
- Consider designing custom components that work better for TORMENT than generic ones

This track is for: deep systems research, experimental performance ideas, custom low-level behavior guided by TORMENT's own principles.

Not for: immediate production changes, random optimization churn, derailing the current roadmap.

---

## Order of operations

1. Finish security hardening + pick off outstanding small fixes
2. MCP compatibility/support polish
3. Path 2 deeper tuning
4. Path 1 personal/live refinement
5. Late research track

---

## One-line summary

hardening → compatibility → tuning → lived experience → research

Not: endless new architecture.
