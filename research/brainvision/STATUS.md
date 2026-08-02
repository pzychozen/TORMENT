# Brainvision - status

Brainvision is a **closed offline research lane**. Nothing in it is an active
prerequisite for other TORMENT work, and nothing in it is wired into the live
system. This file is a signpost, not a governance instrument.

## Scientific work - complete

The primary investigation is finished. The frozen conclusion is:

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

recorded in
`docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATION_FINDINGS_v0.1.md`
as a valid authoritative frozen-family negative. The single F3 evaluation
authority is consumed and no rerun is authorized.

That same record carries `SCIENTIFIC_INFERENCE_AUTHORIZED = False` and
`PRODUCTION_INTEGRATION_AUTHORIZED = False`. The negative stands on its own
terms; it is not licence to infer beyond the frozen family.

## Engineering blockers

| Blocker | State |
| --- | --- |
| BLOCKER-1 - Windows directory durability | Closed, within its authorized synthetic-offline local-fixed-NTFS tmp-path scope |
| BLOCKER-2 - directory promotion primitive | Engineering completed at `3e516bd` |
| BLOCKER-3 - resource admissibility | Closed |
| BLOCKER-4 | Never opened |

## Dormant machinery

`docs/dormant_brainvision_post_blocker2_r4/` holds the 19 post-BLOCKER-2 R4 and
authority drafts, with a README explaining their status. The committed
`blocker2_r4_*` source modules under `research/brainvision/` are dormant in the
same way.

Both are kept for provenance and for future readers of those modules. Neither
is unfinished work, an outstanding obligation, or a governance instrument in
force.

## Canonical results - leave untouched

`research/brainvision/results/` holds retained outputs from authorized runs.
Do not create, delete, move, or regenerate anything under it.

The research tests snapshot canonical FINAL/STAGING existence at import and
assert it is unchanged at the end - they neither create nor remove a canonical
result directory.

## Test baseline

Authoritative Windows run:

```text
pytest -q tests/research -p no:cacheprovider
1513 passed, 1 skipped
```

## Future work

Any future LLM-facing descriptor experiment is a **separate, isolated, one-way
descriptor probe** - a new lane with its own scope, not a continuation of this
one. Closure here is not a pause, and reopening Brainvision is not the route to
that work.
