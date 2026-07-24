# TORMENT Brainvision — Stage S3B v0.3 Durable Evidence Architecture Review v0.1

Status: DRAFT (corrected replacement) for independent review. Docs-only. Creates no authority.
This is a new correction architecture, not a Stage S3B v0.2 retry.
This replacement supersedes the prior v0.1 draft text; the prior draft is review input only and remains unedited.

```text
document_class             = durable-evidence architecture review (docs-only, corrected replacement)
authority_created          = none
implementation_authorized  = false
execution_authorized       = false
manifest_contact           = none
scientific_reconstruction  = none
retained_evidence_modified = none
git_mutations              = none
supersedes_v0_2_authority  = false (v0.2 is consumed and terminal)
current_readiness          = NOT YET IMPLEMENTATION-READY (pending independent review of this corrected architecture)
```

The scientific claim boundary is fixed throughout and never crossed:

```text
two complete scientific passes occurred
the two canonical pass bundles were byte-identical
the unpublished result kind (one of exactly two valid gate outcomes) is NOT durably available
the v0.2 result must not be reconstructed and this document does not imply which outcome occurred
```

---

## 1. Purpose and scope

This review analyzes how a *future, separately authorized* Stage S3B v0.3 one-run execution could preserve durable scientific evidence across infrastructure failures, so that the v0.2 evidence-layer defect — a scientific result that was computed but never durably retained — cannot recur.

In scope: the durability, ordering, tamper-evidence, identity-binding, and recovery semantics of the *evidence layer* around a single authorized invocation — the record model, the immutable scientific bundle, the scientific-completion receipt, the primary and emergency channels, authority-attempt semantics, crash/recovery behavior, publication decoupling, and the fault-injection surface.

Out of scope: the scientific descriptor, the frozen fixture family, the manifest contents, the S1 freeze conclusion, and the authorization/identity-binding machinery, which functioned correctly in v0.2. This document selects no implementation, authorizes none, and reopens no v0.2 state. Any conceptual parallels to measurement, observer, or quantum-software state models appear only as design prompts in §16; they are never treated as evidence that a design is correct or secure, and they are never used as a security requirement.

---

## 2. Frozen v0.2 evidence

Authoritative repository (observed read-only, no mutation):

```text
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
branch = main
HEAD = origin/main = c185e081afd9abba6ebfe4acf45cc59b570281c0
findings commit = c185e081  "docs(research): record synthetic validation v0.2 execution failure findings" (one file added)
```

Retained immutable forensic evidence (reconfirmed byte-for-byte unchanged this review):

```text
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.execution_journal/
  current_state.json      144 bytes  sha256 63bd8dbe4ee9eab89bb4cb9aea66e39b1cecf43def4f2b19a19a6e0c28edc965
  current_state.json.tmp  136 bytes  sha256 b0910c0e5266d23105faae3fc2228396cb5ea54fbc5f33561bd891818c00b11b
```

```json
current_state.json     = {"phase":"STAGING_VERIFYING","authority_consumed":true,"contact_armed":true,"manifest_contact_attempt_count":2,"manifest_read_success_count":2}
current_state.json.tmp = {"phase":"PROMOTING","authority_consumed":true,"contact_armed":true,"manifest_contact_attempt_count":2,"manifest_read_success_count":2}
```

External captures (operator-recorded; not independently re-readable from the connected folder; validated by content-consistency):

```text
stdout  0 bytes    sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
stderr  173 bytes  sha256 e734e97a700364b6bd3d2a82f5f690645311c7ff5e578ee33a29bf86a5b21528
stderr text = EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION last_verified_phase=STAGING_VERIFYING authority_consumed=true manifest_contact_attempt_count=2 manifest_read_success_count=2 exit=4
```

Retained by the v0.2 fallback: last verified durable phase, authority-consumed flag, contact-attempt count, read-success count, exit code.
Not retained: the scientific result kind, the pass-bundle SHA-256, the underlying exception detail, and any terminal evidence JSON.

This evidence is immutable and must not be repaired, renamed, deleted, promoted, terminalized, or recomputed.

---

## 3. Exact failure reconstruction

The one authorized v0.2 invocation ran exactly once and reached the durable phase `STAGING_VERIFYING` while a complete temporary `PROMOTING` payload was retained. Each phase transition advanced a single mutable pointer (`current_state.json`): write `current_state.json.tmp` with exclusive create (flush, fsync, read-back compare, directory sync), `os.replace(tmp, current_state.json)`, read back the target, compare, directory-sync the journal; any exception was raised as `EvidenceUpdateFailedAfterConsumption` carrying the last verified durable state. Publication was reached only after the `PROMOTING` transition durably landed.

Durable `STAGING_VERIFYING` proves that two manifest reads succeeded, two complete scientific passes finished, the two canonical pass bundles were byte-identical, and the result artifacts were constructed in memory. It does **not** durably reveal the scientific result kind.

Corrected immediate failure classification:

```text
ATOMIC_CURRENT_STATE_TRANSITION_FAILURE
```

Historical / narrower candidate label, retained only for continuity (not the supported classification):

```text
ATOMIC_CURRENT_STATE_REPLACEMENT_FAILURE   (narrower; asserts the replace syscall specifically — not established)
```

The retained evidence supports failure **after** the complete temporary next-state (`PROMOTING`) bytes existed and **before** the authoritative current-state pointer durably advanced to `PROMOTING`. It does not identify one exact failing syscall: the artifact pair (a complete `PROMOTING` `.tmp` still present, `current_state.json` still `STAGING_VERIFYING`) is consistent with a failure at the temporary file's directory-sync, at the atomic replacement, or at the target read-back/verify — and the underlying exception detail was not retained. Because publication is reached only after the transition durably lands, no publication and no scientific-result exposure occurred. No deeper operating-system, filesystem, hardware, antivirus, or environmental root cause is asserted.

