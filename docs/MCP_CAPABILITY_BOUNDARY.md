# MCP Capability Boundary — TORMENT 2.4.x

## Purpose

This document defines the actual capability boundary of TORMENT's MCP layer.

It exists to prevent misinterpretation of MCP support as general-purpose tool execution or agent autonomy.

---

## What TORMENT MCP IS

TORMENT exposes a governed memory interface via MCP.

Through MCP, a connected client (e.g. Claude Desktop) can:

- Ingest memory
- Query memory
- Inspect agent state
- Provide feedback and reinforcement
- Submit structured tasks to the Spine

All operations:

- Pass through the Spine
- Are evaluated under trust tiers
- Are logged via the incident system
- Return structured decision envelopes

This makes MCP a controlled access layer to the memory system.

---

## What TORMENT MCP IS NOT

TORMENT MCP does not:

- Execute external tools
- Call APIs on behalf of the agent
- Perform filesystem or network actions
- Allow roles to trigger actions
- Enable autonomous agent loops
- Allow self-directed tool use

There is no tool dispatch system in the Spine.
There is no action execution layer.
This is intentional.

---

## Architecture Principle

TORMENT separates:

- **Epistemology** (memory, reasoning, provenance)
- **Capability** (actions, tools, execution)

TORMENT 2.4.x implements only the first.

---

## Exposure Tiers

MCP exposure is controlled by `TORMENT_MCP_EXPOSURE_TIER`.

### Tier 1 (default: open)

Safe operations:

- Memory ingest
- Memory query
- State inspection
- Feedback / reinforcement

### Tier 2 (guarded)

Advanced operations:

- `cognition_run`
- Memory governance controls

Requires explicit opt-in.

### Tier 3 (internal only)

Never exposed via MCP:

- Identity rewrite
- Seed modification
- Policy changes
- Architecture-level decisions

---

## Autonomy Boundary

TORMENT allows:

- Bounded automatic behavior (e.g. escalation, governance checks)

TORMENT does not allow:

- Autonomous action
- Self-directed tool usage
- External execution

**Automatic is allowed. Autonomous is not.**

---

## Tool-Result Ingest (v2.4.3)

TORMENT now supports governed ingest of externally obtained tool output as memory artifacts.

**What this is:**

- A Spine-governed write operation (`tool_result_ingest`)
- Stores externally supplied tool output with `source_type: "tool_result"`, `write_path: "tool_ingest"` provenance
- Queryable in normal retrieval, visible in `/debug/provenance`
- Endpoint: `POST /tool/ingest`

**What this is not:**

- Not tool execution. TORMENT does not call tools.
- Not automation. There are no background polls, scheduled refreshes, or chained tool calls.
- Not autonomous. Internal roles cannot trigger tool usage.
- Not identity-canonical. Tool results are external observations, not self-knowledge.

**Doctrine:**

> TORMENT may remember what tools returned before it is ever allowed to decide what tools to run.

Tool-result memories are safe parents for archivist writeback (included in `_SAFE_PARENT_SOURCE_TYPES`), but they do not grant execution authority and cannot trigger follow-up tool calls.

---

## Future Expansion

Any future capability layer (tool execution, automation, scheduling) must:

- Pass through Spine governance
- Carry provenance
- Respect exposure tiers
- Remain explicitly gated
- Be implemented as a separate governed phase, not folded into the memory system

---

## Honest Statement of Capability

**TORMENT has:**
A live MCP server exposing governed memory operations with trust-tiered access control and full audit logging.

**TORMENT does not have:**
Tool execution, API calling, or autonomous agent capabilities.

---

## Summary

TORMENT MCP is a memory interface, not an action system.

This boundary is intentional and enforced.

It will not be expanded without corresponding governance and provenance guarantees.
