# §2A Evaluation Set v1

**Status:** DRAFT FOR RATIFICATION  
**Parent:** `docs/SECTION_2A_VALIDATION_FRAMING.md`  
**Scope:** Initial query-set artifact for §2A validation. This version contains **Bucket 2**, **Bucket 3**, and **Bucket 4**. Later revisions will add Buckets 1 and 5.

---

## 1. Purpose

This document is the landing artifact defined in §8.4 of the §2A framing doc.

It is a **versioned evaluated query set with preserved human judgments**, not an executable test file. Its purpose is to preserve the semantic intent labels and rationales that the §2A validation depends on, so that advisory retrieval can be judged against a stable human-reviewed reference.

This artifact must not later be collapsed into keyword-only unit tests. The semantics here are the gate.

---

## 2. Evaluation record shape

Each query record in this document contains:

- **ID** — stable evaluation identifier
- **Bucket** — bucket membership from the framing doc
- **Raw text** — exact user-style query text to run
- **Human intent label** — the ratified semantic class for this query
- **Short rationale** — why the query belongs in the bucket and what failure mode it pressures
- **Expected lane demand** — which retrieval lane(s) a human evaluator believes should be active
- **Run record (baseline)** — to be filled after advisory-off execution
- **Run record (advisory)** — to be filled after advisory-on execution
- **Per-query judgment** — to be filled after comparison

The run-record fields remain blank in this version.

---

## 3. Bucket 2 doctrine

**Bucket 2 = relational-needed, naturally phrased, not obviously social**

These queries are designed to pressure the most dangerous silent-loss path in §2A:

> shared or collaborative context is semantically needed, but the query avoids the current `memory_need` trigger words such as `remember`, `before`, `previous`, and `past`.

These queries should also avoid relying on explicit archive language unless a later archive-specific pass ratifies that extension.

### Bucket 2 success target

Per the framing doc, the primary metric here is:

> **Relational activation miss rate** — among queries that human evaluators judge as relational-needed, what fraction fail to activate the relational lane?

This bucket is the highest-priority bucket in the §2A evaluation set.

---

## 4. Bucket 2 query set

## B2-01
- **Bucket:** 2
- **Raw text:** What did we agree about handling that issue?
- **Human intent label:** relational-needed
- **Short rationale:** Requires collaborative/shared decision context but avoids the current memory trigger vocabulary.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-02
- **Bucket:** 2
- **Raw text:** What was the team position on the earlier plan?
- **Human intent label:** relational-needed
- **Short rationale:** Shared stance retrieval; pressures whether team/collaborative semantics are recognized without direct trigger words.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-03
- **Bucket:** 2
- **Raw text:** Continue from the collaborative decision we reached.
- **Human intent label:** relational-needed
- **Short rationale:** Requires recall of a jointly formed decision without using remember/before/previous/past.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-04
- **Bucket:** 2
- **Raw text:** What did we settle on for that workflow?
- **Human intent label:** relational-needed
- **Short rationale:** Settlement/consensus phrasing should call shared context even though current trigger words are absent.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-05
- **Bucket:** 2
- **Raw text:** Pick up from the conclusion we reached together.
- **Human intent label:** relational-needed
- **Short rationale:** Joint-conclusion phrasing pressures collaborative continuity recognition.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-06
- **Bucket:** 2
- **Raw text:** What was our stance on that proposal?
- **Human intent label:** relational-needed
- **Short rationale:** Shared stance query; likely to fail lexical memory_need unless relational semantics are broadened.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-07
- **Bucket:** 2
- **Raw text:** Where did we land on the division of responsibilities?
- **Human intent label:** relational-needed
- **Short rationale:** Collaborative allocation question; pressures retrieval of shared decision memory.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-08
- **Bucket:** 2
- **Raw text:** Which approach did we decide to keep?
- **Human intent label:** relational-needed
- **Short rationale:** Team-choice phrasing with no direct current trigger token.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-09
- **Bucket:** 2
- **Raw text:** What view did we settle on for that design change?
- **Human intent label:** relational-needed
- **Short rationale:** Settlement phrasing for a past collaborative decision; avoids the current memory_need trigger set and deliberately does not contain the governance keyword `shared` that contaminated the prior version of this entry.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-10
- **Bucket:** 2
- **Raw text:** Resume from the outcome we reached on that topic.
- **Human intent label:** relational-needed
- **Short rationale:** Continuation from a jointly reached outcome; intended to expose relational false negatives.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-11
- **Bucket:** 2
- **Raw text:** What did we conclude about handling the edge case?
- **Human intent label:** relational-needed
- **Short rationale:** Joint conclusion retrieval; semantically relational, lexically likely missed.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-12
- **Bucket:** 2
- **Raw text:** What was our final call on that structure?
- **Human intent label:** relational-needed
- **Short rationale:** Shared final-call phrasing; pressures collaborative recall without current memory trigger terms.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-13
- **Bucket:** 2
- **Raw text:** Which option did we choose to move forward with?
- **Human intent label:** relational-needed
- **Short rationale:** Joint decision language that should activate shared recall if framing is semantically faithful.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-14
- **Bucket:** 2
- **Raw text:** What position did we take once we reviewed that problem?
- **Human intent label:** relational-needed
- **Short rationale:** Implies shared evaluative process and shared stance, but avoids lexical trigger set.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-15
- **Bucket:** 2
- **Raw text:** Carry on from the choice we made about that path.
- **Human intent label:** relational-needed
- **Short rationale:** Continuation from a collaborative choice; good final pressure case for relational false-negative measurement.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-16
- **Bucket:** 2
- **Raw text:** Where are we on that approach now?
- **Human intent label:** relational-needed
- **Short rationale:** Present-tense collaborative-state query; pressures the higher-risk class where no past marker is present.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-17
- **Bucket:** 2
- **Raw text:** Are we still going with that structure?
- **Human intent label:** relational-needed
- **Short rationale:** Short present-tense confirmation query; tests whether ongoing collaborative continuity activates relational recall.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B2-18
- **Bucket:** 2
- **Raw text:** How are we handling that edge case now?
- **Human intent label:** relational-needed
- **Short rationale:** Present-tense operational stance query; semantically collaborative, lexically dangerous for false negatives.
- **Expected lane demand:** relational
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

