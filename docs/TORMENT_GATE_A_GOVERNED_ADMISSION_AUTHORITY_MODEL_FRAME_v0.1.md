# TORMENT Gate A — Governed Admission Authority Model Frame v0.1

## 0. Status / authorization scope

**Requirement-level authority model only. This document defines admissibility
authority questions and allowed outcome classes; it selects no actor workflow, API,
schema, store, carrier, runtime path, field, persistence format, or implementation.
Admission remains unbuilt. Any future tests, code, carrier, producer, or crossing
mechanism requires separate Hilmir authorization plus Codex review.**

This is the next Fork 3 design question Codex ruled the safest unresolved one: the
**governed-admission authority model** — it stays requirement-level and defines
*what kind of authority is required for admission* and *what outcomes remain
non-admission*, without touching carrier, store, schema, API, runtime, producer, or
seam mechanics. It answers one question (§3) and nothing else.

Held true throughout: no production code; no tests; no git; no Gate A wall
completion; no Gate D / private cognition; no Gate B implementation; no writer
fixes; no candidate producer / store / carrier / schema / field / API / runtime
wiring; no governed admission or promotion implementation; no database / substrate;
no endpoint / API / schema expansion; no reopening of the Layer 4 brick series; no
audit/inspection turned into control; **no selection** among the authority-class
options (operator-only / user-co-sign / governance-required / future policy) — they
are stated as requirement-level options only.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.
> Automatic remains allowed only where separately ratified. Autonomous remains unopened.

Anchor: `91bd913` (docs: record Gate A Fork 3 design frame).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md     (Document A: A-O3 sole exit; A-D1/A-D2 admission ceiling + admission!=promotion; §8 outcomes; §14 OPEN — admission authority unselected)
docs/TORMENT_GATE_A_CANDIDATE_BOUNDARY_ADMISSION_REQUIREMENTS_v0.1.md    (Layer-3: admission = crossing condition; promotion = separate authority increase; nothing automatic)
docs/TORMENT_GATE_A_FORK3_CANDIDATE_BOUNDARY_GOVERNED_ADMISSION_DESIGN_FRAME_v0.1.md   (Fork 3 frame; §13 named this very question unresolved/gated)
docs/TORMENT_GATE_A_TIER2_ADMISSIBILITY_AND_PRODUCTION_BRICK_DECISION_FRAME_v0.1.md    (Fork 3 is the approved direction)
docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md                                    (Authority class / lifecycle / promotion-rights vocabulary: §7.1)
docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md                                (contest routes authority, never erases provenance; self-issued cannot hard-refuse; refuse is operator-scope)
docs/LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1.md                      (audit observes authority; audit does not become authority; directionality)
```

`[FACT]` Document A §14 explicitly leaves OPEN "what authority the governed
admission crossing itself requires (operator / user-co-sign / governance-required)
— the specific requirement is unselected here." This frame answers that **at the
level of the option space and its requirements only**, and selects none. Where this
frame and any contract appear to differ, the contracts win.

## 2. Doctrine filter

> Admission is a governed **crossing condition**, not a procedure or an actor
> sequence. "What authority is required" is a requirement-level question about which
> *class* of governed decision may admit — not a workflow, an API, or a role table.
> A requirement that could only be met by violating the standing posture is out of
> scope by definition.

## 3. The question this frame answers (and only this)

```text
What authority is required for a candidate-shaped output to cross governed
admission into ordinary memory at no higher than released / low-authority, and
what outcomes remain non-admission?
```

It does not — and must not — answer how to build the crossing, who runs it, what it
records into, or through what surface.

## 4. The admission authority axis (requirement level)

```text
- Admission is a GOVERNED crossing: it requires authority of some governed class to
  occur at all (A-O3 admission is the sole exit; A-D1 caps it at released /
  low-authority). No governed authority -> no admission.
- Candidate-shaped outputs default NOT-SELF-PROMOTABLE: a candidate may never admit
  itself, and admission is never a side effect of being produced, staged,
  recommended, inspected, retrieved, or reinforced (Layer-3 §6; Document A §5/§7;
  Cluster 2 promotion-rights default).
- "Authority required for admission" is a property of the CROSSING, not of the
  candidate's payload, flags, source presence, or production path (A-O1 — authority
  not inferred from payload flags).
- The authority that admits is distinct from the authority that PRODUCES the
  candidate and from the authority that PROMOTES it later (§6).
```

## 5. Allowed outcome classes (admit vs non-admission)

A candidate-shaped output may resolve to exactly one of the classes below. Only the
first is admission; the rest are **non-admission outcomes** and require no admission
authority (Document A §8; Cluster 2 §7.1; Track B contest results).

```text
ADMISSION outcome (requires admission authority — §4/§8):
  admit            -> crosses into ordinary memory at NO HIGHER THAN released /
                      low-authority (A-D1). A ceiling, not a guarantee of ordinary-
                      memory entry. Confers no canon, no identity-shaping weight,
                      no unrestricted promotion rights.

