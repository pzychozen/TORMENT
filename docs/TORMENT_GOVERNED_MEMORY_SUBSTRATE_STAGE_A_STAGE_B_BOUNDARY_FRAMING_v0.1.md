# TORMENT Governed-Memory Substrate Programme — Stage A / Stage B Boundary Framing v0.1

**Status:** DRAFT — read-only boundary-framing checkpoint. Docs-only. **Not implementation, not database
design, not Stage B mechanics, not schema/carrier/storage selection, not migration design, not
allocator/manifest mechanics, not a runtime patch, not a registry amendment.** It defines a *boundary*
and *carry-forward constraints* only.

**HEAD at drafting:** `b4719a3` (operator-supplied; not copied from stale board/checkpoint text).
**Date:** 2026-06-20.
**Authority:** operator-selected substrate-readiness checkpoint → Claude read-only readiness report
(eligible-at-framing) → Codex **ACCEPT WITH CORRECTIONS** (folded in below). Authority class: **trio**.
**Scope of authorization:** *Stage-B-to-framing only* — this artifact may define what Stage A owns, what
Stage B would later own, what is carried as constraints, and what must not be selected. It opens no gate.

**Standing anchors (carried verbatim):**

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.
> Preserve continuity without preserving compulsion.

---

## 1. Title / status

The recorded-but-unopened umbrella is the **TORMENT Governed-Memory Substrate Programme** (name recorded
in the Substrate Readiness & Phase Consolidation Memo §4). This artifact is its **first framing task**: a
read-only definition of the Stage A / Stage B boundary. It selects no mechanic and opens no stage.

## 2. Non-goals and hard exclusions

This checkpoint does **not**, and may not: open Stage B · choose substrate mechanics · select storage,
schema, carriers, formats, identity tokens, fingerprint algorithms, serialization, allocator, or manifest
mechanics · design a database · design migration · authorize any implementation, tests, or runtime patch ·
open candidate store / governed admission · open Seed-Gov/O6 mechanics · open P4 / source-sameness
mechanics · open Gate 4 writer remedies · open durable private-cognition runtime, the Document B chamber,
or dream/incubation · pin identity · introduce monitoring/autonomy/self-trigger · add an output
blocker/finalizer. Per Decision Registry §L and Consolidation Memo §10.

## 3. Why this checkpoint is eligible

TORMENT is **eligible for a read-only Stage A / Stage B boundary-framing checkpoint** under Decision
Registry **§K**, which makes custom-substrate *consideration* eligible on evidence of (among others)
**transactional guarantees unmet by subordinate primitives** and **portability / auditability / recovery
blockers**. That evidence exists today (§4). The Issue #54 cross-before-design barrier has prior clean-checkpoint
records, most recently re-verified at `01ec838`; any later Stage B opening must reconfirm the barrier at
the then-current HEAD. The requirement-level contracts (Document A, Document B, Seed-Governance, P4, the
Stage A recovery/reconciliation semantics contract, the DB/Substrate Doctrine Reconciliation) are
promoted.

**Eligibility ≠ authorization.** Eligibility means the trio *may* define this boundary. It does not open
Stage B and selects no mechanics.

## 4. Corrected current evidence

Assembled from already-tracked facts and one targeted re-verification; **no new defect-hunting.**

- **`INGEST-NOT-TRANSACTIONAL` (restated, narrowed).** The earlier unknown-domain / motif-registry orphan
  example is **no longer the live illustration** — `fabric.ingest()` now carries a preflight for that
  specific case. The **broader finding stands**: a single `fabric.ingest()` still runs with **no enclosing
  transaction** across graph JSONL (nodes / optional edges), embedding writes, memory events, the SQLite
  sidecar, motif / collective / character side effects, and post-write follow-ons. Concretely (verified at
  drafting against `fabric.py`): `spawn_memory()` writes the embedding/event **before** `flush_node()`
  writes the node row; symbol/resonance enrichment and `_save_symbol_state` occur in between; and a
  `flush_node()` failure is **logged (`_log.debug`), not rolled back**. A crash or partial failure between
  these steps leaves a cross-file inconsistency window. *(Narrowed example; broad no-enclosing-transaction
  finding preserved.)*
- **`JSONL-NO-FSYNC` (carried evidence).** Canonical appends carry no flush/fsync/journal; trailing or torn
  records can be lost on crash. *(Cluster 5 v0.1 §5.1; carried, not re-verified this slice.)*
- **`IDENTITY-NON-ATOMIC-SAVE` (carried evidence).** Identity / character / role saves use raw
  truncate-and-write; a crash can leave zero-byte or partial files. *(Cluster 5 v0.1 §5.2; carried.)*
- **`JSONL-LOADER-NOT-FAIL-TOLERANT` (carried evidence).** The primary loader does not catch
  `JSONDecodeError`; one torn line aborts the whole load. *(Cluster 5 v0.1 §5.10; carried.)*
- **Lineage / source-sameness gaps (carried).** P2.5 memory-lineage identity has no substrate carrier; P4
  O1/O2 source-sameness has no selected carrier or comparison mechanism (live joins presence-only).

Together these establish the **unmet-transactional-guarantees** trigger with **recovery / auditability
blockers** — the §K basis for *this framing*. They authorize **no** fix and **no** mechanism.

## 5. Stage A responsibilities (recovery / reconciliation / semantic obligations)

Stage A owns **semantics, not mechanics**. It defines *what must remain true* of recovery and
reconciliation, independent of how storage is later built:

- what must remain **recoverable** vs. acceptably-lost after a crash;
- what remains **inspectable**, and the `diagnostic_only` posture (eligibility posture, not projection);
- **orphan / partial-write / mismatch** treatment and **quarantine** semantics;
- the **non-coercive recovery boundary** — recovery may restore validity but must never canonize, pin, or
  confer authority by side effect;
- consistency with Stage A O6 (**preserve-without-pinning**) and the §N7 soft-state postures.

Stage A is **strong enough to constrain framing** (it bounds what Stage B may do) but **not strong enough
to solve mechanics** — it names obligations, not implementations.

## 6. Stage B future responsibilities (explicitly UNOPENED)

Stage B is **named here only to fix the boundary; it is not opened and nothing in it is selected** — category labels only, not a roadmap or menu. Stage B
would later own carrier / substrate / durability **mechanics**: identity carriers; revision fingerprints;
serialization; allocator durability; IntegrityManifest mechanics; transactional/atomic write strategy and
fsync/journal policy; the SQLite-sidecar relationship; substrate architecture; packaging-boundary
evaluation; and (separately, P9) migration. **None is chosen, evaluated, or scheduled by this artifact.**
Stage B must later **satisfy** Stage A's semantics; it may surface bounded questions that require an
explicit Stage A amendment, but it must not silently pre-answer Stage A.

## 7. Carry-forward constraints

These travel into any future Stage A/Stage B work as binding inputs:

- **Soft-guidance / O6 unresolved constraints (must not be silently erased, canonicalized, pinned, or made
  authority-bearing):** **warmth · mood · drift · role · symbolic influence.** These include durable-soft
  guidance and live unreconciled identity-pressure surfaces; their precise Stage A/O6 treatment remains
  carried forward. Durability work must not silently erase, canonicalize, pin, or convert them into
  identity/canon authority.
- **Document B interior obligations** — non-reachability by construction, staging ≠ admission, silence as
  a non-reentry footprint; any future durable chamber state inherits these.
- **Seed-Governance** — O6 must-not-pin; authored-seed write-once.
- **P2.5 / P4 lineage & source-sameness** — carriers/comparison remain to be defined; carried as
  requirements, not designed here.
- **Track B durability/survivability** — contest-ledger records must remain recoverable **with their
  governance meaning**; Track B is not absorbed by this programme.
- **Cluster 5 v0.2 fragility handles** — inputs to the programme, not a competing track.
- **P3 shell-continuity (dormant, intact).** `restore_from_checkpoint()` has **no runtime callers found** —
  current references are **definition plus tests only** (Consolidation Memo §6). Fresh awakening remains
  current behavior; P3 becomes load-bearing only before any non-test/non-debug runtime restores checkpoint
  or shell state in a way that affects cognition, identity, agency, continuity claims, or output.

## 8. Boundary rules — what the framing may and may not say

- **May:** name the umbrella; assign an obligation to Stage A (semantics) or Stage B (mechanics); record a
  carry-forward constraint; state that an item is unresolved/unopened; restate evidence as a problem
  statement.
- **May not:** name or imply a specific storage product, schema, format, carrier, fingerprint, allocator,
  manifest, or serialization; assert that a defect is fixed by a particular mechanism; sequence or schedule
  Stage B; convert any soft-state signal into canon/identity authority; treat eligibility as authorization.
- **Separation invariant:** *semantics must not smuggle mechanics; mechanics must not silently pre-answer
  semantics.* Any sentence that does either is out of scope for this artifact.

## 9. Blockers before any later Stage B mechanics

Stage B (separately authorized, later) must not begin until each of these is resolved **by design, under
trio authority**:

1. A defined recovery/reconciliation semantics set (Stage A) sufficient to constrain mechanics, including
   the soft-guidance/O6 carry-forward (§7).
2. A transactional/atomicity model for `fabric.ingest()` cross-file writes (the §4 broad finding) — *what*
   atomicity must hold, before *how*.
3. Durability posture for canonical appends (`JSONL-NO-FSYNC`) and atomic identity saves
   (`IDENTITY-NON-ATOMIC-SAVE`) — as obligations, not chosen mechanisms.
4. Loader fail-tolerance obligation (`JSONL-LOADER-NOT-FAIL-TOLERANT`).
5. P2.5 / P4 carrier & source-sameness requirements pinned as inputs.
6. Issue #54 cross-before-design barrier confirmed clean at the time Stage B opens.
7. Re-verification that P3 `restore_from_checkpoint()` is still dormant (no runtime callers) at that time.

These are blockers before **mechanics**, not before **this framing**.

## 10. Required next authority step after this doc

After promotion, substrate-readiness parks. The only intended follow-up is a short orientation-map
pointer and a status-board row update. Any later Stage A clarification/amendment, Stage B opening
decision, database design, or substrate mechanics pass requires a separate trio/operator authorization.
Stage B remains unopened and is not auto-next.

## 11. Anti-drift footer

This artifact opens no stage, selects no mechanism, designs no database, names no storage product, amends
no registry or upstream contract (Document A / B / P4 / Stage A / Seed-Gov / Cluster 2 / Ledger / MCP
boundary), and authorizes no implementation. It defines a boundary and carries constraints. *Eligibility
is not authorization; framing is not mechanics; naming Stage B is not opening it.*

*End — Governed-Memory Substrate Programme Stage A / Stage B Boundary Framing v0.1. Read-only boundary
artifact; trio-gated; Stage B unopened.*
