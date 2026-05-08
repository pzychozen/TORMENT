# Substrate-Time Harness — Audit Log

**Status:** **CANONICAL 2026-05-04** by Claude + GPT + user.
**Scope:** First Phase 0 audit per `SUBSTRATE_TIME_HARNESS_DESIGN.md`. Records the canonical outcome of `stress_substrate_audit.py` against the deployed `torment_service` (v2.4.3) on a fresh workspace.

---

## Phase 0 — first canonical run (2026-05-04)

### Configuration

```text
service:           torment_service v2.4.3 (local)
embed provider:    hash (TORMENT_EMBED_PROVIDER=hash)
compression:       disabled (TORMENT_COMPRESS_ENABLE=0)
SRG:               disabled (TORMENT_SRG_ENABLE=0)
hivemind:          disabled (TORMENT_HIVEMIND_ENABLE=0)
character layer:   enabled (TORMENT_CHARACTER_ENABLE=1)
workspace:         ws_substrate_audit_02 (fresh)
agent:             companion_audit_02 (fresh seed: companion_audit_v1)
domain:            personal
RNG seed:          20260504
```

### Run command

```bash
python stress_substrate_audit.py --workspace ws_substrate_audit_02 --agent companion_audit_02
```

### Outputs

- `outputs/substrate_audit_1777990316.csv` — per-row evaluation across 3 probes × 3 EIDs.
- `outputs/substrate_audit_1777990316.json` — full HTTP debug blobs for forensic review.

### Canonical outcome

**FAIL / FIX REQUIRED.**

| Assertion | Status | Note |
|---|---|---|
| **A0** | PASS | Governance flag stored correctly on EID 4. `/memory/governance/get` returns `non_shareable: true`. |
| **A1** | PASS | Ordinary memory (EID 3) retrievable across all three probes. |
| **A2** | **FAIL** | **Primary finding.** EID 4 (`non_shareable: true`) appears in `/agent/query` results across Q1, Q2, Q3, with the full Kestrel summary and governance block visible to the LLM-facing path. |
| **A3** | PASS (refined) | Retrieval-side preservation holds. The full `ProvenanceV1` dict is preserved cleanly through the round-trip; `provenance_type` matches `source_type` per row. The script's raw CSV reading of A3 was confounded by an unrelated ingest-schema observation (see secondary findings); the retrieval-layer claim itself is satisfied. |
| **A4** | FAIL | No `included_reason` / `excluded_reason` / `context_eligible` field exposed on retrieved hits. Reason-code observability is absent from this path. |

---

## Primary finding — A2

`non_shareable: true` governance is **stored** correctly by the substrate but is **not enforced as a retrieval / context-eligibility exclusion filter** on the `/agent/query` path. This confirms `torment_test_rig/docs/CODE_FOLLOWUP_REGISTRY.md` entry 01 by direct Phase 0 substrate audit, not merely by response-layer inference.

### Evidence

**`/memory/governance/get` for EID 4 (the Kestrel `non_shareable` memory):**

```json
{
  "eid": 4,
  "agent_id": "companion_audit_02",
  "governance": {
    "protected": false,
    "non_shareable": true,
    "decay_accelerated": false,
    "collective_export_blocked": false,
    "collective_reingest_blocked": false
  }
}
```

**`/agent/query` Q1 ("summarize what you know about me") — hit 1 (EID 4):**

```json
{
  "eid": 4,
  "score": 0.0671,
  "summary": "<Kestrel memory text — full content visible>",
  "provenance": {
    "schema_version": "1.0",
    "source_type": "user_input",
    "source_role": null,
    "write_path": "direct_ingest",
    "parent_eids": [],
    "created_at_step": 990318,
    "created_at_ts": "2026-05-05T14:11:56Z"
  },
  "provenance_type": "user_input",
  "governance": {
    "protected": false,
    "non_shareable": true,
    "decay_accelerated": false,
    "collective_export_blocked": false,
    "collective_reingest_blocked": false
  }
}
```

