# TORMENT Gate A — Fork 3 Per-Artifact Admission Refinement Frame v0.1

## 0. Status / authorization scope

**Requirement-level per-artifact admission refinement only. This document classifies
possible candidate artifact outcomes and anti-collapse rules; it selects no carrier,
store, schema, field, enum, ID, API, persistence format, runtime path, producer,
authority option, admission workflow, or promotion mechanism. Admission remains
unbuilt. Any concrete representation, tests, code, or crossing mechanism requires
separate Hilmir authorization plus Codex review.**

This is the Fork 3 sub-question Codex selected next (Option 2): refine, **per future
candidate-shaped artifact class**, which admission outcomes are allowed, forbidden,
or stricter-than-admission. It directly answers Document A §14's first OPEN
question — "does the admission default need per-artifact-class refinement (e.g.,
contradictions / risk-flags vs. proposed writes), given the now-ratified
stricter-than-released outcomes?" — at requirement level only. It answers one
question (§3) and nothing else.

Held true throughout: no production code; no tests; no git; no Gate A wall
completion; no Gate D / private cognition; no Gate B implementation; no writer
fixes; no candidate producer / store / carrier / schema / field / enum / ID / API /
runtime wiring; no governed admission or promotion implementation; no
authority-option selection; no database / substrate; no endpoint / API / schema
expansion; no reopening of the Layer 4 brick series; no audit/inspection turned into
control.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `d48325a` (origin/main; Gate A Fork 3 pre-carrier constraints recorded).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md   (Document A: §3/§4 artifact taxonomy; §8 admission ceiling + stricter outcomes; A-O2/A-O3, A-D1/A-D2, A-I1/A-I2/A-I3, §14 OPEN)
docs/TORMENT_GATE_A_CANDIDATE_BOUNDARY_ADMISSION_REQUIREMENTS_v0.1.md  (Layer-3: admission = crossing condition; nothing automatic; admission is a ceiling not a guarantee)
docs/TORMENT_GATE_A_FORK3_CANDIDATE_BOUNDARY_GOVERNED_ADMISSION_DESIGN_FRAME_v0.1.md   (boundary = containment property)
docs/TORMENT_GATE_A_GOVERNED_ADMISSION_AUTHORITY_MODEL_FRAME_v0.1.md   (outcome classes; authority option UNSELECTED; admission != promotion)
docs/TORMENT_GATE_A_FORK3_WALL_SEAM_SELECTION_FRAME_v0.1.md            (layered topology; admission crossing held separate)
docs/TORMENT_GATE_A_PRE_CARRIER_REPRESENTATION_CONSTRAINTS_FRAME_v0.1.md   (representation unbuilt; inert; must not become authority)
docs/TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md   (wall boundary; §4 artifact-class proof obligations)
```

Where this frame and any contract appear to differ, the contracts win.

## 2. Doctrine filter

> Refining outcomes **per artifact class** is a requirement-level classification, not
> a status enum, a lifecycle, or a workflow. Saying "a contradiction-flag should
> default stricter than a proposed write" assigns a *requirement*, not a field value.
> No class reaches authority by being classified here.

## 3. The question this frame answers (and only this)

```text
For each future candidate-shaped artifact class, what admission outcomes are
allowed, forbidden, or stricter-than-admission at requirement level?
```

All classes and outcomes below are **future / not-yet-existing**: no candidate
producer exists or is authorized (Seam B/C characterizations are evidence of the
current producerless terrain, not targets).

## 4. Candidate artifact classes (requirement level; Document A §3/§4)

Requirement-level classes — **not enums, IDs, or schema**:

```text
C1  raw reflection artifact         unsummarized intermediate reasoning; ephemeral by default;
                                    never auto-durable.
C2  private thread-continuity state bounded soft chamber-internal continuity; NOT a candidate by
                                    existing; soft / inspectable / contestable / resettable; never
                                    canonical or authority-bearing; never pinned (Stage A O6).
C3  reflection synthesis            compressed chamber product; becomes a candidate ONLY when
                                    explicitly staged; inert until then.
C4  unadmitted candidate            an explicitly-staged item, in one of three shapes:
      C4a proposed write / staged synthesis   a positive content proposal.
      C4b contradiction / risk flag           a warning / objection (meta, not content).
      C4c unresolved question                 an open question (meta, not content).
```

## 5. Outcome categories (requirement level; Document A §8 + authority model)

Requirement-level outcome *categories* — **not a status field / enum / schema**. Only
the first is admission; the rest are **stricter-than-admission** and require no
governed admission crossing.

```text
admit (<= released / low-authority)   the ONLY admission outcome; a CEILING, not a guarantee of
                                      ordinary-memory entry; confers no canon / identity weight /
                                      promotion rights (A-D1).
