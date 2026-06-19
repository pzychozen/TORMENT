# TORMENT Gate B1 — H3 Bounded Writer-Authority Question Frame v0.1

**DOCS-ONLY REQUIREMENT FRAME — NO CODE, NO TESTS, NO WRITER FIX, NO ENDPOINT BEHAVIOR CHANGE, NO
PROMOTE REDESIGN, NO GOVERNANCE VEHICLE, NO DATABASE/SUBSTRATE, NO PHASE-7, NO H1, NO P4, NO SEED-GOV.**

This artifact frames the H3 (`POST /promote` force bypass) writer-authority question **at requirement
level only**. It names no remedy, no mechanism, and no governance vehicle, and it changes no behavior. It
builds on the Gate B1 first-subject selection (which named H3 **for tractability, not severity**) and the
Gate B decision frame. **H1 remains parked and is not de-risked.**

**Date:** 2026-06-19. **Baseline HEAD = origin/main = `cef0634`** (latest commit *docs(engine): select
Gate B1 H3 reconciliation subject*). Grounds on: the Gate B1 selection artifact
(`docs/TORMENT_GATE_B1_FIRST_WRITER_AUTHORITY_RECONCILIATION_SUBJECT_SELECTION_H3_v0.1.md`), the Gate B
hazard inventory §3 H3, the Gate B decision frame §3–§5, Document A
(`docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md`), and the pre-substrate
architecture framing.

> Memory may shape context. Memory may not seize authority.

---

## 1. Status and anti-drift banner

Requirement frame only. This is a **docs-only requirement frame**: it states *what the H3 question is*
and *what properties a governed crossing would have to satisfy*, and it stops there. It contains **no
code, no tests, no writer fix, no endpoint behavior change, no promote redesign, no governance-vehicle
selection, no database/substrate work, no Phase-7 work, no H1/`gravity_correction` work, no P4
mechanics, and no Seed-Governance mechanics.** Naming the H3 question neither opens it nor blesses any
remedy; H3 remains a parked non-conformance. H3 was **selected for tractability, not severity**; **H1
remains parked and is not de-risked**, and H1's sharper automatic-authority concern stands on the
record. Gate B remains the authority-boundary frame; Gate B1 is adjacent to it, not an amendment that
begins construction.

## 2. Scope

In scope: state the **bounded H3 authority question** at requirement level, record the settled H3 facts
it rests on, name the requirement-level question space (visibility / provenance / contestability /
bounded authority posture / scope-sequencing), and name the evidence categories any later design would
require.

Out of scope: every remedy, mechanism, vehicle, code, and test decision. This frame does not change
`/promote`, does not touch `force`, names no approval or authorization policy, names no governance
vehicle, designs no crossing, and changes no canon semantics. The full deferral list is §7 and the full
non-authorization list is §8.

## 3. Settled H3 facts

Carried from the Gate B hazard inventory §3 H3 and confirmed against current source at the baseline above
(narrow anchors only):

- **Source path.** `app.py::promote_chunk_endpoint` (`@app.post("/promote")`) → `promotion.py::promote_chunk`.
  The request model `PromoteReq` carries `force`, which **defaults `False`**.
- **Two-effect `force=True` behavior.** When a caller sets `force=True`, two distinct things currently
  happen — and this frame keeps them distinct:
  - **a. Evaluator pre-loading.** The handler passes `is_canon=bool(req.force)` and
    `user_approved=bool(req.force)` into `evaluate_promotion` — so `force=True` enters the evaluator
    already carrying `is_canon=True` **and** `user_approved=True`.
  - **b. Execution bypass.** The execution guard is `if result.promote or req.force:` — so the promotion
    proceeds even when the evaluator's own `result.promote` is `False`.
  - Stated together: `force=True` both *pre-loads the evaluator toward a canon/approved outcome* and
    *proceeds regardless of the evaluator's decision*. It is **not** only "force skips evaluation."
- **Resulting write shape.** `promote_chunk` writes a core memory with `mtype="identity"`, `canon=True`,
  and `extra_payload kind="canon_promotion"` — a core-identity, canon-asserting, identity-class write
  (on the authority-bearing side per Gate B decision frame §3).
