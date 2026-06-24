# TORMENT Audit — Private Generation Owner Path Design v0.1

## 1. Status

**Docs-only design. Authorizes no implementation.** After the live-owner
candidate inventory closed (`f04b319`), the Codex/operator result on the
owner-shape gate was **PASS, A only**: the *private generation owner* shape is
selected **as a design shape only**. Shape **B** (a private runner delegation
seam) is **not** selected and remains deferred (see §7).

This document defines what a *later* implementation or tests-first slice must
preserve. It does **not** create a module, add tests, wire endpoints, modify
`app.py` or `agent_loop.py`, or open B. The future module name used throughout —
`torment_service/audit_private_generation_owner.py` — is a **name for reference
only; no such file is created by this document.**

Builds on (anchors, not re-opened): live-owner candidate inventory
(`f04b319`, `tests/test_audit_live_owner_candidate_inventory.py`); model-visible
context owner seam ADR (`d2f405f`,
`docs/TORMENT_AUDIT_MODEL_VISIBLE_CONTEXT_OWNER_SEAM_DESIGN_v0.1.md`);
caller-owned same-turn contract (`382a0f1`,
`docs/TORMENT_AUDIT_CALLER_OWNED_SAME_TURN_PROVENANCE_CONTRACT_v0.1.md`);
admissible evidence packet contract
(`docs/TORMENT_MODEL_API_TRUTHFULNESS_AUDIT_ADMISSIBLE_EVIDENCE_PACKET_CONTRACT_v0.1.md`);
A-prime characterization (`464320a`); prompt-inclusion harness (`59b582e`);
selected-items runner bridge (`392caa2`).

## 2. Why this exists

The audit-evidence lane can already *observe* whether selected admitted item text
was present in the captured `AgentRunner` prompt for the final reviewed response
(`bd916a8`), and the selected-items runner bridge (`392caa2`) can forward
selected item dicts into that observer. What is still missing is an honest live
path that **owns both the assembled context and the exact model-visible
prompt/messages used to generate the response** in one frame.

Today (per §3) that ownership is split: `app.py` owns assembly (`/retrieve`) but
runs no generation; `AgentRunner` owns prompt capture and the completion call but
performs no retrieval/assembly/extraction; and the bridge that could pass selected
items is a dead-end. The A-prime characterization (`464320a`) named the bar an
honest owner must clear: it must **control or observe the model-visible context
boundary and check that each selected item text is present there** — structural
co-location of items on a result is not enough.

The private generation owner is the shape that can clear that bar by owning and
capturing the exact prompt/messages it sends to generation, in its own private
frame, **without pushing any of that ownership into `AgentRunner`**.

## 3. Current source topology (from `f04b319`)

The candidate inventory records, by source, the present owner-relevant call
sites (production scope, `torment_service/`):

- `assemble_context` — owned only by `app.py` (the `/retrieve` handler).
- `AgentRunner.run_turn` callers — `agent_loop.py` (the reflex self-call) and the
  selected-items runner bridge; **the bridge is a dead-end** (no production
  caller calls it).
- prompt-request building (`_build_llm_prompt_request`), prompt capture, and
  model completion (`llm_client.complete`) — all in `agent_loop.py`.
- Only `torment_service/audit_selected_items_runner_bridge.py` may pass
  `audit_admitted_context_items`.
- `AgentRunner` owns prompt capture but **not** retrieval, assembly, or
  selected-item extraction.
- The bridge forwards selected item dicts only, reads no result packet, and stays
  packet-blind.
- Generation ownership and assembled-context ownership are **disjoint** across
  production today, except inside the single unwired bridge candidate.

This topology is the ground the design must preserve: nothing in this document
moves any of those call sites, and no new caller is authorized here.

## 4. Selected future shape: private generation owner

The private generation owner is a **private/internal module** (future:
`torment_service/audit_private_generation_owner.py`). It is **not** an endpoint,
**not** `/retrieve`, **not** `/agent/query`, **not** `app.py`, and **not**
`agent_loop.py`.

It owns a single turn's full frame:

- It **receives or builds exactly one explicit `AssembledContext`** in its own
  frame. The `AssembledContext` stays local to the owner.
- It **extracts selected item dicts from that same `AssembledContext` only**,
  using the existing pure extractor (`selected_admitted_items`). Selected item
  dicts are the only thing that flows onward.
- It **renders and captures the exact model-visible prompt/messages** it will send
  to generation, holding them in-frame.
- It **owns the generation call** against those captured prompt/messages and
  obtains the final response (after any review it applies). Because it owns the
  exact prompt/messages, it can **check selected item text inclusion** rather than
  infer it from co-location.
- It composes an **output-only observation packet** from the selected item dicts
  plus the final response text, only after the inclusion check, using the existing
  pure builders/observer.

This is what distinguishes A from B: shape A **owns the model-visible context
construction and the generation call itself**, so the captured prompt is exactly
the one that produced the response. The assembled context never leaves the owner's
frame, and `AgentRunner` is unaffected — it keeps owning prompt capture only and
gains no retrieval/assembly/extraction (see §7).

## 5. Required call order

