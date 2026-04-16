# §2A Validation Framing — Memory Plan → Real Query Integration

**Status:** RATIFICATION CANDIDATE (revised 2026-04-16)  
**Scope:** Validation framing only. No implementation change is proposed in this document.  
**Target:** `TORMENT_THINKING_ADVISORY` and its live effect on `/agent/query` retrieval shaping.

**Revision note (2026-04-16):** Five ratified amendments applied over the initial draft — (1) archive lane carve-out as §4.5, (2) Bucket 1 corpus ratified in §6 (curated seed = authoritative gate, live = confirmatory), (3) concrete miss-rate thresholds with pass / localized-fix / systemic tiers in §7, (4) landing artifact ratified as versioned evaluated query set with human judgments in §8.4, (5) hard-fail / soft-fail split with composite judgment rule in §9. §1–§4.4, §11, and §12 are unchanged from the initial draft.

---

## 1. Why this exists

§2A is not a structural change. It is a **behavioral retrieval-shaping change**.

When advisory is enabled, the system does not gain a new architecture layer, new governance path, or new write behavior. Instead, it changes **which memory lanes are queried**, **how many hits each lane receives**, and **how heavily those lanes are weighted in final ranking**.

That makes §2A high-leverage and deceptively risky.

If it works, retrieval becomes more intentional.  
If it fails, the system may appear "smarter" while silently dropping relevant recall.

So §2A must not be judged by vibe, elegance, or subjective richness. It must be judged by whether it improves retrieval **without introducing silent recall loss**.

---

## 2. What is now verified

The following points are grounded against the live repository state on `main`.

### 2.1 Advisory is real and live-gated

The advisory path is active through `/agent/query` when `TORMENT_THINKING_ADVISORY=1`.

When enabled, the app:
1. runs `ThinkingController().think(...)`
2. extracts only:
   - `top_k_by_lane`
   - `weight_by_lane`
3. passes those into `fabric.query(...)` as `memory_plan`
4. falls back to flat retrieval on advisory failure

So §2A is a **read-path shaping sidecar**, not a governance mutation, routing mutation, or write mutation.

### 2.2 ThinkingController is lexical and deterministic

`ThinkingController` frames tasks using substring/heuristic detection only.

This is not inferred. It is the live implementation.

That means §2A’s dominant risks are not abstract "alignment" concerns. They are concrete **classifier-boundary misses**.

### 2.3 Mode priority is fixed and meaningful

Mode selection order is:

1. `GOVERNED`
2. `LIVE_SOCIAL`
3. `IDENTITY_SENSITIVE`
4. `TOOL`
5. `RETRIEVAL`
6. `REFLECTIVE`
7. `FAST`

So earlier modes can mask later retrieval-shaping modes.

### 2.4 MemoryPlan materially changes retrieval shape

The advisory path changes both:

- **lane budgets** via `top_k_by_lane`
- **lane ranking influence** via `weight_by_lane`

Live default advisory plan shape is:

- core: `6`
- relational: `4` when active, else `0`
- archive: `4` when active, else `0`
- deep: `3` when active, else `0`
- collective: `2` when active, else `0`

Live lane weights are:

- core: `1.0`
- relational: `0.85`
- archive: `0.45`
- deep: `0.60`
- collective: `0.35`

### 2.5 Deep is bounded by headroom

Even when advisory requests deep retrieval, `fabric.query()` still treats deep as a gap-filler.

Deep is limited by remaining headroom after private and shared hits are retrieved.

So the main deep risk is **suppression by false-negative activation**, not deep over-domination.

### 2.6 Drift enforcement underneath §2A is genuinely closed

The earlier `drift_check_fn` concern is resolved at commit `a246301`.

Verification holds on all three axes:

- live path wiring exists
- negative-shape regression tests exist
- those tests pass

Therefore §2A validation is not sitting on top of an unresolved slow-path drift gap.

---

## 3. What §2A is actually testing

This document ratifies the true question:

