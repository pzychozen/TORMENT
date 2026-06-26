# TORMENT Gate A — Fork 3 Wall Seam Selection Frame v0.1

## 0. Status / authorization scope

**Requirement-level seam selection only. This document may assign proof obligations
to seam families and sequence later design questions, but it selects no carrier,
store, schema, field, API, runtime path, producer, admission workflow, promotion
workflow, or implementation mechanism. Seam selection is not wall completion. Any
tests, code, carrier, producer, admission mechanism, or runtime wiring requires
separate Hilmir authorization plus Codex review.**

This is the Fork 3 sub-question Codex ruled safest next: the **wall seam topology**.
It determines, at requirement level, *which seam family carries which obligation*
and *whether a layered topology is required* — without choosing any mechanics. It
answers one question (§3) and nothing else.

Held true throughout: no production code; no tests; no git; no Gate A wall
completion; no Gate D / private cognition; no Gate B implementation; no writer
fixes; no candidate producer / store / carrier / schema / field / API / runtime
wiring; no governed admission or promotion implementation; no authority-option
selection; no database / substrate; no endpoint / API / schema expansion; no
reopening of the Layer 4 brick series; no audit/inspection turned into control.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `5ba0902` (docs: record Gate A admission authority model).

## 1. Subordination (and relationship to the Layer-2 comparison)

Subordinate to, and may not contradict:

```text
docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md   (Document A: A-C1/A-C2/A-C3, A-O1/A-O2/A-O3, A-I1, A-D1/A-D2, A-L1)
docs/TORMENT_GATE_A_SEAM_SELECTION_COMPARISON_v0.1.md                  (Layer-2: the four loci, NON-SELECTING, single-vs-multi left OPEN)
docs/TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md   (wall boundary; §3 roots; §6 proof bars)
docs/TORMENT_GATE_A_FORK3_CANDIDATE_BOUNDARY_GOVERNED_ADMISSION_DESIGN_FRAME_v0.1.md   (boundary = property; admission = crossing condition)
docs/TORMENT_GATE_A_GOVERNED_ADMISSION_AUTHORITY_MODEL_FRAME_v0.1.md   (admission authority = requirement-level options only)
docs/TORMENT_GATE_A_WALL_ENFORCEMENT_PATH_AUTHORIZATION_REVIEW_v0.1.md (Seam B selected as first characterization slice; Tier-2 deferred)
```

**Relationship note (anti-duplication).** A **Layer-2 Seam-Selection Comparison
already exists** and is explicitly **NON-SELECTING**: it compares four loci
(origin-side containment, the `TormentFabric.ingest` chokepoint, the
writer-authority gate, the inspection surface), records that **none is sufficient
alone**, and **deliberately leaves the single-locus vs multi-locus question OPEN**
for a later authorized decision. This Fork 3 frame is that later authorized step: it
**does not re-compare the loci or contradict the Layer-2 doc** — it makes the
**requirement-level topology determination** the Layer-2 doc deferred (which
obligation lands on which seam family; whether layering is required; §6), still
**selecting no mechanics**. Where this frame and any contract appear to differ, the
contracts win. It also sits below the Layer-1 producer-shaped contract; no producer
is assumed or created.

## 2. Doctrine filter

> A seam is a requirement-level **locus an obligation can be held at** — not a
> mechanism, store, or runtime path. Allocating an obligation to a seam family is a
> topology statement, not a build. A seam that could only carry an obligation by
> violating the standing posture cannot honestly carry it.

## 3. The question this frame answers (and only this)

```text
What requirement-level wall seam topology should govern future Gate A work?
  -> Which seam(s) carry which obligations among producer-side containment,
     ingest-entry structural gate, writer-authority gate, and inspection surface,
     and what must remain deferred until carrier / producer / admission mechanics
     are separately authorized?
```

It does not — and must not — choose carriers, mechanics, runtime, or who builds any
seam.

## 4. Candidate seam families (requirement level)

Reconciled with the Layer-2 loci, the enforcement-path proposal seams, and the
characterized evidence. **Naming a family neither builds nor selects a mechanism.**

