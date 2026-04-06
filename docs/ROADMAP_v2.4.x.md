# TORMENT 2.4.x Improvement Roadmap

This roadmap assumes the current direction is fundamentally correct:

- Memory substrate is strong
- Spirit return is a real system, not decorative fluff
- Semantic memory space is the epistemic core
- Spine / MCP belongs to the capability-governance layer
- The goal is not to bloat the architecture, but to make existing layers more real, more testable, and more trustworthy

The roadmap is organized into:

1. Safe now — keep / validate / consolidate
2. Gated next — valuable, but keep behind flags or narrow rollout
3. Blocked until provenance — structurally unsafe until ingest / origin tracking is improved

---

## 1. Safe Now

These are worth keeping and using now because they are bounded, low-risk, or primarily observability / hygiene.

### A. Live Agent Feedback Loop

Keep.

What it really is right now: negative-only retrieval hygiene, not true positive learning yet. Safe because it can penalize noisy retrieval but cannot strongly self-reinforce.

Why it belongs here: helps memory selection without destabilizing the system, fits the existing memory architecture, improves practical retrieval behavior in live use.

What to do: keep it on, describe it honestly as weak / asymmetric feedback, monitor whether it is meaningfully filtering bad retrieval or mostly inert.

### B. Geometric Context Harvester Wiring

Keep.

This is good because it activates already-existing stance/geometric logic, it is read-only, and it uses real kernel/character state instead of decorative defaults.

Why it matters: it makes stance modulation truthful, reduces dead-code behavior, and is system-aligned, not feature sprawl.

### C. WarmupTracker Compaction

Keep.

Pure operational hardening: append-only warmup state gets cleaned up, reduces file bloat, low architectural risk.

### D. Alignment Endpoint / Alias

Keep.

Observability: if the sidecar / thinking alignment exists, you should be able to see it. Helps validate whether routing logic and advisory thinking are aligned.

### E. Spirit Return Status Enhancement

Keep.

Also observability: spirit return is one of the most distinctive parts of TORMENT. More runtime visibility is good, no mutation risk.

---

## 2. Gated Next

These are worth pursuing, but should remain behind flags, controlled rollout, or explicit testing because they affect core behavior.

### A. Memory Plan -> Real Query Integration

Keep gated.

This is not about "fixing memory." It is about making memory selection smarter by letting the thinking layer shape which memory lanes are emphasized.

This sits inside the epistemic/retrieval layer: semantic/core/shared/deep retrieval, lane-specific top_k, lane-specific weighting, better matching between query type and retrieval shape.

Why it matters: this is probably the main next step for better memory selection. It makes the semantic memory space more intentional. It helps distinguish live-social, identity-sensitive, relational, and deep-memory queries.

Why it stays gated: it touches the core query path. Even correct logic can subtly alter system feel. It needs real before/after testing on representative queries.

Testing requirement before broader enablement: identity anchors should not disappear from top results on identity-sensitive queries, deep memory should remain appropriately bounded, lane weighting should improve relevance not just change it.

Recommended state: `TORMENT_THINKING_ADVISORY=0` by default. Enable only for deliberate testing until query behavior is validated.

### B. MCP / Spine-Enabled Capability Usage

Gated, narrow, policy-first.

MCP matters as a separate layer. That does not mean broad autonomous tool use should be turned on by default.

The clean model is: semantic memory space = epistemology / what the system knows, recalls, and weighs. Spine = governance / routing / allowed path. MCP = capability surface / external tools and actions.

This means MCP belongs in TORMENT, but as a governed capability layer, not as general freeform autonomy.

Good next direction: narrow MCP operations, explicit permissions, auditable calls, provenance on tool-originated outcomes, easy disable / rollback.

This should stay gated until the provenance layer is stronger.

### C. Thinking-Enhanced Live Agent Memory Selection

Gated.

For live agents, the most useful next step is not "more autonomy." It is better memory selection, maybe better stance-aware selectivity, but with minimal latency cost.

