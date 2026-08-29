"""Frozen Phase-6 SQLite schema v1 bootstrap and structural startup gate.

This module owns physical schema creation only.  It creates no default database
path and implements no semantic repository, operation, transition, or cutover.
"""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
import time
from typing import Final

from .errors import SubstrateConfigurationError, SubstrateSchemaCompatibilityError
from .ids import generate_native_id, native_id_to_bytes
from .runtime_qualification import qualify_runtime


SCHEMA_ID: Final[str] = "torment.memory.substrate"
SCHEMA_MAJOR: Final[int] = 1
SCHEMA_MINOR: Final[int] = 0
CORE_ROLE_STAGING: Final[str] = "STAGING"

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

EXPECTED_TABLES: Final[frozenset[str]] = frozenset(
    statement.split()[2]
    for statement in _statements(SCHEMA_V1_DDL)
    if statement.startswith("CREATE TABLE")
)
EXPECTED_INDEXES: Final[frozenset[str]] = frozenset(
    statement.split()[3]
    for statement in _statements(SCHEMA_V1_DDL)
    if statement.startswith("CREATE UNIQUE INDEX")
)
EXPECTED_TRIGGERS: Final[frozenset[str]] = frozenset(
    statement.split()[2]
    for statement in _statements(TRIGGER_DDL)
    if statement.startswith("CREATE TRIGGER")
)


def create_schema(connection: sqlite3.Connection) -> SchemaMetadata:
    """Create v1 atomically, or validate an already-compatible native schema."""
    _require_qualified_connection(connection)
    existing = _user_tables(connection)
    if existing:
        if "core_metadata" not in existing:
            raise SubstrateSchemaCompatibilityError("native schema is incomplete or unknown")
        return validate_schema(connection)

    core_id = native_id_to_bytes(generate_native_id())
    now_ns = time.time_ns()
    connection.execute("BEGIN IMMEDIATE")
    try:
        _execute_statements(connection, SCHEMA_V1_DDL)
        _execute_statements(connection, TRIGGER_DDL)
        connection.execute(
            "INSERT INTO core_metadata VALUES (1,?,?,?,?,?,?)",
            (SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR, core_id, CORE_ROLE_STAGING, now_ns),
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
    """Open only exactly-compatible v1 metadata; this slice never migrates."""
    del writable  # Compatibility is exact; unknown, newer, and older schemas all refuse.
    _require_qualified_connection(connection)
    return _validate_schema(connection)


def validate_schema(connection: sqlite3.Connection) -> SchemaMetadata:
    """Validate required structural health without modifying schema or metadata."""
    _require_qualified_connection(connection)
    return _validate_schema(connection)


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
    if _user_tables(connection) != EXPECTED_TABLES:
        raise SubstrateSchemaCompatibilityError("required native tables do not match schema v1")
    indexes = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    triggers = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    if not EXPECTED_INDEXES.issubset(indexes) or not EXPECTED_TRIGGERS.issubset(triggers):
        raise SubstrateSchemaCompatibilityError("required native indexes or triggers are missing")
    table_rows = {row[1]: row[5] for row in connection.execute("PRAGMA table_list")}
    if any(table_rows.get(name) != 1 for name in EXPECTED_TABLES):
        raise SubstrateSchemaCompatibilityError("all native schema tables must be STRICT")
    if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise SubstrateSchemaCompatibilityError("foreign-key structural health check failed")
    integrity = connection.execute("PRAGMA integrity_check").fetchone()
    if integrity != ("ok",):
        raise SubstrateSchemaCompatibilityError("SQLite integrity check failed")
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
        or (schema_id, major, minor) != (SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR)
    ):
        raise SubstrateSchemaCompatibilityError("native core metadata is incompatible")
    return SchemaMetadata(core_id, role, schema_id, major, minor)


def _user_tables(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


def _execute_statements(connection: sqlite3.Connection, script: str) -> None:
    for statement in _statements(script):
        connection.execute(statement)