---

## 4. Security and durability problem statement

The v0.2 authorization, identity binding, single-use consumption, monotonic contact accounting, false-publication prevention, and staging/publication separation all worked. The defects are narrower:

```text
D1  Single mutable authoritative pointer advanced by one atomic transition per phase — one transition failure halted durable progress.
D2  The scientific result kind and canonical bundle were held only in memory at the failure point; nothing durable had recorded them,
    because scientific durability was deferred to phases co-located with the publication gate.
D3  The terminal/emergency evidence writer shared the primary mechanism (same directory, same atomic write, same serializer,
    same exception path); when the primary failed, terminal evidence failed too, degrading to a single stderr line.
D4  "Computation complete" was entangled with "pointer advanced past the publication gate", so an infrastructure failure at the gate
    erased the distinction between "computed" and "durably recorded".
```

Correction goals: make durable scientific completion a *committed pair* — an immutable content-addressed scientific bundle plus a linked completion receipt — recorded *before* the publication gate through a mechanism that uses no single mutable pointer, no single atomic replacement, no single directory sync, no single serializer, and no single exception path; provide an independent emergency channel that can preserve what the process observed in memory without silently becoming authoritative; and never convert any recovery into permission to rerun the protected computation or reopen consumed authority.

---

## 5. Corrected-protocol invariants

### 5.1 Authority invariants

Authority is modeled with three states, not a binary:

```text
AUTHORITY_NOT_ATTEMPTED
AUTHORITY_CONSUMPTION_ATTEMPT_FAILED
AUTHORITY_CONSUMED
```

```text
A1  A durable AUTHORITY_CONSUMED record is the point of no return; authority is consumable exactly once.
A2  Once AUTHORITY_CONSUMED is durable, no recovery path may return the run to an executable state.
A3  Recovery (evidence or publication) never re-arms, re-consumes, or re-invokes the protected computation.
A4  Publication failure must not reopen execution authority.
A5  Evidence-write failure must not reopen execution authority.
A6  Absence of a completion pair is grounds to classify and stop, never to recompute.
A7  AUTHORITY_CONSUMPTION_ATTEMPT_FAILED (the consumption record itself failed to durably commit):
      protected manifest contact = prohibited
      scientific execution = prohibited
      automatic reuse of the original authorization = prohibited
      automatic retry = prohibited
      a new docs-only authorization is required before any new process
    Terminal classification: AUTHORITY_CLOSED_UNEXERCISED_AFTER_CONSUMPTION_RECORD_FAILURE
      = the protected computation was not exercised; successful durable consumption was not established;
        the old authorization is nevertheless closed against automatic reuse.
    This state is neither "fully consumed" nor "still freely open". The emergency capsule should attempt to
    preserve the consumption-record failure and confirm that protected contact did not begin.
```

### 5.2 Manifest-contact invariants

```text
M1  Each contact attempt is durably recorded BEFORE the read, monotonically.
M2  Each successful read is durably recorded after it succeeds, monotonically.
M3  Contact records are write-once; a count can never be reduced or overwritten.
M4  A hard cap (two attempts, two successes) is enforced against the durable record so a crash cannot license a third contact.
M5  Contact evidence is a distinct record kind and is never conflated with scientific-completion evidence.
```

### 5.3 Scientific-completion invariants (bundle + receipt)

```text
S1  Durable scientific completion is a PAIR: an IMMUTABLE_SCIENTIFIC_BUNDLE (§8a) and a linked SCIENTIFIC_COMPLETION receipt (§8b).
S2  The immutable bundle must be durably written and verified, THEN the receipt must be durably written and verified, BEFORE any publication operation begins.
S3  The bundle carries the canonical result/pass-bundle bytes needed to regenerate the exact publication artifacts without executing science again.
S4  The result kind is durable (inside the verified pair) without any dependency on publication succeeding.
S5  The bundle is EVIDENCE STORAGE, not automatic public exposure; the receipt is bounded and references the bundle by hash and length.
S6  A bundle alone does not establish authoritative completion; a receipt alone does not either. Only the verified, linked pair does.
```

The completion pair "becomes valid" at exactly one instant: when the immutable bundle has been written write-once, read back, byte-compared, hash-verified, and its containing directory durability-verified; AND the receipt referencing it has likewise been written, read back, and hash-verified, extends the valid primary chain, and shares the bundle's execution and authorization identities — and never before publication is attempted.

### 5.4 Publication invariants

```text
P1  Computation-completion and publication-completion are separate durable states.
P2  If publication fails, the verified completion pair (result kind + bundle) remains available.
P3  Publication may not begin before a verified, linked bundle+receipt pair exists.
P4  Publication failure cannot alter, weaken, or overwrite the completion pair.
P5  Publication retry, if permitted at all (§13, provisional), is a projection of the committed bundle and never implies scientific rerun.
```

### 5.5 Terminal-evidence invariants

```text
T1  A terminal failure record must remain possible when the primary mechanism has failed AND process/exception handling is still alive.
T2  Emergency evidence must not silently replace or outrank stronger primary evidence.
T3  Primary and emergency records are distinguishable by record kind and channel.
T4  Any contradiction between channels fails closed to the most conservative interpretation and is flagged, never silently reconciled.
T5  Bounded underlying exception detail is retained where it can be captured safely.
```

### 5.6 Canonical-identity invariants

