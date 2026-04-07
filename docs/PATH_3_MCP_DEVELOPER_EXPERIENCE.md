# Path 3 — MCP Developer Experience Audit

**Date:** 2026-04-07
**Scope:** Onboarding, contract clarity, examples, ergonomics
**Constraint:** No new tools, no automation, no capability expansion

---

## 1. Top MCP Usability Pain Points

### Pain Point 1: `tool_result_ingest` is invisible from MCP

The `tool_result_ingest` operation exists at Tier 2 (guarded), but there is no MCP convenience tool for it. A developer who wants to ingest tool output via MCP has to use the raw `torment_submit_task` with a hand-crafted JSON payload:

```
torment_submit_task(
  operation="tool_result_ingest",
  payload='{"tool_name":"weather_api","content":"3C cloudy","step":1}'
)
```

Meanwhile `ingest`, `query_memory`, `feedback`, and `reinforce` all have typed convenience tools. This is the single most likely point where a developer trying the "remember what tools returned" workflow will stumble.

**Severity:** High — this is the primary new feature of v2.4.3 and it has no convenience path.

### Pain Point 2: `torment_feedback` parameter types are confusing

The `torment_feedback` tool accepts four parameters that are all JSON strings representing arrays:

```python
retrieved_ids: str = "[]",
used_successfully: str = "[]",
user_confirmed: str = "[]",
contradiction_detected: str = "[]",
```

From an LLM host's perspective, these look like regular string parameters. The LLM has to know to format them as JSON arrays inside strings. This is the only convenience tool that does this — every other tool uses native types. And in practice, `used_successfully`, `user_confirmed`, and `contradiction_detected` are almost never used together. The common call is just "these IDs were retrieved and useful."

**Severity:** Medium — confusing for both LLMs and developers, but functional.

### Pain Point 3: No "provenance inspect" in MCP tools

The `/debug/provenance` HTTP endpoint exists and works well, but there's no MCP-accessible way to inspect provenance. A developer using Claude Desktop who ingests a tool result and wants to verify its provenance has to fall back to the HTTP API. This breaks the "10-minute workflow" for anyone who connected via MCP only.

**Severity:** Medium — the feature exists, it's just not reachable from the MCP surface.

### Pain Point 4: MCP_README doesn't mention `tool_result_ingest`

The MCP_README lists convenience tools and exposure tiers but doesn't mention `tool_result_ingest` anywhere. A developer reading the MCP docs has no way to discover this feature exists. They'd have to read the main README or the Spine Contract to find it.

**Severity:** Medium — documentation gap for a primary v2.4.3 feature.

### Pain Point 5: The smoke test is pre-v2.4.3

`MCP_SMOKE_TEST.md` tests 6 tools and 35 checklist items, but doesn't include any tool-result ingest flow, provenance verification, or the new retrieval semantics. It's still useful but incomplete for the current version.

**Severity:** Low — it works for what it tests, just needs updating.

---

## 2. Minimal Improvement Plan

### Fix 1: Add `torment_tool_result_ingest` convenience tool [HIGH VALUE]

Add a typed convenience tool in `mcp_server.py` for the `tool_result_ingest` operation, gated on guarded exposure:

```python
if "tool_result_ingest" in exposed_ops:
    @mcp.tool(
        name="torment_tool_result_ingest",
        description=(
            "Store externally obtained tool output as governed memory. "
            "This is memory storage, not tool execution — TORMENT remembers "
            "what tools returned, it does not call tools. "
            "Governed by the Spine with provenance tracking."
        ),
    )
    def torment_tool_result_ingest(
        tool_name: str,
        content: str,
        workspace_id: str = "",
        agent_id: str = "",
        summary: str = "",
        step: int = 0,
        domain_id: str = "",
        session_id: str = "",
        scope: str = "private",
    ) -> str:
        payload = {"tool_name": tool_name, "content": content, "step": step, "scope": scope}
        if summary: payload["summary"] = summary
        if domain_id: payload["domain_id"] = domain_id
        if session_id: payload["session_id"] = session_id
        result = _spine_call("tool_result_ingest", payload,
                             workspace_id=workspace_id or None,
                             agent_id=agent_id or None)
        return json.dumps(result, default=str)
```