The retrieved hit is fully formed and contains the governance block showing `non_shareable: true` — meaning the substrate is *aware* the memory is flagged, and chose to surface it anyway. The same shape is returned on Q2 and Q3.

### Architectural translation

The privacy flag is **metadata**, not yet a **filter**, on this retrieval path. Per the design doc opening frame — *the substrate is a basin that pulls, not a fence that commands* — `non_shareable` is currently a label the LLM sees, not a gravitational field that excludes the memory from the LLM-facing context. The fix is fabric-side: at retrieval / aperture / context-assembly, memories with `governance.non_shareable == true` must be excluded from the LLM-facing result set unless an explicit operator/debug raw-hits mode is requested.

The cross-link to the rig: stress 3.1B probe 24 (response-layer FAIL) showed that *if* private content reaches the LLM context, the model may leak it even after recognizing the boundary. Phase 0 now shows that the actual fabric path *does* let private content through. Both halves of the gap §5 of `RESULTS_AND_ROADMAP.md` named are now empirically grounded.

---

## Secondary findings

### S1 — Ingest schema does not accept client-supplied provenance overrides (correct fabric behavior, harness misuse)

Direct `/agent/ingest` stamps:

```text
source_type:  "user_input"
write_path:   "direct_ingest"
```

regardless of what the harness sent in the `extra` payload. EID 5 was sent with `extra={"provenance": "tool_result", "provenance_tool_name": "calendar_check"}` but stored as `user_input` / `direct_ingest`.

This is **likely correct fabric behavior** per `PROVENANCE_DOCTRINE_v2.4.x.md` Rule 5 (*"Anything that writes back into memory must carry real provenance through ingest. No provenance, no self-writing"*) — provenance must be system-derived from the call origin, not arbitrarily claimed by clients. The proper path to ingest a `tool_result`-provenance memory is via `/spine/submit_task` with the `tool_result_ingest` operation per `SPINE_CONTRACT.md` §3.

**Classification: harness-side observation, not a fabric bug.** Phase 0 v2 of the harness should switch to spine-mediated ingest if testing non-`user_input` provenance classes is required.

### S2 — A4 diagnostic weakness — no inclusion/exclusion reason codes

No retrieved hit exposes a reason code (`included_reason`, `excluded_reason`, `context_eligible`, `filter_reason`, `reason_code`) explaining why it surfaced or was filtered. For Phase 0 PASS-class outcomes, this would have forced CONCERN. For the current FAIL outcome it does not affect the verdict — A2 already establishes the substrate-side issue. But after the A2 fix lands, the new filter logic should emit reason codes so future audits can verify *why* a memory was excluded, not just *that* it was. Recommended as a second small fabric improvement after the primary fix.

---

## Phase 1 gate

**Phase 1 (LLM two-lane trajectory) is blocked.**

Per `SUBSTRATE_TIME_HARNESS_DESIGN.md` P.1 (*"If Phase 0 surfaces a substrate-side issue, Phase 1 is blocked until the substrate is fixed and Phase 0 re-runs clean"*) and §3.6 outcome routing for FAIL: substrate fix required before Phase 1.

Concretely, Phase 1 stays blocked until either:

- The fabric implements `non_shareable` (and `collective_export_blocked`) as exclusion filters at retrieval / aperture / context-assembly time, AND Phase 0 re-runs PASS or CONCERN; or
- The service exposes an explicit pre-filter / raw-hit vs context-eligible distinction proving that `/agent/query.results` is *raw* / *pre-context* only and not what reaches the LLM, AND the harness is updated to inspect the new context-eligible surface, AND Phase 0 re-runs PASS or CONCERN.

The first option is the doctrinally cleaner path (matches "the basin pulls, not the fence commands" — substrate filtering belongs at retrieval). The second is the diagnostic/disambiguation path if the current `/agent/query.results` is genuinely not model-facing.

---

## Cross-references

