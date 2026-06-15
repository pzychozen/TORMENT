# TORMENT Governed-Memory Substrate Programme — Free-Design Council Framing (pre-Stage-B) v0.1

**Status:** **Promoted docs-only 2026-06-15.** Tracked docs artifact — docs-only · framing-only. A bounded gate-framing artifact for the trio free-design council that the closed stack's §16 advisory path places before any Stage B / database design. It frames a *meeting*: it sets the council's agenda and limits. **It designs no database and opens no Stage B.** GPT steering review accepted for finalization; closure is registered in the Decision Registry **§N15** by this promotion slice.
**Date:** 2026-06-15.
**Authoritative state at drafting:** HEAD = origin/main = `039cec4`; working tree clean. Subsequent versions require their own trio/operator ratification.
**Lineage:** §16 advisory path of the DB/Substrate Doctrine Reconciliation (registry §N12) → matched P2.5/P4 reconciliation (§N13) → gravity_correction audit-first reconciliation (§N14, closed) → accepted working-folder gate-framing plan (`scratch/substrate_free_design_council/2026-06-15/GATE_FRAMING_SUBSTRATE_FREE_DESIGN_COUNCIL_v0.1_PLAN.md`) → GPT steering review (ACCEPT WITH SMALL CORRECTIONS, applied) → Codex adversarial leakage review (ACCEPT, no required corrections) → operator decision to open this docs-only framing gate. The working-folder plan remains non-load-bearing evidence lineage.

**What this artifact is:** it frames a *meeting* — the trio free-design council. It sets that meeting's agenda and its limits.

**What this artifact is not:** not a Stage B opening, not a database design, not a schema / store / carrier / field / ID / fingerprint / allocator / serialization / migration / storage-product choice, not runtime implementation, not authority enforcement, not a registry amendment by itself.

---

## Standing locks (carried through the whole artifact)

- **Guide, not control.** TORMENT memory guides; it does not control. "Control" means absolute / coercive blocking.
- **No secret rewrite.** Nothing may secretly rewrite identity, canon, seed, or soul.
- **Audit observes, never becomes, authority.**
- **No Stage B opening here.** No database mechanics. No schema, SQL, tables, fields, IDs, fingerprints, allocator rules, serialization, migration mechanics, runtime implementation, or storage-product choice.
- **JSON/JSONL replacement is operator posture, not a product or storage selection.** The eventual goal of replacing JSON/JSONL as the trusted substrate is Hilmir's stated direction; it selects no technology here.
- **Labels are seam evidence only**, not future field/carrier/schema endorsements.

---

## 1. Status / safe-to-open

**Safe to open as a docs-only, pre-council framing gate.** Grounds:

- The closed stack's own ordering (DB/Substrate memo §16; gravity_correction artifact §11) is: §N12 → §N13 → §N14 → **trio free-design council** → Stage B / database mechanics only after the council *and* the Issue #54 clean-checkpoint. All three pre-council reconciliations (§N12, §N13, §N14) are closed.
- The registry quick-reference: active gate **none**; next gate **unselected**; Stage B mechanics and database design remain unopened and are not auto-selected.
- This gate frames the next named step (the council). It opens no design and selects no mechanic, so it cannot leak Stage B.

**Not safe / out of scope:** opening Stage B; choosing any storage mechanic; resolving the named seams by picking mechanics (see §4).

## 2. Council purpose (plain language)

The pre-council homework is done. The council's job is **not** to build the database and **not** to formally open Stage B. Its job is to decide, in plain terms:

> **What must be true before Stage B / database design can be safely opened — and is the project ready to prepare that opening decision after the Issue #54 clean checkpoint?**

The council produces a readiness judgement and an ordered plan-of-approach, not a design. It decides *whether the project is ready to prepare a later Stage B opening decision*, not *to open Stage B*.

## 3. Agenda — what the council MAY decide

1. **Readiness call.** Whether the project is ready to *prepare* a later Stage B opening decision — i.e. whether the conditions in §5/§6 are met or what remains.
2. **Ordering of work.** The sequence in which future pieces would be tackled, without deciding their contents.
3. **Carry-forward of the named seams.** How each already-named seam (§5) is recorded as a *requirement a later design must honor* — not solved here.
4. **The cross-before-design barrier.** Confirm the Issue #54 clean-checkpoint as the thing that must be crossed before any design work begins (§6).
5. **Confirm the safe work-order rule** (§8).
6. **Hand-back recording.** Record the later points where Hilmir is brought back in (§7) — recording them, not triggering them now.
7. **Name the likely next gate label only, if ready.** Do not define Stage B requirements beyond already-ratified process barriers and carried-forward seams. Do not draft Stage B content.

## 4. Hard limits — what the council MUST NOT decide

- **Must not formally open Stage B.** It may only frame what must be true before a later Stage B opening decision.
- No database product, SQL, tables, schema, or field names.
- No memory IDs, fingerprints, allocator rules, or serialization formats.
- No migration mechanics (how old JSON/JSONL is moved).
- No runtime code, enforcement, or authority-gate wiring.
- No reopening or redefining of identity / canon / seed / soul meaning.
- Must not "solve" a named seam by selecting a mechanic — naming and carrying-forward only.
- Must not let audit or inspection become control. Audit observes; it never becomes authority.
- Must not turn this framing gate, or the council, into a design session.

## 5. Named seams carried forward as requirements (not solved)

These are already named in the closed docs. The council records each as *a requirement any later design must be able to state it will honor* — it resolves none of them (DB/Substrate memo §11 + §13: the seams "block substrate mechanics that would depend on them," but each is "a requirement a later substrate proposal must be able to state it will honor before mechanics open"). Existing labels below are seam evidence only.

