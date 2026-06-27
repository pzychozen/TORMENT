# TORMENT — Memory-to-Prompt-for-Generation Same-Turn Dual-Ownership CALLER-PROPOSAL Frame v0.1

## 1. Status / non-authorization

**CALLER-PROPOSAL frame. Docs-only / NON-AUTHORIZING / no lane opened / fence closed / seam
dormant.** Hilmir authorized **only this proposal frame**; Codex PASS. It answers exactly one
question: which, if any, source-grounded same-turn caller candidate should be **proposed on
paper** to own both governed `AssembledContext.assembled_text` (or a bounded derivative) and
an authoritative `AgentRunner` generation invocation able to pass `memory_context_text` —
while preserving all current fences — or whether the lane must remain **HOLD**.

This frame **may name/select one proposed caller candidate on paper**. A proposed selection
is **NOT** wiring authorization, **NOT** implementation authorization, and **NOT**
endpoint/runtime authorization. It writes **no code and no tests**, makes **no
endpoint/API/schema/public-surface change**, and invents no runtime. Where this frame and any
parent contract/guard differ, the contract/guard wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `daf824c` (repo edge). Subordinate to, and may not contradict: the orchestration
decision frame (`e037ad1` / recorded `5373dac`), the live-caller eligibility frame
(`2cc5210` / recorded `669de81`), the landed dormant slice (`5d04658`), the production
implementation proposal, the candidate proof-contract lock, the caller-owned same-turn
provenance contract, and the PW-1…PW-8 pre-wiring guard.

## 2. Current edge and chain

```text
- daf824c  docs(project): clean memory-to-prompt orchestration pointer   (current edge / anchor)
- 5373dac  docs(project): record memory-to-prompt orchestration decision frame
- e037ad1  docs(cognition): frame memory-to-prompt orchestration decision
           — verdict: a later CALLER-PROPOSAL is admissible only if separately authorized,
             source-grounded, and fence-preserving; this frame IS that CALLER-PROPOSAL.
- 669de81  docs(project): record memory-to-prompt live-caller eligibility frame (2cc5210)
- 2cc5210  docs(cognition): frame memory-to-prompt live caller eligibility
           — verdict: no existing eligible live caller; ownership disjoint; HOLD.
- 5d04658  feat(cognition): add runner-local memory prompt context
           — landed the dormant runner-local memory_context_text seam.
```

This frame adds **no commit-bearing source change** beyond itself and its §0 pointer.

## 3. The exact decision question (Codex-approved, verbatim)

> Which, if any, source-grounded same-turn caller candidate should be proposed on paper to
> own both governed `AssembledContext.assembled_text` or a bounded derivative and
> authoritative `AgentRunner` generation invocation able to pass `memory_context_text`, while
> preserving all current fences; or must the lane remain HOLD?

## 4. Non-authority / allowed scope

```text
ALLOWED:
- docs-only proposal frame;
- compare candidates;
- name/select ONE proposed caller candidate on paper;
- perform a source-first survey INSIDE this artifact BEFORE naming/selecting any candidate;
NOT AUTHORIZED by a proposed selection:
- wiring;          - implementation;          - endpoint/runtime behavior.
```

## 5. Source-first survey (current source, verified before any candidate is named)

### 5.1 `torment_service/agent_loop.py` — AgentRunner (the dormant seam + generation)

```text
- run_turn(self, workspace_id, agent_id, observation, step, *,
           audit_admitted_context_items=None)                       [L503-511]
    · accepts NO memory_context_text — only the audit-staging keyword.
    · frame is built from observation.text via
      self.controller.deliberate_only(raw_input=observation.text, ...) [L532-538];
      no assemble_context / AssembledContext anywhere in the method.
    · calls self._execute_with_prompt_request(frame=..., mode=..., action=...) with NO
      memory_context_text [L601-606] → the seam defaults to None → DORMANT.
    · audit_admitted_context_items is returned only on TurnResult and never routed into
      cognition / review / prompts / ingest / writers / model-visible context [L510-519, L753].
- _execute_with_prompt_request(..., *, memory_context_text=None)     [L1036-1056]
    · forwards into _execute(..., _memory_context_text=memory_context_text). SEAM OWNER.
- _execute(..., _memory_context_text=None)
    · builds the request via _build_llm_prompt_request(..., memory_context_text=
      _memory_context_text) on the ANSWER [L845] and USE_TOOL [L887] paths.
- _build_llm_prompt_request(..., *, tools, memory_context_text=None)  [L1064-1090]
    · when non-empty, prepends exactly ONE bounded labelled guidance message BEFORE the raw
      user input; raw user input stays its own later message; _build_system_prompt unchanged.
- _build_memory_context_message(memory_context_text)                 [L1092-1115]
    · None/non-str/empty/whitespace → None; else stripped, capped at 1200 chars with a
      truncation marker, prefixed with the read-only guidance label; turn-local; NOT stored
      on self; NOT exposed; drives no review/output/retry/ranking/style/write/persistence/
      retrieval path.

OWNERSHIP — AgentRunner owns HALF 2 (authoritative generation + the dormant seam) but NOT
HALF 1 (it touches no assemble_context / AssembledContext / assembled_text; grep of
agent_loop.py for those symbols returns nothing).
```