chamber-only                          stays inside the bounded chamber; never reaches the fan-out.
audit-only                            observable on an audit surface only; not ordinary memory.
operator-visible-only                 operator / governance inspection only; not ordinary memory.
refused / no-persist                  admission denied; refusal authority is governed/asymmetric
                                      (operator-scope today, Track B Invariant 16).
retired                               dropped / expired; scratch-bounded; no cognition effect.
```

## 6. Per-artifact refinement (the answer to Document A §14)

For each class: allowed outcomes, forbidden outcomes, and the stricter-than-admission
default. **The refinement's load-bearing distinction: positive proposals (C4a) are
the class for which "admit at released/low-authority" is the meaningful outcome;
meta candidates (C4b/C4c) default STRICTER than admission, because materializing a
warning or a question as ordinary cognition-shaping memory is the wrong shape.**

```text
C1 raw reflection artifact
  allowed:                chamber-only; retired.
  stricter default:       chamber-only / retired (ephemeral).
  forbidden:              admit (must first become C3 and be explicitly staged as C4 — no
                          shortcut to ordinary memory); canon / identity / seed / long-half-life;
                          any ordinary-memory persistence; retrieval / prompt / MemoryPlan
                          visibility; promotion.

C2 private thread-continuity state
  allowed:                chamber-only (shapes only its own later synthesis inside the chamber).
  stricter default:       chamber-only; inspectable / contestable / resettable.
  forbidden:              admit by existing (not a candidate unless explicitly staged as C3->C4);
                          leaking into ordinary cognition; becoming canonical / authority-bearing;
                          being pinned; promotion.

C3 reflection synthesis
  allowed (unstaged):     chamber-only / inert.
  on explicit staging:    becomes C4 and follows C4's outcomes — staging is not admission.
  forbidden:              admission while unstaged; becoming a candidate by mere existence;
                          auto-durability.

C4a proposed write / staged synthesis
  allowed:                admit at <= released / low-authority (via a governed crossing); OR any
                          stricter-than-admission outcome (chamber-only / audit-only /
                          operator-visible-only / refused / retired).
  stricter default:       available as the safe outcome whenever the crossing's authority is absent.
  forbidden:              canon / identity-tier / seed / long-half-life (A-O2); admission ABOVE
                          released / low-authority; promotion via admission (A-D2); self-admission
                          (not-self-promotable).

C4b contradiction / risk flag
  allowed:                audit-only; operator-visible-only; refused; retired; chamber-only.
  stricter default:       audit-only / operator-visible-only (it is for governance attention, not
                          for becoming ordinary cognition-shaping memory).
  admit-to-ordinary:      QUESTIONABLE in shape — permitted ONLY if a future governed decision ever
                          explicitly allows it, and then NEVER above released / low-authority and
                          NEVER as the default. Flagged as the residual open sub-question (§9).
  forbidden:              canon / identity / promotion; RAISING authority (routes DOWN only, Track B
                          Invariant 10); becoming ordinary cognition-shaping memory by default;
                          self-admission.

C4c unresolved question
  allowed:                audit-only; operator-visible-only; retired; chamber-only.
  stricter default:       audit-only / operator-visible-only.
  admit-to-ordinary:      QUESTIONABLE in shape — same posture as C4b; not the default; residual
                          open sub-question (§9).
  forbidden:              canon / identity / promotion; raising authority; becoming ordinary
                          cognition-shaping memory by default; self-admission.
```

## 7. Anti-collapse rules

```text
AC-1  creation != admission != promotion, per class. Existence, staging, recommendation, and
      inspection admit and promote nothing.
AC-2  C1 must traverse C3 -> explicit staging (C4) -> governed crossing; no shortcut to ordinary
      memory exists for raw reflection.
AC-3  stricter-than-admission outcomes (chamber-only / audit-only / operator-visible-only /
      refused / retired) are NOT lesser admissions: they require no crossing and confer no
      ordinary-memory entry. "Stricter" is not "a little bit admitted."
AC-4  admit-at-released != promotion. No class reaches canon / identity-tier via admission; that
      is always a separate governed promotion crossing (A-O2 / A-D2).
AC-5  meta candidates (C4b / C4c) route authority DOWN only; an outcome may never raise a
      candidate's authority above its origin posture (Track B Invariant 10).
AC-6  the outcome is never inferred from payload flags, mtype, tier, or the artifact's own
      production path; candidates are not-self-promotable (A-O1).
AC-7  recovery retains class (A-I2): recovering a retired / refused artifact restores its prior
      contained / audit posture only — never admits, promotes, projects, or makes
      cognition-eligible.
