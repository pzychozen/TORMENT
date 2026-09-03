# TORMENT Memory Substrate — Phase 9D I1C

## Root-profile anchor and membership corrections

**Status:** qualified offline correction to I1.  This work used isolated SQLite
fixtures only.  It did not contact a real root, start a service, select a
provider, re-embed memory, or alter public/query/post-write cognition.

## 1. Corrected ownership boundary

`torment_service/substrate/root_profile.py` is the root/deployment-profile
read-side authority.  It defines the production constants and contract for
`ROOT_NATIVE_PROFILE_GENERATION`; it creates no object, registry, root, or
membership.

```text
ROOT_PROFILE_OBJECT_KIND = ROOT_NATIVE_PROFILE_GENERATION
ROOT_PROFILE_PAYLOAD_CONTRACT = TMS-ROOT-NATIVE-PROFILE-GENERATION-1
ROOT_PROFILE_CORE_ID_SOURCE = core_metadata.core_id
ROOT_PROFILE_GENERATION_SOURCE = current object revision JSON payload
CURRENT_PROFILE_DISCOVERY_OWNER = ROOT / DEPLOYMENT PROFILE AUTHORITY
```

The durable payload contains only the contract identifier and positive
`profile_generation`.  It does not duplicate `core_id`; discovery reads that
fact from authoritative native core metadata.  The object/revision itself
supplies the object id, revision id, revision ordinal, and semantic scope id.

`current_root_profile_generation(connection)` fails closed unless exactly one
current admissible root-profile object exists.  Its admissibility states use
existing substrate values:

```text
existence_state = EXISTS
lifecycle_state = ACTIVE
governance_state = QUALIFIED
```

Any absent, multiple, malformed, wrong-kind, or non-admissible profile refuses
discovery.  `verify_root_profile_generation()` makes a supplied reference a
claim to validate rather than a caller-owned source of facts.

## 2. Membership consequences

`RootScopeMembershipService` continues to own only the relationship-backed
fact that one semantic scope belongs to one exact root-profile revision.  It
now verifies the reference against root authority before admission and durable
recovery validates the reference before resolution.

```text
PROFILE_CORE_ID_VALIDATION = PASS
PROFILE_GENERATION_VALIDATION = PASS
PROFILE_OBJECT_KIND_VALIDATION = PASS
PROFILE_LIFECYCLE_VALIDATION = PASS
MEMBERSHIP_REVISION_PINNING = EXACT_REVISION

ROOT_PROFILE_REVISION_ADVANCE =
    EXISTING_MEMBERSHIPS_DO_NOT_AUTOMATICALLY_FOLLOW
MEMBERSHIP_REQUIRES_ADMISSION_TO_SUCCESSOR_PROFILE = YES
```

The revision ordinal remains stored on the exact endpoint.  Its role is frozen
as denormalized history and an FK-determined check value; it is not an
independent semantic discriminator or priority/order signal.

```text
MEMBERSHIP_REVISION_ORDINAL =
    DENORMALIZED_HISTORY
    FK_DETERMINED
    NOT_AN_INDEPENDENT_SEMANTIC_DISCRIMINATOR
```

Retirement remains terminal within a profile generation.  A subsequent
generation may receive a separate admission, but no resurrection or automatic
migration path was introduced.

```text
RETIRED_MEMBERSHIP_READMISSION = REQUIRES_NEW_PROFILE_GENERATION
```

## 3. Runtime and identity corrections

`RootScopeMembershipRuntime` now holds `RootScopeMembershipReader`, a narrow
read-only recovery surface, rather than the admission-capable service.  The
former `writable=False` schema call was removed because it was not a SQLite
read capability.  Resolution never invokes admission or mutation.

Active membership requires a matching supplied `NativeMemoryRuntimeScope`.
Retired membership is recovered as durable retired state without requiring its
former binding, so a withdrawn retired resource cannot block surviving active
members.

```text
RETIRED_MEMBERSHIP_REQUIRES_LIVE_BINDING = NO
CURRENT_RESOLUTION_SCOPE_ISOLATION = PASS
RETAINED_RUNTIME_CACHE_QUALIFICATION = NOT_YET_APPLICABLE
```

I1C does not claim a retained hot-path membership cache: each resolution
reconstructs current relationship state.  Any future I3 cache must separately
qualify key isolation, publication, invalidation, retirement, and
profile-revision behavior.

Membership payloads now encode workspace and private/shared qualifier strings
as exact UTF-8 base64 evidence before canonical JSON serialization.  This
prevents canonical JSON NFC handling from silently changing a `RootScopeKey`.
No normalization was added to `RootScopeKey` itself.

```text
ROOT_SCOPE_KEY_COMPARISON = EXACT_STRUCTURAL_IDENTITY
CASE_VARIANTS = DISTINCT
UNICODE_COMPOSED_DECOMPOSED_VARIANTS = DISTINCT
SCOPE_IDENTITY_NORMALIZATION_GATE = PRE_ACTIVATION_OPEN
```

The final gate remains open because exact database identity does not decide
real-host filesystem aliasing or production root-equivalence semantics.

## 4. Witness boundary

Synthetic witness digest construction was removed from the production-facing
membership module and retained only in isolated test support.  Membership
witness evidence now includes an `issuer_reference` and a provenance class:
`QUALIFICATION_TEST` or `EXTERNAL_ISSUED`.

```text
ISSUER_REFERENCE = PROVENANCE
ISSUER_REFERENCE_ALONE = NOT_AUTHORITY_VERIFICATION
EXTERNAL_WITNESS_AUTHORITY_QUALIFIED = NO
NAMED_EXTERNAL_ADMISSION_OWNER_AND_WITNESS = OPEN_PRE_ACTIVATION_GATE
NO_PRODUCTION_PUBLIC_CALLER_MAY_ADMIT_NEW_SCOPE = YES
UNTIL_EXTERNAL_WITNESS_VERIFICATION_IS_QUALIFIED = YES
```

No external identity, issuer verifier, public admission authority, or fake
authority component was created.

## 5. Qualification inventory

The isolated I1C suite covers:

- actual two-connection SQLite admission contention with one durable result;
- private/shared and exact EID isolation;
- retired binding withdrawal and terminal readmission policy;
- profile discovery, restart, multi-profile refusal, revision advancement,
  wrong core/generation/kind, and invalid lifecycle refusal;
- exact case and Unicode structural identity preservation;
- absent-scope non-materialization and a focused import/call boundary check.

Focused I1/I1C tests: `21 passed`.

Directly affected relationship/root-admission/runtime-readiness regressions:
`13 passed`.

## 6. Claude findings disposition

```text
F1_PROFILE_ANCHOR_VALIDATION_INCOMPLETE = CORRECTED
F2_PROFILE_GENERATION_CALLER_MEMORY_ONLY = CORRECTED
F3_CURRENT_PROFILE_DISCOVERY_ABSENT = CORRECTED

FINDINGS_NOT_ADOPTED = NONE
NON_BLOCKING_DEBT =
    real-root filesystem-equivalence reconciliation;
    external witness issuance/verification;
    future retained-runtime-cache qualification
```

## 7. Final correction verdicts

```text
P9D_I1_CORRECTION = PASS
ROOT_PROFILE_GENERATION_CONTRACT = QUALIFIED
CURRENT_ROOT_PROFILE_DISCOVERY = QUALIFIED
I1_READY_AS_I2_FOUNDATION = YES
I1_READY_FOR_COGNITIVE_ADAPTERS = YES

QUERY_COGNITION_CHANGED = NO
POST_WRITE_COGNITION_CHANGED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
BLOCKER_5_REOPEN_REQUIRED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```
