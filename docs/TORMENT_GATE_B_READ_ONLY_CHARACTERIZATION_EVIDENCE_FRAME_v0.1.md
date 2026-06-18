# TORMENT Gate B — Read-Only Characterization Evidence Frame v0.1

**DOCS-ONLY AUTHORIZATION FRAME — AUTHORIZES ONLY A LATER READ-ONLY EVIDENCE PASS.
NO CODE, NO TESTS, NO INSTRUMENTATION, NO BEHAVIOR CHANGE, NO FIX, NO TARGET SELECTION.**

This artifact authorizes a single, later, read-only characterization evidence pass and bounds it in
advance. It runs no evidence itself. The evidence pass it frames may inspect existing facts so that a
future Gate B target-selection decision is not made from stale or assumed information; it may not change
anything it inspects, and it may not generate new behavior to inspect.

**Date:** 2026-06-17. **Baseline HEAD = origin/main = `ee97492`** (latest commit
*docs(engine): point orientation map to Gate B decision frame*).

> Memory may guide context. Memory may not seize authority.

---

## 1. Purpose

Gate B target-selection must not proceed from stale or assumed facts. The decision frame
(`docs/TORMENT_GATE_B_WRITER_AUTHORITY_DECISION_FRAME_v0.1.md`) established the write-side authority
boundary, the requirement-level "governed writer" vocabulary, and a non-binding consideration grouping;
it deliberately selected no target. Before any selection is even considered, three facts should be
checked against current reality rather than assumed: whether H1 is merely reachable or actually
previously observed, whether H5's binding is live or still unverified, and whether the Gate B
documentation anchors have drifted. This frame authorizes a bounded pass to gather exactly those facts —
and nothing more.

## 2. Scope — what the later read-only evidence pass MAY inspect

Using only existing source, existing configuration, and **already-existing artifacts created
independently before this slice** (see §3 method constraints), the later pass MAY characterize:

- whether H1 (`character.gravity_correction` / automatic `canon=True`) appears **reachable** or
  **previously observed**;
- whether H1 **fired in already-existing, independently-created recorded behavior** (e.g.
  `drift_correction` / `core_identity` rows already present in already-existing, operator-identified
  artifacts or workspaces produced independently before this slice);
- **approximate previously-observed frequency**, only if derivable from those already-existing
  artifacts without adding instrumentation;
- **what kind of content** H1 emitted, if observable in those already-existing records;
- whether H5's `FabricHandle → character.gravity_correction` binding is **live or still unverified**;
- whether existing Gate B documentation **anchors appear stale** (e.g. cited symbols / line numbers no
  longer match current source).

Any fact in this list that cannot be obtained read-only (without execution or instrumentation) is to be
recorded as **"not determinable read-only — deferred"**, never pursued by adding capability or by
generating new behavior.

## 3. Method constraints for the later pass (read-only means read-only)

- The pass inspects: current **source**, current **configuration**, and **already-existing artifacts
  created independently before this slice** — operator-identified records / telemetry / on-disk data
  produced by prior, separately-authorized activity, not produced for or during this slice.
- The pass **does not generate the behavior it inspects.** It is explicitly forbidden to:
  - **start the service**;
  - **execute the loop** (`AgentRunner.run_turn` or any turn loop);
  - **call any endpoint**;
  - **call `ingest`** (or any store path);
  - **execute any writer path** (`gravity_correction`, `promote_chunk`, `_maybe_emit_identity_anchor`,
    `_maybe_emit_mood_drift`, or any other writer);
  - **add instrumentation** (logging, counters, hooks, tracing);
  - **force, craft, tweak, or replay any scenario** intended to make H1 (or any hazard) fire.
- The pass adds no tests, no CI locks, and changes no configuration or thresholds.
- It writes only its own docs-only evidence record (§6). It modifies no source, no config, no data, and
  no existing doc.

Rationale: executing H1's path would itself cause a `canon=True` write — the exact hazard under study.
Read-only therefore means inspection of artifacts that already exist, never production of new ones.

## 4. Explicit non-authorizations

This frame, and the pass it authorizes, do **not** authorize:

- target selection;
- hazard ranking;
- remediation criteria;
- writer fixes;
- production behavior changes;
- tests or CI locks;
- new instrumentation;
- logging changes;
- threshold / config changes;
- scenario manipulation designed to force H1 to fire;
- governance-vehicle selection;
- registry amendment;
- P4 / source-sameness mechanics;
- Seed-Gov implementation;
- Document B runtime;
- dream / incubation runtime;
- candidate store;
- durable private state;
- database / substrate;
- schema / storage / carriers / migration;
- `canon_source`;
- hidden finalizers;
- output blockers;
- identity pinning;
- monitoring / autonomy;
- durable user-risk scoring.

## 5. Required wording

**Slice-level.** This slice is read-only characterization evidence only. It may inspect existing source,
existing configuration, and already-existing artifacts created independently before this slice to record
whether named hazards appear reachable or previously observed. It does not execute writer paths, select
a Gate B target, rank hazards, define remediation criteria, add tests, create locks, change thresholds,
add instrumentation, patch writers, or choose a governance vehicle.

**H1.** Observation of H1 firing, non-firing, frequency, or emitted content is evidence for later
decision-making only. It is not a finding of correctness, incorrectness, priority, target selection, or
authorization to fix.

**H5.** H5 review may verify whether a live binding already exists. It may not create, complete, repair,
or recommend the binding.

**Stale anchors.** Anchor freshness may be reported as documentation drift evidence only. Updating
anchors is a separate docs authorization.

## 6. Deliverable of the later pass (when separately authorized)

A single docs-only evidence record (e.g. `docs/TORMENT_GATE_B_..._EVIDENCE_v0.1.md`) that states, for
each inspected item, the observation and how it was obtained, marks anything not determinable read-only
as **"not determinable read-only — deferred"**, and records every observation as **evidence for later
decision-making only** — not a finding of correctness, not incorrectness, not priority, not target
selection, and not authorization to fix. The evidence record selects no target and recommends no fix.

## 7. Sequence (no auto-chain)

1. This frame is written (docs-only).
2. Codex reviews it for scope creep.
3. Operator approves.
4. Only then is the bounded read-only evidence pass performed under §2–§3.
5. The evidence is recorded (§6).
6. Only after that does Gate B revisit target-selection — itself a separate, explicitly-authorized step.

No step opens the next automatically.

---

## Anti-drift footer

DOCS-ONLY AUTHORIZATION FRAME — authorizes only a later read-only evidence pass; runs no evidence here.
Read-only means: inspect existing source / configuration / already-existing artifacts created
independently before this slice; start no service; execute no loop, endpoint, ingest, or writer path;
add no instrumentation; force no scenario. The pass selects no target, ranks no hazard, defines no
remediation, patches no writer, chooses no governance vehicle, and amends no registry. It opens no
writer fixes, tests or CI locks, behavior changes, P4 / source-sameness, Seed-Gov, Document B,
dream/incubation, candidate-store, durable-private-state, or database / substrate / schema / storage /
carriers / migration / `canon_source` work; it introduces no hidden finalizer, output blocker, identity
pin, monitoring, autonomy, or durable user-risk scoring. Facts gathered are evidence for a later
decision, never permission to fix. Guide, not control; audit observes authority and does not become
authority. Memory may guide context. Memory may not seize authority. Each subsequent step is a separate
authorization.
