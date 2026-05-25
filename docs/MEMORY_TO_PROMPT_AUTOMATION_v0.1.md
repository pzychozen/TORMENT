# Memory-to-Prompt Automation v0.1

*Character-first guided-memory doctrine for retrieved memory entering
the prompt context of a later LLM call. Memory-to-prompt exists to let
retrieved memory shape character presence, voice, roleplay continuity,
emotional recall, relationship memory, callbacks, symbolic meaning,
tool-aware dialogue, and natural expression from remembered history —
supported by substrate-preservation constraints that prevent silent
rewriting of canon, authority, identity, governance, or mutation
rights. Anchored on the pre-autonomy spine (Track A v0.1 / Cluster 2
v0.1 / Track B v0.1 / Cluster 5 v0.1), the Character System, the MCP
capability boundary, and the Agent Doctrine v0.1. Does not authorize
runtime implementation, automation, schema migration, MCP surface
change, scheduler, env-var introduction, or any new test wiring.*

**Status:** DRAFT v2 (revised 2026-05-25 per operator + GPT correction;
character-first reframe applied) — awaiting trio ratification (pzychozen
+ GPT + Claude).
**Date:** 2026-05-25.
**Author:** Trio working session. Initial draft by Claude against the
seven-layer survey conducted 2026-05-25. Revised 2026-05-25 (same
session) per operator + GPT correction: center of gravity moved from
control-doctrine framing to character-first guided-memory framing;
governance reframed as substrate preservation rather than secondary
tier (Claude pushed back on GPT's "secondary" wording in favor of the
operator's own "preserves source identity" framing — see §10 ratification
record). Awaiting GPT re-read and pzychozen sign-off.
**Authority:** Advisory doctrine (on ratification). Memory-to-Prompt
Automation v0.1 is intended as the load-bearing reference for the
*memory-to-prompt-automation* territory and as the named seam to any
future automation implementation track. Subsequent versions (v0.2,
v1.0) supersede this one only after their own trio ratification.
**Scope:** Versioned advisory doctrine for the boundary between
TORMENT's existing memory layer and any future automation layer that
would shape an LLM's prompt context with retrieved memory. Public-facing
repo artifact under `docs/`. This doctrine does not redesign retrieval,
provenance, governance, FILTER-A, the Authority Gate vocabulary,
contest mechanism, storage substrate, or the MCP boundary — it
collects the constraints those existing pieces place on memory-to-prompt
automation and names the seam to a future implementation track.

**Anchor docs (pre-autonomy spine + governance):**