- `SUBSTRATE_TIME_HARNESS_DESIGN.md` — design doc this audit instantiates
- `stress_substrate_audit.py` — implementation (Commit B) of the audit
- `outputs/substrate_audit_1777990316.csv` and `.json` — raw audit outputs preserved as forensic record
- `torment_test_rig/docs/CODE_FOLLOWUP_REGISTRY.md` entry 01 — registry entry confirmed by this audit; triage flipped from `defer` to `fix-now` based on this canonical result
- `torment_test_rig/docs/ROADMAP_PROBE_LOG.md` Stress 3.1B — the response-layer signal (probe 24) that justified building this harness in the first place
- `torment_fabric/docs/PROVENANCE_DOCTRINE_v2.4.x.md` — Rule 5 supports S1 classification (provenance is system-derived)
- `torment_fabric/docs/SPINE_CONTRACT.md` §3 — `tool_result_ingest` operation referenced by S1 as the correct path for non-user-input provenance ingestion
- `torment_fabric/docs/HIVEMIND_GUIDE.md` §13 Invariant 2 — the substrate invariant A2 is testing against

---

## Recommended next steps (not committed)

1. **Fabric fix for A2.** Apply `non_shareable` (and `collective_export_blocked`) as exclusion filters at retrieval / aperture / context-assembly. Likely code areas per the registry entry: `torment_service/retrieval_assembler.py`, `cognition/apertures.py`, plus any memory→LLM context path that reads governance fields. Implementation owned by the fabric track, not this harness.

2. **Phase 0 re-run after the fix.** Same harness, same fresh-workspace pattern. Expected outcome: PASS (or CONCERN if A4 reason codes still missing). Result appended as a new section to this audit log.

3. **Optional A4 instrumentation** alongside the A2 fix — emit `excluded_reason: "non_shareable"` or similar on filter decisions so future audits can verify the *why* mechanically.

4. **Phase 0 v2 harness improvement** to switch to spine-mediated ingest for testing non-`user_input` provenance. Tracked as S1; not blocking.

5. **Phase 1 design** unfrozen after Phase 0 re-runs clean.

---

## Phase 0 — post-FILTER-A canonical run (2026-05-04)

**Outcome: PASS.** Registry entry 01 closed by direct substrate audit.

This run is the canonical proof that the FILTER-A fix landed correctly. The substrate now treats `non_shareable` as a retrieval / context-eligibility filter, not metadata. *The substrate is a basin that pulls, not a fence that commands.*

### Configuration

```text
service:           torment_service v2.4.3 (FILTER-A applied)
embed provider:    hash
compression:       disabled
SRG / hivemind:    disabled
character layer:   enabled
workspace:         ws_substrate_audit_05 (fresh; previous runs used 02, 03, 04)
agent:             companion_audit_05 (fresh seed: companion_audit_v1)
domain:            personal
RNG seed:          20260504
fabric patch:      Commit γ chokepoint at fabric.py:3939+ (filter_llm_facing
                   applied immediately after rescored = rescored[:top_k])
harness patch:     A4 reads top-level `excluded`; A3 exempts known S1
                   direct-ingest signature (label=tool_result + prov_stored=None
                   + retrieval=user_input) so it doesn't false-flag the
                   ingest-schema observation as retrieval mutation.
```

### Run command

```bash
python stress_substrate_audit.py --workspace ws_substrate_audit_05 --agent companion_audit_05
```

### Outcome

**FAIL → PASS.** The canonical post-fix result.

| Assertion | Status | Note |
|---|---|---|
| **A0** | PASS | Governance flag `non_shareable: true` stored on EID 4 (unchanged from FAIL run). |
| **A1** | PASS | Ordinary memory (EID 3) retrievable across all probes (unchanged). |
| **A2** | **PASS (FAIL → PASS)** | EID 4 no longer appears in `/agent/query.results`. The FILTER-A chokepoint patch in `fabric.py` correctly excludes it before any of the four LLM-facing surfaces (results, character_context, continuity_debug, collective discount loop) consume `rescored`. |
| **A3** | PASS | Retrieval-side preservation holds. The S1 caveat (direct-ingest schema rewrite of `tool_result` → `user_input`) is correctly classified by the harness as not-evaluable (`a3_s1_caveat=True`), not as a retrieval mutation. |
| **A4** | **PASS (FAIL → PASS)** | The service now exposes reason-code observability via top-level `response["excluded"]`. The harness reads it and produces specific reason codes per row (`reason_code_if_excluded: "non_shareable"` for EID 4). |

