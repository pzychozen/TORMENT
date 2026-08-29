"""Phase 7C native object semantic transaction path; no runtime integration."""
from __future__ import annotations
from dataclasses import dataclass
import sqlite3
from typing import Any
from uuid import UUID
from .canonical_intent import canonical_intent_text
from .errors import SubstrateIdempotencyConflict, SubstrateInvariantViolation, SubstrateObjectNotFound, SubstrateRevisionConflict
from .ids import generate_native_id, native_id_to_bytes
from .schema import open_schema

@dataclass(frozen=True)
class ObjectState:
    identity_namespace_id: UUID; semantic_scope_id: UUID; object_kind: str; existence_state: str; lifecycle_state: str; lifecycle_authoritative: bool; governance_state: str; authority_category: str = "NOT_APPLICABLE"; payload: str | dict[str, Any] | None = None; payload_format: str = "NONE"; provenance_id: UUID | None = None
@dataclass(frozen=True)
class ObjectResult:
    object_id: UUID; revision_id: UUID; transition_id: UUID; operation_id: UUID
@dataclass(frozen=True)
class ObjectRevisionView:
    object_id: UUID; revision_id: UUID; ordinal: int; scope_id: UUID; existence_state: str; lifecycle_state: str; governance_state: str; authority_category: str; payload_format: str; payload: str | None

