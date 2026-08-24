# TORMENT Hivemind Experimental Baseline v1.0

**Status:** frozen experimental baseline

**Repository:** `pzychozen/TORMENT`

**Frozen implementation HEAD:** `5a1c1b53cd0c368f6a8ba4238f959ab8257355ab`

**Freeze date:** 2026-08-24
**Telemetry commit:** `5a1c1b53cd0c368f6a8ba4238f959ab8257355ab` — `instrument-hivemind-structured-telemetry`

## 1. Baseline identity

This is the authoritative Hivemind baseline from which Meridian Outage
experimentation begins.  The baseline requires a clean worktree at the frozen
implementation commit before an experiment is administered.  A documentation
commit that records this freeze is an allowed successor, but does not change
the frozen implementation identity above.

The frozen production/test state includes the structured-telemetry change and
its focused Hivemind, collective, and observability regression surface.  This
freeze records the architecture under test.  It does not claim scientific
benefit.

## 2. What Hivemind currently is

TORMENT Hivemind is a workspace-scoped collective-attention /
epistemic-coordination layer in which private cognition remains agent-scoped,
eligible activity emits bounded collective signals, pairwise resonance produces
persisted salience, and propositional content reaches shared canon only through
separate governed promotion.

It is not:

- an autonomous swarm;
- a task orchestrator;
- all-to-all agent conversation;
- N-agent reasoning;
- or a direct memory merge.

## 3. Current implemented capabilities

At the frozen HEAD, the implementation provides:

- per-agent private `MemoryGraph` instances and a workspace shared
  `MemoryGraph`;
- eligible packet emission and pairwise convergence detection;
- append-only packet and convergence-event persistence;
- explicit collective-echo reingest, reingest deduplication, echo terminality,
  and echo provenance/discount;
- a proposal bridge and distinct-agent quorum handling;
- exclusion of collective artifacts from quorum authority;
- independent-authority ownership of canonical representative content;
- governed shared-canon promotion and workspace isolation; and
- optional structured Hivemind telemetry.

## 4. Automatic versus autonomous behavior

The following are automatic inside already-authorized operations:

- packet creation;
- convergence-event detection;
- persistence; and
- proposal-drafting side effects.

The implementation has no autonomous goal formation, scheduler, autonomous
task delegation, agent-spawning loop, authority expansion, or hidden
agent-to-agent execution chain.

## 5. Current collective-attention semantics

- `_recent_max = 200` is the packet-count working convergence window.
- It is not an agent-population cap and has no fairness or per-agent quota.
- Same-agent packet candidates are excluded.
- Skew may therefore create a hub topology; this is a measured covariate, not
  an implicit fairness guarantee.
- Convergence is pairwise and has only the detector's current event behavior.
- Persistent packet history is independent of the in-memory convergence
  window.

The value `200` is frozen for the initial experiment programme and must not be
reinterpreted or retuned.

## 6. Contentless salience behavior

`ResonancePacket.summary` contains content.  `ConvergenceEvent` does not
transmit the underlying proposition.  Downstream collective salience therefore
communicates that convergence occurred, not the source proposition itself.

Current automatic agent cognition does not consume `collective_context`.
The `retrieve_collective` planning surface exists, but is behaviorally inert in
the frozen B1 condition.

**CONTENTLESSNESS:** current design characteristic.
**COGNITIVE INERTNESS:** known unfinished lane.

Neither is repaired by the baseline experiment.

## 7. Known inert or partial mechanisms

The following are known covariates, not surprise findings:

- `CONVERGENCE_TIME_WINDOW` is currently inert;
- `CONVERGENCE_MIN_AGENTS` is currently inert;
- historical packet vectors are not restored across restart;
- adjacent-stage phase alignment has a format mismatch;
- `collective_context` is not consumed by `AgentRunner`;
- the event query path scans full event history;
- quorum remains population-invariant; and
- collective-policy and flags limitations already characterized in the
  repository remain as-is.

## 8. Post-repair representative-content invariant

Shared canonical summary, embedding, and primary mtype must come from a
proposal contributing independent-agent authority.

Collective-derived artifacts may remain grouped, approved, provenance-bearing,
and listed in source proposal IDs, but may not replace authoritative
propositional content.

