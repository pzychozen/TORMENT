# MCP v1 Smoke Test Checklist

**Target:** Claude Desktop (stdio transport)
**Server:** `python -m torment_service.mcp_server`

## Setup

```bash
cd torment_fabric

# Create a test workspace with an agent before connecting
TORMENT_EMBED_PROVIDER=hash python -c "
from torment_service.fabric import TormentFabric
f = TormentFabric(data_dir='./smoke_data')
f.get_workspace('smoke_ws')
f.create_agent('smoke_ws', 'smoke_agent')
print('Workspace and agent created.')
"
```

Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "torment-memory": {
      "command": "python",
      "args": ["-m", "torment_service.mcp_server"],
      "cwd": "/path/to/torment_fabric",
      "env": {
        "TORMENT_MCP_DATA_DIR": "./smoke_data",
        "TORMENT_MCP_WORKSPACE_ID": "smoke_ws",
        "TORMENT_MCP_AGENT_ID": "smoke_agent",
        "TORMENT_MCP_TRUST_TIER": "0.6",
        "TORMENT_MCP_EXPOSURE_TIER": "open",
        "TORMENT_EMBED_PROVIDER": "hash"
      }
    }
  }
}
```

---

## 1. Connection & Discovery

| # | Test | Pass criteria | P/F |
|---|---|---|---|
| 1.1 | Start Claude Desktop with config | No error in logs, server process running | |
| 1.2 | Tools visible in host | 6 tools appear: `torment_submit_task`, `torment_ingest`, `torment_query_memory`, `torment_query_state`, `torment_feedback`, `torment_reinforce` | |
| 1.3 | Resources visible in host | 3 resource templates appear with `torment://` URIs | |
| 1.4 | No schema errors | Host does not report validation or schema errors on startup | |
| 1.5 | Server name shows as "torment-memory" | Correct name in host server list | |

---

## 2. Tool Sanity — One Valid Call Each

### 2.1 torment_query_state

| # | Test | Input | Expected | P/F |
|---|---|---|---|---|
| 2.1a | Valid call (defaults) | *(no args)* | `ok: true`, `result_code: "state_read"`, result has `workspace_id`, `agent_id`, `memory_count` | |
| 2.1b | Valid call (explicit) | `workspace_id: "smoke_ws"`, `agent_id: "smoke_agent"` | Same as above | |

### 2.2 torment_ingest

| # | Test | Input | Expected | P/F |
|---|---|---|---|---|
| 2.2a | Valid ingest | `text: "The sky turned violet at dusk."` | `ok: true`, `decision_code: "fast_allowed"`, `result_code: "stored"` | |
| 2.2b | Second ingest | `text: "Rain began falling gently."` | Same pattern, different eid | |

### 2.3 torment_query_memory

| # | Test | Input | Expected | P/F |
|---|---|---|---|---|
| 2.3a | Query after ingest | `query: "sky color"` | `ok: true`, `result_code: "queried"`, results include ingested text | |
| 2.3b | Query with explain | `query: "weather"`, `explain: true` | Same but with explanation data | |

### 2.4 torment_feedback

| # | Test | Input | Expected | P/F |
|---|---|---|---|---|
| 2.4a | Valid feedback | `retrieved_ids: "[1]"`, `used_successfully: "[1]"` | `ok: true`, `result_code: "reinforced"` | |

### 2.5 torment_reinforce

| # | Test | Input | Expected | P/F |
|---|---|---|---|---|
| 2.5a | Valid reinforce | `retrieved_ids: "[1]"`, `used_successfully: "[1]"` | `ok: true`, `result_code: "reinforced"` | |

### 2.6 torment_submit_task (canonical)

| # | Test | Input | Expected | P/F |
|---|---|---|---|---|
| 2.6a | Ingest via canonical | `operation: "ingest"`, `payload: '{"text": "Canonical test."}'` | `ok: true`, `result_code: "stored"` | |
| 2.6b | Query via canonical | `operation: "query_memory"`, `payload: '{"query": "canonical"}'` | `ok: true`, `result_code: "queried"` | |

---

## 3. Error & Rejection Tests

