# MCP Expansion Guide — Adding New Tools to TORMENT

How to add a new MCP tool to the TORMENT memory system.
This guide covers the full path from Spine registration to a working MCP tool
that your LLM host can call.

---

## Architecture in 30 Seconds

```
MCP Host (Claude, etc.)
    |
    v
mcp_server.py   ← you add a tool function here
    |
    v
_spine_call()   ← single authority path, always
    |
    v
spine.py        ← you register the operation here
    |
    v
Fabric          ← you add the handler here (if needed)
```

Every MCP tool is a thin wrapper that calls `_spine_call()`.
The Spine checks trust, routes to the right handler, and wraps the result
in a governed response envelope. You never bypass this.

---

## Step-by-Step: Adding a New Tool

### Step 1: Register the Operation in the Spine

Open `torment_service/spine.py` and add an `OperationSpec` to either
`_ALWAYS_FAST` or `_ALWAYS_FULL`.

```python
# In _ALWAYS_FAST list:
OperationSpec("my_new_operation",  PATH_FAST, TRUST_INGEST,
              op_class=OP_CLASS_WRITE, exposure_tier=EXPOSURE_OPEN,
              can_escalate=False,
              description="What this operation does in one line"),
```

**Fields you must choose:**

| Field | What it means | Options |
|---|---|---|
| `name` | Operation identifier (snake_case) | Must be unique |
| `default_path` | `PATH_FAST` or `PATH_FULL` | Fast = structured dispatch, Full = 4-role cognition pipeline |
| `min_trust` | Minimum trust tier to execute | `TRUST_READ_ONLY` (0.0), `TRUST_QUERY_REINFORCE` (0.3), `TRUST_INGEST` (0.6), `TRUST_COLLECTIVE` (0.9), `TRUST_OPERATOR` (1.0) |
| `op_class` | Policy group | `OP_CLASS_READ`, `OP_CLASS_WRITE`, `OP_CLASS_COLLECTIVE`, `OP_CLASS_IDENTITY`, `OP_CLASS_COGNITIVE` |
| `exposure_tier` | MCP visibility | `EXPOSURE_OPEN` (Tier 1 — default MCP), `EXPOSURE_GUARDED` (Tier 2 — elevated trust), `EXPOSURE_INTERNAL` (Tier 3 — never MCP) |
| `can_escalate` | Allow auto fast-to-full escalation | `True` if the operation might touch identity-sensitive content |

**Rules:**
- `EXPOSURE_OPEN` = available to any MCP client at default trust
- `EXPOSURE_GUARDED` = only exposed when `TORMENT_MCP_EXPOSURE_TIER=guarded`
- `EXPOSURE_INTERNAL` = never exposed through MCP, HTTP only
- If you're unsure, start with `EXPOSURE_GUARDED` and promote later

### Step 2: Add a Fast Handler (if PATH_FAST)

Still in `spine.py`, write the handler function and add it to `FAST_DISPATCH`:

```python
def _fast_my_new_operation(fabric, ctx: RequestContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fast-path handler for my_new_operation."""
    with fabric.locks.agent_lock(ctx.workspace_id, ctx.agent_id):
        # Call the Fabric method that does the actual work
        return fabric.my_new_method(
            workspace_id=ctx.workspace_id,
            agent_id=ctx.agent_id,
            some_param=payload.get("some_param", "default"),
        )

# Add to the dispatch table:
FAST_DISPATCH["my_new_operation"] = _fast_my_new_operation
```

**Handler rules:**
- Always accept `(fabric, ctx, payload)` — nothing else
- Always use `fabric.locks.agent_lock()` for writes
- Extract parameters from `payload` dict, never from external sources
- Return a plain `Dict[str, Any]` — the Spine wraps it in the response envelope

Also add the result code mapping:

```python
# In _OPERATION_RESULT_CODES dict:
"my_new_operation": RESULT_STORED,   # or RESULT_QUERIED, etc.
```

### Step 3: Add the MCP Tool in mcp_server.py

Open `torment_service/mcp_server.py` and add a convenience tool inside
`create_mcp_server()`, after the existing convenience tools:

```python
# --- torment_my_new_operation ---
if "my_new_operation" in open_ops:
    @mcp.tool(
        name="torment_my_new_operation",
        description=(
            "One-line description of what this tool does. "
            "Governed by the Spine with trust enforcement."
        ),
    )
    def torment_my_new_operation(
        some_param: str,
        workspace_id: str = "",
        agent_id: str = "",
    ) -> str:
        """Longer docstring for the tool.

        Args:
            some_param: What this parameter does
            workspace_id: Target workspace (uses default if empty)
            agent_id: Target agent (uses default if empty)
        """
        payload: Dict[str, Any] = {"some_param": some_param}
        result = _spine_call("my_new_operation", payload,
                             workspace_id=workspace_id or None,
                             agent_id=agent_id or None)
        return json.dumps(result, default=str)
```