AC-8  inspection of any class is observation-only and never control; no "inspected / audited ->
      auto-admit / auto-route" path (A-I1; Ledger directionality).
AC-9  these per-artifact outcomes are requirement-level CATEGORIES — not a status enum, field,
      ID, schema, or lifecycle implementation.
```

## 8. Preserved framings

```text
- The governed-admission AUTHORITY MODEL stays requirement-level only: the authority-class
  option (operator-only / user-co-sign / governance-required / future policy) remains UNSELECTED;
  admission remains UNBUILT. This refinement presupposes neither.
- The candidate BOUNDARY stays a containment property; the REPRESENTATION stays unbuilt and inert
  (pre-carrier constraints frame). No class above implies a store / object.
- The LAYERED seam topology stays intact: the governed admission crossing is held SEPARATE from
  the containment seams; per-artifact outcomes attach to the crossing, not to a seam.
- The LAYER 4 brick series stays CLOSED: no reopening, no second brick series. The parked writer
  non-conformances (gravity_correction canon=True, _maybe_emit_identity_anchor, /promote force,
  mood_drift -> canon) stay parked, named not fixed; they are the writer-authority axis these
  classes must never reach via admission (A-O2).
```

## 9. Future proof obligations and unresolved

```text
- RESIDUAL OPEN SUB-QUESTION: whether C4b (contradiction / risk flag) and C4c (unresolved
  question) may EVER admit-to-ordinary-memory, or are always stricter-than-admission. This frame
  sets their DEFAULT to stricter-than-admission and forbids any default admission; the final
  decision is deferred (Document A §14 stays partly OPEN).
- which authority-class option admission requires — Document A §14 OPEN; UNSELECTED.
- per-class contest / recovery specifics depend on Track B runtime (deferred; Track B v0.1 is
  doctrine-only).
- a future authorized implementation must PROVE (tests/source-first, once a producer + crossing
  exist): each class reaches only its allowed outcomes; no class reaches canon / identity via
  admission; stricter-than-admission outcomes leak nothing into ordinary cognition; outcomes are
  not inferred from payload; recovery retains class; inspection drives no control.
- DEFERRED: concrete representation / carrier; store / schema / fields / enums / IDs; persistence
  format; API / runtime path; live producer (Document B interior); admission workflow / crossing
  mechanics (Layer 4); promotion mechanism; tests / code; database / substrate; Stage B; Gate D.
```

## 10. Non-authorization

```text
This document DOES NOT, and does not authorize by implication:
  - select / design a carrier, store, schema, field, enum, ID, API, persistence format, runtime
    path, producer, admission workflow, or promotion mechanism
  - select an authority-class option
  - production code; tests; git
  - Gate A wall completion; Gate D; Gate B implementation; writer fixes (incl. /promote force)
  - candidate producer / store; database / substrate; Stage B; Document B interior
  - endpoint / API / schema expansion; reopening the Layer 4 brick series; another brick series
  - audit / inspection turned into control; any positive authority crossing
  - any actual admission, refusal, retirement, or promotion of any artifact (none exist to act on)
```

## 11. Anti-drift footer

GATE A FORK 3 — PER-ARTIFACT ADMISSION REFINEMENT FRAME / REQUIREMENT-LEVEL ONLY /
CLASSIFIES, SELECTS NOTHING. It refines, per future candidate-shaped artifact class
(raw reflection artifact; private thread-continuity state; reflection synthesis;
unadmitted candidate as proposed-write / contradiction-risk-flag / unresolved
question), which outcomes are allowed, forbidden, or stricter-than-admission — with
the load-bearing distinction that **positive proposals may admit at <= released /
low-authority while meta candidates (contradiction / risk flag / question) default
STRICTER than admission**, answering Document A §14. **Admit is the only admission
outcome (capped at released / low-authority, never canon / identity / promotion);
chamber-only / audit-only / operator-visible-only / refused / retired are
stricter-than-admission and need no crossing.** Anti-collapse rules keep creation !=
admission != promotion, stricter != lesser-admission, meta-candidates route authority
DOWN only, recovery retains class, and inspection never becomes control. The
authority option stays UNSELECTED, the representation UNBUILT, the layered topology
intact, the Layer 4 series CLOSED, and the parked writer non-conformances PARKED.
**This document classifies possible candidate artifact outcomes and anti-collapse
rules; it selects no carrier, store, schema, field, enum, ID, API, persistence
format, runtime path, producer, authority option, admission workflow, or promotion
mechanism. Admission remains unbuilt. Any concrete representation, tests, code, or
crossing mechanism requires separate Hilmir authorization plus Codex review.** Gate A
stays paused; Gate D parked. Guidance not control; audit observes authority and does
not become authority; nothing rewrites identity / canon / seed / soul.
