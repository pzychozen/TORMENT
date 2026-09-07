# Unknown original provenance structural contract

This contract applies only to an ordinary, verified legacy R1 whose original
source provenance is absent from both legacy provenance carriers. It preserves
a non-null native provenance witness without asserting a legacy source.

## Exact native provenance record

| Field | Value |
| --- | --- |
| `origin_kind` | `MIGRATION_LEGACY_ORIGINAL_PROVENANCE_UNKNOWN` |
| `source_channel` | `NULL` |
| `source_role` | `NULL` |
| `derivation_status` | `structural_witness` |
| `uncertainty_state` | `UNKNOWN` |
| `source_time_ns` | `NULL` |
| `capture_time_ns` | `NULL` |
| `memory_role` | `NULL` |
| `descriptive_notes` | `NULL` |

The row proves the bounded native normalization lineage only. It does not
describe the legacy memory's original writer, channel, role, time, or write
path. B2 derives all nine fields from verified migration evidence; callers do
not supply them.

## Runtime projection

Only the exact record above projects as:

```python
RuntimeMemoryProvenanceView(None, None, None, False, False)
```

No other migration origin, `UNKNOWN` uncertainty value, or null
`source_channel` is included in this branch. Existing exact `ProvenanceV1`
translation and all other native provenance projection remain unchanged.

## Closed eligibility and downstream boundaries

- B1 emits `UNKNOWN_ORIGINAL_PROVENANCE_NORMALIZATION_REQUIRED` only for the
  ordinary exact R1 absence case. Other semantic unresolved states stay closed.
- `seed_canon` rows remain outside this path and require the existing Character
  seed witness.
- B2 creates one provenance row and one R2. It creates neither a vector nor a
  representation and does not relabel a legacy capture.
- B3A accepts the exact structural witness only after its existing R2,
  transition, capture, source-revision, and representation evidence checks.
- No schema, table, or column is required by this contract.
