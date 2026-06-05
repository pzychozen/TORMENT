# Track B v0.2 — Cognition-Coupling Architecture Fork Memo v0.1

**Status:** Tracked framing artifact. **Framing-only. Not doctrine. Not implementation authorization. Not a Track B slice. No fork selected. No probe authorized. No P6 audit opened. No repair lane opened.**
**Date:** 2026-06-05
**Author:** Claude (drafter), for the trio (Hilmir as operator + GPT review + Codex adversarial review).
**Review lineage:** Claude draft → GPT synthesis → two Codex adversarial-verification rounds (architecture map corrected; runtime boundaries verified) → P5 read-only trace closed → Codex final promotion review: **ACCEPT WITH CORRECTIONS** → operator promotion (Hilmir, 2026-06-05).
**Audit baseline:** resting checkpoint `8d948f7` (post B2-S4). Read-only.
**Anchors:** `LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1.md`, `TRACK_B_V0_2_CONTEST_LEDGER_RUNTIME_BOUNDARY_FRAMING_v0.1.md`, `TRACK_B_V0_2_B2_S4_COUNTER_CONTEST_EVENT_FRAMING_v0.1.md`, `CHECKPOINT_2026-05_CHARACTER_MEMORY_PROBE_V0.md`.
**Mode:** Framing-only. No code, schema, probe, retrieval change, prompt change, doctrine edit, or repair lane. A separate operator decision is required before anything downstream.

---

## 1. Status and purpose

