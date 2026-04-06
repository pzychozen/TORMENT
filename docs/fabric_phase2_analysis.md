# fabric.py — Phase 2: Static Logic Review + Phase 1 Corrections

**File:** `torment_service/fabric.py`
**Date:** 2026-04-01

---

## Phase 1 Corrections

### C1: Local file is truncated — REAL ISSUE

The local working copy of `fabric.py` ends at line 4277 mid-signature. Git HEAD has 4384 lines. The missing 107 lines contain:

- `trace_view()` — complete method
- `_trace_narrative()` — complete helper
- `dominant_thread()` — module-level helper
- `random_chance()` — module-level helper (used by ingest at line 2247 and 2842)
- `_affect_state_path()`, `_load_affect_state()`, `_save_affect_state()` — affect state persistence

The truncation likely happened during a save/edit (CRLF conversion issue — local file has CRLF, git HEAD has LF). The git HEAD version is complete and correct. **The user should restore from git**: `git checkout -- torment_service/fabric.py`

### C2: `ensure_within_base` is NOT imported by fabric.py — CONFIRMED

Phase 1 incorrectly listed `ensure_within_base()` as a direct dependency. Fabric.py imports `save_checkpoint`, `load_latest_checkpoint`, `build_shard_snapshot` from checkpoint.py. Those functions internally use `ensure_within_base`. Fabric.py never touches it directly. Corrected in Phase 1 doc.

### C3: `_anchor_state_path` has NO validation — NEWLY FOUND

`_symbol_state_path` (line 268) calls `_validate_path_component` on both workspace_id and agent_id.
`_affect_state_path` (line 4340) calls `_validate_path_component` AND does a `startswith` containment check.
`_anchor_state_path` (line 233) does NEITHER — it's a bare `os.path.join` with no validation at all.

This is an inconsistency. All three do the same job (build agent-scoped file paths). Two are validated, one is not.

### C4: Section line ranges are approximate but correct

The Phase 1 section map boundaries are within ±5 lines of actual. No major shifts needed.

### C5: Concurrency risk upgraded to MEDIUM — CONFIRMED

See detailed findings below. The Spine layer DOES serialize ingest/feedback but NOT query.

---

## Phase 2 Issue List

### ISSUE 1: `query()` is NOT serialized — **Needs dependency inspection**

**Finding:** The Spine layer (`spine.py`) acquires `agent_lock` for:
- `_fast_ingest` (line 358)
- `_fast_feedback` (line 373)
- `_fast_collective_reingest` (line 389)

But `app.py` line 871-882 calls `fabric.query()` **directly** — no Spine, no lock.

**What query reads (shared mutable state):**
- `self.agent_states[ak]` — not mutated by query, but could be mid-mutation by a concurrent ingest
- `self.private_graphs[ak]` — `.search()` reads while ingest's `.spawn_memory()`/`.flush_node()` could be writing
- `ws.shared_graphs[d]` — same read-write race
- `ws.motif_regs[d]` — centroid reads while ingest's `attach_or_create` mutates

**Classification:** Real bug risk if FastAPI/uvicorn handles concurrent requests (it does with async workers). A query during an ingest could read partially-written graph state.

**Severity:** Medium — in practice, race window is small and Python's GIL prevents memory corruption, but logical inconsistency (reading half-flushed entity) is possible.

**Action:** Verify whether this is intentional (query is read-only so maybe acceptable) or whether query should also go through Spine. Do NOT add locks without understanding performance implications.

### ISSUE 2: `_anchor_state_path` missing validation — **Real bug risk**

**Finding:** Three parallel path helpers exist:
```
_anchor_state_path(data_dir, workspace_id, agent_id)  → NO validation
_symbol_state_path(data_dir, workspace_id, agent_id)  → _validate_path_component on both
_affect_state_path(data_dir, workspace_id, agent_id)  → _validate_path_component + startswith check
```