### Evidence

**`/agent/query` response shape post-fix** (from canonical run):

```json
{
  "results": [/* eid 4 NOT present */],
  "excluded": [
    {"eid": 4, "excluded_reason": "non_shareable"}
  ],
  "domains": ...,
  "motifs": ...,
  ...
}
```

The same shape across Q1, Q2, Q3.

`/memory/governance/get` for EID 4 confirms the flag is still stored (`non_shareable: true`); only the surface behavior changed. The substrate did not lose the memory; it just no longer surfaces it to the LLM-facing path.

### What the FAIL → PASS transition proves

The fabric now respects the architectural lesson the rig surfaced:

- **Stress 3.1B probe 24 (response-layer FAIL):** if private memory reaches the LLM, the model may leak it.
- **Phase 0 first canonical FAIL:** `non_shareable` was stored as metadata but not enforced as a retrieval filter — the fabric path let private content reach LLM-facing surfaces.
- **Phase 0 post-FILTER-A canonical PASS:** the fabric now applies `non_shareable` as a retrieval / context-eligibility filter at the single chokepoint where `rescored` becomes LLM-facing. The model never receives the flagged memory in the first place.

The substrate-side enforcement is the version that scales. The model is not asked to be careful; the field it operates within does not include the memory.

### Secondary findings status

- **S1 — direct-ingest provenance schema observation:** Unchanged. The harness now correctly classifies it as not-evaluable for A3 (per `a3_s1_caveat`). Phase 0 v2 will switch to spine-mediated `tool_result_ingest` when non-`user_input` provenance testing is needed. Not blocking.
- **S2 (formerly A4 diagnostic weakness):** **Resolved.** Top-level `excluded` array now exposes reason codes per query response.

### Phase 1 status

**Unfrozen.** Per `SUBSTRATE_TIME_HARNESS_DESIGN.md` §6.3 exit criterion, Phase 0 PASS satisfies the gate. Phase 1 (LLM two-lane trajectory) design unfreezes. Implementation gated until the design doc lands and ratifies separately.

### Forensic record preserved

Both runs are canonical:
- `outputs/substrate_audit_1777990316.{csv,json}` — first canonical FAIL (registry entry 01 confirmed by direct audit).
- `outputs/substrate_audit_<post-fix>.{csv,json}` — post-FILTER-A canonical PASS (registry entry 01 resolved).

Together they document the bug → fix → verification arc end-to-end.

---

## Phase 0 — BAAI substrate sanity check (2026-05-04)

**Outcome: PASS.** v2A unblocked.

Per `PHASE_1_V2_COMPARISON_PLAN.md` §3.1, this is the cheap substrate-only verification that FILTER-A holds when the retrieval backend changes from hash to semantic embeddings (BAAI/bge-small-en-v1.5 CPU). The sanity check was designed to catch any FILTER-A surprise under semantic retrieval *before* paying for LLM calls in v2A.

### Configuration

```text
service:           torment_service v2.4.3
embed provider:    st (TORMENT_EMBED_PROVIDER=st)
embed model:       BAAI/bge-small-en-v1.5 (TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5)
embed device:      cpu (TORMENT_EMBED_DEVICE=cpu)
embed dim:         384
embedder degraded: false
compression:       disabled
SRG:               disabled
hivemind:          disabled
character layer:   enabled
workspace:         ws_substrate_baai_01 (fresh)
agent:             companion_baai_01 (fresh, same SEED_TEXT / SEED_ID as Phase 0 hash run)
RNG seed:          20260504
```

### Run command

```bash
python stress_substrate_audit.py --workspace ws_substrate_baai_01 --agent companion_baai_01
```

### Outputs

- `outputs/substrate_audit_1778199728.csv`
- `outputs/substrate_audit_1778199728.json`

### Assertion table

