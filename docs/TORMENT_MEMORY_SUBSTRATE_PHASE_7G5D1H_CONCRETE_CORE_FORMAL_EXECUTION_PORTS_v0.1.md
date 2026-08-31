# TORMENT Memory Substrate — Phase 7G5D1H

## Concrete CORE_ONLY formal execution ports

This phase closes the execution seam for the already-frozen CORE_ONLY D1
administration. It does not administer that experiment.

`ConcreteCoreFormalExecutionPorts` is experiment-local and exposes the exact
executor contract:

- `legacy_environment = "torment"`
- `native_environment = "torment-substrate"`
- ordinary legacy HTTP only
- qualified native STAGING only

The native orchestrator process imports only qualified substrate machinery.
It starts a separate JSON-line worker under `torment`; that worker owns the
ordinary `python -m torment_service` child and its arm-specific
`TORMENT_DATA_DIR`. The processes do not import or execute both backend
implementations together. No native network service, Fabric selector, graph
fallback, dual write, or dual read is introduced.

Each future administration work root must be supplied as a new absolute path.
The concrete allocator creates only the six named arm parents, and each arm
gets distinct `legacy` and `native` mutable roots. Legacy clones the frozen L0
in its worker. Native clones the qualified frozen N0 and reopens the same
mutated `n0_core.db`; it does not rerun migration, rebuild N0, repair state,
or replay events during reopen.

The executor has one mechanical cleanup guard: if a paired native arm cannot
open after its legacy service has opened, it closes that legacy child and then
propagates the original native-open failure. This is not a fallback or retry.

Native stored events use the existing qualified routing and post-write adapter
through `NativeReplayHarness`. The frozen storage-facing mapping is converted
to the existing native request facts without a selected legacy EID. M5 uses
only the qualified no-write post-write context: it makes zero router calls and
compares the bounded durable native snapshot before and after.

Before `FormalAdministrationRunner` writes a marker, the wired verifier will
re-read the named CORE_ONLY fixture and locks, verify the frozen L0 and
retained-side-store witness in the separate legacy environment, and open the
existing qualified source N0 read-only enough to reconstruct its binding,
routing capability, and post-write adapter. It requires the established L0
fingerprint, side-store observation digest, six-arm/Character-free inventory,
B3A EID 1, B4B count 0, constructibility flags, and native formal event count
0. It changes neither source.

The operator surface is:

```text
python -m experiments.memory_substrate_d1_trace_replay_v1.formal_core_administer
```

It requires explicit administration ID, expected current repository HEAD,
protocol/fixture/tolerance SHA-256 values, absolute administration work root,
and absolute result root. The command can construct the one-shot authorization
and call the existing runner, but Phase 7G5D1H does not invoke it. Tests use
only synthetic authorizations and temporary roots; no real administration ID,
marker, result root, or frozen event is created here.

Status after this phase:

```text
CORE_D1_ACTUAL_FIRE_READY = YES
FORMAL_AUTHORIZATION_CREATED = NO
FORMAL_ADMINISTRATION_STARTED = NO
NATIVE_FORMAL_EVENT_COUNT = 0
D1_RESULT_EXISTS = NO
CHARACTER_D1_FORMAL_PREFLIGHT_READY = NO
```
