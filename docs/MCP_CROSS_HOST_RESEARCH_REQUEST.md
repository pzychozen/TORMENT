# Research Request — MCP Cross-Host Compatibility for TORMENT 2.4.x

> **Status (2026-04-11): COMPLETED + PAUSED as groundwork.**
>
> This research request was handed off, executed, and returned as
> `docs/TORMENT MCP Cross‑Host Research Findings.pdf`. The findings
> answered every high-priority question and most of the lower-priority
> ones.
>
> Key outcomes from the findings that shaped what happened next:
>
> - Hermes Agent requires WSL2 on Windows, turning the planned
>   two-host reliability pass into a split Windows/WSL2 environment
>   problem. Disproportionate to present demand.
> - FastMCP is not deprecated. `mcp>=1.27.0` is canonical. TORMENT
>   was missing this pin in `requirements.txt` (now fixed).
> - TORMENT's JSON-dumps return shape and envelope-with-`ok=false`
>   pattern are both compatible but not fully idiomatic against the
>   2025-11-25 protocol. Both are deferred, not decided against.
> - Windows stdio discipline (unbuffered mode, UTF-8, stderr-only
>   logging, abrupt stdin close tolerance) now folded into the
>   Claude Desktop docs.
>
> The research is therefore **complete** and **preserved as
> groundwork**. The original framing doc
> (`MCP_CROSS_HOST_FRAMING_v2.4.x.md`) was not ratified into
> implementation; both docs are held at "research complete, track
> paused" maturity pending a real second-host demand or a Linux/WSL2
> development environment.
>
> If the cross-host track is resumed, this document remains
> load-bearing: the 21 questions and the returned findings are still
> the correct starting point, and the answers are not likely to
> decay significantly in the short term. See the paused-status block
> at the top of `MCP_CROSS_HOST_FRAMING_v2.4.x.md` for the resume
> conditions.
>
> The active follow-on track is the **Claude Desktop hardening pass**
> (see `TORMENT_ROADMAP_NOTES.md`).

---

**Requester:** TORMENT Fabric project lead
**Status:** Completed, returned, paused as groundwork (see block above)
**Related doc:** `docs/MCP_CROSS_HOST_FRAMING_v2.4.x.md` (full doctrine, 410 lines)
**Findings doc:** `docs/TORMENT MCP Cross‑Host Research Findings.pdf`
**Scope ceiling:** This is an investigation request, not an implementation
brief. The outcome of this research feeds into the framing doc's
deliverable list; it does not authorize code changes or new MCP tools.

---

## 1. Context in one page

TORMENT Fabric is a governed memory-and-identity system for persistent AI
characters and agents, currently at v2.4.3. It is not an automation
engine and is not a tool runner. Its value proposition is **governed
memory with provenance** — agents plug into TORMENT and get a memory
layer that is trust-tiered, exposure-gated, and fully audit-traced
through a governance component called the Spine.

TORMENT already ships an MCP server (`torment_service/mcp_server.py`,
872 lines) that exposes memory operations over **standard stdio JSON-RPC
transport**. The surface consists of:

- **7 tools:** 1 canonical (`torment_submit_task`) and 6 typed
  convenience wrappers (`torment_ingest`, `torment_query_memory`,
  `torment_query_state`, `torment_feedback`, `torment_reinforce`,
  `torment_tool_result_ingest`).
- **5 read-only resources** exposing agent state, memory summary,
  collective status, and memory provenance.
- **3-tier exposure model** (`open` / `guarded` / `internal`) controlled
  by `TORMENT_MCP_EXPOSURE_TIER`.
- **Trust tiers** (0.0 read-only → 1.0 operator) controlled by
  `TORMENT_MCP_TRUST_TIER`.
- **Governed response envelope** on every call:
  `ok` / `decision_code` / `result_code` / `result` / `drift_status` /
  `escalated` / `escalation_reasons` / `elapsed_ms`.

**What TORMENT's MCP layer does NOT do:** execute tools, call external
APIs, perform filesystem or network actions, run autonomous agent loops,
or let roles trigger actions. This is intentional and enforced by
`docs/MCP_CAPABILITY_BOUNDARY.md`. *TORMENT remembers what tools
returned; it does not decide what tools to run.* This boundary is
explicitly not up for revision in this research.

