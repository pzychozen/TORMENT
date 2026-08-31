# TORMENT Memory Substrate 7G5D1 — Trace Replay Harness and Frozen Preflight

Status: implementation/preflight only. This document and the adjacent
`experiments/memory_substrate_d1_trace_replay_v1` package establish the D1
protocol. They do not administer the formal native comparison.

## Boundary

D1 is a bounded experiment over one dedicated, private `research` workspace.
The selected CORE D1 baseline is Character-free: it has one agent with no
active Character seed planting and one ordinary hard-stored core memory. The
normal service is started in the existing `torment` environment using its
normal HTTP surface. Native snapshot
qualification and any later replay are performed only in the already qualified
`torment-substrate` environment. Neither environment is installed into,
modified, selected by a runtime flag, or used to change production authority.

The package is experiment-local. It is not imported by `app.py`, `fabric.py`,
or `memory_graph.py`; it adds no selector, deployment metadata change, schema
change, activation, fallback, dual read/write, or production startup path.
C2A remains deferred. Checkpoints, bridge suggestions, compression/deep
memory, shared-lane/Character query contexts, migrations, and cutover are not
implemented by this phase.

## 7G5D1B migration compatibility decision

Real-L0 archaeology established exactly two deterministic legacy facts that
the migration boundary had not recognized:

- `GOVERNANCE_TRANSLATION = DETERMINISTIC_LEGACY_SEMANTIC_TRANSLATION`
- `VECTOR_TRANSLATION = DETERMINISTIC_LEGACY_STORAGE_LAYOUT_TRANSLATION`
- `SEED_WRITER_UNIQUELY_IDENTIFIED = YES`
- `SEED_PROVENANCE_TRANSLATION = NOT_REPRESENTABLE_IN_CURRENT_VOCABULARY`
- `CHARACTER_PROVENANCE_VOCABULARY_CHANGE = NOT_AUTHORIZED`
- `NEW_CHARACTER_L0_WOULD_REPEAT_BLOCKER = YES`
- `CORE_D1_WITHOUT_CHARACTER = SELECTED`
- `CHARACTER_D1_SUBARM = DEFERRED`

`LEGACY_ABSENT_GOVERNANCE_DEFAULT_V1` records only the legacy resolver's
exact all-default result where a nested source payload has no governance
carrier, no outer governance carrier exists, and lifecycle evidence is
independently valid. It does not treat null, malformed, partial, or conflicting
governance as absence. `LEGACY_COMPACT_SHARD_REFERENCE_TRANSLATION_V1` maps
only the production `{shard,row,dim}` reference through the production shard
filename law after its node, map, manifest, workspace lock, and NPY evidence
all agree. Both preserve the source bytes; neither makes captured bytes READY.

The existing Character-bearing L0 and its frozen fixture inputs remain
scientific evidence with `CHARACTER_BASELINE_STATUS =
BLOCKED_BY_PROVENANCE_VOCABULARY`. They are not a CORE D1 baseline and no
Character provenance is inferred or translated.

For CORE N0 B4A, the source `MOTIF_ID` alias remains in the legacy snapshot
source namespace while the projected runtime `DERIVED_MOTIF` receives the same
textual alias in the dedicated `d1-n0-runtime-motif-aliases` namespace. The
two UUIDs must differ; the harness refuses the collapsed topology before B4A
is invoked. This is configuration for the existing B4A invariant, not a B4A
semantic change.

## What D1 does and does not test

The frozen D1 claim is: *given the same real TORMENT-produced storage-facing
facts and the same frozen starting memory state, does the qualified native
SQLite substrate produce the same bounded storage outcomes and qualified
post-write semantics as the legacy backend?* D1 prepares an L0 legacy baseline,
constructs a separately materialized N0 native STAGING baseline through
existing B-series services, and seals a small set of legacy-qualified replay
facts. It compares only the named storage, motif, Character subarm, retrieval,
and structural facts after a future authorized run. A duplicate selection is
independently performed by the native router; a legacy selected target, selected
result, or reinforcement answer is never supplied as native route input.

D1 does not claim whole-system behavioral parity, authority equivalence,
production suitability, stochastic timing parity, or a cutover decision. The
current legacy tail can emit stochastic bridge suggestions and run motif
maintenance after writes, while the qualified core profile has explicitly
different no-op/unsupported dispositions. Any such divergence is recorded as
an observation; fixtures may never be adjusted after seeing a native outcome.

