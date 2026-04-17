# Archivist Writeback Gate-Flip Framing (v2.4.x)

**Status:** RATIFIED 2026-04-17 — all six decisions closed. Next: implementation deliverables per §6, then opt-in clearance.

**Filed:** 2026-04-17
**Pattern reference:** `docs/REINFORCE_CONTRACT_FRAMING_v2.4.x.md` (same draft → ratify → code discipline)
**Risk reference:** `.auto-memory/project_archivist_gate_risk.md`
**Recursion safety:** `docs/RECURSION_SAFETY_POLICY_v2.4.x.md`
**Step 6 closure:** `docs/RELEASE_NOTES_v2.4.4.md`, `.auto-memory/project_step6_operational_closure.md`

---

## 1. Context

`TORMENT_ARCHIVIST_WRITEBACK` has been `0` since v2.4.2 (first introduced) through v2.4.4. The gate exists because archivist writeback is the only path in TORMENT where the system writes back into its own memory based on its own cognition output — the cognition→memory loop. Every other ingest path (`torment_ingest`, `torment_tool_result_ingest`, `torment_reinforce`) is triggered by an external caller providing content. Writeback is the system talking to itself.

The gate stayed off while three classes of prerequisite work landed:

1. **Provenance plumbing (v2.4.2–v2.4.3).** `ProvenanceV1` schema, `normalize_parent()`, `for_cognition_writeback()` factory, `WRITE_COGNITION_WRITEBACK` write path, `SOURCE_ROLE_OUTPUT` source type. Without provenance, writeback memories would be indistinguishable from user ingest — no ancestry tracking, no guard input.

2. **Recursion guard (v2.4.3, step 5).** Bounded-DFS ancestry walk replacing the one-hop inline check. Closes the crash path on legacy bare-string provenance and the multi-hop laundering gap. Fail-closed on unknown, malformed, or depth-exceeded ancestry. 33+ tests. This is the load-bearing safety layer.

3. **Migration subsystem (v2.4.4, step 6).** Legacy bare-string provenance rows can now be walked through a two-gate policy and rewritten. Migration-refused rows (`SOURCE_GATE1_UNRECOVERABLE`) are rejected by the recursion guard at walk time. The guard and the migration writer are proven end-to-end on a live workspace.

All three prerequisites are now on `main` and validated. The question this framing addresses is not "is the guard safe?" — it is "what corpus evidence and operational conditions are required before the gate flips on?"

---

## 2. Doctrinal register

Anchor sentence, load-bearing:

> *Archivist writeback is a governed self-write: the system earns the right to remember its own cognition output by proving the ancestry is clean, the provenance is honest, and the recursion guard admits the candidate.*

Unpacked:

- **"Governed self-write"** — writeback is not autonomous memory creation. It is a specific, governed path through the Spine (full cognition → archivist approval → recursion guard → ingest). Every layer has veto power.
- **"Earns the right"** — the gate default is off. Turning it on is a deliberate operational decision, not an implementation detail. The system does not assume it can write to itself.
- **"Ancestry is clean"** — the recursion guard walks parent EIDs to depth 3. Any archivist-origin, collective-echo, derived, migration-refused, or unknown ancestry causes rejection. This is the anti-laundering invariant.
- **"Provenance is honest"** — writeback memories carry `source_role: "archivist_writeback"`, `write_path: "cognition_writeback"`, `parent_eids: [...]`. They are self-declaring. Future retrievals, drift checks, and further guard walks can see exactly what they are and where they came from.
- **"Recursion guard admits"** — the guard is fail-closed. It is the single source of truth on ancestry safety. No other path overrides it.

---

## 3. What writeback IS

1. **A cognition→memory feedback loop.** The archivist reviews proposals from Interpreter/Engineer/Skeptic, approves or rejects them, and approved proposals are ingested back as memories with writeback provenance.
2. **Scoped to the cognition pipeline.** Only `cognition/pipeline.py::_write_back_approved()` can trigger writeback. There is no MCP surface, no REST endpoint, no Spine fast-path for writeback. It runs inside `run_cognition_pipeline()` only.
3. **Guard-gated.** Every approved proposal passes through `recursion_guard_check()` before ingest. The guard has veto power independent of the archivist's approval.
4. **Provenance-tagged.** Writeback memories carry `ProvenanceV1.for_cognition_writeback()` with `source_role="archivist_writeback"` and explicit `parent_eids`. They are permanently distinguishable from user ingest.

---

## 4. What writeback is NOT

