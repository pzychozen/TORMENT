# TORMENT — Pre-Database Cognition Ceiling & Architecture Decision Frame v0.1

## 0. Title / status

**Architecture decision frame. Docs-only / NON-AUTHORIZING. No lane opened.** This
frame consolidates the current pre-database cognition ceiling and the operator
architecture fork so the project **stops re-scanning U1 / audit-owner / shaping /
Gate D for micro-moves**. It authorizes nothing, changes no code, opens no lane, and
lifts no fence. It records a decision that is **Hilmir's to make**.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `cd4d0c2` (repo edge). Consolidates the U1 / audit-owner / shaping / Gate-A /
Gate-D scans recorded in `PROJECT_ORIENTATION_MAP.md` §0 and
`TORMENT_PRE_DATABASE_LAYER_STATUS_BOARD_v0.1.md`.

## 1. Purpose / scope

```text
DEFINES:
  - The current ceiling: why no within-fence capability move remains.
  - The operator architecture fork: which fence to lift first.

DOES NOT:
  - Lift any fence, select any mechanism, or open any lane.
  - Re-scan or reopen U1, audit-owner, dual-ownership, or any shaping micro-slice.
  - Authorize a prompt change, substrate, model-API, Gate D, or Envelope Audit.
```

## 2. Board truth — the ceiling

```text
- The SAFE substrate-independent runway is SPENT for now.
- Thinking / MemoryPlan layer is HARDENED-FOR-NOW / paused (routing + retrieval-shaping
  + observability; it routes, it does not deliberate).
- Ephemeral cognition Slices 1–3 + geometric + relational-prominence shaping are
  LANDED / paused (all default-off, plan-boundary top_k / weight nudges).
- A further Slice 4 is NOT authorized unless it names a REAL cognition capability —
  not another retrieval nudge.
- AgentRunner generation is MEMORY-BLIND: the model-visible request is
  `system_prompt + raw_input` and consumes NO assembled / retrieved memory (A-prime).
- U1 / audit-owner is HOLD because the AUDITABLE EVENT DOES NOT EXIST — there is no
  model-visible memory inclusion to audit while generation is memory-blind.
- Gate A wall Tier-2 needs a CARRIER / SUBSTRATE (producer-independent ground exhausted).
- Gate D / Envelope Audit / private cognition / Document B interior / dream remain
  NO-OPEN / DEFERRED (A0 review: need model-API or substrate authorization).
- Gate B writer-authority, R-field, Probe-v1, and database / substrate remain FENCED.
```

## 3. The root finding — memory-blind generation

The single fact that ties the ceiling together: **the agent's generation does not use
its memory.** `AgentRunner`'s model-visible request is `system_prompt` (the v0.1 minimal
system prompt) plus `messages=[{user: raw_input}]`; it consumes no assembled or retrieved
memory. Consequences:

```text
- The thinking layer can ROUTE retrieval (MemoryPlan) but the retrieved memory never
  reaches the generation prompt — so "thinking" is routing, not thinking-with-memory.
- The audit-owner / model-visible-context lane has a built, inert auditor but NO
  auditable event: there is no memory inclusion in the prompt to prove or audit.
- A "real Envelope Audit" (truthful use of memory) is therefore not merely unbuilt —
  it has nothing to observe until generation consumes memory.
```

This is why U1, dual-ownership orchestration, and audit-owner all dead-end: each tries
to audit / route around a memory-use event that the generation path never produces.

## 4. Why each lane is parked / fenced (so it is not re-scanned)

```text
- U1 caller-path                      → HOLD. Disjoint ownership; no honest live caller;
                                        auditable event absent. (Codex PASS on no-candidate scan.)
- Audit-owner / model-visible-context → ROUTE-TO-GATE-D / HOLD. Exhausted as a standalone
                                        micro-lane; continuation lives in Document B / Gate D.
- Ephemeral cognition shaping         → PAUSED. Slices 1–3 + geometric + relational landed;
                                        Slice 4 is a retrieval nudge unless it names real capability.
- Gate A wall                         → PAUSED. Tier-2 needs carrier = substrate.
- Gate D / Envelope Audit / Doc B     → NO-OPEN / DEFERRED (model-API or substrate).
- Gate B writer-authority             → FENCED.
- R-field / Probe-v1                  → FENCED.
- Database / substrate / carrier      → DEFERRED (deliberately last).
```

**None of these is a missing-work gap.** Each is fenced by a deliberate operator
constraint. Re-scanning them for micro-moves produces framing/characterization churn,
not capability.

## 5. The operator architecture fork

