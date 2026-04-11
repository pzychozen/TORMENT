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
      "args": ["-u", "-m", "torment_service.mcp_server"],
      "cwd": "/path/to/torment_fabric",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8",
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

The `-u` flag, `PYTHONUNBUFFERED=1`, and `PYTHONIOENCODING=utf-8` are
stdio hygiene: MCP stdio transport frames JSON-RPC messages over stdin
and stdout, so the Python process must run unbuffered and in UTF-8
regardless of the host terminal. These settings are harmless on
Linux/macOS and load-bearing on Windows.

### Windows Setup

On Windows (e.g., with conda), use the full path to your Python interpreter and set `PYTHONPATH` to the `torment_fabric` subdirectory:

```json
{
  "mcpServers": {
    "torment-memory": {
      "command": "C:\\Users\\You\\miniconda3\\envs\\torment\\python.exe",
      "args": ["-u", "-m", "torment_service.mcp_server"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8",
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

#### Windows stdio gotchas

MCP stdio is strict about what goes on stdout: anything that is not a
framed JSON-RPC message will corrupt the stream and disconnect the
host. Windows exposes a handful of foot-guns that make this easier to
trip into than on Linux/macOS. The config block above already sets
the three that matter most; this is the "why" so you can recognize
the symptoms if something still looks wrong.

- **Unbuffered I/O.** Python on Windows can buffer stdout aggressively,
  which delays or reorders JSON-RPC frames. The `-u` flag on `args` and
  `PYTHONUNBUFFERED=1` in `env` both disable buffering. Keep both as
  belt-and-suspenders — one without the other is still defensible, but
  not worth the debugging cost if something regresses.
- **UTF-8 on both directions.** Windows defaults to the system code
  page (often cp1252), which will break any memory text containing
  emoji, curly quotes, or non-Latin characters. `PYTHONIOENCODING=utf-8`
  forces stdin and stdout to UTF-8 regardless of the host shell. Do not
  rely on `chcp 65001` — it does not propagate into the launched
  Python process from Claude Desktop.
- **Stderr-only logging.** TORMENT's MCP server routes all diagnostic
  output (including the hivemind packet trace and governance warnings)
  to stderr. If you add your own `print()` or `logger` output to any
  module that runs during MCP boot or tool handling, make sure it goes
  to stderr — `print(..., file=sys.stderr)` or a logger whose handler
  is bound to stderr. Anything that leaks to stdout will break the
  transport.
- **Abrupt stdin close on shutdown.** Claude Desktop closes the MCP
  server's stdin when the host restarts or disconnects. On Windows
  this often arrives as an immediate EOF rather than the graceful
  SIGTERM you would see on Linux. The server tolerates this cleanly;
  you should not see it as a crash or a hang in Claude Desktop's MCP
  logs. If you do, that's a bug worth reporting.

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

### Convenience Tools (Tier 2 — Guarded)

Available when `TORMENT_MCP_EXPOSURE_TIER=guarded`:

| Tool | Operation | Description |
|---|---|---|
| `torment_tool_result_ingest` | tool_result_ingest | Store externally obtained tool output as provenance-tagged memory |

`torment_tool_result_ingest` is **memory storage, not tool execution**. TORMENT remembers what tools returned — it does not call tools. Results are tagged with `provenance_type: "tool_result"` and governed by the same Spine trust enforcement as regular ingest.

## Resources

Read-only views into agent and workspace state:

| URI | Description |
|---|---|
| `torment://workspace/{ws}/agent/{agent}/state` | Identity, drift, memory count, compression |
| `torment://workspace/{ws}/agent/{agent}/memory-summary` | Memory count, active motifs, drift status |
| `torment://workspace/{ws}/collective/status` | Agents, bridges, convergence events, hivemind flag |
| `torment://workspace/{ws}/agent/{agent}/provenance` | Recent memory provenance metadata for verification |

## Exposure Tiers

The MCP server only exposes operations allowed by the Spine's `exposure_tier` policy:

- **Tier 1 (open):** `query_state`, `query_memory`, `ingest`, `feedback`, `reinforce` — available by default
- **Tier 2 (guarded):** `tool_result_ingest`, `collective_reingest`, `memory_governance_set`, `compression_run`, `cognition_run` — available only when `TORMENT_MCP_EXPOSURE_TIER=guarded`
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

### Worked Example: Ingest Tool Result → Query → Verify Provenance

This workflow requires `TORMENT_MCP_EXPOSURE_TIER=guarded`.

1. **Ingest tool output:** Call `torment_tool_result_ingest` with `tool_name: "weather_api"`, `content: "Reykjavik: 3°C cloudy"`. Returns `decision_code: "fast_allowed"`, `result_code: "stored"`.

2. **Query memory:** Call `torment_query_memory` with `query: "weather in Reykjavik"`. Results include `provenance_type: "tool_result"` and `provenance_tool_name: "weather_api"` on the matching hit.

3. **Verify provenance:** Read the `torment://workspace/default/agent/default/provenance` resource. The memory appears with `source_type: "tool_result"`, `write_path: "tool_ingest"`, and `tool_name: "weather_api"`.

Tool-result memories are governed differently from regular memories: they receive a retrieval discount (default 0.85×), are excluded from continuity bonuses, have a capped half-life (default 7 days), and are prioritized for compression. This ensures tool output informs retrieval without dominating it.

### Worked Example: What a Blocked Call Looks Like

If an operation is not available at the current exposure tier, or trust is insufficient, you get a governed rejection:

```
torment_submit_task(
  operation: "identity_rewrite",
  payload: '{"new_seed": "something"}'
)
→ {
    "ok": false,
    "decision_code": "blocked_mcp_not_exposed",
    "result_code": "none",
    "result": null
  }
```

If workspace or agent context is missing:

```
torment_ingest(text: "hello")   # with no default workspace set
→ {
    "ok": false,
    "decision_code": "blocked_mcp_missing_context",
    "result_code": "none",
    "result": null
  }
```

The `decision_code` tells you exactly what went wrong. See the Decision Codes table above for the full list.

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
