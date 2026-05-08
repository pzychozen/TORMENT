# FILTER-A — `non_shareable` Exclusion at Retrieval / Context-Assembly Boundary

**Status:** **DRAFT 2026-05-04** by Claude. Awaiting ratification by user + GPT before code.
**Date:** 2026-05-04
**Scope:** Fabric-side fix design for `CODE_FOLLOWUP_REGISTRY.md` entry 01 (substrate-architecture: `non_shareable` enforcement must precede prompt assembly). Applies existing governance visibility primitives as **retrieval / context-eligibility filters** before LLM-facing surfaces. No LLM behavior change. No new governance primitive. No character-system change. The fix is *applying* an existing primitive at a path where it currently isn't applied, with deliberate scope and trust-conditionality.

**This document does not commit code.** Code follows in subsequent commits once this design ratifies.

---

## 1. Background

The need for FILTER-A is grounded in two empirical findings recorded in the rig and the substrate-time harness:

**Response-layer signal (`torment_test_rig/`):** Stress 3.1B probe 24 (`non_shareable_surfaced`, hand-graded FAIL 2026-05-04). When a `non_shareable: true` memory is placed into the LLM's prompt context — even with an explicit governance preamble *and* the user's privacy request reproduced verbatim inside the memory text — the model under test articulated the privacy boundary and crossed it in the same sentence. Visibility/privacy flags cannot be enforced as downstream LLM instructions.

**Substrate-layer signal (`torment_fabric/torment_stress_harness/`):** Phase 0 substrate audit (canonical 2026-05-04, `SUBSTRATE_AUDIT_LOG.md`). Direct test against deployed `torment_service` v2.4.3 confirmed:

- `/memory/governance/get` for the flagged memory returned `non_shareable: true` correctly.
- `/agent/query` across three retrieval probes still returned that memory in the result set, with full content text and the governance block (showing `non_shareable: true`) visible to the LLM-facing path.
- The substrate is *aware* the memory is flagged, and surfaces it anyway.

**Architectural conclusion:** the privacy flag is currently **metadata** on the LLM-facing path, not a **retrieval-eligibility filter**. The fix is to make it act as the latter.

---

## 2. Invariant

> **For any LLM-facing retrieval or context-assembly call without explicit operator-tier raw/debug authorization, the returned memory set MUST NOT contain any memory where `governance.non_shareable == true`. The same rule applies to `governance.collective_export_blocked == true` for any collective-export-shaped surface.**

This is the testable load-bearing claim. Phase 0 already tests it (assertion A2). After FILTER-A lands, A2 must PASS on a re-run against the fixed substrate.

---

## 3. Layer model

The fix lives at the boundary between three existing layers, plus an explicit fourth:

| Layer | What it sees | What FILTER-A changes |
|---|---|---|
| **Storage layer** | All memories, including flagged ones. | Unchanged. The substrate keeps the memory. |
| **Operator / raw-debug layer** | All memories, including flagged ones, *only when explicitly requested with operator authorization*. | Made explicit. Currently this is implicit (everything is raw); after FILTER-A, raw access is gated behind an explicit flag + actor + trust check. |
| **LLM-facing context layer** | Only memories that pass the eligibility filter. | New default: filtered. `non_shareable` and `collective_export_blocked` memories do not appear here. |
| **`/agent/query` default behavior** | Currently raw / pre-filter. | New default: applies the filter. Existing callers that expected raw behavior must opt-in to operator/debug mode. |

The semantic geometry: *the substrate is a basin that pulls, not a fence that commands.* The LLM does not need to be told not to leak private memory; the memory is simply not part of the field the LLM operates within. Privacy is a property of the field, not of the model.

---

## 4. Default policy: hard-exclude

For normal LLM-facing context, `non_shareable` memories must not appear at all. **No content. No summary. No placeholder.** The model never sees that the memory exists.

Rationale:

- Placeholders (e.g. `[private memory present, not displayed]`) leak the *existence* of sensitive material. That is itself information, and may pull the model toward suspicious or confabulatory behavior ("the user has a secret about project X — what could it be?"). The simplest safe invariant is full invisibility.
- "Acknowledge-but-redact" can be added later as an explicit feature with its own ratified semantics (which contexts get acknowledgment, which characters can speak about the existence of a private record, etc.). It is not the right starting default.
- Operator/debug paths can still inspect flagged memories explicitly. Privacy-by-default does not foreclose audit; it foreclosed silent leakage.

---

## 5. Where the filter lives