- **Reachability.** H3 is **endpoint-driven, explicit, and caller-flag-scoped**: it is reached only
  through an explicit HTTP request to `POST /promote` carrying the `force` field. It is **not
  ordinary-ingest reachable** (it is not part of the `fabric.py::ingest()` post-store fan-out that
  carries the H1/H2/H4/H6 surfaces) and it is **not automatic** (nothing internal triggers it; it
  requires a caller).
- **Precision caveat.** H3 is legible **at the write site** (the anchors above). The **upstream
  `/promote` caller-auth surface is untraced / open** — Document A §11 records the `POST /promote`
  upstream auth surface as still untraced. This frame therefore makes **no assumption** about whether the
  caller is trusted, untrusted, operator-only, admin-only, public, safe, unsafe, or already governed.
  That surface is named as open evidence (§6), not assumed.

## 4. Exact bounded authority question

> **Should a caller-supplied `force=True` be able to assert a `canon=True`, identity-class memory while
> the endpoint's promotion-evaluation step is both *pre-loaded* (`is_canon=True`, `user_approved=True`)
> and *bypassed* (`if result.promote or req.force`) — and if such a crossing is to be permitted at all,
> what requirement-level properties must it satisfy to be a *governed* crossing rather than a
> *self-asserting* one?**

The question is posed; no answer is selected here. "Governed" carries the Gate B decision-frame §4
requirement sense — visible, provenance-bearing, contestable, and bounded in authority posture — as
requirements, not mechanisms.

## 5. Requirement-level question space

Each subsection is a **question** — "what would this need to mean for H3?" — not a directive. No option
is selected and no mechanism is designed.

### 5.1 Visibility question

What would **visibility** need to mean for H3? At requirement level: the question of whether a
`force=True` canon/identity crossing should be *observable as an authority-bearing crossing* rather than
silent, and — per Document A A-I1 — to whom such observability would default (operator / governance
audit, not caller- / model- / prompt-visible). This names a **record-only visibility question**; it
names no audit log, surface, or disclosure.

### 5.2 Provenance / accountability question

What would **provenance** need to mean for H3? The question of whether the resulting canon claim should
*carry where it came from and how it was produced* — that it arose via the `/promote` `force` route with
the evaluator pre-loaded and bypassed — and what caller / context lineage a requirement would call for.
This names a **provenance / accountability question**; it names no field, schema, or carrier.

### 5.3 Contestability question

What would **contestability** need to mean for H3? The question of whether a `force`-driven
canon/identity claim should remain *contestable in principle* rather than treated as unappealable —
carrying the Document A A-I3 sense that contest *constrains future authority outcomes* and does not
itself resolve, apply, admit, or promote (the resolver boundary stays parked). This names a
**contestability / routing question**; it names no resolver, vehicle, or workflow.

### 5.4 Bounded authority posture question

What would **bounded authority posture** need to mean for H3? The question of what default authority
posture a `force`-driven claim should hold — for example, whether it should default to non-authoritative
or characterization-only until a separately governed crossing (the Document A A-O2 / A-D2 posture), or
whether the present immediate-canon behavior is left recorded as a parked non-conformance pending a later
crossing. These are **posture words only**, not an implemented status. This names a **bounded authority
posture question**; it names no posture.

### 5.5 Scope / sequencing question

What would **scope and sequencing** need to mean for H3? The question — carried open from the Gate B
decision frame §8 — of whether the H3 reconciliation sits inside Gate B or an adjacent Gate B1 lane, how
much P4 read-side framing should precede any defined write-side crossing, and whether a governance
vehicle is determined here or deferred. This names a **scope / sequencing question**; it determines none
of these.

## 6. Evidence required before any later H3 design or code

These are **evidence categories**, not tasks that produce behavior. Any later H3 design would first
need:

- **Source anchors** — the write-site facts of §3, kept current against the then-HEAD.
- **Full `/promote` caller / auth surface** — who may call `POST /promote`, under what existing
  authentication / authorization, in the live deployment (currently untraced — Document A §11 `[OPEN]`).
