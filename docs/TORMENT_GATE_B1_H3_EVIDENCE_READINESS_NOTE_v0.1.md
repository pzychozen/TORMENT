# TORMENT Gate B1 — H3 Evidence-Readiness Note v0.1

**DOCS-ONLY EVIDENCE-READINESS NOTE — NO CODE, NO TESTS, NO ENDPOINT CHANGE, NO WRITER FIX, NO PROMOTE
REDESIGN, NO AUTH-POLICY SELECTION, NO GOVERNANCE VEHICLE, NO H1, NO PHASE-7, NO DATABASE/SUBSTRATE.**

This note records HEAD-specific H3 evidence categories — satisfied vs not determined — ahead of any later
H3 target-specific design. It is **evidence-readiness only**: not a next action, not a remedy, not a
mechanism, and not implementation. It exists because the H3 caller/auth split is **load-bearing
evidence** for any later H3 design; it is **not a paper conveyor belt toward implementation**.

**Date:** 2026-06-19. **Baseline HEAD = origin/main = `a91b79a`** (latest commit *docs(engine): frame
Gate B1 H3 authority question*). Grounds on the Gate B1 H3 bounded question frame
(`docs/TORMENT_GATE_B1_H3_BOUNDED_WRITER_AUTHORITY_QUESTION_FRAME_v0.1.md`), the Gate B hazard inventory
§3 H3, the Gate B decision frame, and Document A. The source facts below are from a narrow read-only pass
over `app.py` (`/promote`) and `promotion.py` (`promote_chunk` / `evaluate_promotion`).

> Memory may shape context. Memory may not seize authority.

## 1. Status and anti-drift banner

Evidence-readiness only. This note records *what evidence is already established read-only* and *what
remains not determined*, so a later, separately authorized H3 design has a concrete evidence record to
start from. It **authorizes no remedy, policy, mechanism, code, tests, endpoint change, or
implementation**, and it draws **no severity or exposure conclusion**. Recording an evidence category as
satisfied or not determined neither opens H3 nor blesses any action. H3 remains **selected for
tractability, not severity**; **H1 remains parked and is not de-risked**. Database / substrate remains
last.

## 2. Scope

In scope: a HEAD-specific evidence record for H3 across seven categories (source anchors; two-effect
`force=True`; in-repo application-layer auth finding; deployment exposure; logging/audit/provenance
facts; exact write shape; observed frequency/artifacts), each marked **satisfied** or **not determined**,
with the source facts that support each.

Out of scope: any remedy, policy, mechanism, vehicle, code, test, or design decision. This note changes
nothing, requires nothing, and selects nothing. The full non-authorization list is §10.

## 3. Evidence categories — satisfied vs not determined

| # | Category | Status |
|---|---|---|
| 1 | Source anchors | **Satisfied** (read-only, this HEAD) |
| 2 | Two-effect `force=True` | **Satisfied** |
| 3 | In-repo FastAPI application-layer auth finding | **Satisfied** (surveyed-source evidence) |
| 4 | Deployment / network exposure | **Not determined** (not repo-determinable) |
| 5 | Logging / audit / provenance facts | **Satisfied for in-repo facts**; external audit infrastructure **not determined** |
| 6 | Exact write shape | **Satisfied** (source-verified) |
| 7 | Observed force-promotion frequency / artifacts | **Not determined read-only** |

Detail for each follows in §4–§9.

## 4. Source anchors and two-effect `force=True` shape

**Source anchors (this HEAD).** `app.py::promote_chunk_endpoint` (`@app.post("/promote")`) →
`promotion.py::promote_chunk`. `PromoteReq` carries `force`, defaulting `False`.

**Two-effect `force=True` (kept separate):**

- **a. Evaluator pre-loading.** The handler passes `is_canon=bool(req.force)` and
  `user_approved=bool(req.force)` into `evaluate_promotion` — so `force=True` enters the evaluator
  already carrying `is_canon=True` **and** `user_approved=True`.
- **b. Execution bypass.** The execution guard is `if result.promote or req.force:` — so the promotion
  proceeds even when the evaluator's own `result.promote` is `False`.

These two effects are distinct and are recorded distinctly; this is not "force skips evaluation."

## 5. In-repo FastAPI application-layer auth finding

**No in-repo FastAPI application-layer authentication or authorization wiring was found on `/promote` in
the surveyed source at this HEAD.** The `promote_chunk_endpoint` signature takes only the request body
(no endpoint dependency or security parameter); the surveyed `app.py` shows the application constructed
as a bare `FastAPI(...)` with no application-wide auth dependency, security scheme, or middleware found
in the pass; and no separate server-entrypoint / ASGI-wrapper module was found in the surveyed source.