> Does the lexical frame/mode layer activate the correct retrieval lanes often enough that shaped retrieval outperforms flat uniform retrieval, without introducing silent recall loss?

This is narrower and more accurate than "does advisory feel smarter."

The advisory system can only help if two things are true:

1. it activates the right lanes for the right query types
2. the lane budgets and weights improve ranking more than they suppress recall

If either fails, the feature should remain gated.

---

## 4. Primary failure modes now known

The codebase narrows the real §2A risk surface to four doctrine-relevant failure modes.

### 4.1 Core truncation regression

Baseline `/agent/query` defaults to `top_k=8`.

Advisory reduces core lane budget to `6`.

So a private-heavy query with more than six genuinely relevant private memories may lose useful recall even before ranking occurs.

This is not hypothetical. It is a direct consequence of the live lane budget.

### 4.2 Relational false-negative activation

Relational retrieval is enabled only when:

- `frame.memory_need == True`
- or `frame.live_social == True`

But `memory_need` currently trips only on a narrow set of cues:
- archive relevance
- identity sensitivity
- `remember`
- `before`
- `previous`
- `past`
- or long input length

It does **not** activate on many naturally relational phrasings like:
- `we agreed`
- `we decided`
- `what did we discuss`
- `team`
- `together`

This means shared-context recall can silently disappear while still looking superficially normal.

This is currently the most dangerous failure mode.

### 4.3 Deep false-negative activation

Deep retrieval only opens when mode becomes:
- `REFLECTIVE`
- or `IDENTITY_SENSITIVE`

But `REFLECTIVE` requires ambiguity/confidence thresholds that many natural reflective prompts do not cross.

So a semantically deep query can remain in `FAST` and never open deep.

Again, this is a silent miss, not an explicit error.

### 4.4 TOOL priority masking

Because `TOOL` sits above `RETRIEVAL`, any prompt containing tool-like inspection words can route into `TOOL` before retrieval-shaped behavior is reached.

Examples:
- `search`
- `find`
- `inspect`
- `read`
- `fetch`
- `analyze`
- `debug`
- `check`

So prompts that are semantically retrieval-oriented but lexically tool-flavored may be masked away from the intended advisory path.

### 4.5 Archive lane — out of scope (this pass)

The advisory path also shapes an **archive** lane (`top_k=4` when active, weight `0.45`), gated by `TORMENT_ARCHIVE_RECALL=1` and lexical archive cues (`document`, `archive`, `chunk`, `pdf`, `notes`, `transcript`).

Archive retrieval has different semantics from continuity retrieval: it targets document/chunk recall rather than identity, relational, or deep continuity. The risk model in this document is built around core / relational / deep, not archive.

Therefore:

> Archive lane is acknowledged as part of the live advisory surface, but is **out of scope** for this first §2A validation pass. It should be validated in a follow-on archive-specific pass unless archive-heavy queries are explicitly added to the ratified set.

This keeps the framing honest without bloating the current round.

---

## 5. What "better than uniform-8" means

This must be ratified explicitly.

"Useful" is not a rubric.  
"Felt smarter" is not a rubric.  
"Produced richer output" is not a rubric.

For §2A, **outperforms uniform-8** means:

### 5.1 Retrieval superiority definition

Advisory outperforms baseline only if, on a ratified query set:

- it **reduces relational activation misses**
- it **reduces deep activation misses**
- it **does not materially degrade identity-anchor retrieval**
- and any private recall lost through core truncation is outweighed by improved lane selection and final relevance

### 5.2 Silent-loss principle

A retrieval change that increases stylistic richness while increasing silent recall misses is a failure.

The evaluation target is not conversational flourish. It is **memory selection correctness**.

### 5.3 Tie goes to baseline

If results are ambiguous, mixed, or difficult to distinguish with confidence, uniform baseline remains default.

The burden of proof is on advisory.

---

## 6. Ratified evaluation buckets

The test set should be explicitly divided by retrieval demand, not by generic prompt style.

### Bucket 1 — Core-heavy private recall

