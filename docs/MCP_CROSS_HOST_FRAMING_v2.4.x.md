# TORMENT 2.4.x — MCP Cross-Host Compatibility Framing

> **Status: PAUSED (framing + research preserved as groundwork)**
>
> **As of 2026-04-11**, the active follow-on track is no longer the full
> cross-host compatibility pass described below. This doc is kept as
> ratified groundwork; the active substitute track is the
> **Claude Desktop hardening pass** (see `docs/TORMENT_ROADMAP_NOTES.md`
> and the H1–H4 commit series landed on 2026-04-11).
>
> **Why paused.** The deep research pass (see
> `docs/MCP_CROSS_HOST_RESEARCH_REQUEST.md` and the findings PDF in
> `docs/`) confirmed that Hermes Agent (Nous Research), the only
> second-tested-host candidate we had short-listed, requires WSL2 on
> Windows. That turns a single-environment reliability pass into a
> split Windows/WSL2 test matrix problem, which is disproportionate to
> the present demand. Claude Desktop is already partially hardened and
> much easier to tighten further. The scope pivoted there.
>
> **What remains valid.** Everything in this doc downstream of the
> anchor statement is still correct as a description of the full
> cross-host track: the thesis, the anti-drift guardrails, the
> deliverables D1–D6, the six open decisions, the untested-hosts note,
> and the relationship-to-other-tracks section. If the track is
> resumed, this is the starting point — not a blank page. In particular,
> the capability boundary discipline ("no new tools, no tool-calling
> agent layer, no host-specific hacks") is permanent and carries into
> any future revisit.
>
> **What would resume this track.**
> 1. A Linux or WSL2 test environment becoming available on the
>    project's development machine, making Hermes a realistic second
>    host without a two-machine split.
> 2. A real second-host demand from a TORMENT user — someone running
>    Continue, Cline, Claude Code, or another stdio MCP host who hits
>    a compatibility issue that needs fixing, *and* who can provide
>    reproduction evidence on their own environment.
> 3. A decision to ship a host-agnostic positioning doc in service of
>    an external announcement, at which point the landscape research
>    below becomes load-bearing rather than background.
>
> **What is the active substitute.** The Claude Desktop hardening
> pass (H1–H4) is narrower but immediately applicable:
>
> - **H1** — add `mcp>=1.27.0,<2.0.0` to `requirements.txt` (fixed a
>   real install-time bug).
> - **H2** — audit stdout cleanliness on MCP-reachable runtime paths
>   (found and fixed four real stdout leaks in the hivemind packet
>   emission block of `fabric.py`).
> - **H3** — fold the Windows stdio checklist inline into the Claude
>   Desktop sections of `docs/MCP_README.md` and `docs/MCP_SMOKE_TEST.md`
>   (unbuffered mode, UTF-8 discipline, stderr-only logging, abrupt
>   stdin close tolerance).
> - **H4** — this pause-state housekeeping across the framing doc, the
>   research request doc, roadmap notes, and auto-memory.
>
> Several findings from the research pass that do *not* change in the
> pause should be preserved here for future reference:
>
> - FastMCP (`mcp.server.fastmcp.FastMCP`) is not deprecated. The
>   `mcp` package (v1.27.0, April 2 2026) is the canonical Python SDK.
> - MCP protocol version 2025-11-25 is current; TORMENT does not need
>   to pin a protocol version to work with Claude Desktop.
> - `structuredContent` is now a first-class MCP feature. TORMENT's
>   current `json.dumps` pattern still works but is not the idiomatic
>   2025-11-25 shape. **Deferred, not decided against.**
> - TORMENT's envelope-with-`ok=false` pattern is compatible with MCP
>   but not MCP-native; an idiomatic renderer would map blocked calls
>   to `isError=True`. **Deferred, not decided against.**
> - Mem0 owns the "Memory Layer for AI Apps" tagline and is the main
>   positioning-collision risk if a public positioning doc is ever
>   written. Honcho is the closest adjacent project (cross-session
>   memory for Hermes).
>
> Do not read the sections below as open work. Read them as the
> architectural state of a track that was scoped, researched, and
> then deliberately shelved at framing + research maturity.

---

## Original framing (preserved as groundwork)

### Status (at time of original framing)

Framing pass only. No code changes, no new MCP tools, no Spine changes, no
schema touches, no edits to `torment_service/mcp_server.py`, no edits to
any existing MCP doc beyond stub marker updates, until this framing doc is
ratified. The deliverables listed below are implementation targets for
*after* ratification, not work in progress.

## Thesis

**Make TORMENT's existing MCP server work cleanly and pitch-ably as the
governed memory layer for MCP-capable agents — verified against a narrow
tested target list (Claude Desktop and Hermes), documented host-
agnostically, and positioned so that agent developers immediately
understand: *agents need good memory, and TORMENT is that memory layer*.**

No new capability surface. No new tools. No relaxation of the capability
boundary. The work is compatibility, documentation, and positioning —
nothing more.

## Anchor

**TORMENT's MCP server is correct. What it lacks is evidence of cross-host
reliability and docs that read host-agnostically. This track closes both
gaps without touching the surface itself.**

---

## Why this work

The MCP surface as of the April 7 Path 3 audit is substantially complete:

- 7 tools (1 canonical `torment_submit_task` + 6 convenience wrappers
  covering ingest, query_memory, query_state, feedback, reinforce,
  tool_result_ingest)
- 5 read-only resources including the provenance resource
- 3-tier exposure model (open / guarded / internal)
- Trust-tiered access with full governed response envelope
- Dedicated docs: MCP_README, MCP_CAPABILITY_BOUNDARY, MCP_EXPANSION_GUIDE,
  MCP_SMOKE_TEST

What is missing is **not more surface**. What is missing is:

1. Evidence that the surface works for any MCP host other than Claude
   Desktop.
2. Documentation that reads host-agnostically, so developers running any
   stdio MCP host can connect without reverse-engineering Claude Desktop
   instructions.
3. A short, honest positioning doc that names TORMENT as "the governed
   memory layer for MCP agents" and sells the capability boundary as a
   feature rather than hiding it.

Every existing MCP doc currently reads as if Claude Desktop is the only
target. `MCP_README.md` has Claude Desktop quick-start + Windows Claude
Desktop config and no other host mentioned. `MCP_SMOKE_TEST.md` literally
says "Target: Claude Desktop (stdio transport)." In-process tests exist
but no live second-host validation has been performed.

The underlying server is standard stdio JSON-RPC and should work for any
compliant MCP host, but "probably works" is not "verified and documented."
A developer running Hermes today has no supported path into TORMENT.

---

## What this work is NOT

Explicit scope exclusions, to prevent drift during implementation. These
come directly from user-specified anti-drift guardrails and are hard
constraints on this track:

- **NOT more MCP tools.** The canonical tool + six convenience tools are
  correct as-is. No new convenience wrappers. No new Spine operations
  exposed through MCP.
- **NOT an MCP tool-calling layer.** TORMENT does not become an agent that
  uses other people's tools. `docs/MCP_CAPABILITY_BOUNDARY.md` is the
  authority and is not being relaxed. Epistemology stays separated from
  capability.
- **NOT capability sprawl.** No new exposure tiers, no new trust tiers, no
  new decision codes, no new result codes.
- **NOT host-specific hacks** unless a real compatibility issue forces
  one. If we find a real incompatibility with Hermes, we fix the server;
  we do not add a `TORMENT_MCP_HERMES_MODE` flag or any similar shim.
- **NOT a broad "top N hosts" sweep.** The validated target list is
  exactly Claude Desktop and Hermes. Other hosts may appear in the
  compatibility matrix with explicit "UNTESTED" status, but no test runs,
  no config claims, and no pass criteria are produced for them.
- **NOT clawbot-class shells.** User explicitly de-prioritized these for
  this track. Do not add clawbot as a tested target.
- **NOT a marketing document.** The positioning doc is short, practical,
  and honest. No "revolutionary," no "industry-leading," no unearned
  superlatives. The capability boundary does the actual selling.
- **NOT a refactor of `mcp_server.py`.** The code is in good shape as of
  Path 3. Unless a live Hermes test uncovers a real bug, the code stays
  untouched.
- **NOT a chance to rewrite other MCP docs "while we're in there."**
  MCP_CAPABILITY_BOUNDARY, MCP_EXPANSION_GUIDE, and the test files are
  out of scope. Touch only what this track explicitly lists.

If any deliverable threatens to violate one of these exclusions during
implementation, stop and surface the conflict rather than working around
it.

---

## Target hosts

### Tested targets (validated in this pass)

1. **Claude Desktop** — existing primary target. Config already
   documented; needs only a light repositioning within a host-agnostic
   README structure.
2. **Hermes** — new target. Needs a fresh config snippet, needs live
   validation against the smoke test, needs a per-host quirks section if
   anything surfaces.

Both are stdio-transport MCP hosts. Both run in a user-owned environment
(Windows), so **live validation is environment-side (user), not
sandbox-side (assistant)**. The assistant drafts the smoke test and
config snippets; the user runs them and reports results.

### Mentioned but untested (extension points, no claims)

The compatibility matrix includes rows for other stdio MCP hosts with
status explicitly marked **UNTESTED — no claims, no config provided**, so
future extension has a clean place to land. Candidates to list: Claude
Code, Continue, Cline, and a generic "other stdio MCP host" row.

Explicit exclusion: **no clawbot row** in this pass, per user direction.

The UNTESTED rows are for discoverability only. They do not carry config
snippets, quirks sections, or pass criteria. A prominent header in the
matrix makes the distinction between TESTED and UNTESTED unambiguous,
so untested rows do not create false impressions of support.

---

## Deliverables

Six concrete outputs. Work order is D1 → D3 → D2 → D4 (sandbox drafts),
then user runs live validation, then D5 (conditional) and D6 close out.

### D1 — `docs/MCP_HOST_COMPATIBILITY.md` *(NEW)*

Single compatibility matrix document. Columns:

| Host | Status | Transport | Config reference | Known quirks | Last tested |
|---|---|---|---|---|---|

Initial rows:

- **Claude Desktop** — TESTED (after live run) — stdio — link to config
  subsection in MCP_README — quirks section populated after test run —
  date populated after test run
- **Hermes** — TESTED (after live run) — stdio — link to config subsection
  in MCP_README — quirks section populated after test run — date populated
  after test run
- **Claude Code** — UNTESTED — stdio — no config — no claims — n/a
- **Continue** — UNTESTED — stdio — no config — no claims — n/a
- **Cline** — UNTESTED — stdio — no config — no claims — n/a
- **Other stdio MCP host** — UNTESTED — stdio — no config — follows
  standard stdio JSON-RPC — n/a

A prominent header explains: TESTED means the smoke test has been run
against this host in a real environment and passed; UNTESTED means the
host is listed for discoverability only, with no claims of compatibility
beyond "it is a standard stdio MCP host and should in principle connect."

Draft skeleton lands with all TESTED rows empty (status marked PENDING).
User fills them in after running the smoke test.

### D2 — `docs/MCP_README.md` *(MODIFIED — generalized)*

Rewrite the top sections to be host-agnostic:

- New lead paragraph: "TORMENT is the governed memory and provenance layer
  for MCP agents. The MCP server is a standard stdio JSON-RPC server
  compatible with any MCP host that supports stdio transport."
- Quick Start becomes a generic command-line example that works for any
  stdio MCP host.
- **Host Configuration** section becomes a thin pointer: "See
  `docs/MCP_HOST_COMPATIBILITY.md` for per-host config snippets and the
  current compatibility matrix." Keep Claude Desktop and Hermes config
  snippets *in MCP_README* under subsections, but frame them as
  "examples of stdio MCP host configs," not as "the config."

Everything else — tools table, resources table, exposure tiers, response
envelope, decision codes, worked examples, architecture diagram — is
preserved verbatim. Only the Quick Start and Host Configuration sections
are touched.

### D3 — `docs/MCP_SMOKE_TEST.md` *(MODIFIED — host-agnostic refactor)*

Refactor the existing 35-item checklist:

- Target becomes "any stdio MCP host" instead of "Claude Desktop."
- A short **Per-host setup** section at the top holds subsections for
  Claude Desktop and Hermes, each with the minimal connection config.
- The 35 checklist items are kept verbatim but rephrased (where needed)
  so they test TORMENT's responses, not a specific host's UI behavior.
- Pass criteria remain the same.
- A new **Results log** section is added at the bottom as an append-only
  record: `<date> — <host> — <overall pass/fail> — <notes>`. This creates
  a running track record as the smoke test is re-run over time.

### D4 — `docs/TORMENT_AS_MCP_MEMORY_LAYER.md` *(NEW — positioning doc)*

Short, practical, honest. **Target length: 150–250 lines.** Structure:

1. **Opening line.** One sentence: *TORMENT is the governed memory and
   provenance layer for MCP agents.*
2. **The problem it solves.** Agents need memory that is trustworthy,
   auditable, and doesn't let bad data quietly drift into future
   decisions. Most memory layers are dumb KV stores or unbounded vector
   indexes. TORMENT is neither.
3. **What TORMENT gives you through MCP.** Five short bullets: ingest,
   query, feedback, reinforce, tool-result ingest. One line each.
4. **Capability boundary as a feature.** The key paragraph:
   *TORMENT does not execute tools. It remembers what tools returned.
   This is intentional — it gives your agent a memory layer you can
   trust, because the memory layer never acts on its own. Your agent
   decides what to do; TORMENT decides what is worth remembering and
   with what provenance.*
5. **Trust, exposure, provenance in one paragraph.** How the governance
   model actually shows up in MCP calls (trust tiers, exposure tiers,
   decision codes). Link to MCP_CAPABILITY_BOUNDARY for the doctrine
   and to MCP_README for the surface.
6. **Integration path in one paragraph.** Point at MCP_README for
   connection instructions, MCP_HOST_COMPATIBILITY for host-specific
   configs, MCP_CAPABILITY_BOUNDARY for the doctrinal context.

No marketing superlatives. No "revolutionary." The capability boundary is
the pitch. If the boundary is explained clearly, readers who want a
tool-runner will know to go elsewhere, and readers who want a governed
memory layer will know they found it.

### D5 — Portability fixes *(CONDITIONAL)*

If the live Hermes smoke test uncovers a real portability bug in
`mcp_server.py`, fix it under a **separate** commit with test coverage,
split from the doc commits.

Explicit non-goal: do not speculatively refactor `mcp_server.py` in
anticipation of hypothetical Hermes issues. Wait for the smoke test to
surface concrete failures. If nothing surfaces, this deliverable is
empty, and that is the desired outcome.

### D6 — Housekeeping bundle *(FOLDED IN)*

The 30+ stale `docs/archive/AGENT_SPINE_PLAN.md` references tracked in
`TORMENT_ROADMAP_NOTES.md` §"Outstanding small fixes" — bundled into a
single housekeeping commit at the end of the track. Not the point of
this work, but cheap to include, and clears an outstanding item.

---

## File targets summary

**New files:**
- `docs/MCP_HOST_COMPATIBILITY.md`
- `docs/TORMENT_AS_MCP_MEMORY_LAYER.md`

**Modified files:**
- `docs/MCP_README.md` — generalize Quick Start and Host Configuration
- `docs/MCP_SMOKE_TEST.md` — host-agnostic refactor, add Results log
- `docs/TORMENT_ROADMAP_NOTES.md` — update status after the track closes
- Possibly `torment_service/mcp_server.py` — only if D5 fires
- ~30 files with stale `docs/archive/AGENT_SPINE_PLAN.md` refs (D6)

**Out of scope (do not touch):**
- `docs/MCP_CAPABILITY_BOUNDARY.md`
- `docs/MCP_EXPANSION_GUIDE.md`
- `tests/test_mcp_server.py` — unless D5 requires test coverage for a
  portability fix
- All other Spine / Fabric / cognition code

**No new code in production paths.** **No schema changes.** **No new
Spine operations.** **No new exposure tiers.** **No MCP tool additions.**

---

## Work order

1. **Draft D1** — compatibility matrix skeleton with TESTED rows marked
   PENDING, UNTESTED rows filled.
2. **Draft D3** — host-agnostic smoke test with per-host setup subsections
   for Claude Desktop and Hermes.
3. **Draft D2** — generalized MCP_README.
4. **Draft D4** — positioning doc.
5. **Hand off D1 + D3 to user** for live validation on Windows.
6. **User runs smoke test** against Claude Desktop → records results in D1
   and D3 Results log.
7. **User runs smoke test** against Hermes → records results in D1 and D3
   Results log.
8. **If bugs surface in step 6 or 7**, scope D5 in a follow-up commit with
   tests. Otherwise, skip.
9. **Fold D6** housekeeping into the track close-out commit.
10. **Update `TORMENT_ROADMAP_NOTES.md`** to reflect the closed track.

Steps 1–4 are sandbox-side (assistant draft work). Steps 5–7 are
environment-side (user runs in their Windows setup). Steps 8–10 close
out, split between sandbox and user depending on whether D5 fires.

---

## Open decisions awaiting ratification

Before any deliverable is drafted, the following need explicit sign-off or
revision. Recommendations are provided for each.

1. **File names.** New compatibility matrix at
   `docs/MCP_HOST_COMPATIBILITY.md` and new positioning doc at
   `docs/TORMENT_AS_MCP_MEMORY_LAYER.md`. Alternative names possible;
   confirm or revise. **Recommendation: accept as named.**

2. **Positioning doc location.** Lives in `docs/` alongside the other MCP
   documents, with a link from the top-level `README.md` so it remains
   discoverable from the GitHub landing page. Alternative: place at repo
   root for maximum discoverability. **Recommendation: `docs/` for
   consistency, linked from top-level README.**

3. **Untested host rows.** Include UNTESTED rows for Claude Code,
   Continue, Cline, and "other stdio MCP host" as extension points? Or
   leave the matrix with only Claude Desktop and Hermes?
   **Recommendation: include UNTESTED rows** with a prominent header
   explaining the TESTED/UNTESTED distinction, so future expansion has a
   clear landing spot. **Do not include clawbot** per explicit user
   direction.

4. **Positioning doc tone.** Concrete and honest, no marketing
   superlatives. The capability boundary pitch is the selling point.
   **Recommendation: confirm this tone as an explicit drafting
   constraint.**

5. **Smoke test results format.** Append-only Results log at the bottom
   of `MCP_SMOKE_TEST.md`, recording date + host + overall pass/fail +
   notes for each run. Alternative: separate `MCP_SMOKE_TEST_RESULTS.md`
   file. **Recommendation: append-only in the existing file for
   single-document visibility.**

6. **Scope firmness on "no mcp_server.py changes."** Hold the line unless
   Hermes smoke test uncovers a concrete bug. Explicitly reject
   "while-we're-in-there" refactors. **Recommendation: ratify this as a
   hard constraint on the track.**

7. **Commit structure.** Work lands as:
   - Commit 1: docs-only (D1 + D2 + D3 + D4) as a single doc commit
   - Commit 2 (conditional): portability fix (D5) with test coverage
   - Commit 3: housekeeping bundle (D6) with roadmap notes update
   **Recommendation: accept the three-commit structure.** Alternative:
   split D1/D3 from D2/D4 into separate commits if the review surface is
   too large.

---

## Anti-drift guardrails (user-specified)

Quoted from user scope direction, verbatim intent:

- No more MCP tools
- TORMENT does not become an MCP tool-calling agent
- No capability sprawl
- No host-specific hacks unless a real compatibility issue forces one

And positive goals, also user-specified:

- Clean MCP connection
- Clean docs
- Clean positioning
- Easy setup
- Clear statement that agents need good memory, and TORMENT is that
  memory layer

These are hard constraints on this track. The framing doc, every
deliverable, and every commit must be checkable against this list before
landing.

---

## Relationship to other tracks

- **Step 5 (recursion guard + normalize_parent):** Complete and landed on
  main as commit `9bb310c`. Unaffected by this track. No touches to
  `cognition/recursion_guard.py` or `torment_service/provenance_v1.py`.
- **Step 6 (write migration framing):** Shelved with framing doc drafted
  at `docs/WRITE_MIGRATION_FRAMING_v2.4.x.md`, awaiting ratification on
  six open decisions. Orthogonal to this track. This MCP work does not
  touch any step 6 surface and does not re-open the step 6 shelve.
- **Security hardening:** Substantially complete as of April 9. This
  track is the roadmap's declared item #2 (MCP compatibility), following
  item #1 (hardening).
- **Path 2 (retrieval tuning), Path 1 (live/personal layer), late
  research track:** Untouched, deferred per roadmap order of operations.

---

## Next move after this framing is ratified

1. Address any revisions requested on this framing doc
2. Begin D1 draft (compatibility matrix skeleton)
3. Proceed through sandbox-side work order (steps 1–4)
4. Hand off to user for live smoke tests (steps 5–7)
5. Close out (steps 8–10) depending on whether D5 fires

**No drafting of deliverables before this framing is ratified.**
**No touches to `mcp_server.py` unless the smoke test surfaces a real
portability bug.**
**No clawbot, no capability sprawl, no host-specific hacks, no
marketing bloat.**
