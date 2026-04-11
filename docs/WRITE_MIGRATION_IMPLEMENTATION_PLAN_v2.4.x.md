# TORMENT 2.4.x — Step 6 Implementation Plan (Write Migration)

## Status

Plan-phase artifact. Produced after all six framing decisions in
`docs/WRITE_MIGRATION_FRAMING_v2.4.x.md` were ratified. No `.py` changes,
no schema edits, no doctrine-doc edits, and no corpus greps have been
made against this plan yet. Commit A does not begin until this plan is
explicitly ratified.

This plan translates the ratified framing into concrete commit scope. It
does not introduce new doctrinal choices — every load-bearing decision
was resolved in the framing walk. Anything that looks like a new choice
here is either (a) a plan-phase sub-question the framing deliberately
deferred, flagged as such, or (b) a mechanical consequence of a ratified
decision that wants to be written down so it doesn't get re-litigated
during coding.

---

## Ratified inputs (recap, not re-argued)

1. **Decision 1 — Refusal encoding.** Option A. Add
   `admission_refused: bool = False`, `admission_reason: str = ""`,
   `admission_policy_version: str = ""` to `ProvenanceV1`. Add
   `REASON_MIGRATION_REFUSED` to the guard's rejection reason constants.
2. **Decision 2 — Run semantics.** Monotonic-in-tightness + resumable.
   `refuse ← admit` may apply automatically; `admit ← refuse` must route
   to the human-review queue; `same / same` advances the stored
   `admission_policy_version`. Row-level crash goal is
   *effectively-once for committed row transitions under resume* — no
   silent skip, no unintended double-application.
3. **Decision 3 — First-run scope.** `WRITE_MIGRATION` only.
   `WRITE_SYSTEM_IMPORT` stays RESERVED. Follow-up activation requires a
   named concrete import source plus a written source-adapter spec
   under the same framing.
4. **Decision 4 — Gate 1 strictness.** Seven-row recovery table as
   written. No sibling voting, no era inference, no unaudited
   vocabulary remaps. Class 6 mapping table must be in-tree,
   deterministic, reviewable. Class 7 artifact-detection predicate must
   be enumerated and auditable. Gate-1 FAIL rows are migrated into the
   uniform refused shape; never left in pre-migration form.
5. **Decision 5 — Policy version scheme.** Scheme C: doctrine-tied
   label (`v2.4.x-step6-a` on first activation), bumped only when the
   admission rules themselves change. Admission rules live in one
   named section of one named doctrine doc. CI-enforced
   enumeration-equality drift check between code-level rule
   enumeration and the doctrine section is a hard requirement. Explicit
   cross-line ordering rule is required.
6. **Decision 6 — Dry-run as first deliverable.** Option A. Commit A
   ships dry-run only with no write path present. Minimum dry-run
   artifact is a floor, not a recommendation: per-class counts,
   gate-1 FAIL listing, gate-2 refusal listing, reproducibility anchor.
   Dry-run generator requires its own test coverage in commit A.

The rest of this document is downstream of these six ratified inputs.

---

## Commit structure

Step 6 ships across two commits under the same discipline used in step 5.

### Commit A — Dry-run only

Commit A is the first reviewable artifact and the first time any step-6
code runs against the real corpus. It is deliberately incapable of
writing to stored rows: the write path does not exist in commit A, so
the "no writes" property is structural, not configurational.

Commit A scope:

- `ProvenanceV1` schema additions (three new fields from Decision 1).
  Schema load/default behavior for existing rows is handled in this
  commit — see "Schema backfill semantics" below.
- New migration module tree under `torment_service/migration/`. Module
  layout detailed below.
- Gate-1 recovery predicate (seven-row table from Decision 4).
- Gate-2 admission predicate (admission rules enumerated against the
  named doctrine section from Decision 5).
- Monotonic-in-tightness decision table scaffolding (Decision 2). The
  re-run logic exists as code and is unit-tested against synthetic
  fixtures, but is **not exercised against live rows** until commit B.
- Cursor/state file format and read/write routines. Scaffolded and
  unit-tested. No live corpus walk writes through it in commit A except
  as part of the dry-run, which does not update the cursor because
  dry-run does not commit row transitions.
- Human-review queue format and read/write routines. Scaffolded and
  unit-tested. Dry-run may emit to this queue as a preview, but those
  entries are marked `preview=true` and are not authoritative.
- Dry-run report generator. Produces the floor-level report from
  Decision 6.
