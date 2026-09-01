# Blocker-5 B5-A1 — production environment convergence

## Verdict

~~~text
B5_A1_ENVIRONMENT_CONVERGENCE = PASS
ORDINARY_TORMENT_SQLITE = 3.53.4
ORDINARY_TORMENT_RUNTIME_ADMISSIBLE = YES
ENVIRONMENT_PACKAGE_MOVEMENT = sqlite/libsqlite only
SOLVER_MOVEMENT_RULE_REVISED = NO

CONNECTION_WAL_REQUALIFICATION = PASS
SCHEMA_REQUALIFICATION = PASS
E4D_WRITE_REQUALIFICATION_IN_TORMENT = PASS
E4E_QUERY_REQUALIFICATION_IN_TORMENT = PASS
PUBLIC_LEGACY_RUNTIME_REGRESSION = PASS
REST_SERVICE_LIFECYCLE = PASS
MCP_LEGACY_STARTUP_REGRESSION = PASS

PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO

KERNEL_FILES_CHANGED = 0
PRODUCTION_CODE_DIFF_COUNT = 0
~~~

This closes the environment-and-evidence boundary only. It does not introduce
a deployment selector, ACTIVE_CORE, native public routing, dual read/write,
a cutover fence, rollback, or a native production service.

## Starting state

The repository began at c48b1f0 (HEAD == origin/main) with a clean worktree.
The ordinary production environment was:

| Fact | Before |
| --- | --- |
| Environment | torment |
| Python | 3.11.15 |
| sqlite3 module | 2.6.0 |
| loaded SQLite runtime | 3.51.2 |
| native eligibility | no; the frozen policy accepts exactly 3.53.4 |
| installed SQLite package | sqlite 3.51.2 hee5a0db_0 |
| installed libsqlite package | absent |

The pre-change explicit Conda state was saved outside the repository. No full
environment export was committed.

## Solver gate and constrained transaction

The original online conda-forge dry-run could not retrieve metadata because of
local TLS certificate verification failure. SSL verification, CA configuration,
and network trust settings were not changed.

Safe local-cache dry-runs found the exact cached archives but proposed:

~~~text
add     libsqlite 3.53.4 hf5d6505_1
update  sqlite 3.51.2 -> 3.53.4 hdb435a2_1
update  ca-certificates 2026.6.17 -> 2026.7.22
update  openssl 3.6.3 -> 3.6.4
~~~

Both normal and --freeze-installed plans retained the latter two updates, so
they were rejected under the frozen collateral-movement rule. B5-A1R therefore
used no network and no dependency solve. It first proved the exact cached
package records and a disposable clone, then used this transaction in the
clone and, after it passed, in torment:

~~~cmd
conda install -n <environment> --offline --no-deps ^
  "<conda package cache>\sqlite-3.53.4-hdb435a2_1.conda" ^
  "<conda package cache>\libsqlite-3.53.4-hf5d6505_1.conda"
~~~

| Package | Version | Build | Build number | Subdir |
| --- | --- | --- | ---: | --- |
| sqlite | 3.53.4 | hdb435a2_1 | 1 | win-64 |
| libsqlite | 3.53.4 | hf5d6505_1 | 1 | win-64 |

Neither exact record declares an OpenSSL or CA-certificate dependency:

~~~text
OPENSSL_MOVEMENT_REQUIRED_BY_SQLITE_PACKAGE = NO
CA_CERT_MOVEMENT_REQUIRED_BY_SQLITE_PACKAGE = NO
~~~

The full dependency proof was:

| Required package | Constraint | Installed in torment before install | Satisfied? | ABI/runtime-sensitive |
| --- | --- | --- | --- | --- |
| sqlite | libsqlite 3.53.4 hf5d6505_1 | supplied by paired exact archive | yes | SQLite runtime |
| both exact records | ucrt >=10.0.20348.0 | ucrt 10.0.22621.0 | yes | yes |
| both exact records | vc >=14.3,<15 | vc 14.3 | yes | yes |
| both exact records | vc14_runtime >=14.44.35208 | vc14_runtime 14.44.35208 | yes | yes |

The records have no zlib/libzlib, OpenSSL, or CA-certificate dependency.
Existing low-level package records were inspected; none changed.

## Disposable-clone proof

torment-b5a1-probe was cloned from baseline torment, verified at Python
3.11.15, module 2.6.0, and SQLite 3.51.2, then snapshotted outside the
repository. The two local archives produced exactly:

~~~text
removed/replaced  sqlite-3.51.2-hee5a0db_0
added             sqlite-3.53.4-hdb435a2_1
added             libsqlite-3.53.4-hf5d6505_1
OTHER_PACKAGE_MOVEMENT = NONE
~~~

