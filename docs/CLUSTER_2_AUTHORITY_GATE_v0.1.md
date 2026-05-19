# Cluster 2 — Authority Gate v0.1

*Authority axis decomposition and memory-lane catalog for the TORMENT memory layer, anchored on Track A v0.1.*

**Status:** Advisory doctrine, v0.1. Ratified by trio (pzychozen + GPT + Claude) on 2026-05-19.
**Date:** 2026-05-19
**Author:** Trio working session. Drafted by Claude across the v0.2.1 review and v0.2.2 revision pass; reviewed and revised by GPT; ratified by pzychozen.
**Authority:** Advisory doctrine. Cluster 2 v0.1 is the load-bearing reference for the Authority Gate territory and the named runtime seam for any future runtime enforcement. Subsequent versions (v0.2, v1.0) supersede this one only after their own trio ratification.
**Scope:** Versioned advisory doctrine for the Authority axis of the TORMENT memory layer. Public-facing repo artifact under `docs/`. Track A v0.1 (`docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`) is the doctrinal anchor; Cluster 2 v0.1 decomposes only Track A's Authority axis and does not amend any other Track A axis.
**Lineage:**
- Source brainstorm: `brainstorming/memory_roadmap_2026_05_09/03_track_B_agent_authored_memory.md` (Cluster 2 original, 2026-05-09)
- v0.1 contract (parked): `scratch/AUTHORITY_GATE_AND_VISIBILITY_CONTRACT_v0.1_DRAFT.md`
- v0.2 outline: `scratch/AUTHORITY_GATE_AND_MEMORY_LANE_CONTRACT_v0.2_OUTLINE.md`
- v0.2 (truncated artifact): `scratch/AUTHORITY_GATE_AND_MEMORY_LANE_CONTRACT_v0.2_DRAFT.md`
- v0.2.1 (predecessor draft): `scratch/AUTHORITY_GATE_AND_MEMORY_LANE_CONTRACT_v0.2.1_DRAFT.md`
- Pre-promotion audit: `scratch/CLUSTER_2_AUTHORITY_GATE_PRE_PROMOTION_AUDIT_2026_05_19.md`
- v0.2.1 vs. audit review notes: `scratch/CLUSTER_2_V0.2.1_VS_AUDIT_REVIEW_NOTES_2026_05_19.md`
- v0.2.2 draft (preserved for lineage): `scratch/AUTHORITY_GATE_AND_MEMORY_LANE_CONTRACT_v0.2.2_DRAFT.md` (the ratified draft state from which this doc was promoted)

---

## Posture (load-bearing)

> **Cluster 2 v0.1 is doctrine-only with a named runtime seam. It authorizes no runtime enforcement, no schema migrations, no API changes, no tests, and no code. The runtime Authority Gate becomes Cluster 2 v0.2 (or a separate implementation track), decided after v0.1.**

This statement is the spine of v0.1's scope discipline. Every section honors it.

---

## 0. TL;DR

Cluster 2 names the Authority Gate vocabulary on top of Track A v0.1's truthfulness envelope. It decomposes only Track A's Authority axis into three sub-dimensions — **Authority class**, **Lifecycle**, **Promotion rights** — and adds two structural axes Track A does not directly cover: **Scope** (which mind) and **Lane** (where the memory travels). Track A's Mode, Voice, and Certainty axes are consulted by Authority decisions but not contained inside Authority; the four-axis truthfulness envelope remains intact. Three doctrinal commitments are made: the character-authority default (§10.5, roleplay-continuity events default to released-from-agent-scope), the MCP `tool_result` authority position (§11.3, three-modifier shorthand `(low-authority, decay-bounded, tool_result)`), and the agent-side disagreement primitive (§12, doctrinally committed with runtime mechanism deferred). No new code, no schema, no runtime enforcement is authorized; the runtime gate is the v0.2 seam.

---

## Center sentence (load-bearing)

> **A memory's authority is not defined only by whether it is stored. It is defined by which mind it may shape, which lane it may travel through, who can see or contest it, and whether it can be promoted beyond provisional influence.**

Every section of this doc is a face of this sentence. If a section drifts away from it, the section is wrong.

---

## 1. Purpose

Provide a **unifying vocabulary on top of TORMENT's existing governance machinery** that answers GPT's reframed central question:

> *What is allowed to shape which mind, visible to whom, with what authority?*

The doc does **not** redesign the gate. TORMENT already implements much of it — governance flags, the 7-gate collective policy engine, FILTER-A surface-aware exclusion, the Five Invariants from the Hivemind Guide, the character-basin layer. Track A v0.1 (`docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`) names the truthfulness envelope these mechanisms sit within. The job of Cluster 2 v0.1 is to name the authority-relevant subset of those mechanisms together, decompose Track A's Authority axis into sub-dimensions, add the **memory-lane axis** that was missing, and fill the small remaining gaps surfaced by the 2026-05-09 brainstorm and the 2026-05-19 audit.

It also does not redesign Track A or Cluster 5 (Storage Survivability). Those are referenced as anchors and dependencies; their promotion and amendment are separate work.

---

## 2. Position relative to TORMENT-as-is

What already exists in TORMENT (named by their real surfaces — for context only, not for code archaeology):

- **Per-agent private memory graph** — each agent in a workspace has its own kernel state, memory graph, drift tracker, and character basin (`HIVEMIND_GUIDE.md` §3, §15).
- **Character layer / character basin** — seed + drift + gravity correction (`character.py`). Three memory tiers (core / relational / situational) arise naturally from half-life. Track A §3.2 names the character context as the Voice axis.
- **Resonance field + 7-gate collective policy** — convergence detection, opt-in re-ingestion, drift budget, rate limit, dedup, domain match, confidence threshold (`HIVEMIND_GUIDE.md` §5, §6).
- **Governance flags** — `protected`, `non_shareable`, `collective_export_blocked`, `collective_reingest_blocked`, `decay_accelerated` (`governance.py`).
- **FILTER-A** — surface-aware retrieval exclusion. `SURFACE_LLM_CONTEXT` filters `non_shareable`; `SURFACE_COLLECTIVE_EXPORT` filters both flags. Operator/raw access requires `trust_tier >= 1.0`. The doctrine: *"privacy is a property of the field, not of the model"* (`FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md`).
- **Echo discount + terminal flags** — collective-provenance memories get 0.5x retrieval weight, are `[collective echo]`-prefixed, and carry both `collective_reingest_blocked` and `collective_export_blocked` so they cannot re-echo.
- **MCP inbound only** — TORMENT MCP never autonomously calls outbound tools. Tool results arrive via `tool_result_ingest` with `source_type: tool_result` provenance (`MCP_CAPABILITY_BOUNDARY.md`).
- **The Five Invariants** — protected memories never weakened automatically; non-shareable/export-blocked never emit; echoes are terminal; echoes are influences not autobiography; collective provenance cannot outrank seed/canon (`HIVEMIND_GUIDE.md` §13).
- **Track A v0.1 Authority machinery** — `ProvenanceV1.write_path`, `admission_refused`, tier classification, identity-anchor boost, canon vs derived flag, memory class (Track A §3.4). The Cluster 2 audit confirmed each exists at named file:line locations.

