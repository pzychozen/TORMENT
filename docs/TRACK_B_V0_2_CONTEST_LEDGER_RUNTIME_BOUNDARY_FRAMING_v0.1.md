# Track B v0.2 — Contest-Ledger Runtime Boundary Framing v0.1

**Status:** Ratified framing artifact. **Not doctrine.** Not an implementation authorization. Not a schema authorization. Not an automation authorization.
**Date:** 2026-06-03
**Author:** Claude (drafter), for the trio (Hilmir / pzychozen as operator + GPT + Codex review). Hilmir and pzychozen are the same operator.
**Ratified by:** Hilmir (operator), 2026-06-03, after GPT review → Codex adversarial review → Codex verification pass (PASS with minor wording edits).
**Mode:** Framing-only design boundary. No code, no schema, no tests, no migrations, no automation, no remediation, no implementation authorization. Implementation requires a separate authorization before any code-bearing slice.
**Audit baseline:** `HEAD = 6ff362f`. Produced from the Track B v0.2-A boundary audit and the Cluster 5 Q2 lifecycle-durability dependency micro-audit (dependency verdict: **Option 1**).
**Anchor docs:** Track A v0.1 (`docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`), Cluster 2 v0.1 (`docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md`), Track B v0.1 (`docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md`), Cluster 5 Storage-Survivability v0.1, Cluster 5 Path C Governance-Preservation Framing v0.1, Cluster 5 Path C Q2 Lifecycle Implementation Framing v0.1, Ledger Observational-Boundary Doctrine v0.1, MCP Capability Boundary.
**Lineage:** Promoted from local-only scratch draft `scratch/TRACK_B_V0_2_CONTEST_LEDGER_FRAMING_DRAFT_2026_06_03.md` (preserved for lineage). This artifact frames a *future* implementation boundary. It does not build, schedule, or schema-finalize anything.

---

## 0. Status and scope discipline

This document is a **framing artifact**, not a design finalization and not an implementation plan with authorization. It converts two completed read-only audits into a single bounded statement of *what a future Track B v0.2 contest-ledger implementation would have to decide* — and, just as importantly, *what it must not decide here*.

What this artifact does:

- Names the narrowest future contest-ledger boundary consistent with the ratified spine.
- Inherits Track B v0.1 invariants unchanged.
- Records the current substrate (empty seam + reusable precedents) at `HEAD = 6ff362f`.
- Records the open technical decisions, explicitly **parked** for later review (§13).

What this artifact does **not** do (held closed throughout — see §14):

- No code. No schema field-signature finalization. No writer/reader. No audit endpoint.
- No retrieval-scoring or prompt-assembly integration. No automatic firing. No cognition-dissent coupling. No LLM consultation. No MCP exposure change. No autonomy.

Operational discipline (carried from the spine): **Windows is the source of truth.** This artifact is now tracked framing authority; it is **not** doctrine and **not** implementation authorization. A *separate* operator authorization is required before any code-bearing slice (B2-S2 onward in §12).

---

## 1. Center question

Inherited verbatim from Track B v0.1 §1:

> **How can TORMENT remember that something happened while allowing an agent or character to contest how much authority that memory gets?**

Both clauses remain load-bearing. *"Remember that something happened"* — the event and its provenance are preserved unconditionally. *"Contest how much authority"* — the routing of the memory's **Authority class** (Cluster 2 v0.1 §7.1) is the only locus of contest. Authority can be lowered or held; provenance can never be erased.

**Operator-intent clarification — memo, not control.** A `ContestRecord` is a sidecar memo about a memory's authority posture, not a command that dictates character voice, response, or identity. Any future model-visible surfacing, if separately ratified and governance-gated, must preserve character freedom: a character may engage with the memo, speak on it, resist it, reinterpret it through persona, or leave it untouched. This framing does not authorize prompt surfacing or behavioral control. (Prompt influence remains closed — §9.3; retrieval-ranking influence remains closed — §9.2; the effective-authority resolver remains unresolved — §8.0; implementation remains closed — §14.)

Track B v0.2's job is **not** to re-answer this question — v0.1 answered it doctrinally — but to frame the narrowest runtime seam that would *honor* the answer without quietly importing anything the spine has not ratified.