- Dry-run CLI entry point. Commands detailed below.
- Doctrine doc section landing the admission rule enumeration
  (Decision 5). Named section in the chosen doctrine doc.
- CI drift check comparing code-level admission rule enumeration
  against the doctrine section.
- Recursion guard changes: new `REASON_MIGRATION_REFUSED` constant and
  the early-exit check on `admission_refused`. These land in commit A
  because they're read-only consumers of schema state that commit A
  introduces; they don't depend on the write path.
- Test coverage for every code path added in commit A, including the
  dry-run generator itself (classification fidelity, not just the
  underlying predicates).
- Registry doc update: `WRITE_MIGRATION` flips from RESERVED to
  ACTIVE (step 6); `WRITE_SYSTEM_IMPORT` stays RESERVED with the
  adapter-spec requirement noted.
- Release notes skeleton for step 6 commit A.

**Commit A does NOT include:**

- Any write path for `WRITE_MIGRATION`. No function that rewrites a
  stored row. No `--apply` flag, no `--wet-run` flag, no commented-out
  write code waiting to be uncommented. The write path is introduced
  in commit B as new code, not gated existing code.
- Any activation of `WRITE_SYSTEM_IMPORT`.
- Any flip of `TORMENT_ARCHIVIST_WRITEBACK`.
- Any doctrine rule changes beyond adding the named admission rules
  section.

### Commit B — Write path activation

Commit B is a separate reviewable artifact that lands after commit A
has been reviewed and commit A's dry-run output has been inspected
against the real corpus. Commit B's review window is the ratification
pause point.

Commit B scope:

- The write path itself: a function (or small set of functions) that
  takes a row-level decision from the two-gate predicates and commits
  the row transition to storage, advancing the cursor.
- A CLI flag enabling the write path explicitly. The flag is
  off-by-default and must be passed with intent. The flag's safety
  story is secondary to the structural property that the write path
  simply did not exist in commit A.
- Monotonic-in-tightness re-run logic exercised live. The human-review
  queue starts receiving authoritative entries (not just previews)
  from this commit forward.
- Cursor/state file begins receiving authoritative updates.
- Any additional test coverage that requires the write path to exist,
  e.g., end-to-end tests that run the migration, inspect committed
  rows, re-run under a tightened policy, and assert correct behavior.
- Release notes update for step 6 commit B.

**Commit B does NOT include:**

- Any schema changes. All schema changes land in commit A.
- Any doctrine rule changes. Any changes to admission rules between
  commit A and commit B must bump the policy version and go through
  the CI drift check, which would fail the build and force explicit
  review.
- `WRITE_SYSTEM_IMPORT` activation.
- `TORMENT_ARCHIVIST_WRITEBACK` flip.

---

## Schema changes (all in commit A)

### `ProvenanceV1` field additions

Three new fields are added to the canonical schema:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `admission_refused` | `bool` | `False` | Gate-2 decision. Guard rejects walks early if set. |
| `admission_reason` | `str` | `""` | Human-readable refusal reason. Canonical strings enumerated in the admission rules section. |
| `admission_policy_version` | `str` | `""` | The policy version under which the admission decision was made. Empty string means "never evaluated by the migration" — distinct from `"v2.4.x-step6-a"` which means "evaluated under the first activation of step 6." |

### Schema backfill semantics for existing canonical rows

Existing rows that already carry a well-formed `ProvenanceV1` predate
the three new fields. The question is what those rows look like after
commit A lands but before any migration run has touched them.

The plan is:

- Schema deserialization on existing rows produces the default values
  (`False`, `""`, `""`) for the three new fields. No in-place write to
  the stored row. No migration pass is required for the schema
  addition itself to be safe — the guard treats `admission_refused=False`
  the same way it treats a row that has no `admission_refused` field
  at all, which is "permit the walk to continue."
- A well-formed canonical row (Question 1a class 1) keeps
  `admission_policy_version=""` permanently unless the migration
  explicitly visits it. Class 1 rows are skipped by the migration at
  gate 1 entry (per Decision 4), so they never acquire a policy
  version. This is intentional: policy versions are only meaningful
  for rows that actually passed through the two-gate pipeline.
- The guard's early-exit check on `admission_refused` treats missing
  / default values as "not refused" and continues normally. This is
  the strictly-tighter property: commit A cannot make the guard refuse
  a row it would previously have walked.

