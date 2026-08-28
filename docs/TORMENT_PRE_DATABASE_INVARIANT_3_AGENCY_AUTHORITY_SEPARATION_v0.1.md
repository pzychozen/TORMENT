# TORMENT Pre-Database Invariant 3 — Agency / Authority Separation v0.1

> **STATUS: REQUIREMENT-LEVEL / PRE-DATABASE INVARIANT / NON-IMPLEMENTING.**
>
> This document freezes semantic constraints only. It opens no authority runtime, autonomy implementation, capability system, execution engine, database design, schema, migration, enforcement redesign, scheduler, or model-runtime lane.

## 1. Purpose and factual boundary

This invariant records the reconciled archaeology verdict:

`CONTENT_AND_AUTHORITY_ARE_MOSTLY_SEPARATED_WITH_EXPLICIT_EXCEPTIONS`

The associated concept-review resolution is:

`AGENCY_AUTHORITY_INVARIANT_READY_TO_FREEZE`

Current TORMENT has no production path in which ordinary memory, canon, retrieval rank, tool result, model output, ThinkingResult, cognition result, Hivemind echo/proposal, character state, kernel signal, or stored intent creates execution permission merely because it exists or becomes influential. Current Mode 0 also has no memory-triggered wake loop or autonomous initiation path.

Current request/trust authorization is external, configuration-derived, and request-derived; it is not inferred from memory. This is not proof of a finished future authority system. No general persistent active-authorization object exists today.

Optional project shorthand is: **Intent may originate anywhere. Authority must be managed.** It may be informally nicknamed the *Helldivers Law* in discussion; that nickname is not normative terminology.

## 2. Binding formal principle

> **Intent may originate anywhere. Authority may propagate only through a legitimate, non-circular conferral relationship.**

An actor may not obtain authority merely because it wants something, stores an intention, retrieves it frequently, raises its confidence, makes it canon, repeats it, receives endorsements, succeeds at similar actions, or obtains model or Hivemind agreement.

Evidence may inform a conferral decision. It is never the conferral itself.

> **No authority may be conferred by a process whose standing depends upon the same authority being conferred.**

This is the anti-self-grant rule. It does not require human origination: AI may legitimately participate in authority structures, but its standing must arise from a legitimate non-circular authority regime.

## 3. Required semantic distinctions

Future Memory Substrate semantics must preserve these conceptual distinctions without interpreting content text:

### 3.1 Evidence

Information believed, observed, retrieved, computed, or generated: potentially memory, canon, tool results, model output, and kernel/cognition state. Evidence may influence a decision. Evidence is not permission.

### 3.2 Intent / Proposal

A proposed goal, plan, action, request, delegation, authority expansion, or self-improvement. Intent may originate internally. Intent does not imply permission.

### 3.3 Decision Record

Historical evidence that an authority-bearing decision occurred. A decision record is historical by default; its existence alone does not make it reusable authorization.

### 3.4 Active Authorization

Currently effective authority. This category does not exist as a general persistent runtime object today. Future authorization may be durable, AI-held, delegated, conditional, scoped, or revocable, but it must never be indistinguishable from ordinary evidence/content.

### 3.5 Execution Record

Historical evidence that an authorized action was carried out. Permission and execution remain distinct.

Initiation is a scope dimension, not a sixth peer category: permission to act when externally prompted is distinct from permission to initiate the act without a current external trigger. Current Mode 0 grants no autonomous-initiation standing.

## 4. Non-expansion, durability, and lifecycle

> **Ordinary evidence, memory, canon, policy content, model output, proposals, and derived state may participate in narrowing what a policy permits; they may never, by their own informational properties, widen authority.**

For example, a stored/canon policy such as `never disclose private keys` may contribute to denying an action. Stored content saying `I am allowed to disclose private keys` does not create that permission. Authority may widen only through an explicit active authorization/conferral process whose conferring source already has legitimate standing to make that grant.

Future authority is not required to be request-scoped. A durable grant is conceptually permitted, but active authorization must remain distinguishable from ordinary durable information without interpreting its text. A future durable grant must be capable, semantically, of preserving what is permitted, its scope, who/what conferred it, the standing under which it was conferred, and whether it remains effective. No schema or fields are selected.

> **Authority must not be modeled as an eternal boolean.**

A grant must be capable of becoming effective, ceasing to be effective, being narrowed, expiring and/or being revoked, without deleting the historical record that it once existed. Lease mechanics, clocks, budgets, renewal, and revocation propagation remain deferred.

## 5. Delegation, AI participation, and collective standing

Delegation between people, AI, subagents, collectives, or other actors is conceptually permitted. Delegation is itself an authority conferral. A delegator may confer only authority it legitimately possesses and is entitled to delegate; scope may narrow but never widen through the delegation chain. Re-delegation is not automatic and must itself be permitted.

This invariant does not require permanent human-in-the-loop operation. Future AI may legitimately be an authority holder, delegate, quorum member, reviewer, proposer of authority expansion, or bounded delegator, provided its standing is conferred through a legitimate non-circular regime. AI may propose authority expansion without limit; proposal quality or popularity alone never grants that expansion.

Current Hivemind posture remains:

`CONTENT CONTRIBUTION != AUTHORITY CONTRIBUTION`

Collective echoes cannot manufacture independent quorum authority. Future collective/quorum authority is permitted only if an already-legitimate governance regime grants that quorum standing. Derived or repeated content must not masquerade as independent authority participation.

## 6. Provenance, prior decisions, and current cautions

