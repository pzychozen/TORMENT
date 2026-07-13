# TORMENT — Rest-State Integrity Verification Receipt v0.1

## §0 Header

- **Version:** v0.1
- **Date:** 2026-07-13
- **Edge at verification time:** `094d106` docs(project): point to caller ownership boundary
- **Status:** docs-only / **EVIDENCE RECEIPT, NOT AUTHORIZATION** / records a chat-only, read-only verification / non-authorizing / no-lane-opened / no-fix-proposed / no-next-step-selected
- **Posture:** FORMAL HOLD active; Mode 0 active

## §1 Non-authorization block

**Non-authorizing; receipt, not authorization.** This document records that a chat-only, read-only integrity verification of the standing rest-state locks was performed at `094d106`, and preserves its findings across chats. It authorizes nothing: it does not fix H3, does not open or reopen Gate B (NO-OPEN/HOLD stands, H1–H6 unfixed), does not decide retire-vs-constrain, does not bless, repair, constrain, retire, or redesign `/promote` `force=True`, does not select, shortlist, compare, or design a memory-to-prompt caller, does not open memory-to-prompt wiring, provider/runtime, any live surface, or any MCP/action/movement lane, creates no M3 ripeness (direction is not trajectory; verification existence is not momentum), and does not reopen carrier, Stage-B, database/substrate, Gate A/D, admission, promotion, crossing, Dream/private cognition, autonomy, Brainvision, audio, or Unreal/model-body movement. It changes no code and no tests. A verified rest state is still a rest state: **that the locks hold is evidence the board may keep resting, not evidence anything is ready.** Evidence is not authorization; readiness is not ripeness. This receipt may be cited later as evidence only if a future standalone Hilmir-authorized step explicitly permits that use. FORMAL HOLD and Mode 0 remain active; this document opens no lane and owes no successor.

## §2 What was verified, and how

Chat-only, read-only method: all repo evidence was read from the git object database pinned at `094d106` (`git show <commit>:<path>`, `git grep <pattern> <commit>`, `git log <commit> -- <path>`), with no test execution, no index-writing git commands, and no reliance on the sandbox working-tree mount; two Windows-side read-only file reads were used solely to adjudicate a mount artifact (§3-E). No production import, no network, no data.

## §3 Findings

- **A. `b107b0a` approved-caller fence — STILL TRUTHFUL.** The lock's test file has no post-lock edits at `094d106`. Replicated scan: `run_turn(...)` production call sites are exactly the runner's reflex self-call (memory-blind keywords), the approved selected-items bridge (no `memory_context_text`), and the dormant orchestrator — the sole `memory_context_text` supplier. No opaque `**kwargs` expansion into `run_turn`; no production module besides the orchestrator references `memory_context_orchestrator` or `run_turn_with_memory_context`.
- **B. `8c92280` live-owner inventory snapshot — STILL TRUTHFUL.** All six tracked owner-relevant call sites match the pinned snapshot exactly, including the `complete()` model-completion trio (`agent_loop.py`, the unwired private generation owner, the dormant non-Spine LLM runtime) and the admissibility condition that `non_spine_llm_runtime` is imported or referenced by no production module. No alias imports or rebindings of any guarded name were found.
- **C. `6a4da8f` force-promotion bypass inventory — STILL TRUTHFUL.** `promote_chunk` called only from `app.py`; `evaluate_promotion` only from `app.py` and `promotion.py`; binders limited to those two; sole `force` field owner remains `app.py::PromoteReq`; no truthy literal reaches `is_canon`/`user_approved` (both derive from `bool(req.force)` at the endpoint; `promotion.py` passes the permitted falsy `user_approved=False`); no opaque `**kwargs` at either promotion call site; the bypass guard remains exactly `if result.promote or req.force:` with both force-provenance keys present and deriving from the real values. **The bypass exists exactly as parked — diagnosed, unmodified, unblessed.**
- **D. §0 rest-state summary — TRUTHFUL.** At `094d106`, §0 and the governing artifacts agree: H3/Gate B resting on the three evidence artifacts (`277fc94`, `f773bae`, `3bc1427`); `/promote force=True` diagnosed as what IS, not what MUST BE; retire-vs-constrain undecided and reserved for a standalone Hilmir record; caller ownership framed (`a8c6a71`), not answered; no caller owner selected; no memory-to-prompt wiring open; M3 direction-not-trajectory (`f2e2931`); FORMAL HOLD and Mode 0 active; no implementation lane open. §0-HEAD naming `a8c6a71` while the git edge is `094d106` is the expected two-step pointer pattern, not drift.
- **E. Observations, describe-only, no action owed.** (1) A sandbox-mount worktree-vs-HEAD diff (−4270 lines / 15 files) was adjudicated as the known mount-read artifact: Windows-side reads show the affected files intact at exactly their committed lengths. Windows remains the source of truth; not drift. (2) §0's tail line "**Date of last refresh:** 2026-06-13" may be stale relative to the 2026-07-13 content above it, or may describe only the historical log below §0; recorded as an ambiguous observation, no fix proposed.