1. **Not autonomous action.** Writeback does not call tools, send messages, or modify external state. It only ingests text back into the memory graph.
2. **Not a bypass of the Spine.** Writeback runs inside the full cognition path, which is itself governed by the Spine. The Spine's trust tier, escalation, and drift enforcement all apply before writeback is reached.
3. **Not self-amplifying by construction.** The recursion guard rejects any proposal whose ancestry includes archivist-origin provenance. A writeback memory cannot be the parent of another writeback memory (Rule A/E). This is the structural anti-loop.
4. **Not retroactive.** Flipping the gate on does not rewrite existing memories. It only enables future cognition runs to produce writeback. Existing corpus is unchanged.
5. **Not the archivist writeback gate on the Spine path.** The Spine's `_full_cognition()` deliberately omits `lookup_fn` and `ingest_fn` (see §5.2). This means the Spine slow path is structurally read-only even with the gate on. Only `app.py /cognition/run` passes both functions.

---

## 5. Known gaps requiring decisions

### 5.1 Spine path divergence (lookup_fn / ingest_fn)

**Observation:** `spine.py:1012-1028` documents that `_full_cognition()` does NOT pass `lookup_fn` or `ingest_fn` to `run_cognition_pipeline()`. This means the Spine slow path — reached via MCP tools, `/spine/submit_task`, and escalated operations — silently produces no writes even when `TORMENT_ARCHIVIST_WRITEBACK=1`.

The `app.py /cognition/run` endpoint DOES pass both (lines 2236-2237), with a correct `_lookup_memory_payload` pattern.

**Two candidate positions:**

- **(a) Spine full-cognition is intentionally read-only.** Document it. MCP-surface cognition observes but does not self-write. Only the direct `/cognition/run` endpoint can produce writeback. This is the narrower, safer position — fewer write surfaces to audit.
- **(b) Spine full-cognition must mirror `/cognition/run`.** Add `lookup_fn` and `ingest_fn` to the Spine path using the same `_lookup_memory_payload` pattern. This closes the divergence but widens the writeback surface to include Spine-escalated operations.

**Flagged by:** contract audit (2026-04-12), documented at `spine.py:1012-1028` and `docs/AUDIT_cognition_pipeline_v2.4.x.md`.

### 5.2 Corpus verification

**Observation:** The recursion guard was validated against `ws_dimlock` (82 EIDs, 79 with provenance, 3 null) during step 6 closure. This is a small, well-understood workspace. A production-scale corpus may contain provenance shapes, ancestry depths, or legacy patterns that the closure run did not exercise.

**Question:** Is a single workspace verification sufficient, or should the guard be re-verified against every active workspace before the gate flips on? The conservative answer is "every workspace" — but the practical answer may be "one representative workspace plus the structural guarantees of normalize_parent and fail-closed posture."

### 5.3 Drift enforcement on writeback proposals

**Observation:** The pipeline's drift check (`drift_check_fn`) blocks identity-sensitive proposals when drift is in hard-block territory. This was wired into the Spine path at `a246301` (2026-04-12), fixing the original gap. On the `app.py /cognition/run` path, `make_live_drift_check(fabric)` provides live drift measurement.

**Question:** Is the drift enforcement sufficient to prevent identity-destabilizing writeback? The guard prevents ancestry laundering, but drift enforcement prevents content that moves the identity needle too far. Both layers must hold.

### 5.4 Observability of writeback events

**Observation:** When writeback occurs, the pipeline logs at INFO level (`"Archivist write-back ACCEPTED"` / `"REJECTED"`) and returns a `writeback_results` list in the pipeline output. There is no dedicated MCP surface or `/debug` endpoint for writeback audit.

**Question:** Is logging sufficient, or does the gate-flip require a new observability surface (e.g., `/debug/writeback_history`) before going live? The conservative answer is "logging is sufficient for initial activation" — the operator can inspect logs. A dedicated surface can follow if writeback becomes a routine operation.

---

## 6. Gate-flip criteria (proposed)

The gate flips from `0` to `1` when ALL of the following are satisfied:

### 6.1 Guard re-verification (structural)

Run `recursion_guard_check` against every memory EID in every active workspace used with `TORMENT_CHARACTER_ENABLE=1`. For each EID, construct the parent-EID chain and verify the guard correctly admits or rejects it. Zero guard failures on well-formed provenance.

**Why:** The step-6 closure proved the guard works on `ws_dimlock`. Re-running against the operator's actual corpus proves it works on the population that will be live when the gate is on.

**Deliverable:** a re-verification script (extending `step6_guard_reverify_live.py` or similar) that outputs a pass/fail summary per workspace.

### 6.2 Dry-run writeback (behavioral)

Run the cognition pipeline with `TORMENT_ARCHIVIST_WRITEBACK=1` on a test workspace against representative queries. Inspect:

- How many proposals does the archivist approve per query?
- How many pass the recursion guard?
- What do the writeback memories look like (content, provenance, parent_eids)?
- Does drift enforcement block when expected?
- Is the ingested summary searchable and non-degenerate?

**Why:** Structural verification proves the guard is correct. Behavioral verification proves the pipeline produces useful writeback — not noise, not degenerate summaries, not identity-destabilizing content.

**Deliverable:** a dry-run report showing proposal counts, guard decisions, and sample writeback content.

### 6.3 Spine path decision (§5.1)

