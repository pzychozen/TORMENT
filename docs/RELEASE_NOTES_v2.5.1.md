# TORMENT v2.5.1 — Kernel cleanup and analysis repairs

These are selected release highlights, not an exhaustive audit of the changes
since the August v2.5.0 release. This cleanup, repair and release-preparation
batch does not redesign the tuned live kernel or storage; other work in that
release interval has its own scope.

## Kernel ownership and analysis

The agreed kernel-package cleanup is closed. The live recurrence, saved-history
observables and offline analysis have explicit owners; the live core retains
its established K1–K3 helpers and mutation/RNG ordering. See the
[kernel ownership map](../torment_service/kernel/README.md).

Seven analysis/input repairs are included:

- Long-run diagnostics preserve metadata and other non-temporal values while
  slicing actual per-step histories on the established segment boundaries.
- RSB spectral energy, dominant bands and entropy use the same supported axis
  interpretation as the other wrapper observables.
- RSB summaries retain the supplied seed label without changing randomness.
- Optional `Omega=None` contributes zero phase velocity while retaining the
  available geometric-velocity components.
- Absent optional RSB summary series compose with empty analysis output without
  inventing measurements or discarding available information.
- Incomplete entropy formatting derives `H0 - HT` when both endpoints exist
  and `delta_H` is absent; supplied differences remain authoritative.
- Both CSV scripts reject empty datasets and missing required columns clearly.
  Invalid trajectory input cannot create or overwrite a summary CSV; supported
  successful outputs and the optional health `vrec_mean` message are preserved.

The former `torment_service/kernel/analyze_seed_trajectories.py` and
`torment_service/kernel/c.py` paths were removed. Use the explicit scripts under
`scripts/kernel_offline/` as documented in the ownership map; their data paths
remain relative to the working directory. Compatibility modules re-export owner
functions, but assigning compatibility-module attributes does not retarget a
moved function's globals. Patch the implementation owner when needed.

## HTTP configuration visibility and deployment

With authentication enabled, callers below `TRUST_OPERATOR` receive
`<redacted>` for `TORMENT_DATA_DIR`, `TORMENT_SERVER_LAUNCHER_PATH` and
`TORMENT_TEST_CONDITION` on `/debug/metrics`, and for
`effective.TORMENT_DATA_DIR.value` on `/config`. Ordinary allowed metrics and
configuration remain available. Operators and the accepted auth-off local
profile retain full diagnostic values; pure non-HTTP builders are unchanged.
Native `/config` remains admitted and native `/debug/metrics` remains refused,
with authentication refusal taking precedence for absent or invalid credentials.

Auth-off operation is supported only for a trusted single operator using the
shipped loopback launchers, without exposure, tunneling or forwarding. Untrusted
local software remains a risk. Remote or lower-trust multi-client access requires
configured authentication and appropriate trust assignments before exposure;
this is an operator boundary, not universal security or multi-tenant certification.
See [SECURITY.md](../SECURITY.md) for the accepted deployment policy and preserved
historical advisories.

## Related research and documentation

The root README now links to [Tri-Octagon Physics](https://github.com/pzychozen/trioctagon-physics).
Its newer scientific kernel and independent Historical TORMENT reference kernel
are separate research systems; neither replaces the production memory system.
This release makes no physics-validation claim. QUICKSTART uses the supported
`python -m torment_service` launcher, and active release identifiers are 2.5.1.

## Release-candidate validation

Executed separately on Windows on 4 October 2026, using the existing `torment`
environment and disposable test roots:

| Gate | Actual result |
| --- | --- |
| HTTP/auth/native | 109 passed, 0 skipped, 0 failed |
| Analysis/import | 346 passed, 0 skipped, 0 failed |
| Direct source consumers | 2 passed, 0 skipped, 0 failed |
| Active release identifiers | 4 passed, 0 skipped, 0 failed |
| Historical BASE selection | 5935 passed, 9 skipped, 0 failed; 96 subtests passed |

The HTTP gate includes all 78 focused configuration-visibility cases (20 using
the admitted native runtime), 30 existing HTTP/auth cases and one existing
native HTTP transport check. The analysis gate includes the real 48-step and
default 2,000-step stability runs. The version gate checks the package, FastAPI
metadata, OpenAPI, `/health` and the setup-page badge.

BASE selects current files from the established historical path list and retains
its existing exclusions and `Path.is_file()` filter; all 308 eligible paths were
present. It does not incorporate the new focused analysis, D1 or version files.
Its nine recorded skips were four unavailable symlink-permission checks, one
case-sensitive-filesystem check, one comparison with too few hits, and three
tests requiring local live workspace data. No live data was used to satisfy them.
These separate gates are not a full current-suite run or comprehensive native
route/security certification. The observed counts were added to these notes
after execution; code and test bytes stayed fixed.
