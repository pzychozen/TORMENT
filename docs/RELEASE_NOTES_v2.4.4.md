# TORMENT Memory Fabric — v2.4.4 Release Notes (skeleton)

**Tag:** `v2.4.4` *(not yet cut)*
**Branch:** `v2.4.x-step6-commit-a` → rolls up into `v2.4.4` when
commit B lands and the tag is cut.
**Headline:** `WRITE_MIGRATION` activation — read-only commit A of
step 6 in the v2.4.x tactical provenance pass.

This skeleton tracks the scope of commit A of step 6 so that when
commit B lands and the v2.4.4 tag is cut, the release notes are
already half-written. It is intentionally a skeleton, not a finished
release notes file — gaps marked `TK` are filled in at tag time.

For the architectural context, see:
- [`DOCTRINE_v2.4.x.md`](DOCTRINE_v2.4.x.md) — 12 principles
- [`WRITE_MIGRATION_FRAMING_v2.4.x.md`](WRITE_MIGRATION_FRAMING_v2.4.x.md) — six ratified decisions
- [`ADMISSION_POLICY_v2.4.x.md`](ADMISSION_POLICY_v2.4.x.md) — live admission rule set
- [`WRITE_MIGRATION_IMPLEMENTATION_PLAN_v2.4.x.md`](WRITE_MIGRATION_IMPLEMENTATION_PLAN_v2.4.x.md) — commit A / commit B split

---

## Step 6 Commit A — read-only `WRITE_MIGRATION` surface

Commit A activates the `WRITE_MIGRATION` write path in **read-only
form**. Every decision-layer component of the migration is live and
tested; no actual corpus row is written. The commit A / commit B split
is intentional: it lets the decision pipeline, cursor, review queue,
dry-run reporting, and recursion-guard refusal path be reviewed and
merged in isolation from the row-rewrite path, which lands in commit B
under its own review.

### What commit A ships

**Doctrine**

- `docs/ADMISSION_POLICY_v2.4.x.md` — ratified two-gate decision
  doctrine. Gate 1 (epistemic recovery) enumerates seven row classes;
  gate 2 (ancestry admission) enumerates six refusal rules. The
  re-run policy decision table encodes the monotonic-in-tightness
  invariant. The class-6 deprecated-vocabulary mapping table and the
  class-7 zero-event-artifact pattern list both ship **empty** as
  deliberate conservative defaults. `ADMISSION_POLICY_VERSION =
  "v2.4.x-step6-a"`.
- `docs/WRITE_MIGRATION_FRAMING_v2.4.x.md` — status line updated to
  record that all six decisions are ratified and commit A has landed.
- `docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md` —
  `WRITE_MIGRATION` flipped from **Reserved** to **Active (read-only
  in commit A)**. `WRITE_SYSTEM_IMPORT` remains **Reserved** pending a
  ratified adapter spec (new wording emphasizes that the two paths
  share a source_type but have different authorization semantics and
  must not be conflated).
- `docs/RECURSION_SAFETY_POLICY_v2.4.x.md` — new rejection reason
  `migration_admission_refused` added to the stable vocabulary.

**Schema**

- `torment_service/provenance_v1.py`:
  - New storage sentinel `SOURCE_GATE1_UNRECOVERABLE = "gate1_unrecoverable"`
    with strong module-level documentation that it is **not** an
    admissible origin class. Registered in `VALID_SOURCE_TYPES`.
  - Three new admission fields on `ProvenanceV1`:
    `admission_refused`, `admission_reason`, `admission_policy_version`.
    All default-valued, stripped from `to_dict()` so pre-step-6
    payloads and fresh live-ingest payloads serialize byte-compatibly.
  - Four construction-time invariants enforced in `__post_init__`:
    refused → requires reason, any decision → requires policy version,
    reason without version → raises, `source_type =
    SOURCE_GATE1_UNRECOVERABLE` → requires `admission_refused=True`.

**Migration package** (`torment_service/migration/`)

- `constants.py` — all string-stable vocabulary: sentinel, gate-1
  classes, gate-1 outcome codes, admission reasons, re-run decisions,
  `ADMISSION_POLICY_VERSION`, cursor/review-queue filenames, and the
  deliberately empty `ZERO_EVENT_ARTIFACT_PATTERNS` tuple.
- `gate1_recovery.py` — deterministic gate 1 classifier. Hand-written
  rule cascade covering all seven classes; legacy bare strings are
  recovered against `VALID_SOURCE_TYPES` after case-folding; class 6
  deprecated-vocabulary mapping table ships empty.
- `gate2_admission.py` — policy-driven gate 2 admission decider.
  Rule order matches the doctrine doc; every result (admit or refuse)
  carries `policy_version` so the re-run policy can detect staleness.
