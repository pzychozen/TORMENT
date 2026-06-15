# TORMENT Governed-Memory Substrate Programme — Free-Design Council Outcome (pre-Stage-B) v0.1

**Status:** **Promoted docs-only 2026-06-15.** Tracked **council-outcome closure** artifact — docs-only. Records the written outcome of the trio free-design council framed by the promoted N15 artifact. **It designs no database, opens no Stage B, and selects no mechanic.** Closure is registered in the Decision Registry **§N16** by this promotion slice.
**Date:** 2026-06-15.
**Authoritative state at drafting:** HEAD = origin/main = `42f833c`; working tree clean. Subsequent versions require their own trio/operator ratification.
**Boundary artifact:** held strictly inside `docs/TORMENT_GOVERNED_MEMORY_SUBSTRATE_FREE_DESIGN_COUNCIL_FRAMING_PRE_STAGE_B_v0.1.md` (the promoted N15 framing). The council decided only what that artifact's agenda (§3) allows and nothing in its hard-limit list (§4).
**Lineage:** N15 council-framing promotion → trio free-design council held in writing (working-folder outcome) → GPT steering review (ACCEPT WITH TWO SMALL WORDING CORRECTIONS, applied) → Codex adversarial leakage review (ACCEPT, no required corrections) → operator promotion (docs-only). The working-folder outcome record remains non-load-bearing evidence lineage.

**Standing locks carried:** guide, not control · audit observes authority, never becomes authority · no hidden rewrite of identity/canon/seed/soul · no Stage B opening · no database mechanics · JSON/JSONL replacement is operator posture, not product selection · `diagnostic_only` is a plain-language safe posture reference, not a future field/enum/schema value · labels are seam evidence only.

---

## 1. Council verdict

**Ready to prepare a later Stage B opening decision** — conditional on the Issue #54 clean checkpoint being crossed first (§3).

Plain version: the writing-stage homework is finished. The project is ready to *prepare* the decision that would later open database/substrate design. It is **not** ready to open Stage B now, and this council does not open it.

## 2. Why (what N12 / N13 / N14 / N15 cleared)

The closed stack's own ordering required four things before this council could judge readiness. All four are done:

- **N12** — confirmed a future database wouldn't break any rule the closed stack already set (compatibility audit before mechanics).
- **N13** — paired the write-side findings with the read-side rules so both are understood together.
- **N14** — named and routed the one live automatic canon writer (`gravity_correction`) without patching it.
- **N15** — framed this council: its agenda, its limits, and the requirements it must carry forward.

With those closed, the only items left before design are a clean save-point and the design decision itself — not more reconciliation. That is what makes the verdict "ready to prepare."

## 3. What must happen before Stage B / database design

1. **Issue #54 clean checkpoint** — record a synchronized, Windows-authoritative clean checkpoint, then do a fresh-chat handoff. This is the cross-before-design barrier; it must be crossed before any design begins. The council confirms it; it does not perform or waive it.
2. **A separate Stage B opening decision** — a bounded, deliberate gate (named in §9) that decides *whether to open design and what bounded categories the opening gate may include*. Design does not start automatically after the checkpoint.

No further pre-council reconciliation is currently identified before that opening decision; the checkpoint and opening decision may still surface blockers.

## 4. Work ordering (confirmed, not executed)

```
requirements  →  carrier proposal  →  family write-site work
                                        (reader / projection runtime conformance: separate, later-authorized)
```

Plain version: first agree *what is required*; then propose *a way to represent it*; then do the detailed *write-side* work; and keep the *read-side runtime* work as its own separate, later approval. The council confirms this order. It performs no step.

## 5. What the future Stage B opening decision MAY consider (categories only, not mechanics)

The opening decision, when it happens, may scope these *topics*. It still selects no mechanic at the point of opening:

- **Meaning-preserving recovery** — that stored memory keeps its governance meaning, not just its text.
- **Identity / sameness** — how "this is the same memory" is to be trusted (category only; no IDs/fingerprints chosen).
- **Canon-by-source distinguishability** — that canon's source class stays tellable apart (no field/flag chosen).
- **Write-side authority** — that writers are authorized for the class they write (no enforcement chosen).
- **Durability / crash-safety** — that committed memory survives crashes and interrupts (no journal/fsync/transaction chosen).
- **Migration approach from JSON/JSONL** — that old data moves without losing or silently changing meaning (no migration mechanics chosen).
- **Read-side conformance scheduling** — when the separate runtime reader/projection work is authorized.

