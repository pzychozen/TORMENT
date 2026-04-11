# Provenance Constants Review Notes (April 10, 2026)

> **Status (2026-04-11): superseded as canonical; preserved as historical context.**
>
> This document is the pre-step-6 scratch pad that the provenance-intent
> pass grew out of. The authoritative artifacts are now:
>
> - `docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md` — canonical classification
>   of every declared provenance constant across both vocabularies (spine
>   layer + storage layer), with producer call sites, RSP parent status,
>   and doctrine anchors per row. Steps 1–5 of the tactical provenance
>   pass are closed on main (step 5 commit B at `9bb310c`).
> - `docs/WRITE_MIGRATION_FRAMING_v2.4.x.md` — step 6 framing doc for the
>   reserved migration trio (`SOURCE_MEMORY` + `WRITE_MIGRATION` +
>   `WRITE_SYSTEM_IMPORT`). Contains the two-gate model (epistemic
>   recovery vs ancestry admission) and six open architectural decisions
>   currently shelved pending ratification.
>
> The framing doc references this file as prior art under its
> "understand and connect, do not delete" stance, which is why it is
> retained rather than deleted. **Do not treat anything below this block
> as current canonical** — the material below is the earlier scratch
> shape that the registry and framing doc grew out of, and it is
> incomplete relative to the registry's actual rows. Read the two
> documents above for ground truth.

---

Purpose: track why currently less-used provenance constants exist, and what to do next without deleting intent-critical states.

## Context

User direction: constants that appear disconnected should be understood and connected where needed, not removed by default.

## Current constants under review

From `torment_service/provenance_v1.py`:

- `SOURCE_MEMORY = "memory"`
- `SOURCE_DERIVED = "derived"`
- `WRITE_REFLECTION_WRITEBACK = "reflection_writeback"`
- `WRITE_MIGRATION = "migration"`
- `WRITE_SYSTEM_IMPORT = "system_import"`

## Initial interpretation

- These values are part of the **allowed provenance vocabulary** (`VALID_SOURCE_TYPES` and `VALID_WRITE_PATHS`), so they currently function as schema-accepted states even if few/no active producers emit them.
- Keeping them can be correct if they represent:
  - planned write paths (reflection/import/migration),
  - historical/backfill compatibility,
  - interop with external tools or future pipelines.

## Recommended next implementation pass

1. For each constant, identify intended producer(s) and expected consumer/query surfaces.
2. Add explicit inline comments in provenance modules marking each as:
   - active,
   - reserved/future,
   - legacy-compat.
3. Add or update tests to lock intended behavior:
   - acceptance by validation enums,
   - serialization/deserialization round trip,
   - explicit producer path tests for any newly connected flow.
4. If a constant is genuinely dead after analysis, deprecate with a migration note first, then remove in a separate PR.

## Guardrails

- No silent removals of enum values in provenance schemas.
- Any enum change requires:
  - migration/compat note,
  - targeted tests,
  - changelog/roadmap update.
