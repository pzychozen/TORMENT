# Brainvision — offline research harness

**Offline-only research.** This directory is NOT part of the TORMENT service and MUST NOT be imported by
it. It implements the first Brainvision falsifier described in the design doc, entirely disconnected from
runtime surfaces.

- Design: `../../docs/TORMENT_BRAINVISION_DESCRIPTOR_PSI_FALSIFIER_DESIGN_v0.1.md`
- Boundary: `../../docs/TORMENT_BRAINVISION_OFFLINE_FALSIFIER_BOUNDARY_FRAME_v0.md`
- Recovery map: `../../docs/TORMENT_BRAINVISION_RECOVERY_MAP_v0.5.md`

## Hard rules (enforced by tests)

- **No imports from `torment_service/`** (including `torment_service/kernel/`). Enforced by
  `tests/research/test_brainvision_offline_falsifier.py`.
- No SRG, TriOctaMemoryKernel, RSBModel, MemoryPlan, prompt/context, memory, render-body, tools/MCP,
  scheduler/autonomy, identity/canon, or final-output surfaces.
- No camera, screen capture, sensor stream, browser/game/VR/OS stream, or process polling. **Deterministic
  synthetic descriptor fixtures only.**
- Outputs are offline metrics/logs only, written under `research/brainvision/results/`.
- `PsiBV` is an independently re-derived offline tensor. It does **not** import or reuse `RSBModel`.

## Dependencies

stdlib + `numpy` only (`numpy` is already a project dependency; see `requirements.txt`). No scipy, no
sklearn.

## Run

```
python research/brainvision/run_falsifier.py
```

## Test

Run the complete offline Brainvision suite explicitly:

```
python -m pytest -q -o addopts= research/brainvision tests/research
# or: make test-brainvision
```

For an individual Brainvision test, override the ordinary TORMENT collection options:

```
python -m pytest -q -o addopts= tests/research/test_brainvision_offline_falsifier.py
```

## Status

HELD offline research falsifier. Not wired to any live surface. A negative result ("does not beat
baselines") is a **valid closure**, not permission to widen scope or add runtime inputs.
