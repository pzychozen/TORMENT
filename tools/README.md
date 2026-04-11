# TORMENT Fabric — `tools/` directory

Maintenance, migration, diagnostic, ship-gate, and visualization scripts that
operate on a live TORMENT Fabric data directory. None of these run automatically
during chat — every tool is an explicit, out-of-band operation that the operator
invokes against a specific workspace/agent.

This README exists for **discoverability**. It does not change any tool
behavior, add arguments, or remove scripts; it only documents what is already
in-tree so an operator can pick the right entry point quickly.

---

## At-a-glance classification

| File | Category | Modifies data? | Status |
|---|---|---|---|
| `compact_archive_memory.py` | maintenance | yes (with `--dry-run`) | supported |
| `compact_core_memory.py` | maintenance | yes (with `--dry-run`) | supported |
| `rebuild_sqlite_index.py` | maintenance | yes (SQLite sidecar only) | supported |
| `migrate_embeddings_to_shards.py` | migration | yes, idempotent (with `--dry-run`) | supported |
| `verify_workspace_integrity.py` | diagnostic | no | supported |
| `verify.py` | ship gate | no (writes to temp dir only) | supported |
| `motif_field_viz.py` | visualization | no (writes PNG + CSV to `--out`) | supported |
| `visualize_attractors.py` | visualization | no (writes PNG to `--out`) | supported |
| `run_coherence_field.py` | **dev scratch** | no (read-only print) | **not a supported tool** — see bottom of file |

All tools can be invoked either as a module (`python -m tools.NAME ...`) or as a
script (`python tools/NAME.py ...`) from the repo root. On Windows use `py -3`
in place of `python`. Examples below use `python` for brevity.

---

## Maintenance tools

These tools touch canonical on-disk state. Every one of them supports
`--dry-run` (except `rebuild_sqlite_index.py`, which only rebuilds a
disposable cache and is therefore always safe to re-run). Run them
out-of-band — never while an agent is actively ingesting.

### `compact_archive_memory.py`

Compacts archive memory for a single workspace/agent by:

1. Removing orphan chunks (chunks whose `doc_id` no longer exists)
2. Deduplicating `documents.jsonl` and `chunks.jsonl`
3. Writing compacted output atomically

```
python -m tools.compact_archive_memory --data-dir ./data --workspace default --agent ryuki
python -m tools.compact_archive_memory --data-dir ./data --workspace default --agent ryuki --dry-run
```

### `compact_core_memory.py`

Compacts core memory JSONL files for a single workspace/agent by:

1. Deduplicating `nodes.jsonl` (keeping the latest record per `eid`)
2. Removing expired memories (half-life exhausted and strength below threshold)
3. Writing compacted output atomically

```
python -m tools.compact_core_memory --data-dir ./data --workspace default --agent ryuki
python -m tools.compact_core_memory --data-dir ./data --workspace default --agent ryuki --dry-run
```

### `rebuild_sqlite_index.py`

Rebuilds the SQLite sidecar index from the canonical JSONL and NPY sources.
The SQLite index is a disposable cache — it is always reconstructible from the
JSONL/NPY canon, so this script is safe to run at any time. `--workspace` and
`--agent` are optional filters.

```
python tools/rebuild_sqlite_index.py --data-dir ./data
python tools/rebuild_sqlite_index.py --data-dir ./data --workspace ryuki --agent ryuki_nox
python tools/rebuild_sqlite_index.py --data-dir ./data --dry-run
```

---

## Migration tools

### `migrate_embeddings_to_shards.py`

One-off migration from the legacy per-file embedding layout
(`emb_<eid>.npy`) to shard storage. Scans every graph directory, writes each
embedding into shard storage, updates `nodes.jsonl` with `embedding_ref` and
`memory_class` fields, and moves old `emb_*.npy` files into
`legacy_embeddings/` (they are **not** deleted). Already-migrated nodes are
skipped, so the script is safe to re-run.