`_anchor_state_path` is called by `_load_anchor_state` and `_save_anchor_state`, which are called from `_maybe_emit_identity_anchor` and `_refine_identity_anchors`. Both of those receive `agent_id` from `ingest()` which gets it from the API layer.

**Classification:** Real inconsistency. The app layer validates `agent_id` via Spine/request parsing, so practical exploitation requires bypassing the API. But it's a defense-in-depth gap.

**Safe fix:** Add `_validate_path_component(workspace_id, "workspace_id")` and `_validate_path_component(agent_id, "agent_id")` to `_anchor_state_path`. Two lines, zero behavior change.

### ISSUE 3: `_embed_audit_path` validates workspace_id but not the full path — **Analyzer-confusing but behaviorally OK**

**Finding:** `_embed_audit_path` (line 171) calls `_validate_path_component(workspace_id)` then returns `os.path.normpath(os.path.join(...))`. This blocks traversal but CodeQL can't see that `_validate_path_component` is a sanitizer.

**Classification:** Likely CodeQL false positive. No behavior change needed.

**Safe fix (optional):** Add `os.path.realpath` + `startswith` check like `_affect_state_path` does. This would satisfy CodeQL without changing behavior.

### ISSUE 4: `clone_workspace` follows symlinks during copy — **Needs dependency inspection**

**Finding:** `_copytree_filtered` (line 1596) uses `os.walk(src)` which follows symlinks by default, and `shutil.copy2(srcp, dstp)` which also follows symlinks.

If a malicious symlink exists inside a source workspace directory, the clone could:
- Copy files from outside `data_dir` into the target workspace
- Exfiltrate data by symlinking to sensitive paths

**Classification:** Real but low-probability. Requires attacker to already have write access to workspace directories.

