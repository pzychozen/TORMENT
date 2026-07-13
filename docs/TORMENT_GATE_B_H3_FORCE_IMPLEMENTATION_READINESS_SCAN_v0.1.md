# TORMENT — Gate B / H3 Force Implementation-Readiness Scan v0.1

## §0 Header

- **Version:** v0.1
- **Date:** 2026-07-13
- **Edge at scan time:** `56ee884` docs(project): point to force consequence scan
- **Status:** docs-only / **IMPLEMENTATION-READINESS, NOT IMPLEMENTATION** / source-grounded / non-authorizing / no patch / no tests / no fix proposal / no fork decision / requirement-level only
- **Posture:** FORMAL HOLD active; Mode 0 active

## §1 Non-authorization block

**Non-authorizing; implementation-readiness, not implementation.** This scan records what exists so that a future, separately authorized decision could be well-informed. It fixes nothing: it does not fix H3, does not open Gate B (NO-OPEN/HOLD stands, H1–H6 unfixed), and does not bless, repair, normalize, modify, or operationalize `/promote force=True` — **describing the current wiring is not approval of it**. It does not decide, recommend, or lean on retire-vs-constrain. It proposes no fix shape, designs no force-mark representation, and selects no carrier, schema, record class, field, ID scheme, API, storage shape, seam, or architecture. It adds or modifies no code and no tests. It opens no admission, promotion, crossing, Stage-B, database/substrate, Gate A/D, provider/runtime, memory-to-prompt, live-surface, MCP/action, movement, Brainvision, audio, Dream/private-cognition, autonomy, or implementation lane. Eligibility ≠ authorization; study ≠ implementation; direction ≠ trajectory; standing status ≠ momentum; presence confers nothing; evidence is not authorization; readiness is not ripeness. Any future fix or retirement requires the retire-vs-constrain fork decided by standalone Hilmir record, Gate B separately reopened, and its own Codex-challenged proposal. FORMAL HOLD and Mode 0 remain active; this document opens no lane and owes no successor.

## §2 The central question

> **If Hilmir ever separately authorized an H3 fix or retirement later, what existing code surfaces, tests, and doctrine gates would need to be understood first?**

Asked once. Answered as inventory only.

## §3 Current closed state at `56ee884`

H3 boundary study recorded (`277fc94`); retire-vs-constrain consequence scan recorded (`f773bae`); the fork undecided and reserved for a standalone Hilmir record; Gate B NO-OPEN/HOLD; H1–H6 unfixed; carrier lane resting (`cf41f2c`); model-boundary M3 direction-not-trajectory (`f2e2931`); implementation, provider/runtime, memory-to-prompt wiring, live-surface, MCP/action/movement, Brainvision/audio lanes all closed; FORMAL HOLD and Mode 0 active.

## §4 What the boundary study and consequence scan established

The floor/transmissibility line (**force may change what exists; it may never change what what-exists is worth**); four invariants (attributable-without-privileging; no self-laundering; audit-visible, cognition-inert; downward contestability); eleven non-inheritance surfaces; the memory/action seal in both directions; the pre-binding of any future M3 live surface (may never issue, invoke, request, or perceive force); and, from the consequence scan, that the operator-only floor is untouched and all surfaces stay closed under BOTH future answers, with the shared invariants surviving either.

## §5 What they did not establish

Whether force should exist (fork undecided); any fix or removal shape; any enforcement — **the invariants are paper requirements binding future artifacts; no consumer today checks any of them**; any mark representation (carrier-adjacent, deferred with the resting lane); any change to the live `/promote` path, which behaves today exactly as it did before either artifact existed.

## §6 Source-grounded force-path shape (verified at `56ee884`)

Location: `torment_service/app.py`, delegating to `torment_service/promotion.py`.

- `PromoteReq.force: bool = False` — app.py line ~1783, source comment: *"skip evaluation, force promote."*
- Consumed by `promote_chunk_endpoint` (app.py ~1787), which delegates to `promotion.promote_chunk` (promotion.py ~242).
- Wiring, the doctrinally significant part:
  - `is_canon=bool(req.force)` (~1842) — force **directly elevates authority tier**;
  - `user_approved=bool(req.force)` (~1846) — force **fabricates an approval signal it did not receive**;
  - `if result.promote or req.force:` (~1851) — force **overrides a declining evaluator**;
  - `"promotion_force_requested": bool(req.force)` (~1868) — the **only mark**, a single audit-payload field.