Ratify whether the Spine full-cognition path is intentionally read-only (position a) or must mirror `/cognition/run` (position b). Document the decision. If (b), implement before the gate flip.

### 6.4 Rollback path

The gate must be flippable back to `0` instantly without data loss. Writeback memories are already tagged with `source_role: "archivist_writeback"` and `write_path: "cognition_writeback"`, so they can be identified and quarantined post-hoc if needed. No schema migration needed for rollback.

**Deliverable:** a documented rollback procedure: set `TORMENT_ARCHIVIST_WRITEBACK=0`, restart service, optionally run a cleanup script that marks writeback memories as quarantined.

---

## 7. Open decisions for ratification

Ratify these in order. Do not skip ahead. Do not flip the gate until all are ratified.

**Decision 1 — Spine path divergence (§5.1). RATIFIED 2026-04-17: (a).** Spine full-cognition is intentionally read-only. The `_full_cognition()` path does not pass `lookup_fn` or `ingest_fn`, and this is by design — it keeps the write surface narrow and matches the current doctrine comment at `spine.py:1012-1028`. If Spine writeback is ever wanted, that is a separate ratification. **What this forecloses:** position (b) is closed. No `lookup_fn`/`ingest_fn` wiring in Spine for this pass. **Deliverable:** update the doctrine comment at `spine.py:1012-1028` from a question to a ratified stance.

**Decision 2 — Corpus verification scope (§5.2). RATIFIED 2026-04-17: (a).** Re-verify the recursion guard against every active workspace used with `TORMENT_CHARACTER_ENABLE=1`. The gate has been off for months; the cost of running the script is low; the cost of missing a malformed provenance shape is an incident. **What this forecloses:** positions (b) and (c). No partial verification. **Deliverable:** a re-verification script that outputs a pass/fail summary per workspace, run against all active workspaces with zero failures.

**Decision 3 — Observability requirement (§5.4). RATIFIED 2026-04-17: (a).** INFO-level logging is sufficient for initial activation. Every acceptance and rejection is logged with proposal IDs and rejection reasons. A dedicated `/debug/writeback_history` endpoint can follow as a quality-of-life improvement if writeback becomes routine. **What this forecloses:** position (b) as a blocker. Observability improvements are welcome but do not gate the flip.

**Decision 4 — Dry-run writeback requirement (§6.2). RATIFIED 2026-04-17: (a).** Mandatory dry-run writeback report before any flip. Structural safety (guard correctness) is necessary but not sufficient — the operator must also inspect the content the archivist actually produces to verify it is useful, non-degenerate, and not identity-destabilizing. **What this forecloses:** position (b). No flip without behavioral evidence. **Deliverable:** a dry-run report showing proposal counts, guard decisions, and sample writeback content from representative queries.

**Decision 5 — Rollback procedure scope. RATIFIED 2026-04-17: (b).** Documented rollback: set `TORMENT_ARCHIVIST_WRITEBACK=0`, restart service, then optionally run a quarantine script that identifies all writeback memories by `write_path: "cognition_writeback"`. The quarantine step is cheap and closes the "what if writeback produced bad memories?" recovery question. **Deliverable:** (1) documented rollback procedure, (2) quarantine script that can list/tag/remove writeback memories.

**Decision 6 — Gate-flip authorization. RATIFIED 2026-04-17: opt-in first.** After Decisions 1–5 deliverables are met, the gate is operationally cleared for `TORMENT_ARCHIVIST_WRITEBACK=1` but the code default stays `"0"`. The operator must explicitly set the env var. Flip to default-on only after a period of incident-free opt-in use, following the same pattern as the `TORMENT_THINKING_ADVISORY` default-on decision. **What this forecloses:** immediate default-on. The gate earns promotion through operational evidence, not ratification alone.

---

## 8. What this framing is NOT

1. Not a step-6 reopening. Step 6 (migration) is operationally closed. This framing is about the gate on a different subsystem (archivist writeback) that step 6 was groundwork for.
2. Not a kernel change. Writeback does not touch identity state, bands, or the coupled-oscillator engine.
3. Not an MCP surface change. No new tools, no new Spine operations. The writeback path already exists behind the gate.
4. Not a test-matrix expansion beyond what the gate criteria require. The guard already has 33+ tests. The framing requires operational verification, not new unit tests.
5. Not a reinforce or feedback change. Both are orthogonal and stay untouched.

---

## 9. Re-entry reference

If this work is paused or picked up later, the load-bearing pieces to re-read in order:

1. The anchor sentence in §2.
2. The ratified decisions in §7 — especially D1 (Spine read-only) and D6 (opt-in first).
3. The gate-flip criteria in §6 — these are the deliverables that must be met before opt-in clearance.
4. The known gaps in §5 for context on what was decided and why.

All six decisions are ratified. Do not restart the framing discussion. The next step is the implementation deliverables: Spine doctrine comment (D1), re-verification script + run (D2), dry-run writeback report (D4), quarantine script (D5), rollback doc (D5).
