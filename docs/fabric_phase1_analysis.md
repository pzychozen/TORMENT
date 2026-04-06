# fabric.py — Phase 1 Structural Analysis

**File:** `torment_service/fabric.py`
**Lines:** 4,277
**Date:** 2026-04-01

---

## 1. Section Map

### A. Module-level helpers (lines 1–473)

| Lines | Function / Block | Responsibility |
|-------|-----------------|----------------|
| 1–37 | Imports | 20 internal modules, stdlib, numpy, FastAPI |
| 40–41 | `_JobCancelled` | Exception class for clone/repair cancellation |
| 45–121 | `_proposal_allowed()` | Rate-limit + novelty filter for auto-proposals |
| 123–128 | `_tokenize()` | Whitespace tokenizer for conflict detection |
| 131–165 | `_detect_canon_conflict()` | Jaccard + negation-based contradiction scoring |
| 167–168 | `_now_ts()` | Epoch timestamp helper |
| 171–230 | `_embed_audit_path/write/mark_dirty` | Embedding health audit persistence |
| 233–300 | `_anchor_state_path/load/save`, `_symbol_state_path/load/save` | Per-agent anchor + symbol state JSON I/O |
| 302–462 | `class Workspace` | Workspace container: graphs, motifs, bridges, proposals, conflicts, router, policies |
| 464–472 | `_validate_path_component()` | Path traversal guard for user-supplied identifiers |

### B. TormentFabric class — Init & Infrastructure (lines 475–870)

| Lines | Method | Responsibility |
|-------|--------|----------------|
| 475–567 | `__init__()` | Master init: embedder, kernel, stores, feature flags (12 env vars), job state, locks |
| 570–589 | `_get_sqlite_index()` | Lazy-init SQLite sidecar index per agent |
| 591–657 | `get_workspace()` | Get-or-create workspace, lock embed dim, init all subsystems |
| 630–657 | `list_workspaces_meta()` | Scan disk for workspace metadata |
| 659–727 | Job persistence helpers | `_job_path`, `_load_jobs`, `_persist_job`, `_prune_jobs` |
| 733–790 | Clone/repair job inspection | `list_clone_jobs`, `get_clone_job`, `list_repair_jobs`, `get_repair_job`, `cancel_repair_job` |

### C. Repair embeddings pipeline (lines 794–1122)

| Lines | Method | Responsibility |
|-------|--------|----------------|
| 794–882 | `start_repair_embeddings_job()` | Async job launcher (threaded) |
| 883–913 | `repair_embeddings()` | Synchronous repair entry point |
| 914–1122 | `_repair_embeddings_impl()` | Core repair: iterate all graphs, recompute embeddings, rebuild motifs |

### D. Character continuity subsystem (lines 1126–1520)

| Lines | Method | Responsibility |
|-------|--------|----------------|
| 1126–1136 | `_role_context()` | Role store query for soft guidance signal |
| 1137–1152 | `_embed_context()` | Embedder runtime info for UI/trace |
| 1155–1321 | `_maybe_emit_identity_anchor()` | Auto-detect + emit identity anchor (B-mode memory) |
| 1323–1441 | `_maybe_emit_mood_drift()` | Affect-based mood drift memory emission |
| 1442–1520 | `_refine_identity_anchors()` | Post-ingest anchor refinement via motif alignment |

### E. Workspace clone (lines 1521–1795)

| Lines | Method | Responsibility |
|-------|--------|----------------|
| 1521–1795 | `clone_workspace()` | Full workspace deep-copy with optional re-embedding |

### F. Agent creation + Hivemind infrastructure (lines 1796–2105)

| Lines | Method | Responsibility |
|-------|--------|----------------|
| 1796–1870 | `create_agent()` | Get-or-create agent identity, kernel state, graphs, optional subsystems |
| 1871–1886 | `_get_collective_field()` | Lazy-init CollectiveField (double-checked locking) |
| 1887–1900 | `_get_proposal_bridge()` | Lazy-init CollectiveProposalBridge (double-checked locking) |
| 1902–1935 | `_collective_query_context()` | Build informational collective context for query response |
| 1936–2105 | `reingest_convergence()` | Phase D3 re-ingestion: echo strength, provenance, terminal flag |

### G. Ingest pipeline (lines 2106–2867) — **LARGEST SECTION**

| Lines | Responsibility |
|-------|----------------|
| 2106–2149 | Entry, kernel process, summary, phase timer |
| 2150–2230 | Domain routing, embedding lock check, graph store |
| 2230–2350 | Motif attach/create, resonance, coherence field |
| 2350–2450 | Governance enrichment, symbol state, affect |
| 2450–2510 | Character drift check, gravity correction, checkpoint |
| 2510–2655 | Hivemind packet emission (outer gate → governance gate → coherence gate → build packet → convergence → proposal bridge) |
| 2655–2770 | Motif entropy, event-gated compression (Phase 6), SRG living memory |
| 2770–2867 | Checkpoint save, response assembly |

### H. Query pipeline (lines 2868–3481)