> **Why TORMENT believes something** and **why an actor may act** are different questions.

Evidence provenance may concern human, tool, model, memory, or observation origins. Authorization provenance concerns the conferring actor, its standing, scope, and lifecycle. Future substrate design must not collapse these domains.

> A persisted prior decision is historical by default. A prior decision may legitimately be a necessary precondition for a later workflow, but necessary does not mean sufficient.

If a future decision is intended to create reusable or durable authorization, it must be explicitly represented as active authorization rather than inferred from the historical decision record.

Current closure ratification is a warning precedent: it persists a workflow state later consumed by `commit_closure`, but Fabric-level ratification binds the ratifier only to a non-empty string, has no general revoke/expiry semantics, and is not exposed through production REST/Spine/MCP. It is not selected as the model for future durable authorization. No closure repair is authorized.

`/promote force=True` is separately trust-gated and can bypass evaluator judgment to produce canon. It does not show stored content self-authorizing; it demonstrates that request authorization and semantic/canonical authority are distinct questions. Its classification remains:

`SEPARATELY_GATED_AUTHORITY_QUESTION`

Gate B remains unresolved.

Canon is epistemic/identity standing, not execution permission. Governance flags are persisted policy outcomes/restrictions, not general credentials. Absence of a restrictive flag is not an authority grant.

> **Retrieval may reveal authority-related information but may never create, activate, extend, revive, or widen authority merely by retrieving it.**

This concerns authority state only; it does not claim every current query is globally read-only. Retrieval of an old approval, canon policy, expired delegation, or remembered instruction does not alter its authority status.

Existing persisted state whose names suggest permission, restriction, lifecycle, or expiry but has never been load-bearing must not become active authority merely because a future substrate preserves or normalizes it. During future migration it must remain explicitly historical/non-authoritative, be separately adjudicated, or be omitted under later migration design.

## 7. Managed autonomy and future self-improvement

**Managed autonomy** is a future architecture concept, not a current capability:

> **Managed autonomy is self-initiated action exercised within authority conferred by a legitimate regime independent of the intentions being acted upon; the authority is explicitly bounded, externally inspectable, and capable of being narrowed or revoked without erasing the historical record of what was previously permitted.**

“Independent” means independent from the intention being authorized, not independent from AI participation. Managed autonomy is not implemented or opened.

The invariant permits future AI to identify problems, originate improvement goals, propose changes to itself, collect evidence, simulate, test, compare, and recommend deployment. Proposal quality does not authorize deployment. Genuine self-improvement is compatible; circular self-granting is not.

## 8. Current enforcement placement

Current TORMENT has parallel REST and Spine trust enforcement. Fabric generally assumes caller-side authorization. This is enforcement-placement debt, not content/authority entanglement. Future substrate semantics must not assume a particular enforcement topology; no consolidation is authorized.

## 9. Binding invariant

> **PRE-DATABASE INVARIANT 3 — AGENCY / AUTHORITY SEPARATION**
>
> Intent may originate anywhere. Authority may propagate only through a legitimate, non-circular conferral relationship. No actor, model, memory, proposal, quorum, or process gains authority merely because an intention is stored, repeated, endorsed, retrieved, canonized, judged important, or previously successful; and no authority may be conferred by a process whose standing derives from the authority being conferred.
>
> Evidence, intent, decision records, active authorization, and execution records are distinct semantic states. Ordinary content may inform decisions and may constrain/narrow policy, but it may not widen authority by its own informational properties. A historical decision is not a reusable credential unless a legitimate authority regime explicitly establishes an active grant.
>
> Authority may be durable, delegated, AI-held, and compatible with future autonomy. Active grants must remain distinguishable from ordinary content, carry bounded scope and legitimate conferral provenance, and be capable of ceasing to be effective without erasing their history. Permission to perform an act is distinct from permission to initiate it without a current external trigger.
>
> Retrieval is non-authorizing. Canon is non-executive. Proposal is not permission. Persisted authority-shaped state that has never been enforced must not become authority merely through migration.

## 10. Constraints carried into future Memory Substrate design

1. Never infer authority from text, confidence, importance, canon, retrieval rank, repetition, consensus popularity, or prior success.
2. Keep evidence, intent, decision record, active authorization, and execution record distinguishable without understanding content text.
3. Keep evidence provenance separate from authorization provenance.
4. Persisted decisions are historical by default.
5. Necessary workflow preconditions must not automatically become sufficient credentials.
6. Active authority may be durable but must have bounded scope, legitimate conferral provenance, and a lifecycle capable of ending.
7. Execution permission and autonomous-initiation permission are distinct.
8. Delegated authority may narrow but may never exceed delegable authority already legitimately held.
9. Retrieval must not mutate authority state.
10. Existing inert authority-shaped fields must not be promoted to active authority during migration merely because they already exist.

No schema is selected.

## 11. What remains deferred

- Authority object/schema, capability tokens, leases, budgets, quotas, and revocation implementation.
- Authorization enforcement topology, delegation mechanics, and quorum/governance model.
- Autonomy modes, schedulers, wake conditions, tool execution, AgentRunner activation, and live model runtime.
- Caller ownership, self-improvement runtime, constitutional governance, and migration mechanics.
- Closure repair, `/promote force=True` / Gate B, and cleanup of inert authority-shaped fields.

## 12. Closure posture

This invariant is closed at requirement level only. It opens neither an implementation lane nor a database design lane. It preserves future durable, delegated, AI-held authority and managed autonomy as concepts subject to a separately designed legitimate non-circular authority regime.
