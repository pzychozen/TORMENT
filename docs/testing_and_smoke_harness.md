# Testing and Smoke Harness Guide

TORMENT v2.2

---

## Test Suite Overview

The full test suite runs with `pytest` from the `torment_fabric/` directory:

```bash
cd torment_fabric
python -m pytest tests/ -v
```

Some tests require FastAPI and MCP packages. To skip those in offline environments:

```bash
python -m pytest tests/ -v \
  --ignore=tests/test_app.py \
  --ignore=tests/test_embed_dim_lock.py \
  --ignore=tests/test_mcp_server.py \
  --ignore=tests/test_observability_endpoints.py \
  --ignore=tests/test_smoke_api.py
```

Current count: 1725+ passing tests.

---

## Geometric Comparison Harness

**File:** `tests/run_geo_compare.py`

Runs the stance policy against multiple geometric profiles and test inputs. Reports which profile/input combinations produce stance shifts compared to the no-geometry baseline.

```bash
python tests/run_geo_compare.py
```

**What it does:**

1. Defines 7 geometric profiles (neutral, stable_locked, drifting_fragile, socially_open, ambiguity_tolerant, extreme_low, extreme_high) plus a `none` baseline
2. Runs 9 test inputs through the thinking controller with each profile
3. Compares each result against the `none` baseline
4. Marks shifts with a visual indicator
5. Prints a summary: total comparisons, shift count, shift rate, governance robustness

**JSON output:** `python tests/run_geo_compare.py --json` for machine-readable results.

**What good output looks like:**

- Shift rate between 3-10% — too low means geometry isn't doing anything, too high means the band is too wide
- All governance inputs unchanged across profiles — rules 1-2 must never be modulated
- Shifts should be classifiable as "correct for this character state" — a fragile agent asking for clarification is good; a stable agent suddenly refusing to respond is bad

---

## Stance Policy Tests

**File:** `tests/test_stance_policy.py`

Unit tests for the stance policy including geometric modulation:

- No-geo baseline tests (identity-defer, ambiguity-clarify, and normal stances unchanged when geometry is absent)
- High stability loosens identity-defer threshold
- Low stability tightens identity-defer threshold
- High coherence loosens ambiguity-clarify threshold
- Social resonance appears in modifier dict
- Geometric context round-trips through to_dict / from_dict

Run just these:

```bash
python -m pytest tests/test_stance_policy.py -v
```

---

## Spirit Reflection Tests

**File:** `tests/test_spirit_reflection.py` (31 tests)

Unit tests for the four-stage reflection pipeline:

- Extraction: spirit return hits extracted, non-spirit ignored, reflections filtered by depth
- Influence scoring: high overlap scores high, zero overlap scores low, resonance bonus, warmth bonus
- Building: derived summary not copied, cooldown key format, excerpt truncation, eligible always false
- Anti-echo guard: threshold rejection, depth rejection, cooldown enforcement, duplicate suppression
- Storage: store and retrieve, persistence across instances, recent/stats, path traversal guard
- End-to-end: full pipeline with low/high influence, cooldown blocking, deep memory not mutated

**File:** `tests/test_spirit_reflection_integration.py` (12 tests)

Integration tests for wired behavior:

- Fail-soft: broken storage path doesn't crash, empty blocks, garbage input
- End-to-end creation: valid hit creates reflection, multiple hits scored independently
- Non-spirit hits: normal hits produce zero reflections
- Persistence: eligible_for_spirit_return stays False after reload, tamper resistance on disk
- Retrieval precedence: spirit hit classification unchanged, reflections can't re-enter pipeline

Run both:

```bash
python -m pytest tests/test_spirit_reflection.py tests/test_spirit_reflection_integration.py -v
```

---

## Geometric Harvester Tests

**File:** `tests/test_geometric_harvester.py` (11 tests)

Tests for extracting GeometricStanceContext from character state:

- None returns on missing data
- Minimal character state handling
- Coherence normalization
- High coherence mapping
- High tearing risk
- Drift toward/away from seed
- Basin role boost
- Live social boost
- All fields bounded to [0, 1]

---

## Spirit Return Tests

**File:** `tests/test_spirit_return.py` (53 tests)

Full coverage of the spirit return pipeline:

- Symbol interaction matrix: all 19 rules, echo fallback, contrast fallback, wildcard matching
- Return mode selection: resonance/surfacing/recollection conditions
- Warmth computation: floor, increment, cap, window expiry
- WarmupTracker: creation, subsequent appearances, persistence, stats
- Enrichment pipeline: full enrichment, SRG crystal forcing, heartbeat class boost, duration floor

**File:** `tests/test_spirit_return_voice.py` (34 tests)

Voice cue and retrieval assembly tests:

- Tier classification for spirit return hits
- Voice cue generation by mode
- Block enrichment with flavor text
- Warmth secondary sorting
- Character context spirit_return_summary generation

---

## MCP Smoke Tests

**File:** `docs/MCP_SMOKE_TEST.md`

35-point testing checklist for MCP v1 surface. Requires a running server with FastAPI. Covers connection/discovery, tool sanity (all 6 Tier 1 tools + canonical), error/rejection handling, resources, context behavior, and decision/result code audit.

---

## How to Interpret Failures

**Pre-existing visualization failures** (`test_visualize_attractors.py`): 5 tests that need live agent data. These always fail in clean environments — not a regression.

**FastAPI import errors**: 4 test files require `fastapi` and `mcp` packages. Skip them in offline environments (see command above).

**All other failures are real** and should be investigated. The test suite is designed to have zero non-environment failures.