### 5.2 `torment_service/app.py` — `/agent/query` (possible orchestration terrain ONLY)

```text
- @app.post("/agent/query"); def query(req) -> Dict[str, Any]              [L907-908]
    · runs ThinkingController / geometric harvest; returns a retrieval/MemoryPlan dict.
    · the app module references NO AgentRunner and NO run_turn anywhere (grep negative).
    · assemble_context is imported [L1319] but called ONLY inside retrieve_assembled
      [L1449] — NOT in query.

OWNERSHIP — /agent/query owns NEITHER half today. To own HALF 1 it would have to call
assemble_context inside query; to own HALF 2 it would have to import/instantiate/invoke
AgentRunner. Either changes the endpoint's response/behavior (it returns a retrieval dict
today) → an endpoint/public-surface change. Inspected as orchestration terrain, but it cannot
own both halves WITHOUT such a change.
```

### 5.3 `torment_service/app.py` — `/retrieve` / `retrieve_assembled` (read-only context-source)

```text
- @app.post("/retrieve"); def retrieve_assembled(req) -> Dict[str, Any]    [L1341-1342]
    · runs fabric.query + archive retrieval + assemble_context(...) [L1449] and returns the
      assembled context. No AgentRunner / run_turn.

OWNERSHIP — owns HALF 1 (governed assembled_text) but NOT HALF 2. It must remain read-only /
context-source terrain; making it invoke generation would convert it into generation terrain.
```

### 5.4 `torment_service/retrieval_assembler.py` — `assemble_context` / `AssembledContext`

```text
- imports only stdlib (math, dataclasses, typing)                          [L22-26]
- class AssembledContext: assembled_text: str = ""                         [L77-83]
- def assemble_context(...): builds assembled_text [L546] and returns an AssembledContext
  [L557]; contains no AgentRunner / run_turn / llm_client / generation invocation.

OWNERSHIP — owns HALF 1 (context PRODUCTION) only; never HALF 2. Read-only context-source.
```

### 5.5 `torment_service/audit_private_generation_owner.py` — NEGATIVE terrain

```text
- PrivateGenerationOwner.__init__(self, assembled_context, generation_boundary) [L70-72]
- run(self, user_input): calls self._gen.complete(system_prompt=..., messages=...) [L83]
  then observe_prompt_inclusion_packet(...) [L91].

OWNERSHIP — it holds its own assembled_context, but its generation is its OWN
generation_boundary, NOT the authoritative AgentRunner. So it does NOT own HALF 2 as defined.
Owner-as-generation is foreclosed (W-7 sidecar-only). EXCLUDED / unwired / not authoritative.
```

### 5.6 `torment_service/audit_selected_items_runner_bridge.py` — NEGATIVE terrain

```text
- run_turn_with_selected_items_observation(runner, assembled_context, ...)  [L53-55]
    · selected_items = selected_admitted_items(assembled_context)           [L72]
    · runner.run_turn(..., audit_admitted_context_items=selected_items)     [L73-78]
    · passes audit_admitted_context_items ONLY — NEVER memory_context_text.
    · "called nowhere in production (observation-only)."                    [L44]

OWNERSHIP — uniquely co-locates an assembled_context AND a run_turn invocation, but it feeds
the AUDIT-staging keyword (routed only to TurnResult), not the memory seam. Repurposing it to
feed the seam would reopen U1 / audit-owner. EXCLUDED / negative terrain only.
```

## 6. Candidate eligibility rule