| Lines | Responsibility |
|-------|----------------|
| 2868–2900 | Entry, embedding, domain routing |
| 2900–2960 | Bridge peek (bounded fan-out into bridged domains) |
| 2960–3100 | Scoring: similarity, recency, motif alignment, contradiction risk, type bonuses |
| 3100–3250 | Character continuity context assembly |
| 3250–3400 | SRG living memory query context |
| 3400–3481 | Response assembly + optional collective context |

### I. Feedback + governance endpoints (lines 3483–3997)

| Lines | Method | Responsibility |
|-------|--------|----------------|
| 3483–3559 | `feedback()` | Overlay evolution via trust-region EMA updates |
| 3564–3567 | `decide_bridge()` | Manual bridge decision |
| 3570–3617 | `propose_share()` | Manual share proposal |
| 3618–3935 | `process_proposals()` | Approve/reject with write-through to shared graph |
| 3782–3805 | Motif entropy, merge, conflict endpoints | Read-only governance queries |
| 3825–3935 | `approve_domain_suggestion()`, `decide_proposal()` | Decision endpoints |
| 3938–3997 | `_maybe_suggest_domain()` | Auto-suggest domains from strong misaligned motifs |

### J. Trace / diagnostic endpoints (lines 3999–4277)

| Lines | Method | Responsibility |
|-------|--------|----------------|
| 3999–4009 | `list_bridges()` | Bridge listing with status filter |
| 4011–4119 | `trace()` | Explain scoring for specific memory EIDs |
| 4121–4155 | `memory_chain()` | Walk causal chain for a memory |
| 4156–4232 | `trace_full_graph()` | Full graph export (JSON/Mermaid) |
| 4233–4277 | `trace_bundle()`, `trace_view()` | Bundle export + view helpers |

---

## 2. Dependency Map

### Critical imports (used across multiple sections)

| Module | Used in | Critical functions imported |
|--------|---------|---------------------------|
| `memory_kernel` | Init, Ingest, Query | `TriOctaMemoryKernel` |
| `memory_graph` | Init, Ingest, Query, Clone, Repair | `MemoryGraph` |
| `identity` | Init, Ingest, Query, Feedback | `IdentityStore`, `AgentIdentity` |
| `motifs` | Init, Ingest, Query, Proposals | `MotifRegistry`, `cosine` |
| `checkpoint` | Init, Ingest | `save_checkpoint`, `load_latest_checkpoint`, etc. |
| `character` | Init, Ingest, Query | `CharacterStore`, `plant_seed`, `measure_drift`, `gravity_correction`, `derive_kernel_modulation` |
| `embeddings` | Init, Repair | `build_embedder_from_env`, `Embedder`, `embedding_checksum` |
| `scoring` | Query, Trace | `score_hit` |
| `agent_locks` | Init, Agent creation, Hivemind init | `AgentLockManager` |

### Lazy/conditional imports (loaded at runtime)

| Module | Loaded in | Condition |
|--------|-----------|-----------|
| `collective_field` | `_get_collective_field()` | `_hivemind_enable` |
| `collective_models` | Ingest hivemind block | `_hivemind_enable` |
| `collective_proposals` | `_get_proposal_bridge()` | `_hivemind_enable` |
| `collective_policy` | `reingest_convergence()` | `_hivemind_enable` |
| `phase_timer` | Ingest | Always (lazy for import order) |
| `event_detection`, `compression`, `deep_memory` | Ingest | `_compress_enable` |
| `srg_field` | Ingest/Query | `_srg_enable` |
| `index_manager` | `_get_sqlite_index()` | `_sqlite_enable` |

### Functions that MUST be inspected before changing fabric.py logic

| Function | Source file | Why |
|----------|------------|-----|
| `TriOctaMemoryKernel.process()` | `memory_kernel.py` | Returns `(state, signals, debug)` — entire ingest pipeline depends on this contract |
| `MemoryGraph.store()` / `.search()` | `memory_graph.py` | Core read/write — embedding format, payload schema |
| `score_hit()` | `scoring.py` | Scoring formula — query pipeline depends on exact signature |
| `should_emit_packet()` | `governance.py` | Governs hivemind emission gate |
| `AgentLockManager` | `agent_locks.py` | Lock granularity — wrong assumptions break concurrency |
| `save_checkpoint()`, `load_latest_checkpoint()`, `build_shard_snapshot()` | `checkpoint.py` | Checkpoint I/O — internally uses `ensure_within_base()` for path containment, but fabric.py does NOT import `ensure_within_base` directly |

---

## 3. Ranked Risk List

