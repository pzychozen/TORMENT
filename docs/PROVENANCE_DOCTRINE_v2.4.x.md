# PROVENANCE DOCTRINE — v2.4.x

**Status:** canonical as of 2026-04-12.
**Scope:** compact provenance derivation, presentation invariants, and canonical helpers.
**Companion docs:**

- `PROVENANCE_STATUS_REGISTRY_v2.4.x.md` — audit of every declared constant, write-path producers, RSP parent status.
- `DOCTRINE_v2.4.x.md` — system-wide doctrine (rule #5: provenance is a hard boundary).
- `PROVENANCE_CONSTANTS_NOTES.md` — historical scratch (superseded; retained for context).

---

## 1. Purpose

Provenance tracks where memory-like content came from. It is used for three things:

1. **Classification** — distinguishing collective echoes from autobiographical memory, tool results from role output.
2. **Presentation** — surfacing a human-readable `provenance_type` label on retrieval, debug, and MCP surfaces.
3. **Policy** — feeding retrieval discounts (collective, tool-result), recursion-safety parent eligibility, and writeback gating.

This document defines the compact provenance derivation doctrine used by the v2.4.x read/presentation surfaces. It does not cover write-path provenance production (see the STATUS_REGISTRY) or spine-layer provenance (see `AGENT_SPINE_OVERVIEW.md`).


## 2. Canonical provenance concepts

There are three levels of provenance in the read path. They must not be conflated.

**Raw provenance** — the `provenance` field stored on each memory payload. May be:

- A structured dict (ProvenanceV1-style): `{"source_type": "user_input", "write_path": "direct_ingest", ...}`
- A legacy bare string: `"collective"`, `"user_input"`, or other pre-ProvenanceV1 artifacts.
- `None` or absent — pre-provenance data.

**Compact provenance label** — the derived, human-usable classification string. Produced by `derive_provenance_type()`. Examples: `"collective_echo"`, `"user_input"`, `"tool_result"`, `None`. This is the canonical low-level derivation used by indexing, aperture stamping, debug surfaces, and MCP presentation.

**Query-facing provenance label** — the label exposed on `query()` and `trace()` result surfaces. Produced by `derive_query_provenance_type()`. Identical to the compact label for all structured provenance and for known legacy strings. Differs only for unknown legacy bare strings, which are clamped to `"memory"` (`SOURCE_MEMORY`) to keep query output within the `VALID_SOURCE_TYPES` vocabulary.

The distinction exists because query consumers may depend on the output sitting inside the `VALID_SOURCE_TYPES` frozenset, whereas index/debug/MCP surfaces benefit from seeing the raw canonical classification even when it falls outside that vocabulary.


## 3. Canonical helper functions

### `derive_provenance_type(provenance)`

- **File:** `torment_service/scoring.py`
- **Role:** Single canonical rule for converting raw provenance → compact label.
- **Logic:** Structured dict → `source_type` field. Bare `"collective"` → `"collective_echo"`. Other bare strings → passthrough. `None` → `None`.
- **Used by:** SQLite index (`sqlite_index.py`), aperture stamping (`cognition/apertures.py`), debug provenance route (`app.py`), MCP provenance resource (`mcp_server.py`).
- **Not for:** Query/trace result surfaces (use `derive_query_provenance_type` instead).

### `derive_query_provenance_type(provenance)`

- **File:** `torment_service/scoring.py`
- **Role:** Query/trace-facing provenance adapter. Calls `derive_provenance_type()` as base, then clamps results outside `VALID_SOURCE_TYPES` to `SOURCE_MEMORY`.
- **Used by:** `fabric.query()` result stamping, `fabric.trace()` explain output.
- **Why distinct:** Query output historically guaranteed all labels sat inside `VALID_SOURCE_TYPES`. The adapter preserves that contract while delegating canonical derivation to the shared helper.

### `is_collective_provenance(provenance)`

- **File:** `torment_service/scoring.py`
- **Role:** Boolean check: is this provenance a collective echo? Recognises both bare `"collective"` and structured `{"source_type": "collective_echo"}`.
- **Used by:** `fabric.query()` and `fabric.trace()` for retrieval discount gating.

### `apply_collective_discount(provenance, score, discount)`

- **File:** `torment_service/scoring.py`
- **Role:** Applies the collective retrieval discount to a score if provenance indicates a collective echo. Calls `is_collective_provenance()` internally.
- **Used by:** `fabric.query()` and `fabric.trace()`.

### `_stamp_provenance_type(hits)`

- **File:** `cognition/apertures.py`
- **Role:** Stamps `provenance_type` onto each hit in a lane before returning `MemoryContext`. Delegates to `derive_provenance_type()`. Skips hits that already carry the field.
- **Used by:** Aperture builder (`build_memory_context`) for private, shared, and deep lanes.


## 4. Provenance truth table

Current behaviour as of v2.4.4 post-alignment patches.

| Raw provenance | `derive_provenance_type()` | `derive_query_provenance_type()` | Notes |
|---|---|---|---|
| `None` | `None` | `None` | Pre-provenance data. |
| `"collective"` | `"collective_echo"` | `"collective_echo"` | Legacy bare string; canonical normalises. In vocab. |
| `"user_input"` (bare) | `"user_input"` | `"user_input"` | Legacy bare string; happens to be in vocab. |
| `"memory"` (bare) | `"memory"` | `"memory"` | Legacy bare string; in vocab. |
| `"tool_result"` (bare) | `"tool_result"` | `"tool_result"` | Legacy bare string; in vocab. |
| `"some_unknown"` (bare) | `"some_unknown"` | `"memory"` | Unknown bare string; query adapter clamps. |
| `{"source_type": "collective_echo"}` | `"collective_echo"` | `"collective_echo"` | Structured; both agree. |
| `{"source_type": "user_input"}` | `"user_input"` | `"user_input"` | Structured; both agree. |
| `{"source_type": "tool_result"}` | `"tool_result"` | `"tool_result"` | Structured; both agree. |
| `{"source_type": "memory"}` | `"memory"` | `"memory"` | Structured; both agree. |
| `{}` (missing key) | `None` | `None` | Malformed dict. |


## 5. Provenance invariants

These are statements about code that is true today. Future changes must preserve them or update this section.

**Invariant A — Collective echoes stay visibly collective.**
If raw provenance indicates a collective echo (bare `"collective"` or `source_type == "collective_echo"`), all presentation surfaces must classify it as `"collective_echo"`, not flatten it to `"memory"`. This is enforced by `derive_provenance_type()` normalising `"collective"` → `"collective_echo"` before any downstream vocabulary check.

**Invariant B — Structured provenance is authoritative.**
When raw provenance is a dict containing `source_type`, that value is the primary input for derivation. Legacy normalisation (bare-string rules) only applies when raw provenance is a plain string.

**Invariant C — One canonical derivation, no ad-hoc inline parsing.**
New surfaces that need a compact provenance label must call `derive_provenance_type()` (or `derive_query_provenance_type()` for query-facing output). Inline `isinstance`/`get` chains that re-derive provenance classification are prohibited. The helpers exist to prevent drift.

**Invariant D — Query-facing vocabulary enforcement is explicit.**
The difference between canonical compact labels and query-facing labels lives in a single named function (`derive_query_provenance_type`), not in scattered inline branches. If the query vocabulary contract changes, only that adapter needs updating.

**Invariant E — Derivation must precede legacy normalisation.**
Several surfaces (debug provenance, MCP provenance resource) normalise legacy bare-string provenance to a synthetic dict for display. The compact `provenance_type` must be derived *before* that normalisation, or the canonical classification is lost. This ordering is currently enforced in `app.py` (`/debug/provenance`) and `mcp_server.py` (provenance resource).

**Invariant F — Memory-like user-adjacent surfaces expose `provenance_type`.**
Surfaces that present memory-like content to users or downstream consumers should include the `provenance_type` field. Currently enforced on: query results, trace explain, aperture context blocks, SQLite recent/motif, debug provenance, MCP provenance resource.


## 6. Surface map

Where `provenance_type` currently appears, and which derivation produces it.

| Surface | Location | Derivation | Field |
|---|---|---|---|
| Query results | `fabric.py` `query()` | `derive_query_provenance_type` | `hit["provenance_type"]` |
| Query results — tool name | `fabric.py` `query()` | direct dict extraction | `hit["provenance_tool_name"]` |
| Trace explain | `fabric.py` `trace()` | `derive_query_provenance_type` | `explain["provenance_type"]` |
| Aperture lane hits | `cognition/apertures.py` | `derive_provenance_type` via `_stamp_provenance_type` | `hit["provenance_type"]` |
| SQLite index | `sqlite_index.py` `index_node()` | `derive_provenance_type` | `core_nodes.provenance_type` column |
| SQLite recent | `sqlite_index.py` `recent()` | stored column | returned in row dict |
| SQLite motif | `sqlite_index.py` `motif_*()` | stored column | returned in row dict |
| Debug provenance | `app.py` `/debug/provenance` | `derive_provenance_type` | `entry["provenance_type"]` |
| MCP provenance resource | `mcp_server.py` | `derive_provenance_type` | `entry["provenance_type"]` |
| Telemetry / health | various | not applicable | provenance labels not stamped (these are not memory-like) |


## 7. Known intentional exceptions and historical seams

**Query adapter vs canonical derivation.** `derive_query_provenance_type()` intentionally clamps unknown legacy bare strings to `"memory"` rather than passing them through. This preserves the historical contract that query output labels sit inside `VALID_SOURCE_TYPES`. The canonical helper does not clamp, because index/debug/MCP surfaces benefit from seeing the raw classification.

**Legacy bare strings in historical data.** Pre-ProvenanceV1 memories may contain bare-string provenance values that are not in `VALID_SOURCE_TYPES`. These are handled gracefully (passthrough in canonical, clamped in query), but they are not migrated in place. They will be addressed if the write-migration gate (step 6, currently closed) reopens.

**Trace stamps `provenance_type` in `explain` only.** Unlike `query()`, which stamps `provenance_type` at the top level of each result hit, `trace()` places it inside the `explain` sub-dict. This is the pre-existing structural difference between the two surfaces and is not a doctrinal divergence.

**MCP resource gating is exposure-tier based.** The provenance MCP resource is gated by `TORMENT_MCP_EXPOSURE_TIER`, not by per-request trust. This is a deliberate design choice documented in `MCP_CAPABILITY_BOUNDARY.md`.


## 8. Guidance for future contributors

When adding a new surface that touches memory-like content:

1. **Expose `provenance_type`** — call one of the canonical helpers. Do not parse raw provenance inline.
2. **Choose the right helper.** If the surface feeds query consumers who depend on `VALID_SOURCE_TYPES`, use `derive_query_provenance_type()`. For everything else, use `derive_provenance_type()`.
3. **Derive before normalising.** If the surface also normalises legacy provenance for display, derive the compact label first.
4. **If you need a new provenance label,** add it to `VALID_SOURCE_TYPES` in `provenance_v1.py` and update this truth table.
5. **If a cache/index surface intentionally omits provenance,** document that decision here in section 7.
6. **Do not add inline `isinstance(provenance, ...)` branches.** The helpers exist to prevent drift. If the derivation logic needs to change, change it in one place.
