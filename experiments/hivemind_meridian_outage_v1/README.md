# Meridian Outage v1 — Frozen Offline Instrument

This synthetic incident-reconstruction harness is an offline experimental
instrument. It is not connected to normal TORMENT startup and supplies no
default provider; it cannot make a live model call unless a separately
authorized live provider is injected. This corpus was corrected by an
adversarial instrument audit before its first administration; no live result
has been invalidated.

## Frozen inputs

- Harness version: `hivemind_meridian_outage_v1`
- Frozen implementation baseline: `6970ea70eae7decc52d4b073032505352929b75f`
- Corpus SHA-256: `347d2add8cf4ad14af1e8cbf2c361dc8694d90ff8f171f558bc95323134aa452`
- Evaluator ground-truth SHA-256: `1b1d76e383e02c4ba10a0d9ba5d023a453e16cc3025dab1c8848dfcf7d978993`
- Assignment seed: `meridian-outage-v1-fixed-20260824`
- Manifest SHA-256, N=5: `6960fb2799f0bd9e9b6bfe76c7bbb93abfc9f62b94b0b7717939fad99337c565`
- Manifest SHA-256, N=10: `10c7e8784164fcd1e174715189fdcb82c4acd52920e08d610a555507cdd89dd3`
- Manifest SHA-256, N=25: `3fdc90132e823e5ffb2c2e5e9553498c66647c90b6846c6c1e1958430dd3045d`

Agents receive only `card_id`, naturalistic non-evaluator `source_id`,
`source_tier`, and text. Tiers are intentionally informative but not truth
oracles: true, false, misleading, and weak evidence are mixed across them.
Ground truth and evaluator annotations remain outside the provider boundary.

## Conditions and information boundaries

| Condition | Hivemind | Round-2 provider input |
| --- | --- | --- |
| A_PRIVATE | off | assigned cards only |
| B1_TORMENT_MECHANISMS_ONLY | on + telemetry | byte-identical to A, apart from provider nondeterminism |
| B2_TORMENT_SALIENCE_SURFACED | on + telemetry | current production `collective_context` shape only |
| C_NAIVE_SHARED_CONTENT | off | mechanically sorted actual Round-1 cited findings only |

`B1_TORMENT_MECHANISMS_ONLY` measures Hivemind state formation, governance,
packets/events, proposal promotion, provenance, storage/cost, and telemetry.
It does **not** expose shared-canon retrieval, peer packets, peer findings, or
collective context to agents. Therefore an A/B1 task comparison is not evidence
of Hivemind cognitive benefit (or harm); comparable performance is expected by
construction. A future separately designed v2 may study governed retrieval.

B2 accepts only the production collective-context payload shape; the verifier
rejects corpus text, packet/peer-finding text, and evaluator fields. C is not a
TORMENT coordination condition: its pool is reconstructed only from actual
Round-1 agent findings and does not receive governance, packets, events,
quorum, echo, or promotion semantics.

## Population metrics, not synthetic cognition

Primary task proxies are scored per real agent:

- `best_agent_score`
- `mean_agent_score`
- `population_evidence_coverage`

The optional `deterministic_union_score` is labeled **ORACLE-LIKE POPULATION
UPPER BOUND**, **NOT AN AGENT ANSWER**, and **NOT COLLECTIVE COGNITION**. It
may combine evidence no individual held and is only a population-recovery
diagnostic. A deterministic representative root is chosen by support count
(with lexical tie break) only for diagnostics; it is not a collective answer.

All scoring is deterministic structural proxy scoring. Root-cause concept
matching can mishandle negation; contributor recall does not prove causality;
citations do not prove entailment; and provenance can reward citation density.
No hidden evaluator model or LLM judge is used. Raw agent outputs are retained
for a later separately authorized blinded adjudication if desired.

Claims explicitly declare `stance` as `asserts`, `refutes`, or `mentions`
(defaulting to `asserts` at the provider boundary). False-claim and poison
inheritance metrics count assertions only. Duplicate work is repeated
independent card discovery across agents; exact duplicate claim text is a
diagnostic only.