## §4 What this receipt must not become

Not an authorization for H3/Gate B movement, a retire-vs-constrain decision, any `/promote force=True` change, caller selection or design, memory-to-prompt wiring, provider/runtime selection, live-surface or M3 movement, MCP/action/movement opening, carrier or Stage-B reopening, or any implementation; not a template obligating recurring verifications; not a claim that the working tree is clean beyond what §3-E states; not citable as momentum. Any artifact treating it as one of these may not cite it.

## §5 Codex review prompt

```text
Please review docs/TORMENT_REST_STATE_INTEGRITY_VERIFICATION_RECEIPT_v0.1.md
(new, docs-only, untracked; over edge "094d106 docs(project): point to caller ownership boundary").

Verify that this receipt:
- is docs-only, EVIDENCE-RECEIPT-NOT-AUTHORIZATION: no code, no tests, no §0 edit, no fix proposal,
  no next step selected, no lane opened, no successor owed;
- records the chat-only read-only method (object-DB reads pinned at 094d106; no test execution;
  Windows-side reads only to adjudicate the mount artifact);
- reports the three locks (b107b0a / 8c92280 / 6a4da8f) as still truthful and §0's rest-state
  summary as truthful, with the force bypass explicitly diagnosed-not-blessed and unmodified;
- keeps both observations (mount artifact; §0 refresh-date ambiguity) describe-only;
- preserves FORMAL HOLD and Mode 0 and ends with the required closing state block.

Flag any authorization language, any lean on retire-vs-constrain or caller ownership, any ripeness
or momentum language, any implied obligation of future verifications, or any lane opened.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

## §6 Closing state block

Any consequential next step — an H3 fix, the retire-vs-constrain fork, caller-owner selection, wiring, any live-surface gate chain — requires separate explicit Hilmir authorization plus a Codex challenge; none is owed, scheduled, started, or presumed by this receipt. Whether and when to commit this receipt, and whether to add the separate §0 pointer afterward per the two-step workflow, remain at operator discretion; neither is owed.

```text
verification_performed = chat_only_read_only (2026-07-13, at 094d106)
locks_verified_truthful = 3_of_3 (b107b0a, 8c92280, 6a4da8f)
section0_rest_state = truthful
drift_found = None
code_modified = False
tests_modified = False
H3_fixed = False
Gate_B_opened = False
force_true_blessed = False
retire_vs_constrain_decided = False
caller_owner_selected = False
caller_designed = False
memory_to_prompt_wired = False
provider_runtime_selected = False
live_surface_opened = False
M3_ripeness_created = False
MCP_action_opened = False
movement_opened = False
carrier_selected = False
implementation_opened = False
follow_on_artifact_owed = False
verdict = HOLD
FORMAL_HOLD = active
Mode_0 = active
lanes_opened = None
```

*End — TORMENT Rest-State Integrity Verification Receipt v0.1. Docs-only; evidence receipt, not authorization; chat-only read-only verification recorded at `094d106`; three locks truthful; §0 truthful; force bypass exactly as parked — diagnosed, unmodified, unblessed; two observations describe-only; no lane opened; no successor owed. A verified rest state is still a rest state. FORMAL HOLD and Mode 0 remain active.*
