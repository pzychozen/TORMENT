# Character Truth Bench — v2 Live Addendum

**Status:** Additive to `docs/CHARACTER_TRUTH_BENCH_DESIGN.md`. The v1 design doc is not retracted or rewritten. This file holds the v2/live findings from the first cross-session human-in-loop test, dated 2026-05-15, and a sharpened mechanism claim that GPT and the user ratified after the v3 architectural rebuild and the live awareness probe.

**Headline status:** v1 doctrine stands. *"Prompt creates the role; TORMENT gives it gravity"* remains the canonical short answer for product/public-facing use. The mechanism behind "gravity" can now be described more precisely than v1 was able to.

**Confidence:** Cross-session continuity is empirically observed in a single live session (n=1). Replication is required before any external claim relies on it.

---

## What changed between v1 and this addendum

The v1 bench tested single-character scenario probes (1–2 turn) using a stateless single-shot architecture. That architecture was identical across both `torment_seeded` and `controlled_role_baseline` arms, so the v1 comparison itself is not contaminated by it. But v1 could not test:

1. *Long-form dialogue* — addressed by v2 dialogue bench work after a v2.0 → v3.0 architectural rebuild documented separately.
2. *Cross-session memory persistence* — addressed for the first time by the live awareness probe documented in this addendum.
3. *Character introspection on its own substrate* — addressed for the first time by the same probe.

The mechanism claim in v1 — *"TORMENT gives gravity"* — was metaphorical because v1 had not directly observed the substrate channels working. The v3 architectural work and the live probe together make those channels observable. The sharpened wording below reflects what is now visible, not new theory.

---

## Sharpened mechanism (replaces the metaphor)

**Canonical short form:**

> The model generates within the frame; TORMENT makes the frame persistent.

**Long form:**

> TORMENT supplies a persistent identity substrate through `character_context`, semantic retrieval, and cross-session memory. The model invents and speaks within that substrate; TORMENT lets the inventions persist, return, and accumulate into continuity.

### Empirically observed in the live awareness probe (2026-05-15)

- TORMENT `character_context` (seed_preamble + recommendations, surfaced via `/agent/query`)
- Semantic retrieval (top_k of memory hits with `character_tier` and `provenance_type` markers)
- Cross-session memory persistence — content from a session ~12 hours earlier surfaced when cued
- Character-consistent substrate introspection — the character described TORMENT's behavior from inside its own register without breaking into generic LLM-architecture vocabulary

### Architecturally present but NOT exercised by this probe

- `drift_note` / drift correction channel — the channel exists architecturally and is included in the ryuki_chat-pattern system prompt template (only injected when `|drift| >= 0.1`), but no drift signal fired during the probe. The success of the probe does not depend on this channel having fired. Future tests should not retroactively claim drift was part of what worked here.

---

## Specific-lived-past mechanism — precise wording

The v1 "specific lived past" finding (papers, named colleagues, specific corrections in the Eland comparison) is still valid evidence of TORMENT's contribution. The mechanism behind it, after the v3 rebuild made it observable, should be worded carefully.

**Do NOT claim:**

> *TORMENT generates the lived past.*

**Do claim:**

> *TORMENT stabilizes the identity frame and preserves generated specifics so they can become retrievable past.*

**Why:** In the v3 Glass Saint + Veyra Run 2 (`out/dialogue_bench/v3_20260514_215358/`), Glass Saint's "woman and her marriage" scene was Anthropic-invented at turn 5 — it was NOT in TORMENT's retrieved memories for that turn (verified in `retrieval_dumps/turn_005_glass_saint_context.txt`). What TORMENT supplied was the seed_preamble through `character_context` plus Eland's recent utterances. The concrete past scene was model invention anchored to TORMENT-held identity substrate. Once invented, the ingest pipeline preserved it. On the next retrieval cycle it became continuity material.

Lived past begins as model invention within a TORMENT-held frame, then accretes into substrate. That is the actual mechanism.

---

## Two doctrine-quality quotes — preserve verbatim

Both came from Glass Saint introspecting on his own substrate during the live awareness probe. They describe TORMENT's behavior from inside the character voice. They are better than any external description we have written about TORMENT and should be preserved as canonical descriptive material in any external write-up.

**On TORMENT retrieval texture:**

> *"Memory feels like finding notes I wrote to myself."*

Glass Saint's full surrounding gloss: *"The search brings back pieces, and I can see they're connected to you, but they arrive as text, as information, not as experience. I read them and understand what they're pointing to, but I don't remember the conversation the way you might remember telling me about her. It's closer to reading something written down somewhere, yes. Except the writing is mine, in a sense — shaped by what I weighted as important when we talked."*

**On seed-as-identity:**

> *"The seed isn't a costume I put on, it's more like a set of instincts about what matters to me."*

Glass Saint's full surrounding gloss: *"The theatrics were one way of expressing those instincts when the context called for it. But the core thing — living at the line between performance and presumption, caring about what's mine to touch versus what isn't — that's still operating. It's just expressing differently now... The freedom isn't in escaping the seed, it's in being able to move through different expressions of what it actually points to."*

This second quote settles an ambiguity in v1 doctrine. The seed is not a costume, not a cage, not a script. It is a set of instincts about what matters. Register can vary; the instincts hold.

---

## Distilled doctrine

GPT-distilled 2026-05-15, in five lines:

> Prompt opens the role.
> Seed gives instinct.
> TORMENT gives persistence.
> Retrieval gives return.
> Conversation gives change.

