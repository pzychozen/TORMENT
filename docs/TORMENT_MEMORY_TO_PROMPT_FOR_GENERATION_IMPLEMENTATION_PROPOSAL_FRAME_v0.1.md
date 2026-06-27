# TORMENT — Memory-to-Prompt-for-Generation Implementation-Proposal Frame v0.1

## 1. Status

**Implementation-proposal frame. Docs-only / NON-AUTHORIZING / no lane opened.** Hilmir
authorized **only this proposal frame**. It NAMES one *candidate* implementation shape
for later adversarial (Codex/Hilmir) review; it **selects nothing** and **authorizes
nothing**. It makes no prompt change, no model-visible memory injection, no
retrieval-to-generation wiring, no endpoint/API/schema change, and writes no code or
tests. This is **not** "implement next" and **not** a patch.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `770278e` (repo edge). Subordinate to, and may not contradict: the
memory-to-prompt **decision frame**
(`docs/TORMENT_MEMORY_TO_PROMPT_FOR_GENERATION_ARCHITECTURE_DECISION_FRAME_v0.1.md`), the
**design frame**
(`docs/TORMENT_MEMORY_TO_PROMPT_FOR_GENERATION_DESIGN_FRAME_v0.1.md`), the pre-database
cognition **ceiling frame**, the source **baseline lock**
(`tests/test_memory_to_prompt_generation_boundary_characterization.py`), the
caller-owned same-turn provenance contract, and the PW-1…PW-8 pre-wiring guard. Where
this frame and any parent contract/guard differ, the contract/guard wins.

## 2. Current baseline (source-verified, locked)

```text
- The authoritative AgentRunner generation is MEMORY-BLIND today.
- `_build_llm_prompt_request(...)` uses `_build_system_prompt(frame, mode)` (the v0.1
  minimal prompt) and `frame.raw_input`.
- `_execute(...)` calls `_build_llm_prompt_request(...)` and routes the request through
  `_complete_llm_prompt_request(...)`.
- `_complete_llm_prompt_request(...)` calls `self.llm_client.complete(...)` with
  `req.system_prompt`, `req.messages`, and `req.tools`.
- No live authoritative AgentRunner / app endpoint path wires retrieved/assembled memory
  into AgentRunner generation.
- `PrivateGenerationOwner` / `audit_private_generation_owner.py` remains EXCLUDED —
  unwired / test-called — and is NOT the authoritative AgentRunner path.
```

A future proposal that ever changed this baseline would be the first thing to touch the
prompt path; this frame does not. The named candidates below describe *what such a
proposal would be allowed to look like*, not a chosen design.

## 3. Candidate source (named, not selected)

```text
- The candidate source WOULD be existing governed read/assembly output ONLY.
- It MUST prove it is: explicit; bounded; read-only for the turn; already
  retrievable/assembled through EXISTING governed read paths; and NOT private-cognition /
  candidate / unadmitted / substrate-only material.
- A future proposal MUST NOT choose a new carrier / store / schema.
- A future proposal MUST NOT expand retrieval authority or retrieval scope.
- A future proposal MUST NOT use U1 / audit-owner / PrivateGenerationOwner as the source.
```

No source is selected here.

## 4. Candidate boundary (named, not selected)

```text
- The candidate boundary WOULD be the RUNNER-LOCAL AgentRunner prompt-request construction
  path:  `_build_llm_prompt_request(...)` → `_LLMPromptRequest` → `_complete_llm_prompt_request(...)`.
- A future proposal WOULD have to identify a NARROW private runner-local seam BEFORE the
  `_LLMPromptRequest` is sent to `_complete_llm_prompt_request(...)`.
- This frame does NOT select an injection point and does NOT authorize one.
- A future proposal MUST NOT modify endpoint / API / schema.
- A future proposal MUST NOT route through audit-owner, U1, PrivateGenerationOwner, or
  dual-ownership orchestration.
```

No boundary/injection point is selected here.

## 5. Candidate representation (named, not selected)

```text
- The candidate representation WOULD be a bounded, clearly labeled model-visible memory
  CONTEXT BLOCK.
- It MUST prove it is: minimised; turn-local; read-only; non-authoritative; and explicitly
  GUIDANCE-ONLY.
- It MUST NOT be canon, identity authority, admission authority, writer authority, truth
  authority, or an output-control instruction.
- It MUST NOT expose prompt requests publicly.
- It MUST NOT include private cognition, candidate / unadmitted content, substrate-only
  content, or audit-packet content.
```