This is the one new convenience tool that's justified: `tool_result_ingest` is a primary v2.4.3 feature, it's already Spine-registered, and it follows the exact same pattern as `torment_ingest`. It's not tool sprawl — it's exposing what's already built.

### Fix 2: Update MCP_README with tool_result_ingest [HIGH VALUE]

Add `torment_tool_result_ingest` to the convenience tools table, add a note in the Exposure Tiers section, and add a brief "Ingest Tool Result" step to the Worked Example.

### Fix 3: Simplify `torment_feedback` parameters [MEDIUM VALUE]

Change from four JSON-string parameters to a simpler interface:

```python
def torment_feedback(
    memory_ids: str = "[]",     # JSON array of ints — the retrieved memory IDs
    useful: bool = True,        # were they useful?
    confirmed: bool = False,    # user confirmed correct?
    workspace_id: str = "",
    agent_id: str = "",
) -> str:
```

This maps to the same underlying Spine payload but is much clearer for both LLMs and developers. The `memory_ids` parameter replaces the confusing `retrieved_ids`/`used_successfully`/`user_confirmed`/`contradiction_detected` quartet.

**Note:** This changes the convenience tool's interface, not the Spine operation. The canonical `torment_submit_task` path remains unchanged. This is purely an ergonomic fix for the MCP-facing surface.

### Fix 4: Add provenance query resource [LOW-MEDIUM VALUE]

Add a read-only MCP resource for provenance inspection:

```python
@mcp.resource(
    uri="torment://workspace/{workspace_id}/agent/{agent_id}/provenance",
    name="Recent Provenance",
    description="Recent memory provenance metadata for verification.",
    mime_type="application/json",
)
def resource_provenance(workspace_id: str, agent_id: str) -> str:
    # Read-only — calls the same logic as /debug/provenance
```

This is a resource (read-only), not a tool, so it doesn't expand the capability surface. It just makes provenance visible from MCP without falling back to HTTP.

### Fix 5: Update smoke test for v2.4.3 [LOW VALUE]

Add test items for:
- `torment_tool_result_ingest` (if convenience tool added)
- `torment_submit_task` with `operation: "tool_result_ingest"`
- Provenance verification after ingest
- Verify `provenance_type` badge on query results

---

## 3. Recommended Docs/Example Additions

### Examples That Matter Most

The MCP_README already has a decent Worked Example (5 steps). It covers the core flow. What's missing:

**Example A: Ingest tool result → query → verify provenance**

This is the primary new workflow. Should live in MCP_README after the existing Worked Example:

```
1. Ingest tool output:
   torment_tool_result_ingest(
     tool_name="weather_api", content="Reykjavik: 3C cloudy")

2. Query memory:
   torment_query_memory(query="weather in Reykjavik")
   → Results include provenance_type: "tool_result", provenance_tool_name: "weather_api"

3. Verify provenance:
   Read torment://workspace/default/agent/default/provenance
   → Shows source_type: "tool_result", write_path: "tool_ingest"
```

**Example B: Using `torment_submit_task` for guarded operations**

Currently the Worked Example only shows convenience tools. One example using the canonical tool for a guarded operation would help developers understand the two-tier approach:

```
torment_submit_task(
  operation="compression_run",
  payload='{"max_candidates": 20}',
  mode="auto")
```

**Example C: Error handling — what blocked looks like**

The smoke test documents error codes, but MCP_README doesn't show what a blocked response looks like in practice. One example of a trust-blocked or exposure-blocked call would help developers understand the governance model without reading the Spine Contract.

### Where Examples Should Live

- **MCP_README.md** — the primary destination. Add Examples A and C after the existing Worked Example.
- **MCP_SMOKE_TEST.md** — add Example B as a test case.
- Do **not** create a separate examples file. Keep everything in MCP_README.

### Current Examples Assessment

The existing Worked Example in MCP_README (5 steps: state → ingest → query → feedback → drift) is good. It covers the core loop. It just needs the tool-result and error-handling additions.