**Current docs state.** All existing MCP documentation reads as if
Claude Desktop is the only target host. `docs/MCP_README.md` has a
Claude Desktop quick-start and a Windows Claude Desktop config and no
other host mentioned. `docs/MCP_SMOKE_TEST.md` literally says *"Target:
Claude Desktop (stdio transport)."* No live validation against any
second MCP host exists.

**The gap this research exists to close.** TORMENT's MCP server is
standard stdio JSON-RPC and should work with any compliant MCP host, but
"probably works" is not the same as "verified and documented." The
project wants TORMENT to be pitch-able as **the governed memory layer
for MCP agents in general**, not just for Claude Desktop users. That
requires: evidence it works with at least one second host, docs that
read host-agnostically, and a short honest positioning document.

---

## 2. The research question (single sentence)

**What does TORMENT's MCP server need to know, configure, and document
in order to be cleanly plug-and-play for an agent developer running
Hermes on Windows, and what is the current state of the broader MCP host
ecosystem as of April 2026 relevant to that goal?**

---

## 3. Why this request exists

The assistant that drafted the companion framing doc is confident about
the TORMENT side of this work — the existing code, the existing tools,
the doctrine, the capability boundary, the framing of deliverables.
What the assistant is **not confident** about, and what this research
request is trying to fill in, is the external-world side:

- **What exactly is "Hermes"** in the MCP-host sense, as of April 2026.
  There are multiple projects called Hermes in the AI tooling space.
  The one the project lead cares about is **the MCP host Hermes** — the
  research needs to identify which project that refers to, confirm it
  supports stdio MCP transport, and surface its actual configuration
  format and install path.
- **What Hermes-specific quirks exist** when connecting stdio MCP
  servers, especially on Windows.
- **What the current MCP host ecosystem actually looks like** as of
  April 2026 — which hosts are popular, which are dormant, which have
  changed their MCP support story since earlier in the protocol's life.
- **What common stdio MCP portability gotchas exist** (stdio buffering,
  process lifecycle, JSON-RPC version handshakes, Windows process
  spawning differences) that the TORMENT server might hit even though
  it appears correct in isolation.
- **What language the broader market uses** for "memory layer for
  agents," so the positioning doc can use terminology developers
  actually search for.

The research is not being asked to touch TORMENT code, propose new MCP
tools, or make doctrinal calls. The research is being asked to
**investigate the external landscape** and return concrete facts that
the implementation pass can then act on.

---

## 4. Target host priorities (from the project lead)

- **Tested in this pass:** Claude Desktop, Hermes. These are the short
  list. Support them well rather than half-supporting many.
- **Mentioned but explicitly untested:** Claude Code, Continue, Cline,
  and "other stdio MCP host." These go in a lower-confidence matrix row
  for discoverability; no config, no claims.
- **Explicitly excluded from this pass:** clawbot-class shells. Do not
  investigate.
- **Environment:** The project lead runs on Windows. Live smoke-test
  execution will happen in their Windows environment; this research
  should prioritize Windows-relevant details.

---

## 5. Specific questions to answer

Please answer each one concretely. Cite sources (URLs, GitHub repos,
release notes, docs pages) where possible. Flag confidence level on each
answer — confident vs "best available as of April 2026" vs unknown.

### Host identification and config

**Q1.** What is "Hermes" in the MCP host sense as of April 2026? Which
GitHub repo or project does it refer to? Provide a canonical URL.

**Q2.** Does the identified Hermes project support MCP stdio transport?
What version(s) support it? Are there separate branches or forks to be
aware of?

**Q3.** What does a valid Hermes config entry for a stdio MCP server
look like, concretely? Provide a worked example that could be pasted
into the Hermes config file to connect a standard Python stdio MCP
server — adapted from the existing TORMENT Claude Desktop config if the
structure is similar. If Hermes uses a different config format
(TOML/YAML/etc.), show the equivalent shape.

**Q4.** On Windows, are there any Hermes-specific setup considerations
(paths, shell differences, Python interpreter resolution, PYTHONPATH
handling, environment variable passing)? The existing Claude Desktop
Windows config uses full path to `python.exe` in a conda env and
explicit `PYTHONPATH` — is the same pattern needed for Hermes, or does
it resolve differently?

### Known compatibility gotchas

**Q5.** What are the known stdio MCP portability gotchas that can bite a
server which works fine with Claude Desktop but misbehaves with another
host? Specifically interested in:

- stdout/stderr buffering differences (line-buffered vs block-buffered,
  flush requirements)
- JSON-RPC version handshake differences
- Initialization sequence differences (what a host sends on connect
  before the server can respond)
- Tool-discovery payload shape differences
- Resource URI template handling
- Error response expectations
- Process lifecycle (graceful shutdown, signal handling on Windows)

If there is a known gotcha list maintained by the MCP community or in
the protocol spec, cite it.

**Q6.** Does the current TORMENT MCP server implementation
(`torment_service/mcp_server.py`, which uses the FastMCP framework if
the research can verify that from the repo) have any patterns that are
known to misbehave on hosts other than Claude Desktop? The research
need not read the full 872 lines; a high-level answer about whether
FastMCP is host-portable or has known quirks is enough.

### Broader ecosystem

**Q7.** As of April 2026, what is the state of the MCP host ecosystem?
Which hosts are actively developed and commonly used? Which are dormant
or archived? The framing doc's UNTESTED list (Claude Code, Continue,
Cline) was guessed from earlier knowledge — confirm or correct that
list, and flag any host the research thinks should be on the list that
is not.

**Q8.** Is there a canonical MCP host compatibility matrix or registry
maintained anywhere (e.g., on the MCP spec website, an anthropic repo,
a community wiki)? If yes, what does TORMENT look like it would score
against that matrix, given the surface described in section 1?

### Positioning and language

**Q9.** What terminology does the current agent-developer community use
for "memory layer for agents" or equivalent concepts? The positioning
doc wants to use language developers actually search for and recognize,
not coined terminology. Candidates to evaluate: "memory layer,"
"memory backend," "agent memory," "long-term memory for agents,"
"governed memory," "provenance-aware memory," "agent state store,"
"episodic memory for agents." Which of these are in active use? Which
are dead language? Are there better alternatives?

**Q10.** Are there currently popular projects positioning themselves as
"memory for agents" that would be TORMENT's implicit comparison set?
Naming them is not a competitive analysis ask — it is a *don't
accidentally use the same tagline they use* ask. The positioning doc
needs to be honestly differentiable, and that starts with knowing what
space TORMENT is landing into.

### Smoke-test readiness

**Q11.** Given the current `docs/MCP_SMOKE_TEST.md` (35-item checklist,
7 tools, 5 resources, 5 worked examples), are there specific test items
that would need rephrasing to be host-agnostic? For example, test 1.2
says *"Tools visible in host"* and asserts a specific count — is that
assertion phrasing portable, or does it need to become *"the host
enumerates the tools TORMENT exposes"*? List any items that need
rewording.

**Q12.** What is a reasonable expected-pass-rate for running the
existing smoke test against Hermes, cold, before any TORMENT-side
fixes? This is a calibration question so that a partial pass on first
run is not misread as catastrophe, and a full pass is not misread as
completion. If the research finds a track record of other stdio MCP
servers being tested against Hermes, that baseline is the answer.

---

## 5B. Additional questions added by the drafting assistant

*Confirmed during drafting:* TORMENT's MCP server imports
`from mcp.server.fastmcp import FastMCP` — that is the **official
Anthropic-maintained Python MCP SDK's `FastMCP` class**, not a
third-party framework of the same name. The questions below are
framed around that specific dependency. Also noted: the `mcp`
package is not pinned in `requirements.txt`; the research does
not need to investigate that (it is a TORMENT-internal fix), but
the confirmation may be useful context when answering Q13.

### Framework and protocol-version questions

**Q13.** What is the state of the official Python MCP SDK (the `mcp`
package on PyPI) as of April 2026? Specifically:

- Is `mcp.server.fastmcp.FastMCP` still the recommended way to build a
  Python stdio MCP server, or has it been deprecated in favor of a
  different class or pattern?
- What is the current stable version of the `mcp` package? What version
  range should a server maintainer pin against for broad host
  compatibility?
- Are there known issues with FastMCP on Windows specifically (process
  spawning, stdio handling, signal handling)?
- If FastMCP has been superseded, what would a "minimum diff port" from
  FastMCP to the current recommended API look like at a high level —
  one paragraph, not a code sample?

**Q14.** What is the current state of MCP protocol versioning as of
April 2026?

- What is the current stable protocol version string (e.g., `2024-11-05`
  or whatever the latest is)?
