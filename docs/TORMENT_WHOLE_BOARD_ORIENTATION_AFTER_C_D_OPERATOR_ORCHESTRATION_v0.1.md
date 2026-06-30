# TORMENT — Whole-Board Orientation After C-D Operator Orchestration v0.1

## Status / purpose

**Docs-only / source+docs orientation scan / NON-AUTHORIZING / no code / no tests / no
guards / no provider call / no production change.** Codex decision: **PASS whole-board
source/docs orientation scan.** This artifact records the resting state of the board after
the manual **C-D operator-orchestration** phase. It **selects nothing**, **opens no
architecture gate**, **proposes no production integration**, **adds no tests or guards**, and
**calls no provider / runs no smoke.** It names possible next fronts without choosing one.

Source-grounded at HEAD `345bab1`. The next actual project fork must be chosen **separately,
after this whole-board review** — this scan does not choose it.

## 1. C-D operator orchestration — CLOSED / HOLD

The C-D ("operator orchestration") phase of the memory-to-prompt / live-caller lane is
**closed and at rest**. Its arc (all manual/docs-only, no production wiring):

- `1315d30` review live-caller topology → `5a7117c` frame the architecture question →
  `86ff6d6` evaluate direction (C-D selected as a future, separately-gated paper candidate)
  → `675b460` propose the bounded shape → `f4434c6` **pre-implementation guard** (tests/AST
  characterization) → `b7a8a0a` **manual harness** (`tests/manual/`) → `a14bec6` close pointer
  → `02f2b17` **fake-mode smoke receipt** → `345bab1` **real-provider smoke receipt**.

Resting state, source-verified at HEAD:

- The only landed surface is the **manual, operator-run harness**
  `tests/manual/memory_to_prompt_c_d_operator_orchestration_harness.py` (+ its tests + the
  flipped pre-implementation guard). It lives **outside the production package**.
- The candidate **production orchestrator module
  `torment_service/memory_to_prompt_operator_orchestrator.py` is ABSENT** (confirmed at
  HEAD), and its four production sentinel names remain forbidden/absent (locked by the
  guard).
- The harness **default path is fake / no-provider** (`is_fake=True`,
  `provider_called=False`); the optional real Anthropic path **reuses only the existing
  env-gated adapter, requires the explicit `--real-anthropic` flag + the existing env gate,
  and refuses under pytest**. There is **no automatic provider call**.

### Smokes are evidence only — NOT momentum toward production

The fake-mode (`02f2b17`) and real-provider (`345bab1`) smoke receipts are **sanitized
evidence receipts**, not transcripts/output artifacts and not authorizations. Together they
establish only that the manual C-D path runs end-to-end and can return non-empty text under
explicit operator setup. They **do not** imply, request, or pre-authorize live wiring,
production integration, provider expansion, memory writes, or any further real smoke. The
real-smoke receipt explicitly authorizes none of those. **No production momentum is implied
by the existence of these receipts.**

## 2. Live-board inventory (from source/docs)

### 2.1 Memory-to-prompt / live-caller lane (parent of C-D)

A long arc of **docs-only, non-authorizing** decision/evaluation/proposal frames. Live
production wiring is **NOT authorized**. Source facts at HEAD:

- The live production cognition path is the **deterministic Spine / `cognition.pipeline`**
  (`route → build_memory_context → roles → reintegrate`), with **no LLM/model/prompt
  boundary** (test-locked by `tests/test_spine_cognition_memory_context_characterization_lock.py`,
  `f480b69`). `memory_context` is same-turn, advisory, internal, non-model-visible.
- The dormant `memory_context_orchestrator` (`b3b5647`) + the runner-local
  `AgentRunner.run_turn(..., memory_context_text=...)` seam exist but are **called nowhere in
  production** (DORMANT / test-called).
- `/retrieve` + `assemble_context` / `AssembledContext` remain a **read-only context
  source**, excluded from the live flow.
