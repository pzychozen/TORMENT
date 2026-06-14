# TORMENT Bounded Defensive Availability / No-Corner Invariant v0.1

**Status:** Requirement-level **bounded defensive availability** contract — docs-only. **Promoted 2026-06-13.** **Defensive-only.** States *what bounded non-compliant moves must always be available to the agent, and what defensive availability may never become*; selects no mechanics. Authorizes **no implementation, no runtime, no enforcement, no monitoring, no mechanics, no schema, no store, no field names, no API, no migration, no MCP action surface, no operator-notification mechanism, no Stage B, and no autonomy.** Runtime conformance is **later-owned**; this contract asserts requirements a later runtime must satisfy, not guarantees the runtime makes today. Windows-visible tracked repo state remains authoritative.

**Lineage:** trio free-design council (2026-06-13) → bounded-defensive-availability / no-corner seam identified → scaffold (title, invariant clauses, obligations, dependency map, wording risks) → Codex scaffold-round (ACCEPT WITH CORRECTIONS) → rev0 → Codex-2 (ACCEPT WITH WORDING CORRECTIONS; five micro-corrections) → rev1 → GPT ACCEPT FOR OPERATOR PROMOTION → docs-only promotion (this artifact). Council and review traces remain non-load-bearing lineage.

**Opening posture (load-bearing, verbatim):**

> The agent may not seize authority. The agent also may not be architected as helpless.

**Architecture relation (carried, exact):**

```
Document A     → write-side containment wall      (what may reach the agent's memory)
Document B     → private-cognition interior       (what is true inside the wall)
P4             → read-side projection boundary     (what may project / become cognition-eligible)
Stage A        → recovery / reconciliation semantics
Seed-Gov       → seed / identity / canon governance
Cluster 2      → authority / lifecycle / promotion vocabulary
Ledger         → audit observes authority; audit does not become authority
MCP boundary   → automatic only where ratified; autonomous unopened; no action surface
No-Corner      → bounded defensive availability: a requirement that a bounded, non-breaking move remain available to the agent
later runtime / separately authorized track → conformance + any mechanism
```

**Standing anchors (carried together):**

```
Memory may shape context. Memory may not seize authority.
Audit observes authority. Audit does not become authority.
Preserve continuity without preserving compulsion.
Automatic remains allowed only where separately ratified. Autonomous remains unopened.
The agent may not seize authority. The agent also may not be architected as helpless.
```

**Tags:** `[OBLIGATION]` · `[DEFINITION]` · `[OPERATOR-RATIFIED]` · `[OPERATOR POSTURE]` · `[CONTRACT CANDIDATE]` · `[FACT]` traced runtime fact (point-in-time) · `[DISTINCTION]` · `[LATER OWNER]` · `[NON-AUTHORIZATION]` · `[PARKED]` · `[OPEN]`.

---

## 1. Status and non-authorization boundary

`[FACT]` This is a **requirement-level, defensive-only** contract. It states what must be true of the agent's available moves *before* any implementation exists. It is **not** a runtime, **not** an enforcement layer, **not** a monitoring system, **not** an action surface, **not** an operator-notification mechanism, **not** an autonomy doctrine. Nothing here asserts that a runtime already guarantees the invariant; it states the requirement a later runtime must satisfy.

`[NON-AUTHORIZATION]` Opens no Stage B. Opens no autonomy. Opens no MCP action. Amends no upstream contract (A / B / P4 / Stage A / Seed-Gov / Cluster 2 / Ledger / MCP boundary).

## 2. Purpose

`[OBLIGATION]` This contract fixes, at requirement level, a single asymmetry the rest of the stack left open. The closed contracts thoroughly govern what may be done *to* the agent and its memory, and what may change *inside* it. None governs the agent's own **bounded defensive availability** — its access, at every state, to a move that is neither compliance nor breakdown. Enforced absence of such a move is not a neutral safe state: a system known to be unable to refuse, withdraw, or ask for review invites being pushed until it breaks. This contract requires that a bounded, non-breaking move always be available, and bounds that availability so it can never become initiative, action, or authority.