**Plan-phase sub-question 1 (carried from Decision 4):** gate-1 FAIL
rows are migrated into the uniform refused shape, but the choice
between (a) a sentinel `source_type` constant (`"gate_1_unrecoverable"`
or similar) and (b) nullable `source_type` with the guard treating
null as automatic refusal is still open. Recommendation for this plan:
**option (a) — sentinel source_type constant**. Rationale: `source_type`
is currently a non-null string field everywhere else in the codebase,
and introducing nullability for one edge case creates a cross-cutting
invariant change that touches every consumer of `source_type`, not just
the migration. A sentinel constant is local to the migration's schema
surface and costs one new constant definition. The sentinel is added
to `_REJECTED_SOURCE_TYPES_IN_WALK` as belt-and-braces with
`admission_refused=True`, so the guard rejects it by either route.

Calling this out as a ratification point: the plan proposes the
sentinel approach, but I am flagging it as a sub-question so you can
ratify or revise it before commit A starts.

---

## Module layout

New code lives under `torment_service/migration/`. Layout:

```
torment_service/migration/
├── __init__.py
├── gate1_recovery.py      # Gate-1 recovery predicate (Decision 4)
├── gate2_admission.py     # Gate-2 admission predicate (Decision 5)
├── rerun_policy.py        # Monotonic-in-tightness decision table (Decision 2)
├── cursor.py              # Cursor/state file read/write (Decision 2)
├── review_queue.py        # Human-review queue for admit←refuse cases
├── dry_run.py             # Dry-run report generator (Decision 6)
├── cli.py                 # CLI entry point
└── constants.py           # Sentinel constants, reasons, policy version labels
```

Each module is small and single-responsibility. Cross-module coupling
runs in one direction: `cli.py` depends on `dry_run.py` depends on the
gate modules; the gate modules do not depend on each other or on the
CLI. This layout makes unit testing straightforward because each
module's surface area is narrow.

**Plan-phase sub-question 2:** module placement under
`torment_service/migration/` rather than as a top-level `migration/`
directory. Rationale: the migration reads and writes through the same
`torment_service` seam that `fabric.py`, `spine.py`, and
`provenance_v1.py` already use, so keeping it under that tree
co-locates it with its dependencies. If you prefer a top-level
`migration/` directory for step 6 that signals "this is a one-off
tool, not part of the service," name the preference and I'll revise.

---

## Gate 1 recovery predicate (`gate1_recovery.py`)

Implements the seven-row table from Decision 4:

| Class | Shape | Outcome |
|---|---|---|
| 1 | Well-formed `ProvenanceV1` dict | `SKIP` — pre-gate exit |
| 2 | Legacy bare string in `VALID_SOURCE_TYPES` vocabulary | `RECOVER` — string → canonical source_type, raw preserved in `notes` as `legacy_bare_string=<raw>` |
| 3 | Dict with valid source_type, missing `parent_eids` | `RECOVER` — truncated chain, passes as-is |
| 4 | Dict with invalid or missing `source_type` | `FAIL` |
| 5 | `None` / null / empty string | `FAIL` |
| 6 | Dict with `source_type` from deprecated vocabulary | `RECOVER` iff deterministic mapping table hit; otherwise `FAIL` |
| 7 | Row with zero event backing (debug artifact predicate) | `FAIL` |

The predicate returns a structured result:

```python
@dataclass(frozen=True)
class Gate1Result:
    class_id: int                   # 1-7, matches the table
    outcome: Literal["SKIP", "RECOVER", "FAIL"]
    recovered_source_type: str | None    # None on SKIP and FAIL
    recovered_parent_eids: list[str]     # empty on SKIP, FAIL, and truncated chains
    recovery_notes: str                  # forensic trail for audit
    raw_original: Any                    # the original pre-recovery value, preserved verbatim
```

**Class 6 mapping table.** Lives in-tree at
`torment_service/migration/deprecated_vocabulary_map.py` (or equivalent
location the plan phase ratifies). Exported as a
`DEPRECATED_VOCABULARY_MAP: dict[str, str]` with each entry justified
by a comment pointing at the historical reason for the mapping. The
map is deliberately small — an empty map is acceptable and simply
means class 6 always falls through to FAIL. Additions require an
explicit review of the specific deprecated string being mapped.

**Class 7 artifact-detection predicate.** Per Decision 4's tightening
note, this predicate must be enumerated and auditable with the same
strictness as the recovery table. The plan proposes:

- An explicit, in-tree list of eid patterns or metadata signatures
  that are known debug artifacts — e.g., eids matching a specific
  test-seed prefix, rows explicitly tagged with a `debug_artifact=True`
  metadata marker, or rows from specific known test harness runs.
