# Checkpoint — Spirit-Return Warmth / Warmup Influence Trace (read-only)

**READ-ONLY CHARACTERIZATION — docs-only consolidated influence map. No code, no tests, no implementation,
no runtime execution, no remedy, no registry amendment.**

**Date:** 2026-06-19. **Baseline HEAD = origin/main = `51e7c86`** (latest commit *docs(cognition):
checkpoint tuned-scoring provenance lock*).

> Memory may shape context. Memory may not seize authority.

---

## 1. Status, method, and why static-only

This is a **static, source-grounded characterization** of how spirit-return **warmth / warmup** state
originates, persists, is scored, reaches spirit-return hits, and shapes retrieval/prompt assembly. It is
**characterization, not implementation** — it changes no behavior and proposes no remedy.

**Static inspection only — nothing was executed.** No `/retrieve`, no `fabric.query`, no ingest, no
endpoint, no loop, and no service startup were run. **Why:** `fabric.query` *can persist* warmup state
when the deep / spirit-return lane is active and at least one source-present deep hit is processed —
`WarmupTracker.get_or_create()` persists on each such processed hit — so any execution could mutate
`warmup_state.jsonl`. The trace therefore relied on source / docs / existing-test reading only.

**Prior coverage (this is NOT a wholly untraced area).** Prior work already covered: spirit-return
`/retrieve` **surfacing** (`docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_3_SPIRIT_RETURN.md`), the
**Gap C** summary relationship (`docs/CHECKPOINT_2026-06_MEMORY_TO_PROMPT_GAP_C_SPIRIT_RETURN_SUMMARY_RELATIONSHIP.md`),
**memory-to-prompt** pieces (`docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md` and the v0.2.x observability
checkpoints), and the **O6 / C-9** framing (Pre-Substrate Framing family F → Stage A **O6 parked**;
Database/Substrate Reconciliation **C-9** durable-soft-but-never-pinned). The new value here is the
**consolidated end-to-end static influence map**, not a claim of first discovery.

## 2. Source anchors (current)

- `torment_service/spirit_return.py` — `WarmupTracker`, `WarmupState`, `compute_warmth`,
  `select_return_mode`, `enrich_deep_memory_hit`, `inject_spirit_return_into_hit`.
- `torment_service/fabric.py` — the deep / spirit-return lane in `query` (the `get_or_create` →
  `enrich_deep_memory_hit` → `inject_spirit_return_into_hit` seam, ~3656–3720).
- `torment_service/retrieval_assembler.py` — block classification, voice cues / flavor, secondary
  ordering.

## 3. Influence map

### 3.1 Origin

- `WarmupTracker` tracks warmth **per deep-memory EID**; warmth is **retrieval-history-based**.
- **First appearance** seeds warmth at the floor (the "glimpse").
- **Repeat retrieval within the window** increments warmth (an additive step), **capped at 1.0**.
- **Far-apart appearances** reset **current warmth to the floor / prevent warmth buildup**; they do
  **not** reset the full `WarmupState` identity, `first_appearance_step`, or `appearance_count`
  (`appearance_count` still increments on each processed appearance).

### 3.2 Durability / persistence

- **Durable-soft.** State persists in `warmup_state.jsonl`, **append-only with periodic compaction**
  (auto-compaction on first load when the file has grown significantly).
- **Path-integrity hardened** — the storage path is derived through the canonical sanitizer
  (`ensure_within_base`) at construction and at each filesystem sink; traversal / outside-base paths
  raise.
- `get_or_create()` increments the appearance count, recomputes warmth, and **persists on each processed
  hit** (per §1). Load is lazy.

### 3.3 Scoring / attachment

- `enrich_deep_memory_hit()` reads `warmth = warmup_state.current_warmth`, may apply a **sustained-corridor
  floor** (a minimum warmth when a sustained-corridor condition holds), selects a **return mode** via
  `select_return_mode()`, and emits a spirit-return memory carrying `return_mode` + **`warmth_score`**.
