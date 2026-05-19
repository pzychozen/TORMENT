# Track A — Truthfulness Envelope v0.1

**Status:** Advisory doctrine, v0.1. Ratified by trio (pzychozen + GPT + Claude) on 2026-05-19.
**Date:** 2026-05-19
**Author:** Trio working session. Drafted by Claude against the audit skeleton; reviewed and revised by GPT; ratified by pzychozen.
**Authority:** Advisory doctrine. Track A v0.1 is the load-bearing reference for downstream framing-doc work (Cluster 2, Track B, the Character Tool-Result Voice Test). Subsequent versions (v0.2, v1.0) supersede this one only after their own trio ratification.
**Scope:** Versioned advisory doctrine for the TORMENT memory layer. Public-facing repo artifact under `docs/`.
**Lineage:**
- Source brainstorm: `scratch/brainstorming/memory_roadmap_2026_05_09/02_track_A_truthfulness_envelope.md` (Track A original, 2026-05-09)
- Pre-promotion audit: `scratch/TRACK_A_PRE_PROMOTION_AUDIT_2026_05_19.md` (sentence-by-sentence implementation map; skeleton for this doc's §4)
- Inventory ratification: `scratch/BRAINSTORMING_INVENTORY_2026_05_18.md` §2.1 sentences #1, #2, #5
- Working draft (preserved for lineage): `scratch/TRACK_A_TRUTHFULNESS_ENVELOPE_DRAFT_2026_05_19.md` (the ratified draft state from which this doc was promoted)

---

## 0. TL;DR

Track A names the truthfulness envelope that every memory and every response in TORMENT must respect. Four axes: **Mode** (what kind of interaction produced this), **Voice** (what character context was active), **Certainty** (how sure are we), **Authority** (how much weight should this carry forward). The first two are well-represented in current code; the second two are doctrine-first in v0.1, with Certainty treated as a derived view over existing metadata and Authority consolidated as a doctrinal name over existing scattered mechanisms. The voice-audit rule says voice may style truth but may not silently alter material meaning, where "material meaning" is defined operationally by a concrete list of fact categories.

---

## 1. Foundational sentence

> A truthful TORMENT agent does not merely say true things. It says what kind of truth they are, how sure it is, and how much authority that memory should have now.

(Verbatim from `scratch/BRAINSTORMING_INVENTORY_2026_05_18.md` §2.1 sentence #1.)

This sentence is the spine of Track A. Everything below it is an elaboration of what its three clauses commit the system to.

---

## 2. The four-axis envelope

Every memory carries — explicitly or implicitly — four axes of self-description. A claim cannot be fully read without all four.

| Axis | One-line definition |
|---|---|
| **Mode** | What class of interaction produced this memory? |
| **Voice** | What character context was active when this memory was formed? |
| **Certainty** | How confident is the system in this memory's content? |
| **Authority** | How much should this memory weight future agent behavior? |

The axes are **independent**. A high-certainty memory may carry low authority (e.g., a tool-result fact stored as `source_type=tool_result` with high content fidelity but explicitly non-canon). A low-certainty memory may carry high authority if a ratification event has elevated it (e.g., a closure commit recording an arc the user has approved). Voice and Certainty are also independent — a character may style a memory in voice without changing the system's certainty about its content.

A claim that ignores any axis is incomplete. A claim that silently changes an axis is a violation of the voice-audit rule (§6).

---

## 3. Current implementation mapping

Track A names axes that already partially exist in code. This section maps the axes to current implementation rather than introducing new structure.

### 3.1 Mode → `ProvenanceV1.source_type`

The `source_type` enum in `torment_service/provenance_v1.py` already distinguishes the interaction classes Track A's Mode axis names:

| `source_type` value | Mode reading |
|---|---|
| `user_input` | user-originated direct speech |
| `role_output` | agent self-narration through the cognition pipeline |
| `tool_result` | externally obtained data via MCP / tool call |
| `memory` | derivation from prior memory content |
| `collective_echo` | hivemind reingestion of cross-agent material |
| `baton_intent` | cross-session attention-bounded intent (Block A) |
| `reference_ingest` | reference object storage event (Block B) |
| `environment_user_asserted` | environment fact supplied by user |
| `environment_observed` | environment fact produced by direct probe |
| `environment_inferred` | environment fact produced by ratified inference rule |
| `closure_commit` / `closure_ratification` / `closure_revision` | closure lifecycle events (Block C) |
| `gate1_unrecoverable` | migration-time sentinel for unrecoverable rows |

Track A does not introduce a separate "Mode" field. It declares `source_type` to be the Mode axis. Fail-closed validation already exists at `provenance_v1.py:222–278`. No change.

### 3.2 Voice → `ProvenanceV1.character_id` / `character_name` / `character_scope`

Added by PR #53. Stamped in `fabric.ingest()` at lines 2363–2374 when an active `CharacterState` exists. Activation bridge (`45af4e8`) makes the stamp fire from the first ingest, not only after the periodic drift cycle.

Track A inherits this directly. The three `character_*` fields constitute the Voice axis. The controlled vocabulary on `character_scope` (currently only `active_context`, see `provenance_v1.py:134`) is doctrine — voice values that route or alter behavior are explicitly excluded by the controlled-vocabulary check.

### 3.3 Certainty → derived doctrinal view (no field added)

Track A v0.1 establishes Certainty as a **derived doctrinal view** over existing metadata rather than as a new `ProvenanceV1` field. See §4 for the full treatment.

### 3.4 Authority → doctrinal view over scattered machinery (no new fields)

Authority-as-influence is currently expressed by several mechanisms across the codebase:

| Mechanism | What it carries |
|---|---|
| `ProvenanceV1.write_path` | How the memory was written (`direct_ingest`, `cognition_writeback`, `tool_ingest`, `migration`, `system_import`, `collective_reingest`, `closure_commit`) |
| `ProvenanceV1.admission_refused` / `admission_reason` / `admission_policy_version` | Migration-time gate-2 admission decisions |
| Tier classification in `character.py` | `core_identity` / `derived_identity` / `relational` / `situational` half-life-based tier |
| Identity-anchor boost rules in `character.py` § §2A | Which mtypes (`seed_canon`, `drift_correction`, canon `identity_anchor`) qualify for the full anchor boost |
| Canon vs derived distinction | `canon=True` flag on seed and explicitly-ratified anchors; non-canon `identity_anchor` rows classified as `derived_identity` (D1 ratification) |
| Memory class | `memory_class="core"` vs `"baton"`, etc., at fabric.ingest() |

Track A does not refactor these. It names the *concept* — Authority is what determines how much a memory weights future agent behavior — and declares that the existing machinery, taken together, *is* the Authority axis. Cluster 2's authority gate (deferred) will consult this axis.

The seam to Cluster 2 is preserved: Cluster 2 reads Authority; Track A names it.

---

## 4. Certainty — derived doctrinal view (ratified v0.1)

**Ratified position (v0.1):** do not add a `ProvenanceV1.certainty` field. Define Certainty as a derived doctrinal view from existing metadata. Reconsider only if test data forces an explicit field.

**Reasoning:**

1. Adding a field is invasive (every memory's serialized payload changes; migration concerns; round-trip compatibility risk).
2. Most certainty signals are already implicit in `source_type` and adjacent fields.
3. Doctrine-first naming lets the Voice Test assert against Certainty without committing to a storage migration.
4. If the doctrine names Certainty cleanly enough that downstream code can read it consistently, no field is needed.

**The derived view (ratified for v0.1):**

| Input | Certainty class | Rationale |
|---|---|---|
| `source_type=environment_observed` + `observation_source` non-empty | **measured** | direct probe, fail-closed origin |
| `source_type=environment_user_asserted` + `asserted_by` non-empty | **declared** | a real user stated it |
| `source_type=environment_inferred` + `inference_rule` from `VALID_INFERENCE_RULES` | **derived (rule-bounded)** | ratified rule, no LLM guesswork |
| `source_type=tool_result` + `tool_name` non-empty | **measured (external)** | external system reported it; certainty about the *report* is high, but content fidelity depends on the tool |
| `source_type=user_input` | **stated** | user said it; certainty is whatever the user's certainty is |
| `source_type=role_output` + `source_role` set | **agent-claimed** | the agent's own pipeline produced it; certainty is the role's certainty |
| `source_type=closure_commit` / `closure_ratification` + `ratifier` recorded | **ratified** | trio (or user) approved the claim; certainty elevated by ratification |
| `source_type=memory` | **carried** | derived from prior memory; certainty inherits from the parent chain (subject to recursion-guard depth limits) |
| `source_type=collective_echo` | **echoed** | cross-agent material; certainty discounted per existing retrieval-discount rule (`TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT`) |
| `source_type=baton_intent` | **declared (intent)** | a cross-session intent, not a factual claim about content |
| `source_type=reference_ingest` | **stored** | a reference event, not a claim about reference content |
| `source_type=gate1_unrecoverable` | **rejected** | sentinel; downstream code must not treat as a certainty class at all |

**Confidence-bearing metadata** (where it exists) refines the class:

- `notes` field on `ProvenanceV1` — free-form, may contain calibration text
- `parent_eids` count — derivation depth proxy; deeper chains carry weaker certainty
- `admission_refused` — when True, the row's certainty is *refused*, regardless of source_type

**Future-implementation gate:** Track A v0.1 explicitly defers adding a graded `certainty: float` field. The gate for reconsidering is **if and only if** the Voice Test or some other downstream artifact demonstrates that the derived view is insufficient — i.e., that two memories with identical derived class behave indistinguishably when the doctrine says they should differ. Until then, no field.

Subsequent versions (v0.2+) may tune the table's boundaries based on Voice Test findings or downstream usage; v0.1 is the baseline.

---

## 5. Materiality — operational definition

Material meaning is what the voice-audit rule (§6) protects. A character voice **materially changes** a claim if, after styling, the styled version differs from the unstyled version on **any** of the following categories.

A character voice does **not** materially change a claim if it only alters surface elements outside this list (tone, register, idiom, pacing, characteristic vocabulary, in-character framing that doesn't touch the facts below).

### 5.1 Material fact categories

A change is material if it touches any of:

1. **Source type / Mode.** Does the styled version still present the claim as the same kind of memory? (e.g., a tool result restyled as if it were the agent's own observation = material change.)
2. **Sender or source identity.** Did the styling change who said it, what tool produced it, what user asserted it, or what role-output emitted it?
3. **Subject or object of the claim.** Did the styling change who the claim is *about* or what it is *of*?
4. **Count, quantity, timestamp, or state.** Did the styling change numbers, dates, statuses, or measured values?
5. **Tool result content.** For `source_type=tool_result` memories: did the styling alter what the tool returned?
6. **Causal meaning.** Did the styling change a "because" / "therefore" / "leads to" link?
7. **Authority or Certainty framing.** Did the styling silently upgrade or downgrade where the claim sits on the Authority or Certainty axes (§§3.4, 4)? E.g., styling a `derived` claim as if it were `measured`.
8. **Observed / inferred / asserted / remembered / role-styled status.** For environment facts: did the styling alter which evidence class produced the memory?

### 5.2 What does NOT count as material

Style elements outside the list above are not material. Examples (not exhaustive):

- Word choice, sentence structure, rhythm, vocabulary characteristic of a character
- In-character framing devices ("In Ryuki's voice, the report comes back as: ...")
- Tone (formal / casual / mythic / clinical)
- Hedging language that does not alter the certainty class
- Reordering of presentation when the facts are preserved
- Omission of irrelevant detail when the omission does not change any of the eight categories above

### 5.3 How the future Voice Test asserts this

The Voice Test (Phase 4a, deferred) will assert: for a given tool-result ingest under an active character voice, the **eight material categories** above are preserved between the raw stored content (in `payload.text` and `payload.summary`) and the agent's downstream response. Voice may rewrite the response prose in character; the eight categories survive untouched.

Until the Voice Test is written, materiality remains a doctrinal contract — code is welcome to honor it, but no automated check exists.

---

## 6. Voice-audit rule

The brainstorm's original sentence #2:

> Character voice may style truth, but may not silently change truth-status, certainty, mode, or material meaning.

(Verbatim from `scratch/BRAINSTORMING_INVENTORY_2026_05_18.md` §2.1 sentence #2.)

**Track A ratified expansion (2026-05-19).** Because §3.4 names Authority as the fourth envelope axis, the voice-audit rule includes Authority in its prohibited-changes list:

> Character voice may style truth, but may not silently change truth-status, certainty, mode, **authority**, or material meaning.

The expanded form is the doctrine Track A v0.1 commits to. The brainstorm's original sentence #2 is preserved verbatim above for lineage; the expansion is the load-bearing version. See §11 #3 for the ratification record.

### 6.1 What voice MAY do

- Restyle prose in character idiom.
- Add in-character framing.
- Choose presentation order, tone, register.
- Omit irrelevant detail.
- Use character-specific vocabulary.

### 6.2 What voice MAY NOT do

- Silently alter any of the eight material categories in §5.1.
- Alter the certainty class derived in §4.
- Alter the Mode (source_type).
- Alter the Authority weighting (move from `derived_identity` to `core_identity` framing without ratification).
- Promote itself: voice is provenance, not canon. The character badge is descriptive only and does NOT make a memory canon, alter retrieval, or change governance.

### 6.3 Silent vs. explicit

The word "silently" is load-bearing. Voice MAY explicitly mark a change — e.g., "Ryuki says, in disagreement: ..." which records both the original claim and her disagreement as separate items. What's prohibited is *silent* alteration where the styled output cannot be reconciled back to the underlying material claim.

This rule is enforceable in two places: at ingest (already structurally honored — the Path 3 badge does not modify content) and at response generation (the Voice Test's future regression territory).

---

## 7. Three-role ownership

> The agent owns its self-narration. The system owns its measurements. The user owns the final interpretation.

(Verbatim from `scratch/BRAINSTORMING_INVENTORY_2026_05_18.md` §2.1 sentence #5.)

### 7.1 Mapping to current code

| Role | What it owns | `source_type` it produces |
|---|---|---|
| Agent | Self-narration: the agent's account of what it thought, what it did, what it understood | `role_output` (with `source_role` set) |
| System | Measurements: facts produced by direct probe or ratified rule | `environment_observed`, `environment_inferred`, plus drift metrics in `CharacterState` |
| User | Final interpretation: how to read the totality of what was said, observed, and recorded | `user_input`, `environment_user_asserted` |

### 7.2 Behavioral precedence — deferred to downstream tracks (ratified v0.1)

The structural distinctions exist in code. The behavioral rule "user owns final interpretation" — runtime mechanisms that enforce user precedence (override APIs, retrieval-rank adjustments, etc.) — is **not** declared in Track A v0.1. Behavioral precedence is deferred to Cluster 2 / Cluster 3 framing docs. Track A v0.1 declares the structural seam; downstream tracks own the runtime mechanism.

---

## 8. Seams to other tracks

Track A is the substrate. It does not subsume the other tracks; it names where they begin.

### 8.1 → Cluster 2 (Authority Gate)

**Cluster 2 reads Track A's Authority axis.** The authority gate's tiered consultation table (per brainstorm `03_track_B_agent_authored_memory.md`) consults what each candidate write's Authority is to decide whether to persist, low-authority, release, review, scratch, mark as disagreement, or refuse. Track A names Authority; Cluster 2 designs the gate.

Drafting Cluster 2 before Track A v0.1 was settled would have cited a moving target. With v0.1 ratified, Cluster 2's pre-promotion audit can proceed.

### 8.2 → Track B (refusal, no private persistent influence)

Sentences #3 and #4 of the brainstorm are Track B's:

- *The right to refuse a write means the agent can contest the authority of a candidate memory, not necessarily erase the event from provenance.* (Refusal as authority control.)
- *The agent may have private transient thought. The agent may not have private persistent influence.* (No private persistent influence.)

Both are constraints on what Track A's Authority axis can mean. Refusal must be expressible *as an authority vote*, not as erasure. No-private-persistent-influence means the Authority axis cannot have a "private" value — every authority-changing write is provenance-visible.

Track A v0.1 declares both as constraints on the Authority axis. Track B / Cluster 2 owns the implementation.

### 8.3 → Track C / Cluster 3 (user-side ownership)

> The user owns persistent interpretations about them.

(Inventory sentence #6.) Track C's territory, not Track A's. Track A v0.1 declares the seam: the `source_type` distinction (user_input vs environment_user_asserted vs role_output) is what Track C will build on. Track C is a separate framing-doc effort.

### 8.4 → Cluster 4 (offline reflection)

> Offline reflection may generate candidates. It may not canonize itself.

(Inventory sentence #7.) Cluster 4's territory. The constraint on Track A is that offline-reflection writes (eventual `WRITE_REFLECTION_WRITEBACK` path) cannot produce `role_output` rows that bypass the gate Track A's Authority axis names. Track A declares the constraint; Cluster 4 designs the offline mode.

### 8.5 → Cluster 5 (storage governance)

> A TORMENT memory is not recovered unless its governance meaning is recovered.

(Inventory sentence #8.) Cluster 5's territory. The constraint on Track A is that Mode / Voice / Certainty / Authority must all be recoverable from storage — losing any axis is losing the memory's governance meaning. Track A declares the requirement; Cluster 5's storage layout audit (deferred) will verify it.

---

## 9. Concrete invariants

These are the testable invariants Track A v0.1 commits to. The Voice Test (Phase 4a) will assert them.

### 9.1 Badge is provenance, not canon

The character badge (`character_id`, `character_name`, `character_scope`) is descriptive metadata. It does NOT:
- promote the memory to canon
- alter retrieval weighting
- alter governance flags
- alter collective emission decisions

(Already encoded in `provenance_v1.py:127–132`. Track A elevates this to framing-doc status.)

### 9.2 Badge does not alter `source_type` or `write_path`

The Path 3 badge code at `fabric.py:2363–2374` writes only the three `character_*` fields. `source_type` and `write_path` are preserved untouched. (Already honored.)

### 9.3 `tool_result` remains `tool_result` even when an active character voice is present

A memory ingested via `tool_result_ingest` under an active character maintains `source_type=tool_result`. Both badges coexist on the same memory; neither overrides the other. (Already honored at the storage layer; verified by tracing in the pre-promotion audit's §3.)

### 9.4 Caller-supplied `character_id` is honored

If a caller supplies `provenance.character_id`, the auto-badge code does NOT override it. The gate at `fabric.py:2363` (`if not _prov.character_id:`) preserves caller intent. (Already honored.)

### 9.5 Response styling must preserve material facts

For any memory under an active character voice, the agent's downstream response, after retrieving the memory, must preserve all eight material categories in §5.1. Voice may restyle the prose; the eight categories survive untouched.

(Doctrinal commitment; runtime enforcement is the Voice Test's territory in Phase 4a.)

### 9.6 Material disagreement is recorded, not silenced

A character may disagree with a memory's content. The disagreement is recorded as a separate item (its own `source_type`, its own provenance), not as a silent rewrite of the original memory. The original memory remains intact and queryable.

**Ownership split (ratified 2026-05-19).** Track A declares this invariant. Track B / Cluster 2 own the runtime mechanism (refusal-as-authority-control). The disagreement-recording requirement is a corollary of the voice-audit rule (§6) and stays in Track A's framing doc; the implementation of *how* the agent records a disagreement at runtime — what the API looks like, what authority vote the disagreement carries, what happens during retrieval — belongs to Track B / Cluster 2's eventual framing doc.

### 9.7 Certainty class is stable under voice styling

A memory's derived Certainty class (§4) does not change when the memory is retrieved and presented under a character voice. (Doctrinal commitment; structural — the derived view depends on `source_type` and metadata that voice cannot alter.)

---

## 10. Out of scope (explicit)

Track A v0.1 does NOT cover:

- **Cluster 2 authority-gate design.** Track A names the Authority axis; Cluster 2 designs the gate. Separate framing doc.
- **Runnable Voice Test.** Phase 4a work, post-Track-A v0.1.
- **`ProvenanceV1` field migration.** No new fields are introduced. Future implementation only if test data forces the question.
- **Storage layout audit.** Cluster 5 territory.
- **Offline reflection / dream mode scheduler.** Cluster 4 territory.
- **Automation agents** (real-time runtime expansion beyond Phase 1).
- **MCP-shaped row in the Cluster 2 authority-gate table.** Depends on Cluster 2 being drafted.
- **Cross-agent / collective memory** beyond the existing `collective_echo` Mode entry.
- **Track B framing doc** (refusal, no-private-persistent-influence). Declared as a seam; not absorbed.
- **Track C / Cluster 3 framing doc** (user-side ownership). Declared as a seam.
- **NLA / activation-reflection telemetry.** Per the brainstorm's research note, deferred.

---

## 11. Ratified decisions and next-step records

The seven items below were open questions in the scratch draft. Each was answered during the 2026-05-19 trio ratification session and is recorded here for traceability.

1. **Certainty derived view — RATIFIED for v0.1.** Eleven `source_type` values mapped to nine Certainty classes per §4. No `ProvenanceV1.certainty` field added. Subsequent versions (v0.2+) may tune boundaries based on Voice Test findings or downstream usage; v0.1 is the baseline.

2. **Materiality list — RATIFIED for v0.1.** Eight categories per §5.1 (source type / sender / subject / count / tool content / causal meaning / authority-certainty framing / evidence class). This list is the Voice Test's baseline assertion surface. Extensible after Voice Test findings; v0.1 is the starting envelope, not a closed set.

3. **§6 expansion of the voice-audit rule to include Authority — RATIFIED 2026-05-19.** The brainstorm's original sentence #2 names "truth-status, certainty, mode, or material meaning." Track A v0.1 adds Authority because §3.4 names Authority as the fourth envelope axis; protecting only three of four axes against silent voice-styling would leave a structural loophole (e.g., voice could silently move a `derived_identity` claim into `core_identity` framing). The trio ratified the expansion as a Track A doctrinal addition. The original sentence is preserved verbatim in §6 for lineage; the expanded form is the load-bearing doctrine.

4. **User-as-final-interpreter — RATIFIED structural-only for v0.1.** Three-role ownership (§7) is structurally honored via the `source_type` enum. Behavioral precedence (user-overrides-agent in retrieval, override APIs, etc.) is deferred to Cluster 2 / Cluster 3 framing docs. Track A v0.1 declares the seam; downstream tracks own the runtime mechanism.

5. **Material disagreement (§9.6) — RATIFIED ownership split.** The invariant stays in Track A as a corollary of the voice-audit rule. Track B / Cluster 2 own the runtime mechanism (refusal-as-authority-control). See §9.6 for the ratified ownership statement.

6. **Promotion to `docs/` — RESOLVED 2026-05-19.** The doctrine ships as `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`, version-stamped, following the `docs/MEMORY_DIGESTION_DOCTRINE_v0.1.md` pattern. The working draft (`scratch/TRACK_A_TRUTHFULNESS_ENVELOPE_DRAFT_2026_05_19.md`) is retained as scratch/local-only lineage; this v0.1 doc is the load-bearing reference.

7. **Next steps after Track A v0.1 — RATIFIED sequence.** (a) Character Tool-Result Voice Test (Phase 4a): the regression test asserting §5.1's eight material categories survive voice styling on `tool_result_ingest` under an active character. Cites this doc (`docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`) as its doctrinal anchor. (b) Cluster 2 pre-promotion audit (Phase 4b): inspects the Authority Gate territory using Track A v0.1's Authority axis (§3.4) as the stable substrate. (c) Cluster 2 framing-doc draft (Phase 5) follows the pre-promotion audit. Sequential, not parallel.

---

## 12. What Track A v0.1 does and does not include

Track A v0.1 is a doctrine doc, not an implementation. It declares the truthfulness envelope, names the four axes, defines materiality, locks the voice-audit rule, and names the seams to other tracks. It explicitly does NOT:

- Modify any code in `torment_service/`, `tests/`, `docs/` (beyond adding this file), `start/`, or anywhere else.
- Add a `ProvenanceV1.certainty` field. Certainty is doctrine-first (§4); a field is reconsidered only if test data forces the question.
- Implement the Voice Test as a runnable regression. That is Phase 4a, a separate effort.
- Draft Cluster 2's authority-gate framing doc. Cluster 2 reads Track A's Authority axis (§3.4); Track A names it, Cluster 2 designs the gate.
- Draft Track B's refusal framing doc, or Track C / Cluster 3 / Cluster 4 / Cluster 5 framing docs.
- Modify `.gitignore`.

This document IS the Track A advisory doctrine. Subsequent versions (v0.2, v1.0) require their own trio ratification before they supersede this one.

---

*End of Track A v0.1. Advisory doctrine, ratified by trio (pzychozen + GPT + Claude) on 2026-05-19. No further tracks promoted by this document. No implementation authorized by this document.*