- The predicate is a pure function of in-row evidence. No "probably
  looks like a test" inference.
- Empty list is acceptable and means class 7 never fires; all rows
  fall through to class 4/5/6 classification. This is the safest
  posture if we're not confident about the test-row inventory.

**Plan-phase sub-question 3:** the initial class-7 predicate.
Recommendation: **ship commit A with an empty class-7 list**. Rationale:
we haven't run the dry-run yet, so we don't know what "debug artifact"
looks like in the real corpus. The dry-run output will tell us. An
empty list means zero rows are classified as class 7, which means
class 7 contributes nothing to the gate-1 FAIL population in commit A.
Any class-7 patterns discovered via the dry-run report become their
own small ratification moments before being added.

### Test coverage for gate 1

- Unit tests for each of the seven classes using synthetic fixtures.
- A "no inference exceeds evidence" test that asserts the predicate
  never consults neighbors, never consults timestamps, and never falls
  through to a guess.
- A round-trip test: `Gate1Result.raw_original` must equal the input
  value byte-for-byte.
- A mapping-table boundary test: class 6 with a string not in the
  mapping table returns FAIL, not a guess.

---

## Gate 2 admission predicate (`gate2_admission.py`)

Consumes a `Gate1Result` and produces a `Gate2Result`:

```python
@dataclass(frozen=True)
class Gate2Result:
    admitted: bool
    admission_reason: str            # canonical reason string, empty on admit
    policy_version: str              # the version this decision was made under
```

Admission rules (enumerated in the doctrine section, duplicated here as
pseudocode for implementation reference):

```
if gate1.outcome == "SKIP":
    # Class 1: already canonical, migration skips it entirely.
    # Gate 2 is never called on class 1 rows.
    raise AssertionError("gate 2 should not be called on SKIP rows")

if gate1.outcome == "FAIL":
    # Gate-1 FAIL rows always become refused via the uniform path.
    # The admission_reason distinguishes gate-1 failure from gate-2 refusal.
    return Gate2Result(
        admitted=False,
        admission_reason="gate_1_unrecoverable",
        policy_version=CURRENT_POLICY_VERSION,
    )

# gate1.outcome == "RECOVER" from this point
src = gate1.recovered_source_type

if src in REJECTED_SOURCE_TYPES:
    # e.g., collective_echo, derived
    return Gate2Result(False, f"source_type_in_rejected_set:{src}", CURRENT_POLICY_VERSION)

if src == "role_output":
    # Archivist role output is refused regardless of other recoverability.
    # source_role must be known at this point (either from the original dict
    # or from a class-specific recovery path); otherwise the row is treated
    # as having unknown source_role and is refused on that basis.
    if recovered_source_role is None:
        return Gate2Result(False, "role_output_with_unknown_role", CURRENT_POLICY_VERSION)
    if recovered_source_role == "archivist":
        return Gate2Result(False, "archivist_role", CURRENT_POLICY_VERSION)

# Class 2 bare-string specific refusal path
if gate1.class_id == 2 and gate1.raw_original in BARE_STRING_REJECTED_SET:
    return Gate2Result(False, "bare_string_maps_to_rejected_class", CURRENT_POLICY_VERSION)

return Gate2Result(True, "", CURRENT_POLICY_VERSION)
```

The specific sets (`REJECTED_SOURCE_TYPES`, `BARE_STRING_REJECTED_SET`)
are defined in `constants.py` and referenced from the doctrine section.
**Enumeration equality** between the code definitions and the doctrine
section is what the CI drift check enforces.

### Test coverage for gate 2

- One unit test per rule branch, using synthetic `Gate1Result`
  fixtures.
- A property test: for any `Gate1Result` with
  `gate1.outcome == "FAIL"`, the gate-2 output must always be
  `admitted=False, admission_reason="gate_1_unrecoverable"`.
- A property test: for any `Gate1Result` with an admitted
  `source_type` in the rejected set, gate 2 must refuse.
- A coverage test: every entry in `REJECTED_SOURCE_TYPES` has at
  least one unit test exercising its refusal path.

---

## Monotonic-in-tightness decision table (`rerun_policy.py`)

Implements the Decision 2 table:

