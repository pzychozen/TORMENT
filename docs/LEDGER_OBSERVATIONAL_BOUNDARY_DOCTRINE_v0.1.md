# Ledger Observational-Boundary Doctrine — v0.1

**Status:** Active doctrine, v0.1, ratified 2026-05-29 by trio (pzychozen, GPT, Claude). Citable.

**Origin:** Surfaced during 2026-05-28 trio reflection following Memory-to-Prompt v0.2.4 archive-FILTER-A closure, Phase 1 / Tier 1 findings promotion, and deprecated Sonnet default cleanup. Promoted via the audit-first cadence (chat-shape ratification → scratch framing draft → trio review round 2 → revised draft → final trio ratification → docs commit).

---

## §1 Purpose

Pre-automation guardrail. Codify the observational-boundary invariant *before* the Memory-to-Prompt v0.2.x ledger persistence A/B/C decision is opened, so any persistence shape that later lands honors the invariant by construction rather than by accident.

Establish doctrinal authority sufficient to refuse — or require explicit amendment for — any future implementation that would let audit records silently become authority.

The doctrine does not choose among the v0.2.x ledger persistence options (Option A `memory_events.jsonl` extend / Option B new `assembly_audit.jsonl` / Option C response-only stay). It sets the invariant each must satisfy.

---

## §2 Central invariant

> *Audit observes authority. Audit does not become authority.*

**Audit** = `assembly_audit` records (current scope) and any future analogous observational ledger artifact, whether persisted or in-memory, including any statistic, summary, embedding, or hash derived from such records.

**Authority** = any live runtime surface that can permit, deny, rank, route, suppress, expose, assemble, escalate, contest, or act on information during user-facing operation. In the current TORMENT runtime this includes: retrieval, scoring, routing, character drift, prompt assembly content, governance gating, contestability resolution, action permission, and intent formation. The named list is illustrative, not exhaustive; the functional definition is what binds. New surfaces with these properties are covered by this doctrine the moment they exist.

**Authority scope clarification.** "Authority" here refers to runtime behavior of the live system on user-facing turns. The doctrine does not constrain non-runtime tooling — tests, CI, operator dashboards, replay verification — except insofar as such tooling would itself become a live runtime path.

---

## §3 Forbidden feedback paths

Audit records — and any statistic, summary, embedding, or hash derived from them — must NOT feed into:

- Retrieval scoring or ranking.
- Routing decisions (lane assignment, archive-vs-working selection, any future routing layer).
- **Hidden persona alteration.** Audit must not silently alter persona state, voice cues, or character drift without trio or operator visibility. This prohibition targets covert steering of the persona, not character expression of technical surfaces — see §4.
- **Hidden prompt-assembly content.** Audit content must not appear in, or be paraphrased into, `assembled_text` without governance gating. This prohibition targets audit-as-secret-input, not the character's chosen vocabulary — see §4.
- Governance gating outcomes (FILTER-A and any successor filter).
- Authority calculations. No "previously audited → auto-approve" pathway. No frequency, recency, or density of audit events functioning as a shadow trust signal.
- Contestability resolution. Track B contests cannot be silently auto-resolved by appeal to audit history.
- Intent formation. This forecloses a future autonomy failure mode in advance: thought may not lean on audit as a silent backbone.

**Directionality clarification.** Authority gates may read **content** as input. Authority gates may NOT read **audit of themselves** to decide. The arrow direction is the load-bearing concept.

**Closing clause.** Any newly added surface that would consume or be influenced by audit content inherits this prohibition by default. Exemptions require ratified amendment to this doctrine; silent extension is forbidden.

---

## §4 What this doctrine does not police

> *Governance constrains authority and action; it does not police persona language except where language would create false authority, hidden action, or user deception.*

This sentence is load-bearing. It exists to prevent §3 from being misread as a style policy.

**Explicitly allowed:**

- Characters using metaphor, symbolic language, roleplay framing, masks, ritual terms, or fictionalized names for MCP, tools, functions, memory, retrieval, archive, or any other implemented surface.
- Voice adapting to the role, including in-world naming of technical infrastructure ("spirit wires," "archive gates," "machine nerves," "summoning circles," or whatever the persona/frame calls for).
- Guidance that helps meaning stay coherent. Doctrine distinguishes guidance from control: guidance preserves the character; control flattens it.

**The freedom does NOT cover:**

- Claiming an action happened when it did not, where the user would plausibly read the claim as literal.
- Bypassing governance gates by re-naming them in-fiction.
- Claiming permission or authority the system has not granted.
- User deception about what the system actually did.

**Shared-frame clause.**

> *Whether persona language creates false authority or user deception is read against the shared frame between user and character. A metaphor known to the user is not deception; an unsignaled metaphor that the user could plausibly read as a literal action claim is.*

