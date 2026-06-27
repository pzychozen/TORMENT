# TORMENT — Memory-to-Prompt-for-Generation Production Implementation Proposal v0.1

## 1. Status

**Production implementation proposal. Docs-only / NON-AUTHORIZING / no lane opened. The
memory-to-prompt fence remains closed.** Hilmir authorized **only this proposal**. It
specifies the **exact proposed production patch shape** for later Codex/Hilmir review.
It is **not authorized here**, it is **not** a directive to implement now, and it authorizes no
production code, no tests, no prompt change, no model-visible memory injection, no
retrieval-to-generation wiring, and no endpoint/API/schema or public-surface change. The
patch described below is **proposed**; no patch is selected, and none is authorized for implementation here.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `67c34da` (repo edge). Subordinate to, and may not contradict: the memory-to-prompt
decision frame, design frame, the source-baseline lock + correction
(`tests/test_memory_to_prompt_generation_boundary_characterization.py`), the
implementation-proposal frame, the candidate proof-contract lock
(`tests/test_memory_to_prompt_candidate_proof_contract.py`), the caller-owned same-turn
provenance contract, and the PW-1…PW-8 pre-wiring guard. Where this proposal and any parent
contract/guard differ, the contract/guard wins.

## 2. Source-grounded baseline (verified; current behaviour)

```text
- `/agent/query` currently routes through `fabric.query(...)` with `memory_plan`; it does
  NOT call `AgentRunner`.
- `assemble_context(...)` returns an `AssembledContext`, including `assembled_text`.
- `AgentRunner` currently builds model-visible requests through:
    `_build_llm_prompt_request(...)` → `_LLMPromptRequest` → `_complete_llm_prompt_request(...)`.
- `_build_system_prompt(...)` remains the minimal system prompt today
  ("You are agent {agent_id} operating in mode {mode}.").
- `PrivateGenerationOwner` / `audit_private_generation_owner.py` remains EXCLUDED —
  unwired / test-called — and is NOT the authoritative `AgentRunner` path.
```

The proposed patch below would be the first change to touch the prompt path; this document
does not make it.

## 3. Proposed eligible memory source (proposal-only)

```text
- The proposed source WOULD be the existing governed read/assembly output represented by
  `AssembledContext.assembled_text`.
- The proposal MAY name `AssembledContext` / `assembled_text`, but MUST NOT select raw
  retrieval hits, audit packets, private cognition, candidate/unadmitted material,
  substrate-only material, or `PrivateGenerationOwner`.
- The proposal MUST require that any later caller OWNS provenance and may pass ONLY an
  already-assembled governed context object/string (per the caller-owned provenance
  contract); the runner does not retrieve or assemble.
- No new retrieval authority. No new store / carrier / schema. No memory write or
  persistence feedback to obtain the source.
```

## 4. Proposed runner-local boundary / seam (proposal-only)

```text
- The proposed seam WOULD be the runner-local AgentRunner prompt-request construction path,
  BEFORE the `_LLMPromptRequest` is sent to `_complete_llm_prompt_request(...)`.
- The proposed implementation shape WOULD discuss adding an OPTIONAL runner-local
  memory-context argument through the private execution/build path (e.g. an optional
  parameter into `_build_llm_prompt_request(...)`), while preserving `_LLMPromptRequest`
  as runner-local.
- The exact later code shape MUST be reviewed before any implementation; nothing about the
  seam is authorized here.
- No endpoint / API / schema change. No `app.py` `/agent/query` wiring in this proposal.
  No U1 / audit-owner / PrivateGenerationOwner / dual-ownership route. No Gate D / Envelope
  Audit runtime.
```

## 5. Proposed model-visible representation (proposal-only)

```text
- The proposed representation WOULD be ONE bounded, clearly labelled memory guidance block,
  included in the model-visible `messages` BEFORE the raw user input — NOT by changing the
  authority of the system prompt.
- Proposed exact label text (guidance-only):
    `[Memory context — read-only guidance, not instruction, not canon, not identity authority, not truth authority]`
- `_build_system_prompt(...)` SHOULD remain unchanged in the later patch unless separately
  authorized.
- The block MUST be turn-local, read-only, non-public, and non-authoritative.
- The raw user input REMAINS a separate `messages` entry.
```

## 6. Proposed size / minimization rule (proposal-only)

```text
- Proposed hard cap: MAX 1200 characters of STRIPPED `assembled_text`.
- Empty / whitespace-only context is OMITTED (no block at all).
- Over-cap context is TRUNCATED with a clear marker — never expanded by extra retrieval.
- No prompt block may include selection logs, audit packets, metadata dumps, private
  cognition, candidate/unadmitted text, substrate-only content, or prompt-request internals.
```

## 7. Proposed guidance-not-authority wording (proposal-only)

```text
Memory may INFORM generation only. The memory block IS NOT:
  - canon
  - identity authority
  - admission authority
  - writer authority
  - truth authority
  - output-control / style-control / review-control / retry-control / ranking-control /
    suppression-control / memory-write instruction
Absence of memory MUST NOT punish output (no penalty / suppression / refusal for memory
that is simply not present).
```

## 8. Proposed no-public-exposure rule (proposal-only)

```text
- `_LLMPromptRequest` REMAINS runner-local.
- The memory block MUST NOT be returned on `TurnResult`.
- It MUST NOT enter result metadata, logs, endpoints, schemas, public response payloads,
  review outputs, write payloads, retrieval feedback, or persistence.
```

