# TORMENT — Document A Admission-Crossing Q4: P4-Relation Frame v0.1

**Status:** DOCS-ONLY requirement-level frame. **Non-authorizing, non-designing, non-implementing.** This
is **Q4 only** from the design-framing scope frame
(`docs/TORMENT_DOCUMENT_A_ADMISSION_CROSSING_DESIGN_FRAMING_SCOPE_FRAME_v0.1.md`). It states the
**requirement-level relation** between a future Document A governed admission crossing + candidate carrier
and the **P4 O1/O2 reader-trace / source-sameness** obligations: *what must be exposed / made consultable*
so a later P4 reader-trace can bind to a source across `update_payload` canonical-last reappend and `eid`
reuse. It stays **relation-level** — it never says *how* a reader computes, compares, projects, admits, or
decides. It **inherits P4 O1–O5 and the P4 source-sameness policy frame unchanged** and **implements or
amends none of them**. It reopens neither Q1, Q2, nor Q3 and answers no other question (Q5–Q7). Navigation /
requirement aid only.

**Authority note:** Document A (containment wall / admission edge), the Gate A governed-admission
authority-option selection (`operator-only` floor), the Gate A candidate-representation selection +
pre-carrier constraints, the Q1 carrier-properties frame, the Q2 crossing-record frame, the Q3
floor-binding frame, the P4 Reader/Projection-Safety Contract (O1–O5 + non-coercion invariant), the P4
source-sameness policy frame, the Gate B writer-authority doctrine, Document B, the Ledger
Observational-Boundary, the substrate-readiness memo / Stage-B opening decision record, and
`PROJECT_ORIENTATION_MAP.md` §0 remain source of truth. This frame reads them; it amends none. **P4 O1–O5,
the non-coercion invariant, and the `diagnostic_only` ratified posture are inherited exactly as written;
this frame does not implement, gate, or amend them.**

**Doctrine (carried, exact):**

> Memory may guide context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.
> Presence of a reusable local `eid` is insufficient.

---

## 1. Status / non-authorizing, relation-level Q4-only banner

Exposure-relation statement only. Naming a required *exposure* here neither designs nor selects the carrier
or crossing that provides it, and picks no reader, policy, comparison method, projection, token,
fingerprint, lineage, field, schema, enum, ID, or eligibility gate. Saying the future crossing+carrier must
**expose enough relation evidence** for a later P4 reader-trace / source-sameness obligation states a
**requirement on the exposed relation**; it does **not** author the reader that would consume it, nor decide
what that reader concludes. No admission crossing / reader / policy / mechanism / runtime / persistence is
created or implied. This frame answers **Q4 only**; Q5–Q7 remain open and unanswered, and neither Q1, Q2,
nor Q3 is re-opened. The full non-authorization list is §6.

## 2. Inherited and scoped inputs (carried, NOT re-decided; and the Q4 boundary)

- **Q4 named by the scope frame** as the P4-relation question — a member of the relation tier (Q4/Q5/Q6)
  that follows the closed carrier-properties (Q1) and crossing (Q2/Q3) work. This frame is that question's
  requirement-level answer *shape* — a set of exposure obligations, not a design.
- **Q1 carrier-properties CLOSED and INHERITED, not re-opened.** Q1 states the *intrinsic* properties any
  future carrier must have (source-stability/eid-independence, reappend/reuse survivability, same-source
  determinability, …). **Q4 is complementary, not duplicative:** Q1 asks what a carrier must *be*; Q4 asks
  what the carrier+crossing must *expose / make consultable to a later P4 reader-trace*. Q4 restates and
  redesigns nothing in Q1.
- **Q2 crossing-record CLOSED and INHERITED, not re-opened.** Q2 states what a crossing must record/produce
  — including a **subject-source reference** obligation and an **authority-provenance** obligation. Q4 may
  rely on those obligations being *available to be exposed*, but designs no record / schema / store / log /
  ledger — that surface belongs to Q2, not Q4.
- **Q3 floor-binding CLOSED and INHERITED, not re-opened.** The `operator-only` floor binding is inherited
  as written; Q4 changes nothing about it.
- **P4 O1–O5 + non-coercion invariant INHERITED, NOT implemented or amended.** O1 (echo source-sameness),
  O2 (derived motif-member source-membership sameness under the family-bound adequacy standard), O3
  (intent + re-entry-capability classification), O4 (explicit projection gating), O5 (orphan / mismatch
  observability), and the contract-wide non-coercion invariant are the obligations the exposed relation must
  keep *satisfiable*. Q4 makes them satisfiable-across-the-hazard; it does not satisfy, gate, or rewrite
  them.