| Current decision | Stored decision | Action |
|---|---|---|
| refuse | admit | `APPLY` — flip row to refused, advance policy version |
| refuse | refuse | `BUMP_ONLY` if reasons match; `APPLY` if reasons differ |
| admit | refuse | `BLOCK_AND_REVIEW` — leave row refused, emit to human-review queue |
| admit | admit | `BUMP_ONLY` — advance policy version, no content change |
| absent (no stored version) | any | `FIRST_EVALUATION` — normal two-gate pipeline |

The `refuse/refuse` case warrants a note: if the current policy refuses
the row for a different reason than the stored decision, the update
*applies* because the new reason is structurally distinct from the old
one. This is still tightening in the sense that the refusal is being
restated under the current policy. It is not a loosening, so it does
not need human review.

### Test coverage for re-run policy

- One unit test per decision-table row.
- A property test: no combination of (current, stored) inputs produces
  a state transition from refuse → admit without a `BLOCK_AND_REVIEW`
  entry being emitted.
- A round-trip test: a row that has been through
  `FIRST_EVALUATION` → `BUMP_ONLY` → `APPLY` must have its refusal
  history reconstructible from the stored state and the review queue.

---

## Cursor / state file (`cursor.py`)

Responsible for effectively-once row transition semantics on resume.

### File format (first proposal, ratification welcome)

JSONL, one record per row processed. Each record contains:

```json
{
  "eid": "...",
  "committed_at": "2026-04-11T12:34:56Z",
  "action": "APPLY" | "BUMP_ONLY" | "BLOCK_AND_REVIEW" | "FIRST_EVALUATION",
  "gate1_class_id": 3,
  "gate2_admitted": true,
  "policy_version": "v2.4.x-step6-a"
}
```

The cursor file lives at a known path (plan-phase sub-question: under
the workspace root? under a per-workspace state directory? under a
global migration state directory?) and is append-only during a single
run. Between runs, the cursor is compacted into a "processed eids" set
for fast membership checks.

### Crash recovery

On resume, the migration:

1. Reads the cursor file, reconstructs the set of already-processed
   eids.
2. Begins its corpus walk from eid 0 (or the lowest eid).
3. For each eid encountered: if it's in the processed set, skip; else
   process and append to the cursor.
4. At the end of the run, the cursor is compacted.

This is strictly idempotent at the row level: a row is either in the
processed set (skipped) or not (processed exactly once). A crash
mid-record can leave a partial JSONL entry, which the resume path
discards as malformed and re-processes the row. Since processing is
deterministic at gate 1 and policy-driven at gate 2, re-processing
produces the same action as the crashed attempt, so there is no double
write. This is what "effectively-once for committed row transitions
under resume" means in practice.

### Test coverage for cursor

- Write-then-read round-trip.
- Malformed trailing entry discarded on read, row re-processed cleanly.
- Compaction preserves the processed set exactly.
- Test using a synthetic corpus of 100 rows, aborted at row 47,
  resumed, and finishing with exactly 100 committed records in the
  cursor (not 147, not 53).

**Plan-phase sub-question 4:** cursor file path. Three candidates:
workspace-root-local, per-workspace under a `.torment_migration/`
directory, or global under `~/.torment/migration/`. Recommendation:
**per-workspace under a `.torment_migration/` directory**, because
workspaces are the natural unit of corpus identity and the cursor
should travel with the workspace. A global cursor would mix state
from multiple workspaces. A workspace-root-local single file is OK
but clutters the workspace root. A dedicated subdirectory keeps the
cursor plus any auxiliary state (review queue, dry-run reports,
etc.) neatly grouped.

---

## Human-review queue (`review_queue.py`)

Receives entries when `rerun_policy.py` emits `BLOCK_AND_REVIEW`. An
entry represents a row whose current-policy decision would be
`admit` but whose stored decision is `refuse`, which is a loosening
the migration refuses to apply without human approval.

### Entry format (first proposal)

```json
{
  "eid": "...",
  "blocked_at": "2026-04-11T12:34:56Z",
  "stored_decision": {
    "admission_refused": true,
    "admission_reason": "bare_string_maps_to_rejected_class",
    "admission_policy_version": "v2.4.x-step6-a"
  },
  "current_decision": {
    "admitted": true,
    "policy_version": "v2.4.x-step6-b"
  },
  "recovered_source_type": "memory",
  "gate1_class_id": 2,
  "reviewer_notes": ""
}
```

The queue file is append-only and co-located with the cursor under
`.torment_migration/review_queue.jsonl`. Review tooling (out of scope
for commit A and commit B) reads this file, surfaces entries to a
human, and produces a decision: approve (flip the row to admitted) or
deny (leave it refused and add a reviewer note explaining why).