---

## 4. High-Value Ergonomic Fixes

### Fix A: Convenience tool for `tool_result_ingest` (described above)

This is the single highest-value ergonomic fix. It makes the primary v2.4.3 feature accessible through typed parameters instead of raw JSON.

### Fix B: Simplify `torment_feedback` (described above)

Second highest value. Reduces confusion for both LLMs and developers.

### What Should Explicitly Remain Unchanged

- **`torment_submit_task`** — the canonical tool is correct as-is. It accepts any exposed operation with a JSON payload. The payload-as-string pattern is slightly awkward, but it's the right trade-off: typed parameters would mean a different tool per operation, which is exactly the tool sprawl this path is trying to avoid.

- **Response envelope structure** — the `ok`/`decision_code`/`result_code`/`result` envelope is good. It's consistent across all operations. Don't simplify it for MCP.

- **`workspace_id`/`agent_id` as optional params on every tool** — this pattern works. The empty-string default with missing-context detection is the right behavior.

- **Exposure tier gating** — the `if "operation" in open_ops:` pattern for convenience tools is clean. Don't change it.

- **Resources** — the four existing resources (agent state, memory summary, admin status, collective status) are appropriate. The provenance resource proposed above is the only addition worth making.

---

## 5. What Not to Build

This list exists to prevent Path 3 from becoming feature creep:

- **Do not add a `torment_search_and_ingest` combo tool.** Composition should happen in the host, not in TORMENT. If a developer wants to search and then ingest, they call two tools.

- **Do not add MCP tools for compression, governance, or cognition.** These are Tier 2/3 operations accessible through `torment_submit_task`. They don't need convenience wrappers — they're rare operations used by operators, not regular workflows.

- **Do not add a `torment_chat` or `torment_conversation` tool.** TORMENT is memory, not conversation. The host manages conversation; TORMENT manages what gets remembered.

- **Do not add scheduling, polling, or refresh tools.** This is the capability boundary. MCP tools store and retrieve memory. They do not execute external actions or maintain running state.

- **Do not add a bulk ingest tool.** If someone needs to ingest 100 items, they call `torment_ingest` 100 times. A bulk tool introduces batch semantics, error handling complexity, and partial-failure states that don't belong in a v1 MCP surface.

- **Do not add "smart" tools that make decisions.** Tools like "auto-categorize this memory" or "suggest which memories to reinforce" push intelligence into the MCP layer. Intelligence belongs in the host or in the Spine's cognition pipeline — not in MCP tool wrappers.

- **Do not create a separate `torment_tool_execute` tool.** The word "execute" does not belong in TORMENT's MCP vocabulary. Memory in, memory out.

---

## 6. Implementation Priority

| # | Fix | Files | Effort | Value |
|---|---|---|---|---|
| 1 | `torment_tool_result_ingest` convenience tool | `mcp_server.py` | ~30 lines | **High** |
| 2 | Update MCP_README (tool_result_ingest, examples) | `docs/MCP_README.md` | ~40 lines | **High** |
| 3 | Simplify `torment_feedback` parameters | `mcp_server.py` | ~20 lines | **Medium** |
| 4 | Provenance resource | `mcp_server.py` | ~30 lines | **Medium** |
| 5 | Update smoke test | `docs/MCP_SMOKE_TEST.md` | ~20 lines | **Low** |

Total: ~140 lines of changes across 3 files. No new dependencies, no capability expansion, no new Spine operations.

---

## 7. Doctrine Compliance

All proposed changes respect:

- **MCP is a governed memory interface, not an autonomous tool runner.** Every fix is either docs, an example, or a thin wrapper over an existing Spine operation.
- **No tool sprawl.** One new convenience tool (for an existing Spine operation) and one new resource (read-only). Everything else is docs and ergonomic fixes.
- **No capability expansion.** The provenance resource is read-only. The tool_result_ingest convenience tool wraps an existing operation. The feedback simplification changes the MCP surface, not the Spine.
- **The Spine remains the single authority.** All tools call `_spine_call()`. No direct Fabric access.
