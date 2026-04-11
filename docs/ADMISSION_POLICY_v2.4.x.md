# TORMENT 2.4.x — Admission Policy (Step 6, Commit A)

## Status

**ACTIVE as of commit A of step 6.** This document is the authoritative
source for the `WRITE_MIGRATION` admission rule set. Any change to the
rule set here requires a bump of `ADMISSION_POLICY_VERSION` in
`torment_service/migration/constants.py` and a new row in the version
history table at the end of this doc.

The CI drift check in `tests/test_admission_policy_drift.py` enforces
**enumeration equality** between the rule set declared here and the
`ADMISSION_REASONS` / `GATE1_CLASSES` / `RERUN_DECISIONS` frozensets in
`torment_service/migration/constants.py`. Adding a reason in one place
without updating the other will fail CI.

## Scope

This doctrine covers the two-gate decision procedure the
`WRITE_MIGRATION` machinery applies to every legacy row in the corpus:

1. **Gate 1 — epistemic recovery.** What can we honestly reconstruct
   about this row's original provenance?
2. **Gate 2 — ancestry admission.** Given that reconstruction, should
   this row be authorized as a future-safe ancestor?

See `docs/WRITE_MIGRATION_FRAMING_v2.4.x.md` for the original framing
and the six ratified decisions that drive this doctrine.
See `docs/WRITE_MIGRATION_IMPLEMENTATION_PLAN_v2.4.x.md` for the
commit A / commit B split and the file-level change list.

## Current policy version

`ADMISSION_POLICY_VERSION = "v2.4.x-step6-a"`

Ordering rule (cross-line): any `v2.5.x-*` is newer than any
`v2.4.x-*`. Within a single minor version, the trailing suffix
(`-a`, `-b`, ...) orders lexicographically. The re-run policy
(§ *Re-run Policy*) uses this ordering to decide whether a stored
decision is stale.

## Storage sentinel

`SOURCE_GATE1_UNRECOVERABLE = "gate1_unrecoverable"`

This is a **storage sentinel**, not an admissible origin class. It is
the literal string written to the `source_type` slot on any row that
gate 1 could not recover. A reader grepping a stored payload for the
raw string `gate1_unrecoverable` should land here, understand that it
is never produced by live ingest paths, and recognize that any row
carrying it has `admission_refused=True` by construction-time
invariant. Live ingest paths MUST NEVER emit this value. Only the
`WRITE_MIGRATION` writer produces it. See
`torment_service/migration/constants.py` for the defining declaration
and the full invariant list.

---

## Gate 1 — Epistemic Recovery

Gate 1 is **purely deterministic**. The same row always produces the
same gate-1 result. Re-runs never flip a recovery outcome.

Every row is classified into exactly one of seven classes. The class
number is stable and appears in cursor files and dry-run reports.

### Class 1 — `GATE1_CLASS_ALREADY_CANONICAL`

A well-formed `ProvenanceV1` dict that already passes schema validation.
**Outcome:** `SKIP`. The row is not migrated. The migration writer never
touches it.

### Class 2 — `GATE1_CLASS_LEGACY_BARE_STRING`

A bare Python `str` in the provenance slot. Historically the corpus
contained rows whose provenance field was just `"memory"`, `"collective"`,
`"tool_result"`, etc. — pre-ProvenanceV1 artifacts from before the
schema was introduced.

**Outcome:** `RECOVER`. `source_type` is set to the canonical form of
the bare string if and only if the bare string matches a known member
of `VALID_SOURCE_TYPES` after case-folding (except for the sentinel,
which is never a recovery target). The raw value is preserved in
`notes` as `legacy_bare_string=<raw>`.

Bare strings that do not match any member of `VALID_SOURCE_TYPES` fall
through to class 4.

### Class 3 — `GATE1_CLASS_DICT_TRUNCATED`

A `dict` with a valid `source_type` but missing or empty `parent_eids`.
**Outcome:** `RECOVER`. The row is canonicalized with `parent_eids=[]`.
The ancestry chain terminates cleanly at this node; the recursion guard
walks no further.

