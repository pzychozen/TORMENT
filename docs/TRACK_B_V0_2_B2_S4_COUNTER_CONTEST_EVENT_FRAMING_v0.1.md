# Track B v0.2 — B2-S4 Counter-Contest Event Framing v0.1

**Status:** Candidate framing artifact. **Not doctrine. Not implementation
authorization.** Drafted by Claude for trio review (Hilmir as operator + GPT
review + Codex adversarial review). Produced from the B2-S4 read-only
archaeology survey and the operator's binding design ruling, 2026-06-04.
**Audit baseline:** Windows-authoritative `HEAD = 69bf726` (docs checkpoint) /
`9c027a0` (last code). No code, no schema finalization, no migration, no git.
**Parent framing:** `docs/TRACK_B_V0_2_CONTEST_LEDGER_RUNTIME_BOUNDARY_FRAMING_v0.1.md`
(this artifact narrows its §12 B2-S4 step; it does not supersede it).
**Anchor docs:** Track B v0.1 (`docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md`),
Ledger Observational-Boundary Doctrine v0.1, B2-S2 / B2-S3 checkpoints.

---

## 1. Status and scope

This is a **framing artifact only**. It converts the operator's B2-S4 design
ruling into a precise, narrow slice boundary for later review. It authorizes
nothing.

```
Framing artifact only.
Candidate slice only.
Not implementation authorization.
Not schema authorization.
Not consumer-wiring authorization.
Not resolver authorization.
Not retrieval authorization.
Not prompt-surfacing authorization.
Not cognition authorization.
Not MCP authorization.
Not automation authorization.
Not autonomy authorization.
```

Operational discipline (carried from the spine): **Windows is the source of
truth.** This artifact is a candidate draft for the trio review chain (§13); it
becomes implementation authority for nothing even when landed. A separate
operator directive is required before any code-bearing B2-S4 slice.

---

## 2. Inherited Track B center

The center question is inherited verbatim and unchanged:

> **How can TORMENT remember that something happened while allowing an agent or
> character to contest how much authority that memory gets?**

Inherited invariants this slice preserves, restated as the binding posture for
the counter-contest event:

```
memo != control
literal ledger read != authority resolver
persistence != consumer wiring
recording disagreement != resolving authority
```

A counter-contest event is a sidecar observation beside a sidecar memo. It
records that disagreement occurred. It does not — and in this slice cannot —
resolve, weight, or route authority.

---

## 3. Closed inherited chain

```
B2-S1 runtime-boundary framing
→ CLOSED

B2-S2 isolated ContestRecord vocabulary
→ CLOSED

B2-S3 isolated ContestLedger persistence
→ CLOSED

B2-S4 counter-contest event vocabulary + isolated persistence
→ CANDIDATE ONLY
→ NOT AUTHORIZED
```

B2-S2 landed an immutable `ContestRecord` (vocabulary + fail-closed validator +
pure serialization; no production importer, AST-guarded). B2-S3 landed an
isolated single-file append-only `contest_records.jsonl` ledger (`append_record`
+ literal unbounded `list_records`; fail-closed read; no consumer wiring,
AST-guarded). Both are non-load-bearing by construction. B2-S4 extends that
posture to *counter-contest events* — and to nothing else.

---

## 4. Narrow B2-S4 purpose

```
A counter-contest event records that a ContestRecord identifier
was itself contested.

The event is append-only history.
It is not a mutation.
It is not a verdict.
It is not a resolver input with automatic effect.

The first bounded slice records a structurally valid claimed linkage.
It does not prove target existence.
```

Per the operator's binding ruling, a counter-contest is an **immutable
observational event linked to a `ContestRecord` identifier**. It records that an
earlier `ContestRecord` identifier was itself contested. Explicitly, it **does
not** mutate / reverse / overturn / cancel / supersede / resolve / override /
win against the prior `ContestRecord`. Those verbs name effects this slice does
not build and does not authorize.

---

## 5. Smallest plausible storage shape (described, not ratified)

A candidate isolated event ledger, sibling to the B2-S3 record ledger, under the
existing `contest_memory/` workspace directory:

```
<data_dir>/workspaces/<workspace_id>/contest_memory/contest_events.jsonl
```

