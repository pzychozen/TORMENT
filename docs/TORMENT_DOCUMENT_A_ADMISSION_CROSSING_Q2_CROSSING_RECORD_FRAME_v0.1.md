# TORMENT — Document A Admission-Crossing Q2: Crossing-Record Frame v0.1

**Status:** DOCS-ONLY requirement-level frame. **Non-authorizing, non-designing, non-implementing.** This
is **Q2 only** from the design-framing scope frame
(`docs/TORMENT_DOCUMENT_A_ADMISSION_CROSSING_DESIGN_FRAMING_SCOPE_FRAME_v0.1.md`). It states the
**requirement-level record/produce obligations** a future Document A governed admission crossing would have
to satisfy to be operator-auditable, inspectable, and contestable. It **names, selects, designs, and
implies no record schema / format / field / enum / ID / store / carrier / workflow / actor / API / UI**,
builds no crossing, and answers no other question (Q3–Q7). Navigation / requirement aid only.

**Authority note:** Document A (containment wall / admission edge), the Gate A governed-admission
authority-option selection (`operator-only` floor), the Gate A candidate-representation selection +
pre-carrier constraints, the Q1 carrier-properties frame, the P4 Reader/Projection-Safety Contract
(O1/O2), the Gate B writer-authority doctrine, Document B, the Ledger Observational-Boundary, the
substrate-readiness memo / Stage-B opening decision record, and `PROJECT_ORIENTATION_MAP.md` §0 remain
source of truth. This frame reads them; it amends none.

**Doctrine (carried, exact):**

> Memory may guide context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.
> Presence of a reusable local `eid` is insufficient.

---

## 1. Status / non-authorizing, requirement-level Q2-only banner

Record-obligation statement only. Naming an *obligation to produce evidence* here neither designs nor
selects a record, log, ledger, event, schema, field, store, or carrier that would satisfy it, and picks no
workflow, decision-procedure, actor, API, or UI. No admission crossing / mechanism / runtime / persistence
is created or implied; describing "the crossing must produce an audit record" states the **obligation**,
never a logging / persistence / transcript / store mechanism to build. This frame answers **Q2 only**;
Q3–Q7 remain open and unanswered, and Q1 is not re-opened. The full non-authorization list is §6.

## 2. Inherited and scoped inputs (carried, NOT re-decided)

- **Q2 named by the scope frame** as the requirement-level crossing-record question (step 2 of the
  decomposition). This frame is that question's requirement-level answer *shape* — an obligation set, not a
  design.
- **Q1 carrier-properties is CLOSED and INHERITED, not re-opened.** Q1 states what any future *carrier*
  must support; **Q2 is complementary**: it states what a future *crossing* must record/produce. Where Q2
  references a source at reference level, it does so **consistent with** Q1 source-stability /
  eid-independence — it neither restates nor redesigns the carrier properties.
- **Admission authority floor = `operator-only`** — unchanged and out of scope here. Q2 may require
  *evidence that the floor was satisfied* as a necessary condition, but **defers all floor-binding
  mechanics / procedure to Q3** — it designs no actor, credential, co-sign, or binding procedure.
- **Gate A containment** — the candidate side is structurally contained (A-C2, non-reachability). Q2 may
  require pre/post containment-state evidence, but honors containment as **structural**, never as a tag
  whose downstream honoring is assumed.
- **P4 O1/O2** — the crossing's later reader-trace / source-sameness has *no selected carrier or comparison
  mechanism*; the live joins are presence-only. Q2's subject-source reference obligation is the
  requirement shape that keeps those obligations *satisfiable* later — it does not implement them.
- **Gate B durable writer resolution = HOLD** — Q2 may require the record be *compatible with* a future
  Gate B resolution, but opens no writer crossing or Gate B fix.
- **Dream / Regime-B = HOLD** — Document B stages, Document A crosses. Q2 may require staged-origin
  evidence at reference level, but opens no Dream / Regime-B runtime.
- **§K substrate eligibility-not-authorization; Stage B framing-only** — any actual record store / schema /
  durability routes to Stage-B-framing / P6; this frame selects none of it.

## 3. Q2 boundary: record/produce obligations, not schema/mechanism

Each row below states **what a governed admission crossing must be able to record or produce** as an
obligation, the downstream consumer it serves, and the reading that is **forbidden** (to keep it
requirement-level, not a design). Every obligation is **record-agnostic**: it says *what evidence must be
producible*, never *which* record, log, field, format, or store produces it, and never *how* the crossing
operates. "Producible evidence" is an obligation on a future crossing; it is not a log, ledger, event,
transcript, or persistence artifact authorized here.

## 4. Requirement-level crossing-record obligations (traceability table)