- Have there been breaking protocol changes since early stdio MCP
  servers became common in 2024–2025?
- What does the initialization handshake look like for version
  negotiation? What happens if a host speaks a newer protocol version
  than the server, or vice versa?
- Does the official Python SDK handle version negotiation automatically,
  or does the server author need to specify a version?

**Q15.** Has MCP added a "structured content" response format for tool
results since the protocol stabilized?

- Is wrapping a JSON envelope inside a single string content block
  (which TORMENT currently does by returning `json.dumps(result)` from
  each tool function) still compliant with the current protocol?
- Do newer hosts expect a `structuredContent` field or an equivalent
  typed-data response? If yes, what is the migration path for a server
  that currently returns stringified JSON?
- Would Hermes specifically care about this distinction, or is it
  primarily a Claude Desktop UX concern?

**Q16.** Are there patterns in tool descriptions or parameter schemas
that some MCP hosts tolerate and other hosts reject? For example:

- Length limits on `description` fields?
- Required fields in parameter schemas that the official SDK doesn't
  enforce?
- Parameter types some hosts don't handle (oneOf, allOf, nullable,
  arrays of mixed types, etc.)?
- Default values on parameters — allowed? required? ignored?

TORMENT currently uses plain typed parameters with defaults. A list of
known strictness divergences across hosts would help predict what
breaks first under Hermes.

### Tool-error vs governed-envelope pattern

**Q17.** TORMENT's convention when the Spine rejects an operation is to
return a **successful MCP tool response** whose body is a JSON envelope
with `{"ok": false, "decision_code": "blocked_...", "result_code":
"none", "result": null}`. The idea is that a governance rejection is
not a protocol error — it is a legitimate, auditable outcome that the
host should surface to the user.

- Is this the right MCP-native pattern, or should Spine rejections
  become MCP tool errors (i.e., exceptions propagated through the MCP
  error path) instead?
- How do different hosts render each pattern? Specifically: does Claude
  Desktop show envelope-with-ok-false clearly, and does Hermes?
- Is there a community-recognized best practice for "governance-style
  rejection inside a tool call"?
- If the answer is "some hosts handle envelope-with-ok-false badly," is
  there a middle path (e.g., wrapping the envelope in a structured
  content response with an `isError` flag)?

This question directly affects whether TORMENT's current rejection
pattern needs to change for Hermes, or whether it is already host-
portable.

### Windows-specific stdio concerns

**Q18.** What are the known Python stdio-MCP gotchas on Windows? A
non-exhaustive list of things that can bite Python stdio servers on
Windows specifically:

- Line ending differences (CRLF vs LF) corrupting JSON-RPC framing
- Default console code page (CP1252) mangling UTF-8 content
- `stdout` / `stderr` buffering defaults differing from POSIX
- Process lifecycle: orphan handling, graceful shutdown signals,
  `SIGTERM` not existing on Windows
- PYTHONIOENCODING and PYTHONUNBUFFERED environment variables —
  required? optional? host-dependent?
- Virtualenv / conda activation affecting the spawned subprocess
  environment

Does the official Python MCP SDK handle these correctly out of the box,
or does the server author need to set specific env vars / flags?
Research answer should include a *"Windows checklist for a Python
stdio MCP server"* — items the smoke test should verify are in place
before blaming cross-host issues.

### Positioning landscape questions

**Q19.** Which projects are currently positioned as "memory layer for
agents" or "long-term memory for LLM agents" as of April 2026?

Candidates the assistant is aware of at training time, for the research
to confirm or correct: **Mem0, Zep, Letta (formerly MemGPT), Cognee,
Papr Memory, LangChain memory modules, LlamaIndex memory.** Are any of
these still actively developed? Are any dormant? Are there newer
entrants the assistant is unaware of?

This is **not a competitive analysis request**. The purpose is:

- *Avoid accidental tagline collision* — if three projects already say
  "memory layer for agents," the positioning doc should pick different
  phrasing that captures what TORMENT actually does differently.
- *Identify honest differentiators* — TORMENT's governance model,
  provenance discipline, trust tiers, and capability boundary are
  unusual in this space. Knowing which differentiators are actually
  unique (vs unknowingly shared with another project) sharpens the
  positioning.
- *Surface language developers search for* — terminology the agent-dev
  community actually uses when they search for a memory solution.