```text
C1  Every durable record is canonically serialized (deterministic bytes, single terminal newline).
C2  Every record is bound to execution identity, authorization identity, and protocol/schema identity.
C3  Records are monotonic (sequence numbers strictly increase; kinds do not regress).
C4  Every record carries its own canonical SHA-256 and, where applicable, its predecessor's hash (hash-link).
C5  Each record is independently verifiable from its bytes alone.
C6  Predecessor identity, execution identity, and writer/attempt identity are unambiguous; orphan or mislinked records fail closed.
```

---

## 6. Candidate architecture comparison

The v0.2 failure dependency: one mutable pointer advanced by one atomic transition per phase, with terminal/emergency evidence sharing that same mechanism.

### 6.A Append-only event ledger
Canonical records appended to a single ledger file, each fsync'd.
- Guarantees: total order by append position; no rename/replace; monotonic by construction.
- Does not guarantee: per-record independence (one file object is shared fate); clean handling of a torn trailing append without a framing/self-hash convention; tamper-evidence unless hash-linked.
- Strongest failure mode: a torn trailing record after an abrupt stop, which must be discarded by validation.
- Shares v0.2 dependency? No replace dependency; shares a different single-object (one inode/handle) dependency.

### 6.B Immutable per-record objects (content-addressed)
Each durable event is its own object whose name embeds record kind, sequence, content hash, and a unique write-attempt identity.
- Guarantees: per-record independence; no mutable pointer; no replace; duplicate/fork attempts are visible as distinct candidate objects rather than silent overwrites.
- Does not guarantee: that a created object is complete (an exclusive create can still leave an empty, partial, or unverified object — see §6-note); ordering unless sequence+predecessor are embedded; directory-entry durability without an explicit, validated sync.
- Strongest failure mode: a torn/empty candidate object occupying a filename; handled as forensic debris, never admitted to the valid chain.
- Shares v0.2 dependency? No.

### 6.C Write-once hash-linked chain over content-addressed objects
6.B plus predecessor hash-links, sequence numbers, and record kinds.
- Guarantees: everything B guarantees, plus unambiguous order, gap detection, break detection, tamper-evidence, deterministic replay by byte-validation of candidates.
- Does not guarantee: freedom from directory-durability concerns; protection against whole-directory/volume loss (needs the emergency channel and, ultimately, off-host durability which is out of scope here).
- Strongest failure mode: a partially written or forked candidate is detected by byte/hash validation and excluded fail-closed.
- Shares v0.2 dependency? No. Strongest single-channel forensic option.

### 6.D Dual-channel primary/emergency
A full-fidelity primary channel (A/B/C) plus an independent bounded emergency channel (§10) that captures what the process observed in memory when a primary operation fails, without becoming authoritative.
- Guarantees: an EMERGENCY_OBSERVED_UNCOMMITTED capsule can be produced while process/exception handling remains alive; channel/mechanism diversity.
- Does not guarantee: capture after abrupt termination (kill/interpreter death/host crash/power loss); it is bounded by design and never authoritative.
- Strongest failure mode: the emergency write itself failing; bounded by a pre-opened descriptor and a single append.
- Shares v0.2 dependency? Only if built on the same mechanism as the primary; the mandate is that it must not (see §12 for the layered independence it does and does not provide).

Note (correction to the prior draft): exclusive creation does **not** guarantee "absent or complete". See §9.

### Comparison matrix

| Dimension | A ledger | B content-addressed objects | C hash-linked chain | D dual-channel |
|---|---|---|---|---|
| Depends on rename/replace | No | No | No | No |
| Depends on one mutable pointer | No (one file object) | No | No | No |
| Created-object completeness guaranteed | n/a | No (torn/empty possible) | No (validated by bytes) | capsule bounded |
| Crash behavior | discard torn tail | validate candidates | validate + verify chain | capsule iff caught/controlled |
| Duplicate / fork behavior | needs seq/dedup | visible as distinct candidates | arbitrated by chain rules (§9/§11) | n/a |
| Ordering guarantees | append order | needs embedded seq | strong (seq + hash-link) | primary provides |
| Tamper evidence | only if hash-linked | weak alone | strong | strong for capsule |
| Canonical replayability | good | good | excellent | primary provides |
| Windows directory-durability | uncertain (see §9) | uncertain (see §9) | uncertain (see §9) | uncertain (see §9) |
| Fault-injection surface | small | larger | larger | + capsule points |
| Forensic strength | moderate | moderate-high | high | high (survives caught primary loss) |
| Contradiction risk | low | moderate | low (chain arbitrates) | must define arbitration (§10/§11) |
| Accidental authority reuse | none intrinsic | none intrinsic | none intrinsic | none intrinsic |
| Shares v0.2 dependency | No | No | No | No (by mandate) |

Windows directory-durability is marked uncertain for all candidates by correction; it is not claimed as "good" for any design until the exact primitive is specified and tested (§9).

---

## 7. Recommended provisional architecture

Provisional recommendation (subject to §16 Hilmir decisions and to independent review of this corrected draft): a **composite of C + D** — a write-once, hash-linked chain over content-addressed immutable objects with **no mutable authoritative pointer**, plus an independent bounded emergency capsule.

Core properties:

1. No mutable pointer, no replace (fixes D1). "Current position" is *derived by replay*: recovery scans candidate objects, validates their bytes, verifies the predecessor chain, and takes the longest valid prefix as authoritative. There is no single canonical mutable filename to advance.

2. Bundle-then-receipt before publication (fixes D2/D4). The mandatory order commits the immutable scientific bundle, then the completion receipt referencing it, *before* the first publication operation. The result kind is durable inside that verified pair, independent of publication.