---

## 2. Ratified anchors inherited unchanged from Track B v0.1

The following are inherited as fixed and are **not reopened** by this artifact. They are restated as binding invariants for the future implementation:

1. Preserve the original memory event and its provenance. *(Track B v0.1 Inv 1; Track A §9.6.)*
2. Contest routes authority **downward or holds it**. Contest never increases authority. *(Inv 10; Cluster 2 §11.3.)*
3. Contest never silently rewrites the contested memory — no field of payload, provenance, or governance is mutated by the contest. *(Inv 3.)*
4. `ContestRecord` is a first-class item **separate from the memory graph** (Option C, separate ledger). *(Inv 2; §5.1.)*
5. `ContestRecord` is **immutable**. Reversal is a counter-contest, never an edit. *(Inv; §3.2, Q5.)*
6. Contest **increases** audit visibility. It never becomes a hiding mechanism. *(Inv 14.)*
7. Audit visibility does **not** become retrieval influence. *(Ledger Observational-Boundary Doctrine §3.)*
8. Audit visibility does **not** become prompt influence. *(Ledger Observational-Boundary Doctrine §3.)*
9. Cognition dissent may **inform** a contest; it never automatically fires one. *(Inv 15.)*
10. Agent and character contests **cannot** hard-refuse persistence. *(Inv 16.)*
11. `refuse / no-persist` is **operator-authorized only** (actor identity alone is not authorization — §8.5). *(Inv 16; §7.2.)*
12. A refused candidate remains **durably audit-visible** even when no ordinary memory node spawns. *(Inv 12.)*
13. Separate-ledger boundary — **two distinct claims, not to be compressed into one:**
    - **A. No ProvenanceV1 redesign is authorized.** No `ProvenanceV1` field change and no `source_type` change is authorized here. The contest carries its own provenance; it does not alter the schema.
    - **B. No Track A truthfulness-envelope amendment is authorized.** The Mode / Voice / Certainty / Authority axis framing remains unchanged. *(Track A v0.1; Track B §5.1 Option C.)*
14. **Framing ≠ implementation authorization.** *(Track B v0.1 §13.)*

Anchor documents inherited unchanged: Track A v0.1, Cluster 2 v0.1, Track B v0.1, Cluster 5 Storage-Survivability v0.1, Cluster 5 Path C Governance-Preservation Framing v0.1, Cluster 5 Path C Q2 Lifecycle Implementation Framing v0.1 (plus its now-landed implementation, §3.5), Ledger Observational-Boundary Doctrine v0.1, MCP Capability Boundary.

---

## 3. Existing substrate at current HEAD

### 3.1 Empty Track B runtime seam

Verified at `HEAD = 6ff362f`: **no `ContestRecord` / contest-ledger implementation exists anywhere.** `git grep -niE "contestrecord|contest_ledger|contest_record|contest_scope|reason_class" -- torment_service cognition schemas` → 0 hits. `git log --all -S "ContestRecord"` → doctrinal commits only. No `torment_service/contest_ledger.py` / `contest_memory.py` on any branch (`main`, `origin/path3-character-provenance-badge`, `origin/tier0-agent-runtime-telemetry`). The runtime gap named by v0.1 — *a pre-grant, agent-side authority-contest seam at write time* — is genuinely empty. We are not rediscovering existing work.

### 3.2 Existing disagreement-adjacent primitives

Six adjacent primitives exist; each is either a reusable *precedent* or a *must-remain-separate* concern (Track B v0.1 §0; verified):

