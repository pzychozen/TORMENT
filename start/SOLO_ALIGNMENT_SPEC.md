# SOLO_ALIGNMENT_SPEC — align forge solo output to examples/ryuki_chat.py, bundle per-agent mode

**Status: RATIFIED (2026-04-14).**

**Ratified decisions (answers to §6):**
- **Q1 — Per-agent UI:** third radio on the hivemind tab labeled **"Basic Hive Agent"**,
  alongside Switch Between Agents (window) and Broadcast to All Agents. Structure = single
  terminal per agent, shared workspace + roster, `--agent <id>` required at launch. Internally
  shares the same emitted-Python template family as solo; solo = no roster / no `--agent`,
  Basic Hive Agent = roster + required `--agent`.
- **Q2 — UI doctrinal blurb:** YES. Add a short note near the solo `out-prompts` pane
  explaining that the minimal prompt is intentional — seed traits surface through
  `character_context`, memory retrieval, and drift state; duplicating them in the prompt body
  makes memory decorative rather than authoritative. Condensed from ryuki_chat.py lines 117–131.
- **Q3 — Acceptance-check script:** manual, at `scripts/check_forge_output.py`. No pre-commit
  hook while the forge is still changing.
- **Q4 — Commits:** two, executed sequentially. Solo alignment first, validate, commit.
  Basic Hive Agent second, validate, commit.

**Execution order (locked):**
1. Build `scripts/check_forge_output.py` with the guards from §4.
2. Run against current HTML to establish baseline (expected: window/broadcast pass, solo fails).
3. Execute solo alignment edits in `generateSolo()` + `out-prompts` + `out-loop-curl` +
   `out-loop-python` + `out-response` + UI doctrinal blurb.
4. Re-run checker. Solo must pass. Window/broadcast must remain passing.
5. Hand off for first commit: `fix: align forge solo output to ryuki_chat.py`.
6. Then, as a SEPARATE pass: Basic Hive Agent mode (§2 shared-template boundary, third hivemind
   radio). Out of scope for this commit.

**Target file:** `start/torment_character_creator.html`, `generateSolo()` at line 2183,
output panes `out-prompts`, `out-loop-curl`, `out-loop-python`, `out-response`.

**Reference (ground truth):** `examples/ryuki_chat.py`.
**Secondary reference (for per-agent branch):** `examples/agent_window.py`.

**Scope:** alignment of solo-tab output + bundling of per-agent mode into the same template
family. NOT touching hivemind window/broadcast — those were just field-patched and stay
byte-stable.

---

## 1. Gap table — current emits vs. ryuki_chat.py