class SubstrateTx:
    """The sole BEGIN IMMEDIATE/COMMIT/ROLLBACK owner for one semantic operation."""

    def __init__(self, connection: sqlite3.Connection, operation_id: bytes) -> None:
        self.connection = connection
        self.operation_id = operation_id
        self.transitions: list[bytes] = []
        self.published: list[tuple[bytes, bytes, int]] = []
        self.relationship_published: list[tuple[bytes, bytes, int]] = []
        self.representation_published: list[bytes] = []
        self.representation_ready: list[tuple[bytes, bytes, bytes]] = []
        self.representation_failed: list[tuple[bytes, bytes | None]] = []
        self.representation_verified: list[tuple[bytes, bytes, bytes, str, str]] = []
        self.reconciliation_published: list[tuple[bytes, bytes, int, bytes | None, str | None]] = []
        self.legacy_admitted: list[tuple[bytes, bytes, int, bytes, bytes, bytes, bytes, bytes, str]] = []

    def execute(self, sql: str, parameters: tuple[object,...]=()) -> sqlite3.Cursor: return self.connection.execute(sql,parameters)

    def validate(self) -> None:
        for oid,rid,ordinal in self.published:
            if self.execute("SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",(oid,)).fetchone() != (rid,ordinal): raise SubstrateInvariantViolation("H1 current pointer is incomplete or cross-carrier")
            if self.execute("SELECT 1 FROM operation_outputs WHERE operation_id=? AND output_kind='OBJECT' AND object_id=? AND object_revision_id=? AND object_revision_ordinal=?",(self.operation_id,oid,rid,ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H8 output does not match publication")
            if self.execute("SELECT 1 FROM object_revision_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.object_id=? AND e.object_revision_id=? AND e.object_revision_ordinal=?",(self.operation_id,oid,rid,ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H8 output is not published")
        for tid in self.transitions:
            if self.execute("SELECT 1 FROM object_revision_effects WHERE transition_id=? UNION SELECT 1 FROM relationship_revision_effects WHERE transition_id=? UNION SELECT 1 FROM representation_state_effects WHERE transition_id=? UNION SELECT 1 FROM reconciliation_state_effects WHERE transition_id=? UNION SELECT 1 FROM legacy_admission_effects WHERE transition_id=?",(tid,tid,tid,tid,tid)).fetchone() is None: raise SubstrateInvariantViolation("H2 transition has no typed effect")
        for rid,revision,ordinal in self.relationship_published:
            if self.execute("SELECT current_revision_id,current_revision_ordinal FROM relationships WHERE relationship_id=?",(rid,)).fetchone() != (revision,ordinal): raise SubstrateInvariantViolation("H1 relationship current pointer is incomplete")
            if self.execute("SELECT 1 FROM relationship_revision_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.relationship_id=? AND e.relationship_revision_id=? AND e.relationship_revision_ordinal=?",(self.operation_id,rid,revision,ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H2 relationship effect is missing")
            if self.execute("SELECT 1 FROM operation_outputs WHERE operation_id=? AND output_kind='RELATIONSHIP' AND relationship_id=? AND relationship_revision_id=? AND relationship_revision_ordinal=?",(self.operation_id,rid,revision,ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H8 relationship output does not match publication")
        for representation_id in self.representation_published:
            if self.execute("SELECT 1 FROM representation_state_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.representation_id=?",(self.operation_id,representation_id)).fetchone() is None or self.execute("SELECT 1 FROM operation_outputs WHERE operation_id=? AND output_kind='REPRESENTATION' AND representation_id=?",(self.operation_id,representation_id)).fetchone() is None: raise SubstrateInvariantViolation("H8 representation output does not match publication")
        for representation_id, expectation_id, measurement_id in self.representation_ready:
            state = self.execute("SELECT readiness,operational_disposition,selected_integrity_measurement_id FROM representation_current_state WHERE representation_id=?",(representation_id,)).fetchone()
            if state != ("READY","USABLE",measurement_id): raise SubstrateInvariantViolation("H4 representation is not published as ready and usable")
            payload = self.execute("SELECT p.payload_bytes,p.observed_payload_byte_length,r.expected_payload_byte_length FROM representation_payloads p JOIN representations r USING(representation_id) WHERE p.representation_id=?",(representation_id,)).fetchone()
            if payload is None or payload[1] != len(payload[0]) or (payload[2] is not None and payload[2] != payload[1]): raise SubstrateInvariantViolation("H4 representation payload is not exact")
            expectation = self.execute("SELECT expected_value FROM integrity_expectations WHERE expectation_id=? AND subject_kind='REPRESENTATION' AND representation_id=?",(expectation_id,representation_id)).fetchone()
            measurement = self.execute("SELECT expectation_id,result,observed_value FROM integrity_measurements WHERE measurement_id=?",(measurement_id,)).fetchone()
            if expectation is None or measurement != (expectation_id,"MATCH",expectation[0]): raise SubstrateInvariantViolation("H4 representation integrity measurement is not acceptable")
            if self.execute("SELECT 1 FROM representation_dependencies d JOIN representation_current_state s ON s.representation_id=d.dependency_representation_id WHERE d.representation_id=? AND (s.readiness!='READY' OR s.operational_disposition!='USABLE')",(representation_id,)).fetchone() is not None: raise SubstrateInvariantViolation("H4 representation dependencies are not ready")
            if self.execute("SELECT 1 FROM representation_state_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.representation_id=? AND e.readiness='READY' AND e.operational_disposition='USABLE' AND e.selected_measurement_id=?",(self.operation_id,representation_id,measurement_id)).fetchone() is None: raise SubstrateInvariantViolation("H4 representation readiness effect is missing")
            if self.execute("SELECT 1 FROM integrity_measurement_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.measurement_id=?",(self.operation_id,measurement_id)).fetchone() is None: raise SubstrateInvariantViolation("H4 integrity measurement effect is missing")
            if self.execute("SELECT 1 FROM operation_outputs o JOIN semantic_transitions t ON t.operation_id=o.operation_id JOIN representation_state_effects e ON e.transition_id=t.transition_id WHERE o.operation_id=? AND o.output_kind='REPRESENTATION' AND o.output_role='REPRESENTATION_READY' AND o.representation_id=? AND e.representation_id=? AND e.readiness='READY'",(self.operation_id,representation_id,representation_id)).fetchone() is None: raise SubstrateInvariantViolation("H8 ready representation output does not match publication")
        for representation_id, measurement_id in self.representation_failed:
            state = self.execute("SELECT readiness,operational_disposition,selected_integrity_measurement_id FROM representation_current_state WHERE representation_id=?",(representation_id,)).fetchone()
            if state != ("FAILED","WITHHELD",measurement_id): raise SubstrateInvariantViolation("failed representation state is incomplete")
            if self.execute("SELECT 1 FROM representation_payloads WHERE representation_id=?",(representation_id,)).fetchone() is not None: raise SubstrateInvariantViolation("failed representation must not publish payload")
            if self.execute("SELECT 1 FROM representation_state_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.representation_id=? AND e.readiness='FAILED' AND e.operational_disposition='WITHHELD' AND e.selected_measurement_id IS ?",(self.operation_id,representation_id,measurement_id)).fetchone() is None: raise SubstrateInvariantViolation("failed representation effect is missing")
            if self.execute("SELECT 1 FROM operation_outputs o JOIN semantic_transitions t ON t.operation_id=o.operation_id JOIN representation_state_effects e ON e.transition_id=t.transition_id WHERE o.operation_id=? AND o.output_kind='REPRESENTATION' AND o.output_role='REPRESENTATION_FAILED' AND o.representation_id=? AND e.representation_id=? AND e.readiness='FAILED'",(self.operation_id,representation_id,representation_id)).fetchone() is None: raise SubstrateInvariantViolation("H8 failed representation output does not match publication")
            if measurement_id is not None and self.execute("SELECT 1 FROM integrity_measurement_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.measurement_id=?",(self.operation_id,measurement_id)).fetchone() is None: raise SubstrateInvariantViolation("failed representation integrity measurement effect is missing")
        for representation_id, expectation_id, measurement_id, result, disposition in self.representation_verified:
            state = self.execute("SELECT readiness,operational_disposition,selected_integrity_measurement_id FROM representation_current_state WHERE representation_id=?",(representation_id,)).fetchone()
            if state != ("READY",disposition,measurement_id): raise SubstrateInvariantViolation("later integrity verification state is incomplete")
            measurement = self.execute("SELECT expectation_id,result FROM integrity_measurements WHERE measurement_id=?",(measurement_id,)).fetchone()
            if measurement != (expectation_id,result): raise SubstrateInvariantViolation("later integrity measurement does not match its expectation")
            if result == "MISMATCH" and disposition not in {"WITHHELD","RECONCILIATION_REQUIRED","QUARANTINED","RETAINED_EVIDENCE"}: raise SubstrateInvariantViolation("later integrity mismatch permits normal use")
            if self.execute("SELECT 1 FROM representation_state_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.representation_id=? AND e.readiness='READY' AND e.operational_disposition=? AND e.selected_measurement_id=?",(self.operation_id,representation_id,disposition,measurement_id)).fetchone() is None: raise SubstrateInvariantViolation("later integrity representation effect is missing")
            if self.execute("SELECT 1 FROM integrity_measurement_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.measurement_id=?",(self.operation_id,measurement_id)).fetchone() is None: raise SubstrateInvariantViolation("later integrity measurement effect is missing")
            if self.execute("SELECT 1 FROM operation_outputs o JOIN semantic_transitions t ON t.operation_id=o.operation_id JOIN representation_state_effects e ON e.transition_id=t.transition_id WHERE o.operation_id=? AND o.output_kind='REPRESENTATION' AND o.output_role='REPRESENTATION_INTEGRITY_VERIFIED' AND o.representation_id=? AND e.representation_id=? AND e.selected_measurement_id=?",(self.operation_id,representation_id,representation_id,measurement_id)).fetchone() is None: raise SubstrateInvariantViolation("H8 later integrity output does not match publication")
        for case_id, state_id, state_ordinal, representation_id, disposition in self.reconciliation_published:
            current = self.execute("SELECT current_state_id,current_state_ordinal FROM reconciliation_cases WHERE reconciliation_case_id=?",(case_id,)).fetchone()
            if current != (state_id,state_ordinal): raise SubstrateInvariantViolation("H6 reconciliation current pointer is incomplete or stale")
            if self.execute("SELECT 1 FROM reconciliation_case_states WHERE reconciliation_case_id=? AND reconciliation_state_id=? AND state_ordinal=?",(case_id,state_id,state_ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H6 reconciliation current pointer crosses cases")
            if self.execute("SELECT 1 FROM reconciliation_state_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.reconciliation_case_id=? AND e.reconciliation_state_id=? AND e.reconciliation_state_ordinal=?",(self.operation_id,case_id,state_id,state_ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H2 reconciliation state effect is missing")
            if self.execute("SELECT 1 FROM operation_outputs WHERE operation_id=? AND output_kind='RECONCILIATION_CASE' AND reconciliation_case_id=? AND reconciliation_state_id=? AND reconciliation_state_ordinal=?",(self.operation_id,case_id,state_id,state_ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H8 reconciliation output does not match publication")
            if representation_id is not None and disposition is not None and self.execute("SELECT 1 FROM representation_state_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.representation_id=? AND e.operational_disposition=?",(self.operation_id,representation_id,disposition)).fetchone() is None: raise SubstrateInvariantViolation("H2 reconciliation representation effect is missing")
        for case_id,state_id,state_ordinal in self.execute("SELECT e.reconciliation_case_id,e.reconciliation_state_id,e.reconciliation_state_ordinal FROM reconciliation_state_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=?",(self.operation_id,)).fetchall():
            if self.execute("SELECT current_state_id,current_state_ordinal FROM reconciliation_cases WHERE reconciliation_case_id=?",(case_id,)).fetchone() != (state_id,state_ordinal): raise SubstrateInvariantViolation("H6 reconciliation effect does not publish the current state")
        for object_id,revision_id,ordinal,admission_record_id,transition_id,snapshot_id,artifact_id,artifact_record_id,alias_value in self.legacy_admitted:
            transition = self.execute("SELECT operation_id,transition_kind,origin_kind FROM semantic_transitions WHERE transition_id=?",(transition_id,)).fetchone()
            if transition != (self.operation_id,"LEGACY_OBJECT_ADMISSION","LEGACY_ADMISSION"): raise SubstrateInvariantViolation("H7 imported state is not published through a legacy admission transition")
            if self.execute("SELECT creating_transition_id,current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",(object_id,)).fetchone() != (transition_id,revision_id,ordinal): raise SubstrateInvariantViolation("H7 admitted object current publication is incomplete")
            if self.execute("SELECT lineage_kind,predecessor_revision_id,predecessor_revision_ordinal FROM object_revisions WHERE object_id=? AND object_revision_id=? AND revision_ordinal=?",(object_id,revision_id,ordinal)).fetchone() != ("LEGACY_PREDECESSOR_UNKNOWN",None,None): raise SubstrateInvariantViolation("H7 imported revision lineage is not legacy predecessor unknown")
            if self.execute("SELECT 1 FROM object_revision_effects WHERE transition_id=? AND object_id=? AND object_revision_id=? AND object_revision_ordinal=?",(transition_id,object_id,revision_id,ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H2 legacy admission object revision effect is missing")
            if self.execute("SELECT 1 FROM legacy_admission_effects WHERE transition_id=? AND admission_record_id=?",(transition_id,admission_record_id)).fetchone() is None: raise SubstrateInvariantViolation("H2 legacy admission effect is missing")
            if self.execute("SELECT 1 FROM legacy_admission_records r JOIN legacy_admission_batches b USING(admission_batch_id) JOIN legacy_artifact_records ar USING(legacy_artifact_record_id) WHERE r.admission_record_id=? AND r.admission_status='ADMITTED' AND b.legacy_snapshot_id=? AND ar.legacy_artifact_id=? AND ar.legacy_artifact_record_id=?",(admission_record_id,snapshot_id,artifact_id,artifact_record_id)).fetchone() is None: raise SubstrateInvariantViolation("H7 admission record evidence linkage is incomplete")
            if self.execute("SELECT 1 FROM legacy_object_aliases WHERE legacy_source_namespace_id=(SELECT legacy_source_namespace_id FROM legacy_snapshots WHERE legacy_snapshot_id=?) AND alias_kind='EID' AND alias_value=? AND object_id=?",(snapshot_id,alias_value,object_id)).fetchone() is None: raise SubstrateInvariantViolation("H8 legacy alias does not match admitted object")
            if self.execute("SELECT 1 FROM operation_outputs o JOIN object_revision_effects e ON e.transition_id=? WHERE o.operation_id=? AND o.output_kind='OBJECT' AND o.output_role='LEGACY_OBJECT_ADMISSION' AND o.object_id=? AND o.object_revision_id=? AND o.object_revision_ordinal=? AND e.object_id=o.object_id AND e.object_revision_id=o.object_revision_id AND e.object_revision_ordinal=o.object_revision_ordinal",(transition_id,self.operation_id,object_id,revision_id,ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H8 legacy admission output does not match publication")
        if self.execute("SELECT 1 FROM semantic_transitions t JOIN operation_rejections r ON r.operation_id=t.operation_id WHERE t.operation_id=?",(self.operation_id,)).fetchone() is not None: raise SubstrateInvariantViolation("H3 operation has transition and durable rejection")

class NativeObjectService:
    def __init__(self, connection: sqlite3.Connection) -> None: open_schema(connection); self._connection=connection
    def create_object(self, *, idempotency_namespace_id: UUID, idempotency_key: str, state: ObjectState, object_id: UUID|None=None) -> ObjectResult:
        return self._execute(idempotency_namespace_id,idempotency_key,"CREATE_OBJECT",self._intent("CREATE_OBJECT",state,object_id,None),lambda tx:self._create(tx,state,object_id))
    def transition_object(self, *, idempotency_namespace_id: UUID, idempotency_key: str, object_id: UUID, expected_revision_id: UUID, state: ObjectState) -> ObjectResult:
        return self._execute(idempotency_namespace_id,idempotency_key,"TRANSITION_OBJECT",self._intent("TRANSITION_OBJECT",state,object_id,expected_revision_id),lambda tx:self._successor(tx,object_id,expected_revision_id,state))
    def get_current_object(self, object_id: UUID) -> ObjectRevisionView:
        return self._read("SELECT r.object_id,r.object_revision_id,r.revision_ordinal,r.effective_semantic_scope_id,r.existence_state,r.lifecycle_state,r.governance_state,r.authority_category,r.payload_format,r.payload_text FROM objects o JOIN object_revisions r ON r.object_revision_id=o.current_revision_id WHERE o.object_id=?",object_id)
    def get_object_revision(self, revision_id: UUID) -> ObjectRevisionView:
        return self._read("SELECT object_id,object_revision_id,revision_ordinal,effective_semantic_scope_id,existence_state,lifecycle_state,governance_state,authority_category,payload_format,payload_text FROM object_revisions WHERE object_revision_id=?",revision_id)
    def _read(self,sql:str,value:UUID)->ObjectRevisionView:
        row=self._connection.execute(sql,(_blob(value),)).fetchone()
        if row is None: raise SubstrateObjectNotFound("native object was not found")
        return ObjectRevisionView(UUID(bytes=row[0]),UUID(bytes=row[1]),row[2],UUID(bytes=row[3]),*row[4:])
    def _execute(self, namespace:UUID,key:str,kind:str,intent:str,mutate:Any)->ObjectResult:
        return execute_semantic(self._connection,namespace,key,kind,intent,self._result,mutate)

    def _create(self,tx:SubstrateTx,state:ObjectState,requested:UUID|None)->ObjectResult:
        oid=_blob(requested) if requested else _new(); rid,tid=_new(),_new(); self._state(state)
        tx.execute("INSERT INTO objects(object_id,identity_namespace_id,object_kind,created_at_ns) VALUES (?,?,?,0)",(oid,_blob(state.identity_namespace_id),state.object_kind)); self._revision(tx,rid,oid,1,"NATIVE_CREATION",None,None,state); self._publish(tx,oid,rid,1,tid); return _res(oid,rid,tid,tx.operation_id)
    def _successor(self,tx:SubstrateTx,object_id:UUID,expected:UUID,state:ObjectState)->ObjectResult:
        oid,old=_blob(object_id),_blob(expected); current=tx.execute("SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",(oid,)).fetchone()
        if current is None: raise SubstrateObjectNotFound("native object was not found")
        if current[0]!=old: raise SubstrateRevisionConflict("expected predecessor is not current")
        rid,tid,ordinal=_new(),_new(),current[1]+1; self._state(state); self._revision(tx,rid,oid,ordinal,"NATIVE_ORDINARY",old,current[1],state); self._publish(tx,oid,rid,ordinal,tid); return _res(oid,rid,tid,tx.operation_id)
    def _revision(self,tx:SubstrateTx,rid:bytes,oid:bytes,ordinal:int,lineage:str,pred:bytes|None,pred_ord:int|None,state:ObjectState)->None:
        fmt,text=_payload(state); tx.execute("INSERT INTO object_revisions(object_revision_id,object_id,revision_ordinal,lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,governance_state,authority_category,provenance_id,payload_format,payload_text,created_at_ns) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",(rid,oid,ordinal,lineage,pred,pred_ord,_blob(state.semantic_scope_id),state.existence_state,state.lifecycle_state,int(state.lifecycle_authoritative),state.governance_state,state.authority_category,_blob(state.provenance_id) if state.provenance_id else None,fmt,text))
    def _publish(self,tx:SubstrateTx,oid:bytes,rid:bytes,ordinal:int,tid:bytes)->None:
        tx.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",(tid,tx.operation_id,"OBJECT_REVISION","NATIVE")); tx.execute("INSERT INTO object_revision_effects VALUES (?,?,?,?)",(tid,oid,rid,ordinal)); tx.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,?,?,?,?)",(tx.operation_id,0,"OBJECT","OBJECT",oid,rid,ordinal)); tx.execute("UPDATE objects SET current_revision_id=?,current_revision_ordinal=? WHERE object_id=?",(rid,ordinal,oid)); tx.transitions.append(tid); tx.published.append((oid,rid,ordinal))
    @staticmethod
    def _state(state:ObjectState)->None:_payload(state)
    @staticmethod
    def _intent(kind:str,state:ObjectState,oid:UUID|None,expected:UUID|None)->str:return canonical_intent_text({"kind":kind,"object_id":str(oid) if oid else None,"expected_revision_id":str(expected) if expected else None,"identity_namespace_id":str(state.identity_namespace_id),"semantic_scope_id":str(state.semantic_scope_id),"object_kind":state.object_kind,"existence_state":state.existence_state,"lifecycle_state":state.lifecycle_state,"lifecycle_authoritative":state.lifecycle_authoritative,"governance_state":state.governance_state,"authority_category":state.authority_category,"payload":state.payload,"payload_format":state.payload_format,"provenance_id":str(state.provenance_id) if state.provenance_id else None})
    def _result(self,op:bytes)->ObjectResult|None:
        row=self._connection.execute("SELECT o.object_id,o.object_revision_id,t.transition_id,t.operation_id FROM operation_outputs o JOIN semantic_transitions t ON t.operation_id=o.operation_id WHERE o.operation_id=? AND o.output_kind='OBJECT' ORDER BY o.output_ordinal LIMIT 1",(op,)).fetchone(); return _res(*row) if row else None
def execute_semantic(connection:sqlite3.Connection,namespace:UUID,key:str,kind:str,intent:str,resolver:Any,mutate:Any)->Any:
    if not key: raise ValueError("idempotency key is required")
    connection.execute("BEGIN IMMEDIATE")
    try:
        row=connection.execute("SELECT operation_id,canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",(_blob(namespace),key)).fetchone()
        if row:
            if row[1].encode()!=intent.encode(): raise SubstrateIdempotencyConflict("idempotency intent differs")
            prior=resolver(row[0])
            if prior: connection.execute("COMMIT"); return prior
            op=row[0]
        else:
            op=_new(); connection.execute("INSERT INTO operations VALUES (?,?,?,?,?,?,0)",(op,_blob(namespace),key,kind,"TMS-INTENT-1",intent))
        tx=SubstrateTx(connection,op); result=mutate(tx); tx.validate(); connection.execute("COMMIT"); return result
    except Exception:
        if connection.in_transaction:connection.execute("ROLLBACK")
        raise
def _payload(state:ObjectState)->tuple[str,str|None]:
    if state.payload is None and state.payload_format=="NONE":return "NONE",None
    if state.payload_format=="TEXT" and isinstance(state.payload,str):return "TEXT",state.payload
    if state.payload_format=="JSON" and isinstance(state.payload,dict):return "JSON",canonical_intent_text(state.payload)
    raise ValueError("payload does not match frozen format")
def _blob(v:UUID)->bytes:return native_id_to_bytes(v)
def _new()->bytes:return native_id_to_bytes(generate_native_id())
def _res(oid:bytes,rid:bytes,tid:bytes,op:bytes)->ObjectResult:return ObjectResult(UUID(bytes=oid),UUID(bytes=rid),UUID(bytes=tid),UUID(bytes=op))