```text
FAMILY                         Layer-2 locus / proposal seam     Characterized evidence (NOT a target)
producer-side containment      Locus 1 / Seam A                  (none yet — no producer exists)
ingest-entry structural gate   Locus 2 / Seam B                  aa7befd Seam B ingress-shape (terrain only)
writer-authority gate          Locus 3 / Seam C (Gate B)         6895b8e Seam C / A-O2 evidence
inspection surface             Locus 4                           0dbe7cc / c73add5 inspection / projection-safety
layered topology               (the multi-locus option)          — (the topology question itself)
```

## 5. Obligation allocation — what each seam family CAN and CANNOT carry

Per Document A obligations. **CAN carry** = the obligation can honestly be held at
that locus at requirement level; **CANNOT honestly carry** = holding it there would
overclaim or violate the doctrine filter.

```text
producer-side containment (Locus 1 / Seam A)
  CAN carry:    A-C1 non-reachability held AT ORIGIN; A-C2 structural (not tag-honoring)
                at the point of production.
  CANNOT carry: downstream ARRIVAL coverage at the fan-out root by itself; A-O2 write-side
                authority; A-O3/A-D1/A-D2 admission (it cannot establish how anything
                legitimately LEAVES containment); A-I1 governed inspection.
  Note:         presupposes a producer that does not exist / is not authorized.

ingest-entry structural gate (Locus 2 / Seam B)
  CAN carry:    A-C1/A-C2 at the ORDINARY-INGEST FAN-OUT ROOT (arrival half) — the
                source-grounded sole-entry terrain (aa7befd), held at the ingest entry.
  CANNOT carry: A-C1 ALONE (it concerns arrival, not origin; a chokepoint with nothing
                upstream to contain is not a wall); A-O2 (write-side, different axis);
                admission-sole-exit (no crossing here); inspection.
  Note:         terrain fact, not a wall; characterized as ingress shape only.

writer-authority gate (Locus 3 / Seam C — Gate B territory)
  CAN carry:    A-O1 class-bound writer authority; A-O2 no silent canon/identity from
                cognition; contributes to A-D2 admission != promotion on the write side.
  CANNOT carry: candidate CONTAINMENT (A-C1/A-C2 — it governs authority CLASS, not the
                non-reachability of candidate-shaped outputs); admission as the exit.
  Note:         write-side, sits in later Gate B; the four parked writer non-conformances
                stay parked (incl. /promote force) — named, not fixed.

inspection surface (Locus 4)
  CAN carry:    A-I1 inspection != projection; A-C3 inspectable-without-re-entry; part of
                A-L1 lineage/audit visibility.
  CANNOT carry: any CONTAINMENT obligation (it observes, it does not contain); it must
                never become control (Ledger directionality).

CROSSING obligations (NOT a containment seam):
  A-O3 admission-sole-exit, A-D1 admission ceiling, A-D2 admission != promotion belong to
  the candidate boundary + governed admission CROSSING (Layer 3 / carrier+producer+admission),
  NOT to any single containment seam. No seam family can honestly carry "admission is the
  sole exit" until the crossing exists. DEFERRED (§8).
```

## 6. Topology determination — layered is required; no single seam carries the wall

**Determination (requirement-level, no mechanics): a LAYERED / multi-seam topology
is required. No single seam family can carry the Gate A wall.**

```text
- A-C1/A-C2 containment is layered across producer-side (origin) AND ingest-entry
  (arrival): neither half is sufficient alone (Layer-2 §5). The wall's containment
  spine is these two together, once a producer exists.
- A-O1/A-O2 writer authority is a SEPARATE axis carried by the writer-authority gate
  (Gate B), not by the containment seams.
- A-I1/A-C3 inspection is a SEPARATE observation-only surface, never a container and
  never control.
- A-O3/A-D1/A-D2 admission is a CROSSING, not a seam — it is how a contained
  candidate legitimately leaves, and it is deferred to the candidate boundary +
  governed admission authorization.
```

So the governing topology is: **containment spine (producer-side + ingest-entry) +
writer-authority gate + inspection surface + a governed admission crossing** —
four requirement-level roles, none of which collapses into another, and the crossing
held separate. This determines the *shape* future Gate A work must respect; it
selects **no** mechanism for any role.

## 7. Sequencing of later design questions (requirement-level)

The anti-authorization scope permits sequencing. Requirement-level order only — each
step is separately gated and authorizes nothing here:

