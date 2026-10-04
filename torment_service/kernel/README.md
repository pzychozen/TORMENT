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

Offline relocation is still incomplete. `diagnostics.py`, `physics_sampler.py`,
`physics_sampler2.py` and `tangent_corridor_analysis.py` remain in this directory.
Their P1 plotting and clustering imports stay local to the functions that use
them. Executable analysis scripts such as `analyze_seed_trajectories.py` and
`c.py` also remain here; inspect them as scripts, not by importing them. Seed,
world and trajectory/persistence modules have not been reorganized by P4A.