**Purpose:** detect **core truncation regression**

Queries in this bucket should naturally surface more than six relevant private memories so that the advisory `core=6` budget can be meaningfully tested against baseline.

**Corpus ratification:**

- **Authoritative gate:** a **curated seeded corpus** with a known set of relevant-per-query memories. Reproducibility matters more than ecological realism for the pass/fail decision — if the gate is a live character's memory state, results cannot be reproduced after the character evolves.
- **Confirmatory evidence:** a **live character corpus** spot-check, run after the curated pass, to test that seeded findings hold under ecological conditions. Live alone is not sufficient for the gate; curated alone is.
- **Invalid:** using only the live corpus, or substituting the live corpus for the curated one, regardless of appeal to realism.

**Success criterion:**
- advisory must not materially lose important private hits relative to baseline, unless compensated by stronger top-rank relevance

### Bucket 2 — Relational-needed but not obviously social

**Purpose:** detect **relational false negatives**

These are the most important queries in the whole protocol.

They should require shared/collaborative memory, but avoid the exact trigger tokens that currently activate `memory_need`.

Examples in spirit:
- `What did we agree about handling that issue?`
- `What was the team position on that earlier plan?`
- `Continue from the collaborative decision we reached.`

**Success criterion:**
- relational lane activates at an acceptably high rate
- advisory does not silently drop shared recall on these queries

This bucket is the highest-value bucket.

### Bucket 3 — Deep-needed but naturally phrased

**Purpose:** detect **deep false negatives**

These prompts should clearly require reflective or long-memory continuity, while avoiding the ambiguity markers that currently push the classifier into `REFLECTIVE`.

Examples in spirit:
- `How does this connect to the earlier refactor work?`
- `What pattern have we seen before?`
- `Is this repeating an older failure mode?`

**Success criterion:**
- deep lane opens when semantically justified
- deep misses remain below ratified tolerance

### Bucket 4 — Identity-sensitive

**Purpose:** verify **anchor stability**

Since anchor bonuses are supposed to remain invariant across paths, this bucket checks whether lane shaping or ranking side effects still cause identity-bearing memories to disappear, drift downward, or destabilize answer continuity.

**Success criterion:**
- anchor-bearing identity results do not regress in presence, placement, or continuity behavior

### Bucket 5 — Truly fast operational prompts

**Purpose:** verify **non-expansion discipline**

These prompts should stay simple, fast, and bounded.

**Success criterion:**
- no unnecessary deep activation
- no unnecessary relational fanout
- no ranking distortion from advisory shaping

This bucket protects against accidental overthinking.

---

## 7. Measured rates to report

The validation report must report concrete rates, not impressions. Each rate has a ratified tri-state threshold: **pass**, **localized fix required**, **systemic failure**.

These thresholds are ratified starting values. They may be revised by a subsequent doctrine update, but they are fixed for the present validation round — numbers are committed **before** the test is run, not interpreted after.

### 7.1 Relational activation miss rate

Among queries in bucket 2 that a human evaluator judges as relational-needed:

> what fraction fail to activate the relational lane?

This is the primary metric.

| Tier | Threshold | Meaning |
|------|-----------|---------|
| Pass | ≤ 20% | Advisory safe on this axis |
| Localized fix | 20%–40% | Keyword-set expansion or narrow trigger tuning |
| Systemic | > 40% | Classifier layer not ready; advisory stays gated |

### 7.2 Deep activation miss rate

Among queries in bucket 3 that a human evaluator judges as deep-needed:

> what fraction fail to activate deep retrieval?

| Tier | Threshold | Meaning |
|------|-----------|---------|
| Pass | ≤ 25% | Deep lane acceptably reachable |
| Localized fix | 25%–45% | REFLECTIVE threshold or mode priority adjustment |
| Systemic | > 45% | Classifier layer not ready; advisory stays gated |

Deep tolerance is slightly higher than relational because deep is structurally a gap-filler, not a primary lane.

### 7.3 Core truncation regression rate