| Requirement-level obligation | Downstream consumer served | Forbidden interpretation |
|---|---|---|
| **Occurrence / actuation evidence** — a crossing must be able to produce evidence that it *occurred*, distinguishable from a non-crossing. | Auditability; Document A admission edge is inspectable. | Not a log / event / ledger / transcript to build; names no record, store, or emission mechanism. |
| **Authority-provenance evidence** — it must be able to produce evidence that the `operator-only` floor was satisfied as a necessary condition of the crossing. | Governed-admission authority floor (operator-only). | Not a floor-binding procedure, actor, credential, co-sign, or quorum; **floor-binding mechanics deferred to Q3**; no floor change. |
| **Subject-source reference evidence** — it must be able to reference the crossed item's source at reference level, consistent with Q1 source-stability / eid-independence. | P4 O1/O2 (same-source, not same-`eid`); crossing operating on stable sources. | Not a new source-id / token / fingerprint / field; does not restate or redesign Q1's carrier properties. |
| **Pre/post containment-state evidence** — it must be able to produce evidence that the item was contained (candidate side) before and admitted after, so containment is inspectable. | Gate A containment wall (A-C2, structural non-reachability). | Not a tag / flag / marker whose downstream honoring is assumed; no fan-out coupling; containment stays structural. |
| **Inspectability / recoverability evidence** — its evidence must be operator/governance-inspectable and recoverable-when-valid; never pinned or canonical by itself. | Non-coercion invariant; Stage-A O6 alignment; inspection ≠ projection. | Not a log / transcript / ledger format, event schema, store, or persistence mechanism; no durability route chosen. |
| **Contestability evidence** — a crossing must be identifiable and questionable/contestable after the fact by an operator/governance reader. | Operator contestability of admission. | Not a resolver, decision-procedure, appeal workflow, actor, or UI; states that it *can be contested*, not how. |
| **Determinism / stability of the record** — identical crossings must yield the same recorded-evidence *shape*, so a later audit is stable and reproducible. | Reproducible / stable admission audit; P4 reader-trace stability. | Not a scoring / threshold / heuristic / format design; states stability, not a schema or formula. |
| **Non-authority evidence** — producing crossing evidence must **not itself** confer cognition eligibility, projection, or authority. | Ledger §3 / non-coercion (`diagnostic ≠ cognition-eligible`; audit observes, not becomes, authority). | Not an eligibility flag or gate; evidence-presence must not equal admission or authority. |
| **Gate-B-resolution compatibility** — the evidence must be *compatible with* a future durable writer resolution without providing one. | Gate B durable writer resolution (HOLD). | Not a writer crossing, promotion, or Gate B fix; opens no write-side mechanism. |
| **Dream-staging origin evidence** — for a Document-B-staged candidate (B stages, A crosses), it must be able to record the staged origin at reference level. | Dream staging→crossing (Document B stages, Document A crosses). | Not Dream / Regime-B / chamber runtime; no scheduler, trigger, budget, or staging mechanism. |
| **Carrier/substrate-agnosticism** — the whole obligation set must hold for *any* future record carrier/store; the actual record / schema / durability is out of scope. | Stage-B-framing / §K routing; keeps Q2 requirement-level. | Not a selection of, or bias toward, any record, store, database, schema, or serialization. |

## 5. Explicit exclusions (Q2 boundary)

- **No record schema / format / field / enum / ID / store / carrier is named or selected** — every
  obligation is stated as "the crossing must be able to produce/record…", record-agnostic.
- **No crossing mechanism** — no workflow, decision-procedure, actor, API, UI, emission path, or algorithm
  is designed.
- **No floor-binding mechanics** — Q2 may require *evidence that* the `operator-only` floor was satisfied,
  but the binding procedure / actor / necessary-condition mechanism is **Q3**, not answered here.
- **No logging / persistence / ledger / transcript authorization** — inspectability / contestability /
  recoverability are stated as obligations on future evidence, not as a store or persistence mechanism to
  build.
- **No re-opening of Q1** — the carrier-properties frame is inherited and cited, not restated or redesigned.
- **Q3–Q7 are not answered** — floor binding (Q3), P4 relation (Q4), Gate B relation (Q5), Dream relation
  (Q6), substrate boundary (Q7) remain open for their own future authorized slices.

## 6. Explicit non-authorizations

No record schema / format / field / enum / ID / store / carrier design or selection; no crossing
workflow / decision-procedure / actor / API / UI; no admission mechanism / crossing implementation; no
database / substrate construction or Stage-B mechanics; no memory writes / persistence / logging /
transcripts; no change to the `operator-only` floor; no floor-binding mechanics (Q3); no writer crossing
or Gate B fix; no P4 `ReaderPolicy` / source-sameness / `diagnostic_only` mechanics; no Dream / Regime-B
runtime; no scheduler / trigger / budget / autonomy; no Gate D / Envelope-Audit / Document B chamber
runtime; no AgentRunner / app / spine / MCP wiring; no model / provider / API / prompt path; no
output-control / finalizer / refusal / identity / canon behavior; no dynamic-kernel / `conversation_shock`;
no contract amendment. Edits no other doc and no §0. Doctrine preserved verbatim.

## 7. Verdict

**CROSSING-RECORD OBLIGATIONS FRAMED — REQUIREMENT-LEVEL ONLY / NO RECORD SCHEMA OR MECHANISM / NO
CROSSING DESIGNED.** Q2 is answered at the obligation level: the traceability table (§4) states what a
future governed admission crossing must be able to record or produce — occurrence/actuation,
authority-provenance, subject-source reference, pre/post containment-state, inspectability/recoverability,
contestability, determinism/stability, non-authority, Gate-B-resolution compatibility, Dream-staging
origin, and carrier/substrate-agnosticism — each traced to the downstream consumer it serves and fenced
against a schema / mechanism reading. No record, store, schema, field, enum, ID, workflow, actor, API, or
UI is named or selected; the `operator-only` floor is unchanged and its binding mechanics are deferred to
Q3; Q1 is not re-opened; Q3–Q7 remain open; every mechanism remains deferred to a future,
separately-authorized decision.

*End — Document A Admission-Crossing Q2 Crossing-Record Frame v0.1. Docs-only, requirement-level only.
Verdict: CROSSING-RECORD OBLIGATIONS FRAMED — REQUIREMENT-LEVEL ONLY / NO RECORD SCHEMA OR MECHANISM / NO
CROSSING DESIGNED.*
