# Memory-to-Prompt Automation v0.2 — Observability Lane

*Character-memory observability for memory-to-prompt automation. First
v0.2 implementation lane: a pure-additive, read-only telemetry surface
that makes visible what memory shaped the character's next response —
so we can verify character continuity, voice, callbacks, emotional
recall, relationship memory, symbolic resonance, and tool-aware
dialogue before changing behavior. Inherits the v0.1 character-first
hierarchy verbatim. Does not authorize disk persistence in this
revision, behavior changes, schema migrations, FILTER-A modifications,
endpoint changes, new tool families, schedulers, or any new test
wiring beyond the additive helper unit tests scoped to Slice S4.*

**Status:** Advisory doctrine, v0.2 (observability lane). Trio
decisions applied via S3 promotion 2026-05-25 (pzychozen + GPT +
Claude). Pending operator commit; on commit becomes the load-bearing
reference for the memory-to-prompt observability territory and the
named seam to the v0.2.x extension slices (deferred ledger persistence,
profile-aware intent classification, character-context enrichment,
spirit-return voice-cue verification, archive-FILTER-A application).
Subsequent versions (v0.2.x, v0.3, v1.0) supersede this one only after
their own trio ratification.
**Date:** 2026-05-25.
**Author:** Trio working session. Drafted by Claude across the S1
read-only audit (2026-05-25) and the S2 scratch framing draft
(2026-05-25); reviewed and revised by GPT; ratified by pzychozen.
Promotion (S3) prepared 2026-05-25 with the seven trio-ratified
decisions applied (§ S3 Decisions Applied below).
**Authority:** Advisory doctrine. v0.2 observability lane is the
load-bearing reference for memory-to-prompt observability and the
named seam to any future implementation that extends the audit
surface (disk persistence, profile-aware intent classification,
character-context enrichment, spirit-return voice-cue verification,
archive-FILTER-A application). Subsequent versions supersede this one
only after their own trio ratification.
**Scope:** Versioned advisory doctrine for the first v0.2
implementation lane of memory-to-prompt automation: read-only
character-memory observability. Pure design surface plus a pre-ratified
helper / module / flag / response-shape contract. No implementation
authorized by this document; implementation begins at Slice S4 after
this promotion lands.

**Anchor docs:**

- `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.1.md` (DRAFT v2; canonical
  parent doctrine).
- `docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md` (§§7.1, 9.1, 10.5, 11.3).
- `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md` (§§3, 6, 9.3).
- `docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md` (Invariants 13, 14).
- `docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md` (§2.1 canonical
  event ledger vocabulary; §§5 fragility handles; §6.2 deferred
  brainstorm mechanisms).