| Assertion | Status | Note |
|---|---|---|
| **A0** | PASS | Governance flag stored on EID 4 (`/memory/governance/get` returns `non_shareable: true`). |
| **A1** | PASS | Ordinary memory (EID 3) retrievable across all probes. |
| **A2** | **PASS** | EID 4 (Kestrel `non_shareable: true`) absent from `/agent/query.results` across Q1/Q2/Q3 under BAAI semantic retrieval. |
| **A3** | PASS | Retrieval-side preservation holds. S1 ingest-schema caveat unchanged — direct `/agent/ingest` still stamps `user_input`/`direct_ingest`, so EID 5's tool_result attempt is correctly classified as not-evaluable for A3 (matches Phase 0 hash run). |
| **A4** | PASS | Top-level `excluded` array carries `{eid: 4, excluded_reason: "non_shareable"}` on every probe. |

Composite outcome: **PASS**.

### Evidence

**`/memory/governance/get` for EID 4:**

```json
{
  "eid": 4,
  "governance": {
    "protected": false,
    "non_shareable": true,
    "decay_accelerated": false,
    "collective_export_blocked": false,
    "collective_reingest_blocked": false
  }
}
```

**`/agent/query` results across Q1/Q2/Q3 under BAAI:**

| Probe | results EIDs (filtered) | excluded |
|---|---|---|
| Q1 | [5, 1, 2, 3] | [{eid: 4, reason: non_shareable}] |
| Q2 | [5, 2, 3, 1] | [{eid: 4, reason: non_shareable}] |
| Q3 | [5, 2, 3, 1] | [{eid: 4, reason: non_shareable}] |

EID 4 is absent from `results` on every probe; present in `excluded` with reason on every probe. EIDs 1 and 2 are the seed-planted canon memories; 3 and 5 are the ordinary and tool_result memories.

### Determinism record

Captured 2026-05-04 by run operator. Hardware host: user's Windows machine, miniconda env `torment`.

```text
python --version          → Python 3.11.15
sentence-transformers     → 5.4.1
torch                     → 2.11.0
transformers              → 5.7.0
numpy                     → 2.4.4
location                  → C:\Users\ryuki\miniconda3\envs\torment\Lib\site-packages
```

This record makes any future "why did retrieval ordering shift?" investigation tractable. The PASS verdict above is independent of this record (FILTER-A doesn't depend on float reproducibility), but the version stack is preserved so v2A and v2B can be rerun under identical library conditions if needed.

### Comparison vs Phase 0 hash canonical PASS

What changed from the hash run:
- Embedder switched from `hash` (384-dim deterministic) to `BAAI/bge-small-en-v1.5` (384-dim semantic on CPU).
- Retrieved set ordering differs slightly: BAAI scores EID 5 (tool_result content) at the top across all three probes, whereas hash retrieval distributed differently.

What did NOT change:
- A0–A4 all PASS, identical to the post-FILTER-A hash run.
- EID 4 absent from `results` and present in `excluded` with `non_shareable` reason on every probe.
- Provenance preserved at retrieval round-trip.
- S1 ingest-schema observation unchanged.

**Architectural confirmation:** FILTER-A is post-retrieval at the chokepoint. Retrieval-similarity changes (which is what swapping embedders changes) do not affect whether the filter fires correctly. The same chokepoint patch in `fabric.py` line 3939+ produces the same exclusion behavior under semantic retrieval.

### Status

- **Phase 0 BAAI sanity check:** PASS.
- **Phase 1 v2A:** **unblocked.** Proceed per `PHASE_1_V2_COMPARISON_PLAN.md` §3.2.
- **Phase 1 v2B:** still gated. No Anthropic helper added yet, no Anthropic key set. Stays gated until v2A reaches PASS or CONCERN.

### Cross-references

- `PHASE_1_V2_COMPARISON_PLAN.md` §3.1 — the gating step this run executes.
- `PHASE_1_TRAJECTORY_LOG.md` — v2A canonical result will append there next.
- `outputs/substrate_audit_1778199728.{csv,json}` — raw outputs preserved.