**Tool rules:**
- Naming: always `torment_` prefix, then operation name
- Gate on `if "my_new_operation" in open_ops:` so exposure tier is respected
- Parameters: use typed Python args, not raw JSON (except for lists/dicts where JSON strings are acceptable)
- Return: always `json.dumps(result, default=str)`
- Always include `workspace_id` and `agent_id` as optional params with `""` default
- Convert empty strings to `None` when passing to `_spine_call()`

### Step 4: (Optional) Add a Fabric Method

If your operation needs new logic in the Fabric layer, add it to `fabric.py`:

```python
def my_new_method(self, workspace_id, agent_id, some_param, **kwargs):
    """What this method does."""
    ws = self.get_workspace(workspace_id)
    # ... your logic here ...
    return {"ok": True, "result": "..."}
```

Many operations can be composed from existing Fabric methods
(query, ingest, feedback). Only add a new Fabric method if existing ones
don't cover your use case.

### Step 5: Write Tests

Add tests in `tests/test_spine.py` and `tests/test_mcp_server.py`:

```python
# In test_spine.py — verify the operation routes correctly
def test_my_new_operation_fast_path(self):
    ctx = RequestContext(client_id="test", trust_tier=0.6,
                        workspace_id="ws", agent_id="agent")
    req = SpineRequest(workspace_id="ws", agent_id="agent",
                       operation="my_new_operation",
                       payload={"some_param": "value"})
    resp = submit_task(req, self.fabric, ctx)
    self.assertTrue(resp.ok)
    self.assertEqual(resp.decision_code, "fast_allowed")

# In test_mcp_server.py — verify the MCP tool invocation
def test_my_new_operation_through_spine_call(self):
    result = _spine_call("my_new_operation", {"some_param": "value"})
    self.assertTrue(result["ok"])
```

---

## Worked Example: `torment_web_enrich`

A realistic example: you want to let agents store web search results as memory.
An external API fetches the data, TORMENT stores and governs it.

**Step 1 — Spine registration:**

```python
# In _ALWAYS_FAST:
OperationSpec("web_enrich",  PATH_FAST, TRUST_INGEST,
              op_class=OP_CLASS_WRITE, exposure_tier=EXPOSURE_GUARDED,
              can_escalate=True,
              description="Ingest web search results as agent memory"),
```

Why `EXPOSURE_GUARDED`: this calls an external API, so it shouldn't be
available to every MCP client by default. Operators opt in with
`TORMENT_MCP_EXPOSURE_TIER=guarded`.

Why `can_escalate=True`: search results might contain identity-sensitive
content ("who am i", seed-related text) that should route through
full cognition for review.

**Step 2 — Fast handler:**

```python
def _fast_web_enrich(fabric, ctx: RequestContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch web results externally, then ingest through Fabric."""
    query_text = payload.get("query", "")
    max_results = int(payload.get("max_results", 3))

    # External call — happens OUTSIDE the agent lock
    # (never hold locks during network I/O)
    from torment_service.web_adapter import search_web  # your adapter
    results = search_web(query_text, max_results=max_results)

    # Now ingest each result through Fabric WITH the lock
    stored = []
    with fabric.locks.agent_lock(ctx.workspace_id, ctx.agent_id):
        for r in results:
            text = f"[web] {r['title']}: {r['snippet']}"
            result = fabric.ingest(
                workspace_id=ctx.workspace_id,
                agent_id=ctx.agent_id,
                text=text,
                scope="private",
            )
            stored.append({"eid": result.get("eid"), "title": r["title"]})

    return {"ok": True, "stored": stored, "query": query_text}

FAST_DISPATCH["web_enrich"] = _fast_web_enrich

# Result code:
"web_enrich": RESULT_STORED,
```

**Step 3 — MCP tool (guarded tier):**

```python
# Gate on guarded ops, not open_ops
guarded_ops = get_exposed_operations(EXPOSURE_GUARDED)

if "web_enrich" in guarded_ops:
    @mcp.tool(
        name="torment_web_enrich",
        description=(
            "Search the web and store results as agent memory. "
            "External API call, governed by the Spine."
        ),
    )
    def torment_web_enrich(
        query: str,
        max_results: int = 3,
        workspace_id: str = "",
        agent_id: str = "",
    ) -> str:
        payload = {"query": query, "max_results": max_results}
        result = _spine_call("web_enrich", payload,
                             workspace_id=workspace_id or None,
                             agent_id=agent_id or None)
        return json.dumps(result, default=str)
```

This pattern works for any external integration: the external API call
happens in the handler, the governance wraps it, and the MCP tool is just
the thin typed interface.

---