- **P4 source-sameness policy frame INHERITED.** It defines the meaning / evidence model (why `eid`, row,
  motif-member, current-canonical, or label presence is insufficient; single-source *source-sameness* vs.
  motif/member *source-membership sameness*; `diagnostic_only` as a ratified posture only, no behavior
  change). Q4 reuses this meaning; it selects no comparison mechanism and changes no posture.
- **`update_payload` canonical-last reappend + `eid` reuse** — the characterized "moving target behind an
  `eid`" hazard. Q4's exposure obligations are the requirement shape that keeps a later reader-trace able to
  bind to the *source*, not to the canonical-last payload or the reused slot. Q4 proposes **no**
  `update_payload` fix.
- **Admission authority floor = `operator-only` — unchanged and out of scope here.** §K substrate
  eligibility-not-authorization; Stage B framing-only — any actual reader / policy / comparison / projection
  routes to a later separately-authorized slice (P4 mechanics / P5b / P6 / Stage-B); this frame selects none
  of it.
- **HOLD posture preserved** — Gate A producer-independent wall = HOLD; P4 mechanics = unopened; Gate B
  writer-authority micro-work = HOLD; Dream / Regime-B = HOLD / blocker-dependent.

## 3. Q4 boundary: exposure relation, not reader mechanism

Each row below states **what the future crossing+carrier must expose / make consultable** so that a later P4
reader-trace can satisfy an O1/O2 obligation (while remaining compatible with O3/O4/O5 and the non-coercion
invariant), the P4 obligation it serves, and the reading that is **forbidden** (to keep it relation-level,
not a mechanism). Every obligation is **reader-mechanism-agnostic**: it says *what must be exposed*, never
*how* a reader computes, compares, projects, admits, gates, or decides. "The exposure must let a reader
distinguish same-source from same-`eid`" is an obligation on the exposed relation; it is **not** a reader,
`ReaderPolicy`, comparison method, projection, or eligibility gate authorized here.

## 4. Requirement-level P4-relation exposure obligations (traceability table)

| Requirement-level P4-relation exposure obligation | P4 obligation served | Forbidden interpretation |
|---|---|---|
| **Same-source referent consultability** — the crossing+carrier must expose a same-source referent a later reader-trace can consult, independent of the local `eid` slot. | O1 echo source-sameness (same source, not same `eid`). | Not a source-id field / column / `ReaderPolicy` / comparison call; names no identifier or method. |
| **Reappend / `eid`-reuse disambiguation** — the exposed referent must let a reader distinguish "same source" from "same `eid` slot / canonical-last payload" across `update_payload` reappend and `eid` reuse. | O1/O2 across the characterized `update_payload` hazard. | Not an `update_payload` fix, versioning, revision id, or token scheme; states legibility, not a mechanism. |
| **Family-bound adequacy judgeability** — the exposure must carry enough for a *per-family* source-membership sameness adequacy judgment to be made by a later reader, without one central mechanism or motif redesign. | O2 family-bound source-membership sameness. | Not a shared/central matcher, threshold, or standard; picks no family's bar or cutoff. |
| **Presence-insufficiency legibility** — the exposure must let a reader tell "unproven" apart from "proven-same"; presence of an `eid`, row, motif-member, current-canonical match, or label is not itself exposed as proof. | O1/O2 insufficiency doctrine (P4 source-sameness policy frame). | Does not decide the proof; states that presence must not read as sameness, not how sameness is judged. |
| **Eligibility-neutral / non-coercive exposure** — being consultable must **not itself** confer cognition eligibility, projection, or authority; exposure is evidence, not admission. | Non-coercion invariant (`diagnostic ≠ cognition-eligible`; audit observes, not becomes, authority). | Not an eligibility flag, `diagnostic_only` gate, or auto-admit; evidence-presence must never equal admission. |
| **Projection-gating compatibility** — the referent must be consumable only through an explicit, surface-classified projection, never leaked prompt-/caller-visible by default payload spread. | O3 (intent + re-entry classification); O4 (explicit projection gating). | Not a projection mechanism, allowlist, version format, or schema; states gating-compatibility, not a gate. |
| **Orphan / mismatch observability** — an unresolved, mismatched, or sameness-unprovable reference over the exposed relation must be able to be surfaced as operator-auditable — not silently entering cognition, not invisibly disappearing. | O5 orphan and mismatch observability. | Not a notice channel, ledger format, event schema, counter, or quarantine record; states the capability, not a surface. |
| **Auditable / inspectable / contestable relation** — a later reader-trace and its sameness / orphan outcome over the exposed referent must be operator/governance-auditable, inspectable, and contestable; never pinned or canonical by itself. | O5 + Ledger Observational-Boundary; Document A inspection ≠ projection. | Not a log / transcript / ledger / store format or persistence mechanic; no record designed. |
| **Determinism / stability of the exposed relation** — identical circumstances must expose the same referent, so a later reader-trace is stable and reproducible. | P4 reader-trace stability; auditable / reproducible relation evidence. | Not a scoring / threshold / heuristic design; states stability, not a formula. |
| **Reader-mechanism-agnosticism** — the whole exposure set must hold for *any* future family-bound `ReaderPolicy`; the actual reader / policy / comparison / projection is out of scope. | Keeps `ReaderPolicy` a contract noun; P4-mechanics / P5b / P6 routing. | Not a selection of, or bias toward, any reader engine, policy, comparison method, or projection. |