A later implementation or tests-first slice must preserve this order (mirroring
the owner-seam ADR `d2f405f` and the harness proof shape `59b582e`):

1. **Frame opens.** Receive or build exactly one explicit `AssembledContext` in
   the owner's own frame.
2. **Extract.** Take selected item dicts from that same `AssembledContext` via the
   existing pure `selected_admitted_items` extractor — selected item dicts only;
   never the whole `AssembledContext`.
3. **Render.** Build the exact model-visible prompt/messages the owner will send
   to generation.
4. **Capture.** Hold those exact prompt/messages in-frame (the captured boundary).
5. **Generate.** Run generation against the captured prompt/messages; apply any
   review the owner performs; obtain the final response text.
6. **Inclusion check.** Check that each selected item text is present in the
   captured prompt/messages that produced the final response. If any selected item
   text is absent → **no packet** (fail closed for the packet only); the turn
   still completes normally and absence is non-punitive.
7. **Compose (observation-only).** Only then compose the audit evidence packet
   from the selected item dicts plus the final response text, via the existing
   pure packet/sidecar/observer helpers.
8. **Emit as observation.** Return/emit the packet as output-only observation;
   route it nowhere that controls behavior.

Capture (step 4) precedes generation (step 5); the inclusion check and packet
composition (steps 6–7) happen only once the final response is known, and only
against the captured boundary that produced it.

## 6. Invariants / forbidden flows

**Invariants the owner must satisfy:**

1. **Private/internal only.** It is not `/retrieve`, not `/agent/query`, not
   `app.py`, and not `agent_loop.py`.
2. **One explicit `AssembledContext` in its own frame** — received or built
   locally.
3. **Extraction from that same `AssembledContext` only** — selected item dicts
   are derived from the one local `AssembledContext`, not from a re-query, a
   different context, or `assembled_text` parsing.
4. **Renders and captures the exact prompt/messages** it sends to generation.
5. **Checks selected item text against that captured prompt/messages before
   passing items onward.**
6. **Never passes `AssembledContext` into `AgentRunner`.**
7. **Passes only selected item dicts onward.**
8. **Packet presence/absence is output-only observation, never control.**
9. **B remains deferred** (see §7); this shape does not implement or open it.

**Forbidden flows (this owner must never introduce):**

- endpoint behavior changes;
- public schema/API changes;
- prompt-request exposure (the captured prompt/messages stay private to the
  owner's frame — not surfaced on any result, metadata, debug, endpoint, or
  schema);
- persistence;
- memory writes;
- writer paths;
- retrieval feedback;
- ranking / suppression / retry / style steering;
- review / output / ingest / fabric feedback driven by packet presence/absence;
- database / substrate;
- Gate D;
- dream / private cognition runtime;
- Envelope Audit runtime;
- authority wording in the surface or its flags (no `verified`, `trusted`,
  `certified`, `truth`, `same_turn_verified`, or "provenance verification").

## 7. Why B remains deferred

Shape **B** is a *private runner delegation seam*: a caller that drives
`AgentRunner.run_turn(...)` while owning retrieval/assembly/extraction around it.
B sits **closer to the runner boundary** and carries a specific hazard: it risks
making `AgentRunner` **silently own retrieval/assembly context** — the exact
boundary the candidate inventory (`f04b319`) and the owner-seam ADR (`d2f405f`)
were written to protect. The moment assembled context flows toward the runner,
`AgentRunner`'s "prompt capture only" ownership starts to blur.

Shape **A** avoids that hazard structurally: the `AssembledContext` and the exact
prompt/messages stay entirely inside the owner's own frame, **outside**
`AgentRunner`. `AgentRunner` continues to own prompt capture only and never gains
retrieval, assembly, or selected-item extraction. Because A is the lower-risk
boundary, it is the one selected as a design shape; **B stays deferred until A is
proven safe in a later tests-first slice**, and opening B requires its own
separate gate.

## 8. What this document does not authorize

This document authorizes **no implementation of any kind**. Specifically, it does
**not**:

- create `torment_service/audit_private_generation_owner.py` (a name for
  reference only) or any other module;
- add tests;
- wire any endpoint, or change `/retrieve` or `/agent/query`;
- modify `app.py` or `agent_loop.py`;
- open or design shape B;
- add any public schema/API, persistence, memory write, writer path, retrieval
  feedback, ranking/suppression/retry/style steering, review/output/ingest/fabric
  feedback, database/substrate, Gate D, dream/private cognition runtime, or
  Envelope Audit runtime;
- introduce any authority flag or wording.

It defines only the shape and the invariants a later, separately-ratified slice
must preserve.

## 9. Next admissible slice

The next admissible step is a **tests-first / source-only characterization of the
private generation owner shape** — demonstrating the required call order (§5) and
invariants (§6) against a **test-local fake generation boundary** (in the manner
of the harness `59b582e`), with **no production module and no wiring**. That slice
must be selected by a separate Codex/operator gate before any test file is named.

Only if that characterization passes may a private module be proposed in a
**later, separately-ratified** slice. **B remains deferred.** Nothing here
pre-authorizes either step.
