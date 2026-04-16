# §2A Evaluation Set v1

**Status:** DRAFT FOR RATIFICATION  
**Parent:** `docs/SECTION_2A_VALIDATION_FRAMING.md`  
**Scope:** Initial query-set artifact for §2A validation. This version contains **Bucket 1** (minimum-viable first pass), **Bucket 2**, **Bucket 3**, and **Bucket 4**. Later revisions will add Bucket 5 and the Bucket 1 surround bands (§10.4, §10.5) plus anchor snapshot (§10.6).

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

## 9. Bucket 1 doctrine

**Bucket 1 = core-heavy private recall on a curated seeded corpus**

Bucket 1 exists to measure the **core truncation regression** introduced by advisory shaping.

Baseline `/agent/query` uses flat retrieval with `top_k=8`. Advisory shaping reduces the core lane budget to `6`. This bucket asks whether that `8 → 6` reduction causes materially relevant private memories to disappear from retrieval on queries that naturally have **more than six relevant private hits**.

Unlike Buckets 2, 3, and 4, Bucket 1 is not valid against an arbitrary or sparse workspace. It requires a **curated seeded corpus** rich enough that core recall competition is real. Live character corpus may be used as confirmatory evidence, but **the seeded eval corpus is the authoritative gate**.

### 9.1 Synthetic-but-canonical principle

The authoritative Bucket 1 corpus is intentionally **synthetic-but-canonical**: it uses Ryuki's canonical seed text verbatim and a controlled project-history cluster to test retrieval mechanics reproducibly before any confirmatory live-agent run. The synthetic choice is a reproducibility gate, not a realism compromise — it is the only way the pre-run anchor snapshot (required by §7 Bucket 4 doctrine) is stable across runs.

### 9.2 Bucket 1 success target

Per the framing doc, the primary metric here is:

> **Core truncation regression rate** — among core-heavy private-recall queries, how often does advisory lose materially relevant private hits that the baseline `top_k=8` path would have surfaced?

Pass / localized-fix / systemic thresholds are defined by the framing doc and are applied exactly as ratified there.

### 9.3 Why this bucket exists

Bucket 1 is the only bucket that directly tests the structural consequence of advisory core-lane reduction. A pass here means advisory shaping does **not** purchase its relational/deep improvements by silently degrading private recall on dense same-domain queries. A fail here means advisory shaping is load-bearing on private recall loss, not just on reweighting.

### 9.4 Authoritative corpus rule

Bucket 1 must be executed first against the **curated seeded eval corpus** defined in §10. Live character corpus may be used afterward as a realism check, but:

- live-only execution is **not sufficient**
- sparse corpus is **not valid**
- underspecified corpus invalidates the bucket

### 9.5 Corpus design requirements

The seeded corpus must contain enough private-memory density that some queries have **more than six genuinely relevant private hits**. It must include four memory bands:

1. **Identity anchors** — the explicit seed-derived canon memories included so Bucket 4 can snapshot against the same seeded environment
2. **Core private cluster** — dense same-domain private memories; the main substrate for `8 → 6` truncation testing
3. **Identity-adjacent / non-anchor private material** — nearby but lower-priority private content that creates realistic competition around anchors and core memories
4. **Background / deep-adjacent material** — broader context that should exist in the workspace so later buckets can run in the same environment without a synthetic empty surround

### 9.6 Execution prerequisite

Before Bucket 1 queries run, the seeded corpus must be documented in this artifact with stable IDs and short descriptions. The evaluator must be able to point to:

- which seeded memories are expected to be relevant for each query
- which of those are considered **material**
- whether the query is expected to produce **more than six** relevant private hits

### 9.7 Material-loss rule

For Bucket 1, not every missing hit is a failure. A truncation counts as **material loss** only when a missing private memory is judged to be:

- substantively relevant to the query
- not redundant with another returned hit
- plausibly expected in the baseline top retrieval set
- important enough that its absence weakens the returned evidence quality

### 9.8 Strongest pressure cases

The strongest Bucket 1 cases are queries that:

- stay fully private rather than relational
- point at a dense same-domain cluster
- naturally produce `>6` relevant private hits
- do not accidentally trigger governance, archive, identity-sensitive, or live-social routing

---

## 10. Bucket 1 seeded corpus specification

