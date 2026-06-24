# TORMENT Audit — Private Owner Live-Wiring Gate Frame v0.1

## 1. Status

**Docs/design only. This frame authorizes no live wiring.** It defines what must
be true before a future Codex/operator gate could even *consider* wiring the
private generation owner into a live path. It selects nothing, builds nothing, and
changes no production code or tests. Crossing the gate requires a separate,
explicit Codex/operator decision.

Builds on (anchors, not re-opened): private generation owner design (`4bbfdcd`,
`docs/TORMENT_AUDIT_PRIVATE_GENERATION_OWNER_PATH_DESIGN_v0.1.md`); model-visible
context owner seam ADR (`d2f405f`,
`docs/TORMENT_AUDIT_MODEL_VISIBLE_CONTEXT_OWNER_SEAM_DESIGN_v0.1.md`); caller-owned
same-turn contract (`382a0f1`,
`docs/TORMENT_AUDIT_CALLER_OWNED_SAME_TURN_PROVENANCE_CONTRACT_v0.1.md`);
admissible evidence packet contract
(`docs/TORMENT_MODEL_API_TRUTHFULNESS_AUDIT_ADMISSIBLE_EVIDENCE_PACKET_CONTRACT_v0.1.md`);
live-owner candidate inventory (`f04b319`); owner implementation (`2b507d8`).

Doctrine this frame exists to protect:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

## 2. Current closed-as-built state

The observe-authority lane is built and closed-as-built:

- **Shape A is implemented** as a private, test-called owner
  (`torment_service/audit_private_generation_owner.py`, `2b507d8`): it holds a
  caller-held `AssembledContext`, extracts `selected_admitted_items(...)` from that
  same object, renders and captures its own prompt/messages, calls a private
  generation boundary, composes an observation-only packet via
  `observe_prompt_inclusion_packet(...)`, and returns response text plus an
  optional packet.
- **Shape B** (a private runner delegation seam) remains **deferred**.
- **The live observation spine** exists in `agent_loop.py` but is **dormant**: no
  live production caller feeds `audit_admitted_context_items`, so in live operation
  the packet is always absent (`None`). The selected-items runner bridge that could
  feed it is a **dead-end** (called only by tests).
- The audit packet remains **optional and non-punitive**: its absence carries no
  negative meaning and changes no behavior.
- No endpoint/schema/API exposure; no prompt-request exposure; no `AgentRunner`
  retrieval/assembly/extraction ownership expansion; no audit-to-control feedback.

This is the baseline a future wiring proposal would change. Until such a proposal
clears this gate, **the owner remains unwired.**

## 3. Future live-wiring admissibility criteria

A future live-owner wiring proposal must specify, concretely and by source, ALL of:

1. **Exact caller path** — the precise private/internal module and function that
   would invoke the owner in a live turn, and the call sequence around it.
2. **Exact owner of `AssembledContext`** — which frame holds the single explicit
   assembled context, and that it never leaves that frame.
3. **Exact source of selected admitted items** — that they come from
   `selected_admitted_items(...)` over that same assembled context, and from
   nothing else (no re-query, no different context, no `assembled_text` parsing).
4. **Exact private generation boundary** — the specific completion call the owner
   drives, and that it receives only the captured prompt/messages.
5. **Exact point where prompt/messages are captured** — the line at which the owner
   records what it sends, before generation.
6. **Exact point where the observation packet is composed** — after a final
   response exists, via `observe_prompt_inclusion_packet(...)`, only on observed
   inclusion.
7. **Exact result surface** — where the optional packet is returned, and that it is
   observation-only and reaches no control path.
8. **Exact tests** showing the packet cannot influence output, review, retry,
   ranking, style, writes, ingest, retrieval, or persistence.

A proposal missing any item is inadmissible.

## 4. Hard forbidden surfaces

A live-wiring proposal must introduce none of the following:

- endpoint/schema/API changes;
- prompt-request exposure;
- captured prompt/messages on metadata, logs, debug, result, or any public surface;
- `AgentRunner` retrieval/assembly/extraction ownership expansion;
- Shape B, unless separately authorized;
- writer path;
- retrieval feedback;
- persistence / database / substrate;
- durable private cognition / dream runtime / Gate D / Envelope Audit runtime;
- autonomy;
- audit-to-control feedback (packet presence or absence steering any behavior).

## 5. Required future proof shape

Before any implementation, a future proposal must land (tests/source first):

- a **tests-only characterization** of the intended live caller path (against a
  test-local generation boundary, no wiring);
- a **source guard** that only the sanctioned live caller may feed selected audit
  items into the owner / run path;
- a **source guard** that `app.py` and public endpoints remain non-callers;
- an **AST/source guard** that packet presence/absence drives no branch;
- a **no-prompt-exposure guard** (captured prompt/messages never reach result,
  metadata, log, debug, endpoint, or schema);
- a **no-`AgentRunner`-ownership-expansion guard**;
- a **fail-soft / absence-non-punitive behavior guard** (packet absence changes
  nothing; observer/builder failure yields no packet and no error path).

These are the same guard shapes already used across the closed audit lane; a
live-wiring proposal must extend them to the new caller, not weaken them.

## 6. Stop rule

If a future proposal cannot demonstrate every condition in §3–§5, **the owner
remains unwired.** Inability to meet the gate is a valid, expected outcome: the
dormant observation spine and the test-only owner are a stable resting state, not
a deficiency to be patched around.

## 7. What this frame does not authorize

No live wiring; no production code; no tests beyond doc tooling; no endpoint /
schema / API; no prompt-request exposure; no Shape B; no `AgentRunner` ownership
expansion; no writer path; no retrieval feedback; no persistence / database /
substrate; no durable private cognition / dream runtime / Gate D / Envelope Audit
runtime; no autonomy; no audit-to-control feedback; and no selection of a caller
path. It records the gate only.
