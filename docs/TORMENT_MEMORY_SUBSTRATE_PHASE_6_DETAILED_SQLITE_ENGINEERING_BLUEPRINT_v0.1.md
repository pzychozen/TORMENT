# TORMENT Memory Substrate — Phase 6 Detailed SQLite Engineering Blueprint v0.1

**Status:** frozen engineering blueprint for the SQLite substrate. This is not implementation verification.

**Scope:** This document regenerates the candidate schema, API boundary, maintenance model, cutover fence, and qualification plan from the corrected Phase 6 invariants. It does not create a database, select an eligible runtime, migrate data, execute cutover, or authorize production wiring.

```text
PHASE_6_IS_ENGINEERING_BLUEPRINT_NOT_IMPLEMENTATION_VERIFICATION = YES
NATIVE_ID_STORAGE = 16_BYTE_BLOB
NATIVE_ID_GENERATION = UUIDV4
UUIDV7_REQUIRED = NO
SQLITE_JSON_SUPPORT_REQUIRED = YES
```

## 1. Native identity, namespaces, and deployment role

All native identities use standard-library UUIDv4 values. The API/diagnostic boundary uses canonical UUID text; SQLite stores the 16-byte UUID representation in `BLOB` columns, always validated with `length(id) = 16`. This applies to carriers, revisions, operations, transitions, representations, integrity records, reconciliation records, admissions, namespaces/scopes, and maintenance records.

SQLite `rowid` is never logical identity. UUID ordering has no semantic significance; semantic chronology comes from explicit revision ordinals, timestamps, and transitions. Legacy EIDs remain source-namespaced aliases.

Identity-resolution namespace, semantic scope, and legacy-source namespace are separate concepts and tables:

```text
IDENTITY_NAMESPACE != SEMANTIC_SCOPE
```

An identity row may retain immutable identity-resolution context. Effective semantic scope is revision-bound. Legacy-source namespace identifies the imported reference universe.

The physical core records `core_role`, never `authority_state`:

```text
STAGING | ACTIVE_CORE | EVIDENCE_ONLY
```

This is deployment state only and confers no TORMENT agency, permission, or authorization.

## 2. Candidate SQLite DDL

All tables below are `STRICT`; all foreign keys use default non-cascading deletion behavior. IDs shown as `BLOB` carry `CHECK(length(...)=16)`. The implementation expands that check for every native-ID column.

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE core_metadata (
  singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
  schema_id TEXT NOT NULL CHECK (schema_id = 'torment.memory.substrate'),
  schema_major INTEGER NOT NULL CHECK (schema_major >= 1),
  schema_minor INTEGER NOT NULL CHECK (schema_minor >= 0),
  core_id BLOB NOT NULL UNIQUE CHECK (length(core_id) = 16),
  core_role TEXT NOT NULL CHECK (core_role IN ('STAGING', 'ACTIVE_CORE', 'EVIDENCE_ONLY')),
  created_at_ns INTEGER NOT NULL
) STRICT;

CREATE TABLE maintenance_events (
  maintenance_id BLOB PRIMARY KEY CHECK (length(maintenance_id) = 16),
  maintenance_kind TEXT NOT NULL CHECK (maintenance_kind IN ('SCHEMA_UPGRADE', 'CUTOVER', 'RESTORE', 'BACKUP')),
  started_at_ns INTEGER NOT NULL,
  completed_at_ns INTEGER,
  detail_json TEXT NOT NULL CHECK (json_valid(detail_json))
) STRICT;

CREATE TABLE schema_migration_ledger (
  migration_key TEXT PRIMARY KEY,
  from_major INTEGER NOT NULL,
  from_minor INTEGER NOT NULL,
  to_major INTEGER NOT NULL,
  to_minor INTEGER NOT NULL,
  maintenance_id BLOB NOT NULL CHECK (length(maintenance_id) = 16),
  applied_at_ns INTEGER NOT NULL,
  FOREIGN KEY (maintenance_id) REFERENCES maintenance_events(maintenance_id)
) STRICT;

CREATE TABLE identity_namespaces (
  identity_namespace_id BLOB PRIMARY KEY CHECK (length(identity_namespace_id) = 16),
  namespace_key TEXT NOT NULL UNIQUE,
  created_at_ns INTEGER NOT NULL
) STRICT;

CREATE TABLE semantic_scopes (
  semantic_scope_id BLOB PRIMARY KEY CHECK (length(semantic_scope_id) = 16),
  scope_key TEXT NOT NULL UNIQUE,
  created_at_ns INTEGER NOT NULL
) STRICT;