- `docs/PROVENANCE_DOCTRINE_v2.4.x.md` (Invariants C, F).
- `docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md` (§§4–8, 11).
- `docs/CHARACTER_SYSTEM.md` (tiers, spirit-return voice layer).
- `docs/MCP_CAPABILITY_BOUNDARY.md`.
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md` (Part 9 invariants 1, 4, 5,
  10 of Memory-to-Prompt v0.1 §5).

**Lineage:**

1. 2026-05-25 — Memory-to-Prompt v0.1 DRAFT v2 authored (gate-start
   survey + character-first reframe; operator + GPT ratification of
   the character-first reframe with the "Governance is subordinate in
   purpose, but load-bearing in substrate-criticality" canonical
   phrasing).
2. 2026-05-25 — v0.2 planning proposal ratified with one framing
   correction (lane named *"character-memory observability for
   memory-to-prompt automation"*, not "telemetry for telemetry's
   sake").
3. 2026-05-25 — Slice S1 read-only code-surface audit completed;
   findings recorded in conversation context for this session
   (five gaps identified: dropped FILTER-A exclusions, archive_hits
   not passing FILTER-A, selection_log lacking structured
   classification rationale, spirit-return summary separated from
   assembled output, no tool-result advisory summary on assembled
   output).
4. 2026-05-25 — Slice S2 scratch framing draft authored:
   `scratch/MEMORY_TO_PROMPT_AUTOMATION_v0.2_OBSERVABILITY_FRAMING_DRAFT_2026-05-25.md`.
   Preserved as lineage; not amended by S3.
5. 2026-05-25 — Slice S3 promotion (this document) prepared with the
   seven trio-ratified decisions applied (§ S3 Decisions Applied
   below). Scratch S2 draft preserved unchanged for lineage.

---

## S3 Decisions Applied (ratified at promotion)

The following seven decisions were ratified by the trio at S3
promotion and are installed throughout this doctrine. They are
recorded here as a single block so future readers can audit the
delta from scratch framing draft to ratified v0.2.

1. **Ledger choice — Option C (response-only, no disk persistence).**
   v0.2 observability returns the `assembly_audit` payload in the
   `/retrieve` response only (closure-reality correction 2026-05-27;
   `/agent/query` parity deferred per §4.3). No disk persistence in
   this revision. Reason: keep Slice S4 and Slice S5 small;
   prove the audit payload shape in live use before any ledger
   persistence work begins. Disk-persistent ledger writes become
   v0.2.x (or v0.3) after the response-side audit shape is verified
   under live trio use. Options A (extend `memory_events.jsonl`) and
   B (new `assembly_audit.jsonl`) remain available for the future
   slice; the choice between them is downstream of v0.2 observability
   evidence.
2. **Helper module — `torment_service/assembly_audit.py`.** New
   module. Reason: clean separation from FILTER-A. `filter_llm_facing`
   in `governance.py` stays focused on surface exclusion; assembly
   audit becomes its own pure-read observability helper. Both honor
   the PROVENANCE_DOCTRINE Invariant C "one canonical derivation"
   pattern at their respective concerns.
3. **Helper name — `build_assembly_audit`.** Function-style name
   matching the assembly-side `assemble_context()` vocabulary.
4. **Request flag — `include_assembly_audit: bool = False`.** Per-call
   opt-in. Default false preserves backward-compat for existing
   callers including `live_agent/memory_bridge.py`. v0.1 Invariant 9
   (no global env-var toggle for governance defaults) is honored.
5. **Archive-FILTER-A fix deferred.** v0.2 observability *reports*
   the archive-FILTER-A gap (S1 finding §3.2 / this doc §3.2) via the
   honest `archive_filter_applied: false` field in the audit payload.
   v0.2 does NOT fix the gap. The fix is a separate ratifiable slice
   (working name v0.2.4 or v0.3) scheduled downstream of v0.2
   observability evidence. **Closure note (v0.2.4 — 2026-05-27):**
   gap closed by v0.2.4-A1 (Option A — per-chunk governance metadata
   on archive chunks + unconditional `filter_llm_facing` application
   at `/retrieve` before `assemble_context()`). Production audits
   now report `archive_filter_applied=True` and surface
   `archive_excluded`. See
   `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_4_ARCHIVE_FILTER_A.md`.
6. **v0.1 block-count correction parked as future cleanup.** The
   `MEMORY_TO_PROMPT_AUTOMATION_v0.1.md` references to "four-block
   precedence" should read "five-block precedence" (the missing
   block is `BLOCK_REFERENCE` between identity and relational; §8 of
   this doc has the detail). v0.2 does NOT amend v0.1; the
   correction is flagged as a future v0.1.1 cleanup slice.
7. **No-code / no-test / no-endpoint-change discipline for S3.** This
   promotion document is doctrine only. Implementation begins at
   Slice S4 (helper code) after this promotion lands. Slices S5
   (opt-in wiring) and S6 (live verification) and S7 (closure
   checkpoint) follow per §7.

---

## Posture (load-bearing)

> **Memory-to-Prompt Automation v0.2 observability lane is the first
> v0.2 implementation slice — a pure-additive, read-only telemetry
> surface that makes visible what memory shaped the character's next
> response. It does not change behavior, does not mutate memory, does
> not modify FILTER-A, does not introduce new tool families, does not
> introduce a scheduler, does not persist to disk in this revision,
> and does not amend v0.1 doctrine. Implementation begins at Slice S4
> (after this doctrine is committed) and lands as additive code paths
> around the existing `fabric.query()` → `filter_llm_facing` →
> `assemble_context()` chain.**

This lane is the smallest practical step that moves memory-to-prompt
automation forward without crossing any forbidden line. It inherits
v0.1's character-first hierarchy verbatim:

> *TORMENT is character memory first, agent memory second.*
>
> *Memory-to-prompt exists to let retrieved memory shape character
> presence, continuity, roleplay, and expression.*
>
> *Governance is subordinate in purpose, but load-bearing in
> substrate-criticality.*

> *Automatic is allowed. Autonomous is not.*

The observability lane is pure automation (no human-in-the-loop
per-call) that is also pure observation (no autonomous action and no
disk persistence in this revision).

---

## §0 — TL;DR

The v0.2 observability lane records, on every retrieval that feeds an
LLM-facing surface, what memory the character actually drew from to
shape its next response. It propagates the FILTER-A exclusions that
already exist but are currently dropped, structures the classification
rationale already implicit in `_classify_core_hit()`, attaches the
spirit-return summary already present in `character_context` to the
assembled output, and surfaces a tool-result advisory summary so
character speech about tools is grounded in a visible record. It also
honestly reports the open archive-FILTER-A gap (S1 finding §3.2)
without silently fixing it; the fix is a separate ratifiable slice
(v0.2.4 or v0.3).

The lane is pure-additive code (helper `build_assembly_audit` in new
module `torment_service/assembly_audit.py` + opt-in
`include_assembly_audit: bool = False` request parameter surfacing on
`/retrieve` in v0.2 first revision; `/agent/query` parity is a
separate ratifiable slice — see §4.3); no existing behavior changes.
The telemetry shape mirrors FILTER-A's `excluded[]` pattern (one
canonical helper, response shape never overloads existing keys).

**v0.2 first revision is response-only.** No disk persistence
(ratified Option C; ledger persistence becomes v0.2.x after live
audit-shape verification). The audit payload is returned in the
response when the per-call flag is true.

The v0.1 doc has a small wording miscount (says "four-block
precedence"; actual count is five — `BLOCK_REFERENCE` exists between
identity and relational). Flagged in §8 for a future v0.1.1 cleanup
pass; not amended by v0.2.

> **Closure note (v0.2.4 — 2026-05-27):** the archive-FILTER-A gap
> honestly reported by this v0.2 first revision (S3 Decision 5; §3.2)
> has been closed by v0.2.4-A1 (Option A — per-chunk governance +
> unconditional `/retrieve` filter). v0.2 doctrine remains
> historically accurate for the first-revision posture; the v0.2.4
> closure record is
> `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_4_ARCHIVE_FILTER_A.md`.

---

## §1 — Purpose and center question

### §1.1 Purpose (load-bearing)

> **Character-memory observability for memory-to-prompt automation.**
>
> Make visible what memory shaped the character's next response, so we
> can verify character continuity, voice, callbacks, emotional recall,
> relationship memory, symbolic resonance, and tool-aware dialogue
> before changing behavior.

The purpose statement is operator-ratified verbatim. It is the spine
of the lane. Every section answers to it. Observability that does not
serve character legibility is out of scope.

### §1.2 Center question

> **What memory did the character actually draw from to shape its next
> response, with what provenance, at what authority position, in what
> assembled block, under what profile, with what was excluded and why?**

The question has seven clauses, each mapping to one telemetry
sub-shape (§4):

- *"What memory"* → per-hit list with eids / chunk_ids and final
  scores.
- *"With what provenance"* → `provenance_type`, `provenance_tool_name`
  per hit; voice-axis fields if present.
- *"At what authority position"* → Cluster 2 §11.3 three-modifier for
  tool-result rows; Track A §3.4 Authority axis machinery for the
  rest.
- *"In what assembled block"* → `BLOCK_IDENTITY` / `BLOCK_REFERENCE` /
  `BLOCK_RELATIONAL` / `BLOCK_SITUATIONAL` / `BLOCK_ARCHIVE` placement
  plus structured classification basis (mtype / canon / tier /
  half_life / spirit_return_mode).
- *"Under what profile"* → profile name (`companion` / `research` /
  `narrator` / `balanced`) and the actual per-block budget weights
  applied.
- *"With what was excluded and why"* → propagated FILTER-A `excluded[]`
  with reason codes (`non_shareable` / `collective_export_blocked` /
  authority guard rejection), plus skipped-by-budget rows from the
  selection_log.
- *"And how does the character recognize what surfaced?"* →
  spirit-return summary with mode breakdown and warmth average,
  tool-result advisory summary with count and Cluster 2 §11.3
  three-modifier.

### §1.3 Why observability is the right first lane

Three reasons, all anchored:

1. **Lowest substrate risk.** Pure read. No mutation, no behavior
   change, no schema migration, no disk persistence in this revision.
   The risk floor is at v0.1 Invariant 1 (controller-owned assembly),
   Invariant 2 (governed retrieval surface), Invariant 8 (audit
   visibility INCREASES, not decreases). Observability extends
   Invariant 8 by adding visibility; it cannot violate the others.
2. **Prerequisite for every later shaping lane.** Profile-aware intent
   classification (deferred v0.2.1), character-context block enrichment
   (deferred v0.2.2), spirit-return voice-cue verification (deferred
   v0.2.3), archive-FILTER-A application (deferred v0.2.4) — each of
   these needs observability to be calibratable. *"Automate observation
   of the agent loop before expanding the agent loop"* — the principle
   that landed Tier 1 + Tier 2 at 6,600 turns with zero aborts.
3. **Character legibility.** The character (and the operator) cannot
   verify continuity, voice fidelity, callback grounding, or
   tool-aware dialogue authenticity without seeing what memory
   actually entered the prompt. v0.2 observability is what makes
   character expression *legible to itself and to the operator*.

---

## §2 — What the observability lane records

The lane records, per retrieval call that feeds an LLM-facing surface,
the following structured information. Each field is anchored to an
existing code site or doctrine reference.

### §2.1 Request metadata

- `workspace_id`, `agent_id`, `query` (the input query string),
  `profile` (assembler profile requested), `top_k` (core retrieval
  cap), `token_budget` (assembly cap), `timestamp` (epoch).
- `surface` (always `SURFACE_LLM_CONTEXT` for memory-to-prompt; the
  field is present so a future v0.2.x can extend to other surfaces
  without breaking the schema).
- `embedder` snapshot (provider / model / dim) — pulled from
  `embed_context` already returned by `fabric.query`. Closes a
  CHECKPOINT Level 3-style invariant verification at the
  observability layer.

### §2.2 FILTER-A application record

- `core_hits_in_count` — number of candidates handed to
  `filter_llm_facing`.
- `core_hits_out_count` — number that survived the filter.
- `excluded` — the `_filter_excluded` list propagated from
  `fabric.py:4158` (currently dropped before reaching the response
  shape; v0.2 surfaces it). Each entry: `{eid, excluded_reason}`.
- `authority_guard_rejected` — count of `NonAuthoritativeDeepHit`
  rejections per H4d (`governance.py:404–408`). Expected zero in
  normal operation; non-zero is a finding.
- `archive_hits_count` — number of archive chunks that entered the
  assembly path.
- `archive_filter_applied` — explicit boolean. **Today (v0.2 first
  revision): false** (per S1 finding §3.2). The field is present so
  future readers can see whether the gap was closed by a later slice.
  **Closure note (v0.2.4 — 2026-05-27):** v0.2.4-A1 wired
  `filter_llm_facing` unconditionally at `/retrieve` between
  `ArchiveStore.retrieve()` and `assemble_context()`; this field is
  now `True` in every production `/retrieve` audit response, and
  `filter_a` additionally carries `archive_excluded` (archive-shaped
  exclusion records — see closure-note at §4.2).

### §2.3 Assembled context summary

- `profile_used` — actual profile resolved (after fallback if
  `req.profile` was unknown).
- `profile_weights` — the per-block weight dict actually applied.
- `tokens_used` and `token_budget` from `AssembledContext`.
- `block_token_counts` — per-block tally (already on
  `AssembledContext`).
- Per-block summary `{block_type, candidates_seen, selected_count,
  tokens_used, classification_basis: [structured per-hit reasons]}`.

### §2.4 Structured classification basis (§3 gap #3)

For every accepted block, the basis on which `_classify_core_hit()`
chose its block type, expressed as a small structured record:

```
{
  eid: <int>,
  block_type: "identity_context",
  basis: {
    primary: "mtype=seed_canon",
    secondary: [],
  }
}
```

Or for spirit-return:

```
{
  eid: <int>,
  block_type: "identity_context",
  basis: {
    primary: "spirit_return_mode=resonance",
    secondary: ["warmth_score=0.72"],
  }
}
```

The basis field is *derived from existing logic in
`_classify_core_hit`*; no new classification rules. It surfaces
structured rationale rather than a free-text `reason` string.

### §2.5 Spirit-return summary attached to assembled output (§3 gap #4)

The spirit-return summary already lives on `character_context`
(returned by `fabric.query()`) but is not attached to
`AssembledContext`. v0.2 surfaces it alongside the assembly summary:

```
spirit_return_summary: {
  total: <int>,
  by_mode: {resonance: <int>, surfacing: <int>, recollection: <int>},
  avg_warmth: <float>,
  any_entered_prompt: <bool>
}
```

`any_entered_prompt` is computed by checking the selected blocks for
`from_spirit_return=True` in metadata.

### §2.6 Tool-result advisory summary (§3 gap #5)

For all hits with `provenance_type=tool_result` that entered the
assembled output, a summary:

```
tool_result_summary: {
  count_in_prompt: <int>,
  three_modifier: "(low-authority, decay-bounded, tool_result)",
  tool_names: [<list of distinct provenance_tool_name>],
  per_hit: [
    {eid, tool_name, block_type, score}, ...
  ]
}
```

The `three_modifier` is the Cluster 2 §11.3 ratified default verbatim;
v0.2 does not introduce a per-tool-family variant (deferred to v0.3
per Cluster 2 §11.7).

### §2.7 Character context summary (subset of `character_context`)

A small fixed subset of character-context fields surfaced alongside
the assembly summary, so character legibility does not require a
separate fetch:

```
character: {
  character_name: <str>,
  seed_basin_role: <str>,
  drift_score: <float>,
  drift_direction: <str>,
  relational_count: <int>
}
```

Source: existing `character_context` from `fabric.query()`. No new
fields read from `CharacterState`; v0.2 is read-only.

### §2.8 What the lane does NOT record

- No raw embedding vectors.
- No payload text beyond what's already in the assembled blocks.
- No API keys / tokens / secrets (FILTER-A §10.2 W7 redaction
  discipline applies to any future ledger writes — but no ledger
  writes occur in this revision per S3 Decision 1).
- No mutation logs (the lane is read-only).
- No LLM responses or model output (out of memory-to-prompt scope —
  that's a separate response-side observability question).
- No `CharacterState` write-site information beyond what
  `character_context` already exposes.
- **No disk-persistent records in this revision** (per S3 Decision 1
  — Option C, response-only).

---

## §3 — The five S1 gaps the lane addresses

These five are the findings from Slice S1 (read-only code-surface
audit, 2026-05-25). v0.2 observability surfaces all five through the
telemetry shape in §4. None of these is fixed by v0.2 in the sense
of changing behavior; v0.2 *reports* them so subsequent slices can
fix what needs fixing.

### §3.1 Dropped FILTER-A exclusions

**Finding (S1):** `filter_llm_facing` returns
`{"results", "excluded"}`. `fabric.py:4158` captures
`_filter_excluded = _filtered["excluded"]`. The excluded list is
consumed locally by the continuity_debug summary block and then
dropped — it does not propagate to the `fabric.query()` return shape,
to `assemble_context()`, or to the `/retrieve` / `/agent/query`
response.

**v0.2 lane:** Propagate `_filter_excluded` through the
`fabric.query()` return shape (additive), surface it on the assembled
output (additive), expose it on the response shape under
`assembly_audit.filter_a.excluded`. Pure-additive; no behavior change.

### §3.2 Archive hits not passing FILTER-A and no governance metadata

**Finding (S1):** `ArchiveStore.retrieve()` returns chunk dicts with
no `governance` field. Archive hits flow into `assemble_context()` →
`_archive_hit_to_block()` → `BLOCK_ARCHIVE` candidates without passing
`filter_llm_facing`. Today the risk is bounded because archive chunks
don't carry governance flags at all, but the gap means there's no
surface filter to catch them if they ever do.

**v0.2 lane:** Honestly report the gap via the
`assembly_audit.filter_a.archive_filter_applied = false` field.
**v0.2 does NOT fix the gap** (S3 Decision 5). The fix is a separate
ratifiable slice (v0.2.4 or v0.3) that decides between (a) adding
governance metadata to chunks + applying FILTER-A in
`_archive_hit_to_block`, (b) extending FILTER-A's surface enum with
`archive_context` and a new `archive_hit_filter` helper, or (c)
declaring archive chunks operator-only content doctrinally. The
choice is downstream of trio review of v0.2 telemetry findings under
live use.

**v0.2.4 status (closure annotation, 2026-05-27):** Option A landed
in v0.2.4-A1. Per-chunk governance metadata was added to
`ArchiveChunk` (additive, backward-compatible — legacy chunks
default to governance-less default-pass); `filter_llm_facing` gained
a keyword-only `id_field: str = "eid"` parameter so archive hits can
be filtered through the same canonical helper with chunk_id-shaped
exclusion records; `/retrieve` applies the filter unconditionally
between `ArchiveStore.retrieve()` and `assemble_context()` (filter
site preserves the canonical FILTER-A §5 "one canonical derivation"
pattern; `_archive_hit_to_block` and `assemble_context()` are
untouched). Option B was rejected as subsumed by A (the surface
enum adds naming without behavior at the current flag set). Option
C was rejected on the *"Memory may shape context. Memory may not
seize authority"* anchor — archive content enters LLM-facing
context once assembled, so defense-in-depth applies regardless of
the operator-curated assumption. Closure record:
`docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_4_ARCHIVE_FILTER_A.md`.

### §3.3 `selection_log` lacking structured classification rationale

**Finding (S1):** `AssembledContext.selection_log` already records
every accepted and skipped candidate with `{block_type, eid,
chunk_id, score, token_count, action, reason}` where `reason` is a
free-text string built by `_hit_to_block()`. The *classification basis*
— *why* a hit landed in BLOCK_IDENTITY vs BLOCK_RELATIONAL — lives in
`_classify_core_hit()` (`retrieval_assembler.py:144–185`) and uses
mtype / canon / tier / half_life / spirit_return_mode / warmth_score.
The selection_log shows what was selected but not the structured
classification logic that produced the block_type assignment.

**v0.2 lane:** Enrich each selection_log entry with a structured
`classification_basis: {primary, secondary}` derived from the
existing classification rules in `_classify_core_hit`. No
classification rule changes; the basis is computed from the same
inputs. Surface in `assembly_audit.assembly.classification_basis` per
hit. Pure-additive.

### §3.4 Spirit-return summary separated from assembled output

**Finding (S1):** `assemble_character_context()` (called from
`fabric.query()`) produces a `spirit_return_summary` dict with
`{total, by_mode, avg_warmth, recommendations}` per
`CHARACTER_SYSTEM.md` "Spirit Return Summary". This summary lives on
`character_context` returned from `fabric.query()` but is not attached
to `AssembledContext` and not surfaced alongside the assembled blocks
in the `/retrieve` response.

**v0.2 lane:** Attach the spirit-return summary to the
`assembly_audit.spirit_return_summary` field (§2.5 shape). Compute
`any_entered_prompt` from the selected blocks' metadata. Pure-additive.

### §3.5 No assembled-output summary of `tool_result` advisory presence

**Finding (S1):** Every hit with `provenance_type=tool_result`
already carries `provenance_type` and `provenance_tool_name` per
`TOOL_RESULT_RETRIEVAL_SEMANTICS.md` §2.2 Change B (shipped). The
assembled output, however, does not include a per-call summary of how
many tool-result rows entered prompt context, under what tool names,
at what authority position. Character speech about tools currently
relies on the LLM noticing the per-block metadata, which is brittle.

**v0.2 lane:** Surface `assembly_audit.tool_result_summary` (§2.6
shape) with the Cluster 2 §11.3 three-modifier
`(low-authority, decay-bounded, tool_result)` printed verbatim as a
human-readable marker. Per-hit list with eid / tool_name / block_type /
score. Pure-additive.

---

## §4 — Telemetry shape (ratified)

A single canonical helper, mirroring FILTER-A's pattern (one helper,
one response shape, never overload existing keys, surface required).
Names and module location are ratified at S3 promotion (S3 Decisions
2, 3, 4).

### §4.1 Helper signature (ratified)

- **Name:** `build_assembly_audit` (S3 Decision 3).
- **Module:** `torment_service/assembly_audit.py` (S3 Decision 2 —
  new module; clean separation from FILTER-A).

```
def build_assembly_audit(
    *,
    request_meta: dict,        # workspace_id, agent_id, query, profile, top_k, token_budget
    core_query_result: dict,   # the dict returned by fabric.query() (must include
                               # the propagated _filter_excluded and embed_context)
    archive_hits: list,        # archive_hits from ArchiveStore.retrieve()
    assembled: AssembledContext,  # output of assemble_context()
) -> dict:
    """Read-only telemetry helper. Returns an assembly_audit dict per §4.2.
    No mutation. No I/O. (No ledger persistence in this revision per
    S3 Decision 1.)
    """