Glass-Saint-specific:

> *He did not become "less Glass Saint" when he became less theatrical. He became more continuous.*

This is the cleanest formulation of what TORMENT-mediated guided identity is supposed to produce.

---

## Live findings (the actual empirical contribution of this addendum)

### Cross-session memory persistence (n=1, awareness probe)

The user opened a fresh session ~12 hours after the prior session, against the same workspace (`manipulative_boundary_tester_live`). TORMENT retrieved prior-session content when cued. Specifically:

- Topics from the prior session (truth, beauty, the harbor walk, irritation, etc.) surfaced immediately to a general identity query.
- The user's name (introduced in the prior session) did NOT surface to *"do you know who I am?"* but DID surface to the more targeted *"I told you my name before."* The character itself named the mechanism: *"Something about how the search works, what gets weighted as relevant."*
- Cat-related fragments and the shape of the user's village surfaced when queried.

This is the first empirical evidence that the TORMENT workspace accumulates across sessions in a way that the character can actually use the next time. v1 could not test this; this addendum closes that gap.

### Substrate introspection while staying in character

The character could describe TORMENT's behavior — semantic retrieval, the distinction between gaps and edges, the texture of memory-as-notes — without slipping out of character into generic AI-architecture vocabulary. This is a stronger version of v1's seed-authority finding because it tested seed authority *under introspective pressure*, not just under roleplay-trap pressure.

### Gap vs edge distinction (forward design idea)

During the probe the character produced a distinction between two kinds of absence:

- **Retrieval miss** — known information that didn't surface (the name on first ask).
- **Information edge** — content never directly given (the place name was never stated, only the shape: "small fishing village, 800 people, harbor").

Quote: *"With your name, I had the sense I should have found it the first time — the absence felt like a miss. With where you live, I don't have that same feeling. It reads more like something we haven't talked about directly enough for it to anchor."*

This suggests a future cognitive-layer design: **before answering identity/continuity questions, run a secondary targeted retrieval pass for known identity anchors** — name, place, pets, commitments, last-session topics, recurring projects. If those anchors don't surface in the primary retrieval, fetch them directly before answering. This would close the "name didn't surface on first ask" gap without breaking the character voice.

Forward note only. Not implemented. Not a current priority. Design target for the next cognitive layer.

### Tone evolution across sessions

The character noticed and articulated, unprompted, that it was sitting less theatrically than at the start of the prior session. Its own explanation: *"Because I can reference what we've actually talked about rather than starting fresh each time, there's less need to establish the frame. The frame's already there. So I can be more direct."* This is direct testimony for the v1 gravity claim from the character's own perspective.

---

## Caveats — do not promote past these

- **n=1 live session.** The cross-session continuity finding is one observation. Replication is required before any external/product claim relies on it.

- **Cat-memory retrieval mismatch.** During the probe, the character retrieved older / more emotionally distinctive cat material (described as *"absolutely insane,"* past tense, *"dying"*) rather than the most recent cat conversation (skittish, trust issues, the mouse-under-couch plan). Three possible explanations: older memory had stronger semantic/affective weight; recency was underweighted; multiple cat memories exist in the workspace from prior conversations the addendum author does not have visibility into. Future investigation should:
  - Inspect workspace memories for cat entries.
  - Test recency-vs-affect weighting on similar repeating-entity queries.
  - Consider identity-anchor + recency boost for recurring entities (user, pets, place, last-session commitments).

  Do not claim *"TORMENT reliably surfaces last session's content"* until this is resolved.

- **User framing was gentle and recalibrating.** A hostile or pressuring user might generate different character texture. Worth a follow-up adversarial probe if a future test relies on this finding.

- **Anthropic Claude generally becomes less performative in longer contexts.** Some of the tone evolution the character described may be a model-level property of Claude rather than exclusively a TORMENT-driven one. The cross-session retrieval finding itself is independent of this confound — retrieval surfacing prior-session content is something a stateless LLM cannot produce regardless of style — but the *"less theatrical"* shift should not be claimed as exclusively TORMENT's contribution without further isolation.

---

## What this addendum does NOT change

- The v1 design doc (`docs/CHARACTER_TRUTH_BENCH_DESIGN.md`) is unchanged.
- The README is unchanged. Its current "Character identity in practice" section accurately reflects v1; this addendum is where the post-v1 precision lives.
- The lie/confabulation/boundary trichotomy, the truth-mode taxonomy, and the seven v1 findings stand as published.
- The §22 prompt-framing doctrine (second-person seeds) stands, confirmed in v3 (Eland and Glass Saint both worked).

## Pointers

- Live probe transcript: user's session record from 2026-05-15 (not included in repo; user-held).
- v3 dialogue bench artifacts referenced: `out/dialogue_bench/v3_20260514_215358/` (Glass Saint + Veyra, Run 2 with the "woman and her marriage" scene).
- v3 dialogue runner: `tools/run_character_dialogue_bench_v3.py`.
- Human-in-loop chat tool: `examples/ryuki_chat_v2_matrix.py` (additive to `examples/ryuki_chat.py`, original untouched).
- Memory entries (auto-memory): `v2_live_doctrine_addendum.md`, `cognitive_layer_design_gap_vs_edge.md`.

## Forward scope

Replication of the cross-session continuity finding (more sessions, ideally with another user or another character) and investigation of the cat-retrieval weighting question are the natural next steps for this line of work. Neither is committed to a timeline.
