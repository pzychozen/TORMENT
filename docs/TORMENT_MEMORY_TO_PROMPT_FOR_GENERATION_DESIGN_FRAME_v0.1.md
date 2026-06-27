# TORMENT — Memory-to-Prompt-for-Generation Design Frame v0.1

## 1. Status

**Design frame. Docs-only / NON-AUTHORIZING / no lane opened.** Hilmir authorized
**only this design frame** (the "later design frame" outcome of the decision frame
`docs/TORMENT_MEMORY_TO_PROMPT_FOR_GENERATION_ARCHITECTURE_DECISION_FRAME_v0.1.md`).
It defines **what a future memory-to-prompt-for-generation design would have to prove
before any tests or code** — it is a requirements / proof frame, **not** a mechanism
selection. It makes **no prompt change, no model-visible memory injection, and no
retrieval-to-generation wiring**, and writes no code or tests.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `8bd1746` (repo edge). Subordinate to: the decision frame (above), the
pre-database cognition ceiling frame, the caller-owned same-turn provenance contract
(`docs/TORMENT_AUDIT_CALLER_OWNED_SAME_TURN_PROVENANCE_CONTRACT_v0.1.md`), and the
PW-1…PW-8 pre-wiring guard. Where this frame and any parent contract/guard differ, the
contract/guard wins.

## 2. Meaning

```text
"Memory-to-prompt-for-generation" MEANS:
  the authoritative AgentRunner generation boundary may, in a FUTURE separately
  authorized design, receive SOME retrieved/assembled memory as model-visible context.

It DOES NOT mean:
  - that /retrieve output, audit-packet content, debug text, or sidecar observation
    automatically becomes prompt-visible;
  - that any memory becomes model-visible now (it does not; §4 records the memory-blind
    boundary);
  - that a specific mechanism, source, injection point, or prompt format is chosen
    (none is — this frame selects nothing).
```

## 3. Eligible memory source (constraints only — no source selected)

A future design's memory source must satisfy these eligibility constraints. **This frame
names no source.**

```text
ELIGIBLE source must be:
  - EXPLICIT (named, not implicit/ambient);
  - BOUNDED (finite, minimizable — see §6);
  - already retrievable/assembled through EXISTING GOVERNED READ PATHS;
  - READ-ONLY for the turn (the design reads it; it writes nothing back);
  - NOT private-cognition / candidate / unadmitted / substrate-only material.

A future design must NOT:
  - create new retrieval authority, new retrieval surfaces, or expanded retrieval scope;
  - perform any memory write or persistence change to obtain the source;
  - promote, admit, canonize, or re-rank memory as a side effect of becoming source.
```

## 4. Authoritative boundary (named; injection point / format NOT selected)

The boundary a future design must speak to is the **AgentRunner model call**, today:

```text
system_prompt = self._build_system_prompt(frame, mode)
              = "You are agent {agent_id} operating in mode {mode}."   (v0.1 minimal; memory-blind)
messages      = [{"role": "user", "content": frame.raw_input}]
→ assembled into the runner-local _LLMPromptRequest, sent to
  self._complete_llm_prompt_request(req)  (the single model-call boundary).
```

```text
- Any future design MUST name EXACTLY where memory would become model-visible
  (which field of the request, at which point, for which turn).
- This frame selects NO injection point and NO prompt format. It records only that the
  boundary is the _LLMPromptRequest → _complete_llm_prompt_request(...) call, and that
  today nothing memory-bearing crosses it.
- The request must remain RUNNER-LOCAL (a future design may not expose it; see §5/§6).
```

## 5. Forbidden crossings

```text
- no endpoint / API / schema
- no prompt mutation in this frame
- no output-control / review / suppression / retry / ranking / style steering
- no audit-as-control
- no U1 / audit-owner reopening
- no PrivateGenerationOwner wiring
- no Gate D / private cognition / dream / Envelope Audit runtime
- no database / substrate / carrier / schema / storage / migration
- no Gate B; no R-field; no Probe-v1; no shaping slice
- no code; no tests
```

This frame records requirements only. Nothing above is opened, designed, selected, or
authorized.

## 6. Proof obligations before implementation

A future proposal, **if ever authorized**, must establish all of the following **before
any code** — each a bar, not a chosen mechanism:

```text
- EXACT MEMORY SOURCE (which governed read path; §3-eligible).
- EXACT GENERATION BOUNDARY (which field of the _LLMPromptRequest; which turn).
- EXACT MODEL-VISIBLE REPRESENTATION (how the memory is rendered into the request).
- BOUNDED SIZE / MINIMIZATION (capped items / length; smallest sufficient projection).
- NO PROMPT-REQUEST EXPOSURE (request stays runner-local: never on TurnResult /
  ExecutionOutcome / metadata / logs / debug / endpoint / schema / persistence / self).
- NO PUBLIC SURFACE CHANGE (no endpoint / API / schema delta).
- NO MEMORY-WRITE FEEDBACK (becoming prompt-visible writes/persists/promotes nothing).
- NO RETRIEVAL-AUTHORITY EXPANSION (uses existing governed reads only; §3).
- NO OUTPUT / REVIEW / CONTROL COUPLING (the change drives no output/review/retry/
  ranking/style/suppression behavior).
- TESTS-FIRST / SOURCE GUARDS required before code (characterization + AST guards land
  before any implementation), preserving the caller-owned provenance contract and PW-1…PW-8.
```

## 7. Guidance not authority

```text
- Memory may INFORM generation, but must NOT become canon, identity authority, admission
  authority, writer authority, or truth authority merely by being prompt-visible.
- Unsupported memory ABSENCE must not punish output (no penalty / suppression / refusal
  for memory that is simply not present).
- Retrieved memory remains CONTESTABLE / LOW-AUTHORITY unless separately governed; being
  in the prompt confers no elevation of authority.
```

## 8. Audit observation

```text
- Audit MAY observe whether selected/eligible memory was included in the model-visible
  context (the inert observation seam already exists for this shape).
- The audit packet remains OPTIONAL, DOWNSTREAM, INERT, FAIL-SOFT, ABSENCE-NON-PUNITIVE,
  and NON-CONTROL (TurnResult-only; drives no branch).
- Audit CANNOT steer prompt, output, review, retry, ranking, style, retrieval, write, or
  persistence. (Note: a real memory-inclusion event would, for the first time, give that
  inert auditor something to observe — but observing is all it may ever do.)
```

## 9. Substrate independence

```text
- This can remain SUBSTRATE-INDEPENDENT only if a future design uses EXISTING read /
  assembly surfaces and introduces NO new carrier / store / schema / persistence.
- Any design requiring a NEW carrier or a durable candidate representation EXITS this
  frame and needs SEPARATE substrate authorization (Stage B / database decision), which
  this frame does not grant.
```

## Non-authorization line

**Landing this frame authorizes no tests, no code, no prompt change, no memory injection,
and no generation wiring.** It only defines what a future memory-to-prompt design must
prove before any later proposal. Any next step (a tests-only characterization, or an
implementation proposal that touches the prompt) is a **separate** explicit Hilmir
authorization under Codex review, and must satisfy §6.

## Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION DESIGN / DOCS-ONLY / NON-AUTHORIZING / NO LANE
OPENED. It defines what a future design must prove before any tests or code: the meaning
(the authoritative `AgentRunner` generation boundary may, in a future authorized design,
receive some governed retrieved/assembled memory as model-visible context — **not**
`/retrieve` output / audit packet / debug / sidecar becoming prompt-visible automatically);
eligible-source constraints (explicit, bounded, governed-read, read-only, not
private/candidate/unadmitted/substrate-only; no new retrieval authority / memory write /
persistence); the named boundary (`_build_system_prompt(frame, mode)` minimal prompt +
`frame.raw_input` messages → runner-local `_LLMPromptRequest` → `_complete_llm_prompt_request(...)`;
memory-blind today; **no injection point or format selected**); proof obligations before
implementation (exact source / boundary / representation; bounded minimization; no
prompt-request exposure; no public-surface change; no memory-write feedback; no
retrieval-authority expansion; no output/review/control coupling; tests-first + source
guards; provenance contract + PW-1…PW-8 preserved); guidance-not-authority (memory informs
but does not become canon/identity/admission/writer/truth authority; absence non-punitive;
memory stays contestable/low-authority); audit-observation-only (optional, downstream,
inert, fail-soft, absence-non-punitive, non-control); and substrate-independence (existing
read/assembly surfaces only — any new carrier exits this frame and needs separate substrate
authorization). **It selects no mechanism, source, injection point, prompt format, owner,
endpoint, runtime, schema, or carrier, makes no prompt change or memory injection, opens no
lane, and authorizes no code or tests.** Any next step is a separate Hilmir decision under
Codex review. Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.