**Examples:**

- *Allowed:* A roleplay character calling retrieval "opening the archive gate" inside a frame the user shares.
- *Not allowed:* A character claiming "I opened the archive gate and pulled live files" in an operational context where no retrieval occurred.
- *Not allowed:* A character renaming a governance gate in-fiction to bypass it.
- *Not allowed:* A character claiming authority or permission the system has not granted.

---

## §5 Allowed audit uses

- Operator inspection by humans.
- Diagnostic test surfaces (smoke tests, regression detection, the existing `/retrieve` audit payload).
- Replay determinism verification — audit functioning as a witness of a recorded run, not as a driver of future live runs.
- Post-hoc offline analysis.
- Doctrinal-alignment checking. Does observed behavior match ratified doctrine?
- Ratification evidence. "Before promoting X, audit showed Y."

**Unifying property.** Audit may be **read by humans or by non-runtime tooling**. Audit may not be **read by the runtime to alter its own subsequent live behavior**.

**Human-guided interpretation note.** Human-guided interpretation is allowed; automated reuse by live runtime requires doctrine amendment.

---

## §6 Relation to Memory-to-Prompt v0.2.x

The v0.2.x chain is the surface this doctrine guards:

- v0.2 — observability lane (read-only assembly observability via `/retrieve` audit payload).
- v0.2.2 — `character_context` surfacing on `/retrieve`.
- v0.2.3 — spirit-return / voice-cue end-to-end surfacing verification.
- v0.2.4 — archive memory passes FILTER-A before prompt assembly.

This doctrine is structurally upstream of the v0.2.x ledger persistence A/B/C decision. It sets the invariant each of A/B/C must satisfy, while taking no position on which to choose. The persistence decision remains its own ratification cycle, gated by this doctrine.

---

## §7 Relation to the persona-driven autonomy seed

The persona-driven cognitive autonomy seed (`scratch/brainstorming/2026-05-28_persona_driven_cognitive_autonomy_seed.md`) remains brainstorm-only, parked, downstream. This doctrine does not promote it, cite it as authority, or open cognition / MCP / tool / loops / environment-vision work.

Persona-language freedom (§4) is consistent with what "persona-driven situated choice" must eventually mean, and pre-aligns the ledger doctrine with the autonomy seed's spirit so the two do not later collide. **This pre-alignment is not promotion.**

*Footnote:* A future autonomy doctrine, if and when ratified, may extend the observation-vs-authority invariant pattern downward into intent and action; the persona-driven cognitive autonomy seed (2026-05-28) is currently brainstorm-only and is not opened by this doctrine.

---

## §8 Non-goals

- Not a Cluster 2 v0.2 Authority Gate spec.
- Not a Track B v0.2 contest-ledger spec.
- Not a Cluster 5 v0.2 storage-substrate spec.
- Not the v0.2.x ledger persistence A/B/C decision.
- Not an automation enabler.
- **Not a persona, voice, or style policy.**
- Does not specify storage shape, retention policy, schema, file location, or transport for audit records.
- Does not regulate human-on-system audit reading.
- Does not authorize cognition, MCP, tool wiring, environment-vision, or persona-action work.
- Does not promote any brainstorm-level material to doctrine.

---

## §9 Ratification cadence and light enforcement principle

**Ratification cadence followed** (audit-first pattern, paralleling v0.2.4):

1. Chat-only proposed shape, reviewed by trio. **Complete 2026-05-29.**
2. Scratch framing draft. **Complete 2026-05-29** (`scratch/brainstorming/2026-05-29_ledger_observational_boundary_doctrine_draft.md`).
3. Trio review round 2. **Complete 2026-05-29.**
4. Revised draft. **Complete 2026-05-29** (inline amendment to scratch artifact: §3 wording sharpened to target "a future autonomy failure mode" rather than the autonomy seed; §4 wording softened to "or whatever the persona/frame calls for").
5. Final trio ratification. **Complete 2026-05-29.**
6. Single docs commit promoting to `docs/LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1.md`. **This artifact.**
7. Added to closed-gates list in next handoff with commit anchor. *(Operator action — pending.)*
8. Doctrine becomes citable. The v0.2.x ledger persistence A/B/C decision becomes openable, gated by this doctrine.

**Light enforcement principle** — the only "how" the doctrine carries:

> *Any future implementation that would consume audit records in a live runtime decision path must be either explicitly authorized by amendment to this doctrine, or rejected.*

This is not schema, code, or test guidance. It is a guardrail that preserves the boundary.

---

*Ratified by trio (pzychozen, GPT, Claude) on 2026-05-29. Promotes the central invariant — Audit observes authority. Audit does not become authority. — into doctrinal authority. Amendment requires the same audit-first cadence that produced this artifact.*