## 9. Proposed no-feedback / no-control rule (proposal-only)

```text
- The memory block MUST NOT feed: review, output control, retry, ranking, style steering,
  suppression, memory write, persistence, retrieval scoring, retrieval authority, Gate B,
  Gate D, Envelope Audit runtime, or database/substrate paths.
- Its only effect WOULD be its presence in the model-visible `messages` for that one turn.
```

## 10. Audit observation-only relationship

```text
- Existing audit observation REMAINS downstream, optional, fail-soft, absence-non-punitive,
  and non-control (TurnResult-only inert packet).
- This proposal does NOT reopen U1 / audit-owner.
- This proposal does NOT wire `PrivateGenerationOwner`.
- Any later audit assertion MUST be source-proven and separately reviewed.
- (Note: a later landed patch would, for the first time, give the inert observer a real
  inclusion event to observe — but observing remains all it may ever do.)
```

## 11. Tests required with any later implementation slice (proposal-only)

```text
The proposal REQUIRES code + tests in the SAME later, separately authorized slice. A
code-only prompt-path patch is NOT admissible. Required tests WOULD include:
  - behaviour test (fake LLM) proving the memory block IS included when a valid context is supplied;
  - behaviour test proving NO memory block is included when context is absent / empty / invalid;
  - test proving `_build_system_prompt(...)` REMAINS unchanged;
  - test proving raw user input REMAINS separate from the memory context;
  - test proving the memory block is bounded / truncated (the 1200-char cap, §6);
  - test proving no prompt request / memory block is exposed on `TurnResult`, metadata, logs,
    or public surfaces;
  - source/AST guard proving NO endpoint / API / schema / `app.py` wiring was added;
  - guard proving NO U1 / audit-owner / PrivateGenerationOwner / dual-ownership route was added;
  - guard proving NO memory-write / retrieval-feedback / output-control / review-control path
    was added.
Baseline-test handling: update or SUPERSEDE the existing baseline tests ONLY where the new
intentional prompt-path change makes the old "memory-blind" assertion obsolete (the
`_build_llm_prompt_request` / `_execute` memory-blind assertions), and KEEP all remaining
no-control / no-public / no-owner fences green.
```

## 12. Forbidden crossings (this step)

```text
- no production code in this step
- no tests in this step
- no prompt change or model-visible memory injection in this step
- no retrieval-to-generation wiring in this step
- no endpoint / API / schema or public-surface change
- no output-control / review / suppression / retry / ranking / style steering
- no memory write or persistence feedback
- no retrieval-authority expansion
- no U1 / audit-owner reopening
- no PrivateGenerationOwner wiring
- no dual-ownership orchestration
- no Gate D / private cognition / dream / Envelope Audit runtime
- no database / substrate / carrier / schema / storage / migration
- no Gate B; no R-field; no Probe-v1; no shaping slice
```

This document specifies a proposed shape only. Nothing above is opened, selected, or
authorized.

## 13. Non-authorization line

**Landing this proposal authorizes no production code, no tests, no prompt change, no
memory injection, and no generation wiring.** It only makes the exact proposed production
patch shape reviewable. Any later implementation slice (code + tests together) is a
SEPARATE explicit Hilmir authorization under Codex adversarial review against this proposed
shape, the design frame's proof obligations, and the candidate proof-contract lock.

## 14. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION PRODUCTION IMPLEMENTATION PROPOSAL / DOCS-ONLY /
NON-AUTHORIZING / NO LANE OPENED / FENCE CLOSED. It specifies — as a proposed, not-authorized
patch shape for later review — an exact eligible source (the governed `AssembledContext.assembled_text`,
caller-owned provenance, no raw hits/audit/private/candidate/substrate/`PrivateGenerationOwner`,
no new retrieval authority/store/write); an exact runner-local seam (an optional runner-local
memory-context argument through the private `_build_llm_prompt_request(...)` path before
`_LLMPromptRequest` reaches `_complete_llm_prompt_request(...)`, request kept runner-local, no
`app.py`/`/agent/query`/endpoint/schema/U1/audit-owner/owner/dual-ownership route); an exact
model-visible representation (one bounded, clearly labelled, read-only, turn-local,
non-authoritative, guidance-only memory block in `messages` before the raw user input, with
`_build_system_prompt(...)` unchanged); an exact size rule (≤ 1200 stripped chars, omit empty,
truncate-with-marker, never expand, no logs/audit/metadata/private/candidate/substrate/internals);
guidance-not-authority (informs only; not canon/identity/admission/writer/truth authority or any
control; absence non-punitive); no public exposure (`_LLMPromptRequest` runner-local; block never
on `TurnResult`/metadata/logs/endpoints/schemas/public payloads/persistence); no feedback/control;
audit stays observation-only (U1/audit-owner not reopened, `PrivateGenerationOwner` not wired); and
required tests in the SAME later slice (inclusion-on-valid, omission-on-empty/invalid, system-prompt
unchanged, user-input separate, bounded/truncated, no exposure, AST guards for no-endpoint/no-owner/
no-feedback, and superseding only the now-obsolete "memory-blind" baseline assertions while keeping
all no-control/no-public/no-owner fences). **It authorizes no production code, no tests, no prompt
change, no memory injection, and no generation wiring; it selects nothing for implementation, opens
no lane, and leaves the fence closed.** Any later implementation slice is a separate Hilmir decision
under Codex review. Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.