- `rerun_policy.py` — four-branch re-run decision: `FIRST_EVALUATION`,
  `BUMP_ONLY`, `APPLY` (tightening), `BLOCK_AND_REVIEW` (loosening).
  Implements the cross-line version-ordering rule (v2.5.x > v2.4.x)
  and preserves the monotonic-in-tightness invariant.
- `cursor.py` — append-only JSONL cursor file under
  `.torment_migration/cursor.jsonl`. `processed_eids()` helper for
  crash-safe resume. Rejects unknown actions at construction.
- `review_queue.py` — append-only JSONL review queue under
  `.torment_migration/review_queue.jsonl`. Each entry contains both
  the stored decision and the current decision so a reviewer can see
  the delta without re-running gate 2.
- `dry_run.py` — four-section report generator (per-class counts,
  gate-1 FAIL listing, gate-2 refusal listing, reproducibility
  anchor). Row-source API is an iterable of `(eid, raw_provenance)`
  tuples — no corpus coupling. Honors `write_cursor` and
  `skip_processed` for resumable dry-runs.
- `cli.py` — `torment-migration` entry point with three subcommands:
  `dry-run` (the read-only surface), `status` (cursor + review queue
  summary), and `apply` (present but blocked; non-zero exit with a
  clear pointer to the plan doc).

**Recursion guard** (`cognition/recursion_guard.py`)

- New rejection reason constant `REASON_MIGRATION_REFUSED =
  "migration_admission_refused"`.
- Early-exit check in the walk loop: any node with
  `admission_refused=True` **or** `source_type ==
  SOURCE_GATE1_UNRECOVERABLE` is rejected immediately, before the
  existing source_type and source_role evaluation. This ensures a
  migration-refused row can never be chain-admitted through ancestry
  walking.
- `SOURCE_GATE1_UNRECOVERABLE` added to
  `_REJECTED_SOURCE_TYPES_IN_WALK` as defense-in-depth (the early
  exit already catches it, but this keeps the set doctrinally
  complete).
- Module docstring updated to include rule 7 — the migration refusal
  short-circuit.

**Tests**

- `tests/test_provenance_v1_admission.py` — 18 tests covering sentinel
  registration, admission field defaults, invariant enforcement, and
  backward-compatible serialization.
- `tests/test_migration_gate1_recovery.py` — 20 tests covering all
  seven classes, determinism, and sentinel-row handling.
- `tests/test_migration_gate2_admission.py` — 16 tests covering every
  admission rule with hand-constructed fixtures.
- `tests/test_migration_rerun_policy.py` — 13 tests covering the four
  re-run branches, the monotonicity invariant, and cross-line version
  ordering.
- `tests/test_migration_cursor_and_review_queue.py` — 9 tests
  covering append semantics, round-trip, resume helper, and invalid
  action rejection.
- `tests/test_migration_dry_run.py` — 9 tests covering the four-
  section report shape, cursor bookkeeping, resume-via-skip, and the
  **no-corpus-write invariant** (AST import inspection that asserts
  `dry_run.py` never imports `torment_service.app`, `mcp_server`,
  `fabric`, `memory_graph`, `embedding_store`, or `spine`).
- `tests/test_migration_cli.py` — 13 tests covering every CLI
  subcommand including the blocked `apply` path.
- `tests/test_writeback_recursion_guard.py` — 7 new migration-refusal
  tests on top of the 26 existing ones. Covers direct-parent rejection,
  deep-ancestor rejection, priority ordering with archivist blocks,
  and the "no decision on file" fast-path.
- `tests/test_admission_policy_drift.py` — 13-test CI drift check
  enforcing enumeration equality between `migration/constants.py` and
  `docs/ADMISSION_POLICY_v2.4.x.md`.

### Running totals (commit A only)

- 7 new migration-package modules, 2 schema/guard updates.
- 1 new doctrine doc, 3 updated docs, 1 updated framing status.
- 98 new tests in the migration and admission surfaces.
- 7 new recursion-guard tests.
- 13 new drift-check tests.
- Zero regressions in the 33-test recursion guard suite.

### What commit A does NOT ship

- No row-rewrite path. The `apply` CLI subcommand is present but
  exits non-zero with a message pointing to the plan doc.
- No class-6 deprecated-vocabulary mappings. Entries land only after
  a dry-run against a real corpus surfaces candidate values.
- No class-7 zero-event-artifact patterns. Same discipline — the
  empty tuple is intentional.
- No `WRITE_SYSTEM_IMPORT` activation. That path is blocked on a
  ratified adapter spec.

---

## Upgrade notes

TK *(filled in at tag time once commit B lands)*

## Operational notes

TK *(filled in at tag time)*

## Migration runbook

TK *(filled in at tag time after the first real-corpus dry-run)*