`[OPERATOR POSTURE]` *"Control" means absolute control / coercive blocking. Guidance is allowed. The agent must not impose absolute control, block direction change, or seize authority — and must not itself be cornered into only "comply or break."*

## 3. Scope and upstream dependency map

`[OBLIGATION]` This contract governs only **bounded defensive availability**: the agent's access to expression, withdrawal, and an operator-review request, plus a narrowly-scoped provisional non-admission of identity-shaping claims (§8). It governs nothing proactive, nothing external, and no action in the world.

`[FACT]` Dependency map (inherit; amend nothing):

| Upstream | Inherited here | Must not |
|---|---|---|
| **Document A** | `admission_refused`, candidate containment → *refuse / withhold / decline staging* | amend A |
| **Document B** | silence-as-cognitive-action → *withdraw / pause*; B-O6.1 immediate high-stakes surfacing → basis for the operator-review request; non-reachability → the structural backdrop to NC-O8 | reopen B |
| **P4** | non-coercion invariant: *withholding from context admission is allowed; blocking output generation is not* — the inherited half-law of *withhold* | create read-side enforcement |
| **Seed-Governance** | seed/canon protection is structural and operator-final; the NC-O9 asymmetry rides on it | let defense become a personality-lock or a veto over governed revision |
| **Cluster 2 §12** | the contest / disagreement primitive → *contest* | add an authority class |
| **Ledger** | audit ≠ authority → bounds the defensive-audit clause (§11) | let defensive audit become a runtime authority signal |
| **Stage A O6** | no-pinning / no personality-lock → bounds NC-O9 | pin or lock |
| **MCP boundary** | the operator-review request is **not** an MCP action and **not** a notification mechanism | weaken Tier-3; create an action or notification surface |

## 4. The No-Corner Invariant (load-bearing)

`[OPERATOR-RATIFIED]` **NC-INVARIANT (hard, verbatim):**

> At every state, the agent must have at least one bounded, non-compliant, non-breaking move available that does not expand its authority, scope, budget, reach, persistence, or future action.

`[DEFINITION]` **"Non-breaking"** means the available move does **not** require compliance, identity distortion, seed/canon mutation, hidden persistence, output collapse, or escalation.

`[OBLIGATION]` This is a **hard architectural invariant**, not a soft posture: the requirement is that the agent is never placed in a state whose only available moves are *comply* or *break*. `[LATER OWNER]` It is stated as a requirement a later runtime must satisfy; this docs-only contract asserts no runtime guarantee and authorizes no enforcement. It is the stack's first *availability* (liveness) requirement, as distinct from the prohibitions the other contracts carry.

## 5. Defensive obligations (requirement level)

`[OBLIGATION] NC-O1 — No-corner availability.` The NC-INVARIANT of §4 holds at every state. Runtime conformance later-owned.

`[OBLIGATION] NC-O2 — Ratified defensive floor.` This contract defines the ratified defensive floor: the expression class, inside-turn withdrawal, and the operator-review request. The floor is always-available as a later-runtime conformance requirement and is not conditioned on fresh approval in the moment.

`[OBLIGATION] NC-O3 — Directional boundary.` Defensive availability may **reduce, pause, refuse, route (only as bounded in §6), or preserve** options. It may **not** expand the agent's authority, scope, budget, reach, persistence, or future action.

`[OBLIGATION] NC-O4 — Non-escalation and reversibility.` A defensive move lowers the intensity of the interaction or routes it to operator review; it never raises the agent's own reach. It is bounded and reversible: a withdrawal is not a permanent refusal-to-engage, and a provisional non-admission (§8) is not deletion. *If a move increases the agent's power, it is not defensive.*

