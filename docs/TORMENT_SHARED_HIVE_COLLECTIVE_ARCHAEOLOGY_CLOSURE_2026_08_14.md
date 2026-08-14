# Shared / Hive / Collective Archaeology Closure — 2026-08-14

`SHARED_HIVE_COLLECTIVE_ARCHAEOLOGY_V1 = CLOSED`

This closure records:

- `HIVE_PHASE2_CHARACTERIZATION_COMPLETE`
- `HIVE_CLOSURE_AUDIT_CLEAN`

## Characterized architecture

```text
private/shared MemoryGraph
  -> Hivemind packet
  -> workspace CollectiveField
  -> convergence
  -> pending collective proposal OR explicit private echo re-ingestion
```

Behavioral evidence confirmed that packet identity derives from runtime
workspace, agent, domain, and source scope; normal ingest payload cannot forge
that identity. It also confirmed echo terminality, restart re-ingest dedup,
cross-workspace zero crossing, and valid `non_shareable` governance blocking
packet emission.

The current policy behavior is characterized, not changed:

- `OPT_OUT_NOT_EXPOSED`
- `EVENT_DOMAIN_ONLY`
- `SELF_REINGEST_ALLOWED`

## E6: collective quorum authority seam

Hive-derived convergence proposals entered the pre-Hive proposal registry with
a participating `agent_id`. The historical distinct-`agent_id` consumer then
treated that derived artifact as independent agent evidence.

The repair preserves a collective proposal with
`mtype == "collective_echo"` as persisted, grouped, reviewable, content-bearing
evidence included in `source_proposal_ids`. It may participate under the
existing representative-selection wording once genuine quorum exists. It does
not contribute an independent-agent quorum vote.

```text
CONTENT CONTRIBUTION != AUTHORITY CONTRIBUTION
```

Regression evidence:

- one direct proposal plus one collective-derived proposal: no quorum and no
  shared canon;
- two genuine direct proposals: quorum and one shared canonical node preserved;
- two direct proposals plus a collective proposal: genuine quorum preserved,
  with collective evidence still grouped/content-bearing and `support_agents`
  reflecting genuine independent agents.

## Evidence and bounded terrain

Final evidence:

- E1/E3/E6 repair harness: 4 passed;
- initial broader Hive regression: 239 passed;
- expanded characterization: 7 passed;
- final broad Hive neighborhood: 242 passed, 1 warning;
- final closure audit: `HIVE_CLOSURE_AUDIT_CLEAN`.

Carry forward as bounded, non-blocking terrain:

- agent opt-out is not exposed;
- echo delivery is event-domain-only and self-reingestion is allowed;
- restart convergence is limited by the in-memory-only embedding cache;
- `source_eids` are graph-local, unqualified integers and are not dereferenced;
- packet/event `policy_flags` are mostly metadata-only;
- the pending collective-proposal cap check is vacuous while the production
  domain cooldown provides a bound;
- temporary `PACKET-GATE` stderr debug instrumentation remains.

## Core / Hive boundary

Core establishes graph-local EIDs, private scope as workspace plus agent,
shared scope as workspace plus domain, canonical persistence, and SQLite as a
derived index. Raw EIDs are unsafe across graphs.

Hive is the export, convergence, echo, and shared-canon authority-policy layer.