3. Independent emergency channel (fixes D3, within its limits). A capsule descriptor is opened in a separate directory before authority consumption; a caught failure at any durable transition writes one bounded EMERGENCY_OBSERVED_UNCOMMITTED capsule via a single append, using a distinct minimal serializer and a distinct exception path. Its independence is layered and bounded (§12).

4. Publication is downstream projection (provisional; §13). A separately authorized publication-only process projects the verified bundle; it can never run science.

Minimum sufficient durable sequence (the granularity tradeoff resolved conservatively):

```text
MANDATORY (durable, write-once, hash-linked, content-addressed):
  1. AUTHORITY_CONSUMED
  2. MANIFEST_CONTACT_ATTEMPT   (one per attempt, durable BEFORE the read — M1/M4)
  3. MANIFEST_READ_SUCCESS      (one per success, durable AFTER the read — M2)
  4. IMMUTABLE_SCIENTIFIC_BUNDLE (durably written and verified; §8a)
  5. SCIENTIFIC_COMPLETION       (receipt referencing #4; durably written and verified; §8b)
  6. PUBLICATION_ATTEMPTED
  7. PUBLICATION_COMPLETED       (only on success)
  8. TERMINAL_STATUS             (primary if reachable; else emergency capsule)

OPTIONAL (forensic resolution, NOT safety-bearing, NOT durable-guaranteed):
  SCIENTIFIC_PASS_1_COMPLETED, SCIENTIFIC_PASS_2_COMPLETED
```

Rationale: the manifest-contact records are not collapsible (the attempt must be durable before each read so a crash can never license a third contact). Per-pass scientific records are optional because the two-read cap and the byte-identical comparison are captured in the bundle+receipt pair. Greater event granularity improves forensic resolution but adds durable writes before completion, each an independent failure point. Because per-pass records are optional, no downstream reasoning may treat "a pass occurred" as a durable primary fact unless a mandatory record or a caught-exception capsule captured it (§11).

Every durable record binds: `record_kind`, `sequence_number`, `protocol_version`, `record_schema_version`, `execution_identity`, `authorization_identity`, `predecessor_record_sha256`, `writer_attempt_identity`, a kind-specific `payload`, and `record_sha256` over the canonical bytes.

---

## 8. Durable scientific-completion: bundle + receipt

### 8a. IMMUTABLE_SCIENTIFIC_BUNDLE (mandatory object)

The bundle contains the canonical result/pass-bundle bytes required to regenerate the exact publication artifacts **without executing science again**. It must be:

```text
canonically serialized (deterministic bytes)
content-addressed by SHA-256
bound to protocol identity and execution identity
written BEFORE publication
written WITHOUT mutating any authoritative pointer (content-addressed object; no replace)
read back and byte-compared to the intended bytes
hash-verified (stored SHA-256 == recomputed SHA-256 of the read-back bytes)
durability-verified using the strongest validated Windows mechanism (see §9; may require a scoped adapter)
immutable after creation
```

The bundle is evidence storage, not automatic public exposure. A bundle existing by itself does not establish authoritative scientific completion.

```text
verified bundle WITHOUT a valid matching completion receipt = ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE
An orphan bundle:
  is retained for forensics
  is never repaired or deleted automatically
  does not authorize publication
  does not independently establish the scientific result
  does not reopen execution authority
```

Minimal exposure is preserved by storing the full canonical bytes only inside the immutable evidence object (not in the receipt and not automatically published); the receipt references it by hash and length.

### 8b. SCIENTIFIC_COMPLETION (bounded, canonical, hash-linked receipt)

A receipt that references the exact verified immutable bundle. Field determinations:

| Field | Determination |
|---|---|
| protocol_version | Mandatory |
| record_schema_version | Mandatory |
| execution_identity | Mandatory |
| authorization_identity | Mandatory |
| authority_consumed_status | Mandatory (must be AUTHORITY_CONSUMED) |
| manifest_contact_attempt_count | Mandatory (== 2) |
| manifest_read_success_count | Mandatory (== 2) |
| scientific_pass_count | Mandatory (== 2) |
| two_pass_canonical_identity_status | Mandatory (== identical) |
| scientific_result_kind | Mandatory (exactly one of the two valid gate outcomes; §18) |
| immutable_scientific_bundle_sha256 | Mandatory |
| immutable_scientific_bundle_byte_length | Mandatory |
| runner_git_blob / runner_raw_sha256 | Mandatory (implementation identity) |
| test_git_blob / test_raw_sha256 | Mandatory (implementation identity) |
| schema_git_blob / schema_raw_sha256 | Mandatory (implementation identity) |
| configuration_identity | Mandatory |
| manifest_external_sha256 / manifest_payload_sha256 | Mandatory |
| sequence_number | Mandatory |
| predecessor_record_sha256 | Mandatory (hash-link) |
| record_identity (kind + writer_attempt) | Mandatory |
| record_sha256 | Mandatory (self-hash over canonical bytes) |
| completion_validity | Mandatory (separate field; §18 — never a result-kind value) |
| creation_phase | Derived (include only if it adds forensic value) |
| full scientific payload bytes | Inappropriate in the receipt (they live only in the immutable bundle) |
| wall-clock timestamp / host detail | Optional, bounded, advisory; never authoritative or an ordering key |

A completion receipt is **valid** only when: the referenced bundle exists; the referenced bundle is complete; its canonical bytes read back exactly; its byte length matches; its SHA-256 matches; the receipt is itself complete and valid; the receipt shares the bundle's execution and authorization identities; and the receipt extends the valid primary record chain.

Definitions (the authoritative-result state machine):