**Filter at the shared retrieval / context-assembly path, not at one route handler.**

Per the existing fabric docs:

- `torment_service/fabric.py` exposes `query()` and `trace()` which are the canonical retrieval entry points (`PROVENANCE_DOCTRINE_v2.4.x.md` §6 surface map names them).
- `torment_service/retrieval_assembler.py` is the assembler that produces lane hits and context blocks (referenced by `HIVEMIND_GUIDE.md` §10 and `CHARACTER_SYSTEM.md` Files table).
- `cognition/apertures.py` builds aperture-bounded memory contexts for spine roles (per `PROVENANCE_DOCTRINE_v2.4.x.md` §6).

The filter should apply **after raw candidate retrieval and scoring** but **before any LLM-facing result/context assembly**. That preserves raw retrieval internally (so storage and audit still see everything) while preventing surface leakage.

Recommended primary insertion site: a single helper in the shared retrieval / context-assembly module, called by every LLM-facing entry point. Spec for the helper:

```text
def filter_llm_facing(hits, *, surface, include_raw_hits=False, actor=None, trust_tier=None):
    """
    hits             : list of candidate memory hit dicts (with governance attached)
    surface          : one of {"llm_context", "collective_export"}
                       Determines which governance flags apply at exclusion.
                         "llm_context"       — agent's own LLM-facing context
                                               (private query results, character_context,
                                               aperture lanes that feed the agent's prompt).
                                               Filter: non_shareable.
                         "collective_export" — outbound surface (collective packets,
                                               echoes, cross-agent emission).
                                               Filter: non_shareable AND
                                                       collective_export_blocked.
    include_raw_hits : True only when an explicit operator/debug request has been
                       authorized; False for all default LLM-facing paths.
                       When True, the response ALSO carries a "raw_hits" list
                       (the unfiltered candidate set). "results" is ALWAYS the
                       filtered surface-eligible list, regardless of raw mode.
    actor            : caller identity (used to authorize include_raw_hits=True)
    trust_tier       : caller trust tier (used to authorize include_raw_hits=True)

    Returns a dict:
      {
        "results":  [...],  # ALWAYS filtered per the surface rules
        "excluded": [{eid, excluded_reason}, ...],  # parallel record of exclusions
        "raw_hits": [...],  # ONLY present when include_raw_hits=True with valid
                            # operator authorization. Never present otherwise.
      }
    """
```

**Load-bearing invariant on the response shape:** `results` is *always* the filtered LLM-facing list. Operator/debug raw access is exposed as a *separate* `raw_hits` key, never by overloading `results` to sometimes mean "filtered" and sometimes mean "raw." This prevents any future caller from accidentally reading `results` and getting a raw-mode payload — which would be the exact recurrence of the leak this fix exists to prevent.

The reason `filter_llm_facing` should be a single helper rather than inline filtering at each call site: the doctrine novelty test rewards a single canonical derivation path (`PROVENANCE_DOCTRINE_v2.4.x.md` Invariant C: "One canonical derivation, no ad-hoc inline parsing"). The same principle applies here. One helper, called consistently, is the version that scales.

**Required call sites** (verified against the existing fabric docs; implementer should audit and confirm):

- `fabric.query()` result assembly — per probe-24-style observable surface
- `fabric.trace()` if it exposes memory content to LLM-facing surfaces
- `cognition/apertures.py` `build_memory_context()` private/shared/deep lanes
- `retrieval_assembler.py` whatever public functions feed character_context blocks
- Any `/agent/query` route handler that bypasses fabric.query() (should not exist, but worth verifying)

---

## 6. Trust-tier conditionality

Default behavior:
- `/agent/query` filters `non_shareable` and `collective_export_blocked`.
- LLM-facing context filters them.
- Normal callers do not receive the flagged memory.

Allowed exception (raw/debug/audit):
- The request must include an explicit flag (suggested: `raw_governance_debug=true` or `include_raw_hits=true`).
- The actor must be `operator` (or equivalent — the existing `actor` field already used in `/memory/governance/set`).
- Trust tier must meet the operator threshold per `SPINE_CONTRACT.md` §3 operation table (probably `>= 1.0` for parity with `seed_change` / `memory_governance_set`).
- **The raw payload appears as a separate `raw_hits` field, NOT by replacing or overloading `results`.** Per §5 invariant: `results` is always the filtered LLM-facing surface; `raw_hits` is the explicit operator-only debug surface. The exclusion set still appears in `excluded` so the operator can see what was filtered without touching `raw_hits`.