**Safe fix:** Add `followlinks=False` to `os.walk(src)` (it's False by default, so this is already safe!). For `shutil.copy2`, add `follow_symlinks=False`. One-line change.

**Wait — re-checking:** `os.walk` default `followlinks` is `False`. So the walk itself doesn't follow symlinks. But `shutil.copy2(srcp, dstp)` DOES follow symlinks by default — if a file in the workspace is a symlink to `/etc/passwd`, `copy2` would copy its content.

**Corrected classification:** The walk is safe but individual file copies follow symlinks. The fix is adding `follow_symlinks=False` to the `shutil.copy2` call.

### ISSUE 5: `_job_path` doesn't validate `kind` or `job_id` — **Analyzer-confusing but behaviorally OK**

**Finding:** `_job_path(self, kind, job_id)` (line 659) returns `os.path.normpath(os.path.join(self._jobs_root, kind, f"{job_id}.json"))`. Neither `kind` nor `job_id` are validated.

However: `kind` is always a hardcoded string (`"clone"` or `"repair"`) from fabric.py itself. `job_id` is generated by `uuid.uuid4()` internally. Neither comes from user input.

**Classification:** Analyzer-confusing (CodeQL might flag it) but no real risk.

### ISSUE 6: `Workspace.__init__` paths don't validate `workspace_id` — **Analyzer-confusing but behaviorally OK**

**Finding:** `Workspace.__init__` (line 302) builds paths like `domain_suggestions_path`, `domain_policies_path` using `workspace_id` without calling `_validate_path_component`. But `Workspace` is only created by `get_workspace()` which calls `_validate_path_component(workspace_id)` at line 592.

**Classification:** Validation happens at the caller, not the constructor. Behaviorally safe but CodeQL can't see the call chain.

### ISSUE 7: `ws = self.get_workspace(workspace_id)` called twice in `ingest()` — **Analyzer-confusing but behaviorally OK**

**Finding:** Lines 2123 and 2126 in `ingest()`:
```python
ws = self.get_workspace(workspace_id)
ak = self._agent_key(workspace_id, agent_id)
ident = self.create_agent(workspace_id, agent_id)
ws = self.get_workspace(workspace_id)  # ← second call
```

**Classification:** Not a bug. `create_agent` may modify workspace state (add domains, init agent), so re-fetching `ws` ensures the latest state. The first call is needed to exist before `create_agent`. Slightly wasteful but correct.

### ISSUE 8: `motif_ids` declared twice — **Analyzer-confusing but behaviorally OK**

**Finding:** In `ingest()`:
- Line ~2216 (git HEAD): `motif_ids: List[str] = []`
- Line ~2248 (git HEAD): `motif_ids: list = []`

The second declaration shadows the first. Both initialize to `[]`. The second one is inside the `allow_write` branch setup.

**Classification:** Cosmetic. The first declaration sets the default for the non-write path. The second re-declares for the write path. No behavior difference since both start at `[]`.

### ISSUE 9: `random_chance` defined at module bottom, used at line 2247 — **Behaviorally OK**

**Finding:** `random_chance()` is defined at line 4336 (git HEAD) but used in `ingest()` at line 2247. In Python, module-level functions can be called from anywhere as long as the module has finished loading. Since `random_chance` is a plain function (not inside a class), this is fine.

**Classification:** Not a bug. But note that the local truncated file is MISSING this function entirely, which would cause a runtime `NameError` if the truncated file were actually used.

### ISSUE 10: `_affect_state_path` has its own `startswith` containment check — **Inconsistent with other helpers**

**Finding:** `_affect_state_path` (git HEAD line 4340) does:
```python
safe_dir = os.path.normpath(data_dir)
base = os.path.normpath(os.path.join(...))
if not base.startswith(safe_dir):
    raise ValueError("Path escapes data directory")
```

This is a different pattern from `checkpoint.py`'s `ensure_within_base()` which uses `os.path.realpath`. The `normpath` version doesn't resolve symlinks.

**Classification:** Minor inconsistency. The `_validate_path_component` guard already blocks `..` so `normpath` is sufficient in practice. But if you ever want to unify the pattern, this one should switch to `realpath`.

---

## Safe Reshapes (smallest changes, no behavior change)

Listed in order of safety and value:

### S1: Add validation to `_anchor_state_path` (2 lines)
```python
def _anchor_state_path(data_dir: str, workspace_id: str, agent_id: str) -> str:
    _validate_path_component(workspace_id, "workspace_id")
    _validate_path_component(agent_id, "agent_id")
    return os.path.join(data_dir, "workspaces", workspace_id, "agents", agent_id, "anchors.json")
```
**Risk:** Zero — adds validation that all sibling helpers already have.

### S2: Add `follow_symlinks=False` to clone copy (1 line change)
```python
shutil.copy2(srcp, dstp, follow_symlinks=False)
```
**Risk:** Near-zero — prevents symlink following during workspace clones.

### S3: Restore truncated `fabric.py` from git HEAD
```
git checkout -- torment_service/fabric.py
```
**Risk:** Zero if there are no intentional local edits. The truncation removes `random_chance`, `_affect_state_path`, `trace_view`, and `_trace_narrative` — all of which are needed for the system to function.

---

## Dependency inspection still needed before any further changes

| Question | Where to look |
|----------|--------------|
| Is query intentionally unlocked? | Ask the original author / check git blame on spine.py for whether query was ever in Spine |
| Does `MemoryGraph.search()` tolerate concurrent `.spawn_memory()`? | `memory_graph.py` — check if entity dict access is atomic |
| Is `motif_ids` double-declaration intentional? | Git blame on the ingest function |
| Are there other callers of `_anchor_state_path` outside fabric.py? | `grep -rn '_anchor_state_path'` |

---

## Summary

- **1 real file issue** (truncation — needs immediate restore)
- **1 real inconsistency** (anchor path missing validation — safe 2-line fix)
- **1 real but low-probability security gap** (clone follows symlinks — safe 1-line fix)
- **1 concurrency question** (query unlocked — needs design intent check)
- **6 analyzer-confusing but behaviorally OK** items (dismissible or optional tidy-up)
- **0 items requiring broad rewrites**
