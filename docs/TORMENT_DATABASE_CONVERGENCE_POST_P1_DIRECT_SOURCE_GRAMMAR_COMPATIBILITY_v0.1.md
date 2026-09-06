# TORMENT Database Convergence — Post-P1 Direct-Source Grammar Compatibility

## Result

`POST_P1_DIRECT_SOURCE_GRAMMAR_COMPATIBILITY = QUALIFIED`

The direct admission source path now recognizes an optional top-level
`substrate/` directory as the native database/deployment control plane.  It
validates only that direct path is a real non-link, non-reparse directory; it
does not enumerate, open, hash, or otherwise read descendants.

`DIRECT_ADMISSION_SUBSTRATE_ROLE = NATIVE_CONTROL_PLANE`

`SUBSTRATE_SOURCE_AUTHORITY = NONE`

`SUBSTRATE_MANIFEST_MEMBERSHIP = NONE`

`SUBSTRATE_DESCENDANT_READ = NONE`

The historical corrective compatibility route remains strict: its
`capture_typed_evidence(...)` path still refuses a root that contains
`substrate/`.

`HISTORICAL_CORRECTIVE_GRAMMAR_CHANGED = NO`

`UNKNOWN_ROOT_ARTIFACT_REFUSAL_PRESERVED = YES`

## Boundary

This is a grammar compatibility repair only.  It changes neither P1 identities
nor P2 lifecycle semantics, and makes no deployment authority transition.

`P1_SEMANTICS_CHANGED = NO`

`P2_SEMANTICS_CHANGED = NO`

`P2_EXECUTED = NO`

`REAL_ROOT_CONTACT = NONE`

`PRODUCTION_SQLITE_WRITE = NONE`
