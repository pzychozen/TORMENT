# Checkpoint — Authored Seed-Content Stability Lock

**CODE-SLICE CHECKPOINT — docs-only record of a landed tests-only protection slice. No new
gate, no behavior change, no registry amendment.**

**Anchor:** `4742b87` *test(seed): lock authored seed-content stability*. **Date:** 2026-06-19.

> Memory may shape context. Memory may not seize authority.

---

## 1. Status and anti-drift banner

This is a **tests-only characterization / protection lock** over authored character-seed content.
It is **not** a behavior change, **not** a Seed-Governance mechanism, **not** a seed-revision API,
**not** governed admission, **not** Writer Authority, **not** private cognition / dream runtime, and
**not** database/substrate. It records the **current** runtime behavior — that ordinary agent
creation/planting and ordinary ingest do not rewrite authored seed content — so a future agent cannot
silently introduce a seed-overwrite regression without a test failing loudly.

## 2. What landed (and what did not)

A new focused test file pins the **current** stability of authored seed content through the real
plant/save path, exercised via `TormentFabric.create_agent` against an isolated temp data dir.

**No production code changed. No Seed-Gov mechanics, seed-revision path, or governed-admission handler
introduced. No behavior changed.**

- **Test file:** `tests/test_seed_text_write_once.py` (two tests).
- **Source surfaces characterized (unchanged, only locked):**
  - `torment_service/character.py` — `CharacterSeed`, `CharacterStore.save_seed`,
    `CharacterStore.load_seed`.
  - `torment_service/fabric.py` — `TormentFabric.create_agent` and its character plant/save path
    (the single `save_seed` call-site, gated by `char_seed is None` then `if not
    char_seed.seed_motif_id:` — plant-once).

## 3. What is locked

- Authored **`seed_text`** remains stable across create/plant **and** one ordinary ingest.
- Authored **`seed_id`** remains stable.
- **`character_name`** remains stable as the authored display label — recorded as such, **without**
  elevating it to seed-revision doctrine.
- A repeat **`create_agent`** for the same workspace/agent with a **different** seed payload does
  **not** overwrite the persisted authored seed content. This is locked as **current idempotent-create
  characterization** — `create_agent` skips identity creation when the agent already exists, so the
  second payload is ignored. It is explicitly **not** described as a seed-revision or overwrite API,
  and the different payload persists **no** new seed.

## 4. Positive control (locks authored content, not object identity)

Derived basin fields such as **`seed_motif_id`** and **`seed_eids`** **may populate** after planting,
and the test asserts they do. This proves the lock is on **authored content**, not on whole-object
immutability. The test makes **no** "seed never changes" claim — `plant_seed` legitimately populates
derived basin fields (and `created_ts`), and that is allowed.

## 5. Explicit non-authorizations

No production code changed. No Seed-Gov mechanics. No seed-revision API. No governed-admission
implementation. No seed rewrite. No canon/admission/promotion change. No identity-anchor behavior
change. No Writer Authority continuation. No P4 / source-sameness mechanics. No database/substrate
mechanics. No private cognition / dream / incubation runtime. No hidden chain-of-thought storage or
exposure. No output blocker / hidden finalizer / autonomy / monitoring / coercive mechanism.

## 6. Why it mattered

The A/B/Seed-Gov reconciliation
(`docs/TORMENT_A_B_SEED_GOV_IDENTITY_SEED_CANON_CANDIDATE_CROSSING_RECONCILIATION_FRAME_v0.1.md`) and
Seed-Governance §7 hold that **actual authored seed revision is separate from ordinary admission and is
never automatic**. In the current runtime, authored-seed stability existed only by the **absence of a
revision writer** — `seed_text` is never reassigned by any ingest/query/drift path, and the plant-once
gate prevents re-save — but that was protected by **nothing executable**. This lock turns the
write-once-by-absence convention into an executable regression boundary: a silent authored-seed
overwrite would now fail loudly, **without building the seed-revision boundary** the heavy gate still
owns.

## 7. Audit-wiring isolation note (transient, did not reproduce)

A single prior full-suite run showed one audit-wiring A/B failure
(`tests/test_assembly_audit_wiring.py::TestWiring_ResultsByteIdentityABTest::test_common_keys_byte_identical_with_vs_without_audit`,
`blocks` divergence, with captured SQLite cross-thread write warnings). Isolation proved it was **not**
caused by the seed tests: the audit-wiring test passed alone; `seed → audit-wiring` passed;
`audit-wiring → seed` passed; and two subsequent full suites passed. Collection is alphabetical (no
conftest / `addopts` / randomizer under `torment_fabric/`), so the audit-wiring test runs **before**
`test_seed_text_write_once.py` and the seed tests had not executed when it ran. The seed file touches no
app globals, no `os.environ` / `TORMENT_DATA_DIR`, no module-level `fabric`/`app`, and no shared kernel
(`TriOctaMemoryKernel` is constructed per `TormentFabric` instance). The transient failure is recorded
here as a **separate, parked** order/timing/shared-state observation (suspected retrieval-side warmup
persistence and/or async SQLite write timing between the two `/retrieve` calls) — **not** a seed-slice
concern and **not** addressed by this checkpoint.

## 8. Lane posture

This likely **exhausts the final clean tests-only slice** adjacent to Seed / Private-Cognition
governance. The remaining items are **heavy-gate decisions**, not small slices: the candidate crossing
mechanism, the seed-revision boundary construction, chamber representation, and the runtime-conformance
gap. The lane should **pause** here pending a deliberate operator-selected heavy gate; do not manufacture
another protection lock. Database/substrate remains last.

---

*Code-slice checkpoint only. Tests-only protection, not behavior change. No production code changed; no
Seed-Gov mechanics, seed-revision path, or governed admission introduced. Authored-seed stability is now
test-locked without building the seed-revision boundary. Audit observes authority and does not become
authority. Memory may shape context. Memory may not seize authority. Database / substrate remains last.*
