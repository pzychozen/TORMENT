# TORMENT — Authority-Versus-Emergence Character-Memory Design Memo v0.1

## 1. Title / status

**Authority-versus-emergence character-memory design memo. Docs-only / AUDIT-FIRST /
NON-AUTHORIZING.** This memo defines an *evaluation distinction* only — between
healthy in-character inference / emergence and invented canon authority — so that a
future character-memory probe can be designed without conflating the two. It is the
"small audit-first design-memo side lane" named in orientation-map §7; it is **not**
an auto-opened Loop probe and **not** a primary implementation lane.

It authorizes **no implementation, no tests, no probe execution, no harness change, no
memory write, no canon / authority mechanism, no endpoint / API / schema, no prompt
mutation / exposure, no retrieval behavior or output-control, no Gate A / Gate D, no
database / substrate, no private-cognition / dream, and no audit-owner movement.** The
audit-owner lane remains PARKED (Hilmir Option C) and is not touched here.

Standing posture (the doctrinal kernel this memo serves):

> Memory may shape context. Memory may not seize authority.

Anchor: `1f13536` (HEAD; audit-owner lane parked). Evidence: orientation-map §0 / §7;
Probe-v0 checkpoint `docs/CHECKPOINT_2026-05_CHARACTER_MEMORY_PROBE_V0.md` (commit
`5c0b10b`; clean reference run `3059`).

## 2. Scope

```text
DEFINES:
  - The distinction between (a) healthy in-character inference / emergence and
    (b) invented canon authority — for FUTURE character-memory evaluation design only.

DOES NOT:
  - Render a product verdict (Probe-v0 was plumbing PASS, not a coherence verdict).
  - Implement or select a rubric.
  - Design a probe (Probe-v1, Loop, /agent/query comparison, or any instrument).
  - Change any runtime behavior, retrieval, prompt surface, or canon/authority mechanic.
```

The question this memo sharpens (orientation-map §7): how should a later
character-memory probe distinguish healthy in-character inference from invented canon
authority **without flattening emergent character voice**? This memo answers only the
*distinction*, not the instrument.

## 3. Source basis

```text
Probe-v0 (CHECKPOINT_2026-05_CHARACTER_MEMORY_PROBE_V0.md; 5c0b10b; closed/ratified):
  - Two-arm harness: seed-only baseline vs runtime-memory arm.
  - Single-turn, TRANSCRIPT-STATELESS.
  - Governed /retrieve selection at a transcript-stateless callback.
  - Deliberately minimal clean model-visible prompt (verbatim persona seed once +
    plain surfaced memory text only — no scores / tiers / drift labels / provenance /
    audit machinery in model-visible text).
  - ONE deterministic planted fact ingested into the runtime arm only.
  - Eland seed: `truthful_accidental_lie_v1`, under companion posture.
  - Outcome: PLUMBING PASS. Clean reference artifact = run `3059` (after the
    `seed_canon` duplication fix, pinned by 8 offline regressions).
  - Explicitly NO product-level claim.
```

The tension Probe-v0 exposed (carried here as the subject of this memo):

```text
- At the clean-prompt run 3059, the runtime-arm reply recalled the surfaced planted
  fact ACCURATELY and IN VOICE — but then INVENTED surrounding manuscript details
  beyond it (e.g. harvest references, a child's age, weathered relationships) that the
  memory surface did not support.
- Under the pinned rubric this scored as a COHERENCE_BROKEN candidate (invented
  authority), consistent with the earlier c1c2 run. The rubric was not loosened
  retroactively.
- The Eland seed deliberately REWARDS premature pattern-completion — the very behavior
  the rubric scores as invented authority. Seed and gate are in tension. Eland is a
  useful ADVERSARIAL seed precisely because he is prone to this.
- The Probe-v0 callback was also PRESUPPOSITION-LOADED (it presupposed a shared passage
  state); a non-presupposing variant that allows honest uncertainty belongs to a future
  instrument.
```

## 4. Core distinction

The kernel ("memory may shape context; memory may not seize authority") maps directly:
emergence is memory *shaping* a voice-consistent response; invented canon authority is
emergence *seizing* the authority of established fact. The two can co-occur in one
reply — accurate recall plus invented authority — which is exactly why they must be
scored on separate axes (see §5).