```text
receipt WITHOUT a valid matching bundle          = INVALID_SCIENTIFIC_COMPLETION
bundle WITHOUT a valid matching receipt          = ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE
valid bundle + valid matching receipt            = AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
```

The observer/evidence boundary — the instant at which "the run has a durable determinate scientific result" becomes an asserted fact — occurs **only** at the third condition (the verified pair), never at a lone bundle or a lone receipt. (For the v0.2 lineage, no such pair exists; its result kind remains permanently unavailable and must not be reconstructed.)

---

## 9. Primary evidence channel and immutable-record write semantics

Corrected write semantics — an exclusive-create write does **not** guarantee a record is either absent or complete. A failed write can leave any of:

```text
a created but empty object
a partially written object
a fully written but unverified object
a synced file whose directory-entry durability is uncertain
an invalid object occupying a candidate filename
```

No torn or invalid object may be repaired, overwritten, renamed into validity, or silently discarded. The construction therefore uses:

```text
a unique write-attempt identity
content-addressed object identity (name embeds the content/record SHA-256)
canonical internal sequence and predecessor identity
NO single canonical mutable filename
```

Defensible object naming: `<record_kind>.<sequence>.<record_sha256>.<writer_attempt_identity>`. Recovery scans candidate objects and validates their bytes (self-hash, then predecessor link), rather than trusting filenames. Candidate handling:

```text
zero valid candidates extending the predecessor                       = stop at the predecessor
one valid candidate extending the predecessor                         = accept
multiple byte-identical valid candidates, same record identity        = redundant immutable copies; flag, do not invent a fork
multiple valid candidates, different identities, one seq/predecessor   = SAME_SEQUENCE_FORK; fail closed
invalid or torn candidates                                            = forensic debris; retained; never admitted to the valid chain
```

No mutable `current_state` pointer is reintroduced. Each record is written by: canonical serialize → compute record SHA-256 → exclusive-create the content-addressed object → write → flush → file fsync → read back → byte-compare → directory-durability step (§9-Windows) → treat as durable only after byte-compare and directory durability both succeed. Anything short of that is a candidate object validated (or rejected) at recovery, not a trusted record.

Windows directory-durability (correction 9): the Python standard library can provide exclusive file creation, writes, flush, file fsync, read-back verification, rename/replace primitives, and pre-opened descriptors. **Durable directory-entry synchronization on Windows requires implementation-specific validation and may require a narrow Win32 adapter.** This review does not claim any design is simply "good" or "strong" on Windows, and does not claim full directory durability until the exact primitive is specified and tested on the authoritative Windows environment. It *recommends investigating* a narrowly scoped Windows directory-durability adapter as a named pre-implementation decision (§15); it does not implement or authorize one.

---

## 10. Emergency evidence channel

Purpose: preserve computed-but-primary-uncommitted evidence when a primary bundle or completion-record operation fails **and process/exception handling is still alive**.

Independence mandate — the emergency channel must not share the primary's temporary path, replace operation, directory sync, mutable pointer, serialization function, or exception-handling path. Recommended form: a capsule file opened with exclusive create in a *separate directory*, or a descriptor pre-opened before authority consumption and appended once at failure time, using a distinct minimal fixed-format serializer.

Independence is layered, and the proposed mechanism must be described honestly against each layer — it does not provide all of them:

```text
code-path independence      : YES  (distinct exception/handling path)
serializer independence     : YES  (distinct minimal fixed-format serializer, not the primary canonical serializer)
directory independence      : YES  (separate directory)
file-handle independence    : YES  (own descriptor, pre-opened before consumption)
filesystem independence     : NO by default (same filesystem unless deliberately separated)
volume independence         : NO   (same volume — a volume-level failure can take both channels)
host independence            : NO   (same host — a host crash takes both channels)
power-loss independence     : NO   (power loss can precede any fsync on either channel)
```

A separate directory and serializer on the same volume provide mechanism diversity (they can survive a caught, localized primary-mechanism fault), but they are not volume, host, or power-loss independence. The mechanism can survive: a caught primary serialization/write/replace/sync exception and controlled termination. It cannot survive: forced process kill, interpreter death, host crash, or power loss (see §11).

Capsule fields explicitly classified as `EMERGENCY_OBSERVED_UNCOMMITTED`:

```text
scientific_result_kind_observed_in_memory
canonical_bundle_sha256_observed_in_memory
canonical_bundle_byte_length_observed_in_memory
two_pass_identity_observed
immutable_bundle_primary_commit_confirmed        (true/false — did the primary bundle durably commit?)
primary_scientific_completion_committed          (true/false — did the primary receipt durably commit?)
last_valid_primary_record_sequence
last_valid_primary_record_sha256
```

Plus, for authority-attempt failures: the consumption-record failure and a confirmation that protected contact did not begin. Plus the failing operation, exception type, a length-bounded canonicalized exception message (strip control/non-UTF-8 bytes, collapse whitespace, truncate to a fixed budget, retain original length so truncation is visible), and the exit code.

`EMERGENCY_OBSERVED_UNCOMMITTED` semantics:

```text
does NOT authorize publication
does NOT establish AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
does NOT permit execution recovery
does NOT permit scientific-result reconstruction
DOES preserve the otherwise-lost observed result kind and bundle identity (as observation only)
```

If later primary evidence conflicts with the capsule:

```text
classification            = CONTRADICTORY_EVIDENCE
scientific-verdict assertion = prohibited
automatic reconciliation  = prohibited
```

Arbitration (T2/T4): the capsule never outranks a stronger primary record for the same fact; disagreement fails closed to the most conservative interpretation and is flagged for operator forensic review, never silently reconciled.