This memo names an architecture fork the project has just walked up to and must not cross by momentum. Track B v0.2 has built a **closed, isolated disagreement substrate through B2-S4, including a verdict-free counter-contest event shape** — and that property is *not* uniform: `CounterContestEvent` is verdict-free, while `ContestRecord` still carries `contest_result` (the contestant's proposed authority outcome). The next question is no longer "what is the next storage slice"; it is whether — and through which architectural surface — remembered disagreement could ever become *psychologically meaningful to a character* without becoming control. That is a project-level decision touching character freedom, architecture, doctrine, and the operator's meaning of automation. This memo makes the alternatives explicit and answers none of them.

## 2. Verified current substrate

Binding starting ground, after Codex correction:

```
No live service path currently implements a separate LLM deliberation room.
Cognition roles are deterministic.
ThinkingController is deterministic but behavior-shaping.
AgentRunner, where wired, performs at most one LLM synthesis pass.
```

Concretely:

- **No deliberation room.** There is no production path shaped like *model call A → internal reasoning artifact → model call B → user-facing response.*
- **Cognition roles are deterministic.** `roles/base.py:9,71-72`, `roles/interpreter.py:8-10` — rule-based transforms, no network/LLM/filesystem calls. `cognition/pipeline.py:28-135` is a single-pass deterministic orchestration whose `final_answer` / `dissent` / `memory_effects` / `routing` are returned in the `/cognition/run` payload. Separately, the app endpoint has an env-gated archivist write-back path through `TORMENT_ARCHIVIST_WRITEBACK`, default `0`, while Spine cognition remains intentionally read-only.
- **ThinkingController is deterministic but behavior-shaping — not merely observational.** Its `memory_plan` (derived from raw input, source_type, text-derived sensitivity tags, and mode selection) can **alter lane retrieval opportunity, including functional lane starvation through `top_k = 0`** for lanes such as relational / archive / deep / collective. Lane **weights** also affect scoring, although weights are clamped to `[0.1, 2.0]` before application (so `weight=0` is not hard scoring deletion after clamp, but `top_k=0` is functional lane starvation). App and Spine pass the plan into `fabric.query()` by default; deep retrieval is additionally bounded by remaining headroom.
- **Verified Spine-wording contradiction (flagged, not opened).** Spine currently states advisory thinking "NEVER influences execution," but the query-memory paths pass `memory_plan` into `fabric.query()` and therefore alter retrieval opportunity. This inaccuracy is **parked as a separate documentation/runtime-boundary concern** — not fixed here, no slice proposed.
- **AgentRunner one-pass synthesis.** Where wired, AgentRunner performs at most a single LLM synthesis pass — not a multi-call deliberation.
- **Live retrieval/assembly is active.** `/agent/query`, MCP `query_memory`, and `/retrieve` carry live retrieval, ranking, filtering (`filter_llm_facing`, `fabric.py:41`), and assembly behavior. Retrieval already applies default-on score bonuses — `affect_match`, `mood_drift`, `mood_spiral_penalty` (`fabric.py:4066-4173`) — and a query-keyword `wants_contested` gate (`fabric.py:3987,4149`).
- **Track B is isolated and non-load-bearing.** The four modules import only each other and tests; AST conformance guards enforce zero production importers. No current consumer wires contest history into retrieval, governance, cognition, prompt assembly, MCP, or output.

The honest one-line map: **deterministic cognition machinery + behavior-shaping retrieval planning (including possible functional lane starvation) + an optional one-pass LLM synthesis** — *not* an internal deliberation room.

## 3. Operator intent (to preserve)

A remembered disagreement should not remain psychologically inert forever. A future character encountering a relevant remembered tension may: hesitate, reconsider, compare it against other evidence, resist it, reinterpret it through persona, decide it does not matter, ignore it entirely, mention it naturally, or choose not to mention it. **The option to ignore is load-bearing.**

```
A character that may decide a tension does not matter is deliberating.
A character that must acknowledge it is being operated.
```

Desired posture: **pressure, not puppet.** This memo treats that as an aspiration requiring falsifiable boundaries — not as an already-proven property of the architecture.

## 4. Why the current substrate cannot honestly claim cognition-only influence

The "pressure in the mind, not the mouth" image presupposes a private thought chamber separate from expression. **That chamber does not exist in the live character path.**

```
The live voice is a single client-side generation pass.

The minimal prompt is a Probe-v0 harness property,
not a production property.

Production clients already inject labeled context; see §5 Fork A.
```

For a one-pass model, any token placed in context can shift the output distribution; there is no mechanism that touches "deliberation" but not "expression," because they are the same forward pass. **There is no private deliberation room separate from expression in the live path.** Therefore a guarantee of the form *"influences cognition but never output"* is stronger than the substrate can provide. The honest contract any surfacing could offer is behavioral: **verdict-free, non-deterministic, non-templated, inspectable, experimentally ablatable across matched paired runs, retrieval-rank-neutral only** — never "mind-only," and never isolatable inside a single live generation. Calling Fork A "cognition-only influence" would be a category error; the accurate term is **token-bounded model conditioning** (token size bounded; behavioral effect not presumed bounded).

## 5. Architecture forks

### Fork A — existing model-facing prompt surface (token-bounded model conditioning)

*Verdict-free contest annotation, added only beside a memory selected independently of contest state, included in the same one-pass character generation context.*

Honest assessment: psychologically meaningful; **retrieval-rank-neutral only** if carefully bounded; inspectable; **experimentally ablatable across matched paired runs**; **no separate inner room**; can still influence output; risks steering; risks mandatory acknowledgment; risks invented canon.

```
Fork A collides with the Probe-v0 clean-prompt discipline,
which is harness-only.

Whether that discipline should govern production prompt assembly
is an open doctrine and architecture question.

Verified caveat:
production prompt assembly is not clean today.

Example production clients already inject model-visible:
- scores
- tier tags
- provenance tags
- [Drift:]
- [Core identity]
- [Guidance]
- [Voice:]
- [Flavor:]

A contest annotation in production would therefore not breach
an existing production clean-prompt safeguard, because no such
safeguard currently exists.

It would join an already-labeled prompt surface whose own
doctrine compliance is unresolved.

That does not lower Fork A's steering, salience, puppetry,
or invented-canon risk.
```

(Anchors for the caveat: `examples/character_chat_probe.py:239-247,531-568`; `torment_service/retrieval_assembler.py:83,193-195,282`; `CHECKPOINT_2026-05_CHARACTER_MEMORY_PROBE_V0.md:52`.) Also note:

```
Fork A is not isolatable inside one live generation.
The presence of annotation tokens changes model conditioning
and may alter the full output distribution.

Retrieval-rank-neutral does not mean prompt-effect-neutral.
An annotation can leave hit selection unchanged while still changing
salience, attention distribution, voice, emphasis, confidence,
or surrounding invention inside the one-pass generation.

Token size may be bounded. Behavioral effect is not presumed bounded.
```

It is token-bounded model conditioning, not cognition-only influence.

### Fork B — deterministic cognition channel

*Contest history routed through the deterministic cognition / dissent / reintegration surface as an audit-visible structured result.*

Honest assessment: inspectable; deterministic; preserves verdict-free disagreement; may support operator observability. It does **not** currently deliver character hesitation in the live voice-generation sense — `/cognition/run` makes no model call and terminates in a payload. An audit payload is not a psychological effect, and this memo will not pretend it is.

**Producer isolation != consumer isolation.** Fork B is observational **only while both conditions hold:**

```
1. Producer boundary:
   cognition output does not directly alter planning, retrieval,
   ranking, suppression, routing, action selection, tool execution,
   or write-back.

2. Consumer boundary:
   downstream internal or external consumers do not read cognition
   payload fields (final_answer / dissent / memory_effects / routing)
   and convert them into behavior-shaping decisions.
```

A structured audit payload can launder control through an external orchestrator; payload visibility alone is therefore not harmless. App `/cognition/run` can pass `ingest_fn = fabric.ingest` and thus already has an env-gated write-back path (default off); Spine cognition is read-only. No current local examples, live agents, or harness consumers were found converting cognition fields into retrieval/ranking/assembly/routing/action/write-back — **but absence of current local consumers does not prove safety.** The **AST importer guards around Track B and cognition modules do not prove consumer-side isolation**; a runtime-boundary argument would eventually have to account for both producers *and* consumers. Any future consumer of cognition output must be classified before Fork B can remain observational. "Observational groundwork" must not become an implicit permission path.

### Fork C — new genuine deliberation boundary

*model call A → bounded deliberation artifact → model call B → user-facing character response.*

Honest assessment: Fork C is **the most literal structural candidate for separating bounded deliberation from final expression** — it creates a real intermediate surface that could, in principle, be inspectable and ablatable, and could allow bounded contest visibility *before* the final response. That structural match is the *only* thing it has going for it.

```
Fork C is not presumed safer.

A new deliberation room may amplify:
- steering
- invented canon
- recursive drift
- latency
- hidden authority
- automation-posture risk
```

A room can become a steering chamber. Fork C introduces new architecture and new failure modes, **is not a Track B micro-slice**, and would require separate ratification as a foundational architecture decision. No implementation is recommended here.

A fourth, **staged**, possibility is named only as a sequencing question, not a recommendation: *Fork B as observational groundwork — observational only under producer and consumer isolation — with Fork C considered separately and only if evidence later warrants it.* It is listed in the open decisions (§11), not advocated.

## 6. Doctrine consistency and ratification choices

State plainly:

```
Current doctrine does not permit model-visible contest facts today
as silent live prompt or ranking inputs.
Any future model-visible surfacing requires a separately ratified
governance decision.
```

The Ledger Observational-Boundary Doctrine §3 forbids audit feeding **intent formation** and forbids contests being "silently auto-resolved by appeal to audit history." The Track B framing §9 distinction — a `ContestRecord` is "a durable authority-action record whose visibility is audited," not "audit" — may be relevant to evaluating a future separately ratified single-record projection, but does not itself permit surfacing, and **dissolves for contest history** (counts, recency, chains), which is audit-shaped and falls back under §3. That distinction is a door, not a wall, until an explicit clause is written.

**Even a single-fact projection is not harmless by definition.** Repeated exposure of "a disagreement exists here" may still produce indirect density, salience, familiarity, or posture effects even when explicit counts and recency signals are absent. Thinner is not the same as safe.

Possible rulings (for the operator to choose, not for this memo):

```
A. remain doctrine-consistent by keeping contest history audit-only
B. clarify doctrine to permit one verdict-free, retrieval-rank-neutral
   fact-of-contest annotation
C. ratify a narrow exception for bounded experiment only
D. amend doctrine to permit a broader cognition-coupling surface
E. reject model-visible contest surfacing as incompatible
```

This memo does not imply that ruling B is already acceptable; it is one possible future ruling among five. Whichever is chosen, these prohibitions are preserved: density weighting; count-based trust signals; recency-as-precedence; append-order precedence; latest-event-wins; contest-result surfacing; hidden suppression; rank changes caused by contest history; mandatory acknowledgment.

## 7. Data-shape constraints

Preserve the verified asymmetry:

```
CounterContestEvent → verdict-free (no outcome field)
ContestRecord       → carries contest_result (contest_record.py:220)
```

If any future experiment is ever authorized, **do not surface a full `ContestRecord` blindly** — its `contest_result` would hand the character a verdict. Candidate projections, ordered thinner → richer, are **the thinnest currently imaginable candidate projections for later evaluation, if separately ratified** — not an emerging design choice:

```
A. "a disagreement exists here"
B. "a disagreement exists here, for reason_class=X"

Projection B carries more posture and would require separate justification.
Neither projection is authorized.
```

Projection A is the bare minimum and is still not harmless — repeated exposure may produce indirect salience/familiarity/posture effects (§6). `reason_class` (Projection B) hands the character a *frame* a pattern-completing character could inflate; it is an optional escalation that must justify itself, not a default.

```
Event-shaped projection is thinner than surfacing ContestRecord,
but it remains posture-bearing and requires separate ratification.
thinner != safe
```

If anything is ever surfaced it must be event-shaped (never `ContestRecord` with `contest_result`), **retrieval-rank-neutral only**, single-fact, linked to a memory **selected independently of contest state**, inspectable, and **experimentally ablatable across matched paired runs** — described here, authorized nowhere.

## 8. Surfacing-gate risks

```
A surfacing gate can become a relocated resolver.
```

Removing the classical resolver does not remove the authority problem; it moves it to "which tensions are surfaced, and when." Any future gate must be scrutinized for: ranking influence; eligibility influence; suppression; density weighting; recency weighting; salience amplification; append-order precedence; latest-event behavior; hidden authority routing. The lowest-risk *conceptual* shape — a candidate for evaluation only, not an authorization:

```
contest status never changes whether or where a memory surfaces;
it may only annotate a memory selected independently of contest state.
```

Even this is not authorized here, and even here, **selected independently of contest state does not mean prompt-effect-neutral** — annotation can still change salience inside the one-pass generation. On the clean-prompt question:

```
By the Probe-v0 harness contract's terms,
a contest annotation is audit-shaped model-visible text.

That contract is harness-only,
so it does not by itself bar a production annotation.

The live question is therefore not:
"does this break the production clean prompt?"

Production has no clean-prompt rule today.

The live questions are:
- should production adopt a clean-prompt discipline?
- does today's labeled production assembly already satisfy
  the observational-boundary doctrine?
- would adding contest annotation worsen an unresolved surface?
```

This memo does not answer those questions.

## 9. Measurement-first requirement

Probe-v0 run `3059` is the warning shot:

```
clean fact surfacing → invented surrounding manuscript detail
```

What it supports: invented-canon risk is real; model-visible memory content can expand beyond the stored fact; any future contest-annotation experiment requires paired-run ablation. What it does **not** prove: it does not prove puppetry; it does not prove contest annotations are unsafe; it does not prove a separate cognition room exists.

A future probe (not designed here) would need to distinguish: acceptable natural reflection; healthy ignore behavior; mandatory acknowledgment; templated uncertainty; voice flattening; invented canon; false-authority expansion; retrieval-rank drift. The current Probe rubric scores invented authority but does **not** yet score puppetry/flattening — a named gap.

Hard epistemic limit, stated plainly:

```
Paired-run A/B comparison can reveal behavioral drift,
but cannot prove:
- cognition-only influence
- live isolation
- reversible conditioning
- access to a private inner room
```

## 10. Existing behavior-shaping precedents

TORMENT already contains deterministic, authority-shaped behavior in retrieval planning: ThinkingController `memory_plan` (including possible **functional lane starvation via `top_k = 0`** and clamped lane weights), lane top-k, affect scoring, mood drift, contradiction handling (`wants_contested`), reinforcement, SRG adjustments, and FILTER-A suppression. It also already presents **labeled, audit-shaped context to the production model prompt** (scores, tiers, provenance, `[Drift:]`, `[Core identity]`, `[Guidance]`, `[Voice:]`, `[Flavor:]` — see §5 Fork A caveat and P6). So the real question is not *whether* cognition-adjacent control may shape what the character sees and reads — it already does — but: which influences are legitimate, bounded, inspectable, contestable, and compatible with character freedom?

```
implementation fact != normative precedent
```

That these mechanisms ship proves influence *exists*. It does **not** prove:

```
- that every current influence is doctrinally settled
- that every current influence is desirable
- that contest history may reuse those mechanisms
- that ranking or the labeled prompt is the correct home for future coupling
```

Existing behavior is **evidence to audit, not automatic permission.** In particular: existing ThinkingController behavior, and the existing labeled production prompt surface, are implementation facts requiring separate future architectural scrutiny; they are not precedent authorizing Track B coupling, and **any future Track B input into ThinkingController or the production prompt would require its own authority-boundary audit before any discussion of wiring.** That affect/mood bonuses already nudge rank, or that production already injects labeled context, does not license a contest signal to do either.

## 11. Open operator decisions (for Hilmir — not answered here)

```
1. Desired long-term architecture:
   A. token-bounded prompt conditioning (Fork A)
   B. deterministic cognition visibility (Fork B)
   C. a genuine new deliberation phase (Fork C)
   D. a staged path where B is observational groundwork — under producer
      and consumer isolation — before separately considering C

2. Doctrine:
   A. remain unchanged (audit-only)
   B. allow a narrow single-fact clarification
   C. permit a probe-only exception
   D. be amended later only after evidence
   E. reject model-visible contest surfacing

3. Is an event-shaped projection thin enough, or must the first
   hypothetical projection expose only "a disagreement exists here"
   (dropping reason_class)?

4. Must measurement instrumentation be framed before any
   cognition-coupling implementation discussion?

5. Does a new deliberation phase (Fork C) alter the project's
   automation posture enough to require a separate architecture lane?
```

## 12. Explicit non-goals

No edits, no implementation, no patch, no slice number, no B2-S5, no prompt injection, no cognition wiring, no resolver, no surfacing gate, no retrieval weighting, no suppression, no authority score, no confidence score, no probe design, no probe implementation, no payload-contract design, no runtime-assertion design, no MCP change, no ThinkingController repair lane, no P6 audit, no automation design, no autonomy expansion, no database work, no fork selection.

## 13. Recommended next discussion boundary

This memo recommends a *process*, not a fork. The decision in §11 #1 is the load-bearing one and is genuinely the operator's: it determines whether "pressure, not puppet" is pursued inside the existing one-pass context (Fork A), held to deterministic observability (Fork B), or eventually given a real room (Fork C) — with no fork presumed safer in advance. Two process points are safe to assert without choosing a fork:

```
- measurement instrumentation is a framing requirement only;
  it must be framed before coupling implementation can be discussed,
  and no probe shape, probe implementation, or experimental annotation
  is authorized by this memo;

- the doctrine question must be answered in writing before any
  model-visible surfacing (current doctrine does not permit model-visible
  contest facts today as silent live prompt or ranking inputs).
```

D1 (this lane) and D2 (authority-versus-emergence) should be treated as one lane with two guardrails — puppetry and invented canon. Beyond that, the fork is open; the blueprint should be drawn before the door is built.

## 14. Parked concerns surfaced by this audit (recorded, not opened)

These were surfaced while producing this memo and are preserved for discoverability. None is opened by this artifact; each would require its own audit-first cycle and explicit operator authorization.

```
P1  Spine doc/runtime inaccuracy: advisory thinking "NEVER influences execution"
    is false for query-memory (memory_plan -> fabric.query()).
P2  ThinkingController lane-starvation (top_k=0) as an existing behavior-shaping
    authority path deserving its own future architectural scrutiny.
P3  Default-on retrieval bonuses (affect_match / mood_drift / mood_spiral_penalty)
    vs the observational-boundary doctrine.
P4  Probe rubric gap: scores invented-canon but not puppetry/flattening.
P5  RESOLVED — clean-prompt discipline is harness-only.
    Anchors: character_memory_harness/test_prompt_surface_offline.py:5-6,28-33,51,115-138;
    character_memory_harness/run_bounded_loop.py:493;
    examples/character_chat_probe.py:239-247,531-568;
    torment_service/retrieval_assembler.py:83,193-195,282;
    docs/CHECKPOINT_2026-05_CHARACTER_MEMORY_PROBE_V0.md:52
P6  Production prompt assembly already injects audit-shaped,
    score-/tier-/provenance-/drift-labeled model-visible context.
    Whether that existing labeled surface complies with the
    observational-boundary doctrine is a separate open question.
    Flagged. Parked. Not opened.
```

---

*End of Track B v0.2 — Cognition-Coupling Architecture Fork Memo v0.1. Tracked framing artifact (operator promotion, Hilmir, 2026-06-05). Framing-only: not doctrine, not implementation authorization, not a Track B slice; no fork selected, no probe authorized, no P6 audit opened, no repair lane opened. Names the verified architecture boundaries and frames the operator decision. Subsequent framing or doctrine versions require their own ratification before they supersede this one.*
