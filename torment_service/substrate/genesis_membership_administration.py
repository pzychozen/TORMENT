"""Offline I5 root profile and initial memberships under the existing I3 lock.

Native objects and relationships own authority. The PREPARING record retains
only references; this module neither plants a Character nor completes Genesis.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from uuid import UUID

from . import genesis_administration as i3
from . import genesis_character_administration as i4
from .canonical_intent import canonical_intent_text
from .connection import open_existing_native_core_connection
from .deployment_types import QualifiedDeploymentProfile
from .genesis_contracts import (
    GenesisEvidenceReference, GenesisIntent, GenesisMembershipReference,
    GenesisRootProfileReference, initial_membership_closure_digest,
    payload_digest, runtime_plan_digest, text,
)
from .genesis_fence import GenesisPreparationRefused, canonical_genesis_root
from .native_character_seed_plant import NativeCharacterSeedPlantRequest, NativeCharacterSeedPlantRuntime
from .objects import NativeObjectService, ObjectState
from .relationships import NativeRelationshipService
from .root_profile import (
    ROOT_NATIVE_PROFILE_GENERATION_KIND, current_root_profile_generation,
    root_profile_generation_payload, verify_root_profile_generation,
)
from .root_scope_membership import (
    ROOT_SCOPE_MEMBERSHIP_KIND, RootScopeMembershipReader,
    RootScopeMembershipService, RootScopeMembershipWitness,
)
from .runtime_binding import NativeMemoryRuntimeScope
from .schema import require_current_schema

_LIVE_SESSION = object()
_OWNERS = ("root-profile-generation", "initial-root-membership-closure")


def qualified_genesis_profile(intent: GenesisIntent) -> QualifiedDeploymentProfile:
    """Use the frozen production profile and I1 projections, without persistence."""
    return QualifiedDeploymentProfile(**intent.payload()["profile_choice"],
        admitted_scope_plan_digest=runtime_plan_digest(intent.runtime_plans),
        external_owner_digest=payload_digest(intent.external_owner_projection()))


def _operation_key(intent, role, **facts):
    return "genesis-i5:" + payload_digest(dict(
        genesis_operation_key=intent.operation_key, intent_digest=intent.digest,
        role=role, profile_generation=intent.payload()["allocations"]["root_profile_generation"], **facts))


def _reference(intent, owner, result):
    return GenesisEvidenceReference.from_payload(dict(owner=owner,
        operation_key=_operation_key(intent, owner), result_digest=payload_digest(result)))


def _publication_plans(intent):
    plans = [p.payload() for p in intent.runtime_plans]
    shared = {p["scope_key"]["domain_id"]: p for p in plans if p["scope_key"]["scope_kind"] == "SHARED"}
    private = [p for p in plans if p["scope_key"]["scope_kind"] == "PRIVATE"]
    return tuple(shared[domain] for domain in intent.payload()["workspace"]["ordered_domains"]) + tuple(private)


def _runtime_scope(plan):
    scope, key = plan["scope_plan"], plan["scope_key"]
    return NativeMemoryRuntimeScope(workspace_id=scope["workspace_id"], scope_kind=scope["scope_kind"],
        legacy_source_namespace_id=UUID(scope["legacy_source_namespace_id"]),
        identity_namespace_id=UUID(scope["target_identity_namespace_id"]),
        semantic_scope_id=UUID(scope["target_semantic_scope_id"]),
        agent_id=key["agent_id"], domain_id=key["domain_id"])


def _witness(intent, profile, plan, issuer):
    text(issuer, "operator issuer reference")
    evidence = dict(actor="LOCAL_HUMAN_OPERATOR", genesis_operation_key=intent.operation_key,
        intent_digest=intent.digest, root_profile=i4._json_result(asdict(profile)),
        runtime_scope_plan=plan, scope_key=plan["scope_key"], issuer_reference=issuer)
    digest = payload_digest(evidence)
    return RootScopeMembershipWitness("genesis-i5-membership:" + digest, digest, issuer, "EXTERNAL_ISSUED")


def _profile_state(intent):
    allocation = intent.payload()["allocations"]
    return ObjectState(UUID(allocation["root_profile_identity_namespace_id"]),
        UUID(allocation["root_profile_semantic_scope_id"]), ROOT_NATIVE_PROFILE_GENERATION_KIND,
        "EXISTS", "ACTIVE", True, "QUALIFIED", "EVIDENCE",
        root_profile_generation_payload(allocation["root_profile_generation"]), "JSON")


class _CommittedLane:
    """Metadata required by the existing recovery API; no provider is constructed."""
    def __init__(self, intent):
        lane = intent.payload()["representation_lane"]
        self.provider, self.model, self.dim = lane["provider"], lane["model"], lane["dimension"]

    def embed(self, _text):
        raise GenesisPreparationRefused("I5 may only recover committed Character evidence")


def _receipt(connection, namespace, key, kind, intent_text, output_kind, identifier, revision, ordinal):
    row = connection.execute("SELECT operation_id,operation_kind,intent_contract,canonical_intent_json "
        "FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?", (namespace.bytes, key)).fetchone()
    if row is None or row[1:] != (kind, "TMS-INTENT-1", intent_text):
        raise GenesisPreparationRefused("I5 native operation receipt conflicts or is absent")
    column = "object" if output_kind == "OBJECT" else "relationship"
    outputs = connection.execute(f"SELECT output_role,output_kind,{column}_id,{column}_revision_id,"
        f"{column}_revision_ordinal FROM operation_outputs WHERE operation_id=?", (row[0],)).fetchall()
    if outputs != [(output_kind, output_kind, identifier.bytes, revision.bytes, ordinal)]:
        raise GenesisPreparationRefused("I5 operation output does not identify the initial native revision")
    transitions = connection.execute("SELECT transition_id,transition_kind,origin_kind FROM semantic_transitions "
        "WHERE operation_id=?", (row[0],)).fetchall()
    if len(transitions) != 1 or transitions[0][1:] != (output_kind + "_REVISION", "NATIVE"):
        raise GenesisPreparationRefused("I5 initial native transition receipt conflicts")
    effects = connection.execute(f"SELECT {column}_id,{column}_revision_id,{column}_revision_ordinal "
        f"FROM {column}_revision_effects WHERE transition_id=?", (transitions[0][0],)).fetchall()
    if effects != [(identifier.bytes, revision.bytes, ordinal)]:
        raise GenesisPreparationRefused("I5 initial native revision effect conflicts")
    return row[0]


def _recover_profile(connection, intent):
    allocation = intent.payload()["allocations"]
    oid = UUID(allocation["root_profile_object_id"])
    rows = connection.execute("SELECT object_id FROM objects WHERE object_kind=? OR object_id=?",
        (ROOT_NATIVE_PROFILE_GENERATION_KIND, oid.bytes)).fetchall()
    if not rows:
        return None
    if rows != [(oid.bytes,)]:
        raise GenesisPreparationRefused("I5 root profile object identity or count conflicts")
    profile = current_root_profile_generation(connection)
    verify_root_profile_generation(connection, profile)
    if (profile.core_id != UUID(allocation["core_id"]) or profile.profile_object_id != oid
        or profile.profile_generation != allocation["root_profile_generation"]
        or profile.profile_semantic_scope_id != UUID(allocation["root_profile_semantic_scope_id"])
        or profile.profile_revision_ordinal != 1):
        raise GenesisPreparationRefused("I5 root profile reference conflicts")
    state = _profile_state(intent)
    actual = connection.execute("SELECT o.identity_namespace_id,r.object_revision_id,r.revision_ordinal,"
        "r.lineage_kind,r.predecessor_revision_id,r.predecessor_revision_ordinal,r.effective_semantic_scope_id,"
        "r.existence_state,r.lifecycle_state,r.lifecycle_authoritative,r.governance_state,r.authority_category,"
        "r.provenance_id,r.payload_format,r.payload_text FROM objects o JOIN object_revisions r ON r.object_id=o.object_id "
        "WHERE o.object_id=?", (oid.bytes,)).fetchall()
    expected = (state.identity_namespace_id.bytes, profile.profile_revision_id.bytes, 1, "NATIVE_CREATION", None, None,
        state.semantic_scope_id.bytes, "EXISTS", "ACTIVE", 1, "QUALIFIED", "EVIDENCE", None, "JSON",
        canonical_intent_text(state.payload))
    if actual != [expected]:
        raise GenesisPreparationRefused("I5 root profile immutable state conflicts")
    _receipt(connection, UUID(allocation["root_profile_idempotency_namespace_id"]),
        _operation_key(intent, _OWNERS[0]), "CREATE_OBJECT", NativeObjectService._intent("CREATE_OBJECT", state, oid, None),
        "OBJECT", oid, profile.profile_revision_id, 1)
    return profile


def _recover_members(connection, intent, profile, issuer):
    all_ids = {r[0] for r in connection.execute("SELECT relationship_id FROM relationships WHERE relationship_kind=?",
        (ROOT_SCOPE_MEMBERSHIP_KIND,))}
    if profile is None:
        if all_ids:
            raise GenesisPreparationRefused("I5 memberships exist without the allocated profile")
        return ()
    records = RootScopeMembershipReader(connection).recover(profile)
    if {r.relationship_id.bytes for r in records} != all_ids:
        raise GenesisPreparationRefused("I5 membership belongs to a foreign profile or revision")
    plans = _publication_plans(intent)
    by_scope = {r.semantic_scope_id: r for r in records}
    if len(by_scope) != len(records):
        raise GenesisPreparationRefused("I5 duplicate membership semantic scope")
    recovered, gap = [], False
    service = RootScopeMembershipService(connection)
    for plan in plans:
        scope = _runtime_scope(plan)
        record = by_scope.pop(scope.semantic_scope_id, None)
        if record is None:
            gap = True
            continue
        key = plan["scope_key"]
        actual_key = record.runtime_key.scope_key
        if (gap or actual_key.workspace_id != key["workspace_id"] or actual_key.scope_kind.value != key["scope_kind"]
            or actual_key.agent_id != key["agent_id"] or actual_key.domain_id != key["domain_id"]
            or record.runtime_key.profile != profile or not record.active or record.relationship_revision_ordinal != 1
            or record.membership_identity_namespace_id != UUID(plan["scope_plan"]["membership_identity_namespace_id"])
            or record.witness != _witness(intent, profile, plan, issuer)):
            raise GenesisPreparationRefused("I5 initial membership identity, witness, lifecycle or publication order conflicts")
        state = service._relationship_state(profile=profile, runtime_scope=scope, witness=record.witness,
            membership_identity_namespace_id=record.membership_identity_namespace_id, lifecycle_state="ACTIVE")
        rows = connection.execute("SELECT revision_ordinal,lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,"
            "effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,governance_state,"
            "authority_category,provenance_id,payload_format,payload_text FROM relationship_revisions WHERE relationship_id=?",
            (record.relationship_id.bytes,)).fetchall()
        if rows != [(1, "NATIVE_CREATION", None, None, scope.semantic_scope_id.bytes,
            "EXISTS", "ACTIVE", 1, "QUALIFIED", "EVIDENCE", None, "JSON", canonical_intent_text(state.payload))]:
            raise GenesisPreparationRefused("I5 initial membership revision conflicts")
        endpoints = connection.execute("SELECT endpoint_ordinal,endpoint_role,endpoint_semantic_scope_id,object_id,"
            "binding_mode,bound_object_revision_id,bound_object_revision_ordinal FROM relationship_revision_endpoints "
            "WHERE relationship_revision_id=?", (record.relationship_revision_id.bytes,)).fetchall()
        if endpoints != [(0, "ROOT_PROFILE_GENERATION", profile.profile_semantic_scope_id.bytes,
            profile.profile_object_id.bytes, "EXACT_REVISION", profile.profile_revision_id.bytes, 1)]:
            raise GenesisPreparationRefused("I5 membership endpoint closure conflicts")
        _receipt(connection, UUID(plan["scope_plan"]["idempotency_namespace_id"]),
            _operation_key(intent, "initial-membership", scope_key=key), "CREATE_RELATIONSHIP",
            NativeRelationshipService._intent("CREATE", state, None, None),
            "RELATIONSHIP", record.relationship_id, record.relationship_revision_id, 1)
        recovered.append(record)
    if by_scope:
        raise GenesisPreparationRefused("I5 contains a foreign membership scope")
    return tuple(recovered)


@dataclass(frozen=True)
class GenesisInitialMembershipClosure:
    qualified_deployment_profile: QualifiedDeploymentProfile
    root_profile: GenesisRootProfileReference
    initial_memberships: tuple[GenesisMembershipReference, ...]
    initial_membership_closure_digest: str
    child_references: tuple[GenesisEvidenceReference, ...]


def _closure(intent, profile, records):
    if profile is None or len(records) != len(intent.runtime_plans):
        return None
    reference = GenesisRootProfileReference.from_payload(i4._json_result(asdict(profile)))
    members = tuple(GenesisMembershipReference.from_payload(dict(scope_key=plan["scope_key"],
        relationship_id=str(record.relationship_id), relationship_revision_id=str(record.relationship_revision_id),
        relationship_revision_ordinal=record.relationship_revision_ordinal, lifecycle=record.lifecycle_state,
        membership_witness=record.witness.payload())) for plan, record in zip(_publication_plans(intent), records, strict=True))
    digest = initial_membership_closure_digest(reference, intent.runtime_plans, members)
    refs = (_reference(intent, _OWNERS[0], reference.payload()),
        _reference(intent, _OWNERS[1], dict(initial_membership_closure_digest=digest)))
    return GenesisInitialMembershipClosure(qualified_genesis_profile(intent), reference, members, digest, refs)


def _verify_core(connection, intent, profile, records):
    """Verify I3 catalogs and the exact union of committed I4 and initial I5 effects.

    I4's stricter, seed-only verifier remains unchanged. Recovery here accepts
    only the separately verified profile and membership revisions in addition.
    """
    metadata = require_current_schema(connection)
    allocation = intent.payload()["allocations"]
    if (metadata.core_id != UUID(allocation["core_id"]).bytes or metadata.core_role != "STAGING"
        or connection.execute("SELECT deployment_state,referenced_core_id FROM deployment_metadata").fetchall() != [("LEGACY_ACTIVE", None)]):
        raise GenesisPreparationRefused("I5 core identity or inert deployment state conflicts")
    expected = i3.genesis_prerequisites(intent)
    for table, (identifier, key) in i3.CATALOG_COLUMNS.items():
        rows = connection.execute(f"SELECT {identifier},{key}" + (",created_at_ns" if table != "idempotency_namespaces" else "") + f" FROM {table}").fetchall()
        if ({str(UUID(bytes=r[0])): r[1] for r in rows} != expected[table]
            or (table != "idempotency_namespaces" and any(r[2] != 0 for r in rows))):
            raise GenesisPreparationRefused("I5 prerequisite catalog differs from frozen I3 allocation")
    operations, objects, relationships = set(), {}, {}
    if profile is not None:
        operations.add((UUID(allocation["root_profile_idempotency_namespace_id"]).bytes, _operation_key(intent, _OWNERS[0])))
        objects[profile.profile_object_id.bytes] = (UUID(allocation["root_profile_identity_namespace_id"]).bytes,
            ROOT_NATIVE_PROFILE_GENERATION_KIND, profile.profile_semantic_scope_id.bytes)
    for plan, record in zip(_publication_plans(intent), records):
        operations.add((UUID(plan["scope_plan"]["idempotency_namespace_id"]).bytes,
            _operation_key(intent, "initial-membership", scope_key=plan["scope_key"])))
        relationships[record.relationship_id.bytes] = (record.membership_identity_namespace_id.bytes,
            ROOT_SCOPE_MEMBERSHIP_KIND, record.semantic_scope_id.bytes)
    seed_result = None
    seed = i4._seed(intent)
    if seed is not None:
        config = i4._configuration(intent, _CommittedLane(intent))
        runtime = NativeCharacterSeedPlantRuntime(connection, configuration=config)
        request = NativeCharacterSeedPlantRequest(seed)
        seed_result = runtime.recover_completed_seed(request)
        if seed_result is None:
            raise GenesisPreparationRefused("I5 requires committed I4 Character completion; planting is forbidden")
        scope = config.routing_scope
        namespace = scope.idempotency_namespace_id.bytes
        source_ids = set()
        for source in seed_result.sources:
            stored = runtime._recover_source(request, seed_result.seed_definition_digest, source.concept_index, source.concept)
            source_ids.add(source.object_id.bytes)
            objects[source.object_id.bytes] = (scope.runtime_scope.identity_namespace_id.bytes,
                "LEGACY_CORE_NODE", scope.runtime_scope.semantic_scope_id.bytes)
            operations.add((namespace, runtime._source_key(seed.seed_id, source.concept_index)))
            operations.add((namespace, runtime._motif_key(seed.seed_id, "DECISION:" + str(source.concept_index))))
            operations.update((namespace, runtime._representation_key(stored, stage)) for stage in ("PENDING", "EXPECTATION", "READY"))
        operations.add((namespace, runtime._motif_key(seed.seed_id, "SEED_BASIN_BOOST")))
        catalog = runtime._motif_reader.list_runtime_motifs(motif_alias_namespace_id=scope.motif_alias_namespace_id,
            domain_id=config.domain_id, semantic_scope_id=scope.runtime_scope.semantic_scope_id)
        members = set()
        for motif in catalog:
            objects[motif.motif_object_id.bytes] = (scope.motif_identity_namespace_id.bytes,
                "DERIVED_MOTIF", scope.runtime_scope.semantic_scope_id.bytes)
            for member in runtime._motifs.list_current_motif_members(motif.motif_object_id):
                if member.member_object_id.bytes not in source_ids or member.member_semantic_scope_id != scope.runtime_scope.semantic_scope_id:
                    raise GenesisPreparationRefused("I5 Character motif contains a foreign source")
                members.add(member.member_object_id.bytes)
        if members != source_ids:
            raise GenesisPreparationRefused("I5 Character motif membership closure is incomplete")
        # I4 motif split/advance operations can retain historical relationships.
        for rid, ns, kind in connection.execute("SELECT relationship_id,identity_namespace_id,relationship_kind FROM relationships"):
            if kind == "MOTIF_MEMBERSHIP" and ns == scope.membership_identity_namespace_id.bytes:
                relationships[rid] = (ns, kind, scope.runtime_scope.semantic_scope_id.bytes)
    if set(connection.execute("SELECT idempotency_namespace_id,idempotency_key FROM operations")) != operations:
        raise GenesisPreparationRefused("I5 native operation closure contains missing or foreign effects")
    for table, identity, kind, expected_rows in (("objects", "object", "object_kind", objects),
                                              ("relationships", "relationship", "relationship_kind", relationships)):
        actual = {row[0]: row[1:] for row in connection.execute(f"SELECT {identity}_id,identity_namespace_id,{kind} FROM {table}")}
        if actual != {key: value[:2] for key, value in expected_rows.items()}:
            raise GenesisPreparationRefused("I5 native object or relationship closure conflicts")
        for identifier, semantic in connection.execute(f"SELECT {identity}_id,effective_semantic_scope_id FROM {identity}_revisions"):
            if identifier not in expected_rows or semantic != expected_rows[identifier][2]:
                raise GenesisPreparationRefused("I5 native revision scope conflicts")
    for table, column in (("object_revisions", "object_revision_id"),
                          ("relationship_revisions", "relationship_revision_id"), ("representations", "representation_id")):
        if connection.execute(f"SELECT 1 FROM {table} r WHERE NOT EXISTS "
            f"(SELECT 1 FROM operation_outputs o WHERE o.{column}=r.{column}) LIMIT 1").fetchone():
            raise GenesisPreparationRefused("I5 native effect has no committed operation output")
    allowed = set(i3.CATALOG_COLUMNS) | {
        "core_metadata", "deployment_metadata", "objects", "provenance_records", "object_revisions",
        "relationships", "relationship_revisions", "relationship_revision_endpoints", "operations", "operation_outputs",
        "semantic_transitions", "object_revision_effects", "relationship_revision_effects", "representation_state_effects",
        "integrity_measurement_effects", "representations", "representation_current_state", "representation_payloads",
        "integrity_expectations", "integrity_measurements", "legacy_object_aliases", "object_revision_governance",
        "memory_runtime_enumeration_orders",
    }
    if seed is None:
        allowed = set(i3.CATALOG_COLUMNS) | {
            "core_metadata", "deployment_metadata", "objects", "object_revisions", "relationships",
            "relationship_revisions", "relationship_revision_endpoints", "operations", "operation_outputs",
            "semantic_transitions", "object_revision_effects", "relationship_revision_effects",
        }
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='view' LIMIT 1").fetchone():
        raise GenesisPreparationRefused("I5 undeclared schema view")
    for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        if table not in allowed and connection.execute('SELECT 1 FROM "' + table.replace('"', '""') + '" LIMIT 1').fetchone():
            raise GenesisPreparationRefused("I5 unexpected native content outside authorized effects")
    if connection.execute("PRAGMA foreign_key_check").fetchone():
        raise GenesisPreparationRefused("I5 native foreign-key integrity conflicts")
    return seed_result


class GenesisMembershipAdministration(i3.GenesisAdministration):
    """An I5-only session; construction does not acquire or prove the OS lock."""
    def __init__(self, root, record, fault=i3._noop):
        super().__init__(root, record, fault)
        self._lease = None

    def _require_active(self):
        super()._require_active()
        if self._lease is not _LIVE_SESSION:
            raise GenesisPreparationRefused("I5 requires a live root-onboarding lock session")

    # Reuse the exact I4 observation protocol and pure checkpoint projection.
    observe_quiescence = i4.GenesisCharacterAdministration.observe_quiescence
    _reference = i4.GenesisCharacterAdministration._reference

    def _require_record(self):
        self._require_active()
        record, _entries = i4._inspect(self.root, self.intent)
        if record != self.record or record.sealed_completion_payload is not None or record.final_activation_references:
            raise GenesisPreparationRefused("I5 requires the unchanged, unsealed PREPARING record")
        expected = [i3.GenesisAdministration._reference(self, "native-core-preparation", i3._bootstrap_manifest(self.intent))]
        for table, rows in i3.genesis_prerequisites(self.intent).items():
            expected.append(i3.GenesisAdministration._reference(self, "native-catalog:" + table, dict(table=table, rows=rows)))
        owners = i4._EXTERNAL_OWNERS + (i4._NATIVE_OWNERS if i4._seed(self.intent) is not None else ())
        seen = set()
        for ref in record.child_operation_references:
            if ref in expected:
                continue
            value = ref.payload()
            owner = value["owner"]
            if owner in seen:
                raise GenesisPreparationRefused("I5 duplicate owner checkpoint")
            seen.add(owner)
            key = self._reference(owner, {}).payload()["operation_key"] if owner in owners else _operation_key(self.intent, owner)
            if owner not in owners + _OWNERS or value["operation_key"] != key:
                raise GenesisPreparationRefused("I5 unsupported child checkpoint")
        if (not all(ref in record.child_operation_references for ref in expected) or not set(owners) <= seen
            or (seen.intersection(_OWNERS) and not set(_OWNERS) <= seen)):
            raise GenesisPreparationRefused("I5 requires complete I3/I4 checkpoints and atomic I5 references")

    def _read(self, issuer):
        self._require_record()
        core = self.root / i3.CORE_DIRECTORY / self.intent.payload()["allocations"]["core_relative_path"]
        with closing(i3._open_readonly(core)) as connection:
            profile = _recover_profile(connection, self.intent)
            records = _recover_members(connection, self.intent, profile, issuer)
            seed = _verify_core(connection, self.intent, profile, records)
        i4.GenesisCharacterAdministration._verify_external(self, seed)
        for ref in i4.GenesisCharacterAdministration._references(self, seed):
            if not self._has_reference(ref):
                raise GenesisPreparationRefused("I5 required I4 committed result checkpoint is absent")
        result = _closure(self.intent, profile, records)
        existing = [r for r in self.record.child_operation_references if r.payload()["owner"] in _OWNERS]
        if existing and (result is None or set(existing) != set(result.child_references)):
            raise GenesisPreparationRefused("I5 checkpoint conflicts with native closure")
        return profile, records, result

    def prepare_initial_memberships(self, *, observer, operator_attestation, issuer_reference):
        self._require_record()
        text(issuer_reference, "operator issuer reference")
        if not self._quiescent:
            raise GenesisPreparationRefused("fresh successful quiescence observation required")
        self._read(issuer_reference)
        value = self.intent.payload()
        allocation = value["allocations"]
        core = self.root / i3.CORE_DIRECTORY / allocation["core_relative_path"]

        def preflight():
            self.observe_quiescence(observer, operator_attestation=operator_attestation, issuer_reference=issuer_reference)
            self._quiescent = False
            return self._read(issuer_reference)

        profile, records, result = preflight()
        if profile is None:
            with open_existing_native_core_connection(core) as opened:
                NativeObjectService(opened.connection).create_object(
                    idempotency_namespace_id=UUID(allocation["root_profile_idempotency_namespace_id"]),
                    idempotency_key=_operation_key(self.intent, _OWNERS[0]), state=_profile_state(self.intent),
                    object_id=UUID(allocation["root_profile_object_id"]))
            self.fault("after-root-profile-commit")
        for index, plan in enumerate(_publication_plans(self.intent)):
            profile, records, result = preflight()
            if index < len(records):
                continue
            if plan["scope_key"]["scope_kind"] == "PRIVATE":
                self.fault("before-private-membership")
            with open_existing_native_core_connection(core) as opened:
                RootScopeMembershipService(opened.connection).admit(profile=profile, runtime_scope=_runtime_scope(plan),
                    witness=_witness(self.intent, profile, plan, issuer_reference),
                    membership_identity_namespace_id=UUID(plan["scope_plan"]["membership_identity_namespace_id"]),
                    idempotency_namespace_id=UUID(plan["scope_plan"]["idempotency_namespace_id"]),
                    idempotency_key=_operation_key(self.intent, "initial-membership", scope_key=plan["scope_key"]))
            self.fault("after-membership-commit:" + str(index))
        _profile, _records, result = preflight()
        if result is None or self._read(issuer_reference)[2] != result:
            raise GenesisPreparationRefused("I5 complete membership closure did not stabilize")
        if not all(self._has_reference(ref) for ref in result.child_references):
            self.fault("before-initial-membership-checkpoint")
            self.replace_record(self.record, replace(self.record, phase_revision=self.record.phase_revision + 1,
                child_operation_references=self.record.child_operation_references + result.child_references))
            self.fault("after-initial-membership-checkpoint")
        if self._read(issuer_reference)[2] != result:
            raise GenesisPreparationRefused("I5 final native closure changed")
        return result


@contextmanager
def begin_genesis_membership_administration(*, data_root: str | Path, intent: GenesisIntent,
                                           timeout_seconds=1.0, fault=i3._noop):
    root = canonical_genesis_root(data_root)
    record, before = i4._inspect(root, intent)
    with i3.root_onboarding_lock(data_root=root, timeout_seconds=timeout_seconds):
        current, after = i4._inspect(root, intent)
        if current != record or after != before:
            raise GenesisPreparationRefused("I5 root changed while acquiring the onboarding lock")
        session = GenesisMembershipAdministration(root, record, fault)
        session._lease = _LIVE_SESSION
        try:
            session._require_record()
            yield session
        finally:
            session._lease = None
            session._active = False
            session._quiescent = False