---

## 11. Crash and recovery semantics

Global rule: scientific execution is never repeated under the consumed authority. Recovery interprets durable evidence; it does not continue computation. The four recovery notions are distinct:

```text
execution recovery   = FORBIDDEN once AUTHORITY_CONSUMED is durable (never resumes the protected computation)
evidence recovery    = replay + validate immutable candidates; assert only what survives validation
publication recovery = re-project an already-committed bundle via the publication-only process (only if §13 permits)
operator forensic interpretation = human reading of retained evidence; never a state-mutating code path
```

Failure taxonomy — the emergency descriptor can assist **only** for caught exceptions and controlled termination; it cannot be assumed to write after a forced process kill, interpreter death, host crash, or power loss:

```text
caught filesystem/serialization exception   -> primary record fails; emergency capsule MAY be written
normal controlled termination               -> orderly; capsule available if used
forced process kill                         -> no capsule; only already-durable primary records survive
interpreter crash                           -> no capsule; only already-durable primary records survive
host crash                                  -> no capsule; only already-durable primary records survive
power loss                                  -> no capsule; only already-durable primary records survive
```

Evidence classes used below:

```text
primary-durable fact         = provable from a validated durable primary record
emergency-observed fact      = present only in an EMERGENCY_OBSERVED_UNCOMMITTED capsule (never authoritative)
operator-transcript fact     = stdout/stderr the operator retained externally (advisory)
in-memory fact lost on abrupt termination = not provable after kill/interpreter/host/power loss
unsupported fact             = not provable from any retained channel
```

For each crash point, only mandatory durable primary records prove anything under abrupt termination. Because per-pass records are optional, a hard crash after pass 1 or pass 2 does **not** by itself prove those passes occurred.

| Crash / fault point (abrupt unless noted) | Primary-durable facts | Cannot assert (abrupt) | Publication eligible | Execution resume | Authority state | Terminal classification |
|---|---|---|---|---|---|---|
| Before AUTHORITY_CONSUMED durable | none consumed | any progress | no | new lineage only | AUTHORITY_NOT_ATTEMPTED or ATTEMPT_FAILED | see below |
| Consumption record failed (caught) | contact not begun (capsule) | durable consumption | no | never | AUTHORITY_CONSUMPTION_ATTEMPT_FAILED | AUTHORITY_CLOSED_UNEXERCISED_AFTER_CONSUMPTION_RECORD_FAILURE |
| Just after AUTHORITY_CONSUMED | authority consumed | any contact/science | no | never | AUTHORITY_CONSUMED | CONSUMED_NO_CONTACT |
| After 1st contact attempt record | ≤1 attempt | read success / science | no | never | consumed | CONSUMED_PARTIAL_CONTACT |
| After 2nd read-success record, before bundle | 2 reads occurred | that any pass completed, 2-pass identity, result kind | no | never | consumed | CONSUMED_READS_NO_COMPLETION |
| After bundle-commit failure (caught) | reads durable; capsule may hold observed kind/hash | durable authoritative result | no | never | consumed | CONSUMED_COMPLETION_UNCOMMITTED (bundle uncommitted) |
| Orphan bundle present, no receipt | reads durable; a bundle object exists | authoritative result (pair incomplete) | no | never | consumed | ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE |
| Receipt present but bundle absent/mismatched | chain up to receipt | authoritative result | no | never | consumed | INVALID_SCIENTIFIC_COMPLETION (fail closed) |
| Verified bundle + verified receipt durable | AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT | that it was published | yes (projection) | never | consumed | CONSUMED_COMPLETE_UNPUBLISHED |
| During publication | completion pair durable | publication complete | yes (idempotent) | never | consumed | CONSUMED_PUBLICATION_INTERRUPTED |
| After publication, before terminal record | pair + publication durable | terminal record present | already done | never | consumed | CONSUMED_PUBLISHED_NO_TERMINAL |
| Primary object torn/empty/unverified | prior validated records | that record | per furthest valid record | never | consumed | classify at furthest valid record; debris retained |
| Directory-durability unverified for a record | prior validated records | that record durable | per furthest valid | never | consumed | fail closed at prior valid record |
| SAME_SEQUENCE_FORK | prior chain | which fork is authentic | no | never | consumed | SAME_SEQUENCE_FORK (fail closed, flag) |
| Broken predecessor hash / sequence gap | records before break/gap | records past it | no | never | consumed | BROKEN_LINK / SEQUENCE_GAP (fail closed) |
| Contradictory primary vs emergency | conservative subset | the disputed fact | no until resolved | never | consumed | CONTRADICTORY_EVIDENCE (fail closed, flag) |

In every consumed row, authority remains consumed, all retained evidence (including debris and orphan bundles) is preserved, and scientific execution never resumes.

---

## 12. Publication semantics

Provisional architecture decision (pending §16): **publication is a downstream projection of the authoritative durable scientific result**, where the authoritative result is the verified `IMMUTABLE_SCIENTIFIC_BUNDLE` + valid linked `SCIENTIFIC_COMPLETION` receipt. Publication does not create or alter scientific truth.

```text
PUB1  Publication begins only after a verified, linked bundle+receipt pair exists (P3). Never after only a bundle write; never after only a receipt write.
PUB2  Publication projects the exact committed bundle bytes into publication artifacts; staging/final separation is retained, but the scientific result no longer depends on that promotion.
PUB3  Publication is idempotent: re-projecting the same committed bundle yields byte-identical artifacts.
PUB4  Publication failure records PUBLICATION_ATTEMPTED without PUBLICATION_COMPLETED, leaves the completion pair untouched, and never re-runs computation.
PUB5  A PUBLICATION_COMPLETED record is itself a durable record in the primary chain.
```