- **Current deployment exposure assumptions** — how / whether `/promote` is reachable in the deployed
  configuration; recorded as assumptions, none presumed here.
- **Current logging / audit / provenance facts** — what, if anything, is already observable about a
  `force` promotion today (recorded as fact, not as a named surface).
- **Exact write shape** — the precise `mtype` / `canon` / `tier` / half-life / payload written,
  confirmed at the then-HEAD.
- **Evaluator-versus-`force` behavior** — the precise relationship between `evaluate_promotion`'s
  decision and the `or req.force` guard (the two-effect shape of §3).
- **Existing docs / contract constraints** — the Document A obligations (A-O1 / A-O2 / A-O5), the Gate B
  decision-frame requirements (§3–§5), and the standing doctrine that would bind any later crossing.
- **Unknowns explicitly marked not determined** — anything not establishable read-only (e.g. observed
  frequency or prior force-promotion artifacts) is recorded as *not determined*, not assumed.

The construction-entry proof bar (Gate B decision frame §7) — applicable Registry §K evidence,
requirement-to-carrier traceability, a fresh clean checkpoint, and operator hand-back — remains later
and unchanged. No construction-entry follows from this frame.

## 7. What remains explicitly deferred

This frame opens none of the following; each is a separate, later, explicitly authorized step:

- any remedy; any code; any tests;
- any `/promote` endpoint behavior;
- any approval / authorization policy selection;
- any governance-vehicle determination, **including Cluster 2 v0.2**;
- any canon-semantics change;
- any H1 / `gravity_correction` work;
- any Phase-7 work;
- any database / substrate;
- any P4 / source-sameness mechanics;
- any Seed-Governance mechanics;
- any Document B / dream / incubation runtime;
- any candidate store;
- any durable private state.

## 8. Explicit non-authorizations

No implementation. No code. No tests. No writer fix. No promote redesign. No endpoint behavior change.
No disabling/changing `force`. No approval/auth policy selection. No governance-vehicle selection. No
canon-semantics change. No registry amendment. No H1/`gravity_correction` work. No Phase-7 work. No
database/substrate. No schema/storage/carriers/migration. No P4/source-sameness mechanics. No Seed-Gov
mechanics. No Document B runtime. No dream/incubation runtime. No candidate store. No durable private
state. No hidden finalizer, output blocker, identity pinning, monitoring/autonomy layer, durable
user-risk scoring, or coercive mechanism.

Guidance, not coercion: this frame makes the H3 question *answerable* for a later governed decision and
introduces no hidden or coercive mechanism.

## 9. Codex / operator review note

This is a **draft** requirement frame. It requires **Codex artifact review and operator review before
promotion**, and before any subsequent H3-specific design or authorization is drafted. **The orientation
map is not updated until after that artifact review and any corrections.** Selection and framing at this
layer are authority-relevant — they concern a real canon/identity writer — so they follow the
established Gate B / Gate B1 practice of an independent adversarial pass plus operator ratification. No
H3 design is auto-opened.

---

## Anti-drift footer

REQUIREMENT FRAME ONLY — no code, no tests, no writer fix, no promote redesign, no endpoint behavior
change, no disabling/changing of `force`, no approval/auth policy, no governance vehicle (incl. Cluster 2
v0.2), no canon-semantics change, no registry amendment, no H1/`gravity_correction` work, no Phase-7
work, no database/substrate, no schema/storage/carriers/migration, no P4/source-sameness, no Seed-Gov
mechanics, no Document B / dream / incubation runtime, no candidate store, no durable private state. H3
was **selected for tractability, not severity**; **H1 remains parked and is not de-risked**, its sharper
automatic-authority concern standing on the record. The `force=True` shape is two-effect (evaluator
pre-loading **and** execution bypass), not "force skips evaluation"; the upstream `/promote` caller-auth
surface is untraced / open, and no caller trust posture is assumed. Naming the H3 question opens nothing.
Audit observes authority and does not become authority. Memory may shape context. Memory may not seize
authority. Database / substrate remains last. Any subsequent Gate B / Gate B1 decision remains a separate
authorization.