```text
1. (this frame)  wall seam topology — DETERMINED layered (§6).
2. carrier / representation of the candidate boundary — DEFERRED; needs separate
   authorization (Stage B / P6). Now well-posed: it must serve the layered topology.
3. live candidate producer — DEFERRED; Document B interior; required before the
   producer-side containment seam can be proven against a real candidate.
4. governed admission crossing mechanics — DEFERRED; Layer 4 runtime; the crossing
   obligations (A-O3/A-D1/A-D2) attach here.
5. per-artifact admission refinement — DEFERRED; depends on (1)+(2)+(4): admission
   outcomes mean different things per the layered topology, so this is now
   well-posed but not opened.
```

Codex's reasoning is preserved: carrier/representation is sequenced AFTER topology
(so an object is not designed before its boundary is known); the live-producer
boundary stays runtime-adjacent and deferred; per-artifact refinement depends on
this topology.

## 8. What remains deferred until carrier / producer / admission mechanics are authorized

```text
- the candidate-boundary CARRIER / representation / store / "recorded" format — Stage B/P6.
- the live candidate PRODUCER — Document B interior; none exists / authorized.
- the governed ADMISSION crossing implementation and the A-O3/A-D1/A-D2 crossing obligations.
- which AUTHORITY-CLASS option admission requires — Document A §14 OPEN; unselected.
- per-artifact admission refinement (contradiction / risk-flag vs proposed write).
- ALL mechanics for every seam role (containment object, gate, inspection surface, crossing).
- the four parked writer non-conformances (incl. /promote force) — stay parked, not fixed.
- Gate D (Layer 5), database / substrate, Stage B — separately authorized.
```

## 9. Preserved framings

```text
- Seam B (aa7befd) and Seam C (6895b8e) remain CHARACTERIZED EVIDENCE — terrain /
  A-O2 inventory respectively — NOT implementation targets. This frame allocates
  obligations to their seam families; it does not build or wire either.
- The governed-admission authority model stays REQUIREMENT-LEVEL ONLY: admission is a
  governed crossing whose authority-class option is unselected; admission != promotion;
  recommendation / contest / inspection are not admission authority; audit observes
  authority and does not become authority.
- The candidate boundary stays a CONTAINMENT PROPERTY (Fork 3 design frame), not a
  store; this frame's "containment spine" language is topology, not an object.
```

## 10. What seam selection does and does not authorize

```text
DOES:    determine, at requirement level, the wall seam TOPOLOGY (layered §6);
         allocate which Document A obligation each seam family can / cannot carry
         (§5); hold the admission CROSSING separate from the containment seams; and
         SEQUENCE later design questions (§7).

DOES NOT (and does not authorize by implication):
  - select any carrier / store / schema / field / API / runtime path / producer /
    admission workflow / promotion workflow / implementation mechanism for ANY seam
  - select an authority-class option
  - production code; tests; git
  - Gate A wall completion; Gate D; Gate B implementation; writer fixes (incl. /promote force)
  - candidate producer / store; database / substrate; Stage B; Document B interior
  - endpoint / API / schema expansion; reopening the Layer 4 brick series
  - audit / inspection turned into control; any positive authority crossing
```

## 11. Anti-drift footer

GATE A FORK 3 — WALL SEAM SELECTION FRAME / REQUIREMENT-LEVEL ONLY / SELECTS NO
MECHANICS. It answers one question — the wall seam topology — by **determining that a
layered / multi-seam topology is required**: a containment spine (**producer-side +
ingest-entry**, jointly carrying A-C1/A-C2, neither sufficient alone), a separate
**writer-authority gate** (A-O1/A-O2, Gate B), a separate **inspection surface**
(A-I1/A-C3, observation-only), and a separate **governed admission crossing**
(A-O3/A-D1/A-D2) held apart from the seams and deferred. No single seam carries the
wall. It **consolidates, without contradicting,** the Layer-2 comparison that left
single-vs-multi open, and **sequences** carrier → producer → admission → per-artifact
refinement as separately-gated later steps. Seam B and Seam C stay characterized
evidence, not targets; the admission authority model stays requirement-level only.
**This document may assign proof obligations to seam families and sequence later
design questions, but it selects no carrier, store, schema, field, API, runtime path,
producer, admission workflow, promotion workflow, or implementation mechanism. Seam
selection is not wall completion. Any tests, code, carrier, producer, admission
mechanism, or runtime wiring requires separate Hilmir authorization plus Codex
review.** Gate A stays paused; Gate D parked; the parked writer non-conformances stay
parked. Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.
