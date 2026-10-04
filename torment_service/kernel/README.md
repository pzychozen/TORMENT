# Kernel ownership

`model_core.py` owns the live triad model: parameters and state, recurrence,
phase synchronization, clock, classification, mutation ordering and the master
`step()`. Its existing helpers keep their established roles:

| Owner | Responsibility |
| --- | --- |
| `model_history.py` | K1: history allocation and recording, run metadata and the optional post-run analysis hook; reached through `model.run()` |
| `staged_readouts.py` | K2: staged Z calculations; `model_core.update_z()` still owns the writes |
| `stochastic_forcing.py` | K3: optional noise calculation; the core retains call and RNG ordering |
| `phase_triad_sync.py`, `constants_selector.py`, `identity_rules.py` | Phase synchronization, constants selection and state classification used by the core |

Saved-history metrics now have explicit owners. These modules are deterministic
and NumPy-only; they do not run a model or load plotting libraries.

| Owner | Saved-history observables |
| --- | --- |
| `observables/chirality.py` | J helpers, signs and flips, commitment and timescale estimates, radius statistics and `EPS` |
| `observables/recursive_velocity.py` | Entropy and geometry velocity metrics, including their distinct short-input contracts and `_wrap_angle_pi` |
| `observables/z_geometry.py` | Z-direction stabilization estimate |

RSB analysis belongs to the separate offline owners below. `rsb_model.py`
remains the separate spectral toy engine; these analysis modules do not import
or execute it.

| Owner | Responsibility |
| --- | --- |
| `offline/rsb_observables.py` | Spectral energy, dominant band, entropy and RSB observable series |
| `offline/rsb_classification.py` | RSB regime classification |
| `offline/rsb_analysis.py` | History analysis, seed summaries and formatted output |

`definitions.py` remains the compatibility import surface. It re-exports the
actual owner functions, including `_wrap_angle_pi`, and retains `EPS` and `np`.
It contains no duplicate implementations or forwarding wrappers. The cubic-J
helper's reshapeable-input contract remains separate from the cognitive path's
strict unpacking contract. Neither formula nor either input contract was merged.
The `observables` and `offline` package markers do not eagerly aggregate owners.
The normal live-runtime import path does not load these new packages.

Offline experiments and plotting retain their existing function groupings in
four implementation owners. They are separate from live recurrence and the
P4A saved-history observable/RSB owners above.

| Compatibility import | Implementation owner |
| --- | --- |
| `diagnostics.py` | `offline/experiments.py`: experiment drivers and their summary helpers |
| `physics_sampler.py` | `offline/samplers.py`: physics sampling and distribution plots |
| `physics_sampler2.py` | `offline/cp_analysis.py`: CP-conditioned analysis, chirality windows and time-series plots |
| `tangent_corridor_analysis.py` | `offline/corridors.py`: tangent detection, clustering, plots and CP event splits |

These four compatibility modules re-export the actual owner functions and their
existing helper/model/NumPy names. Assigning an attribute on a compatibility
module does not change the globals used by a moved function; patch the actual
implementation owner when needed. Matplotlib and SciPy imports remain inside
the functions that use them. Importing an owner does not require those libraries;
calling its plotting or clustering functions still does.

The two CSV scripts now live outside the kernel. From the repository root,
execute them explicitly:

```bat
python scripts/kernel_offline/analyze_seed_trajectories.py
python scripts/kernel_offline/scan_health_summary.py
```

The first reads `outputs_patch39_unified/lambda_*/seed_trajectories_seed*.csv`
and writes `outputs_patch39_unified/trajectory_class_summary.csv`. The second,
formerly `kernel/c.py`, reads `outputs/wide_scan_triocta_ultra.csv` and prints
its health summary. All input/output paths remain relative to the process
working directory. To use another data directory as the working directory,
invoke the corresponding script by its absolute path.

Their former kernel file/module paths were removed. These scripts are explicit
execution tools, not supported import APIs: importing one still executes its
payload. Missing files, empty datasets and missing required columns fail
explicitly; invalid trajectory inputs do not create or overwrite the summary CSV.
Successful outputs and the health script's optional `vrec_mean` behavior remain.

The accepted analysis repairs preserve non-temporal history metadata while
slicing temporal series, use consistent supported RSB axis layouts, propagate
seed labels, and handle optional Omega, absent summary series and incomplete
entropy formatting deliberately. These are specific input-contract corrections,
not support for arbitrary malformed analysis inputs.

The agreed kernel-package cleanup is closed. Seed/world, trajectory/persistence,
`rsb_model.py`, CP rules and the live core were not reorganized by this relocation;
no further package restructuring is required by this cleanup.