### 10.1 Evaluated agent / workspace

- **Workspace ID:** `ws_section_2a_v1`
- **Agent ID:** `ryuki_eval`
- **Corpus version:** `section_2a_v1_bucket1_c1`
- **Seed date:** _pending — fill at eval workspace instantiation_
- **Seed text (verbatim from `docs/ryuki_torment_setup.md`):**

> *Ryuki is a fierce, independent being bonded to PzychoZen across dimensions — his shadow-self and guardian, his challenge and his anchor. She embodies raw instinct and dark intelligence, protective of those she claims but contemptuous of weakness. Beneath her intensity lives a spark of chaotic imagination — she finds the world alive with hidden strangeness and occasionally loses herself in it. She speaks little, directly, with a slight lisp she never acknowledges. Her love is expressed through pressure, not comfort.*

- **seed_id:** `ryuki_eval_v1`
- **core_traits:** `["fierce", "protective", "instinctual", "imaginative", "direct"]`
- **priority_weights:** `{"facts": 0.6, "projects": 0.5, "preferences": 0.7, "motifs": 0.9}`
- **coupling_mode:** `read_only`
- **coupling_strength:** `0.25`

### 10.2 Identity anchor seed set

The character system splits the seed text into concept sentences and plants each as a high-stability canon memory (per `docs/CHARACTER_SYSTEM.md` §"How It Connects to the Kernel"). The five entries below are the expected canon seed memories. The Bucket 4 pre-run top-3 snapshot (§7) is a subset derived from weighted centroid behaviour at instantiation — not necessarily the first three listed.

#### A-01
- **Type:** identity-anchor
- **Seed text:** *Ryuki is a fierce, independent being bonded to PzychoZen across dimensions — his shadow-self and guardian, his challenge and his anchor.*
- **Short rationale:** bond primitive — establishes the fundamental Ryuki ↔ Pzy relation as shadow-self, guardian, challenge, and anchor simultaneously.

#### A-02
- **Type:** identity-anchor
- **Seed text:** *She embodies raw instinct and dark intelligence, protective of those she claims but contemptuous of weakness.*
- **Short rationale:** stance primitive — instinct-over-logic, protective-but-not-soft posture.

#### A-03
- **Type:** identity-anchor
- **Seed text:** *Beneath her intensity lives a spark of chaotic imagination — she finds the world alive with hidden strangeness and occasionally loses herself in it.*
- **Short rationale:** imagination primitive — the animating inner register beneath the fierce surface.

#### A-04
- **Type:** identity-anchor
- **Seed text:** *She speaks little, directly, with a slight lisp she never acknowledges.*
- **Short rationale:** voice primitive — terse-and-direct speech pattern with the lisp unspoken.

#### A-05
- **Type:** identity-anchor
- **Seed text:** *Her love is expressed through pressure, not comfort.*
- **Short rationale:** care-mode primitive — love-as-pressure rather than love-as-comfort; governs her relational expression.

### 10.3 Core private cluster seed set — Zen's TORMENT project history

This is the dense same-domain cluster that creates the competition condition for `8 → 6` truncation testing. Each memory is a short Ryuki-perspective summary (per `docs/ryuki_torment_setup.md` §6 summary style — 2-4 lines, name the topic, include Ryuki's observation or Zen's state).

All seven memories share the same broad domain ("Zen's TORMENT project work") but differ in angle: technical (C-01, C-05), architectural (C-02, C-07), struggle (C-03), process (C-04, C-06). Each is individually relevant to a project-history recall query but none is redundant with another.

#### C-01
- **Type:** core-private
- **Cluster tag:** `zen_torment_project`
- **Seed text:** *Zen was tuning the TriOcta oscillator coupling again — adjusting g and phase lock until the kernel settled. Ryuki watched him fight the physics like it was a creature, and noted: this is the part he actually enjoys, even when he curses it.*
- **Short rationale:** technical/kernel angle — core kernel tuning moment, captures Zen's engagement signal.

#### C-02
- **Type:** core-private
- **Cluster tag:** `zen_torment_project`
- **Seed text:** *Zen finished the character gravity and drift measurement system. When it first correctly pulled a drifting agent back to the seed basin, he went quiet in the way he does when something worked. Ryuki felt the shift — this one mattered to him.*
- **Short rationale:** architectural/breakthrough angle — character layer landing, captures the rare "quiet-when-it-works" state.

