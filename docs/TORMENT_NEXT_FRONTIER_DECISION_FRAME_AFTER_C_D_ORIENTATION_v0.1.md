# TORMENT — Next-Frontier Decision Frame After C-D Orientation v0.1

## Status / purpose

**Docs-only / decision frame / NON-AUTHORIZING / no code / no tests / no smoke / no
implementation lane.** Codex decision: **PASS docs-only next-frontier decision frame.** This
frame renders one decision only — **which next frontier (a docs-only review direction) the
board should turn to, or whether to remain HOLD** — using the whole-board orientation as
**evidence, not implementation authority**. It selects exactly one option, opens no gate, and
authorizes nothing.

Anchored on `docs/TORMENT_WHOLE_BOARD_ORIENTATION_AFTER_C_D_OPERATOR_ORCHESTRATION_v0.1.md`
(HEAD `345bab1`). Manual C-D operator orchestration is **CLOSED / HOLD**.

## 1. Evidence basis (not authority)

The whole-board orientation is **evidence**. It established (source-verified at HEAD) that:
manual C-D is closed, the production orchestrator module is absent, the dormant non-Spine
runtime and the `memory_context_orchestrator` seam are called nowhere, `AgentRunner` is off
the live Spine path (`0×` in `app.py` / `spine.py`), and every larger lane sits at HOLD.

That orientation **selected nothing**. This frame selects only the **next docs-only review
direction**; it does **not** convert any evidence into implementation authority, and it does
**not** itself perform the selected work. Selecting a frontier here authorizes only a later,
**separately gated** slice in that direction.

## 2. Candidate fronts compared

| Front | Admissible now? | Dependencies / blockers | Risk / authority footprint |
|---|---|---|---|
| **Remain HOLD** | Always | None | None — but leaves a known correctness defect in the living map |
| **Memory-to-prompt ownership questions** | No (not mine to open) | Operator product/runtime fork (`3e4bc2d` Option D); *not source-derivable* | High — carries live-LLM-generation / model-boundary implementation pressure |
| **Gate A / B / D review** | Partly, but low-yield | Gate A already heavily characterized + awaiting wall-enforcement authorization; Gate B fenced (R-field rejected pending a cross-agent leak fix); Gate D blocked behind the Gate A wall **and** a carrier/substrate | Medium — re-treads recent frames; blocked on upstream authorizations |
| **Substrate readiness review** | Premature | Roadmap is deliberately **substrate-independent**; database/substrate (Stage B) is **deferred** by choice | Medium — pulls a deferred lane forward against the stated roadmap |
| **Stale-boundary cleanup** | **Yes** | **None** | **Lowest** — docs/map-wording hygiene only; no authority, no new surface |

## 3. Selected next frontier

**SELECTED: stale-boundary cleanup.**

The next frontier is a bounded, docs-only (plus, in its own later slice, possibly
guard-*wording*-only) **map-hygiene pass** that reconciles the known stale-on-face boundary
wording left behind by the C-D arc — primarily the older §0 "C-D PRE-IMPLEMENTATION GUARD"
bullet, which still asserts "no candidate module/harness exists" and lists
`memory_to_prompt_c_d_operator_orchestration_harness` among "forbidden/absent sentinels,"
both of which the landed manual harness + flipped guard have superseded. The cleanup
frontier's scope is to **find and reconcile such superseded "absent/forbidden" wording across
§0 and adjacent map/guard prose**, so the living navigation authority stops contradicting the
landed reality.

This frame **selects** that direction; it does **not** perform it. The cleanup itself is a
**separate, later, separately-gated slice**.

## 4. Why the selected frontier is admissible now

- **Zero dependencies.** It needs no operator product decision, no carrier/substrate, no
  Gate-A wall authorization, and no provider/runtime. Every other front is blocked on at
  least one of these.
- **Lowest risk / authority-neutral.** It touches only map/guard **wording**; it adds no
  production surface, no endpoint, no provider path, no gate. The tests that lock the C-D
  reality already pass (closure sanity check green).