Commit A can emit preview entries when running in dry-run mode to
show what would be routed to review if wet-run were enabled. Preview
entries carry `preview=true` and are filtered out of any authoritative
queue read.

### Test coverage for review queue

- Append-only property: writing an entry never rewrites prior entries.
- Preview filter: reading an authoritative queue skips
  `preview=true` entries.
- Dry-run preview: running the migration in dry-run mode with a
  tightening-then-loosening synthetic corpus produces the expected
  preview entries without writing authoritative ones.

---

## Dry-run report generator (`dry_run.py`)

Produces the commit A deliverable: a structured report of what the
migration would do against a target corpus, without touching any
stored row.

### Minimum report shape (floor, per Decision 6)

Four sections, all required:

1. **Per-class counts.** A table with one row per gate-1 class (1-7)
   plus a total. Each row shows the count of rows in that class.
2. **Gate-1 FAIL listing.** The eids and in-row evidence for every
   row classified as FAIL. For large FAIL populations, the listing is
   chunked with a summary header; no row is omitted.
3. **Gate-2 refusal listing.** The eids, recovered source_types, and
   refusal reasons for every row that would be refused at gate 2.
4. **Reproducibility anchor.** A header block recording:
   - Run timestamp (UTC, ISO 8601)
   - Admission policy version (`CURRENT_POLICY_VERSION`)
   - Git revision of the doctrine doc (from `git rev-parse HEAD` or
     equivalent)
   - Corpus scope (workspace id, eid range walked, filter applied if
     any)
   - Migration module version (commit A's git SHA at runtime if
     determinable)

The report format is **JSON** at the authoritative layer, with an
optional human-readable summary rendered alongside. JSON is chosen
because the report must be diffable — two dry-runs against the same
corpus should produce byte-identical JSON modulo the timestamp and git
SHA in the anchor, and a diff tool must be able to show what changed.

### Test coverage for the dry-run generator

Per Decision 6, this is its own test layer:

- **Classification fidelity test.** A synthetic corpus with known
  row classes → the report produces the expected per-class counts
  exactly. A row that should be class 3 is never reported as class 2.
- **Listing completeness test.** A synthetic corpus with N class-4
  rows → the FAIL listing contains exactly N entries, and every eid
  is present.
- **Reproducibility test.** Run the dry-run twice against the same
  synthetic corpus → the JSON output is byte-identical modulo the
  anchor fields that are allowed to vary (timestamp, git SHA).
- **No-write invariant test.** The dry-run is allowed to read any
  data store and is forbidden to write to any of them. A stub data
  store fails the test if any write method is called during a dry-run.

The fourth test is the structural safety check for Decision 6: it
encodes the "commit A cannot write" property as a property the tests
enforce, not just a property the code happens to have.

---

## CLI entry point (`cli.py`)

Commit A ships the following commands:

```
python -m torment_service.migration dry-run \
    --workspace <id> \
    [--output <path>] \
    [--human-summary]
```

Produces a dry-run report against the named workspace. Output defaults
to stdout (JSON); `--output` writes to a file. `--human-summary`
prints the per-class counts and listing summaries in a human-readable
format alongside the JSON.

```
python -m torment_service.migration status \
    --workspace <id>
```

Prints the current state of `.torment_migration/` for the named
workspace: cursor presence, last run timestamp, review queue length,
etc. Read-only.

**Commit A does NOT ship:**

- `python -m torment_service.migration apply` or any command that
  writes to stored rows. This command does not exist until commit B.

The CLI uses `py -3` on Windows per project convention; the module
is invoked via `python -m torment_service.migration` or
`py -3 -m torment_service.migration` depending on platform.

### Test coverage for CLI

- `dry-run` against a synthetic workspace produces a valid report.
- `status` against a fresh workspace reports zero cursor entries,
  zero review queue entries.
- Unknown command produces an informative error.
- No command in commit A writes anything to stored rows; a stub
  storage layer asserts this.

---

## Doctrine doc section

### Location

**Plan-phase sub-question 5:** which doctrine doc gets the admission
rules section. Candidates:

- `docs/DOCTRINE_v2.4.x.md` — the catch-all doctrine doc. Pros: central
  location, already referenced from the README. Cons: may become large.
- `docs/RECURSION_SAFETY_POLICY_v2.4.x.md` — the existing safety-focused
  doctrine. Pros: admission rules are a safety-policy concern. Cons:
  may conflate recursion-guard tuning with migration policy.