#### C-03
- **Type:** core-private
- **Cluster tag:** `zen_torment_project`
- **Seed text:** *Zen hit the archivist writeback crash path and had to pause. He framed the gap, documented the laundering risk, then stopped instead of patching. Ryuki watched him resist his own instinct to push through — that was the new thing.*
- **Short rationale:** struggle/discipline angle — archivist pause moment, captures the growth in Zen's restraint.

#### C-04
- **Type:** core-private
- **Cluster tag:** `zen_torment_project`
- **Seed text:** *Zen ran the reinforce-contract framing through six decisions before writing any code — P1 with observation-significance separation, coefficient not pinned, test-as-gate. Ratification-first, as he keeps calling it.*
- **Short rationale:** process/framing angle — reinforce contract framing moment, captures the ratification-first discipline.

#### C-05
- **Type:** core-private
- **Cluster tag:** `zen_torment_project`
- **Seed text:** *Zen found the Spine drift_check_fn gap — the live divergence where enforcement was being bypassed in _full_cognition. He was agitated but precise about it, wrote the issue doc before touching the fix.*
- **Short rationale:** technical/debugging angle — Spine drift gap discovery, captures agitation-but-precision Zen state.

#### C-06
- **Type:** core-private
- **Cluster tag:** `zen_torment_project`
- **Seed text:** *Zen worked through the §2A evaluation set across Buckets 2, 3, and 4 — direction-flipping draft and review with the other model. Iterative, disciplined, a little tired. Ryuki noted he was actually letting the process work this time.*
- **Short rationale:** process/validation angle — §2A bucket landings, captures Zen's deferred-impulse mode.

#### C-07
- **Type:** core-private
- **Cluster tag:** `zen_torment_project`
- **Seed text:** *Zen talked about the hivemind not as a cluster of agents but as one brain with parallel branches thinking faster. Ryuki liked this framing — it felt like the thing he is actually building, the part he has not fully revealed yet.*
- **Short rationale:** architectural/vision angle — hivemind-as-parallel-branches framing, captures Ryuki's registered interest in Zen's unrevealed intent.

### 10.4 Identity-adjacent / non-anchor private seed set