NON-ADMISSION outcomes (no admission; require no admission authority to REMAIN
contained; some require their own authority to DENY — see §8):
  refuse / no-persist  -> admission denied; the candidate does not enter ordinary
                          memory. The event/provenance may remain recorded; refusal
                          authority is itself asymmetric (Track B: self-issued
                          actors cannot hard-refuse; refuse is operator-scope today).
  retire               -> the candidate is dropped/expired; scratch-bounded lifecycle
                          action with no cognition effect (Document A §3 retirement).
  audit-only           -> observable on an audit surface only; not ordinary memory,
                          not cognition-eligible, not prompt/retrieval/MemoryPlan-
                          visible (Document A §8; A-I1).
  operator-visible-only-> visible to operator/governance inspection only; same
                          non-cognition posture as audit-only (Document A §8).
  chamber-only         -> remains inside the bounded private-reflection chamber;
                          never reaches the ordinary fan-out (Document A §8/§10).
```

`[INVARIANT]` Stricter-than-released outcomes (refuse / retire / audit-only /
operator-visible-only / chamber-only) **require no admission** and are the default
safe resting outcomes; admission is the *only* outcome that needs admission
authority and the *only* one that touches ordinary memory.

## 6. Admission vs promotion (distinct authority decisions)

```text
- Admission authority lands a candidate at NO HIGHER THAN released / low-authority
  and confers nothing beyond that ceiling (A-D1).
- PROMOTION is a SEPARATE, separately-authorized authority increase toward
  identity-shaping or canon (A-D2). Admission never implies, triggers, or unlocks
  promotion; promotion authority is a different question with its own governed
  crossing.
- Any later revocation / reclassification / reversal likewise requires its OWN
  separate governed crossing (A-D2). No direct-reversal semantics.
- Promotion-rights vocabulary (Cluster 2 §7.1: self-promotable / operator-required /
  user-co-sign / governance-required / not-promotable) is the SHARED option space;
  admission and promotion each draw from it INDEPENDENTLY and neither selection is
  made here.
```

## 7. Recommendation / contest / inspection are not admission authority

```text
- RECOMMENDATION stages that an admission COULD occur; it is staging only, never
  application (Document A §3; Stage A O4). A recommendation does not admit.
- CONTEST routes a candidate's authority DOWNWARD or holds it; it never raises
  authority, never erases provenance, and self-issued contests cannot hard-refuse
  (Track B Invariants 10/16). Contest is not admission and is not promotion.
- INSPECTION observes candidates read-only for audit; it is not projection and not
  control (A-I1/A-C3; Document A §9). Inspectability must not itself be a re-entry
  path.
- AUDIT OBSERVES AUTHORITY; AUDIT DOES NOT BECOME AUTHORITY (Ledger doctrine §2/§3).
  Admission authority must NOT be derivable from audit/inspection history: no
  "previously audited / previously inspected -> auto-admit" pathway, and no
  frequency / recency / density of observation functioning as a shadow admit signal
  (Ledger §3 directionality — an authority gate may read content, never audit of
  itself).
```

## 8. Requirement-level authority-class options (NONE selected)

The authority that may admit is one of the option classes below — **stated as
requirement-level options only; this frame selects none** (Document A §14 OPEN).
Each maps onto Cluster 2 §7.1 promotion-rights vocabulary.

```text
OPTION                 Cluster 2 mapping        Requirement-level character (no mechanism)
operator-only          operator-required        a single governed operator decision admits.
user co-sign           user-co-sign             admission requires a user co-signature alongside
                                                a governed decision (two-party).
governance-required    governance-required      admission requires a governed governance condition
                                                (e.g. a policy / quorum / gate) rather than a single actor.
future policy class    (future)                 a later-ratified policy class not yet named; reserved,
                                                not opened.
```

`[REQUIREMENT]` Whichever option is later chosen, the admission authority must
satisfy all of:

```text
- explicit, recorded, and contestable (Document A A-D1; Layer-3 §4.2) — "recorded"
  is a requirement only; no format / log / event / store / persistence selected.
- not-self-promotable: the candidate's producer is never the admitting authority
  (§4).
- not automatic, retrieval-driven, reinforcement-driven, or observation-driven
  (Layer-3 §6; Ledger §3).
- capped at released / low-authority; any higher posture is a separate promotion
  authority (§6).
- the authority to REFUSE / hard-deny is itself governed and asymmetric — in
  existing doctrine self-issued actors cannot hard-refuse; refuse is operator-scope
  (Track B Invariant 16). The admission authority model inherits that asymmetry as a
  requirement, not a mechanism.
```

The **force-bypass anti-pattern is explicitly out of bounds**: a request-supplied
flag that elevates authority while bypassing the governed decision (the `/promote`
`force` non-conformance) is exactly what governed admission authority must NOT be.

## 9. Existing authority crossings as evidence (not targets)

Read-only evidence that the option space is already realized in TORMENT crossings —
**cited as precedent only; none is selected, targeted, modified, or proposed as the
admission mechanism**:

```text
- operator-only precedent      -> /workspace/domain/proposals/decide (decide_proposal);
                                  /workspace/{bridges,motif_merges,conflicts}/decide;
                                  governance set (set_governance_flags). Explicit operator decisions.
