# TORMENT — Memory-to-Prompt C-D Operator Orchestration Real-Provider Smoke Receipt v0.1

## Status

**Docs-only / sanitized evidence receipt / NON-AUTHORIZING / no code / no tests / no
production change.** This file records that **exactly one** intentional, operator-run
**real-provider** smoke of the gated **manual C-D operator-orchestration** path completed and
returned non-empty text. It is a **sanitized evidence receipt — not a transcript or output
artifact** — and it authorizes nothing and wires nothing.

## Run

- **Run mode:** **REAL provider (Anthropic), explicit one-shot**, operator-run, local
  session. Reached only via the harness's explicit real path (the `--real-anthropic` flag)
  **plus** the existing env gate; the CLI refuses the real path under pytest.
- **Harness:** `tests/manual/memory_to_prompt_c_d_operator_orchestration_harness.py` — the
  manual C-D operator-orchestration harness (default path is fake / no-provider; the real
  path reuses only the existing env-gated adapter).
- **Invocation shape (minimal smoke prompt redacted):**

  ```
  python -m tests.manual.memory_to_prompt_c_d_operator_orchestration_harness ...
  ```

  **One minimal smoke prompt** was used; its content is **not** recorded here beyond this
  generic module-invocation shape.
- **Existing env gate / model / timeout** (validated inside the adapter, fail-closed):
  - `TORMENT_NON_SPINE_LLM_REAL_PROVIDER=1` (gate — explicitly set)
  - `TORMENT_NON_SPINE_ANTHROPIC_MODEL=claude-sonnet-4-6` (model name recorded)
  - `TORMENT_NON_SPINE_PROVIDER_TIMEOUT_SECONDS=30`
- **API key:** supplied in the operator's local environment only. The value was **never**
  recorded, printed, echoed, or characterized, and is **not** present in this receipt.
- **Anthropic SDK:** had to be **installed in the active Python environment** before the
  smoke succeeded (the SDK is optional and lazily imported; it is not pinned in repo
  requirements). This was a **local-environment install only** — **no repo file changed**
  (`git status --short` was clean afterward).

## Observed result

- **Non-empty terminal output was observed** — in the terminal only. **What** the output
  said is deliberately **not** recorded.

## What was NOT recorded / NOT created

- **No provider response text** recorded.
- **No prompt transcript** recorded (only the generic invocation shape above).
- **No API key / secret** recorded or characterized.
- **No raw provider payload, request id, trace id, or headers** recorded.
- **No stdout / stderr contents** recorded.
- **No screenshot** taken or referenced.
- **No transcript, log, or output file** created or referenced by the smoke or this receipt.

## Scope / non-claims

- **No repo file changed during the smoke** — `git status --short` was clean afterward.
- **No app / server / MCP / endpoint** was used; **no endpoint / MCP / API / schema** surface.
- **No live wiring; no production integration** is claimed.
- **No AgentRunner / Terrain B wiring.**
- **No retrieval / assembly behavior change.**
- **No memory write; no model-output-to-memory feedback.**
- **No automatic provider call** — the single real call happened **only** via the explicit
  one-shot operator invocation (explicit flag + env gate); nothing calls the provider on its
  own.
- **Cleanup completed** after the run.

## What this proves (and does not)

This receipt proves **only** that the manual C-D operator-orchestration path can return
non-empty text under explicit operator setup (gate + model + timeout + a locally-installed
SDK + the explicit real-path flag). It is a **sanitized evidence receipt, not a transcript /
output artifact.** It does **not** authorize any further real-provider smoke, any production
integration, any memory writes, or any provider expansion. Every further step — another
real-provider smoke, a source-only integration review, any live app / MCP wiring or design,
any AgentRunner / Terrain B path, or any memory path — remains a **SEPARATE, separately
gated** decision under Hilmir + Codex review.

- Harness edge: `b7a8a0a` (test(runtime): add manual operator orchestration harness).
- Prior fake-smoke receipt edge: `02f2b17` (docs(runtime): record operator orchestration fake smoke).
- This receipt's docs edge: the new docs commit for this slice.
