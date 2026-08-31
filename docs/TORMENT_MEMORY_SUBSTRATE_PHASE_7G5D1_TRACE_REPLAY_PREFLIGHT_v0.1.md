# TORMENT Memory Substrate 7G5D1 — Trace Replay Harness and Frozen Preflight

Status: implementation/preflight only. This document and the adjacent
`experiments/memory_substrate_d1_trace_replay_v1` package establish the D1
protocol. They do not administer the formal native comparison.

## Boundary

D1 is a bounded experiment over one dedicated, private `research` workspace
and one frozen Character seed. The normal service is started in the existing
`torment` environment using its normal HTTP surface. Native snapshot
qualification and any later replay are performed only in the already qualified
`torment-substrate` environment. Neither environment is installed into,
modified, selected by a runtime flag, or used to change production authority.

The package is experiment-local. It is not imported by `app.py`, `fabric.py`,
or `memory_graph.py`; it adds no selector, deployment metadata change, schema
change, activation, fallback, dual read/write, or production startup path.
C2A remains deferred. Checkpoints, bridge suggestions, compression/deep
memory, shared-lane/Character query contexts, migrations, and cutover are not
implemented by this phase.

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
   `/agent/create`, passing the frozen Character seed. Ordinary seed planting is
   therefore owned by the normal service.
3. Do not administer a microtrace during construction. Stop the service cleanly.
4. Hash every regular file in the dedicated root, then require and hash the
   workspace embedding lock, identity, seed, Character state, private memory
   rows, raw embedding evidence, research motif state, and all retained side
   stores. The tree rejects symlinks and any subsequent change fails recheck.

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
It deliberately excludes legacy selected EIDs, output motifs, conflict targets,
and all legacy route answers. Native duplicate selection is consequently
independent.

The Character sub-arm has a separate L0C/N0C recipe. Before its concrete
request can freeze, legacy-only qualification must prove recent non-seed memory
evidence, Character enabled, one genuinely stored hard-gated request at logical
step 25, no split/checkpoint edge, and byte-stable correction embeddings across
`torment` and `torment-substrate`. It then measures occurrence/classification,
direction and score, correction occurrence/text/semantics, and reflex edge as
separate qualified results; it does not create a Character query context.

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
