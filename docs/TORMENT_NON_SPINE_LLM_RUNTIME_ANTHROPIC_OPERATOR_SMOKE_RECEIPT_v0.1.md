# TORMENT — Non-Spine LLM Runtime Anthropic Operator Smoke Receipt v0.1

## Status

**Docs-only receipt / NON-AUTHORIZING / no code / no tests / no runtime change.** This file
records that ONE intentional, operator-run real-provider smoke of the gated manual Anthropic
non-Spine path completed successfully. It deliberately stores **no** provider response text,
**no** prompt transcript beyond the generic command shape, **no** API key or secret, and
**no** raw provider payload, request id, or trace. It authorizes nothing and wires nothing.

## Run

- **Run date:** 2026-06-29 (operator-run).
- **Harness:** `tests/manual/non_spine_llm_anthropic_provider_harness.py` (the gated manual
  Anthropic operator harness; CLI refuses under pytest).
- **Command shape (secrets and toy prompt redacted):**

  ```
  conda run -n torment python tests\manual\non_spine_llm_anthropic_provider_harness.py --user-input "<toy prompt>"
  ```

  The `--user-input` value was a synthetic, non-memory-bearing toy prompt; it is **not**
  recorded here beyond this generic shape.
- **Env names used** (values not recorded):
  - `TORMENT_NON_SPINE_LLM_REAL_PROVIDER=1` (gate)
  - `ANTHROPIC_API_KEY` — loaded from a local repo-root `.env`; **value not recorded**
  - `TORMENT_NON_SPINE_ANTHROPIC_MODEL=claude-sonnet-4-6` (model name recorded)
  - `TORMENT_NON_SPINE_PROVIDER_TIMEOUT_SECONDS=30`
  - `PYTHONPATH` set to the repo root for script import

## Observed result

- **Successful command completion** — no conda/script error observed (exit-success).
- **Real provider path reached** — yes, through the gated manual Anthropic harness
  (`AnthropicNonSpineLLMProviderAdapter`), after its gate / key / model / timeout validation.
- **Non-empty provider text observed** — yes (seen in the terminal only).

## Confirmations (what was NOT recorded / NOT created)

- **No provider response text recorded** — output was observed in the terminal only.
- **No prompt transcript recorded** beyond the generic command shape above.
- **No API key / secret recorded** — the key value was never printed, stored, or echoed.
- **No raw provider payload, request id, or raw error trace recorded.**
- **No transcript, log, or output file created** by the smoke or this receipt.
- **Environment variables were cleared** after the smoke.

## Validation after cleanup

After clearing the env vars, the focused suite was re-run:

```
conda run -n torment python -m unittest tests.test_non_spine_llm_anthropic_provider_harness tests.test_non_spine_llm_real_provider_adapter tests.test_non_spine_llm_runtime_skeleton tests.test_non_spine_llm_callable_adapter_harness tests.test_spine_cognition_memory_context_characterization_lock
```

→ **Ran 82 tests, OK.**

## Scope / non-authorization

- **No repo files were changed by the smoke** before this receipt; the only changes in this
  slice are this receipt doc and an optional `docs/PROJECT_ORIENTATION_MAP.md` §0 pointer.
- **No code, no tests, no runtime behavior change.**
- **No live wiring; no endpoint/MCP/API/schema; no startup/autonomy/scheduler; no
  retrieval/assembly; no memory writes; no persistence/logging/transcripts; no
  model-output-to-memory feedback; no database/substrate; no dream/private-cognition
  runtime; no AgentRunner/Terrain B; no output-control paths.**

This receipt records a one-shot operator observation only. Any further step (e.g. live
app/MCP wiring) remains a SEPARATE, separately-authorized gate.
