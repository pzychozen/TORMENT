# TORMENT Database Convergence — Real Root Disposition and P7

Date: 2026-09-10

## Result

`REAL_ROOT_DISPOSITION_EXECUTION = PASS`
`REAL_P7 = PASS`

- Corrected core: `f21c730f-5222-4aa8-9a5f-1c1188456df3`
- P6 receipt: `f5efc57f-28a0-4ce2-bfc4-2787c15bafb1`
- Root disposition receipt digest: `c49d34e8d099e795973994d8077a6a940633eb11b3e556bed014035ff8745293`
- Selector: generation `8`, `NATIVE_ACTIVE`
- P7 operation: `B5-A5:real-root-p3-production-20260909:envelope-d-recovery:root-external-active`

The real production adapter completed the one Character disposition class
(36 retained current-state successors; the ratified `ryuki/ryuki_nox` state
remains absent), seven receipt-only classifications, two synthetic-only
classifications, and the exact declared materialized trajectory census:

```text
runtime plans                         154
materialized trajectory scopes        124
completed trajectory receipts         124
unaccounted / overlapping scopes      0 / 0
root owner results                    11
```

The 30 unmaterialized shared runtime plans were preserved and were not given
trajectory authority. Model D remains 76 private plans with `motif_domain_id`
unset. Certified refusals remain 35 memory and 23 motif records with no
runtime leak.

The final read-only diagnostic reports `NATIVE_AGREEMENT`, `NATIVE` public
backend, `admission_identity_matches = true`, and
`completion_witness_valid = true`. No legacy restoration or selector rollback
occurred.

## Bounded post-P7 production smoke

The authorized, qualified-native smoke completed after selector activation.
It used the selected `NativeProductionResourceOwner` for one ordinary native
create followed by one native reinforcement, in a private scope with no
retained Character state:

```text
workspace / agent                  audit_smoke_v0_2 / smoke_runner
native memory EID                  5
private native query               PASS (3 qualified hits)
shared native query                PASS (0 qualified hits; valid empty result)
native create / reinforcement      PASS / PASS
Character successor continuity     PASS
private/shared isolation           PASS
fresh-owner restart recovery       PASS
native trajectory write            PASS (private and shared representative scopes)
stale legacy trajectory write      REFUSED
conflicting native writer          REFUSED
```

The after-smoke refusal audit is still exact: 35 memory refusals have zero
ordinary-native successors, representations, or usable runtime embeddings;
all 23 motif refusals remain absent from target aliases and the runtime reader.
The independent after-smoke root verifier again proved the same valid root
receipt, 124/124 trajectory aggregate, selector generation 8, and
`NATIVE_AGREEMENT`.

## Recovery correction

The real Character successors legitimately changed workspace files after the
P2 snapshot. The controller now recognizes an already-recorded, production-
verified root disposition receipt for P7 recovery rather than treating those
authorized successors as a pre-disposition source-epoch rewrite. This fallback
requires the active core, selected core, typed P6 completion witness, selector
envelope binding, durable receipt, and production owner proofs to agree.

The native Character target-geometry digest also now canonicalizes immutable
nested payload mappings before hashing; it does not broaden accepted values.

## Validation

- Focused production files, run in fresh pytest processes: **35 passed**
  (`9 + 9 + 10 + 1 + 1 + 5`). They cover Character baseline, trajectory
  handoff and fencing, production disposition, root-v2 recovery, and P7
  recovery.
- A Windows spawned-process test exposed a lock-file race: a peer could deny a
  pre-lock byte read. The coordinator now atomically initializes the one-byte
  lock file and reads no lock byte before acquiring its OS lock. Its dedicated
  multiprocess suite passes 9/9 after that correction.
- One combined cross-file pytest pass exposed disposable-fixture state coupling
  in a root-v2 test; that test passes independently in a fresh process. This is
  not a production-state discrepancy.
- Real post-P7 verifier: receipt valid, 124/124 aggregate, selector native,
  diagnostic native agreement.

The next authorization boundary is `POST_P7_NATIVE_PRODUCTION_VALIDATION`.
