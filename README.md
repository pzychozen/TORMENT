# TORMENT Memory Fabric — v2.4.4

TORMENT is a governed memory and identity engine for building persistent AI characters and agents. It focuses on long-lived memory, identity that resists drift, provenance-aware governance, and a clear boundary between remembering and acting. It is not a generic autonomous agent stack.

---

## What makes TORMENT different

- **Structured persistent memory** — geometric kernel, half-life decay, reinforcement, and event-gated compression
- **Identity that resists drift** — character basins, seed gravity, and drift monitoring
- **Provenance-aware by default** — memory writes carry structured provenance and can be audited by origin
- **Governed decisions through the Agent Spine** — trust tiers, escalation, and structured result codes
- **Multi-agent / collective support** — workspace-level resonance, convergence detection, and controlled echo flows
- **MCP as a governed extension layer** — memory operations exposed through a narrow, audited interface

---

## Is TORMENT for you?

**Good fit for**

- persistent AI characters, companions, NPCs, and modding experiments
- memory-governed agent research
- multi-agent and hivemind identity experiments
- developers building on top of a structured memory substrate

**Not a fit for**

- plug-and-play general automation
- unrestricted autonomous tool execution
- a thin prompt wrapper with no real architecture

---

## Architecture at a glance

- **Memory / epistemology** — TriOcta kernel, fabric orchestration, compression, and spirit return
- **Stance / modulation** — advisory thinking and stance policy shaped by internal kernel state
- **Spine / governance** — trust-aware routing, audit trails, decision/result codes
- **MCP / capability surface** — governed memory operations exposed to external clients; no tool dispatch, no autonomous action

Deeper reference:

- `docs/PROJECT_OVERVIEW.md`
- `docs/AGENT_SPINE_OVERVIEW.md`
- `docs/MEMORY_KERNEL_ARCHITECTURE.md`

---

## Quick start

```bash
python -m pip install -r requirements.txt
# then follow docs/QUICKSTART.md for your platform
```

TORMENT runs as a local service with a governed MCP surface for clients such as Claude Desktop.

Start here:

- **Quick start** — `docs/QUICKSTART.md`
- **General guide** — `docs/GUIDE.md`
- **Claude Desktop / MCP setup** — `docs/MCP_README.md`
- **Smoke test** — `docs/MCP_SMOKE_TEST.md`
- **Zero-code character creator** — `start/torment_character_creator.html`

---

## Current status — v2.4.4

v2.4.4 closes the provenance-migration subsystem (step 6). Legacy memory rows can be walked through a two-gate policy — gate 1 epistemic recovery, gate 2 ancestry admission — and rewritten by a narrow append-only writer that preserves refusal state and recursion safety. The full closure sequence — export, dry-run, apply, and guard re-verification — has been validated end-to-end against a live workspace. `TORMENT_ARCHIVIST_WRITEBACK` remains off; enabling it is a separate later decision gate.

Recent work in the v2.4.x line:

- **v2.4.4** — provenance migration closure (step 6), recursion guard and refusal sentinels validated end-to-end
- **v2.4.3** — tool-result memory lane, governed ingest of external tool outputs
- **v2.4.2** — provenance system, recursion safety policy, MCP capability boundary
- **v2.4.1** — thinking controller, stance policy, first live voice-agent deployment
- **v2.4.0** — memory lifecycle overhaul, Agent Spine formalization, unified observability

For the full history, see the release notes under `docs/`.

---

## Extending TORMENT — MCP tools

TORMENT exposes governed memory operations to Claude Desktop and other MCP clients through a narrow MCP server. New tools should be registered through the Spine so they inherit trust-tier enforcement, audit trails, and stable result codes.

TORMENT is a memory and cognition interface, not an unrestricted action system. It remembers; it does not decide what tools to run.

Relevant docs:

- `docs/MCP_EXPANSION_GUIDE.md` — adding a new MCP tool end-to-end
- `docs/MCP_README.md` — Claude Desktop integration
- `docs/MCP_SMOKE_TEST.md` — verifying a new tool
- `docs/MCP_CAPABILITY_BOUNDARY.md` — what belongs in the MCP surface and what doesn't

---

## Where to go next

**Core doctrine**

- `docs/DOCTRINE_v2.4.x.md` — 12 principles that govern v2.4.x change decisions
- `docs/RECURSION_SAFETY_POLICY_v2.4.x.md` — archivist write-back safety
- `docs/ADMISSION_POLICY_v2.4.x.md` — two-gate admission for migrated rows
- `docs/MCP_CAPABILITY_BOUNDARY.md` — the memory/action boundary

**Setup and operation**

- `docs/QUICKSTART.md`, `docs/GUIDE.md`, `docs/TUNING.md`, `docs/TROUBLESHOOTING.md`
- `docs/MCP_README.md`, `docs/MCP_SMOKE_TEST.md`

**Architecture reference**

- `docs/PROJECT_OVERVIEW.md` — comprehensive architecture reference
- `docs/AGENT_SPINE_OVERVIEW.md` — cognition pipeline
- `docs/SPINE_CONTRACT.md` — trust tiers, decision codes, exposure tiers
- `docs/MEMORY_KERNEL_ARCHITECTURE.md` — kernel design, compression gating, warmup
- `docs/CHARACTER_SYSTEM.md` — living character identity and spirit return
- `docs/HIVEMIND_GUIDE.md` — multi-agent convergence and echo re-ingestion

**Roadmap and release history**

- `docs/ROADMAP_v2.4.x.md`
- `docs/RELEASE_NOTES_v2.4.4.md`
- `docs/RELEASE_NOTES_v2.4.3.md`
- earlier release notes under `docs/`

**Research archive**

- [TriOctagon Toy Model — Full Diagnostics (12 versions) on Zenodo](https://zenodo.org/records/18215874) — the standalone research archive for the coupled-oscillator kernel at the heart of TORMENT's memory dynamics.

---

## Support this project

If TORMENT is useful to you, support is appreciated.

- **Ko-fi** — [ko-fi.com/hilmirhalldorsson](https://ko-fi.com/hilmirhalldorsson)
- **BTC** — `bc1p8g9dd2y4fgnshdsvyq5ecu22mdr5kjfw8zdcptfdhghh4a0837ssjqzgka`
- **ETH** — `0x52a31b19bC79d412621aA898adCC2BDd3580fDf4`
- **SOL** — `2AmeJwpE68FbytofrUgrNtYwwtzLnjfDi1ACzkBDxBUj`