- The separate, dormant **non-Spine LLM runtime** is the on-paper Option-C home for any future
  LLM-bearing generation (see 2.7).

**HOLD:** any live caller / production wiring / endpoint / `/agent/query` or `/retrieve`
change / model boundary on the Spine path.

### 2.2 Gate A (containment wall / audit-evidence / owners)

- **Containment wall (Document A):** enforcement-path is **unselected / HOLD**. Resting-state
  non-reachability and no-tag-dependence are characterized tests-only
  (`test_gate_a_containment_wall_nonreachability_characterization.py`,
  `..._no_tag_dependence...`); an enforcement-path **proposal** is docs-only/non-authorizing
  (`b84191b`). No wall mechanics exist.
- **Selected-items runner bridge** (`392caa2`): the **one approved private,
  observation-only** caller bridge — passes selected item dicts from one `AssembledContext`
  into `run_turn(..., audit_admitted_context_items=...)`; reads nothing back; called nowhere
  else. Topology doctrine = "exactly one approved private bridge; all other paths forbidden."
- **Private generation owner** (`2b507d8`): implemented as a **private, test-called, unwired**
  module; not a live owner; observation packets drive no control.
- **U1 / audit-owner:** **HOLD** (Option C parked); no live caller passes audit items in
  production beyond the single dead-end bridge.
- **Gate A Tier-2** needs a **carrier/substrate** (depends on 2.5).

### 2.3 Gate B (writer-authority / R-field / Probe-v1)

**Fenced / HOLD.** Gate B writer-authority, the R-field, and Probe-v1 remain unopened. (R-field
was rejected pending a prior cross-agent leak fix; recorded elsewhere.) No movement.

### 2.4 Gate D / Terrain B / AgentRunner

**NO-OPEN / HOLD / disjoint.** Source-verified at HEAD: `app.py` and `spine.py` reference
**`AgentRunner` zero times**; the live cognition path is the Spine, architecturally
**disjoint** from the `AgentRunner.run_turn` runtime that any "Terrain B" caller would drive;
`fabric.drift_reflex_callback` is a **dormant, never-set** hook; the
`memory_context_orchestrator` is called nowhere. The Terrain B **live-trigger** decision is
**Option D — HOLD (no live trigger selected)**. Gate D / Envelope Audit / private-cognition /
dream runtime remain **NO-OPEN** and are **blocked behind the Gate A containment-wall
enforcement path** (the roadmap dependency: A-wall → P4 gates → Document B interior).

### 2.5 Substrate / database

**Deferred / fenced.** The currently followed roadmap is the **substrate-independent**
ephemeral Layer-1 / MemoryPlan-shaping lane; **database/substrate (Stage B) is deferred**. A
carrier/substrate is the prerequisite for Gate A Tier-2 and for any durable Document B
interior. No substrate work is opened.

### 2.6 Private cognition / dream runtime

**NO-OPEN / HOLD.** No live Document B / private-cognition / dream / incubation entrypoint
exists in source (characterized at `2732f32`). It is gated behind the Gate A wall enforcement
path and a carrier/substrate; the operator's interest in a temporally-extended private
reflection layer is noted but **not opened here**.

### 2.7 Model-audit / provider lanes

- **Model-API audit lane:** prompt-inclusion observation helper, the private generation
  owner, and the selected-items bridge are all **observation-only / non-control / unwired**;
  audit packets drive no prompt / review / output / ingest / retrieval / write branch.
- **Non-Spine provider lane:** the dormant **non-Spine LLM runtime** (`a2d271e` and the
  provider/completion/callable/gated-Anthropic adapter slices) is the on-paper **Option C**
  home for LLM generation kept **off** the deterministic Spine. The real Anthropic adapter is
  **gated, lazy-import, fail-closed, operator-constructed only, never the default, never
  live-wired**; a real provider remains **admissible only as a future, separately-gated
  step** (readiness review). The **model-boundary decision (`3e4bc2d`) is Option D — HOLD**:
  whether/where live LLM generation should exist is an operator product/runtime fork, not
  source-derivable. The **C-D manual harness is the manual surface in this lane** (see §1).

