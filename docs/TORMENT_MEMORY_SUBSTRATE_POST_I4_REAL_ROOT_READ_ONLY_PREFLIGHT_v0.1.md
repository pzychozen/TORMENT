# TORMENT Memory Substrate — Post-I4 Real-Root Read-Only Prefight v0.1

**Status:** `READ_ONLY_CHARACTERIZATION`

**Admission authority:** `NOT_ADMISSION_EVIDENCE`

**Writer state:** `NO_WRITER_FREEZE`

**Activation authority:** `NO_REAL_ACTIVATION_AUTHORIZATION`

## Purpose and authority boundary

This document records an observational characterization of the production data
root after the explicit `REAL_ROOT_READ_ONLY_CONTACT = YES` gate.  It is not a
snapshot, source manifest, writer-freeze witness, admission record, or runtime
activation authorization.

The resolved root was:

```text
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data
```

Only directory names, path structure, file existence, stat metadata, and the
minimum JSON metadata/field presence needed for this report were read.  No
service was started; no `TormentFabric` was constructed; no REST endpoint,
provider, model, network, or SQLite database was opened; and no data-root file
was created, modified, moved, or deleted.

## Q1 — current materialized census

`discover_canonical_root_layout` was invoked as its documented pure
directory-identity discoverer against the resolved root.  It found:

| Measure | Observed |
| --- | ---: |
| Workspaces | 51 |
| Materialized private scopes | 76 |
| Materialized shared scopes | 48 |
| Total materialized scopes | 124 |
| Private scopes per workspace | 41 with 1; 7 with 5; 3 with 0 |
| Shared scopes per workspace | 44 with 1; 1 with 4; 6 with 0 |

The historical approximately `50 / 75 / 44 / 119` census is therefore not
current: the root now has one additional workspace, one additional private
scope, four additional shared scopes, and five additional total scopes.

`data/lived_use/...` contains nested alternate runtime basins selected by
their own `TORMENT_DATA_DIR` launchers.  They are not children of the selected
root's `workspaces/` canonical layout and were not included in this census.

## Q2 — public-topology compatibility

The current qualified root-v2 public topology requires every served workspace
to have exactly one private scope and at least one shared scope.  On the full
discovered root:

| Classification | Workspaces |
| --- | ---: |
| Matches the qualified shape | 38 |
| Outside the qualified shape | 13 |
| Has multiple private scopes | 7 |
| Has no private scope | 3 |
| Has no shared scope | 6 |

The category counts intentionally overlap.  In particular, raw materialized
private scopes are not silently treated as publicly required runtime scopes.
There is no fresh frozen runtime-scope plan that could lawfully narrow the
full-root preflight to a smaller served subset.  Consequently the full real
root **does not match** the current qualified public topology; this is a
pre-admission blocker, not evidence for a topology rewrite.

## Q3 — RootScopeKey identity

All 124 full `(workspace, kind, qualifier)` keys are unique.  No qualifier is
missing.  Eight private qualifier labels are reused across workspaces (67
occurrences total) and three shared qualifier labels are reused across
workspaces (45 occurrences total); that reuse is permitted because the full
RootScopeKey is unique.  No private/shared qualifier-label overlap was found.

## Q4–Q5 — representation census and demand

Only compact embedding manifests and workspace metadata were read; vectors
were not loaded.  The observed representation groups are:

| Provider / model / dimension / storage | Scope count | Disposition demand |
| --- | ---: | --- |
| `st` / `BAAI/bge-small-en-v1.5` / 384 / `float32` NPY | 71 | target-compatible raw vector |
| `hash` / `hash:384:torment` / 384 / `float32` NPY | 50 | requires future normalization/rematerialization |
| metadata or manifest absent | 3 | unknown; identify or explicitly refuse under freeze |

All 121 manifested scopes report the current compact numeric NPY form and
`float32`; target compatibility is based on the persisted provider, model, and
dimension identity and does not load BGE.  The historical representation count
changed from approximately `66 ST / 50 hash / 3 unknown` to `71 / 50 / 3`.

## Q6 — root-v2 layout expressibility

All 124 discoverable materialized scopes are expressible by the generalized
canonical root-v2 discovery layout.  Existing source semantics bind supported
workspaces under `data/workspaces/<workspace>/...`; the nested `lived_use`
basins are alternate selected roots, not implicit workspace children.

Two top-level legacy residual artifacts (`nodes.jsonl` and `emb_1.npy`) exist
outside `workspaces/`.  They are not a discoverable workspace/scope and are
not a supported canonical agent path under the current root-v2 layout.  They
were not parsed or admitted.  A future frozen manifest must explicitly record
their exclusion or give them a separately authorized disposition; they cannot
be silently absorbed into a scoped admission.

## Q7–Q8 — external-owner observation and frozen dispositions

The following durable external-owner classes were found structurally.  Counts
are existence counts, not semantic-state counts.

