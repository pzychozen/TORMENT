# TORMENT — Non-Spine LLM Character Operator Anthropic Smoke Receipt v0.1

## Status

**Docs-only / sanitized evidence receipt / NON-AUTHORIZING / no code / no tests / no
production change.** This file records that ONE intentional, operator-run real-provider
smoke of the gated **manual character-shaped** non-Spine path completed and returned text.
It is a **sanitized evidence receipt — not a transcript or output artifact** — and it
authorizes nothing and wires nothing.

## Run

- **Run date:** 2026-06-29 (operator-run, local CMD session).
- **Harness:** `tests/manual/non_spine_llm_character_operator_harness.py` — the manual
  character-shaped operator harness (operator-supplied primitive character fields only;
  the CLI refuses the real path under pytest).
- **Invocation shape (toy inputs redacted):**

  ```
  python -m tests.manual.non_spine_llm_character_operator_harness --real-anthropic ...
  ```

  The character / user inputs were synthetic toy values and are **not** recorded here
  beyond this generic module-invocation shape.
- **API key:** `ANTHROPIC_API_KEY` was **entered manually in the local CMD session**. There
  was **no `.env` auto-loading**. The key value was never printed, stored, echoed, or
  characterized, and is **not** recorded here.
- **Existing env gate / model / timeout used** (already enforced inside the adapter):
  - `TORMENT_NON_SPINE_LLM_REAL_PROVIDER=1` (gate)
  - `TORMENT_NON_SPINE_ANTHROPIC_MODEL=claude-sonnet-4-6` (model name recorded)
  - `TORMENT_NON_SPINE_PROVIDER_TIMEOUT_SECONDS=30`

## Observed result

- **Non-empty terminal output was observed** — in the terminal only. **What** the output
  said is deliberately **not** recorded.

## What was NOT recorded / NOT created

- **No provider response text** recorded.
- **No prompt transcript** recorded (only the generic invocation shape above).
- **No API key / secret** recorded or characterized.
- **No raw provider payload, request id, trace id, or headers** recorded.
- **No stdout / stderr contents** recorded.
- **No transcript, log, or output file** created or referenced by the smoke or this receipt.

## Scope / non-claims

- **No repo file changed during the smoke** — `git status --short` was empty afterward.
- **No app / server / MCP endpoint** was used.
- **No live wiring.**
- **No memory write.**
- **No production character integration** is claimed; no app / server / MCP integration is
  claimed; no memory integration is claimed; **no identity / canon behavior** is claimed.
- **Cleanup completed** after the run.

## Validation after cleanup

```
python -m unittest tests.test_non_spine_llm_character_operator_harness tests.test_non_spine_llm_anthropic_provider_harness tests.test_non_spine_llm_real_provider_adapter tests.test_non_spine_llm_runtime_skeleton tests.test_non_spine_llm_callable_adapter_harness tests.test_spine_cognition_memory_context_characterization_lock
```

→ **94 tests OK.**

## What this proves (and does not)

This receipt proves **only** that a manual character-shaped non-Spine provider path can
return text under explicit operator setup. It is a **sanitized evidence receipt, not a
transcript / output artifact, and not authorization for live wiring.** Any further step —
a further real-provider smoke, a source-only integration review, any live app / MCP wiring
or design, any character-production path, or any memory path — remains a **SEPARATE,
separately gated** decision under Hilmir + Codex review.

- Meaningful harness edge: `92e9554`.
- This receipt's docs edge: the new docs commit for this slice.