Publication recovery is provisionally permitted **only** through a separately controlled and separately authorized **publication-only process**. It is not automatic, not scientific execution, not execution recovery, not authorization reuse, not manifest contact, and not recomputation. The publication-only process must be architecturally **incapable** of:

```text
importing or invoking the scientific descriptor
contacting the manifest
changing fixtures
changing thresholds or tolerances
constructing a new result kind
altering the scientific bundle
creating a primary SCIENTIFIC_COMPLETION record
opening a new scientific execution
```

It may **only**: verify the existing bundle and receipt, project the exact committed bytes, verify the projected bytes, and write publication-attempt/completion evidence. This publication-recovery rule is flagged provisional pending Hilmir's confirmation before any implementation authorization.

---

## 13. Fault-injection requirements

A future test matrix (to be built under a new lineage; not authorized here) must inject failure at every durable operation and assert deterministic, fail-closed behavior. Injected operations:

```text
file creation, exclusive creation, write, flush, file fsync, close, rename, replace, target read-back,
canonical byte comparison, directory fsync/durability, hash calculation, serialization,
emergency-evidence creation, emergency-evidence write, publication-directory creation,
publication-file creation, publication verification, terminal-record creation
```

Injection timings (each operation): pre-operation failure; partial write; post-write/pre-sync failure; post-sync/pre-read-back failure; successful operation followed by process crash; duplicate operation attempt; stale temporary/candidate object; unexpected existing immutable object; hash mismatch; sequence mismatch; contradictory channel evidence.

Added mandatory cases (correction 14):

```text
immutable-bundle exclusive-create failure
partial immutable-bundle write
bundle file fsync failure
bundle read-back failure
bundle byte mismatch
bundle hash mismatch
bundle directory-durability failure
orphan valid bundle (no receipt)
torn bundle object
completion receipt with absent bundle
completion receipt with mismatched bundle
completion receipt write failure
emergency observed-uncommitted capture (success path)
emergency capture failure
authority-consumption-attempt failure
forced process kill where emergency code cannot run
interpreter crash
host crash or simulated abrupt durability loss
same-sequence identical duplicate
same-sequence different-record fork
cross-execution replay
cross-authorization replay
publication-only recovery
publication-only utility attempting a prohibited science import (must be structurally impossible)
Windows directory-durability adapter behavior
```

Every test must confirm:

```text
no automatic authority reuse
no repeated manifest contact
no repeated scientific execution
no publication before a verified bundle+receipt pair
no promotion of EMERGENCY_OBSERVED_UNCOMMITTED evidence into primary truth
deterministic fail-closed classification
the emergency channel does not share the failed primary mechanism (independence itself is tested)
```

The fault-injection harness must be isolated from external subprocess churn, so the v0.2-class pytest/git Windows access-violation (a harness/toolchain anomaly, not an authoritative-path defect) can never be confused with an authoritative durability failure, or vice versa.

---

## 14. Security analysis

Mapping to threats and the v0.2 defects:

```text
Silent authority reuse         -> A1–A3, A7, C2: three-state authority + identity binding; ATTEMPT_FAILED closes against reuse.
Silent manifest re-contact      -> M1/M4: attempt recorded durably before read; cap enforced against durable count across crashes.
Silent recomputation            -> global rule + A3/A6: absence of a completion pair => classify and stop, never recompute.
Publication before completion    -> P3/PUB1: publication gated on a verified bundle+receipt pair.
Result loss at the gate (D2)     -> S1–S6: full canonical bytes durable in the immutable bundle BEFORE publication, on a mechanism independent of the gate.
Single-pointer/replace fragility -> §7/§9: no mutable pointer, no replace; state derived by byte-validating candidates.
Shared primary/emergency path    -> §10/§12 independence (layered, bounded); T2–T4 arbitration.
Tamper / silent edits            -> C1/C4: canonical bytes + self-hash + predecessor link make edits, reorders, and forks detectable.
Forks / replay                   -> §11 fail-closed rules; §9 candidate handling.
Contradictory evidence           -> T4/§10: fail closed, flag, never silently reconcile.
```

Security identity binding is concrete, not metaphysical: a primary scientific record is accepted only when bound to execution identity, authorization identity, protocol/schema identity, sequence, predecessor record hash, record kind, record/content hash, and a writer/attempt identity. The writer/attempt identity is anti-ambiguity metadata; no observer-theory, quantum, or metaphysical identity is used as a security requirement.

Fail-closed is the default disposition of every ambiguity: gap, broken link, fork, duplicate, orphan bundle, invalid completion, or contradiction all resolve to the most conservative interpretation and stop. Residual: no on-host architecture guarantees durability against whole-directory/volume loss, host crash, or power loss; the dual channel provides mechanism diversity, not volume/host/power-loss independence (§12). What the architecture can guarantee is that no single injected fault silently violates the authority, contact, recomputation, or publication-ordering invariants, and that whatever survives is interpretable and fail-closed.

---

## 15. Remaining risks

