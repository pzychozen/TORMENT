# §2A Evaluation Set v1

**Status:** DRAFT FOR RATIFICATION  
**Parent:** `docs/SECTION_2A_VALIDATION_FRAMING.md`  
**Scope:** Initial query-set artifact for §2A validation. This version contains **Bucket 2** only. Later revisions will add Buckets 3, 1, 4, and 5.

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

## 5. Notes for later revisions

Planned additions in subsequent revisions:

- **Bucket 3** — deep-needed, naturally phrased, avoids ambiguity markers
- **Bucket 1** — curated seeded corpus cases with >6 relevant private memories per query
- **Bucket 4** — identity-sensitive anchor-preservation checks
- **Bucket 5** — truly fast operational prompts

This file should evolve by appending bucket sections, not by replacing prior ratified records without note.