## 3. Possible next fronts (named — NONE selected)

Recorded as options for a separate fork decision; this scan selects, opens, and authorizes
**none** of them:

1. **Memory-to-prompt for the deterministic Spine path / the live-LLM-generation product
   fork** — whether live generation should exist at all and, if so, as a separate non-Spine
   runtime (Option C) or a model boundary on the Spine (rejected-leaning Option B). This is
   the `3e4bc2d` HOLD fork and the historical "root memory-blind ceiling" question.
2. **Substrate / carrier / database (Stage B)** — unblocks Gate A Tier-2 and a durable
   Document B interior.
3. **Gate A containment-wall enforcement path** — the dependency that gates Gate D /
   private-cognition / dream.
4. **Model-API / Envelope-Audit live-owner wiring** — gated behind the Gate A wall.
5. **A source-only integration review of the non-Spine / C-D surface** — would itself be a
   **separate** docs-only gate; **not opened here**.
6. **Remain HOLD.**

No front is recommended over another here; the choice is the operator's, after this review.

## 4. HOLD surfaces preserved (explicit)

Everything below remains **HOLD unless separately opened later**: production code;
endpoint / MCP / API / schema; app/server/character integration; retrieval/assembly behavior
changes; AgentRunner / Terrain B; provider expansion; memory writes; persistence / logging /
transcripts / output files; model-output-to-memory feedback; identity / canon rewrite;
output-control; hidden finalizer / refusal / identity rewrite; automatic provider calls;
database / substrate; dream / private-cognition runtime.

## 5. Stale / conflicting map facts found

- **§0 HEAD line was stale (now corrected in this same slice):** it read `5f7a00a`
  (character non-Spine smoke receipt) while the actual pushed HEAD is `345bab1`
  (`docs(runtime): record operator orchestration real smoke`) — roughly ten commits behind
  (the entire C-D arc `1315d30 → 345bab1`). Corrected to `345bab1`.
- **Older §0 "C-D PRE-IMPLEMENTATION GUARD" bullet reads stale on its face:** it still says
  "no candidate module/harness exists" and lists
  `memory_to_prompt_c_d_operator_orchestration_harness` among "forbidden/absent sentinels."
  That is **superseded** by the three newer C-D §0 bullets (manual harness landed; guard
  flipped to "manual harness EXISTS, production wiring ABSENT"; the harness name was removed
  from the absent-sentinel set). Per §0 doctrine the most-recent bullet wins; the older bullet
  is **left in place as historical record** (not chased in this slice).

## 6. Validation

Reconstructed-HEAD run of the eight named modules:

```
python -m unittest tests.test_memory_to_prompt_c_d_operator_orchestration_harness \
  tests.test_memory_to_prompt_c_d_operator_orchestration_preimplementation_guard \
  tests.test_non_spine_llm_character_operator_harness \
  tests.test_non_spine_llm_anthropic_provider_harness \
  tests.test_non_spine_llm_real_provider_adapter \
  tests.test_non_spine_llm_runtime_skeleton \
  tests.test_non_spine_llm_callable_adapter_harness \
  tests.test_spine_cognition_memory_context_characterization_lock
```

→ **Ran 123 tests, OK.** Source spot-checks at HEAD: production orchestrator module
**absent**; `AgentRunner` referenced **0×** in `app.py` / `spine.py`; **no** production module
imports `non_spine_llm_runtime`.

## 7. What this is NOT

No new architecture gate. No implementation selected or proposed. No production integration.
No tests or guards added. No provider called and no smoke run. A docs-only resting-state map,
plus a §0 HEAD correction and a compact pointer.