- **SRG: observed optional metadata amplifier / watch item only.** When an SRG crystal / heartbeat marker
  is present, a Class-A path can raise a warmth floor (+ increment). This is recorded **only as an
  observed optional amplifier**; it is **not validated**, **not opened**, and the current Class-A behavior
  is **not** characterized here as a ratified design. SRG remains default-off per the registry.
- `inject_spirit_return_into_hit()` sets hit **strength = warmth × a mode-dependent multiplier**
  (resonance / surfacing / recollection) and attaches `spirit_return_mode` + `warmth_score` onto the hit.

### 3.4 Retrieval / prompt-shaping effects (retrieval assembly)

- **Hit strength** — warmth scales the re-entry strength via the per-mode multiplier (above).
- **Return-mode effects** — `return_mode` (surfacing / recollection / resonance) drives downstream
  classification and voice.
- **Block classification** — spirit-return hits are classified by `return_mode` + warmth instead of
  half-life: `resonance` with `warmth ≥ 0.5` → **identity block**; `surfacing` with `warmth ≥ 0.3` →
  relational block; otherwise situational. So warmth **can cause identity-block placement** for
  resonance / high-warmth spirit-return hits.
- **Model-visible voice cue / text** — spirit-return hits receive a voice-cue string by mode, and the cue
  + flavor are embedded into the assembled **block text** (a `[Returning Memory]`-style prefix).
- **Metadata / reason text** — `spirit_return_mode`, `warmth_score`, and a human-readable
  "spirit return (mode), warmth=…" reason are attached.
- **Secondary ordering** — `warmth_score` is the **secondary sort key** for spirit-return memories
  (primary key = score).

## 4. Boundary classification (evidence language)

- **Durable-soft** — persisted in `warmup_state.jsonl`; survives across queries / sessions.
- **Non-canon** — warmth / warmup writes no canon and no graph memory.
- **Prompt / retrieval-shaping** — affects strength, classification, block text, metadata, and secondary
  ordering.
- **O6 parked** — durable-soft, must-not-be-pinned (Stage A O6; Reconciliation C-9).
- **No remedy** proposed.
- **No canon / admission / promotion / writer-authority decision.** It **does** make
  retrieval / prompt-shaping decisions — including **possible identity-block placement** for resonance /
  high-warmth spirit-return hits — but those are retrieval-side shaping, not authority crossings.
- **No safety / unsafe verdict** is made.
- **Opens nothing:** no Writer Authority continuation; no Seed-Gov / P4 / source-sameness; no private
  cognition / dream runtime; no database / substrate mechanics. (The deep lane is *gated by* a source-row
  presence (beta) filter — observed, not opened. SRG is an observed optional amplifier — observed, not
  opened.)

## 5. Tuned-constant caution

The warmth floor, the repeat-retrieval increment, the cap, the per-mode strength multipliers, and the
block-classification warmth thresholds are **tuned constants**. They must **not** be casually changed or
"cleaned up." As with the ambiguity-clarify thresholds and the scoring buckets, any future change
requires **provenance archaeology** (source / tests / docs / history / operator context) first.

## 6. Anti-drift notes

- Do not overstate: warmth is **durable-soft retrieval shaping**, not identity authority, not canon, not
  governance. "Durable" ≠ "pinned" or "authority-bearing".
- Do not infer that warmth crosses into canon / identity authority; identity-**block placement** is a
  prompt-assembly classification, not a canon or admission decision.
- Do not infer that warmth reaching block **text** (voice cue) is "model-visible private cognition" — it
  is ordinary retrieval-prompt shaping of already-admitted memory.
- Do not infer SRG is "running" from the Class-A floor: it is an observed optional amplifier, default-off.

---

*Read-only characterization checkpoint only. Static source/docs inspection; no runtime executed, no
warmup state mutated, no behavior changed, no remedy, no registry amendment. Spirit-return warmth is a
durable-soft, non-canon, prompt/retrieval-shaping signal (O6 parked) — no canon / admission / promotion /
writer-authority decision; it does make retrieval-side shaping decisions including possible identity-block
placement. Audit observes authority and does not become authority. Memory may shape context. Memory may
not seize authority. Database / substrate remains last.*