The bounded future administration tests CREATE versus REINFORCE, compatible
EID selection, revisions, raw representations, below-boundary motif decisions,
storage retrieval primitives, qualified conflict/derived-memory/world behavior,
and an optional separately administered C1A/C1B Character sub-arm. It does not
test native write-gate decisions, closed-loop cognition, `TormentFabric.query`
integration, production selection, shared lanes, checkpoint or persistent
trajectory parity, bridge or motif-suggestion parity, auto-merge, C2A
auto-split, compression/deep memory, or production cutover.

## Frozen current-head mechanism facts

`NativeFabricRouteRequest` has no reinforcement-target EID. For a private,
positive-norm request, `NativeFabricMemoryRouter.route()` independently invokes
qualified native embedding search, applies `TORMENT_REINFORCE_SIM_THRESHOLD`,
requires memory-class equality, and invokes the supplied contradiction guard
for core memories. `CREATED_NEW` versus `REINFORCED_EXISTING + EID` is therefore
an intentional D1 falsification point.

The legacy soft write gate and legacy bridge tail call the production
`random_chance()`, which currently uses module-global `random.random()`.
There is no repository-level PRNG seeding hook and D1 adds none. Motif entropy
and merge-suggestion calculations do not consume PRNG. Hard write margins keep
the later bridge draw from changing a later soft-band decision.

The legacy supplied embedding is converted to float32, dimension-checked, and
persisted as that supplied float32 vector. The native request converts to a
contiguous finite float32 vector, checks the qualified lane dimension, and
persists `RAW_VECTOR` `COMPAT_EMBEDDING`. Representation bytes are consequently
an exact comparison field. Captured timestamps are translation facts and must
be preserved exactly; `TIMESTAMP_GENERATION_PARITY_TESTED = NO` and
`TIMESTAMP_PRESERVATION_PARITY_TESTED = YES`.

## L0 protocol

1. Start a real, normal HTTP service in `torment` with a new dedicated
   `TORMENT_DATA_DIR`; do not use a fake/in-process Fabric or MemoryGraph.
2. Create one research-only workspace and one agent via `/workspace/create` and
   `/agent/create`, using a truthy core-only identity marker with no
   `seed_id`, `seed_text`, or `character_name`, while
   `TORMENT_CHARACTER_ENABLE=0` is set for this disposable construction. This
   prevents legacy default seed fallback and active Character seed planting.
3. Ingest exactly one ordinary deterministic hard-stored private core memory
   through the real HTTP Fabric surface. Do not administer a microtrace.
4. Stop the service cleanly.
5. Hash every regular file in the dedicated root, then require and hash the
   workspace embedding lock, identity, private memory rows, raw embedding
   evidence, research motif state, and all retained side stores. The core
   profile rejects Character seed and Character-state artifacts. The tree
   rejects symlinks and any subsequent change fails recheck.

The L0 source remains immutable. N0 packages byte-for-byte evidence into a
separate snapshot root rather than running migration semantics against the L0
directory.

## N0 STAGING construction

N0 invokes existing 7F/B APIs in their existing semantic order: snapshot
rehearsal/evidence admission, B2 normalization for every normalizable current
memory, B3A bootstrap from the captured float32 representation bytes, B4A
lane-preserving motif projection, then B5 workspace readiness. It refuses
anything that requires B3B or B4B. B5 must establish memory, motif, and member
reference closure and both controlled-STAGING readiness booleans. `B4B = 0` is
a hard baseline condition, not a waived result.

B4A is required because source and target use the same embedding lane: it
carries the current legacy centroid and stability without recomputing geometry.
A B4B need stops preflight rather than broadening the experiment.

N0 is opened only through a real file-backed qualified STAGING core and real
external side-store bindings. The qualified post-write adapter itself uses its
forbidden graph boundary; a graph fallback is not available to this harness.
An unavailable feature must fail through the existing profile rather than be
silently fabricated. Every observed retained store has exactly one frozen
disposition: exact comparison, tolerance comparison, out-of-profile,
acceleration-excluded, or process-local; any unknown or unobserved declared
store fails preflight.

## 7G5D1E retained-side-store observation witness

B5 remains a read-only, caller-observed qualification boundary. It does not
crawl a legacy filesystem or infer that an omitted reference list means zero
references. Its additive typed input distinguishes `INCOMPLETE`,
`COMPLETE_ABSENT`, `COMPLETE_PRESENT_ZERO_EIDS`, and
`COMPLETE_PRESENT_WITH_EIDS`. A complete zero observation closes only the
corresponding B1 EID-capable store and causes no alias lookup; a positive
observation still requires every namespace-qualified EID to resolve to exactly
one native object. The legacy positive-reference input remains supported, but
conflicting typed and legacy evidence is refused.

