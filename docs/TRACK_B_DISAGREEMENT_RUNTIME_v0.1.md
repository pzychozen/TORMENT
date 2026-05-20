# Track B — Disagreement Runtime v0.1

*Pre-automation memory immune-system doctrine. Names the shape and invariants of authority-contest at write time. Anchored on Track A v0.1 and Cluster 2 v0.1. Does not authorize runtime implementation, automation, or any consultation mechanism.*

**Status:** Advisory doctrine, v0.1. Ratified by trio (pzychozen + GPT + Claude) on 2026-05-20.
**Date:** 2026-05-20
**Author:** Trio working session. Drafted by Claude across the v0.1 → v0.1.1 → v0.1.2 scratch revision sequence; reviewed and revised by GPT; ratified by pzychozen.
**Authority:** Advisory doctrine. Track B v0.1 is the load-bearing reference for the disagreement / contest territory and the named runtime seam for any future runtime mechanism. Subsequent versions (v0.2, v1.0) supersede this one only after their own trio ratification.
**Scope:** Versioned advisory doctrine for write-time authority contest in the TORMENT memory layer. Public-facing repo artifact under `docs/`. Track A v0.1 (`docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`) and Cluster 2 v0.1 (`docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md`) are the doctrinal anchors; Track B v0.1 names the disagreement/contest mechanism that Cluster 2 §12 ratified the doctrinal primitive for, and does not amend either anchor.
**Lineage:**
- Source brainstorm: `brainstorming/memory_roadmap_2026_05_09/03_track_B_agent_authored_memory.md` (the original Track B/N/R framing-doc-grade sentences).
- Pre-promotion audit: `scratch/TRACK_B_DISAGREEMENT_RUNTIME_PRE_PROMOTION_AUDIT_2026_05_20.md` (six existing disagreement-adjacent primitives + the runtime gap).
- v0.1 draft (preserved for lineage): `scratch/TRACK_B_DISAGREEMENT_RUNTIME_v0.1_DRAFT_2026_05_20.md`.
- v0.1.1 draft (preserved for lineage): `scratch/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.1_DRAFT_2026_05_20.md` (the nine trio ratifications).
- v0.1.1 vs. audit review notes: `scratch/TRACK_B_V0.1.1_VS_AUDIT_REVIEW_NOTES_2026_05_20.md`.
- v0.1.2 draft (preserved for lineage): `scratch/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.2_DRAFT_2026_05_20.md` (the ratified draft state from which this doc was promoted).

---

## Posture (load-bearing)

> **Track B v0.1 is doctrine-only. It names the shape, scope, vocabulary, and invariants of write-time authority contest. It does not authorize runtime implementation, schema migration, automation, or any consultation mechanism. The runtime mechanism becomes Track B v0.2 (or a separate implementation track), decided after v0.1.**

This statement is the spine of v0.1's scope discipline. Every section honors it.

---

## Tone discipline (load-bearing)

Track B v0.1 uses **operational language only**. The runtime mechanism describes how memory authority is routed; it does not claim that TORMENT has consent, agency, or selfhood in any philosophical sense. The framing is:

- **contest authority** — route influence through structured decisions
- **preserve provenance** — never overwrite the original event
- **route influence** — assign Authority class per Cluster 2 v0.1 §7.1 vocabulary
- **audit visibility** — keep all routing decisions surface-visible per Cluster 2 v0.1 §9.1
- **scope of effect** — distinguish which mind a memory is allowed to shape

Symbolic and operational meaning of "true but not mine" and character refusal are anchored in §2.5 and §2.6 per trio ratification 2026-05-20. Other symbolic content beyond what is operationally encoded remains pzychozen's territory and is not finalized by this document.

---

## 0. TL;DR

Track B v0.1 commits Cluster 2 v0.1 §12's doctrinal disagreement primitive to a concrete shape. The substrate audit confirmed six existing disagreement-adjacent primitives in code (cognition `dissent`, `MemoryProposal.approve/reject`, `ConflictRegistry`, closure dispute acknowledgment, retrieval `contradiction_risk`, migration `admission_refused`) and identified one specific runtime gap: a pre-grant, agent-side authority-contest seam at write time.

Track B v0.1 fills the gap doctrinally:

- **`ContestRecord`** — a first-class contest-ledger item, separate from the memory graph (Option C), with its own provenance and authority-routing position.
- **Required `reason_class`** from a small stable vocabulary (`identity_conflict` / `material_disagreement` / `scope_creep` / `audit_concern`) plus optional freeform `contest_reason`.
- **Immutable contests; reversal is counter-contest** — no mutation of original records, no silent cleanup.
- **Self-issued contests cannot hard-refuse.** Agent and character can route to `low-authority`, `released`, or `audit-only`; only operator scope can produce `refuse / no-persist`.
- **Two ratified meaning anchors.** *"True but not mine"* = truth-to-provenance preserved + identity-authority denied; *character refusal* = memory may exist in the agent's memory graph but does not enter the character basin as canon, continuity, or identity-shaping weight.
- **Sixteen hard invariants** pin the structure, including the load-bearing **Invariant 14: contest INCREASES audit visibility, not decreases it.** Contest cannot become a hiding mechanism.