The clone loaded Python 3.11.15, module 2.6.0, and SQLite 3.53.4. Its
unmocked qualification reported JSON available, transaction/savepoint
available, runtime admissible, and reason qualified.

| Clone evidence | Result |
| --- | --- |
| runtime, connection/WAL, schema/bootstrap/current-STAGING core, and native routing | 83 passed |
| vector runtime, multi-scope admission/recovery, E1 ingest, A2 read model, A3 cognition-parity smoke | 34 passed, 12 skipped |

All listed clone tests used the clone's python -m pytest interpreter. A bare
pytest executable initially resolved to original torment; that pre-transaction
attempt was rejected as non-evidence.

After evidence capture and ordinary-environment qualification, the disposable
torment-b5a1-probe environment was removed. torment-substrate was retained
unchanged as the historical qualification environment.

## Ordinary production environment result

After the clone gate passed, the same archive transaction was applied to
ordinary torment. Its explicit before/after snapshots show exactly:

~~~text
removed/replaced  sqlite-3.51.2-hee5a0db_0
added             sqlite-3.53.4-hdb435a2_1
added             libsqlite-3.53.4-hf5d6505_1
ONLY_CHANGED_PACKAGES = sqlite, libsqlite
~~~

| Fact | After |
| --- | --- |
| Environment | torment |
| Python | 3.11.15 |
| sqlite3 module | 2.6.0 |
| loaded SQLite runtime | 3.53.4 |
| runtime qualification | JSON PASS; transaction/savepoint PASS; admissible YES; qualified |

No Python, OpenSSL, CA-certificate, application dependency, kernel dependency,
or TORMENT package record changed.

## Requalification evidence in ordinary torment

Every test command used ordinary torment's python -m pytest, isolated temporary
storage, and no production source modification.

| Evidence grouping | Result |
| --- | --- |
| unmocked runtime; connection/WAL; schema/bootstrap/current schema; router; multi-scope recovery; M1/M2; D0–D6; B1; vector freshness; retries and cold recovery | 206 passed, 12 skipped |
| E4E A1 identity locks, A2 native read model, A3 full cognition parity, NativeMemoryVectorRuntime, and multi-scope query recovery | 36 passed, 12 skipped |
| legacy public ingest/query, /retrieve, query explain, continuity, conflicts, Character context, SRG, governance filtering, and FastAPI test-client lifecycle | 398 passed |
| MCP legacy construction/startup and selector-name non-activation regression | 22 passed |

These native batches prove the actual runtime supports foreign keys, WAL,
synchronous-full-or-stronger policy, busy handling, same-thread connection
discipline, transactions/savepoints, and current schema compatibility. The
qualified profile remains compression/deep disabled; enabled compression still
refuses before effects.

## Real REST lifecycle smoke

python -m torment_service ran twice against one fresh temporary data root in
ordinary torment. The deterministic local smoke used hash embeddings and
disabled SQLite indexing; it set no native backend or selector.

Both starts completed normally. The first run proved:

~~~text
GET /health = 200 / ok
legacy workspace creation = PASS
legacy agent creation = PASS
legacy ingest = stored
legacy explained query = one result
~~~

The server's normal interrupt path logged application shutdown completion. The
second start reopened the same root, returned healthy status, and recovered the
persisted legacy memory through normal query; it also logged shutdown
completion. No native public request, resource, or selector was introduced.

## Comparison with torment-substrate

torment-substrate was retained unchanged.

| Contract fact | torment-substrate | ordinary torment |
| --- | --- | --- |
| Python | 3.11.15 | 3.11.15 |
| sqlite3 module | 2.6.0 | 2.6.0 |
| loaded SQLite | 3.53.4 | 3.53.4 |
| sqlite | 3.53.4 hdb435a2_1 | 3.53.4 hdb435a2_1 |
| libsqlite | 3.53.4 hf5d6505_1 | 3.53.4 hf5d6505_1 |

Both contain 69 explicit package records. Their only remaining record
differences are intentionally retained:

~~~text
torment-substrate: ca-certificates 2026.7.22; openssl 3.6.4
torment:           ca-certificates 2026.6.17; openssl 3.6.3
~~~

Those packages are not dependencies of the exact SQLite archives and were not
part of this SQLite-only convergence.

## Production state and next boundary

~~~text
PUBLIC_INGEST_BACKEND = LEGACY
PUBLIC_QUERY_BACKEND = LEGACY
DURABLE_DEPLOYMENT_SELECTOR_IMPLEMENTED = NO
ACTIVE_CORE_TRANSITION_IMPLEMENTED = NO
CUTOVER_FENCE_IMPLEMENTED = NO
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
~~~

The next separately authorized slice is B5-A2: external selector/era and
agreement resolver plus active-core/pending maintenance-transition mechanics.
It does not authorize public Fabric routing by itself.