## 5. Explicit exclusions (Q4 boundary)

- **No reader mechanism is designed** — no `ReaderPolicy`, centralized reader engine, source-sameness
  algorithm, comparison / matcher / hash / fingerprint / token / lineage, projection mechanism,
  `diagnostic_only` flag, or eligibility gate; every obligation is stated as "the crossing+carrier must
  expose…", reader-mechanism-agnostic.
- **P4 O1–O5 are inherited, not implemented or amended** — Q4 keeps them *satisfiable across the hazard*;
  it satisfies, gates, and rewrites none of them, and changes no `diagnostic_only` posture.
- **No `update_payload` fix** — the reappend/`eid`-reuse disambiguation obligation states legibility of the
  relation; it repairs no code path and selects no revision/versioning scheme.
- **No re-opening of Q1, Q2, or Q3** — carrier properties (Q1), crossing record (Q2), and floor binding
  (Q3) are inherited and cited, not restated or redesigned.
- **Q5–Q7 are not answered** — Gate B relation (Q5), Dream relation (Q6), and substrate boundary (Q7)
  remain open for their own future authorized slices.

## 6. Explicit non-authorizations

No `ReaderPolicy` implementation or centralized reader engine; no source-sameness algorithm / comparison /
matcher / hash / fingerprint / token / lineage; no `diagnostic_only` flag or mechanics; no reader-projection
implementation; no `update_payload` fix; no carrier / store / schema / field / enum / ID design or
selection; no admission mechanism / crossing / workflow / actor / API / UI; no database / substrate / Stage-B
mechanics; no change to (re-opening, lowering, reinterpretation, or amendment of) the `operator-only` floor;
no writer crossing or Gate B fix; no Dream / Regime-B runtime; no scheduler / trigger / budget / autonomy;
no Gate D / Envelope-Audit / Document B chamber runtime; no AgentRunner / app / spine / MCP wiring; no
model / provider / API / prompt path; no memory writes / persistence / logging / transcripts; no
output-control / finalizer / refusal / identity / canon behavior; no dynamic-kernel / `conversation_shock`;
no contract amendment. Edits no other doc and no §0. Doctrine preserved verbatim.

## 7. Verdict

**P4 RELATION OBLIGATIONS FRAMED — REQUIREMENT-LEVEL ONLY / NO READERPOLICY OR SOURCE-SAMENESS MECHANISM /
NO CARRIER OR CROSSING DESIGNED.** Q4 is answered at the exposure-relation level: the traceability table
(§4) states what a future governed admission crossing + candidate carrier must expose / make consultable so
a later P4 reader-trace can bind to a source across `update_payload` canonical-last reappend and `eid` reuse
— same-source referent consultability, reappend/`eid`-reuse disambiguation, family-bound adequacy
judgeability, presence-insufficiency legibility, eligibility-neutral / non-coercive exposure,
projection-gating compatibility, orphan/mismatch observability, auditable/inspectable/contestable relation,
determinism/stability of the exposed relation, and reader-mechanism-agnosticism — each traced to the P4
obligation it serves and fenced against a reader-mechanism reading. P4 O1–O5, the non-coercion invariant,
and the `diagnostic_only` posture are inherited exactly and left unchanged; no reader, `ReaderPolicy`,
comparison method, projection, `diagnostic_only` gate, eligibility gate, `update_payload` fix, carrier, or
crossing is named or designed; Q1, Q2, and Q3 are not re-opened; Q5–Q7 remain open; every mechanism remains
deferred to a future, separately-authorized decision.

*End — Document A Admission-Crossing Q4 P4-Relation Frame v0.1. Docs-only, requirement-level only. Verdict:
P4 RELATION OBLIGATIONS FRAMED — REQUIREMENT-LEVEL ONLY / NO READERPOLICY OR SOURCE-SAMENESS MECHANISM / NO
CARRIER OR CROSSING DESIGNED.*