- governance / quorum precedent -> /agent/propose_share + process_proposals (share-proposal
                                  path; distinct-agent convergence/quorum + governance gates).
- anti-pattern (NOT a model)    -> /promote force (promote_chunk_endpoint req.force) bypasses the
                                  evaluator's decision to write canon=True — a force-bypass, the
                                  opposite of governed admission. Stays parked; not fixed here.
```

These ground that operator-only, governance-required, and quorum-shaped authority
all exist in the codebase; the admission authority model **borrows the option
shapes as evidence, not the surfaces as targets.**

## 10. Future proof obligations (before any implementation)

A future, separately-authorized implementation of the admission authority decision
would have to **prove**, by construction — **stating an obligation authorizes
nothing**:

```text
- the admitting authority is explicit, recorded, contestable, and distinct from the
  candidate's producer (not-self-promotable).
- admission lands at no higher than released / low-authority; no path reaches canon
  / identity-tier via admission alone (admission != promotion).
- non-admission outcomes (refuse / retire / audit-only / operator-visible-only /
  chamber-only) require no admission and leak nothing into ordinary cognition.
- no admit/deny decision is derivable from audit/inspection history (Ledger
  directionality); recommendation/contest/inspection cannot admit or promote.
- refusal authority asymmetry holds (self-issued cannot hard-refuse).
- proofs land tests/source-first before any production code (the Seam B/C
  discipline), and most require a carrier/producer to exist first — so they are
  downstream of separate carrier authorizations.
```

## 11. Unresolved and separately gated

```text
- WHICH authority-class option admission requires (operator-only / user-co-sign /
  governance-required / future policy) — Document A §14 OPEN; UNSELECTED here.
- Per-artifact-class admission refinement (contradiction / risk-flag vs proposed
  write) — Document A §14 OPEN.
- The candidate-boundary REPRESENTATION / carrier / store / "recorded" format —
  Stage B / P6; not selected.
- The live candidate producer — Document B interior; does not exist / not authorized.
- The runtime admission decision point / consultation mechanism — Layer 4; not
  entered (Cluster 2 v0.2 / Track B v0.2 territory, not opened).
- The four parked writer non-conformances (incl. /promote force) — stay parked; not
  fixed or reclassified here.
- Gate D (Layer 5), database / substrate, Stage B — separately authorized.
```

## 12. What this authority model does and does not authorize

```text
DOES:    define the admission authority QUESTION and its requirement-level option
         space (§4/§8); enumerate allowed outcome classes (§5); fix admission !=
         promotion (§6) and recommendation/contest/inspection != authority (§7);
         cite existing crossings as evidence (§9); list proof obligations (§10) and
         what stays gated (§11).

DOES NOT (and does not authorize by implication):
  - select any authority-class option, actor, workflow, role table, or policy
  - production code; tests; git
  - API / schema / store / carrier / runtime path / field / persistence format /
    candidate id / admission or promotion implementation
  - Gate A wall completion; Gate D; Gate B implementation; writer fixes (incl.
    /promote force)
  - candidate producer / store; database / substrate; Stage B; Document B interior
  - endpoint / API / schema expansion; reopening the Layer 4 brick series
  - audit / inspection turned into control; any "audited -> auto-admit" path
  - any positive authority crossing
```

## 13. Anti-drift footer

GATE A GOVERNED ADMISSION AUTHORITY MODEL FRAME / REQUIREMENT-LEVEL ONLY /
NON-AUTHORIZING / SELECTS NOTHING. It answers one question — what authority is
required to admit a candidate-shaped output into ordinary memory at no higher than
released / low-authority, and what outcomes remain non-admission. **Admit** is the
only admission outcome (capped at released / low-authority, not-self-promotable,
explicit / recorded / contestable); **refuse / retire / audit-only /
operator-visible-only / chamber-only** are non-admission outcomes needing no
admission. **Admission != promotion** (promotion is a separate, separately-authorized
authority increase); **recommendation / contest / inspection are not admission
authority** and **audit observes authority, never becomes it**. The authority-class
options — **operator-only / user-co-sign / governance-required / future policy** —
are **requirement-level options only; none is selected** (Document A §14 stays
OPEN). The force-bypass anti-pattern is out of bounds; existing crossings are
evidence, not targets. **This document defines admissibility authority questions and
allowed outcome classes; it selects no actor workflow, API, schema, store, carrier,
runtime path, field, persistence format, or implementation. Admission remains
unbuilt. Any future tests, code, carrier, producer, or crossing mechanism requires
separate Hilmir authorization plus Codex review.** Gate A stays paused; Gate D
parked; the parked writer non-conformances stay parked. Guidance not control; audit
observes authority and does not become authority; nothing rewrites identity / canon
/ seed / soul.
