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

## Future Expansion (Not in 2.4.x)

The system is structurally prepared for:

- Tool result ingestion (`source_type: "tool_result"`)
- Governed capability expansion

However, no external tool execution exists in 2.4.x.

Any future capability layer must:

- Pass through Spine governance
- Carry provenance
- Respect exposure tiers
- Remain explicitly gated

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