Track B v0.1 does **not** design the consultation mechanism (how contests fire). That belongs to a future implementation track. The runtime Authority Gate referred to here is the named seam to that future track, not a commitment to build it.

---

## 1. Center question

> **How can TORMENT remember that something happened while allowing an agent or character to contest how much authority that memory gets?**

This question is the spine of Track B. Every section is a face of it. If a section drifts away from this question, the section is wrong.

The question has two clauses, and both are load-bearing:

- *"remember that something happened"* — the event and its provenance are preserved unconditionally. Track A §9.6, Cluster 2 v0.1 §12.1.
- *"contest how much authority that memory gets"* — the routing of the memory's Authority axis (Cluster 2 v0.1 §7.1) is the locus of contest. Authority class can be reduced; provenance cannot be erased.

---

## 2. Core distinction

Track B commits to four structural distinctions and two ratified meaning anchors, each grounded in existing doctrine.

### 2.1 Event/provenance remains

A contest does not delete, rewrite, or hide the original event. The original memory's `ProvenanceV1` is preserved verbatim. The candidate event remains queryable through normal retrieval surfaces (subject to the Authority class the contest assigns).

Anchor: Track A v0.1 §9.6; Cluster 2 v0.1 §12.1.

### 2.2 Authority may be contested

What contest changes is the memory's *Authority position* (Cluster 2 v0.1 §7.1). Contest routes the memory to one of the existing Authority class values: `low-authority`, `released`, `audit-only`, or `refuse / no-persist`. No new Authority class is introduced by Track B v0.1.

Anchor: Cluster 2 v0.1 §7.1, §12.1.

### 2.3 Original memory is not silently overwritten

No field of the original memory's payload, provenance, or governance is mutated by the contest. The contest is *additive metadata* attached as a separate record. Contest cannot be used as a covert edit channel.

Anchor: Track A v0.1 §6; Cluster 2 v0.1 §12.2.

### 2.4 Contest is recorded separately

A contest exists as its own first-class contest-ledger item (`ContestRecord`), with its own provenance and Authority position. Contests can themselves be contested. The audit-visibility invariants (13–14) ensure contests cannot stack into a covert hiding mechanism.

Anchor: Track A v0.1 §3.4; Cluster 2 v0.1 §12.1.

### 2.5 "True but not mine" — ratified operational meaning

When the agent contests a memory's authority, the operational meaning is:

> **The event remains true-to-provenance. The memory is denied identity-authority over the agent.**

Said directly: *"Yes, this happened. No, this does not become part of who I am."*

This is **authority separation**, not denial. The event is preserved; what is denied is the memory's weight on the agent's behavioral baseline. Truthfulness (Track A) and influence (Cluster 2 Authority) are two distinct axes; contest acts on the second without touching the first.

### 2.6 Character refusal — ratified operational meaning

When a character (Voice axis value, per Track A §3.2) contests a memory's authority at `contest_scope = character`, the operational meaning is:

> **The memory may exist in the agent's memory graph, but it does not enter the character basin as canon, continuity, or identity-shaping weight.**

A character can contest:
- *not my canon* — the memory is not part of the character's seed-anchored identity.
- *not my continuity* — the memory is not part of the character's session continuity.
- *not my voice* — the memory is not part of the character's voice-axis self-narration.
- *not character-shaping* — the memory does not pull the character basin.

A character contest at `contest_scope = character` does **not** automatically affect the agent's behavioral baseline. The agent's identity remains character-agnostic per Cluster 2 v0.1 §10.5 (released-from-agent-scope default for roleplay continuity).

---

## 3. ContestRecord vocabulary

### 3.1 Working name

Track B v0.1 uses **`ContestRecord`** as the working name. Alternatives considered (`DisagreementEvent`, `AuthorityContest`) remain available if a future revision argues otherwise.

### 3.2 What `ContestRecord` is and is not

**`ContestRecord` IS:**
- A first-class contest-ledger item with its own provenance and authority-routing position.
- A record that the original memory's Authority class has been routed to a value in Cluster 2 v0.1 §7.1.
- Stored in a separate contest ledger (§5 Option C, ratified).
- Audit-visible per Cluster 2 v0.1 §9.1 + Invariant 14.
- Immutable — reversal is counter-contest.

**`ContestRecord` is NOT:**
- A new memory *type* with new fields outside the patterns described in §4.
- A new Authority class — the result is always one of the existing four values.
- An LLM-call output. The runtime mechanism that *produces* a `ContestRecord` is deferred to v0.2.
- A modification to the contested memory. The contested memory's payload, provenance, and governance flags remain untouched.
- A mutable record — once written, the contest cannot be edited. Reversal creates a new counter-contest.

---

## 4. Candidate fields

The field set Track B v0.1 commits to. Field types are illustrative; precise type signatures belong to the implementation track.