- **It fixes a real defect in the authority surface.** §0 is the living work-order the trio
  navigates by; leaving it asserting "no harness exists / forbidden sentinel" for a harness
  that *does* exist is an active hazard (a reader could act on stale authority). Correctness
  of the map is a precondition for trustworthy future decisions.
- **It clears the board before any larger fork.** The big product fork (memory-to-prompt
  ownership) and the substrate lane deserve to be deliberated against a map that does not
  contradict itself. Cleaning first is the disciplined ordering.
- **Smallest bounded change.** It honors the established "audit-first, smallest bounded move,
  don't bundle" posture: a dedicated, narrowly-scoped hygiene slice, not a cleanup smuggled
  into a feature.

## 5. Why the non-selected fronts remain deferred or HOLD

- **Memory-to-prompt ownership questions — DEFERRED to the operator.** The orientation and
  `3e4bc2d` classify whether/where live LLM generation should exist (a separate non-Spine
  runtime vs a model boundary on the Spine) as an **operator product/runtime fork that is not
  source-derivable**. A docs frame cannot resolve it, and selecting it would apply
  implementation pressure toward live generation. It is the operator's to open, not this
  frame's to select.
- **Substrate readiness review — DEFERRED.** The followed roadmap is explicitly
  substrate-independent and defers database/substrate (Stage B). Pulling a substrate review
  forward now would contradict that deliberate deferral; it should wait until the operator
  turns toward substrate.
- **Gate A / B / D review — DEFERRED / HOLD.** Gate A's containment wall already has recent
  non-reachability / no-tag-dependence locks and an enforcement-path proposal; its next
  substantive move requires separate Codex/operator authorization, not another review. Gate B
  (writer-authority / R-field / Probe-v1) is fenced — the R-field is rejected pending a
  cross-agent leak fix. Gate D / Envelope-Audit / private-cognition / dream are **NO-OPEN**,
  blocked behind the Gate A wall and a carrier/substrate. A review now would be redundant or
  dependency-blocked.
- **Remain HOLD — not selected, but preserved everywhere else.** HOLD is the correct posture
  for every lane above; it is declined as the *board-wide* answer only because one concrete,
  admissible, low-risk correctness item exists. Selecting the bounded cleanup is strictly more
  useful than pure HOLD while remaining fully within the HOLD discipline for all other lanes.

## 6. This frame opens NOTHING

This frame opens, authorizes, and implies **no**: production integration; provider call;
smoke; memory write; endpoint / MCP / API / schema; AgentRunner / Terrain B wiring;
database / substrate implementation; private-cognition / dream runtime; output-control path;
hidden finalizer / refusal / identity rewrite; automatic provider path. It changes no
production code, no tests, and no runtime behavior. It is a decision frame plus a §0 pointer.

## 7. Status of the known stale §0 / pre-implementation wording

Because **cleanup is the selected frontier**, the known stale §0 / pre-implementation guard
wording is **registered as the concrete scope of the next (separately-gated) cleanup slice** —
*not* merely left as historical/superseded. Specifically targeted for that later slice:

- the older §0 "C-D operator-orchestration PRE-IMPLEMENTATION GUARD — LANDED" bullet, whose
  "no candidate module/harness exists" / "forbidden-absent sentinel (harness name)" wording is
  superseded by the landed manual harness and the flipped guard; and
- any adjacent map/guard prose that still implies the C-D manual surface is absent.

Until that slice lands, the "most-recent-wins" §0 rule governs: the newer C-D bullets
(manual harness LANDED; fake/real smoke receipts; whole-board orientation) are authoritative,
and the older guard bullet is read as a historical snapshot of commit `f4434c6`, not current
state. **This frame performs no cleanup edits** beyond filing itself and a compact §0 pointer.

## 8. What this is NOT

No new architecture gate. No implementation, provider, smoke, or test change. No selection of
any production lane. A docs-only decision frame that selects the **stale-boundary cleanup**
frontier and defers every other front, plus one compact §0 pointer.
