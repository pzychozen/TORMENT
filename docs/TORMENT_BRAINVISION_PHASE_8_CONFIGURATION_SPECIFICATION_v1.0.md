# TORMENT Brainvision Phase 8 Configuration Specification v1.0

## Status and authority

**FROZEN PRE-IMPLEMENTATION PHASE-8 SPECIFICATION**

Phase 8 freezes Brainvision configuration representation, validation, canonical
serialization, safe contained configuration paths, atomic configuration-file
primitives, and exact configuration-field compatibility checks. It does not
implement recursive VHE sidecar persistence, Fabric lifecycle transitions,
direct visual ingress, or any Phase-9 or Phase-10 behavior. It does not reopen
Phases 0-7.

Phase-7 modulation mathematics, implementation, and formal result remain
closed. Phase-8 configuration records the selected frozen modulation profile.
It does not derive a profile from CharacterSeed or any other TORMENT subsystem.

## 1. Ownership boundary

Phase 8 owns:

1. Brainvision configuration DTO/schema.
2. Strict parse and validation.
3. Canonical serialization.
4. Safe contained configuration-path derivation.
5. Atomic configuration-file read/write primitives.
6. Exact configuration-field compatibility checks.

Phase 9 owns:

1. Recursive VHE sidecar schema.
2. F/S/R persistence.
3. Committed active visual time.
4. Sidecar source-sequence copy.
5. Bit-exact continuation encoding.

Phase 10 owns:

1. Configuration creation/deletion authorization.
2. Lifecycle transition authorization.
3. Enable/suspend/resume/reset/disable orchestration.
4. Known-agent proof.
5. Per-agent locking.
6. Sidecar/config transaction ordering.
7. Recovery-matrix execution.
8. Runtime allocation/deallocation.

Phase-8 persistence primitives are mechanical only. They must not decide
whether a lifecycle transition, reconfiguration, or configuration deletion is
authorized.

## 2. Storage location and path boundary

The sole v1a configuration artifact path is:

~~~text
<data_root>/workspaces/<workspace_id>/agents/<agent_id>/brainvision/configuration.json
~~~

Dynamic workspace_id and agent_id path components must pass existing strict
path-safety validation and final resolved-path containment checks. Path
derivation and configuration read must not create directories or files.

A low-level authorized write may create only the Brainvision-owned brainvision
leaf directory required for configuration.json. This does not establish that an
ordinary TORMENT agent exists. Phase 10 must establish known-agent existence
before using a Phase-8 write primitive in a production lifecycle flow.

## 3. Configuration schema

The exact, complete v1 configuration field set is:

~~~text
schema_id
lifecycle_status
stream_identity
adapter_contract_id
last_accepted_source_sequence
expected_operator_id
expected_projection_id
modulation_schema_id
modulation_mapping_id
modulation_profile_schema_id
theta
modulation_profile_id
~~~

No convenience fields are admitted. Configuration contains no VHE state, active
visual time, sidecar state, adapter ID, observation ID, capture time,
confidence, semantic event, world event, CharacterSeed, CharacterState, native
checkpoint content, memory content, or Fabric runtime state.

The fixed schema identity is:

~~~text
brainvision.configuration.v1
~~~

No persisted content-hash or content-derived configuration ID is added in v1a.
The artifact legitimately changes as lifecycle status and replay watermark
change. Compatibility is established by strict schema validation and the
individually frozen continuation identities.

## 4. Lifecycle status

The closed exact lifecycle-status vocabulary is:

~~~text
disabled
active
suspended
~~~

Reset is an operation, not a lifecycle status. There are no defaults, case
folding, aliases, or coercions.

A disabled configuration is fully populated. It retains stream identity,
adapter-contract identity, replay watermark, base identities, modulation
identities, theta, and profile ID. Disabled means configuration may persist but
no VHE runtime continuation and no VHE sidecar exist. Disabled does not mean
configuration is absent.

