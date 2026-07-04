# TORMENT Brainvision Recovery Map v0.5 — HELD Research State

**Status:** DOCS-ONLY recording pass. **Non-authorizing, non-implementing. Opens no implementation lane.**

This document records the receipt-consolidated Brainvision recovery state after source archaeology
(Claude) and a Codex **MODIFY** review. It restores Brainvision as a recovered *research direction*
only — **not** a live system, **not** an active bridge, **not** implementation authorization.
`PROJECT_ORIENTATION_MAP.md` Section 0 remains the active work-order and wins unless Hilmir explicitly
overrides. Current ceiling remains **memory/context floor + Mode 0**.

**Safe thesis (use this):**

> Brainvision is a possible future offline research question: whether visual/retinal descriptors can be
> mapped into a quarantined ψ-like spectral space using service-disconnected spectral research math,
> without touching live memory, prompt/context, identity, action, render-body, or autonomy surfaces.

**Avoid these phrases (receipts do not support them):**

- "Brainvision is the visual bridge into TORMENT."
- "Brainvision plugs vision into the live kernel."
- "Brainvision uses SRG for perception."
- "Brainvision uses the live memory kernel."
- "Brainvision has an active descriptor→ψ bridge."

## 0. Status

- HELD research state.
- No implementation lane open.
- No live Brainvision bridge.
- No camera/runtime/sensor lane.
- No render-body lane.
- No autonomy lane.
- No memory/prompt/context lane.
- No Section 0 pointer yet.

## 1. What was restored

The older Brainvision idea — partly lost in a PC crash and reconstructed from surviving materials
(`../visual_bus_v0/`, the root `TRIOCTA_VISUAL_NEURAL_BUS_RESEARCH_SCAN.md`, the two
`TRIOCTA_VISUAL_BUS_EXPERIMENT_SPEC*` files, and `../brainvision_research/…/rainbow.pdf`) — is recovered
as a serious **visual/retinal descriptor research direction**. It is not a random new feature and not
merely "add a vision model." The recovered intuition is a geometry-first perception front-end feeding
spectral/recursive diagnostics, distinct from a generic learned latent world model (e.g. LeWorldModel,
used only as an external reference, not a target). Brainvision is restored as a **recovered, bounded,
not-live, not-implemented, not-connected, not-authoritative, HELD** research direction.

## 2. What was corrected

Codex returned **MODIFY / blocked until source receipt** on the earlier recovery map. Source archaeology
produced the following corrections:

- TriOctaMemoryKernel is live/active as a memory-modulation surface.
- RSBModel / ψ[c,m,h] exists but is research/dormant relative to the live path.
- Co-location under `torment_service/kernel/` does not prove live execution.
- visual_bus_v0 is old-demo evidence only, not Brainvision validation.
- No active descriptor→ψ Brainvision bridge is source-confirmed.
- No Brainvision event export is source-confirmed.
- Camera/runtime/control/autonomy lanes remain closed.

## 3. Source-safe claims

The following are safe enough after receipts and Codex review:

- TriOctaMemoryKernel is live/active as a memory-modulation surface.
- RSBModel / ψ[c,m,h] exists, but is research/dormant relative to the live path.
- Co-location under `torment_service/kernel/` does not prove live execution.
- visual_bus_v0 is old-demo evidence only, not Brainvision validation.
- No active descriptor→ψ Brainvision bridge is source-confirmed.
- No Brainvision event export is source-confirmed.
- Camera/runtime/control/autonomy lanes remain closed.
- The hard quarantine (Section 5) is necessary.

## 4. Receipt-consolidated surface statuses

### TriOctaMemoryKernel

**Status:** live memory-modulation surface; Brainvision must not call, import, perturb, wrap, or feed it.

*Receipts:* def `torment_service/memory_kernel.py:58` (`kernel/model_core.py:114`); instantiated
`torment_service/fabric.py:694`; invoked every live turn at `fabric.py:2596`
(`self.kernel.process(...)`). Downstream reads are `debug["coherence"]` and `debug["tri_mod"]`, which
modulate strength/confidence/half_life/promotion (`memory_kernel.py:392-395`).

### RSBModel / ψ[c,m,h]

**Status:** research/dormant relative to live path.

**Footgun warning:**

> RSBModel / ψ[c,m,h] physically lives inside `torment_service/kernel/`, but physical co-location does
> not mean live-path execution. Future work must not mistake co-location for live authority.

*Receipts:* def `torment_service/kernel/rsb_model.py:45`; **zero import/instantiation/call in any
live-path module of `torment_service/`**; ψ/`psi_hist` produced only at `kernel/rsb_model.py:389` and
consumed only at `kernel/definitions.py:240-597`; the live kernel state is `Omega` (a complex 3-vector),
not ψ. spectral entropy (`definitions.py:476`), dominant band m0 (`definitions.py:464`), helicity, and
`alpha_eff` (`rsb_model.py:250-297`) have no live-path caller. The spectral `classify_run` Class I/II/III
(`definitions.py:354`) is **not** the live `drift_regime` action veto (`action_policy.py` /
`agent_loop.py`) — those are separate mechanisms.

**Brainvision rule:** Do not import dormant RSBModel from `torment_service/kernel/` for Brainvision.
Copy or re-derive only the pure spectral equations into an offline Brainvision research namespace.

### Z surfaces (Z_macro / Z_chiral / Z_vec / Z_total)

