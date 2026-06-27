# TORMENT — Memory-to-Prompt-for-Generation Architecture Decision Frame v0.1

## 0. Status

**Architecture decision frame. Docs-only / NON-AUTHORIZING / no lane opened.** This
frame asks **one decision question** and nothing more. It selects no mechanism, no
caller, no prompt format, no memory source, no carrier, no schema, no endpoint, no
owner, no runtime, and no implementation path. It is **not** a prompt-design proposal:
it does not say *how* memory could become model-visible, only *whether the question may
be opened at all*. The decision is **Hilmir's**.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `b8cb6fa` (repo edge). Subordinate to the pre-database cognition ceiling frame
(`docs/TORMENT_PRE_DATABASE_COGNITION_CEILING_ARCHITECTURE_DECISION_FRAME_v0.1.md`,
fork Option 1).

## 1. Scope

```text
ASKS: one decision question (§4) — may the authoritative AgentRunner generation path
      consume retrieved/assembled memory, i.e. may memory become model-visible to
      generation at all?

DOES NOT:
  - answer it by selecting a mechanism / caller / prompt format / source / carrier /
    schema / endpoint / owner / runtime / implementation;
  - propose a prompt design, injection point, or memory representation;
  - lift the "no model-visible prompt change" fence;
  - open any lane.
```

## 2. Current root ceiling — memory-blind generation (source-verified)

The authoritative generation path does **not** consume retrieved/assembled memory.
`AgentRunner` sends the model exactly:

```text
system_prompt = _build_system_prompt(frame, mode)
              = "You are agent {agent_id} operating in mode {mode}."   (the v0.1 minimal prompt)
messages      = [{"role": "user", "content": frame.raw_input}]
```

There is **no** assembled context, no `assembled_text`, no retrieved memory, no
`character_context` in the model-visible request. (The `_build_system_prompt` docstring
notes a *future* "behavior pack will shape this via … character context" — that is intent,
not current behavior.) So the model sees only its agent/mode identity line plus the raw
user input. **The agent generates blind to its own memory.**

## 3. Why this matters

```text
- Thinking stays ROUTING, not thinking-with-memory. The thinking layer / MemoryPlan
  shapes *retrieval* (which lanes, how much), but the retrieved memory never reaches the
  generation prompt — so the agent never reasons over its memory while generating.
- U1 / audit-owner / Envelope Audit lack an AUDITABLE EVENT. There is no model-visible
  memory inclusion to observe or prove while generation is memory-blind; the inert
  audit-evidence seam observes an empty set every turn.
- Therefore the most-requested capabilities (memory-aware generation; a meaningful
  truthfulness/evidence audit) are gated on this one architectural fact — not on more
  shaping, framing, or characterization.
```

## 4. The decision question (the only thing this frame asks)

```text
DECISION QUESTION:
  May the authoritative AgentRunner generation path consume retrieved/assembled memory —
  i.e., may memory become model-visible to generation at all?

This is a yes / no / not-yet question about WHETHER the fence may be opened. It is NOT a
question about how, where, what format, which memory, or which mechanism — those are out
of scope here and belong to a separately authorized later step (§6, §7).
```

## 5. Historical note (evidence / background only)

Older **"memory-to-prompt automation" (v0.2.x)** artifacts — `character_context`
surfacing, archive-FILTER-A, spirit-return verification, the assembly-audit lane, the
`/retrieve` `assembled_text` surface — concern the **retrieval / assembly surface and its
observability**, and what is *LLM-facing within that assembled surface*. They do **not**
mean the authoritative `AgentRunner` generation path consumes assembled/retrieved memory;
it does not (§2). Any external inference layer that builds its own prompt from `/retrieve`
output is a **separate** path and is not the authoritative generation path this frame asks
about. These artifacts are background context for the decision, **not** evidence that the
fence is already open.

## 6. Allowed decision outcomes (select none here unless recording "decision pending")

