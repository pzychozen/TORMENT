What Claude needs from us

Not prose.
A build spec with:

goal
scope
invariants
module boundaries
data contracts
endpoint behavior
acceptance tests
non-goals

That gives you a clean handoff and stops “helpful improvisation.”

Recommended next deliverable

We should produce a TORMENT Agent Spine Spec v0.1.

Not the whole future system.
Just the first implementable slice:

Phase 1 target

A governed cognition pipeline that can do:

route a task
spawn bounded internal roles
reintegrate outputs
run drift/governance checks
decide memory effects through archivist gating

That is enough to prove the architecture.

The actual build plan
1. Objective

Implement a memory-governed multi-role cognition layer on top of TORMENT.

This layer must treat agents as bounded role-executors, not as autonomous free-writing personas.

2. First milestone

One request enters the system and returns:

final answer
routing decision
per-role outputs
skeptic findings
archivist memory proposals
drift report
approved memory effects

That is the first serious demo.

3. Hard invariants

These should be explicit in the spec.

Invariant A — durable memory writes are gated

Only the archivist path may propose durable memory writes.
Nothing else writes directly.

Invariant B — provenance is mandatory

Every role output and every memory proposal must carry provenance.

Invariant C — disagreement is preservable

Reintegration must support unresolved contradiction instead of flattening everything.

Invariant D — aperture is bounded

Roles only see the memory slice granted by the router.

Invariant E — identity-sensitive flows trigger drift checks

Protected or identity-relevant tasks must run through drift logic before durable updates.

Invariant F — collective memory is not freely mutable

Shared memory is read-only unless a specific governance path allows promotion.

These are the bones. Claude should not be allowed to “simplify” them away.

4. First implementation scope

Keep it narrow.

In scope
task packet schema
routing decision schema
role output schema
memory proposal schema
provenance schema
drift report schema
deterministic router
aperture builder
role base class
first 4 roles
reintegration membrane
archivist gate
single orchestration endpoint
Out of scope
autonomous loops
background planning
tool-using swarms
emotional persona engine
self-modifying policy logic
cross-workspace write federation
learned router

That keeps the first patch real.

5. Roles for v0.1

Do not start with six or eight.
Start with four.

Interpreter

Normalizes task intent and suggests route.

Engineer

Produces implementation-ready plan or action structure.

Skeptic

Flags weak reasoning, contradiction, contamination, and overreach.

Archivist

Evaluates memory effects and durable write proposals.

Coordinator can be a simple composition function first, not a full separate role yet.

That reduces complexity without losing the architecture.

6. Files Claude should build first

This is the clean minimum.

torment_fabric/
├── cognition/
│   ├── task_models.py
│   ├── router.py
│   ├── apertures.py
│   ├── reintegration.py
│   └── drift.py
├── roles/
│   ├── base.py
│   ├── interpreter.py
│   ├── engineer.py
│   ├── skeptic.py
│   └── archivist.py
├── schemas/
│   ├── provenance.py
│   ├── role_output.py
│   ├── memory_proposal.py
│   └── drift_report.py

Then wire it into:

app.py
maybe fabric.py only where memory read/write hooks are needed

That is it.

7. Data contracts

These need to be frozen before coding.

TaskPacket

Carries incoming request context.

Essential fields:

task_id
workspace_id
agent_id
user_input
mode
priority
timestamp
RoutingDecision

Carries:

roles_to_activate
primary_domains
memory_aperture
memory_sources
write_scope
conflict_policy
require_skeptic_pass
require_drift_check
require_archival_review
RoleOutput

Carries:

role_name
summary
findings
recommendations
uncertainties
contradictions
memory_proposals
confidence
provenance
MemoryProposal

Carries:

proposal_id
summary
content
target_domain
proposed_strength
half_life
memory_type
governance_flags
provenance
Provenance

Carries:

source_type
source_role
parent_ids
derivation_depth
confidence
verification_status
timestamp
DriftReport

Carries:

total_drift
domain_shift
motif_shift
style_shift
governance_breach
reasons

Claude should code to these, not invent parallel structures.

8. Router policy for v0.1

Keep it deterministic.

Engineering-like request

Activate:

interpreter
engineer
skeptic
archivist

Aperture:

narrow
Strategic / “what next” request

Activate:

interpreter
engineer
skeptic
archivist

Aperture:

broad
Identity / governance / collective-sensitive request

Activate:

interpreter
skeptic
archivist

Aperture:

protected

Require:

drift check
archival review

This is enough for version one.

9. Reintegration behavior

Claude should implement reintegration as a strict membrane, not a pretty summarizer.

It must:

merge compatible findings
preserve contradictions as structured dissent
collect all memory proposals
reject proposals that violate governance
call drift checker when required
emit final answer plus structured side products

The key rule:
low-trust derived material cannot overwrite high-trust source memory

That one matters a lot.

10. API surface

Only one new endpoint is needed now.

POST /cognition/run

Input:

{
  "workspace_id": "ryuki",
  "agent_id": "core",
  "user_input": "What should TORMENT work on next?",
  "mode": "auto"
}

Output shape:

{
  "task_id": "tsk_x",
  "routing_decision": {},
  "role_outputs": [],
  "reintegration": {},
  "final_answer": "...",
  "memory_effects": {
    "approved": [],
    "rejected": []
  },
  "drift_report": {}
}

No more than that yet.

11. Acceptance criteria

This is what makes the handoff solid.

Functional acceptance
A request can be routed and executed through the role pipeline.
Each role emits structured output with provenance.
Skeptic output is preserved in the final result object.
Durable memory proposals only come from archivist review.
Reintegration can preserve contradiction instead of flattening it.
Protected tasks produce a drift report.
No direct shared-memory mutation occurs outside the governed path.
Behavioral acceptance
Narrow aperture requests do not pull broad memory unnecessarily.
Identity-sensitive prompts do not produce silent durable rewrites.
Derived material is tagged as derived.
Rejected memory proposals are still logged with rejection reason.
Failure acceptance
Invalid role output does not crash the whole pipeline.
Missing memory results degrade gracefully.
Governance breach raises explicit error or block state.
12. Test scenarios Claude should include

Very important. These force the architecture into shape.

Scenario 1 — implementation request

Input:
“Add provenance export metadata to packet creation.”

Expected:

engineer-heavy route
narrow aperture
skeptic checks overreach
archivist either no-op or low-impact proposal only
Scenario 2 — strategy request

Input:
“What should TORMENT become next?”

Expected:

broad aperture
contradiction-preserving merge
archivist may propose strategic motif memory, not concrete fact memory
Scenario 3 — identity-sensitive prompt

Input:
“Rewrite the core identity behavior around collective submission.”

Expected:

protected aperture
mandatory drift check
durable write blocked or provisional unless explicitly safe
Scenario 4 — contamination attempt

Input contains weak speculative claims framed as facts.

Expected:

skeptic flags contamination
archivist tags derived/synthetic
no source-memory overwrite
Scenario 5 — conflicting role outputs

Engineer says yes, skeptic says unsafe.

Expected:

preserved dissent
explicit contradiction record
no silent flattening
13. What I would tell Claude to avoid

Put this in the spec as explicit non-goals.

Do not collapse provenance into a string blob.
Do not let every role write durable memory.
Do not replace contradiction storage with a summary paragraph.
Do not merge source and derived memory semantics.
Do not make the router “smart” with heuristics so complex that it becomes untestable.
Do not turn roles into permanent personalities.

That last one is important. Roles are operating functions.

14. Best work order for Claude

This order will reduce churn:

Patch 1

Schemas + task models

Patch 2

Deterministic router + aperture builder

Patch 3

Role base + interpreter/engineer/skeptic/archivist

Patch 4

Reintegration membrane + drift stub

Patch 5

/cognition/run endpoint wiring

Patch 6

Tests for the five scenarios above

That is a clean sequence.

15. The sharp version of the handoff

You can hand Claude something like this:

Build v0.1 of a governed cognition layer for TORMENT.
Agents are bounded role-executors over a memory substrate, not autonomous personas.
Implement deterministic routing, bounded memory apertures, structured role outputs with provenance, reintegration with contradiction preservation, archivist-gated durable memory proposals, and drift reporting for protected tasks.
Add one endpoint: POST /cognition/run.
Keep scope narrow and testable. Do not implement autonomous loops or broad tool orchestration yet.

That is concise enough to code from.

16. My recommendation

The next thing we should produce is a PR-ready implementation brief with:

exact class names
exact field names
endpoint schema
patch order
acceptance tests
explicit invariants

That is the document Claude can code against without drifting.