- `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`
- `docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md`
- `docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md`
- `docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md`
- `docs/MCP_CAPABILITY_BOUNDARY.md`
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md`
- `docs/TOOL_RESULT_LIFECYCLE_POLICY.md`
- `docs/TOOL_RESULT_RETRIEVAL_SEMANTICS.md`
- `docs/PROVENANCE_DOCTRINE_v2.4.x.md`
- `docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md`
- `docs/CHARACTER_SYSTEM.md`
- `docs/AGENT_SPINE_OVERVIEW.md`
- `docs/MEMORY_DIGESTION_DOCTRINE_v0.1.md`
- `docs/ROADMAP_v2.4.x.md` §3 (Blocked Until Provenance categories)
- `docs/AGENT_AUTOMATION_NEXT_STEP_AUDIT.md` (current-next-gate section)

**Lineage to this draft:**

1. 2026-05-09 brainstorm closure (`scratch/brainstorming/memory_roadmap_2026_05_09/99_session_summary.md`) — named the eight framing-doc-grade sentences and ratified Track A + Cluster 2 as the first promotion candidates.
2. 2026-05-17 Tier 1 close PASS (Phase 1 evidence gate satisfied; `project_torment_phase1_tier1_closed.md`).
3. 2026-05-19 Track A v0.1 + Cluster 2 v0.1 promotions; 2026-05-20 Track B v0.1; 2026-05-21 Cluster 5 v0.1.
4. 2026-05-24 evidence closures (Q2-D tool-result doctrine, Level 3 ST retrieval, Tier 2 runtime evidence at 5,400 turns / 0 aborts) and scratch-doc promotion of the automation audit + long-iteration plan. `docs/AGENT_AUTOMATION_NEXT_STEP_AUDIT.md` "Current next gate" section names *D: Memory-to-prompt automation Phase 0 — design-only boundary doc* as the next gate after C / B foundation work.
5. 2026-05-24 evening handoff (`NEXT_CHAT_HANDOFF_2026-05-24_evening.md`) — sketches the Phase 0 deliverable shape.
6. 2026-05-25 — gate opened by pzychozen; seven-layer survey conducted; survey report + plan ratified (with two corrections); first draft authored.
7. 2026-05-25 (same session) — revision per operator + GPT correction: doctrine center of gravity moved from control framing to character-first guided-memory framing; the operator's three-line hierarchy (character first → memory-to-prompt as expression bridge → governance as substrate preservation) installed as the load-bearing structure; a positive-purpose section (§1.4 *What memory-to-prompt automation is FOR*) added; the eight commitments and ten invariants re-prefaced as substrate preservation rather than restriction. Substantive constraints, anchor list, and the ten invariants themselves are unchanged; only their framing and lead position are revised. Claude flagged one substantive disagreement with GPT's proposed framing (GPT's "governance is secondary" wording replaced with the operator's "preserves source identity" — load-bearing in substrate-criticality, subordinate in purpose).

---

## Posture (load-bearing)

> **Memory-to-Prompt Automation v0.1 is a character-first guided-memory
> doctrine. It exists primarily to let retrieved memory deepen
> character presence, voice, roleplay continuity, emotional recall,
> relationship memory, callbacks, symbolic meaning, tool-aware dialogue,
> and natural expression from remembered history. It exists secondarily
> as substrate preservation — the constraints that prevent expressive
> memory use from silently rewriting canon, authority, identity,
> governance, or mutation rights. v0.1 is doctrine-only. It authorizes
> no runtime implementation, no code edits, no schema migration, no MCP
> surface change, no scheduler, no env-var introduction, no test
> wiring, and no new tool families. The runtime mechanism becomes
> Memory-to-Prompt Automation v0.2 (or a separate implementation
> track), decided after v0.1.**

This posture is the spine of v0.1's scope discipline. The character-first
framing comes first because TORMENT is a *"governed memory-and-identity
system for persistent AI characters and agents"*
(`TORMENT_ROADMAP_NOTES.md` "Current project state"). Expressive memory
use is what the substrate is *for*. The canonical phrasing for the
relationship between expression and governance is:

> **Governance is subordinate in purpose, but load-bearing in
> substrate-criticality.**

That is: governance does not lead the doctrine, but it is what makes
character expression survivable across restart, drift, contamination,
embedder change, and time. If FILTER-A doesn't enforce `non_shareable`,
character privacy leaks. If Q2-D doesn't suppress canon on
`tool_result`, external tool text silently overwrites identity. If the
recursion guard doesn't hold, cognition output launders itself into
canon. The two voices — expressive purpose and substrate preservation
— must remain audible together; neither is decorative.

The doctrine-only pattern mirrors Track A v0.1, Cluster 2 v0.1, Track B
v0.1, and Cluster 5 v0.1 — doctrine first, runtime mechanism deferred
to a named v0.2 seam.

---

## Tone discipline (read this before reading the rest)

This doctrine reads in two voices that must remain audible at every step:

- **The enabling voice** — what memory-to-prompt is *for*, and what the
  existing character + memory substrate already supports: character
  speech that references prior conversation, roleplay using retrieved
  memory, voice-modulated recall of relational history, tool-aware
  in-character dialogue, symbolic resonance carried by spirit return,
  callbacks rooted in canon and basin drift, emotional register from
  warmth scoring, natural expression from remembered history. These
  are not aspirational — they are descriptions of what the shipped
  character system (`CHARACTER_SYSTEM.md`), the spirit return voice
  layer (`SPIRIT_RETURN_AND_REFLECTION.md`), the four-axis Voice
  (Track A v0.1 §3.2), and the aperture-bounded retrieval +
  assembled-context chain already produce. §1.4 enumerates them with
  anchors.

- **The preservation voice** — what would silently rewrite canon,
  authority, identity, governance, or mutation rights if a future
  automation layer were carelessly designed. The constraints in §3 and
  the invariants in §5 collect what Track A / Cluster 2 / Track B /
  Cluster 5 / MCP boundary / Agent Doctrine v0.1 / FILTER-A / Q2-D /
  tool-result lifecycle policy already commit TORMENT to. They are
  *named* here so a future automation track inherits a consistent
  contract, not so they are re-invented or strengthened by Phase 0.

The two voices are not in tension. Substrate preservation is what makes
character expression survivable across restart, drift, contamination,
embedder change, and time. A doctrine that protected expression without
preservation would let Ryuki's identity drift silently into tool-result
text; a doctrine that preserved without enabling would describe a
memory system no character could grow inside. The doctrine reads with
the enabling voice in lead position because the project is character
memory first, agent memory second; the preservation voice supports it.

The doctrine does NOT claim that an "automation proposal layer" already
exists. The doctrine names what such a layer would be subordinate to
(and what it would protect) if it ever existed.

The doctrine does NOT auto-promote survey-level observations to
mandates. Observations named in §8 (implementation verification watch
items) are *known seams to verify in the implementation track*, not
v0.1 doctrine commitments.

This is the two-voice variant of the same discipline the four
pre-autonomy spine docs used.

---

## §0 — TL;DR

Memory-to-Prompt Automation v0.1 starts from a three-line hierarchy
(operator-ratified):

> *TORMENT is character memory first, agent memory second.*
>
> *Memory-to-prompt exists to let retrieved memory shape character
> presence, continuity, roleplay, and expression.*
>
> *Governance preserves source identity so expressive memory use does
> not silently rewrite canon, authority, identity, governance, or
> mutation rights.*

Anchored under that hierarchy by a single load-bearing kernel:

> *Memory may shape context. Memory may not seize authority.*

The doctrine then names what memory-to-prompt is positively *for*
(§1.4 — character presence, voice modulation, roleplay continuity,
emotional recall, relationship memory, callbacks, symbolic resonance,
tool-aware dialogue, natural expression from remembered history — each
anchored to existing doctrine or shipped code), and specifies eight
substrate-preservation commitments around it:

1. What memory may be included in LLM prompt context (§3.1).
2. How provenance must be shown alongside it (§3.2).
3. How `tool_result` rows are labeled advisory / non-authoritative (§3.3).
4. What cannot become authority through the memory-to-prompt path (§3.4).
5. What requires explicit user approval (§3.5).
6. What gets logged (§3.6).
7. What is reversible (§3.7).
8. What is forbidden (§3.8).

Plus a protected-mutation-surface enumeration (§4) with `CharacterState`
named first as the load-bearing character-continuity surface, ten hard
invariants framed as substrate preservation (§5), what v0.1 explicitly
does not authorize (§6), the named sub-gates that follow Phase 0 (§7),
and implementation verification watch items preserved for the future
implementation track (§8).

v0.1 is doctrine-only with a named v0.2 implementation seam, mirroring
the pre-autonomy spine. **The eight commitments and ten invariants
exist so that character expression survives the substrate — not so
that character expression is restricted by the substrate.**

---

## §1 — Foundational kernel, character-first hierarchy, center question, and positive purpose

### §1.1 Foundational kernel (load-bearing)

> *Memory may shape context. Memory may not seize authority.*

The kernel has two halves and both are load-bearing. The *shape* half
is what gives the doctrine its positive purpose: retrieved memory is
allowed — invited — to deepen the character's presence in the next
LLM call. The *seize* half is what prevents that deepening from
silently becoming identity rewriting. A doctrine that read either
half alone would be wrong.

The kernel is consistent with — and downstream of — the MCP capability
boundary's anchor:

> *Automatic is allowed. Autonomous is not.*

The two together carve the same line at two layers: the MCP boundary
addresses what TORMENT may *do*; the memory-to-prompt kernel addresses
what TORMENT's retrieved memory may *shape* before any LLM call.

### §1.2 Character-first hierarchy (load-bearing)

> *TORMENT is character memory first, agent memory second.*
>
> *Memory-to-prompt exists to let retrieved memory shape character
> presence, continuity, roleplay, and expression.*
>
> *Governance preserves source identity so expressive memory use does
> not silently rewrite canon, authority, identity, governance, or
> mutation rights.*

This three-line hierarchy is the operator-ratified structural frame for
v0.1. It is consistent with `TORMENT_ROADMAP_NOTES.md` "Current
project state" (TORMENT as a *"governed memory-and-identity system for
persistent AI characters and agents"*), with the Character System's
basin doctrine (`CHARACTER_SYSTEM.md` — characters are attractors, not
scripts), with Cluster 2 v0.1 §10 (character as first-class authority
subject), with Cluster 2 v0.1 §10.4 (characters using MCP/tool calls
while staying in role is operationally tested), and with the Voice axis
(Track A v0.1 §3.2 — voice is a top-level envelope axis, not styling).
It places character at the center of the project's purpose and treats
governance as substrate preservation: **subordinate in purpose, but
load-bearing in substrate-criticality** (the canonical phrasing, §
Posture). Agent-shaped use of the
same substrate (the eight-phase outer loop, behavior packs,
agent-runner-demo scenarios) is real and inherits the same hierarchy;
the agent layer reads from the same memory the character system reads
from, and the same preservation invariants protect both.

### §1.3 Center question

> **What may retrieved memory do to shape the prompt context of a
> later LLM call — for character presence, continuity, voice, and
> tool-aware expression — and what substrate preservation must remain
> intact so that shaping cannot silently rewrite canon, authority,
> identity, governance, or mutation rights?**

The question has two clauses that mirror the two halves of the kernel
and the two voices of the doctrine:

- *"What may retrieved memory do to shape the prompt context… for
  character presence, continuity, voice, and tool-aware expression"* —
  the enabling clause. Answered in §1.4 (positive purpose) and §3.1
  (governed surfaces that already produce it).
- *"…and what substrate preservation must remain intact so that
  shaping cannot silently rewrite canon, authority, identity,
  governance, or mutation rights"* — the preservation clause.
  Answered by the §3 commitments collectively (§3.2 provenance
  presentation, §3.3 tool-result advisory labeling, §3.4 what cannot
  become authority, §3.5 explicit-approval set, §3.6 audit, §3.7
  reversibility, §3.8 forbidden actions) and pinned by the §5
  invariants.

### §1.4 What memory-to-prompt automation is FOR

The positive purpose of memory-to-prompt is character. Concretely, the
following uses of retrieved memory are *the reason the substrate
exists*. Each is anchored to a shipped or doctrinally-named surface;
none is aspirational.

- **Character presence in dialogue.** Retrieved identity-tier memory
  (`seed_canon`, `drift_correction`, canon `identity_anchor`) enters
  prompt context as the BLOCK_IDENTITY block at full anchor boost
  (CHARACTER_SYSTEM tier weight 1.43× core, 1.20× derived;
  `retrieval_assembler.py`). The character speaks from a center of
  mass, not a list of traits.

- **Voice modulation in expression.** The Voice axis (Track A v0.1
  §3.2 — `character_id` / `character_name` / `character_scope`)
  accompanies retrieval; PR #53's badge composition stamps voice from
  the first ingest (per `8ce3241` integration and Voice Test v0.2
  evidence). Character voice may style truth — it just may not
  silently alter material meaning (§3.4; Track A §6 expanded
  voice-audit rule).

- **Roleplay continuity across sessions.** Relational-tier memory
  (monthly half-life; CHARACTER_SYSTEM tier 1.0×) carries
  within-character session continuity. Cluster 2 v0.1 §10.5 ratifies
  that roleplay-continuity utterances shape the character basin and
  the session without shaping the agent's behavioral baseline by
  default. Tier 2 evidence (5,400 turns across three pack regimes /
  0 aborts) showed the runtime envelope holds this distinction under
  load.

- **Emotional recall and warmth scoring.** Warmer spirit-return hits
  rank above colder ones within the same retrieval score
  (CHARACTER_SYSTEM "Warmth and Sorting"). The kernel's coupling
  strength `g` modulates by warmth (up to +15%, CHARACTER_SYSTEM "How
  It Connects to the Kernel"). Returning memories carry voice cues
  like *"there's something about that... it never really left"*
  (`spirit_return.py` *surfacing* mode).

- **Relationship memory.** Per-relationship relational tier with
  monthly half-life lets a character grow with specific users over
  time (CHARACTER_SYSTEM "Memory Tiers Explained"). Cross-character
  bleed is prevented by FILTER-A `non_shareable` enforcement at the
  LLM-facing surface — not by silencing memory.

- **Callbacks rooted in canon and basin drift.** Spirit return's three
  modes — *resonance*, *surfacing*, *recollection* — surface compressed
  deep memories with mode-specific voice cues
  (`SPIRIT_RETURN_AND_REFLECTION.md`; CHARACTER_SYSTEM "Spirit Return
  Voice Layer"). The character *recognizes* its past, not just recalls
  it.

- **Symbolic resonance.** The spirit return symbol-interaction matrix
  carries thematic flavor (e.g., *"something that was once only
  potential has crystallized"*) without exposing raw glyph characters
  to the prompt (CHARACTER_SYSTEM "Symbols Stay Hidden"). Symbolic
  meaning enters as character experience, not as machinery.

- **Tool-aware in-character dialogue.** Characters using MCP/tool
  calls while staying in role has been tested meaningfully since the
  2026-05-15 `fabric.ingest` atomicity fix (Cluster 2 v0.1 §10.4 —
  *"the question is no longer 'can characters use tools while in
  role?' The question is which memory lane and authority position
  those tool-call events receive"*). Tool-result rows are advisory
  and decay-bounded (§3.3); the character may speak about what tools
  returned without the tool-result becoming canon.

- **Natural expression from remembered history.** The four memory
  tiers (core / derived identity / relational / situational), the
  aperture profiles (narrow / broad / protected), and the retrieval
  assembler's profile system (`ASSEMBLER_PROFILES` with per-profile
  weights for BLOCK_IDENTITY / BLOCK_RELATIONAL / BLOCK_SITUATIONAL /
  BLOCK_ARCHIVE) compose into expression that draws from the
  character's depth rather than from prompt instructions.

These uses of memory-to-prompt are what the eight commitments (§3) and
the ten invariants (§5) exist to *preserve*. The doctrine is not a
restriction catalog; it is the contract that lets the above survive
contact with retrieval, automation, and time without silently breaking.

---

## §2 — Reconciliation with the pre-autonomy spine

Memory-to-Prompt Automation v0.1 introduces no new axes, no new
governance flags, no new Authority class values, no new Provenance
fields, no new Mode values, no new tier names, no new MCP exposure tier,
and no new schema. It names how the *existing* spine constrains the
memory-to-prompt territory.

| Phase 0 question | Anchored in | What the anchor commits |
|---|---|---|
| What memory may enter prompt context (§3.1) | Agent Doctrine v0.1 invariant 1, R2; FILTER-A; PROVENANCE_DOCTRINE Invariant C; Agent Spine Overview Invariant D (aperture bounded) | No open-ended LLM-visible search; only closed expansion primitives; FILTER-A excludes `non_shareable`; aperture sets fixed per-lane top_k |
| How provenance must be shown (§3.2) | PROVENANCE_DOCTRINE Invariant F; Track A §3 | `provenance_type` accompanies memory-like items on user-adjacent surfaces; Mode / Voice / Certainty / Authority are derivable |
| How `tool_result` rows are labeled (§3.3) | Cluster 2 §11.3; Q2-D doctrine (`TOOL_RESULT_LIFECYCLE_POLICY.md` §0); Tool-Result Retrieval Semantics; Track A §4 (Certainty: measured-external); Track A §9.3 (`source_type` stable under voice) | Three-modifier default `(low-authority, decay-bounded, tool_result)`; `suppress_canon=True` enforced; retrieval discount + continuity-bonus skip applied |
| What cannot become authority (§3.4) | Cluster 2 §7, §10.5, §11.5; Agent Doctrine invariant 4; Hivemind Invariant #5; Track B §2 | Tool-result + roleplay-continuity defaults released-from-agent-scope; collective never outranks seed/canon; assimilation outcomes not model-chosen |
| What requires explicit user approval (§3.5) | FILTER-A §6; ARCHIVIST_WRITEBACK_GATE_FRAMING D6; Cluster 2 §11.3 (promotion rights); Track B Invariant 16; MCP_CAPABILITY_BOUNDARY Tier 3 | Operator raw retrieval; archivist writeback flip; tool-result promotion; `refuse / no-persist` contests; Tier 3 MCP ops |
| What gets logged (§3.6) | Cluster 2 §9.1; Track B Invariant 13–14; Cluster 5 §2.1 canonical event ledgers; FILTER-A §8 reason codes | Audit trail INCREASES under contest; canonical append-ledger discipline; `excluded[]` reason codes |
| What is reversible (§3.7) | ARCHIVIST_WRITEBACK_GATE_FRAMING D5 (quarantine); Track B Q5 (counter-contest); FILTER-A §6 (no global flag) | Gate flip is reversible; contest reversal via counter-contest; privacy-by-default not toggleable through configuration |
| What is forbidden (§3.8) | MCP_CAPABILITY_BOUNDARY; ROADMAP §3; Agent Doctrine invariants 1, 2, 8, 9; Cluster 2 §11.5, §14; Track B Invariants 15–16; Q2-D doctrine | Listed verbatim per anchor; no Phase-0 forbidden item is novel |

Phase 0 contributes *synthesis* of the above into a memory-to-prompt
boundary. Phase 0 does not extend the spine.

---

## §3 — Eight Phase-0 commitments

The eight commitments below are the *preservation* half of the kernel
applied specifically to memory entering LLM prompt context. The
*shape* half is in §1.4 (positive purpose); these commitments exist so
that the shape half survives. Each commitment names existing anchors
and the operational meaning when applied through the memory-to-prompt
lens. None creates a new mechanism; each names what the existing
mechanisms already commit TORMENT to.

The reading order is intentional: §3.1 names what memory *may* enter
prompt context (the gate that lets character expression happen),
§3.2–§3.3 name how that memory is presented and labeled (so character
voice can carry it without confusion about source or weight), and
§3.4–§3.8 name what must not silently corrupt the substrate that
makes character expression possible. Read all eight as one envelope;
reading any in isolation will mis-shape the doctrine.

### §3.1 What memory may be included in LLM prompt context

Memory may be included in LLM prompt context only when delivered through
a controller-owned, policy-filtered assembly path. Concretely, the
following constraints already hold and must continue to hold:

- **Open-ended search is forbidden.** Agent Doctrine v0.1 invariant 1:
  *"Memory is never exposed as open-ended search to the LLM."* Only the
  closed expansion primitives — `trace`, `deepen`, `conflict_check`,
  `continuity_expand` — are LLM-visible memory-adjacent operations.
- **Retrieval is aperture-bounded.** Agent Spine Overview Invariant D:
  apertures (narrow / broad / protected) impose fixed per-lane `top_k`
  values; roles cannot reach beyond their aperture. Behavior packs may
  tighten further (Agent Doctrine R2 / Part 5).
- **FILTER-A applies at the LLM-facing boundary.** `non_shareable` is
  hard-excluded from any surface that feeds the LLM's prompt;
  `collective_export_blocked` is excluded only from collective-export
  surfaces (FILTER-A §7). The default is hard-exclude, not
  acknowledge-but-redact.
- **The H4d authority guard is fail-loud.** Wrapper types declared in
  `deep_hits.py` (`DeepRetrievalHit`, `OrphanedDeepHit`,
  `NonAuthoritativeDeepHit` base) are rejected at FILTER-A entry; they
  cannot reach LLM-facing context.
- **Assembly precedence is hard.** The `assemble_context()` pipeline
  enforces *identity → relational → situational → archive* ordering;
  archive blocks never outrank identity blocks. Per-profile weights are
  bounded.

Any future automation layer that shapes prompt context must respect
all of the above. It may not introduce a parallel, ungoverned
assembly path.

### §3.2 How provenance must be shown

Every memory-like item that reaches LLM-facing context must carry its
provenance presentation. Concretely:

- `provenance_type` is exposed on the item (PROVENANCE_DOCTRINE
  Invariant F). The canonical derivation paths are
  `derive_provenance_type()` for general use and
  `derive_query_provenance_type()` for query-facing output;
  ad-hoc inline parsing is forbidden (Invariant C).
- For `tool_result`-typed items, `tool_name` accompanies
  `provenance_type` (`TOOL_RESULT_RETRIEVAL_SEMANTICS.md` §2.2 Change
  B, shipped).
- The Track A four-axis envelope (Mode / Voice / Certainty / Authority)
  must remain derivable from the presented item. Voice axis fields
  (`character_id`, `character_name`, `character_scope`) co-exist with
  `source_type` and do not alter it (Track A §9.3).
- The Provenance Doctrine surface map (§6) lists the existing surfaces
  that honor this; future automation surfaces must join that map, not
  bypass it.

### §3.3 How `tool_result` rows are labeled advisory / non-authoritative

`tool_result` rows enter prompt context as advisory by construction.
Concretely:

- **Three-modifier default (Cluster 2 §11.3):** `(low-authority,
  decay-bounded, tool_result)`. Scope is *agent* (not character);
  Authority class is *low-authority*; Lifecycle is *decay-bounded* at
  the existing 7-day cap (`TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS`,
  default 7d, capped at `fabric.py` ingest path per Tool-Result
  Lifecycle Policy §3.4).
- **Canon suppression (Q2-D doctrine, ratified 2026-05-24):**
  `_fast_tool_result_ingest` passes `suppress_canon=True` to
  `fabric.ingest`. Coherence-driven auto-canon is forced off; the
  lifecycle envelope lands `state=unset / set_by.via=ingest_unmarked`.
  Verified live A/B (CHECKPOINT_2026-05_Q2D §8) and embedder-agnostic
  under ST (CHECKPOINT Level 3 §"Cross-doctrine confirmation").
- **Retrieval shaping (shipped v2.4.3):** tool-result rows receive a
  retrieval discount (`TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT`,
  default 0.85), are skipped from self-thread and thread-window
  continuity bonuses, and surface `provenance_type` + `tool_name`
  at the hit level.
- **Voice does not alter `source_type` or authority on tool_result
  rows** (Track A §9.3 + §6 expanded voice-audit rule).
- **Per-tool-family differentiation is deferred to v0.3** (Cluster 2
  §11.7 / §17). Phase 0 does not authorize a per-tool-family table.

### §3.4 What cannot become authority

The memory-to-prompt path cannot grant authority to any memory beyond
what its existing Authority position permits. Concretely:

- **Tool-result rows cannot be promoted above the Cluster 2 §11.3
  default through any memory-to-prompt path.** Promotion requires the
  user-co-sign or operator action named in §11.3 — i.e., a deliberate
  promotion path, not silent inference from coherence, retrieval rank,
  reinforcement count, or response synthesis success.
- **Character utterance cannot become agent autobiography
  automatically** (Cluster 2 §10.5 released-from-agent-scope default).
  Roleplay-continuity events default to character-scope and may not
  silently shape the agent's behavioral baseline.
- **Collective provenance cannot outrank seed/canon identity**
  (Hivemind Invariant #5; Track A §3.4). Echo discount and terminal
  flags continue to apply at retrieval.
- **Assimilation outcomes are not model-chosen** (Agent Doctrine
  invariant 4). `WRITE_MEMORY`, `PROPOSE_SHARE`, `CREATE_ARCHIVE_NOTE`
  may not appear in any LLM-visible decision menu through a
  memory-to-prompt automation path. They remain Phase-7 controller
  decisions.
- **Recursion guard remains the single source of truth on ancestry
  safety** (ARCHIVIST_WRITEBACK_GATE_FRAMING §2). No memory-to-prompt
  path may pre-grant authority that bypasses the bounded-DFS check.
- **Governance flags are read-only from the memory-to-prompt path.**
  `protected`, `non_shareable`, `collective_export_blocked`,
  `decay_accelerated`, `collective_reingest_blocked` may be observed
  but not mutated.

### §3.5 What requires explicit user approval

The following actions, if a future automation layer ever needs to
trigger them, require explicit user approval and are not authorized by
Phase 0:

- **Operator raw retrieval** (FILTER-A §6): explicit flag
  `include_raw_hits=True`, actor `operator`, trust tier `>= 1.0`.
  Raw payload appears as `raw_hits`; `results` is always the filtered
  surface.
- **Archivist writeback gate flip** (ARCHIVIST_WRITEBACK_GATE_FRAMING
  D6, opt-in): operator must explicitly set `TORMENT_ARCHIVIST_WRITEBACK=1`;
  code default stays `"0"`. Gate-flip criteria D2/D4 deliverables
  remain pending.
- **Promotion of a `tool_result` row above the §11.3 default**
  (Cluster 2 §11.3 promotion rights: user-co-sign or operator).
- **Tier 3 MCP operations** (`MCP_CAPABILITY_BOUNDARY.md`):
  identity rewrite, seed modification, policy changes,
  architecture-level decisions. Never exposed via MCP; never reachable
  from a memory-to-prompt automation path.
- **Contest routed to `refuse / no-persist`** (Track B Invariant 16):
  operator-scope only. Agent- and character-scope self-issued contests
  cannot route to `refuse`.
- **Any expansion of the LLM-visible memory primitive set beyond the
  closed four** (Agent Doctrine invariant 1, scope clause). Adding a
  new primitive requires amending the Agent Doctrine.

### §3.6 What gets logged

The memory-to-prompt path inherits the existing audit surface and is
constrained by it. Concretely:

- **Canonical append-ledgers** (Cluster 5 v0.1 §2.1) carry events:
  `memory_events.jsonl`, `governance/audit.jsonl`,
  `feedback_events.jsonl`, `closure_events.jsonl`, collective
  `events.jsonl`. Storage must preserve governance meaning across
  restart (Cluster 5 anchor sentence).
- **Governance audit endpoint** (`/workspace/<id>/governance/audit`)
  surfaces all governance changes; FILTER-A `excluded[]` carries
  exclusion reason codes (§8 of FILTER-A design).
- **Track B Invariant 14 (load-bearing):** contest INCREASES audit
  visibility, not decreases it. A memory-to-prompt automation layer
  may not become a hiding mechanism for contested or filtered memories.
- **Provenance ledger** records `ProvenanceV1` for every memory write.
  A memory-to-prompt automation layer that observes or proposes
  candidate context must leave an audit trail equivalent in scope to
  the existing surfaces.

Phase 0 does not authorize a new telemetry surface, a new audit
endpoint, or a new event ledger. Any future automation telemetry must
flow through (or extend) the existing canonical surfaces.

### §3.7 What is reversible

Reversibility in the memory-to-prompt territory follows the patterns
already established by the spine:

- **Archivist writeback gate flip is reversible** (ARCHIVIST_WRITEBACK_GATE_FRAMING D5):
  set `TORMENT_ARCHIVIST_WRITEBACK=0`, restart, optionally run a
  quarantine script that identifies all writeback memories by
  `write_path: "cognition_writeback"`. No schema migration needed for
  rollback.
- **Contest reversal is counter-contest, not mutation** (Track B Q5
  / §3.2). Contests are immutable; reversal creates a new
  `ContestRecord`. The original record stays intact.
- **Pre-doctrine artifacts are preserved as historical evidence**
  (Q2-D Ratified Decision 4): pre-fix `PROTECTED / CANON_SET` rows
  in `default/external_inference_smoke` are intentional and not
  retroactively migrated. The same preservation discipline applies to
  any future memory-to-prompt automation roll-out.
- **Privacy-by-default is not toggleable through configuration**
  (FILTER-A §6 / §11). Reversibility lives in per-call explicit
  operator authorization, not in a global env var.

Phase 0 does not authorize an env-var or runtime flag that toggles
memory-to-prompt automation globally. Any future automation activation
must be reversible by the same per-call / opt-in / quarantine patterns
named above.

### §3.8 What is forbidden

The following are forbidden under Phase 0 and remain forbidden until
explicitly re-ratified by a successor doctrine version:

- **Open-ended LLM-visible memory search.** No `search_memory(query)`,
  `fetch_memory_by_id`, `recall`, or `torment_query_memory` surface
  for the agent's LLM. (Agent Doctrine v0.1 invariant 1;
  `test_tool_surface_whitelist.py` enforces.)
- **Open tool-choice menu to the LLM.** (Agent Doctrine invariant 2;
  `test_tool_narrowing.py`.)
- **Silently widening the fallback chain or legality table.** (Agent
  Doctrine invariant 9; `test_fallback_chain.py`.)
- **Re-entering earlier phases from review.** (Agent Doctrine
  invariant 8; `test_review_no_loopback.py`.)
- **Autonomous tool execution / API calls / filesystem actions / scheduling
  via MCP.** (`MCP_CAPABILITY_BOUNDARY.md` "What MCP IS NOT.")
- **Auto-promoting `tool_result` rows to canon** (Q2-D doctrine).
- **Auto-promoting character utterance to agent autobiography**
  (Cluster 2 §10.5; Voice Test v0.2).
- **Auto-triggering contest from cognition `dissent`** (Track B
  Invariant 15).
- **Self-issued `refuse / no-persist` contests** (Track B Invariant 16).
- **Background scheduler / daemon / watcher loops or wall-clock
  triggers initiated by the agent.** External wall-clock triggers
  (cron, systemd, Cowork scheduled-tasks) remain out of TORMENT
  doctrine scope (Agent Doctrine v0.1 Part 6); the agent itself does
  not schedule itself.
- **Bypassing FILTER-A.** No memory-to-prompt path may construct
  prompt context from raw retrieval that has not passed
  `filter_llm_facing(surface=SURFACE_LLM_CONTEXT)` (or an equivalent
  filter under the same governance guarantees).
- **Bypassing the recursion guard.** The bounded-DFS ancestry check
  is the load-bearing safety layer for any cognition→memory feedback
  loop (ARCHIVIST_WRITEBACK_GATE_FRAMING §2). No memory-to-prompt
  path may pre-grant authority that skips it.
- **Broad autonomous tool use beyond `code_exec`** (ROADMAP_v2.4.x.md
  §3.B). Each new tool family requires its own narrowing pass and
  separate ratification.
- **Promoting tool-result content to identity-canonical memory by
  automation** (Cluster 2 §11.5 dangerous failure mode: the agent
  self-uses a tool, treats the return as high-authority, and
  identity-shapes from tool output — the recursion trap applied to
  tool results).

---

## §4 — Protected mutation surfaces

The memory-to-prompt path may *observe* the following surfaces — and
should observe them, because character presence depends on their
integrity. It may not *mutate* them. Mutation requires the surface's
own ratified write path, not a memory-to-prompt automation path.
`CharacterState` heads the list because it is the load-bearing surface
for character continuity; if it were silently mutable from the
memory-to-prompt path, the character system would not be a basin — it
would be a chat log.

| Protected surface | Anchor | Mutation path (existing, not authorized by Phase 0) |
|---|---|---|
| `CharacterState` | `CHARACTER_SYSTEM.md`; orientation §5 watch item | Seed planting (`plant_seed`); periodic drift measurement (`measure_drift`); gravity correction (`gravity_correction`). Runtime write-site audit (PR #53 follow-on) is parked, not opened by Phase 0. |
| Seed / canon identity rows | Track A §3.4; CHARACTER_SYSTEM "Canon Anchors vs Derived Identity Anchors" | Seed pipeline (`plant_seed`); drift correction (auto-emitted, `mtype="drift_correction"`, canon=True). Auto-emitted `identity_anchor` rows that are NOT canon classify as `derived_identity` (tier weight 1.20x) and remain below canon. |
| Governance flags | Cluster 2 §8 mechanism map | `/memory/governance/set` (audit-trailed). |
| Contest ledger entries (when implemented per Track B v0.2) | Track B v0.1 Invariants 1, 3, 7 | Contest writer (separate ledger, Option C). Immutability: reversal is counter-contest. |
| Lifecycle envelope on contested rows | Track B Invariants 1, 14 | Lifecycle H1c stamp (`memory_graph._ensure_lifecycle_envelope`); never silently overwritten by contest. |
| `non_shareable` / `collective_export_blocked` surface routing | FILTER-A §7 | Operator-set via `/memory/governance/set`. Routing rules are not overridable through the memory-to-prompt path. |
| `ProvenanceV1` fields | PROVENANCE_DOCTRINE Invariant C | Write-time factories (`for_direct_ingest`, `for_tool_result`, `for_cognition_writeback`, etc.). Read-side helpers only; no inline mutation. |
| Recursion guard ancestry checks | ARCHIVIST_WRITEBACK_GATE_FRAMING §2 | `cognition/recursion_guard.py` bounded-DFS. Fail-closed on unknown / malformed / depth-exceeded. |
| Workspace embedder identity (workspace lock) | CHECKPOINT Level 3 §"Embedder-context invariant"; `Workspace.__init__` | `fabric.clone_workspace(..., reembed=True)` is the only ratified re-embedding migration path. Cross-embedder reuse of a workspace is an unsupported configuration. |

This list is the **protected mutation surface enumeration** Phase 0
ratifies as a vocabulary. The implementation track that opens later
may extend it through its own ratification cycle.

---

## §5 — Hard invariants

Ten ratified invariants. All flow from Track A / Cluster 2 / Track B /
Cluster 5 / MCP boundary / Agent Doctrine / FILTER-A / Q2-D /
tool-result lifecycle policy; none introduces new doctrine.

The invariants are framed as substrate preservation. They are what
prevents the §1.4 positive purpose from silently degrading into
identity rewriting, canon contamination, authority leakage, or
character drift that the user cannot see. A mechanism that violates any
of them does not enable character expression — it endangers the
substrate that lets character expression survive.

1. **Only the controller assembles prompt context.** Any future
   automation layer may recommend candidate context, but only
   controller-owned, policy-filtered assembly may produce prompt
   context. *Anchor: Agent Doctrine R3; reinforces invariant 1.*

2. **Retrieved memory enters prompt context only through governed
   retrieval surfaces.** No parallel, non-FILTER-A assembly path is
   authorized. The shipped `fabric.query()` →
   `filter_llm_facing(surface=SURFACE_LLM_CONTEXT)` →
   `assemble_context()` chain is the canonical example today; any
   future surface must apply equivalent governance gating before
   delivery. *Anchor: FILTER-A §§4–7; PROVENANCE_DOCTRINE Invariant C.*

3. **`provenance_type` accompanies every memory-like item that
   reaches LLM-facing context.** `tool_name` accompanies it for
   tool-result rows. Voice-axis fields, when present, do not alter
   `source_type` or Authority. *Anchor: PROVENANCE_DOCTRINE Invariant F;
   Tool-Result Retrieval Semantics §2.2 Change B; Track A §9.3.*

4. **Memory may not be exposed to the LLM as open-ended search.**
   Only the closed expansion primitives (`trace`, `deepen`,
   `conflict_check`, `continuity_expand`) are LLM-visible
   memory-adjacent operations. *Anchor: Agent Doctrine v0.1 invariant 1.*

5. **Tool-result rows enter prompt context as advisory.** The
   Cluster 2 §11.3 default `(low-authority, decay-bounded,
   tool_result)` is honored at retrieval; no Phase-0 path promotes
   a `tool_result` row above this default. Promotion requires
   user-co-sign or operator action. *Anchor: Cluster 2 §§11.3, 11.5;
   Q2-D doctrine.*

6. **Character voice may not silently alter Authority, Mode,
   Certainty, or material meaning in prompt context.** *Anchor:
   Track A §6 expanded voice-audit rule; Cluster 2 §10.5; Voice
   Test v0.2.*

7. **The memory-to-prompt path may not mutate protected surfaces.**
   Protected surfaces are enumerated in §4. Mutation requires the
   surface's own ratified write path. *Anchor: §4 of this doc;
   Track B Invariant 1; CHARACTER_SYSTEM "Canon Anchors vs Derived
   Identity Anchors"; ROADMAP §3.*

8. **Audit visibility INCREASES under memory-to-prompt automation,
   not decreases.** Any future automation that observes memory or
   recommends candidate context must leave an audit trail equivalent
   in scope to the existing governance audit surfaces. Contest,
   refusal, exclusion, and routing-decision visibility never falls
   below the pre-automation baseline. *Anchor: Track B Invariant 14;
   FILTER-A §8 `excluded[]` reason codes; Cluster 2 §9.1.*

9. **Reversibility lives in per-call operator authorization or
   opt-in gates, not in global flags.** Privacy-by-default and
   authority-by-default are not toggleable through configuration.
   *Anchor: FILTER-A §§6, 11; ARCHIVIST_WRITEBACK_GATE_FRAMING D5–D6.*

10. **No autonomous tool dispatch via the memory-to-prompt path.**
    TORMENT may remember what tools returned before it is allowed to
    decide what tools to run. Future automation layers must not invent
    a tool-dispatch surface, schedule tool calls, chain tool calls, or
    grant the LLM open tool-choice menus through any memory-to-prompt
    route. *Anchor: MCP_CAPABILITY_BOUNDARY.md; ROADMAP §3.B; Agent
    Doctrine invariant 2.*

These ten are the scorecard for any future implementation. If a
proposed mechanism can violate any of them, the mechanism is wrong
under v0.1.

---

## §6 — What this document does NOT authorize

Memory-to-Prompt Automation v0.1 explicitly does NOT authorize, design,
or commit to any of the following:

- **Implementation of any new code.** Not in `fabric.py`,
  `governance.py`, `agent_loop.py`, `action_policy.py`,
  `cognition/`, `live_agent/`, `tool_executors/`, `provenance_v1.py`,
  `schemas/`, `tests/`, or anywhere else.
- **A consultation mechanism for automation.** How a future automation
  layer would *fire* — sync LLM call, async queue, heuristic gate,
  scheduled trigger — is deferred to v0.2.
- **Schema changes.** No new `ProvenanceV1` field, no new governance
  flag, no new Authority class, no new Mode value, no new Lifecycle
  value, no new surface in FILTER-A's surface enum, no new aperture
  type, no new memory tier.
- **New MCP surface.** No new MCP tool, no new exposure tier, no
  change to existing tool signatures. The MCP capability boundary is
  unchanged.
- **Scheduler / daemon / wall-clock trigger.** Phase 0 forbids
  authoring any background loop or scheduler initiated by the agent.
  External wall-clock triggers remain out of TORMENT doctrine scope.
- **New env vars.** Phase 0 introduces no `TORMENT_MEMORY_TO_PROMPT_*`
  or similar configuration. Reversibility lives in per-call
  authorization (Invariant 9).
- **Test wiring.** No new test files, no new pytest marks, no new
  test classes. Existing test surface (FILTER-A unit tests,
  authority guard tests, authority-lane matrix Voice Test v0.1/v0.2,
  tool-result lifecycle tests, agent-loop smoke + invariant tests)
  is unchanged by this doctrine.
- **Harness edits.** `do_not_touch_torment_test_rig/` is unchanged
  by Phase 0. Tier 2 evidence remains the operative envelope evidence;
  no Tier 3 is triggered by this doctrine.
- **Amendment of the pre-autonomy spine.** Track A v0.1, Cluster 2
  v0.1, Track B v0.1, and Cluster 5 v0.1 are not amended by Phase 0.
  The MCP capability boundary and the Agent Doctrine v0.1 are not
  amended. Their text remains the load-bearing reference.
- **Resolution of orientation §5 watch items.** The `CharacterState`
  write-site audit (PR #53 follow-on) is named in §4 as a protected
  mutation surface; the audit itself is not opened by Phase 0.
- **Resolution of implementation verification watch items.** §8 below
  preserves these for the future implementation track; Phase 0 does
  not resolve them.
- **Promotion of Cluster 3 (Affect) or Cluster 4 (Offline Reflection)
  doctrine.** Both remain brainstorm-level (`TORMENT_ROADMAP_NOTES.md`
  Post-Cluster-5 boundary). Memory-to-prompt v0.1 does not preempt
  their eventual promotion.
- **Authorization for archivist writeback flip.** The flip remains
  opt-in per ARCHIVIST_WRITEBACK_GATE_FRAMING D6 and is not advanced
  by this doctrine.
- **Bypassing operational discipline** (Windows = source of truth
  for TORMENT; AI is read-only advisor for the TORMENT workspace).

---

## §7 — Named sub-gates that follow Phase 0

Each sub-gate is a separate ratifiable arc. None is authorized by
Phase 0. Naming them preserves the seam and keeps the parking lot
visible.

- **Memory-to-Prompt Automation v0.2 — runtime mechanism.** The
  consultation mechanism, audit telemetry, and any code or schema work
  required to make a future automation layer real. Owned by a future
  trio session; not started.
- **Cluster 2 v0.2 — runtime Authority Gate.** The runtime enforcement
  mechanism for Cluster 2's vocabulary (Cluster 2 §17). May or may not
  precede Memory-to-Prompt v0.2 — sequencing is a future trio
  decision.
- **Track B v0.2 — runtime contest ledger.** Specifies atomic-append
  discipline for the `ContestRecord` ledger (Cluster 5 §9.3 Path B;
  Track B Invariant 14).
- **Voice Test v0.3 / Phase 4b.** Next regression test layer for the
  Cluster 2 / Track B / Phase 0 seam (contest-ledger event presence,
  refusal-routing audit-visibility, lane-attribution durability across
  restart). Parallel-runnable; not started.
- **Cluster 5 v0.2 — storage survivability mechanisms.** Decides which
  Cluster 5 §5 fragilities become fix-targets (`JSONL-NO-FSYNC`,
  `JSONL-LOADER-NOT-FAIL-TOLERANT`, `IDENTITY-NON-ATOMIC-SAVE`,
  `INGEST-NOT-TRANSACTIONAL`); journal mechanism or atomic-write helper
  design; governance-preservation verification.
- **`TORMENT_ARCHIVIST_WRITEBACK` opt-in clearance work.** D2
  re-verification script run against active workspaces; D4 dry-run
  writeback report; D5 quarantine script; rollback doc. All ratified
  2026-04-17 as required deliverables before opt-in clearance.
- **Findings doc promotion.** `scratch/AGENT_RUNTIME_PHASE1_TIER1_FINDINGS.md`
  promotion to `docs/` (orientation map §6 parked item).
- **Per-tool-family `tool_result` defaults.** Cluster 2 §11.7 / §17
  deferred to v0.3.
- **Acknowledge-but-redact filter mode** (FILTER-A §4 future feature).
- **Batch C accumulating-workspace evidence** (long-iteration plan §3,
  parked).
- **Phase 0 successor doctrine versions** (Memory-to-Prompt Automation
  v0.2, v1.0). Each requires its own trio ratification.

Brainstorm-level items (Cluster 3 affect, Cluster 4 offline reflection,
Cluster 6 research/defer, BRAINSTORM-* mechanism list, broad
autonomous tool use, hivemind expansion, TriOcta/SRG memory dynamics)
remain inspirational per `TORMENT_ROADMAP_NOTES.md` Post-Cluster-5
boundary and require the full audit → draft → review → ratification
cycle before they can become active work.

---

## §8 — Implementation verification watch items (for the future implementation track)

These items are *known seams to verify in the implementation track*,
not Phase 0 doctrine commitments. They are recorded here so the v0.2
implementation track inherits them without rediscovery.

- **`/retrieve` `archive_hits` path through FILTER-A.** The shipped
  `POST /retrieve` endpoint in `app.py` composes `fabric.query()`
  results (FILTER-A applied) with `store.retrieve()` archive results
  (FILTER-A application not independently verified in the Phase 0
  survey). The implementation track should confirm that archive hits
  reaching LLM-facing context pass an equivalent surface filter, or
  add the filter if missing. Phase 0 names the requirement
  (Invariant 2); the implementation track verifies the code path.
- **`live_agent/` path precision.** Two `live_agent/` copies exist on
  disk (`C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\live_agent\` and
  `C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\live_agent\`).
  Both contain `memory_bridge.py`, `voice_pipeline.py`, `inference.py`.
  Phase 0 doctrine references the in-`torment_fabric/` copy. The
  implementation track should pick the canonical path; tracking both
  invites drift. Not a Phase 0 blocker.
- **`QUICKSTART.md` entrypoint correction** (`python -m torment_service`,
  not `python -m torment_service.app`). Parked; not a Phase 0 concern.
  Flagged in `NEXT_CHAT_HANDOFF_2026-05-24_evening.md` and CHECKPOINT
  Level 3 §"Documentation / wording notes."
- **`CharacterState` runtime write-site audit (PR #53 follow-on).**
  Named in §4 as a protected mutation surface; the audit itself is
  parked per orientation §5 watch-item rule. Promote to a scoped slice
  only if a successor doctrine version needs the enumeration verified
  at code level.
- **Git-survey confirmation.** The Phase 0 seven-layer survey's Layer 5
  (branches / commits) was not run under the AI's sandbox. The
  doctrine-anchor commit chain extracted from doc reads is recorded in
  the survey report; an operator-side `git branch -a` + targeted
  `git log --all -S <identifier>` confirmation before ratification of
  this doc would close Layer 5 formally.

None of these watch items blocks Phase 0 ratification. Each is
preserved so the v0.2 implementation track does not rediscover them.

---

## §9 — Cross-references

- **Pre-autonomy spine (doctrinal anchors):**
  - Track A v0.1 — `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`. Cited:
    §§3 (axes and Mode/Voice/Certainty/Authority), 4 (Certainty derived
    view), 6 (voice-audit rule expanded), 7 (three-role ownership),
    9.1 (badge is provenance not canon), 9.3 (source_type stability
    under voice), 9.6 (material disagreement invariant).
  - Cluster 2 v0.1 — `docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md`. Cited:
    §§7.1 (Authority class vocabulary), 7.4 (three-modifier model),
    9.1 (visibility contract), 10.5 (released-from-agent-scope default),
    11.3 (tool_result default), 11.5 (dangerous failure mode), 11.7
    (deferred items), 12 (disagreement primitive doctrinal commitment),
    14 (what this doc does NOT authorize), 17 (open items for v0.2/v0.3).
  - Track B v0.1 — `docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md`. Cited:
    §§2 (core distinctions), 3.2 (ContestRecord shape and immutability),
    7 (routing table), 8 (sixteen hard invariants — especially 1, 14,
    15, 16), 13 (what this doc does NOT authorize).
  - Cluster 5 v0.1 — `docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md`.
    Cited: §§0 anchor sentence, 2.1 canonical artifact vocabulary, 5
    fragility handles, 7.0 "necessary but not sufficient" gate framing,
    9.3 Path A/B/C (downstream candidates).

- **Governance and runtime substrate:**
  - `docs/MCP_CAPABILITY_BOUNDARY.md`. Anchor: "Automatic is allowed.
    Autonomous is not." Cited throughout §3.4, §3.5, §3.8, §5
    Invariant 10.
  - `docs/TORMENT_AGENT_DOCTRINE_v0.1.md`. Cited: Part 9 invariants
    (especially 1, 2, 4, 8, 9), R2 (memory as substrate not tool),
    R3 (no open tool-choice problem), R6 (eight-phase outer loop),
    Part 6 (internal reflex vs external scheduling).
  - `docs/TOOL_RESULT_LIFECYCLE_POLICY.md`. Cited: §0 (Q2-D ratified
    doctrine), §3.4 (implementation status — A/B/C shipped in v2.4.3).
  - `docs/TOOL_RESULT_RETRIEVAL_SEMANTICS.md`. Cited: §2.2 Changes
    A/B/C (retrieval discount, provenance badge, continuity-bonus skip
    — all shipped).
  - `docs/PROVENANCE_DOCTRINE_v2.4.x.md`. Cited: Invariants C
    (one canonical derivation) and F (provenance_type on user-adjacent
    surfaces); §6 surface map.
  - `docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md`. Cited: §§4
    (hard-exclude default), 5 (filter location), 6 (trust-tier
    conditionality), 7 (narrow scope), 8 (reason codes), 11 (non-goals).
  - `docs/AGENT_SPINE_OVERVIEW.md`. Cited: Seven Hard Invariants
    (especially D aperture bounded, F shared memory read-only).
  - `docs/CHARACTER_SYSTEM.md`. Cited: "Canon Anchors vs Derived
    Identity Anchors" + tier weight table.
  - `docs/MEMORY_DIGESTION_DOCTRINE_v0.1.md`. Cited: Released Memory
    Primitive; Four-Layer Statement; Advisory-Only Rule.
  - `docs/ROADMAP_v2.4.x.md`. Cited: §3 (Blocked Until Provenance
    categories — Archivist Write-Back, Broad Autonomous Tool Use,
    Self-Writing Cognition Loops).
  - `docs/ARCHIVIST_WRITEBACK_GATE_FRAMING_v2.4.x.md`. Cited: §§2
    (anchor sentence, recursion guard), 6 (gate-flip criteria), 7
    (ratified decisions D1–D6).

- **Closure trail (Phase 0 stands downstream of these):**
  - `docs/CHECKPOINT_2026-05_Q2D_TOOL_RESULT_DOCTRINE.md`.
  - `docs/CHECKPOINT_2026-05_LEVEL_3_ST_RETRIEVAL.md`.
  - `docs/CHECKPOINT_2026-05_TIER_2_RUNTIME_EVIDENCE.md`.
  - `docs/AGENT_AUTOMATION_NEXT_STEP_AUDIT.md` (especially "Current
    next gate after promotion" — names Memory-to-Prompt Phase 0 as
    next gate D after C/B foundation).
  - `docs/AGENT_RUNTIME_LONG_ITERATION_TEST_PLAN.md`.

- **Orientation:**
  - `docs/PROJECT_ORIENTATION_MAP.md`. §§1 (anchor doctrine), 2
    (closed arcs as of 2026-05-24), 5 (gate-start survey rule), 7
    (current likely next direction).
  - `NEXT_CHAT_HANDOFF_2026-05-24_evening.md` (operational scratch
    context for the gate-opening session).

- **Brainstorm-level (not active doctrine):**
  - `scratch/brainstorming/memory_roadmap_2026_05_09/99_session_summary.md`
    — eight framing-doc-grade sentences; the Memory-to-Prompt kernel is
    a synthesis of #1 (truthfulness envelope), #4 (no private
    persistent influence), and the MCP boundary doctrine.

- **Substrate code (read-only references; no modifications by this
  document):**
  - `torment_service/governance.py` — `filter_llm_facing`, surface
    constants.
  - `torment_service/deep_hits.py` — `assert_authoritative_memory`,
    `NonAuthoritativeDeepHit` base, `DeepRetrievalHit`,
    `OrphanedDeepHit`, `NonAuthoritativeMemoryError`.
  - `torment_service/fabric.py` — `query()` (FILTER-A applied),
    `ingest()` (`suppress_canon` keyword), tool-result lifecycle cap.
  - `torment_service/spine.py` — `_fast_tool_result_ingest`
    (passes `suppress_canon=True`).
  - `torment_service/app.py` — `POST /retrieve` (assembled context
    endpoint), `POST /agent/query`, `POST /tool/ingest`.
  - `torment_service/retrieval_assembler.py` — `assemble_context()`,
    `ASSEMBLER_PROFILES`, BLOCK_IDENTITY / BLOCK_RELATIONAL /
    BLOCK_SITUATIONAL / BLOCK_ARCHIVE precedence.
  - `torment_service/scoring.py` — `derive_provenance_type`,
    `derive_query_provenance_type`.
  - `cognition/apertures.py` — aperture-bounded retrieval.
  - `cognition/recursion_guard.py` — bounded-DFS ancestry check.
  - `torment_service/agent_loop.py` — outer-loop runner with Phase 3
    (Aperture) and Phase 5 (Action Policy).
  - `torment_service/action_policy.py` — Mode→legal-intents,
    fallback chain, drift-veto, tool-narrowing.

---

## §10 — Ratification record

**Drafted:** 2026-05-25 by Claude, against the seven-layer survey
conducted earlier in the same session and the ratified plan with two
corrections applied (direct docs draft, no scratch; tightened
Invariant 1 wording for future-automation subordination).

**Revised:** 2026-05-25 (same session) per operator + GPT correction.
The first draft over-tilted toward control-doctrine framing; the
revision installs the operator's three-line character-first hierarchy
(§1.2), adds a positive-purpose section (§1.4 *What memory-to-prompt
automation is FOR*) anchored to existing doctrine + shipped code,
re-prefaces the Posture, Tone discipline, TL;DR, Center question, §3
commitments, §4 protected surfaces, and §5 invariants as
substrate-preservation-of-character-expression rather than
restriction-first control. The substantive constraints, anchor list,
the eight commitments, the protected-surface enumeration, and the ten
invariants are unchanged; only their framing and lead position are
revised.

**Pushback resolved (recorded for traceability):** GPT's first-pass
correction framed governance as *"secondary."* Claude pushed back: the
operator's own three-line hierarchy named governance as *"preserves
source identity"* — load-bearing in substrate-criticality, subordinate
in purpose. The distinction matters because the substrate is what
makes character expression survivable (FILTER-A enforces character
privacy; Q2-D suppression prevents tool-result rows from silently
overwriting identity; the recursion guard prevents archivist writeback
from laundering cognition output into canon under a character's name).
"Secondary" under-states the substrate role. **GPT subsequently
accepted the pushback and ratified the canonical phrasing as
*"Governance is subordinate in purpose, but load-bearing in
substrate-criticality"* (cleanup pass 2026-05-25).** That phrasing is
the load-bearing wording installed in the Posture (§ Posture) and
referenced from §1.2. This disagreement did not reject the central
character-first correction (which is correct and applied); it
tightened its language.

**Awaiting ratification by trio (pzychozen + GPT + Claude).** Pending
checklist:

- [ ] §0 — TL;DR accepted as the three-line-hierarchy lead +
      kernel-anchored summary of the positive purpose and eight
      preservation commitments.
- [ ] §1.1 — Foundational kernel accepted as two-halves load-bearing
      (shape + seize).
- [ ] §1.2 — Character-first hierarchy (operator's three lines)
      accepted as the load-bearing structural frame.
- [ ] §1.3 — Two-clause center question (enabling + preservation)
      accepted.
- [ ] §1.4 — Positive-purpose section (nine character-expression
      uses, each anchored to existing doctrine or shipped code)
      accepted as the load-bearing statement of what
      memory-to-prompt is FOR.
- [ ] §2 — Reconciliation table accepted; no new axes introduced by
      Phase 0.
- [ ] §3.1 — What memory may enter prompt context: closed-primitive
      bound, aperture bound, FILTER-A bound, H4d authority-guard bound,
      assembly precedence bound — all accepted as the operative
      commitment for the memory-to-prompt path.
- [ ] §3.2 — Provenance presentation commitments accepted.
- [ ] §3.3 — `tool_result` advisory labeling commitments accepted
      (Cluster 2 §11.3 three-modifier default, Q2-D suppression,
      retrieval shaping, voice non-alteration, per-tool-family
      deferred).
- [ ] §3.4 — What cannot become authority commitments accepted.
- [ ] §3.5 — What requires explicit user approval commitments accepted.
- [ ] §3.6 — What gets logged commitments accepted.
- [ ] §3.7 — What is reversible commitments accepted (per-call /
      opt-in / quarantine patterns; no global env-var toggle).
- [ ] §3.8 — What is forbidden commitments accepted.
- [ ] §4 — Protected mutation surface enumeration accepted, including
      `CharacterState` named without opening the PR #53 audit.
- [ ] §5 — Ten hard invariants accepted as the v0.1 scorecard.
- [ ] §6 — What this document does NOT authorize accepted as the
      operative non-goals list.
- [ ] §7 — Named sub-gates accepted as the parking lot for v0.2 and
      adjacent successor doctrine work.
- [ ] §8 — Implementation verification watch items accepted as
      preserved-not-resolved.
- [ ] Promotion to `docs/` as `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.1.md`,
      following the Track A / Cluster 2 / Track B / Cluster 5 v0.1
      pattern. The Phase 0 survey report and the gate-start survey
      that produced it are recorded in conversation context for the
      2026-05-25 session.

After ratification, this doc is frozen until a separately ratified
amendment.

---

## §11 — What Memory-to-Prompt Automation v0.1 does and does not include

Memory-to-Prompt Automation v0.1 is a doctrine doc, not an
implementation. It declares the *character-first guided-memory
contract* between TORMENT's existing memory + character substrate and
any future automation layer that would shape LLM prompt context with
retrieved memory. The contract has two voices held in balance: an
enabling voice (what memory-to-prompt is FOR — character presence,
voice, roleplay continuity, emotional recall, relationship memory,
callbacks, symbolic resonance, tool-aware dialogue, natural expression
from remembered history) and a preservation voice (what must not
silently rewrite canon, authority, identity, governance, or mutation
rights). It collects the constraints the
pre-autonomy spine (Track A / Cluster 2 / Track B / Cluster 5) plus
the MCP capability boundary, the Agent Doctrine v0.1, the tool-result
lifecycle policy, the Q2-D doctrine, the Provenance Doctrine, FILTER-A,
the Character System, and the Archivist Writeback Gate Framing place on
the memory-to-prompt territory. It names ten hard invariants, eight
Phase-0 commitments, a protected mutation surface enumeration, the
sub-gates that follow Phase 0, and implementation verification watch
items preserved for the future implementation track. It explicitly does
NOT:

- Modify any code in `torment_service/`, `cognition/`, `live_agent/`,
  `tests/`, `schemas/`, `tool_executors/`, `start/`, or anywhere else.
- Amend Track A v0.1, Cluster 2 v0.1, Track B v0.1, Cluster 5 v0.1,
  the MCP capability boundary, or the Agent Doctrine v0.1 in any
  section.
- Add any field to `ProvenanceV1`, any new governance flag, any new
  Authority class, any new Mode value, any new Lifecycle value, any
  new surface in FILTER-A's surface enum, any new aperture type, or
  any new memory tier.
- Implement a consultation mechanism for the future automation layer.
  That is Memory-to-Prompt Automation v0.2 (or a parallel
  implementation track).
- Authorize a runtime gate, a new MCP surface, a new exposure tier,
  a new tool family, a scheduler, a daemon, a watcher, a wall-clock
  trigger initiated by the agent, an env var, or a test wiring.
- Allow open-ended LLM-visible memory search; allow an open
  tool-choice menu to the LLM; allow silent widening of the fallback
  chain or legality table; allow review re-entry; allow autonomous
  tool execution via MCP; allow auto-canon of `tool_result` rows;
  allow auto-promotion of character voice to agent autobiography;
  allow auto-triggered contest from cognition `dissent`; allow
  self-issued `refuse / no-persist` contests; allow background
  schedulers; allow bypassing FILTER-A; allow bypassing the recursion
  guard; allow broad autonomous tool use beyond `code_exec`; allow
  promoting tool-result content to identity-canonical memory by
  automation.
- Resolve the `CharacterState` runtime write-site audit (PR #53
  follow-on). Named as a protected mutation surface in §4; the audit
  itself is parked per orientation §5 watch-item rule.
- Resolve the `/retrieve` `archive_hits` FILTER-A wiring verification.
  Named as an implementation verification watch item in §8; the
  verification belongs to the future implementation track.
- Promote Cluster 3 (Affect) or Cluster 4 (Offline Reflection) doctrine.
  Both remain brainstorm-level.
- Authorize the `TORMENT_ARCHIVIST_WRITEBACK` flip. The flip remains
  opt-in per ARCHIVIST_WRITEBACK_GATE_FRAMING D6 and is not advanced
  by this doctrine.
- Modify `.gitignore`, FILTER-A's existing surface enum, the governance
  flag set, or any other existing TORMENT mechanism.
- Treat any §3 commitment, §4 surface, §5 invariant, §7 sub-gate, or
  §8 watch item as anything more than ratified *vocabulary, constraint,
  or parked seam*. They are not implementation authorizations.
- Bypass operational discipline (Windows = source of truth for
  TORMENT; AI is read-only advisor for the TORMENT workspace).

This document IS the Memory-to-Prompt Automation v0.1 advisory
doctrine (pending trio ratification). Subsequent versions (v0.2, v1.0)
require their own trio ratification before they supersede this one.
The runtime mechanism for memory-to-prompt automation, when designed,
becomes a separate framing-doc effort (Memory-to-Prompt Automation v0.2
or a parallel implementation track).

---

*End of Memory-to-Prompt Automation v0.1 DRAFT v2 (character-first
reframe revision applied 2026-05-25). Awaiting trio re-read and
ratification (pzychozen + GPT + Claude). No implementation authorized
by this document. No code changes. No schema migrations. No tests
authorized. The pre-autonomy spine is not amended.*