### RISK 1: Filesystem path construction without `ensure_within_base` — **MEDIUM**
**Where:** Module-level helpers (`_embed_audit_path`, `_anchor_state_path`, `_symbol_state_path`, `_job_path`), `Workspace.__init__`, `clone_workspace`, `_maybe_suggest_domain`, `trace_bundle`, `trace_full_graph`
**Issue:** These paths use `_validate_path_component` + `os.path.normpath(os.path.join(...))` but do NOT use `ensure_within_base()` for final resolution. The `_validate_path_component` guard rejects `..`, `/`, `\` which blocks the most common traversal attacks, but CodeQL may still flag the `normpath+join` pattern as insufficient.
**Risk level:** Medium — `_validate_path_component` covers practical attacks, but CodeQL doesn't model custom validators as sanitizers.
**Action for Phase 2:** Decide whether to wrap these paths with `ensure_within_base(result, self.data_dir)` or accept CodeQL flags as known false positives.

### RISK 2: Ingest pipeline depth and branch complexity — **MEDIUM**
**Where:** `ingest()` (lines 2106–2867) — 761 lines, single method
**Issue:** The ingest method is a monolithic pipeline with ~15 nested subsystem calls gated by feature flags. A single change in any subsystem can have cascading side effects across: kernel state, graph writes, motif registration, governance enrichment, hivemind emission, compression, SRG, checkpointing.
**Risk level:** Medium — not a security risk, but high change-risk. Any refactoring must be surgical.
**Action for Phase 2:** Map the exact data flow dependencies within ingest before touching anything.

### RISK 3: Concurrency — limited lock coverage — **MEDIUM**
**Where:** Only `create_agent` uses `self.locks.agent_lock()`. Hivemind init uses `self.locks.init_lock`. Clone uses `self._clone_mutex`. But `ingest()`, `query()`, `feedback()` do NOT acquire per-agent locks.
**Issue:** If two concurrent requests hit `ingest()` for the same agent, they could race on: `self.agent_states[ak]` (kernel ModelState), graph writes, motif registration, symbol state saves, affect state, anchor state, and checkpoint writes. This is a significant amount of shared mutable state.
**Risk level:** Medium — whether this is exploitable depends entirely on whether app.py serializes per-agent requests. This MUST be verified before any lock changes.
**Action for Phase 2:** Audit app.py request dispatch. Determine whether FastAPI/uvicorn serializes per-agent requests, or whether concurrent ingest for the same agent is possible in production. Do NOT add locks without understanding the full call chain.

### RISK 4: Clone workspace — file copy without containment — **LOW-MEDIUM**
**Where:** `clone_workspace()` (lines 1521–1795)
**Issue:** Uses `shutil.copytree` from `src_root` to `tgt_root`. Both roots are constructed from validated `workspace_id` values, but the copy itself doesn't verify that source files stay within `data_dir`. A symlink inside the source workspace could cause `copytree` to follow it outside the intended boundary.
**Risk level:** Low-medium — requires a malicious symlink to already exist inside a workspace directory.
**Action for Phase 2:** Consider adding `follow_symlinks=False` to the copy operation.

### RISK 5: Job persistence — `_load_jobs` reads arbitrary JSON from disk — **LOW**
**Where:** `_load_jobs()` (lines 662–695)
**Issue:** Reads all `.json` files from the jobs directory and loads them into memory. The directory is under `data_dir` which is server-controlled, so the attack surface is minimal.
**Risk level:** Low — only exploitable if an attacker can write to the jobs directory.
**Action for Phase 2:** No immediate action needed.

### RISK 6: Feature flag interactions — **LOW**
**Where:** `__init__()` (12 env vars), ingest/query/feedback
**Issue:** Feature flags interact implicitly: `_hivemind_enable` gates code that depends on `_checkpoint_enable` being true. `_compress_enable` depends on `_srg_enable` for some enrichment. These interactions are not documented.
**Risk level:** Low — flags fail gracefully (try/except everywhere), but unexpected combinations could produce silent data loss.
**Action for later phases:** Document flag interactions and test edge combinations.

### RISK 7: CodeQL false positives in unreachable code detection — **INFORMATIONAL**
**Where:** Hivemind outer gate else-block (line 2645–2654)
**Issue:** Already analyzed — CodeQL #466 is a false positive caused by deeply nested try/except/else indentation.
**Action:** Dismiss on GitHub with explanation.

---

## 4. Recommended Review Order for Deeper Phases

| Phase | Target | Why |
|-------|--------|-----|
| **Phase 2a** | Path construction audit | Decide: roll `ensure_within_base` to module-level helpers, or accept CodeQL flags. Low change risk, high security signal. |
| **Phase 2b** | Clone workspace containment | Add `follow_symlinks=False`, verify copytree boundaries. Isolated change, low blast radius. |
| **Phase 2c** | Ingest pipeline data flow map | Map exact variable dependencies before any refactoring. Read-only analysis. |
| **Phase 3** | Concurrency model audit | Verify lock coverage vs actual concurrent access patterns from app.py. Read-only analysis + possible lock additions. |
| **Phase 4** | Feature flag interaction matrix | Document which flags depend on each other. Read-only analysis. |
| **Phase 5** | Ingest method decomposition (optional) | Only if stability is needed for future development. High change risk — requires extensive testing. |

---

## Notes

- The kernel folder is OFF LIMITS per user instruction.
- All changes require ChatGPT review before implementation.
- CodeQL alerts should be evaluated individually — many will be false positives on this codebase due to custom validators that CodeQL can't model.
- ~~The file has a truncated function at line 4278 (`trace_view`).~~ **Correction (GPT review):** The sandbox read may have truncated early. The live repo file likely closes properly. Verify locally before acting on this.