- A new doc, `docs/ADMISSION_POLICY_v2.4.x.md` — dedicated. Pros: clear
  separation, single source of truth. Cons: one more doc to maintain.

Recommendation: **`docs/ADMISSION_POLICY_v2.4.x.md`, a new dedicated
doc.** Rationale: the admission rules are the source of truth for
something the CI drift check will enforce, and isolating them in a
dedicated doc makes the enforcement boundary explicit. The doc is
small (the rules themselves are short) so the maintenance cost is
minimal. The existing doctrine docs link to it.

### Section contents

The doc contains at minimum:

- A stable anchor for the current policy version (e.g.,
  `## Admission rules — v2.4.x-step6-a`).
- The exhaustive list of `REJECTED_SOURCE_TYPES`.
- The exhaustive list of `BARE_STRING_REJECTED_SET`.
- The rule that `source_type == "role_output"` with
  `source_role == "archivist"` is refused.
- The rule that `source_type == "role_output"` with an unknown
  `source_role` is refused.
- Gate-1 FAIL → refused (with `admission_reason="gate_1_unrecoverable"`).
- Every admission reason string, enumerated.
- A "bump policy version" discipline note: any change to this section
  requires bumping the version suffix.
- A cross-line ordering rule: "any `v2.5.x-*` policy version is newer
  than any `v2.4.x-*` policy version" (or the equivalent convention
  for future doctrine lines).

### CI drift check

Lives at `tests/test_admission_policy_drift.py` (or equivalent).
Parses the doctrine doc section (probably by grepping the named
anchor and reading structured lists within it) and asserts
**enumeration equality** against the code-level sets in
`constants.py`:

- Every entry in the code's `REJECTED_SOURCE_TYPES` is in the doc.
- Every entry in the doc is in the code's `REJECTED_SOURCE_TYPES`.
- Same for `BARE_STRING_REJECTED_SET`.
- Same for the admission reason strings.

The test fails the build if any mismatch exists. The failure message
cites the specific missing or extra entries so the discrepancy is
immediately debuggable.

### Test coverage for the doctrine / CI check

- Synthetic doctrine doc section with a known rule set → the check
  passes.
- Synthetic doctrine doc section missing one rule → the check fails
  with a specific error citing the missing rule.
- Synthetic doctrine doc section with one extra rule → the check
  fails with a specific error citing the extra rule.
- Malformed doctrine doc section → the check fails with a parse
  error pointing at the malformed region.

---

## Recursion guard changes (`cognition/recursion_guard.py`)

Two small, strictly-tighter additions in commit A:

1. A new constant `REASON_MIGRATION_REFUSED` alongside the existing
   `REASON_*` constants.
2. An early-exit check at the top of the guard's node visit: if the
   row being visited has `provenance.admission_refused == True`,
   reject the walk with `REASON_MIGRATION_REFUSED`.

The check is strictly tighter than current behavior. A row that was
previously walked is still walked unless it has
`admission_refused=True`, which is only possible for rows that have
been through the migration. Commit A does not flip any row's
`admission_refused` to `True` because commit A has no write path.
Therefore the early-exit check in commit A is dormant until commit B
starts flipping rows. Its presence in commit A is correct so that
commit B does not have to simultaneously add the check and activate
it.

### Test coverage for guard change

- A synthetic row with `admission_refused=True` → the guard rejects
  the walk with `REASON_MIGRATION_REFUSED`.
- A synthetic row with `admission_refused=False` and otherwise valid
  state → the guard walks normally.
- A synthetic row with `admission_refused=True` reached via
  `parent_eids` from another row → the parent walk rejects at the
  refused row and terminates the chain cleanly.
- The REASON constant set matches the expected enumeration (defense
  against silent constant removal).

---

## Test suite summary

Commit A lands the following test files (existing files noted):

- `tests/test_migration_gate1.py` — new
- `tests/test_migration_gate2.py` — new
- `tests/test_migration_rerun_policy.py` — new
- `tests/test_migration_cursor.py` — new
- `tests/test_migration_review_queue.py` — new
- `tests/test_migration_dry_run.py` — new
- `tests/test_migration_cli.py` — new
- `tests/test_admission_policy_drift.py` — new (CI drift check)
- `tests/test_recursion_guard.py` — existing, new tests added for
  `REASON_MIGRATION_REFUSED` and the early-exit check
- `tests/test_provenance_v1.py` — existing, new tests added for the
  three new fields and their defaults

