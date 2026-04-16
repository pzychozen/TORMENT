# TORMENT Spine Contract

**Version:** 1.0
**Status:** Active
**Last Updated:** 2026-03-28

## 1. Spine as Official External Interface

The Agent Spine (`POST /spine/submit_task`) is the **official external write interface** for all governed operations against TORMENT memory.

### Preferred Interface

All external consumers (MCP servers, HTTP clients, future protocol adapters) should use:

```
POST /spine/submit_task
```

This is the **single authoritative entrypoint** for write operations. It provides trust enforcement, per-agent serialization, auto-escalation, drift monitoring, structured audit, and a governed response envelope on every call.

### Legacy Compatibility Layer

The following legacy endpoints remain available for backward compatibility. Internally, they construct a `SpineRequest` and route through the Spine. They are **not recommended for new integrations**.

| Legacy Endpoint | Spine Operation | Status |
|---|---|---|
| `POST /agent/ingest` | `ingest` | Shimmed through Spine |
| `POST /agent/feedback` | `feedback` | Shimmed through Spine |
| `POST /collective/reingest` | `collective_reingest` | Shimmed through Spine |
| `POST /memory/governance/set` | `memory_governance_set` | Shimmed through Spine |

New consumers should never call legacy endpoints directly. They exist only to avoid breaking existing deployments during migration.

### Discovery

```
GET /spine/operations
```

Returns all registered operations, their trust requirements, default paths, operation classes, and escalation eligibility.

---

## 2. Request/Response Contract

### SpineRequest

```json
{
  "workspace_id": "string",
  "agent_id": "string",
  "operation": "string",
  "payload": {},
  "mode": "auto"
}
```

`mode` options: `"auto"` (default, recommended), `"fast"`, `"full"`.

### SpineResponse Envelope

Every response wraps the Fabric result with governance metadata:

```json
{
  "ok": true,
  "path": "fast",
  "operation": "ingest",
  "allowed": true,
  "workspace_id": "ws1",
  "agent_id": "atlas",
  "trust_tier": 0.6,
  "drift_status": "green",
  "decision_code": "fast_allowed",
  "result_code": "stored",
  "result": { "...fabric result..." },
  "audit": { "client_id": "...", "trust_tier": 0.6 },
  "task_id": "spine_a1b2c3d4e5f6",
  "escalated": false,
  "escalation_reasons": [],
  "elapsed_ms": 12.34
}
```

### Decision Codes

| Code | Meaning |
|---|---|
| `fast_allowed` | Routed to fast governance path, executed normally |
| `full_allowed` | Routed to full cognition pipeline, executed normally |
| `escalated_full` | Auto-escalated from fast to full (see `escalation_reasons`) |
| `blocked_unknown_operation` | Operation not in registry |
| `blocked_insufficient_trust` | Caller trust tier below minimum |
| `blocked_no_handler` | No handler in fast dispatch table |
| `error_dispatch` | Handler raised an unexpected exception |
| `error_trust` | Trust error during dispatch |

### Result Codes

| Code | Meaning |
|---|---|
| `stored` | New memory created (ingest, tool_result_ingest) |
| `reinforced` | Feedback applied (static); or reinforce moved at least one eid's per-memory significance (handler-driven, v2.4.x contract) |
| `no_op` | Reinforce call admitted but no eid moved (all missing, out-of-scope, or shared). Callers may trust this: no per-memory state changed. |
| `reingested` | Collective reingest completed |
| `queried` | Read-only query returned results |
| `governed` | Governance flags updated |
| `compressed` | Compression cycle ran |
| `cognition` | Full cognition pipeline completed |
| `state_read` | Agent state snapshot returned |
| `none` | No result (blocked or errored) |

### Escalation Reason Codes

When `escalated: true`, the `escalation_reasons` array contains one or more of:

| Code | Trigger |
|---|---|
| `identity_sensitive` | Payload contains seed/canon/identity keywords |
| `high_drift` | Drift score exceeds 0.20 threshold |
| `protected_memory` | Protected or canon memory flag in payload |
| `borderline_trust` | Trust is within 0.1 of the required minimum |
| `open_ended_request` | Payload is long text (>500 chars) with multiple question marks |

---

## 3. Operation Registry

### Operation Classes

Every operation belongs to exactly one class. Classes enable policy grouping for trust, exposure, logging, rate limiting, and client capability negotiation.

| Class | Description |
|---|---|
| `read` | Read-only queries, no state mutation |
| `write` | Creates or modifies individual agent memory |
| `collective` | Cross-agent / hive-mind operations |
| `identity` | Modifies agent seed, character, or identity |
| `cognitive` | Full multi-role cognition pipeline |

### Complete Operation Table

The `exposure_tier` field is set directly on each `OperationSpec` in `spine.py` and is returned by `GET /spine/operations`. The MCP server reads this field at startup to determine what to expose — **docs and code cannot drift apart**.

Use `get_exposed_operations(max_tier)` in code to query the registry:
- `get_exposed_operations("open")` → 5 Tier 1 operations
- `get_exposed_operations("guarded")` → 9 Tier 1 + Tier 2 operations

| Operation | Class | Exposure | Path | Min Trust | Escalatable | Description |
|---|---|---|---|---|---|---|
| `query_state` | read | open | fast | 0.0 | no | Read agent state / identity / character |
| `query_memory` | read | open | fast | 0.0 | **yes** | Search agent memory |
| `ingest` | write | open | fast | 0.6 | **yes** | Ingest text as new memory |
| `feedback` | write | open | fast | 0.3 | no | Operator/outcome signal → overlay mutation |
| `reinforce` | write | open | fast | 0.3 | no | Per-memory evidence signal → per-memory significance mutation (result_code: `reinforced` or `no_op`) |
| `memory_governance_set` | write | guarded | fast | 1.0 | no | Update governance flags |
| `compression_run` | write | guarded | fast | 1.0 | no | Trigger compression cycle |
| `collective_reingest` | collective | guarded | fast | 0.9 | **yes** | Re-ingest convergence event as echo |
| `collective_policy_change` | collective | internal | full | 1.0 | no | Modify collective policy parameters |
| `proposal_review` | collective | internal | full | 0.9 | no | Review and decide on proposals |
| `identity_rewrite` | identity | internal | full | 1.0 | no | Rewrite agent seed or identity |
| `seed_change` | identity | internal | full | 1.0 | no | Change agent character seed |
| `cognition_run` | cognitive | guarded | full | 0.6 | no | Run full 4-role cognition pipeline |
| `role_conflict_resolution` | cognitive | internal | full | 1.0 | no | Resolve inter-role conflicts |
| `architecture_review` | cognitive | internal | full | 1.0 | no | Full pipeline review of change |
| `tool_result_ingest` | write | guarded | fast | 0.6 | no | Ingest externally obtained tool output as memory |

---

## 4. MCP Exposure Matrix (v1)

This matrix defines which operations should be exposed through the MCP protocol boundary in the first release, and under what constraints.

### Exposure Tiers

- **Tier 1 — Open:** Exposed to any authenticated MCP client. Low risk, high utility.
- **Tier 2 — Guarded:** Exposed with elevated trust requirement. Moderate risk, specific use cases.
- **Tier 3 — Internal:** Not exposed through MCP in v1. Requires direct API or operator access.

### Exposure Decision Matrix