## 9. Telemetry contract

Enable optional decision telemetry with:

```text
TORMENT_HIVEMIND_TELEMETRY=1
```

Truthy aliases are `true`, `yes`, and `on`; the default is disabled.  Records
are emitted through logger `torment.hivemind` at INFO level in
`LogRecord.hivemind_telemetry`.  Each packet-decision record currently carries:

- `event_kind`, `timestamp`, and per-Fabric `sequence`;
- `workspace_id`, `agent_id`, `domain_id`, and `source_eid` where available;
- `packet_emitted`, `gate_outcome`, `skip_reason`, and `coherence`;
- `provenance_class` when relevant; and
- `convergence_occurred`, `convergence_event_id`,
  `convergence_partner_agent_id`, and `semantic_similarity` when produced.

Telemetry is observational.  Enabled and disabled telemetry have been
characterized as producing identical packet/event semantic snapshots.  It must
not add model calls, retrieval, persistence, ordering, authority, or control
flow changes.

## 10. Experimental conditions

The initial Meridian Outage programme freezes four conditions.

### A — PRIVATE

Hivemind is disabled.  Agents retain private state; no collective signal or
shared Hivemind processing is available.

### B1 — TORMENT CURRENT

Hivemind is enabled exactly as frozen.  No collective-context prompt injection
is added.  If its collective signal is cognitively inert, that is the result.

### B2 — TORMENT + SALIENCE SURFACED

This is an explicitly labelled experimental extension of B1.  The only
addition is surfacing Fabric's already-existing `collective_context` verbatim
or through a strictly mechanical formatter to the next agent prompt/context.
It must not add peer packet summaries, peer private memories, an orchestrator,
model-generated summaries of other agents, task selection, or new collective
content.

### C — NAIVE SHARED CONTENT

Permitted agent findings are pooled into a simple, explicitly shared content
surface available to participating agents.  This arm must not silently copy
TORMENT quorum, governance, echo, or convergence semantics, and must not be
made artificially weak.

## 11. Scientific progression

The intended order is an untimed N=5 characterization, followed by formal N=5,
N=10, and N=25 experiments.  N=50 requires review.  Later conditional tiers
are N=100, N=200, N=500, and N=2000.

Listing a tier is not evidence of support or benefit.

## 12. Frozen non-changes

The initial baseline experiment does not modify:

- non-autonomy;
- terminal echoes or echo provenance discount;
- private/shared separation;
- contentless convergence events;
- the 200-packet window or quorum structure;
- append-only persistence;
- collective-context inertness in B1;
- phase alignment;
- post-restart vector behavior; or
- the event-history read path during early small-N characterization.

It also does not change packet fairness, agent population scaling, or
collective-context consumption outside the explicitly separated B2 extension.

### Operator and evidence discipline

The current system is non-autonomous.  Any future call to operations such as
proposal processing or convergence reingest must use a frozen deterministic
schedule, documented before the run.  The experiment harness must not choose
recipients or tasks intelligently.

All experimental inputs, raw outputs, telemetry, hashes, and result artifacts
must be durable and append-only by run.  Characterization and formal
administration are separate activities; first characterization results do not
authorize threshold tuning.

### Restart and attention covariates

Restart is outside the first formal task-quality comparison unless separately
pre-registered.  If a characterization restart is performed, it must record
that historical packet descriptors reload while historical packet vectors do
not; old packets therefore cannot semantically converge until fresh packets
repopulate effective active attention.

For N <= 50, retain cumulative event count and event-query latency as an
event-history-rescan covariate.  Also retain active-window count, distinct
agent IDs, per-agent occupancy, and event-degree distribution so possible hub
formation is measured rather than assumed to be a failure.

## 13. Scientific interpretation rule

> A null result is a valid result.

If B1 performs like A on task quality, the programme must not add hidden
orchestration or prompt injection to rescue the Hivemind condition.  B1 exists
to measure the current implementation honestly.

## 14. Evidence status

Prior 200–2,000-agent scale testing is user-reported historical engineering
evidence.  No auditable repository artifact currently establishes those runs.
The Meridian programme therefore creates fresh durable evidence instead of
treating past recollection as measured scientific result.