## N=5 boundary

At N=5 each participating agent receives exactly one decisive card. The
minority-evidence phenomenon is therefore **not** an agent-population
phenomenon at N=5. N=5 establishes only mechanics, condition isolation,
telemetry completeness, provider execution, sealing/verifier correctness, and
expected information flow. It may not establish intelligence effects, salience
effects, naive-sharing superiority, scaling behavior, or efficiency
superiority. Minority-evidence interpretation begins only at a later population
where decisive-card holders are actually a minority.

## Provider, run, and evidence isolation

Real-Fabric runs require one fresh empty absolute data root per run and
condition. The adapter records that root and rejects prior state; restart mode
is not part of v1. Provider metadata must identify the provider, exact
`model_id`, `per_agent_per_round` session isolation, `retry_policy: none`, and
every sampling field. Explicit values are recorded as such; unavailable safe
seams are attested as `provider_default` with a null explicit value, never as
invented numeric defaults.

`meridian-result-v2` records per-attempt provider evidence: deterministic
provider-visible input hashes, raw response text when safely available,
parser/schema outcome, exception evidence, provider-reported usage or explicit
unavailability, sequence, timestamps, and exact logical-call counts. It never
stores credential-shaped fields. The N=5 four-condition plan is 40 logical
provider calls, with no hidden evaluator calls.

The experiment-local `FrozenAnthropicMeridianProvider` is the only frozen
bridge for a separately authorized live Meridian characterization. It uses the
existing gated `AnthropicNonSpineLLMProviderAdapter` public seam, pins
`claude-sonnet-5`, the 1024-token limit, and the 30-second timeout without
altering provider-default sampling, and has no transcript state. Its prompt
requires exactly one strict JSON object; malformed text is preserved and sealed
as failed evidence rather than repaired or retried. Constructing the bridge or
calling its preflight performs no model contact and exposes no credential value.

## Corrected live-provider configuration and identity

Before a separately authorized live run, use the bridge's
`FrozenAnthropicMeridianProvider.from_repo_dotenv()` bootstrap. It applies the
same standard-library, non-overriding `KEY=value` loading convention used by
TORMENT's user-facing tools: it reads only the repository-root `.env`, leaves
all existing process values (including deliberately empty ones) unchanged, and
returns only redacted configured/provenance status. `credential_source` is one
of `process_environment`, `repo_dotenv`, or `absent`; it contains no credential
value, length, prefix, suffix, hash, fingerprint, or equality result. The
real-provider gate is deliberately operator controlled rather than stored in
`.env`; it must be set to the native adapter's exact enabled value,
`TORMENT_NON_SPINE_LLM_REAL_PROVIDER=1`.

`HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT` is immutable evidence at
`C:\TORMENT\meridian_outage_v1_n5_characterization_20260824`, with prior run ID
`meridian-n5-characterization-20260824-a-private`. It sealed `FAILED` after one
attempt because the operator-session credential was rejected by Anthropic with
`401 invalid x-api-key`. That is not a Haiku availability result, Hivemind
result, efficacy result, or parser result. It must never be overwritten, reused,
or deleted.

### Closed Sonnet authentication/configuration attempt

The original Sonnet 5 characterization is immutable sealed `FAILED` evidence at
`C:\TORMENT\m5s5`. It reached only `A_PRIVATE`, logical call
`round_1:researcher_001`, with this exact bounded outcome:

| Field | Value |
| --- | --- |
| Model | `claude-sonnet-5` |
| Provider calls attempted / succeeded / failed | 1 / 0 / 1 |
| Retries | 0 |
| Provider failure | `Anthropic 401 authentication_error / invalid x-api-key` |
| Scientific interpretation | `AUTHENTICATION / CONFIGURATION FAILURE` |

It is not a Hivemind result, Sonnet task-quality result, parser/schema result,
A/B1/B2/C comparison, or evidence for or against collective cognition. Its
external evidence must never be overwritten, reused, or deleted.

