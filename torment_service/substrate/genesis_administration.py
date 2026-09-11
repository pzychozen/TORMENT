"""Offline Genesis I3: a root mutex, PREPARING fence, and inert prerequisites.

No public routing, source admission, external-owner bundle, semantic objects,
profile, memberships, representation generation, sealing, or activation.
"""

from __future__ import annotations

from contextlib import contextmanager, closing
from dataclasses import dataclass, replace
import hashlib
import math
import os
from pathlib import Path
import stat
import time
from typing import Callable
from uuid import UUID

from ..atomic_publication import publish_if_absent, replace_if_exact_predecessor
from ..diagnostic_query_timing import sqlite_connect
from ..external_owner_json import owner_bytes, strict_object
from .connection import (
    open_existing_native_bootstrap_connection, open_existing_native_core_connection,
    open_new_native_core_connection,
)
from .genesis_contracts import (
    GenesisAcceptedStart, GenesisAdministrativePhase, GenesisEvidenceReference,
    GenesisIntent, GenesisOperationRecord, GenesisQuiescenceObservation,
    GenesisStartKind, payload_digest,
)
from .genesis_fence import (
    CONTROL_DIRECTORY, LOCK_NAME, RECORD_NAME, GenesisPreparationRefused,
    canonical_genesis_root, checked_stat, read_genesis_operation_record,
)
from .runtime_qualification import qualify_runtime
from .schema import create_schema, require_current_schema
from .writer_freeze_evidence import (
    ListenerObservation, ListenerObservationResult, RootWriterClass,
    WriterObservationResult, WriterProcessObservation,
)

PRIVATE_DIRECTORY = CONTROL_DIRECTORY / "genesis-core-bootstrap"
PRIVATE_MANIFEST = PRIVATE_DIRECTORY / "intent.json"
PRIVATE_CORE = PRIVATE_DIRECTORY / "core.db"
CORE_DIRECTORY = Path("substrate/cores")
CATALOG_COLUMNS = {
    "identity_namespaces": ("identity_namespace_id", "namespace_key"),
    "semantic_scopes": ("semantic_scope_id", "scope_key"),
    "legacy_source_namespaces": ("legacy_source_namespace_id", "source_key"),
    "idempotency_namespaces": ("idempotency_namespace_id", "namespace_key"),
}


def _noop(_point: str) -> None:
    pass


def _ensure_directory(path: Path) -> None:
    info = checked_stat(path)
    if info is None:
        path.mkdir()  # never create undeclared ancestors
        _sync_directory(path.parent)
        info = checked_stat(path)
    if info is None or not stat.S_ISDIR(info.st_mode):
        raise GenesisPreparationRefused("Genesis directory is invalid")


def _establish_control(root: Path) -> None:
    for path in (root, root / "substrate", root / CONTROL_DIRECTORY):
        _ensure_directory(path)


