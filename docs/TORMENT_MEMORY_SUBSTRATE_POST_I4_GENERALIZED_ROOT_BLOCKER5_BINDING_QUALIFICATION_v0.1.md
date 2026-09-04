# TORMENT Memory Substrate — Post-I4 Generalized Root Blocker-5 Binding Qualification v0.1

```text
STATUS = SYNTHETIC_OFFLINE_QUALIFIED
REAL_ROOT_CONTACT = NONE
REAL_ROOT_ACTIVATION_READY = NO
REAL_PRODUCTION_ACTIVATION_AUTHORIZED = NO
```

## Scope

This record qualifies the smallest offline bridge from
`RootNativeProductionAdmissionDescription`, root-wide normalization, and
durable `RootScopeMembership` evidence into the surviving Blocker-5
administration model:

```text
OfflineCutoverController
deployment_selector
deployment_core_maintenance
existing deployment diagnostic/agreement model
```

It adds no second controller, deployment authority, selector, core authority,
or progress ledger. It does not start services, contact providers, download
models, activate a real root, mutate a real external owner, or widen public
capabilities.

## Completion evidence

`RootAdmissionCompletionWitness` is the discriminated/versioned v2 form for
the existing `ACTIVATE_CORE` completion-evidence slot:

```text
CONTRACT = TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS
VERSION = 2
```

Historical `AdmissionCompletionWitness` v1 payloads remain decoder-supported
without rewriting them or using a fake-workspace sentinel. The v2 form binds:

- data-root identity and root admission envelope digest;
- declared/discovered census digests and manifest digest;
- external-owner observation and frozen geometry-plan digests;
- target representation identity and root writer-freeze witness digest;
- native staging core, qualified profile, root-profile object/revision/ordinal;
- durable root-membership closure and normalization-closure digests.

## Root gates

The bridge discovers only canonical layout identities:

```text
workspaces/<workspace>
workspaces/<workspace>/agents/<agent>/private
workspaces/<workspace>/domains/<domain>/shared
```

It does not recurse within materialized scopes or fingerprint unrelated files.
Both an undeclared materialized scope and a declared-but-undiscovered scope
refuse root completion. The P2 envelope binds a root-scoped writer-freeze
witness, deterministic discovered census, manifest, profile, root-profile
revision, durable membership closure, and the frozen owner-specific geometry
table.

Manifest evidence is rechecked at normalization start, P4 completion
verification, and immediately before P6. Any drift refuses; the frozen P2
envelope is never silently refreshed.

## Lifecycle and recovery law

```text
P2  existing selector -> CUTOVER_PENDING with root envelope digest
P3  existing NativeRootWideNormalizationService under maintenance-only fence
P4  manifest/census/membership/normalization verification -> v2 completion
P5  existing core -> CUTOVER_PENDING
P6  existing core ACTIVATE_CORE durable commit (point of no return)
    selector remains CUTOVER_PENDING / maintenance-only
    legacy rollback remains refused
P6+ deterministic synthetic disposition execution -> immutable receipt
P7  existing selector -> NATIVE_ACTIVE only with exact receipt digest
```

The post-P6 receipt is stored as an explicitly discriminated record in the
existing constrained `CUTOVER` maintenance evidence stream. It is evidence,
not a deployment authority or progress ledger. It is idempotently recovered by
operation identity; conflicting receipt intent is refused.

`activate_selector_native` preserves v1 behavior and, for a v2 root
completion, requires the matching durable disposition receipt and binds its
digest into selector activation intent. A missing or mismatched receipt refuses
P7. Repeated P6/P7 calls recover the same committed evidence without duplicate
activation.

## Frozen geometry contract

The receipt validator requires all eleven ratified owner entries and their
exact dispositions: Character active-baseline recomputation; historical
Character drift retention; Character seed retention; exact SRG retention;
checkpoint calibration-only reinitialization; proposal retention with future
consumer guard; historical bridge/Hivemind retention; world/trajectory
retention; untouched disabled deep/archive state; and no geometry disposition
for conflict/role/affect/identity.

Only deterministic synthetic adapters are accepted by this phase. Their result
records bind owner identity, source observation digest, chosen frozen
disposition, result/no-mutation outcome, and geometry transition identity.
No real owner implementation was changed.

## Qualification evidence

All commands used `conda activate torment` and an explicit temporary base
outside the repository because the host default pytest temp directory denies
enumeration access.

```text
pytest -q tests/test_post_i4_generalized_root_blocker5_binding.py
  3 passed

pytest -q tests/test_b5_a2_deployment_fence.py
          tests/test_substrate_root_scope_membership.py
          tests/test_substrate_root_normalization.py
  45 passed
```

The synthetic bridge coverage includes v1/v2 decoding; P2 canonical census
parity and undeclared-workspace refusal; root writer-freeze binding; P4 and
immediately-pre-P6 manifest-drift refusal; durable P6 activation and
lost-response retry; post-P6-only disposition execution; receipt idempotency
and conflicting-intent refusal; P7 refusal without receipt; P7 exact-receipt
activation and retry recovery. The predecessor suites retain historical
first-profile fence behavior, root membership revision/isolation/retirement
safeguards, and deterministic root normalization recovery.

## Explicit non-claims

```text
ST_BGE_PRODUCTION_PARITY = NOT_CLAIMED
REAL_ROOT_READ_OR_WRITE = NOT_PERFORMED
REAL_EXTERNAL_OWNER_MUTATION = NOT_PERFORMED
PUBLIC_API_EXPANSION = NONE
COMPRESSION_ENABLED = NO
DEEP_MEMORY_ENABLED = NO
NEW_UNADMITTED_SCOPE_CREATION = REFUSED
```
