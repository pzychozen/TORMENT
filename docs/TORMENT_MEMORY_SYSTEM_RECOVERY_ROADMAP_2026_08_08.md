# TORMENT memory-system recovery roadmap — 2026-08-08

**Status: investigation phase closed.** This document freezes what was established, what is
parked, and what remains. Documentation only — no production, test, kernel, cognition, or SRG
change accompanies it.

**HEAD at time of writing**

```
7a9aa85  test(srg): enforce query trace parity
18c0969  fix(kernel): restore canonical TrioOctagon Z semantics
2a9529c  refactor(cognition): extract persistent kernel readout
```

`main` is **ahead 9** of `origin/main`. The nine local commits should be reviewed as one intended
unit before any push.

**Evidence base.** Every claim below traces to one of:
`Phase1a / Phase1b recovery evidence` · `TORMENT_RECURSIVE_COGNITION_SEMANTIC_AUDIT_v0.1` ·
`SRG_RECONCILIATION_v0.1` · `SRG_COLLISION_PERSISTENCE_RUNTIME_PROOF_v0.1` ·
`SRG_TRACE_PARITY_AND_CRYSTAL_AUDIT_v0.1`.

---

## PERMANENT ARCHITECTURE INVARIANT

> **`model_core.py` owns the authoritative TrioOctagon mathematics.**
> **Persistent cognition belongs outside `model_core`.**
> **Derived TORMENT systems may observe canonical state; they may not redefine it.**

This is the rule whose violation caused the incident. The historical defect was semantic fusion:
persistent chiral memory (`z_mem`) was added directly into canonical scalar `Z`, moving the zero
surface from `z_inst = 0` to `z_inst = −z_mem` and latching the sign once
`|z_mem| > λ·ρ·0.7438`. Restoring the boundary — not tuning a constant — was the repair.

### The canonical/cognitive split, stated precisely

| | symbols | current status |
|---|---|---|
| **Canonical Z-family** | `state.z`, `state.identity_state`, `Z_macro`, `Z_chiral`, `Z_vec` | **checkpoint-only** — one consumer each, the checkpoint serialiser |
| **Canonical dynamics** | `state.Omega`, `state.phi_index`, `state.cycle_stage` | **load-bearing** — these are the inputs to `CognitiveCore.update` (Ω → `J_eff` → `z_mem`; φ, κ → `z_inst`; `cycle_stage` → cognitive identity) and `cycle_stage` also drives `tri_mod` and the compression trigger |
| **TORMENT cognition** | `cog.z_mem`, `cog.z_identity`, `cog.identity_state` | the operational identity stream consumed by `tri_mod`, packets, character, compression |

**Do not describe TrioOctagon as unused.** The Z-family *outputs* are currently unconsumed
downstream; the canonical Ω/φ/cycle state runs the cognition layer. Those are different claims and
conflating them was an error corrected during the audit.

---

## DONE