The next real progress is **not a lane — it is a Hilmir decision about which fence to
lift first.** The four options (this frame selects none, lifts none):

```text
1. MEMORY-TO-PROMPT-FOR-GENERATION — let the agent's generation actually consume its
   retrieved / assembled memory (lifts the "no model-visible prompt change" fence).
   Unlocks: thinking-with-memory; AND makes the parked audit-owner / Envelope-Audit lane
   meaningful (gives it a real event to audit).
2. SUBSTRATE / CARRIER — open a minimal durable carrier (lifts the database/substrate
   fence). Unlocks: Gate A Tier-2 enforcement, durable private cognition, candidate store.
3. MODEL-API / ENVELOPE AUDIT — authorize a real model-API observation track (lifts the
   audit-owner / model-API fence). Unlocks: real Envelope Audit over model cognition.
4. REMAIN HOLD — keep all fences; accept that the pre-database cognition layers rest
   where they are.
```

## 6. Recommended first decision question (a QUESTION, not an authorization)

```text
RECOMMENDED FIRST QUESTION: Option 1 — memory-to-prompt-for-generation.
WHY:
  - It is the ROOT of the ceiling. Memory-blind generation is what makes the thinking
    layer "routing not thinking" and makes the audit-owner lane eventless.
  - It is the PREREQUISITE for a meaningful audit of memory use: you cannot audit
    whether the model truthfully used its memory until the model is given its memory.
  - It is substrate-INDEPENDENT in principle (it is a prompt-architecture decision, not
    a durable-state decision), so it does not require opening database/substrate first.
```

**This frame does NOT lift that fence.** It only recommends that, when Hilmir is ready to
move, the memory-to-prompt-for-generation question is the highest-leverage one to open —
under a separate, explicitly authorized decision with Codex review, and with its own
safety analysis (it touches the model-visible prompt and therefore needs careful scoping
that is out of bounds here).

## 7. Forbidden crossings (hard boundaries of this frame)

```text
- no code; no tests; no production change
- no prompt change; no model-visible memory injection
- no PrivateGenerationOwner wiring; no U1 caller wiring; no dual-ownership orchestration
- no endpoint / API / schema
- no output-control / review / suppression / retry / ranking / style steering
- no memory write
- no retrieval-authority expansion
- no Gate D / private cognition runtime
- no dream / incubation runtime
- no Envelope Audit runtime
- no database / substrate / carrier / schema / storage / migration
- no Gate B; no R-field; no Probe-v1
- no shaping slice
```

This frame records a decision question only. Nothing above is opened, selected, or
authorized.

## 8. Future gate

```text
- This frame authorizes NO implementation and opens NO lane.
- Lifting ANY fence (Options 1–3) requires a SEPARATE explicit Hilmir decision + Codex
  review, with its own safety scoping — especially Option 1, which touches the
  model-visible prompt and is out of bounds for this docs-only frame.
- Until a fence is lifted, the truthful state is FORMAL HOLD. This frame is the single
  consolidated record of that HOLD so the lanes in §4 are not re-scanned for micro-moves.
```

## 9. Anti-drift footer

TORMENT — PRE-DATABASE COGNITION CEILING & ARCHITECTURE DECISION / DOCS-ONLY /
NON-AUTHORIZING / NO LANE OPENED. It consolidates the pre-database cognition ceiling: the
safe substrate-independent runway is spent; the thinking / MemoryPlan layer is
hardened-for-now; ephemeral cognition Slices 1–3 + geometric + relational shaping are
landed/paused (Slice 4 only if it is real capability, not a retrieval nudge); **AgentRunner
generation is memory-blind (`system_prompt + raw_input`, no assembled/retrieved memory)**,
which is why U1 / audit-owner is HOLD (the auditable event does not exist), Gate A Tier-2
needs a carrier/substrate, and Gate D / Envelope Audit / private cognition / dream remain
NO-OPEN; Gate B / R-field / Probe-v1 / database-substrate stay fenced. The next real move
is an **operator architecture decision** among (1) memory-to-prompt-for-generation,
(2) substrate/carrier, (3) model-API / Envelope Audit, or (4) remain HOLD — with
**(1) recommended as the first decision question** because memory-blind generation is the
root ceiling and the prerequisite for any meaningful audit of memory use. **It lifts no
fence, opens no lane, writes no code or tests, changes no prompt, and authorizes nothing;
any fence-lift needs a separate Hilmir decision + Codex review.** Guidance not control;
audit observes authority and does not become authority; nothing rewrites identity / canon
/ seed / soul.