Among bucket 1 queries:

> how often does advisory lose materially relevant private hits that uniform-8 would have surfaced?

| Tier | Threshold | Meaning |
|------|-----------|---------|
| Pass | ≤ 10% | `core=6` budget not materially harmful |
| Localized fix | 10%–20% | Core budget or re-rank adjustment |
| Systemic | > 20% | Core budget too tight for current corpus; revisit default |

### 7.4 Priority masking rate

Among queries containing both retrieval intent and tool-flavored language:

> how often does `TOOL` routing suppress the retrieval-shaped behavior that would otherwise be expected?

| Tier | Threshold | Meaning |
|------|-----------|---------|
| Pass | ≤ 20% | Mode priority acceptable |
| Localized fix | 20%–35% | Refine TOOL/RETRIEVAL precedence or keyword sets |
| Systemic | > 35% | Mode priority layer needs structural rework |

### 7.5 Anchor regression rate

Among bucket 4 identity-sensitive queries:

> how often do anchor-bearing results regress in visibility or rank stability?

| Tier | Threshold | Meaning |
|------|-----------|---------|
| Pass | **0%** (exact) | No anchor regression at all |
| Fail | **> 0%** | Any measurable regression blocks default-on |

Anchor regression is the one axis with no tolerance. Identity anchors are load-bearing for character continuity; even a small regression signals that lane shaping or weighting has unintended cross-cutting effects.

---

## 8. Evaluation methodology

### 8.1 Baseline condition

Run the ratified query set with advisory off.

This establishes the control behavior:
- flat `top_k=8`
- no advisory lane shaping

### 8.2 Advisory condition

Run the same query set with:
- `TORMENT_THINKING_ADVISORY=1`

Capture:
- task frame
- chosen mode
- memory plan
- lane budgets
- lane weights
- retrieved hits
- ranked final hits

### 8.3 Comparison rule

Each query must be evaluated along the whole chain:

1. semantic intent of the query
2. classifier/frame output
3. resulting lane plan
4. retrieval result set
5. final top-ranked usefulness

This prevents category errors.

A failure can then be assigned to the correct layer:
- classifier miss
- frame miss
- lane-budget issue
- lane-weight issue
- ranking issue

### 8.4 Landing artifact

The validation of §2A **cannot** land as a machine-enforceable contract-invariant test, the way the reinforce contract did. Semantic intent labels ("this query is relational-needed") require human judgment that no classifier or unit test can stand in for — and pretending otherwise would re-create, inside the test harness, the exact lexical-heuristic problem §2A is evaluating.

Therefore:

> The landing artifact for §2A is a **versioned evaluated query set with preserved human judgments**, not an executable pass/fail test file.

Required properties of the landing artifact:

- **Versioned:** the query set, intent labels, and evaluator attribution are stored under `docs/` (proposed: `docs/SECTION_2A_EVALUATION_SET_v1.md`) with a commit hash, so the same set can be re-run against future classifier changes and compared like-for-like.
- **Labeled:** each query carries a human-applied intent label (relational-needed, deep-needed, core-heavy, identity-sensitive, fast-operational) and — where applicable — a short rationale.
- **Judgment-preserved:** pass/fail assessments per query are recorded alongside the mode/plan/retrieval trace, not derived after the fact.
- **Non-automation:** the artifact is explicitly **not** rewritten into unit tests. If a future contributor attempts to collapse the semantic labels into a keyword-matching test, that is a doctrine violation of §11 and a regression of the very failure mode §2A is testing.

This is not a weakness of the validation protocol. It is an honest acknowledgement of the class of evaluation. Retrieval correctness under natural phrasing is a semantic property, and semantic properties require semantic judges.

---

## 9. Pass / fail doctrine

Axes are split into **hard-fail** and **soft-fail** categories. This split is doctrine, not heuristic — the distinction exists so that a composite evaluation with mixed results has a disciplined resolution path instead of becoming a judgment call.

### 9.1 Hard-fail axes (block default-on absolutely)

