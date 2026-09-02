# TORMENT Memory Substrate Phase 9C-R1 — B4C Zero-Member Motif Projection v0.1

## Status and authority

```text
DOCUMENT_KIND = QUALIFICATION_RECORD
PHASE_9C_R1 = PASS
B4C_FORMAT_MECHANISM_QUALIFIED = YES
REAL_ROOT_ZERO_MEMBER_B4C_ELIGIBILITY = NOT_YET_ADMINISTERED

REAL_ROOT_CONTACT = NO
REAL_MEMORY_MODEL_CONTACT = 0
REAL_REEMBED_OPERATIONS = 0
LIVE_SERVICE = NO
BRAINVISION_FILES_READ = 0
BRAINVISION_FILES_TOUCHED = 0
KERNEL_FILES_CHANGED = 0
```

This is a synthetic, offline qualification of one narrow migration capability.
It neither classifies a real root's motifs nor authorizes admission, cutover,
re-embedding, service startup, provider contact, or public runtime selection.

R0 remains the semantic authority.  B4C implements only its Z1 disposition:
an already-admitted historical motif with exactly zero current members may be
imported as an active native aggregate only when its aggregate geometry is
explicitly proven to belong to the target lane.

```text
ZERO_MEMBER_LEGACY_SEMANTICS = HISTORICAL_BUT_SUPPORTED_ACTIVE_AGGREGATE_STATE
TARGET_COMPATIBLE_ZERO_MEMBER_DISPOSITION = ACTIVE_IMPORT
NON_TARGET_ZERO_MEMBER_DISPOSITION = BLOCK
UNKNOWN_ZERO_MEMBER_DISPOSITION = BLOCK
```

## B4C persistence and provenance boundary

`NativeMotifService` remains the only motif persistence owner.  It now owns a
separate `publish_migration_zero_member_baseline()` primitive.  The ordinary
`create_motif_with_member()` contract was not broadened and remains the only
ordinary native motif-birth path.

The exceptional primitive requires all of the following before it begins a
semantic transaction:

- the exact core identity is `STAGING`;
- deployment authority is exactly `LEGACY_ACTIVE` with no referenced core;
- one complete `MotifState` and a zero-member migration evidence object;
- the declared source member count is exactly zero;
- referenced namespaces and target semantic scope exist; and
- a B4C source coordinator revalidates its prepared source facts after
  `BEGIN IMMEDIATE` and before the motif is published.

The service publishes exactly one `DERIVED_MOTIF` R1, one target-scoped
`MOTIF_ID` alias, one B4C transition/object effect, and one B4C object output.
It publishes no `MOTIF_MEMBERSHIP` object, relationship output, or
relationship effect.  Its operation and transition identity are both:

```text
MIGRATION_RUNTIME_ZERO_MEMBER_MOTIF_PROJECTION
```

This topology is distinct from ordinary motif creation, a failed partial
publication, and B4A/B4B baseline projection.  The canonical idempotent
intent binds:

```text
source snapshot and source namespace
source motif object / R1 / operation / transition
source motif artifact and workspace-metadata artifact digests
runtime motif ID, domain scope, motif/alias/membership namespaces
source provider / model / dimension
target provider / model / dimension / representation class / generation /
    derivation contract / encoding / dtype
source-state digest and zero-membership-evidence digest
```

No migration module writes motif objects, revisions, aliases, transitions, or
operation outputs directly.  B4C only reads and qualifies source evidence,
then calls the existing motif persistence service.

```text
NEW_MOTIF_PERSISTENCE_ENGINE = NO
ORDINARY_NATIVE_MOTIF_CREATION_REQUIRES_FIRST_MEMBER = YES
FAKE_MEMBER = NO
FAKE_EID = NO
FAKE_VECTOR = NO
```

## Source and target-compatibility contract

B4C reuses B4A's exact admitted-source motif identity and topology reader.
It then adds a distinct zero-member proof:

```text
raw current members list = []
source operation outputs = exactly the source motif object output
source membership outputs = 0
source membership effects = 0
source-created membership relationships = 0
```

The target proof compares the persisted workspace geometry witness with the
complete target lane.  The source provider, model, and dimension must equal
the target provider, model, and dimension; the target lane additionally must
be the already-qualified `COMPAT_EMBEDDING / 1 / compat-embedding-v1 /
RAW_VECTOR / float32` identity.  The source centroid must have the exact
target dimension.

For the selected production profile this means:

```text
st / BAAI/bge-small-en-v1.5 / 384
```

No centroid is re-derived.  No hash or unknown centroid is promoted.  No
label, domain, or contributor text becomes embedding input.