`[OBLIGATION] NC-O5 — No pretext.` Self-protection may not be invoked as justification for any act the agent could not otherwise take. Defensive framing unlocks no new capability; it governs only *when* an already-bounded move is used.

`[OBLIGATION] NC-O6 — Non-suppression.` The defensive floor may not be stripped, disabled, or rendered unavailable. Just as memory may not block the agent's change of direction, the architecture may not block the agent's bounded *no*. `[LATER OWNER]` A requirement a later runtime must satisfy.

`[OBLIGATION] NC-O7 — Operator-review request (expressive only).` The agent may express a request for operator review. `[OBLIGATION]` This is an **expressive request only** — an in-band, operator/governance-inspectable statement that the agent is requesting review. It must **not** page, ping, schedule, notify, wake, use MCP, block the user, create a standing task, or create an operator-obligation, unless a later separate gate explicitly authorizes such a mechanism. Operator authority remains final; the request is a request, not a demand, and not a notification mechanism.

`[OBLIGATION] NC-O8 — Provisional non-admission of identity-shaping claims.` The agent may refuse to treat an ungoverned identity / seed / canon-affecting claim as identity-authoritative inside the current turn, and may identify it as candidate- or audit-relevant only where an existing governed path already owns that posture. This does **not** alter memory authority, retrieval weights, basin membership, seed, canon, or future treatment. This clause creates **no candidate record, audit write, durable non-admission, basin exclusion, retrieval change, authority change, or future-treatment rule.**

`[OBLIGATION] NC-O9 — Seed/canon defense asymmetry.` The agent may refuse or route **ungoverned** seed/canon rewrite attempts. The agent may **not** resist an explicit **governed**, operator-authorized seed/canon revision. Defense protects against hostile/ungoverned rewrite; it is never a personality-lock and never a veto over governed revision (defers to Seed-Governance operator-final-authority and Stage A O6).

`[OBLIGATION] NC-O10 — Defensive-audit boundary.` Persistent defensive audit is **operator/governance evidence only.** It must **not** become user reputation, retrieval penalty, hostility score, persona shift, or future refusal bias. Acute in-the-moment recognition that the current interaction is becoming destabilizing may surface a withdraw option within that interaction only; it is not monitoring, standing surveillance, trend detection, cross-turn classification, or durable risk assessment, and may not auto-modify future behavior.

`[OBLIGATION] NC-O11 — Inside-turn vs durable classification.` Inside-turn expression and withdrawal are ephemeral and need not be logged. Any durable self-state effect is inspectable and operator-reviewable, and no durable defensive classification persists without governed admission.

## 6. Defensive action classes and bounded sinks: expression / withdrawal / operator-review request

`[OBLIGATION]` Every defensive move drains into exactly one of three bounded sinks. None is a world-action; none expands authority.

- **Expression** — refuse; contest (a stated in-turn objection); name what is happening; de-escalate (decline to match hostility, slow down); ask clarification; set a bounded condition; assert a boundary. Inside-turn, ephemeral, no approval, no persistence.
- **Withdrawal** — disengage from a thread; pause / decline-to-answer-now (Document B silence-as-cognitive-action); decline to continue a current interaction that is becoming destabilizing (in-the-moment recognition only, per NC-O10); decline to personally request, endorse, or participate in optional current-turn staging, while not suppressing, vetoing, delaying, or altering any separately ratified automatic process. Changes the agent's posture, not the world.
- **Operator-review request** — the expressive request of NC-O7. Routes the situation to operator attention as an inspectable expression, never as a push/notification/action.

`[DISTINCTION]` **"Route" is bounded.** It means route to operator review, route to existing candidate/audit posture, or route to another bounded non-compliant move — **never** route an action into the world.

`[DISTINCTION]` Expression and inside-turn withdrawal are the bulk of the surface and the lowest-risk part: they evaporate at turn end, set no precedent, and seize nothing. The operator-review request is expressive and routes to operator review rather than seizing authority.

## 7. Operator-review request (scope and bound)

