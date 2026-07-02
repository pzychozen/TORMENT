# TORMENT — Document A Admission-Crossing Q3: Floor-Binding Frame v0.1

**Status:** DOCS-ONLY requirement-level frame. **Non-authorizing, non-designing, non-implementing.** This
is **Q3 only** from the design-framing scope frame
(`docs/TORMENT_DOCUMENT_A_ADMISSION_CROSSING_DESIGN_FRAMING_SCOPE_FRAME_v0.1.md`). It states the
**requirement-level floor-binding obligations** that must hold for a future Document A governed admission
crossing to be bound to the already-decided **`operator-only`** admission authority floor as a necessary
condition. It **inherits the floor unchanged** and **designs no enforcement mechanism, check, guard,
workflow, actor model, credential, signature, approval step, decision-procedure, UI, or API**. It reopens
neither Q1 nor Q2 and answers no other question (Q4–Q7). Navigation / requirement aid only.

**Authority note:** Document A (containment wall / admission edge), the Gate A governed-admission
authority-option selection (which decided the `operator-only` floor), the Gate A candidate-representation
selection + pre-carrier constraints, the Q1 carrier-properties frame, the Q2 crossing-record frame, the P4
Reader/Projection-Safety Contract, the Gate B writer-authority doctrine, Document B, the Ledger
Observational-Boundary, the substrate-readiness memo / Stage-B opening decision record, and
`PROJECT_ORIENTATION_MAP.md` §0 remain source of truth. This frame reads them; it amends none. **The
`operator-only` floor is inherited exactly as decided; this frame does not re-open, lower, reinterpret, or
amend it.**

**Doctrine (carried, exact):**

> Memory may guide context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.
> Presence of a reusable local `eid` is insufficient.

---

## 1. Status / non-authorizing, requirement-level Q3-only banner

Binding-obligation statement only. Naming a required *property of the binding* here neither designs nor
selects an enforcement point, check, guard, gate, approval step, credential, signature, actor, workflow,
decision-procedure, UI, or API that would satisfy or enforce it. Stating that the floor must be a
**necessary, non-bypassable** condition states the **requirement**; it does **not** authorize the
enforcement point that would make it so. No admission crossing / mechanism / runtime / persistence is
created or implied. This frame answers **Q3 only**; Q4–Q7 remain open and unanswered, and neither Q1 nor Q2
is re-opened. The full non-authorization list is §6.

## 2. Inherited and scoped inputs (carried, NOT re-decided)

- **Q3 named by the scope frame** as the floor-binding question (step-2 companion to Q2). This frame is
  that question's requirement-level answer *shape* — a binding-property set, not a design.
- **Admission authority floor = `operator-only` — INHERITED AND UNCHANGED.** The floor was decided by the
  Gate A governed-admission authority-option selection. Q3 states how a future crossing must be **bound to**
  that floor; it **does not re-open, lower, reinterpret, or amend** the floor, and names no floor-holder
  representation.
- **Q1 carrier-properties CLOSED and INHERITED, not re-opened.** Q1 states what any future carrier must
  support. Q3 does not restate or redesign it.
- **Q2 crossing-record CLOSED and INHERITED, not re-opened.** Q2 states what a crossing must record/produce
  — including an **authority-provenance** obligation (evidence that the floor was satisfied). **Q3 may
  require that floor satisfaction be *evidenced through* Q2's authority-provenance obligation, but designs
  no record / schema / store / log / ledger mechanism** — that evidence surface belongs to Q2's obligation,
  not to Q3.
- **Gate A containment** — the candidate side is structurally contained. A non-bypassable floor binding is
  consistent with containment's no-side-path posture, but Q3 designs no containment mechanism.
- **Gate B durable writer resolution = HOLD; Dream / Regime-B = HOLD** — untouched here.
- **§K substrate eligibility-not-authorization; Stage B framing-only** — any actual enforcement mechanism /
  check / procedure routes to a later separately-authorized slice / Stage-B; this frame selects none of it.

## 3. Q3 boundary: binding properties, not enforcement mechanism

Each row below states **a property the binding between a future crossing and the `operator-only` floor must
have**, the guarantee it preserves, and the reading that is **forbidden** (to keep it requirement-level,
not a design). Every obligation is **mechanism-agnostic**: it says *what must be true of the binding*, never
*how* the floor is checked, satisfied, enforced, approved, signed, or recorded. "The floor must be
satisfied" is an obligation on a future binding; it is not an enforcement point, guard, or approval
mechanism authorized here.

## 4. Requirement-level floor-binding obligations (traceability table)