This mirrors the `conflicts.py` records-file + events-file split while leaving
the B2-S3 `contest_records.jsonl` file and its module untouched. Candidate
surface (illustrative names only — not a finalized API):

```
append_event(event) -> None
list_events() -> list[CounterContestEvent]
list_events_for_contest(contest_id) -> list[CounterContestEvent]
```

The linked-event reader is **literal and observational**:

```
return matching linked events in append order
```

Hard boundaries on the reader, carried verbatim from the ruling:

```
No derived state.
No status field derived from replay.
No effective view.
No latest-wins rule.
```

`list_events_for_contest(contest_id)` returns the literal linked events in
append order and **nothing more** — no count-as-signal, no "active/overturned",
no winner, no precedence, no ranking weight. It is a linkage view, not a verdict
view. (See §6 of the parent framing: full-ledger replay is sufficient for
correctness; no cache or index is required, and none on the authority path is
permitted.)

---

## 6. Candidate event vocabulary boundary

Minimum conceptual fields (names illustrative; **no schema finality** is claimed
or authorized here — schema signatures remain deferred per parent framing §5.2):

```
event_id            UUID-shaped, never auto-derived from content
target_contest_id   UUID-shaped; structurally identifies the ContestRecord
                    the event claims to contest
contestant_actor    closed actor vocabulary (agent / character / operator / user*)
contestant_id       non-empty
reason_class        closed required-reason vocabulary
event_provenance    ProvenanceV1 (carries created_at_step / session_id)
```

UUID-shaped **structural** validation is used where appropriate (`event_id`,
`target_contest_id`) — mirroring the B2-S2 `contest_id` / `candidate_handle`
discipline, which validates shape without performing any existence lookup.
Explicitly, in the first bounded slice:

```
target-existence validation is parked
dangling-linkage policy is parked
the first bounded slice validates UUID shape only
```

**No `contest_result` field is included in the first candidate slice.** This is
deliberate. A counter-contest result field would prematurely reopen:

```
- authority routing
- reversal semantics
- refuse semantics
- operator authorization
- effective-authority interpretation
```

A counter-contest in this slice records *that* a prior contest was contested and
*by whom, for what stated reason class* — it does not assert an outcome. Outcome
vocabulary, if it is ever wanted, is a separate later gate that must travel
through the effective-authority resolver-boundary audit (parent framing §8.0)
first.

---

## 7. Explicit non-goals

Held closed by this artifact — not opened, not designed, not authorized:

```
No prior ContestRecord mutation.
No reversal.
No supersession.
No cancellation.
No effective-authority resolution.
No active/inactive state.
No overturned state.
No winner.
No precedence.
No latest-wins semantics.
No target-existence policy.
No candidate_handle → eid binding.
No runtime consumer wiring.
No retrieval influence.
No prompt surfacing.
No cognition coupling.
No MCP exposure.
No automatic firing.
No autonomy expansion.
No fsync or lock hardening.
No generic ledger redesign.
```

This list is the load-bearing fence. Any future B2-S4 implementation that would
need to cross one of these lines is, by definition, outside this slice and
requires its own gate.

---

## 8. Relevant precedent handling

The repo's append-only event family is well-worn, but it carries one pattern
this slice must deliberately refuse: replay that derives an *effective state*.
For Track B, replay-derived effective state would become **replay-derived
effective authority**, which the parent framing holds explicitly closed (§8.0).
The borrow/do-not-borrow split:

```
Borrow:
- immutable base record + append-only event split
- literal replay discipline
- append-order preservation
- fail-closed read posture
- path-safety conventions
- AST import-purity guard pattern

Do not borrow:
- apply_events() effective-state semantics
- latest-event-wins semantics
- status resolution
- list_pending()-style effective filtering
- skip-malformed-lines behavior
```

Relevant precedent files:

```
torment_service/conflicts.py      record+events split; eid linkage — but
                                  apply_events() RESOLVES status (do not copy)
torment_service/proposals.py      record+events split; replay derives EFFECTIVE
                                  status, list_pending() filters on it (do not copy)
torment_service/closure_ledger.py literal last-event discipline + build_*_event
                                  factories — but last-event-kind DEFINES state
                                  (borrow the literalness, not the state derivation)
torment_service/baton_ledger.py   the cleanest "events are history, not a state
                                  store" posture — closest in spirit
```