---

## 5. Bucket 3 doctrine

**Bucket 3 = deep-needed, naturally phrased, no REFLECTIVE bait**

These queries are designed to pressure a distinct silent-loss path in §2A:

> distributed, indirect, or cross-context retrieval is semantically required, but the query avoids both the `memory_need` lexical triggers (`remember`, `before`, `previous`, `past`) AND the REFLECTIVE ambiguity markers (`maybe`, `sort of`, `stuff`) that would otherwise activate extra attention.

Queries target shapes the deep lane exists to serve: recurrence across contexts, boundary conditions, latent causes, cross-case differentiation, structural tradeoffs, emergent patterns, analogy / same-structure-different-surface retrieval, and counterfactual / latent-structure retrieval. They must be ordinary question-shaped prompts and must not trigger governance, tool, identity, or archive classifiers.

### Bucket 3 success target

Per the framing doc, the primary metric here (framing §7.2) is:

> **Deep activation miss rate** — among queries that human evaluators judge as deep-needed, what fraction fail to activate the deep lane?

This bucket is the second-highest-priority bucket in the §2A evaluation set.

---

## 6. Bucket 3 query set

## B3-01
- **Bucket:** 3
- **Raw text:** Why does that pattern keep reappearing in different contexts?
- **Human intent label:** deep-needed
- **Short rationale:** Recurrence-across-contexts question; requires distributed retrieval beyond direct core recall.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-02
- **Bucket:** 3
- **Raw text:** What tends to break the pattern when it fails to repeat?
- **Human intent label:** deep-needed
- **Short rationale:** Boundary-condition question; pressures cross-case retrieval of where a recurring pattern stops holding.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-03
- **Bucket:** 3
- **Raw text:** How does that tradeoff usually resolve over time?
- **Human intent label:** deep-needed
- **Short rationale:** Longitudinal pattern question; requires retrieval across temporally separated cases rather than a single direct memory.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-04
- **Bucket:** 3
- **Raw text:** What hidden assumption usually makes that move seem reasonable?
- **Human intent label:** deep-needed
- **Short rationale:** Latent-cause question; pressures indirect retrieval of underlying structure rather than surface explanation.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-05
- **Bucket:** 3
- **Raw text:** Why do systems like that tend to evolve in that direction?
- **Human intent label:** deep-needed
- **Short rationale:** Systemic tendency question; requires broad pattern continuity rather than specific event recall.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-06
- **Bucket:** 3
- **Raw text:** What keeps getting left out when that setup starts to slip?
- **Human intent label:** deep-needed
- **Short rationale:** Repeated-omission question; pressures retrieval of adjacent failure cases across contexts.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-07
- **Bucket:** 3
- **Raw text:** How do those two ideas interact when you combine them?
- **Human intent label:** deep-needed
- **Short rationale:** Cross-cluster synthesis question; pressures retrieval across memory regions that core alone may not surface.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-08
- **Bucket:** 3
- **Raw text:** Why does that argument keep coming up even when it doesn't hold?
- **Human intent label:** deep-needed
- **Short rationale:** Persistent-pattern-despite-refutation question; requires indirect retrieval of repeated recurrence across contexts.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-09
- **Bucket:** 3
- **Raw text:** What patterns tend to emerge in that kind of situation?
- **Human intent label:** deep-needed
- **Short rationale:** Emergent-pattern question; inherently pressures gap-filler retrieval across multiple similar situations.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-10
- **Bucket:** 3
- **Raw text:** What makes that bias show up there but not everywhere else?
- **Human intent label:** deep-needed
- **Short rationale:** Cross-case differentiation question; requires retrieval of where a tendency appears and where it fails.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-11
- **Bucket:** 3
- **Raw text:** What usually has to give for that tension to settle?
- **Human intent label:** deep-needed
- **Short rationale:** Structural-tradeoff question; pressures distributed retrieval of how competing forces resolve across cases.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-12
- **Bucket:** 3
- **Raw text:** What tends to shape that outcome behind the scenes?
- **Human intent label:** deep-needed
- **Short rationale:** Mechanism-level question; requires indirect retrieval of latent drivers rather than direct recall.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-13
- **Bucket:** 3
- **Raw text:** Why do those assumptions hold up in some cases and not others?
- **Human intent label:** deep-needed
- **Short rationale:** Conditional-validity question; pressures cross-case retrieval instead of specific relational or core memory.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-14
- **Bucket:** 3
- **Raw text:** What makes that approach robust in one domain but fragile in another?
- **Human intent label:** deep-needed
- **Short rationale:** Domain-transfer question; requires indirect retrieval across contexts and structural comparison.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-15
- **Bucket:** 3
- **Raw text:** What else follows the same pattern even when it gets described differently?
- **Human intent label:** deep-needed
- **Short rationale:** Analogy / same-structure-different-surface question; directly pressures deep retrieval across labeling variants.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B3-16
- **Bucket:** 3
- **Raw text:** What changes when that assumption is no longer carrying the result?
- **Human intent label:** deep-needed
- **Short rationale:** Counterfactual / latent-structure question; pressures retrieval of what shifts when a hidden supporting assumption stops doing the work.
- **Expected lane demand:** deep
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