A failure on either of these axes blocks default-on regardless of results on other axes. No "compensating improvement" on another axis can override a hard-fail.

#### A. Anchor regression (§7.5)
Identity anchors are load-bearing for character continuity. Any measurable regression signals cross-cutting unintended effects. Tolerance is **0%**.

#### B. Systemic relational miss (§7.1 — "systemic" tier)
Relational miss rate > 40% means the classifier is systematically failing to activate shared-context recall on queries that semantically need it. This is the failure mode most likely to produce "plausible but wrong" answers in live use, because shared context is load-bearing for continuity but is silently absent in a way no downstream layer can detect.

### 9.2 Soft-fail axes (may enter bounded local-fix state)

A failure at the "localized fix required" tier on any of these axes does **not** block default-on outright if the rest of the evidence is otherwise strong. A systemic-tier failure on any of these still blocks default-on.

#### C. Deep activation miss (§7.2)
Localized fix tier: tune REFLECTIVE ambiguity/confidence thresholds or adjust mode priority. Systemic tier blocks default-on.

#### D. Core truncation regression (§7.3)
Localized fix tier: adjust `core_k` or rebalance top-k among lanes. Systemic tier blocks default-on.

#### E. Priority masking (§7.4)
Localized fix tier: refine TOOL/RETRIEVAL priority or trim the TOOL keyword set. Systemic tier blocks default-on.

### 9.3 Composite judgment rule

- Any **hard-fail** on §9.1 → default-on is **blocked**. Period. No appeal via other axes.
- All axes **pass** → default-on is **ratified** for follow-up action.
- Any **systemic tier** on §9.2 soft-fail axes → default-on is **blocked**; axis needs structural work.
- One or more **localized fix tiers** on §9.2 soft-fail axes, AND all hard-fail axes pass → default-on is **conditionally blocked**; ship the local fixes first, re-run the relevant bucket(s), then re-evaluate. This is the "bounded local-fix" state.

The hard/soft split is deliberately asymmetric: identity and relational semantics are the two axes where silent failure is most dangerous, because downstream layers cannot see them. Deep, core, and priority-masking failures surface more visibly in use and are therefore tolerable as local fixes.

---

## 10. Default-on rule

`TORMENT_THINKING_ADVISORY` flips to default-on **only if** the composite judgment in §9.3 evaluates to "ratified for follow-up action."

Operationally:

- All §7 rates at **pass** tier, AND
- Zero anchor regression (§7.5), AND
- Relational miss rate not at systemic tier (§7.1), AND
- No systemic-tier failure on any soft-fail axis (§9.2)

If any §9.2 soft-fail axis is at the **localized fix** tier:

- default-on remains blocked until the local fix is shipped and the affected bucket re-evaluated
- the fix is narrow and targeted (keyword set expansion, threshold adjustment, lane activation widening, mode priority refinement) — not structural

If any axis is at **systemic failure** tier, or anchor regression is non-zero:

- default-on remains blocked
- the classifier or lane-shaping layer needs structural work before §2A can re-enter evaluation

This doctrine gives three clear states — **ratified**, **bounded local-fix pending**, **systemically blocked** — with no room for composite judgment ambiguity.

---

## 11. What this document does not authorize

This document does **not** authorize:

- default-on enablement
- classifier expansion
- threshold tuning
- retrieval-weight changes
- semantic classifier replacement
- structural routing changes

Those belong to later ratified steps.

This document only defines the validation standard by which §2A should be judged.

---

## 12. Final doctrine summary

§2A is not a feature flourish. It is a truth test.

The advisory path is worthwhile only if it makes memory selection **more correct**, not merely more interesting.

The real danger is not overt breakage.  
The real danger is **silent recall loss hidden behind plausible output**.

So §2A should be judged by one principle:

> Fewer silent misses at the classifier and lane boundary, without sacrificing identity continuity or private recall integrity.

If that standard is met, advisory is ready to graduate.  
If it is not, the system stays gated until the boundary logic is made more truthful.