@contextmanager
def root_onboarding_lock(*, data_root: str | Path, timeout_seconds: float = 1.0):
    """OS mutex only; possession does not attest quiescence or grant authority."""
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 <= timeout_seconds <= 60:
        raise GenesisPreparationRefused("root lock timeout must be between zero and 60 seconds")
    root = canonical_genesis_root(data_root)
    _establish_control(root)
    path = root / CONTROL_DIRECTORY / LOCK_NAME
    info = checked_stat(path)
    if info is not None and not stat.S_ISREG(info.st_mode):
        raise GenesisPreparationRefused("root rendezvous is not a regular file")
    deadline = time.monotonic() + timeout_seconds
    with path.open("a+b") as handle:
        while True:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise GenesisPreparationRefused("root-onboarding-lock-busy") from exc
                time.sleep(min(0.01, max(0, deadline - time.monotonic())))
        try:
            # Windows forbids reading another process's locked byte. Initialize
            # only after ownership; locking one byte beyond EOF is supported.
            handle.seek(0)
            if not handle.read(1):
                handle.write(b"0")
                handle.flush()
                os.fsync(handle.fileno())
            yield root
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _inventory(root: Path) -> dict[str, tuple]:
    """No SQLite; retain file identity/content for the before/after lock check."""
    entries = {}

    def visit(path: Path):
        info = checked_stat(path)
        if info is None:
            return
        name = "." if path == root else path.relative_to(root).as_posix()
        directory = stat.S_ISDIR(info.st_mode)
        fingerprint = (directory, info.st_dev, info.st_ino)
        if not directory and not path.name.endswith(".lock"):
            fingerprint += (info.st_size, info.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        entries[name] = fingerprint
        if directory:
            for child in sorted(path.iterdir()):
                visit(child)

    visit(root)
    return entries


def _matching_record(root: Path, intent: GenesisIntent) -> GenesisOperationRecord | None:
    record = read_genesis_operation_record(data_root=root)
    if record is not None and (
        record.expanded_intent != intent or
        record.administrative_phase is not GenesisAdministrativePhase.PREPARING
    ):
        raise GenesisPreparationRefused("competing Genesis intent or unsupported later phase")
    return record


def _recovery_paths(intent: GenesisIntent, record: GenesisOperationRecord) -> dict[str, bool]:
    expected = {name: name != GenesisAcceptedStart.CONTROL_ENTRIES[-1]
                for name in GenesisAcceptedStart.CONTROL_ENTRIES}
    for file in record.accepted_start_observation.payload()["observed_entries"]:
        if file in GenesisAcceptedStart.ALLOWED_FILES:
            expected[file] = False
    for path in (PRIVATE_DIRECTORY, CORE_DIRECTORY):
        expected[path.as_posix()] = True
    core = CORE_DIRECTORY / intent.payload()["allocations"]["core_relative_path"]
    for path in (CONTROL_DIRECTORY / RECORD_NAME,
                 CONTROL_DIRECTORY / f".{RECORD_NAME}.publication.lock",
                 PRIVATE_MANIFEST, PRIVATE_CORE, core):
        expected[path.as_posix()] = False
    for path in (PRIVATE_CORE, core):
        for suffix in ("-wal", "-shm", "-journal"):
            expected[path.as_posix() + suffix] = False
    return expected


def _classify(root: Path, intent: GenesisIntent, entries: dict[str, tuple]) -> GenesisAcceptedStart:
    if str(root) != intent.data_root_identity:
        raise GenesisPreparationRefused("intent must name the canonical explicit root")
    record = _matching_record(root, intent)
    names = set(entries)
    observed = []
    operation = None
    if record is not None:
        allowed = _recovery_paths(intent, record)
        if any(name not in allowed or value[0] != allowed[name] for name, value in entries.items()):
            raise GenesisPreparationRefused("unknown artifact in Genesis recovery root")
        for name in names:
            if name.endswith(("-wal", "-shm", "-journal")) and name.rsplit("-", 1)[0] not in names:
                raise GenesisPreparationRefused("orphan SQLite sidecar")
        kind = GenesisStartKind.MATCHING_GENESIS_RECOVERY_STATE
        operation = intent.operation_key
    elif not entries:
        kind = GenesisStartKind.ABSENT_ROOT
    elif names == {"."}:
        kind = GenesisStartKind.EMPTY_ROOT
    elif names - {"."} <= GenesisAcceptedStart.ALLOWED_FILES and all(not entries[n][0] for n in names - {"."}):
        kind = GenesisStartKind.ALLOWED_NON_AUTHORITATIVE_ROOT_FILES
        observed = sorted(names - {"."})
    else:
        prefix = GenesisAcceptedStart.CONTROL_ENTRIES[:len(entries)]
        if names != set(prefix) or any(entries[n][0] != (n != GenesisAcceptedStart.CONTROL_ENTRIES[-1]) for n in names):
            raise GenesisPreparationRefused("root is not an accepted Genesis start")
        kind = GenesisStartKind.PRE_INTENT_GENESIS_CONTROL_RESIDUE
        observed = list(prefix)
    return GenesisAcceptedStart.from_payload(dict(
        classification=kind.value, data_root_identity=str(root), observed_at_ns=time.time_ns(),
        observed_entries=observed, matching_operation_key=operation,
    ))


def inspect_genesis_start(*, data_root: str | Path, intent: GenesisIntent) -> GenesisAcceptedStart:
    root = canonical_genesis_root(data_root)
    return _classify(root, intent, _inventory(root))


@dataclass(frozen=True)
class GenesisWriterObservation:
    """Injected current-root facts, distinct from attestation and OS ownership."""
    data_root_identity: str
    operation_key: str
    observed_at_ns: int
    writers: tuple[WriterProcessObservation, ...]
    listeners: tuple[ListenerObservation, ...]
    complete: bool
    competing_operation_keys: tuple[str, ...] = ()

    def evidence(self, intent: GenesisIntent, *, since_ns: int,
                 operator_attestation: str, issuer_reference: str) -> GenesisQuiescenceObservation:
        if self.data_root_identity != intent.data_root_identity or self.operation_key != intent.operation_key:
            raise GenesisPreparationRefused("writer observation names another root or operation")
        if self.complete is not True or type(self.observed_at_ns) is not int or not since_ns <= self.observed_at_ns <= time.time_ns():
            raise GenesisPreparationRefused("incomplete or stale writer observation")
        if type(self.competing_operation_keys) is not tuple or self.competing_operation_keys:
            raise GenesisPreparationRefused("competing Genesis operation observed")
        if (type(self.writers) is not tuple or
            any(not isinstance(v, WriterProcessObservation) for v in self.writers) or
            len(self.writers) != len(RootWriterClass) or
            {v.writer_class for v in self.writers} != set(RootWriterClass)):
            raise GenesisPreparationRefused("incomplete or duplicate writer classes")
        if any(v.result not in (WriterObservationResult.ABSENT, WriterObservationResult.STOPPED) for v in self.writers):
            raise GenesisPreparationRefused("writer running or unresolved")
        if (type(self.listeners) is not tuple or not self.listeners or
            any(not isinstance(v, ListenerObservation) for v in self.listeners) or
            len({v.listener_identity for v in self.listeners}) != len(self.listeners)):
            raise GenesisPreparationRefused("incomplete or duplicate listener observation")
        if any(v.result is not ListenerObservationResult.ABSENT for v in self.listeners):
            raise GenesisPreparationRefused("listener active or unresolved")
        return GenesisQuiescenceObservation.from_payload(dict(
            data_root_identity=self.data_root_identity, operation_key=self.operation_key,
            observed_at_ns=self.observed_at_ns, operator_attestation=operator_attestation,
            issuer_reference=issuer_reference, observations=dict(
                complete=True, writers=[v.payload() for v in self.writers],
                listeners=[v.payload() for v in self.listeners], competing_operation_keys=[],
            ),
        ))


class GenesisAdministration:
    """One live lock session. Construct through begin_genesis_administration."""

    def __init__(self, root: Path, record: GenesisOperationRecord, fault: Callable[[str], None]):
        self.root, self.record, self.fault = root, record, fault
        self._active = True
        self._quiescent = False

    @property
    def intent(self) -> GenesisIntent:
        return self.record.expanded_intent

    def _require_active(self):
        if not self._active:
            raise GenesisPreparationRefused("Genesis administrative lock session has ended")

    def replace_record(self, expected: GenesisOperationRecord, replacement: GenesisOperationRecord):
        self._require_active()
        if (expected.expanded_intent != self.intent or replacement.expanded_intent != self.intent or
            replacement.accepted_start_observation != expected.accepted_start_observation or
            expected.administrative_phase is not GenesisAdministrativePhase.PREPARING or
            replacement.administrative_phase is not GenesisAdministrativePhase.PREPARING or
            replacement.phase_revision != expected.phase_revision + 1 or
            replacement.child_operation_references[:len(expected.child_operation_references)] != expected.child_operation_references or
            replacement.quiescence_observations[:len(expected.quiescence_observations)] != expected.quiescence_observations):
            raise GenesisPreparationRefused("checkpoint is not an append-only PREPARING successor")
        path = self.root / CONTROL_DIRECTORY / RECORD_NAME
        checked_stat(path)
        predecessor_bytes = path.read_bytes()
        current = GenesisOperationRecord.from_payload(strict_object(predecessor_bytes))
        if current == replacement:
            self.record = replacement
            return
        if current != expected:
            raise GenesisPreparationRefused("checkpoint predecessor conflicts")
        replace_if_exact_predecessor(path, predecessor_bytes, owner_bytes(replacement.payload()))
        self.record = replacement
        self.fault("after-checkpoint")

    def observe_quiescence(self, observer: Callable[[Path, GenesisIntent], GenesisWriterObservation], *,
                           operator_attestation: str, issuer_reference: str) -> GenesisQuiescenceObservation:
        self._require_active()
        self._quiescent = False
        since = time.time_ns()
        facts = observer(self.root, self.intent)  # called only after durable PREPARING
        if not isinstance(facts, GenesisWriterObservation):
            raise GenesisPreparationRefused("typed writer observation required")
        evidence = facts.evidence(self.intent, since_ns=since,
                                  operator_attestation=operator_attestation, issuer_reference=issuer_reference)
        # Reinspect for paths created by a racing/non-cooperating startup.
        _classify(self.root, self.intent, _inventory(self.root))
        current = _matching_record(self.root, self.intent)
        if current != self.record:
            raise GenesisPreparationRefused("administrative record changed during observation")
        self.replace_record(self.record, replace(
            self.record, phase_revision=self.record.phase_revision + 1,
            quiescence_observations=self.record.quiescence_observations + (evidence,),
        ))
        self._quiescent = True
        return evidence

    def _reference(self, owner: str, result: dict) -> GenesisEvidenceReference:
        # Bounded deterministic child identity even for a 160-character parent key.
        return GenesisEvidenceReference.from_payload(dict(
            owner=owner, operation_key="genesis-i3:" + payload_digest(dict(intent=self.intent.digest, owner=owner)),
            result_digest=payload_digest(result),
        ))

    def _has_reference(self, reference: GenesisEvidenceReference) -> bool:
        for existing in self.record.child_operation_references:
            if existing.payload()["owner"] == reference.payload()["owner"]:
                if existing != reference:
                    raise GenesisPreparationRefused("child checkpoint conflicts with native result")
                return True
        return False

    def _checkpoint_child(self, reference: GenesisEvidenceReference):
        if not self._has_reference(reference):
            self.fault("before-checkpoint:" + reference.payload()["owner"])
            self.replace_record(self.record, replace(
                self.record, phase_revision=self.record.phase_revision + 1,
                child_operation_references=self.record.child_operation_references + (reference,),
            ))

    def prepare_inert_core(self) -> Path:
        self._require_active()
        if not self._quiescent:
            raise GenesisPreparationRefused("fresh successful quiescence observation required")
        _classify(self.root, self.intent, _inventory(self.root))
        expected = genesis_prerequisites(self.intent)
        path = self.root / CORE_DIRECTORY / self.intent.payload()["allocations"]["core_relative_path"]
        core_ref = self._reference("native-core-preparation", _bootstrap_manifest(self.intent))
        catalog_refs = {table: self._reference("native-catalog:" + table, dict(table=table, rows=rows))
                        for table, rows in expected.items()}
        allowed_refs = {core_ref, *catalog_refs.values()}
        if any(ref not in allowed_refs for ref in self.record.child_operation_references):
            raise GenesisPreparationRefused("unsupported or conflicting I3 child checkpoint")
        if self.record.child_operation_references and not path.is_file():
            raise GenesisPreparationRefused("checkpointed core is missing")
        if path.is_file():
            with closing(_open_readonly(path)) as connection:
                present = _verify_native(connection, self.intent, expected)
            for table, reference in catalog_refs.items():
                if self._has_reference(reference) and present[table] != expected[table]:
                    raise GenesisPreparationRefused("checkpointed native prerequisites are missing")
        _prepare_core(self, path, expected)
        self._checkpoint_child(core_ref)
        with open_existing_native_core_connection(path) as opened:
            connection = opened.connection
            for table, rows in expected.items():
                reference = catalog_refs[table]
                present = _verify_native(connection, self.intent, expected)
                if self._has_reference(reference) and present[table] != rows:
                    raise GenesisPreparationRefused("checkpointed native prerequisites are missing")
                if present[table] != rows:
                    connection.execute("BEGIN IMMEDIATE")
                    try:
                        # Recheck under the SQLite write lock as well as the root mutex.
                        present = _verify_native(connection, self.intent, expected, schema_gate=False)
                        for identifier, key in rows.items():
                            if identifier not in present[table]:
                                id_column, key_column = CATALOG_COLUMNS[table]
                                columns = f"{id_column},{key_column}"
                                values = "?,?"
                                if table != "idempotency_namespaces":
                                    columns += ",created_at_ns"
                                    values += ",0"
                                connection.execute(f"INSERT INTO {table} ({columns}) VALUES ({values})", (UUID(identifier).bytes, key))
                                self.fault("during-catalog:" + table)
                        connection.execute("COMMIT")
                    except BaseException:
                        if connection.in_transaction:
                            connection.execute("ROLLBACK")
                        raise
                    self.fault("after-native-commit:" + table)
                self._checkpoint_child(reference)
            _verify_native(connection, self.intent, expected, complete=True)
        return path


@contextmanager
def begin_genesis_administration(*, data_root: str | Path, intent: GenesisIntent,
                                 timeout_seconds: float = 1.0, fault: Callable[[str], None] = _noop):
    """Inspect, lock, prove the control-only delta, then publish the first fence."""
    root = canonical_genesis_root(data_root)
    before = _inventory(root)
    accepted = _classify(root, intent, before)
    with root_onboarding_lock(data_root=root, timeout_seconds=timeout_seconds):
        after = _inventory(root)
        controls = set(GenesisAcceptedStart.CONTROL_ENTRIES)
        if (any(after.get(name) != value for name, value in before.items()) or
            not set(after).difference(before) <= controls):
            raise GenesisPreparationRefused("root changed beyond the fixed pre-intent control residue")
        # Verify fixed path types, then preserve the truthful PRE-lock observation
        # (e.g. README.md plus only our newly introduced control tree).
        for name in controls:
            if name not in after or after[name][0] != (name != GenesisAcceptedStart.CONTROL_ENTRIES[-1]):
                raise GenesisPreparationRefused("fixed pre-intent control residue is invalid")
        record = _matching_record(root, intent)
        if record is None:
            record = GenesisOperationRecord(intent, intent.digest, accepted,
                GenesisAdministrativePhase.PREPARING, 1, (), (), None, ())
            path = root / CONTROL_DIRECTORY / RECORD_NAME
            publish_if_absent(path, owner_bytes(record.payload()))
            published = _matching_record(root, intent)
            if published != record:
                raise GenesisPreparationRefused("initial Genesis record publication conflict")
        fault("after-record-publication")
        session = GenesisAdministration(root, record, fault)
        try:
            yield session
        finally:
            session._active = False
            session._quiescent = False


def prepare_genesis_inert_root(*, data_root: str | Path, intent: GenesisIntent,
                              observer: Callable[[Path, GenesisIntent], GenesisWriterObservation],
                              operator_attestation: str, issuer_reference: str,
                              timeout_seconds: float = 1.0, fault: Callable[[str], None] = _noop) -> GenesisOperationRecord:
    with begin_genesis_administration(data_root=data_root, intent=intent, timeout_seconds=timeout_seconds, fault=fault) as session:
        session.observe_quiescence(observer, operator_attestation=operator_attestation, issuer_reference=issuer_reference)
        session.prepare_inert_core()
        return session.record


def genesis_prerequisites(intent: GenesisIntent) -> dict[str, dict[str, str]]:
    """Exact generic catalogs, with semantic-scope keys derived from their UUIDs.

    No additional generated identities or semantic rows. Historical alias-table
    names describe the native EID/motif alias catalogs, not source observations.
    """
    allocations = intent.payload()["allocations"]
    keys = allocations["namespace_keys"]
    result = {table: {} for table in CATALOG_COLUMNS}
    profile_operation_namespace = allocations["root_profile_idempotency_namespace_id"]
    result["idempotency_namespaces"][profile_operation_namespace] = keys[profile_operation_namespace]
    root_id = allocations["root_profile_identity_namespace_id"]
    result["identity_namespaces"][root_id] = keys[root_id]
    scope_id = allocations["root_profile_semantic_scope_id"]
    result["semantic_scopes"][scope_id] = "genesis-semantic-scope:" + scope_id
    mapping = {
        "target_identity_namespace_id": "identity_namespaces",
        "motif_identity_namespace_id": "identity_namespaces",
        "membership_identity_namespace_id": "identity_namespaces",
        "legacy_source_namespace_id": "legacy_source_namespaces",
        "motif_alias_namespace_id": "legacy_source_namespaces",
        "idempotency_namespace_id": "idempotency_namespaces",
    }
    for plan in intent.runtime_plans:
        scope = plan.payload()["scope_plan"]
        for field, table in mapping.items():
            identifier = scope[field]
            result[table][identifier] = keys[identifier]
        identifier = scope["target_semantic_scope_id"]
        result["semantic_scopes"][identifier] = "genesis-semantic-scope:" + identifier
    return result


def _bootstrap_manifest(intent: GenesisIntent) -> dict:
    allocations = intent.payload()["allocations"]
    return dict(contract="TORMENT_GENESIS_PRIVATE_BOOTSTRAP", version=1,
                operation_key=intent.operation_key, intent_digest=intent.digest,
                core_id=allocations["core_id"], core_relative_path=allocations["core_relative_path"])


def _open_readonly(path: Path):
    qualify_runtime()
    connection = sqlite_connect(f"{path.as_uri()}?mode=ro", uri=True, isolation_level=None)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA query_only = ON")
        return connection
    except BaseException:
        connection.close()
        raise


def _verify_native(connection, intent: GenesisIntent, expected: dict, *, complete=False, schema_gate=True):
    if schema_gate:
        metadata = require_current_schema(connection)
        if metadata.core_id != UUID(intent.payload()["allocations"]["core_id"]).bytes or metadata.core_role != "STAGING":
            raise GenesisPreparationRefused("foreign or non-inert core identity")
    else:
        row = connection.execute("SELECT core_id,core_role FROM core_metadata").fetchall()
        if row != [(UUID(intent.payload()["allocations"]["core_id"]).bytes, "STAGING")]:
            raise GenesisPreparationRefused("foreign or non-inert core identity")
    if connection.execute("SELECT deployment_state,referenced_core_id FROM deployment_metadata").fetchall() != [("LEGACY_ACTIVE", None)]:
        raise GenesisPreparationRefused("core deployment is not inert")
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='view' LIMIT 1").fetchone() is not None:
        raise GenesisPreparationRefused("undeclared native schema view")
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in tables - set(CATALOG_COLUMNS) - {"core_metadata", "deployment_metadata"}:
        if connection.execute(f'SELECT 1 FROM "{table}" LIMIT 1').fetchone() is not None:
            raise GenesisPreparationRefused("unexpected native content outside Genesis prerequisites")
    present = {}
    for table, (id_column, key_column) in CATALOG_COLUMNS.items():
        suffix = "" if table == "idempotency_namespaces" else ",created_at_ns"
        rows = connection.execute(f"SELECT {id_column},{key_column}{suffix} FROM {table}").fetchall()
        if suffix and any(row[2] != 0 for row in rows):
            raise GenesisPreparationRefused("namespace creation facts conflict")
        actual = {str(UUID(bytes=row[0])): row[1] for row in rows}
        if any(expected[table].get(identifier) != key for identifier, key in actual.items()):
            raise GenesisPreparationRefused("undeclared namespace, scope, UUID, or key")
        if complete and actual != expected[table]:
            raise GenesisPreparationRefused("native prerequisite closure is incomplete")
        present[table] = actual
    return present


def _sync_file_and_parent(path: Path):
    with path.open("r+b") as handle:
        os.fsync(handle.fileno())
    _sync_directory(path.parent)


def _sync_directory(path: Path):
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _prepare_core(session: GenesisAdministration, path: Path, expected: dict):
    root, intent = session.root, session.intent
    manifest_path, private = root / PRIVATE_MANIFEST, root / PRIVATE_CORE
    manifest = _bootstrap_manifest(intent)
    if manifest_path.exists() and strict_object(manifest_path.read_bytes()) != manifest:
        raise GenesisPreparationRefused("private bootstrap intent conflicts")
    if path.exists():
        with closing(_open_readonly(path)) as connection:
            _verify_native(connection, intent, expected)
        if private.exists():
            if not manifest_path.is_file() or strict_object(manifest_path.read_bytes()) != manifest or not os.path.samefile(path, private):
                raise GenesisPreparationRefused("unexplained private core alongside published core")
            private.unlink()  # our completed link publication, never a foreign core
            _sync_directory(private.parent)
        return
    _ensure_directory(root / PRIVATE_DIRECTORY)
    if private.exists() and not manifest_path.exists():
        raise GenesisPreparationRefused("private bootstrap has no matching immutable intent")
    if manifest_path.exists():
        if strict_object(manifest_path.read_bytes()) != manifest:
            raise GenesisPreparationRefused("private bootstrap intent conflicts")
    else:
        publish_if_absent(manifest_path, owner_bytes(manifest))
        if strict_object(manifest_path.read_bytes()) != manifest:
            raise GenesisPreparationRefused("private bootstrap publication conflicts")
    opener = open_new_native_core_connection
    if private.exists():
        with closing(_open_readonly(private)) as connection:
            objects = connection.execute("SELECT name FROM sqlite_master").fetchall()
            if objects:
                _verify_native(connection, intent, expected)
        # Only the exact recorded private filename with its matching manifest
        # can resume an interrupted initial schema transaction (zero tables).
        opener = open_existing_native_bootstrap_connection
    with opener(private) as opened:
        session.fault("after-private-open")
        create_schema(opened.connection, core_id=UUID(intent.payload()["allocations"]["core_id"]))
        _verify_native(opened.connection, intent, expected)
        if opened.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone() != (0, 0, 0):
            raise GenesisPreparationRefused("private core checkpoint did not complete")
    _sync_file_and_parent(private)
    session.fault("after-private-preparation")
    _ensure_directory(root / CORE_DIRECTORY)
    try:
        os.link(private, path)  # complete, closed SQLite file; no replacing a target
    except FileExistsError:
        if not os.path.samefile(private, path):
            raise GenesisPreparationRefused("native core publication target already exists")
    _sync_file_and_parent(path)
    session.fault("after-core-publication")
    private.unlink()
    _sync_directory(private.parent)