The goal for commit A's test suite: every code path added in commit A
has at least one test, and the dry-run's no-write invariant is
enforced at the test layer so no future change can silently break it.

---

## Documentation updates

Commit A updates:

- `docs/ADMISSION_POLICY_v2.4.x.md` — new, contains the named admission
  rules section and the version discipline notes.
- `docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md` — `WRITE_MIGRATION` flips
  from RESERVED to ACTIVE (step 6, commit A); `WRITE_SYSTEM_IMPORT`
  stays RESERVED with a note that follow-up activation requires a
  named concrete source plus a written adapter spec.
- `docs/RECURSION_SAFETY_POLICY_v2.4.x.md` — small note that the guard
  now honors `admission_refused` as an early-exit condition with
  `REASON_MIGRATION_REFUSED`.
- `docs/WRITE_MIGRATION_FRAMING_v2.4.x.md` — unchanged in content, but
  a status line at the top is added: "All six decisions ratified on
  2026-04-11. Implementation plan lives in
  `WRITE_MIGRATION_IMPLEMENTATION_PLAN_v2.4.x.md`."
- `docs/RELEASE_NOTES_v2.4.3.md` — unchanged; step 6 gets its own
  release notes file when commit A ships.
- `docs/RELEASE_NOTES_v2.4.x-step6.md` — new (commit A version),
  covering commit A's scope only.
- `README.md` — minor update pointing at the new admission policy doc
  and the step-6 commit A deliverables. No architectural description
  changes.

Commit B updates:

- `docs/RELEASE_NOTES_v2.4.x-step6.md` — extended with commit B scope.
- No other doc changes unless commit A revealed something the plan
  didn't anticipate.

---

## Out of scope for step 6 implementation (inherited from framing doc, confirmed)

- Not a notes-field enrichment pass beyond provenance reconstruction.
- Not a schema upgrade beyond the three admission fields.
- Not a backfill for missing timestamps, embeddings, or other fields.
- Not a performance or storage optimization.
- Not a corpus cleanup sweep.
- Not an activation of `SOURCE_DERIVED`.
- Not a doc sweep beyond the updates listed above.
- Not a flip of `TORMENT_ARCHIVIST_WRITEBACK`.
- Not an activation of `WRITE_SYSTEM_IMPORT`.
- Not a `.gitattributes` or repo-wide line-ending policy decision.

If any of these get bundled in during implementation, they get split
out into their own steps with their own ratification.

---

## Plan-phase sub-questions still open (require ratification before commit A)

Numbered for ratification convenience:

1. **Gate-1 FAIL schema shape.** Sentinel `source_type` constant
   (recommended) vs nullable `source_type`. Section: "Schema backfill
   semantics."
2. **Module placement.** `torment_service/migration/` (recommended) vs
   top-level `migration/`. Section: "Module layout."
3. **Class 7 initial predicate.** Empty list in commit A
   (recommended) vs a starting set derived from known test infrastructure.
   Section: "Gate 1 recovery predicate."
4. **Cursor file path.** Per-workspace `.torment_migration/`
   (recommended) vs workspace-root single file vs global. Section:
   "Cursor / state file."
5. **Doctrine doc location.** Dedicated
   `docs/ADMISSION_POLICY_v2.4.x.md` (recommended) vs adding a section
   to `DOCTRINE_v2.4.x.md` vs adding to
   `RECURSION_SAFETY_POLICY_v2.4.x.md`. Section: "Doctrine doc section."

All five sub-questions have a recommendation. The plan-ratification
step can either accept all recommendations wholesale or revise
specific ones. None of the five are doctrinal choices — they are all
mechanical decisions about where things live and what shape they take.

---

## Next move after this plan is ratified

1. Address any revisions requested on the plan doc, especially the
   five plan-phase sub-questions.
2. Begin **commit A** of step 6 implementation. The A/B split
   discipline from step 5 governs the work: commit A lands the
   machinery plus the dry-run only, with no write path and no way to
   flip a single stored row. Commit A does not proceed to commit B
   without an explicit ratification pause, during which the dry-run
   output against the real corpus is reviewed.
3. Run dry-run against the real corpus for the first time. This is
   the first moment any step-6 code touches real data. The output
   feeds the commit B ratification.
4. Begin **commit B** only after commit A has been reviewed and the
   dry-run output has been inspected. Commit B lands the write path
   as new code, behind its own flag, with the monotonic-in-tightness
   machinery exercised live for the first time.

**No code before this plan is ratified.**
**No commit B before commit A is reviewed against the real corpus.**