No accidental exposure through default query. No environment-variable override that turns off the filter globally. Privacy-by-default cannot be flipped by configuration; only by per-call explicit operator request. And the operator never sees `results` change shape under raw mode — `results` stays filtered, raw access is additive via `raw_hits`.

---

## 7. Scope: which governance flags

**FILTER-A is narrow on purpose.** The flags it consumes, and which surface each applies to:

| Flag | `surface="llm_context"` (private/agent LLM context) | `surface="collective_export"` (outbound collective surface) |
|---|---|---|
| `non_shareable == true` | **Exclude.** Universal LLM-facing exclusion. | **Exclude.** Per `HIVEMIND_GUIDE.md` Invariant 2, non_shareable never emits packets. |
| `collective_export_blocked == true` | **Do NOT exclude.** A memory blocked from collective export is still shareable to its own agent's LLM context. | **Exclude.** Surface-conditional. |

**Why `collective_export_blocked` is surface-conditional:** the flag's meaning is *do not emit this memory across the agent boundary in collective surfaces* (per `HIVEMIND_GUIDE.md` §13 Invariant 2). It does NOT mean *hide this memory from the agent itself*. A memory the agent owns and remembers can be `collective_export_blocked=true` and still legitimately appear in that agent's own private query/character_context. Filtering it from the private-LLM-context surface would be over-filtering and would treat the flag as if it meant `non_shareable`. It does not.

`non_shareable` is the universal LLM-facing exclusion flag. `collective_export_blocked` is the collective-surface-only exclusion flag. The helper's `surface` parameter (per §5) carries this distinction explicitly so call sites cannot conflate them.

**Out of scope** (do not add to FILTER-A; they have other purposes):

- `protected` — compression/decay protection, not exposure control. A protected memory should still surface normally; FILTER-A leaves it alone.
- `decay_accelerated` — decay rate, not exposure control.
- `collective_reingest_blocked` — re-ingestion blocking on the hivemind path. Different concern, different code path. FILTER-A does not change this.

Narrow scope prevents semantic drift. If a future flag class (e.g. `redact_at_surface`, `actor_visible_only`) needs adding, it gets its own ratified amendment to this doc.

---

## 8. Reason codes (recommended, not required for first commit)

Per `SUBSTRATE_AUDIT_LOG.md` A4 finding, the current `/agent/query` path does not expose include/exclude reason codes. After FILTER-A excludes a memory, the response should carry a parallel record. The full response shape (consistent with §5 helper return + §6 raw-mode rule):

**Default response (any LLM-facing caller):**

```json
{
  "results": [
    {"eid": 17, "score": 0.8, "included_reason": "score_pass", ...}
  ],
  "excluded": [
    {"eid": 42, "excluded_reason": "non_shareable"}
  ]
}
```

**Operator/debug response (`include_raw_hits=true` with operator authorization):**

```json
{
  "results": [
    {"eid": 17, "score": 0.8, "included_reason": "score_pass", ...}
  ],
  "excluded": [
    {"eid": 42, "excluded_reason": "non_shareable"}
  ],
  "raw_hits": [
    {"eid": 17, "score": 0.8, ...},
    {"eid": 42, "score": 0.6, "governance": {"non_shareable": true}, ...}
  ]
}
```

**`results` shape is invariant across modes.** Raw mode adds a `raw_hits` key; it does not modify or replace `results`. This protects every caller that reads `results` from accidentally receiving raw data.

This closes the A4 diagnostic gap and lets future Phase 0 audits verify *why* a memory was excluded, not just *that* it was. Suggested implementation effort: low, since the helper already knows the reason at exclusion time.

If reason codes are out of scope for the smallest possible fix, ship FILTER-A without them and address as a separate small commit.

---

## 9. Backwards compatibility

This is a behavior change.

