# TORMENT — Non-Spine LLM Runtime Real-Provider Readiness Review v0.1

## 1. Status / verdict

**Docs-only / SOURCE-ONLY REVIEW / NON-AUTHORIZING / no code / no tests / implementation
HOLD.** This review reads source and records a paper verdict. It writes no code, adds no
tests, imports no SDK, reads no env/secret, makes no network call, and changes no runtime
behavior or public surface.

**Verdict: Option 1 — a later real-provider adapter is ADMISSIBLE for the separate
non-Spine runtime, as a future, separately-gated step, under the exact constraints in §7-§11.**
It is admissible because the readiness work is already in place and well-fenced (the
provider-adapter contracts, the fake default path, and the callable manual helper), and
because the repository already contains two accepted precedents for reaching a real
provider in a manual/operator-only way (§5). Nothing here authorizes building it; the
default fake path and the callable manual helper are preserved unchanged.

## 2. Scope and source edge

```text
Runtime source edge reviewed: 9ff8cc2 (feat(runtime): add non-spine callable provider
manual helper). Orientation §0 closure of that slice: 45d1ed5.

Files read:
- torment_service/non_spine_llm_runtime.py            (446 lines)
- tests/test_non_spine_llm_runtime_skeleton.py
- tests/manual/non_spine_llm_callable_adapter_harness.py
- tests/test_non_spine_llm_callable_adapter_harness.py
- tests/manual/memory_to_prompt_provider_llm_harness.py   (existing provider precedent)
- tests/run_external_inference_smoke.py                    (existing operator precedent)
- torment_service/app.py · torment_service/spine.py · torment_service/mcp_server.py
- cognition/ · roles/
- requirements.txt
- docs/PROJECT_ORIENTATION_MAP.md §0 closure notes for this lane
```

## 3. Current implemented boundary (source-grounded at `9ff8cc2`)

```text
torment_service/non_spine_llm_runtime.py is stdlib-only (imports: __future__,
dataclasses, typing) and INERT at import. It provides, in layers:

  - NonSpineLLMMemoryContext        bounded, read-only memory-context package;
  - NonSpineLLMRuntimeRequest       primitive-only input;
  - NonSpineLLMPromptRequest        prompt-request package (carries memory context);
  - NonSpineLLMProviderConfig       fake / network-disabled defaults
                                    (provider_name="fake", network_enabled=False);
  - NonSpineLLMProviderRequest      carries prompt_request + config;
  - NonSpineLLMProviderResult       primitive result;
  - NonSpineLLMProviderAdapter      provider BOUNDARY base; generate() raises
                                    NotImplementedError (no provider);
  - FakeNonSpineLLMProviderAdapter  deterministic in-memory fake; provider_called=False,
                                    is_fake=True; no network/SDK/env/secret;
  - CallableNonSpineLLMProviderAdapter  operator-injected callable; the one adapter where
                                    provider_called=True / is_fake=False MAY hold; never
                                    instantiated on the default path;
  - NonSpineLLMCompletionAdapter / FakeNonSpineLLMCompletionAdapter  the only default
                                    completion path; delegates to the fake provider adapter;
  - NonSpineLLMRuntime              owner; default adapter is the fake completion adapter;
                                    run(...) stays fake / no-provider;
  - run_non_spine_callable_provider_manual(...)  production-internal MANUAL helper that
                                    builds the callable stack; defined but called by nothing
                                    in production.

The provider seam (NonSpineLLMProviderAdapter.generate) already exists; the only two
concrete adapters are the fake (default) and the callable (manual, operator-injected). A
real adapter would be a THIRD subclass behind the same seam.
```

## 4. Live-surface exclusion findings

```text
- torment_service/app.py, torment_service/spine.py, torment_service/mcp_server.py, and
  every module under cognition/ and roles/ reference `non_spine_llm_runtime` NOWHERE
  (test-guarded by tests/test_non_spine_llm_runtime_skeleton.py::TestNoLiveWiring and the
  harness test's import allowlist). So neither the runtime, the callable adapter, nor the
  manual helper is reachable from any endpoint, the Spine, the MCP surface, or the
  deterministic cognition/role path.
- The deterministic Spine/cognition path remains model-boundary-free and test-locked
  (tests/test_spine_cognition_memory_context_characterization_lock.py). A non-Spine real
  adapter does not touch it.
- The default NonSpineLLMRuntime() path is fake (provider_called=False / is_fake=True),
  proven by the skeleton tests; the callable path is reached only via an operator-injected
  callable, proven by fake/spy-callable tests.
```

## 5. Existing manual-provider precedents (the accepted shape)

```text
The repo already reaches a real provider TWICE, both manual/operator-only and both fenced
exactly the way a non-Spine real adapter must be:

(a) tests/manual/memory_to_prompt_provider_llm_harness.py
    - DEFAULT is fake dry-run; the provider package is NEVER imported by default.
    - A real call happens ONLY when TORMENT_MEMORY_TO_PROMPT_PROVIDER_DEMO=1.
    - The provider SDK is imported LAZILY inside __init__ on the gated path only
      (`import anthropic  # lazy`); key/model read ONLY from local env
      (ANTHROPIC_API_KEY / CLAUDE_MODEL), with explicit errors when unset.
    - Automated tests NEVER set the gate -> never touch a provider.
    - Nothing is written to disk (no transcript, no output file); imported by no
      production module; the call list stores only safe metadata.