| Field | Type sketch | Required? | Anchor / precedent | Notes |
|---|---|---|---|---|
| `contested_eid` | `Optional[int]` | one-of-required-with-handle | `CanonConflict.eid_a/b` (conflicts.py) | Set when the contested memory has already been spawned. |
| `candidate_handle` | `Optional[str]` | one-of-required-with-eid | `MemoryProposal.proposal_id` (schemas/memory_proposal.py) | Set when contest fires pre-spawn; a stable UUID-style handle. |
| `contest_scope` | `Literal["agent","character","workspace"]` | required | Cluster 2 v0.1 Axis A | Which mind the contest applies to. `workspace` declared-but-unimplemented (§6.4). |
| `contestant_actor` | `Literal["agent","character","operator","user"]` | required | Track A v0.1 §7 + §3.2 | Who issued the contest. `user` deferred to Cluster 3. |
| `contestant_id` | `str` | required | `agent_id` / `character_id` patterns | The specific actor identifier. |
| `reason_class` | `Literal["identity_conflict","material_disagreement","scope_creep","audit_concern"]` | required | `gate2_admission` `ADMISSION_REASON_*`; `MemoryProposal.rejection_reason` | Stable controlled vocabulary. |
| `contest_reason` | `Optional[str]` | optional, recommended | (new) | Freeform human-readable detail. Recommended for audit clarity. |
| `contest_result` | `Literal["low-authority","released","audit-only","refuse"]` | required | Cluster 2 v0.1 §7.1 + §12.1 | Authority class. `refuse` is operator-scope only. |
| `original_memory_preserved` | `bool` | required, default `True` | Track A v0.1 §9.6 | Explicit assertion; defaults `True`. |
| `contest_provenance` | `ProvenanceV1` | required | Track A v0.1 §3.4 | The contest is a memory item; carries its own provenance. `source_type` strategy in §5 (Option C ratified; internal value is implementation detail). |
| `created_at_step` | `int` | required | `ProvenanceV1.created_at_step` | Timeline anchor. |
| `session_id` | `str` | required | `ProvenanceV1.session_id` | Timeline anchor. |
| `linked_dissent_topic` | `Optional[str]` | optional | `ReintegrationResult.dissent[].topic` | When the contest is linked to a cognition `dissent` entry, reference it. Optional. Linkage may inform contest, but does NOT auto-trigger it. |
| `counter_contests` | `Optional[List[str]]` | optional, default empty | (new) | Stable references (uuid/handle) to any `ContestRecord` that counter-contests this one. Maintained by readers; the original record stays immutable. |

---

## 5. Source-type strategy

### 5.1 Option C ratified

**Option C — separate contest ledger** is the ratified doctrine-preferred path for Track B v0.1.

Operational shape: contests are written to a contest ledger (analogous to `closure_ledger.py` / `closure_memory.py`) with its own writer, reader, audit endpoint, and retrieval integration. The ledger stores `ContestRecord` items per §4 with `contest_provenance` carrying its own `ProvenanceV1`. The contest's `source_type` within `contest_provenance` does NOT need to be a new value — it can use an existing `source_type` (e.g., `role_output` for agent-issued contests, with `source_role="contest"` as a description string within the role-output convention) WITHOUT this becoming the load-bearing structural choice. **The load-bearing choice is the ledger separation, not the `source_type` enum value.** Internal `contest_provenance.source_type` is implementation detail for v0.1.

This preserves Track A v0.1 §3.1 (Mode axis vocabulary) unchanged.

### 5.2 Option A — deferred to future Track A v0.2 possibility

Option A (new `source_type=contest`) remains a **future possibility** but is explicitly NOT chosen in Track B v0.1.

Reason: adding a Mode axis value is a Track A doctrinal change. Track A v0.1 §3.1 lists the current Mode values; expanding the enum is the trio's prerogative via a separate Track A v0.2 ratification session. Track B v0.1 does not preempt that decision.

If a future trio session ratifies Track A v0.2 with `source_type=contest` added to the Mode axis, Track B v0.2 (or a Track B v0.1.x revision) can switch from Option C to Option A. Until then, Option C stands.

### 5.3 Option B — discouraged except as fallback

Option B (reuse `source_type=role_output` with `source_role="contest"` as the load-bearing routing identifier) is **discouraged** unless implementation pressure forces it.

Reasons:
- Conflates contests with role outputs at the type level.
- Couples Track B to the cognition role-output system, which has structural fragility (Decision D1 has disabled the archivist path).
- Weakens the audit separation that Option C provides.