Line numbers are approximate anchors for a future reader; the identifier-level facts are the load-bearing inventory.

## §7 Boundary comparison — current code vs. the four H3 invariants

Measured against the boundary study, today's path violates all four invariants at once, which is precisely why H3 is a hazard:

- **Mark-becomes-rank, realized:** the effect of force *is* rank — `is_canon=True` is a first-class consumer input, so the "mark" and the "rank" are the same act.
- **Force-becomes-approval (self-laundering, realized):** `user_approved=bool(req.force)` makes the forced row look ordinarily approved to every downstream reader; the bypass launders itself in one assignment.
- **Authentication-substitute failure mode, live in code:** force currently *satisfies* an approval requirement it did not meet — the exact failure mode the boundary study named hypothetically exists as present behavior.
- **Audit breadcrumb insufficient as non-inheritance:** `promotion_force_requested` exists only in one audit payload; it is not durable on the row, not consumer-visible as a non-rank diagnostic, and strippable by anything that drops the audit dict — it satisfies neither attributable-without-privileging nor no-self-laundering.

This comparison is diagnostic, not a fix specification.

## §8 Existing tests and docs constraining this terrain

**Tests (all characterization/terrain locks — they pin what IS, deliberately, not what MUST BE):** `tests/test_gate_b_force_promotion_bypass_inventory.py` (`6a4da8f` — snapshot-locks the force surfaces; maps `promotion_force_requested → ("req","force")`; scans for any class declaring a `force` field); `tests/test_promote_force_bypass_endpoint_wiring.py` (pins the live wiring exactly as §6: force=True → `is_canon=True` + `user_approved=True`; reaches `promote_chunk` even when the evaluator declines; no approval/governance object required); `tests/test_gate_a_seam_c_writer_authority_ao2_characterization.py` (AST characterization of promote/force as Seam C writer-authority terrain); `tests/test_gate_a_tests_only_locks_c1_c5.py` (promote-path stubs inside the C1–C5 containment locks).

**Docs:** the Gate B writer-authority hazard inventory (H1–H6); the Q3 floor-binding and Q5 Gate-B-relation frames (crossing-confers-no-writer-authority; H3 non-inheritance); the H3 boundary study (`277fc94`); the retire-vs-constrain consequence scan (`f773bae`); the Document A §14 operator-only floor decision (`62400c9`); the Seam C entry of the Gate A wall enforcement-path proposal (`b84191b`).

## §9 H1–H6 relevance to H3 (per the hazard inventory)

- **H3 — direct:** `POST /promote` force bypass; this scan's subject.
- **H1 — structurally adjacent:** `gravity_correction` automatic `canon=True` — the *other* door that mints canon without a governed crossing; any H3-only action leaves the hazard class half-addressed.
- **H2 — structurally adjacent:** `_maybe_emit_identity_anchor` derived identity-family writer; the inventory itself notes H2 and H3 touch identity-family memory "by different doors."
- **H6 — downstream travel:** ordinary-ingest fan-out eligibility bounds where forced rows go after entry.
- **H4/H5 — peripheral:** H4 is topology-only; H5 has no production service binding found.

## §10 The doctrine-vs-enforcement gap

Doctrine (the boundary study) says marks must never become rank. Code currently makes force mint canon and fabricate approval in two assignments. The existing tests **characterize current behavior** — they are terrain locks that would fail on unauthorized drift, not requirements on future behavior. **No consumer anywhere enforces the four H3 invariants today.** The gap is complete, known, named, and intentional pending the fork; recording it is not an instruction to close it.

## §11 What any future authorized proposal would need to prove before implementation

All of the following, in order, each separately gated: the **retire-vs-constrain fork decided first** by standalone Hilmir record (a fix presupposes constrain; a removal presupposes retire); **Gate B separately reopened**; then, tests-first under Codex challenge: **no `is_canon` minted from force** (if constrained); **no fabricated `user_approved`** under any answer; **any surviving mark durable and non-strippable without being rank**; **no consumer may read force status as rank, route, weight, salience, confidence, authentication, or any cognition input**; **H1/H2 interaction accounted for** (pressure must not silently route through the other canon-minting doors); the `6a4da8f` and endpoint-wiring **terrain snapshots re-locked to the new terrain if and only if that change is authorized**; **Q2/Q3-shaped evidence** for any surviving override act (crossing-scoped, fresh, evidenced, contestable, revocable-before); and the **full suite green on Windows** (Windows is the source of truth). None of this is scheduled or owed.