| # | Test | Input | Expected decision_code | P/F |
|---|---|---|---|---|
| 3.1 | Invalid payload JSON | `torment_submit_task` with `payload: "not json{"` | `blocked_mcp_invalid_payload` | |
| 3.2 | Non-exposed operation | `torment_submit_task` with `operation: "identity_rewrite"` | `blocked_mcp_not_exposed` | |
| 3.3 | Unknown operation | `torment_submit_task` with `operation: "destroy_everything"` | `blocked_mcp_not_exposed` | |
| 3.4 | Missing context | Remove `TORMENT_MCP_WORKSPACE_ID` from env, restart, call any tool without explicit workspace | `blocked_mcp_missing_context` | |

---

## 4. Resource Sanity

| # | Test | URI | Expected | P/F |
|---|---|---|---|---|
| 4.1 | Agent state | `torment://workspace/smoke_ws/agent/smoke_agent/state` | JSON with `workspace_id`, `agent_id`, `memory_count`, `character` | |
| 4.2 | Memory summary | `torment://workspace/smoke_ws/agent/smoke_agent/memory-summary` | JSON with `memory_count`, `drift_status` | |
| 4.3 | Collective status | `torment://workspace/smoke_ws/collective/status` | JSON with `agents`, `agent_count`, `shared_domains` | |
| 4.4 | Wrong workspace | `torment://workspace/nonexistent/agent/x/state` | Graceful error, no crash | |
| 4.5 | No internal leakage | Check all resource outputs | No file paths, no internal class names, no stack traces | |

---

## 5. Context Behavior

| # | Test | Setup | Expected | P/F |
|---|---|---|---|---|
| 5.1 | Defaults from env | Set env vars, call tool with no workspace/agent args | Uses default workspace and agent | |
| 5.2 | Explicit override | Call tool with `workspace_id: "smoke_ws"`, `agent_id: "smoke_agent"` | Uses provided values, ignores defaults | |
| 5.3 | Partial override | Provide only `workspace_id`, leave `agent_id` empty | Uses provided workspace + default agent | |
| 5.4 | Wrong agent | Call with `agent_id: "nonexistent"` | Graceful error (not a crash/hang) | |
| 5.5 | Wrong workspace | Call with `workspace_id: "nonexistent"` | Graceful error | |

---

## 6. Decision/Result Code Audit

After running all tests above, verify these codes were observed:

| Code | Where it should appear | Seen? |
|---|---|---|
| `fast_allowed` | All successful Tier 1 tool calls | |
| `state_read` | query_state calls | |
| `stored` | ingest calls | |
| `queried` | query_memory calls | |
| `reinforced` | feedback/reinforce calls | |
| `blocked_mcp_not_exposed` | Non-exposed operation attempt (3.2, 3.3) | |
| `blocked_mcp_invalid_payload` | Bad JSON payload (3.1) | |
| `blocked_mcp_missing_context` | Missing workspace/agent (3.4) | |

---

## 7. UX Notes

Fill in during testing — these are subjective but important:

| Question | Notes |
|---|---|
| Are tool names clear in the host UI? | |
| Are tool descriptions helpful or too long? | |
| Are parameter names obvious? | |
| Is the JSON payload string for `torment_submit_task` awkward? | |
| Do resources show up in a discoverable way? | |
| Is the response envelope too verbose for the host? | |
| Does the host render `decision_code` / `result_code` usefully? | |
| Any surprising behavior from default context? | |

---

## Bug Report Template

Copy this for each issue found:

```
### Bug: [short title]

- **Host:** Claude Desktop / other
- **Tool/Resource:** torment_ingest / torment://workspace/.../state / etc.
- **Input:** [exact parameters used]
- **Expected:** [what should have happened]
- **Actual:** [what actually happened]
- **decision_code:** [if present]
- **result_code:** [if present]
- **Defaults set:** WORKSPACE_ID=smoke_ws, AGENT_ID=smoke_agent, TRUST=0.6
- **Notes:** [anything else relevant]
```

---

## Post-Test Summary

| Category | Pass | Fail | Notes |
|---|---|---|---|
| Connection & Discovery | /5 | | |
| Tool Sanity | /8 | | |
| Error & Rejection | /4 | | |
| Resource Sanity | /5 | | |
| Context Behavior | /5 | | |
| Decision/Result Codes | /8 | | |
| **Total** | **/35** | | |
