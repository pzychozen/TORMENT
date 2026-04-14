# PER_AGENT_MODE_SPEC — third generator output: "per-agent single-terminal"

**Status: RATIFIED — DEFER (2026-04-14).**

**Decision:** defer per-agent mode until the same pass as the solo-generator alignment to
`examples/ryuki_chat.py`.

**Why:**
1. Window/broadcast has just been corrected (four field-shape bugs patched) and must be
   field-validated before the generator surface area is expanded again.
2. Per-agent is structurally closer to **solo** than to hivemind window/broadcast — it is a solo
   terminal that happens to share a workspace and know the roster. Building it now would fork a
   third near-duplicate hivemind block; building it with the solo alignment lets both outputs
   come from one shared template family.
3. Deferring means per-agent inherits the already-validated response and identity shapes
   (`summary`, `final_score`, `seed_preamble`, `drift_score`, `/agent/{id}/identity`) instead of
   risking re-introduction of the same key mismatches.

**Doctrine locked in:** per-agent terminals share a workspace and collective roster but do NOT
IPC with each other. The operator composes the collective by opening multiple terminals. The
script itself never cross-talks.

**Constraint locked in:** drift-budget, rate-limit, and coupling constants remain kernel-side
(safety constants), never surfaced as UI sliders or per-script CLI flags in this mode.

**Acceptance locked in:** the emitted Python must include grep-style checks against the four
fixed bugs (`h.get("text")`, `identity_mode`, `char_ctx.get("drift")`, `/character/identity`)
so they cannot silently reappear.

**Ship order:**
1. **Now:** window mode as the recommended collective path, broadcast as experimental.
2. **Validate next:** real usage — fixed field shapes, slash-command flow, generated summary
   text, manual reingest workflow.
3. **Then build:** per-agent mode together with solo → `ryuki_chat.py` alignment, one shared
   template family, no third hivemind-specific fork.

Do not re-open this decision without a concrete operational reason.

---

**File to edit:** `start/torment_character_creator.html`

---

## 1. Why this mode exists

The hivemind generator (window/broadcast) launches N agents from ONE process. That is doctrine,
but it assumes the operator wants them co-located. Some users prefer the legacy workflow:

- one terminal per agent
- each terminal talks to ONE agent in the same workspace
- memory/drift/collective coupling still works, because they all share `workspace_id` and roster seeds
- the operator composes the "hivemind" themselves by tiling terminals

This mode is the bridge between `examples/ryuki_chat.py` (true solo, no collective) and
`examples/agent_window.py` (N agents, one window, /switch). It is the "solo, but knows it's part
of a collective" shape.

## 2. User-facing additions in the Forge UI

Add a THIRD radio in the Hivemind section beside the existing `window` / `broadcast` pair:

- `per-agent` — "Single-agent terminal (run N copies, one per agent)"

Keep the existing hivemind character list, seeds, slider values, `COLLECTIVE_ROSTER`, and workspace
binding. The only UI delta when `per-agent` is selected:

- show a short inline note: "Generator will emit ONE script. Copy it N times and set
  `--agent <id>` per terminal. All copies share the same workspace."
- the Drift Budget and Rate Limit sliders remain as they are (doctrine: kernel safety constants,
  not per-session knobs — do NOT surface them differently here).

## 3. Generated script shape

Emit exactly ONE Python file, structured like `ryuki_chat.py` but with hivemind awareness:

### Top of file
```python
WORKSPACE_ID  = "<forge>"
BASE_URL      = "http://127.0.0.1:8765"
MODEL         = "<forge-selected>"
TOP_K         = 6

# Full collective, so this agent's prompt can reference its peers
AGENTS = {
    "<agent_id>": {
        "name": "<display_name>",
        "seed": { ... doctrinal seed fields ... },
        "system_prompt": "<per-agent template, accepts {collective_roster}, "
                         "{character_context}, {memory_context}, {drift_note}>",
    },
    # ...every agent in the collective, not just this terminal's agent
}

COLLECTIVE_ROSTER = "<multi-line textblock naming each agent + one-line bio>"
```