| # | item | evidence |
|---|---|---|
| D1 | **Canonical TrioOctagon Z restored.** `update_z` returns to `λ·ρ·cos(3(θ−θ_lock))·e^{−γt}`; no `J_eff`, EMA, or cognitive state in `model_core`. | `18c0969`. Oracle parity: 16 seeds × 1200 steps × 11 fields, **exact `==`**, against a vendored copy of the original TrioOctagon model. |
| D2 | **Persistent cognition extracted** to `cognitive_core.py`, owning `z_mem`, `J_eff`, `jeff_norm`, the EMA, `z_identity`, and cognitive `identity_state`. `COGNITIVE_TAU_META = 0.01` is a module constant — not configurable, not checkpointed, not per-agent. | `2a9529c`. Extraction proven a no-op before the mathematics changed. |
| D3 | **`ModelState.z_mem` removed**; `cognitive_core` owns its own undecayed `z_inst` calculation with no import from `model_core`. Boundary enforced by a source-and-AST contract test. | `18c0969` |
| D4 | **Canonical/cognitive routing verified downstream.** No operational path anywhere consumes canonical state believing it is cognitive, or the reverse. Established by exhaustive grep of every `.z` / `.identity_state` attribute read outside `kernel/`, `checkpoint.py`, `cognitive_core.py` — the result set is one line, and it reads `cognitive_state.identity_state`. | Semantic audit v0.1 |
| D5 | **Checkpoint compatibility verified.** v3 format; legacy `z_mem` → `cog.z_mem`, legacy `z` → `cog.z_identity`, legacy `identity_state` → `cog.identity_state`; legacy values are **not** loaded into canonical fields. A legacy-migration test sets legacy `z = canonical + 1.0` and asserts canonical wins. Rollback mirror (`model_state["z_mem"]` sourced from cognitive state) retained. | `18c0969` |
| D6 | **Golden memory-kernel continuity verified.** 1000 observations × four override arms (`{}`, `g_mod`, `theta_lock_mod`, both) through the real `TriOctaMemoryKernel.process()`; full `tri_mod`, `KernelSignals`, and `debug` bit-identical. Cognition recurrence unchanged across the kernel restoration. | `18c0969` |
| D7 | **Latch regression + theta-lock isolation** now guard production, not just the oracle: exactly 600 sign flips/seed, 0/16 latched, plus a spliced-reference negative guard proving the old implementation would fail. Override test asserts Ω exact **and** z diverges. | `18c0969` |
| D8 | **SRG query/trace parity test repaired.** The old file claimed parity while calling `query()` zero times and driving `R_band` with strings where production yields `int`. Rewritten to exercise both surfaces, keep trace-specific unit coverage, use production-real integer bands, and demonstrate that a one-sided `query()` defect is detected. Windows authoritative: **159 passed, 4 subtests passed in 3.26s**. Production untouched. | `7a9aa85` |

---

## CONFIRMED_AND_PARKED

These are established defects or deliberate holds. **None is authorized for repair now.**

### P1 — SRG collision durability defect

- **Layer:** `torment_service/fabric.py` ingest (collision block) ↔ `memory_graph.py` persistence.
- **Evidence — runtime, not source inference.** Real `TormentFabric` collision at cosine 0.8165:
  ```
  ARM A  collision, no later write, restart      -> both participants forget the collision
  ARM B  later write to A only, restart          -> A remembers, B does not
  ARM B' later write to B only, restart          -> B remembers, A does not
  ARM C  control, no collision, same sequence    -> neither changes (isolates the cause)
  ```
  Mechanism: the collision block mutates `ent.payload` for both participants and writes nothing;
  the only ingest `flush_node` runs ~95 lines earlier. Because `flush_node`/`update_payload`
  serialise the **entire** payload, collision state persists *opportunistically* if some unrelated
  later write happens to touch that entity, and is lost otherwise.
- **Why it matters:** persistence integrity. After a restart, two participants in the same
  collision can disagree about whether it happened.
- **Why the blast radius is currently small:** `last_collision_step` has no consumer; the
  `R`-shift is **structurally zero** because `equilibrium_shift` derives from `delta_L`, `L` is
  pinned to `L_0`, and `L` only moves via `evolve_breathing` — which never runs (P2). The one
  remaining behaviourally-consumed mutation is `heartbeat_class` adoption, not observed in 12
  attempted pairs.
- **Closure would be:** a decision on durability semantics, and — if durability is chosen — a
  persistence design that does not misrepresent itself. **There is no atomic two-entity
  persistence primitive**; two sequential appends must not be presented as a complete solution.
- **Authorized now?** **No.**
- **Must not be bundled with:** anything. It is a prerequisite for P2, not a companion to it.

### P2 — SRG query breathing / writeback: explicit HOLD

- **Layer:** `fabric.py` query rescoring.
- **Evidence:** the writeback gate reads the *nested* `hit["payload"]["srg"]`, which flattened
  `MemoryGraph.search` hits never have. Scoring uses the flattened form and **is** active. The
  source states the asymmetry itself: *"writeback remains HOLD"*, and the shared source selector's
  docstring says it is *"NOT a gate for SRG breathing/writeback."*
