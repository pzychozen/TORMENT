# TORMENT Brainvision Tiny Synthetic Target Proposal v2.64

## 1. Scope

**DOCS-ONLY PROPOSAL.** It defines **one** candidate offline synthetic falsification target, in plain language, and
**authorizes no implementation**. It contains **no** code, **no** tests, **no** fixture data, **no** arrays or images,
**no** metrics, **no** thresholds, **no** decision rules, and **no** real clips. It opens **no** screen, runtime, memory,
integration, classifier, or neural path, and makes **no** vision claim.

Brainvision remains **offline / quarantined** under `research/brainvision/` + `tests/research/`, HELD per v0.6.

**Nothing here is authorized. Any implementation requires separate operator approval and separate Codex review.**

**And one standing rule must be met head-on rather than stepped around**, because stepping around it quietly is the exact
failure this record keeps catching:

> **THE MACHINERY CEILING.** The standing rule has been: *if a question cannot be posed without adopting machinery, that
> is the finding, and the honest response is to stop.* That rule governed **docs-only slices** — it forbade a document
> from quietly adopting a metric in order to sound like it had asked something.
>
> **This proposal does not evade that rule. It triggers the other half of it.** The finding stands: **the questions this
> programme is now asking cannot be posed without machinery.** The options that follow are therefore exactly two —
> **stop**, or **build a small thing deliberately, with the operator saying so out loud.** This document is a request for
> that second decision. It is not a document pretending it can proceed without one.
>
> If the operator reads that and prefers **stop**, that is a complete and honest answer, and this proposal is the right
> place to give it.

```text
NO IMPLEMENTATION. NO CODE. NO TESTS. NO FIXTURE DATA. NO ARRAYS / IMAGES. NO REAL CLIPS.
NO METRICS. NO THRESHOLDS. NO DECISION RULES. NO SCHEMAS. NO DESCRIPTORS.
NO SCREEN / RUNTIME / MEMORY / INTEGRATION PATH. NO CLASSIFIER / NEURAL WORK.
NO VISION CLAIM. NO READINESS CLAIM. NO §0 POINTER. NO TAGS.
```

```text
flat_field_validated = False    role_validated = False    schema_validated = False
entanglement_resolved = False   by_residual_isolated = False
generic_chroma_proxy_ruled_out = False   null_rejected = False   artifact_ruled_out = False
proxy_ruled_out = False   confound_controlled = False
control_collapse_ruled_out = False   control_collapse_detected = False
control_collapse_reachability_validated = False
candidate_structure_validated = False   candidate_structure_survived = False
candidate_structure_detected = False
anti_inevitability_validated = False    control_honesty_validated = False
first_pass_structure_validity_claim_allowed = False   temporal_claim_allowed = False
descriptor_validity_claim_allowed = False   geometry_validity_claim_allowed = False
screen_readiness_claim_allowed = False   runtime_readiness_claim_allowed = False
memory_readiness_claim_allowed = False   integration_readiness_claim_allowed = False
vision_claim_allowed = False
verdict = HOLD
```

## 2. The Tiny Target

**One task. Small. Synthetic. Offline. Two classes of very short artificial stream, described here in plain words only —
no data, no arrays, no generation rules, no parameters.**

> **Each stream shows two simple moving elements against a plain background.**
>
> **In class ONE, the two elements' movements are RELATED across time** — what one does constrains what the other does.
> The relation persists through the clip.
>
> **In class TWO, the two elements move INDEPENDENTLY** — each drawn from the same kind of movement as in class ONE, but
> with no relation between them.
>
> **The two classes are built to look the same to anything that does not track a relation across frames.** Same colours.
> Same brightness. Same kinds of shape. Each element, taken alone, moves the same way in both classes. Each single frame,
> taken alone, is the same sort of picture in both classes. The amount of change from frame to frame is the same sort of
> amount in both classes.
>
> **The only thing that differs is whether a relation between the two elements is maintained over time.**

**Why this shape.** Colour and intensity alone should not separate the classes, because the palettes are the same.
Frame-difference magnitude alone should not, because the amount of change is matched. A single-frame descriptor should
not, because single frames carry no relation. What is left is **relation / continuity across frames** — which is the one
thing this programme has claimed to care about and has never tested in isolation.

**No metrics are defined here. No thresholds. No generation rules. No data. Those are separate gated questions, and
Section 7 says so.**

## 3. What Would Make It Useful

**The task is useful only if cheap baselines are expected to struggle — and only if that expectation is CHECKED BEFORE
anything Brainvision-style is looked at.**

This is the anti-inevitability requirement made concrete, and it is the most important paragraph in the proposal:

> **THE CHEAP BASELINES RUN FIRST. THE BRAINVISION-STYLE READING IS NOT LOOKED AT UNTIL THEY HAVE FAILED.**
>
> **If a cheap baseline separates the classes, the task is DEAD.** Not adjusted. Not re-tuned. Dead — and the
> Brainvision-style reading is **never run on it**, because a candidate that is only examined after the easy
> explanations have been cleared away is a candidate that cannot be flattered by the clearing.
>
> **A task whose difficulty is DESIGNED is worthless. A task whose difficulty is DEMONSTRATED is the only kind worth
> having.** We can trivially build a task where cheap baselines fail by construction and a fancier reading succeeds by
> construction; both results would be manufactured, and neither would tell us anything. So the difficulty is a
> **property to be verified**, not an intention to be declared.

