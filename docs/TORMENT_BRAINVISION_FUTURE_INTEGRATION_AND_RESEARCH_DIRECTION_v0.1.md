# TORMENT BRAINVISION — FUTURE INTEGRATION AND RESEARCH DIRECTION v0.1

**Status:** NON-NORMATIVE / PRESERVATION AND FUTURE-QUESTION NOTES
**Brainvision production state:** v1a QUALIFIED
**Phase 13:** CLOSED
**Mandatory hold:** ACTIVE

This document does not authorize Phase 14, integration design, prototyping, implementation, or connection to memory, character, cognition, models, prompts, or other TORMENT subsystems.

Its present purpose is limited to preserving the meaning and boundaries of qualified Brainvision v1a and recording open questions for later consideration.

---

# 1. Purpose of This Document

Brainvision v1a is complete as an isolated visual-state subsystem and has passed its corrected formal qualification.

The purpose of this document is to preserve a clear shared understanding of:

* what Brainvision currently is;
* what Brainvision currently is not;
* what qualified v1a actually established;
* what remains private/internal to Brainvision by contract;
* what interfaces already exist;
* what Brainvision is not currently connected to;
* which future questions may eventually require separate authorization before design work begins.

Nothing described here is implemented or authorized merely because it is mentioned here.

Nothing here overrides the frozen Brainvision specifications, bindings, qualification result, claim ceiling, or mandatory hold.

---

# 2. What Brainvision v1a Is

Brainvision v1a is a bounded, deterministic visual-state continuity subsystem.

It accepts lawful `FIRSTHAND_VISUAL` observations containing bounded low-level descriptor values.

Brainvision does not receive images or video frames directly and performs no classification, recognition, object detection, scene understanding, or semantic interpretation.

Its output is not a function of the current descriptor alone.

The qualified system evolves internal state from:

* current bounded descriptor input;
* prior committed descriptor inputs;
* active visual time;
* frozen relational dynamics;
* bounded contextual modulation under the qualified `CONTEXT_INTEGRATION` contract.

Brainvision therefore implements a recursive visual-state process whose current bounded projection can depend on prior committed observations.

Under the frozen retained-history fixture, two histories ending at the same terminal descriptor can produce different retained-history output while current and immediate relational coordinates are equal.

Under the frozen order fixture, Brainvision distinguishes two histories that differ only in the order of two events by the sign of one relational coordinate.

This establishes bounded order dependence on that specific fixture.

It does not establish general history-order sensitivity or a general trace of the path by which arbitrary states were reached.

---

## 2.1 Projection is deliberately bounded and lossy

Brainvision exposes a bounded projection of its internal dynamical state.

The projection is deliberately lossy and non-injective.

Therefore:

> Equality of projection fields means no observable divergence at the qualified projection resolution.

It does not establish equality of raw recursive internal state.

A future consumer must not infer raw-state identity from equal projections.

---

## 2.2 The 300-active-second result is a product floor

Brainvision satisfied the frozen 300-active-second product-horizon requirement.

This means the retained state required by the frozen contract survives at least the qualified active-time horizon.

It does not establish:

* a natural memory duration;
* a half-life;
* a decay constant;
* an upper memory bound;
* a biological or psychological memory analogue.

The 300-second value is a tested product requirement, not a discovered natural timescale.

---

## 2.3 Projection codes have no natural-language semantic meaning

Brainvision projection codes are structural outputs of the qualified dynamical system.

They must not be interpreted as:

* emotion;
* attention;
* salience;
* interest;
* awareness;
* understanding;
* subjective experience;
* cognitive meaning.

Any future consumer must preserve this distinction.

---

# 3. Qualification History

The corrected Phase-13 administration completed:

* 45 / 45 formal arms;
* 81 / 81 primary criteria;
* 147 / 147 evidence obligations;
* 228 / 228 total criteria and obligations.

The corrected result was:

`V1A_QUALIFICATION_PASS`

and:

`BRAINVISION_V1A: QUALIFIED`

The mandatory post-qualification hold is active.

The earlier formal administration remains permanently preserved as:

`FAIL / V1A_QUALIFICATION_FAIL / FAIL_IMPLEMENTATION`

That historical result was not erased, regraded, superseded, or silently rerun.

The forensic record established that the first administration contained:

* implementation-class failures;
* instrument/evidence-contract defects;
* scientific-class E3 criteria that were rendered unevaluable rather than falsified.

The corrected administration used:

* repaired production behavior;
* a separately corrected and frozen instrument;
* a new formal authorization;
* a new administration identity;
* a new full 45-arm administration.

The PASS establishes only that the corrected assembled system satisfies the bounded Phase-13 qualification contract under the preregistered synthetic fixtures and schedules.

---

# 4. What Brainvision Is Not

Brainvision v1a is not itself:

* an LLM;
* a conversational system;
* a character;
* a MemoryGraph;
* a memory-formation system;
* a memory-retrieval system;
* CharacterState;
* CharacterSeed;
* CognitiveCore;
* SRG;
* Hivermind;
* Spine;
* a general computer-vision system;
* an object-recognition system;
* a scene-understanding system;
* a physical-world truth detector;
* an emotion system;
* an attention system;
* consciousness;
* awareness;
* subjective experience;
* semantic understanding.

Brainvision's present state depends on prior inputs, as expected of a recursive filter.

This is not memory in any TORMENT sense.

Brainvision performs no memory formation, no memory retrieval, and contains no MemoryGraph state.

No future integration contract can convert Brainvision's internal recursive state into memory.