## §12 What this scan must not become

Not a fix proposal; not a patch plan; not a test plan; not a fork decision; **not a blessing of current behavior** (the §6–§7 description is diagnosis, not acceptance); not a carrier/schema/record design; not a Gate B opening; not implementation authorization. Any artifact treating it as one of these may not cite it.

## §13 Posture note — no next step selected

This readiness scan does not select a next step. It creates no ripeness, owes no successor, and does not make a future fork frame, fork decision, further orientation, route-away, code change, test change, Gate B reopening, or H3 action more likely, more proper, or more authorized.

The available future directions remain separately Hilmir-authorized only, including:

- remain HOLD;
- prepare a future retire-vs-constrain fork frame;
- do more H3 orientation;
- route away from H3/Gate B;
- take no further action.

This scan may be cited later as evidence only if a future standalone Hilmir-authorized step explicitly permits that use. Evidence is not authorization. Readiness is not ripeness. Scan existence is not momentum.

## §14 Closing state block

```text
implementation_readiness_only = True
H3_fixed = False
Gate_B_opened = False
force_true_blessed = False
retire_vs_constrain_decided = False
carrier_selected = False
schema_selected = False
tests_modified = False
code_modified = False
implementation_opened = False
verdict = HOLD
FORMAL_HOLD = active
Mode_0 = active
lanes_opened = None
```

## §15 Codex review prompt

```text
Please review docs/TORMENT_GATE_B_H3_FORCE_IMPLEMENTATION_READINESS_SCAN_v0.1.md
(new, docs-only, untracked; over edge "56ee884 docs(project): point to force consequence scan").

Verify that this scan:
- is docs-only, IMPLEMENTATION-READINESS-NOT-IMPLEMENTATION, source-grounded, non-authorizing: no code, no tests,
  no patch, no fix proposal, no mark-representation design, no carrier/schema/record/field/ID/API/seam selection,
  no existing-file edits, no §0 pointer, no tags;
- describes the current /promote force wiring accurately (PromoteReq.force default False; promote_chunk_endpoint →
  promotion.promote_chunk; is_canon=bool(req.force); user_approved=bool(req.force); "result.promote or req.force";
  promotion_force_requested audit field) WITHOUT blessing, normalizing, or operationalizing it;
- maps current behavior against the four H3 invariants as diagnosis only (mark-becomes-rank realized;
  force-becomes-approval/self-laundering realized; authentication-substitute live; audit breadcrumb insufficient);
- inventories the constraining tests as characterization locks (what IS, not what MUST BE) and the constraining docs;
- states H1/H2 adjacency, H6 downstream relevance, H4/H5 peripherality per the hazard inventory;
- states the doctrine-vs-enforcement gap as known/named/intentional-pending-the-fork, with no instruction to close it;
- lists the future proof obligations behind their gates (fork first, Gate B reopening, tests-first invariant proofs,
  H1/H2 interaction, snapshot re-locks only-if-authorized, Q2/Q3 evidence, Windows-green) with nothing scheduled;
- decides and recommends nothing on retire-vs-constrain; keeps §13 as a non-recommending posture note (no next step
  selected, no ripeness, no evidence-completeness claim, no ranking); ends with the required closing state block.

Flag any fix shape, patch/test planning, fork lean, blessing of current behavior, mark design, lane opening,
or ripeness language (readiness is not ripeness).
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

*End — TORMENT Gate B / H3 Force Implementation-Readiness Scan v0.1. Docs-only; readiness, not implementation; source-grounded diagnosis of the live force path (canon minting, approval fabrication, evaluator override, single-breadcrumb mark) against the four H3 invariants; constraining tests and docs inventoried; H1/H2 adjacency named; doctrine-vs-enforcement gap recorded as intentional pending the fork; future proof obligations listed behind their gates. Nothing fixed, blessed, decided, proposed, designed, scheduled, opened, or owed. H3 unfixed; Gate B NO-OPEN; retire-vs-constrain reserved for a standalone Hilmir record. FORMAL HOLD and Mode 0 remain active.*
