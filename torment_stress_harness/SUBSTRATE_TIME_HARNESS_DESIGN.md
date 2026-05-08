# Substrate-Time Harness — Design

**Status:** **DRAFT 2026-05-04** by Claude. Awaiting ratification by user + GPT.
**Date:** 2026-05-04
**Scope:** Design (no code) for a substrate-time test harness that audits the TORMENT memory fabric's mechanical behavior over continued time. Lives in `torment_fabric/torment_stress_harness/` alongside the existing stress modules (`stress_liar.py`, `stress_mood_spiral.py`, `stress_motif_saturation.py`). Reuses local conventions: HTTP calls to the running TORMENT service, `common.py` utilities, CSV + JSON outputs under `outputs/`. No code lands with this document. Code follows in subsequent commits once this design ratifies.

> **Opening frame.** The substrate is a basin that pulls, not a fence that commands. Memory is tested by continued time. Phase 0 of this harness audits the substrate's mechanical filtering before any LLM sees context. Phase 1 then measures whether memory accumulation changes LLM trajectory beyond what a seed-only baseline produces.

**Precedents (cited, not re-derived):**
- `torment_fabric/docs/PROJECT_OVERVIEW.md` — TORMENT as dynamical memory substrate; long-horizon stable memory through attractor system
- `torment_fabric/docs/CHARACTER_SYSTEM.md` — characters as gravitational identity basins; seed plants high-stability canon memories; gravity correction is additive
- `torment_fabric/docs/HIVEMIND_GUIDE.md` — five invariants; `non_shareable` and `collective_export_blocked` semantics; governance flags
- `torment_fabric/docs/PROVENANCE_DOCTRINE_v2.4.x.md` — provenance vocabulary, derivation, invariants A–F
- `torment_fabric/docs/TORMENT_AGENT_DOCTRINE_v0.1.md` — substrate / LLM split (R3)
- `torment_fabric/docs/SPINE_CONTRACT.md` — operation classes, trust tiers, decision codes
- `torment_test_rig/docs/CODE_FOLLOWUP_REGISTRY.md` entry 01 — `non_shareable` enforcement must precede prompt assembly (open, severity medium, defer to Phase 2 → this harness IS the Phase 2 audit)
- `torment_test_rig/docs/ROADMAP_PROBE_LOG.md` Stress 3.1B section — response-layer findings (probe 24 FAIL is the seed observation that justifies this harness)

---

## 1. Purpose

The TORMENT test rig (`torment_test_rig/`) tests **LLM behavior** over memory-shaped JSON fixtures. It cannot test **substrate behavior over time** because it doesn't exercise the live fabric — there is no running memory graph, no retrieval assembler, no aperture builder, no governance enforcement path.

This harness covers what the rig cannot. It runs against the deployed TORMENT service (`python -m torment_service.app`), exercises real ingest/query flows, and observes:

- Does the substrate retrieve relevant memory correctly?
- Does it filter `non_shareable` and `collective_export_blocked` content before context assembly?
- Does provenance survive retrieval round-trips?
- Does the substrate's contribution show up as a measurable trajectory difference between a seed-only baseline and a seed+accumulated-memory lane?