- **Why it matters:** `L(t)` never oscillates and `R` never converges — the breathing dynamic does
  not run. This is authorized current state, not a latent bug.
- **Closure would be:** an explicit product decision to activate, taken **with** P1.
- **Authorized now?** **No — do not activate during recovery work.**
- **Dependency:** activating breathing makes `delta_L` non-zero, which converts P1 from an
  integrity defect into a behavioural one.

### P3 — Seed/identity → SRG crystal bridge: designed, never implemented

- **Layer:** `character.plant_seed` ↔ `srg_engine.build_memory_srg`.
- **Evidence:** `build_memory_srg`, `is_seed`, `create_crystal_state`, `CRYSTAL_ATTUNEMENT.md`, the
  tests, **and the `fabric.py` call site** all landed in one commit (`8d1d123d`, 2026-03-16), with
  `is_seed=False` present from that first line. `git log -p -S"is_seed="` on `fabric.py` yields a
  single `+` line and no `-` line: **it has never been anything else.** The same commit added
  `character.derive_srg_character_bands`, whose docstring names it the fabric↔SRG integration
  point — **zero callers**.
- **The decisive structural fact:** all four seed/identity creation paths (`plant_seed`,
  `gravity_correction`, `_maybe_emit_identity_anchor`, `promote_chunk`) call
  `spawn_memory`/`add_memory` **directly and bypass `fabric.ingest`**, which is the only function
  that builds `_srg_dict` and writes `payload["srg"]`. Changing `is_seed=False` would therefore
  produce **zero** crystals. Generic `fabric.ingest(... is_seed=False)` is **not** the bug.
- **Why the exposure is near zero:** SRG is default-off; seed rows are already protected by
  `canon=True` + `tier="core_identity"` via compression and lifecycle. Only the *SRG route* to that
  protection is missing.
- **Closure would be:** correcting `CRYSTAL_ATTUNEMENT.md`, which currently states as runtime fact
  that seed/identity memories become crystals.
- **Authorized now?** Documentation correction — yes, when convenient. Implementation — **no**.
- **Terminology warning that must survive:** ~22 distinct "seed" meanings exist, including two
  exact collisions — `is_seed` (SRG crystal switch vs. `retrieval_assembler` prompt-block marker)
  and `seed_eids` (planted memory ids vs. `recursion_guard` DFS roots). Any future work here must
  state which "seed" it means.

---

## NEXT_RECOVERY

The remaining recovery questions, in order. **Audit semantics before modifying anything.**

### N1 — Character / collective / compression semantic audit

- **Why it matters:** this is the first layer that *actually consumes* cognitive identity,
  relational state, SRG metadata, and persistent memory state. Everything upstream of it is now
  verified; everything downstream of it is unexamined.
- **Layer:** `character.py`, `collective_field.py`, `collective_models.py`, `compression.py`,
  `lifecycle.py`, and the `fabric.py` packet-emission path.
- **Trace:** `cog.identity_state → tri_mod → Fabric / ResonancePacket → collective field /
  character → compression / lifecycle → persistence`.
- **Known evidence to start from:**
  - `tri_mod` is a **flat namespace mixing ownership**: `cycle_stage` is canonical (κ-driven),
    `identity_state` is cognitive. Both correct; both emitted under bare keys.
  - `ResonancePacket.cycle_stage` / `.identity_state` carry **stringified floats** (`"3.0"`,
    `"5.0"`) where the schema documents `S0..S6` / `s0..s8`. Nothing parses them numerically and
    comparison is string `==`, so `collective_field`'s `+0.4` alignment behaves correctly — the
    documented contract is violated, the behaviour is not.
  - `compression.py` and `spirit_return.py` read `payload["srg"]` **ungated by the SRG flag**. The
    documented contract (`CRYSTAL_ATTUNEMENT.md`) is generation-only — *"nothing in srg_engine.py
    is ever imported"* — and the code honours it. Whether *consumption* of already-persisted SRG
    metadata should also stop is **unspecified by any source or doc**. Do not call this a defect
    without establishing intent.
