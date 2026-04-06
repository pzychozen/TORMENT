# TORMENT MCP Server

MCP v1 — stdio transport, governed by the Agent Spine.

## Quick Start

```bash
cd torment_fabric

# Minimal (uses defaults)
python -m torment_service.mcp_server

# With configuration
TORMENT_MCP_DATA_DIR=./data \
TORMENT_MCP_WORKSPACE_ID=my_workspace \
TORMENT_MCP_AGENT_ID=atlas \
TORMENT_MCP_TRUST_TIER=0.6 \
python -m torment_service.mcp_server
```

The server communicates over stdio using the MCP JSON-RPC protocol. Connect it to any MCP-capable host (Claude Desktop, etc.).

## Host Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "torment-memory": {
      "command": "python",
      "args": ["-m", "torment_service.mcp_server"],
      "cwd": "/path/to/torment_fabric",
      "env": {
        "TORMENT_MCP_DATA_DIR": "./data",
        "TORMENT_MCP_WORKSPACE_ID": "default",
        "TORMENT_MCP_AGENT_ID": "default",
        "TORMENT_MCP_TRUST_TIER": "0.6",
        "TORMENT_EMBED_PROVIDER": "hash"
      }
    }
  }
}
```

Replace `TORMENT_EMBED_PROVIDER` with your embedding provider if using real embeddings.

### Windows Setup

On Windows (e.g., with conda), use the full path to your Python interpreter and set `PYTHONPATH` to the `torment_fabric` subdirectory:

```json
{
  "mcpServers": {
    "torment-memory": {
      "command": "C:\\Users\\You\\miniconda3\\envs\\torment\\python.exe",
      "args": ["-m", "torment_service.mcp_server"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\TORMENT-fabric_v2\\torment_fabric",
        "TORMENT_MCP_DATA_DIR": "C:\\path\\to\\TORMENT-fabric_v2\\torment_fabric\\data",
        "TORMENT_MCP_WORKSPACE_ID": "default",
        "TORMENT_MCP_AGENT_ID": "default",
        "TORMENT_MCP_TRUST_TIER": "0.6",
        "TORMENT_EMBED_PROVIDER": "hash"
      }
    }
  }
}
```

Key differences from Linux/Mac: use absolute paths everywhere (including `TORMENT_MCP_DATA_DIR`), set `PYTHONPATH` explicitly, and use the full path to the conda environment's `python.exe`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TORMENT_MCP_DATA_DIR` | `./data` | Fabric data directory (persistent storage) |
| `TORMENT_MCP_CLIENT_ID` | `mcp_client` | Identity of this MCP session |
| `TORMENT_MCP_TRUST_TIER` | `0.6` | Trust level (0.0=read-only, 0.6=ingest, 0.9=collective, 1.0=operator) |
| `TORMENT_MCP_WORKSPACE_ID` | *(empty)* | Default workspace — **set this** or provide per-call |
| `TORMENT_MCP_AGENT_ID` | *(empty)* | Default agent — **set this** or provide per-call |
| `TORMENT_MCP_EXPOSURE_TIER` | `open` | Max exposure: `open` (Tier 1 only) or `guarded` (Tier 1+2) |
| `TORMENT_EMBED_PROVIDER` | *(required)* | Embedding provider (`hash` for testing, or your real provider) |

## Tools

### Canonical Tool

**`torment_submit_task`** — the universal governed interface. Accepts any exposed operation name, a JSON payload, and optional workspace/agent/mode overrides. This is the single authority path.

```
operation: "ingest"
payload: '{"text": "The sky turned violet at dusk.", "step": 1}'
workspace_id: "my_workspace"
agent_id: "atlas"
mode: "auto"
```

### Convenience Tools (Tier 1)

These wrap `torment_submit_task` with typed parameters for common operations:

| Tool | Operation | Description |
|---|---|---|
| `torment_ingest` | ingest | Store text as new memory |
| `torment_query_memory` | query_memory | Semantic memory search |
| `torment_query_state` | query_state | Agent state snapshot (identity, drift, memory count) |
| `torment_feedback` | feedback | Reinforcement feedback on retrieved memories |
| `torment_reinforce` | reinforce | Direct memory reinforcement |