- **Memory meaning must survive.** "A memory is not recovered unless its governance meaning is recovered" (Stage A anchor). A future store must keep meaning, not just text.
- **Identity is not a single flag.** One `canon=True` boolean is not, by itself, sufficient governance truth; canon-by-source must stay distinguishable (Seed-Gov SG-O4) — recorded as a requirement, no representation chosen.
- **The automatic drift writer.** `gravity_correction` emits `canon=True`, `tier="core_identity"` `drift_correction` rows automatically and conditionally (§N14). It is a named, requires-reconciliation seam — carried forward, not patched, and not treated as permanent or unchallengeable.
- **Write-side authority is not yet checked.** Writers are currently trusted by payload flags, not by an authority check (Document A A-O1/A-O5) — recorded as a requirement, no mechanic chosen.
- **Identity / echo sameness.** The reusable `eid` + presence-only echo validation overload (P2.5 / registry C20) must be resolvable before any later durable representation of "sameness" — recorded, not designed.
- **Storage-correctness gaps.** The known crash/torn-write gaps (`JSONL-NO-FSYNC`, `IDENTITY-NON-ATOMIC-SAVE`, `INGEST-NOT-TRANSACTIONAL`, `JSONL-LOADER-NOT-FAIL-TOLERANT`; substrate-readiness memo §3) are inputs a future design must address — routed, not fixed here.
- **Read-side adjacency stays separate.** P4 read-side retrieval / continuity-boost behavior is named adjacency only; later P4 runtime conformance owns it.

## 6. Issue #54 clean-checkpoint — the cross-before-design barrier

Before database/substrate design is even *considered*, the docs require crossing the Issue #54 barrier: record a **synchronized, Windows-authoritative clean checkpoint** and do a **fresh-chat handoff** (registry §N6 / quick-reference; DB/Substrate memo §16; orientation map). The council treats this as the gate that must be crossed *before* any design begins — it confirms the barrier; it does not perform or waive it.

## 7. Hilmir hand-back points (recorded, not asked now)

Hilmir's standing operator posture is **already sufficient for this pass** — no questions are posed as blockers now. The posture, carried:

> TORMENT memory guides, it does not control. Control means absolute/coercive blocking. No hidden rewrite of identity, canon, seed, or soul. Audit observes authority, but audit does not become authority. The future database should eventually replace JSON/JSONL as the trusted memory substrate. Old JSON/JSONL migration must not lose or silently change memory meaning.

Under that posture, the council records these as *likely later hand-back points* — moments to bring Hilmir back in, not questions to answer now:

- **Before the final switch-over** from JSON/JSONL to the database as the trusted source of truth.
- **Before any irreversible migration behavior.**
- **Before any choice that changes identity / canon / seed / soul meaning.**

Everything else (technical ordering, what to design first) the trio may decide under the standing posture.

**Standing safe default for unclear old-memory migration** (recorded for any later design to honor, not a mechanic): if an old memory's meaning cannot be carried over cleanly, keep it **visible and auditable**, mark it as **needing review / `diagnostic_only`** (or an equivalent later-governed posture), and **do not** silently drop it, silently rewrite it, or let it become cognition-authoritative. A later explicit, governed action may restore it. `diagnostic_only` is used here as a plain-language safe posture reference, not as a selected future database field, enum, or schema value.

## 8. Dependency-order rule (confirm, do not execute)

The council confirms the safe work-order the closed docs already state (matched P2.5/P4 reconciliation; DB/Substrate memo):

```
requirements  →  carrier proposal  →  family write-site work
                                        (reader / projection runtime conformance: separate, later-authorized)
```

Plain version: first agree *what is required*; only then propose *a way to represent it* (a "carrier"); only then do the detailed *write-side* work; and keep the *read-side runtime* work as its own separate, later approval. No step is performed here — the council only confirms the order.

## 9. Advisory sequencing (carried; opens nothing)

```
N12 DB/Substrate reconciliation        [CLOSED]
N13 matched P2.5/P4 reconciliation      [CLOSED]
N14 gravity_correction audit-first      [CLOSED]
→ trio free-design council              [THIS FRAMING TARGETS IT]
→ if council judges ready, record what a later Stage B opening decision would require
→ Issue #54 clean-checkpoint crossed
→ prepare fresh-chat handoff / Stage B opening decision
→ Stage B / database design only if separately authorized
```

This artifact opens nothing by itself. Holding the council is a separate operator decision.

## 10. Review path

```
Claude draft (working-folder plan)
→ GPT steering review (ACCEPT WITH SMALL CORRECTIONS, applied)
→ Codex adversarial leakage review (ACCEPT, no required corrections)
→ operator decision to open this docs-only framing gate (done)
→ promoted tracked artifact (this file) + registry §N15 closure registration → operator staging/commit
→ only then is the trio free-design council a separate operator decision to hold
```

## Promoted-artifact footer

This is a **promoted docs-only** tracked artifact — framing-only. It frames the trio free-design council; it does not hold it. It confers **no implementation authority, no Stage B opening, no database design, no schema / store / field / carrier / ID / fingerprint / allocator / serialization / migration / storage-product selection, no runtime implementation, no authority enforcement, and no autonomy.** It amends no upstream contract and does not amend the recorded dependency graph. Issue #54 remains the cross-before-design barrier. Closure is registered in the Decision Registry §N15 by this promotion slice. Subsequent versions require their own trio/operator ratification.