```text
R1  Whole-directory / whole-volume / host / power-loss events defeat on-host evidence; the dual channel bounds, not eliminates, this.
R2  Windows directory-entry durability is unresolved; without a validated primitive/adapter, per-record durability is weaker than intended.
R3  A pre-opened emergency descriptor helps only while process/exception handling is alive; it cannot survive kill/interpreter/host/power loss.
R4  Candidate-object validation (self-hash + predecessor link) is load-bearing; torn/empty/forked candidates must be fault-injected.
R5  More per-record directory-durability operations increase the aggregate failure surface; measure under fault on the authoritative environment.
R6  The state-model questions (publication as projection vs. authoritative transition; the pair as THE result) are foundational and unresolved (§16).
R7  Fault-injection completeness is itself a risk: an un-injected transition is an unproven transition.
R8  Emergency-capsule bounding could truncate the one detail that would explain a future failure; choose the budget deliberately and retain original-length metadata.
R9  No design removes infrastructure failure; the goal is bounded, interpretable, fail-closed loss — not zero failure.
R10 Same-volume emergency independence is mechanism diversity only; it must not be described as volume/host/power independence.
```

---

## 16. Decisions requiring Hilmir

Conceptual/state-model decisions, treated as architecture prompts only (never as proofs, never as security requirements):

```text
H1  Is publication a PROJECTION of an already-authoritative result, or a SEPARATE AUTHORITATIVE STATE TRANSITION?
    The corrected design treats it as a projection (§12). If publication is authoritative, the pair alone would not be THE result and the model changes.
H2  Is the verified IMMUTABLE_SCIENTIFIC_BUNDLE + linked SCIENTIFIC_COMPLETION receipt THE authoritative result, with publication a copy/projection? (Provisional: yes.)
H3  Where is the observer/evidence boundary? Provisionally: at the verified pair (§8b), and nowhere earlier.
H4  Is publication RESUME permitted at all after a crash, or is a crashed publication itself terminal (leaving a durable, complete-but-unpublished result)?
H5  Contradiction policy: confirm fail-closed-and-flag (never silent reconciliation) as the intended operator semantics for primary/emergency disagreement.
```

These change what "the result" *is*; they are flagged for Hilmir before implementation. They are not engineering details and are not resolved here.

---

## 17. Implementation-readiness verdict

```text
B. IMPLEMENTATION_READY_WITH_NAMED_DECISIONS
```

with the explicit qualification:

```text
This corrected draft is NOT YET IMPLEMENTATION-READY.
It becomes implementation-ready only after this corrected architecture is independently reviewed and accepted,
and the named pre-implementation decisions below are settled. No implementation is authorized by this document.
```

Named pre-implementation decisions:

```text
Architectural (resolve before build):
  - final IMMUTABLE_SCIENTIFIC_BUNDLE object schema
  - final SCIENTIFIC_COMPLETION receipt schema
  - unique immutable write-attempt / content-addressed file-naming model
  - same-sequence duplicate and SAME_SEQUENCE_FORK rules (confirm §9/§11)
  - authority-consumption-attempt closure semantics (confirm §5.1 / AUTHORITY_CLOSED_UNEXERCISED...)
  - Windows directory-durability mechanism (primitive and/or scoped adapter; §9)
  - emergency capsule fixed format and bounding policy (§10)
  - publication-recovery authorization policy (publication-only process; §12/§13)
  - complete fault-injection matrix (§13)

Test-design:
  - instantiation of the full fault-injection matrix and its isolation from subprocess churn
  - mechanical assertion of emergency-channel independence (layered; §12)
  - replay tests for torn/empty/fork/duplicate/gap/broken-link/contradiction/cross-identity replay

Operator-policy:
  - whether publication resume after crash is operationally permitted (couples to H4)
  - retention/labeling policy for orphan bundles, forensic debris, and contradiction flags

Conceptual (require Hilmir; §16):
  - H1/H2 publication-as-projection vs authoritative-transition; the pair as THE result
  - H3 observer/evidence boundary location
  - H4 publication-resume permissibility
  - H5 fail-closed-and-flag contradiction policy
```

Implementation must not begin until the architectural and conceptual decisions are settled and this corrected architecture is independently accepted.

---

## 18. Non-authorizations and preserved boundaries

This document creates no authority and changes nothing. It does not authorize or recommend enacting:

```text
implementation of the v0.3 protocol            execution or invocation of any runner
manifest contact                               scientific rerun or recomputation
publication of any result                      automatic publication
evidence repair, rename, deletion, promotion, or terminalization
reconstruction of the v0.2 scientific verdict  a v0.2 retry
PsiTRS contact                                 historical F3 reinterpretation
production-kernel modification                 live Brainvision integration
memory-system integration                      live capture or ingestion
service/runtime integration                    threshold or tolerance tuning
majority-rule rescue                           scientific rescue
production claims                              a new one-run authorization
```

Preserved:

```text
docs-only; no implementation, execution, manifest-contact, or publication authority
FORMAL_HOLD = active
Mode 0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
Brainvision remains offline and quarantined under research/brainvision/
v0.2 is consumed, terminal, and immutable; any future evaluation is a NEW lineage with new identities, tests,
  specification, review, and a separate one-run authorization — never a retry.
```

Scientific result taxonomy (correction 10): the two valid scientific outcomes are exactly

```text
scientific_result_kind = SYNTHETIC_GATE_PASSED
scientific_result_kind = SYNTHETIC_GATE_FAILED
```

and `completion_validity`, `execution_failure_kind`, and `terminal_classification` are separate fields/record-classes. A scientifically invalid, incomplete, contradictory, or infrastructure-failed execution must not produce a valid `SCIENTIFIC_COMPLETION` receipt. This document does not state or imply which of the two valid result kinds occurred during v0.2; that result is not durably available and must not be reconstructed.

Scientific claim boundary, restated and not crossed anywhere in this document:

```text
two complete scientific passes occurred
the two canonical pass bundles were byte-identical
the unpublished result kind is not durably available
the v0.2 result must not be reconstructed
```

*End of corrected replacement draft v0.1. Docs-only. No repository change, execution, manifest access, or scientific reconstruction was performed in producing this review.*