## Resources

Read-only views into agent and workspace state:

| URI | Description |
|---|---|
| `torment://workspace/{ws}/agent/{agent}/state` | Identity, drift, memory count, compression |
| `torment://workspace/{ws}/agent/{agent}/memory-summary` | Memory count, active motifs, drift status |
| `torment://workspace/{ws}/collective/status` | Agents, bridges, convergence events, hivemind flag |

## Exposure Tiers

The MCP server only exposes operations allowed by the Spine's `exposure_tier` policy:

- **Tier 1 (open):** `query_state`, `query_memory`, `ingest`, `feedback`, `reinforce` — available by default
- **Tier 2 (guarded):** `collective_reingest`, `memory_governance_set`, `compression_run`, `cognition_run` — available only when `TORMENT_MCP_EXPOSURE_TIER=guarded`
- **Tier 3 (internal):** `identity_rewrite`, `seed_change`, etc. — never exposed through MCP

Set `TORMENT_MCP_EXPOSURE_TIER=guarded` to enable Tier 2 operations.

## Response Envelope

Every tool call returns a governed response envelope:

```json
{
  "ok": true,
  "path": "fast",
  "operation": "ingest",
  "allowed": true,
  "decision_code": "fast_allowed",
  "result_code": "stored",
  "drift_status": "green",
  "escalated": false,
  "escalation_reasons": [],
  "result": { "eid": 42, "summary": "..." },
  "elapsed_ms": 12.3
}
```

### Decision Codes

| Code | Meaning |
|---|---|
| `fast_allowed` | Executed on fast governance path |
| `full_allowed` | Executed through full cognition pipeline |
| `escalated_full` | Auto-escalated from fast to full |
| `blocked_insufficient_trust` | Trust tier too low |
| `blocked_mcp_not_exposed` | Operation not available at current exposure tier |
| `blocked_mcp_missing_context` | workspace_id or agent_id not resolvable |
| `blocked_mcp_invalid_payload` | Malformed JSON payload |

### Result Codes

| Code | Meaning |
|---|---|
| `stored` | Memory created |
| `reinforced` | Feedback applied |
| `queried` | Search results returned |
| `state_read` | State snapshot returned |
| `none` | Blocked or errored |

## Worked Example

Using Claude Desktop with the MCP server connected:

1. **Check agent state:** Call `torment_query_state` with default workspace/agent. Returns identity, drift score, and memory count.

2. **Ingest a memory:** Call `torment_ingest` with `text: "The user prefers concise responses."`. Returns `decision_code: "fast_allowed"`, `result_code: "stored"`.

3. **Search memory:** Call `torment_query_memory` with `query: "user preferences"`. Returns ranked results from the geometric memory kernel.

4. **Provide feedback:** Call `torment_feedback` with the memory IDs that were useful. This shapes future retrieval ranking.

5. **Check drift:** Read the `torment://workspace/default/agent/default/state` resource. The `drift_status` field shows whether the agent's character is drifting from its seed.

## Architecture

```
MCP Host (Claude Desktop)
    │
    ├── stdio (JSON-RPC)
    │
MCP Server (mcp_server.py)
    │
    ├── MCPClientContext → RequestContext
    │
Agent Spine (spine.py)
    │
    ├── Trust check → Path routing → Auto-escalation → Dispatch
    │
TORMENT Fabric (fabric.py)
    │
    └── Geometric memory kernel, graphs, compression, collective
```

The MCP server never touches the Fabric directly. All operations go through the Spine's governed authority layer.

When the advisory thinking layer is enabled (`TORMENT_THINKING_ADVISORY=1`), MCP-connected characters gain access to task framing, memory planning, and optional stance modulation (contextual abstention). This means characters can decline to respond, ask for clarification, or choose brevity based on cognitive context — not just always answer. The thinking layer is a sidecar that observes and advises; it never overrides Spine decisions. See `docs/advanced_cognition.md` for the full architecture.