| Owner/state class | Structural observation | Frozen future disposition |
| --- | --- | --- |
| Character | 36 `character_state.json`; seed/identity artifacts present | recompute target baseline; retain drift history and seed |
| Conflict | 2 conflict logs | no geometry disposition required |
| RoleStore | 73 role stores | no geometry disposition required |
| Affect | 2 affect stores | no geometry disposition required |
| Symbols | 66 symbol stores | no geometry disposition required |
| Proposal registry | 6 registry files; 12 records | retain with consumer guard |
| Bridge registry | absent | retain if later observed |
| Hivemind / collective | 7 collective directories | retain historical scores |
| Trajectory | 10 private and 13 shared trajectory directories | retain |
| Checkpoint | 2 persisted checkpoint files | reinitialize calibration only |
| Deep memory | no deep-memory artifact path observed | disabled posture remains applicable |
| Archive | 21 archive directories with vector artifacts | retain untouched and disabled |
| Identity / anchors | 88 identity files and 39 anchor files | no geometry disposition required |

`memory_index.sqlite` files are explicitly documented derived indexes and
`feedback_events.jsonl` as an append-only causal-tracing audit; neither was
opened and neither is a newly observed external semantic owner class.  Motif
and core graph artifacts remain scoped core evidence rather than independent
external owners.

No unclassified geometry-derived external owner state was observed.  The two
unscoped top-level legacy core residual artifacts noted in Q6 remain outside
this owner census and require explicit manifest disposition before any future
admission.

## Q9 — Character readiness

All 36 persisted CharacterState artifacts structurally contain the required
field names: `distance_to_seed`, `drift_direction`, `seed_id`, and
`drift_history`.  Values were neither recomputed nor reported.  The future
Character disposition is structurally expressible: baseline geometry can be
recomputed while seed identity and historical drift evidence remain retained.

## Q10 — checkpoint readiness

Two persisted checkpoint artifacts exist at the canonical
`agents/<agent>/private/checkpoints/` location.  No artifact named as a
separate calibration store was found.  The observed checkpoint state is
structurally covered by the future `REINITIALIZE_CALIBRATION_ONLY` disposition;
no checkpoint was restored or executed.

## Q11 — proposal raw-vector hazard

There are 12 persisted ShareProposal records in six registries.  The current
ShareProposal schema stores `embedding` but no representation-identity fields;
therefore all 12 have unidentified vector geometry.  No proposal text or
other semantic content was exposed.  The configured initial native profile's
consumer-refusal posture must remain enforced, then be re-attested under a
fresh freeze before any real admission.

## Q12–Q13 — deep/archive and compression posture

No deep-memory artifacts were observed.  Archive vector artifacts are present
in 21 `memory_archive` lanes and remain `RETAIN_UNTOUCHED_AND_DISABLED` for
the first profile.  Source-policy compatibility supports an initial native
profile with `compression_enabled = false`; this is a future-profile
compatibility observation and did not alter a legacy feature.

## Q14 — bounded writer activity observation

A non-interfering five-second comparison of `st_mtime_ns` over 2,869 entries
under canonical `data/workspaces/` observed zero mtime changes.  This is only
`NOT_OBSERVED_DURING_BOUNDED_PREFLIGHT`; it is explicitly **not** a writer
freeze, immutable snapshot, or admission witness.

## Q15 — requirements for a separately authorized writer-freeze phase

Before an admission preflight, a separate authorization must obtain all of:

1. A root writer-freeze witness covering the declared production root and
   selected runtime scope plan.
2. A fresh discovered census and fresh declared census taken during that
   frozen epoch.
3. A fresh explicit source manifest, including an explicit disposition for
   unscoped top-level legacy residual artifacts and any excluded alternate
   roots.
4. A fresh representation census, with the three unknown scopes either
   identified or refused and the 50 hash scopes assigned a lawful
   normalization/rematerialization plan.
5. A fresh external-owner observation digest and confirmation of every
   owner-specific frozen disposition.
6. An explicit runtime-scope plan resolving the 13-workspace public-topology
   mismatch; it must distinguish materialized scopes from publicly required
   private runtime scopes.
7. A qualified production profile that preserves proposal consumer refusal,
   deep-memory disablement, archive refusal, and initial compression disabled.
8. A separately authorized real admission, real normalization where required,
   and later P6/P7 activation decisions.  No legacy retirement is implied.

## Q16 — current P0 / preactivation gate ledger

