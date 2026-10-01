# Ordered theta-pair production-before fixture

Phase 2D admits the immutable Phase 2C observations for the ordered theta prefix
inside `theta_soft_triplet` and `theta_triplet_scaled`. This is test admission
only. The profiles, later arithmetic, guards, dispatch and production code remain
separate and unchanged.

`theta_fixture.json` was copied byte-for-byte, never regenerated. Its SHA-256 is
`ad0f439cebc5419bd14adc414489941334c2131267f7e36927529a240145dd8c`.
The external Phase 2C manifest SHA-256 is
`83cd925fd3ef5d9ba41ce3565ec423add919c3f9c1b85cac11377d77112cbbce`.
See `provenance.json` for origin, admission date and baseline source identities.
The local `.gitattributes` disables text conversion for the sealed fixture.

## Contract and independence

All 88 frozen cases are admitted: ordered calls (1), soft domains/failures (33),
scaled output (1), injected failures (8), separate guards (20), selector dispatch
(13), import compatibility (4), and pure ModelParams factories (8).
Four negative-control tests independently reject swapped/duplicated pair tuples
for each profile and verify restored bindings and behavior afterward.

The test module observes current production and compares it with inert expected
records. It never generates one profile's expectations from the other or from a
future helper. Exact types, float bits, array layout/ownership, mutation, warnings,
exceptions and call order are protected. The existing bare-import model oracle is
imported only for its ModelParams constructor; no trajectory is executed.

Baseline HEAD, selector hash and source structure are historical provenance only,
not future acceptance conditions. A later authorized implementation may change
source bytes while preserving all frozen behavior. The test has no capture mode,
AST equivalence requirement, Git invocation, or external-report dependency.
Never update the expected fixture to accommodate a refactor.

## Bounded invocation

From this repository in Windows Command Prompt:

```bat
conda activate torment
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
set PYTEST_ADDOPTS=
python -I -B -X utf8 -m pytest --noconftest -p no:cacheprovider -q tests/test_theta_cleanup_frozen_contract.py
```

For an explicit negative-control run, append `-k negative_control`.
For bounded package/bare/factory observations, append
`-k "import or factory"`.
The test imports only the pure selector/model dependencies. It restores temporary
module bindings, bare aliases, search paths and NumPy error policy. Do not run
service, database, memory, embedding/model or trajectory suites for this candidate.

The freeze was captured on Python 3.11.15 / NumPy 2.4.4, Windows x64, little endian.
NumPy divide/overflow/invalid warnings are enabled and underflow is ignored.
Special-value bits, warning messages and exception messages are exact observations
in that environment; arbitrary platform/library changes require separate review,
not automatic fixture regeneration. Tracebacks, addresses and warning source line
numbers are not frozen.