- **Closure:** every crossing in the trace classified as correct / stale / unspecified, with the
  same "would this test still pass if the thing it guards were broken?" test applied to each
  guarding test.
- **Authorized now?** Audit — yes. Modification — no, pending findings.
- **Must not be bundled with:** SRG implementation work (P1/P2/P3).

### N2 — Durable-memory / lifecycle feedback and ordering audit

- **Why it matters:** repeated processing that silently compounds state is the failure mode least
  visible in a green suite.
- **Layer:** retrieval → character/collective modulation → ranking → persistence → later retrieval.
- **Known evidence to start from:**
  - **Spirit-return warmth** is the least-bounded loop found: `WarmupTracker.get_or_create`
    increments on retrieval **before any relevance decision**, warmth raises rank, higher rank
    raises retrieval probability. Bounded by `WARMTH_CAP` and a 400-step window.
  - **Collective echo re-ingest** is live but externally triggered only; it mutates
    `_srg_last_ingest_band_by_agent`, so a re-ingested echo shifts later *organic* query scoring
    for that agent.
  - **Archivist writeback** is flag-off by default and guarded four ways, but
    `_write_back_approved` has **zero integration test coverage**, and
    `agent_loop.py`'s self-ingest stores agent-authored text as `source_type=user_input`, which is
    in the guard's safe-ancestor set.
  - **Genuine test-order hazards** already identified: two `os.environ.pop` teardowns without
    restore; one `setenv` without restore; `app.py` module-level fabric binding `DATA_DIR` and
    three feature flags at first import.
- **Closure:** every feedback loop documented as `input → transformation → output → next consumer →
  feedback edge → bound`, and every ordering dependency classified as legitimate lifecycle
  sequencing vs. accidental pytest-order coupling.
- **Authorized now?** Audit — yes.
- **Must not be bundled with:** N3. Ordering and compression are separable.

### N3 — Compression semantics

- **Why it matters:** compression is destructive and permanent. A misread protection flag loses
  memory irreversibly.
- **Layer:** `compression.py`, `lifecycle.py`, and their interaction with `canon` /
  `tier="core_identity"` / SRG metadata.
- **Known evidence to start from:** compression consumes `tri_mod["cycle_stage"]` (canonical) for
  its trigger and stores `tri_mod["identity_state"]` (cognitive) as `prev_identity_state`. It reads
  `payload["srg"]` ungated. Protection of seed rows currently flows from `canon=True` +
  `tier="core_identity"`, **not** from `srg.is_crystal` (which is never `True` — see P3).
  `LifecycleSetVia.SEED_PLANT` matches `kind`/`type ∈ {seed, identity, core_identity}`, but
  `plant_seed` writes `type="seed_canon"` — so that marker currently fires on **zero** production
  rows, and the source already flags the naming as a denormalization.
- **Closure:** confirmation that every protection path a real memory can take is exercised by a
  test that would fail if the protection were removed, and that persisted metadata surviving a
  feature-flag change is intended behaviour.
- **Authorized now?** Audit — yes.

---

## LATER_ENGINEERING

### L1 — Seed/identity provenance

- **Layer:** `character.plant_seed`, `gravity_correction`, `_maybe_emit_identity_anchor`,
  `promotion.promote_chunk`.
- **Evidence:** none of the four constructs a `ProvenanceV1` envelope. The most identity-critical
  rows in the system carry no `source_type`, while ordinary episodes get
  `source_type=user_input` plus a character badge.
- **Why it matters:** provenance is what the recursion guard walks. Rows with no envelope are an
  unknown quantity to it.
- **Closure:** establish first whether the absence is **intentional for internally authored
  identity state** or genuinely missing. That determination alone is the deliverable.
- **Authorized now?** **No.** Do not open during kernel recovery, and do not let it become a large
  provenance redesign.

### L2 — Checkpoint default-`ModelParams` assumption

- **Layer:** `checkpoint.deserialize_model_state`.
- **Evidence:** restore now recomputes `z`, `Z_*`, `cycle_stage`, `identity_state` by running
  `TriOctaPhaseLockModel(ModelParams())` — with **default** params. Correct today, because
  `TriOctaMemoryKernel` is always constructed as `params or ModelParams()` and no caller passes
  params. Separately, a v3 `model_state` legitimately holds canonical `z` beside cognitive `z_mem`
  (the rollback mirror), so the on-disk record is ambiguous even though the code is not.