A future separately authorized consumer could, in principle, derive memory content from a bounded Brainvision projection, but that memory would belong to the consuming system rather than to Brainvision itself.

The controlling frozen claim ceiling additionally does not establish:

* a natural 300-second memory duration, half-life, decay constant, or upper memory bound;
* physical-world visual accuracy;
* arbitrary-camera behavior;
* arbitrary frame-rate or cadence invariance;
* LLM usefulness;
* improved model output;
* cognitive usefulness;
* v1b readiness;
* integration correctness;
* general order sensitivity beyond the frozen order fixture;
* universal cross-platform determinism beyond the administered conditions;
* cross-process sink serialization beyond what was administered;
* that Phase-11 direct ingress is the only possible code path capable of mutating VHE state.

In any conflict between this summary and the frozen Phase-13 specification, the frozen specification remains authoritative.

---

# 5. Current Isolation Boundary

Brainvision v1a remains functionally isolated from TORMENT's normal cognitive, memory, prompt, and model pathways.

It is not connected by default to:

* MemoryGraph;
* memory formation;
* memory retrieval;
* CharacterSeed;
* CharacterState;
* CognitiveCore;
* SRG;
* Hivermind;
* Spine;
* prompts;
* model inference;
* ordinary `Fabric.ingest`;
* language conversation flow.

When Brainvision is absent or disabled, ordinary TORMENT semantics remain unchanged.

A running Brainvision instance does not automatically cause:

* a model call;
* a character thought;
* a memory write;
* a prompt change;
* an action;
* a character-state transition;
* a CognitiveCore transition;
* a semantic interpretation.

Brainvision is therefore functionally isolated from those systems.

However, it is not literally import-independent or lifecycle-independent from Fabric.

`TormentFabric` currently constructs and hosts `BrainvisionLifecycleManager`, and Brainvision shares Fabric-level resources including the data root, identity infrastructure, agent locks, and shutdown lifecycle.

The correct statement is therefore:

> Brainvision is functionally isolated from ordinary ingest, memory, cognition, prompts, and model inference, while being hosted within the broader Fabric lifecycle.

---

# 6. Internal State and Existing Output Surface

Brainvision's recursive internal state is non-consumer state by architectural contract.

It should not be treated as a general integration surface.

This is a contract boundary, not a technical impossibility.

Current APIs can expose runtime snapshots containing VHE state, and projection functions are callable.

No current memory, character, cognition, prompt, or model consumer uses those APIs.

The intended future-facing principle remains:

> Other systems should consume bounded Brainvision projections rather than depend on Brainvision's raw recursive internals.

A bounded projection delivery seam already exists in Phase 12.

The Phase-12 sink is:

* optional;
* push-only;
* post-durability;
* projection-only;
* non-persistent.

It has no:

* queue;
* pull API;
* batching;
* retry;
* recovery backfill;
* persistent delivery store.

The existing Phase-12 sink is a diagnostic/delivery boundary.

It is not an integration bridge and must not be silently repurposed into one.

Any future consumer architecture would require separately authorized design.

A future consumer must also respect projection non-injectivity and must not assign natural-language semantic meaning to structural projection codes.

---

# 7. Current Clock and Update Semantics

Brainvision has its own active visual clock semantics.

Its persistent context and semantic register change only on committed observations.

Its fast trace additionally evolves with active visual time.

Brainvision is therefore observation-driven rather than an autonomous free-running capture system.

It contains no autonomous image-acquisition or update scheduler.

A deployment could submit visual observations more frequently than conversational exchanges occur, but v1a was qualified only under the frozen administered schedules.

No arbitrary frame-rate or cadence invariance has been established.

The current Phase-12 sink is synchronous.

Therefore a slow consumer callback can delay the caller that submits later observations.

A future integration must not silently allow model latency or consumer latency to redefine Brainvision visual-time semantics.

This is a future constraint only.

No integration design is authorized by this statement.

---

# 8. Open Future Problem — Temporal Mismatch

If Brainvision is ever considered for connection to a slower conversational or character system, one unresolved problem is temporal mismatch.

A visual-state subsystem may receive multiple committed observations during the interval between two language-model interactions.

Conversational inference and visual-state updates therefore need not occur at the same cadence.

Two constraints follow immediately:

> Brainvision must not automatically trigger model inference for every visual update.

and:

> model inference cadence must not silently control Brainvision's internal visual-time semantics.

How, whether, or through what architecture such a mismatch should be resolved is intentionally left undefined.

No bridge, queue, context assembler, character integration, memory integration, or model integration is specified by this document.

Design toward those mechanisms remains prohibited while the mandatory hold is active unless a separately recorded authorization explicitly releases a named scope.

---

# 9. Current Future-Direction Boundary

At the present mandatory hold, lawful activity is limited to:

* preserving what Brainvision v1a means;
* documenting known boundaries;
* recording unresolved questions;
* recording known non-claims;
* discussing whether any future scope should be released.

The following remain unauthorized:

* Phase 14 implementation;
* character integration design;
* memory integration design;
* model integration design;
* prompt integration;
* CognitiveCore integration;
* SRG integration;
* Hivermind integration;
* Spine integration;
* dream-system design;
* imagined-scene system design;
* prototyping of any integration surface.

If future conceptual architecture work is desired, the mandatory hold should first be cleared only for a specifically named scope.

An example of such a scope could be:

`CONCEPTUAL_BRAINVISION_INTEGRATION_ARCHITECTURE_ONLY`

with explicit exclusions for:

* production code;
* prototypes;
* runtime wiring;
* model calls;
* memory writes;
* character-state changes;
* Phase 14 implementation.

Until such a scope release exists, this document stops here.
