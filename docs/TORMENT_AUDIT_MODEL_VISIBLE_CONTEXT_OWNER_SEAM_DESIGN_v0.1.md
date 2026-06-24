# TORMENT Audit — Model-Visible Context Owner Seam Design (ADR) v0.1

**Status:** DRAFT — docs-only design / ADR. It **authorizes no code, no tests, no
wiring, no endpoint/schema/API, and no AgentRunner change.** It designs the
minimal *internal, non-endpoint* owner seam for a future caller-owned same-turn
provenance path, following the prompt-inclusion harness proof shape. Another
Codex/operator review is required before any production module or AgentRunner
prompt-path change.

**Baseline:** read-only; Windows repo state authoritative.

**Relation to previous proof artifacts (design follows them; implements none):**

- `382a0f1` — caller-owned same-turn provenance contract: `AgentRunner` composes
  explicit inputs only; the caller owns the same-turn claim; pre-extracted item
  dicts only, never `AssembledContext`; co-location ≠ provenance; observation-only
  packet; no public endpoint/API/flag/wiring.
- `464320a` — A-prime prompt-boundary characterization: the model-visible
  boundary is `AgentRunner._execute`'s `self._build_system_prompt(frame, mode)` +
  `llm_client.complete(system_prompt, messages=[user frame.raw_input])`; the
  prompt path consumes no admitted context, so a retrieve/assemble-then-`run_turn`
  wrapper proves only co-location.
- `ba41a44` — candidate model-visible context characterization: `assembled_text`
  is candidate material (not today's prompt context); `selected_admitted_items`
  is the extracted subset; packet snippets are minimized audit evidence whose
  marker/identity exclusions are audit boundaries, not prompt rules.
- `59b582e` — prompt-inclusion harness: the executable proof shape — render into
  the exact model-visible prompt/messages, capture that boundary before
  generation, prove selected item-text inclusion, only then compose audit
  evidence; refuse if any selected item text is absent; co-location insufficient.

**This design follows the `59b582e` harness but does NOT implement it.** It names
the seam, responsibilities, call order, I/O, and the non-reentry guarantees a
future (separately reviewed) module would have to satisfy.

**Governed by, amends in no way:** the caller-owned provenance contract; the
Admissible Evidence Packet Contract (§2/§5 same-turn rule, §4 + §4A exclusions,
§6 incomplete-evidence, §7 non-reentry); the boundary frame (`444cc9b`); Document
B; P4; the Ledger Observational-Boundary; Track-A; the MCP capability boundary.

**Core posture (governing).** TORMENT is an ethical memory system, not a control
system. *Audit observes authority; audit does not become authority.*

---

## 1. Framing

- The owner is **separate from `AgentRunner`** at first — a distinct internal
  component, **not** an endpoint and **not** part of the public API.
- The owner **may eventually own or wrap prompt construction**, but `AgentRunner`
  **must not silently absorb retrieval / assembly / provenance ownership**. If a
  later step gives the owner prompt construction, that is its own ratified change,
  not an implicit side effect.
- This design **creates no live provenance**, no endpoint/public-API/schema
  behavior, and **authorizes no production wiring**.

This is the role the caller-owned provenance contract (`382a0f1`) left
deliberately unselected: the concrete internal owner. It is named here as a
**design**, not built.

## 2. Owner responsibilities

A conforming owner MUST:

1. **Render the exact model-visible prompt/messages** for the turn.
2. **Capture the exact prompt/messages** handed to generation (the same bytes the
   model sees), before generation runs.
3. **Prove every `selected_admitted_items(...)` text is present in that captured
   context** before passing any item onward.
4. **Pass only selected admitted item dicts** — **never `AssembledContext`** —
   into audit composition.
5. Treat **packet construction as observation-only**, after response generation
   and review finalization.
6. **Fail closed** for packet/provenance observation if inclusion cannot be
   proven (no packet rather than an unproven one).

## 3. Call-order sketch (design only)

```
1. Build or RECEIVE an AssembledContext.            # owner's frame, not AgentRunner's
2. items = selected_admitted_items(assembled)       # extracted from the SAME object
3. render the candidate context into the EXACT model-visible prompt/messages
4. capture the final rendered prompt/messages       # before generation
5. prove every item text in items is present in the captured prompt/messages
       └─ if not provable: FAIL CLOSED (no packet); proceed with generation only
6. call generation                                  # the model sees the captured context
7. complete review / response finalization          # review remains the only suppressor
8. compose audit evidence ONLY AFTER (5) proved AND final response available
9. return the observation packet AS OBSERVATION ONLY # never as authority
```

The ordering is load-bearing: inclusion is proven against the **captured**
prompt/messages (step 5) **before** generation (step 6); the packet is composed
**after** the final reviewed response (step 8). Co-location of items and response
on a result object never substitutes for step 5.

## 4. Non-reentry / non-control guarantees

The owner MUST NEVER:

- retrieve again for the audit;
- re-filter raw hits;
- use stale / different-turn context;
- infer provenance from co-location;
- use packet snippets as prompt material;
- pass `AssembledContext` into `AgentRunner`;
- add endpoint / API / schema fields;
- add `same_turn_verified`, `truth`, `authority`, `provenance`, verification,
  certification, or equivalent flags;
- route audit results into prompt, review, output suppression, ranking, retry,
  style steering, persistence, memory writes, fabric, writer paths, retrieval
  feedback, eligibility, or authority decisions;
- make packet absence evidence of dishonesty or unsupportedness.

## 5. Explicit hidden-authority warning

**This becomes output control or hidden authority the moment packet/inclusion
results can revise, block, rank, suppress, retry, steer style, affect review,
change memory eligibility, become model-visible feedback, or influence writer
paths.** The owner is observation-only by construction; any feedback edge from
audit output back into the turn is the line that must not be crossed. The
inclusion proof (§2.3) gates *whether an observation packet may exist*, never
*what the agent says or does*.

## 6. Inputs / outputs to name

**Inputs:**

- user input;
- assembled context or candidate context material — **used by the owner, not
  passed into `AgentRunner`**;
- selected admitted item dicts extracted from the **same** assembled result;
- generation configuration / system-prompt ingredients, if needed.

**Outputs:**

- final response text;
- **optional** observation-only audit evidence packet (absent when inclusion is
  unproven or the response is empty/blocked — fail-closed);
- captured prompt/context debug/audit material **only if explicitly allowed in a
  later ratified step** (not authorized here);
- **no verification flag.**

## 7. Not yet (what this ADR does not authorize)

- No production code.
- No tests (unless this design reveals a concrete contradiction).
- No `AgentRunner` change.
- No endpoint, `/retrieve`, `/agent/query`, public API, schema, or
  provider/model/prompt/evaluator behavior change.
- No persistence, memory write, output control, authority, database/substrate,
  dream/private cognition, Gate D, or Envelope Audit runtime.
- **Another Codex/operator review is required before any production module or
  AgentRunner prompt-path change.**

The first permissible later step, *if* ratified, would be a minimal
internal-only owner module (no endpoint) plus tests, mirroring the `59b582e`
harness shape — built only after this design is reviewed and a production module
is explicitly allowed.

---

*End — TORMENT Audit Model-Visible Context Owner Seam Design (ADR) v0.1.
Docs-only; designs the internal non-endpoint owner seam following the prompt-
inclusion harness proof shape; authorizes no code, no wiring, no AgentRunner
change. Wiring stays blocked pending explicit Codex/operator review.*
