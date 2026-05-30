# Memory-to-Prompt v0.2.x Ledger Persistence Decision — Option C Ratified

**Status:** Active checkpoint, ratified 2026-05-30 by trio (pzychozen, GPT, Claude). Citable. Closes the Memory-to-Prompt v0.2.x chain at v0.2.4.

**Origin:** 2026-05-30 trio decision following the 2026-05-30 ledger-persistence audit, itself following the 2026-05-29 ratification of Ledger Observational-Boundary Doctrine v0.1. Promoted via the audit-first cadence (chat-shape ratification → scratch framing draft → trio review round 2 → revised draft (not required; inline polish only) → final ratification → docs commit).

---

## §1 Decision (citable block)

- **Option C ratified** for current runtime. `assembly_audit` remains opt-in, response-only, persisted nowhere, and consumed by no production runtime path.
- **Option A foreclosed** under the current doctrine. Reopening it would require explicit doctrine amendment and a concrete justification strong enough to outweigh the retrieval-coupling hazard. `memory_events.jsonl` is the canonical input to the SQLite index rebuild that drives retrieval. Mixing audit lines into that file would place audit one bug or refactor away from feeding live retrieval — exactly the failure mode Ledger Observational-Boundary Doctrine v0.1 §3 forecloses.
- **Option B preserved as use-case-gated fallback.** If persistence later becomes justified by a concrete operational question, a dedicated observational ledger separate from canonical memory is the preferred *starting shape*. **No schema, retention policy, write helper, rotation, implementation, or tests are ratified now.** Ratification would require its own audit-first cycle.
- **Memory-to-Prompt v0.2.x chain closed at v0.2.4** (archive-FILTER-A). Any future persisted audit work opens its own audit-first gate, not a v0.2.5 / v0.2.x extension.

> *The audit did not reveal a missing feature. It confirmed that the existing response-only design is the doctrine-compatible shape for the present runtime.*

---

## §2 Rationale

Full audit trace: `scratch/brainstorming/2026-05-30_ledger_persistence_audit.md` (local scratch). This checkpoint stands alone; the substantive findings are summarized below.

- **Doctrine baseline already satisfied by construction.** `assembly_audit.py` is explicitly response-only per its module docstring (*"No I/O: no file open, no socket, no network, no ledger writes... the helper does not persist any audit record. The audit payload exists only in memory and in the HTTP response."*). The audit dict is built only when `include_assembly_audit=True` is set on the request. The only places that handle the dict in production code are the helper itself, the `/retrieve` response assembly (`app.py` §6), and the HTTP client passthrough (`live_agent/memory_bridge.py`). No production code path consumes a prior audit.
- **No present operational question requires persistence.** Replay determinism is served by `memory_events.jsonl` directly. Operator inspection is served by opt-in `/retrieve` capture. No production code, test, replay workflow, or operator need asks for historical audit.
- **Option A's retrieval-coupling hazard is concrete, not hypothetical.** `sqlite_index.py` rebuilds from `memory_events.jsonl` (see the in-code comment at `sqlite_index.py:267`). Mixing audit into this file places audit physically inside the retrieval input pipeline. Discipline tags (e.g., `type=audit; do-not-index`) would be one bug or refactor away from violation.
- **Persistence without a concrete question is speculative collection.** Storing because storage is cheap is the surveillance-default posture the project has explicitly chosen to avoid.

---

## §3 Minimum-observation stance (recorded principle, not new doctrine)

> *Observe only what is necessary, for a reason, under a visible boundary.*

This is **the principle informing this decision**, not new doctrine. It is recorded here so future readers understand the framing the trio applied; it is not binding on future audit-related decisions. If the trio later wants this principle elevated to doctrine, that elevation requires its own audit-first cycle.

---

## §4 What this checkpoint does NOT do

- Does not amend Ledger Observational-Boundary Doctrine v0.1.
- Does not specify schema, retention, write path, rotation policy, or any implementation for Option B.
- Does not promote any brainstorm-level material.
- Does not authorize cognition, MCP, tool wiring, autonomy, environment-vision, or persona-action work.
- Does not preclude a future trio from ratifying Option B if a concrete operational question emerges.
- Does not establish the minimum-observation stance (§3) as binding doctrine.
- Does not amend the existing handoff (2026-05-28 phase-preparation handoff). That handoff was a correct snapshot at the time; the new state is reflected naturally in the next handoff.

---

## §5 Relation to Ledger Observational-Boundary Doctrine v0.1

This checkpoint operates under the doctrine and exercises its §9 light enforcement principle —

> *Any future implementation that would consume audit records in a live runtime decision path must be either explicitly authorized by amendment to this doctrine, or rejected.*

— as the rule that forecloses Option A. The doctrine itself is not modified.

---

## §6 Relation to the Memory-to-Prompt v0.2.x chain (chain closure folded in)

This checkpoint **closes the Memory-to-Prompt v0.2.x chain at v0.2.4**. Closed gates for traceability:

- **v0.2** — observability lane (read-only assembly observability via `/retrieve` audit payload).
- **v0.2.2** — `character_context` surfacing on `/retrieve`.
- **v0.2.3** — spirit-return / voice-cue end-to-end surfacing verification.
- **v0.2.4** — archive memory passes FILTER-A before prompt assembly.

The ledger persistence question was the final open consideration downstream of v0.2.4. With this checkpoint, the chain is complete.

Any future persisted audit work opens its own gate (e.g., a v0.3 audit-ledger track, or a separately-named track depending on the use case). It is not a quiet continuation of v0.2.x.

---

## §7 Ratification cadence

Following the v0.2.4 / doctrine pattern:

1. Chat-only proposed shape, reviewed by trio. **Complete 2026-05-30.**
2. Scratch framing draft. **Complete 2026-05-30.**
3. Trio review round 2. **Complete 2026-05-30.**
4. Revised draft. **Not required — inline polish only.**
5. Final trio ratification. **Complete 2026-05-30.**
6. Single docs commit promoting to `docs/CHECKPOINT_2026-05_LEDGER_PERSISTENCE_DECISION_OPTION_C.md`. **This artifact.**
7. Added to closed-gates list in next handoff with commit anchor. *(Operator action — pending.)*

---

*Ratified by trio (pzychozen, GPT, Claude) on 2026-05-30. Confirms Option C as the doctrine-compatible shape for the present runtime, closes the Memory-to-Prompt v0.2.x chain at v0.2.4, and preserves any future persisted-audit work as its own use-case-gated audit-first decision.*
