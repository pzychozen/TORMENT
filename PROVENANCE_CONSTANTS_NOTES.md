# Provenance Constants Review Notes (April 10, 2026)

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