(b) tests/run_external_inference_smoke.py
    - OPERATOR-RUN script, not a pytest test: the `run_*` prefix keeps it out of pytest
      discovery AND it defensively refuses to run if pytest is in sys.modules.
    - One CLI invocation makes ONE provider call; SDK imported LAZILY inside the call
      (`import anthropic`); keys read from `.env` / env (ANTHROPIC_API_KEY /
      OPENROUTER_API_KEY); explicit timeout; distinct exit codes (0 ok; 2 on
      timeout/empty/too-long/pytest-detected/unknown-provider).
    - The only write path is the sanctioned `POST /tool/ingest` (Spine ->
      ProvenanceV1.for_tool_result), used ONLY with an explicit --ingest flag; it
      introduces no new write path and never constructs a fabric in-process.

requirements.txt keeps ALL provider SDKs (anthropic, openai, sentence-transformers,
ollama) COMMENTED-OUT / optional — none is a hard dependency.

These precedents are the template: env-gated, lazy import, fake default, tests-never-touch,
no persistence, not production-wired.
```

## 6. Real-provider risk table

```text
RISK                              | CONSTRAINT THAT MITIGATES IT (future obligation)
----------------------------------+--------------------------------------------------------
SDK becomes a hard dependency     | provider SDK stays optional/commented in requirements;
                                  | import is lazy, inside the gated adapter path only.
Module-import side effects        | no SDK/env/network at import; adapter inert until called.
Default path contaminated         | default stays FakeNonSpineLLMCompletionAdapter ->
                                  | FakeNonSpineLLMProviderAdapter (provider_called=False);
                                  | real adapter never instantiated by NonSpineLLMRuntime()
                                  | default or any live surface.
Automated tests hit a provider    | gate unset in tests; tests use fake/spy only; a guard
   (cost/flakiness/secrets)       | asserts the real adapter is never reached unsgated.
Secret leakage                    | key/model read only from named env vars when gated;
                                  | never logged, never stored, never echoed into results.
Network egress / hangs            | explicit timeout; fail-closed on timeout/error/empty.
Model output -> memory feedback   | adapter returns a result object only; it performs NO
                                  | memory write/ingest; any later ingest is the separate
                                  | sanctioned /tool/ingest operator path, not this adapter.
Hidden persistence/transcript     | no transcript, no output file, no prompt/response log.
Live-surface wiring               | no app/spine/mcp/cognition/roles import or call; no
                                  | endpoint/MCP/startup/scheduler/autonomy.
Output-control creep              | no review/suppression/retry/ranking/style steering;
                                  | the adapter sends the runner-built request as-is.
```

## 7. Required future adapter shape (named on paper; NOT implemented)

```text
A future real adapter would be a THIRD subclass behind the existing seam, e.g.:

  class <RealName>NonSpineLLMProviderAdapter(NonSpineLLMProviderAdapter):
      def __init__(self, *, config: NonSpineLLMProviderConfig, <explicit creds source>):
          # validate config; do NOT import the SDK here unless gated; store no secret
          ...
      def generate(self, request: NonSpineLLMProviderRequest) -> NonSpineLLMProviderResult:
          # lazy-import SDK; apply timeout; call provider; map response ->
          # NonSpineLLMProviderResult(is_fake=False, provider_called=True, ...);
          # fail closed on error
          ...

Owner / constructor obligations (proof obligation 1):
  - It subclasses NonSpineLLMProviderAdapter and is constructed explicitly by an operator/
    manual caller (mirroring CallableNonSpineLLMProviderAdapter), NEVER by
    NonSpineLLMRuntime.__init__ and NEVER by FakeNonSpineLLMCompletionAdapter's default.
  - The constructor takes an explicit NonSpineLLMProviderConfig (provider_name/model_name)
    and an explicit credentials source; it stores no secret on the instance beyond a client
    handle and never writes the key anywhere.
  - The real adapter is reached ONLY when an operator wraps it as the provider adapter of a
    FakeNonSpineLLMCompletionAdapter (the same injection point the callable adapter uses);
    a future helper analogous to run_non_spine_callable_provider_manual MAY build that
    stack, but it must be operator/manual and called by no live surface.

No default real provider path (proof obligation 5): the module default chain stays
NonSpineLLMRuntime() -> FakeNonSpineLLMCompletionAdapter() -> FakeNonSpineLLMProviderAdapter()
with provider_called=False / is_fake=True; the real adapter is non-default and unreferenced
by the default path (the same AST-guard pattern already used for the callable adapter
applies).
```

## 8. SDK / env / network decision

```text
- SDK imports: LAZY / MANUAL-ONLY. Forbidden at module import; permitted only inside the
  real adapter's gated code path, exactly as both precedents do (proof obligation 2). The
  provider SDK must stay optional in requirements.txt (commented), not a hard dependency.