This is **surveyed-source evidence only** — a narrow statement about what the in-repo application surface
contains at this HEAD. It draws **no** global authentication/authorization conclusion and **no** exposure
conclusion; reachability is governed by deployment (§6), which this pass does not determine.

## 6. Deployment / network exposure unknown

**Deployment/network exposure is not repo-determinable from this evidence pass. Reverse proxies,
gateways, network ACLs, bind host/port, and operator deployment controls are outside the surveyed in-repo
application surface and remain operator-supplied / not determined here.** No claim is made or implied
about whether the endpoint is reachable, by whom, or under what controls in any deployment.

## 7. Logging / audit / provenance facts

Recorded as what is present or not found in the surveyed source — no log, audit, provenance, field,
carrier, or mechanism is required by this note:

- **Present (in-repo).** On a successful promotion, `promote_chunk` emits an application info-level log
  line (`"Promoted chunk … → core eid=…"`, with a sanitized chunk id); on failure it emits a
  warning-level line. The written node carries provenance fields in its payload: `kind="canon_promotion"`,
  `source_ref` (original `doc_id` / `chunk_id`), a `promoted_at` UTC timestamp, and
  `user_id="promotion_system"` (the write is attributed to a system actor, not to the caller).
- **Observed limitation (neutral fact, no requirement implied).** The promotion log line and the written
  row's provenance fields, as surveyed, do **not** distinguish a `force`-route promotion from an
  evaluator-approved one — the `force` flag is not propagated into the row payload or the log line in the
  surveyed handler. This is recorded as a source fact only; it implies no obligation.
- **Not determined.** Whether any external audit infrastructure observes promotions, and any
  retention/observability outside the surveyed source, are not determined here.

## 8. Exact write shape

Source-verified in this bounded pass (`promotion.py::promote_chunk`):

- `mtype="identity"`;
- `canon=True` (set both in the node payload and as the `spawn_memory` argument);
- `extra_payload kind="canon_promotion"`;
- `tier="core_identity"`, `memory_class="core"` — a **core-identity shape**;
- `half_life_days=3650.0` (decade half-life), `strength=0.90`, `confidence=0.85`;
- `source_ref` preserved (`doc_id` / `chunk_id`) and a `promoted_at` timestamp.

## 9. Observed force-promotion frequency / artifacts

**Not determined read-only.** No pre-existing promotion artifacts or workspaces were inspected in this
pass; observed frequency of `force`-route promotions is therefore not established. This is recorded as
*not determined* — **no inference of zero** is made.

## 10. Explicit non-authorizations

No endpoint change. No tests. No auth-policy selection. No governance vehicle. No H1/`gravity_correction`
work. No Phase-7 work. No database/substrate. No writer fix. No promote redesign. No canon-semantics
change. No P4/source-sameness mechanics. No Seed-Gov mechanics. No Document B/dream/incubation runtime.
No candidate store. No durable private state. No registry amendment. No hidden finalizer, output blocker,
identity pinning, monitoring/autonomy layer, durable user-risk scoring, or coercive mechanism.

Guidance, not coercion: this note makes H3 evidence legible for a later governed decision and introduces
no mechanism.

## 11. Codex / operator review note

This is a **draft** evidence-readiness note. It requires **Codex artifact review and operator review
before promotion**, and before any subsequent H3-specific design or authorization. **The orientation map
is not updated until after that artifact review and any corrections.** It records evidence only; it must
not be read as a step toward implementation. No H3 design is auto-opened.

## 12. Anti-drift footer

EVIDENCE-READINESS ONLY — no code, no tests, no endpoint change, no writer fix, no promote redesign, no
auth-policy selection, no governance vehicle, no canon-semantics change, no H1/`gravity_correction` work,
no Phase-7 work, no P4/source-sameness, no Seed-Gov mechanics, no Document B/dream/incubation runtime, no
candidate store, no durable private state, no database/substrate, no registry amendment. The in-repo
application-layer finding is **surveyed-source evidence only** and draws no exposure conclusion;
deployment/network exposure is **not repo-determinable** and remains operator-supplied / not determined.
The `force=True` shape is two-effect (evaluator pre-loading **and** execution bypass). H3 remains
**selected for tractability, not severity**; **H1 remains parked and is not de-risked**. Naming evidence
opens nothing. Audit observes authority and does not become authority. Memory may shape context. Memory
may not seize authority. Database / substrate remains last. Any subsequent Gate B / Gate B1 decision
remains a separate authorization.