```text
- REMAIN HOLD — keep the fence closed; memory stays non-model-visible to generation.
- AUTHORIZE A LATER DESIGN FRAME — permit a future docs-only design question (still no code).
- AUTHORIZE A LATER TESTS-ONLY CHARACTERIZATION — permit a future source/AST characterization.
- AUTHORIZE A LATER IMPLEMENTATION PROPOSAL — permit a future proposal (still gated, reviewed).

These are FUTURE POSSIBILITIES only. This frame selects NONE of them. Recorded state:
DECISION PENDING — the question is filed for Hilmir; no outcome is chosen here.
```

## 7. Required future proof obligations (only if Hilmir later opens the fence)

Stated as obligations a **future, separately authorized** step would have to satisfy —
**not** a design, and not opened here:

```text
- Name the EXACT SOURCE of memory that would become model-visible.
- Name the EXACT GENERATION PATH it would enter.
- Name the EXACT MODEL-VISIBLE BOUNDARY (where/how it becomes visible to the model).
- Prove NO output-control / review / retry / ranking / suppression / style-steering /
  memory-write feedback is created by the change.
- Prove AUDIT remains OBSERVATION-ONLY (inert packet; drives no branch; no audit-as-control).
- Prove NO prompt-request EXPOSURE occurs (request stays runner-local; not on TurnResult /
  ExecutionOutcome / metadata / logs / endpoint / schema / persistence / self).
- Carry forward the caller-owned provenance contract and the PW-1…PW-8 invariants.
```

Each obligation is a *bar for a future proposal*, not a chosen mechanism. This frame
specifies none of the "how."

## 8. Forbidden crossings (hard boundaries of this frame)

```text
- no prompt change
- no model-visible memory injection
- no retrieval-to-generation wiring
- no U1 / audit-owner reopening
- no PrivateGenerationOwner wiring
- no dual-ownership orchestration
- no endpoint / API / schema
- no output-control / review / suppression / retry / ranking / style steering
- no memory write
- no retrieval-authority expansion
- no Gate D / private cognition runtime
- no dream / incubation runtime
- no Envelope Audit runtime
- no database / substrate / carrier / schema / storage / migration
- no Gate B; no R-field; no Probe-v1; no shaping slice
- no code; no tests; no implementation
```

This frame records a decision question only. Nothing above is opened, designed, selected,
or authorized.

## 9. Future gate

```text
- This frame authorizes NO implementation and opens NO lane; it lifts no fence.
- If Hilmir chooses to open the fence (any §6 outcome other than REMAIN HOLD), that choice
  is a SEPARATE explicit decision; the chosen next step (design frame / tests-only / proposal)
  is then itself separately authorized and Codex-reviewed, and must satisfy §7.
- Until Hilmir decides, the state is DECISION PENDING under FORMAL HOLD. No §0 HEAD / Last-closed
  pointer is added until after this frame is committed.
```

## 10. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION ARCHITECTURE DECISION / DOCS-ONLY /
NON-AUTHORIZING / NO LANE OPENED. It asks one question: **may the authoritative
`AgentRunner` generation path consume retrieved/assembled memory — may memory become
model-visible to generation at all?** It records the source-verified root ceiling
(`AgentRunner`'s model-visible request is the minimal `system_prompt` "You are agent … in
mode …" plus the user's raw input — no assembled/retrieved memory), why it matters
(thinking stays routing, and U1/audit-owner/Envelope-Audit lack an auditable event), a
historical note that older "memory-to-prompt automation" concerns the `/retrieve` assembly
surface and observability — **not** the authoritative generation path — the allowed
future decision outcomes (remain HOLD / authorize a later design frame / tests-only
characterization / implementation proposal — **none selected here; state DECISION
PENDING**), and the proof obligations a future opening would have to satisfy (exact memory
source / generation path / model-visible boundary; no output-control/review/retry/ranking/
style/memory-write feedback; audit stays observation-only; no prompt-request exposure;
caller-owned provenance + PW-1…PW-8 preserved). **It is not a prompt-design proposal; it
selects no mechanism, caller, format, source, carrier, schema, endpoint, owner, or runtime,
lifts no fence, opens no lane, and authorizes no code, tests, or implementation.** Any
fence-lift is a separate Hilmir decision under Codex review. Guidance not control; audit
observes authority and does not become authority; nothing rewrites identity / canon / seed
/ soul.