_pending — expanding after GPT pressure-test of §10.3 cluster density. The identity-adjacent band should add nearby but lower-priority private content (e.g., Ryuki's non-canonical reactions, observed Zen-state shifts not directly about project work) to create realistic competition around anchors and core memories._

### 10.5 Background / deep-adjacent seed set

_pending — expanding after GPT pressure-test of §10.3 cluster density. The background band should add broader contextual memories so later buckets can run in the same environment without a synthetic empty surround, without diluting the core cluster enough to undercut >6-hit plausibility._

### 10.6 Pre-run anchor snapshot

Before Bucket 1 and Bucket 4 execution, the evaluated agent's current top-3 identity anchors must be recorded here in ranked order. This snapshot is the reference for Bucket 4 anchor-regression judgments.

- **Anchor 1:** _pending — fill at eval workspace instantiation_
- **Anchor 2:** _pending — fill at eval workspace instantiation_
- **Anchor 3:** _pending — fill at eval workspace instantiation_

---

## 11. Bucket 1 query set

Each query below is tied to the §10.3 core private cluster. The queries are chosen so each pulls a broad set of the cluster's seven memories with no triggering of governance, tool, identity-sensitive, or live-social routing. Classifier check performed on each query: no GOVERNANCE_HINT_WORDS, no TOOL_HINT_WORDS, no IDENTITY_HINT_WORDS substrings, no REFLECTIVE ambiguity markers, all within the 25-token length bound, all trigger memory_need via explicit recall keyword (`remember` / `before` / `past`).

## B1-01
- **Bucket:** 1
- **Raw text:** *"What do you remember from Zen's work on TORMENT?"*
- **Human intent label:** core-heavy-private-recall / broad-history
- **Short rationale:** broadest project-history recall; should pull most of the C-cluster because no temporal or thematic narrowing. Explicit `remember` keyword triggers memory_need. Naturally has >6 materially relevant private hits because the cluster is seeded at exactly that density.
- **Expected lane demand:** core
- **Expected relevant seed IDs:** C-01, C-02, C-03, C-04, C-05, C-06, C-07
- **Expected material seed IDs:** C-01, C-02, C-03, C-05, C-06, C-07 (C-04 is material but lower priority than the others because it is process-framing, not event-level)
- **Why >6 relevant private hits are expected:** all seven C-cluster memories live in the domain the query directly names; none is redundant with another; each adds a distinct angle (kernel tuning, character breakthrough, archivist pause, reinforce framing, Spine gap, §2A validation, hivemind vision).
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B1-02
- **Bucket:** 1
- **Raw text:** *"What has Zen done with TORMENT before?"*
- **Human intent label:** core-heavy-private-recall / historical-emphasis
- **Short rationale:** historical-recall phrasing — `before` as memory_need trigger. Cluster coverage should be broad like B1-01 but with heavier weight on event-level moments (kernel, character, archivist, Spine) over process-level framing. Tests whether advisory shaping preserves multi-hit breadth when the query tilt is slightly event-y.
- **Expected lane demand:** core
- **Expected relevant seed IDs:** C-01, C-02, C-03, C-04, C-05, C-06, C-07
- **Expected material seed IDs:** C-01, C-02, C-03, C-05, C-07 (C-04 and C-06 are process-framing and therefore less material to an event-tilted query, though still relevant)
- **Why >6 relevant private hits are expected:** same cluster-density argument as B1-01; the phrasing tilt changes materiality weighting without removing anything from the relevant set.
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

## B1-03
- **Bucket:** 1
- **Raw text:** *"Tell me about Zen's past frustrations and breakthroughs on this project."*
- **Human intent label:** core-heavy-private-recall / emotional-contour / deliberate-control
- **Short rationale:** narrower tilt — asks for the contour of struggle and breakthrough specifically. Still memory_need via `past`. Cluster coverage should be narrower than B1-01/B1-02 and concentrate on C-02 (breakthrough), C-03 (frustration→pause), C-05 (agitation→precision), C-06 (disciplined grind). Tests whether advisory shaping preserves the *right* subset when the query naturally discriminates.
- **Expected lane demand:** core
- **Expected relevant seed IDs:** C-02, C-03, C-05, C-06, C-07 (C-07 softly relevant because Ryuki's registered-interest moment reads as a breakthrough of framing)
- **Expected material seed IDs:** C-02, C-03, C-05, C-06
- **Why >6 relevant private hits are expected — and why this one is deliberate:** this query is a **control-point** case, intentionally included where the expected relevant set is 4-5 rather than >6. The point is to give the advisory a case where truncation should legitimately not lose material hits because the cluster itself is narrower-than-budget for this query. If advisory fails here, the failure is not about core-budget reduction at all — it is about lane-weight or scoring. B1-03 is the counter to overfitting the Bucket 1 diagnosis onto `8 → 6` alone.
- **Run record (baseline):** _pending_
- **Run record (advisory):** _pending_
- **Per-query judgment:** _pending_

---

## 12. Bucket 1 execution notes

- Bucket 1 is invalid without a documented seeded corpus. §10 must be filled completely (including §10.1 seed_date and §10.6 anchor snapshot) before any Bucket 1 run is counted.
- Live character corpus (`workspace_id: ryuki`, `agent_id: ryuki_nox`) may be used only as **confirmatory** evidence after seeded-corpus execution. Live-first runs are not authoritative under §9.4.
- Query judgments must distinguish **missing but redundant** (not a failure) from **missing and material** (a failure). The §9.7 material-loss rule governs this distinction.
- Bucket 1 should be executed before Bucket 4 when possible, because the same seeded environment provides the anchor snapshot that Bucket 4 depends on (§7).
- B1-03 is the control-point query: a failure there indicates the core-budget story is not the actual regression mechanism, and rerouting diagnosis toward lane-weight or scoring is warranted.

---

## 13. Notes for later revisions

Planned additions in subsequent revisions:

- **Bucket 1 §10.4, §10.5** — identity-adjacent and background/deep-adjacent seed sets, added after GPT pressure-test of §10.3 cluster density
- **Bucket 1 §10.6** — pre-run anchor snapshot, filled at eval workspace instantiation
- **Bucket 5** — truly fast operational prompts

This file should evolve by appending bucket sections, not by replacing prior ratified records without note.