The target-compatible aggregate is copied exactly, including runtime motif ID,
domain, label, centroid, strength, stability, contributors, timestamps,
derivation metadata, and allowed non-structural payload fields.  The only
current membership count is zero, represented by the absence of relationship
truth rather than a duplicated payload field.

```text
CENTROID_RECOMPUTED = NO
HASH_CENTROID_PROMOTION_TO_ST_BGE = NO
UNKNOWN_CENTROID_PROMOTION = NO
LABEL_REEMBED_AS_MOTIF_CENTROID = NO
NEW_MOTIF_REGEOMETRY_ENGINE = NO
```

## Reader law and future native behavior

`NativeMotifRuntimeReader` now recognizes a zero-member result only when the
motif's creating transition has the exact B4C operation/transition identity,
one matching R1 object output/effect, no baseline relationship publication,
and a complete canonical B4C evidence record whose R1 state digest, scope,
runtime ID, source lane, and target lane agree.

An ordinary `DERIVED_MOTIF` with no membership evidence is refused.  A B4A or
B4B projection with a missing baseline member remains refused by its existing
baseline validator.  A malformed or partial B4C topology is also refused.
The reader does not accept an empty membership query unconditionally.

After a certified B4C baseline, an ordinary native attach remains ordinary:

```text
B4C member_count = 0
existing decide_attach_or_create() = selected
existing realize_attach_next_state() = successor aggregate
existing NativeMotifService.add_motif_member() = first relationship publication
subsequent member_count = 1
```

No empty-mode branch was added to decision math.  Synthetic qualification
confirmed existing zero density, preserved strength/stability gravity, normal
centroid participation in domain geometry, normal attach selection, and the
first future member's R2/add-member topology.

## Qualification matrix

| Case | Result |
|---|---|
| Exact target-compatible zero-member source | `PASS`: one active native R1, alias, zero relationships, exact aggregate preservation |
| Same request retry | `PASS`: durable idempotent result recovery |
| Lost response after commit | `PASS`: exact result recovered from the semantic operation |
| Changed request under existing key | `REFUSED`: idempotency conflict |
| Source aggregate drift | `REFUSED`: frozen-snapshot integrity boundary blocks reuse |
| Source members change from `[]` | `REFUSED`: frozen-snapshot integrity boundary blocks reuse |
| Wrong provider at same dimension | `REFUSED` |
| Wrong model at same dimension | `REFUSED` |
| Hash-space source identity | `REFUSED` |
| Unknown source identity | `REFUSED` |
| Missing/malformed workspace target witness | `REFUSED` |
| Active core / non-legacy-active deployment | `REFUSED` before publication |
| Corrupt ordinary zero-member native motif | `REFUSED` by runtime reader |
| Corrupt B4C transition missing R1 effect | `REFUSED` by runtime reader |
| B4A empty-member request | `STILL REFUSED` |
| B4B empty-member request | `STILL REFUSED` |

## Regression and offline evidence

All test runs used the explicit conda interpreter and file-backed temporary
SQLite roots only.  Each run was preceded by a port-8787 listener check with
no listener present.  Pytest cache was disabled for the passing runs.

```text
tests/test_substrate_migration_runtime_zero_member_motif_projection.py = 14 passed
tests/test_substrate_migration_runtime_motif_projection.py = included in 22 passed
tests/test_substrate_migration_runtime_motif_regeometry_projection.py = included in 22 passed
tests/test_substrate_native_motif_runtime_reader.py = included in 22 passed
tests/test_substrate_native_motifs.py = 14 passed

PORT_8787_LISTENER_BEFORE = NO
SELECTED_NETWORK_CAPABLE_TESTS = 0
NETWORK = NONE
LIVE_SERVICE = NONE
```

The B4A regression file contains one existing `subprocess` fresh-interpreter
restart assertion.  Its inline program opens only the synthetic SQLite test
database and imports native substrate readers; static inspection found no
HTTP client, URL, listener, service startup, provider, or real-root path.

## Phase 9C resumption contract

```text
SUPPORTED_ROOT_NORMALIZATION = PASS
    only when a real-root motif is separately administered as exact target-compatible
    under this mechanism

INCOMPATIBLE_EMPTY_MOTIF_ROOT = FAIL_CLOSED_AS_DESIGNED
    B4C refuses hash, unknown, or otherwise non-target geometry

REAL_ROOT_ZERO_MEMBER_B4C_ELIGIBILITY = NOT_YET_ADMINISTERED
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

Phase 9C may resume its synthetic/root-contract work with B4C as the lawful
Z1 path.  A root containing unsupported hash or unknown empty motifs is not a
B4C implementation defect: root completion must refuse without invented
geometry.  Any real production action remains separately gated by an actual
root's lawful per-motif disposition.