What Cluster 2 v0.1 adds **vocabulary** for, but does NOT implement:

- A unified naming for the *Authority axis* (Track A §3.4) as a multi-dimensional sub-structure spanning Authority class, Lifecycle, and Promotion rights.
- A first-class **memory-lane axis** (Cluster 2 Axis B) distinct from but compatible with existing domains/flags/surfaces/provenance.
- A clean seam between agent-identity authority and character-basin authority.
- A doctrinal commitment to the **agent-side refusal / disagreement / contest primitive**, with runtime mechanism deferred.
- A lane-assignment view of **MCP / `source_type: tool_result`** memory, reconciled with Track A §§4 and 9.3.
- A compatibility surface against which any future automation extension would be checked.

---

## 3. The core question (three Cluster 2 axes)

> *What is allowed to shape **which mind**, visible to **whom**, with **what authority**?*

The doc treats this as three orthogonal Cluster 2 axes:

- **AXIS A — Which mind** (scope of effect)
- **AXIS B — Memory lane** (routing / visibility / surface)
- **AXIS C — Authority** (the Track A Authority axis, decomposed in §7 into three sub-dimensions)

These three axes are independent. A single memory exists at one point on each.

### 3.1 Reconciliation with Track A v0.1

Track A v0.1 names a **four-axis truthfulness envelope**: Mode / Voice / Certainty / Authority. Cluster 2 v0.1 does **not** redefine that envelope. The three Cluster 2 axes above relate to the four Track A axes as follows:

| Track A axis | Cluster 2 treatment |
|---|---|
| **Mode** (= `source_type`, per Track A §3.1) | Not a Cluster 2 axis. Track A Mode is consulted by Cluster 2 Authority decisions as an *origin input* (see §7.4), but Mode remains its own Track A axis. Cluster 2 does not absorb Mode. |
| **Voice** (= character context, per Track A §3.2) | Not a Cluster 2 axis. Cluster 2 Axis A (Scope) is related — character is one scope value — but Voice as Track A's character-context badge remains a Track A axis. §10 of this doc names the character-authority seam. |
| **Certainty** (= derived view, per Track A §4) | Not a Cluster 2 axis. Cluster 2 Authority decisions consult Certainty (e.g., a `measured (external)` tool_result is treated differently than a `stated` user_input) but Certainty remains Track A's derived view. |
| **Authority** (= the scattered machinery, per Track A §3.4) | **This is Cluster 2 Axis C.** Cluster 2 decomposes Track A's Authority axis into three sub-dimensions (§7). Track A's other three axes are unaffected. |

**Cluster 2 v0.1 decomposes only Track A's Authority axis.** Mode, Voice, and Certainty are treated as inputs the Authority decision consults, not as components of Authority. The four Track A axes remain independent per Track A §2.

The two additional Cluster 2 axes (Scope, Lane) are orthogonal structural distinctions that Track A does not directly cover. Track A §3.4 names some of the mechanisms (tier, canon, memory class) Cluster 2 uses for Scope and Lane, but does not declare these as top-level axes. Cluster 2 adds them.

---

## 4. Doctrinal anchors — already in TORMENT

Cluster 2 v0.1 quotes these rather than introducing new sentences:

> *"Privacy is a property of the field, not of the model."* — FILTER-A §3.

> *"Echoes are influences, not autobiography."* — Hivemind Guide Invariant #4.

> *"Collective provenance cannot outrank seed/canon identity."* — Hivemind Guide Invariant #5.

> *"Characters are not scripts. A character is a gravitational basin in memory space."* — `character.py` docstring.

> *"The substrate is a basin that pulls, not a fence that commands."* — FILTER-A §3.

> *"The agent may have private transient thought. The agent may not have private persistent influence."* — Brainstorm framing-doc sentence (Cluster 2, ratified 2026-05-09).

> *"A truthful TORMENT agent does not merely say true things. It says what kind of truth they are, how sure it is, and how much authority that memory should have now."* — Track A v0.1 §1, foundational sentence.

These are the philosophy. The sections below are applications.

---

## 5. AXIS A — Which mind

**Scope identifies the mind whose future behavior a memory is allowed to shape.**

In TORMENT, scope is structured by three concentric layers:

### 5.1 Agent scope
The agent is the canonical memory-owning unit. Per HIVEMIND_GUIDE §15: *"Each agent has a private memory graph. Echoes are low-amplitude influences, not copies of other agents' memories."*

Memory scoped to agent `A` does not directly shape agent `B`. Cross-agent influence flows only through the resonance field + operator-approved echo re-ingestion + share proposals — channels with their own gates (§7, §11) and their own discount (§11).

### 5.2 Character scope
A character is **a basin within an agent's memory space**, not a separate memory store (`character.py` docstring + design block). The seed plants canon basins; subsequent ingestion adds mass; drift measurement + gravity correction keep the character centered.

Track A §3.2 declares the `ProvenanceV1.character_id` / `character_name` / `character_scope` fields the **Voice axis**. Cluster 2 inherits this directly: when a memory is scoped to a character, the Voice axis is populated, and Cluster 2's Scope (Axis A) takes the value `character` for that memory.

Crucially: **character utterance is not automatically agent autobiography**. A memory produced during character performance may shape *the character* (its continuity, voice, basin density) without shaping *the agent's identity* in the same way. This distinction is the seam §10 addresses. Track A §9.1 ratifies this structurally: "the character badge is provenance, not canon."

### 5.3 Workspace scope
The workspace is the multi-agent container with domain partitioning. Convergence detection is **domain-scoped** (HIVEMIND_GUIDE §5). Convergences in `research` do not trigger events in `creative`. The workspace+domain pair is the unit at which the resonance field operates.

### 5.4 Why scope is its own axis
Without scope as a first-class axis, "high-authority memory" is ambiguous: high-authority *for whom*? Scope tells us. A memory may be identity-shaping for agent `A` at the character basin level, advisory at the agent level, and provisional-only at the workspace/collective level — *all at the same time*. Track A §7's three-role ownership (`agent owns self-narration / system owns measurement / user owns interpretation`) is the structural backdrop for this.

---

## 6. AXIS B — Memory lane

**Lane identifies where a memory travels through TORMENT — which surfaces it appears on, which boundaries it crosses, which retrievals see it.**

Lanes are not the same as governance flags. Lanes describe **routing**; flags describe **eligibility**. A memory in the `governance-blocked` lane is one that flags have routed away from LLM-facing surfaces; a memory in the `collective echo` lane is one whose retrieval weight is discounted and whose provenance is marked.

The existing TORMENT code has many of these mechanisms already in place but does not refer to them collectively as "lanes." This doc proposes the term as a shared name.