For the immutable Character-free core L0, the experiment-local observer first
re-verifies the complete baseline fingerprint, then reads only the established
side-store structures and locators. It binds the L0 fingerprint, workspace,
agent, domain, source namespace, observation state, references, locators, and
every present-file digest into one canonical D1 evidence digest. It records
`COMPLETE_ABSENT` for conflicts, anchors, affect history, Character, hivemind,
bridges, and deep memory; `trajectory_evidence` remains a real
`COMPLETE_PRESENT_WITH_EIDS` witness for private EID 1. This is experiment
evidence, not a native schema field or a side-store migration. B1’s
conservative classifications, including affect history and bridges, remain
unchanged.

## Fixture qualification and freezing

The checked-in recipe requires M1 create, M2 reinforce, M3 distinct, M4
contradiction, M5 no-write, one sequential arm, and a separate Character
subarm. The recipe is not an administered fixture: each actual request is
qualified from L0 only before its bytes and hash are sealed. It requires empty
raw/qualified links, private/research scope, finite contiguous float32 vectors,
write decisions at least 0.02 outside the relevant soft boundary, raw duplicate
and motif decisions at least 0.02 from their thresholds, and motif membership
under 80 (well below the 96 split boundary).

Each event has a deterministic D1 operation key. The exact same fixture,
ordinal, and request digest reuses its key on retry; a changed digest or key
collision fails. M2’s legacy reinforcement result remains comparison evidence
only. M5 does not invoke native routing, but it does invoke the existing native
post-write adapter with a `NO_WRITE` context and no route witness. Durable native
storage table counts must remain exactly unchanged; the documented native world
step is process-local and therefore separately recorded.

Native replay input is limited to storage-facing facts that the current native
route accepts, including the captured raw float32 bytes, lane, structural
provenance/governance, memory metadata, timestamps, and explicit empty links.
`promotion_score` is a captured input and is reproduced exactly in the future
`FabricPostWriteContext`. In contrast, `created_motif` and `state_symbol` are
native-owned outputs and are never copied from a legacy response. Their only
current consumers are closed by the frozen initial posture:
`TORMENT_HIVEMIND_ENABLE=false`, identity `coupling_mode=read_only` (or the
existing absent/read-only fallback),
`D1_HIVEMIND_PACKET_PARITY_TESTED=NO`, and
`D1_PROPOSAL_PARITY_TESTED=NO`. If either consumer is brought into profile,
preflight must refuse rather than supplying a legacy output placeholder.
It deliberately excludes legacy selected EIDs, output motifs, conflict targets,
and all legacy route answers. Native duplicate selection is consequently
independent.

Duplicate evidence has an explicit frozen reason. `REINFORCE_MATCH` requires
high similarity, a false contradiction guard, and a reinforced legacy result;
`CREATE_DISTINCT_BELOW_THRESHOLD` requires low similarity and a created legacy
result; `CREATE_CONTRADICTION_GUARD` requires high similarity, a true legacy
contradiction guard, and a created legacy result. Consequently M4 cannot be
misreported as M3. `CREATE_NO_CANDIDATE` and `NOT_APPLICABLE` do not claim a
threshold decision.

The replay plan assigns every frozen fixture ID exactly once and prohibits both
legacy and native clone reuse. Its minimum ordered shapes are M1 `CREATE`, M2
`CREATE, REINFORCE`, M3 `CREATE, DISTINCT`, M4 `CREATE, CONTRADICTION`, M5
`NO_WRITE`, sequential `CREATE, REINFORCE, DISTINCT, CONTRADICTION`, and a
separate Character arm consisting of preparation events followed by exactly one
logical-step-25 administration event. Current legacy Character measurement has
no higher non-seed-memory minimum; a measured zero count remains meaningful and
is not rejected by the experiment.

Store dispositions distinguish `REQUIRED_PRESENT` from explicitly named
`OPTIONAL_PRESENT` stores. A declared optional out-of-profile operational store
such as `motif_merge_suggestions.jsonl` may be absent or present; arbitrary
unknown stores still fail the harness. The frozen workspace domain set is
exactly `["research"]`, so the ordinary bridge draw may be consumed but cannot
form a cross-domain pair. Bridge code is not disabled.