## 5. Stream lineage and replay watermark

stream_identity uses the exact Phase-2 ASCII identifier syntax. It is immutable
for one configuration/replay lineage. Configuration deletion followed by
creation establishes a new lineage and may choose a different stream. Reset,
suspension, resume, disable, and disable-to-enable never change it.

adapter_contract_id uses the exact Phase-2 ASCII identifier syntax. It
identifies the descriptor measurement contract bound to the configured stream
and is immutable for the lineage. A changed descriptor-semantic measurement
contract requires a new configuration lineage. adapter_id remains observation
provenance and is not persisted in Brainvision configuration.

last_accepted_source_sequence has the exact type rule:

~~~text
type(value) is int
bool is invalid
range: -1 .. 9223372036854775807
~~~

The fresh/new-lineage value is -1. Phase 2 permits source sequence zero and
the frozen refusal condition is:

~~~text
source_sequence <= last_accepted_source_sequence
~~~

Therefore -1 is the simple sentinel that admits sequence zero without an
exceptional replay rule. The watermark is monotonic nondecreasing and never
decreases across reset, suspend, resume, disable, disable-to-enable, or reload.
Explicit configuration deletion/new lineage resets it to -1.

## 6. Frozen base identities

The configuration must contain exactly:

~~~text
expected_operator_id =
bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb

expected_projection_id =
bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f
~~~

No alternate identity is accepted in v1a. No migration subsystem exists.

## 7. Phase-7 profile binding

The configuration persists all of:

~~~text
modulation_schema_id
modulation_mapping_id
modulation_profile_schema_id
theta
modulation_profile_id
~~~

Their frozen values are:

~~~text
modulation_schema_id =
brainvision.character_modulation.v1

modulation_mapping_id =
bvmodmap1_f8b41a1987437410613157ae403d10ac12fbce3b34cc760f0cc8376193206aeb

modulation_profile_schema_id =
brainvision.character_modulation.profile.v1
~~~

Theta is an exact non-bool integer in {-1, 0, +1}. Stored
modulation_profile_id must equal the exact profile ID derived from stored theta
under the frozen mapping:

| theta | modulation_profile_id |
| ---: | --- |
| -1 | bvmodprof1_95cf73f228a5c02a16e13b90cf17aa46d31bbc312643f7dbf374d33816d9ad49 |
| 0 | bvmodprof1_9f65a350c2526bc63733e9267d7846ce4eace56a6c4ec3261bfc748a18287abc |
| +1 | bvmodprof1_ceeb161b2dcb510601d85fc7b5a64eb023827bb044220b046b2c61b98be422f5 |

There is no CharacterSeed-to-theta derivation and no modulation data is added
to recursive VHE state.

## 8. Mutability and replacement compatibility

Schema identity, stream identity, adapter-contract identity, expected operator
and projection identities, and modulation schema/mapping/profile-schema
identities are immutable for a configuration lineage. The watermark may move
only upward. Lifecycle status may be changed only by a Phase-10 lifecycle
operation.

Theta/profile may be explicitly reconfigured only while lifecycle_status is
disabled. They are immutable while active or suspended because F/S/R produced
under profile A must not continue under profile B. A valid disabled-state
profile change atomically changes both theta and modulation_profile_id while
retaining stream identity, adapter contract, watermark, base identities, and
mapping/schema identities. Its authorization and transaction belong to Phase 10.

Phase 8 freezes a pure replacement-compatibility validator. It rejects a
watermark decrease, stream change within a lineage, adapter-contract change
within a lineage, base-identity change, mapping/schema-identity change, and a
theta/profile change when the prior status is active or suspended. It permits a
consistent disabled-state theta/profile replacement. Artifact validity and
transition authorization remain separate concerns.

## 9. Canonical serialization and strict read semantics

Canonical configuration bytes use:

