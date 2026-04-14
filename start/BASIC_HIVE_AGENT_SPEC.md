# Basic Hive Agent — Forge Generator Spec

**Status:** RATIFIED (2026-04-14)
**Scope:** second commit of the split `fix: align forge solo output to ryuki_chat.py` → `feat: add Basic Hive Agent mode to forge`
**Follows:** SOLO_ALIGNMENT_SPEC.md (shipped 2026-04-14), PER_AGENT_MODE_SPEC.md (RATIFIED — DEFER)

---

## 0. Intent

Add a third interaction mode on the hivemind tab that emits a script matching `examples/agent_window.py` semantics — **one agent per terminal, required `--agent`, no `/switch`**. Shared workspace still enables convergence between agents running in separate terminals.

This is the doctrinal pattern from `HIVEMIND_GUIDE.md`: each terminal is a window into the collective, not a switchboard.

---

## 1. Gap table — current state vs Basic Hive Agent target

| # | Area | Today | Target |
|---|------|-------|--------|
| A | UI radio group | 2 cards: `window`, `broadcast` | 3 cards: `window`, `broadcast`, `basic_hive` |
| B | `interactionMode` values | `'window' \| 'broadcast'` | `'window' \| 'broadcast' \| 'basic_hive'` |
| C | Help blurb for new mode | n/a | Short doctrinal blurb explaining "one terminal per agent" |
| D | argparse `--agent` (new mode) | window: `default=sorted(AGENTS.keys())[0]` | basic_hive: `required=True`, no default |
| E | `/switch` slash command | Window: present, clears conversation + swaps agent | basic_hive: absent |
| F | `/agents` slash command | Window: lists roster with `*` marker | basic_hive: absent |
| G | `/help` slash command | Window: re-prints banner | basic_hive: absent |
| H | Banner command list | Window: includes `/switch <id>  /agents  /help` | basic_hive: omit those three |
| I | Docstring "Run:" line | Window: `python …py --agent <id>` | basic_hive: same + note "open one terminal per agent" |
| J | Export markdown step-3 | Window: "use `/agents` to list, `/switch` to change" | basic_hive: "open a new terminal for each agent — no `/switch`" |
| K | Run banner title | `TORMENT Hivemind Window` | basic_hive: `TORMENT Hivemind Window (basic mode)` or similar |
| L | Roster block in prompt | Included (N participants) | Same — roster still printed so agent knows peers exist |
| M | Workspace/agents creation | `setup()` idempotent (409 path) | Unchanged — each terminal runs setup(), 409 protects |
| N | Acceptance checker | Discovers `solo` + `hivemind` sections | Discovers three hivemind sub-modes via fence comments |
| O | jsdom exercise matrix | 4 LLM × 2 hive modes = 8 combos | 4 LLM × 3 hive modes = 12 combos |

---

## 2. Shared-template boundary

**Shared verbatim between `window` and `basic_hive`:**
- `COLLECTIVE_ROSTER` textwrap block (N participants list)
- `AGENTS` dict (pyAgentsDict emitter — including per-agent system_prompt template and output rules)
- `t_post` / `t_get` / `t_query` / `t_ingest` / `t_collective_status` / `t_collective_events` / `t_collective_reingest` / `t_agent_identity` / `t_agent_character_state` / `t_health`
- `setup()` with idempotent 409 handling
- `format_memories` / `format_character_context` / `format_drift_note`
- `sanitize_reply_for_summary` / `build_summary`
- `run_agent_turn` (identical — takes `current_agent_id` + `conversation`)
- Slash commands: `/status /events /reingest /health /identity /debug /memories /clear`
- Convergence poll at end of chat loop turn