### CLI
```
python per_agent.py --agent <agent_id>
```
- `--agent` is REQUIRED. No default. Script exits with a clear error listing valid ids if missing
  or wrong.
- No `--mode` flag. This script is single-agent by construction.

### Startup
On first run per agent, register/seed that agent only (409 is fine, same `try/except` idiom as
`agent_window.py`). Do NOT re-register the others — they'll be seeded by their own terminals.
Rationale: idempotent registration is cheap; peers self-register when their operators launch them.

### Turn loop
Same as `agent_window.py`'s `run_agent_turn`, but:
- `current_agent_id` is fixed from `--agent` at startup
- no `/switch` command (there is no other agent in this process)
- `/agents` prints the full roster with a marker on `current_agent_id` so the operator can see
  who the peers are and which terminals they should be running in

### Slash commands (subset of window mode)
Keep: `/status /events /reingest <id> /health /identity /memories <query> /clear /debug /agents /help /quit`
Remove: `/switch` (meaningless here)

### Field shapes — MUST match what we just fixed
All three helpers read the TORMENT response shape exactly as in the window/broadcast blocks after
the recent patch:

- `format_memories` → `h.get("summary")`, `h.get("final_score", h.get("score", 0.0))`,
  `character_tier`, `provenance_type`
- `format_character_context` → `seed_preamble`, `recommendations`
- `format_drift_note` → `drift_score`, `drift_summary`, suppress when `abs(ds) < 0.1` and no summary
- identity endpoint → `/agent/{agent_id}/identity?workspace_id={WS}` (NOT `/character/identity`)

Do NOT re-derive these. Copy the helpers verbatim from the window-mode block.

## 4. Doctrine guardrails (do not violate)

- **No broadcast-from-solo**: this terminal never queries or prompts other agents. It only knows
  about them via `COLLECTIVE_ROSTER` text + `AGENTS` seeds for system-prompt formatting.
- **Coupling stays `read_only` at strength 0.25**: these are kernel safety constants. Do not expose
  as per-script CLI flags.
- **Drift Budget / Rate Limit**: same. Read from kernel defaults; do not surface.
- **Memory ingest summary** must be the sanitized reply summary, same idiom as window mode's
  `build_summary(agent_name, user_msg, reply)`.
- **Provenance**: default `provenance_type="participant"`, `provenance_confidence=0.85` on ingest,
  identical to window mode.

## 5. What NOT to build

- No process supervisor / launcher script for the N terminals. The operator launches them.
- No inter-process signalling. The workspace + TORMENT is the shared medium.
- No `--broadcast` mode inside this script. If the user wants broadcast, they pick broadcast in the
  forge.
- No extra UI sliders beyond what the hivemind generator already has.

## 6. Acceptance checks before handing back

1. `node --check` on the extracted `<script>` block passes.
2. `py_compile` on the emitted Python script passes (generate once, save to tmp, compile).
3. Emitted file references `workspace_id` consistently in every endpoint call.
4. `/switch` is absent from the emitted slash-command handler AND from `/help` output.
5. The four field-shape bugs from the last patch CANNOT recur — grep the emitted script for
   `h.get("text")`, `identity_mode`, `char_ctx.get("drift")`, `/character/identity` and fail the
   build if any appear.
6. Running `python per_agent.py` (no `--agent`) exits non-zero with a message listing valid ids.

## 7. Deliverable

One HTML edit. Diff should be additive where possible:
- one new radio option in the mode group
- one new Python-template string emitted when `per-agent` is selected
- shared helper functions extracted or duplicated (duplication is acceptable — the existing
  window/broadcast blocks already duplicate)

Do not refactor window or broadcast while adding this. Those blocks are now field-patched and
should stay byte-stable.
