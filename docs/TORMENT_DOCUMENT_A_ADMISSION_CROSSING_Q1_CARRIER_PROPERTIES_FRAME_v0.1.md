# TORMENT — Document A Admission-Crossing Q1: Carrier-Properties Frame v0.1

**Status:** DOCS-ONLY requirement-level frame. **Non-authorizing, non-selecting, non-designing.** This is
**Q1 only** from the design-framing scope frame
(`docs/TORMENT_DOCUMENT_A_ADMISSION_CROSSING_DESIGN_FRAMING_SCOPE_FRAME_v0.1.md`). It states the
**requirement-level properties any future candidate carrier must satisfy** so the Document A governed
admission crossing can *later* support P4 O1/O2 reader-trace / source-sameness, Gate B durable writer
resolution, and Dream staging→crossing. It **names, selects, designs, and implies no carrier / store /
schema / field / enum / ID / mechanism**, sets no adequacy threshold, and answers no other question
(Q2–Q7). Navigation / requirement aid only.

**Authority note:** Document A (containment wall / admission edge), the Gate A governed-admission
authority-option selection (`operator-only` floor), the Gate A candidate-representation selection +
pre-carrier constraints, the P4 Reader/Projection-Safety Contract (O1/O2), the Gate B writer-authority
doctrine, Document B, the Ledger Observational-Boundary, the substrate-readiness memo / Stage-B opening
decision record, and `PROJECT_ORIENTATION_MAP.md` §0 remain source of truth. This frame reads them; it
amends none.

**Doctrine (carried, exact):**

> Memory may guide context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.
> Presence of a reusable local `eid` is insufficient.

---

## 1. Status / non-authorizing, non-selecting banner

Requirement-properties statement only. Naming a required *property* here neither designs nor selects a
carrier that satisfies it, and picks no comparison mechanism, token, fingerprint, lineage, field, schema,
enum, or ID. No admission crossing / workflow / actor / API / UI / runtime / persistence is created or
implied. This frame answers **Q1 only**; Q2–Q7 remain open and unanswered. The full non-authorization list
is §5.

## 2. Inherited and scoped inputs (carried, NOT re-decided; and the Q1 boundary)

- **Q1 named by the scope frame** as the recommended first sub-question; this frame is that question's
  requirement-level answer *shape* — a property set, not a design.
- **Admission authority floor = `operator-only`** — unchanged and out of scope here; a carrier must
  *support* (never bypass or satisfy) it.
- **Candidate-representation selection + pre-carrier constraints are INHERITED, not re-opened.** Q1 is
  **complementary, not duplicative**: those artifacts constrain the *candidate representation*; **Q1 asks
  what a future carrier must be able to support for the governed admission crossing across P4 / Gate B /
  Dream** — it does not select, redesign, or restate the representation.
- **P4 O1/O2** — the crossing's later reader-trace / source-sameness has *no selected carrier or comparison
  mechanism*; the live joins are presence-only. The properties below are the requirement shape that any
  future carrier must meet so those obligations remain *satisfiable* — they do not implement them.
- **`update_payload` canonical-last reappend + `eid` reuse** — the characterized "moving target behind an
  `eid`" hazard the carrier must be able to withstand.
- **§K substrate eligibility-not-authorization; Stage B framing-only** — the actual carrier / store /
  schema / durability routes to Stage-B-framing / P6; this frame selects none of it.
- **HOLD posture preserved** — Gate A wall, P4 mechanics, Gate B writer-authority, and Dream/Regime-B all
  remain unopened.

## 3. Requirement-level carrier properties (traceability table)

Each row is a property **any** future carrier must satisfy, the downstream obligation it serves, and the
reading that is **forbidden** (to keep it requirement-level, not a design). All properties are
**carrier-agnostic**: they say *what must be true of any carrier*, never *which* carrier, field, or
mechanism.

