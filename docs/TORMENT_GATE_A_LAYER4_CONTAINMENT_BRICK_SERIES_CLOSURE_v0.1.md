# TORMENT — Gate A Layer 4 Containment Brick Series Closure v0.1

**Status:** Implementation checkpoint (docs-only closure). Negative containment
only. **NOT Gate A wall completion.**

This document records the first Gate A Layer 4 containment brick series: five
landed implementation bricks that refuse an inert `CandidateShapedValue` at
specific ordinary-memory / caller-visible write ingresses, each *before* the
targeted surface's mutation, fan-out, or persistence side effects. It closes the
series as a paused checkpoint. It authorizes nothing further.

---

## 1. Landed bricks (five)

```text
0122b7e — TormentFabric.ingest refuses CandidateShapedValue passed as text before mutation/fan-out.
b8f9a35 — MemoryGraph.spawn_memory refuses CandidateShapedValue passed as summary before node creation.
e5821bc — MemoryGraph.spawn_memory refuses CandidateShapedValue passed as extra_payload object or immediate extra_payload value before side effects.
8748f61 — EnvironmentStore.write refuses CandidateShapedValue passed as value before RAM/persistence side effects.
d008fb8 — ReferenceStore.ingest refuses CandidateShapedValue in title/body/source_link/source_kind/metadata object/immediate metadata values before RAM/persistence side effects.
```

---

## 2. What this series IS, and is NOT

- This is the **first Gate A Layer 4 containment brick series**.
- It is an **implementation checkpoint**.
- It is **negative containment only**.
- It is **not Gate A wall completion**.
- It **does not create positive authority**.
- It **does not create candidate producer / store / admission / promotion behavior**.
- It **does not open Gate D / runtime / private cognition**.
- It **does not touch database / substrate**.
- It **does not fix direct writer hazards**.

---

## 3. Refused surfaces

```text
ordinary ingest text
MemoryGraph creation summary
MemoryGraph creation extra_payload object / immediate values
EnvironmentStore value
ReferenceStore title / body / source_link / source_kind / metadata object / immediate metadata values
```

---

## 4. Guard character (uniform across the five bricks)

```text
type-only
content-blind
contents-free errors
pre-side-effect for the targeted surface
no recursive scanning
no tag / marker / provenance / key filtering
no schema policing
```

Each guard is a structural `isinstance(..., CandidateShapedValue)` check that
raises a `TypeError` whose message never interpolates the inspected value. Where
a dict field is involved (`extra_payload`, reference `metadata`), the immediate
values are checked key-blind via `.values()` only — non-recursive, no key
inspection. `provenance` is internally constructed by its caller and is **not**
inspected.

---

## 5. Postponed surfaces (recorded, not closed)

```text
ArchiveStore:
- postponed
- lower ordinary-memory relevance
- HTTP cannot carry CandidateShapedValue
- archive text self-defends

links:
- postponed
- structurally open but production-unreachable

update_payload:
- postponed
- current callers internally constructed
- all-values guard had wrong payload-scanning shape
- summary-only mutation guard lower value for now

direct writer hazards:
- parked
- no writer fixes authorized
```

---

## 6. Standing constraints

- **Gate D remains parked** until a separate operator choice reopens it.
- **The next frontier is not authorized by this doc.** Any further brick or
  store target requires separate Codex/operator authorization.
