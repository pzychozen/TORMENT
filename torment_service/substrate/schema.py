"""Frozen Phase-6 SQLite schema v1 bootstrap and structural startup gate.

This module owns physical schema creation only.  It creates no default database
path and implements no semantic repository, operation, transition, or cutover.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
import time
from typing import Final

from .errors import SubstrateConfigurationError, SubstrateSchemaCompatibilityError
from .ids import generate_native_id, native_id_to_bytes
from .runtime_qualification import qualify_runtime


SCHEMA_ID: Final[str] = "torment.memory.substrate"
SCHEMA_MAJOR: Final[int] = 1
SCHEMA_MINOR: Final[int] = 2
SCHEMA_V1_MAJOR: Final[int] = 1
SCHEMA_V1_MINOR: Final[int] = 0
SCHEMA_V1_1_MAJOR: Final[int] = 1
SCHEMA_V1_1_MINOR: Final[int] = 1
CORE_ROLE_STAGING: Final[str] = "STAGING"
SCHEMA_V1_TO_V1_1_GOVERNANCE_MIGRATION_KEY: Final[str] = (
    "TMS_SCHEMA_V1_TO_V1_1_GOVERNANCE"
)
SCHEMA_V1_1_TO_V1_2_RUNTIME_ORDER_MIGRATION_KEY: Final[str] = (
    "TMS_SCHEMA_V1_1_TO_V1_2_RUNTIME_ORDER"
)

HELPER_OWNED_INVARIANTS: Final[dict[str, str]] = {
    "H1_CURRENT_POINTER_COMPLETE": "Committed carriers require same-carrier current pointers.",
    "H2_TRANSITION_EFFECT_COMPLETE": "Every semantic transition requires typed effects.",
    "H3_REJECTION_XOR_TRANSITION": "An operation cannot resolve to both rejection and transition.",
    "H4_REPRESENTATION_READY_COMPLETE": "READY representation publication needs complete evidence.",
    "H5_IMMUTABLE_AGGREGATE_CLOSED": "Published immutable aggregates cannot be extended or mutated.",
    "H6_RECONCILIATION_CURRENT_COMPLETE": "Reconciliation current selection must publish complete state.",
    "H7_LEGACY_ADMISSION_TYPED": "Imported state publishes only through typed legacy admission.",
    "H8_ALLOCATED_OUTPUT_PUBLICATION_MATCH": "Allocated outputs and backlinks match typed publication.",
}


@dataclass(frozen=True)
class SchemaMetadata:
    core_id: bytes
    core_role: str
    schema_id: str
    schema_major: int
    schema_minor: int


def _statements(script: str) -> tuple[str, ...]:
    statements: list[str] = []
    pending = ""
    for line in script.splitlines():
        pending += line + "\n"
        if sqlite3.complete_statement(pending):
            statement = pending.strip()
            if statement:
                statements.append(statement)
            pending = ""
    if pending.strip():
        raise RuntimeError("schema DDL contains an incomplete statement")
    return tuple(statements)


# This is deliberately SQL rather than an ORM model.  Statements execute one at
# a time inside create_schema's explicit bootstrap transaction.
SCHEMA_V1_DDL: Final[str] = """
CREATE TABLE core_metadata (
 singleton INTEGER PRIMARY KEY CHECK (singleton = 1), schema_id TEXT NOT NULL CHECK (schema_id = 'torment.memory.substrate'), schema_major INTEGER NOT NULL CHECK (schema_major >= 1), schema_minor INTEGER NOT NULL CHECK (schema_minor >= 0), core_id BLOB NOT NULL UNIQUE CHECK (length(core_id) = 16), core_role TEXT NOT NULL CHECK (core_role IN ('STAGING','ACTIVE_CORE','EVIDENCE_ONLY')), created_at_ns INTEGER NOT NULL
) STRICT;
CREATE TABLE deployment_metadata (
 singleton INTEGER PRIMARY KEY CHECK (singleton = 1), deployment_state TEXT NOT NULL CHECK (deployment_state IN ('LEGACY_ACTIVE','CUTOVER_PENDING','NATIVE_ACTIVE')), referenced_core_id BLOB CHECK (referenced_core_id IS NULL OR length(referenced_core_id) = 16), updated_at_ns INTEGER NOT NULL, CHECK ((deployment_state = 'LEGACY_ACTIVE' AND referenced_core_id IS NULL) OR (deployment_state IN ('CUTOVER_PENDING','NATIVE_ACTIVE') AND referenced_core_id IS NOT NULL)), FOREIGN KEY (referenced_core_id) REFERENCES core_metadata(core_id)
) STRICT;
CREATE TABLE maintenance_events (
 maintenance_id BLOB PRIMARY KEY CHECK (length(maintenance_id) = 16), maintenance_kind TEXT NOT NULL CHECK (maintenance_kind IN ('SCHEMA_UPGRADE','CUTOVER','RESTORE','BACKUP')), started_at_ns INTEGER NOT NULL, completed_at_ns INTEGER, detail_json TEXT NOT NULL CHECK (json_valid(detail_json))
) STRICT;
CREATE TABLE schema_migration_ledger (
 migration_key TEXT PRIMARY KEY, from_major INTEGER NOT NULL, from_minor INTEGER NOT NULL, to_major INTEGER NOT NULL, to_minor INTEGER NOT NULL, maintenance_id BLOB NOT NULL CHECK (length(maintenance_id) = 16), applied_at_ns INTEGER NOT NULL, FOREIGN KEY (maintenance_id) REFERENCES maintenance_events(maintenance_id)
) STRICT;
CREATE TABLE identity_namespaces (
 identity_namespace_id BLOB PRIMARY KEY CHECK (length(identity_namespace_id) = 16), namespace_key TEXT NOT NULL UNIQUE, created_at_ns INTEGER NOT NULL
) STRICT;
CREATE TABLE semantic_scopes (
 semantic_scope_id BLOB PRIMARY KEY CHECK (length(semantic_scope_id) = 16), scope_key TEXT NOT NULL UNIQUE, created_at_ns INTEGER NOT NULL
) STRICT;
CREATE TABLE legacy_source_namespaces (
 legacy_source_namespace_id BLOB PRIMARY KEY CHECK (length(legacy_source_namespace_id) = 16), source_key TEXT NOT NULL UNIQUE, created_at_ns INTEGER NOT NULL
) STRICT;
CREATE TABLE objects (
 object_id BLOB PRIMARY KEY CHECK (length(object_id) = 16), identity_namespace_id BLOB NOT NULL CHECK (length(identity_namespace_id) = 16), object_kind TEXT NOT NULL, creating_transition_id BLOB CHECK (creating_transition_id IS NULL OR length(creating_transition_id) = 16), current_revision_id BLOB CHECK (current_revision_id IS NULL OR length(current_revision_id) = 16), current_revision_ordinal INTEGER, created_at_ns INTEGER NOT NULL, UNIQUE (object_id,current_revision_id,current_revision_ordinal), CHECK ((current_revision_id IS NULL) = (current_revision_ordinal IS NULL)), FOREIGN KEY (identity_namespace_id) REFERENCES identity_namespaces(identity_namespace_id), FOREIGN KEY (object_id,current_revision_id,current_revision_ordinal) REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY (creating_transition_id) REFERENCES semantic_transitions(transition_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE provenance_records (
 provenance_id BLOB PRIMARY KEY CHECK (length(provenance_id) = 16), origin_kind TEXT NOT NULL, source_channel TEXT, source_role TEXT, derivation_status TEXT NOT NULL, uncertainty_state TEXT NOT NULL, source_time_ns INTEGER, capture_time_ns INTEGER, memory_role TEXT, descriptive_notes TEXT
) STRICT;
CREATE TABLE object_revisions (
 object_revision_id BLOB PRIMARY KEY CHECK (length(object_revision_id) = 16), object_id BLOB NOT NULL CHECK (length(object_id) = 16), revision_ordinal INTEGER NOT NULL CHECK (revision_ordinal >= 1), lineage_kind TEXT NOT NULL CHECK (lineage_kind IN ('NATIVE_CREATION','NATIVE_ORDINARY','LEGACY_PREDECESSOR_UNKNOWN')), predecessor_revision_id BLOB CHECK (predecessor_revision_id IS NULL OR length(predecessor_revision_id) = 16), predecessor_revision_ordinal INTEGER, effective_semantic_scope_id BLOB NOT NULL CHECK (length(effective_semantic_scope_id) = 16), existence_state TEXT NOT NULL, lifecycle_state TEXT NOT NULL, lifecycle_authoritative INTEGER NOT NULL CHECK (lifecycle_authoritative IN (0,1)), lifecycle_actor TEXT, lifecycle_via TEXT, lifecycle_set_at_ns INTEGER, governance_state TEXT NOT NULL, authority_category TEXT NOT NULL CHECK (authority_category IN ('NOT_APPLICABLE','UNKNOWN','EVIDENCE','INTENT_PROPOSAL','DECISION_RECORD','ACTIVE_AUTHORIZATION','EXECUTION_RECORD')), provenance_id BLOB CHECK (provenance_id IS NULL OR length(provenance_id) = 16), payload_format TEXT NOT NULL CHECK (payload_format IN ('NONE','JSON','TEXT','BLOB')), payload_text TEXT, payload_blob BLOB, created_at_ns INTEGER NOT NULL, UNIQUE (object_id,object_revision_id,revision_ordinal), UNIQUE (object_id,revision_ordinal), CHECK ((lineage_kind = 'NATIVE_CREATION' AND revision_ordinal = 1 AND predecessor_revision_id IS NULL AND predecessor_revision_ordinal IS NULL) OR (lineage_kind = 'NATIVE_ORDINARY' AND revision_ordinal > 1 AND predecessor_revision_id IS NOT NULL AND predecessor_revision_ordinal IS NOT NULL AND revision_ordinal = predecessor_revision_ordinal + 1) OR (lineage_kind = 'LEGACY_PREDECESSOR_UNKNOWN' AND revision_ordinal = 1 AND predecessor_revision_id IS NULL AND predecessor_revision_ordinal IS NULL)), CHECK ((payload_format = 'NONE' AND payload_text IS NULL AND payload_blob IS NULL) OR (payload_format = 'JSON' AND payload_text IS NOT NULL AND payload_blob IS NULL AND json_valid(payload_text)) OR (payload_format = 'TEXT' AND payload_text IS NOT NULL AND payload_blob IS NULL) OR (payload_format = 'BLOB' AND payload_text IS NULL AND payload_blob IS NOT NULL)), FOREIGN KEY (object_id) REFERENCES objects(object_id), FOREIGN KEY (object_id,predecessor_revision_id,predecessor_revision_ordinal) REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY (effective_semantic_scope_id) REFERENCES semantic_scopes(semantic_scope_id), FOREIGN KEY (provenance_id) REFERENCES provenance_records(provenance_id)
) STRICT;
CREATE UNIQUE INDEX object_one_ordinary_successor ON object_revisions(object_id,predecessor_revision_id) WHERE lineage_kind = 'NATIVE_ORDINARY';
CREATE TABLE relationships (
 relationship_id BLOB PRIMARY KEY CHECK (length(relationship_id) = 16), identity_namespace_id BLOB NOT NULL CHECK (length(identity_namespace_id) = 16), relationship_kind TEXT NOT NULL, creating_transition_id BLOB CHECK (creating_transition_id IS NULL OR length(creating_transition_id) = 16), current_revision_id BLOB CHECK (current_revision_id IS NULL OR length(current_revision_id) = 16), current_revision_ordinal INTEGER, created_at_ns INTEGER NOT NULL, UNIQUE (relationship_id,current_revision_id,current_revision_ordinal), CHECK ((current_revision_id IS NULL) = (current_revision_ordinal IS NULL)), FOREIGN KEY (identity_namespace_id) REFERENCES identity_namespaces(identity_namespace_id), FOREIGN KEY (relationship_id,current_revision_id,current_revision_ordinal) REFERENCES relationship_revisions(relationship_id,relationship_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY (creating_transition_id) REFERENCES semantic_transitions(transition_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE relationship_revisions (
 relationship_revision_id BLOB PRIMARY KEY CHECK (length(relationship_revision_id) = 16), relationship_id BLOB NOT NULL CHECK (length(relationship_id) = 16), revision_ordinal INTEGER NOT NULL CHECK (revision_ordinal >= 1), lineage_kind TEXT NOT NULL CHECK (lineage_kind IN ('NATIVE_CREATION','NATIVE_ORDINARY','LEGACY_PREDECESSOR_UNKNOWN')), predecessor_revision_id BLOB CHECK (predecessor_revision_id IS NULL OR length(predecessor_revision_id) = 16), predecessor_revision_ordinal INTEGER, effective_semantic_scope_id BLOB NOT NULL CHECK (length(effective_semantic_scope_id) = 16), existence_state TEXT NOT NULL, lifecycle_state TEXT NOT NULL, lifecycle_authoritative INTEGER NOT NULL CHECK (lifecycle_authoritative IN (0,1)), governance_state TEXT NOT NULL, authority_category TEXT NOT NULL CHECK (authority_category IN ('NOT_APPLICABLE','UNKNOWN','EVIDENCE','INTENT_PROPOSAL','DECISION_RECORD','ACTIVE_AUTHORIZATION','EXECUTION_RECORD')), provenance_id BLOB CHECK (provenance_id IS NULL OR length(provenance_id) = 16), payload_format TEXT NOT NULL CHECK (payload_format IN ('NONE','JSON','TEXT','BLOB')), payload_text TEXT, payload_blob BLOB, created_at_ns INTEGER NOT NULL, UNIQUE (relationship_id,relationship_revision_id,revision_ordinal), UNIQUE (relationship_id,revision_ordinal), CHECK ((lineage_kind = 'NATIVE_CREATION' AND revision_ordinal = 1 AND predecessor_revision_id IS NULL AND predecessor_revision_ordinal IS NULL) OR (lineage_kind = 'NATIVE_ORDINARY' AND revision_ordinal > 1 AND predecessor_revision_id IS NOT NULL AND predecessor_revision_ordinal IS NOT NULL AND revision_ordinal = predecessor_revision_ordinal + 1) OR (lineage_kind = 'LEGACY_PREDECESSOR_UNKNOWN' AND revision_ordinal = 1 AND predecessor_revision_id IS NULL AND predecessor_revision_ordinal IS NULL)), CHECK ((payload_format = 'NONE' AND payload_text IS NULL AND payload_blob IS NULL) OR (payload_format = 'JSON' AND payload_text IS NOT NULL AND payload_blob IS NULL AND json_valid(payload_text)) OR (payload_format = 'TEXT' AND payload_text IS NOT NULL AND payload_blob IS NULL) OR (payload_format = 'BLOB' AND payload_text IS NULL AND payload_blob IS NOT NULL)), FOREIGN KEY (relationship_id) REFERENCES relationships(relationship_id), FOREIGN KEY (relationship_id,predecessor_revision_id,predecessor_revision_ordinal) REFERENCES relationship_revisions(relationship_id,relationship_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY (effective_semantic_scope_id) REFERENCES semantic_scopes(semantic_scope_id), FOREIGN KEY (provenance_id) REFERENCES provenance_records(provenance_id)
) STRICT;
CREATE UNIQUE INDEX relationship_one_ordinary_successor ON relationship_revisions(relationship_id,predecessor_revision_id) WHERE lineage_kind = 'NATIVE_ORDINARY';
CREATE TABLE relationship_revision_endpoints (
 relationship_revision_id BLOB NOT NULL CHECK (length(relationship_revision_id) = 16), endpoint_ordinal INTEGER NOT NULL CHECK (endpoint_ordinal >= 0), endpoint_role TEXT NOT NULL, endpoint_semantic_scope_id BLOB NOT NULL CHECK (length(endpoint_semantic_scope_id) = 16), object_id BLOB NOT NULL CHECK (length(object_id) = 16), binding_mode TEXT NOT NULL CHECK (binding_mode IN ('IDENTITY','EXACT_REVISION')), bound_object_revision_id BLOB CHECK (bound_object_revision_id IS NULL OR length(bound_object_revision_id) = 16), bound_object_revision_ordinal INTEGER, PRIMARY KEY (relationship_revision_id,endpoint_ordinal), CHECK ((binding_mode = 'IDENTITY' AND bound_object_revision_id IS NULL AND bound_object_revision_ordinal IS NULL) OR (binding_mode = 'EXACT_REVISION' AND bound_object_revision_id IS NOT NULL AND bound_object_revision_ordinal IS NOT NULL)), FOREIGN KEY (relationship_revision_id) REFERENCES relationship_revisions(relationship_revision_id), FOREIGN KEY (endpoint_semantic_scope_id) REFERENCES semantic_scopes(semantic_scope_id), FOREIGN KEY (object_id) REFERENCES objects(object_id), FOREIGN KEY (object_id,bound_object_revision_id,bound_object_revision_ordinal) REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE idempotency_namespaces (
 idempotency_namespace_id BLOB PRIMARY KEY CHECK (length(idempotency_namespace_id) = 16), namespace_key TEXT NOT NULL UNIQUE
) STRICT;
CREATE TABLE operations (
 operation_id BLOB PRIMARY KEY CHECK (length(operation_id) = 16), idempotency_namespace_id BLOB NOT NULL CHECK (length(idempotency_namespace_id) = 16), idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) > 0), operation_kind TEXT NOT NULL, intent_contract TEXT NOT NULL CHECK (intent_contract = 'TMS-INTENT-1'), canonical_intent_json TEXT NOT NULL CHECK (json_valid(canonical_intent_json)), created_at_ns INTEGER NOT NULL, UNIQUE (idempotency_namespace_id,idempotency_key), FOREIGN KEY (idempotency_namespace_id) REFERENCES idempotency_namespaces(idempotency_namespace_id)
) STRICT;
CREATE TABLE operation_targets (
 operation_id BLOB NOT NULL CHECK (length(operation_id) = 16), target_ordinal INTEGER NOT NULL CHECK (target_ordinal >= 0), target_role TEXT NOT NULL, target_kind TEXT NOT NULL CHECK (target_kind IN ('OBJECT','RELATIONSHIP')), object_id BLOB, object_revision_id BLOB, object_revision_ordinal INTEGER, relationship_id BLOB, relationship_revision_id BLOB, relationship_revision_ordinal INTEGER, PRIMARY KEY (operation_id,target_ordinal), CHECK ((target_kind = 'OBJECT' AND object_id IS NOT NULL AND relationship_id IS NULL AND relationship_revision_id IS NULL) OR (target_kind = 'RELATIONSHIP' AND relationship_id IS NOT NULL AND object_id IS NULL AND object_revision_id IS NULL)), CHECK ((object_revision_id IS NULL) = (object_revision_ordinal IS NULL)), CHECK ((relationship_revision_id IS NULL) = (relationship_revision_ordinal IS NULL)), FOREIGN KEY (operation_id) REFERENCES operations(operation_id), FOREIGN KEY (object_id) REFERENCES objects(object_id), FOREIGN KEY (object_id,object_revision_id,object_revision_ordinal) REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY (relationship_id) REFERENCES relationships(relationship_id), FOREIGN KEY (relationship_id,relationship_revision_id,relationship_revision_ordinal) REFERENCES relationship_revisions(relationship_id,relationship_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE operation_outputs (
 operation_id BLOB NOT NULL CHECK (length(operation_id) = 16), output_ordinal INTEGER NOT NULL CHECK (output_ordinal >= 0), output_role TEXT NOT NULL, output_kind TEXT NOT NULL CHECK (output_kind IN ('OBJECT','RELATIONSHIP','REPRESENTATION','RECONCILIATION_CASE')), object_id BLOB, object_revision_id BLOB, object_revision_ordinal INTEGER, relationship_id BLOB, relationship_revision_id BLOB, relationship_revision_ordinal INTEGER, representation_id BLOB, reconciliation_case_id BLOB, reconciliation_state_id BLOB, reconciliation_state_ordinal INTEGER, PRIMARY KEY (operation_id,output_ordinal), CHECK ((output_kind = 'OBJECT' AND object_id IS NOT NULL AND relationship_id IS NULL AND representation_id IS NULL AND reconciliation_case_id IS NULL AND reconciliation_state_id IS NULL AND reconciliation_state_ordinal IS NULL) OR (output_kind = 'RELATIONSHIP' AND relationship_id IS NOT NULL AND object_id IS NULL AND representation_id IS NULL AND reconciliation_case_id IS NULL AND reconciliation_state_id IS NULL AND reconciliation_state_ordinal IS NULL) OR (output_kind = 'REPRESENTATION' AND representation_id IS NOT NULL AND object_id IS NULL AND relationship_id IS NULL AND reconciliation_case_id IS NULL AND reconciliation_state_id IS NULL AND reconciliation_state_ordinal IS NULL) OR (output_kind = 'RECONCILIATION_CASE' AND reconciliation_case_id IS NOT NULL AND reconciliation_state_id IS NOT NULL AND reconciliation_state_ordinal IS NOT NULL AND object_id IS NULL AND relationship_id IS NULL AND representation_id IS NULL)), CHECK ((object_revision_id IS NULL) = (object_revision_ordinal IS NULL)), CHECK ((relationship_revision_id IS NULL) = (relationship_revision_ordinal IS NULL)), CHECK ((reconciliation_state_id IS NULL) = (reconciliation_state_ordinal IS NULL)), FOREIGN KEY (operation_id) REFERENCES operations(operation_id), FOREIGN KEY (object_id) REFERENCES objects(object_id), FOREIGN KEY (object_id,object_revision_id,object_revision_ordinal) REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY (relationship_id) REFERENCES relationships(relationship_id), FOREIGN KEY (relationship_id,relationship_revision_id,relationship_revision_ordinal) REFERENCES relationship_revisions(relationship_id,relationship_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY (representation_id) REFERENCES representations(representation_id) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY (reconciliation_case_id,reconciliation_state_id,reconciliation_state_ordinal) REFERENCES reconciliation_case_states(reconciliation_case_id,reconciliation_state_id,state_ordinal) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE operation_rejections (
 operation_id BLOB PRIMARY KEY CHECK (length(operation_id) = 16), rejection_code TEXT NOT NULL, rejection_detail TEXT, rejected_at_ns INTEGER NOT NULL, FOREIGN KEY (operation_id) REFERENCES operations(operation_id)
) STRICT;
CREATE TABLE semantic_transitions (
 transition_id BLOB PRIMARY KEY CHECK (length(transition_id) = 16), operation_id BLOB NOT NULL UNIQUE CHECK (length(operation_id) = 16), transition_kind TEXT NOT NULL, origin_kind TEXT NOT NULL CHECK (origin_kind IN ('NATIVE','LEGACY_ADMISSION')), committed_at_ns INTEGER NOT NULL, FOREIGN KEY (operation_id) REFERENCES operations(operation_id)
) STRICT;
CREATE TABLE object_revision_effects (transition_id BLOB NOT NULL CHECK(length(transition_id)=16), object_id BLOB NOT NULL CHECK(length(object_id)=16), object_revision_id BLOB NOT NULL CHECK(length(object_revision_id)=16), object_revision_ordinal INTEGER NOT NULL, PRIMARY KEY (transition_id,object_id,object_revision_id), FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id), FOREIGN KEY (object_id,object_revision_id,object_revision_ordinal) REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal)) STRICT;
CREATE TABLE relationship_revision_effects (transition_id BLOB NOT NULL CHECK(length(transition_id)=16), relationship_id BLOB NOT NULL CHECK(length(relationship_id)=16), relationship_revision_id BLOB NOT NULL CHECK(length(relationship_revision_id)=16), relationship_revision_ordinal INTEGER NOT NULL, PRIMARY KEY (transition_id,relationship_id,relationship_revision_id), FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id), FOREIGN KEY (relationship_id,relationship_revision_id,relationship_revision_ordinal) REFERENCES relationship_revisions(relationship_id,relationship_revision_id,revision_ordinal)) STRICT;
CREATE TABLE representation_state_effects (transition_id BLOB NOT NULL CHECK(length(transition_id)=16), representation_id BLOB NOT NULL CHECK(length(representation_id)=16), readiness TEXT NOT NULL, operational_disposition TEXT NOT NULL, selected_measurement_id BLOB CHECK(selected_measurement_id IS NULL OR length(selected_measurement_id)=16), PRIMARY KEY (transition_id,representation_id), FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id), FOREIGN KEY (representation_id) REFERENCES representations(representation_id), FOREIGN KEY (selected_measurement_id) REFERENCES integrity_measurements(measurement_id) DEFERRABLE INITIALLY DEFERRED) STRICT;
CREATE TABLE integrity_measurement_effects (transition_id BLOB NOT NULL CHECK(length(transition_id)=16), measurement_id BLOB NOT NULL CHECK(length(measurement_id)=16), PRIMARY KEY (transition_id,measurement_id), FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id), FOREIGN KEY (measurement_id) REFERENCES integrity_measurements(measurement_id)) STRICT;
CREATE TABLE reconciliation_state_effects (transition_id BLOB NOT NULL CHECK(length(transition_id)=16), reconciliation_case_id BLOB NOT NULL CHECK(length(reconciliation_case_id)=16), reconciliation_state_id BLOB NOT NULL CHECK(length(reconciliation_state_id)=16), reconciliation_state_ordinal INTEGER NOT NULL, PRIMARY KEY (transition_id,reconciliation_case_id,reconciliation_state_id), FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id), FOREIGN KEY (reconciliation_case_id,reconciliation_state_id,reconciliation_state_ordinal) REFERENCES reconciliation_case_states(reconciliation_case_id,reconciliation_state_id,state_ordinal)) STRICT;
CREATE TABLE legacy_admission_effects (transition_id BLOB NOT NULL CHECK(length(transition_id)=16), admission_record_id BLOB NOT NULL CHECK(length(admission_record_id)=16), PRIMARY KEY (transition_id,admission_record_id), FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id), FOREIGN KEY (admission_record_id) REFERENCES legacy_admission_records(admission_record_id)) STRICT;
CREATE TABLE representations (
 representation_id BLOB PRIMARY KEY CHECK(length(representation_id)=16), source_kind TEXT NOT NULL CHECK(source_kind IN ('OBJECT_REVISION','RELATIONSHIP_REVISION')), source_object_id BLOB, source_object_revision_id BLOB, source_object_revision_ordinal INTEGER, source_relationship_id BLOB, source_relationship_revision_id BLOB, source_relationship_revision_ordinal INTEGER, representation_class TEXT NOT NULL, generation INTEGER NOT NULL CHECK(generation >= 1), derivation_contract_version TEXT NOT NULL, encoding_id TEXT NOT NULL, dtype TEXT, dimension INTEGER CHECK(dimension IS NULL OR dimension > 0), expected_payload_byte_length INTEGER CHECK(expected_payload_byte_length IS NULL OR expected_payload_byte_length >= 0), created_at_ns INTEGER NOT NULL, CHECK ((source_kind='OBJECT_REVISION' AND source_object_id IS NOT NULL AND source_object_revision_id IS NOT NULL AND source_object_revision_ordinal IS NOT NULL AND source_relationship_id IS NULL AND source_relationship_revision_id IS NULL AND source_relationship_revision_ordinal IS NULL) OR (source_kind='RELATIONSHIP_REVISION' AND source_relationship_id IS NOT NULL AND source_relationship_revision_id IS NOT NULL AND source_relationship_revision_ordinal IS NOT NULL AND source_object_id IS NULL AND source_object_revision_id IS NULL AND source_object_revision_ordinal IS NULL)), FOREIGN KEY(source_object_id,source_object_revision_id,source_object_revision_ordinal) REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY(source_relationship_id,source_relationship_revision_id,source_relationship_revision_ordinal) REFERENCES relationship_revisions(relationship_id,relationship_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE UNIQUE INDEX representation_object_source_generation ON representations(source_object_revision_id,representation_class,generation) WHERE source_kind = 'OBJECT_REVISION';
CREATE UNIQUE INDEX representation_relationship_source_generation ON representations(source_relationship_revision_id,representation_class,generation) WHERE source_kind = 'RELATIONSHIP_REVISION';
CREATE TABLE representation_current_state (representation_id BLOB PRIMARY KEY CHECK(length(representation_id)=16), readiness TEXT NOT NULL CHECK(readiness IN ('PENDING','READY','FAILED','UNKNOWN')), operational_disposition TEXT NOT NULL CHECK(operational_disposition IN ('USABLE','WITHHELD','RECONCILIATION_REQUIRED','QUARANTINED','RETAINED_EVIDENCE')), selected_integrity_measurement_id BLOB CHECK(selected_integrity_measurement_id IS NULL OR length(selected_integrity_measurement_id)=16), FOREIGN KEY(representation_id) REFERENCES representations(representation_id), FOREIGN KEY(selected_integrity_measurement_id) REFERENCES integrity_measurements(measurement_id) DEFERRABLE INITIALLY DEFERRED) STRICT;
CREATE TABLE representation_payloads (representation_id BLOB PRIMARY KEY CHECK(length(representation_id)=16), payload_bytes BLOB NOT NULL, observed_payload_byte_length INTEGER NOT NULL CHECK(observed_payload_byte_length = length(payload_bytes)), stored_at_ns INTEGER NOT NULL, FOREIGN KEY(representation_id) REFERENCES representations(representation_id)) STRICT;
CREATE TABLE representation_dependencies (representation_id BLOB NOT NULL CHECK(length(representation_id)=16), dependency_representation_id BLOB NOT NULL CHECK(length(dependency_representation_id)=16), dependency_role TEXT NOT NULL, PRIMARY KEY(representation_id,dependency_representation_id,dependency_role), CHECK(representation_id != dependency_representation_id), FOREIGN KEY(representation_id) REFERENCES representations(representation_id), FOREIGN KEY(dependency_representation_id) REFERENCES representations(representation_id)) STRICT;
CREATE TABLE integrity_expectations (
 expectation_id BLOB PRIMARY KEY CHECK(length(expectation_id)=16), subject_kind TEXT NOT NULL CHECK(subject_kind IN ('OBJECT_REVISION','RELATIONSHIP_REVISION','REPRESENTATION')), object_id BLOB, object_revision_id BLOB, object_revision_ordinal INTEGER, relationship_id BLOB, relationship_revision_id BLOB, relationship_revision_ordinal INTEGER, representation_id BLOB, algorithm_id TEXT NOT NULL, expected_value BLOB NOT NULL, value_encoding TEXT NOT NULL, established_at_ns INTEGER NOT NULL, CHECK ((subject_kind='OBJECT_REVISION' AND object_id IS NOT NULL AND object_revision_id IS NOT NULL AND object_revision_ordinal IS NOT NULL AND relationship_id IS NULL AND relationship_revision_id IS NULL AND relationship_revision_ordinal IS NULL AND representation_id IS NULL) OR (subject_kind='RELATIONSHIP_REVISION' AND relationship_id IS NOT NULL AND relationship_revision_id IS NOT NULL AND relationship_revision_ordinal IS NOT NULL AND object_id IS NULL AND object_revision_id IS NULL AND object_revision_ordinal IS NULL AND representation_id IS NULL) OR (subject_kind='REPRESENTATION' AND representation_id IS NOT NULL AND object_id IS NULL AND object_revision_id IS NULL AND object_revision_ordinal IS NULL AND relationship_id IS NULL AND relationship_revision_id IS NULL AND relationship_revision_ordinal IS NULL)), FOREIGN KEY(object_id,object_revision_id,object_revision_ordinal) REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY(relationship_id,relationship_revision_id,relationship_revision_ordinal) REFERENCES relationship_revisions(relationship_id,relationship_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY(representation_id) REFERENCES representations(representation_id)
) STRICT;
CREATE TABLE integrity_measurements (measurement_id BLOB PRIMARY KEY CHECK(length(measurement_id)=16), expectation_id BLOB NOT NULL CHECK(length(expectation_id)=16), result TEXT NOT NULL CHECK(result IN ('MATCH','MISMATCH','UNVERIFIABLE','ERROR')), observed_value BLOB, reason TEXT, measured_at_ns INTEGER NOT NULL, FOREIGN KEY(expectation_id) REFERENCES integrity_expectations(expectation_id)) STRICT;
CREATE TABLE reconciliation_cases (
 reconciliation_case_id BLOB PRIMARY KEY CHECK(length(reconciliation_case_id)=16), condition_code TEXT NOT NULL, reason_text TEXT NOT NULL, subject_kind TEXT NOT NULL CHECK(subject_kind IN ('OBJECT_REVISION','RELATIONSHIP_REVISION','REPRESENTATION','CORE','LEGACY_ADMISSION')), object_id BLOB, object_revision_id BLOB, object_revision_ordinal INTEGER, relationship_id BLOB, relationship_revision_id BLOB, relationship_revision_ordinal INTEGER, representation_id BLOB, legacy_admission_record_id BLOB, current_state_id BLOB, current_state_ordinal INTEGER, opened_at_ns INTEGER NOT NULL, UNIQUE(reconciliation_case_id,current_state_id,current_state_ordinal), CHECK((current_state_id IS NULL) = (current_state_ordinal IS NULL)), CHECK ((subject_kind='OBJECT_REVISION' AND object_id IS NOT NULL AND object_revision_id IS NOT NULL AND object_revision_ordinal IS NOT NULL AND relationship_id IS NULL AND relationship_revision_id IS NULL AND relationship_revision_ordinal IS NULL AND representation_id IS NULL AND legacy_admission_record_id IS NULL) OR (subject_kind='RELATIONSHIP_REVISION' AND relationship_id IS NOT NULL AND relationship_revision_id IS NOT NULL AND relationship_revision_ordinal IS NOT NULL AND object_id IS NULL AND object_revision_id IS NULL AND object_revision_ordinal IS NULL AND representation_id IS NULL AND legacy_admission_record_id IS NULL) OR (subject_kind='REPRESENTATION' AND representation_id IS NOT NULL AND object_id IS NULL AND object_revision_id IS NULL AND object_revision_ordinal IS NULL AND relationship_id IS NULL AND relationship_revision_id IS NULL AND relationship_revision_ordinal IS NULL AND legacy_admission_record_id IS NULL) OR (subject_kind='CORE' AND object_id IS NULL AND object_revision_id IS NULL AND object_revision_ordinal IS NULL AND relationship_id IS NULL AND relationship_revision_id IS NULL AND relationship_revision_ordinal IS NULL AND representation_id IS NULL AND legacy_admission_record_id IS NULL) OR (subject_kind='LEGACY_ADMISSION' AND legacy_admission_record_id IS NOT NULL AND object_id IS NULL AND object_revision_id IS NULL AND object_revision_ordinal IS NULL AND relationship_id IS NULL AND relationship_revision_id IS NULL AND relationship_revision_ordinal IS NULL AND representation_id IS NULL)), FOREIGN KEY(object_id,object_revision_id,object_revision_ordinal) REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY(relationship_id,relationship_revision_id,relationship_revision_ordinal) REFERENCES relationship_revisions(relationship_id,relationship_revision_id,revision_ordinal) DEFERRABLE INITIALLY DEFERRED, FOREIGN KEY(representation_id) REFERENCES representations(representation_id), FOREIGN KEY(legacy_admission_record_id) REFERENCES legacy_admission_records(admission_record_id), FOREIGN KEY(reconciliation_case_id,current_state_id,current_state_ordinal) REFERENCES reconciliation_case_states(reconciliation_case_id,reconciliation_state_id,state_ordinal) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE reconciliation_case_states (reconciliation_state_id BLOB PRIMARY KEY CHECK(length(reconciliation_state_id)=16), reconciliation_case_id BLOB NOT NULL CHECK(length(reconciliation_case_id)=16), state_ordinal INTEGER NOT NULL CHECK(state_ordinal >= 1), lineage_kind TEXT NOT NULL CHECK(lineage_kind IN ('NATIVE_CREATION','NATIVE_ORDINARY','LEGACY_PREDECESSOR_UNKNOWN')), predecessor_state_id BLOB CHECK(predecessor_state_id IS NULL OR length(predecessor_state_id)=16), predecessor_state_ordinal INTEGER, operational_disposition TEXT NOT NULL, determination TEXT, resolution_reason TEXT, created_at_ns INTEGER NOT NULL, UNIQUE(reconciliation_case_id,reconciliation_state_id,state_ordinal), UNIQUE(reconciliation_case_id,state_ordinal), CHECK ((lineage_kind IN ('NATIVE_CREATION','LEGACY_PREDECESSOR_UNKNOWN') AND state_ordinal=1 AND predecessor_state_id IS NULL AND predecessor_state_ordinal IS NULL) OR (lineage_kind='NATIVE_ORDINARY' AND state_ordinal>1 AND predecessor_state_id IS NOT NULL AND predecessor_state_ordinal IS NOT NULL AND state_ordinal=predecessor_state_ordinal+1)), FOREIGN KEY(reconciliation_case_id) REFERENCES reconciliation_cases(reconciliation_case_id), FOREIGN KEY(reconciliation_case_id,predecessor_state_id,predecessor_state_ordinal) REFERENCES reconciliation_case_states(reconciliation_case_id,reconciliation_state_id,state_ordinal) DEFERRABLE INITIALLY DEFERRED) STRICT;
CREATE UNIQUE INDEX reconciliation_one_ordinary_successor ON reconciliation_case_states(reconciliation_case_id,predecessor_state_id) WHERE lineage_kind='NATIVE_ORDINARY';
CREATE TABLE provenance_material_sources (provenance_id BLOB NOT NULL CHECK(length(provenance_id)=16), source_ordinal INTEGER NOT NULL CHECK(source_ordinal>=0), source_kind TEXT NOT NULL CHECK(source_kind IN ('REPRESENTATION','LEGACY_ARTIFACT','EXTERNAL_LOCATOR')), representation_id BLOB, legacy_artifact_id BLOB, external_locator TEXT, PRIMARY KEY(provenance_id,source_ordinal), CHECK ((source_kind='REPRESENTATION' AND representation_id IS NOT NULL AND legacy_artifact_id IS NULL AND external_locator IS NULL) OR (source_kind='LEGACY_ARTIFACT' AND legacy_artifact_id IS NOT NULL AND representation_id IS NULL AND external_locator IS NULL) OR (source_kind='EXTERNAL_LOCATOR' AND external_locator IS NOT NULL AND representation_id IS NULL AND legacy_artifact_id IS NULL)), FOREIGN KEY(provenance_id) REFERENCES provenance_records(provenance_id), FOREIGN KEY(representation_id) REFERENCES representations(representation_id), FOREIGN KEY(legacy_artifact_id) REFERENCES legacy_artifacts(legacy_artifact_id)) STRICT;
CREATE TABLE legacy_snapshots (legacy_snapshot_id BLOB PRIMARY KEY CHECK(length(legacy_snapshot_id)=16), legacy_source_namespace_id BLOB NOT NULL CHECK(length(legacy_source_namespace_id)=16), snapshot_identity TEXT NOT NULL UNIQUE, captured_at_ns INTEGER NOT NULL, FOREIGN KEY(legacy_source_namespace_id) REFERENCES legacy_source_namespaces(legacy_source_namespace_id)) STRICT;
CREATE TABLE legacy_artifacts (legacy_artifact_id BLOB PRIMARY KEY CHECK(length(legacy_artifact_id)=16), legacy_snapshot_id BLOB NOT NULL CHECK(length(legacy_snapshot_id)=16), artifact_identity TEXT NOT NULL, artifact_kind TEXT NOT NULL, observed_locator TEXT, digest_algorithm TEXT, digest_value BLOB, retained_bytes BLOB, UNIQUE(legacy_snapshot_id,artifact_identity), FOREIGN KEY(legacy_snapshot_id) REFERENCES legacy_snapshots(legacy_snapshot_id)) STRICT;
CREATE TABLE legacy_artifact_records (legacy_artifact_record_id BLOB PRIMARY KEY CHECK(length(legacy_artifact_record_id)=16), legacy_artifact_id BLOB NOT NULL CHECK(length(legacy_artifact_id)=16), record_identity TEXT NOT NULL, observed_locator TEXT, UNIQUE(legacy_artifact_id,record_identity), FOREIGN KEY(legacy_artifact_id) REFERENCES legacy_artifacts(legacy_artifact_id)) STRICT;
CREATE TABLE legacy_admission_batches (admission_batch_id BLOB PRIMARY KEY CHECK(length(admission_batch_id)=16), legacy_snapshot_id BLOB NOT NULL CHECK(length(legacy_snapshot_id)=16), batch_identity TEXT NOT NULL, opened_at_ns INTEGER NOT NULL, completed_at_ns INTEGER, UNIQUE(legacy_snapshot_id,batch_identity), FOREIGN KEY(legacy_snapshot_id) REFERENCES legacy_snapshots(legacy_snapshot_id)) STRICT;
CREATE TABLE legacy_admission_records (admission_record_id BLOB PRIMARY KEY CHECK(length(admission_record_id)=16), admission_batch_id BLOB NOT NULL CHECK(length(admission_batch_id)=16), legacy_artifact_record_id BLOB NOT NULL CHECK(length(legacy_artifact_record_id)=16), admission_status TEXT NOT NULL CHECK(admission_status IN ('ADMITTED','UNKNOWN','QUARANTINED','NOT_ADMITTED')), unknown_fields_json TEXT CHECK(unknown_fields_json IS NULL OR json_valid(unknown_fields_json)), UNIQUE(admission_batch_id,legacy_artifact_record_id), FOREIGN KEY(admission_batch_id) REFERENCES legacy_admission_batches(admission_batch_id), FOREIGN KEY(legacy_artifact_record_id) REFERENCES legacy_artifact_records(legacy_artifact_record_id)) STRICT;
CREATE TABLE legacy_object_aliases (legacy_source_namespace_id BLOB NOT NULL CHECK(length(legacy_source_namespace_id)=16), alias_kind TEXT NOT NULL, alias_value TEXT NOT NULL, object_id BLOB NOT NULL CHECK(length(object_id)=16), PRIMARY KEY(legacy_source_namespace_id,alias_kind,alias_value), FOREIGN KEY(legacy_source_namespace_id) REFERENCES legacy_source_namespaces(legacy_source_namespace_id), FOREIGN KEY(object_id) REFERENCES objects(object_id)) STRICT;
CREATE TABLE legacy_relationship_aliases (legacy_source_namespace_id BLOB NOT NULL CHECK(length(legacy_source_namespace_id)=16), alias_kind TEXT NOT NULL, alias_value TEXT NOT NULL, relationship_id BLOB NOT NULL CHECK(length(relationship_id)=16), PRIMARY KEY(legacy_source_namespace_id,alias_kind,alias_value), FOREIGN KEY(legacy_source_namespace_id) REFERENCES legacy_source_namespaces(legacy_source_namespace_id), FOREIGN KEY(relationship_id) REFERENCES relationships(relationship_id)) STRICT;
CREATE TABLE legacy_quarantine_records (quarantine_record_id BLOB PRIMARY KEY CHECK(length(quarantine_record_id)=16), admission_record_id BLOB NOT NULL UNIQUE CHECK(length(admission_record_id)=16), condition_code TEXT NOT NULL, reason_text TEXT NOT NULL, retained_legacy_artifact_id BLOB NOT NULL CHECK(length(retained_legacy_artifact_id)=16), reconciliation_case_id BLOB CHECK(reconciliation_case_id IS NULL OR length(reconciliation_case_id)=16), FOREIGN KEY(admission_record_id) REFERENCES legacy_admission_records(admission_record_id), FOREIGN KEY(retained_legacy_artifact_id) REFERENCES legacy_artifacts(legacy_artifact_id), FOREIGN KEY(reconciliation_case_id) REFERENCES reconciliation_cases(reconciliation_case_id)) STRICT;
"""

TRIGGER_DDL: Final[str] = """
CREATE TRIGGER immutable_object_revision_update BEFORE UPDATE ON object_revisions BEGIN SELECT RAISE(ABORT,'immutable object revision'); END;
CREATE TRIGGER immutable_object_revision_delete BEFORE DELETE ON object_revisions BEGIN SELECT RAISE(ABORT,'immutable object revision'); END;
CREATE TRIGGER immutable_relationship_revision_update BEFORE UPDATE ON relationship_revisions BEGIN SELECT RAISE(ABORT,'immutable relationship revision'); END;
CREATE TRIGGER immutable_relationship_revision_delete BEFORE DELETE ON relationship_revisions BEGIN SELECT RAISE(ABORT,'immutable relationship revision'); END;
CREATE TRIGGER immutable_relationship_endpoint_update BEFORE UPDATE ON relationship_revision_endpoints BEGIN SELECT RAISE(ABORT,'immutable relationship endpoint'); END;
CREATE TRIGGER immutable_relationship_endpoint_delete BEFORE DELETE ON relationship_revision_endpoints BEGIN SELECT RAISE(ABORT,'immutable relationship endpoint'); END;
CREATE TRIGGER immutable_provenance_update BEFORE UPDATE ON provenance_records BEGIN SELECT RAISE(ABORT,'immutable provenance'); END;
CREATE TRIGGER immutable_provenance_delete BEFORE DELETE ON provenance_records BEGIN SELECT RAISE(ABORT,'immutable provenance'); END;
CREATE TRIGGER immutable_transition_update BEFORE UPDATE ON semantic_transitions BEGIN SELECT RAISE(ABORT,'immutable transition'); END;
CREATE TRIGGER immutable_transition_delete BEFORE DELETE ON semantic_transitions BEGIN SELECT RAISE(ABORT,'immutable transition'); END;
CREATE TRIGGER immutable_representation_fields BEFORE UPDATE OF source_kind,source_object_id,source_object_revision_id,source_object_revision_ordinal,source_relationship_id,source_relationship_revision_id,source_relationship_revision_ordinal,representation_class,generation,derivation_contract_version,encoding_id,dtype,dimension,expected_payload_byte_length,created_at_ns ON representations BEGIN SELECT RAISE(ABORT,'immutable representation fields'); END;
CREATE TRIGGER immutable_representation_delete BEFORE DELETE ON representations BEGIN SELECT RAISE(ABORT,'immutable representation'); END;
CREATE TRIGGER immutable_payload_update BEFORE UPDATE ON representation_payloads BEGIN SELECT RAISE(ABORT,'immutable representation payload'); END;
CREATE TRIGGER immutable_payload_delete BEFORE DELETE ON representation_payloads BEGIN SELECT RAISE(ABORT,'immutable representation payload'); END;
CREATE TRIGGER immutable_representation_dependency_update BEFORE UPDATE ON representation_dependencies BEGIN SELECT RAISE(ABORT,'immutable representation dependency'); END;
CREATE TRIGGER immutable_representation_dependency_delete BEFORE DELETE ON representation_dependencies BEGIN SELECT RAISE(ABORT,'immutable representation dependency'); END;
CREATE TRIGGER immutable_legacy_artifact_record_update BEFORE UPDATE ON legacy_artifact_records BEGIN SELECT RAISE(ABORT,'immutable legacy artifact record'); END;
CREATE TRIGGER immutable_legacy_artifact_record_delete BEFORE DELETE ON legacy_artifact_records BEGIN SELECT RAISE(ABORT,'immutable legacy artifact record'); END;
CREATE TRIGGER immutable_legacy_admission_record_update BEFORE UPDATE ON legacy_admission_records BEGIN SELECT RAISE(ABORT,'immutable legacy admission record'); END;
CREATE TRIGGER immutable_legacy_admission_record_delete BEFORE DELETE ON legacy_admission_records BEGIN SELECT RAISE(ABORT,'immutable legacy admission record'); END;
CREATE TRIGGER immutable_legacy_admission_effect_update BEFORE UPDATE ON legacy_admission_effects BEGIN SELECT RAISE(ABORT,'immutable legacy admission effect'); END;
CREATE TRIGGER immutable_legacy_admission_effect_delete BEFORE DELETE ON legacy_admission_effects BEGIN SELECT RAISE(ABORT,'immutable legacy admission effect'); END;
CREATE TRIGGER immutable_expectation_update BEFORE UPDATE ON integrity_expectations BEGIN SELECT RAISE(ABORT,'immutable integrity expectation'); END;
CREATE TRIGGER immutable_expectation_delete BEFORE DELETE ON integrity_expectations BEGIN SELECT RAISE(ABORT,'immutable integrity expectation'); END;
CREATE TRIGGER immutable_measurement_update BEFORE UPDATE ON integrity_measurements BEGIN SELECT RAISE(ABORT,'immutable integrity measurement'); END;
CREATE TRIGGER immutable_measurement_delete BEFORE DELETE ON integrity_measurements BEGIN SELECT RAISE(ABORT,'immutable integrity measurement'); END;
CREATE TRIGGER immutable_reconciliation_state_update BEFORE UPDATE ON reconciliation_case_states BEGIN SELECT RAISE(ABORT,'immutable reconciliation state'); END;
CREATE TRIGGER immutable_reconciliation_state_delete BEFORE DELETE ON reconciliation_case_states BEGIN SELECT RAISE(ABORT,'immutable reconciliation state'); END;
"""

SCHEMA_V1_1_DDL: Final[str] = """
CREATE TABLE object_revision_governance (
 object_id BLOB NOT NULL CHECK (length(object_id) = 16),
 object_revision_id BLOB NOT NULL CHECK (length(object_revision_id) = 16),
 object_revision_ordinal INTEGER NOT NULL CHECK (object_revision_ordinal >= 1),
 protected INTEGER NOT NULL CHECK (protected IN (0,1)),
 non_shareable INTEGER NOT NULL CHECK (non_shareable IN (0,1)),
 collective_export_blocked INTEGER NOT NULL CHECK (collective_export_blocked IN (0,1)),
 collective_reingest_blocked INTEGER NOT NULL CHECK (collective_reingest_blocked IN (0,1)),
 decay_accelerated INTEGER NOT NULL CHECK (decay_accelerated IN (0,1)),
 PRIMARY KEY (object_id,object_revision_id,object_revision_ordinal),
 FOREIGN KEY (object_id,object_revision_id,object_revision_ordinal)
   REFERENCES object_revisions(object_id,object_revision_id,revision_ordinal)
) STRICT;
"""

SCHEMA_V1_1_TRIGGER_DDL: Final[str] = """
CREATE TRIGGER immutable_object_revision_governance_update BEFORE UPDATE ON object_revision_governance BEGIN SELECT RAISE(ABORT,'immutable object revision governance'); END;
CREATE TRIGGER immutable_object_revision_governance_delete BEFORE DELETE ON object_revision_governance BEGIN SELECT RAISE(ABORT,'immutable object revision governance'); END;
"""

# A3D5: compatibility structure only.  This is deliberately separate from
# memory payload, revision ordinals, EID aliases, and governance.  It records
# the first-appearance enumeration position required by the legacy source.
SCHEMA_V1_2_DDL: Final[str] = """
CREATE TABLE memory_runtime_enumeration_orders (
 legacy_source_namespace_id BLOB NOT NULL CHECK (length(legacy_source_namespace_id) = 16),
 object_id BLOB NOT NULL CHECK (length(object_id) = 16),
 runtime_ordinal INTEGER NOT NULL CHECK (runtime_ordinal >= 0),
 PRIMARY KEY (legacy_source_namespace_id,object_id),
 UNIQUE (legacy_source_namespace_id,runtime_ordinal),
 FOREIGN KEY (legacy_source_namespace_id) REFERENCES legacy_source_namespaces(legacy_source_namespace_id),
 FOREIGN KEY (object_id) REFERENCES objects(object_id)
) STRICT;
"""

SCHEMA_V1_2_TRIGGER_DDL: Final[str] = """
CREATE TRIGGER immutable_memory_runtime_enumeration_order_update BEFORE UPDATE ON memory_runtime_enumeration_orders BEGIN SELECT RAISE(ABORT,'immutable memory runtime enumeration order'); END;
CREATE TRIGGER immutable_memory_runtime_enumeration_order_delete BEFORE DELETE ON memory_runtime_enumeration_orders BEGIN SELECT RAISE(ABORT,'immutable memory runtime enumeration order'); END;
"""

EXPECTED_TABLES_V1: Final[frozenset[str]] = frozenset(
    statement.split()[2]
    for statement in _statements(SCHEMA_V1_DDL)
    if statement.startswith("CREATE TABLE")
)
EXPECTED_INDEXES_V1: Final[frozenset[str]] = frozenset(
    statement.split()[3]
    for statement in _statements(SCHEMA_V1_DDL)
    if statement.startswith("CREATE UNIQUE INDEX")
)
EXPECTED_TRIGGERS_V1: Final[frozenset[str]] = frozenset(
    statement.split()[2]
    for statement in _statements(TRIGGER_DDL)
    if statement.startswith("CREATE TRIGGER")
)
EXPECTED_TABLES_V1_1: Final[frozenset[str]] = EXPECTED_TABLES_V1 | frozenset(
    statement.split()[2]
    for statement in _statements(SCHEMA_V1_1_DDL)
    if statement.startswith("CREATE TABLE")
)
EXPECTED_INDEXES_V1_1: Final[frozenset[str]] = EXPECTED_INDEXES_V1
EXPECTED_TRIGGERS_V1_1: Final[frozenset[str]] = EXPECTED_TRIGGERS_V1 | frozenset(
    statement.split()[2]
    for statement in _statements(SCHEMA_V1_1_TRIGGER_DDL)
    if statement.startswith("CREATE TRIGGER")
)
EXPECTED_TABLES: Final[frozenset[str]] = EXPECTED_TABLES_V1_1 | frozenset(
    statement.split()[2]
    for statement in _statements(SCHEMA_V1_2_DDL)
    if statement.startswith("CREATE TABLE")
)
EXPECTED_INDEXES: Final[frozenset[str]] = EXPECTED_INDEXES_V1_1
EXPECTED_TRIGGERS: Final[frozenset[str]] = EXPECTED_TRIGGERS_V1_1 | frozenset(
    statement.split()[2]
    for statement in _statements(SCHEMA_V1_2_TRIGGER_DDL)
    if statement.startswith("CREATE TRIGGER")
)
_SCHEMA_V1_VERSION: Final[tuple[int, int]] = (SCHEMA_V1_MAJOR, SCHEMA_V1_MINOR)
_SCHEMA_V1_1_VERSION: Final[tuple[int, int]] = (SCHEMA_V1_1_MAJOR, SCHEMA_V1_1_MINOR)
_CURRENT_SCHEMA_VERSION: Final[tuple[int, int]] = (SCHEMA_MAJOR, SCHEMA_MINOR)
_V1_TO_V1_1_MAINTENANCE_DETAIL: Final[str] = json.dumps(
    {
        "from": {"major": SCHEMA_V1_MAJOR, "minor": SCHEMA_V1_MINOR},
        "migration_key": SCHEMA_V1_TO_V1_1_GOVERNANCE_MIGRATION_KEY,
        "to": {"major": SCHEMA_V1_1_MAJOR, "minor": SCHEMA_V1_1_MINOR},
    },
    separators=(",", ":"),
    sort_keys=True,
)
_V1_1_TO_V1_2_MAINTENANCE_DETAIL: Final[str] = json.dumps(
    {
        "from": {"major": SCHEMA_V1_1_MAJOR, "minor": SCHEMA_V1_1_MINOR},
        "migration_key": SCHEMA_V1_1_TO_V1_2_RUNTIME_ORDER_MIGRATION_KEY,
        "to": {"major": SCHEMA_MAJOR, "minor": SCHEMA_MINOR},
    },
    separators=(",", ":"),
    sort_keys=True,
)


def create_schema(connection: sqlite3.Connection) -> SchemaMetadata:
    """Create the current v1.2 schema, never upgrading an existing core."""
    return _create_schema(connection, target_version=_CURRENT_SCHEMA_VERSION)


def create_schema_v1(connection: sqlite3.Connection) -> SchemaMetadata:
    """Create historical v1.0 only for explicit evolution qualification."""
    return _create_schema(connection, target_version=_SCHEMA_V1_VERSION)


def create_schema_v1_1(connection: sqlite3.Connection) -> SchemaMetadata:
    """Create historical v1.1 only for explicit v1.2 evolution qualification."""
    return _create_schema(connection, target_version=_SCHEMA_V1_1_VERSION)


def _create_schema(connection: sqlite3.Connection, *, target_version: tuple[int, int]) -> SchemaMetadata:
    if target_version not in {_SCHEMA_V1_VERSION, _SCHEMA_V1_1_VERSION, _CURRENT_SCHEMA_VERSION}:
        raise ValueError("target schema version is unsupported")
    _require_qualified_connection(connection)
    existing = _user_tables(connection)
    if existing:
        if "core_metadata" not in existing:
            raise SubstrateSchemaCompatibilityError("native schema is incomplete or unknown")
        metadata = validate_schema(connection)
        if (metadata.schema_major, metadata.schema_minor) != target_version:
            raise SubstrateSchemaCompatibilityError(
                "schema bootstrap requires an explicit versioned schema upgrade"
            )
        return metadata

    core_id = native_id_to_bytes(generate_native_id())
    now_ns = time.time_ns()
    connection.execute("BEGIN IMMEDIATE")
    try:
        _execute_statements(connection, SCHEMA_V1_DDL)
        _execute_statements(connection, TRIGGER_DDL)
        if target_version in {_SCHEMA_V1_1_VERSION, _CURRENT_SCHEMA_VERSION}:
            _execute_statements(connection, SCHEMA_V1_1_DDL)
            _execute_statements(connection, SCHEMA_V1_1_TRIGGER_DDL)
        if target_version == _CURRENT_SCHEMA_VERSION:
            _execute_statements(connection, SCHEMA_V1_2_DDL)
            _execute_statements(connection, SCHEMA_V1_2_TRIGGER_DDL)
        version = target_version
        connection.execute(
            "INSERT INTO core_metadata VALUES (1,?,?,?,?,?,?)",
            (SCHEMA_ID, version[0], version[1], core_id, CORE_ROLE_STAGING, now_ns),
        )
        connection.execute(
            "INSERT INTO deployment_metadata VALUES (1,'LEGACY_ACTIVE',NULL,?)", (now_ns,)
        )
        metadata = _validate_schema(connection)
        connection.execute("COMMIT")
        return metadata
    except Exception:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise


def open_schema(connection: sqlite3.Connection, *, writable: bool = True) -> SchemaMetadata:
    """Open a validated core, refusing writes against older supported versions."""
    _require_qualified_connection(connection)
    metadata = _validate_schema(connection)
    if writable and (metadata.schema_major, metadata.schema_minor) != _CURRENT_SCHEMA_VERSION:
        raise SubstrateSchemaCompatibilityError(
            "older schema is read-only; explicit schema upgrade is required for writes"
        )
    return metadata


def validate_schema(connection: sqlite3.Connection) -> SchemaMetadata:
    """Validate required structural health without modifying schema or metadata."""
    _require_qualified_connection(connection)
    return _validate_schema(connection)


def require_current_schema(connection: sqlite3.Connection) -> SchemaMetadata:
    """Require v1.2 for APIs that need revision-bound runtime order facts."""
    metadata = open_schema(connection)
    if (metadata.schema_major, metadata.schema_minor) != _CURRENT_SCHEMA_VERSION:
        raise SubstrateSchemaCompatibilityError(
            "runtime enumeration order requires explicit v1.2 schema upgrade"
        )
    return metadata


def upgrade_schema_v1_to_v1_1(connection: sqlite3.Connection) -> SchemaMetadata:
    """Explicitly and atomically evolve one exact v1.0 core to v1.1.

    This is intentionally a single named upgrade, not an automatic or generic
    migration mechanism. An already-current compatible core is returned without
    recording another maintenance or ledger row.
    """
    _require_qualified_connection(connection)
    metadata = _validate_schema(connection)
    version = (metadata.schema_major, metadata.schema_minor)
    if version in {_SCHEMA_V1_1_VERSION, _CURRENT_SCHEMA_VERSION}:
        return metadata
    if version != _SCHEMA_V1_VERSION:
        raise SubstrateSchemaCompatibilityError("schema is not an exact v1.0 upgrade source")

    maintenance_id = native_id_to_bytes(generate_native_id())
    now_ns = time.time_ns()
    connection.execute("BEGIN IMMEDIATE")
    try:
        _execute_statements(connection, SCHEMA_V1_1_DDL)
        _execute_statements(connection, SCHEMA_V1_1_TRIGGER_DDL)
        _validate_governance_structure(connection)
        connection.execute(
            "INSERT INTO maintenance_events VALUES (?, 'SCHEMA_UPGRADE', ?, ?, ?)",
            (maintenance_id, now_ns, now_ns, _V1_TO_V1_1_MAINTENANCE_DETAIL),
        )
        connection.execute(
            "INSERT INTO schema_migration_ledger VALUES (?,?,?,?,?,?,?)",
            (
                SCHEMA_V1_TO_V1_1_GOVERNANCE_MIGRATION_KEY,
                SCHEMA_V1_MAJOR,
                SCHEMA_V1_MINOR,
                SCHEMA_V1_1_MAJOR,
                SCHEMA_V1_1_MINOR,
                maintenance_id,
                now_ns,
            ),
        )
        _before_upgrade_metadata_write(connection)
        connection.execute(
            "UPDATE core_metadata SET schema_major=?,schema_minor=? WHERE singleton=1",
            (SCHEMA_V1_1_MAJOR, SCHEMA_V1_1_MINOR),
        )
        metadata = _validate_schema(connection)
        connection.execute("COMMIT")
        return metadata
    except Exception:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise


def upgrade_schema_v1_1_to_v1_2(connection: sqlite3.Connection) -> SchemaMetadata:
    """Explicitly and atomically evolve one exact v1.1 core to v1.2."""
    _require_qualified_connection(connection)
    metadata = _validate_schema(connection)
    version = (metadata.schema_major, metadata.schema_minor)
    if version == _CURRENT_SCHEMA_VERSION:
        return metadata
    if version != _SCHEMA_V1_1_VERSION:
        raise SubstrateSchemaCompatibilityError("schema is not an exact v1.1 upgrade source")

    maintenance_id = native_id_to_bytes(generate_native_id())
    now_ns = time.time_ns()
    connection.execute("BEGIN IMMEDIATE")
    try:
        _execute_statements(connection, SCHEMA_V1_2_DDL)
        _execute_statements(connection, SCHEMA_V1_2_TRIGGER_DDL)
        _validate_runtime_order_structure(connection)
        connection.execute(
            "INSERT INTO maintenance_events VALUES (?, 'SCHEMA_UPGRADE', ?, ?, ?)",
            (maintenance_id, now_ns, now_ns, _V1_1_TO_V1_2_MAINTENANCE_DETAIL),
        )
        connection.execute(
            "INSERT INTO schema_migration_ledger VALUES (?,?,?,?,?,?,?)",
            (
                SCHEMA_V1_1_TO_V1_2_RUNTIME_ORDER_MIGRATION_KEY,
                SCHEMA_V1_1_MAJOR,
                SCHEMA_V1_1_MINOR,
                SCHEMA_MAJOR,
                SCHEMA_MINOR,
                maintenance_id,
                now_ns,
            ),
        )
        _before_v1_1_to_v1_2_metadata_write(connection)
        connection.execute(
            "UPDATE core_metadata SET schema_major=?,schema_minor=? WHERE singleton=1",
            (SCHEMA_MAJOR, SCHEMA_MINOR),
        )
        metadata = _validate_schema(connection)
        connection.execute("COMMIT")
        return metadata
    except Exception:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise


def _before_upgrade_metadata_write(connection: sqlite3.Connection) -> None:
    """Narrow test seam for forced-failure rollback qualification."""
    del connection


def _before_v1_1_to_v1_2_metadata_write(connection: sqlite3.Connection) -> None:
    """Narrow test seam for forced v1.2-upgrade rollback qualification."""
    del connection


def _require_qualified_connection(connection: sqlite3.Connection) -> None:
    if not isinstance(connection, sqlite3.Connection):
        raise SubstrateConfigurationError("a qualified sqlite connection is required")
    if connection.in_transaction:
        raise SubstrateConfigurationError("schema gate must run before a transaction begins")
    qualify_runtime()
    try:
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
    except sqlite3.Error as exc:
        raise SubstrateConfigurationError("foreign-key verification failed") from exc
    if foreign_keys != 1:
        raise SubstrateConfigurationError("foreign keys must be enabled before schema bootstrap")


def _validate_schema(connection: sqlite3.Connection) -> SchemaMetadata:
    tables = _user_tables(connection)
    if "core_metadata" not in tables:
        raise SubstrateSchemaCompatibilityError("native schema is incomplete or unknown")
    rows = connection.execute(
        "SELECT core_id,core_role,schema_id,schema_major,schema_minor FROM core_metadata"
    ).fetchall()
    if len(rows) != 1:
        raise SubstrateSchemaCompatibilityError("native core metadata is not singleton")
    core_id, role, schema_id, major, minor = rows[0]
    if (
        not isinstance(core_id, bytes)
        or len(core_id) != 16
        or role not in {"STAGING", "ACTIVE_CORE", "EVIDENCE_ONLY"}
        or schema_id != SCHEMA_ID
    ):
        raise SubstrateSchemaCompatibilityError("native core metadata is incompatible")
    expected_tables, expected_indexes, expected_triggers = _schema_expectations(major, minor)
    if tables != expected_tables:
        raise SubstrateSchemaCompatibilityError("required native tables do not match declared schema version")
    indexes = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")
        if not row[0].startswith("sqlite_")
    }
    triggers = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    if indexes != expected_indexes or triggers != expected_triggers:
        raise SubstrateSchemaCompatibilityError("native indexes or triggers do not exactly match declared schema version")
    table_rows = {row[1]: row[5] for row in connection.execute("PRAGMA table_list")}
    if any(table_rows.get(name) != 1 for name in expected_tables):
        raise SubstrateSchemaCompatibilityError("all native schema tables must be STRICT")
    if (major, minor) in {_SCHEMA_V1_1_VERSION, _CURRENT_SCHEMA_VERSION}:
        _validate_governance_structure(connection)
    if (major, minor) == _CURRENT_SCHEMA_VERSION:
        _validate_runtime_order_structure(connection)
    _validate_migration_ledger(connection, major, minor)
    if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise SubstrateSchemaCompatibilityError("foreign-key structural health check failed")
    integrity = connection.execute("PRAGMA integrity_check").fetchone()
    if integrity != ("ok",):
        raise SubstrateSchemaCompatibilityError("SQLite integrity check failed")
    return SchemaMetadata(core_id, role, schema_id, major, minor)


def _schema_expectations(
    major: object, minor: object
) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    version = (major, minor)
    if version == _SCHEMA_V1_VERSION:
        return EXPECTED_TABLES_V1, EXPECTED_INDEXES_V1, EXPECTED_TRIGGERS_V1
    if version == _SCHEMA_V1_1_VERSION:
        return EXPECTED_TABLES_V1_1, EXPECTED_INDEXES_V1_1, EXPECTED_TRIGGERS_V1_1
    if version == _CURRENT_SCHEMA_VERSION:
        return EXPECTED_TABLES, EXPECTED_INDEXES, EXPECTED_TRIGGERS
    raise SubstrateSchemaCompatibilityError("native core schema version is unsupported")


def _validate_governance_structure(connection: sqlite3.Connection) -> None:
    expected_columns = (
        ("object_id", "BLOB", 1, 1),
        ("object_revision_id", "BLOB", 1, 2),
        ("object_revision_ordinal", "INTEGER", 1, 3),
        ("protected", "INTEGER", 1, 0),
        ("non_shareable", "INTEGER", 1, 0),
        ("collective_export_blocked", "INTEGER", 1, 0),
        ("collective_reingest_blocked", "INTEGER", 1, 0),
        ("decay_accelerated", "INTEGER", 1, 0),
    )
    actual_columns = tuple(
        (row[1], row[2].upper(), row[3], row[5])
        for row in connection.execute("PRAGMA table_info(object_revision_governance)")
    )
    if actual_columns != expected_columns:
        raise SubstrateSchemaCompatibilityError("revision governance columns are incompatible")
    foreign_keys = tuple(
        (row[2], row[3], row[4])
        for row in sorted(
            connection.execute("PRAGMA foreign_key_list(object_revision_governance)").fetchall(),
            key=lambda row: (row[0], row[1]),
        )
    )
    if foreign_keys != (
        ("object_revisions", "object_id", "object_id"),
        ("object_revisions", "object_revision_id", "object_revision_id"),
        ("object_revisions", "object_revision_ordinal", "revision_ordinal"),
    ):
        raise SubstrateSchemaCompatibilityError("revision governance foreign key is incompatible")
    indexes = tuple(
        (row[2], row[3], row[4])
        for row in connection.execute("PRAGMA index_list(object_revision_governance)")
    )
    if indexes != ((1, "pk", 0),):
        raise SubstrateSchemaCompatibilityError("revision governance key structure is incompatible")
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='object_revision_governance'"
    ).fetchone()
    normalized = "" if row is None or row[0] is None else "".join(row[0].split())
    if any(
        f"CHECK({name}IN(0,1))" not in normalized
        for name in (
            "protected",
            "non_shareable",
            "collective_export_blocked",
            "collective_reingest_blocked",
            "decay_accelerated",
        )
    ):
        raise SubstrateSchemaCompatibilityError("revision governance booleans are not constrained")
    expected_triggers = {
        statement.split()[2]: _normalize_schema_sql(statement)
        for statement in _statements(SCHEMA_V1_1_TRIGGER_DDL)
    }
    actual_triggers = {
        name: _normalize_schema_sql(sql)
        for name, sql in connection.execute(
            "SELECT name,sql FROM sqlite_master WHERE type='trigger' "
            "AND tbl_name='object_revision_governance'"
        )
    }
    if actual_triggers != expected_triggers:
        raise SubstrateSchemaCompatibilityError("revision governance immutability triggers are incompatible")


def _validate_runtime_order_structure(connection: sqlite3.Connection) -> None:
    expected_columns = (
        ("legacy_source_namespace_id", "BLOB", 1, 1),
        ("object_id", "BLOB", 1, 2),
        ("runtime_ordinal", "INTEGER", 1, 0),
    )
    actual_columns = tuple(
        (row[1], row[2].upper(), row[3], row[5])
        for row in connection.execute("PRAGMA table_info(memory_runtime_enumeration_orders)")
    )
    if actual_columns != expected_columns:
        raise SubstrateSchemaCompatibilityError("runtime enumeration order columns are incompatible")
    foreign_keys = frozenset(
        (row[2], row[3], row[4])
        for row in connection.execute(
            "PRAGMA foreign_key_list(memory_runtime_enumeration_orders)"
        )
    )
    if foreign_keys != {
        ("legacy_source_namespaces", "legacy_source_namespace_id", "legacy_source_namespace_id"),
        ("objects", "object_id", "object_id"),
    }:
        raise SubstrateSchemaCompatibilityError("runtime enumeration order foreign keys are incompatible")
    indexes = frozenset(
        (row[2], row[3], row[4])
        for row in connection.execute("PRAGMA index_list(memory_runtime_enumeration_orders)")
    )
    if indexes != {(1, "pk", 0), (1, "u", 0)}:
        raise SubstrateSchemaCompatibilityError("runtime enumeration order key structure is incompatible")
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='memory_runtime_enumeration_orders'"
    ).fetchone()
    normalized = "" if row is None or row[0] is None else "".join(row[0].split())
    if "CHECK(runtime_ordinal>=0)" not in normalized:
        raise SubstrateSchemaCompatibilityError("runtime enumeration ordinal is not non-negative")
    expected_triggers = {
        statement.split()[2]: _normalize_schema_sql(statement)
        for statement in _statements(SCHEMA_V1_2_TRIGGER_DDL)
    }
    actual_triggers = {
        name: _normalize_schema_sql(sql)
        for name, sql in connection.execute(
            "SELECT name,sql FROM sqlite_master WHERE type='trigger' "
            "AND tbl_name='memory_runtime_enumeration_orders'"
        )
    }
    if actual_triggers != expected_triggers:
        raise SubstrateSchemaCompatibilityError("runtime enumeration order immutability triggers are incompatible")


def _validate_migration_ledger(connection: sqlite3.Connection, major: object, minor: object) -> None:
    rows = connection.execute(
        "SELECT migration_key,from_major,from_minor,to_major,to_minor,maintenance_id "
        "FROM schema_migration_ledger"
    ).fetchall()
    if (major, minor) == _SCHEMA_V1_VERSION:
        if rows:
            raise SubstrateSchemaCompatibilityError("schema v1 cannot carry an upgrade ledger entry")
        return
    v1_to_v1_1 = (
        SCHEMA_V1_TO_V1_1_GOVERNANCE_MIGRATION_KEY,
        SCHEMA_V1_MAJOR,
        SCHEMA_V1_MINOR,
        SCHEMA_V1_1_MAJOR,
        SCHEMA_V1_1_MINOR,
    )
    v1_1_to_v1_2 = (
        SCHEMA_V1_1_TO_V1_2_RUNTIME_ORDER_MIGRATION_KEY,
        SCHEMA_V1_1_MAJOR,
        SCHEMA_V1_1_MINOR,
        SCHEMA_MAJOR,
        SCHEMA_MINOR,
    )
    version = (major, minor)
    if version == _SCHEMA_V1_1_VERSION:
        if not rows:
            return  # Fresh v1.1 bootstrap has no historical upgrade to record.
        if len(rows) != 1 or rows[0][:5] != v1_to_v1_1:
            raise SubstrateSchemaCompatibilityError("schema v1.1 migration ledger entry is incompatible")
        _validate_migration_maintenance(connection, rows[0][5], _V1_TO_V1_1_MAINTENANCE_DETAIL)
        return
    if version != _CURRENT_SCHEMA_VERSION:
        raise SubstrateSchemaCompatibilityError("schema migration ledger version is unsupported")
    if not rows:
        return  # Fresh v1.2 bootstrap has no historical upgrade to record.
    expected_rows = (v1_1_to_v1_2,) if len(rows) == 1 else (v1_to_v1_1, v1_1_to_v1_2)
    rows_by_key = {row[0]: row for row in rows}
    if len(rows) != len(expected_rows) or set(rows_by_key) != {row[0] for row in expected_rows}:
        raise SubstrateSchemaCompatibilityError("schema v1.2 migration ledger entries are incompatible")
    for expected, detail in zip(
        expected_rows,
        (_V1_TO_V1_1_MAINTENANCE_DETAIL, _V1_1_TO_V1_2_MAINTENANCE_DETAIL)[-len(rows):],
    ):
        row = rows_by_key[expected[0]]
        if row[:5] != expected:
            raise SubstrateSchemaCompatibilityError("schema v1.2 migration ledger entries are incompatible")
        _validate_migration_maintenance(connection, row[5], detail)


def _validate_migration_maintenance(
    connection: sqlite3.Connection, maintenance_id: bytes, expected_detail: str,
) -> None:
    maintenance = connection.execute(
        "SELECT maintenance_kind,completed_at_ns,detail_json FROM maintenance_events WHERE maintenance_id=?",
        (maintenance_id,),
    ).fetchone()
    if (
        maintenance is None
        or maintenance[0] != "SCHEMA_UPGRADE"
        or maintenance[1] is None
        or maintenance[2] != expected_detail
    ):
        raise SubstrateSchemaCompatibilityError("schema migration maintenance evidence is incomplete")


def _user_tables(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


def _normalize_schema_sql(value: str | None) -> str:
    return "" if value is None else "".join(value.split()).rstrip(";")


def _execute_statements(connection: sqlite3.Connection, script: str) -> None:
    for statement in _statements(script):
        connection.execute(statement)