| Gate | Current classification |
| --- | --- |
| Root topology expressibility | `OBSERVATIONALLY_MATCHES_BUT_REQUIRES_FROZEN_EPOCH_EVIDENCE` |
| Public topology compatibility | `BLOCKED_BY_REAL_ROOT_MISMATCH` |
| Representation target compatibility | `OPEN_REAL_ROOT_GATE` |
| Normalization requirement | `OPEN_REAL_ROOT_GATE` |
| RootScopeKey identity | `OBSERVATIONALLY_MATCHES_BUT_REQUIRES_FROZEN_EPOCH_EVIDENCE` |
| External-owner census | `OBSERVATIONALLY_MATCHES_BUT_REQUIRES_FROZEN_EPOCH_EVIDENCE` |
| Geometry disposition coverage | `OBSERVATIONALLY_MATCHES_BUT_REQUIRES_FROZEN_EPOCH_EVIDENCE` |
| Character disposition applicability | `OBSERVATIONALLY_MATCHES_BUT_REQUIRES_FROZEN_EPOCH_EVIDENCE` |
| Deep-memory disabled posture | `CLOSED_BY_EXISTING_QUALIFICATION` |
| Compression-disabled posture | `CLOSED_BY_EXISTING_QUALIFICATION` |
| Fresh frozen census | `OPEN_REAL_ROOT_GATE` |
| Fresh source manifest | `OPEN_REAL_ROOT_GATE` |
| Root writer freeze | `REAL_OPERATION_REQUIRING_SEPARATE_AUTHORIZATION` |
| Real admission | `REAL_OPERATION_REQUIRING_SEPARATE_AUTHORIZATION` |
| Real normalization | `REAL_OPERATION_REQUIRING_SEPARATE_AUTHORIZATION` |
| P6 activation | `REAL_OPERATION_REQUIRING_SEPARATE_AUTHORIZATION` |
| P7 activation | `REAL_OPERATION_REQUIRING_SEPARATE_AUTHORIZATION` |
| Legacy retirement | `REAL_OPERATION_REQUIRING_SEPARATE_AUTHORIZATION` |

## Required status ledger

```text
REAL_ROOT_READ_ONLY_PREFLIGHT = PASS
RESOLVED_REAL_ROOT = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data
REAL_ROOT_READ_CONTACT = YES
REAL_ROOT_WRITE_CONTACT = NONE
WRITER_FREEZE = NOT_PERFORMED
SERVICE_STARTED = NO

WORKSPACES = 51
MATERIALIZED_PRIVATE_SCOPES = 76
MATERIALIZED_SHARED_SCOPES = 48
TOTAL_MATERIALIZED_SCOPES = 124
REAL_ROOT_PUBLIC_TOPOLOGY = DOES_NOT_MATCH_CURRENT_QUALIFIED_PROFILE
FULL_ROOT_SCOPE_KEY_UNIQUENESS = PASS

TARGET_ST_BGE_384_SCOPES = 71
NON_TARGET_SCOPES = 50
UNKNOWN_REPRESENTATION_SCOPES = 3
SCOPES_REQUIRING_NORMALIZATION = 50
ROOT_V2_LAYOUT_EXPRESSIBILITY = YES

EXTERNAL_OWNER_CLASSES_PRESENT = Character, conflicts, RoleStore, affect, symbols, proposal registry, Hivemind/collective, trajectory, checkpoint, archive, identity/anchors
UNCLASSIFIED_DURABLE_OWNER_STATE = NONE_OBSERVED_IN_EXTERNAL_OWNER_CENSUS; TWO_UNSCOPED_LEGACY_CORE_RESIDUAL_ARTIFACTS_REQUIRE_MANIFEST_DISPOSITION
REAL_OWNER_STATE_COVERED_BY_FROZEN_DISPOSITION_TABLE = YES
CHARACTER_DISPOSITION_STRUCTURALLY_APPLICABLE = YES
CHECKPOINT_CALIBRATION_STATE_PRESENT = YES
CHECKPOINT_DISPOSITION_STRUCTURALLY_APPLICABLE = YES

PROPOSAL_RECORDS_PRESENT = 12
PROPOSAL_RECORDS_WITH_UNIDENTIFIED_VECTOR_GEOMETRY = 12
DEEP_MEMORY_ARTIFACTS_PRESENT = NO
ARCHIVE_VECTOR_ARTIFACTS_PRESENT = YES
INITIAL_NATIVE_COMPRESSION_DISABLED_PROFILE_STILL_EXPRESSIBLE = YES
CURRENT_WRITER_ACTIVITY = NOT_OBSERVED_DURING_BOUNDED_PREFLIGHT
HISTORICAL_CENSUS_STILL_CURRENT = NO

FRESH_WRITER_FREEZE_REQUIRED_BEFORE_ADMISSION = YES
FRESH_MANIFEST_REQUIRED = YES
FRESH_EXTERNAL_OWNER_OBSERVATIONS_REQUIRED = YES
REAL_ROOT_ADMISSION_READY = NO
REAL_ROOT_ACTIVATION_READY = NO
REAL_PRODUCTION_ACTIVATION_AUTHORIZED = NO

PRODUCTION_CODE_CHANGES = 0
TEST_CODE_CHANGES = 0
TESTS_RUN = 0
CLAUDE_ADVERSARIAL_REVIEW_REQUIRED = NO
BRAINVISION_OPENED = NO
SECOND_COGNITIVE_FUNCTION_INSPECTED = NO
TORMENT_MATHEMATICS_CHANGED = NO
```

## Conclusion

The real-root read-only characterization passed, but it does not authorize
real admission or activation.  The exact remaining gates are: separately
authorized writer freeze; frozen fresh census; frozen explicit source
manifest; frozen external-owner digest and disposition attestation; an
explicit runtime-scope plan resolving public-topology mismatch; representation
identification/refusal for three unknown scopes; lawful handling of 50 hash
scopes; proposal consumer-refusal attestation; qualified production profile;
then separately authorized real admission, any real normalization, P6/P7
activation, and only later any legacy-retirement decision.