**And the honest prior, stated now so it cannot be discovered conveniently later:**

> **THE MOST LIKELY OUTCOME IS THAT A CHEAP BASELINE WINS.** A simple relational baseline — one that compares how two
> regions change *together*, without any Brainvision machinery at all — is a very plausible solution to this task. If it
> works, the answer is: **no Brainvision-specific reading is warranted for relational structure**, and that is a real,
> useful, unwelcome result.
>
> **If we are not willing to be interested in that outcome, we should not run the test.** That sentence is the
> precondition for the whole proposal.

## 4. Cheap Baselines To Include Later

**Future comparison requirements only. Not implementation, not a design, not a specification. Named so that the
comparison cannot be quietly narrowed later to a set the candidate can beat.**

```text
- colour / intensity baseline
- frame-difference baseline
- static (single-frame) descriptor baseline
- random / control baseline
- simple spectral (FFT) baseline, if applicable
- AND -- added here, because its absence would rig the comparison --
  a CHEAP RELATIONAL baseline: the simplest thing that looks at two regions changing together, with no Brainvision
  machinery of any kind. This is the baseline most likely to win, and it is therefore the one most likely to be left
  out.
```

**The baseline set must be fixed BEFORE any data exists.** Adding baselines after seeing results is how a candidate
survives; removing one is how it survives faster.

## 5. Failure Outcomes Allowed

**All of these are legitimate results. None is a failed slice. Each is pre-accepted here, before anything is known.**

```text
- the Brainvision-style signal fails.
- a cheap baseline wins -- INCLUDING the cheap relational baseline, which is the expected case.
- the task is flawed, or is solvable for a reason nobody intended.
- an artifact explains the result.
- a proxy explains the result.
- no conclusion can be drawn at all.
```

**And the outcome that is NOT on this list, because it would not be an outcome:** *the candidate looked promising, so we
adjusted the task.* That is not a result. That is the manufacture of one.

## 6. What This Does Not Claim

```text
- no Brainvision claim.
- no vision claim.
- no primitive validation. PRIMITIVE SELECTION REMAINS UNRESOLVED, and this task selects nothing.
- no geometry validation.
- no memory bridge validation. MEMORY INTEGRATION IS NOT AUTHORIZED.
- no runtime / screen / integration readiness.
- no descriptor, metric, or threshold, since none is defined here.
- no evidence of any kind. THIS DOCUMENT PRODUCES NONE.
```

**And a limit that will hold even in the best case:** a result on a tiny synthetic task made by us would be a fact about
**that task**. It would not be a fact about streams, about colour, about the world, or about vision. It would authorize
nothing; at most, it could become material for a later, separately gated operator decision about whether another small
question should even be proposed.

## 7. Operator Checkpoint

```text
RECOMMEND: CODEX REVIEW OF THIS PROPOSAL BEFORE ANY IMPLEMENTATION IS CONSIDERED.

AFTER REVIEW, THE OPERATOR MAY CHOOSE:

  A. Implement exactly this tiny test.
  B. Modify the proposed target.
  C. Pause.
  D. Choose a different tiny target.

These are operator options only, undeveloped and unranked. None is owed. Pause is co-equal and is a complete answer.

IF A IS CHOSEN, TWO THINGS MUST HAPPEN IN A SEPARATE GATED SLICE, BEFORE ANY DATA EXISTS:
  - the metrics, thresholds, and decision rules must be PRE-REGISTERED, and the baseline set FIXED (Section 4);
  - the ORDER must be locked: BASELINES FIRST; the Brainvision-style reading is not looked at unless the baselines have
    already failed (Section 3).
Choosing criteria after seeing results is the oldest way to survive a test, and it is available to us.
```

## 8. Conclusion

```text
This proposal defines only one tiny offline synthetic target candidate.
It produces no evidence.
It authorizes no implementation.
Cheap-baseline failure is required before any Brainvision-style result would be interesting.
Failure, artifact, proxy, and no-conclusion outcomes remain valid.
No claim lock moves.
verdict = HOLD
```

`OUTCOME_LABEL: BRAINVISION_TINY_SYNTHETIC_TARGET_PROPOSAL_ONLY`

## 9. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_TINY_SYNTHETIC_TARGET_PROPOSAL_v2.64.md
(new, docs-only, untracked; over the accepted v2.63 edge "7686b64 docs(research): record brainvision standing ledger").

Verify that this proposal:
- is docs-only and authorizes NOTHING: no code, no tests, no implementation, no fixture data, no arrays / images, no
  real clips, no metrics, no thresholds, no decision rules, no schemas, no descriptors, no generation rules; no screen /
  runtime / memory / integration path; no classifier / neural work; no vision or readiness claim; no §0 pointer; no tags;