CREATE TABLE legacy_source_namespaces (
  legacy_source_namespace_id BLOB PRIMARY KEY CHECK (length(legacy_source_namespace_id) = 16),
  source_key TEXT NOT NULL UNIQUE,
  created_at_ns INTEGER NOT NULL
) STRICT;
```

### Objects and revisions

```sql
CREATE TABLE objects (
  object_id BLOB PRIMARY KEY CHECK (length(object_id) = 16),
  identity_namespace_id BLOB NOT NULL CHECK (length(identity_namespace_id) = 16),
  object_kind TEXT NOT NULL,
  creating_transition_id BLOB CHECK (creating_transition_id IS NULL OR length(creating_transition_id) = 16),
  current_revision_id BLOB CHECK (current_revision_id IS NULL OR length(current_revision_id) = 16),
  current_revision_ordinal INTEGER,
  created_at_ns INTEGER NOT NULL,
  UNIQUE (object_id, current_revision_id, current_revision_ordinal),
  CHECK ((current_revision_id IS NULL) = (current_revision_ordinal IS NULL)),
  FOREIGN KEY (identity_namespace_id) REFERENCES identity_namespaces(identity_namespace_id),
  FOREIGN KEY (object_id, current_revision_id, current_revision_ordinal)
    REFERENCES object_revisions(object_id, object_revision_id, revision_ordinal)
    DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (creating_transition_id)
    REFERENCES semantic_transitions(transition_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE provenance_records (
  provenance_id BLOB PRIMARY KEY CHECK (length(provenance_id) = 16),
  origin_kind TEXT NOT NULL,
  source_channel TEXT,
  source_role TEXT,
  derivation_status TEXT NOT NULL,
  uncertainty_state TEXT NOT NULL,
  source_time_ns INTEGER,
  capture_time_ns INTEGER,
  memory_role TEXT,
  descriptive_notes TEXT
) STRICT;

CREATE TABLE object_revisions (
  object_revision_id BLOB PRIMARY KEY CHECK (length(object_revision_id) = 16),
  object_id BLOB NOT NULL CHECK (length(object_id) = 16),
  revision_ordinal INTEGER NOT NULL CHECK (revision_ordinal >= 1),
  lineage_kind TEXT NOT NULL CHECK (lineage_kind IN ('NATIVE_CREATION', 'NATIVE_ORDINARY', 'LEGACY_PREDECESSOR_UNKNOWN')),
  predecessor_revision_id BLOB CHECK (predecessor_revision_id IS NULL OR length(predecessor_revision_id) = 16),
  predecessor_revision_ordinal INTEGER,
  effective_semantic_scope_id BLOB NOT NULL CHECK (length(effective_semantic_scope_id) = 16),
  existence_state TEXT NOT NULL,
  lifecycle_state TEXT NOT NULL,
  lifecycle_authoritative INTEGER NOT NULL CHECK (lifecycle_authoritative IN (0, 1)),
  lifecycle_actor TEXT,
  lifecycle_via TEXT,
  lifecycle_set_at_ns INTEGER,
  governance_state TEXT NOT NULL,
  authority_category TEXT NOT NULL CHECK (authority_category IN (
    'NOT_APPLICABLE', 'UNKNOWN', 'EVIDENCE', 'INTENT_PROPOSAL',
    'DECISION_RECORD', 'ACTIVE_AUTHORIZATION', 'EXECUTION_RECORD'
  )),
  provenance_id BLOB CHECK (provenance_id IS NULL OR length(provenance_id) = 16),
  payload_format TEXT NOT NULL CHECK (payload_format IN ('NONE', 'JSON', 'TEXT', 'BLOB')),
  payload_text TEXT,
  payload_blob BLOB,
  created_at_ns INTEGER NOT NULL,
  UNIQUE (object_id, object_revision_id, revision_ordinal),
  UNIQUE (object_id, revision_ordinal),
  CHECK (
    (lineage_kind = 'NATIVE_CREATION' AND revision_ordinal = 1 AND predecessor_revision_id IS NULL AND predecessor_revision_ordinal IS NULL)
    OR
    (lineage_kind = 'NATIVE_ORDINARY' AND revision_ordinal > 1 AND predecessor_revision_id IS NOT NULL
      AND predecessor_revision_ordinal IS NOT NULL AND revision_ordinal = predecessor_revision_ordinal + 1)
    OR
    (lineage_kind = 'LEGACY_PREDECESSOR_UNKNOWN' AND revision_ordinal = 1 AND predecessor_revision_id IS NULL AND predecessor_revision_ordinal IS NULL)
  ),
  CHECK (
    (payload_format = 'NONE' AND payload_text IS NULL AND payload_blob IS NULL)
    OR (payload_format = 'JSON' AND payload_text IS NOT NULL AND payload_blob IS NULL AND json_valid(payload_text))
    OR (payload_format = 'TEXT' AND payload_text IS NOT NULL AND payload_blob IS NULL)
    OR (payload_format = 'BLOB' AND payload_text IS NULL AND payload_blob IS NOT NULL)
  ),
  FOREIGN KEY (object_id) REFERENCES objects(object_id),
  FOREIGN KEY (object_id, predecessor_revision_id, predecessor_revision_ordinal)
    REFERENCES object_revisions(object_id, object_revision_id, revision_ordinal)
    DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (effective_semantic_scope_id) REFERENCES semantic_scopes(semantic_scope_id),
  FOREIGN KEY (provenance_id) REFERENCES provenance_records(provenance_id)
) STRICT;

CREATE UNIQUE INDEX object_one_ordinary_successor
  ON object_revisions(object_id, predecessor_revision_id)
  WHERE lineage_kind = 'NATIVE_ORDINARY';
```

### Relationships, revisions, and endpoints

```sql
CREATE TABLE relationships (
  relationship_id BLOB PRIMARY KEY CHECK (length(relationship_id) = 16),
  identity_namespace_id BLOB NOT NULL CHECK (length(identity_namespace_id) = 16),
  relationship_kind TEXT NOT NULL,
  creating_transition_id BLOB CHECK (creating_transition_id IS NULL OR length(creating_transition_id) = 16),
  current_revision_id BLOB CHECK (current_revision_id IS NULL OR length(current_revision_id) = 16),
  current_revision_ordinal INTEGER,
  created_at_ns INTEGER NOT NULL,
  UNIQUE (relationship_id, current_revision_id, current_revision_ordinal),
  CHECK ((current_revision_id IS NULL) = (current_revision_ordinal IS NULL)),
  FOREIGN KEY (identity_namespace_id) REFERENCES identity_namespaces(identity_namespace_id),
  FOREIGN KEY (relationship_id, current_revision_id, current_revision_ordinal)
    REFERENCES relationship_revisions(relationship_id, relationship_revision_id, revision_ordinal)
    DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (creating_transition_id)
    REFERENCES semantic_transitions(transition_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE relationship_revisions (
  relationship_revision_id BLOB PRIMARY KEY CHECK (length(relationship_revision_id) = 16),
  relationship_id BLOB NOT NULL CHECK (length(relationship_id) = 16),
  revision_ordinal INTEGER NOT NULL CHECK (revision_ordinal >= 1),
  lineage_kind TEXT NOT NULL CHECK (lineage_kind IN ('NATIVE_CREATION', 'NATIVE_ORDINARY', 'LEGACY_PREDECESSOR_UNKNOWN')),
  predecessor_revision_id BLOB CHECK (predecessor_revision_id IS NULL OR length(predecessor_revision_id) = 16),
  predecessor_revision_ordinal INTEGER,
  effective_semantic_scope_id BLOB NOT NULL CHECK (length(effective_semantic_scope_id) = 16),
  lifecycle_state TEXT NOT NULL,
  lifecycle_authoritative INTEGER NOT NULL CHECK (lifecycle_authoritative IN (0, 1)),
  governance_state TEXT NOT NULL,
  authority_category TEXT NOT NULL CHECK (authority_category IN (
    'NOT_APPLICABLE', 'UNKNOWN', 'EVIDENCE', 'INTENT_PROPOSAL',
    'DECISION_RECORD', 'ACTIVE_AUTHORIZATION', 'EXECUTION_RECORD'
  )),
  provenance_id BLOB CHECK (provenance_id IS NULL OR length(provenance_id) = 16),
  payload_format TEXT NOT NULL CHECK (payload_format IN ('NONE', 'JSON', 'TEXT', 'BLOB')),
  payload_text TEXT,
  payload_blob BLOB,
  created_at_ns INTEGER NOT NULL,
  UNIQUE (relationship_id, relationship_revision_id, revision_ordinal),
  UNIQUE (relationship_id, revision_ordinal),
  CHECK (
    (lineage_kind = 'NATIVE_CREATION' AND revision_ordinal = 1 AND predecessor_revision_id IS NULL AND predecessor_revision_ordinal IS NULL)
    OR
    (lineage_kind = 'NATIVE_ORDINARY' AND revision_ordinal > 1 AND predecessor_revision_id IS NOT NULL
      AND predecessor_revision_ordinal IS NOT NULL AND revision_ordinal = predecessor_revision_ordinal + 1)
    OR
    (lineage_kind = 'LEGACY_PREDECESSOR_UNKNOWN' AND revision_ordinal = 1 AND predecessor_revision_id IS NULL AND predecessor_revision_ordinal IS NULL)
  ),
  CHECK (
    (payload_format = 'NONE' AND payload_text IS NULL AND payload_blob IS NULL)
    OR (payload_format = 'JSON' AND payload_text IS NOT NULL AND payload_blob IS NULL AND json_valid(payload_text))
    OR (payload_format = 'TEXT' AND payload_text IS NOT NULL AND payload_blob IS NULL)
    OR (payload_format = 'BLOB' AND payload_text IS NULL AND payload_blob IS NOT NULL)
  ),
  FOREIGN KEY (relationship_id) REFERENCES relationships(relationship_id),
  FOREIGN KEY (relationship_id, predecessor_revision_id, predecessor_revision_ordinal)
    REFERENCES relationship_revisions(relationship_id, relationship_revision_id, revision_ordinal)
    DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (effective_semantic_scope_id) REFERENCES semantic_scopes(semantic_scope_id),
  FOREIGN KEY (provenance_id) REFERENCES provenance_records(provenance_id)
) STRICT;

CREATE UNIQUE INDEX relationship_one_ordinary_successor
  ON relationship_revisions(relationship_id, predecessor_revision_id)
  WHERE lineage_kind = 'NATIVE_ORDINARY';

CREATE TABLE relationship_revision_endpoints (
  relationship_revision_id BLOB NOT NULL CHECK (length(relationship_revision_id) = 16),
  endpoint_ordinal INTEGER NOT NULL CHECK (endpoint_ordinal >= 0),
  endpoint_role TEXT NOT NULL,
  endpoint_semantic_scope_id BLOB NOT NULL CHECK (length(endpoint_semantic_scope_id) = 16),
  object_id BLOB NOT NULL CHECK (length(object_id) = 16),
  binding_mode TEXT NOT NULL CHECK (binding_mode IN ('IDENTITY', 'EXACT_REVISION')),
  bound_object_revision_id BLOB CHECK (bound_object_revision_id IS NULL OR length(bound_object_revision_id) = 16),
  bound_object_revision_ordinal INTEGER,
  PRIMARY KEY (relationship_revision_id, endpoint_ordinal),
  CHECK (
    (binding_mode = 'IDENTITY' AND bound_object_revision_id IS NULL AND bound_object_revision_ordinal IS NULL)
    OR
    (binding_mode = 'EXACT_REVISION' AND bound_object_revision_id IS NOT NULL AND bound_object_revision_ordinal IS NOT NULL)
  ),
  FOREIGN KEY (relationship_revision_id) REFERENCES relationship_revisions(relationship_revision_id),
  FOREIGN KEY (endpoint_semantic_scope_id) REFERENCES semantic_scopes(semantic_scope_id),
  FOREIGN KEY (object_id) REFERENCES objects(object_id),
  FOREIGN KEY (object_id, bound_object_revision_id, bound_object_revision_ordinal)
    REFERENCES object_revisions(object_id, object_revision_id, revision_ordinal)
    DEFERRABLE INITIALLY DEFERRED
) STRICT;
```

### Operations, transitions, and typed effects

```sql
CREATE TABLE idempotency_namespaces (
  idempotency_namespace_id BLOB PRIMARY KEY CHECK (length(idempotency_namespace_id) = 16),
  namespace_key TEXT NOT NULL UNIQUE
) STRICT;

CREATE TABLE operations (
  operation_id BLOB PRIMARY KEY CHECK (length(operation_id) = 16),
  idempotency_namespace_id BLOB NOT NULL CHECK (length(idempotency_namespace_id) = 16),
  idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) > 0),
  operation_kind TEXT NOT NULL,
  intent_contract TEXT NOT NULL CHECK (intent_contract = 'TMS-INTENT-1'),
  canonical_intent_json TEXT NOT NULL CHECK (json_valid(canonical_intent_json)),
  created_at_ns INTEGER NOT NULL,
  UNIQUE (idempotency_namespace_id, idempotency_key),
  FOREIGN KEY (idempotency_namespace_id) REFERENCES idempotency_namespaces(idempotency_namespace_id)
) STRICT;

CREATE TABLE operation_targets (
  operation_id BLOB NOT NULL CHECK (length(operation_id) = 16),
  target_ordinal INTEGER NOT NULL CHECK (target_ordinal >= 0),
  target_role TEXT NOT NULL,
  target_kind TEXT NOT NULL CHECK (target_kind IN ('OBJECT', 'RELATIONSHIP')),
  object_id BLOB,
  object_revision_id BLOB,
  object_revision_ordinal INTEGER,
  relationship_id BLOB,
  relationship_revision_id BLOB,
  relationship_revision_ordinal INTEGER,
  PRIMARY KEY (operation_id, target_ordinal),
  CHECK (
    (target_kind = 'OBJECT' AND object_id IS NOT NULL AND relationship_id IS NULL AND relationship_revision_id IS NULL)
    OR
    (target_kind = 'RELATIONSHIP' AND relationship_id IS NOT NULL AND object_id IS NULL AND object_revision_id IS NULL)
  ),
  CHECK ((object_revision_id IS NULL) = (object_revision_ordinal IS NULL)),
  CHECK ((relationship_revision_id IS NULL) = (relationship_revision_ordinal IS NULL)),
  FOREIGN KEY (operation_id) REFERENCES operations(operation_id),
  FOREIGN KEY (object_id) REFERENCES objects(object_id),
  FOREIGN KEY (object_id, object_revision_id, object_revision_ordinal)
    REFERENCES object_revisions(object_id, object_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (relationship_id) REFERENCES relationships(relationship_id),
  FOREIGN KEY (relationship_id, relationship_revision_id, relationship_revision_ordinal)
    REFERENCES relationship_revisions(relationship_id, relationship_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE operation_outputs (
  operation_id BLOB NOT NULL CHECK (length(operation_id) = 16),
  output_ordinal INTEGER NOT NULL CHECK (output_ordinal >= 0),
  output_role TEXT NOT NULL,
  output_kind TEXT NOT NULL CHECK (output_kind IN ('OBJECT', 'RELATIONSHIP', 'REPRESENTATION')),
  object_id BLOB,
  object_revision_id BLOB,
  object_revision_ordinal INTEGER,
  relationship_id BLOB,
  relationship_revision_id BLOB,
  relationship_revision_ordinal INTEGER,
  representation_id BLOB,
  PRIMARY KEY (operation_id, output_ordinal),
  CHECK (
    (output_kind = 'OBJECT' AND object_id IS NOT NULL AND relationship_id IS NULL AND representation_id IS NULL)
    OR
    (output_kind = 'RELATIONSHIP' AND relationship_id IS NOT NULL AND object_id IS NULL AND representation_id IS NULL)
    OR
    (output_kind = 'REPRESENTATION' AND representation_id IS NOT NULL AND object_id IS NULL AND relationship_id IS NULL)
  ),
  CHECK ((object_revision_id IS NULL) = (object_revision_ordinal IS NULL)),
  CHECK ((relationship_revision_id IS NULL) = (relationship_revision_ordinal IS NULL)),
  FOREIGN KEY (operation_id) REFERENCES operations(operation_id),
  FOREIGN KEY (object_id) REFERENCES objects(object_id),
  FOREIGN KEY (object_id, object_revision_id, object_revision_ordinal)
    REFERENCES object_revisions(object_id, object_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (relationship_id) REFERENCES relationships(relationship_id),
  FOREIGN KEY (relationship_id, relationship_revision_id, relationship_revision_ordinal)
    REFERENCES relationship_revisions(relationship_id, relationship_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (representation_id) REFERENCES representations(representation_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE operation_rejections (
  operation_id BLOB PRIMARY KEY CHECK (length(operation_id) = 16),
  rejection_code TEXT NOT NULL,
  rejection_detail TEXT,
  rejected_at_ns INTEGER NOT NULL,
  FOREIGN KEY (operation_id) REFERENCES operations(operation_id)
) STRICT;

CREATE TABLE semantic_transitions (
  transition_id BLOB PRIMARY KEY CHECK (length(transition_id) = 16),
  operation_id BLOB NOT NULL UNIQUE CHECK (length(operation_id) = 16),
  transition_kind TEXT NOT NULL,
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('NATIVE', 'LEGACY_ADMISSION')),
  committed_at_ns INTEGER NOT NULL,
  FOREIGN KEY (operation_id) REFERENCES operations(operation_id)
) STRICT;
```

Typed effects have real FKs and are unordered atomic sets. There is deliberately no global effect ordinal and no unconstrained generic `subject_id`.

```sql
CREATE TABLE object_revision_effects (
  transition_id BLOB NOT NULL,
  object_id BLOB NOT NULL,
  object_revision_id BLOB NOT NULL,
  object_revision_ordinal INTEGER NOT NULL,
  PRIMARY KEY (transition_id, object_id, object_revision_id),
  FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id),
  FOREIGN KEY (object_id, object_revision_id, object_revision_ordinal)
    REFERENCES object_revisions(object_id, object_revision_id, revision_ordinal)
) STRICT;

CREATE TABLE relationship_revision_effects (
  transition_id BLOB NOT NULL,
  relationship_id BLOB NOT NULL,
  relationship_revision_id BLOB NOT NULL,
  relationship_revision_ordinal INTEGER NOT NULL,
  PRIMARY KEY (transition_id, relationship_id, relationship_revision_id),
  FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id),
  FOREIGN KEY (relationship_id, relationship_revision_id, relationship_revision_ordinal)
    REFERENCES relationship_revisions(relationship_id, relationship_revision_id, revision_ordinal)
) STRICT;

CREATE TABLE representation_state_effects (
  transition_id BLOB NOT NULL,
  representation_id BLOB NOT NULL,
  readiness TEXT NOT NULL,
  operational_disposition TEXT NOT NULL,
  selected_measurement_id BLOB,
  PRIMARY KEY (transition_id, representation_id),
  FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id),
  FOREIGN KEY (representation_id) REFERENCES representations(representation_id),
  FOREIGN KEY (selected_measurement_id) REFERENCES integrity_measurements(measurement_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE integrity_measurement_effects (
  transition_id BLOB NOT NULL,
  measurement_id BLOB NOT NULL,
  PRIMARY KEY (transition_id, measurement_id),
  FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id),
  FOREIGN KEY (measurement_id) REFERENCES integrity_measurements(measurement_id)
) STRICT;

CREATE TABLE reconciliation_state_effects (
  transition_id BLOB NOT NULL,
  reconciliation_case_id BLOB NOT NULL,
  reconciliation_state_id BLOB NOT NULL,
  reconciliation_state_ordinal INTEGER NOT NULL,
  PRIMARY KEY (transition_id, reconciliation_case_id, reconciliation_state_id),
  FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id),
  FOREIGN KEY (reconciliation_case_id, reconciliation_state_id, reconciliation_state_ordinal)
    REFERENCES reconciliation_case_states(reconciliation_case_id, reconciliation_state_id, state_ordinal)
) STRICT;

CREATE TABLE legacy_admission_effects (
  transition_id BLOB NOT NULL,
  admission_record_id BLOB NOT NULL,
  PRIMARY KEY (transition_id, admission_record_id),
  FOREIGN KEY (transition_id) REFERENCES semantic_transitions(transition_id),
  FOREIGN KEY (admission_record_id) REFERENCES legacy_admission_records(admission_record_id)
) STRICT;
```

### Representations, integrity, and reconciliation

```sql
CREATE TABLE representations (
  representation_id BLOB PRIMARY KEY CHECK (length(representation_id) = 16),
  source_kind TEXT NOT NULL CHECK (source_kind IN ('OBJECT_REVISION', 'RELATIONSHIP_REVISION')),
  source_object_id BLOB,
  source_object_revision_id BLOB,
  source_object_revision_ordinal INTEGER,
  source_relationship_id BLOB,
  source_relationship_revision_id BLOB,
  source_relationship_revision_ordinal INTEGER,
  representation_class TEXT NOT NULL,
  generation INTEGER NOT NULL CHECK (generation >= 1),
  derivation_contract_version TEXT NOT NULL,
  encoding_id TEXT NOT NULL,
  dtype TEXT,
  dimension INTEGER CHECK (dimension IS NULL OR dimension > 0),
  expected_payload_byte_length INTEGER CHECK (expected_payload_byte_length IS NULL OR expected_payload_byte_length >= 0),
  created_at_ns INTEGER NOT NULL,
  CHECK (
    (source_kind = 'OBJECT_REVISION' AND source_object_id IS NOT NULL AND source_object_revision_id IS NOT NULL
      AND source_object_revision_ordinal IS NOT NULL AND source_relationship_id IS NULL)
    OR
    (source_kind = 'RELATIONSHIP_REVISION' AND source_relationship_id IS NOT NULL AND source_relationship_revision_id IS NOT NULL
      AND source_relationship_revision_ordinal IS NOT NULL AND source_object_id IS NULL)
  ),
  FOREIGN KEY (source_object_id, source_object_revision_id, source_object_revision_ordinal)
    REFERENCES object_revisions(object_id, object_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (source_relationship_id, source_relationship_revision_id, source_relationship_revision_ordinal)
    REFERENCES relationship_revisions(relationship_id, relationship_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE UNIQUE INDEX representation_object_source_generation
  ON representations(source_object_revision_id, representation_class, generation)
  WHERE source_kind = 'OBJECT_REVISION';
CREATE UNIQUE INDEX representation_relationship_source_generation
  ON representations(source_relationship_revision_id, representation_class, generation)
  WHERE source_kind = 'RELATIONSHIP_REVISION';

CREATE TABLE representation_current_state (
  representation_id BLOB PRIMARY KEY CHECK (length(representation_id) = 16),
  readiness TEXT NOT NULL CHECK (readiness IN ('PENDING', 'READY', 'FAILED', 'UNKNOWN')),
  operational_disposition TEXT NOT NULL CHECK (operational_disposition IN (
    'USABLE', 'WITHHELD', 'RECONCILIATION_REQUIRED', 'QUARANTINED', 'RETAINED_EVIDENCE'
  )),
  selected_integrity_measurement_id BLOB,
  FOREIGN KEY (representation_id) REFERENCES representations(representation_id),
  FOREIGN KEY (selected_integrity_measurement_id)
    REFERENCES integrity_measurements(measurement_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE representation_payloads (
  representation_id BLOB PRIMARY KEY CHECK (length(representation_id) = 16),
  payload_bytes BLOB NOT NULL,
  observed_payload_byte_length INTEGER NOT NULL CHECK (observed_payload_byte_length = length(payload_bytes)),
  stored_at_ns INTEGER NOT NULL,
  FOREIGN KEY (representation_id) REFERENCES representations(representation_id)
) STRICT;

CREATE TABLE representation_dependencies (
  representation_id BLOB NOT NULL,
  dependency_representation_id BLOB NOT NULL,
  dependency_role TEXT NOT NULL,
  PRIMARY KEY (representation_id, dependency_representation_id, dependency_role),
  CHECK (representation_id != dependency_representation_id),
  FOREIGN KEY (representation_id) REFERENCES representations(representation_id),
  FOREIGN KEY (dependency_representation_id) REFERENCES representations(representation_id)
) STRICT;

CREATE TABLE integrity_expectations (
  expectation_id BLOB PRIMARY KEY CHECK (length(expectation_id) = 16),
  subject_kind TEXT NOT NULL CHECK (subject_kind IN ('OBJECT_REVISION', 'RELATIONSHIP_REVISION', 'REPRESENTATION')),
  object_id BLOB,
  object_revision_id BLOB,
  object_revision_ordinal INTEGER,
  relationship_id BLOB,
  relationship_revision_id BLOB,
  relationship_revision_ordinal INTEGER,
  representation_id BLOB,
  algorithm_id TEXT NOT NULL,
  expected_value BLOB NOT NULL,
  value_encoding TEXT NOT NULL,
  established_at_ns INTEGER NOT NULL,
  CHECK (
    (subject_kind = 'OBJECT_REVISION' AND object_id IS NOT NULL AND object_revision_id IS NOT NULL AND object_revision_ordinal IS NOT NULL
      AND relationship_id IS NULL AND representation_id IS NULL)
    OR
    (subject_kind = 'RELATIONSHIP_REVISION' AND relationship_id IS NOT NULL AND relationship_revision_id IS NOT NULL AND relationship_revision_ordinal IS NOT NULL
      AND object_id IS NULL AND representation_id IS NULL)
    OR
    (subject_kind = 'REPRESENTATION' AND representation_id IS NOT NULL AND object_id IS NULL AND relationship_id IS NULL)
  ),
  FOREIGN KEY (object_id, object_revision_id, object_revision_ordinal)
    REFERENCES object_revisions(object_id, object_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (relationship_id, relationship_revision_id, relationship_revision_ordinal)
    REFERENCES relationship_revisions(relationship_id, relationship_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (representation_id) REFERENCES representations(representation_id)
) STRICT;

CREATE TABLE integrity_measurements (
  measurement_id BLOB PRIMARY KEY CHECK (length(measurement_id) = 16),
  expectation_id BLOB NOT NULL CHECK (length(expectation_id) = 16),
  result TEXT NOT NULL CHECK (result IN ('MATCH', 'MISMATCH', 'UNVERIFIABLE', 'ERROR')),
  observed_value BLOB,
  reason TEXT,
  measured_at_ns INTEGER NOT NULL,
  FOREIGN KEY (expectation_id) REFERENCES integrity_expectations(expectation_id)
) STRICT;

CREATE TABLE reconciliation_cases (
  reconciliation_case_id BLOB PRIMARY KEY CHECK (length(reconciliation_case_id) = 16),
  condition_code TEXT NOT NULL,
  reason_text TEXT NOT NULL,
  subject_kind TEXT NOT NULL CHECK (subject_kind IN ('OBJECT_REVISION', 'RELATIONSHIP_REVISION', 'REPRESENTATION', 'CORE', 'LEGACY_ADMISSION')),
  object_id BLOB,
  object_revision_id BLOB,
  object_revision_ordinal INTEGER,
  relationship_id BLOB,
  relationship_revision_id BLOB,
  relationship_revision_ordinal INTEGER,
  representation_id BLOB,
  legacy_admission_record_id BLOB,
  current_state_id BLOB,
  current_state_ordinal INTEGER,
  opened_at_ns INTEGER NOT NULL,
  UNIQUE (reconciliation_case_id, current_state_id, current_state_ordinal),
  CHECK ((current_state_id IS NULL) = (current_state_ordinal IS NULL)),
  CHECK (
    (subject_kind = 'OBJECT_REVISION' AND object_id IS NOT NULL AND object_revision_id IS NOT NULL AND object_revision_ordinal IS NOT NULL
      AND relationship_id IS NULL AND representation_id IS NULL AND legacy_admission_record_id IS NULL)
    OR
    (subject_kind = 'RELATIONSHIP_REVISION' AND relationship_id IS NOT NULL AND relationship_revision_id IS NOT NULL AND relationship_revision_ordinal IS NOT NULL
      AND object_id IS NULL AND representation_id IS NULL AND legacy_admission_record_id IS NULL)
    OR
    (subject_kind = 'REPRESENTATION' AND representation_id IS NOT NULL AND object_id IS NULL AND relationship_id IS NULL AND legacy_admission_record_id IS NULL)
    OR
    (subject_kind = 'CORE' AND object_id IS NULL AND relationship_id IS NULL AND representation_id IS NULL AND legacy_admission_record_id IS NULL)
    OR
    (subject_kind = 'LEGACY_ADMISSION' AND legacy_admission_record_id IS NOT NULL AND object_id IS NULL AND relationship_id IS NULL AND representation_id IS NULL)
  ),
  FOREIGN KEY (object_id, object_revision_id, object_revision_ordinal)
    REFERENCES object_revisions(object_id, object_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (relationship_id, relationship_revision_id, relationship_revision_ordinal)
    REFERENCES relationship_revisions(relationship_id, relationship_revision_id, revision_ordinal) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (representation_id) REFERENCES representations(representation_id),
  FOREIGN KEY (legacy_admission_record_id) REFERENCES legacy_admission_records(admission_record_id),
  FOREIGN KEY (reconciliation_case_id, current_state_id, current_state_ordinal)
    REFERENCES reconciliation_case_states(reconciliation_case_id, reconciliation_state_id, state_ordinal) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE reconciliation_case_states (
  reconciliation_state_id BLOB PRIMARY KEY CHECK (length(reconciliation_state_id) = 16),
  reconciliation_case_id BLOB NOT NULL CHECK (length(reconciliation_case_id) = 16),
  state_ordinal INTEGER NOT NULL CHECK (state_ordinal >= 1),
  lineage_kind TEXT NOT NULL CHECK (lineage_kind IN ('NATIVE_CREATION', 'NATIVE_ORDINARY', 'LEGACY_PREDECESSOR_UNKNOWN')),
  predecessor_state_id BLOB,
  predecessor_state_ordinal INTEGER,
  operational_disposition TEXT NOT NULL,
  determination TEXT,
  resolution_reason TEXT,
  created_at_ns INTEGER NOT NULL,
  UNIQUE (reconciliation_case_id, reconciliation_state_id, state_ordinal),
  UNIQUE (reconciliation_case_id, state_ordinal),
  CHECK (
    (lineage_kind IN ('NATIVE_CREATION', 'LEGACY_PREDECESSOR_UNKNOWN') AND state_ordinal = 1
      AND predecessor_state_id IS NULL AND predecessor_state_ordinal IS NULL)
    OR
    (lineage_kind = 'NATIVE_ORDINARY' AND state_ordinal > 1 AND predecessor_state_id IS NOT NULL
      AND predecessor_state_ordinal IS NOT NULL AND state_ordinal = predecessor_state_ordinal + 1)
  ),
  FOREIGN KEY (reconciliation_case_id) REFERENCES reconciliation_cases(reconciliation_case_id),
  FOREIGN KEY (reconciliation_case_id, predecessor_state_id, predecessor_state_ordinal)
    REFERENCES reconciliation_case_states(reconciliation_case_id, reconciliation_state_id, state_ordinal) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE UNIQUE INDEX reconciliation_one_ordinary_successor
  ON reconciliation_case_states(reconciliation_case_id, predecessor_state_id)
  WHERE lineage_kind = 'NATIVE_ORDINARY';
```

### Provenance children and legacy admission/evidence

```sql
CREATE TABLE provenance_material_sources (
  provenance_id BLOB NOT NULL,
  source_ordinal INTEGER NOT NULL CHECK (source_ordinal >= 0),
  source_kind TEXT NOT NULL CHECK (source_kind IN ('REPRESENTATION', 'LEGACY_ARTIFACT', 'EXTERNAL_LOCATOR')),
  representation_id BLOB,
  legacy_artifact_id BLOB,
  external_locator TEXT,
  PRIMARY KEY (provenance_id, source_ordinal),
  CHECK (
    (source_kind = 'REPRESENTATION' AND representation_id IS NOT NULL AND legacy_artifact_id IS NULL AND external_locator IS NULL)
    OR
    (source_kind = 'LEGACY_ARTIFACT' AND legacy_artifact_id IS NOT NULL AND representation_id IS NULL AND external_locator IS NULL)
    OR
    (source_kind = 'EXTERNAL_LOCATOR' AND external_locator IS NOT NULL AND representation_id IS NULL AND legacy_artifact_id IS NULL)
  ),
  FOREIGN KEY (provenance_id) REFERENCES provenance_records(provenance_id),
  FOREIGN KEY (representation_id) REFERENCES representations(representation_id),
  FOREIGN KEY (legacy_artifact_id) REFERENCES legacy_artifacts(legacy_artifact_id)
) STRICT;

CREATE TABLE legacy_snapshots (
  legacy_snapshot_id BLOB PRIMARY KEY CHECK (length(legacy_snapshot_id) = 16),
  legacy_source_namespace_id BLOB NOT NULL CHECK (length(legacy_source_namespace_id) = 16),
  snapshot_identity TEXT NOT NULL UNIQUE,
  captured_at_ns INTEGER NOT NULL,
  FOREIGN KEY (legacy_source_namespace_id) REFERENCES legacy_source_namespaces(legacy_source_namespace_id)
) STRICT;

CREATE TABLE legacy_artifacts (
  legacy_artifact_id BLOB PRIMARY KEY CHECK (length(legacy_artifact_id) = 16),
  legacy_snapshot_id BLOB NOT NULL CHECK (length(legacy_snapshot_id) = 16),
  artifact_identity TEXT NOT NULL,
  artifact_kind TEXT NOT NULL,
  observed_locator TEXT,
  digest_algorithm TEXT,
  digest_value BLOB,
  retained_bytes BLOB,
  UNIQUE (legacy_snapshot_id, artifact_identity),
  FOREIGN KEY (legacy_snapshot_id) REFERENCES legacy_snapshots(legacy_snapshot_id)
) STRICT;

CREATE TABLE legacy_artifact_records (
  legacy_artifact_record_id BLOB PRIMARY KEY CHECK (length(legacy_artifact_record_id) = 16),
  legacy_artifact_id BLOB NOT NULL CHECK (length(legacy_artifact_id) = 16),
  record_identity TEXT NOT NULL,
  observed_locator TEXT,
  UNIQUE (legacy_artifact_id, record_identity),
  FOREIGN KEY (legacy_artifact_id) REFERENCES legacy_artifacts(legacy_artifact_id)
) STRICT;

CREATE TABLE legacy_admission_batches (
  admission_batch_id BLOB PRIMARY KEY CHECK (length(admission_batch_id) = 16),
  legacy_snapshot_id BLOB NOT NULL CHECK (length(legacy_snapshot_id) = 16),
  batch_identity TEXT NOT NULL,
  opened_at_ns INTEGER NOT NULL,
  completed_at_ns INTEGER,
  UNIQUE (legacy_snapshot_id, batch_identity),
  FOREIGN KEY (legacy_snapshot_id) REFERENCES legacy_snapshots(legacy_snapshot_id)
) STRICT;

CREATE TABLE legacy_admission_records (
  admission_record_id BLOB PRIMARY KEY CHECK (length(admission_record_id) = 16),
  admission_batch_id BLOB NOT NULL CHECK (length(admission_batch_id) = 16),
  legacy_artifact_record_id BLOB NOT NULL CHECK (length(legacy_artifact_record_id) = 16),
  admission_status TEXT NOT NULL CHECK (admission_status IN ('ADMITTED', 'UNKNOWN', 'QUARANTINED', 'NOT_ADMITTED')),
  unknown_fields_json TEXT CHECK (unknown_fields_json IS NULL OR json_valid(unknown_fields_json)),
  UNIQUE (admission_batch_id, legacy_artifact_record_id),
  FOREIGN KEY (admission_batch_id) REFERENCES legacy_admission_batches(admission_batch_id),
  FOREIGN KEY (legacy_artifact_record_id) REFERENCES legacy_artifact_records(legacy_artifact_record_id)
) STRICT;

CREATE TABLE legacy_object_aliases (
  legacy_source_namespace_id BLOB NOT NULL,
  alias_kind TEXT NOT NULL,
  alias_value TEXT NOT NULL,
  object_id BLOB NOT NULL,
  PRIMARY KEY (legacy_source_namespace_id, alias_kind, alias_value),
  FOREIGN KEY (legacy_source_namespace_id) REFERENCES legacy_source_namespaces(legacy_source_namespace_id),
  FOREIGN KEY (object_id) REFERENCES objects(object_id)
) STRICT;

CREATE TABLE legacy_relationship_aliases (
  legacy_source_namespace_id BLOB NOT NULL,
  alias_kind TEXT NOT NULL,
  alias_value TEXT NOT NULL,
  relationship_id BLOB NOT NULL,
  PRIMARY KEY (legacy_source_namespace_id, alias_kind, alias_value),
  FOREIGN KEY (legacy_source_namespace_id) REFERENCES legacy_source_namespaces(legacy_source_namespace_id),
  FOREIGN KEY (relationship_id) REFERENCES relationships(relationship_id)
) STRICT;

CREATE TABLE legacy_quarantine_records (
  quarantine_record_id BLOB PRIMARY KEY CHECK (length(quarantine_record_id) = 16),
  admission_record_id BLOB NOT NULL UNIQUE CHECK (length(admission_record_id) = 16),
  condition_code TEXT NOT NULL,
  reason_text TEXT NOT NULL,
  retained_legacy_artifact_id BLOB NOT NULL CHECK (length(retained_legacy_artifact_id) = 16),
  reconciliation_case_id BLOB,
  FOREIGN KEY (admission_record_id) REFERENCES legacy_admission_records(admission_record_id),
  FOREIGN KEY (retained_legacy_artifact_id) REFERENCES legacy_artifacts(legacy_artifact_id),
  FOREIGN KEY (reconciliation_case_id) REFERENCES reconciliation_cases(reconciliation_case_id)
) STRICT;
```

## 3. Publication, immutability, and helper-owned invariants

Typed transition effects are the authoritative publication linkage. Immutable revisions and current-state rows do not carry independently writable `published_transition_id` columns. Retained creation/admission backlinks on carrier identities are immutable backlinks; the helper verifies that each agrees with the relevant typed transition effect.

Triggers enforce row-local rules only: immutable revision/transition/provenance rows reject `UPDATE` and `DELETE`; immutable representation identity/generation fields reject change; and JSON payload format requires `json_valid()`. There is no semantic cascade delete.

The closed schema-v1 helper-owned invariant list is:

1. Every committed object/relationship ends a transaction with a non-null same-carrier current revision.
2. Every semantic transition has at least one typed effect, and each semantic mutation has its required effect.
3. One operation never resolves to both a transition and a durable rejection.
4. `READY` representation publication has exact payload, pre-established expectation, acceptable measurement, valid source, satisfied dependencies, and compatible generation/contract.
5. Published immutable aggregates are closed: revision children, endpoints, representation dependencies, provenance material-source children, and equivalent child sets cannot later be extended or mutated.
6. Reconciliation current selection resolves to the state published by its transition and cannot commit incomplete.
7. Imported semantic state publishes only through legacy-admission transition/effect and never impersonates native historical creation.
8. Allocated outputs and retained creation/admission backlinks resolve to subjects actually published by their operation/transition.

SQLite does not naturally express these deferred aggregate or cross-table XOR checks. The one outer transaction helper validates them immediately before commit. Adding a helper-owned invariant requires a schema-contract update, documented invariant, and qualification case.

## 4. Canonical intent and operation resolution

`operation_id` is a native UUIDv4/BLOB identity. Idempotency is separate: `(idempotency_namespace_id, idempotency_key)` is unique and stable before repeat execution can create ambiguous effects. The key may be caller-supplied or internally deterministically recoverable; it need not be a UUID.

`TMS-INTENT-1` is canonical UTF-8 JSON produced by typed builders: Unicode normalization, deterministic key ordering, compact serialization, operation-defined ordering for set-like collections, deterministic numeric normalization, and rejection of NaN/Infinity. It excludes allocated outputs, incidental timestamps, process-local values, and other execution artifacts. `json_valid()` proves syntax only; retry compares the canonical representation itself. A later digest is non-semantic acceleration only.

The operation-resolution helper loads the unique idempotency pair, compares canonical intent, returns the existing transition outputs or durable rejection, and rejects conflicting reuse. Ordinary rollback produces no synthetic negative row.

## 5. Representation ready protocol

Expensive derivation runs outside the transaction. Before publication, the derivation result establishes its immutable integrity expectation and any expected byte length.

```text
derive output and establish expectation in memory
BEGIN IMMEDIATE
  resolve idempotency pair and canonical intent
  return existing result on exact retry; reject conflicting reuse
  verify exact representation/source revision and declared dependencies
  insert immutable representation facts if PENDING creation is part of this operation
  insert expectation before payload publication
  insert payload with observed length
  insert measurement against expectation
  update representation_current_state to READY/usable or withheld
  insert one semantic transition and representation/integrity typed effects
  validate helper-owned invariants
COMMIT
```

Expectation is never synthesized from bytes already accepted in storage as its own expected truth. `representation_current_state` selects one measurement; integrity status derives from that measurement and expectation rather than becoming a second independently writable authority.

## 6. Connection qualification and transaction ownership

Every connection is created, owned, and used within one execution thread for a complete substrate operation. It never crosses threads. Initial policy remains `check_same_thread=True`; async callers dispatch the whole synchronous operation in one worker invocation. Short-lived versus thread-local reuse is tuning; no general pool is required.

Qualification is one controlled path. While no transaction or savepoint is active it executes `PRAGMA foreign_keys = ON`, immediately reads `PRAGMA foreign_keys`, and requires `1` before any semantic transaction. It also positively probes JSON functions, then verifies runtime admissibility/WAL-reset fix, schema compatibility, actual `journal_mode = WAL`, `synchronous >= FULL` for semantic writers, busy policy, core-role/deployment-selector agreement, and the applicable structural-health gate.

One outer `SubstrateTx` helper owns `BEGIN IMMEDIATE`, validation, `COMMIT`, and `ROLLBACK`. Repositories receive only `SubstrateTx`; no subsystem receives a commit-capable raw connection. Nested semantic operations share that context. Savepoints are internal implementation details and never semantic commit boundaries.

## 7. Storage API and module boundary

Freeze a thin, explicit TORMENT-owned persistence layer with no ORM:

```text
ids / canonical intent
runtime qualification
connection
schema/bootstrap
transaction ownership
object repository
relationship repository
operation/transition repository
representation repository
integrity/reconciliation repository
legacy admission
backup
migration/cutover
public substrate facade
```

The facade owns current/exact revision reads, object and relationship transitions, operation retry resolution, multi-carrier transitions, representation pending/ready/failure, reconciliation, semantic-history reads, legacy admission, consistent backup, and close. Exact filenames may evolve without widening the boundary.

Schema maintenance and cutover maintenance use `maintenance_events`, not normal semantic operations. Startup never performs writable automatic migration. Explicit maintenance drains writers; where SQLite permits, schema DDL/data work and its maintenance-ledger record share one maintenance transaction after a SQLite-consistent backup. Older supported-but-unupgraded schemas are read-only or refused; newer/unknown/incompatible schemas refuse writable startup.

The backup API exposes a SQLite-consistent snapshot operation. It never treats copying a live main `.db` alone as a valid WAL backup.

## 8. Offline cutover fence and migration tooling

Migration tooling has separate snapshot, inventory, admission, verification, and cutover responsibilities. It is rerunnable against stable snapshot/artifact/record identities without duplicating admitted output. Paths are observed locators, not evidence identities.

The durable deployment fence has three states:

```text
LEGACY_ACTIVE
CUTOVER_PENDING(new_core_id)
NATIVE_ACTIVE(new_core_id)
```

Before activation, stop legacy writes and persist `CUTOVER_PENDING`. During that state, legacy writes and new-core normal semantic writes are forbidden; startup allows maintenance/recovery only and never guesses the authority. Complete admission and verification, activate the new core through maintenance state, then atomically set the external deployment selector to `NATIVE_ACTIVE(new_core_id)`.

Normal startup requires selector `NATIVE_ACTIVE(core_id)` and matching core metadata `ACTIVE_CORE`; disagreement fails closed. Immediately after native semantic writes resume, legacy storage is evidence only. There is no dual-write, automatic rollback, or automatic reverse migration.

## 9. Bounded qualification suite

Use approximately thirteen scenario groups, exercising every helper-owned invariant:

1. runtime/startup gates: eligible WAL runtime, JSON probe, verified foreign keys, schema compatibility, and selector/core-role agreement;
2. same-idempotency retry and conflicting reuse;
3. durable rejection XOR transition;
4. creation allocation retry and output linkage;
5. stale predecessor, same-carrier ownership, and ordinal/predecessor inconsistency rejection;
6. ordinary successor fork rejection and current-pointer completeness;
7. relationship identity/exact-revision endpoint binding;
8. multi-carrier atomicity and restart after acknowledged commit;
9. representation PENDING, READY retry, READY-precondition rejection, and failure;
10. integrity mismatch and reconciliation resolution;
11. immutable aggregate closure;
12. legacy snapshot/artifact identity, namespaced aliases, admission transition, quarantine, and rerun idempotency;
13. writer contention plus cutover-pending crash, activation, and old-store evidence-only behavior.

This is intentionally a bounded qualification suite, not a combinatorial fault campaign.

## 10. Phase 7 implementation sequence

1. **7A:** pin eligible SQLite runtime; package shell; UUID/canonical-intent codecs; runtime qualification; connection discipline.
2. **7B:** corrected DDL; bootstrap; compatibility checks; maintenance metadata; startup gates.
3. **7C:** `SubstrateTx`; operations; transitions/effects; object/revision path.
4. **7D:** relationships, revisions, and endpoints.
5. **7E:** representations, payloads, dependencies, integrity, and reconciliation.
6. **7F:** legacy snapshot, inventory, admission, and quarantine tooling.
7. **7G:** compatibility persistence facade adapting current callers without inheriting JSONL ontology.
8. **7H:** offline migration/cutover controller with durable fence.
9. **7I:** bounded formal qualification and cutover rehearsal.

The first slice must not wire current runtime to a half-built core. No slice authorizes dual-write.

## 11. Deferred and non-scope

Deferred: exact UUIDv4 helper implementation details, eligible SQLite package pin, integrity-algorithm registry values, final indexes/query plans, busy timeout, checkpoint/backup schedule, payload optimization, deployment-manifest path/encoding, and production migration commands.

Out of scope: production code/tests, database creation, SQLite upgrade, migration execution, benchmarks, vector-search selection, Character-runtime redesign, autonomy, and reopening Phases 0–5. No contradiction with the frozen phases was found.

## 12. Freeze verdict

```text
MEMORY_SUBSTRATE_PHASE_6_ENGINEERING_BLUEPRINT_FROZEN = YES
EXACT_SQLITE_DDL_BLUEPRINT_FROZEN = YES
NATIVE_ID_STORAGE_16_BYTE_BLOB = YES
NATIVE_ID_GENERATION_UUIDV4 = YES
UUIDV7_REQUIRED = NO
IDEMPOTENCY_IDENTITY_SEPARATE_FROM_OPERATION_ID = YES
STORAGE_API_BLUEPRINT_FROZEN = YES
CUTOVER_FENCE_MODEL_FROZEN = YES
BOUNDED_QUALIFICATION_SUITE_FROZEN = YES
PHASE_0_1_2_3_4_5_CONTRADICTION_FOUND = NO
ADDITIONAL_REPOSITORY_ARCHAEOLOGY_REQUIRED = NO
PRE_FREEZE_IMPLEMENTATION_PROTOTYPE_REQUIRED = NO
CURRENT_SQLITE_3_51_2_USED_FOR_NEW_CORE = NO
PRODUCTION_CODE_CHANGED = NO
TEST_CODE_CHANGED = NO
MEMORY_SUBSTRATE_PHASE_7_NEXT = YES
```