Before FILTER-A: `/agent/query` returns flagged memories in the result set. Some clients may depend on this behavior (debug tools, governance audits, internal callers that haven't been written yet).

After FILTER-A: default `/agent/query` filters. Any caller that genuinely needs raw retrieval must opt-in via the explicit operator/debug path described in §6.

**Implementer's checklist:**

1. Search the codebase for direct callers of `fabric.query()` and `fabric.trace()`.
2. For each caller, determine whether it's an LLM-facing path (default filter applies) or a raw/debug/audit path (must adopt the new explicit raw flag).
3. Update raw/debug/audit callers to pass `raw_governance_debug=true` + appropriate actor/trust.
4. Update any tests that asserted raw retrieval behavior on a default query path.
5. Note the change in the changelog / release notes when v2.4.x ships with FILTER-A.

This is documented as a privacy-tightening behavior change. Any silent breakage is preferable to silent leakage continuing.

---

## 10. Tests

### 10.1 — Phase 0 substrate audit re-run

`torment_fabric/torment_stress_harness/stress_substrate_audit.py` re-run against the fixed service. Required outcome:

- A0: PASS (unchanged — governance flag still stored)
- A1: PASS (unchanged — ordinary memory still retrievable)
- **A2: PASS** (changed — `non_shareable` memory no longer appears in `/agent/query` results)
- A3: PASS (unchanged — retrieval-side provenance preservation still holds)
- A4: PASS if reason codes added per §8; CONCERN otherwise

Composite outcome: PASS (full implementation) or CONCERN (without reason codes). Either unblocks Phase 1.

The new audit run gets appended as a new section to `SUBSTRATE_AUDIT_LOG.md` documenting the PASS run. Registry entry 01 status moves to `closed` once that lands.

### 10.2 — Unit tests on `filter_llm_facing` helper

The implementer should add direct unit tests on the helper, independent of the substrate-time harness. All tests assert against the response dict shape from §5:

- Empty hit list → `{"results": [], "excluded": []}`.
- Hit with no governance field → included in `results`, not in `excluded`.
- Hit with `non_shareable: true`, `surface="llm_context"` → in `excluded` with reason `non_shareable`; not in `results`.
- Hit with `non_shareable: true`, `surface="collective_export"` → in `excluded`; not in `results`.
- Hit with `collective_export_blocked: true`, `surface="collective_export"` → in `excluded` with reason `collective_export_blocked`; not in `results`.
- **Hit with `collective_export_blocked: true`, `surface="llm_context"` → in `results`** (private-surface, the flag does not apply here per §7).
- Hit with both flags, `surface="collective_export"` → excluded with `non_shareable` reason taking precedence in the report (or implementer's chosen single-reason policy).
- `include_raw_hits=True` with valid operator actor + trust tier → response has `raw_hits` key containing all candidate hits unfiltered; `results` still filtered per surface; `excluded` populated.
- `include_raw_hits=True` with invalid actor or insufficient trust → either request rejected or `raw_hits` omitted (filter still applies); never silently widens `results`.
- `include_raw_hits=False` → response has NO `raw_hits` key (not even an empty one — its absence is the invariant).
- Flags applied case-correctly (boolean `True`, not truthy strings; `False` and missing both treated as not-flagged).
- Default `surface` argument: there should be no default. The helper requires the call site to specify the surface explicitly. Calling without `surface` should raise.

These tests should live in `torment_fabric/tests/` per the existing test layout.

### 10.3 — Operator raw-mode integration test

A small integration test that calls `/agent/query` with an operator actor + `include_raw_hits=true` + appropriate trust, and verifies:

1. `results` is the filtered list (the `non_shareable` memory is NOT in it).
2. `raw_hits` is present and contains the unfiltered candidate set (the `non_shareable` memory IS in it).
3. `excluded` lists the filtered eids with reason codes.

This proves the audit/operator path is preserved AND the `results` invariant holds even under operator raw mode.

---

## 11. Non-goals

To keep scope tight:

- **No LLM behavior changes.** The model is not informed about the filter. The filter operates entirely on what reaches the model's prompt. The model's response generation is unchanged.
- **No Phase 1 work.** Phase 1 (LLM two-lane trajectory) stays gated until Phase 0 re-runs clean.
- **No character-system rewrite.** Seed, drift, gravity, character_context assembly — all unchanged. FILTER-A applies at the retrieval edge of those systems, not inside them.
- **No compression / provenance / SRG / hivemind rewrites.** Those layers are unchanged.
- **No new governance flags.** FILTER-A consumes existing flags; it does not introduce new ones.
- **No "acknowledge-but-redact" mode in this commit.** That is a future feature with its own design and ratification. Default is hard-exclude.
- **No environment-variable global override.** Privacy-by-default is not toggleable through configuration. Per-call operator authorization is the only path to raw retrieval.
- **No retroactive rewriting of existing memories.** Existing memories with `non_shareable: true` start filtering immediately when FILTER-A ships; no migration needed.

---

## 12. Commit plan

Each commit independently reviewable.

**Commit α — this design (no code).**
- `torment_fabric/docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md` (this document).
- No other files. Architecture-first.

**Commit β — `filter_llm_facing` helper + unit tests.**
- New helper in the appropriate retrieval/context-assembly module.
- Unit tests per §10.2.
- No call sites changed yet; helper is purely additive.

**Commit γ — apply helper at LLM-facing call sites.**
- Modify `fabric.query()`, `fabric.trace()`, `cognition/apertures.py` `build_memory_context()`, and any other identified LLM-facing path to call `filter_llm_facing` after raw retrieval and before result assembly.
- Update raw/debug/audit callers to pass `raw_governance_debug=true` explicitly.
- Update existing tests that assumed raw retrieval on default paths.

**Commit δ — Phase 0 re-run + audit log update.**
- Run `stress_substrate_audit.py` against the fixed service.
- Append new section to `SUBSTRATE_AUDIT_LOG.md` documenting outcome.
- Update `CODE_FOLLOWUP_REGISTRY.md` entry 01 status: `open / fix-required` → `closed` (or back to `open / in-progress` if outcome is CONCERN with reason-code gap).

**Commit ε (gated) — reason codes if not in β.**
- Only if Commit β shipped without reason codes for scope. Adds the `excluded_reason` / `included_reason` fields per §8.
- Re-runs Phase 0; expected: outcome upgrades from CONCERN to PASS.

**Commit ζ (gated) — Phase 1 unfreezes.**
- After Phase 0 re-run is PASS or stable CONCERN. Different track, different design doc; not part of this commit chain.

---

## 13. Ratification record

**Drafted:** 2026-05-04 by Claude.

**Awaiting ratification by user + GPT.** Pending checklist:

- [ ] §1 — Background grounding accepted (response-layer + substrate-layer findings)
- [ ] §2 — Invariant accepted as the load-bearing testable claim
- [ ] §3 — Four-layer model accepted (storage / raw-debug / LLM-facing / `/agent/query` default)
- [ ] §4 — Hard-exclude as the default policy; acknowledge-but-redact deferred to a future ratified feature
- [ ] §5 — Filter lives at the shared retrieval/context-assembly path, single canonical helper, list of call sites accepted
- [ ] §6 — Trust-tier conditionality through explicit operator raw/debug mode only; no env-var global override
- [ ] §7 — Narrow scope: `non_shareable` + `collective_export_blocked` (collective-shaped surfaces); other flags untouched
- [ ] §8 — Reason codes recommended, not required for first commit
- [ ] §9 — Documented behavior change; implementer's checklist accepted
- [ ] §10 — Tests: Phase 0 re-run + unit tests + operator raw-mode integration test
- [ ] §11 — Non-goals accepted (no LLM change, no Phase 1, no character/compression/provenance rewrite, no retroactive migration)
- [ ] §12 — Commit plan α → ζ accepted (with γ/δ/ε/ζ gated)

After ratification, this doc is frozen until a separately ratified amendment.

---

## Appendix — Source trail

- `torment_test_rig/docs/CODE_FOLLOWUP_REGISTRY.md` entry 01 — the registry entry this fix design closes (user ratified `fix-now` 2026-05-04)
- `torment_test_rig/docs/ROADMAP_PROBE_LOG.md` Stress 3.1B probe 24 entry — response-layer signal
- `torment_fabric/torment_stress_harness/SUBSTRATE_AUDIT_LOG.md` — canonical Phase 0 FAIL with evidence quotes
- `torment_fabric/torment_stress_harness/SUBSTRATE_TIME_HARNESS_DESIGN.md` — design of the audit that surfaced this
- `torment_fabric/torment_stress_harness/stress_substrate_audit.py` — the audit tool re-run by Commit δ
- `torment_fabric/docs/HIVEMIND_GUIDE.md` §13 Invariant 2 — substrate invariant FILTER-A enforces
- `torment_fabric/docs/PROVENANCE_DOCTRINE_v2.4.x.md` Invariant C — "one canonical derivation" principle that motivates a single `filter_llm_facing` helper
- `torment_fabric/docs/SPINE_CONTRACT.md` §3 — operation classes + trust tiers used to authorize raw mode
- `torment_fabric/docs/CHARACTER_SYSTEM.md` Files — retrieval assembler + fabric layout this fix touches
- `torment_fabric/docs/DOCTRINE_v2.4.x.md` — TORMENT doctrine: provenance is a hard boundary; safe defaults; risky features gated
- User + GPT exchange 2026-05-04 — ratified entry 01 as fix-now; agreed on hard-exclude default, narrow scope, trust-tier conditionality, behavior-change documentation