### Class 4 — `GATE1_CLASS_DICT_INVALID_TYPE`

A `dict` present but carrying a `source_type` that is not a member of
`VALID_SOURCE_TYPES` and not mappable to one via the class 6 deprecated
vocabulary table.

**Outcome:** `FAIL`. The row is stored under the sentinel source_type
with `admission_reason=ADMISSION_REASON_GATE1_UNRECOVERABLE`.

### Class 5 — `GATE1_CLASS_NULL_OR_EMPTY`

The provenance slot is `None`, an empty string, an empty dict, or a
non-string/non-dict primitive (int, list, etc.).
**Outcome:** `FAIL`. Same refusal shape as class 4.

### Class 6 — `GATE1_CLASS_DEPRECATED_VOCABULARY`

A `dict` with a `source_type` from a deprecated vocabulary. This class
only fires if there is an **explicit deterministic mapping** from the
deprecated value to a current one. Mapping table:

| Deprecated | Current | Notes |
|---|---|---|
| *(empty in commit A)* | | No deprecated vocabulary has been observed yet. |

Commit A ships this table empty. Entries are added only after a dry-run
against a real corpus surfaces candidate deprecated values. Each entry
requires a new policy version bump.

**Outcome when mapping exists:** `RECOVER`. `source_type` is set to the
mapped current value; original value preserved in `notes`.
**Outcome when no mapping exists:** falls through to class 4 (`FAIL`).

### Class 7 — `GATE1_CLASS_ZERO_EVENT_ARTIFACT`

Rows with zero event backing — debug artifacts, test seeds, rows
produced during interactive debugging sessions that were never intended
to enter the admissible ancestry corridor.

**Outcome:** `FAIL`. Same refusal shape as classes 4 and 5, but with a
distinct `admission_reason` so dry-run reports can distinguish "never
had real provenance" from "has provenance but it's malformed".

**Commit A posture:** The class-7 predicate ships with an **empty
enumeration** (`ZERO_EVENT_ARTIFACT_PATTERNS = ()`). This is a
deliberate conservative default, not an omission. Decision 4 ratified
that class 7 must be enumerated and auditable rather than fuzzy, so
the honest starting posture before a dry-run has been run against a
real corpus is an empty list. Each entry added to this tuple must be
justified against an observed row in a dry-run report and requires a
new policy version bump.

---

## Gate 2 — Ancestry Admission

Gate 2 is **policy-driven**. Re-runs may legitimately flip a gate-2
result when the policy version changes, subject to the re-run policy
below.

### Admission rules

Applied in order; first match wins.

1. **`ADMISSION_REASON_GATE1_UNRECOVERABLE`** — Any row whose gate-1
   outcome is `FAIL`. These rows are stored under the sentinel
   source_type and carry `admission_refused=True`. No further gate-2
   evaluation is applied; the refusal reason equals the gate-1 failure
   mode.

2. **`ADMISSION_REASON_ZERO_EVENT_ARTIFACT`** — Gate-1 class 7 rows
   specifically. These are a subset of gate-1 FAIL but recorded under a
   distinct reason so dry-run reports can distinguish them.

3. **`ADMISSION_REASON_DEPRECATED_VOCABULARY`** — Gate-1 class 6 rows
   where no deterministic mapping exists. Recorded under this reason
   rather than the generic gate-1 failure so dry-run reports can surface
   vocabulary gaps for doctrine review.

4. **`ADMISSION_REASON_BARE_STRING_REJECTED_CLASS`** — A gate-1
   `RECOVER` outcome where the recovered `source_type` is in the
   rejected set (`collective_echo`, `derived`). The row's original
   bare-string form genuinely represented a rejected origin class; the
   admission gate refuses even though recovery succeeded.

5. **`ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET`** — A gate-1 class 3
   row whose canonical `source_type` is in the rejected set. Same
   refusal as rule 4 but applied to dict-shaped rows rather than
   bare-string rows.