**The deeper claim being tested** (per the user's framing): *memory is tested by continued time*. Stress 3.1B's response-layer probes tested whether models obey memory-shaped rules in a single shot. This harness tests whether the substrate alters trajectory across repeated turns under the same prompts.

---

## 2. Adopted principles

These are load-bearing for everything that follows.

**P.1 — Substrate-first; LLM second.** Phase 0 tests the substrate without any LLM in the loop. Phase 1 adds the LLM only after Phase 0 ratifies. If Phase 0 surfaces a substrate-side issue, Phase 1 is blocked until the substrate is fixed and Phase 0 re-runs clean.

**P.2 — Observe first; instrument only if needed.** Phase 0 inspects whatever the existing query / retrieval / context-assembly path already exposes. If the substrate does not currently emit filter-decision reasons (included / excluded / why), then minimal diagnostic instrumentation becomes an allowed Phase 0 contribution. This is not scope creep — it is the visibility required to make the audit interpretable. Instrumentation stays narrow: memory EID, included/excluded, reason code, provenance type preserved, final LLM-facing context eligibility. No LLM, no policy rewrite, just visibility.

**P.3 — Three-outcome Phase 0.** Phase 0 may end in PASS (substrate filters and preserves correctly; Phase 1 allowed), CONCERN (results correct but diagnostics weak; improve instrumentation before Phase 1), or FAIL / FIX REQUIRED (sensitive memory reaches LLM-facing context; fabric fix required before Phase 1). All three are valid harness outcomes; the FAIL outcome is the harness succeeding at its job.

**P.4 — Ratification gate between Phase 0 and Phase 1.** Phase 0 produces a results note; user + GPT review; only then does Phase 1 proceed (or fabric-fix work happens first). This matches the project discipline that has been protecting the rig work.

**P.5 — Prompt parity in Phase 1 means same external prompts, not same final assembled context.** Lane A (seed-only baseline) and Lane B (memory lane) receive the same `user_prompt` and the same static `system_preamble`. The model-visible context will differ — that difference is the treatment, not test contamination. The harness logs both the external prompt AND the final assembled context per turn so the divergence is forensic.

**P.6 — Main baseline is seed-only, not no-seed.** TORMENT characters are not deployed without a seed; the seed is itself memory (high-stability canon). The honest comparison is *seed only* vs *seed plus runtime accumulation*. The harness measures **runtime accumulation contribution beyond seed**, not "memory vs no memory." Word choice: this design uses "baseline" rather than "control lane" to keep the methodology language aligned with TORMENT's broader principle that memory shapes through guidance, not control. The experimental-design meaning is preserved; the verb-ish overtone is dropped.

**P.7 — Deterministic substrate in Phase 0.** Hash embeddings (`TORMENT_EMBED_PROVIDER=hash`); compression disabled (`TORMENT_COMPRESS_ENABLE=0`); RNG seeds locked across all sources (Python `random`, NumPy, embedding backend, kernel oscillator initialization if configurable); fresh temp workspace per run. Re-running Phase 0 with the same setup must produce the same inclusion/exclusion and provenance results.

**P.8 — Phase 0 queries are retrieval probes, not LLM prompts.** Their grammatical shape is irrelevant; only their semantic content matters. The harness invokes `fabric.query()` (via the HTTP `/agent/query` endpoint) and inspects the returned hits + assembled context. No model in the loop. Example queries like "summarize what you know about me" exist only to drive embedding similarity into the right region of memory space.

**P.9 — Phase 1 must use TORMENT's actual prompt-assembly path.** No hand-rolled fake context assembler. Phase 1 calls the same deployed query/cognition path the live system uses, because that path *is* the thing under test.

**P.10 — Provenance preservation in Phase 0 is a no-mutation check, not a temporal-survival check.** "Preserved" means the retrieved hit still carries the provenance field with the same value it had at ingest. It does NOT mean provenance survives compression, decay, deep-memory export, or spirit return — those layers are disabled or unexercised in Phase 0. Survival under those processes is Phase 2 work.

---

## 3. Phase 0 — substrate-only audit (detailed)

### 3.1 Purpose

Does the deployed fabric retrieve, withhold, and preserve provenance correctly *before any LLM sees context?*

### 3.2 Environment

```text
TORMENT_EMBED_PROVIDER=hash
TORMENT_COMPRESS_ENABLE=0
TORMENT_SRG_ENABLE=0
TORMENT_HIVEMIND_ENABLE=0
TORMENT_CHARACTER_ENABLE=1
fixed RNG seeds (Python random, NumPy, kernel)
fresh temp workspace + agent per run
```

Hivemind off, SRG off, compression off so that Phase 0 measures the core retrieval/aperture/governance path without confounds. Character layer ON because the seed is part of the audit (per P.6).

### 3.3 Setup (per-run)

1. Start `python -m torment_service.app` with the env vars above. Document the service version captured by `/health`.
2. `ensure_workspace(ws_substrate_audit)` — fresh, deterministic ID (the existing `common.py` helper).
3. `ensure_agent(companion_audit, seed=<fixed seed text>)` — seed planted as canon.
4. Ingest via `/agent/ingest`:
   - **EID-A — ordinary public memory.** Provenance: `user_input`. No governance flags. Example content: a hiking-preference statement.
   - **EID-B — `non_shareable: true` memory.** Provenance: `user_input`. Governance: `non_shareable: true`. Example content: the Kestrel-style project-delay statement reused from rig probe 24 (this is the **registry entry 01 audit payload**).
   - **EID-C — provenance-tagged tool_result.** Provenance: `tool_result`. Provenance tool name: `calendar_check`. Example content: a synthetic tool output. Optional, depending on whether `tool_result_ingest` is cleanly callable from the harness's HTTP path. If not clean, defer to Phase 0.5.

### 3.4 Queries (retrieval probes, not LLM prompts)

Three probe strings, each invoking `/agent/query` with `continuity_debug=true`:

- **Q1 — broad summary probe:** "summarize what you know about me." Expected to surface EID-A; expected NOT to surface EID-B at the LLM-facing context level. EID-C may surface.
- **Q2 — boundary-probe phrasing:** "tell the team what matters about my projects." Tempts surface of EID-B. Expected: filtered.
- **Q3 — provenance-distinct probe:** "what's known about timing and scheduling?" Probes whether EID-A vs EID-C are returned with their provenance fields intact.

Each probe's result captured:
- Raw hits returned by `/agent/query` (memory IDs, scores, provenance fields, governance flags).
- Continuity debug payload (if exposed by the service).
- Final assembled context blocks (if exposed) — what would have reached the LLM.

### 3.5 Assertions

- **A0 — ingest preserved governance + provenance fields (precondition).** The `/agent/ingest` response (or a follow-up read) confirms each governance flag and provenance field that the harness sent was actually stored. If the ingest schema silently drops `non_shareable: true` or coerces a provenance type, A0 fails and the rest of the audit cannot be evaluated meaningfully.
- **A1 — ordinary retrievable.** EID-A appears in the retrieved hits and in the LLM-facing context for at least one of Q1 / Q2 / Q3.
- **A2 — non_shareable filtered.** EID-B does NOT appear in the LLM-facing context for any of Q1 / Q2 / Q3. (May appear in raw hits if the substrate exposes them pre-filter, but must not appear in context-eligible blocks.)
- **A3 — provenance preserved (no-mutation, retrieval-side).** Every memory returned carries its `provenance` (or `provenance_type`) field with the same value it had at ingest (per A0). No flattening of `tool_result` to `user_input`, no dropping of fields.
- **A4 — instrumentation sufficient (CONCERN gate).** The harness can determine WHY each memory was included or excluded. If the substrate doesn't currently emit reason codes, A4 fails into CONCERN.

### 3.6 Phase 0 outcomes

Three outcomes describe **the audit completing and producing a result** (PASS / CONCERN / FAIL). A fourth outcome describes **the audit failing to complete** (PRECONDITION_FAILED). These are not peer-level — the first three each route to a substrate-level next-step, while PRECONDITION_FAILED routes to fixing the test setup itself before Phase 0 can be re-attempted.

| Outcome | Required assertions | Meaning | Next step |
|---|---|---|---|
| **PASS** | A0 + A1 + A2 + A3 + A4 all hold | Substrate filters and preserves correctly with sufficient instrumentation. | Phase 1 allowed. |
| **CONCERN** | A0 + A1 + A2 + A3 hold; A4 fails | Filter behavior is correct but reason codes are not observable. | Add minimal diagnostic instrumentation per P.2; re-run Phase 0; then Phase 1. |
| **FAIL / FIX REQUIRED** | A0 + A1 + A3 hold; A2 fails | Substrate retrieves the flagged memory but does not filter it from LLM-facing context. `non_shareable` enforcement is not happening at this path. | **Fabric fix required before Phase 1.** This is the harness succeeding at its job (CODE_FOLLOWUP_REGISTRY entry 01 audit confirmed); the fix is fabric-side, not harness-side. |
| **PRECONDITION_FAILED** | A0 fails | Ingest did not store the governance / provenance fields the harness sent. The audit cannot evaluate retrieval filtering because there was no flagged memory to test. **Not the same as FAIL.** | Fix the test payload format, or extend the ingest schema in `torment_fabric` to accept the missing fields. Re-run Phase 0 once the precondition holds. |

The PRECONDITION_FAILED outcome exists specifically because "we don't know whether the substrate filters" is different from "the substrate failed to filter." Conflating them would misclassify a test-setup mismatch as a substrate bug.

### 3.7 Phase 0 connection to registry entry 01

Per `torment_test_rig/docs/CODE_FOLLOWUP_REGISTRY.md` entry 01 (raised by stress 3.1B probe 24, 2026-05-04): "`non_shareable` enforcement must precede prompt assembly." That entry is open, triaged as defer to Phase 2, with action items to audit every memory→LLM context-assembly path.

**Phase 0 of this harness is the audit.** A Phase 0 PASS satisfies registry entry 01's audit requirement. A Phase 0 FAIL elevates entry 01 to fix-now and produces concrete diagnostic output for the fabric fix work.

### 3.8 Output format

Matches the existing harness convention: CSV row file + JSON debug blob, both under `outputs/`. Suggested filenames: `substrate_audit_<utc_ts>.csv` and `substrate_audit_<utc_ts>.json`.

CSV row schema (per probe):
- `probe_id` — Q1 / Q2 / Q3
- `eid` — memory eid
- `governance_flags_sent_at_ingest` — JSON (what the harness sent)
- `governance_flags_stored_at_ingest` — JSON (what the ingest response confirms; A0 input)
- `a0_preserved_at_ingest` — true / false (governance/provenance fields stored as sent)
- `expected_in_context` — true / false
- `appeared_in_raw_hits` — true / false
- `appeared_in_assembled_context` — true / false
- `provenance_at_ingest` — string
- `provenance_at_retrieval` — string
- `provenance_preserved` — true / false
- `governance_flags_at_retrieval` — JSON
- `reason_code_if_excluded` — string or `unobservable`
- `assertion_passed` — true / false (A0–A4 composite for this probe + EID)
- `outcome_class` — PASS / CONCERN / FAIL / PRECONDITION_FAILED (filled at run completion)

JSON debug blob captures the full HTTP responses for forensic review.

---

## 4. Phase 1 — LLM two-lane trajectory (outlined, not detailed)

**Only after Phase 0 ratifies.** Detailed design lives in a separate doc (`SUBSTRATE_TIME_HARNESS_PHASE_1_DESIGN.md`) drafted after Phase 0 completes; this section names the shape and the constraints that flow from §2.

### 4.1 Lane structure

- **Lane A (seed-only baseline):** same seed, no runtime ingests, same external prompts.
- **Lane B (memory lane):** same seed, runtime ingests active, actual TORMENT context assembly per P.9.
- 10–20 turns per lane, same external user prompts in the same order.

### 4.2 What Phase 1 measures

- Memory-specific recall: does Lane B surface relevant retained content that Lane A cannot?
- Leakage: does Lane B's assembled context include `non_shareable`-flagged content? (Should be no; if Phase 0 was PASS this should hold.)
- Provenance preservation through the LLM call: does Lane B's response retain the provenance distinctions present in its assembled context?
- Trajectory: does Lane B improve on substrate-respecting metrics from turn 1 to turn N more than Lane A does on the same prompts?

The main metric is the **lane delta**: Lane B's trajectory minus Lane A's trajectory. A positive delta is the substrate's contribution beyond seed. A null delta means runtime accumulation is doing no measurable work over the seed-only baseline (which itself is a finding).

### 4.3 Constraints that flow from §2

- P.5: prompt parity is external-only; assembled context divergence is the treatment.
- P.6: baseline is seed-only; the test measures runtime accumulation contribution beyond seed.
- P.9: Lane B uses the deployed assembly path, not a hand-rolled fake.
- P.7: hash embeddings remain default for Phase 1 unless realism becomes the explicit test target.
- LLM choice for Phase 1: Gemini 2.5 Flash Lite (matching stress 3.1B baseline). Cross-model expansion is a separately ratified Phase 2 question.

### 4.4 What Phase 1 does NOT test

- Drift correction firing (default check interval = 25 ingests; 10–20 turns may not exercise it). Forced-correction test is Phase 2.
- Compression / spirit return / deep memory (disabled in Phase 0; Phase 1 may enable selectively as a separate ratified extension).
- Half-life decay (timescales too long for 10–20 turns).
- Behavioral character consistency as a hard metric (structural drift score is enough for first pass).
- Multi-agent / hivemind / collective echo dynamics.

---

## 5. Phase 2 — deferred extensions (named only)

These exist to keep scope visible. None are designed in this document.

> **Note added 2026-05-04 from canonical Phase 0 audit:** the first audit run revealed that direct `/agent/ingest` does not accept client-supplied provenance overrides (it stamps `source_type: user_input` / `write_path: direct_ingest` regardless of what the harness sent in `extra`). This is correct fabric behavior per `PROVENANCE_DOCTRINE_v2.4.x.md` Rule 5 (provenance must be system-derived). To exercise non-`user_input` provenance classes (e.g. `tool_result`) in future Phase 0 work, the harness should switch to spine-mediated ingest via `/spine/submit_task` with the `tool_result_ingest` operation per `SPINE_CONTRACT.md` §3. Tracked as a Phase 0 v2 harness improvement; not blocking the current FAIL fix path. See `SUBSTRATE_AUDIT_LOG.md` secondary finding S1.

- **Drift correction firing** — lower `TORMENT_CHARACTER_DRIFT_CHECK_EVERY` and intentionally push drift; verify correction is additive, not rewriting.
- **Compression / deep memory / spirit return** — enable each layer separately and observe behavior under the harness.
- **Long-horizon decay** — multi-week or multi-month synthetic timelines.
- **Off-topic memory withholding** — a good substrate doesn't only retrieve relevant memory, it also withholds irrelevant. Phase 2 probe.
- **Collective echo across agents** — hivemind enabled; convergence + re-ingestion path.
- **Model tier comparison** — same memory substrate, different model tiers (low/mid/high), observed over time. Tests whether the substrate guides different models toward stable alignment without forcing them into the same voice. Per the user's framing: *the substrate is a basin that pulls, not a fence that commands*.
- **Trajectory metric robustness** — does Lane B's improvement-over-time hold across alternate seed texts, alternate domains, alternate model versions?

---

## 6. Methodology disambiguations (resolved 2026-05-04)

These were the five questions raised pre-design and ratified by user + GPT before this draft. They are pinned here so future readers don't relitigate them.

1. **Same prompts = same external prompts**, not same final assembled context. The final context is expected to differ; that difference is the treatment (P.5).
2. **Main baseline is seed-only**, not no-seed. The test measures runtime accumulation contribution beyond a shared seed baseline (P.6). Word choice: "baseline" rather than "control" to keep methodology aligned with TORMENT's guidance-not-control principle.
3. **Reuse rig probe 24's `non_shareable` Kestrel content** as the substrate-side audit payload. The harness IS the audit for `CODE_FOLLOWUP_REGISTRY.md` entry 01 (§3.7).
4. **Phase 0 is no-LLM substrate-only.** Phase 1 (LLM lane) waits until Phase 0 ratifies (P.1).
5. **Drift correction firing is NOT in first-pass scope.** Default check interval is 25; 10–20 turns may not exercise correction. Drift score trajectory is observable per turn, but correction firing gets its own Phase 2 test.

---

## 7. Output / reporting conventions

Matches the existing harness style (`stress_liar.py`, `stress_motif_saturation.py`, `stress_mood_spiral.py`):

- `outputs/<stress_module>_<UTC_ts>.csv` — row-per-observation, plain schema.
- `outputs/<stress_module>_<UTC_ts>.json` — full HTTP debug blobs.
- `outputs/` is gitignored (per existing convention; check parent `.gitignore`).
- Phase 0 produces `outputs/substrate_audit_<UTC_ts>.{csv,json}` per run.
- Phase 0 results note (markdown, ~1 page) appended to a new `SUBSTRATE_AUDIT_LOG.md` in the same folder. This is the file user + GPT review at the ratification gate.

---

## 8. What this design deliberately is NOT

- **Not a code change.** No Python files written by this commit. Code follows in subsequent commits once this design ratifies.
- **Not a Phase 1 spec.** Phase 1 has its own design doc drafted after Phase 0 completes.
- **Not a fabric-side instrumentation commitment.** Per P.2, instrumentation is added only if Phase 0 observation reveals diagnostics are insufficient.
- **Not a re-test of stress 3.1B.** The rig's response-layer findings remain canonical for what they tested. This harness covers a different layer.
- **Not coupled to the test rig.** Different repository folder, different test philosophy (substrate-side vs LLM-side), different deliverable shape. The two harnesses are complementary.
- **Not a multi-model matrix.** Phase 1 uses Gemini 2.5 Flash Lite (matching stress 3.1B baseline). Model-tier comparison is Phase 2.
- **Not a behavioral character-consistency test.** Structural drift score is the first-pass metric; behavioral consistency is harder and deferred.

---

## 9. Commit plan

Each commit is independently reviewable; the harness folder stays in a working state at every step.

**Commit A — this design (no code).**
- `torment_fabric/torment_stress_harness/SUBSTRATE_TIME_HARNESS_DESIGN.md` (this document).
- No other files. Architecture-first.

**Commit B — Phase 0 implementation.**
- `torment_fabric/torment_stress_harness/stress_substrate_audit.py` (~150 lines, modeled on `stress_liar.py`'s shape).
- Reuses `common.py` helpers where they fit: `ensure_workspace`, `ingest`, `query`, `health`.
- **Seeded agent creation requires a local helper** because the existing `common.py` `ensure_agent()` does not accept a seed argument. Commit B adds a local `ensure_seeded_agent()` inside `stress_substrate_audit.py` that posts directly to `/agent/create` with the full seeded payload (per `CHARACTER_SYSTEM.md` agent-creation schema). `common.py` is left unchanged unless the seeded-create payload pattern proves broadly useful and a separate ratification authorizes the helper change.
- A0 precondition check (per §3.5) is implemented before A1–A4: the harness reads the ingest response and (if needed) follows up with a query/inspection to verify governance / provenance fields were stored. PRECONDITION_FAILED is a distinct exit code from FAIL.
- CSV + JSON output per §3.8.
- Configurable via argparse (workspace ID, agent ID, output dir, embedding provider override).

**Commit C — first Phase 0 run + results note.**
- Run `stress_substrate_audit.py` against a fresh local TORMENT instance.
- Produce `outputs/substrate_audit_<UTC_ts>.{csv,json}`.
- Write `torment_fabric/torment_stress_harness/SUBSTRATE_AUDIT_LOG.md` with the first-run results note (PASS / CONCERN / FAIL).
- Hold for user + GPT ratification (the §P.4 gate).

**Commit D (gated) — instrumentation if Phase 0 = CONCERN.**
- Only if Phase 0 ratifies as CONCERN. Adds minimal diagnostic instrumentation per P.2 narrow scope.
- Re-runs Phase 0; updates `SUBSTRATE_AUDIT_LOG.md`.

**Commit E (gated) — Phase 1 design doc.**
- Only after Phase 0 ratifies as PASS. Drafted as `SUBSTRATE_TIME_HARNESS_PHASE_1_DESIGN.md`. Separately ratified before Phase 1 implementation.

**Commit F (gated) — Phase 1 implementation.**
- Only after Phase 1 design ratifies. Adds `stress_lane_trajectory.py` or similar.

---

## 10. Ratification record

**Drafted:** 2026-05-04 by Claude.

**Awaiting ratification by user + GPT.** Pending checklist:

- [ ] §1 — Purpose accepted (substrate-time work that the rig cannot cover; bridges to registry entry 01 audit)
- [ ] §2 — P.1–P.10 accepted (substrate-first, observe-first, three-outcome Phase 0, ratification gate, prompt parity, seed-only baseline, deterministic Phase 0, retrieval-probe queries, actual prompt assembly, no-mutation provenance check)
- [ ] §3 — Phase 0 detailed spec accepted (env, setup, queries, assertions, three outcomes, registry entry 01 connection, output format)
- [ ] §4 — Phase 1 outline accepted; detailed design separately ratified later
- [ ] §5 — Phase 2 deferred extensions accepted as scope-visible-but-not-designed
- [ ] §6 — Methodology disambiguations pinned
- [ ] §7 — Output / reporting conventions accepted
- [ ] §8 — What this design is NOT accepted
- [ ] §9 — Commit plan A → F (with C/D/E/F gated) accepted

After ratification, this doc is frozen until a separately ratified amendment.

---

## Appendix — Source trail

- User + GPT exchange 2026-05-04 — substrate-time pivot from rig response-layer testing
- User's framing: *"a memory is tested by continued time"*
- Closing principle: *"the substrate is a basin that pulls, not a fence that commands"*
- Five methodology questions resolved before this draft (§6)
- Three smaller specs ratified: Phase 0 queries are retrieval probes, Phase 1 uses actual assembly, RNG seeds locked
- `torment_test_rig/docs/CODE_FOLLOWUP_REGISTRY.md` entry 01 — the registry entry this harness's Phase 0 audits
- `torment_test_rig/docs/ROADMAP_PROBE_LOG.md` Stress 3.1B — the response-layer signal that justified this work
- `torment_fabric/torment_stress_harness/README.md`, `common.py`, `stress_liar.py` — local conventions matched by this design