A candidate is eligible to be **PROPOSED on paper** only if, from current source:

```text
R1  it owns (or, for a new internal owner, can own in its own body, in one turn) BOTH
      HALF 1  governed AssembledContext.assembled_text or a bounded derivative produced
              through existing governed read/assembly paths; AND
      HALF 2  an authoritative AgentRunner generation invocation able to pass
              memory_context_text into the dormant runner-local seam; AND
R2  selecting it crosses NONE of the fences (AgentRunner stays runner-local and does not own
      retrieval/assembly authority; /retrieve stays read-only/context-source; no
      endpoint/API/schema/public-surface change; PrivateGenerationOwner excluded; audit bridge
      excluded; the seam stays guidance-only/bounded/labelled/read-only/turn-local/
      non-public/non-persistent; no retrieval-authority expansion; no U1/audit-owner).
If no candidate satisfies R1+R2, the verdict is HOLD.
```

## 7. Candidate comparison table

```text
# CANDIDATE                         | HALF 1 (assembled    | HALF 2 (authoritative      | FENCE VIOLATION IF      | VERDICT
                                    | context)             | AgentRunner generation)    | SELECTED                |
--+---------------------------------+----------------------+----------------------------+-------------------------+----------
1 AgentRunner self-ownership        | ✗ frame=observation  | ✓ owns generation + the    | YES — would have to      | FAIL
                                    |   .text; no assembly  |   dormant seam              |   acquire retrieval/    |
                                    |   in agent_loop.py    |                            |   assembly authority;   |
                                    |                      |                            |   must stay runner-local|
2 /retrieve · retrieve_assembled ·  | ✓ assemble_context → | ✗ no AgentRunner/run_turn  | YES — would have to     | FAIL
  assemble_context                  |   assembled_text     |                            |   invoke generation;    |
                                    |                      |                            |   must stay read-only   |
3 /agent/query (app.py terrain)     | ✗ returns retrieval/ | ✗ no AgentRunner/run_turn  | YES — owning either half| FAIL
                                    |   MemoryPlan dict    |   in app.py                |   changes endpoint      |
                                    |                      |                            |   behavior/public surface|
4 PrivateGenerationOwner            | ~ holds its own      | ✗ invokes its OWN          | YES — owner-as-         | EXCLUDED
                                    |   assembled_context  |   generation_boundary, NOT |   generation foreclosed |
                                    |                      |   authoritative AgentRunner|   (W-7); not AgentRunner |
5 selected-items audit bridge       | ~ holds assembled_   | ✓ calls runner.run_turn,   | YES — feeds AUDIT        | EXCLUDED
                                    |   context (co-located)|   BUT passes audit_admitted| staging, not the seam;   |
                                    |                      |   _context_items, never    |   repurposing reopens   |
                                    |                      |   memory_context_text      |   U1/audit-owner        |
6 NEW internal non-endpoint same-   | ✓ (paper) calls       | ✓ (paper) invokes          | NO — orchestrator owns  | PROPOSED
  turn memory-orchestration caller  |   assemble_context,   |   AgentRunner.run_turn with|   assembly (not Runner);| (paper-only,
                                    |   derives a bounded   |   the bounded derivative   |   Runner stays runner-  |  deferred)
                                    |   read-only derivative|   passed into the dormant  |   local; /retrieve       |
                                    |   of assembled_text   |   seam (needs future       |   untouched; no endpoint|
                                    |                      |   run_turn→seam threading) |   change; no retrieval-  |
                                    |                      |                            |   authority expansion   |
```

## 8. Proposed caller candidate (candidate 6)

**PROPOSED on paper, non-authorizing, deferred:** a **NEW internal, non-endpoint, same-turn
memory-orchestration caller** — a future module/function, separate from `AgentRunner`,
`/retrieve`, `/agent/query`, `PrivateGenerationOwner`, and the audit bridge — that, in one
turn and in its OWN body:

```text
(a) HALF 1 — calls the existing governed assemble_context(...) [retrieval_assembler.py] as a
    FUNCTION (not via the /retrieve endpoint) to obtain an AssembledContext, and derives a
    bounded, read-only derivative of AssembledContext.assembled_text; AND
(b) HALF 2 — invokes the authoritative AgentRunner.run_turn(...) for that same turn, supplying
    the bounded derivative as memory context so it reaches the dormant runner-local seam
    (_execute_with_prompt_request → _execute → _build_llm_prompt_request →
    _build_memory_context_message).
```