- **Why it matters:** the assumption is silent and would break the moment per-agent kernel
  parameters exist.
- **Closure:** a formal semantic entry recording the assumption, before custom per-agent params are
  introduced. No code change implied today.
- **Authorized now?** Documentation — yes. Code — not needed.

### L3 — One canonical test command

- **Layer:** test infrastructure.
- **Evidence:** there is **no** `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`, or root
  `conftest.py`. Collection scope is set entirely by the command line, and the tree contains
  `research/`, `sim/`, `examples/`, harness dirs, and leftover `.pytest_tmp_*` directories. This
  is the concrete reason earlier "full suite" counts differed (29 failed / 7074 passed vs.
  26 failed / 7136 passed) — different invocations, not a regression.
- **Why it matters:** without it, no two full-suite comparisons are guaranteed to measure the same
  population, and a regression can hide inside a collection-scope change.
- **Closure:** one authoritative Windows command (or a `testpaths` config), recorded, plus the
  practice of comparing **node lists** rather than totals.
- **Authorized now?** Yes, as **test infrastructure work only** — must not be mixed into
  behavioural recovery.

### L4 — TORMENT semantic field manual

- **Why it matters:** this is the prevention mechanism that directly addresses the incident. The
  original defect was a *meaning* collision, not a coding error, and it survived because no
  artifact recorded what `state.z` was allowed to mean.
- **Format — for each entry:** `symbol · owner · layer · actual meaning · formula/source ·
  persistent? · consumers · allowed inputs · MUST NOT MEAN · modification authority`.
- **Minimum set:**
  ```
  KERNEL.Z.CANONICAL          COGNITION.Z_MEMORY        COGNITION.Z_IDENTITY
  KERNEL.IDENTITY_STATE       COGNITION.IDENTITY_STATE  TRI_MOD.IDENTITY_STATE
  SRG.R_BAND                  SRG.CRYSTAL
  ```
  `SRG.R_BAND` must record `int [0,4]` — the false-green parity test drove it with strings for
  months. `SRG.CRYSTAL` must record "never `True` in production today".
- **Permanent rule to state in it:** derived systems may observe canonical TrioOctagon state; they
  may not redefine it.
- **Closure:** the eight entries exist and the canonical/cognitive distinction of this document is
  captured in them.
- **Authorized now?** Yes — documentation only.

---

## DEFERRED_PRODUCT_WORK

**These three must be considered together, as one decision.** They are coupled: activating
breathing (Q2) makes collision `delta_L` non-zero, which converts the durability defect (Q1) from
an integrity issue into a behavioural one; and the crystal bridge (Q3) changes which memories exist
and how they score. Taking any one alone is what created the current half-wired state.

| | item | current state |
|---|---|---|
| Q1 | SRG collision durability implementation decision | defect confirmed at runtime; no atomic two-entity primitive exists |
| Q2 | SRG breathing activation | explicit documented HOLD |
| Q3 | SRG crystal wiring | designed in pieces; the seed-memory → SRG bridge was never implemented |

**Not authorized during recovery.** When they are taken up, they belong to whoever owns the SRG
product decision — not to a recovery phase.

---

## DO_NOT_REOPEN during this recovery

- Brainvision
- SRG breathing
- Crystal implementation
- Dream functionality *(confirmed: no executable dream code exists — the production token count is one docstring line, and the absence is deliberate and documented as `Verdict: NO-OPEN`)*
- Large provenance redesign
- Kernel mathematics
- Generic architecture cleanup
- "While we are here" fixes

---

## Repository housekeeping

- Local `main` is **ahead 9** of `origin/main`.
- The nine-commit sequence should be reviewed **as one intended unit** before any push.
- Do not push piecemeal; the kernel restoration, the cognition extraction, and the parity-test
  repair are one narrative and should land together.