- CONFRONTS THE MACHINERY CEILING EXPLICITLY rather than stepping around it: the finding stands that these questions
  cannot be posed without machinery, so the only honest options are STOP or BUILD DELIBERATELY WITH OPERATOR CONSENT --
  and this document requests that consent rather than assuming it;
- defines ONE tiny synthetic target in PLAIN LANGUAGE ONLY (two short artificial streams; two moving elements; class ONE
  relates their movements across time, class TWO does not; palettes, per-element motion, single-frame appearance, and
  frame-to-frame change amounts matched), with NO metrics, thresholds, parameters, generation rules, or data;
- states that the task is useful ONLY IF cheap baselines are expected to struggle, and that this must be DEMONSTRATED
  rather than DESIGNED -- with the ORDER locked: BASELINES FIRST, and the Brainvision-style reading NEVER RUN on a task
  a cheap baseline has already solved (a solved task is DEAD, not re-tuned);
- states the HONEST PRIOR that a cheap relational baseline is the most likely winner, and that this outcome is valuable
  and must be pre-accepted -- if we are unwilling to be interested in it, the test should not be run;
- lists the cheap baselines as FUTURE COMPARISON REQUIREMENTS ONLY (colour / intensity; frame-difference; static
  descriptor; random / control; simple spectral; and a CHEAP RELATIONAL baseline), and requires the baseline set to be
  FIXED BEFORE ANY DATA EXISTS;
- pre-accepts all failure outcomes (Brainvision signal fails; cheap baseline wins; task flawed; artifact explains; proxy
  explains; no conclusion) and explicitly forbids "the candidate looked promising, so we adjusted the task";
- claims NOTHING (no Brainvision, vision, primitive, geometry, or memory-bridge validation; no readiness), and states
  that even a best-case result would be a fact about the task and not about streams or the world;
- recommends CODEX REVIEW BEFORE IMPLEMENTATION and offers exactly four operator choices (implement as proposed; modify;
  pause; different target), undeveloped, unranked, none owed, pause co-equal;
- requires, if implementation is chosen, a SEPARATE GATED SLICE that PRE-REGISTERS metrics / thresholds / decision rules
  and FIXES the baseline set and the baselines-first order BEFORE any data exists;
- states the required conclusion block verbatim and preserves all claim locks False with verdict = HOLD.

Flag any metric / threshold / decision rule / descriptor / schema / parameter / generation rule defined anywhere; any
data, array, or image; any implementation authorized or assumed; any task difficulty asserted by design rather than
demanded as demonstration; any ordering that would let the candidate be looked at before the baselines have failed; any
baseline omitted or left adjustable after data exists; any outcome treated as a failure of the slice; any claim about
streams, colour, or the world; any successor treated as owed; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

All claim locks False, and the frozen verdict **HOLD**, are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Tiny Synthetic Target Proposal v2.64. Docs-only proposal over the accepted v2.63 edge.
Contains no code, tests, implementation, fixture data, arrays, images, real clips, metrics, thresholds, decision rules,
schemas, descriptors, or generation rules; opens no screen / runtime / memory / integration / classifier / neural path;
makes no vision or readiness claim; authorizes nothing. Confronts the MACHINERY CEILING head-on: the finding stands that
these questions cannot be posed without machinery, so the honest options are STOP or BUILD DELIBERATELY WITH OPERATOR
CONSENT — and this document REQUESTS that consent rather than assuming it; STOP remains a complete answer. Proposes ONE
tiny offline synthetic target in plain language: two short artificial streams, each showing two moving elements, where
class ONE maintains a RELATION between their movements across time and class TWO does not, with palettes, per-element
motion, single-frame appearance, and frame-to-frame change amounts MATCHED, so that colour / intensity, frame-difference
magnitude, and single-frame descriptors should not separate them and only RELATION / CONTINUITY ACROSS FRAMES remains.
Requires that the task's difficulty be DEMONSTRATED, NOT DESIGNED: BASELINES RUN FIRST, and if a cheap baseline separates
the classes the task is DEAD and the Brainvision-style reading is NEVER RUN on it. States the HONEST PRIOR that a CHEAP
RELATIONAL baseline is the most likely winner — a real, useful, unwelcome result — and that unwillingness to be
interested in that outcome is a reason not to run the test at all. Lists cheap baselines as future comparison
requirements only (colour / intensity; frame-difference; static descriptor; random / control; simple spectral; and a
cheap relational baseline, named because its absence would rig the comparison), with the set to be FIXED BEFORE ANY DATA
EXISTS. Pre-accepts failure, cheap-baseline victory, flawed task, artifact, proxy, and no-conclusion outcomes, and
forbids adjusting the task because the candidate looked promising. Claims nothing, and notes that even a best-case result
would be a fact about THAT TASK, not about streams, colour, the world, or vision. Recommends Codex review before any
implementation and offers four undeveloped operator choices (implement; modify; pause; different target), none owed,
pause co-equal; requires a separate gated slice to PRE-REGISTER metrics / thresholds / decision rules and FIX the
baseline set and baselines-first order before any data exists. Preserves all claim locks False and the frozen verdict
HOLD; outcome label BRAINVISION_TINY_SYNTHETIC_TARGET_PROPOSAL_ONLY; no `§0` pointer added; no tags.*