Note the B2-S3 governance departure carries forward: the event reader **fails
closed** on a malformed line and on a duplicate `event_id` (raise on read), and
does **not** inherit the `closure_ledger` / `baton_ledger` skip-malformed-lines
behavior — a silently skipped counter-contest event would hide a contest,
contradicting the inherited audit-visibility invariant.

---

## 9. Integrity policy intentionally parked

Target-existence validation is **out of the first B2-S4 slice on purpose**, and
the reason is sharpened here so the boundary is not overstated:

```
Target-existence validation is intentionally parked because
it introduces premature cross-ledger integrity policy.

The first bounded slice only needs structural linkage validation:
target_contest_id must be UUID-shaped.

A later explicit gate may decide whether dangling linkage:
- fails on append
- fails on replay
- appears in an audit report
- remains representable as a historical anomaly
```

The point is *not* that a ledger-to-ledger lookup automatically becomes
production consumer wiring — that would overstate the boundary. The point is
that *what dangling linkage should mean* is a genuine cross-ledger integrity
decision with several legitimate answers, and choosing among them is its own
gate. Structural UUID-shape validation is the minimum the first slice needs and
the maximum it should assume. The first slice records a structurally valid
*claimed* linkage; it does not prove that the target exists.

---

## 10. Scope discrepancy correction

The source docs drifted on what B2-S4 contains. The parent framing §12 wording
("target-linkage support: contested_eid, candidate_handle, **handle → eid
binding**, counter-contest replay") bundled handle-binding into B2-S4, while the
B2-S3 checkpoint §7 and the operator handoff scope B2-S4 to counter-contest
events only. This artifact resolves the drift in favor of the narrow reading:

```
B2-S4 does not include candidate_handle → eid durable binding.

Any earlier wording that appeared to bundle handle binding into
B2-S4 is narrowed by this framing artifact.

candidate_handle → eid durable binding remains separately parked.
```

This is consistent with the parent framing's own §13 #3, which already parks
`handle → eid` binding as an independent open trio decision. Older docs are
**not edited by this artifact**; if the trio ratifies this narrowing, a separate
small docs-reconciliation pass may align the parent framing §12 wording — flagged
here, not performed here.

---

## 11. Candidate implementation boundary (described, not authorized)

The smallest possible future implementation slice, named so the trio can judge
its size — **no code is written and none is authorized**:

```
- one isolated event vocabulary module
- one isolated append-only event-ledger module
- focused unit tests
- fail-closed replay tests
- duplicate event_id detection on read
- AST import-purity guards
- zero production consumers
```

This mirrors the B2-S2 (vocabulary module + tests) and B2-S3 (ledger module +
tests + AST guards) shape exactly, one level out. It would import `ProvenanceV1`
and nothing from the authority/consumer surfaces (memory_graph / fabric / spine /
governance / retrieval / cognition / mcp_server / app), enforced by the same
import-purity AST guard B2-S3 established.

---

## 12. Parked follow-on gates

Named, not opened, not sequenced:

```
- target-existence integrity policy
- candidate_handle → eid durable binding
- counter-contest result routing
- operator authorization completion
- effective-authority resolver-boundary audit
- first observation surface
- retrieval surfacing
- prompt surfacing
- cognition coupling
- MCP exposure
- automatic firing
- autonomy
- fsync and locking
- generic storage redesign
```

None of these is opened by this artifact. The effective-authority
resolver-boundary audit (parent framing §8.0 / §13 #8) remains the gate that
must precede any *application* of contest or counter-contest history to
authority.

---

## 13. Proposed review sequence

```
1. Claude drafts framing artifact.
2. GPT reviews framing artifact.
3. Codex performs adversarial boundary review.
4. Hilmir + GPT decide whether implementation authorization is safe.
5. Only then may Claude receive a bounded implementation directive.
```

---

*End of Track B v0.2 — B2-S4 Counter-Contest Event Framing v0.1. Candidate
framing artifact for trio review. Not doctrine. Not implementation
authorization. Narrows the parent framing §12 B2-S4 step to counter-contest
event vocabulary + isolated append-only persistence; `candidate_handle → eid`
binding, target-existence policy, and counter-contest result routing remain
separately parked. A separate operator directive is required before any
code-bearing B2-S4 slice.*
