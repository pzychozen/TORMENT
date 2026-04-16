# §2A Validation Framing — Memory Plan → Real Query Integration

**Status:** DRAFT FOR RATIFICATION  
**Scope:** Validation framing only. No implementation change is proposed in this document.  
**Target:** `TORMENT_THINKING_ADVISORY` and its live effect on `/agent/query` retrieval shaping.

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

The validation report must report concrete rates, not impressions.

### 7.1 Relational activation miss rate

Among queries in bucket 2 that a human evaluator judges as relational-needed:

> what fraction fail to activate the relational lane?

This is the primary metric.

### 7.2 Deep activation miss rate

Among queries in bucket 3 that a human evaluator judges as deep-needed:

> what fraction fail to activate deep retrieval?

### 7.3 Core truncation regression rate

Among bucket 1 queries:

> how often does advisory lose materially relevant private hits that uniform-8 would have surfaced?

### 7.4 Priority masking rate

Among queries containing both retrieval intent and tool-flavored language:

> how often does `TOOL` routing suppress the retrieval-shaped behavior that would otherwise be expected?

### 7.5 Anchor regression rate

Among bucket 4 identity-sensitive queries:

> how often do anchor-bearing results regress in visibility or rank stability?

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

---

## 9. Pass / fail doctrine

### §2A passes only if all of the following hold:

#### A. Identity safety holds
Identity-sensitive prompts do not show anchor-bearing regression.

#### B. Relational recall improves or at least does not silently degrade
Relational-needed queries do not suffer unacceptable miss rates.

#### C. Deep recall becomes available when semantically needed
Deep-needed queries are not systematically trapped in `FAST`.

#### D. Core truncation remains bounded
Any private recall loss introduced by `core=6` remains limited and is offset by superior lane-aware retrieval quality.

#### E. Priority masking is not materially harmful
`TOOL` precedence does not suppress retrieval-shaped behavior at a rate that makes advisory misleading.

---

## 10. Default-on rule

`TORMENT_THINKING_ADVISORY` should flip to default-on **only if** the validation report shows:

- low relational miss rate
- low deep miss rate
- no meaningful anchor regression
- bounded core truncation cost
- no material priority-masking harm

If one dimension fails but is clearly local, the fix is targeted:
- keyword set expansion
- threshold adjustment
- lane activation widening
- mode priority refinement

If failures are systemic across buckets, the classifier layer is not ready for default-on.

In that case, §2A remains gated.

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