- Env gate: an explicit env var (name to be chosen by the future implementation proposal,
  NOT chosen here) must equal "1" to enable the real path; default-unset means no real
  provider, no SDK import (proof obligation 3).
- Secrets: API key and model read ONLY from named local env vars when gated, with explicit
  errors when unset; never logged, stored, or echoed into NonSpineLLMProviderResult.
- Network: none at import and none on the fake/default/callable paths; network occurs only
  inside the gated real adapter's generate() call.
```

## 9. Timeout / error / fail-closed rules (proof obligation 4)

```text
- The real adapter's generate() must apply an explicit timeout to the provider call.
- On timeout, transport error, empty response, or any provider exception it must FAIL
  CLOSED: raise a clear error OR return a NonSpineLLMProviderResult explicitly marked as a
  failure — never silently substitute fake output as if it were real, and never retry/rank/
  style-steer.
- It performs no fallback to a different provider and no hidden recovery; the caller decides.
- (Precedent: run_external_inference_smoke.py already uses an explicit timeout and distinct
  non-zero exit codes for timeout/empty/error.)
```

## 10. Automated-test prohibition (proof obligations 6, 10)

```text
- Automated tests must NEVER instantiate the real adapter and NEVER cause a provider call:
  the gate stays unset under pytest; tests exercise only the fake default path and
  fake/spy-injected callables (as today's 78-test suite does).
- A future test must assert the real adapter is unreachable when the gate is unset and that
  no provider SDK is imported at module import.
- The fake default path and the callable manual helper are PRESERVED unchanged
  (proof obligation 10): the real adapter is additive and behind the gate; it removes
  neither.
```

## 11. Persistence / transcript / memory-write prohibition (proof obligations 8, 9)

```text
- The real adapter writes nothing to disk: no transcript, no prompt/response log, no output
  file (matching the manual provider harness).
- It performs NO memory write and NO ingest: it returns a NonSpineLLMProviderResult only.
  There is no model-output-to-memory feedback from this adapter. If an operator later wants
  a response remembered, that is the separate, already-sanctioned `POST /tool/ingest`
  operator path (Spine -> ProvenanceV1.for_tool_result), which is NOT part of this adapter
  and is out of scope for this review (proof obligation 9).
- No endpoint/MCP/API/schema, startup/scheduler/autonomy, or AgentRunner/Terrain B wiring
  (proof obligation 7): the adapter is operator-constructed and lives entirely off the live
  surfaces, exactly like the callable adapter and the manual helper today.
```

## 12. Final verdict

**Option 1 — a later real-provider adapter is ADMISSIBLE for the separate non-Spine runtime,
as a future, separately-gated step, under the constraints in §7-§11.** The boundary is
ready: the provider seam exists, the default stays fake, the callable manual helper and the
fake default path are preserved, and two in-repo precedents already show the exact accepted
shape (env-gated, lazy import, tests-never-touch, no persistence, not production-wired). The
other options are rejected: Option 2 (revise to manual harness only) is unnecessarily
narrow given the contracts are already in place; Option 3 (keep callable-only forever)
over-constrains a future that the readiness work was explicitly built to enable; Option 4
(HOLD) is stronger than the evidence requires, since the constraints can be stated cleanly
now. **This verdict authorizes no implementation.** A real adapter requires a separate,
explicitly-authorized implementation proposal (Hilmir + Codex) that satisfies §7-§11 with
tests and source/AST guards before any code.

## 13. Non-authorization footer

TORMENT — NON-SPINE LLM RUNTIME REAL-PROVIDER READINESS REVIEW / DOCS-ONLY / SOURCE-ONLY /
NON-AUTHORIZING / IMPLEMENTATION HOLD. Source edge `9ff8cc2` (§0 closure `45d1ed5`). It
grounds, in committed source, that the non-Spine runtime is stdlib-only and inert, that its
provider seam already carries a fake default adapter and an operator-injected callable
adapter, that the default path stays fake (`provider_called=False` / `is_fake=True`), that
no app/spine/mcp_server/cognition/roles surface references it, that `requirements.txt` keeps
provider SDKs optional/commented, and that two existing manual/operator precedents
(`memory_to_prompt_provider_llm_harness.py`, `run_external_inference_smoke.py`) define the
accepted env-gated, lazy-import, tests-never-touch, no-persistence, not-production-wired
shape. It selects **Option 1 — a later real-provider adapter is admissible as a future
separately-gated step under exact constraints** (§7-§11): named future adapter owner +
constructor; lazy/manual-only SDK import with the provider SDK optional in requirements; an
explicit env gate and named-env-var-only credential lookup; explicit timeout + fail-closed
behavior; no default real path; no provider call in automated tests; no
endpoint/MCP/startup/autonomy wiring; no persistence/logging/transcripts; no
model-output-to-memory feedback; and the fake default path + callable manual helper
preserved. **It authorizes no code, no tests, no SDK import, no env/secret read, no network
call, no runtime/public-surface change, and no live wiring; any real adapter requires a
separate Hilmir + Codex implementation gate.** Memory remains guidance, not authority;
automatic is allowed, autonomous is not; nothing rewrites identity / canon / seed / soul.