Row = one divergence. `action` = what to do. Severity = `BUG` (wrong in current API),
`DOCTRINE` (violates the TORMENT design principle in ryuki_chat.py's comment block 117–131),
`UX` (stylistic / usability), `DOC` (reference pane misleads users).

| # | Area | Current (forge solo) | ryuki_chat.py | Severity | Action |
|---|---|---|---|---|---|
| A | System prompt template | `You are {name}.\n\n{character_context}\n\n{firstLine}.\nSpeak as {name}. Stay true to who you are...` (line 2500) plus seed-first-sentence duplicated at 2403 | Minimal: `You are {agent_name}. {character_context} {memory_context} {drift_note}` (134–142) | DOCTRINE | ALIGN: drop firstLine + "Stay true" scaffolding. Use the three-slot minimal template. |
| B | Memory retrieval key | `result.get("results", [])` only (2544) | `query_result.get("hits", query_result.get("results", []))` (539) | **BUG** | ALIGN: try `hits` first, fall back to `results`. Without this, generated script never sees memories. |
| C | Memory field reads | `h.get('text', h.get('summary', ''))` — prefers non-existent `text` key (2546) | `hit.get("summary", "")` + `final_score/score` fallback + `character_tier` + `provenance_type` (297–309) | **BUG** | ALIGN: read `summary` primary, add score/tier/provenance tags. |
| D | Helper structure | Single monolithic `format_context(result)` (2534–2548) handling char_ctx + memories together | Three separate helpers: `format_memories`, `format_character_context`, `format_drift_note` | UX | SPLIT into three helpers (matches hivemind block, enables per-agent reuse). |
| E | Drift note | Absent — drift never injected into prompt | `format_drift_note(char_ctx)` with `abs(ds) < 0.1` suppression (330–339) | DOCTRINE | ADD: third prompt slot surfaces drift when relevant. |
| F | Prompt slot wiring | `SYSTEM_PROMPT.replace("{character_context}", context)` (2444, 2457, 2472, 2486) | `SYSTEM_PROMPT_TEMPLATE.format(agent_name=..., character_context=..., memory_context=..., drift_note=...)` | DOCTRINE | ALIGN: use `.format()` with all three slots. |
| G | Ingest summary | `f"User: {user_input[:120]}. {name} responded about the topic."` — never references actual reply (2564) | `build_summary(user_msg, reply)` returning `f"Zen said: {u}\nRyuki responded: {r}"` (367–381) | **BUG** | ALIGN: build summary from both sides. Current memory is unsearchable — every turn stores the same nothing-string. |
| H | Slash commands | None | `/status /identity /debug /memories <query> /clear` (483–524) | UX | ADD: port the five commands, match the split-and-dispatch style. |
| I | Banner | `print(f"\\n=== {name} is ready. Type 'quit' to exit. ===\\n")` (2554) | Rich banner with workspace/agent/model/top_k + command list + `/clear` note (438–455) | UX | ALIGN: richer banner once slash commands exist. |
| J | 409 handling | `if r.status_code == 200: print("...ready.")` — silent on conflict (2514–2521) | `try/except RuntimeError` checking `" 409 "`, prints "already exists" (408–421) | UX | LIGHT-POLISH: optional. Current is correct, just quieter. |
| K | HTTP client | Inline `requests.post/get` | `TormentClient` class with session + timeout + error wrapping (171–238) | UX | **DECIDE** — see §3 risk #8. Recommendation: keep inline for "paste-and-run" ethos. |
| L | LLM client | Inline anthropic/openai/ollama/other (2439–2492) | `ClaudeClient` with SDK→HTTP fallback (245–290) | UX | KEEP inline: forge supports four LLMs, ryuki_chat.py is Claude-only. |
| M | `out-response` reference | Documents `results` (not `hits`), shows `text` key as memory field (2571–2604) | n/a (not a forge thing, but truth is `hits`/`summary`) | DOC | ALIGN: update to real response shape so users don't learn wrong keys. |
| N | `out-loop-curl` comment | "Response includes character_context... Also includes results (memory hits) and identity_state" (2420) | n/a | DOC | ALIGN: `results` → `hits`. |
| O | `firstLine` derivation | `seed.split(/[.!?]/)[0].trim()` at line 2401, injected twice (2403, 2500) | Not done | DOCTRINE | REMOVE entirely. Exact anti-pattern flagged by ryuki_chat.py comment 117–131. |
| P | Identity endpoint | `/agent/{agentId}/identity?workspace_id={wsId}` (2434) | `/agent/{agent_id}/identity` (222) | — | KEEP: already correct. |

**Bug count in current solo generator: 3 real (B, C, G) + 1 doctrinal (O) + 2 documentation
errors (M, N). B alone silently breaks retrieval.**

---

## 2. Shared-template boundary — solo + per-agent from one family

Goal: one emitted-Python template shape that produces both:
- **solo** (no collective, no roster, `ryuki_chat.py` equivalent)
- **per-agent-in-collective** (shared workspace, roster-aware prompt, single terminal, single
  `--agent <id>`)

### Identical across both
- TORMENT endpoint URLs and payload shapes
- `format_memories`, `format_character_context`, `format_drift_note` — byte-identical
- `build_summary(user_msg, reply)` idiom, with agent-name substitution
- Claude/OpenAI/Ollama/Other client branch (forge multi-LLM, unchanged)
- Workspace + agent `create` with 409 tolerance
- Chat loop: input → query → prompt → LLM → display → ingest
- Slash-command subset: `/status /identity /debug /memories <query> /clear`
- Env emission (SRG, character, compression, spine, etc.) — same server, same flags

### Divergent (small, clean)
- **CLI:** solo no args; per-agent requires `--agent <id>` with valid-id listing on bad input.
- **Agent config:** solo has single `SEED` + `AGENT_ID`; per-agent has full `AGENTS` dict +
  `COLLECTIVE_ROSTER`, `current_agent_id` from `--agent`.
- **System prompt:** solo uses 3-slot minimal; per-agent uses 4-slot (`{collective_roster}`
  added so the agent knows its peers).
- **Slash commands:** per-agent adds `/agents` (list roster, mark self). No `/switch` either
  way.
- **Setup:** per-agent registers only its own agent; peers self-register from their own
  terminals.
- **Banner:** per-agent shows "participant in <team>" + roster lines.

### Verdict
Divergence is small and confined to a handful of conditionals at generation time. **One
template family works.** Branch point: a single boolean `isCollectiveParticipant` in the
generator, driven by a UI toggle (or by whether the user came in via the solo tab vs. hivemind
tab with `per-agent` radio selected).

Helpers are duplicated across output scripts by choice (forge ethos: one file, paste and run).
No shared-module emission.

---

## 3. Risk list + mitigations

1. **LLM coverage symmetry** — solo supports claude/openai/ollama/other; agent_window.py is
   Claude-only. Per-agent inherits forge's four-way branch. Mitigation: acceptance check that
   all four branches compile for per-agent too.

2. **Reference panes (`out-response`, `out-loop-curl`) teach wrong keys** — users copy these as
   learning material. Fixing script without fixing reference panes leaves doc drift.
   Mitigation: rows M + N in gap table are in-scope for this pass, not a later one.

3. **Minimal-prompt shock** — users may perceive the post-alignment prompt as "too empty" once
   firstLine + "Stay true" scaffolding is gone. Mitigation: port a condensed version of
   ryuki_chat.py comment block 117–131 into the forge UI near the `out-prompts` pane, explaining
   that seed traits surface through `{character_context}` and hardcoding them defeats the memory
   system.

4. **`results` vs `hits` migration signal** — add inline comment near the fallback so future
   readers know `results` is legacy compatibility.

5. **Summary regression on existing workspaces** — current ingest is essentially noise. Fixing
   the script doesn't retroactively improve old memories. Mitigation: flag in release notes /
   user message that retrieval quality improves on fresh workspaces or after new turns
   accumulate.

6. **Voice pipeline (`out-voice`)** — solo-only today. Recommendation: **out of scope** for this
   pass. If per-agent wants voice later, that's a separate spec.

7. **Env emission reuse** — per-agent and solo share identical env emission. No risk if we treat
   it as shared code path in the generator.

8. **Helper duplication across four emitted scripts** (solo, per-agent, window, broadcast) — we
   accept this. Extracting a `torment_helpers.py` module would break "paste-and-run". Acceptance
   greps (below) keep the four copies in sync.

9. **Two-site firstLine edit** — lines 2401 (derivation), 2403 (out-prompts), 2500 (python
   template). Remove all three in one edit to avoid partial removal.

10. **Slash-command parser style** — use `parts = lower.split(None, 1); op = parts[0]; arg = parts[1] if len(parts) > 1 else ""` so solo and per-agent share the same handler shape. Matches agent_window.py and the window-mode block we just patched.

---

## 4. Acceptance checks (blocking — fail the pass if any trip)

Run against the emitted Python for BOTH solo and per-agent output modes:

1. `node --check` on the extracted forge `<script>` block: OK.
2. `py_compile` on each emitted script: OK.
3. **Grep guards — must NOT match:**
   - `h.get("text")` / `hit.get("text"` — wrong memory key
   - `identity_mode` / `identity_state"` in a format helper — wrong char-ctx key
   - `char_ctx.get("drift")` / `char.get("drift")` — wrong drift key (must be `drift_score` / `drift_summary`)
   - `/character/identity` — wrong identity path
   - `firstLine` / `Stay true to who you are` / `Speak as .* Stay true` — doctrinal violation
   - `responded about the topic` — lazy ingest summary
4. **Grep guards — MUST match:**
   - `h.get("summary")` appears in `format_memories`
   - `seed_preamble` and `recommendations` appear in `format_character_context`
   - `drift_score` and `drift_summary` appear in `format_drift_note`
   - `query_result.get("hits"` appears before any `.get("results"` in retrieval path
   - `SYSTEM_PROMPT_TEMPLATE` has all three (solo) or four (per-agent) slots
5. Per-agent only: running emitted script without `--agent` exits non-zero with a message
   listing valid agent ids.
6. Per-agent only: `/switch` is absent from both the dispatcher and `/help` output.

---

## 5. Execution order (when ratified)

1. **Prep** — write acceptance-check script (`scripts/check_forge_output.py` or similar) first,
   so every subsequent edit can be validated.
2. **Solo alignment first (rows A, B, C, D, E, F, G, H, I, M, N, O)** — one atomic edit block to
   `generateSolo()` plus the output panes. No per-agent yet.
3. **Validate** — run acceptance checks, hand-test generated script against a local TORMENT.
4. **Per-agent second** — add the UI toggle + the conditional branches in the shared generator.
   New hivemind radio option OR a "participant mode" checkbox on the solo tab, TBD during
   ratification.
5. **Validate per-agent** — acceptance checks + hand-test.
6. **Commits** — two: `fix: align forge solo output to ryuki_chat.py` and `feat: per-agent
   single-terminal generator mode`.

---

## 6. Open questions for ratification

- **Q1:** UI placement of per-agent — third radio on the hivemind tab, or a "participant mode"
  checkbox on the solo tab? The former matches the original PER_AGENT_MODE_SPEC framing. The
  latter matches the "per-agent is solo-shaped" conclusion we reached in ratification. My
  recommendation: **solo tab checkbox**, because it follows the structural truth.
- **Q2:** Port the ryuki_chat.py comment block 117–131 into the forge UI (see risk #3)? Yes/no?
- **Q3:** Acceptance-check script location — `scripts/` folder or inline in CI/pre-commit? Lower
  priority; can decide during execution.
- **Q4:** Commit split — two commits (solo, then per-agent) or one? Two is cleaner for bisect.

Do not begin any edit until all four are answered and this status block flips to RATIFIED.