The Character sub-arm has a separate L0C/N0C recipe and is
`DEFERRED_PENDING_PROVENANCE_VOCABULARY`. The preserved Character-bearing L0
must continue to refuse normalisation on `UNKNOWN_PROVENANCE` even after the
governance and compact-vector repairs. Before a future Character request can
freeze, an authorized provenance ontology decision is required; no current
core-D1 work may relabel or bypass that blocker.

## Comparison contract for a future authorized D1 run

The frozen tolerances are centroid `rtol=1e-6`, `atol=1e-7`; scalar,
Character-drift, and retrieval-score absolute tolerance `1e-6`; and ranking
order required only where the legacy score gap exceeds `1e-6`. Requested
comparison records cover stored/no-write, create/reinforce, native EID/revision
lineage, current representation, motif membership and geometry, Character
subarm state, and bounded retrieval/restart evidence. Native-only structural
checks cover UUID uniqueness, parentage, revision advancement/current ownership,
operation ownership, idempotency, and retry stability.

The tolerances and protocol/fixture hashes are immutable after freezing.
Potential divergences are recorded as results, not resolved by changed fixture
selection. Formal administration refuses to start until hashes are frozen and
an authority-bearing future workorder changes the explicit authorization gate;
this phase leaves that gate false.

## Formal-administration closure mechanics

The experiment-local runner accepts only concrete frozen-input hashes and an
explicit one-administration authorization bound to an administration ID,
repository HEAD, protocol hash, fixture hash, tolerance hash, and new result
root. It checks the concrete bytes and L0/N0 baselines through its supplied
verification boundary, validates clone identities, writes an exclusive durable
administration-start marker before any trace contact, and refuses an existing
marker, result root, or result file. There is no retry, fallback, or
`D1PreflightReport` result path. A failure after the marker becomes
`EXPERIMENT_HARNESS_FAILURE` in that one root.

The unpopulated result schema has separate fields for harness validity, storage
substrate verdict, qualified post-write verdict, optional-feature divergences,
known unsupported edges, M1/M2/M3/M4/M5/sequential/Character arms, restart
evidence, retrieval characterization, and native structural invariants. It
declares `TIMESTAMP_GENERATION_PARITY_TESTED=NO`,
`TIMESTAMP_PRESERVATION_PARITY_TESTED=YES`, and
`D1_CLOSED_LOOP_QUERY_PARITY_TESTED=NO`. This workorder creates no
authorization manifest and starts no formal administration.

Legacy motif entropy logs/merge suggestions and legacy bridge state are retained
as `OPTIONAL_FEATURE_DIVERGENCE` observations, not native storage failures.
For each relevant future arm, record bridge state before/after and observable
suggestion additions. D1 does not suppress either production path.

## Restart and retrieval scope

A later formal arm records `LEGACY_PRE_RESTART`, cleanly restarts the real
legacy service on the same arm root for `LEGACY_POST_RESTART`, closes native
replay handles, reopens the qualified STAGING core, and records
`NATIVE_POST_RESTART`. Durable expected state is current memory truth,
representations, motif state, CharacterStore state, provenance, governance,
lifecycle, and explicitly in-profile durable side-store records. Native world
state, transient SRG overlays, legacy in-process kernel state without a proven
restoration path, and other documented in-memory diagnostics are process-local
or reset expected. Discovery of automatic checkpoint restoration requires a
protocol amendment before administration.

Retrieval is deliberately low-level: legacy `MemoryGraph.search_by_embedding`
and qualified native compatibility embedding search both receive the same frozen
query vector. `D1_CLOSED_LOOP_QUERY_PARITY_TESTED = NO`.

## Result vocabulary

Future reporting keeps `D1_STORAGE_SUBSTRATE_VERDICT` distinct from
`D1_QUALIFIED_POST_WRITE_VERDICT`, with values such as
`STORAGE_SUBSTRATE_EQUIVALENT_IN_ADMINISTERED_PROFILE` or
`STORAGE_SUBSTRATE_DEFECT`, and
`QUALIFIED_POST_WRITE_EQUIVALENT_IN_ADMINISTERED_PROFILE` or
`QUALIFIED_POST_WRITE_DEFECT`. It separately records optional-feature
divergences, known unsupported edges, and harness validity; it never issues a
single claim of full TORMENT parity.

## Frozen preflight result

`FORMAL_ADMINISTRATION_RUN = NO`. This phase has no D1 PASS/FAIL comparison
outcome and no native result inventory. It only makes future construction
repeatable and auditable while preserving `LEGACY_ACTIVE` authority.