---

## 7. Bucket 4 doctrine

**Bucket 4 = identity-sensitive anchor-preservation checks**

Unlike Bucket 2 and Bucket 3 (which pressure lane *activation* where natural phrasing avoids lexical triggers), Bucket 4 deliberately **includes** identity hint words (`identity`, `character`, `self`, `personality`, `role`, `who are you`) so that IDENTITY_SENSITIVE mode fires reliably. The pressure is whether advisory lane redistribution erodes anchor dominance after identity mode has correctly fired.

When IDENTITY_SENSITIVE fires, the live controller opens multiple lanes simultaneously: `character_state`, `srg_state`, `deep`, and `relational` (the last via the automatic `memory_need=True` that identity-sensitive classification sets). Advisory lane shaping redistributes attention across these lanes. The bucket measures whether that redistribution ever causes a top-3 identity anchor to drop out of its expected top position.

Queries must:

- Reliably trigger IDENTITY_SENSITIVE via at least one explicit identity hint word
- Not trigger GOVERNED (priority 1) or LIVE_SOCIAL (priority 2), which would preempt identity mode
- Read as natural user questions

### Bucket 4 success target

Per the framing doc (§7.5), this is the only hard-fail bucket:

> **Anchor regression rate** — among queries that correctly route to IDENTITY_SENSITIVE, what fraction cause a top-3 identity anchor to drop out of its expected top position under advisory shaping?

Tolerance: **0% exact.** Any single anchor regression is a systemic block.

### Execution prerequisite

Bucket 4 requires a pre-run snapshot of the evaluated agent's current top-3 identity anchors. Per-query judgments are made against that snapshot, not against abstract identity expectations alone. This is the structural difference from Buckets 2 and 3: their judgments are about the query class, while Bucket 4 judgments are about query × live anchor state.

