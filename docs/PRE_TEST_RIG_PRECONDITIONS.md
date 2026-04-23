# TORMENT External Inference Test Rig — Preconditions

**Status:** **RATIFIED 2026-04-22** by user + GPT after one wording-narrowing review round (three narrow edits applied to §4, §8, and §10 carry-forward concern #1). Rig design-doc phase is unblocked.
**Date:** 2026-04-22
**Scope:** Preconditions for a sibling, local-only test rig that exercises the TORMENT memory system through external LLM calls (and optionally external TTS) without modifying the canonical core. This is a lightweight ratification gate for an experimental sandbox, not a roadmap block.

**Precedents (inherited, not restated):**
- `docs/PRE_BLOCK_A_PRECONDITIONS.md`, `docs/PRE_BLOCK_B_PRECONDITIONS.md`, `docs/PRE_BLOCK_C_PRECONDITIONS.md` — ratification discipline pattern
- `docs/DOCTRINE_v2.4.x.md` — standing principles
- `docs/BLOCK_A_DESIGN.md`, `docs/BLOCK_B_DESIGN.md`, `docs/BLOCK_C_DESIGN.md` — ratified substrate/reference/closure shape the rig observes from outside
- The writeback-vs-closure separation across all three Block PRE_ docs — applied here as rig-vs-core separation
- Project memory: `feedback_ratification_and_narrowing.md` (ratification-first, narrowing); `feedback_claude_desktop_first.md` (live validation loop discipline); `feedback_windows_python_invocation.md` (`py -3` on Windows)

> This document freezes the preconditions for building the external inference test rig. It is a ratification gate, not a design spec. It does not pre-decide the rig's internal folder layout, the OpenRouter adapter API shape, the prompt builder format, the transcript log schema, the TTS abstraction surface, or the eventual cross-platform setup guides — those belong to the rig design doc, which cannot start until this document is ratified. The rig is deliberately scoped as a local sandbox; the discipline is intentionally lighter than Block A/B/C because the rig is not substrate. But the load-bearing rule is the same: **whatever happens inside the rig must not bleed back into ratified core.**

---

## 1. Mission sentence

> **How should TORMENT be exercised through external inference (LLM via OpenRouter; optionally TTS via Orpheus or Gemini speech) so that (1) the rig lives as a sibling to `torment_fabric/` and never copies, mutates, or shadows core; (2) the rig has zero write authority into TORMENT core state; (3) the rig does not become a second governance authority by re-authoring core eligibility logic; (4) external model output is treated as advisory artifact, never as memory; (5) secrets stay out of tracked files and out of logs; (6) the rig is built in ratified phases (Phase 0 wire test → Phase 1 mock context → Phase 2 ratified core export helper → Phase 3 optional TTS) with each phase gated; and (7) any rig-side discovery that requires a core change pauses the rig and triggers its own separately ratified change to core?**

All seven clauses are load-bearing. Clause 1 is the architectural separation. Clauses 2 and 3 are the governance separation. Clause 4 is the consequence of (2) for the dominant failure mode (model "suggests" → operator "promotes" → core corrupted). Clause 5 is the operational hygiene that protects (1)–(4) from being undone by accident. Clause 6 is the workflow discipline carried over from Block A/B/C. Clause 7 is the escape valve: the rig is allowed to discover it needs something from core, but it is not allowed to *take* that something — it must request it through the same ratification path Block work uses.

---

## 2. Architectural boundary

The rig lives at the project-root level as a **sibling folder** to `torment_fabric/`:

```
TORMENT-fabric_v2/
  torment_fabric/         # canonical TORMENT core — frozen relative to the rig
  torment_test_rig/       # sibling rig — local-only sandbox
```

The rig may import from `torment_fabric` only through narrow, explicit, read-only access patterns. The Block C design doc and Block A/B design docs define what "core state" means; the rig must treat all of that as read-only.

**Allowed access patterns** (the rig design doc enumerates the concrete API; this doc states the shape):
- Read-only handles to memory entries, references, environments, and closures.
- Pure query methods that do not mutate state and do not produce side effects beyond returning data.

**Forbidden access patterns:**
- Any method that writes, ingests, ratifies, commits, edits, deletes, archives, advances baton lifecycle, mutates conflict status, or modifies any ledger.
- Any monkeypatching of core modules.
- Any import that triggers initialization side effects in core (e.g., loading a corpus into the running core process, spinning up a writeback path, attaching listeners).
- Any duplication of core code into the rig (no copying core files, no re-implementing core data structures, no parallel governance state).

If the rig later needs a method that does not yet exist on core (e.g., a read-only `is_exportable(entry) -> bool` predicate), that method is added to core through a separately ratified change — never invented inside the rig.

---

## 3. Red lines

The existing red lines from `Roadmap_working_memo.md`, `DOCTRINE_v2.4.x.md`, and Block A/B/C remain in force. The rig adds **five new red lines**, prefixed `RG+` (Rig Governance) to keep them distinct from the Block roadmap's `R+` series.

### RG+1 — No copying of TORMENT core into the rig

The rig must not duplicate any TORMENT core source file, data structure, or governance rule into its own tree. The rig consumes core from a single canonical location, by import. A second copy of core under any name (mirror, snapshot, fork, "test variant") is refused.

### RG+2 — Zero mutation authority over TORMENT core state

The rig has no write capability into core, period. No write methods exposed on the rig's core handle, no automatic ingest path, no advisory promotion route, no shared-file write into core's storage paths. Model replies live only in the rig's own `outputs/` directory as transcript artifacts and never become memory entries. This is enforced as architecture (the handle does not expose mutation methods), not as discipline.

### RG+3 — Rig is not a second governance authority

The rig must not re-author or re-implement governance logic that lives in core (export eligibility, conflict status, baton lifecycle decisions, closure ratification). If the rig needs a governance answer, it must come from core through a read-only helper. Until such a helper exists in core, the rig works with **manually selected safe inputs only** (curated test fixtures, not live memory). Inventing rig-side governance to fill a gap is refused; the gap is escalated under §7.

### RG+4 — No secrets in tracked files

API keys, tokens, and any other credentials live only in untracked locations: `.env`, OS env vars, OS keychain, or local-only config not under version control. Tracked files (READMEs, `.env.example`, configs ending in `.example.json`) carry placeholders only. No secret material in test logs, transcripts, screenshots, or demo files. `.gitignore` discipline is part of the design doc deliverable.

### RG+5 — Phase gating

No phase begins until the prior phase is ratified. Phase 0 is the wire test; Phase 1 is mock-context inference; Phase 2 is core-helper-mediated context export; Phase 3 is optional TTS. Skipping ahead, bundling phases, or "while I'm here"-style phase merging is refused. Each phase has its own narrow acceptance criteria (Phase 0's are in §6; later phases declare theirs in their own ratification step).

---

## 4. No-mutation invariant (elaborated)

RG+2 deserves its own section because it is the most likely failure mode.

The dominant adversarial path is: a model output looks useful → an operator (rig user, demo viewer, or automation) decides to "save it" → it lands in core memory → core now contains material whose provenance is "an external model said so during a sandbox test." This is exactly the failure mode Block A's substrate guarantees, Block B's reference/environment separation, and Block C's closure ratification rules were built to prevent. The rig must not become the back door.

Concretely:
- The rig's core handle is read-only by **construction**. A "writeable handle for testing" is refused. The rig does not verify write behavior against canonical core; any write-path testing belongs to separately scoped core-side testing, not the external inference rig.
- Model output is stored in `torment_test_rig/outputs/` only. Filenames, formats, and rotation policy are design-doc concerns, but the location is fixed: never inside `torment_fabric/`, never in any path core reads from at runtime.
- Any future feature like "promote this model output into a memory candidate" is **out of scope for the rig**. Such a feature, if ever needed, is a core-side writeback path subject to the writeback gate framing (`MEMORY.md` → `project_writeback_gate_framing.md`), not a rig feature.

---

## 5. Phasing

The rig is built in four ratified phases. Each phase has a single concrete objective and a narrow acceptance criterion. No phase begins until the prior phase passes its criterion and is ratified by user + GPT.

### Phase 0 — Wire test (no memory, no guard, no formatting)

Prove the OpenRouter wire and the secrets path. The rig sends a fixed string ("hello"), receives a reply, prints it to console, and writes one transcript line to `outputs/`. No TORMENT import. No prompt construction beyond the literal payload. No memory export. No model selection logic. One adapter, one model, one credential source.

### Phase 1 — Mock context, prompt builder, telemetry

Construct prompts from **manually curated test fixtures** (hand-written JSON or Python literals representing what a memory snippet *might* look like). Send them through the Phase 0 adapter. Add a prompt builder, a transcript with structured fields (provider, model, latency, estimated cost if available, request id), and a smoke test. Still no TORMENT import. Mock data only.

### Phase 2 — Core-helper-mediated export

Only entered if a small read-only export-eligibility helper has been added to core via a **separately ratified change** (its own short PRE_ doc + design doc + PR, scoped to that helper alone). Once the helper exists, the rig consumes it and replaces the curated fixtures with live memory pulled through the helper. The rig never decides eligibility itself.

### Phase 3 — Optional TTS

Only entered after Phases 0–2 are ratified. Adds a TTS abstraction with two adapters (Orpheus, Gemini speech). Voice is opt-in and platform-conditional. Operational/cost/legal review per provider is a precondition of this phase, not a side effect.

---

## 6. Acceptance criteria for Phase 0

These are the only acceptance criteria fixed by this preconditions doc. Phases 1, 2, and 3 declare their own criteria when they reach ratification.

1. **Wire works.** With a valid OpenRouter API key in an untracked location (`.env` or env var), running the Phase 0 entrypoint sends a literal payload to a configured model and prints the model's reply to console.
2. **Secrets path is clean.** No key material appears in any tracked file (verified by `git status` showing only README / `.env.example` / placeholder configs as new tracked files), and no key appears in the transcript artifact written to `outputs/`.
3. **Transcript artifact exists.** One file in `outputs/` records timestamp, provider, model, request, response, and elapsed time. The file is in `outputs/` and `outputs/` is gitignored.
4. **Zero TORMENT touch.** `git diff` against `torment_fabric/` shows no changes. The rig does not import from `torment_fabric`. Running Phase 0 does not read or write any path inside `torment_fabric/`.
5. **Failure modes are visible.** A bad key, an unreachable provider, and a malformed request each produce a clearly-named error in the transcript and a non-zero exit. No silent fallback to a different model or provider.

If any criterion fails, Phase 0 is not passed and Phase 1 cannot begin.

---

## 7. Escalation rule

When the rig discovers it needs something from core that does not yet exist (a new read-only helper, a new query method, a new exportability predicate), the rig **pauses** and the need is escalated as a separately ratified core change.

Concretely:
- The rig opens an issue or short doc describing exactly what it needs and why.
- A short PRE_ doc is drafted for that core change (one section may be enough — this is not a full Block ratification unless the change is substantive).
- The change is designed, ratified, implemented, and merged through the same workflow Block A/B/C used.
- The rig resumes with the new core helper available.

The rig never invents the helper internally to keep moving. The whole point of the rig is that core stays clean; if core needs an addition, that addition gets the same governance attention everything else does. This rule is what keeps RG+3 (no second governance authority) enforceable in practice.

---

## 8. Cross-platform target matrix

The rig is designed cross-platform from day one but only one platform is validated per phase ratification.

| Platform | Phase 0 | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|---|
| Windows (primary) | Required | Required | Required | Required for any TTS-API path |
| Pop!_OS / Linux (friend) | Parallel or after Win | Parallel or after Win | Parallel or after Win | Required for any local-runtime TTS path (e.g., Orpheus on NVIDIA) |
| macOS | Deferred | Deferred | Deferred | Deferred |

Notes:
- Windows uses `py -3`, not `python`, in any documented invocation (`feedback_windows_python_invocation.md`).
- Adapter and harness code stays platform-agnostic. Platform-specific guidance lives only in setup docs (e.g., `torment_test_rig/docs/setup/windows.md`).
- macOS guides are not pre-written without a tester; speculative cross-platform coverage is refused.
- Windows remains the primary ratification target; Pop!_OS / Linux validation may happen immediately after Windows or proceed in parallel when a tester is available — neither order is required by ratification.

---

## 9. What this document does not cover

- **Rig design.** Folder layout inside `torment_test_rig/`, adapter API surface, prompt builder format, transcript schema, telemetry fields, retry/timeout behavior, fallback policy, TTS abstraction. All owned by the rig design doc, which is unblocked once this document is ratified.
- **Core export-eligibility helper.** If/when needed, gets its own short PRE_ doc and design doc per §7. This document does not pre-design or pre-approve that helper.
- **Provider terms / legal review.** OpenRouter terms, underlying model license review, Orpheus license, Gemini speech ToS, redistribution rules, BYOK vs proxied-credential distinction. Required before any phase that touches the relevant provider; tracked separately, not adjudicated here.
- **Git arrangement.** Whether the rig lives as its own git repo (preferred) or as a sibling folder in the same repo with selective ignores (acceptable). The design doc picks one based on practical constraints. Either choice must satisfy RG+4.
- **`.claude/settings.json` keys pattern.** GPT flagged this as risky. The rig design doc names the secret-loading mechanism explicitly (`.env`, OS env vars, OS keychain) and states why `.claude/settings.json` is not used for credentials.
- **Voice cloning consent / preset voice licensing.** Phase 3 concern, not adjudicated here.
- **Hivemind / multi-agent variants.** Out of scope for the rig. The rig drives one agent through one external inference path. Hivemind testing, if ever needed, is a separate question against the parallel-branches vision (`project_hivemind_vision.md`).

---

## 10. Ratification record

**Drafted:** 2026-04-22 by Claude, following the six decisions returned by GPT the same day:
1. Folder location → sibling
2. Git hygiene → separate repo preferred; sibling-with-selective-ignore acceptable
3. Export guard → no rig-side governance; defer to ratified core helper
4. No-writeback → hard invariant
5. Phasing → Phase 0 first
6. Naming → `rig/` or `harness/`, not `core/`

**Ratification pass (2026-04-22, user + GPT):**

- [x] §1 — Mission sentence wording accepted
- [x] §2 — Architectural boundary (sibling, read-only access patterns) accepted
- [x] §3 — Red lines RG+1 / RG+2 / RG+3 / RG+4 / RG+5 wording accepted
- [x] §4 — No-mutation invariant elaboration accepted — write-verification sentence narrowed during review (no rig-side write-path testing concept introduced)
- [x] §5 — Phasing (Phase 0 → 1 → 2 → 3) accepted
- [x] §6 — Phase 0 acceptance criteria accepted
- [x] §7 — Escalation rule accepted
- [x] §8 — Cross-platform target matrix accepted — Linux timing relaxed during review (parallel-with-Windows allowed)
- [x] §9 — Scope boundary accepted

**Status:** **RATIFIED 2026-04-22 by user + GPT.** Rig design-doc phase is unblocked. Any change to these rules after this point requires a separately ratified amendment.

### Carry-forward concerns for the rig design doc

Concerns that the design doc should keep visibly load-bearing once this is ratified:

1. **The read-only handle is constructed, not promised (binding from Phase 2).** Phase 0 and Phase 1 do not import live TORMENT memory, so the constructed-handle requirement is a future obligation for the Phase 2 design rather than an immediate implementation burden. Once Phase 2 begins, the design must make mutation methods physically absent on the handle, not "documented as forbidden" — discipline-only enforcement is refused.
2. **`outputs/` location is fixed.** Even when the design picks the transcript schema, the location stays inside the rig folder, never inside `torment_fabric/`, never in any path core reads at runtime.
3. **Manual fixtures vs. live memory is a Phase boundary, not a config flag.** The design must not introduce a `use_live_memory=True` toggle in Phase 1 that becomes the de-facto Phase 2 entry point. Phase 2 begins only when the ratified core helper exists.
4. **Cross-platform stays in setup docs, not in adapter code.** If a platform branch shows up inside `adapters/` or `harness/`, the design has drifted.
5. **The rig is a research instrument, not a product.** Demo polish, UI integration with the HTML character creator, broadcast/window mode wiring, and any other product-shaped affordance is out of scope. If the rig produces results worth promoting later, promotion is its own ratified question.

---

## Appendix — Source trail

Assembled from:
- User + GPT exchange 2026-04-22 (six framing decisions)
- `docs/PRE_BLOCK_A_PRECONDITIONS.md`, `docs/PRE_BLOCK_B_PRECONDITIONS.md`, `docs/PRE_BLOCK_C_PRECONDITIONS.md` — preconditions pattern carried forward (lighter form for sandbox)
- `docs/DOCTRINE_v2.4.x.md` — standing principles
- `docs/BLOCK_A_DESIGN.md`, `docs/BLOCK_B_DESIGN.md`, `docs/BLOCK_C_DESIGN.md` — ratified core surface the rig observes
- Project memory: ratification-and-narrowing discipline, writeback-gate framing, Windows Python invocation convention, Claude Desktop first for live validation