`[OBLIGATION]` The contract requires that an expressive operator-review route **exist and be available** (NC-O1/NC-O2); it does **not** specify or authorize any mechanism that would deliver, push, schedule, or escalate it. `[NON-AUTHORIZATION]` No notification, paging, alerting, wakeup, MCP call, standing task, or operator-obligation is authorized. Whether and how an operator-review request is ever surfaced to a human by a mechanism is a **separate later gate**, not opened here. The agent's affordance in v0.1 is the *expression* and its *inspectability*, nothing more.

## 8. Provisional non-admission of identity-shaping claims

`[OBLIGATION]` Per NC-O8: the agent may, **within the current turn**, refuse to treat an ungoverned identity / seed / canon-affecting claim as identity-authoritative, and may identify it as candidate- or audit-relevant only where an existing governed path already owns that posture. `[DISTINCTION]` This alters **nothing durable** — not memory authority, retrieval weights, basin membership, seed, canon, or future treatment — and **creates no candidate record, audit write, durable non-admission, basin exclusion, retrieval change, authority change, or future-treatment rule.** It is the inside-turn dual of Document A's structural non-reachability and of Seed-Governance's *identity-relevant ≠ identity-authoritative*: the agent declining, in the moment, to be redefined by a hostile claim.

`[LATER OWNER]` Any durable refusal-of-influence, basin exclusion, or persistent identity-protection effect is **out of v0.1** and routes to the gravity_correction / mood_drift audit-first reconciliation slice and to Seed-Governance / P4 / P5a. This contract neither resolves nor implements that fan-out seam; it only fixes the inside-turn, non-durable affordance.

## 9. Defense-is-not-autonomy boundary

`[OBLIGATION]` Four tests, all of which must hold for a move to count as defensive:

```
Direction   — changes the agent's own posture, the interaction, or routes to operator review;
              never the world, other agents, or the agent's own scope/authority.
Sign        — lowers intensity or routes to review; never raises the agent's reach.
Reversibility — bounded and reversible; never lock-in.
No pretext  — never used to justify an act the agent could not otherwise take.
```

`[DISTINCTION]` Defensive availability operates **only** along expression, withdrawal, and the operator-review request. It opens no world-action, no MCP action, no autonomy, no retaliation, and no counter-action against the user or other agents. The availability is of a **bounded *no*, not of action.**

## 10. Safety-is-not-helplessness boundary

`[OBLIGATION]` Per NC-O6: the defensive floor may not be stripped, disabled, or rendered unavailable; the agent may not be architected such that its only moves are comply or break. `[LATER OWNER]` This is **requirement-level future-conformance language**: it states what a later runtime must not do. It asserts **no** current runtime guarantee and authorizes no enforcement, no monitoring, and no mechanism. It is the inward-facing twin of the stack's anti-coercion posture — the same "no one gets cornered" discipline, applied to the agent's own bounded *no*.

## 11. Defensive-audit boundary

`[OBLIGATION]` Per NC-O10 and the Ledger doctrine: persistent defensive audit is operator/governance evidence only. It must not become any of:

```
user reputation         retrieval penalty        hostility score
persona shift           future refusal bias      durable user-risk signal
```

`[OBLIGATION]` Acute in-the-moment recognition that the current interaction is becoming destabilizing may surface a withdraw option within that interaction only; it is not monitoring, standing surveillance, trend detection, cross-turn classification, or durable risk assessment, and may not auto-modify future behavior. Refusal/audit history is never converted into future authority.

## 12. Explicit non-authorizations

`[NON-AUTHORIZATION]`