**Status:**

> Z surfaces are computed live where the TriOcta model runs, but no source-confirmed authority-bearing
> consumer has been established for Brainvision purposes.

Equivalently: computed-live but non-authorizing for Brainvision; no source-confirmed Brainvision, action,
memory-write, prompt, identity, or final-output authority attaches to Z surfaces.

*Receipts:* computed each turn at `kernel/model_core.py:209-223`; only `Z_chiral` is persisted
(`checkpoint.py:129,157-158`); no scoring/retrieval/compression module reads them.

### SRG

**Status:**

> SRG production/scoring is implemented but default-off; however SRG-shaped metadata has existing live
> readers if present, so Brainvision must not produce, mutate, import, or reinterpret SRG payloads.

*Receipts:* `torment_service/srg_engine.py`; live path guarded by `self._srg_enable`, default off
(`fabric.py:736`, env `TORMENT_SRG_ENABLE=0`). When enabled, SRG feeds character/stance surfaces
(`fabric.py:2620-2647` → `_srg_relational_ema` → `geometric_harvester.py:137-139` social_resonance →
`stance_policy.py:78`), i.e. **character identity / three-gravity** territory — not perception.

**Brainvision rule:** Brainvision must remain SRG-free.

### Spirit-return warmth

**Status:**

> Spirit-return has no visual/Brainvision source; any existing SRG influence into warmth or presentation
> remains an already-separate surface and must not be fed by Brainvision.

*Receipts:* producer `torment_service/spirit_return.py` (`WarmupTracker`) + text-word warmth
(`character.py:647-703`); consumers `character.py:914-970` (voice guidance; warmth modulates a character
gravity `g_mod` at `character.py:708`), `app.py:1484-1489` (surfaced into character context), endpoints
`app.py:2045` and `app.py:2124`. Warmth source is text + warmup tracker — no visual input.

**Brainvision rule:** Brainvision must not feed warmth, character gravity, voice presentation,
spirit-return summaries, or character context.

### visual_bus_v0

**Status:** old-demo only; fixed mapping; not learned; H0 not rejected; not Brainvision validation;
useful as baseline and warning evidence.

*Receipts:* `../visual_bus_v0/experiment_torment_visual_bus_v0.py` maps radial-2D-FFT bands of luminance,
frame-difference, and Sobel edge into ψ(3,M,2) (`build_psi:265-289`, channels 0/1/2; helicity slot 1 =
one-step temporal delta); mapping is fixed/frozen (`Config:83-117`); baseline is frame-diff
(`frame_diff_signal:502-509`). `outputs/results_summary.md`: H1(a) NOT SUPPORTED, H1(b) NOT SUPPORTED,
H0 not rejected (surviving summary is the n=4 synthetic dry-run variant). It imports the `v4.0/` kernel,
not the live service.

**Interpretation:** visual_bus_v0 proves that an old fixed descriptor→ψ attempt existed. It does not
prove that Brainvision works. It warns that fixed FFT-style mappings may fail and must be tested against
explicit baselines.

## 5. Hard quarantine

No Brainvision descriptor may touch:

- SRG payloads
- TriOctaMemoryKernel
- retrieval scoring
- compression
- lifecycle protection
- spirit-return warmth
- character gravity
- stance/social resonance
- MemoryPlan
- prompt/context
- durable memory
- canon/identity/personhood evidence
- final-output authority
- action policy
- MCP/tools
- OS input
- scheduler
- camera runtime
- sensor loop
- render-body movement
- autonomy
- shared env flags
- service config
- dispatcher
- export bus

## 6. Pure-math research guardrail

> Copy or re-derive only the pure spectral equations into an offline Brainvision research namespace, with
> no service imports and no authority-bearing outputs.

This means:

- no import from torment_service
- no call into TriOctaMemoryKernel
- no SRG payloads
- no prompt/context access
- no memory read/write
- no render-body/control/action path
- no shared env flags
- no service config
- no dispatcher
- no export bus
- no tools
- no scheduler
- no autonomy

## 7. Minimum future offline falsifier wording

If a future falsifier is opened, it must be framed this narrowly:

> A future Brainvision falsifier, if opened, may use only offline prerecorded visual descriptors and
> service-disconnected spectral math to test predeclared descriptor→ψ mappings against explicit
> baselines; it may not use camera/runtime input, prompt/context, memory, SRG, TriOctaMemoryKernel,
> render-body control, tools, scheduler/autonomy, durable writes, identity/canon evidence, or
> final-output authority.

## 8. Future implementation posture

> Future Brainvision code, if ever opened, should live in a separate offline research namespace inside
> the repo, such as `research/brainvision/` or `experiments/brainvision/`, not in `torment_service/`.

> The first future code lane must be an offline falsifier harness only, using prerecorded inputs and
> explicit baselines.

No implementation is authorized by this document. This section records posture only.

## 9. Current next-state

- Remain HELD.
- No Section 0 pointer yet.
- No implementation yet.
- No falsifier yet.
- The next legitimate move after recording this doc is a fresh-chat handoff or a chat-only offline
  falsifier boundary frame — chosen by the operator, not opened by momentum.

Until then, Brainvision remains: **recovered / bounded / not live / not implemented / not connected /
not authoritative / held.**

*End — TORMENT Brainvision Recovery Map v0.5. Docs-only, non-authorizing. Opens no implementation lane.*
