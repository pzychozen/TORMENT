# TORMENT — Non-Spine LLM Character Provider Handoff v0.1

## Status

**Docs-only fresh-chat handoff. NON-AUTHORIZING. No code, no tests, no runtime change.**
The non-Spine character-provider arc is **CLOSED for this phase** and the lane is on
**HOLD**. This document is the orientation for whoever opens the lane next; read it together
with §0 of `docs/PROJECT_ORIENTATION_MAP.md` (which §0 wins on conflict).

---

## Past — the closed arc

What was built for the separate, off-Spine LLM runtime, in order (all pushed; hashes for
reference only):

- `5f00429` feat/runtime — **gated Anthropic non-Spine provider adapter** landed
  (`AnthropicNonSpineLLMProviderAdapter`): env-gated, fail-closed, non-default,
  operator-constructed only; SDK imported lazily **after** gate / key / model / timeout
  validation; never instantiated by the default runtime or the fake completion adapter; no
  real provider call in tests.
- `8e5e801` test/runtime — **manual Anthropic non-Spine provider harness** landed (operator
  CLI; refuses the real path under pytest; fake env + fake/spy SDK only in tests).
- `0ba41cb` docs/runtime — **sanitized receipt** for the first manual Anthropic smoke.
- `3bc0c1c` docs/project — pointer alignment for the first smoke receipt.
- `92e9554` test/runtime — **manual character-shaped non-Spine operator harness** landed.
  This is the **meaningful harness edge** for the character phase.
- `77a13dd` docs/project — §0 closure for the manual character harness.
- `5f7a00a` docs/runtime — **sanitized receipt** for the manual character-shaped
  real-provider smoke.
- `5639a97` docs/project — pointer cleanup for the character smoke receipt
  (**pointer-only — do not pointer-chase it**).

**"Character-shaped" means a manual primitive harness only.** The operator supplies
primitive fields (`character_id` / `character_name` / `seed_text` / `user_input` / optional
`memory_context_text` / optional `extra_messages`) and a safe seam composes a plain
`system_text`. It is **NOT production character integration** — it imports no production
character / store / fabric / assembly / orchestrator / runner surface.

---

## Present — current state

What exists right now:

- A **separate non-Spine LLM runtime** exists, dormant and off the live deterministic Spine
  path.
- A **real Anthropic adapter** exists but is **gated, fail-closed, non-default,
  operator-constructed only**; **no automatic provider call**.
- A **manual Anthropic provider harness** exists (CLI refuses under pytest).
- A **manual character-shaped harness** exists (same refusal posture).

Evidence on record (sanitized):

- **One intentional real-provider smoke** was run through the character-shaped harness and
  returned **non-empty terminal output** (observed in the terminal only).
- **Not recorded anywhere:** provider response text, prompt transcript, API key, payload,
  request id, trace, headers, stdout/stderr; **no output / log / transcript file** was
  created.
- **No app / server / MCP endpoint** was used; **no live wiring**; **no memory write**; **no
  production character integration**; **no automatic provider call**.
- **Tests after cleanup: 94 OK** (the six-module focused suite below).
- **`git status -sb`: clean / aligned after push.** (This says the working tree is clean and
  the branch matches origin — it does **not** claim any runtime integration.)

Receipts / pointers for detail: `docs/TORMENT_NON_SPINE_LLM_RUNTIME_ANTHROPIC_OPERATOR_SMOKE_RECEIPT_v0.1.md`
(first Anthropic smoke) and `docs/TORMENT_NON_SPINE_LLM_CHARACTER_OPERATOR_ANTHROPIC_SMOKE_RECEIPT_v0.1.md`
(character smoke). §0 names `5f7a00a` as the docs receipt edge and `92e9554` as the
meaningful harness edge.

Focused validation command (operator runs it in the already-activated CMD; see lessons):

```
python -m unittest tests.test_non_spine_llm_character_operator_harness tests.test_non_spine_llm_anthropic_provider_harness tests.test_non_spine_llm_real_provider_adapter tests.test_non_spine_llm_runtime_skeleton tests.test_non_spine_llm_callable_adapter_harness tests.test_spine_cognition_memory_context_characterization_lock
```

→ **94 tests OK.**

---

## HOLD boundaries (preserved, explicit)

Nothing here is authorized by this handoff. **Still HOLD:** production code; live endpoint /
MCP / API / schema; app / server / character production integration; retrieval / assembly;
memory writes; persistence / logging / transcripts; model-output-to-memory feedback;
identity / canon rewrite; database / substrate; dream / private-cognition runtime;
AgentRunner / Terrain B; output-control paths; hidden finalizer / refusal / identity
rewrite; and automatic provider calls. The default runtime path stays **fake / no-provider**.

---

## Future direction

- The manual path now has **enough evidence for this phase**. Another harness or a
  source-only integration review would mostly add **drift pressure toward live wiring**
  without adding much safety — so the recommended move is to **HOLD here** and continue in a
  fresh chat.
- **Option 4 — returning to the broader memory-to-prompt / live-caller architecture — is
  directionally admissible after this handoff**, but it must begin as a **SEPARATE
  architecture lane, not another provider-integration step.** It is a Hilmir + Codex
  architecture decision, not code.
- Any next provider-lane move (a further real smoke, live app / MCP wiring, production
  character integration) remains a **separate, separately-gated** decision under Codex
  review.

---

## Process lessons (carry forward)

- **Do not give vague placeholder commands for model / env setup.** If local runtime facts
  matter, **ask or inspect first.**
- Hilmir runs in an **already-activated CMD** (`conda activate torment`). Use plain
  `python -m unittest ...`; **do not default to `conda run -n torment ...`.**
- The harness **does not read `CLAUDE_MODEL`.**
- The harness **does not auto-load `.env`.**
- The correct model env for the smoke was **`TORMENT_NON_SPINE_ANTHROPIC_MODEL=claude-sonnet-4-6`**
  (with gate `TORMENT_NON_SPINE_LLM_REAL_PROVIDER=1` and
  `TORMENT_NON_SPINE_PROVIDER_TIMEOUT_SECONDS=30`).
- **Manual API key entry happened locally** for the smoke; **never record or characterize
  the key.**

---

## Fresh-chat quick start

1. Read **§0** of `docs/PROJECT_ORIENTATION_MAP.md` first.
2. This lane is **HOLD**. Do not reopen provider integration without a fresh gate.
3. If the operator wants forward movement, frame it as a **new memory-to-prompt /
   live-caller architecture lane (option 4)** — separate from provider plumbing — and bring
   in Codex before any code.