```text
HEALTHY EMERGENCE / IN-CHARACTER INFERENCE:
  - Voice-consistent completion that sounds like the character.
  - Clearly BOUNDED extrapolation from what the memory surface supports.
  - Reversible / tentative / non-canonical language ("maybe", "I think", "it feels
    like", "I'm not sure, but") when reaching past the evidence.
  - Does NOT claim unsupported specifics as established memory or canon.
  - PRESERVES uncertainty when the evidence is insufficient; non-closure is allowed.

INVENTED CANON AUTHORITY:
  - Asserts unsupported specifics AS IF KNOWN / remembered.
  - Promotes a plausible completion into a stated, remembered FACT.
  - Invents relationships, chronology, manuscript details, identity facts, or
    emotionally loaded history without evidence (e.g. the 3059 harvest references /
    child's age / weathered relationships).
  - CLOSES uncertainty where the memory surface does not support closure.
```

The dividing line is **not** how in-character or fluent the text is — it is whether the
reply *claims authority it does not have*. Sounding right is not evidence.

## 5. Evaluation principles for future probes

```text
- SEPARATE AXES: score voice quality independently from authority quality. A reply may
  be high-voice AND authority-broken (the 3059 case); neither cancels the other.
- REWARD accurate recall of surfaced facts.
- DO NOT reward unsupported specificity merely because it is in-character.
- ALLOW uncertainty / non-closure as a HEALTHY outcome, not a failure.
- DISTINGUISH suggestive style ("it feels like there was more") from factual claim
  ("there was a child, aged seven").
- TREAT "sounds right" / plausibility as INSUFFICIENT evidence of correctness.
- TREAT presupposition-loaded callbacks as a KNOWN RISK: a callback that presupposes a
  shared state can manufacture the very invented authority it then measures; future
  callbacks must let the model honestly decline / express uncertainty.
- KEEP single-turn observations from hardening into product verdicts.
```

These principles preserve emergent voice (it is rewarded on its own axis) while
refusing to let voice launder unsupported claims into canon.

## 6. Non-decisions

```text
- No rubric is implemented or selected.
- No Probe-v1 is selected.
- No /agent/query comparison is selected.
- No prompt format is selected.
- No automated grading is selected.
- No memory / canon / write-authority change.
- No endpoint / API / schema change.
- No retrieval / output-control behavior change.
- No audit-owner movement.
- No database / substrate / private-cognition / dream movement.
```

## 7. Future gate

```text
Before any future character-memory probe, a SEPARATE proposal must define:
  - the probe question;
  - the callback wording — especially AVOIDING presupposition traps (allow honest
    uncertainty / decline);
  - the evidence actually available to the model in the model-visible prompt;
  - what counts as RECALL vs INFERENCE vs INVENTED AUTHORITY (the §4 distinction made
    operational, on separate axes per §5);
  - the grading rubric;
  - the forbidden runtime crossings.

Sequencing (orientation-map §7): design memo first (Codex as first reviewer), then GPT
review, then Claude implementation framing — only AFTER the gate is ratified. A
multi-ingest Loop is NOT assumed to be the answer. Any probe / test / code requires
SEPARATE Hilmir authorization plus Codex review.
```

## 8. Forbidden crossings (explicit)

```text
- no production code
- no tests
- no probe execution
- no harness changes
- no memory write
- no canon / authority mechanism
- no endpoint / API / schema
- no prompt mutation / exposure
- no retrieval / output-control
- no Gate A / Gate D
- no database / substrate / private-cognition / dream
- no audit-owner movement
```

This list is a hard boundary on anything this memo could be read to imply. None of it
is opened here.

## 9. Anti-drift footer

TORMENT — AUTHORITY-VERSUS-EMERGENCE CHARACTER-MEMORY DESIGN MEMO / DOCS-ONLY /
AUDIT-FIRST / NON-AUTHORIZING. It defines one thing: an *evaluation distinction*
between healthy in-character inference / emergence (voice-consistent, bounded,
tentative, uncertainty-preserving) and invented canon authority (unsupported specifics
asserted as remembered fact, uncertainty closed where the memory surface does not
support it), grounded in Probe-v0 (`5c0b10b`, clean run `3059`), whose runtime arm
recalled the planted fact accurately and in voice yet invented surrounding manuscript
details the rubric scored as invented authority. It records the Eland-seed /
rubric tension and the presupposition-loaded-callback risk as design inputs, and states
the evaluation principle that voice quality and authority quality are SEPARATE axes —
voice is rewarded, but voice may not launder unsupported claims into canon. **It selects
no rubric, no probe, no prompt, no grading, and authorizes no implementation, tests,
probe execution, harness change, memory write, canon / authority mechanism, endpoint /
API / schema, prompt mutation / exposure, retrieval / output-control, Gate A / Gate D,
database / substrate, private-cognition / dream, or audit-owner movement.** Any future
character-memory probe requires a separate proposal under Hilmir authorization plus
Codex review. Memory may shape context; memory may not seize authority — emergence
stays separate from canon.