- **Cognition dissent** — `cognition/task_models.py:152` (`ReintegrationResult`), `:161` (`dissent` field), `:172` (`has_dissent`); `cognition/reintegration.py:149` (`_detect_dissent`). **Must remain separate**; may *inform* via `linked_dissent_topic` only (Inv 15).
- **MemoryProposal approve/reject** — `schemas/memory_proposal.py:29–69` (`decision`, `rejection_reason`, `approve()`, `reject(reason)`). **Reusable precedent** for the required-reason pattern.
- **ConflictRegistry** — `torment_service/conflicts.py:14` (`CanonConflict`), `:49–50` (two files `conflicts.jsonl` + `conflict_events.jsonl`), `:59` (`add`), `:76` (`decide`). **Strongest structural precedent** (record + events, immutable record, eid linkage).
- **Migration `admission_refused`** — `torment_service/migration/gate2_admission.py:30–35` (`ADMISSION_REASON_*` stable strings). **Reusable precedent** for controlled-vocabulary refusal that preserves the candidate; **do not redesign** (Track B v0.1 §9).
- **contradiction_risk / contested retrieval** — `torment_service/fabric.py:3987` (`wants_contested`), `:4149`, `:6497`. **Reusable read-side hook** for Inv 14 visibility; observational only.
- **Governance filtering** — `torment_service/governance.py:55` (`resolve_governance`), `:318` (`filter_llm_facing`), `:552` (`GovernanceAuditLog`). **Authority surface** and candidate observation surface; not a contest object.

### 3.3 Existing append-ledger precedents

The contest ledger has well-worn precedents in the codebase (verified, *current code behavior*):

- **`closure_ledger.py`** — append-only JSONL at `<data_dir>/workspaces/<ws>/closure_memory/closure_events.jsonl`; **no in-memory cache** (every read walks the file); state by **literal last-event lookup, no fuzzy inference**; `build_*_event` factories; `ProvenanceV1` per event. Header enumerates the sibling ledger family: `baton_events.jsonl`, `reference_load_events.jsonl`, `environment_memory/events.jsonl`. A `contest_events.jsonl` would be a fifth member of an established pattern.
- **`closure_memory.py`** — `ClosureEntry` (`:77`) with `deferred_or_open_items` **REQUIRED, no default** (`:100`, anti-false-finality) and `version_history` that grows, never replaces (`:102`, R+8 immutability). Governance-carrying, version-immutable record.
- **`conflicts.py`** — the **record + events** two-file split with event-replay to derive status. Closest shape match for "immutable record + reader-derived counter-contests."

### 3.4 Existing authority-routing precedents / substrate vocabulary

The Authority-class values Track B routes to have **existing governance-flag precedents** that already express comparable routing for non-contest reasons (Cluster 2 §7.1 substrate mapping, verified in `governance.py`). These are **precedent vocabulary**, **not** an authorized contest-application path — see the effective-authority resolution boundary (§8.0):

- `low-authority` / `released` → precedent flags: `decay_accelerated`, reduced strength, retrieval discount, no-canon (Cluster 2 §7.1 lines 305–306).
- `audit-only` → precedent: `non_shareable` + FILTER-A `SURFACE_LLM_CONTEXT` exclusion (`governance.py:103`; Cluster 2 §7.1 line 308).
- `refuse / no-persist` → `admission_refused` exists **but is migration-only, not live-write** (Cluster 2 §7.1 line 307; line 473). This is the one routing value lacking even a precedent live-write substrate (§8.4, §11.3).

This is *why* the Q2 dependency verdict was Option 1: the contest's routing axis has durable **precedent** substrate independent of the lifecycle envelope. **It does NOT mean a contest may apply its result by mutating these flags on the original row** — that would violate inherited Invariant 3. How effective authority is resolved from `row + contest ledger` without mutating the row is the unresolved boundary held open in §8.0.

### 3.5 Existing lifecycle substrate

The Q2 lifecycle work has **substantially landed since the 2026-05-22 framing snapshot** (caught by the seven-layer survey; verified at current HEAD):

- `torment_service/lifecycle.py` exists. `LifecycleState(str, Enum)` (`:90`): `UNSET, SCRATCH, RELEASED, PROTECTED, REVIEW_PENDING, ACTIVE, CONSUMED, ARCHIVED`.
- Envelope stamped at the spawn write-site (`memory_graph.py:_ensure_lifecycle_envelope` ~`:105`, Q2-H1c); commit arc `fecff87` (Slice 0) → `659e2f2` (tool-result doctrine).
- Q2-F enforcement primitive landed (`0e07b9c`); Q2-D protected dual-source collapse Slices 1–5 (`b3d0e77`→`6e8d537`).
- **Caveat for accuracy:** production currently *writes* only `UNSET` (default) and `PROTECTED` (dual-source collapse). `RELEASED`/`SCRATCH`/`ACTIVE`/`CONSUMED`/`REVIEW_PENDING`/`ARCHIVED` are **vocabulary-durable but not yet write-wired** (`memory_graph.py:79–87`; `lifecycle.py:618–621`).

