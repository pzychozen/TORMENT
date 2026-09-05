# TORMENT Memory Substrate — I4G-R2 Empty-Scope and Multi-Topology Implementation Qualification v0.1

## Scope

This record qualifies a synthetic/offline implementation only. It does not
authorize a real-root census, writer freeze, admission, normalization,
activation, service startup, provider contact, or model loading.

## Implementation surface

- `torment_service/substrate/migration/root_admission_description.py`
- `torment_service/substrate/migration/root_normalization.py`
- `torment_service/substrate/migration/generalized_runtime_readiness.py`
- `torment_service/substrate/root_blocker5_binding.py`
- `torment_service/substrate/production_native_owner.py`
- `torment_service/public_runtime.py`

## New posture contracts

`DECLARED_EMPTY_SHARED` is a shared `RootScopeKey` with `NO_VECTOR`, a lawful
domain declaration, no physical `shared/` source scope, no nodes, and either
present or absent motif evidence. It receives a complete runtime scope plan and
active membership. It schedules zero B3 requests. Present motif evidence uses
only the existing B4C zero-member projection; absent motif evidence schedules
no B4 request and invents no motif.

`EMPTY_PRIVATE` is a physically present private scope with `NO_VECTOR`, absent
nodes, and a required identity-only observation for the existing agent. It
receives a complete runtime scope plan and active membership, schedules zero
B3/B4 requests, and does not provide a dynamic agent-creation path. Vector
residue without canonical nodes remains non-memory source evidence.

The synthetic fixture proves this for both an embedding manifest with
`total_rows: 0` and one with `total_rows: 1` plus an orphan vector artifact:
both retain zero B3/B4 receipts and zero canonical memory admission.

The census now distinguishes physical materialization from declared-empty
shared runtime obligations. Discovered parity compares only physical source
scopes; runtime-plan and membership parity compare all explicit runtime scopes.
An undeclared physical scope still refuses closure.

## Public topology and routing

Root-v2 accepts `0..n` private scopes and requires `1..n` shared scopes for a
public workspace. The public workspace view exposes immutable exact mappings
for private agent scopes and ordered shared domain scopes. Private and shared
resolution remain exact; absent qualifiers refuse. A zero-private workspace can
construct a view but cannot prepare or create an unadmitted agent. Private-only
and zero-scope public workspaces refuse as a whole.

## Synthetic qualification evidence

The expanded root-normalization fixture covers a multi-workspace topology with
five private lanes, multiple shared lanes, an `EMPTY_PRIVATE` lane,
`DECLARED_EMPTY_SHARED` without motifs, and `DECLARED_EMPTY_SHARED` with a
zero-member B4C motif. The empty-private and no-motif declared-shared scopes
produce no B3/B4 receipts. The motif-bearing declared-shared scope produces B4C
only. The existing metadata-less `UNKNOWN_IDENTITY` fixture still reaches the
deterministic Phase 9B re-embedding route without relabeling a provider or
dimension.

Negative coverage refuses absent empty-private identity proof, absent
declared-domain proof, invalid non-`NO_VECTOR` empty dispositions, zero shared
public topologies, duplicate public scope identities, unknown agent/domain
lookups, unadmitted agent creation, and an undeclared physical shared scope.

## Test commands

All commands used the `torment` Conda environment and synthetic `--basetemp`
directories only.

```text
python -m pytest -q tests/test_substrate_root_admission_description.py
python -m pytest -q tests/test_substrate_root_normalization.py::test_root_wide_normalization_composes_b3_b4_and_generalized_readiness
python -m pytest -q tests/test_substrate_root_normalization.py::test_declared_empty_shared_is_runtime_membership_but_not_discovered_materialization
python -m pytest -q tests/test_post_i4g_r2_public_multi_topology.py
python -m pytest -q tests/test_post_i4_generalized_root_blocker5_binding.py
python -m pytest -q tests/test_post_i4_root_v2_production_recovery.py
```

Predecessor compatibility covered by these focused suites includes I4G root
normalization, Blocker-5 envelope binding, root-v2 recovery, and the existing
Phase 9B metadata-less unknown-identity path. No second controller, deployment
authority, selector, legacy fallback, or mathematics change was introduced.

## Boundary

Synthetic qualification is not real-root readiness. The next real-root
observation remains separately authorized and must re-establish evidence under
the frozen contracts above.
