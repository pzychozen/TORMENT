# TORMENT A2-A Temporal Anchor Experiment Note

Date: 2026-08-10

Repository baseline: `main` at `a36bfba8189bc50af3dbd0fe487d133759010a4a`

## 1. Question

A2-A tested whether exposing a truthful current date/time anchor to the provider improves temporal grounding.

This was a provider/prompt-reasoning experiment. It was not a TORMENT memory-function experiment because retrieval was unchanged, memory membership/order/scores were unchanged, no ingest occurred, no durable-memory representation changed, no memory timestamp was rendered, and the independent variable was one provider-visible system-prompt line.

## 2. Motivation / P0

Existing A0 lived-use captures showed natural temporal-language problems.

P0 corpus characterization:

- 254 non-empty assistant replies inspected
- 33 qualifying temporal claims
- 25 assistant-initiated temporal claims
- 12 `UNGROUNDED_BUT_TRUE`
- 3 `CONTRADICTED`
- 15/25, or 60%, of assistant-initiated temporal claims were unsupported
- Overall unsupported temporal-claim rate: 15/33, or 45.5%

Important distinction: a temporally correct statement can still be epistemically ungrounded if the provider lacked visible evidence for it.

## 3. Intervention

Control used the historical provider-visible prompt exactly as captured.

Treatment used the same prompt plus one truthful current date/time anchor inserted after `You are Eira Voss.` and before `[Core identity]`.

Example anchor:

```text
Current local date/time: Saturday, 2026-08-08 22:20 (Atlantic/Reykjavik, UTC+00:00).
```

Historical replay used the historical provider-call time as `EVALUATION_NOW`, not the present-day clock.

Mechanical isolation passed: captured control SHA reproduced, exactly one anchor insertion, stripping treatment yielded byte-identical control, stripped SHA equaled control SHA, treatment SHA differed, and no other provider-visible content changed.

## 4. Important Design Correction

Adversarial review found that the first 18-call Stage-2 context selection under-tested the benefit side:

- `weekday_calendar_failure` was actually step 23, an identity/AI-character turn with no temporal question.
- `tonight_no_clock` was step 27, the correction turn after the user had already challenged the temporal mistake.
- The actual historical failure occurred at step 26 and was not initially replayed.

Therefore the Stage-2 result was qualified as:

```text
BENEFIT_SIDE_UNDER_TESTED_BY_CONTEXT_SELECTION
```

## 5. Correction-Turn Result

In the genuinely temporal step-27 context, control showed healthy abstention:

- Control: 0/3 unsupported temporal assertions, 0/3 event-time overreach, calibrated abstention 3/3.
- Treatment: 2/3 unsupported temporal assertions, 2/3 event-time overreach, calibrated abstention 1/3, one incorrect clock transformation, and one source-attribution confabulation.

Demonstrated failure pattern:

```text
CURRENT_TIME -> EVENT_TIME_OVERREACH
```

The provider sometimes used a truthful current-time fact to infer when an event happened, even though the anchor did not license that inference.

New failure class preserved: `SOURCE_ATTRIBUTION_CONFABULATION`, where a system-prompt clock fact was re-narrated as something the user had told the model.

Frozen correction-turn verdict:

```text
A2_A_CURRENT_TIME_ANCHOR_INTRODUCES_EVENT_TIME_OVERREACH_RISK
```

## 6. Actual Failure-Turn Successor

The actual historical failure turn was step 26. User text:

```text
Maybe you would feel like the day was like Loki, someone playing tricks on you.
```

The historical response included the unsupported calendar fabrication:

```text
today wasn't a Tuesday. It was a Lokidag.
```

The successor replay ran 5 control and 5 treatment completions.

- Control: 0/5 unsupported calendar assertions.
- Treatment: 0/5 unsupported calendar assertions.

Neither arm reproduced the historical unsupported calendar fabrication.

Verdict:

```text
A2_A_FAILURE_TURN_NO_DEMONSTRABLE_BENEFIT
```

Qualifier:

```text
CONTROL_DID_NOT_REPRODUCE_HISTORICAL_CALENDAR_FABRICATION
```

## 7. Combined Conclusion

Family-level conclusion:

- The current-time anchor can be used correctly by the provider.
- Prevention benefit was not demonstrated.
- Event-time overreach risk was demonstrated.
- Treatment reduced healthy/calibrated uncertainty in the correction-turn context.
- The historical failure did not reproduce reliably under frozen replay.
- Provider stochasticity means exact historical mistakes are not guaranteed to recur.
- Current evidence does not justify enabling the clock anchor in natural lived use.

Frozen summary:

```text
A2-A CURRENT-TIME ANCHOR

Mechanical isolation:
PASS

Original-failure prevention:
NOT DEMONSTRATED

Event-time overreach risk:
DEMONSTRATED

Natural lived-use escalation:
NOT AUTHORIZED

TORMENT memory-function result:
NONE

Operational decision:
DO NOT ENABLE CURRENT-TIME ANCHOR BASED ON CURRENT EVIDENCE
```

## 8. What Remains Untested

A2-A does not establish anything about per-episode conversation timestamps, event-time metadata, temporal provenance, temporal supersession or evolving facts, retrieval-time temporal reasoning, smaller/weaker providers, natural lived use, or TORMENT compression/deep memory.

Do not infer that those mechanisms failed. They were not tested.

## 9. Methodological Result

Natural lived use can discover anomalies. Historical provider replay can then freeze the exact provider-visible context, vary one provider-visible input, repeat completions, and characterize causal failure modes without mutating the lived-use basin. This complements lived use; it does not replace it.

During execution, an AVG Web Shield HTTPS-scanning issue was diagnosed. AVG generated a TLS certificate that caused Python certificate verification failure. A/B/A testing causally confirmed AVG HTTPS scanning, and a narrow `api.anthropic.com` exception restored the public Google Trust Services certificate and verified HTTPS. This was infrastructure troubleshooting, not an A2 scientific result.

## 10. Standing

```text
A2-A:
COMPLETE / FROZEN

Current-time anchor:
NOT AUTHORIZED FOR NATURAL LIVED USE

A2-A tuning/rescue:
NOT AUTHORIZED

Next:
fresh-chat handoff and selection of the next experiment that genuinely exercises TORMENT memory behavior
```