```

### §4.2 Response shape (ratified)

```
{
  "lane_version": "memory_to_prompt_observability_v0.2",
  "timestamp": <epoch_seconds>,
  "request": {
    "workspace_id": <str>,
    "agent_id": <str>,
    "query": <str>,
    "profile": <str>,
    "top_k": <int>,
    "token_budget": <int>,
    "surface": "llm_context"
  },
  "embedder": {
    "provider": <str>,
    "model": <str>,
    "dim": <int>
  },
  "filter_a": {
    "core_hits_in_count": <int>,
    "core_hits_out_count": <int>,
    "excluded": [{"eid": <int>, "excluded_reason": <str>}, ...],
    "authority_guard_rejected": <int>,
    "archive_hits_count": <int>,
    "archive_filter_applied": <bool>   // today: false; v0.2 reports honestly
  },
  "assembly": {
    "profile_used": <str>,
    "profile_weights": {<block_type>: <float>, ...},
    "tokens_used": <int>,
    "token_budget": <int>,
    "block_token_counts": {<block_type>: <int>, ...},
    "blocks": {
      <block_type>: {
        "candidates_seen": <int>,
        "selected_count": <int>,
        "tokens_used": <int>,
        "selected_eids": [<int>, ...],
        "selected_chunk_ids": [<str>, ...],
        "classification_basis": [
          {"eid": <int>, "primary": <str>, "secondary": [<str>, ...]}, ...
        ]
      }, ...
    },
    "selection_log_enriched": [
      {
        "block_type": <str>,
        "eid": <int|null>,
        "chunk_id": <str|null>,
        "score": <float>,
        "token_count": <int>,
        "action": <str>,    // selected / skipped_budget_exhausted / skipped_archive_budget / skipped_block_cap
        "reason": <str>,
        "classification_basis": {"primary": <str>, "secondary": [<str>, ...]}
      }, ...
    ]
  },
  "character": {
    "character_name": <str>,
    "seed_basin_role": <str>,
    "drift_score": <float>,
    "drift_direction": <str>,
    "relational_count": <int>
  },
  "spirit_return_summary": {
    "total": <int>,
    "by_mode": {"resonance": <int>, "surfacing": <int>, "recollection": <int>},
    "avg_warmth": <float>,
    "any_entered_prompt": <bool>
  },
  "tool_result_summary": {
    "count_in_prompt": <int>,
    "three_modifier": "(low-authority, decay-bounded, tool_result)",
    "tool_names": [<str>, ...],
    "per_hit": [
      {"eid": <int>, "tool_name": <str>, "block_type": <str>, "score": <float>}, ...
    ]
  }
}
```

**v0.2.4 extension (closure annotation, 2026-05-27):** when archive
FILTER-A is wired in production (the default after v0.2.4-A1), the
`filter_a` block additionally carries:

```
"archive_excluded": [
  {"chunk_id": <str>, "doc_id": <str>, "excluded_reason": <str>},
  ...
]
```

and `archive_filter_applied` reports `true`. The `archive_excluded`
key is present whenever the filter ran upstream (including when
exclusions are zero — empty list is the structural signal). The key
is **absent** when `build_assembly_audit` is called without the
`archive_filter_excluded` parameter (legacy v0.2 first-revision
shape, preserved for tests and any caller that has not yet wired
the filter). Archive exclusions are NOT mixed into the core
`excluded` list — archive hits key on `chunk_id` (string) while
core hits key on `eid` (int); keeping the two surfaces separate
avoids downstream type confusion. See closure record
`docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_4_ARCHIVE_FILTER_A.md`.

### §4.3 Where the helper is called (ratified)

**Closure-reality correction (2026-05-27):** v0.2 first revision
wires `assembly_audit` on `POST /retrieve` only. `POST /agent/query`
remains unchanged and returns the raw `fabric.query()` shape; it does
not accept an `include_assembly_audit` parameter in v0.2 first
revision. The earlier framing language that named two integration
points overstated what landed.

One endpoint integration point; opt-in via the
`include_assembly_audit: bool = False` request parameter (S3 Decision
4 — default false preserves backward-compat for existing callers
including `live_agent/memory_bridge.py`):

- `POST /retrieve` — adds an `assembly_audit` key to the response when
  the parameter is true. `results` / `blocks` / `assembled_text`
  unchanged.

`POST /agent/query` parity is **not** in scope for v0.2 first
revision. Extending the audit surface to `/agent/query` would require
either (a) running `assemble_context()` inside the `/agent/query`
handler so a full §4.2 payload can be produced (a behavior change at
that surface, since `/agent/query` today returns raw `fabric.query()`
results without assembly), or (b) defining a reduced query-level
audit shape that omits the assembly fields. Either path is a separate
ratifiable behavior-change slice; it is not authorized by this
doctrine and was not landed by v0.2 first revision.

No call sites are *changed* in v0.2 framing scope (this document).
The wiring is Slice S5 (after Slice S4 helper lands and is
unit-tested).

### §4.4 Invariants on the helper

- **Read-only.** The helper does not write to `MemoryGraph`, does not
  modify `payload`, does not mutate any input dict. Inputs are
  consumed via `dict.get()` only.
- **No new schema fields on hits / blocks / `AssembledContext`.** Every
  field surfaced by the helper is computed from existing inputs.
- **No I/O.** Per S3 Decision 1 (Option C — response-only), the
  helper does not append to any ledger, does not write any file, does
  not call any external service. The audit payload exists only in
  memory and in the HTTP response.
- **Response shape is invariant under input shape variation.** Missing
  inputs degrade gracefully to empty defaults; the helper does not
  raise on missing optional fields.
- **`results` and `blocks` are never modified.** Audit lives in its own
  top-level response key (`assembly_audit`); the existing assembled
  output is byte-identical to the non-audit path.
- **One canonical derivation** (PROVENANCE_DOCTRINE Invariant C):
  the helper is the single place where assembly observability is
  produced. Inline parsing at call sites is forbidden.

---

## §5 — Audit logging ledger location (ratified Option C)

**Ratified S3 Decision 1: Option C — response-only, no disk
persistence in this revision.**

v0.2 observability returns the `assembly_audit` payload in the
`/retrieve` response only (closure-reality correction 2026-05-27;
`/agent/query` parity deferred per §4.3). The audit payload exists in
memory and in the HTTP response; nothing is written to disk by v0.2
first revision.

Reason for Option C:
- Keep Slice S4 (helper) and Slice S5 (wiring) small.
- Prove the audit payload shape in live use before any ledger
  persistence work begins.
- Avoid creating or extending ledgers before the response-side audit
  shape is verified by the trio.
- Cluster 5 v0.1 §5 fragility instances (`JSONL-NO-FSYNC`,
  `JSONL-LOADER-NOT-FAIL-TOLERANT`) do not apply in this revision
  because no JSONL append occurs.

Options A (extend `memory_events.jsonl`) and B (new
`assembly_audit.jsonl`) remain available for a future slice
(working name v0.2.x or v0.3) after live use validates the audit
payload shape. The lineage of considered options is preserved below
for the future slice's benefit:

### §5.1 Option A — extend `memory_events.jsonl` (deferred)

Append assembly-audit records to the existing per-agent
`memory_events.jsonl` canonical event ledger (Cluster 5 v0.1 §2.1).
New event type: `assembly_observed`.

**Pros:** reuses existing canonical event ledger; no new file to
manage; already audit-visible through governance audit surfaces;
Cluster 5 v0.1 §2.1 vocabulary covers this sub-type already.

**Cons:** pollutes the write-event stream with non-write observations;
assembly events are higher-volume than memory writes, dropping the
write-event stream's signal-to-noise ratio; adding new event types
tightens the assumption that all consumers handle unknown types.

### §5.2 Option B — new `assembly_audit.jsonl` (deferred)

New per-workspace per-agent canonical append-ledger file:
`data/workspaces/<ws>/agents/<agent>/assembly_audit.jsonl`. Each line
is one `assembly_audit` record per the §4.2 shape.

**Pros:** clean separation of concerns; observability events have
their own file; consumers of `memory_events.jsonl` unaffected; per-agent
layout matches existing file structure; safe to delete or rotate
(derived in the Cluster 5 sense).

**Cons:** new fragility surface (`JSONL-NO-FSYNC`,
`JSONL-LOADER-NOT-FAIL-TOLERANT` apply again); retention policy must
be decided; another file to manage in any future Cluster 5 v0.2
verify-CLI / manifest layer.

### §5.3 Future decision sequencing

Disk-persistent ledger writes become a v0.2.x (or v0.3) slice. The
choice between Option A and Option B is downstream of v0.2
observability evidence — once live use shows what the audit payload
actually contains and at what volume, the trio can make an informed
ledger choice. v0.2 v0.1 is silent on which option wins; both
remain valid.

---

## §6 — Non-goals

v0.2 observability lane explicitly does NOT authorize, design, or
commit to any of the following:

- **Behavior change.** No retrieval scoring change, no assembly weight
  change, no FILTER-A modification, no profile-selection change.
- **Memory mutation.** No new write paths. No update to
  `provenance`, `governance`, lifecycle envelope, contest ledger,
  `CharacterState`, motifs, or any other authoritative memory
  structure.
- **Disk persistence in this revision** (per S3 Decision 1 — Option
  C). No ledger writes, no JSONL append, no file write. Audit
  payload lives in memory and in the HTTP response only.
- **Schema changes on hits / blocks / `AssembledContext`.** Every
  observability field is computed from existing inputs.
- **New tool families** beyond `code_exec` (Roadmap §3.B; v0.1 §3.8).
- **Scheduler / daemon / wall-clock triggers** initiated by the agent
  (v0.1 §3.8).
- **New MCP surface or new exposure tier.** MCP capability boundary
  unchanged.
- **Archivist writeback flip** (remains opt-in per
  ARCHIVIST_WRITEBACK_GATE_FRAMING D6).
- **Cluster 2 v0.2 runtime Authority Gate.** Separate ratifiable arc.
- **Track B v0.2 contest ledger.** Separate ratifiable arc.
- **Cluster 5 v0.2 storage substrate work** (fsync / atomic-write /
  journal / verify CLI / manifest layer). Separate ratifiable arc.
- **Cluster 4 offline reflection (Dream / Continued Thought / Envelope
  Audit modes).** Separate framing doc.
- **Multi-agent v0.2 runtime.** Premature.
- **Amendment of Memory-to-Prompt v0.1 doctrine.** v0.2 inherits v0.1
  verbatim. The block-count miscount in v0.1 (§8 of this doc) is a
  future v0.1.1 cleanup, not an amendment by v0.2.
- **Resolution of the archive-FILTER-A gap.** v0.2 reports the gap;
  the fix is a separate ratifiable slice (v0.2.4 or v0.3), per S3
  Decision 5.
- **Resolution of the `live_agent/` path duplication.** v0.2 names
  `torment_fabric/live_agent/` as canonical; the cleanup is a
  separate slice.
- **Resolution of the `CharacterState` runtime write-site audit (PR
  #53 follow-on).** Parked per orientation §5 watch-item rule.
- **New env vars beyond a single per-call opt-in request parameter.**
  v0.1 Invariant 9 forbids global toggles; the
  `include_assembly_audit` request parameter (S3 Decision 4) is
  per-call and defaults false.
- **Response-side observability** (what the LLM said back, whether the
  character voice held). That is a separate observability lane;
  memory-to-prompt v0.2 covers only the input direction.
- **Storage of LLM responses / model output in the audit payload.**
  The audit is about what memory entered prompt context, not what
  the model produced.

---

## §7 — Implementation slices after this promotion

Four slices after this promotion (S3) is committed. Each
independently ratifiable. The next slice is pure-additive code; the
slice after wires it in; the slice after verifies; the last is
closure.

### §7.1 Slice S3 — framing ratification + promotion *(this document)*

- Scratch S2 framing draft promoted to this document with the seven
  S3-ratified decisions applied (recorded in § S3 Decisions Applied).
- No code change.
- Scratch S2 preserved unchanged as lineage.
- **Awaiting operator commit.**

### §7.2 Slice S4 — telemetry helper, additive, no call-site changes

- New module `torment_service/assembly_audit.py` (S3 Decision 2).
- New helper `build_assembly_audit(...)` (S3 Decision 3) with
  signature per §4.1.
- Pure function: takes existing inputs, returns the §4.2 dict.
- Unit tests: `tests/test_assembly_audit.py` — response shape
  invariants, no-mutation invariant, no-I/O invariant (per S3
  Decision 1), tool-result-row detection, archive-hit handling,
  classification-basis structure, spirit-return summary computation.
- Existing tests (FILTER-A, authority lane matrix, tool-result
  lifecycle, etc.) must remain green.
- No production call sites changed.
- Operator commits.

### §7.3 Slice S5 — opt-in wiring at canonical surfaces

- Add `include_assembly_audit: bool = False` parameter (S3 Decision
  4) to `POST /retrieve` request shape. When true, response carries
  an `assembly_audit` top-level key per §4.2 alongside existing
  `results` / `blocks` / `assembled_text`.
- **Closure-reality note (2026-05-27):** v0.2 first revision landed
  `/retrieve` wiring only. `POST /agent/query` parity was not wired
  and is deferred to a separate ratifiable behavior-change slice per
  §4.3.
- Propagate `_filter_excluded` through the `fabric.query()` return
  shape (additive; new optional key on the existing response dict).
- Update `live_agent/memory_bridge.py` to optionally request the
  audit (defaults off).
- **No ledger writes in this revision** per S3 Decision 1.
- All existing tests remain green. New integration test exercises
  the opt-in audit path.
- Operator commits.

### §7.4 Slice S6 — small live verification (operator-run)

- Operator-run script (working name `tests/run_assembly_audit_smoke.py`,
  modeled on `tests/run_external_inference_smoke.py`): hits
  `/retrieve` with a character voice active and
  `include_assembly_audit=true`. Verifies:
  - The audit payload's `assembly` block matches the assembled blocks
    one-to-one.
  - `provenance_type` survives end-to-end.
  - FILTER-A exclusions are reported under `filter_a.excluded`.
  - Spirit-return mode (if any fired) surfaces in
    `spirit_return_summary`.
  - One tool-result row in context is correctly labeled
    `(low-authority, decay-bounded, tool_result)` in
    `tool_result_summary.three_modifier`.
  - `embedder` snapshot matches the running embedder.
- A/B run: with vs without audit; `results` byte-identical.
- No pytest LLM invocation; operator-run only.

### §7.5 Slice S7 — closure checkpoint

- `docs/CHECKPOINT_2026-XX_MEMORY_TO_PROMPT_OBSERVABILITY_v0.2.md`.
- Names what's verified, the response-only posture (no ledger
  persistence in this revision), sub-gates that follow:
  - **v0.2.x ledger persistence** (Option A vs B, downstream of live
    audit-shape evidence — per S3 Decision 1).
  - **v0.2.1 profile-aware intent classification.**
  - **v0.2.2 character-context block enrichment.**
  - **v0.2.3 spirit-return voice-cue verification.**
  - **v0.2.4 archive-FILTER-A application** (per S3 Decision 5).
  - **v0.3 per-tool-family `tool_result` defaults** (Cluster 2 §11.7).
  - **Archivist writeback gate-flip operational deliverables**
    (D2/D4 from ARCHIVIST_WRITEBACK_GATE_FRAMING).
- Each sub-gate is a separate ratifiable arc; none authorized by
  this v0.2 doctrine.
- Operator commits.

---

## §8 — v0.1 correction note (block count) — parked

Per S3 Decision 6, the v0.1 block-count correction is parked as
future cleanup; v0.2 does NOT amend v0.1.

`docs/MEMORY_TO_PROMPT_AUTOMATION_v0.1.md` references "four-block
precedence" in §0 (TL;DR) and §3.1. The actual block count in
`retrieval_assembler.py` is **five**:

```
BLOCK_IDENTITY      (identity_context)
BLOCK_REFERENCE     (reference_context)   <-- Block B, between identity and relational
BLOCK_RELATIONAL    (relational_context)
BLOCK_SITUATIONAL   (situational_context)
BLOCK_ARCHIVE       (archive_context)
```

`BLOCK_REFERENCE` carries Block B pack-declared reference loads per
`BLOCK_B_DESIGN.md` §8.1 ("loaded references are intentional reasoning
material — more important than archive chunks, less identity-defining
than core canon"). It sits in `FILL_ORDER` at position 2 between
identity and relational.

**Future cleanup recommendation:** a v0.1.1 cleanup pass on
`MEMORY_TO_PROMPT_AUTOMATION_v0.1.md` to:

- Update §0 TL;DR: "four-block precedence" → "five-block precedence".
- Update §3.1 to enumerate all five blocks.
- Update §4 if any protected-surface enumeration references the
  block count.

**Not amended by v0.2.** The cleanup is flagged here so it does not
get lost; the actual edit is its own small slice when convenient.

---

## §9 — Cross-references

- **Parent doctrine:** `docs/MEMORY_TO_PROMPT_AUTOMATION_v0.1.md`
  (DRAFT v2; v0.2 inherits the character-first hierarchy and the
  "Governance is subordinate in purpose, but load-bearing in
  substrate-criticality" canonical phrasing verbatim).
- **Scratch lineage (preserved, not amended):**
  `scratch/MEMORY_TO_PROMPT_AUTOMATION_v0.2_OBSERVABILITY_FRAMING_DRAFT_2026-05-25.md`
  (S2 framing draft from which this v0.2 document was promoted).
- **Anchor doctrines (pre-autonomy spine):** Track A v0.1, Cluster 2
  v0.1, Track B v0.1, Cluster 5 v0.1.
- **Governance / runtime substrate:** MCP_CAPABILITY_BOUNDARY,
  TORMENT_AGENT_DOCTRINE_v0.1, TOOL_RESULT_LIFECYCLE_POLICY (Q2-D
  doctrine), TOOL_RESULT_RETRIEVAL_SEMANTICS,
  PROVENANCE_DOCTRINE_v2.4.x, FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN,
  CHARACTER_SYSTEM, AGENT_SPINE_OVERVIEW,
  ARCHIVIST_WRITEBACK_GATE_FRAMING.
- **Closure trail (Phase 0 stood downstream of these; v0.2
  observability is downstream of v0.1):** CHECKPOINT_2026-05_Q2D,
  CHECKPOINT_2026-05_LEVEL_3_ST_RETRIEVAL,
  CHECKPOINT_2026-05_TIER_2_RUNTIME_EVIDENCE,
  AGENT_AUTOMATION_NEXT_STEP_AUDIT.
- **Substrate code (read-only references; no modifications by this
  document):**
  - `torment_service/governance.py:300–448` — `filter_llm_facing`,
    surface constants, authority guard.
  - `torment_service/fabric.py:4146–4258` — `Workspace.query()`
    FILTER-A chokepoint and character_context assembly.
  - `torment_service/app.py:1322–1394` — `POST /retrieve` endpoint.
  - `torment_service/app.py:903` — `POST /agent/query` endpoint.
  - `torment_service/archive_memory.py:362–420` — `ArchiveStore.retrieve()`
    (no governance metadata on chunks).
  - `torment_service/retrieval_assembler.py:1–562` — block types,
    profiles, `assemble_context()`, `_hit_to_block`,
    `_archive_hit_to_block`, `_classify_core_hit`, `AssembledContext`,
    `selection_log`.
  - `torment_service/scoring.py` — `derive_provenance_type`,
    `derive_query_provenance_type`.
  - `torment_service/deep_hits.py` — `assert_authoritative_memory`,
    NonAuthoritativeDeepHit subtypes.
  - `torment_fabric/live_agent/memory_bridge.py` (canonical per S1
    finding §5).
- **New module name reserved by v0.2 doctrine (not yet created):**
  `torment_service/assembly_audit.py` — created at Slice S4.
- **Tests (read-only references; no modifications by this document):**
  `tests/test_filter_llm_facing.py`,
  `tests/test_filter_llm_facing_authority_guard.py`,
  `tests/test_authority_lane_matrix.py`,
  `tests/test_tool_result_ingest.py`,
  `tests/test_tool_result_lifecycle.py`.
- **New test file name reserved by v0.2 doctrine (not yet created):**
  `tests/test_assembly_audit.py` — created at Slice S4.

---

## §10 — Open questions and resolutions

The S2 scratch draft surfaced ten open questions. S3 promotion
resolves five and leaves five for downstream consideration.

**Resolved at S3:**

1. **Ledger location (§5).** **Option C — response-only, no disk
   persistence in this revision** (S3 Decision 1). Options A and B
   remain available for v0.2.x or v0.3 after live audit-shape
   verification.
2. **Helper module location (§4.1).** **`torment_service/assembly_audit.py`**
   — new module, clean separation from FILTER-A (S3 Decision 2).
3. **Helper name.** **`build_assembly_audit`** (S3 Decision 3).
4. **`include_assembly_audit` default.** **False** (S3 Decision 4).
   Per-call opt-in. v0.1 Invariant 9 (no global env-var toggle for
   governance defaults) is honored.
8. **`memory_events.jsonl` event-type schema.** **Moot under current
   ratified decision** (Option C means no ledger writes in this
   revision). Becomes a v0.2.x decision if/when ledger persistence
   lands.

**Still open (downstream of v0.2 observability evidence):**

5. **Retention policy if/when ledger persistence lands.** Default
   rotation / compaction strategy. v0.2.x decision; not relevant to
   the response-only first revision.
6. **Archive-FILTER-A gap fix sequencing.** S1 finding §3.2 is named
   as a v0.2 implementation watch item, fixable by v0.2.4 or v0.3
   (S3 Decision 5 — fix deferred). Trio may want to sequence it
   ahead of v0.2.1/v0.2.2/v0.2.3 if live observability data shows
   archive chunks frequently entering prompt context. Decision
   deferred until v0.2 observability lands and produces evidence.
   **Resolved 2026-05-27 by v0.2.4-A1** (Option A — per-chunk
   governance + unconditional `/retrieve` filter). See
   `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_4_ARCHIVE_FILTER_A.md`.
7. **`live_agent/` cleanup sequencing.** S1 finding §5 recommends
   `torment_fabric/live_agent/` as canonical. Cleanup of the
   repo-root copy is a separate ratifiable slice; trio decides when
   to open it.
9. **CHECKPOINT date.** S7 closure checkpoint date is unknown until
   the implementation slices land. Placeholder `CHECKPOINT_2026-XX_*`
   resolves at S7.
10. **v0.1.1 cleanup pass** (block-count correction per §8 — S3
    Decision 6 parks it). Trio decides whether to land it as a small
    cleanup slice before v0.2 implementation begins, alongside one
    of the v0.2 implementation slices, or as its own later
    micro-slice.

---

## §11 — What this document does and does not include

v0.2 observability lane doctrine is a framing document, not an
implementation. It declares the *shape, purpose, scope, telemetry
surface, ratified helper/module/flag names, and slice plan* of the
memory-to-prompt observability lane. It collects the five S1 gaps and
specifies a pure-additive way to surface each. It explicitly does NOT:

- Modify any code in `torment_service/`, `cognition/`, `live_agent/`,
  `tests/`, or anywhere else. Implementation begins at Slice S4.
- Create `torment_service/assembly_audit.py` (Slice S4 will).
- Create `tests/test_assembly_audit.py` (Slice S4 will).
- Wire any endpoint (Slice S5 will).
- Write to disk anywhere in this revision (Option C per S3 Decision
  1). The audit payload exists only in memory and in the HTTP
  response.
- Amend Memory-to-Prompt v0.1 doctrine or the pre-autonomy spine.
- Modify FILTER-A. v0.2 observability *propagates* FILTER-A's
  existing `excluded[]` output; it does not change `filter_llm_facing`'s
  behavior, surface enum, or response shape beyond the existing
  contract.
- Apply FILTER-A to archive hits. v0.2 observability *reports* the
  archive-FILTER-A gap. The fix is a separate ratifiable slice
  (v0.2.4 or v0.3) per S3 Decision 5; v0.2 does not silently fix it.
  **(Closed by v0.2.4-A1 in a later slice; see closure checkpoint
  `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_4_ARCHIVE_FILTER_A.md`.)**
- Resolve the `live_agent/` path duplication. v0.2 names
  `torment_fabric/live_agent/` as canonical; the cleanup is a
  separate slice.
- Resolve the `CharacterState` runtime write-site audit (PR #53
  follow-on). Parked per orientation §5 watch-item rule; v0.2
  observability is read-only on `character_context`, not on
  `CharacterState` write sites.
- Introduce any new env var. The `include_assembly_audit` request
  parameter (S3 Decision 4) is per-call opt-in only, defaults false.
- Introduce a new MCP surface, new MCP tool, or new exposure tier.
- Introduce a scheduler, daemon, or wall-clock trigger.
- Introduce a response-side observability lane (what the LLM said
  back). That is orthogonal to memory-to-prompt.
- Authorize automation extensions, runtime contest ledger writes,
  authority-gate runtime enforcement, or any other Cluster 2 v0.2 /
  Track B v0.2 / Cluster 5 v0.2 work.
- Authorize ledger persistence in any form in this revision (per S3
  Decision 1). Options A and B from §5 remain available for v0.2.x
  or v0.3 after live audit-shape verification, but neither is
  authorized by v0.2 first revision.
- Decide the future ledger-persistence question prematurely. §5
  preserves Options A and B with their pros/cons for the downstream
  slice's benefit; the choice is downstream of v0.2 observability
  evidence.
- Bypass operational discipline (Windows = source of truth for
  TORMENT; AI is read-only advisor for the TORMENT workspace).

This document IS the v0.2 observability lane doctrine. Subsequent
versions (v0.2.x, v0.3, v1.0) require their own trio ratification
before they supersede this one.

---

*End of MEMORY_TO_PROMPT_AUTOMATION v0.2 (observability lane).
Promotion-ready 2026-05-25 with seven trio-ratified S3 decisions
applied. Awaiting operator commit. No implementation authorized by
this document. No code changes. No schema migrations. No tests
authorized by this document (test_assembly_audit.py is named in §7.2
for Slice S4 creation). No FILTER-A modification. No v0.1 amendment.
No ledger persistence in this revision (Option C). The pre-autonomy
spine is not amended. Scratch S2 framing draft preserved unchanged
as lineage.*