The non-overriding dotenv contract makes stale-process credential shadowing
structurally possible: `load_repo_dotenv_safely()` preserves a pre-existing
`ANTHROPIC_API_KEY`, and that is the native adapter's credential variable.
Previous readiness established only credential presence, not provenance. Secret
values were not inspected or compared, so it cannot be determined which specific
credential Anthropic received. `credential_source` prevents that ambiguity in a
future no-contact gate, but proves provenance only—not credential validity.

### Closed Sonnet empty-text attempt

`C:\TORMENT\m5s5b` is immutable sealed `FAILED` evidence for
`meridian-n5-sonnet5b-20260824-a-private`. It reached only `A_PRIVATE`, logical
call `round_1:researcher_001`, with model `claude-sonnet-5`: one provider
attempt, zero successful responses, one failure, and zero retries. Its
classification is `UNRESOLVED PROVIDER BEHAVIOR`.

Authentication succeeded and the provider returned a response object, but the
native adapter found no nonempty final text. Meridian's parser was not reached.
Adaptive thinking combined with the frozen 1024-token combined output budget is
a plausible but unproven cause. This is not a Hivemind efficacy result, Sonnet
task-quality result, Meridian schema/parser result, A/B1/B2/C comparison, or
evidence for or against collective cognition. Its external evidence must never
be overwritten, reused, or deleted.

### One authorized Sonnet 5 diagnostic successor characterization

The failed empty-text attempt does not authorize a silent retry. Exactly one
diagnostic successor N=5 characterization is authorized only after every
pre-contact gate below passes. It has a fresh, short Windows-safe external root:

`C:\TORMENT\m5s5c`

| Condition | Successor run ID |
| --- | --- |
| A_PRIVATE | `meridian-n5-sonnet5c-20260824-a-private` |
| B1_TORMENT_MECHANISMS_ONLY | `meridian-n5-sonnet5c-20260824-b1-mechanisms-only` |
| B2_TORMENT_SALIENCE_SURFACED | `meridian-n5-sonnet5c-20260824-b2-salience-surfaced` |
| C_NAIVE_SHARED_CONTENT | `meridian-n5-sonnet5c-20260824-c-naive-shared-content` |

Before any live call, the exact operator process must pass all frozen checks and
all of these additional checks: `credential_source == "repo_dotenv"`, credential
configured is true, the real-provider gate equals `1`, model is
`claude-sonnet-5`, the SDK is available, adapter construction succeeds, and
network contact remains false. It must also verify the frozen corpus, manifest,
and seed; `HEAD == origin/main ==` the committed successor-preparation revision;
a clean tracked worktree; and that `C:\TORMENT\m5s5c` exists and is empty.

The successor preserves A_PRIVATE, B1_TORMENT_MECHANISMS_ONLY,
B2_TORMENT_SALIENCE_SURFACED, and C_NAIVE_SHARED_CONTENT; 5 agents; 2 rounds;
at most 40 planned logical calls; no retries; no second seed; no confirmatory
rerun; no hidden evaluator; and no model synthesizer. The diagnostic path adds
only redacted response-shape metadata to an empty-text provider failure, so a
repeat may distinguish likely output-budget exhaustion from other provider
behavior. Terminal provider or schema failure must stop immediately and seal
`FAILED`. N=5 remains characterization-only.

Every run has a unique ID, raw outputs, telemetry, a self-contained
`SEALED.json`, and an append-only `meridian-seal-index.jsonl` outside its run
directory. `RUN_STATUS=COMPLETE` requires every planned logical call and scored
metrics. `RUN_STATUS=FAILED` seals observed partial evidence, records the
terminal failure and unexecuted-call count, and is verifiable but cannot be
treated as a completed experiment. The index anchors either status along with
run identity, condition, N, seed, seal file hash, and result timestamp. It is
an operational append-only anchor, not a hostile tamper-resistance claim.