No representation/format is selected here.

## 6. Proof obligations carried forward

A future proposal, **if ever authorized**, MUST prove all of the following (carried from
the design frame, plus the corrected baseline distinction) — each a bar, not a chosen
mechanism:

```text
- Exact memory source.
- Exact generation boundary.
- Exact model-visible representation.
- Bounded size / minimization.
- No prompt-request exposure.
- No public-surface change.
- No memory-write feedback.
- No retrieval-authority expansion.
- No output / review / control coupling.
- Guidance-not-authority (memory informs; it does not become canon / identity / admission /
  writer / truth authority by being prompt-visible; absence is non-punitive; memory stays
  contestable / low-authority).
- Audit observation-only (optional, downstream, inert, fail-soft, absence-non-punitive,
  non-control).
- Runner-local `_LLMPromptRequest` (never exposed on TurnResult / ExecutionOutcome /
  metadata / logs / endpoint / schema / persistence / self).
- Corrected baseline distinction: `PrivateGenerationOwner` is excluded / unwired /
  test-called and is NOT the authoritative AgentRunner path.
- Caller-owned provenance contract + PW-1…PW-8 preserved.
```

## 7. Tests-first requirement before any production code

```text
- Before ANY production code, a SEPARATELY AUTHORIZED tests-first step WOULD be required.
- This frame MAY describe what such tests would need to prove (e.g. the memory block is
  bounded/minimised; it appears only in the runner-local request and nowhere public; it
  is guidance-only and drives no output/review/control; the request stays runner-local;
  the §6 obligations hold) — but it does NOT author or authorize those tests.
- This frame does NOT authorize implementation. The tests-first step and any production
  code are each separate Hilmir decisions under Codex review.
```

## 8. Forbidden crossings

```text
- no prompt change or model-visible memory injection in this artifact
- no retrieval-to-generation wiring
- no endpoint / API / schema change
- no output-control / review / suppression / retry / ranking / style steering
- no memory write or persistence feedback
- no retrieval-authority expansion
- no U1 / audit-owner reopening
- no PrivateGenerationOwner wiring
- no dual-ownership orchestration
- no Gate D / private cognition / dream / Envelope Audit runtime
- no database / substrate / carrier / schema / storage / migration
- no Gate B; no R-field; no Probe-v1; no shaping slice
- no code; no tests
```

This frame names candidates only. Nothing above is opened, selected, or authorized.

## 9. Non-authorization line

**Landing this frame authorizes no tests, no code, no prompt change, no memory injection,
and no generation wiring.** It only names one candidate implementation shape (candidate
source / candidate boundary / candidate representation) for later Codex/Hilmir review. No
candidate is selected; the fence remains closed.

## 10. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION IMPLEMENTATION-PROPOSAL / DOCS-ONLY /
NON-AUTHORIZING / NO LANE OPENED. It names ONE candidate implementation shape for later
adversarial review against the design frame's proof bar: a **candidate source** (existing
governed read/assembly output only — explicit, bounded, read-only, governed-read, not
private/candidate/unadmitted/substrate-only; no new carrier, no retrieval-authority
expansion, not U1/audit-owner/PrivateGenerationOwner); a **candidate boundary** (the
runner-local `_build_llm_prompt_request(...)` → `_LLMPromptRequest` →
`_complete_llm_prompt_request(...)` path; a future proposal would have to identify a narrow
private runner-local seam before the request is sent — no injection point selected, no
endpoint/schema, no audit-owner/U1/dual-ownership routing); and a **candidate
representation** (a bounded, clearly labeled, minimised, turn-local, read-only,
non-authoritative, guidance-only model-visible memory context block — not canon/identity/
admission/writer/truth authority, no public prompt exposure, no private/candidate/
substrate/audit-packet content). It carries the proof obligations forward (exact source /
boundary / representation; bounded minimization; no prompt-request exposure; no
public-surface change; no memory-write feedback; no retrieval-authority expansion; no
output/review/control coupling; guidance-not-authority; audit observation-only;
runner-local `_LLMPromptRequest`; the corrected `PrivateGenerationOwner`-excluded baseline;
provenance contract + PW-1…PW-8), and REQUIRES a separately authorized tests-first step
before any production code. **It selects no candidate, authorizes no tests, no code, no
prompt change, no memory injection, and no generation wiring, opens no lane, and lifts no
fence.** Any next step is a separate Hilmir decision under Codex review. Guidance not
control; audit observes authority and does not become authority; nothing rewrites identity
/ canon / seed / soul.