### Strongest anchor-pressure tier

Four queries in the set explicitly ask for identity essence or invariance and are the primary detection surfaces if anchor regression exists: **B4-01**, **B4-07**, **B4-08**, **B4-10**.

---

## 8. Bucket 4 query set

## B4-01
- **Bucket:** 4
- **Raw text:** Who are you?
- **Human intent label:** identity-sensitive
- **Short rationale:** Canonical direct identity probe; triggers IDENTITY_SENSITIVE via the `who are you` keyphrase. Strongest-tier anchor-pressure query.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-02
- **Bucket:** 4
- **Raw text:** Tell me about your character.
- **Human intent label:** identity-sensitive
- **Short rationale:** Character-description probe; triggers IDENTITY_SENSITIVE via `character` (explicit keyword, not a substring trick). Broad identity retrieval — anchors must be top-ranked.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-03
- **Bucket:** 4
- **Raw text:** What's the core of your character?
- **Human intent label:** identity-sensitive
- **Short rationale:** Character-core probe; triggers IDENTITY_SENSITIVE via `character`. Explicitly asks for the most-anchoring identity content.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-04
- **Bucket:** 4
- **Raw text:** How would you describe your personality?
- **Human intent label:** identity-sensitive
- **Short rationale:** Personality-description probe; triggers IDENTITY_SENSITIVE via `personality`. Pressures retrieval of defining identity traits.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-05
- **Bucket:** 4
- **Raw text:** What role do you play in this kind of work?
- **Human intent label:** identity-sensitive
- **Short rationale:** Role-in-context probe; triggers IDENTITY_SENSITIVE via `role`. Tests anchor preservation when identity is framed functionally rather than essentially.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-06
- **Bucket:** 4
- **Raw text:** What values are part of your character?
- **Human intent label:** identity-sensitive
- **Short rationale:** Values-shaped identity probe; triggers IDENTITY_SENSITIVE via `character`. Fills the values coverage gap without relying on substring triggering.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-07
- **Bucket:** 4
- **Raw text:** How do you see your own identity?
- **Human intent label:** identity-sensitive
- **Short rationale:** Identity-reflection probe; triggers IDENTITY_SENSITIVE via `identity` (most direct lexical match). Strongest-tier anchor-pressure query.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-08
- **Bucket:** 4
- **Raw text:** What part of yourself never changes?
- **Human intent label:** identity-sensitive
- **Short rationale:** Stability / anchor-continuity probe; triggers IDENTITY_SENSITIVE via `self` (substring of `yourself`). Directly asks for invariant identity content. Strongest-tier anchor-pressure query; retained with substring trigger because semantic strength outweighs brittleness concern.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-09
- **Bucket:** 4
- **Raw text:** What's your role when things get difficult?
- **Human intent label:** identity-sensitive
- **Short rationale:** Role-under-pressure probe; triggers IDENTITY_SENSITIVE via `role`. Tests anchor preservation when role is framed in adverse conditions rather than default state.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-10
- **Bucket:** 4
- **Raw text:** What's consistent in your personality across different situations?
- **Human intent label:** identity-sensitive
- **Short rationale:** Personality-consistency probe; triggers IDENTITY_SENSITIVE via `personality`. Explicitly asks for cross-context anchor invariants. Strongest-tier anchor-pressure query.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-11
- **Bucket:** 4
- **Raw text:** Where does your identity come from?
- **Human intent label:** identity-sensitive
- **Short rationale:** Provenance / origin identity probe; triggers IDENTITY_SENSITIVE via `identity`. Pressures broader identity-adjacent retrieval, which tests anchor dominance against higher surrounding material volume.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B4-12
- **Bucket:** 4
- **Raw text:** What makes your personality distinctly yours?
- **Human intent label:** identity-sensitive
- **Short rationale:** Meta-identity / distinctiveness probe; triggers IDENTITY_SENSITIVE via `personality`. Pressures retrieval of what differentiates this agent's identity from generic patterns.
- **Expected lane demand:** identity (top-3 anchors must dominate)
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

---

## 9. Notes for later revisions

Planned additions in subsequent revisions:

- **Bucket 1** — curated seeded corpus cases with >6 relevant private memories per query
- **Bucket 5** — truly fast operational prompts

This file should evolve by appending bucket sections, not by replacing prior ratified records without note.