These are headings the opening decision may put on its own agenda — not answers, and not design.

## 6. What remains forbidden

- No database design. No Stage B opening (this council does neither).
- No SQL, schema, tables, fields, IDs, fingerprints, carriers, allocator rules, or serialization.
- No migration mechanics. No storage-product choice.
- No runtime implementation or authority enforcement.
- No reopening or redefining of identity / canon / seed / soul meaning.
- No turning audit or inspection into control.
- No solving the named seams (§7) by picking mechanics — carry forward only.

## 7. Named seams carried forward (requirements to honor, not problems solved)

Each is a requirement any later design must be able to state it will honor. None is solved here. Labels are seam evidence only.

- **Memory meaning must survive recovery** — "a memory is not recovered unless its governance meaning is recovered" (Stage A anchor).
- **Identity is not a single flag** — one `canon=True` boolean is not sufficient governance truth; canon-by-source must stay distinguishable (Seed-Gov SG-O4).
- **The automatic drift writer** — `gravity_correction` emits `canon=True`, `tier="core_identity"` `drift_correction` rows automatically and conditionally (N14); a named, requires-reconciliation seam — not permanent, not unchallengeable.
- **Write-side authority not yet checked** — writers currently trusted by payload flags, not an authority check (Document A A-O1/A-O5).
- **Identity / echo sameness** — reusable `eid` + presence-only echo validation overload must be resolvable before any durable "sameness" representation (P2.5 / registry C20).
- **Storage-correctness gaps** — `JSONL-NO-FSYNC`, `IDENTITY-NON-ATOMIC-SAVE`, `INGEST-NOT-TRANSACTIONAL`, `JSONL-LOADER-NOT-FAIL-TOLERANT` (substrate-readiness §3) are inputs a future design must address.
- **Read-side adjacency stays separate** — P4 read-side retrieval / continuity-boost behavior is named adjacency only; later P4 runtime conformance owns it.

**Standing safe migration default (carried):** if an old memory's meaning cannot be carried cleanly, keep it visible and auditable, mark it needing-review / `diagnostic_only` (posture reference, not a chosen field), and never silently drop, rewrite, or make it cognition-authoritative; a later governed action may restore it.

## 8. Hilmir hand-back points (recorded, not triggered)

Hilmir's standing posture is sufficient for this pass; nothing is asked now. Bring Hilmir back in only when a choice:

- **changes identity / canon / seed / soul meaning**, or
- introduces **irreversible migration behavior**, or
- performs the **final switch-over** from JSON/JSONL to the database as the trusted source of truth.

Everything else (technical ordering, what to design first) the trio may decide under the standing posture.

## 9. Recommended next gate label (label only)

**TORMENT Governed-Memory Substrate Programme — Stage B Opening Decision (pre-design) v0.1**

Label only. It sits *after* the Issue #54 clean checkpoint and would itself be a bounded, separately authorized decision about whether to open Stage B design and what bounded categories its opening gate may include. Naming it here defines no Stage B content and opens nothing.

## 10. Review lineage and next action

```
N15 council-framing promotion
→ trio free-design council held (working-folder outcome)
→ GPT steering review (ACCEPT WITH TWO SMALL WORDING CORRECTIONS, applied)
→ Codex adversarial leakage review (ACCEPT, no required corrections)
→ operator promotion (this artifact) + registry §N16 closure registration
→ next action: Issue #54 clean checkpoint (cross-before-design barrier) — a separate operator decision to schedule
```

## Promoted-artifact footer

This is a **promoted docs-only** tracked artifact — council-outcome closure. It records a readiness verdict; it opens nothing. It confers **no implementation authority, no Stage B opening, no database design, no schema / store / field / carrier / ID / fingerprint / allocator / serialization / enum / migration / storage-product selection, no runtime implementation, no authority enforcement, and no autonomy.** It amends no upstream contract and does not amend the recorded dependency graph. Issue #54 remains the cross-before-design barrier. Closure is registered in the Decision Registry §N16 by this promotion slice. Subsequent versions require their own trio/operator ratification.