| Requirement-level floor-binding obligation | Guarantee it preserves | Forbidden interpretation |
|---|---|---|
| **Necessity / non-bypassability** — no governed admission crossing may complete unless the `operator-only` floor is satisfied; there is no alternate path to admission that skips it. | The floor is a *necessary condition* for admission; Gate A no-side-path. | Not a guard / check / gate / enforcement-point implementation; states necessity, not how it is enforced. |
| **Sole-authority / exclusivity** — floor satisfaction rests with the operator authority alone; the binding admits no co-author, delegate, quorum, or automatic / system-derived substitute. | `operator-only` preserved (not widened to other authorities). | Not an actor model, role, permission scheme, or credential; names no authority-holder representation. |
| **Non-self-authorization / non-coercion** — no memory, audit, carrier evidence, candidate presence, source-sameness determination, or Q2 crossing-record may itself satisfy or substitute for the floor. | Doctrine (*memory may not seize authority*); Ledger §3 / non-coercion (audit observes, not becomes, authority). | Not an eligibility flag or gate; evidence-presence must never equal floor satisfaction. |
| **Crossing-scoped binding** — floor satisfaction binds to the specific crossing it authorizes; it is not a standing / blanket / global authorization for arbitrary future crossings. | Bounded authority; auditability / contestability (Q2). | Not a session / token / scope mechanism; states scoping requirement, not a scoping implementation. |
| **Freshness / non-replay** — a prior authorization must not be reusable to authorize a different or later crossing; the binding is to a live decision, not a reusable artifact. | Authority cannot be replayed; each crossing is freshly authorized. | Not a nonce / timestamp / expiry / signature algorithm; states the property, not an anti-replay mechanism. |
| **Revocability before crossing** — the operator's authorization can be withheld, and — before the crossing completes — reversed; the floor is an operator-controlled gate, not an irreversible trigger. | Operator control; HOLD posture preserved. | Not a revocation workflow, state machine, or API; states controllability, not a procedure. |
| **Evidenced-via-Q2** — that the floor was satisfied and bound to *this* crossing must be inspectable / contestable through Q2's authority-provenance obligation. | Auditable, contestable authority (Q2 authority-provenance). | Cross-references Q2's obligation only; designs no record / schema / store / log / ledger here. |
| **Floor-preservation / non-weakening** — the binding is a relationship *to* the inherited floor, never a redefinition, lowering, or reinterpretation *of* it. | The decided `operator-only` floor is unchanged. | Not a floor amendment, relaxation, or reinterpretation; adds no exception or alternate authority. |
| **Determinism / stability of the binding relation** — identical authorization circumstances must yield the same bound / not-bound outcome, so the binding is reproducible and auditable. | Reproducible / stable admission authority; audit stability. | Not a decision-procedure, scoring, heuristic, or threshold; states stability, not a formula. |
| **Mechanism-agnosticism** — the whole obligation set must hold for *any* future enforcement mechanism; the actual check / guard / approval / procedure is out of scope. | Stage-B-framing / §K routing; keeps Q3 requirement-level. | Not a selection of, or bias toward, any enforcement mechanism, guard, credential, signature, or procedure. |

## 5. Explicit exclusions (Q3 boundary)

- **No enforcement mechanism is designed** — no check, guard, gate, enforcement point, approval step,
  workflow, actor model, credential, signature, decision-procedure, UI, or API; every obligation is stated
  as "the binding must…", mechanism-agnostic.
- **The `operator-only` floor is inherited unchanged** — Q3 neither re-opens, lowers, reinterprets, nor
  amends it; it defines no floor-holder and adds no alternate authority.
- **No evidence/record mechanism** — the evidenced-via-Q2 obligation cross-references Q2's authority-
  provenance obligation; it authorizes no record / schema / store / log / ledger / transcript here.
- **"Necessary / non-bypassable" is a requirement, not an authorization** — stating that the floor must be a
  necessary, non-bypassable condition does not authorize the enforcement point that would make it so.
- **No re-opening of Q1 or Q2** — both are inherited and cited, not restated or redesigned.
- **Q4–Q7 are not answered** — P4 relation (Q4), Gate B relation (Q5), Dream relation (Q6), substrate
  boundary (Q7) remain open for their own future authorized slices.

## 6. Explicit non-authorizations

No workflow / actor model / credential / signature / approval mechanism / decision-procedure / UI / API; no
guard / check / gate / enforcement-point implementation; no change to (re-opening, lowering,
reinterpretation, or amendment of) the `operator-only` floor; no carrier / store / schema / field / enum /
ID design or selection; no admission mechanism / crossing implementation; no logging / persistence / ledger
/ transcript authorization; no memory writes / persistence; no database / substrate construction or Stage-B
mechanics; no writer crossing or Gate B fix; no P4 `ReaderPolicy` / source-sameness / `diagnostic_only`
mechanics; no Dream / Regime-B runtime; no scheduler / trigger / budget / autonomy; no Gate D /
Envelope-Audit / Document B chamber runtime; no AgentRunner / app / spine / MCP wiring; no model / provider
/ API / prompt path; no output-control / finalizer / refusal / identity / canon behavior; no
dynamic-kernel / `conversation_shock`; no contract amendment. Edits no other doc and no §0. Doctrine
preserved verbatim.

## 7. Verdict

**FLOOR-BINDING OBLIGATIONS FRAMED — REQUIREMENT-LEVEL ONLY / FLOOR INHERITED UNCHANGED / NO ENFORCEMENT
MECHANISM OR CROSSING DESIGNED.** Q3 is answered at the obligation level: the traceability table (§4) states
what must be true of the binding between a future governed admission crossing and the `operator-only` floor
— necessity/non-bypassability, sole-authority/exclusivity, non-self-authorization/non-coercion,
crossing-scoped binding, freshness/non-replay, revocability before crossing, evidenced-via-Q2,
floor-preservation/non-weakening, determinism/stability, and mechanism-agnosticism — each traced to the
guarantee it preserves and fenced against an enforcement-mechanism reading. The `operator-only` floor is
inherited exactly as decided and left unchanged; no check, guard, workflow, actor, credential, signature,
approval step, decision-procedure, record, or API is named or designed; Q1 and Q2 are not re-opened; Q4–Q7
remain open; every mechanism remains deferred to a future, separately-authorized decision.

*End — Document A Admission-Crossing Q3 Floor-Binding Frame v0.1. Docs-only, requirement-level only.
Verdict: FLOOR-BINDING OBLIGATIONS FRAMED — REQUIREMENT-LEVEL ONLY / FLOOR INHERITED UNCHANGED / NO
ENFORCEMENT MECHANISM OR CROSSING DESIGNED.*