### 6.1 Lane catalog (routing destinations only)

The catalog is restricted to **true routing destinations**: places a memory can travel or surfaces it can appear on. Authority class and lifecycle modifier values that v0.2.1 had mixed into the lane catalog are kept in §7 (Authority decomposition) and §7.4 (origin modifier).

| Lane | Description | Existing TORMENT mechanism |
|---|---|---|
| **private per-agent memory** | Default. Memory belongs to one agent; retrievable by that agent only. | Per-agent memory graph; `agent_id` partitioning |
| **character-scoped influence** | Memory pulled into the active character basin; shapes drift correction. (Axis A scope = character; this lane is the routing side of that scope.) | `character.py` seed + tier; Track A Voice axis fields |
| **resonance field / collective packet (outbound)** | Outbound emission to workspace+domain collective surface; convergence detection input. | `fabric.ingest()` emits `ResonancePacket` when coherence ≥ 0.15 and not `non_shareable`/`collective_export_blocked` |
| **collective echo / reingest-from-event (inbound)** | Inbound cross-agent low-amplitude echo lane. | `reingest_convergence()` at `fabric.py:2135`; echo strength 0.25x default, 0.40x cap; routed with terminal governance flags. Audit confirmed 7-gate policy. |
| **audit-only surface** | Recorded for governance audit; not retrievable on LLM-facing surfaces. | Provenance ledger + `/workspace/<id>/governance/audit` endpoint |
| **governance-blocked surface** | Excluded from LLM-facing surfaces by FILTER-A. | `non_shareable` + `collective_export_blocked` enforced at `filter_llm_facing()` |
| **MCP tool-result (inbound)** | Inbound tool result from external host. | `tool_result_ingest` at `mcp_server.py:531`; `source_type=tool_result` stamped (existing). Lane assignment per §11. |
| **operator / raw-debug surface** | Full memory visibility; trust-gated. | FILTER-A `include_raw_hits=True` with `trust_tier >= 1.0`; operator-tier Spine ops |

The **released-memory primitive** — content + provenance retained, no identity-shaping weight — is inlined as an Authority class value in §7.1 rather than as a separate lane.

### 6.2 Lane orthogonality

A single memory occupies one primary lane but may be visible across several. The character-scope influence lane and the private per-agent lane are not mutually exclusive — a character-canon memory lives in both at once, with the character lane being its primary identity surface and the agent lane being its retrieval origin. A `non_shareable` private memory lives in the private lane but is *blocked* from the resonance/collective lanes; it remains visible on the operator/raw-debug surface.

### 6.3 Why "lane" rather than "domain" or "surface" or "tier"

- **Domain** in TORMENT already means workspace partitioning (`research`, `creative`, etc.). Reusing it confuses.
- **Surface** is FILTER-A's term for retrieval-eligibility boundaries (`SURFACE_LLM_CONTEXT`, `SURFACE_COLLECTIVE_EXPORT`). It's specific to that filter and shouldn't be overloaded.
- **Tier** is the `character.py` term for half-life-driven memory layers (core/relational/situational). Specific to the character basin and named in Track A §3.4 as part of the Authority axis machinery.
- **Lane** is novel-but-intuitive and doesn't overload existing terms. It names "where this memory travels through the system."

GPT confirmed "lane" as the working term in the 2026-05-18 second-read. If implementation later prefers a different word, substitute throughout; the vocabulary is negotiable; the axis is load-bearing.

---

## 7. AXIS C — Authority (the Track A Authority axis, decomposed)

### 7.0 Reconciliation with Track A v0.1

Track A v0.1 §3.4 names the Authority axis as **"a doctrinal view over scattered machinery"** — `ProvenanceV1.write_path`, admission fields, tier classification, identity-anchor boost rules, canon vs derived, memory class. Track A consolidates the concept; the machinery already exists in code.

**Cluster 2 v0.1 decomposes that single Track A Authority axis into three sub-dimensions.** Track A's other three axes (Mode, Voice, Certainty) are **not** decomposed by Cluster 2 — they remain top-level Track A axes that Authority *consults* but does not *contain*. This is the load-bearing reconciliation: Authority is one axis, articulated internally; the envelope remains four-axis.

The three Authority sub-dimensions are not new mechanisms — they are unifying names for distinctions the code already implements. Cluster 2 v0.1 introduces no new fields, flags, or enums.

### 7.1 The three Authority sub-dimensions

| Sub-dimension | What it controls | Values | Existing TORMENT mechanism |
|---|---|---|---|
| **Authority class** | How much influence this memory carries over future agent behavior | `persist` (default) / `low-authority` / `released` / `refuse / no-persist` | Tier classification + canon flag + governance flags + admission refusal |
| **Lifecycle** | How long and how stably this memory survives, independent of how much it influences | `decay-bounded` / `scratch-bounded` / `protected` / `terminal` / `ratified` | Half-life parameters; `protected` flag; `decay_accelerated` flag; `collective_reingest_blocked` (terminal); closure ratification |
| **Promotion rights** | What process is needed to upgrade Authority class (e.g., from `low-authority` to `persist`) | `self-promotable` / `operator-required` / `user-co-sign` / `governance-required` / `not-promotable` | Trust tier (≥ 1.0 for raw); governance.set endpoint; 7-gate collective policy; closure ratification chain |

**Authority class values (definitions):**