| Operation | MCP Tier | Exposed? | Rationale |
|---|---|---|---|
| `query_state` | Tier 1 | **Yes** | Read-only, essential for any MCP integration |
| `query_memory` | Tier 1 | **Yes** | Read-only with auto-escalation for safety |
| `ingest` | Tier 1 | **Yes** | Core write operation, trust-gated at 0.6 |
| `feedback` | Tier 1 | **Yes** | Essential feedback loop, low trust requirement |
| `reinforce` | Tier 1 | **Yes** | Same as feedback, different semantic |
| `collective_reingest` | Tier 2 | **Maybe** | Cross-agent mutation, requires trust 0.9. Expose only for collective-enabled clients. |
| `compression_run` | Tier 2 | **Maybe** | Maintenance operation, operator trust. Expose only for admin MCP clients. |
| `memory_governance_set` | Tier 2 | **Maybe** | Governance mutation, operator trust. Expose only for admin MCP clients. |
| `cognition_run` | Tier 2 | **Maybe** | Expensive full pipeline. Expose with rate limiting and elevated trust. |
| `tool_result_ingest` | Tier 2 | **Maybe** | Governed tool-result memory write. Not tool execution. Expose for MCP clients that supply external tool output. |
| `proposal_review` | Tier 3 | **No** | Internal collective governance. Not v1 MCP. |
| `collective_policy_change` | Tier 3 | **No** | Policy mutation too sensitive for broad MCP access. |
| `identity_rewrite` | Tier 3 | **No** | Identity mutation must never be MCP-accessible in v1. |
| `seed_change` | Tier 3 | **No** | Same as identity_rewrite. |
| `role_conflict_resolution` | Tier 3 | **No** | Internal cognitive maintenance only. |
| `architecture_review` | Tier 3 | **No** | Internal cognitive maintenance only. |

### MCP v1 Tool Surface (Recommended)

Based on the matrix above, the MCP server should expose these tools:

**Core tools (always available):**
1. `torment_query_state` — read agent state
2. `torment_query_memory` — search agent memory
3. `torment_ingest` — create new memory
4. `torment_feedback` — provide reinforcement feedback

**Extended tools (available to elevated clients):**
5. `torment_collective_reingest` — re-ingest convergence events (trust >= 0.9)
6. `torment_cognition_run` — run full cognition pipeline (rate-limited)

**Admin tools (operator-only MCP clients):**
7. `torment_compression_run` — trigger compression
8. `torment_governance_set` — update governance flags

**Never exposed as MCP tools in v1:**
- `identity_rewrite`, `seed_change`, `collective_policy_change`, `proposal_review`, `role_conflict_resolution`, `architecture_review`

### MCP Resources (Read-Only Context)

In addition to tools, the MCP server should expose these as **resources** (read-only context that hosts can pull):

- `torment://workspace/{ws_id}/agent/{agent_id}/state` — agent identity, drift, memory count
- `torment://workspace/{ws_id}/agent/{agent_id}/memory?query={q}` — memory search results
- `torment://workspace/{ws_id}/health` — workspace health summary
- `torment://workspace/{ws_id}/operations` — available operations and trust requirements

---

## 5. Design Rules

1. **Fabric never receives direct external calls for write operations.** Everything goes through the Spine.
2. **Trust is checked at the Spine, not at the Fabric.** Fabric assumes its caller (the Spine) has already validated trust.
3. **Locking is handled by Spine fast handlers.** Fabric methods are not expected to self-lock.
4. **Auto-escalation is a Spine decision.** Fabric has no concept of fast vs full paths.
5. **The response envelope is the Spine's contract.** MCP and HTTP consumers should parse the envelope, not raw Fabric results.
6. **Legacy endpoints are compatibility shims.** They internally construct SpineRequests and call `submit_task`. New code should never add new legacy-style endpoints.
7. **The thinking layer is advisory, not authoritative.** When enabled (`TORMENT_THINKING_ADVISORY=1`), the thinking controller runs alongside Spine to provide task framing, memory planning, and stance recommendations. It never writes memory, never blocks execution, and never overrides Spine decisions. See `docs/advanced_cognition.md` for details.
8. **Tool-result ingest is memory, not execution.** The `tool_result_ingest` operation stores externally obtained tool output as provenance-tagged memory. It does not execute tools, dispatch actions, create automation loops, or grant execution authority. TORMENT may remember what tools returned before it is ever allowed to decide what tools to run.