~~~text
JSON
sort_keys=True
separators=(",", ":")
ensure_ascii=True
allow_nan=False
ASCII encoding
~~~

The field set is exact. Missing fields and unknown fields are rejected. There
are no defaults, migration, float coercion, or bool-as-int acceptance.

The frozen absent-file contract is:

~~~text
configuration read returns None only when configuration.json is absent.
~~~

Read derives the contained path without creating a directory or file. Existing
bytes are strictly decoded and validated. Corrupt or incompatible content never
defaults and must raise a validation or distinct storage exception.

## 10. Atomic write and deletion boundary

A Phase-8 write primitive accepts only a fully validated configuration object,
serializes canonical bytes, creates only the necessary Brainvision leaf
directory, writes a same-directory temporary file, validates containment for
both target and temporary paths, and uses atomic os.replace as its commit. If
temporary-file writing fails, the prior valid target remains unchanged.

The primitive does not enable, disable, suspend, resume, reset, delete
configuration, advance the watermark automatically, or change theta
automatically. It persists only the exact supplied valid configuration.

Configuration deletion is not disable. Phase 8 authorizes no public deletion
semantics. A future low-level contained removal primitive is permissible only if
Phase-10 implementation requires it; configuration deletion/new-lineage remains
a Phase-10 lifecycle and ownership operation.

## 11. Validation failure surface

The configuration parser uses:

~~~text
BrainvisionConfigurationValidationError(field, reason)
~~~

It fails closed with at least these distinct reason classes:

~~~text
must_be_mapping
missing_field
unknown_field
schema_mismatch
invalid_lifecycle_status
invalid_identifier
must_be_exact_int
out_of_range
operator_identity_mismatch
projection_identity_mismatch
modulation_schema_mismatch
modulation_mapping_mismatch
modulation_profile_schema_mismatch
modulation_profile_mismatch
~~~

Filesystem, contained-path, and atomic-write failures remain distinct storage
or path exceptions; they must not be mislabeled as schema-validation failures.
Phase 8 performs no silent repair.

## 12. Recovery support and architectural isolation

Phase 8 implements no recovery. It exposes lifecycle status, stream identity,
adapter-contract identity, watermark, operator identity, projection identity,
and modulation mapping/profile identities that Phases 9 and 10 need to execute
the frozen Phase-0 recovery matrix.

Future Phase-8 configuration code may depend only on stdlib,
brainvision.character_modulation, brainvision.vhe, brainvision.projection,
brainvision.observation, and torment_service.pathing as narrowly necessary. It
must not depend on torment_service.fabric, AgentLockManager, kernel, memory,
CognitiveCore, SRG, Hivermind, or model/prompt systems. It acquires no locks.

## 13. Frozen test plan

The later bounded Phase-8 suite must cover:

1. Exact field set and canonical bytes.
2. Strict round-trip decode.
3. Closed lifecycle vocabulary and rejection of reset as status.
4. Fresh watermark -1, implied sequence-zero eligibility, min/max bounds, and
   bool rejection.
5. Stream and adapter-contract identifier validation.
6. Missing/unknown-field rejection.
7. Exact operator/projection and modulation-identity guards.
8. Exact legal theta/profile pairs and mismatched-pair rejection.
9. Disabled profile retention.
10. Replacement watermark monotonicity and immutable lineage fields.
11. Active/suspended theta-change rejection and disabled consistent
    theta/profile replacement.
12. Path containment and non-mutating reads.
13. Canonical atomic replacement and temporary-write failure preservation of
    the prior target.
14. Absence of Fabric, lock, cognition, memory, kernel, sidecar, and lifecycle
    orchestration behavior.

## 14. Claim ceiling

This specification does not establish Phase-9 sidecar correctness, bit-exact
VHE persistence, Phase-10 lifecycle correctness, recovery-matrix correctness,
known-agent lifecycle hosting, direct visual ingress, Fabric integration, v1a
full qualification, or v1b integration.