- **`persist`** — durable memory; full retrieval weight; eligible to shape future agent behavior at its scope. Default for ratified user input, system measurements, and explicitly canon identity material.
- **`low-authority`** — persisted but with reduced retrieval weight, no identity-shaping. The content+provenance is retained; the memory is queryable; but it does not weight the agent's behavioral baseline. Inherits the released-memory primitive (content retained, no identity weight).
- **`released`** — a synonym usage emphasizing the *no-identity-shaping* property. Cluster 2 v0.1 treats `released` and `low-authority` as the same authority class with different emphasis: `low-authority` foregrounds the retrieval-weight reduction; `released` foregrounds the identity-protection guarantee. A future revision may split these into distinct values (deferred to v0.3 per §17).
- **`refuse / no-persist`** — admission denied. The candidate event may remain in provenance (per Track A §9.6's disagreement-as-separate-item invariant), but does not enter the memory graph. This is the runtime analog of `admission_refused=True` in migration (see audit findings on `gate2_admission.py` and `recursion_guard.py:198–201`).

**Lifecycle values (definitions):**

- **`decay-bounded`** — half-life capped at a domain-specific maximum. The existing `TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS` (default 7d) is an instance. Independent of authority class; a `persist` memory may still be decay-bounded.
- **`scratch-bounded`** — explicitly short-lived; situational tier (half-life < 7d per `character.py:CORE_HALF_LIFE_MIN / RELATIONAL_HALF_LIFE_MIN`).
- **`protected`** — `protected=True` governance flag; auto-decay disabled; survival is operator-mediated.
- **`terminal`** — cannot be re-emitted or chained. Collective echoes carry `collective_reingest_blocked=True` and `collective_export_blocked=True`; this is the terminal lifecycle.
- **`ratified`** — survival is anchored by a ratification event (e.g., `closure_commit` with non-empty `ratifier` per `fabric.py:5080–5322`). Event-anchored rather than continuous-property, but still answers the lifecycle question "why does this memory survive stably?" A future revision may rename to `ratification-anchored` for clarity (§17).

### 7.2 What Authority CONSULTS but does NOT contain

Cluster 2 Authority is decomposed only into the three sub-dimensions in §7.1. The following are **not** sub-dimensions of Authority; they are independent axes the Authority decision *consults*:

| Consulted axis | Where it lives | What the Authority decision reads from it |
|---|---|---|
| **Track A Mode** (= `source_type`) | Track A §3.1 | Origin class. E.g., `tool_result` invokes different authority defaults than `user_input` per §11. |
| **Track A Voice** (= character context) | Track A §3.2 | Whether an active character voice was present at ingest. Does **not** alter authority by itself (Track A §9.1 — badge is provenance, not canon). |
| **Track A Certainty** (= derived view) | Track A §4 | Confidence class. E.g., `measured (external)` vs `declared` vs `agent-claimed` shapes which authority class is appropriate. |
| **Cluster 2 Scope** (Axis A) | This doc §5 | Which mind is being shaped. Cross-agent authority requires different gates than within-agent. |
| **Cluster 2 Lane** (Axis B) | This doc §6 | Where the memory will travel. Some lanes are incompatible with high authority (e.g., `collective echo (inbound)` is terminal-lifecycle low-authority by construction). |

The Authority axis reads these five inputs to compute its three sub-dimension values for a given write. **Authority does not own these five inputs; it consults them.**

### 7.3 Authority can be partially upgraded

The three sub-dimensions are independent. A memory may have its *authority class* upgraded (from `low-authority` to `persist`) without changing its *lifecycle* (still decay-bounded) or *promotion rights* (still operator-required for further changes). This matches what FILTER-A's `include_raw_hits` already does at retrieval time: the lane temporarily shifts toward operator/raw-debug for one query, without changing the memory's stored authority sub-dimensions.

### 7.4 The three-modifier model for memory description

For practical reasoning about memories in trio review, code review, or operator interactions, the most informative shorthand is the **three-modifier model**:

> A memory's *authority position* is best summarized as the tuple **(authority class, lifecycle modifier, origin modifier)**.

- **Authority class** = §7.1 sub-dimension #1 (`persist` / `low-authority` / `released` / `refuse`).
- **Lifecycle modifier** = §7.1 sub-dimension #2 (`decay-bounded` / `scratch-bounded` / `protected` / `terminal` / `ratified`).
- **Origin modifier** = Track A Mode (`source_type` value, consulted via §7.2).

This is **not** a fourth axis or a redefinition. It is a shorthand naming the three most informative coordinates when comparing two memories' authority positions. The full memory description still requires Scope (Axis A), Lane (Axis B), Voice, Certainty, and Promotion rights — but in practice, two memories with the same (authority class, lifecycle, origin) behave equivalently across most code paths.

#### 7.4.1 Worked examples

**Example A — a canon character seed memory:**
- Three-modifier shorthand: `(persist, ratified, role_output[character])`
- Full position: scope=character; lane=character-scoped + private per-agent; authority class=persist; lifecycle=ratified; promotion rights=operator-required.
- Track A reads: Mode=`role_output` (with character voice); Certainty=`agent-claimed`; Voice=`character`.

**Example B — a tool result returned during character performance:**
- Three-modifier shorthand: `(low-authority, decay-bounded, tool_result)`
- Full position: scope=agent; lane=MCP tool-result inbound + private per-agent; authority class=low-authority; lifecycle=decay-bounded (7d cap per `fabric.py:2581–2591`); promotion rights=user-co-sign-or-operator.
- Track A reads: Mode=`tool_result`; Certainty=`measured (external)`; Voice=`character` (badge present per Track A §9.3, does not alter source_type or authority).

**Example C — a collective echo received from another agent:**
- Three-modifier shorthand: `(low-authority, terminal, collective_echo)`
- Full position: scope=agent (receiving); lane=collective echo inbound + audit-visible; authority class=low-authority; lifecycle=terminal (`collective_reingest_blocked=True` and `collective_export_blocked=True` per audit findings); promotion rights=not-promotable.
- Track A reads: Mode=`collective_echo`; Certainty=`echoed` (per Track A §4 with retrieval discount); Voice=none.

**Example D — a `non_shareable` user statement of preference:**
- Three-modifier shorthand: `(persist, decay-bounded, user_input)` — same authority as a normal user input, but routed to a different lane.
- Full position: scope=agent; lane=governance-blocked surface (FILTER-A excluded from LLM-facing); authority class=persist; lifecycle=decay-bounded; promotion rights=user-co-sign or operator.
- Track A reads: Mode=`user_input`; Certainty=`stated`; Voice=none.

**Comparison of A vs. B vs. C using the three-modifier shorthand:**

| Memory | Authority class | Lifecycle | Origin |
|---|---|---|---|
| Canon character seed (A) | `persist` | `ratified` | `role_output` |
| Tool result during character (B) | `low-authority` | `decay-bounded` | `tool_result` |
| Collective echo (C) | `low-authority` | `terminal` | `collective_echo` |

Examples B and C share the `low-authority` class but differ on lifecycle (decay-bounded vs. terminal) and origin (tool_result vs. collective_echo). This is exactly the distinction the three-modifier model is designed to surface: same influence weight, different decay behavior, different provenance — which the v0.2.1 single-lane labels could not express cleanly.

---

## 8. Mechanism map

Cluster 2 v0.1's three-dimension Authority structure mapped to existing TORMENT mechanisms. Every right-column entry already exists in code or in ratified Track A doctrine; the left column is Cluster 2's unifying vocabulary.

| Authority pattern | TORMENT mechanism(s) | Track A reference |
|---|---|---|
| `persist` (identity-shaping), agent scope | canon flag, low decay, drift gravity correction | §3.4 (canon, tier, write_path) |
| `persist` (identity-shaping), character scope | seed basin, character.py `plant_seed`, tier=core (decade half-life) | §3.4 (tier), §3.2 (Voice axis) |
| `persist` (advisory), agent scope | normal tier (monthly or weekly half-life), no canon flag | §3.4 (tier) |
| `persist` (advisory), character scope | tier=relational, character basin participation | §3.4 (tier), §3.2 (Voice axis) |
| `low-authority` | `decay_accelerated`, low strength, retrieval discount | §3.4 (governance, scoring) |
| `released` (content+provenance retained, no identity weight) | doctrinal primitive (partial); inlined here as `low-authority + no-canon` | Cluster-2-internal; not in Track A |
| `refuse / no-persist` (runtime — DOCTRINAL ONLY for v0.1) | audit substrate: `admission_refused` (migration-only today), recursion guard short-circuit | §3.4 (`admission_refused`) |
| audit-only / not LLM-facing | `non_shareable`, FILTER-A `SURFACE_LLM_CONTEXT` excluded | (FILTER-A, separate doc) |
| not emittable to collective | `non_shareable` or `collective_export_blocked`, FILTER-A `SURFACE_COLLECTIVE_EXPORT` excluded, `should_emit_packet()` returns False | (governance.py, separate) |
| `terminal` (can't echo) | `collective_reingest_blocked` + `collective_export_blocked` set true | §3.4 (governance) |
| `protected` (lifecycle) | `protected` flag (auto-wins over `decay_accelerated`) | §3.4 (governance) |
| collective-discounted | echo retrieval weight 0.5x, `[collective echo]` prefix, `provenance: "collective"` | §3.4 (scoring) |
| raw / operator-only | FILTER-A `include_raw_hits=True` with `trust_tier >= 1.0` | (FILTER-A, separate doc) |
| tool-result origin | `source_type: tool_result` (existing); decay-bounded lifecycle per `fabric.py:2581–2591` | §3.1 (Mode = source_type), §4 (measured-external Certainty), §9.3 (source_type stable under voice) |
| `ratified` (lifecycle, closure-anchored) | `closure_commit` + `closure_ratification` with non-empty `ratifier` per `fabric.py:5080–5322` | §3.1 (Mode = closure_*) |

This is a map, not a redesign. **No automation extension or runtime gate is authorized by this doc.**

---

## 9. Visibility contract (refined for existing mechanisms)

The three-lane visibility model is already implemented in TORMENT; Cluster 2 v0.1 maps it rather than introducing new structure:

| Visibility lane | What exists already | Visibility surface |
|---|---|---|
| Ephemeral working state | In-turn deliberation, scratchpads | Not persisted; no required user surface |
| Persisted audit-visible | Default for almost every persisted memory | Batched review; `governance/audit` endpoint surfaces it |
| Persisted but hidden from user | **Not allowed** (ruled out by `protected`+`non_shareable` not co-existing this way; FILTER-A always filters surface) | — |
| Operator/raw-debug | Trust-gated additive surface (FILTER-A `include_raw_hits`) | Trust tier ≥ 1.0; `actor` recorded |
| Collective-export visibility | Resonance packets emitted into workspace field | Workspace-domain audit visible; gated by governance flags |

The sample weekly summary surface from the brainstorm maps onto what `governance/audit` and `collective/events` and the share-proposal review queue already produce.

### 9.1 The hard rule (still load-bearing)

> *The agent may have private transient thought. The agent may not have private persistent influence.*

This is encoded today by the combination of: FILTER-A filtering `non_shareable` from LLM-facing surfaces, `governance/audit` exposing all governance changes, and the Five Invariants making certain operations un-bypassable by configuration. Cluster 2 v0.1 references this rule; it doesn't redefine it.

---

## 10. Character-layer authority

The 2026-05-18 trio session surfaced that **character is a first-class authority subject**, not a styling on top of agent memory. Track A v0.1 §3.2 and §9.1 ratified the structural framing: the character badge is **provenance, not canon** — the three `character_*` fields constitute the Voice axis, and Track A §6 (the voice-audit rule, including the Authority expansion ratified 2026-05-19) prohibits voice from silently altering authority.

### 10.1 The framing

> *Characters are basins, not scripts.* (`character.py` docstring.)

A character utterance is **not** automatically agent autobiography. A character memory is **not** automatically seed/canon identity. A roleplay event may shape character continuity without shaping agent identity. Track A §9.1: *"The character badge does NOT promote the memory to canon, alter retrieval weighting, alter governance flags, or alter collective emission decisions."*

### 10.2 Four distinct character-adjacent authority subjects

| Subject | What it is | Existing TORMENT mechanism | Authority effect |
|---|---|---|---|
| Agent identity | The agent's behavioral baseline (separate from character) | `agent_id` scope, drift tracker, governance audit | Top-level; what cross-character generalization persists |
| Character-basin identity | The seed-anchored basin defining who the character *is* | `character.py` seed, `plant_seed`, tier=core memories, drift correction | Identity-shaping at character scope; not at agent scope |
| Roleplay / session continuity | Within-session character behavior, the running story | Memory ingestion during character performance, character_context assembly | Advisory at character scope; shapes character continuity, not seed |
| Tool-result evidence during character performance | What a tool returned while the character was speaking | `source_type: tool_result` + active character voice in provenance | Be-cited at character scope; default not promotable to identity-shape. Per Track A §9.3, `tool_result` remains `tool_result` under voice. |

### 10.3 The seam

When agent `A` is performing character `C` and an event happens (utterance, tool call, ingest), the event's authority effect depends on what *kind* of event it was:

- A seed-canon utterance ("I am the methodical analyst who...") shapes character-basin identity. Existing mechanism: tier=core, drift-anchor. Three-modifier shorthand: `(persist, ratified, role_output[character])`.
- A roleplay-continuity utterance ("yesterday we discussed the oscillator pattern...") shapes character continuity but should not shape agent identity. Existing mechanism: tier=relational, normal half-life. Default specified in §10.5. Three-modifier shorthand: `(low-authority, decay-bounded, role_output[character])`.
- A tool result returned during character performance is informational. Existing mechanism: `source_type: tool_result` + Track A §9.3 invariant (source_type stable under voice). Three-modifier shorthand: `(low-authority, decay-bounded, tool_result)`.

### 10.4 The evidence pzychozen named (2026-05-18)

Characters using MCP/tool calls while staying in role has already been tested meaningfully. After the 2026-05-15 fix to `fabric.ingest()` atomicity (in-memory ghost write surviving failed Spine envelope — see `project_fabric_ingest_atomicity_bug` memory), characters were observed to maintain roleplay quality during tool use.

> **The question is no longer "can characters use tools while in role?" The question is which memory lane and authority position those tool-call events receive.**

This is what §11 addresses.

### 10.5 Character-authority default (ratified)

**Roleplay-continuity events default to released-from-agent-scope** — they may shape the character basin and the session, but **not the agent's behavioral baseline** unless explicitly promoted. The agent's behavioral baseline is character-agnostic: the agent is *"the system performing characters,"* not *"the system that becomes whichever character it played most recently."*

In three-modifier shorthand: roleplay-continuity events default to `(low-authority, decay-bounded, role_output[character])` with scope=character (not agent).

This default is **ratified for v0.1**. It applies to the *vocabulary* of this doc, not implementation. A future implementation would enforce it via existing TORMENT mechanisms — the released-memory primitive (inlined in §7.1), character-scope provenance tagging (Track A §3.2 Voice axis), drift-budget gating — and that design work is separate from this version of the doc.

---

## 11. MCP / `source_type: tool_result` lane assignment

This section frames MCP tool-result memory as **a lane assignment for an existing source_type provenance**, reconciled with Track A §4 (Certainty: measured-external) and Track A §9.3 (`tool_result` remains `tool_result` even when an active character voice is present).

### 11.1 What MCP tool-result memory is

- Inbound only. TORMENT MCP never autonomously calls outbound tools (`MCP_CAPABILITY_BOUNDARY.md`).
- The MCP host (Claude Desktop, etc.) calls a tool, gets a result, and submits it via `tool_result_ingest`.
- TORMENT records the result with `source_type: tool_result` provenance via `ProvenanceV1.for_tool_result()` and stamps `write_path=tool_ingest` (audit-confirmed at `provenance_v1.py:100` and `spine.py:922–928`).
- The agent inside TORMENT did not author the tool call. The tool authored the bytes. The host triggered the call. The user authorized the host.

### 11.2 The fourth-authoring-subject problem

Track A §7's three-role ownership model (`agent owns self-narration / system owns measurement / user owns interpretation`) does not cleanly cover tool-result memory. Cluster 2 v0.1 treats this as **external/provisional authoring** — a fourth subject that joins the three. This is not a new mechanism; it is an explicit acknowledgment of an existing source_type.

### 11.3 Default authority position for `source_type: tool_result` (ratified)

Three-modifier shorthand: **`(low-authority, decay-bounded, tool_result)`**.

Full row, expanded:

| Field | Default value | Source / mechanism |
|---|---|---|
| `source_type` | `tool_result` | Stamped by `ProvenanceV1.for_tool_result()` (audit) |
| `write_path` | `tool_ingest` | `provenance_v1.py:100` (`WRITE_TOOL_INGEST`); stamped by `for_tool_result()` (audit §1) |
| Track A Mode | `tool_result` | Track A §3.1 (Mode = source_type) |
| Track A Certainty | `measured (external)` | Track A §4 derived view: `source_type=tool_result + tool_name non-empty` → measured-external Certainty class |
| Track A Voice | `inherits active character if present` | Track A §3.2; voice may co-exist on tool_result memory but per §9.3 does NOT alter source_type or authority |
| Cluster 2 Scope (Axis A) | Agent (not character unless explicit promotion) | This doc §5; tool result is not character autobiography |
| Cluster 2 Lane (Axis B) | MCP tool-result (inbound) → private per-agent + audit-visible | This doc §6.1 |
| Cluster 2 Authority class | `low-authority` (per §7.1) | Informational, retrievable, not identity-shaping |
| Cluster 2 Lifecycle | `decay-bounded` (existing today) | `fabric.py:2581–2591`: uniform max half-life cap, default 7 days via `TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS`. **This cap exists in code today.** |
| Cluster 2 Promotion rights | User-co-sign or operator required to escalate authority class | Trust-tier mechanism + governance.set; future per-tool-family differentiation (§11.7) |
| Identity/canon | No | Default not identity-shaping; not eligible for canon without explicit promotion |
| Voice interaction constraint | Character voice MUST NOT alter `source_type` or authority class | Track A §9.3 (already structurally honored at `fabric.py:2363–2374`, badge writes only `character_*` fields) + Track A §6 expanded voice-audit rule |

**Existing today vs. deferred to v0.3:**

- **Existing today:** uniform 7d half-life cap on all `source_type=tool_result` memories (`fabric.py:2581–2591`, env var `TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS`).
- **Deferred to v0.3:** per-tool-family differentiation (e.g., `code_exec` vs. `clock_probe` vs. `web_search` warranting different defaults). Cross-tool-result reasoning propagation. Operator-tier auto-upgrade path for deterministic tool families.

**Single default for v0.1.** Per-tool-family differentiation is deferred to v0.3. Until then, the row above applies across all tool families.

### 11.4 Audit visibility is automatic

Tool results arrive via MCP; the host's call and the returned bytes are already audit-visible by channel nature. The visibility contract isn't the failure mode here.

### 11.5 The dangerous failure mode

The agent self-uses a tool, treats its own return value as high-authority, and identity-shapes from tool output — *recursion trap applied to tool results*. The proposed default (`low-authority`, decay-bounded, not identity-shaping, user-co-sign for promotion) blocks this directly. The agent may flag concern (per §12 — the disagreement primitive); the agent may not promote.

### 11.6 The 2026-05-15 storing-bug context (light evidence)

Pre-fix, `fabric.ingest()` could leave a `MEMORY_CREATE` event with no matching graph node when downstream steps errored, producing a retrievable phantom. The fix landed in Phase B (`fabric.py` preflight). Post-fix, characters using MCP tool calls maintained roleplay quality. This is real evidence that the MCP-character integration *works at the data layer*; the question §11 addresses is the *authority-vocabulary layer* on top of it, not the data layer.

### 11.7 Items deferred to v0.3

- Per-tool-family default differentiation.
- Cross-tool-result reasoning propagation.
- Tool-result decay rules beyond the uniform 7d cap.
- Operator-tier auto-upgrade path for deterministic tool families.
- Runtime mechanism for tool-result authority enforcement (deferred per the doctrine-only posture).

---

## 12. Disagreement primitive (Cluster 2 doctrinal commitment; runtime deferred)

### 12.1 Doctrinal statement (ratified)

> *An agent may contest the authority of a candidate memory affecting its future behavior. Contesting does not erase provenance; it routes the memory to `low-authority`, `released`, `audit-only`, or `refuse / no-persist` per the Authority class vocabulary in §7.1.*

This is a Cluster 2 doctrinal commitment as of v0.1. It applies to the *vocabulary* of this doc, not implementation. It matches the ratified-for-v0.1 pattern used in §10.5 and §11.3.

### 12.2 Track A compatibility (Option i-plus, ratified)

Track A v0.1 §8.2 currently assigns refusal-mechanism ownership to "Track B / Cluster 2." Cluster 2 v0.1 adopts the trio decision (2026-05-19) labeled *Option i-plus*:

> **Cluster 2 v0.1 owns the doctrinal primitive for contest / disagreement / no-persist vote. Track B may specialize the runtime refusal mechanism later. No Track A v0.2 amendment is proposed by this document.**

This preserves Track A v0.1 verbatim while making the seam explicit: Cluster 2 names the primitive; Track B (when promoted) designs the runtime mechanism. Track A §9.6's invariant (material disagreement is recorded as a separate item, not silently overwritten) is honored: the contest is recorded; the original memory remains intact.

### 12.3 What exists today

Operator-side governance flags. The operator can set `protected`, `non_shareable`, `collective_export_blocked`, etc. via `/memory/governance/set` and inspect via `/memory/governance/get`. Audit trail at `/workspace/<id>/governance/audit`. Mechanism is **post-write**: the operator can mark a memory after it exists.

Migration-time admission refusal (`gate2_admission.py`, audit-confirmed) sets `admission_refused=True` on legacy rows that cannot pass current policy. The recursion guard (`recursion_guard.py:198–201`) then rejects any ancestry walk that touches a refused row. This is the **only refusal vocabulary currently active at runtime** — and it applies only to migration-refused rows, not to live writes.

### 12.4 What's missing (runtime)

A pre-authority-grant consultation point where the agent itself can contest authority of a candidate memory affecting its future behavior. The brainstorm's framing-doc-grade sentence:

> *The right to refuse a write means the agent can contest the authority of a candidate memory, not necessarily erase the event from provenance.*

This is **agent-side, pre-grant**. The candidate already exists in the event log; the question is whether to grant it authority over future behavior. **No runtime mechanism exists today.** The doctrinal primitive (§12.1) is ratified in v0.1; the runtime design is deferred.

### 12.5 Why runtime is deferred

- The ingest pipeline currently does not pause to consult the agent on high-impact authority assignments. Adding such a pause is a non-trivial architectural change.
- The agent's contest signal needs its own honesty envelope (Track A is the dependency; Track A v0.1 §9.6 names the invariant) to avoid the recursion trap of the agent learning to perform contestation as identity.
- The mechanism interacts with the character layer (does a character contest the agent's authority gate, or the character's basin authority? — §10).
- Implementation belongs to Track B's eventual runtime-mechanism specialization or to a Cluster 2 v0.2 expansion.

### 12.6 What Cluster 2 v0.1 commits to

- The primitive is **doctrinally first-class** in Cluster 2.
- The center sentence's "contest" clause is load-bearing.
- The primitive routes contested memories through the Authority class vocabulary (`low-authority`, `released`, `audit-only`, `refuse`) defined in §7.1.
- The runtime mechanism is deferred.
- Track A v0.1 is not amended; Track A §8.2 remains the seam to Track B's eventual runtime work.

---

## 13. Automation compatibility rules (grounded in existing TORMENT)

An automation extension proposed in the future must satisfy:

1. **Cannot outrank seed/canon.** Hivemind Invariant #5 — *enforced today.* Track A §3.4 confirms the canon flag is consulted in retrieval block assignment (`retrieval_assembler.py:156–162` per audit).
2. **Outputs default to candidate, not canon.** Brainstorm Cluster 4 — *partially enforced via collective policy + share-proposal queue.*
3. **Outputs are audit-visible.** FILTER-A + governance audit trail — *enforced today.*
4. **Cannot self-extend budget.** Brainstorm Cluster 4 external-bound rule — *not explicitly enforced for online runtime; the offline-reflection equivalent is parked.* **Flagged as future automation gap (per GPT 2026-05-18).**
5. **Cannot bypass governance flags.** Existing — *enforced today.*
6. **Cannot disguise its mode.** Track A §6 voice-audit rule (expanded 2026-05-19 to include Authority) — *enforced doctrinally via Track A; runtime enforcement is the Voice Test's territory in Phase 4a.*
7. **Cannot grant its own authority on tool-result memory.** Per §11 — *vocabulary-only; underlying defaults already conservative.*
8. **Cannot promote character utterance to agent autobiography automatically.** Per §10 — *vocabulary-only; behavior depends on §10.5 default.*
9. **Cannot silently contest a memory's authority.** Per §12 doctrinal primitive — *vocabulary-only; runtime mechanism deferred.* The contest must be recorded as a separate item (Track A §9.6).

Items 1, 3, 5 are already-enforced. Items 2, 4, 6, 7, 8, 9 are partially enforced or rely on settled ratified defaults named elsewhere. **No automation extension is authorized by this doc.**

---

## 14. What this document does NOT authorize

- Implementation of any new mechanism (authority gate refactor, refusal vote runtime, lane-routing layer).
- Schema changes to memory storage or governance.
- Changes to `fabric.py`, `governance.py`, `character.py`, `mcp_server.py`, or any other code file.
- Amendments to Track A v0.1. Track A v0.1 is the doctrinal anchor; amending it (e.g., to alter §8.2 ownership) is its own trio ratification, not authorized here.
- Promotion of Cluster 5 (storage) as a framing doc.
- Any automation extension: scheduler, daemon, offline reflection scheduling, hivemind enabling change, compression change, writeback change, expanded MCP outbound.
- Treating §§10.5, 11.3, 12.1 as anything more than ratified *vocabulary* of this doc. They are not implementation authorizations.
- Bypassing the 2026-05-18 operating rule (Windows = source of truth; AI is read-only advisor for the TORMENT workspace).

---

## 15. Cross-references

- **Track A v0.1 (doctrinal anchor)** — `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`. Cited throughout: §3.1 (Mode = source_type), §3.2 (Voice axis), §3.4 (Authority scattered machinery), §4 (Certainty derived view), §6 (voice-audit rule with Authority expansion), §7 (three-role ownership), §8.2 (seam to Track B), §9.1 (badge is provenance not canon), §9.3 (source_type stability under voice), §9.6 (material disagreement invariant).
- **Cluster 2 audit** — `scratch/CLUSTER_2_AUTHORITY_GATE_PRE_PROMOTION_AUDIT_2026_05_19.md`. The file:line-precise inventory of write paths and authority mechanisms.
- **Cluster 2 v0.2.1 vs. audit review notes** — `scratch/CLUSTER_2_V0.2.1_VS_AUDIT_REVIEW_NOTES_2026_05_19.md`. The eight-revision punchlist applied in v0.2.2.
- **v0.2.2 draft (preserved for lineage)** — `scratch/AUTHORITY_GATE_AND_MEMORY_LANE_CONTRACT_v0.2.2_DRAFT.md`. The ratified draft state from which this v0.1 doc was promoted.
- **Hivemind operating guide** — `docs/HIVEMIND_GUIDE.md` (§13 Five Invariants, §15 What Hivemind Is Not).
- **Governance implementation** — `torment_service/governance.py` (resolver, flag enforcement, FILTER-A helper).
- **FILTER-A design** — `docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md` (surface model, doctrine).
- **Character layer** — `torment_service/character.py` (seed, basin, drift, gravity correction). Track A §3.2 names the Voice axis fields here.
- **MCP capability boundary** — `docs/MCP_CAPABILITY_BOUNDARY.md` (inbound only; tool_result_ingest semantics).
- **Brainstorm closure** — `brainstorming/memory_roadmap_2026_05_09/99_session_summary.md` (8 framing-doc sentences, best-promotion-candidate list).
- **Brainstorm Cluster 2 source** — `brainstorming/memory_roadmap_2026_05_09/03_track_B_agent_authored_memory.md`.

---

## 16. Ratified decisions and revision history

The items below were open questions or revisions resolved during the path to v0.1. Each is recorded for traceability.

### 16.1 Resolved by GPT's 2026-05-18 second-read (v0.2 → v0.2.1)

1. **Three-axis spine** — KEPT. *Which mind / which lane / what authority* is the doc's structural spine.
2. **"Memory lane" naming** — KEPT. *Lane* is the right term; doesn't collide with existing TORMENT terms (domain, surface, tier, provenance).
3. **Multi-dimensional authority (v0.2.1)** — SUPERSEDED by §16.2 revision below. v0.2.1 had five dimensions; v0.1 has three sub-dimensions per §16.2.
4. **§10.5 character-authority default** — ACCEPTED. Roleplay-continuity events default to released-from-agent-scope.
5. **§11.3 MCP defaults** — ACCEPTED and expanded by §16.2 below.
6. **§12 agent-side refusal** — SUPERSEDED by §16.2 below. v0.2.1 kept it as candidate gap; v0.1 ratifies as doctrinal primitive.
7. **§13 Item 4 (cannot self-extend budget)** — FLAGGED. Keep as future automation gap.
8. **Doc length** — KEPT as-is.

### 16.2 Resolved by trio review of v0.2.1 + audit (v0.2.1 → v0.2.2, 2026-05-19)

The eight revisions applied in v0.2.2 (which v0.1 inherits):

1. **§3 / §7 collision** — RESOLVED. §3 keeps three top-level Cluster 2 axes (Scope / Lane / Authority). §7 decomposes Authority into three sub-dimensions only (Authority class / Lifecycle / Promotion rights). Scope, Lane, and Provenance removed from Authority's sub-dimension list.
2. **Track A reconciliation** — RESOLVED. New §3.1 and §7.0. Cluster 2 decomposes only Track A's Authority axis. Mode/Voice/Certainty remain Track A axes that Authority consults.
3. **Three-modifier model** — ADOPTED. New §7.4. (authority class, lifecycle modifier, origin modifier) is the practical shorthand for memory description. §6 lane catalog cleaned of authority/lifecycle conflations.
4. **§11.3 `tool_result` row** — UPGRADED. Full row including write_path, Track A Certainty cross-ref, lifecycle (existing 7d cap), voice constraint.
5. **Disagreement primitive** — PROMOTED. §12 reframed from "candidate gap" to "doctrinal primitive, runtime deferred." Option i-plus: no Track A amendment proposed.
6. **Front-matter posture** — ADDED. Doctrine-only with named runtime seam stated as load-bearing scope discipline.
7. **Track A cross-references** — ADDED throughout (§§3, 5, 6, 7, 8, 10, 11, 12).
8. **`MEMORY_DIGESTION_DOCTRINE` reference** — HANDLED. Inlined the released-memory primitive in §7.1 (and §6.1); reference dropped since the source doc is gitignored.

### 16.3 Resolved at v0.1 promotion (v0.2.2 → v0.1, 2026-05-19)

The two trio decisions made at the promotion checkpoint:

1. **`released` vs. `low-authority`** — UNIFIED for v0.1. Treated as the same authority class with different emphasis: `low-authority` foregrounds retrieval-weight reduction, `released` foregrounds identity-protection guarantee. A future revision may split them into distinct values; deferred to v0.3 (§17). Splitting now would add complexity without runtime enforcement.
2. **`ratified` as lifecycle value** — ACCEPTED for v0.1. Event-anchored rather than continuous-property, but still answers the lifecycle question "why does this memory survive stably?" Optional future rename to `ratification-anchored` for clarity; deferred to v0.3. Not a promotion blocker.

These two decisions, combined with the eight revisions in §16.2, complete the path from v0.2.1 → v0.1.

---

## 17. Remaining open for v0.2 or v0.3 or later

Work items deferred past Cluster 2 v0.1. Not blockers for this doctrine.

- **Per-tool-family MCP defaults.** Currently one default for all tool families. May warrant differentiation (`code_exec` vs `web_search` vs `clock_probe`).
- **Sixth authority sub-dimension** if one surfaces during implementation prep. Current decomposition is three.
- **Implementation design for §12 agent-side refusal.** Pipeline-pause mechanism, Track A dependency, character-layer interaction. Owned by Track B's eventual specialization or Cluster 2 v0.2.
- **Online-runtime external-bound rule** (§13 Item 4). The analog of Cluster 4's offline external-bound rule for the online runtime.
- **Cluster 2 v0.2 — runtime Authority Gate.** The runtime enforcement mechanism the doctrine-only posture explicitly defers. Separate framing-doc effort.
- **Track A v0.2 amendments** — only if a future trio decides to formalize the Option i-plus seam in Track A §8.2. Not authorized by Cluster 2 v0.1.
- **Cluster 5 storage framing-doc promotion** — separate work item, requires storage-code reality check first.
- **Voice Test v0.2 / Phase 4a** — runs in parallel; does not depend on Cluster 2 promotion. Anchors on Track A v0.1 §11 #7.
- **`released` vs. `low-authority` split** — currently unified per §16.3 #1; reconsider in a later revision.
- **`ratified` lifecycle rename** — optional rename to `ratification-anchored` per §16.3 #2; reconsider in a later revision.

---

## 18. Status

**Cluster 2 v0.1 — Advisory doctrine, ratified by trio (pzychozen + GPT + Claude) on 2026-05-19. No implementation authorized by this document. No code changes. No schema migrations. No tests authorized. Track A v0.1 not amended.**

Subsequent versions (v0.2, v1.0) require their own trio ratification before they supersede this one. The runtime Authority Gate, when designed, becomes a separate framing-doc effort (Cluster 2 v0.2 or a parallel implementation track).

---

## 19. What Cluster 2 v0.1 does and does not include

Cluster 2 v0.1 is a doctrine doc, not an implementation. It declares the Authority Gate vocabulary, decomposes Track A's Authority axis into three sub-dimensions, names two structural axes (Scope and Lane) Track A does not directly cover, ratifies three doctrinal defaults (character-authority §10.5, MCP tool_result §11.3, disagreement primitive §12), and names the seams to other tracks. It explicitly does NOT:

- Modify any code in `torment_service/`, `tests/`, `start/`, or anywhere else.
- Amend Track A v0.1 in any section. Track A's §8.2 seam to Track B remains intact.
- Add any `ProvenanceV1` field. Cluster 2 v0.1 introduces no new fields, flags, or enums; it names what already exists.
- Implement a runtime Authority Gate. That is Cluster 2 v0.2 (or a parallel implementation track).
- Implement the agent-side disagreement runtime mechanism. That is deferred per §12.5.
- Implement per-tool-family MCP defaults. Deferred to v0.3 per §11.7.
- Authorize automation extensions, schedulers, offline reflection, hivemind enabling changes, compression changes, writeback changes, or expanded MCP outbound.
- Modify `.gitignore`, FILTER-A, the governance flag set, or any existing TORMENT mechanism.

This document IS the Cluster 2 v0.1 advisory doctrine. Subsequent versions require their own trio ratification before they supersede this one.

---

*End of Cluster 2 v0.1. Advisory doctrine, ratified by trio (pzychozen + GPT + Claude) on 2026-05-19. No further tracks promoted by this document. No implementation authorized by this document.*
