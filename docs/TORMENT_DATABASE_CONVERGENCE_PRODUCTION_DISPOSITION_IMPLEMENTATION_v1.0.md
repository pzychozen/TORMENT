# TORMENT production disposition implementation v1.0

**Status:** implemented and disposable-qualified. This document records code
implementation of the ratified v1.2 contract; it does not authorize or record
real-root disposition or P7.

## Boundaries preserved

- `TrajectoryWriterHandoffCoordinator` owns only the durable trajectory
  generation/session protocol in
  `substrate/trajectory_writer_handoff/authority.sqlite` and scope locks.
- `CharacterStore` remains the semantic Character state owner. The rebaseline
  operation changes only `distance_to_seed` and `drift_direction`, with an
  operation sidecar containing redacted state/seed/input digests.
- Seven receipt-only records consume exactly bound evidence. The two
  synthetic-only records are classification evidence only; neither has a
  production mutation path.
- The root adapter invokes owners but has no selector method. Canonical P7 is
  still the explicit `OfflineCutoverController` action.

## Writer authority law in code

`TrajectoryScopeIdentity.exclusivity_key` hashes exactly the data-root
identity, `RootScopeKey` identity payload, legacy source namespace, and
canonical artifact root. Every legacy `MemoryGraph` and native
`NativeTrajectoryEvidenceRuntime` trajectory effect obtains the durable token
immediately before construction, genesis, reset, frame, classification event,
legacy append, or V2 close. A runtime constructed before sidecar installation
discovers it at its next effect; an already-issued token is never refreshed.

The only forward states are:

```text
LEGACY_AUTHORITATIVE -> QUIESCING -> LEGACY_QUIESCED
-> NATIVE_ADMITTING -> NATIVE_AUTHORITATIVE -> HANDOFF_COMPLETE
```

All effects have a durable prepared/settled intent while holding the same
OS-backed scope lock as a fence transition. A partial intent blocks the fence;
there is no legacy reactivation or automatic rollback.

## Production receipt / P7 law

`ProductionRootDispositionAdapter` emits owner-specific production receipt
tokens only after a Character receipt, an aggregate trajectory receipt, or
bound existing evidence has validated. Before selector activation,
`OfflineCutoverController.activate_root_external_selector` reopens and checks
the Character successor receipt and current trajectory aggregate/session
state. Missing, partial, wrong-core, wrong-plan, or wrong-envelope proof is a
refusal. The lower-level selector transition remains an internal primitive;
the root controller is the canonical P7 path.

## Review matrix

`CLAUDE_REVIEW=UNAVAILABLE`; an internal bounded review and tests cover:

| Question | Result |
| --- | --- |
| Stale legacy writer after fence | Refused before artifact effect. |
| Two native writers for one scope | One current session/generation only; stale token refuses. |
| Crash or partial state | Durable phase/intent/operation records recover or refuse; no rollback. |
| Partial aggregate | Refused unless exact expected scope census is terminal and current. |
| Receipt-only / synthetic-only mutation | None exists in the adapter. |
| Character semantic expansion | Refused; only the two ratified fields may differ. |
| Disposition activating selector | Impossible: adapter exposes no selector operation. |

## Disposable qualification

Focused tests cover cross-process legacy/native races, restartable Character
operations, native target-geometry observation, aggregate/P7 negatives, and a
full disposable P6 -> production disposition -> P7 continuation with a native
trajectory artifact write and stale legacy refusal. The real P6-active root
was not opened for mutation.