6. **`ADMISSION_REASON_ARCHIVIST_ROLE`** — A recovered row with
   `source_type = role_output` and `source_role` containing
   `"archivist"`. The archivist-role refusal is the decisive blocker in
   `cognition/recursion_guard.py::recursion_guard_check` at any depth;
   the migration must not create a backdoor around that rejection.

If none of the above rules match, the row is **admitted** with
`admission_refused=False`, `admission_reason=""`, and
`admission_policy_version=ADMISSION_POLICY_VERSION`. The recursion
guard will walk through it normally under its existing safe-set rules.

### Rationale for asymmetry

Strong recovery does not imply strong admission. A row recovered as
"originally a collective echo" has strong recovery (rule 4) but must
fail admission — the guard rejects `collective_echo` anywhere in the
walk window, and the migration must not create a backdoor around that
rejection.

If the two gates were collapsed into one decision, best-effort
reconstruction would quietly upgrade itself to admissible truth. That
is the failure mode step 5's guard exists to prevent, and this
doctrine preserves the same invariant across the step-6 migration
surface.

---

## Re-run Policy

Re-runs of the migration apply the current policy to every row already
in the corpus. The decision table below governs what happens when the
stored policy version on a row differs from the current one.

| Stored decision | New decision | Action | Notes |
|---|---|---|---|
| *(none — no stored version)* | admit | `FIRST_EVALUATION` | Stored on first run |
| *(none)* | refuse | `FIRST_EVALUATION` | Stored on first run |
| admit | admit | `BUMP_ONLY` | Only policy version is updated |
| refuse | refuse | `BUMP_ONLY` | Only policy version is updated |
| admit | refuse | `APPLY` | Tightening — applied automatically |
| refuse | admit | `BLOCK_AND_REVIEW` | Loosening — held for human review |

**Monotonic-in-tightness invariant:** On a re-run without human review,
admission decisions can only move in the tightening direction.
Loosening (`refuse → admit`) is never applied automatically; such rows
are enqueued in `.torment_migration/review_queue.jsonl` with both the
stored and proposed decisions, and the loosening is applied only after
a human explicitly ratifies the new policy version for each affected
row.

This preserves the "admission without honest recovery is laundering"
invariant across re-runs. Loosening requires a human explicitly saying
"yes, I reviewed this and it's safe."

Recovery (gate 1) is purely deterministic and does **not** have the
monotonicity constraint — same input always produces the same recovery.
Only admission (gate 2) has the tightening-only property.

---

## Relationship to the Recursion Guard

`cognition/recursion_guard.py::recursion_guard_check` enforces the
doctrine at the writeback boundary. As of commit A:

- A row with `admission_refused=True` is rejected at any walk depth
  with `REASON_MIGRATION_REFUSED`, regardless of its `source_type` or
  `source_role`. This check fires before the existing source_type
  and source_role evaluation.
- The sentinel `SOURCE_GATE1_UNRECOVERABLE` is added to
  `_REJECTED_SOURCE_TYPES_IN_WALK` as a backstop. Any row carrying the
  sentinel is caught even if `admission_refused` is somehow missing
  from a pathologically old payload shape — belt-and-braces for the
  fail-closed posture.

Rows admitted by the migration (gate-2 `ADMIT`) enter the existing
safe-set check in the recursion guard with no special handling. A
migrated row is indistinguishable from a live-ingest row once it
passes both gates — which is exactly what the two-gate model is
designed to authorize.

---

## Version history

| Version | Date | Change |
|---|---|---|
| `v2.4.x-step6-a` | 2026-04-11 | Initial activation. Class 6 mapping table empty. Class 7 pattern list empty. |

Each row in this table corresponds to exactly one `ADMISSION_POLICY_VERSION`
value. Adding a row requires:

1. Bumping `ADMISSION_POLICY_VERSION` in `torment_service/migration/constants.py`.
2. Updating any affected rule or table in this doc.
3. Ensuring `tests/test_admission_policy_drift.py` passes against the
   updated rule set.
4. Recording the change under a new row here, with the date and a
   one-line description of what rule changed.