**Diverges only at:**
1. `parse_args()` — `required=True`, no default (basic_hive) vs `default=sorted(AGENTS.keys())[0]` (window)
2. `handle_slash_command` — drop `/switch /agents /help` branches in basic_hive
3. `print_banner` — drop the three commands from the cmd list line; append "(basic mode — one terminal per agent)" to title
4. Docstring `Run:` line — add "Run one terminal per agent you want to talk to. No /switch."
5. `chat_loop` — drop the "if new_agent_id != current_agent_id" switch path (dead branch in basic_hive since /switch doesn't exist)

**Broadcast stays untouched.** This is a minimal additive change.

---

## 3. Risks

1. **Multiple terminals racing workspace_create** — setup() already 409-tolerates. Verified in existing window mode. No change needed.
2. **Multiple terminals racing agent_create for the same agent_id** — forbidden by design (one terminal per agent), but 409 path still protects if a user accidentally opens two terminals with the same `--agent`. Fine.
3. **User picks basic_hive with only 1 agent configured** — behaves identically to a solo script but with hivemind policy enabled. Banner should note "collective shines with 2+ agents". No hard error.
4. **Convergence observability is per-terminal** — `/status` and `/events` return the same workspace-scoped view from any terminal. Fine.
5. **User expects /switch, gets "Unknown command"** — mitigate with clear banner showing only the valid commands and the help blurb in UI. Do not print an "did you mean X" hint — agent_window.py doesn't, staying faithful.
6. **Banner clutter** — we're removing three commands, so the cmd list fits cleanly on one or two lines.
7. **Acceptance checker section discovery** — add `// <<< BEGIN basic_hive >>>` / `// <<< END basic_hive >>>` fence comments inside generateHivemind around each `if (interactionMode === ...)` branch so the checker can scope its FORBIDDEN/REQUIRED sets per-mode without relying on fragile line-number slicing.
8. **Export markdown step-3 language drifts if we add more modes later** — make the conditional a simple `if/else if/else` chain keyed on `interactionMode` so future modes plug in cleanly.
9. **`required=True` on --agent breaks existing users running `python hivemind_xxx.py` with no args** — this is a new mode, not a regression to the old one. The window mode keeps default-to-first.
10. **pyAgentsDict is shared — accidental divergence** — enforce via checker REQUIRED patterns that must pass in all three modes: `seed_preamble`, `drift_score`, `recommendations`, `hits`, `COLLECTIVE_ROSTER`.

---

## 4. Acceptance checks (per-mode)

Checker discovers sections via fence comments in the HTML. Each emitted Python script (per LLM × per mode) is scanned with the corresponding FORBIDDEN/REQUIRED set.

### 4a. All hivemind modes (shared)
REQUIRED:
- `COLLECTIVE_ROSTER\s*=\s*textwrap\.dedent`
- `seed_preamble`
- `recommendations`
- `drift_score`
- `drift_summary`
- `\.get\("hits"`
- `format_memories\(`
- `format_character_context\(`
- `format_drift_note\(`
- `build_summary\(`
- `/agent/{agent_id}/identity` (via t_agent_identity)

FORBIDDEN:
- `identity_mode`
- `h\.get\("text"\)`
- `/character/identity` (deprecated endpoint)
- `Stay true to who you are`

### 4b. `window` mode — additional
REQUIRED:
- `if op == "/switch"`
- `if op == "/agents"`
- `default=sorted\(AGENTS\.keys\(\)\)\[0\]`

FORBIDDEN:
- `required=True` on the --agent argparse line (mutually exclusive with the default)

### 4c. `broadcast` mode — additional
REQUIRED:
- `for agent_id, agent in AGENTS\.items\(\):` inside a broadcast loop
- banner text mentioning "Broadcast" or "every agent"

FORBIDDEN:
- `argparse` (broadcast currently has no CLI) — *note: this is the status quo; if we want to change it, a separate ticket*
- `if op == "/switch"`

### 4d. `basic_hive` mode — NEW
REQUIRED:
- `required=True` inside the argparse add_argument for `--agent`
- `COLLECTIVE_ROSTER` (shared)
- `one terminal per agent` or `basic mode` somewhere in banner/docstring
- All 4a REQUIRED patterns

FORBIDDEN:
- `if op == "/switch"`
- `if op == "/agents"`
- `if op == "/help"`
- `default=sorted\(AGENTS\.keys`
- `/switch <agent_id>` in banner command list

---

## 5. Execution order

1. **Ratify this spec** (open questions §6 resolved).
2. **UI**: add third radio card in §02.5 between window and broadcast; add short help blurb div above or below the radio-grid explaining the doctrinal choice (analogous to the solo blurb we just shipped).
3. **Generator**: extend `generateHivemind()` with a third branch `if (interactionMode === 'basic_hive') { ... }`. Wrap all three branches with `// <<< BEGIN {mode} >>>` / `// <<< END {mode} >>>` fence comments so the checker can scope.
4. **Export markdown**: extend the conditional in `exportSetup()` (hivemind branch) to handle basic_hive with its own step-3 language.
5. **Checker**: extend `scripts/check_forge_output.py` to discover the three hivemind sub-modes via fence comments and apply the per-mode REQUIRED/FORBIDDEN sets above.
6. **Validation**:
   - Acceptance checker PASS for solo + all 3 hivemind sub-modes
   - `node --check` on extracted JS
   - jsdom exercise: 4 LLM × 3 hive modes = 12 emitted scripts, all `py_compile` clean
7. **Hand off for commit**: `feat: add Basic Hive Agent mode to forge`

---

## 6. Open questions (need ratification before §5)

| # | Question | Recommendation |
|---|----------|----------------|
| Q1 | Third radio card, or replace the existing "Switch Between Agents" card with a dropdown/toggle? | **Third card** — keep existing modes pristine, minimal diff, easier to revert if needed. |
| Q2 | Should basic_hive accept an optional `--workspace` override like agent_window.py? | **No for this commit** — match window mode's current CLI surface (only `--agent`). Can add in a follow-up if you want it for all modes. |
| Q3 | Radio card label | **"Basic Hive Agent"** (your phrase, stored in memory). Alt: "Single-Agent Window". |
| Q4 | Radio card badge | **No badge** (neither `recommended` nor `experimental`). It's the doctrinal pattern per HIVEMIND_GUIDE.md so calling it experimental would mislead; calling it recommended would undersell `window`. |
| Q5 | UI help blurb wording (suggested) | *"ONE TERMINAL PER AGENT. Basic Hive Agent emits a script that talks to exactly one agent. Open a separate terminal for each agent you want to chat with — they share memory through the collective field, so convergence still happens across terminals. No `/switch` command by design."* |
| Q6 | Section discovery in checker | **Fence comments** (`// <<< BEGIN basic_hive >>>`) over line-number heuristics. Robust against future edits. |
| Q7 | Should we also add a doctrinal blurb in the generated script's docstring header? | **Yes, one line**: `"Run one terminal per agent. Agents share memory via the collective field — no /switch command."` |

---

## 7. Out of scope for this commit

- Changes to `window` or `broadcast` modes
- Optional `--workspace` CLI (Q2)
- Field-validation against a running TORMENT server — separate pass
- Per-agent mode (already RATIFIED — DEFER per PER_AGENT_MODE_SPEC.md)

---

## 8. Ratification record

- [x] Q1 — third radio card, do not disturb existing modes
- [x] Q2 — no --workspace override this commit (match window surface)
- [x] Q3 — label: "Basic Hive Agent"
- [x] Q4 — no badge
- [x] Q5 — UI blurb wording confirmed
- [x] Q6 — fence comments in HTML for checker discovery
- [x] Q7 — one-line docstring blurb in generated script

**Ratified 2026-04-14.** Implementation guardrail from user: *"Basic Hive Agent should feel like the simplest 'one agent, one terminal, shared collective underneath' path — not like a stripped-down expert mode."* Carry this framing into the radio label, blurb, banner title, and docstring.