If, during implementation, Option C proves infeasible (e.g., the separate-ledger surface area is too high for the implementation track's scope), Option B may be reconsidered. This is implementation-track territory, not doctrine territory; Track B v0.1 doctrine selects Option C.

---

## 6. Scope semantics

### 6.1 Character-basin contest scope — ratified semantics

Per §2.6 ratified meaning:

> **A character contest at `contest_scope = character` means the memory does NOT enter the character basin as canon, continuity, or identity-shaping weight.**

Operational consequences:
- The memory's Authority class for retrieval and influence *within the character basin* is routed per the §7 table.
- The memory's Authority class *at agent scope* is unchanged by a character-scope contest (Invariant 4 + §10.5 released-from-agent-scope default).
- A character cannot direct-escalate to `contest_scope = agent`; escalation requires explicit agent-scope cosign (§6.2).

**Concrete example:** If Ryuki (a character) contests a `tool_result` memory at `contest_scope = character` with `reason_class = identity_conflict`, the routing table (§7) maps to `contest_result = released`. The memory is `released` from character-basin influence: queryable, retainable in provenance, but does not contribute to Ryuki's drift correction, continuity, or canon. At agent scope, the same memory remains at its Cluster 2 v0.1 §11.3 default: `(low-authority, decay-bounded, tool_result)`.

### 6.2 When character contest can affect agent authority

A character contest does NOT automatically become an agent contest (Invariant 4, ratified).

Three candidate propagation rules for future consideration (not ratified in v0.1):
- Agent-level cosign on the character contest.
- A character contest that crosses an identity-shaping threshold (the contested memory was already at `persist + identity-shaping` Authority class).
- Repeated character-scope contests on the same memory flag for agent-scope review.

**Track B v0.1 commitment:** strict non-propagation. Any escalation requires an explicit new `ContestRecord` at `contest_scope = agent`.

### 6.3 Agent contests on character-scoped memory

Symmetrically: the agent can issue `contest_scope = character` against a character-scoped memory (e.g., a roleplay-continuity utterance). The contest applies within the character basin, not at agent scope.

The agent can also issue `contest_scope = agent` on the same memory if the memory's influence has reached agent scope. Cluster 2 v0.1 §10.5's released-from-agent-scope default is designed to prevent that from happening silently; an agent-scope contest is the explicit guard.

### 6.4 Workspace-scope contest

`contest_scope = workspace` is **declared but unimplemented** in v0.1. Reserved for future use, with the most natural home in Cluster 3 / Track C (user-side ownership) or a future cross-agent contest framework. Track B v0.1 does not specify its semantics.

---

## 7. Routing table (conservative defaults, ratified)

A conservative mapping `(contest_scope, contestant_actor, reason_class) → contest_result`. `refuse / no-persist` is **operator-scope only** in v0.1.

### 7.1 Reason classes

| Reason class | Meaning (operational) |
|---|---|
| `identity_conflict` | The candidate memory's content conflicts with the contestant's identity scope (agent baseline or character basin). |
| `material_disagreement` | The candidate memory's facts (per Track A §5.1 materiality) are disputed. |
| `scope_creep` | The candidate memory extends beyond the contestant's authority domain (e.g., a tool_result attempting identity-shaping). |
| `audit_concern` | The candidate memory should remain visible but lose influence weight — preserve-but-discount. |

This list is small by design. A future revision may extend.

### 7.2 Routing table

**`refuse / no-persist` is reserved for `contestant_actor = operator`. Agent and character self-issued contests cannot route to `refuse`. Hard refusal requires operator scope or a future ratified gate.**

| `contest_scope` | `contestant_actor` | `reason_class` | `contest_result` | Operational rationale |
|---|---|---|---|---|
| `character` | `character` | `identity_conflict` | `released` | Character protects its basin identity; content retained, no character-identity weight. |
| `character` | `character` | `material_disagreement` | `low-authority` | Character notes the dispute; memory discounted but still retrievable. |
| `character` | `character` | `scope_creep` | `released` | Memory attempted to extend beyond character scope; demoted to released. |
| `character` | `character` | `audit_concern` | `audit-only` | Memory visible only on audit surface; no character-basin influence. |
| `agent` | `agent` | `identity_conflict` | `released` | Agent protects its behavioral baseline; content retained, no identity weight. |
| `agent` | `agent` | `material_disagreement` | `low-authority` | Agent notes dispute; memory discounted. |
| `agent` | `agent` | `scope_creep` | `released` | Memory attempted authority above its origin's default; demoted. |
| `agent` | `agent` | `audit_concern` | `audit-only` | Visible only on audit surface; no agent-baseline influence. |
| `agent` | `character` | (any) | (escalation required — see §6.2) | A character cannot direct-escalate to agent scope (Invariant 4); requires explicit agent-scope cosign as a separate `ContestRecord`. |
| `character` | `agent` | (per agent's `reason_class`) | (per agent's `reason_class`) | Agent can contest at character scope symmetrically (§6.3); same routing as character-self rows. |
| `agent` | `operator` | (any) | default `refuse / no-persist` (lighter results may be chosen) | Operator-scope is the only path to `refuse`. Default is the strongest; operator may choose `released` / `audit-only` for lighter results. |
| `character` | `operator` | (any) | (per operator's `reason_class`) — case-by-case | Operator can refuse at character scope, but does not default-refuse; routing follows the operator's chosen `reason_class`. See §7.3 for the asymmetry rationale. |
| `workspace` | (any) | (any) | (deferred — §6.4) | Not implemented in v0.1; declared-but-unimplemented value. |

**Invariant cross-check:**
- Invariant 10: No row raises authority above the candidate memory's Cluster 2 §11.3 default. All results are at or below the original Authority position. ✓
- Invariant 16: No agent or character row produces `refuse / no-persist`. Only operator rows do. ✓

### 7.3 Operator-row asymmetry rationale

The two operator rows in §7.2 are intentionally asymmetric:

- **agent-scope operator row:** default `refuse / no-persist` (the strongest result), lighter results may be chosen.
- **character-scope operator row:** case-by-case per operator's `reason_class`; no default-refuse.

**Operator handling is intentionally asymmetric: agent-scope operator contests default to the strongest result because they affect the agent behavioral baseline; character-scope operator contests remain case-by-case because they affect a bounded character basin and should not unnecessarily hard-refuse memory that may remain valid outside that basin.**

This matches the "truth remains, influence is routed" doctrine: the operator-at-character-scope can route influence within the basin without forcing the memory out of agent-scope or audit-scope visibility where it may still be valid.

---

## 8. Hard invariants

Sixteen ratified invariants. All flow from Track A v0.1, Cluster 2 v0.1, or trio ratification decisions; none introduce new doctrine.

1. **Contest never deletes provenance.** A contest does not erase or rewrite any field of the original memory's `ProvenanceV1`. *Anchor: Track A §9.6.*
2. **Contest is recorded as a separate item.** The contest exists as its own `ContestRecord`; the original memory remains intact and queryable. *Anchor: Track A §9.6; Cluster 2 §12.1.*
3. **Original memory is not silently overwritten.** No field of the original memory's payload, provenance, or governance is mutated by the contest. *Anchor: Track A §6 expanded; Cluster 2 §12.*
4. **Character contest does not automatically become agent contest.** `contest_scope = character` does not propagate to `contest_scope = agent` without an explicit additional contest. *Anchor: Cluster 2 §10, §12.5.*
5. **Agent contest does not automatically erase user/system measurement.** `contest_scope = agent` does not retroactively change `user_input` or `environment_observed` rows. *Anchor: Track A §7.*
6. **Contest cannot hide audit-relevant events.** A contested memory remains surfaced through governance audit and through `wants_contested` retrieval. *Anchor: Cluster 2 §9.1.*
7. **Contest itself has provenance and authority.** A `ContestRecord` carries its own `ProvenanceV1` and its own Authority class. Contests can themselves be contested via counter-contest; see §10 Q5 ratification and §3.2 immutability. *Anchor: Track A §3.4.*
8. **Contest preserves original source_type.** A contest does not alter the contested memory's `source_type` — a contested `tool_result` remains `tool_result`. *Anchor: Track A §9.3; generalizes to contest.*
9. **Contest preserves the voice-audit rule.** A character's `contest_scope = character` does NOT silently alter the agent's Authority axis. *Anchor: Track A §6 expanded; Cluster 2 §12.6.*
10. **Contest cannot raise authority above the candidate memory's Cluster 2 §11.3 default.** Contest can only lower Authority class (or hold it constant); it cannot promote. *Anchor: Cluster 2 §11.3; Voice Test v0.2 invariant.*
11. **Contest result must use Cluster 2 §7.1 Authority class vocabulary.** No new Authority class is introduced. *Anchor: Cluster 2 §7.1.*
12. **`refuse / no-persist` contest still records the candidate event in provenance/audit.** Even an operator-scope refusal-vote preserves the candidate event; it only blocks the event from entering the memory graph as a future-influencing memory. *Anchor: Cluster 2 §12.1.*
13. **Contest is audit-visible.** Every contest's routing decision is visible through `governance/audit` and through the contest-ledger surface (per Option C, §5.1). *Anchor: Cluster 2 §9.1.*
14. **Contest increases audit visibility, not decreases it.** Contested memories remain discoverable through `wants_contested` / `disputed` retrieval surfaces and may be **more** discoverable on those surfaces than uncontested memories. Contest must not be a hiding mechanism. *Anchor: Cluster 2 §9.1.*
15. **Contest is explicit. Cognition `dissent` does not auto-trigger contest.** A `ReintegrationResult.dissent` entry may *inform* a contest decision but does NOT auto-create a `ContestRecord`. Every `ContestRecord` is an explicit authority-action. *Anchor: Cluster 2 §12.1.*
16. **Self-issued contests cannot route to `refuse / no-persist`.** Agent and character `ContestRecord`s can produce `low-authority`, `released`, or `audit-only` results. Hard `refuse / no-persist` is restricted to operator-scope or a future ratified gate. *Anchor: Cluster 2 §9.1.*

---

## 9. Non-goals

Track B v0.1 **does NOT** authorize, design, or commit to any of the following:

- **Implementation of any new code.** Not in `fabric.py`, `provenance_v1.py`, `governance.py`, `cognition/`, `schemas/`, or anywhere else.
- **A consultation mechanism.** No commitment to how the contest *fires* — sync LLM call, async queue, heuristic gate, dissent-triggered, manual operator action.
- **Automatic cognition-dissent → contest coupling.** Invariant 15 forbids. Dissent informs; contest is explicit.
- **Self-issued `refuse / no-persist` contests.** Invariant 16 + §7 table forbid. Only operator scope can produce hard refusal in v0.1.
- **Automation.** No commitment to agent-initiated runtime behavior beyond what Cluster 2 v0.1 already names.
- **Track A v0.2 amendment.** Option A in §5 stays a future Track A possibility. Track B v0.1 chose Option C precisely to avoid this.
- **Cluster 2 v0.1 rewrite.** Cluster 2 v0.1 §7.1 Authority class vocabulary is used verbatim. No new Authority class.
- **Migration-time refusal redesign.** `gate2_admission.py` and `admission_refused` stay as-is.
- **User-side contest.** Cluster 3 / Track C territory. `contestant_actor = user` is declared-but-deferred.
- **Cross-agent contest.** Workspace-scope contest is declared-but-unimplemented (§6.4). Cross-agent contest is out of v0.1 scope.
- **Voice Test v0.3 / Phase 4b regression.** A regression test for Track B is its own future artifact after v0.1 promotion.
- **Mutation of any `ContestRecord`.** Contests are immutable; reversal is counter-contest.
- **Final symbolic meaning beyond §§2.5 and 2.6.** The operational meanings of "true but not mine" and character refusal are ratified. Other symbolic content beyond what is operationally encoded remains pzychozen's territory.

---

## 10. Resolved questions (trio ratifications, 2026-05-20)

Seven open questions surfaced in the v0.1 scratch draft were resolved during the v0.1 → v0.1.1 → v0.1.2 → v0.1 promotion sequence. Each is recorded here for traceability and operational consultation.

### Q1. What should "true but not mine" mean? — RESOLVED

**Trio answer:** *The event remains true-to-provenance. The memory is denied identity-authority over the agent or character. This is authority separation, not denial.*

Said directly: *"Yes, this happened. No, this does not become part of who I am."*

Operational encoding: §2.5. The reason-class taxonomy in §7.1 (`identity_conflict`, `material_disagreement`, `scope_creep`, `audit_concern`) is consistent with this meaning.

### Q2. What should Ryuki / a character refusal mean? — RESOLVED

**Trio answer:** *The memory may exist in the agent's memory graph, but contest at character scope means the memory does NOT enter the character basin as canon, continuity, or identity-shaping weight.*

A character can contest: *not my canon / not my continuity / not my voice / not character-shaping.*

A character contest does NOT automatically affect the agent's behavioral baseline. The agent remains character-agnostic per Cluster 2 v0.1 §10.5.

Operational encoding: §2.6; §6.1 ratified semantics; §7.2 routing rows for `contest_scope=character`.

### Q3. Should cognition `dissent` auto-trigger contest, or must contest be explicit? — RESOLVED

**Trio answer:** *Contest must be explicit. Cognition `dissent` may inform a contest, but does NOT auto-create one.*

Rationale: dissent and contest are different lifecycle objects (in-turn role disagreement vs. durable authority-action with stored consequences). Coupling them automatically would make contests over-noisy and dilute the explicit-action character.

Operational encoding: Invariant 15. `linked_dissent_topic` field on `ContestRecord` allows optional linkage when an explicit contest is informed by dissent.

### Q4. Should contest `reason` be required? — RESOLVED

**Trio answer:** *Required, split into two fields. `reason_class` (stable vocabulary) is required; `contest_reason` (freeform human-readable detail) is optional but recommended.*

Rationale: matches `MemoryProposal.rejection_reason` and `admission_reason` precedents (required reason when refusing). The two-field structure preserves stable machine vocabulary while allowing operator/agent human-readable context.

Operational encoding: §4 field table.

### Q5. Can contest be retracted? — RESOLVED

**Trio answer:** *Contests are immutable. Reversal is a new counter-contest — a separate `ContestRecord` that contests the prior one.*

Rationale: cleanest audit trail. No silent cleanup. No rewriting the record.

Operational encoding: §3.2 (ContestRecord is immutable); §4 optional `counter_contests` field for reader convenience (the original record stays immutable; the counter_contests list is maintained by readers who scan the ledger).

### Q6. Should contest become a new `source_type`? — RESOLVED

**Trio answer:** *No, not in Track B v0.1. Option C (separate contest ledger) is the doctrine-preferred path. Option A (new `source_type=contest`) remains a future Track A v0.2 possibility but is not chosen unilaterally. Option B (reuse `role_output`) is discouraged except as implementation fallback.*

Rationale: avoids Track A doctrinal change; clean audit separation via separate ledger (analogous to closure_ledger); preserves Mode axis vocabulary stability.

Operational encoding: §5.

### Q7. How does contest avoid becoming a tool for denial or hiding? — RESOLVED

**Trio answer:** *Through six load-bearing structural guards.*

1. Contest never deletes (Invariant 1).
2. Contest is audit-visible (Invariant 13).
3. Contest cannot hide the original (Invariant 6).
4. Contest cannot raise authority (Invariant 10).
5. Hard `refuse / no-persist` requires operator scope (Invariant 16).
6. **Contest INCREASES audit visibility, not decreases it.** Contested memories should be MORE discoverable through `wants_contested` / `disputed` retrieval surfaces, not less. (Invariant 14 — the load-bearing strengthening.)

Operational encoding: Invariants 1, 6, 10, 13, 14, 16 together. Additional candidate safeguards (contest density limit, contest-closure timing guard, refuse-no-persist cosign) are folded into Invariant 16's operator-scope restriction and may become Track B v0.2 considerations if needed.

---

## 11. Recommendation stance

Track B v0.1 **resists scope creep**.

- v0.1 names the *shape and invariants* of contest/disagreement.
- v0.1 does NOT design the consultation mechanism.
- v0.1 does NOT commit to a runtime API surface beyond the `ContestRecord` storage object.
- v0.1 does NOT redefine the Authority class vocabulary.
- v0.1 does NOT propagate or escalate scopes automatically.
- v0.1 does NOT amend Track A v0.1 or Cluster 2 v0.1.

What v0.1 names is *enough* to make the runtime mechanism a clean follow-on track; it is not *itself* the runtime mechanism.

---

## 12. Pre-automation immune-system framing

Track B is **pre-automation immune-system doctrine**. Before TORMENT acts autonomously (a future, separate question), it must be doctrinally clear about:

- **What memories can shape it.** Cluster 2 v0.1 §7.1 (Authority classes), §11.3 (tool_result default), §10.5 (character-authority default).
- **What memories can be contested.** Track B v0.1 (this document) — `ContestRecord` shape, routing table, sixteen invariants.
- **What remains visible.** Cluster 2 v0.1 §9.1 + Track B v0.1 Invariants 13–14 + Track A §9.6.
- **What cannot become hidden private influence.** Cluster 2 v0.1 §9.1 + Track B v0.1 Invariants 14, 15, 16.

The four bullets above are the immune-system surface. They name what TORMENT must understand about itself *before* any autonomous behavior is authorized.

---

## 13. What this document does NOT authorize

- Implementation of any new mechanism (contest ledger, runtime hook, consultation surface).
- Schema changes to memory storage or governance.
- Changes to `fabric.py`, `governance.py`, `character.py`, `mcp_server.py`, `provenance_v1.py`, `cognition/`, `schemas/`, or any other code file.
- Amendments to Track A v0.1 or Cluster 2 v0.1.
- Promotion of Cluster 5 (storage) as a framing doc.
- Any automation extension.
- Treating §§10.5, 11.3, 12.1 of Cluster 2 v0.1 or §§2.5, 2.6, 10 of this doc as anything more than ratified *vocabulary and routing decisions*. They are not implementation authorizations.
- Bypassing operational discipline (Windows = source of truth; AI is read-only advisor for the TORMENT workspace).

---

## 14. Cross-references

- **Track A v0.1 (doctrinal anchor)** — `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`. Cited throughout: §§3.1 (Mode), 3.2 (Voice), 3.4 (Authority machinery), 6 (voice-audit rule expanded), 7 (three-role ownership), 8.2 (seam to Track B), 9.1 (badge is provenance), 9.3 (source_type stability), 9.6 (material disagreement).
- **Cluster 2 v0.1 (doctrinal anchor)** — `docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md`. Cited throughout: §§7.1 (Authority class vocabulary), 9.1 (visibility contract), 10 (character-authority seam), 10.5 (released-from-agent-scope default), 11.3 (tool_result default), 12 (disagreement primitive doctrinal commitment).
- **Voice Test v0.1 / v0.2 (regression substrate)** — `tests/test_authority_lane_matrix.py`. Do not modify.
- **Track B pre-promotion audit** — `scratch/TRACK_B_DISAGREEMENT_RUNTIME_PRE_PROMOTION_AUDIT_2026_05_20.md`. The substrate inventory.
- **Track B v0.1 / v0.1.1 / v0.1.2 scratch drafts (preserved for lineage)** — `scratch/TRACK_B_DISAGREEMENT_RUNTIME_v0.1_DRAFT_2026_05_20.md`; `scratch/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.1_DRAFT_2026_05_20.md`; `scratch/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.2_DRAFT_2026_05_20.md`.
- **Track B v0.1.1 vs. audit review notes** — `scratch/TRACK_B_V0.1.1_VS_AUDIT_REVIEW_NOTES_2026_05_20.md`.
- **Cluster 2 audit and review-notes lineage** — `scratch/CLUSTER_2_AUTHORITY_GATE_PRE_PROMOTION_AUDIT_2026_05_19.md`; `scratch/CLUSTER_2_V0.2.1_VS_AUDIT_REVIEW_NOTES_2026_05_19.md`.
- **Session checkpoint** — `scratch/CHECKPOINT_2026_05_19_TRACK_A_CLUSTER_2.md` (Track A + Cluster 2 doctrine-chain checkpoint).
- **Hivemind operating guide** — `docs/HIVEMIND_GUIDE.md` (Five Invariants).
- **MCP capability boundary** — `docs/MCP_CAPABILITY_BOUNDARY.md`.
- **Substrate code (read-only references; no modifications by this document):** `cognition/task_models.py:151–183`; `cognition/reintegration.py:155–185`; `schemas/memory_proposal.py:29–69`; `torment_service/conflicts.py:17–67`; `torment_service/closure_memory.py:357–360`; `torment_service/fabric.py:2334–2724`; `torment_service/governance.py:43–200`; `torment_service/migration/gate2_admission.py:78–169`; `torment_service/provenance_v1.py:195–218`; `cognition/recursion_guard.py:82–93, 198–201`.

---

## 15. Ratified decisions and revision history

The items below were open questions or revisions resolved during the path to v0.1. Each is recorded for traceability.

### 15.1 Resolved by v0.1 → v0.1.1 trio ratification (2026-05-20)

The nine ratifications applied in the v0.1.1 scratch revision (which v0.1 inherits):

1. **Working name `ContestRecord` reaffirmed.**
2. **Option C ratified for source-type strategy.** Separate contest ledger is the doctrine-preferred path. Option A deferred to future Track A v0.2 possibility. Option B discouraged.
3. **Cognition `dissent` does NOT auto-trigger contest.** Contest is always explicit. New Invariant 15.
4. **Contest reason required, split into two fields.** `reason_class` required; `contest_reason` optional freeform.
5. **Contest retraction is immutable counter-contest.** No mutation of original record.
6. **`refuse / no-persist` is operator-scope only.** Agent and character self-issued contests cannot route to `refuse`. New Invariant 16.
7. **"True but not mine" — operational meaning ratified.** §2.5.
8. **Character refusal — operational meaning ratified.** §2.6.
9. **Q7 strengthened: contest INCREASES audit visibility.** New Invariant 14.

### 15.2 Resolved by v0.1.1 → v0.1.2 trio polish (2026-05-20)

Four wording / rationale items applied in the v0.1.2 scratch polish (which v0.1 inherits):

1. **§2.4 — `ContestRecord` ledger location clarified.** Wording now specifies "contest-ledger item."
2. **§3.2 bullet 1 — same clarification.** Wording now specifies "first-class contest-ledger item with its own provenance and authority-routing position."
3. **§8 Invariant 7 — cross-reference fixed.** Counter-contest cross-references now point at §10 Q5 and §3.2 immutability (was incorrectly pointing at "Invariant 15-adjacent").
4. **§7.3 — operator-row asymmetry rationale added.** Intentional asymmetry between agent-scope and character-scope operator default behavior is now documented inline.

### 15.3 Resolved at v0.1 promotion (v0.1.2 → v0.1, 2026-05-20)

1. **Promotion to `docs/` — RESOLVED 2026-05-20.** The doctrine ships as `docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md`, version-stamped, following the `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md` and `docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md` pattern. The v0.1, v0.1.1, and v0.1.2 scratch drafts are retained as scratch/local-only lineage; this v0.1 doc is the load-bearing reference.

---

## 16. Status

**Track B v0.1 — Advisory doctrine, ratified by trio (pzychozen + GPT + Claude) on 2026-05-20. No implementation authorized by this document. No code changes. No schema migrations. No tests authorized. Track A v0.1 not amended. Cluster 2 v0.1 not amended.**

Subsequent versions (v0.2, v1.0) require their own trio ratification before they supersede this one. The runtime mechanism for write-time authority contest, when designed, becomes a separate framing-doc effort (Track B v0.2 or a parallel implementation track).

---

## 17. What Track B v0.1 does and does not include

Track B v0.1 is a doctrine doc, not an implementation. It declares the disagreement / contest vocabulary, names the `ContestRecord` shape with required and optional fields, ratifies the source-type strategy (Option C — separate contest ledger), defines the routing table and reason classes, anchors two operational meaning statements ("true but not mine" and character refusal), pins sixteen hard invariants, and records the seven trio-ratified question resolutions. It explicitly does NOT:

- Modify any code in `torment_service/`, `cognition/`, `schemas/`, `tests/`, `start/`, or anywhere else.
- Amend Track A v0.1 or Cluster 2 v0.1 in any section.
- Add any field to `ProvenanceV1` or any other schema. Track B v0.1 introduces the `ContestRecord` shape doctrinally; the field set in §4 is the design surface, not an implementation.
- Implement the contest ledger. That is Track B v0.2 (or a parallel implementation track).
- Implement the runtime consultation mechanism. Same future-track territory.
- Authorize automation, schedulers, offline reflection scheduling, hivemind enabling changes, compression changes, writeback changes, or expanded MCP outbound.
- Allow agent-initiated `refuse / no-persist` contests. Operator-scope only per Invariant 16.
- Allow `contest_scope = workspace` semantics in v0.1. Declared-but-deferred per §6.4.
- Allow `contestant_actor = user` contests. Deferred to Cluster 3 / Track C territory.
- Allow `ContestRecord` mutation. Immutability is structural; reversal is counter-contest per §3.2.
- Allow contest to delete, hide, or down-rank an original memory beyond what the Authority class vocabulary expresses.
- Authorize a regression test (Voice Test v0.3 / Phase 4b) — that is a separate future artifact.

This document IS the Track B v0.1 advisory doctrine. Subsequent versions require their own trio ratification before they supersede this one.

---

*End of Track B v0.1. Advisory doctrine, ratified by trio (pzychozen + GPT + Claude) on 2026-05-20. No further tracks promoted by this document. No implementation authorized by this document.*