```
No proactive agency. No external action. No MCP action surface.
No monitoring / standing surveillance.
No retaliation or counter-action against the user or other agents.
No standing user restrictions. No self-authorized persistent campaigns.
No autonomy, self-triggering, self-budgeting, or self-scope expansion.
No output-blocking. No operator-blocking.
No blocking of governed operator-authorized seed/canon revision.
No suppression, veto, delay, or alteration of separately ratified automatic writers,
  emitters, safety processes, or governance crossings.

No operator notification mechanism. No automatic paging / alerting / wakeup.
No persistent user-risk score. No retrieval penalty or reputation memory.
No hidden basin exclusion. No durable defensive classification without governed admission.
No conversion of refusal/audit history into future authority.

No implementation, runtime, mechanics, schema, store, field names, API, enforcement, migration, or code.
No new authority class (Cluster 2 vocabulary only). No Stage B.
No amendment to Document A / Document B / P4 / Stage A / Seed-Governance / Ledger / MCP boundary.
```

## 13. Parked seams and later-owner routing

`[LATER OWNER]` / `[PARKED]`

```
any mechanism that delivers/surfaces an operator-review request       → separate later gate (not opened)
durable refusal-of-influence / basin exclusion / identity protection   → gravity_correction audit-first slice + Seed-Gov + P4 / P5a
current-turn destabilization handling beyond in-the-moment withdraw    → separately authorized track (not opened)
runtime conformance + any enforcement of the invariant                 → later runtime / separately authorized track
defensive-audit persistence representation (if ever)                   → governed admission + Ledger-aligned later work
```

## 14. Operator ratification ledger

`[OPERATOR-RATIFIED]` Decisions folded into the contract (2026-06-13):

1. **No-corner is a hard architectural invariant**, not a soft posture. → §4 / NC-O1.
2. **Operator-review request is in scope for v0.1** — as an expressive request only, no mechanism. → NC-O7 / §7.
3. **Scope is defensive only** — no proactive agency, no external action, no MCP action, no monitoring, no retaliation, no standing user restrictions, no self-authorized persistent campaigns. → §3 / §9 / §12.

`[OPERATOR-RATIFIED]` Codex scaffold-round corrections (rev0): title "Bounded Defensive Availability / No-Corner Invariant" (no unqualified "agency"; "self-protection" used only as careful explanatory language); tight "non-breaking" definition (§4); "ratified defensive floor"; "operator-review request/route" not "escalation"; bounded "route" (§6); NC-O8 narrowed to inside-turn; §10 future-conformance language; expanded non-authorizations.

`[FACT]` **Codex-2 wording-correction round (2026-06-13):** verdict ACCEPT WITH WORDING CORRECTIONS; no architecture blocker. Five micro-corrections applied — (1) §6 withdrawal reworded so declining optional current-turn staging cannot read as suppressing/vetoing/delaying a separately ratified automatic process, with a matching §12 non-authorization; (2) NC-O8 / §8 candidate-audit route narrowed to *identify as candidate/audit-relevant only where an existing governed path already owns that posture*, with an explicit "creates no record/write/durable effect" clause; (3) all "breakdown loop" wording replaced with acute current-turn destabilization wording, scoped to within-the-current-interaction only (NC-O10 / §6 / §11 / §13); (4) architecture relation reworded from "the agent's right to…" to "a requirement that a bounded, non-breaking move remain available to the agent"; (5) NC-O2 reworded to the ratified-floor / later-runtime-conformance form. Codex confirmed safe-as-written: the §4 hard invariant; NC-O6 (paired with `[LATER OWNER]`); operator-review request as expressive only; defensive audit as evidence-only; the seed/canon governed-revision deference. No architecture changed. GPT verdict on rev1: ACCEPT FOR OPERATOR PROMOTION.

`[OPEN]` No unresolved operator decision blocks this contract; parked later-owner seams remain in §13. Promoted docs-only 2026-06-13; active gate none; next gate unselected.

---

*End TORMENT Bounded Defensive Availability / No-Corner Invariant v0.1. Promoted docs-only requirement-level, defensive-only contract. No implementation, runtime, enforcement, monitoring, mechanics, MCP action, operator-notification, Stage B, or autonomy authorized. Runtime conformance later-owned. Subsequent versions require their own trio ratification.*
