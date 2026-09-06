# TORMENT Database Convergence — Successor Real-Root P2

## Result

`SUCCESSOR_REAL_ROOT_P2 = PASS`

The P2-only successor operation began from `e2ac023ce12d461480e6ec10739b563f3c7deacb`, with `HEAD == origin/main` and a clean tracked worktree.  It used the repository-owned module entrypoint under the explicit Torment interpreter and repository cwd, with a successful no-contact import probe.

The runner re-established the required start state before any P2 write: selector generation 2 / `LEGACY_ACTIVE`, public `LEGACY_PUBLIC`, and native core `0e9cb4b7-cf57-49fa-b60a-0e5a25f9d288` as inert `STAGING / LEGACY_ACTIVE / never active / no witness`.  It recovered 154 active P1 memberships with closure `132d0a8f9253d84c2466da17b990a5b9018e42aae12b49ff3f8e5ff73296bb60`.

## Fresh frozen epoch and source identity

A new writer-freeze operation, `successor-real-root-p2-recoverable-external-pending-20260906`, passed bounded writer/listener/job checks, captured a fresh `t0`/`t1`/`t2` epoch with a 60-second stability interval, and rechecked immediately before the controller call.  The direct adapter used the frozen Phase-9B bindings `ws3|PRIVATE|a1`, `ws4|PRIVATE|a1`, and `ws5|PRIVATE|a1`; `orchard|PRIVATE|aria` remained `EMPTY_PRIVATE`, and the three Phase-9B private scopes remained `UNKNOWN_IDENTITY -> REEMBED_FROM_CANONICAL_SOURCE`.

```text
WORKSPACE_TREE_DIGEST = 52ff2f04d839015d43ef73a0ad02415d19587126ff2e6e0b3fbe4737f4487275
WORKSPACE_FILE_COUNT = 1748
WORKSPACE_MAX_MTIME_NS = 1788363578805346200
ROOT_DESCRIPTION_DIGEST = 8b2f036836dca398273100b4447256c93d71519edba9aec49fe35702d40d1dc4
RUNTIME_SCOPE_PLAN_DIGEST = bf15b13deb855bf4ecdf46fb532c151ca29874814ed8ba6b01795524052036ac
QUALIFIED_PROFILE_DIGEST = 562e55a8a3b6cf952cac933aacd00997e938d1b58116f825942b5d9420e07c3f
SUCCESSOR_WRITER_EVIDENCE_DIGEST = b4ddc8f5a4048c3f368d6fb274156aa5b48cec5065974f60eb327d58861c02bc
SUCCESSOR_WRITER_FREEZE_WITNESS_DIGEST = 56a5280c1bea7c5ce48d4dcd62949272894d8dc73a8b15c388b8e714e526a457
```

## Controller-persisted P2 evidence

The operation called only `OfflineCutoverController.enter_root_external_pending(request)`.  The historical envelope was retained untouched; no evidence was fabricated for it.  The controller persisted and reread successor envelope B and its full writer-freeze evidence record before selecting the core.

```text
HISTORICAL_P2_ENVELOPE_RETAINED = YES
HISTORICAL_P2_ENVELOPE_DIGEST = cf4204318974458f986f99efae39a4ead0fe0cb984b3bf520266b68308cbe436
SUCCESSOR_P2_ENVELOPE_DIGEST = 99e4445739ea2c4edc478d2c246bb0cdc9864318df0cf5dea3a3be7667e5818f
SUCCESSOR_ENVELOPE_DISTINCT_FROM_HISTORICAL = YES
ROOT_ADMISSION_ENVELOPE_RECORD_COUNT = 2
HISTORICAL_WRITER_EVIDENCE_RECORD = ABSENT_EXPECTED
SUCCESSOR_WRITER_EVIDENCE_RECORD = PRESENT
SUCCESSOR_WRITER_EVIDENCE_EXACT_REREAD = PASS
SUCCESSOR_P2_PROCESS_LOSS_EVIDENCE_RECOVERY = PASS
```

For the process-loss proof, the runner discarded its in-memory capture and request/result objects after the controller returned.  It then recovered B solely through the selector descriptor, `RootAdmissionEnvelopeRecord`, and `RootWriterFreezeEvidenceRecord`; decoded the exact payload and witness; required their binding; and required the payload digest and frozen tree to agree with the envelope.  No fresh P3 recheck was run.

## Final fenced state

```text
SELECTOR_GENERATION = 3
SELECTOR_STATE = CUTOVER_PENDING
PUBLIC_DEPLOYMENT = MAINTENANCE_ONLY
CORE_ROLE = STAGING
CORE_DEPLOYMENT_STATE = LEGACY_ACTIVE
CORE_EVER_ACTIVE = NO
CORE_WITNESS = NONE
P1_MEMBERSHIP_COUNT = 154
P1_MEMBERSHIP_CLOSURE_PRESERVED = YES
NORMALIZATION_EXECUTED = NO
P3_EXECUTED = NO
P4_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
LEGACY_SOURCE_MUTATION = NONE
PROVIDER_CONTACT = NONE
MODEL_LOADING = NONE
STOPPED_FOR_SUCCESSOR_P2_REVIEW = YES
```

P3 and every later phase remain separately authorized.  This operation performed no normalization, embedding, model loading, provider contact, legacy-source mutation, or core activation.
