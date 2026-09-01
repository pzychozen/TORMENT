# 7G5E4D Authorized Share-Proposal Native Materialization

Status: qualification-only. This document records a bounded storage adapter;
it does not describe production backend selection.

Proposal authority remains in TORMENT. Existing `process_proposals()` decides
quorum and its representative, while `decide_proposal()` decides operator
approval. The native adapter accepts only their already-authorized facts and
uses the prepared `NativeFabricRoutingCapability` plus
`NativeFabricMemoryRouter` to write a STAGING core. It cannot mark proposal
status, create bridge or conflict records, or make domain suggestions.

The materializer maps a quorum write to `SOURCE_SHARE_PROPOSAL` /
`WRITE_SHARE_PROPOSAL_QUORUM` using
`ProvenanceV1.for_share_proposal_quorum()`. All content-contributing proposal
creation timestamps, including a `collective_echo`, are supplied to that
factory; only existing authority supplies the sorted genuine `support_agents`.
The operator path maps to the corresponding operator factory and carries only
the approved proposal's timestamp. Both paths preserve `parent_eids=[]`.

Legacy `canon=True` materialization, including its
`lifecycle_status.set_by.via=canon_set` envelope, maps to native `lifecycle_state=PROTECTED`,
`lifecycle_authoritative=True`, `governance_state=EXPLICIT`, all-false explicit
governance facts, and `authority_category=NOT_APPLICABLE`. `canon=True`
remains in the compatibility payload. Shared `scope` is represented by the
claimed native semantic scope rather than duplicated into flexible payload,
because the existing payload-shadow policy reserves `scope` as structural.
The router owns native structural lifecycle storage; the adapter does not
invent a second lifecycle envelope.

The adapter receives a caller-supplied stable operation key and an explicit,
retry-stable storage clock. No random key or wall-clock value is generated.
Qualification freezes the operator's existing wall-clock step only to compare
legacy and native facts. Production ownership of retry-stable operator
operation-step/time is still BLOCKER-5 and a selector/cutover prerequisite.

This slice adds no production selection or attachment behavior:
`process_proposals()` and `decide_proposal()` remain legacy-only,
`NativeMemoryRuntimeBinding` remains inert, and native active, dual-write,
dual-read, and cutover remain closed.
