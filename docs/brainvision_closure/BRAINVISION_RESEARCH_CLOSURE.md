# Brainvision research closure

Final closure record for the Brainvision offline research lane. Descriptive
only: it creates no authority, authorizes no execution, and reinterprets no
retained finding.

## What Brainvision investigated

Whether a frozen, descriptor-blind higher-order witness family could detect
temporal-order structure in visual input beyond what spectral and related
lower-order descriptors already explain - the strong order hypothesis. The lane
ran fully offline and quarantined, with synthetic and retained fixtures, under
one-run execution authorities.

## Final scientific conclusion

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Source of record:
`docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATION_FINDINGS_v0.1.md`

That findings document classifies the result as a valid authoritative
frozen-family negative, and records the surrounding state: the F3 execution
authority is consumed, `F3_RERUN_AUTHORIZED = False`,
`SCIENTIFIC_INFERENCE_AUTHORIZED = False`,
`PRODUCTION_INTEGRATION_AUTHORIZED = False`.

The conclusion is bound to the frozen family that was evaluated. It is not a
general claim about temporal order in vision.

## Why no further temporal-order experiment is required for closure

The frozen-family F3 evaluation was the designated decisive test for the
question this lane posed. It was authorized once, executed once, and returned a
result. The question was answered - in the negative.

Closure follows from the question having been answered, not from a positive
finding. A further temporal-order experiment would be a new investigation with
its own scope and authority, not the completion of this one. No such experiment
is outstanding.

## Blocker status

- **BLOCKER-1** - Windows directory-entry durability. Closed within its
  authorized synthetic-offline, local-fixed-NTFS, isolated-tmp-path scope, per
  `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_CLOSURE_ASSESSMENT_v0.1.md`.
  The closure is scoped as written there; it is not arbitrary-filesystem
  durability and not a production readiness decision.
- **BLOCKER-2** - directory promotion primitive. Engineering completed at commit
  `3e516bd` ("fix(brainvision/blocker2): propagate A3 collision preservation
  evidence"). This is an engineering-completion point recorded by the operator,
  not a separate formal closure assessment of the kind BLOCKER-1 and BLOCKER-3
  each have.
- **BLOCKER-3** - resource admissibility. Closed, per
  `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_CLOSURE_ASSESSMENT_v0.1.md`.
- **BLOCKER-4** - never opened.

## Dormancy of post-BLOCKER-2 R4 and authority work

The R4, authority, Strategy-2, nomination and authentication chain that grew
after `3e516bd` is dormant. Its 19 drafts are archived under
`docs/dormant_brainvision_post_blocker2_r4/` (commit `18df353`), and the
committed `blocker2_r4_*` source modules under `research/brainvision/` are
dormant alongside them.

They are historical material. They are not active prerequisites, not unfinished
obligations, and not governance instruments in force. Nothing in that chain
requires completion for this lane to be closed.

## What is preserved

- Canonical retained results under `research/brainvision/results/` - untouched,
  and to remain so.
- The findings, specification and authorization documents that establish the
  above.
- The dormant R4 and durable-evidence engineering, kept for provenance and
  reference rather than deleted.

## Test baseline at closure

Authoritative native Windows checkout:

```text
pytest -q tests/research -p no:cacheprovider
1513 passed, 1 skipped
```

## What is deliberately not being done

- No BLOCKER-4.
- No completion of the R4 or authority chain.
- No live kernel, memory, prompt, action or production integration.
- No claim that Brainvision provides production vision capability or any
  temporal-order capability.
- No rerun, threshold adjustment, witness replacement or reinterpretation of
  the retained result.

## Future LLM-facing work

Any future LLM-facing experiment must be a **separate, isolated, one-way
descriptor probe**, scoped and authorized on its own terms. It is not a
continuation of this closed lane, and this closure does not carry authority
forward into it.