Return format: for each project listed (or corrected), one line each:
name, tagline they use, one-sentence positioning summary, status
(active / dormant / archived), and one note on whether they overlap
with TORMENT's claimed differentiation.

**Q20.** Does the term **"Spine"** or **"Agent Spine"** have an
established meaning in the MCP or agent-framework ecosystem that would
collide with TORMENT's usage?

TORMENT uses "Spine" as the name of its governance layer — the thing
that sits between the MCP surface and the Fabric (memory kernel) and
enforces trust tiers, exposure tiers, and operation routing. If another
popular project uses "Spine" to mean something incompatible (e.g., a
workflow runner, an execution engine, a UI layer), that is a branding
problem for the positioning doc that the project needs to know about
before the doc ships.

One paragraph of findings is sufficient. If no collision exists, "no
collision found" is a valid answer.

### Lower-priority protocol surface questions

These are nice-to-have. Answer if sources are easily available; skip if
they require deep digging.

**Q21.** Assorted surface questions:

- **MCP auth:** Has the protocol added authentication since early stdio
  servers? Does Hermes require any auth handshake that Claude Desktop
  does not?
- **Sampling:** MCP has a "sampling" feature where servers can request
  LLM completions from the host. TORMENT does not use sampling. Do
  some hosts require the server to declare sampling support (even as
  unsupported) during init, and does the Python SDK do this
  automatically?
- **Resource URI templates:** TORMENT uses URIs like
  `torment://workspace/{workspace_id}/agent/{agent_id}/state`. Are URI
  templates handled consistently across hosts, or do some hosts require
  concrete URIs only?
- **stderr expectations:** Does Hermes or any known host parse the MCP
  server's stderr for structured logs, or is stderr free-form debug
  output?
- **Response size limits:** Do different hosts enforce different max
  sizes on tool responses? TORMENT's memory query results can be
  large; is there a documented ceiling to stay under?
- **Consent model:** Claude Desktop prompts the user for consent on
  each tool call (or on first use per session). Does Hermes have a
  consent model, a trust-on-first-use model, or a fully trusted model?
  This affects how the worked examples in MCP_README should be
  phrased.

---

## 6. Deliverables from the research

A single response document with these sections, in order:

1. **Q1–Q21 answered** concretely, with sources cited and confidence
   levels flagged. (Q1–Q12 from the project lead, Q13–Q21 from the
   drafting assistant.) Questions where the research cannot find
   reliable sources should be returned with a clear *"not confirmable
   as of April 2026"* note rather than guessed.
2. **A Hermes connection cookbook.** Not just "here is a config snippet"
   — include: install path, required env vars, how to verify the host
   actually picked up the server, and what a successful connection looks
   like in Hermes's logs or UI. Windows-specific.
3. **A portability risk list** for TORMENT's MCP server: concrete items
   the smoke test should watch for based on the known gotchas from Q5,
   Q15, Q16, Q17, and Q18, ordered by likelihood. Use the format
   *"Risk: X. Symptom: Y. Mitigation if triggered: Z."*
4. **A Windows checklist for a Python stdio MCP server** based on the
   Q18 findings — the 5–10 concrete things the project lead should
   verify are in place before blaming Hermes for any smoke-test
   failures. Format: plain checklist, each item independently
   verifiable.
5. **A framework-state verdict on FastMCP** from Q13 — one paragraph
   answering "should TORMENT stay on `mcp.server.fastmcp.FastMCP` or
   migrate to something newer?" with a confidence level. If a
   migration is recommended, flag it as a *separate* follow-up track,
   not part of the current MCP cross-host compatibility pass.
6. **A corrections list** for the framing doc's UNTESTED host row
   candidates (Claude Code, Continue, Cline, "other stdio MCP host").
   Which should stay, which should be cut, which should be added, with
   a one-line rationale for each.
7. **A positioning terminology short list** — the 3–5 phrases that
   landed as recommended from Q9, Q19, and Q20, with a one-line note on
   *why* each landed. Must include a verdict on whether "Spine" /
   "Agent Spine" is a safe term to keep using.
8. **A competitor/landscape table** from Q19 — the "memory layer for
   agents" projects confirmed to exist, with tagline, positioning
   summary, status, and TORMENT-differentiation note for each. Keep
   this short — one line per project, max 8 projects.