This substrate is **adjacent context**, not a Track B dependency — see §4.

---

## 4. Axis disambiguation

This section is load-bearing. The entire dependency question turned on it.

### 4.1 Authority-class `released`

`contest_result="released"` is a **Cluster 2 §7.1 Authority-class** value. Cluster 2 §7.1 (line 220) treats `released` as a **synonym of `low-authority`** with identity-protection emphasis: *content + provenance retained, no identity-shaping weight.* It is a **demotion of influence**. Its existing **authority-class precedent surface** is the governance-flag composite `low-authority + no-canon` (§3.4) — precedent vocabulary only, **not** an authorized contest-application path (§8.0).

### 4.2 Lifecycle `RELEASED`

`LifecycleState.RELEASED` is a **Q2 lifecycle stage** value meaning *material formally released for normal operational use* (Q2 framing §5). It is an **availability/stage** signal, not an influence-weight signal.

### 4.3 Why Track B routes only the authority-class axis

Cluster 2 §7 (line 247) states the Authority sub-dimensions (Authority class, Lifecycle, Promotion rights) are **independent**. Track B v0.1 §2.2 binds `contest_result` to the **Authority-class** axis only. Therefore:

> ```
> contest_result="released"   →  Cluster 2 authority class  →  released FROM identity-shaping influence
> LifecycleState.RELEASED     →  Q2 lifecycle state         →  released FOR operational use
> ```
>
> **Same word. Independent axes. Nearly opposite valence. Must never be conflated.**

Consequence: a future implementer must resolve `contest_result` against the **authority-class precedent surface** (governance-flag vocabulary), **not** the lifecycle envelope — and only via a future, separately-audited effective-authority resolver (§8.0), never by mutating the contested row. The lifecycle substrate (§3.5) is context, not a routing target. This disambiguation must survive in tracked authority.

---

## 5. Minimum future ContestRecord boundary

### 5.1 What the record must express

At minimum, a future `ContestRecord` must durably express (field *names/types illustrative, not finalized* — §5.2):

- **Target** — one-of-required: `contested_eid` (already-spawned row) **or** `candidate_handle` (pre-spawn candidate). *(Track B v0.1 §4.)*
- **Scope** — `contest_scope ∈ {agent, character, workspace*}` (`workspace` declared-but-unimplemented).
- **Actor** — `contestant_actor ∈ {agent, character, operator, user*}` (`user` deferred to Cluster 3) + `contestant_id`.
- **Reason** — required `reason_class ∈ {identity_conflict, material_disagreement, scope_creep, audit_concern}` + optional freeform `contest_reason`.
- **Result** — `contest_result ∈ {low-authority, released, audit-only, refuse}` — **Authority-class axis only** (§4); `refuse` operator-authorized only.
- **Preservation assertion** — `original_memory_preserved: bool` (default `True`).
- **Self-provenance** — `contest_provenance: ProvenanceV1` + `created_at_step`, `session_id`.
- **Optional linkage** — `linked_dissent_topic` (informational only, Inv 9), `counter_contests` (reader-maintained).

### 5.2 What remains illustrative, not finalized

Exact field names, type signatures, enum serialization, file layout, and the `contest_provenance.source_type` internal value are **all deferred to a future schema step**. Track B v0.1 §5.1 already ruled the load-bearing choice is *ledger separation*, not the `source_type` enum value. This artifact does not finalize any of it.

### 5.3 Immutable record / counter-contest posture

Records are **append-only and immutable**. A reversal is a **new** counter-contest record referencing the prior one; the original is never edited. `counter_contests` is a **reader-derived** convenience (reconstructed by ledger replay — §6.3), not a mutable field on the immutable record.

### 5.4 Governance-carrying snapshot requirement

Per Cluster 5 Path C Governance-Preservation Framing §4/§4.1, the record must be **governance-carrying**: it must carry enough provenance/authority context to be read authoritatively in isolation **or** declare itself non-authoritative and require rehydration. A consumer must be able to tell *which*, without guessing. The v0.1 field set (`contest_provenance`, `original_memory_preserved`) leans governance-carrying; a future schema step must confirm it passes the §4.1 acceptance test.