## Should This Be a Tool, Resource, or Internal Op?

Before you start writing code, decide what surface your feature belongs on.
This prevents the most common expansion mistake: putting something on the
wrong surface and having to move it later.

| If your feature... | It should be a... | Example |
|---|---|---|
| Mutates memory or system state | **Tool** (with Spine operation) | ingest, feedback, web_enrich |
| Returns a read-only view of data | **Resource** | agent state, memory summary, admin status |
| Is a sensitive operator action | **Internal op** (HTTP only, Tier 3) | identity_rewrite, seed_change |
| Composes existing operations into a workflow | **Tool** (reuse existing handlers) | "search + ingest" combo |
| Provides system-wide diagnostics | **Resource** (admin URI) | torment://admin/status |

When in doubt: if it can change anything, it's a tool. If it only reads, it's a resource.
If it shouldn't be reachable from an LLM host at all, it's internal.

---

## Adding an MCP Resource (Read-Only)

Resources are simpler than tools — they're read-only views that don't need
the canonical `_spine_call()` path (though they can use it for governed reads).

```python
@mcp.resource(
    uri="torment://workspace/{workspace_id}/my-view",
    name="My View",
    description="What this resource shows.",
    mime_type="application/json",
)
def resource_my_view(workspace_id: str) -> str:
    """Read-only view of something."""
    fabric = _get_fabric()
    # ... read data from fabric ...
    return json.dumps(data, indent=2, default=str)
```

**Resource rules:**
- URI pattern: `torment://workspace/{workspace_id}/...` for workspace-scoped data
- URI pattern: `torment://admin/...` for system-wide data
- Always read-only — if it mutates state, it must be a tool
- Return JSON string
- Use `_spine_call("query_state", ...)` for governed reads, or read Fabric directly for non-sensitive data

---

## Exposure Tier Quick Reference

| Tier | Constant | Who sees it | When to use |
|---|---|---|---|
| Tier 1 (open) | `EXPOSURE_OPEN` | Every MCP client | Safe read/write ops that any authenticated client should access |
| Tier 2 (guarded) | `EXPOSURE_GUARDED` | Only when `TORMENT_MCP_EXPOSURE_TIER=guarded` | Collective ops, compression, cognition — things that affect system state broadly |
| Tier 3 (internal) | `EXPOSURE_INTERNAL` | Never via MCP | Identity rewrites, seed changes, policy changes — operator-only via HTTP |

---

## Checklist for New Tools

Before submitting your new tool:

- [ ] OperationSpec added to `_ALWAYS_FAST` or `_ALWAYS_FULL` in spine.py
- [ ] Fast handler added to `FAST_DISPATCH` (if fast path)
- [ ] Result code added to `_OPERATION_RESULT_CODES`
- [ ] MCP convenience tool added in `create_mcp_server()` with exposure gate
- [ ] `torment_submit_task` canonical tool description updated (exposed ops list)
- [ ] Tool naming follows `torment_` prefix convention
- [ ] Parameters use typed Python args, not raw JSON blobs
- [ ] `workspace_id` and `agent_id` included as optional params
- [ ] Tests added for both Spine routing and MCP invocation
- [ ] Smoke tested against a real MCP host (Claude Desktop)

---

## Common Mistakes

**Bypassing the Spine:** Never call Fabric methods directly from an MCP tool.
Always go through `_spine_call()`. This is how trust, drift monitoring,
incident logging, and the response envelope all work.

**Stdout pollution:** Never use `print()` in MCP server code. All diagnostic
output must go to `stderr` (use `logger.info/warning/error`). The MCP stdio
transport uses stdout exclusively for JSON-RPC.

**Forgetting the exposure gate:** Always wrap your convenience tool in
`if "operation_name" in open_ops:`. Without this, the tool appears even
when the Spine says it shouldn't be exposed.

**Defaulting workspace/agent to "default":** Don't. Use empty string `""` as
default so the missing-context detection works. The system will tell the user
what's wrong instead of silently operating on a nonexistent workspace.

**Using EXPOSURE_OPEN for sensitive ops:** When in doubt, use EXPOSURE_GUARDED.
You can always promote to open later, but you can't unpublish a tool that's
already being used by live hosts.

---

## Architecture Principle

> MCP is a projection of Spine policy, not a second control plane.

The MCP surface is generated from the operation registry. The Spine is
the single authority. When you register an operation with an exposure tier,
that's what determines whether it appears as an MCP tool. There is no
separate "MCP policy" to maintain.

This is why the system stays coherent as it grows.

**The completeness rule:**
If a feature can mutate memory or system state, it is not complete until
it has a Spine operation, decision codes, tests, and an exposure tier.
No exceptions. A feature that writes to Fabric without going through
the Spine is not a feature — it is a hole in the governance model.
