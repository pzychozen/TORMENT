# Checkpoint — Gap C: Spirit-Return Summary Relationship Lock (Memory-to-Prompt)

**Status:** CLOSED. Test-only regression lock; **no production change**.
**Date:** 2026-06-06
**Commit:** `aab9f5d` — `test(spirit-return): lock summary parity and budget divergence`
**New file:** `tests/test_spirit_return_summary_parity.py` (4 focused tests)
**Lineage:** Claude audit-first read-only trace → GPT framing refinement (invariant set) → Codex adversarial review (narrow, read-only) → test-only implementation → Windows-authoritative validation and push (Hilmir).
**Audit baseline for the trace:** `d47c76f`.

---

## 1. What closed, and why the wording changed

Gap C was parked in `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_3_SPIRIT_RETURN.md`
§A under the shorthand:

```
character_context.spirit_return_summary
must agree with
assembly_audit.spirit_return_summary
when both fire
```

Audit-first tracing showed that **naive equality would misencode the live
documented contract**. The two summaries deliberately measure different
stages:

```
character_context.spirit_return_summary
  = retrieval-stage observability
    (post-top-k, post-FILTER-A query hits;
     character.py:905-962, built inside fabric.query at fabric.py:4412-4418)

assembly_audit.spirit_return_summary
  = entered-prompt-stage observability
    (post-token-budget assembled blocks;
     assembly_audit.py:482-514 over assembled.blocks)
```

The audit-side helper's docstring states the distinction explicitly:
*"Reports what entered prompt context (not what was retrieved); these can
differ when budget skips spirit-return hits."* The assembler bridge
(`retrieval_assembler.py:266-274`) copies `from_spirit_return`,
`spirit_return_mode`, and `warmth_score` 1:1 from hit to block metadata, so
the audit population is by construction a subset of the character population.

An unconditional `==` test would therefore have been wrong twice over: it
would fail spuriously under token pressure, and it would flatten two
intentionally distinct observability stages into one.

## 2. The locked relationship

```
1. Conditional parity — with ample token budget and no dropped
   spirit-return hit, shared fields agree exactly:
   total, canonical by_mode, avg_warmth.

2. Audit-side subset — audit.total <= character.total, and per
   canonical mode audit.by_mode[m] <= character.by_mode[m].

3. Designed divergence — with a constrained budget that drops a
   spirit-return hit, audit.total < character.total is correct
   intended behavior, not a bug (selection_log records
   skipped_budget_exhausted for the dropped hit).

4. Audit-only truthfulness — any_entered_prompt exists only on the
   audit summary and remains truthful, including the zero-entered
   case (total=0, any_entered_prompt=False) while the character
   summary still reports the retrieved hit.
```

Comparison is on shared fields only; `any_entered_prompt` stays
audit-specific.

## 3. The production seam (verified single-caller facts)

As of the trace baseline `d47c76f`:

```
POST /retrieve  →  assemble_context()  →  build_assembly_audit()

assemble_context():      one production caller (app.py:1443)
build_assembly_audit():  one production caller (app.py:1494, opt-in)
all other callers:       tests only
```

`/retrieve` is the sole production seam composing both summaries. The test
module records this fact in its docstring so that if a second production
caller ever appears, the lock's scope is explicit rather than silently
overclaiming. Both surfaces derive from the same post-FILTER-A hit list on
this path; the only divergence mechanism is token-budget block selection.

## 4. Implementation record

`tests/test_spirit_return_summary_parity.py`, commit `aab9f5d`. Four
constructor-level tests mirroring the production seam without HTTP:

```
test_ample_budget_shared_fields_match_character_summary
test_audit_summary_counts_are_never_larger_than_character_counts
test_constrained_budget_allows_audit_summary_to_be_lower
test_any_entered_prompt_is_audit_only_and_truthful
```

Design decisions held: constructor-level only (HTTP smoke deliberately not
added — `tests/test_assembly_audit_wiring.py` and
`tests/test_spirit_return_surfacing_v0_2_3.py` already cover `/retrieve`
wiring); every fixture hit carries an explicit `warmth_score`; the real
assembler bridge runs before the audit summary is built; the "both fire"
phrase was dropped in favor of structural preconditions (fixtures contain
spirit-flagged hits). Production edits: **none**.

## 5. Validation evidence (Windows-authoritative)

```
new parity module: passed
focused surrounding spirit-return surface: passed
full Windows pytest suite: passed
```

Pre-slice baseline for reference: 3,812 passed / 5 skipped / 22 subtests at
`d47c76f`; this slice adds 4 tests and touches no production code.

## 6. Non-goals preserved (observed, parked, not widened)

```
unknown-mode vocabulary asymmetry:
  character-side by_mode is open-ended (setdefault); audit-side by_mode is a
  fixed three-mode vocabulary (unknown modes counted in total, dropped from
  by_mode). Live spirit_return.py emits only canonical modes. Observed and
  parked; NOT widened into mode validation.

synthetic warmth fallback asymmetry:
  character side falls back to 0.2; the audit helper falls back to 0.0. The
  real assembler bridge stamps warmth_score (default 0.2) into block
  metadata, so the audit's 0.0 fallback is unreachable via the production
  path. Observed and parked; excluded because the lock exercises the real
  bridge with explicit warmth values.

immediate spirit-return influence audit:
  still named but unopened (surface map Bucket I). Gap C's closure does NOT
  open it.

broader retrieval-stack audit:
  still named but unopened (surface map Bucket P).
```

## 7. Posture after closure

```
Gap C:                          closed (test-only)
production behavior:            unchanged
maintenance lane:               closed (d47c76f)
Track B:                        parked
retrieval influence audits:     named, unopened
next substantive gate:          intentionally unselected
```

---

*End of Gap C checkpoint. The closure deliberately locks the relationship
between two observability stages rather than forcing them equal: retrieval-
stage and entered-prompt-stage truth remain distinct, and future work cannot
accidentally flatten them into the same thing.*