9. **Flagged uncertainties.** Anything the research could not confirm
   from reliable sources as of April 2026. Be honest; "could not
   confirm" is a valid research outcome and is more useful than
   guessing.

Total length guideline: 2,500–5,000 words given the expanded question
set. Shorter is fine if the answers are tight. Longer is acceptable
only if the sources are unusual enough to need quoting.

---

## 7. Source materials the researcher should read first

**In this repo, in order:**

1. `docs/MCP_CROSS_HOST_FRAMING_v2.4.x.md` — full framing doc (410
   lines). This is the context for why the research is being asked.
2. `docs/MCP_CAPABILITY_BOUNDARY.md` — the doctrine that must not be
   violated. Short, 165 lines. Read in full.
3. `docs/MCP_README.md` — the current state of user-facing MCP docs.
   Read the Quick Start, Host Configuration, and Tools sections
   specifically to understand what is currently Claude-Desktop-shaped.
4. `docs/MCP_SMOKE_TEST.md` — the current 35-item checklist. Read
   sections 1 and 2 in detail to answer Q11.
5. `torment_service/mcp_server.py` — not required in full, but the top
   ~100 lines show how the server is instantiated (which MCP framework
   it uses, what transport it opens). That is relevant to Q6.

**Outside the repo:**

- The current MCP protocol specification (find via modelcontextprotocol
  official source as of April 2026).
- Hermes project source repo and its MCP integration docs (once Q1 has
  identified which project "Hermes" refers to).
- Any maintained community list of MCP hosts.

---

## 8. Constraints on any recommendations the research makes

The research is investigation, not design, but if recommendations are
included, they must respect these hard constraints from the framing
doc. Do not propose anything that requires relaxing any of these:

- **No new MCP tools.** The 7 existing tools are correct.
- **No MCP tool-calling layer.** TORMENT does not become an agent that
  uses other people's tools.
- **No capability sprawl.** No new exposure tiers, trust tiers, decision
  codes, or result codes.
- **No host-specific hacks** unless a real portability bug makes one
  strictly necessary, and in that case a single documented gate is the
  ceiling — no sprawling compatibility layer.
- **No clawbot-class shells** in the tested or untested host lists.
- **No marketing superlatives** in any positioning language suggested.
  The capability boundary itself is the pitch.
- **No revisions to `MCP_CAPABILITY_BOUNDARY.md`.** The doctrine is
  fixed. Recommendations that implicitly require loosening it should
  be flagged as out-of-scope, not smuggled through.

---

## 9. Timeline and urgency

Not urgent. This research is the prerequisite for starting the
sandbox-side drafting of deliverables D1–D4 in the framing doc's work
order. The project lead has explicitly said this track is not time-
sensitive.

A thoughtful response with confident sourcing is better than a fast
response. If Q1 (identifying which "Hermes" is meant) cannot be resolved
with confidence, stop and return that finding as the primary deliverable
rather than guessing.

---

## 10. What happens after the research is returned

Once the research response is in hand, the workflow resumes as follows:

1. Project lead reviews the research answers and ratifies or revises the
   framing doc's open decisions based on the findings.
2. Sandbox-side drafting begins on D1 (compatibility matrix), D3 (host-
   agnostic smoke test), D2 (generalized MCP_README), and D4
   (positioning doc) — informed by the Hermes cookbook and the
   portability risk list.
3. Project lead runs the drafted smoke test against Claude Desktop and
   Hermes on their Windows environment, records results in the D3
   Results log.
4. Any real portability bugs surfaced become a conditional D5 fix
   commit, with tests.
5. Track closes with a D6 housekeeping bundle and a roadmap-notes
   update.

The research is the one step where the work meaningfully benefits from
a fresh pair of eyes that can go look at the real MCP ecosystem as of
April 2026, rather than relying on what the assistant already remembers.

---

## 11. Return format

Respond as a single Markdown document following the deliverables
structure in section 6. Cite URLs inline as `[text](url)`. Flag
confidence levels explicitly (e.g., *"Confidence: high — from official
Hermes release notes v1.2.0"* or *"Confidence: low — inferred from a
single GitHub issue"*). Put uncertainty in section 6 step 6, not
scattered through the document.

Do not include implementation code, do not draft the deliverables
themselves (D1–D4), do not write TORMENT doc content. This is
research; implementation is a separate step gated on the framing
doc's ratification, which is gated on this research.
