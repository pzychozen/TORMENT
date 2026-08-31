# 7G5D1 trace-to-STAGING replay preflight

This package is an experiment-only, non-activating D1 instrument. It creates
and fingerprints an L0 baseline through the real legacy HTTP service, packages
that evidence for existing B-series N0 STAGING construction, validates
legacy-only fixture margins, and prepares native replay inputs without passing
legacy route answers to the native router.

Use `torment` for the normal service and `torment-substrate` for native
qualification/replay. Both environments are pre-existing and must remain
unchanged. The package has no command that administers a formal D1 comparison:
`run_formal_administration()` deliberately raises until a later workorder
changes the authorization boundary.

The executable contract is in `protocol.py`; concrete L0-specific facts are
sealed with `run.seal_fixture_set()` only after legacy-only qualification. The
checked-in JSON is a recipe, not a formal fixture result. See
`docs/TORMENT_MEMORY_SUBSTRATE_PHASE_7G5D1_TRACE_REPLAY_PREFLIGHT_v0.1.md` for
the complete protocol and boundaries.