| Requirement-level property | Downstream obligation served | Forbidden interpretation |
|---|---|---|
| **Source-stability / eid-independence** — a reference must be able to denote the *same source* independent of the local `eid` slot. | P4 O1/O2 (same-source, not same-`eid`); Document A crossing operating on stable sources. | Not "add a source-id field/column"; names no identifier, key, or slot. |
| **Reappend/reuse survivability** — the same-source denotation must survive `update_payload` canonical-last reappend and `eid` reuse (a moving payload behind an `eid`). | P4 O1/O2 across the characterized `update_payload` hazard. | Not a versioning/revision scheme, token, or fingerprint; no algorithm chosen. |
| **Same-source determinability** — it must *support a same-source determination* (an adequacy judgment can be made) as a capability. | P4 O1/O2 "provably the same source"; Gate B attributable authority-bearing writes. | Not a comparison mechanism, hash, or matcher; states capability, not method; sets no threshold. |
| **Family-bound adequacy compatibility** — it must accommodate *per-family* adequacy standards, not force one central mechanism or motif redesign. | P4 O2 family-bound adequacy standard. | Not a shared/central carrier mandate; picks no family's standard or threshold. |
| **Auditability / inspectability / recoverability** — its evidence must be operator/governance-auditable, inspectable, and recoverable-when-valid; never pinned or canonical by itself. | Non-coercion invariant; Stage A O6 alignment; Document A inspection≠projection. | Not a log/transcript/ledger format, event schema, or store; no persistence mechanics. |
| **Non-authority / non-coercion** — carrying source evidence must **not itself** confer cognition eligibility, projection, or authority. | Ledger §3 / non-coercion (`diagnostic ≠ cognition-eligible`; audit observes, not becomes, authority). | Not an eligibility flag or gate; evidence-presence must not equal admission. |
| **Operator-only-floor compatibility** — it must *support* the `operator-only` admission floor as a necessary condition, never provide an alternative path to admission. | Governed-admission authority floor (operator-only). | Not a new authority actor, co-sign, quorum, or auto-admit path; no floor change. |
| **Containment compatibility** — carrying it must not create a side-path into the ordinary fan-out; separation must be structural, not tag-honoring. | Document A containment wall (A-C2, structural non-reachability). | Not a tag/flag/marker whose honoring downstream is assumed; no fan-out coupling. |
| **Determinism / stability of judgment** — identical inputs must yield the same same-source determination, so a later reader-trace is stable and reproducible. | P4 reader-trace stability; auditable/reproducible admission evidence. | Not a scoring/threshold/heuristic design; states stability, not a formula. |
| **Carrier/substrate-agnosticism** — the whole property set must hold for *any* future carrier; the actual carrier / store / schema / durability is out of scope. | Stage-B-framing / §K routing; keeps Q1 requirement-level. | Not a selection of, or bias toward, any carrier, store, database, or serialization. |

## 4. Explicit exclusions (Q1 boundary)

- **No carrier / store / schema / field / enum / ID is named or selected** — every property is stated as
  "any carrier must…", carrier-agnostic.
- **No comparison mechanism** — no token, fingerprint, lineage, hash, matcher, or algorithm is chosen.
- **No adequacy threshold** — Q1 states the *shape* of adequacy (that a same-source determination must be
  supportable, per family), never a family's bar or cutoff.
- **No re-opening of the candidate representation** — the pre-carrier constraints / representation
  selection are inherited and cited, not restated or redesigned.
- **Q2–Q7 are not answered** — crossing record (Q2), floor binding (Q3), P4 relation (Q4), Gate B relation
  (Q5), Dream relation (Q6), substrate boundary (Q7) remain open for their own future authorized slices.

## 5. Explicit non-authorizations

No carrier/store/schema/field/enum/ID design or selection; no token/fingerprint/lineage mechanism or
algorithm; no adequacy threshold; no admission mechanism/crossing/workflow/decision-procedure/actor/API/UI;
no database/substrate construction or Stage-B mechanics; no change to the `operator-only` floor; no writer
crossing or Gate B fix; no P4 `ReaderPolicy`/source-sameness/`diagnostic_only` mechanics; no Dream/Regime-B
runtime; no scheduler/trigger/budget/autonomy; no Gate D / Envelope-Audit / Document B chamber runtime; no
AgentRunner/app/spine/MCP wiring; no model/provider/API/prompt path; no memory writes/persistence/logging/
transcripts; no output-control/finalizer/refusal/identity/canon behavior; no dynamic-kernel/
`conversation_shock`; no contract amendment. Edits no other doc and no §0. Doctrine preserved verbatim.

## 6. Verdict

**CARRIER PROPERTIES FRAMED — REQUIREMENT-LEVEL ONLY / NO CARRIER SELECTED / NO MECHANICS OPENED.** Q1 is
answered at the property level: the traceability table (§3) states what **any** future candidate carrier
must satisfy — source-stability/eid-independence, reappend/reuse survivability, same-source
determinability, family-bound adequacy compatibility, auditability/inspectability/recoverability,
non-authority/non-coercion, operator-only-floor compatibility, containment compatibility, determinism, and
carrier/substrate-agnosticism — each traced to the downstream obligation it serves and fenced against a
mechanism reading. No carrier, store, schema, field, enum, ID, mechanism, or threshold is named or
selected; Q2–Q7 remain open; every mechanism remains deferred to a future, separately-authorized decision.

*End — Document A Admission-Crossing Q1 Carrier-Properties Frame v0.1. Docs-only, requirement-level only.
Verdict: CARRIER PROPERTIES FRAMED — REQUIREMENT-LEVEL ONLY / NO CARRIER SELECTED / NO MECHANICS OPENED.*