```
python -m tools.migrate_embeddings_to_shards --data-dir ./data
python -m tools.migrate_embeddings_to_shards --data-dir ./data --dry-run
```

---

## Diagnostic tools

### `verify_workspace_integrity.py`

Read-only cross-check of a workspace/agent. Reports issues but never modifies
data. Checks:

1. Every `eid` in `nodes.jsonl` has a valid `embedding_ref` pointing at an
   existing shard row
2. Every chunk in `chunks.jsonl` has a valid `doc_id` in `documents.jsonl`
3. SQLite index row counts match canonical JSONL counts
4. Shard manifest matches actual shard file sizes
5. Character seed references exist

```
python -m tools.verify_workspace_integrity --data-dir ./data --workspace default --agent ryuki
```

### `verify.py` (ship gate)

Deterministic replay verification. Runs a small fixed simulation
(`sim.run_sim`, workspace `verify-ws`, 8 agents, 120 steps, scenario `mixed`,
seed `0`) twice — once recording a replay log, once replaying from that log —
and compares the two `summary.json` outputs. This catches:

- accidental nondeterminism regressions
- obvious runtime failures on core API / governance paths

The script forces `TORMENT_EMBED_PROVIDER=hash` for determinism and uses a
temp dir at `$TORMENT_VERIFY_TMP` (default `/tmp/torment_verify`). It exits 0
on pass, non-zero on any mismatch or subprocess failure.

```
python tools/verify.py
# optional: override the temp dir
TORMENT_VERIFY_TMP=/path/to/scratch python tools/verify.py
```

This is the minimum bar before shipping any change that touches the core
API, governance, or simulation paths.

---

## Visualization tools

These are read-only — they load canonical state and write PNG / CSV artifacts
to `--out`.

### `motif_field_viz.py`

Visualizes TORMENT motif basins (gravity wells) for a single
`workspace/domain` pair. Loads `motifs.json` and member embeddings, projects
them to 2D with PCA (numpy SVD, no sklearn dependency), and draws member
points colored by motif, motif centroids as stars, and "gravity circles"
sized by motif strength + density + stability. Writes:

- `motif_field_<workspace>_<domain>.png`
- `motif_field_<workspace>_<domain>_summary.csv`

```
python tools/motif_field_viz.py \
  --data-dir data \
  --workspace ws_stress_gw1 \
  --domain research \
  --out outputs
```

Optional: `--title "..."`, `--max-points-per-motif 200`.

### `visualize_attractors.py`

Multi-panel attractor visualization for a single `workspace/agent[/domain]`.
Generates three stacked layers in one PNG:

1. **Basin Landscape** — native engine geometry (phi vs kappa, colored by
   tension) beside an embedding PCA projection of semantic space
2. **Phase Space Dynamics** — trajectory through D24 sectors, coherence,
   and corridor proximity
3. **Drift + Identity Timeline** — drift score, memory events, coherence /
   corridor over time

```
python tools/visualize_attractors.py \
  --data-dir data \
  --workspace ryuki \
  --agent ryuki_nox \
  --domain research \
  --out outputs
```

Optional: `--layers basin,orbits,timeline` (or `all`), `--dpi 180`,
`--title "..."`.

---

## Not a supported tool

### `run_coherence_field.py` — **dev scratch, not a general tool**

This file is kept in-tree for reference but is **not** a supported entry
point. It has no argparse and loads a hardcoded motif path:

```
data/workspaces/ws_stress_split1/domains/research/motifs.json
```

That workspace is a developer stress-test fixture — it will not exist in a
normal data directory. The script is a one-off scratchpad that prints a
coherence field summary and the top-10 motifs for that specific fixture.

Treat it as a worked example of the `coherence_field` API, not as a tool
you can run against your own workspace. If you need the same output for a
real workspace, call `torment_service.coherence_field.compute_coherence_field`
and `summarize_coherence_field` directly; do not edit this file expecting
it to generalize.

This script's fate (fix, generalize, relocate under `examples/`, or delete)
is out of scope for the v2.4.3 consolidation branch and will be decided
separately.