Why it is source-supportable WITHOUT crossing any fence:

```text
- The ORCHESTRATOR (not AgentRunner) owns the assembly; AgentRunner stays runner-local and
  only CONSUMES the optional bounded text through its EXISTING dormant seam — AgentRunner
  acquires no retrieval/assembly authority.
- assemble_context is consumed as a plain function; the /retrieve endpoint, its API/schema/
  response shape are untouched; /retrieve stays read-only/context-source.
- The orchestrator is a NEW INTERNAL site, not an endpoint; the proposal mandates no
  endpoint/API/schema/public-surface change. Its live entrypoint/wiring is DEFERRED and
  separately gated (see §10).
- It consumes existing governed assembly only — no new retrieval authority, store, or write.
- The seam already enforces guidance-only/bounded(≤1200)/labelled/read-only/turn-local/
  non-public/non-persistent; the orchestrator passes only a bounded derivative.
```

**One unresolved future-code dependency, named not built:** today `run_turn(...)` does **not**
accept `memory_context_text` (it accepts only `audit_admitted_context_items`), and the seam is
reachable only through the private `_execute_with_prompt_request`. A later implementation slice
would have to add an OPTIONAL `memory_context_text` parameter to `run_turn` that threads ONLY
into `_execute_with_prompt_request` (default `None` preserving byte-identical memory-blind
behavior). **That threading is a deferred obligation (§10), not authorized here.**

This selects the candidate **on paper only.** It wires nothing and authorizes nothing.

## 9. Why the rejected candidates fail

```text
1 AgentRunner self-ownership — FAIL: owning HALF 1 means AgentRunner taking on retrieval/
  assembly authority (importing/calling assemble_context inside the runner). The fence
  requires AgentRunner to stay runner-local and NOT own retrieval/assembly. Source confirms it
  owns no assembled context today (frame = observation.text).
2 /retrieve · assemble_context — FAIL: owning HALF 2 means the retrieval path invoking
  AgentRunner generation, converting read-only/context-source terrain into generation terrain.
  The fence requires /retrieve to stay read-only/context-source only.
3 /agent/query — FAIL: it owns neither half today and app.py holds no AgentRunner/run_turn;
  making it own either half changes the endpoint's behavior/response (public surface). The
  fence forbids endpoint/API/schema/public-surface change. (Inspected as orchestration terrain,
  not merely negative — it still fails the no-endpoint-change fence.)
4 PrivateGenerationOwner — EXCLUDED: its generation is its OWN boundary, not the authoritative
  AgentRunner; owner-as-generation is foreclosed (W-7 sidecar-only). Remains unwired/not
  authoritative.
5 selected-items audit bridge — EXCLUDED: it feeds audit_admitted_context_items (audit staging
  routed only to TurnResult), never memory_context_text; repurposing it to feed the seam
  conflates audit observation with generation-context supply and reopens U1/audit-owner.
  Remains negative terrain / observation-only / called nowhere in production.
```

## 10. Required proof obligations for any later implementation proposal

Any later, **separately authorized** implementation proposal (and the code+tests slice after
it) for candidate 6 must prove ALL of:

```text
P1  run_turn gains an OPTIONAL memory_context_text param threading ONLY to
    _execute_with_prompt_request → _execute → _build_llm_prompt_request →
    _build_memory_context_message; default None preserves byte-identical memory-blind behavior.
P2  the orchestrator derives the bounded text ONLY from governed AssembledContext.assembled_text
    (or a bounded derivative); no raw hits, no audit packets, no private/candidate/unadmitted/
    substrate-only content; no new retrieval authority/store/write.
P3  AgentRunner imports/owns NO assemble_context/AssembledContext/retrieval_assembler (the
    grep-provable runner-local invariant is preserved).
P4  the /retrieve endpoint, its API/schema/response shape are unchanged; assemble_context is
    consumed as a function, not via the endpoint.
P5  no endpoint/API/schema/public-surface change; the orchestrator's live entrypoint must be
    fence-preserving (internal) and is separately gated — if none exists without an endpoint
    change, the candidate fails THEN.
P6  the seam stays guidance-only/bounded(≤1200)/labelled/read-only/turn-local/non-public/
    non-persistent; never on TurnResult/metadata/logs/endpoints/schemas/persistence; drives no
    review/output/retry/ranking/style/write/retrieval path.
P7  PrivateGenerationOwner stays unwired; the audit bridge stays observation-only; no
    U1/audit-owner reopening; no dual-ownership-as-audit.
P8  tests + source/AST guards land in the SAME later slice (inclusion-on-valid; omission-on-
    empty/invalid; system-prompt-unchanged; user-input-separate; bounded-truncated; no-exposure;
    AgentRunner-owns-no-assembly; no-endpoint/schema/app-change; no-owner/U1/dual-ownership;
    no-write/feedback/control).
```