This means use gated advisory retrieval improvements first. Do not yet overload live agents with the full heavy cognition path unless latency is proven acceptable.

---

## 3. Blocked Until Provenance

These are structurally blocked until origin tracking and ingest-level provenance are real.

### A. Archivist Write-Back

Blocked. Keep disabled.

Reason: once the system writes memories from cognition back into the fabric, origin becomes critical. Without provenance through ingest, recursion protection is unreliable. Self-reinforcement becomes hard to see and hard to stop.

Required before enabling:
- Ingest must accept structured provenance
- Written memories must preserve that provenance
- Query / audit must be able to distinguish: user input, role output, derived memory, tool result, archivist write-back
- Recursion guards must operate on the actual ingested memory provenance, not just the proposal object

Until that exists: keep `TORMENT_ARCHIVIST_WRITEBACK=0`.

### B. Broad Autonomous Tool Use

Blocked until provenance + policy are stronger.

If tools can be used "by themselves," then you need: permission scope, origin/provenance of actions, audit trail, rollback / disable path, rate limits, trusted operation registry, boundaries on what can be initiated.

MCP presence is not the blocker. Provenance + policy integrity is the blocker. This is not "never." It is not yet, not until the rails are real.

### C. Stronger Self-Writing Cognition Loops

Blocked until provenance.

Anything that turns cognition, memory reflection, role outputs, or tool outputs into new persistent memory must wait until provenance is first-class.

Otherwise the system can no longer reliably tell what it observed, what it inferred, what it generated, and what it acted upon. That is the line.

---

## Clarifying the Architecture

To reduce confusion, the current architecture should be thought of like this:

**Layer 1 — Semantic Memory / Epistemology.** The main memory substrate: semantic retrieval, memory graph, identity / relational / situational memory, archive / deep memory, spirit return as a special resurfacing mechanism. This is where "better memory selection" mostly lives.

**Layer 2 — Stance / Modulation / Geometric Interpretation.** Shapes how the system weighs and responds: geometric context, stance policy, ambiguity tolerance, social resonance, confidence modulation.

**Layer 3 — Spine / Governance.** Decides what path to use, what operations are allowed, what should be audited, what should remain bounded.

**Layer 4 — MCP / Tool Capability.** The plug-in action layer: external functionality, capability access, tool calling, integration surface. Important, but not the same thing as memory or epistemology.

---

## Practical Priorities for 2.4.x

**Highest-value priority: Better memory selection.** Validate Memory Plan retrieval shaping, improve semantic retrieval choice by query type, preserve identity anchors, keep deep memory bounded, treat spirit return as a distinct resurfacing lane not generic retrieval.

**Second priority: Provenance plumbing.** The structural prerequisite for the next wave: archivist write-back, tool-result memory, stronger autonomous actions, safer self-writing loops.

**Third priority: Bounded MCP capability refinement.** Not broad autonomy. Refine MCP as governed, auditable, narrow, optional, easy to disable.

---

## What Not to Do in 2.4.x

- Do not broadly enable autonomous tool use
- Do not enable archivist write-back before provenance is fixed
- Do not treat MCP presence as justification for general agent initiative
- Do not over-modify spirit return when the surrounding loops are the real issue
- Do not add more conceptual layers unless an existing layer is truly blocked

---

## Final Summary

**Safe now:** live agent feedback loop, geometric context harvester, warmup compaction, alignment endpoint / alias, spirit return status enhancement.

**Gated next:** Memory Plan -> real query integration, thinking-enhanced live memory selection, narrow policy-gated MCP capability usage.

**Blocked until provenance:** Archivist write-back, broad autonomous tool use, stronger self-writing cognition loops, persistent tool-result memory without origin tracking.

**Bottom line:** The memory system does not need to be reinvented. Spirit return does not appear to be the main current problem. The main next steps are: (1) validate smarter retrieval / memory selection, (2) strengthen provenance, (3) keep MCP/tool capability narrow and governed until provenance catches up. That keeps TORMENT true to itself while still moving toward a more capable system.
