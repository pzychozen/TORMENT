# 7G5E4D-R1 Proposal-Orchestration Recovery Receipts

## Boundary

R1 repairs retry recovery only for the explicitly qualified private native
proposal paths:

- `TormentFabric._process_proposals_with_qualified_native_storage`; and
- `TormentFabric._decide_proposal_with_qualified_native_storage` for an
  already-authorized `approve` decision.

Public `process_proposals` and `decide_proposal` still instantiate
`LegacyAuthorizedSharedProposalStorage` directly.  No production selector,
activation, native discovery, fallback, dual read/write, shared direct ingest,
vector replacement, kernel edit, generic transaction/saga, or global
`ProposalRegistry.mark` behavior was added.

```text
PRODUCTION_PROPOSAL_ORCHESTRATION = LEGACY
NATIVE_RECOVERY_SCOPE = PRIVATE_QUALIFICATION_ONLY
AUTHORITY_DECISION_OWNER = TORMENT
RECEIPT_OWNER = NATIVE_RECOVERY_LAYER
```

## Durable evidence design

`NativeAuthorizedProposalReceiptStore` uses the existing qualified native
core's `operations` ledger.  It creates no schema/table.  The ledger contract
permits an operation with canonical intent and zero semantic transitions,
targets, and outputs, which truthfully represents this receipt: evidence that
TORMENT already made an authority decision, not an alternate authority system.

Receipt records use `NATIVE_AUTHORIZED_PROPOSAL_RECEIPT_PREPARED`; separate
no-effect operations record stages and immutable completion evidence.  All are
under the caller's already claimed shared/collective/domain idempotency scope
and use short-lived qualified core connections.

A prepared quorum receipt freezes:

- schema (`7G5E4D-R1`), kind, `AUTHORITY_DECISION_OWNER=TORMENT`, workspace,
  domain, and prepared native-core ID;
- ordered source/group IDs, caller-emitted authority source IDs and agents,
  representative ID, quorum similarity/minimum, explicit step, and stable
  native storage key;
- native storage clock values and the exact pre-conflict candidate witness plus
  its digest;
- M1/M2 policy knobs, embedding provider/model, and the private process-call
  knobs used for a completed replay;
- a digest of immutable source facts: IDs, scope, agent, summary, embedding,
  type, confidence, strength, creation time, and half-life.  It intentionally
  excludes mutable `status`, `note`, and `processed_ts`.

An operator receipt freezes only an already-authorized `approve`; rejects and
collective-echo refusals do not receive a receipt.  A repeated preparation with
the same stable storage key returns the frozen receipt.  Any changed frozen
intent fails closed.  The storage adapter consumes receipt-provided key and
clock, so recovery never produces a fresh native materialization identity or
time.

## Recovery order

Before fresh private native processing, R1 lists incomplete quorum receipts in
the requested claimed scope.  It verifies current ProposalRegistry records
against each immutable digest without reconsidering quorum, grouping, or
representative selection.  Only after all incomplete receipts are reconciled
does it enumerate fresh pending proposals.

For each receipt, the fixed sequence is:

1. recover/materialize native shared storage with the receipt's key and clock;
2. read-before-append the frozen expected conflict; zero matches adds it, one
   match is already reconciled, and multiple matches fail closed;
3. use existing M1 maintenance (and existing M2 auto-merge when enabled), then
   record its stage;
4. reconcile source proposals: pending appends one approved event, approved
   skips, rejected/unknown/missing fails closed;
5. run and stage bridge suggestion;
6. run and stage domain suggestion; and
7. record immutable completion/result evidence before the response fault seam.

The completed private replay first verifies source facts, returns the frozen
result, and creates no proposal event, conflict, M1/M2, bridge, domain, or
native-memory duplicate.  Operator recovery uses the same source verification,
stable materialization, mark reconciliation, bridge/domain stages, and
completion evidence.

The existing M1, M2, bridge, domain-suggestion, vector, conflict, and proposal
stores remain their own owners.  R1 adds no broad atomicity claim across those
external stores; its durable stages make the specified recovery boundaries
resumable and prevent the characterized duplicate callbacks on replay.

## Fail-closed conditions

Recovery refuses malformed/noncanonical receipt, completion, or stage
evidence; a changed receipt intent for the same storage key; source-content
drift; missing source/representative; authority IDs outside the frozen source
set; rejected or unknown proposal status; ambiguous conflict state; unclaimed
scope; and an operator proposal already approved without qualified receipt
evidence.  A receipt presented through a different prepared native core is
also refused.  Completed replay verifies source facts before returning.

## Verification

Focused qualification covers:

- legacy/native normal and auto-merge parity, unchanged public routing, and
  unchanged authority/trace ordering;
- process fault boundaries A–G: one native memory, one conflict, one M1 event,
  three exactly-once proposal approvals, one bridge invocation, one domain
  invocation, and stable original result on recovery;
- cold restart after a partial quorum mark and after an operator lost response;
- completed replay with no additional semantic effects;
- receipt operations having zero `semantic_transitions`, `operation_outputs`,
  and `operation_targets`; and
- changed frozen intent, immutable source drift, storage-key/group mismatch,
  different-core receipt, and malformed ledger evidence failing closed before
  alternate materialization or proposal events.

The earlier retry-characterization document remains historical: its blocked
and duplicate results are superseded for the qualified native private paths by
this R1 recovery receipt boundary.  It remains accurate for the unchanged
public legacy methods.