---

## 6. Separate-ledger boundary

### 6.1 Why Option C remains load-bearing

Track B v0.1 §5.1 ratified **Option C — a separate contest ledger**. It remains load-bearing because it (a) avoids a Track A Mode-axis change (Option A), (b) avoids coupling contests to the role-output system (Option B), and (c) preserves clean audit separation. Nothing in the audits weakened Option C.

### 6.2 Existing ledger precedents

`closure_ledger.py` (separation + no-cache + last-event-literal) and `conflicts.py` (record + events + replay) are the two precedents. A future contest ledger most naturally resembles a `conflicts.py`-shaped record+events pair applying `closure_ledger`'s no-cache/replay discipline — **precedent observation, not a design commitment** (the one-file-vs-two-file choice is an open trio decision, §13).

### 6.3 Append-only and replay-derived correctness

Full-ledger replay is **sufficient for correctness**: counter-contest relationships and any aggregate view are derivable by scanning records. This matches `conflicts.apply_events` and `closure_ledger`'s full-walk model. No cache is required for correctness.

### 6.4 Derived indexes remain optional and non-authoritative

A derived index would be a **performance optimization only**. Under the Ledger Observational-Boundary Doctrine §3, any such index must remain **non-authoritative**: it may accelerate reader reconstruction but must never become a back-edge that feeds retrieval scoring, routing, governance gating, prompt assembly, or contest auto-resolution. Whether to *forbid* an index in v0.2 or merely *declare it optional/non-authoritative* is an open trio decision (§13 #7).

**Boundary clarification:** any index used by **live authority resolution** is no longer a mere audit optimization — it would become part of the **authority path** and require **separate ratification**. The optional/non-authoritative status holds only for indexes serving reader reconstruction, never authority computation.

---

## 7. Target-linkage boundary

### 7.1 Already-spawned row: `contested_eid`

When the contested memory already exists, the record targets its integer `eid`. Precedent: `CanonConflict.eid_a/eid_b`. eids are assigned monotonically from the persisted maximum (`memory_graph.py:535,552–553`), are **stable across normal restart**, and are **not reused**. The system already treats `eid` as a durable join key (the Q2 review-queue join uses `join_key="eid"`), so reusing it for contests is consistent with shipped design.

### 7.2 Pre-spawn candidate: `candidate_handle`

When the contest fires before the candidate is spawned, the record targets a stable handle (UUID-style). Precedent: `MemoryProposal.proposal_id` (`schemas/memory_proposal.py:49`).

### 7.3 Handle → eid binding remains an implementation item

**Precision note B (carried explicitly):**

> A pre-spawn contest may target `candidate_handle`. If the candidate later spawns, a durable `handle → eid` linkage must eventually be recorded.
>
> **No such durable binding exists at HEAD** — `proposal_id` is not durably mapped to a spawned `eid` (the per-run `used` set in `fabric.py:6004–6008` is run-scoped, not a durable index). This is an **unbuilt Track-B-local implementation item.** It is **not** a prerequisite for framing and **not** a Cluster 5 lifecycle dependency. One plausible option is a binding event appended to the contest ledger at spawn time. A side-channel, another append-only linkage record, or deferred resolution until implementation planning all remain open trio choices (§13 #3).

This artifact **names** the item and **does not solve it.**

### 7.4 Counter-contest linkage

A counter-contest references the prior `ContestRecord` id. The linkage is reconstructed by replay (§6.3); the prior record stays immutable.

### 7.5 Restart / rebuild posture

`contested_eid` is safe across normal restart (§7.1). The only residual risk is a *hypothetical future* compaction/renumbering pass — **none exists at HEAD**. No repair is proposed here. Whether a storage-readiness checkpoint should precede any code-bearing slice is an open trio decision (§13).

---

## 8. Authority-routing boundary

All routing is on the Authority-class axis (§4). The conservative routing table is inherited from Track B v0.1 §7.2 unchanged; this section only restates the per-value boundary. Naming a `contest_result` value is **not** the same as authorizing how that result takes effect — see §8.0.

### 8.0 Effective-authority resolution boundary (UNRESOLVED — held open)

This is the load-bearing gap Codex's review surfaced. Because `ContestRecord` is **separate and immutable** and the contested row **must not be mutated** (Inv 3, 5):

> **A future contest must lower or hold *effective* authority without mutating the contested memory row.**
>
> The framing does **not** yet decide how consumers derive *effective authority* from:
>
> ```
> original row  +  separate immutable contest ledger
> ```
>
> A resolver, overlay, reader projection, or equivalent mechanism may eventually be required, but **this artifact does not design or authorize one.** The governance-flag precedents named in §3.4 / §8.1–§8.3 must **not** be read as a live enforcement bridge — there is **no authorized contest-application path** at this framing. How effective authority is computed without mutating the row, and without creating a hidden audit-as-authority back-edge, is an open trio decision (§13 #8) and a candidate dedicated resolver-boundary audit (§12).

### 8.1 `low-authority`

Reduced retrieval weight, no identity-shaping. Existing **precedent vocabulary** (not an authorized contest-application path — §8.0): `decay_accelerated` + reduced strength + retrieval discount. The default self-issued result for `material_disagreement`.

### 8.2 `released`

Authority-class synonym of `low-authority` with identity-protection emphasis (§4.1). Existing **precedent vocabulary** (not an authorized application path — §8.0): `low-authority + no-canon`. The default self-issued result for `identity_conflict` / `scope_creep`. **Not** the lifecycle `RELEASED` state.

### 8.3 `audit-only`

Recorded for governance audit; not LLM-facing. Existing **precedent vocabulary** (not an authorized application path — §8.0): `non_shareable` + FILTER-A. The default self-issued result for `audit_concern`.

### 8.4 Operator-only `refuse / no-persist`

**Precision note C (carried explicitly):**

> Operator-only refusal must remain **audit-visible even if no ordinary memory node is spawned.** The `ContestRecord` is the candidate **durable audit carrier** of the refused candidate's provenance snapshot (Inv 12).
>
> **Live-write enforcement of `refuse` remains unbuilt and unauthorized.** The only refusal vocabulary active at runtime today is `admission_refused`, which is **migration-only, not live-write** (Cluster 2 §7.1 line 473). How the operator-refuse path carries the refused candidate's provenance snapshot is an open trio decision (§13).

### 8.5 Self-issued hard-refusal prohibition

Agent- and character-issued contests **cannot** route to `refuse / no-persist` (Inv 10/11/16). Non-operator actors must be **rejected** from `refuse / no-persist`. Self-issued contests max out at `low-authority` / `released` / `audit-only`.

The complete operator authorization rule remains a **future implementation-boundary decision**: `contestant_actor=operator` is **necessary but not sufficient**. `contest_scope` names the affected mind; it is **not** itself an authorization tier. This artifact does not design operator authorization (§13 #5).

---

## 9. Audit visibility boundary

**`ContestRecord` is not merely an audit record. It is a durable authority-action record whose visibility is audited.** Audit observations of it must never silently become scoring, prompt, or hidden routing inputs.

### 9.1 Contest increases discoverability

Per Inv 14, a contest must become **more** audit-discoverable, never less; contest is never a hiding mechanism. **Which first surface characterizes that visibility remains an open trio decision (§13 #6).** Possible observation surfaces may include existing audit-oriented or contested-material surfaces, but **none is selected here.**

### 9.2 Audit visibility ≠ retrieval influence

Per Ledger Observational-Boundary Doctrine §3: contest frequency, recency, or density must **never** feed retrieval scoring or ranking. Surfacing a contested item is allowed; letting contest history *weight* retrieval is forbidden.

### 9.3 Audit visibility ≠ prompt influence

Contest content must **not** appear in, or be paraphrased into, `assembled_text` without governance gating. Audit-as-secret-prompt-input is forbidden.

### 9.4 Audit history cannot silently auto-resolve authority

Per Observational-Boundary §3 (named explicitly for Track B): contests **cannot** be silently auto-resolved by appeal to audit history. No "previously contested → auto-route" pathway. Resolution is always an explicit authority action.

---

## 10. Consultation boundary remains deferred

### 10.1 Dissent may inform; dissent must not auto-trigger

`linked_dissent_topic` allows an explicit contest to *reference* a cognition dissent entry. It does **not** auto-create a `ContestRecord` (Inv 9/15). Dissent and contest remain different lifecycle objects.

### 10.2 No LLM consultation design in this framing

How a contest *fires* — sync LLM call, async queue, heuristic gate, manual operator action — is **not designed here** and not in v0.2 framing scope. Track B v0.1 §9 deferred it; this artifact holds that deferral.

### 10.3 No autonomous firing mechanism

No agent-initiated runtime firing is framed. No scheduler, no loop, no automatic emission. The seam is named; the trigger is not.

---

## 11. Storage-readiness notes

### 11.1 No blocking Cluster 5 dependency for framing

Per the Q2 micro-audit (Option 1): the contest routes the Authority-class axis, which is **truthfully nameable at framing level today** via existing governance-flag precedents (§3.4), independent of the Q2 lifecycle envelope. **No separate Cluster 5 lifecycle-modeling gate must close before drafting or before the record can be stated truthfully.** (Nameability at framing level is not an enforcement path — application still awaits the §8.0 resolver-boundary audit.)

### 11.2 Handle → eid binding as Track-B-local implementation work

See §7.3. Unbuilt, Track-B-local, nameable now, not a Cluster 5 precondition.

### 11.3 Operator refuse live-write substrate remains unbuilt

See §8.4. `admission_refused` is migration-only; live-write refuse enforcement is unbuilt and unauthorized. The record-side audit carry is self-contained; the enforcement side is deferred Track B implementation.

### 11.4 Future storage-hardening questions remain separate

eid-durability-under-compaction (§7.5), governance-carrying §4.1 conformance (§5.4), and any durable index policy (§6.4) are storage-hardening questions that belong to implementation planning, not to this framing. Whether they need their own storage-readiness checkpoint is an open trio decision (§13).

---

## 12. Candidate staged implementation sequence — FRAME ONLY (not authorized)

Conservative possible sequence, mirroring the audit-first slice cadence used by Q1/Q2. **Each step ends in a review gate; no step authorizes the next. This is illustration, not authorization, and may change after review. A separate operator authorization is required before B2-S2 onward.**

```
B2-S1   tracked framing promotion only (docs-only; no code)   [THIS ARTIFACT]
B2-S2   ContestRecord vocabulary + validator + pure serialization tests
        (no production wiring — mirrors Q2 Slice 0 pattern)
B2-S3   append-only separate-ledger writer/reader + replay tests
        (isolated; no consumer wiring)
B2-S4   target-linkage support: contested_eid, candidate_handle,
        handle -> eid binding, counter-contest replay
B2-S5   operator-only refuse validation + audit-visibility tests
        (record-side audit carry; no live-write enforcement)
B2-S6   cross-surface characterization:
        observation surfaces only — no scoring influence,
        no prompt influence, no mutation, no auto-firing
```

**Resolver-boundary framing note (no resolver slice added).** Before any consumer wiring — i.e., before B2-S6 and before any later *application* of contest results — run a dedicated **read-only effective-authority resolver-boundary audit** (§8.0). That audit must determine how `row + contest ledger` produces *effective authority* **without mutating the row** and **without creating a hidden audit-as-authority back-edge**. This artifact does **not** decide whether the resolver is an overlay, a reader projection, a side index, a derived view, or a policy layer — those remain future questions. **No resolver *implementation* slice is added to the sequence.**

**Deliberately excluded from the sequence:** any resolver-implementation slice; any runtime firing-mechanism slice; any cognition-dissent coupling slice; any LLM-consultation slice; any retrieval-integration slice beyond observational characterization (B2-S6); any MCP-exposure slice (parked as a future question only).

---

## 13. Open trio decisions — parked for later review

Per operator ratification (2026-06-03), the technical choices below are **explicitly parked**, not resolved by this framing. Each must be resolved (or explicitly re-parked) before the **relevant code-bearing slice** in §12, not before this framing promotion:

1. **Working name.** Is `ContestRecord` the final public working name (vs `DisagreementEvent` / `AuthorityContest`)?
2. **Ledger shape.** One-file records only, or a `conflicts.py`-style records + events pair?
3. **Handle → eid linkage.** An appended binding event, a separate side-channel, another append-only linkage record, or left unresolved until implementation planning? (See §7.3.)
4. **Operator-refuse provenance carry.** How should operator `refuse` carry the refused candidate's provenance snapshot when no memory node spawns? (See §8.4.)
5. **Operator authorization / validator boundary.** Beyond rejecting non-operator actors, what is the complete operator authorization rule for `refuse / no-persist`? (`contestant_actor=operator` is necessary but not sufficient; `contest_scope` is not an authorization tier — see §8.5.)
6. **First observation surface.** Which surface should characterize contest visibility first? None is selected here. (See §9.1.)
7. **Derived index policy.** Should a future derived index be *explicitly forbidden* in v0.2, or merely *declared optional and non-authoritative* — and in all cases never on the authority path? (See §6.4.)
8. **Effective-authority resolution.** How is *effective authority* resolved from a separate immutable contest ledger **without mutating the contested memory row** (§8.0)? Does this require a dedicated **read-only resolver-boundary audit** before any consumer wiring or implementation planning? (See §12.)
9. **Storage-readiness checkpoint.** Does the staged sequence need a separate storage-readiness checkpoint before any code-bearing slice? (See §7.5, §11.4.)

---

## 14. Explicitly out of scope

Held closed by this artifact (not opened, not designed, not authorized):

```
implementation                         Cluster 2 v0.2 runtime Authority Gate
schema finalization                    Cluster 5 generic storage redesign
writer / reader code                   lifecycle transition work
audit endpoint                         migration
retrieval scoring influence            backfill
prompt assembly influence              database replacement
automatic contest firing               Q3-D2
cognition-dissent auto-coupling        Q3-D3
LLM consultation                       fallback vocabulary redesign
                                       public MCP expansion
                                       autonomy
```

MCP note: the MCP Capability Boundary is unchanged — MCP remains a governed memory surface with no action/tool dispatch. Any future contest exposure over MCP is **parked as a future question only**, not opened here.

---

## 15. Ratification conformance record

The following conformance checks were verified across the review chain (GPT review → Codex adversarial review → Codex verification pass → Hilmir ratification, 2026-06-03):

- [x] Center question (§1) unchanged from Track B v0.1.
- [x] All inherited invariants (§2) preserved in intent.
- [x] Axis disambiguation (§4) correct and unambiguous: authority-class `released` ≠ lifecycle `RELEASED`.
- [x] Effective-authority resolution boundary (§8.0) named as **unresolved**; no resolver designed; governance-flag precedents (§3.4, §8.1–8.3) presented as precedent vocabulary only, **not** an authorized contest-application path.
- [x] §2 item 13 split into two distinct claims (A: no ProvenanceV1 redesign; B: no Track A amendment), not compressed.
- [x] No section finalizes a schema signature, file layout, or enum serialization.
- [x] Handle → eid binding (§7.3) named as unbuilt, not solved.
- [x] Operator refuse (§8.4) named as audit-carrying but not live-write-wired.
- [x] Option C separation (§6.1) intact; ProvenanceV1 not redesigned (Inv 13).
- [x] Audit-visibility boundaries (§9) consistent with Ledger Observational-Boundary Doctrine §3.
- [x] Consultation / firing mechanism (§10) still deferred.
- [x] Staged sequence (§12) framed as illustration only; no firing/cognition/LLM/retrieval-integration slice present.
- [x] Out-of-scope list (§14) complete.
- [x] Open trio decisions (§13) capture every unresolved choice; none silently decided in the body.
- [x] Storage-readiness verdict (§11.1) consistent with the Q2 micro-audit Option 1 result.

---

*End of Track B v0.2 — Contest-Ledger Runtime Boundary Framing v0.1. Ratified framing artifact (Hilmir, 2026-06-03). Not doctrine. Not implementation authorization. The runtime contest-ledger mechanism, when built, requires a separate operator authorization before any code-bearing slice (B2-S2 onward). Subsequent framing or doctrine versions require their own ratification before they supersede this one.*