## 11. Forbidden crossings (this step)

```text
- no code            - no tests             - no wiring
- no runtime orchestration implementation
- no endpoint/API/schema/public-surface change
- no retrieval-authority expansion
- no memory write/persistence
- no review/output-control/suppression/retry/ranking/style steering
- no U1/audit-owner reopening
- no PrivateGenerationOwner
- no Gate D/private cognition/dream/Envelope Audit runtime
- no database/substrate/carrier/schema/storage/migration
- no Gate B/R-field/Probe-v1/shaping
- no hidden finalizer/refusal/identity rewrite
- no hidden chain-of-thought storage or exposure
```

This document proposes a caller candidate on paper only. Nothing above is wired, implemented,
or authorized.

## 12. Final verdict

**PROPOSED (paper-only, deferred):** the single source-grounded candidate that can own both
halves in one turn without crossing any fence is **candidate 6 — a NEW internal, non-endpoint,
same-turn memory-orchestration caller** that calls `assemble_context(...)` for a bounded
read-only derivative of `assembled_text` (HALF 1) and invokes `AgentRunner.run_turn(...)`
supplying that derivative into the dormant runner-local seam (HALF 2, via a future
`run_turn`→seam threading named in §10). Candidates 1–3 **FAIL** (AgentRunner self-ownership
would seize retrieval/assembly authority; `/retrieve` would become generation terrain;
`/agent/query` would require an endpoint/public-surface change); candidates 4–5 remain
**EXCLUDED** (`PrivateGenerationOwner` is owner-as-generation, foreclosed; the audit bridge is
audit-lane / negative terrain). **The caller-proposal question no longer remains HOLD-for-lack-of-candidate — one candidate
is named on paper — but the live-caller / implementation / wiring lane remains HOLD until a
later separately authorized implementation proposal + code/test slice under Hilmir + Codex;
this selection authorizes no wiring, no implementation, and no endpoint/runtime change. This
frame selects the candidate on paper only.**

## 13. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION SAME-TURN DUAL-OWNERSHIP CALLER-PROPOSAL FRAME /
DOCS-ONLY / NON-AUTHORIZING / NO LANE OPENED / FENCE CLOSED / SEAM DORMANT. It performs a
source-first survey of `agent_loop.py` (run_turn takes no memory_context_text; frame =
observation.text; the dormant seam runs `_execute_with_prompt_request → _execute →
_build_llm_prompt_request → _build_memory_context_message`, bounded ≤1200, labelled, read-only,
turn-local, non-exposed; AgentRunner references no assemble_context/AssembledContext),
`app.py` (`/agent/query` and the module hold no AgentRunner/run_turn; `assemble_context` is
called only inside `/retrieve`'s `retrieve_assembled`), `retrieval_assembler.py` (stdlib-only;
`assemble_context` → `AssembledContext.assembled_text`; no generation), and the two negative
terrains (`PrivateGenerationOwner.run` calls its own `generation_boundary.complete`, not
AgentRunner; the selected-items bridge passes `audit_admitted_context_items`, never
`memory_context_text`, and is called nowhere). It then compares candidates against the two
halves and the fences and selects, **on paper only**, candidate 6 — a NEW internal,
non-endpoint, same-turn memory-orchestration caller (assemble_context derivative + AgentRunner
generation via a future seam-threading) — as the one fence-preserving proposal; candidates 1–3
FAIL and 4–5 stay EXCLUDED. **It selects this caller on paper only — it wires nothing, writes
no code/tests, changes no endpoint/API/schema/public surface, expands no retrieval authority,
reopens no U1/audit-owner, wires no PrivateGenerationOwner, opens no lane, and lifts no fence;
any implementation requires a separately authorized proposal + code/test slice under Hilmir +
Codex review.** Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.
