# tools/ Correctness Audit — v2.4.4

**Date:** 2026-04-12  
**Scope:** All 9 Python files under `tools/`. Read-only audit — no refactoring.  
**Focus:** Contract accuracy, boundary behavior, error handling, stale imports, shape drift, doc/test mismatches.

---

## Risk-Ranked Findings

| # | File | Finding | Risk | Category |
|---|------|---------|------|----------|
| 1 | `motif_field_viz.py` | Loads embeddings **only** from legacy `emb_<eid>.npy` files. Has zero awareness of shard storage introduced in `migrate_embeddings_to_shards.py`. After migration, this tool silently produces empty or incomplete visualizations. | **High** | Stale contract / storage drift |
| 2 | `run_coherence_field.py` | Hardcoded workspace path `ws_stress_split1/research/motifs.json`. No CLI arguments. Cannot be pointed at any other workspace without editing source. | **Medium** | Hardcoded path / usability |
| 3 | `visualize_attractors.py` | Duplicates four helpers from `motif_field_viz.py`: `_unit`, `_pca_2d`, `MotifInfo` dataclass, `make_color_cycle`. Any fix to `motif_field_viz.py` (e.g. shard support) won't propagate. | **Medium** | Code duplication / drift risk |
| 4 | `visualize_attractors.py` | Seed motif detection uses heuristic (`"seed" in label.lower() or mid.endswith("0001")`). No contract with the engine's actual seed classification; may mis-label or miss seeds. | **Low** | Heuristic fragility |
| 5 | `compact_core_memory.py` | Half-life decay expiry threshold is a hardcoded constant. No connection to any engine-side configuration or doctrine parameter. If the engine's decay model changes, this tool's pruning decisions diverge silently. | **Low** | Implicit coupling |
| 6 | `rebuild_sqlite_index.py` | Imports `IndexManager` from `torment_service.sqlite_index`. If the `rebuild_from_jsonl()` method signature or node schema changes, this tool breaks. No version guard or schema assertion. | **Low** | Import contract / no schema guard |
| 7 | `migrate_embeddings_to_shards.py` | Updates `nodes.jsonl` in-place with `embedding_ref` fields. Uses atomic `os.replace` for the write — correct. However, no backup of the original `nodes.jsonl` is created before mutation. A crash mid-write (between temp-file write and `os.replace`) is safe, but operator has no rollback path if the migration itself produces incorrect refs. | **Low** | No pre-mutation backup |
| 8 | `verify_workspace_integrity.py` | Fully shard-aware, cross-checks nodes/shards/archive/SQLite. Read-only. Clean error accumulation pattern (`IntegrityReport`). No findings — this is the gold standard in the directory. | **None** | — |
| 9 | `compact_archive_memory.py` | Self-contained JSONL dedup with atomic writes via `os.replace`. No imports from `torment_service`. Clean. | **None** | — |
| 10 | `verify.py` | Deterministic sim replay wrapper. Subprocess-isolated (calls `sim.run_sim` as a subprocess). Clean boundary. | **None** | — |

---

## Detail: Finding #1 — `motif_field_viz.py` legacy-only embedding loading

This is the highest-risk finding because it creates a silent correctness failure: after running `migrate_embeddings_to_shards.py`, the legacy `emb_<eid>.npy` files are (by design) no longer the source of truth. `motif_field_viz.py` will either find stale copies or find nothing, producing an incomplete or misleading visualization with no warning.

`visualize_attractors.py` already handles this correctly — it tries `EmbeddingShardReader` first, falls back to legacy files. The fix for `motif_field_viz.py` is to adopt the same shard-first loading pattern.

**Smallest safe fix:** Add shard-aware loading to `motif_field_viz.py` matching `visualize_attractors.py`'s `load_member_embeddings` pattern. This also creates the opportunity to extract the shared loading logic into a single helper, resolving finding #3.

## Detail: Finding #2 — `run_coherence_field.py` hardcoded path

```python
motifs_path = os.path.join("ws_stress_split1", "research", "motifs.json")
```

This is a 38-line diagnostic script. The hardcoded path means it only works for the `ws_stress_split1` workspace. Any other workspace requires editing the source.

**Smallest safe fix:** Add `--workspace` and `--domain` CLI args, defaulting to `ws_stress_split1` and `research`.

## Detail: Finding #3 — duplicated helpers across visualization tools

Both `motif_field_viz.py` and `visualize_attractors.py` define their own copies of:

- `_unit(v)` — L2 normalization
- `_pca_2d(X)` — SVD-based PCA to 2D
- `MotifInfo` — dataclass with `density` and `gravity_bonus` properties
- `make_color_cycle(n)` — tab color list

`visualize_attractors.py` line 55 even has the comment `# Shared helpers (reused from motif_field_viz.py)`, acknowledging the duplication. Today they're identical, but any fix applied to one copy (particularly shard support for finding #1) won't propagate to the other.

**Smallest safe fix:** Extract shared helpers into `tools/_viz_common.py` (or similar), import from both scripts.

---

## Summary by risk tier

- **High (act before next feature work touches embeddings):** 1 finding — `motif_field_viz.py` legacy-only loading
- **Medium (fix opportunistically):** 2 findings — hardcoded path, code duplication
- **Low (document or defer):** 4 findings — heuristic fragility, implicit coupling, no schema guard, no pre-mutation backup
- **Clean:** 3 files — `verify_workspace_integrity.py`, `compact_archive_memory.py`, `verify.py`

No trust/auth issues found (none of these tools touch the network or MCP layer). No retry/idempotency issues found (all tools are either read-only or use atomic writes). No test mismatches found (these tools have no dedicated test files to mismatch against, which is itself a gap but not a correctness finding per the audit scope).
