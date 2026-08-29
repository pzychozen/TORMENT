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
    def __init__(self, connection: sqlite3.Connection, operation_id: bytes) -> None: self.connection,self.operation_id,self.transitions,self.published=connection,operation_id,[],[]
    def execute(self, sql: str, parameters: tuple[object,...]=()) -> sqlite3.Cursor: return self.connection.execute(sql,parameters)
    def validate(self) -> None:
        for oid,rid,ordinal in self.published:
            if self.execute("SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",(oid,)).fetchone() != (rid,ordinal): raise SubstrateInvariantViolation("H1 current pointer is incomplete or cross-carrier")
            if self.execute("SELECT 1 FROM operation_outputs WHERE operation_id=? AND output_kind='OBJECT' AND object_id=? AND object_revision_id=? AND object_revision_ordinal=?",(self.operation_id,oid,rid,ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H8 output does not match publication")
            if self.execute("SELECT 1 FROM object_revision_effects e JOIN semantic_transitions t ON t.transition_id=e.transition_id WHERE t.operation_id=? AND e.object_id=? AND e.object_revision_id=? AND e.object_revision_ordinal=?",(self.operation_id,oid,rid,ordinal)).fetchone() is None: raise SubstrateInvariantViolation("H8 output is not published")
        for tid in self.transitions:
            if self.execute("SELECT 1 FROM object_revision_effects WHERE transition_id=?",(tid,)).fetchone() is None: raise SubstrateInvariantViolation("H2 transition has no typed effect")
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
        if not key: raise ValueError("idempotency key is required")
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row=self._connection.execute("SELECT operation_id,canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",(_blob(namespace),key)).fetchone()
            if row:
                if row[1].encode()!=intent.encode(): raise SubstrateIdempotencyConflict("idempotency intent differs")
                prior=self._result(row[0])
                if prior: self._connection.execute("COMMIT"); return prior
                op=row[0]
            else:
                op=_new(); self._connection.execute("INSERT INTO operations VALUES (?,?,?,?,?,?,0)",(op,_blob(namespace),key,kind,"TMS-INTENT-1",intent))
            tx=SubstrateTx(self._connection,op); result=mutate(tx); tx.validate(); self._connection.execute("COMMIT"); return result
        except Exception:
            if self._connection.in_transaction:self._connection.execute("ROLLBACK")
            raise
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
def _payload(state:ObjectState)->tuple[str,str|None]:
    if state.payload is None and state.payload_format=="NONE":return "NONE",None
    if state.payload_format=="TEXT" and isinstance(state.payload,str):return "TEXT",state.payload
    if state.payload_format=="JSON" and isinstance(state.payload,dict):return "JSON",canonical_intent_text(state.payload)
    raise ValueError("payload does not match frozen format")
def _blob(v:UUID)->bytes:return native_id_to_bytes(v)
def _new()->bytes:return native_id_to_bytes(generate_native_id())
def _res(oid:bytes,rid:bytes,tid:bytes,op:bytes)->ObjectResult:return ObjectResult(UUID(bytes=oid),UUID(bytes=rid),UUID(bytes=tid),UUID(bytes=op))
