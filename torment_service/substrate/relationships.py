"""Phase 7D first-class relationship semantic path, sharing 7C transaction ownership."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from uuid import UUID
import sqlite3
from .canonical_intent import canonical_intent_text
from .errors import SubstrateObjectNotFound,SubstrateRevisionConflict
from .ids import generate_native_id,native_id_to_bytes
from .objects import SubstrateTx,execute_semantic,ObjectState
from .schema import open_schema

@dataclass(frozen=True)
class Endpoint:
    ordinal:int; role:str; semantic_scope_id:UUID; object_id:UUID; binding_mode:str="IDENTITY"; object_revision_id:UUID|None=None; object_revision_ordinal:int|None=None
@dataclass(frozen=True)
class RelationshipState:
    identity_namespace_id:UUID; semantic_scope_id:UUID; relationship_kind:str; existence_state:str; lifecycle_state:str; lifecycle_authoritative:bool; governance_state:str; authority_category:str="NOT_APPLICABLE"; endpoints:tuple[Endpoint,...]=(); payload:str|dict[str,Any]|None=None; payload_format:str="NONE"
@dataclass(frozen=True)
class RelationshipResult:
    relationship_id:UUID; revision_id:UUID; transition_id:UUID; operation_id:UUID
@dataclass(frozen=True)
class RelationshipView:
    relationship_id:UUID; revision_id:UUID; ordinal:int; scope_id:UUID; endpoints:tuple[Endpoint,...]
@dataclass(frozen=True)
class JointResult:
    object_id:UUID; object_revision_id:UUID; relationship_id:UUID; relationship_revision_id:UUID; transition_id:UUID; operation_id:UUID

class NativeRelationshipService:
    def __init__(self,connection:sqlite3.Connection)->None:open_schema(connection);self._connection=connection
    def create_relationship(self,*,idempotency_namespace_id:UUID,idempotency_key:str,state:RelationshipState,relationship_id:UUID|None=None,preflight:Callable[[SubstrateTx],None]|None=None)->RelationshipResult:
        return execute_semantic(self._connection,idempotency_namespace_id,idempotency_key,"CREATE_RELATIONSHIP",self._intent("CREATE",state,relationship_id,None),self._result,lambda tx:self._create(tx,state,relationship_id,preflight))
    def transition_relationship(self,*,idempotency_namespace_id:UUID,idempotency_key:str,relationship_id:UUID,expected_revision_id:UUID,state:RelationshipState)->RelationshipResult:
        return execute_semantic(self._connection,idempotency_namespace_id,idempotency_key,"TRANSITION_RELATIONSHIP",self._intent("TRANSITION",state,relationship_id,expected_revision_id),self._result,lambda tx:self._successor(tx,relationship_id,expected_revision_id,state))
    def transition_object_and_relationship(self,*,idempotency_namespace_id:UUID,idempotency_key:str,object_id:UUID,expected_object_revision_id:UUID,object_state:ObjectState,relationship_id:UUID,expected_relationship_revision_id:UUID,relationship_state:RelationshipState,_omit_relationship_effect:bool=False)->JointResult:
        intent=canonical_intent_text({"kind":"JOINT_OBJECT_RELATIONSHIP","object_id":str(object_id),"expected_object_revision_id":str(expected_object_revision_id),"relationship_id":str(relationship_id),"expected_relationship_revision_id":str(expected_relationship_revision_id),"object_state":{"scope":str(object_state.semantic_scope_id),"payload":object_state.payload,"payload_format":object_state.payload_format},"relationship":self._intent("JOINT",relationship_state,relationship_id,expected_relationship_revision_id)})
        return execute_semantic(self._connection,idempotency_namespace_id,idempotency_key,"JOINT_OBJECT_RELATIONSHIP",intent,self._joint_result,lambda tx:self._joint(tx,object_id,expected_object_revision_id,object_state,relationship_id,expected_relationship_revision_id,relationship_state,_omit_relationship_effect))
    def get_current_relationship(self,relationship_id:UUID)->RelationshipView:
        row=self._connection.execute("SELECT r.relationship_id,r.relationship_revision_id,r.revision_ordinal,r.effective_semantic_scope_id FROM relationships h JOIN relationship_revisions r ON r.relationship_revision_id=h.current_revision_id WHERE h.relationship_id=?",(_b(relationship_id),)).fetchone()
        if not row:raise SubstrateObjectNotFound("native relationship was not found")
        return self._view(row)
    def get_relationship_revision(self,revision_id:UUID)->RelationshipView:
        row=self._connection.execute("SELECT relationship_id,relationship_revision_id,revision_ordinal,effective_semantic_scope_id FROM relationship_revisions WHERE relationship_revision_id=?",(_b(revision_id),)).fetchone()
        if not row:raise SubstrateObjectNotFound("native relationship revision was not found")
        return self._view(row)
    def _view(self,row:tuple)->RelationshipView:
        endpoints=tuple(Endpoint(r[1],r[2],UUID(bytes=r[3]),UUID(bytes=r[4]),r[5],UUID(bytes=r[6]) if r[6] else None,r[7]) for r in self._connection.execute("SELECT relationship_revision_id,endpoint_ordinal,endpoint_role,endpoint_semantic_scope_id,object_id,binding_mode,bound_object_revision_id,bound_object_revision_ordinal FROM relationship_revision_endpoints WHERE relationship_revision_id=? ORDER BY endpoint_ordinal",(row[1],)))
        return RelationshipView(UUID(bytes=row[0]),UUID(bytes=row[1]),row[2],UUID(bytes=row[3]),endpoints)
    def _create(self,tx:SubstrateTx,state:RelationshipState,requested:UUID|None,preflight:Callable[[SubstrateTx],None]|None=None)->RelationshipResult:
        if preflight:preflight(tx)
        oid=_b(requested) if requested else _new();rid,tid=_new(),_new();self._check(state,tx);tx.execute("INSERT INTO relationships(relationship_id,identity_namespace_id,relationship_kind,created_at_ns) VALUES (?,?,?,0)",(oid,_b(state.identity_namespace_id),state.relationship_kind));self._revision(tx,oid,rid,1,"NATIVE_CREATION",None,None,state);self._publish(tx,oid,rid,1,tid);return _result(oid,rid,tid,tx.operation_id)
    def _successor(self,tx:SubstrateTx,relationship_id:UUID,expected:UUID,state:RelationshipState)->RelationshipResult:
        oid,old=_b(relationship_id),_b(expected);row=tx.execute("SELECT current_revision_id,current_revision_ordinal FROM relationships WHERE relationship_id=?",(oid,)).fetchone()
        if not row:raise SubstrateObjectNotFound("native relationship was not found")
        if row[0]!=old:raise SubstrateRevisionConflict("expected relationship predecessor is not current")
        rid,tid,ordinal=_new(),_new(),row[1]+1;self._check(state,tx);self._revision(tx,oid,rid,ordinal,"NATIVE_ORDINARY",old,row[1],state);self._publish(tx,oid,rid,ordinal,tid);return _result(oid,rid,tid,tx.operation_id)
    def _check(self,state:RelationshipState,tx:SubstrateTx)->None:
        if not state.endpoints or len({e.ordinal for e in state.endpoints})!=len(state.endpoints):raise ValueError("explicit unique endpoint ordinals are required")
        for e in state.endpoints:
            if e.binding_mode not in {"IDENTITY","EXACT_REVISION"}:raise ValueError("unsupported endpoint binding")
            if tx.execute("SELECT 1 FROM objects WHERE object_id=?",(_b(e.object_id),)).fetchone() is None:raise SubstrateObjectNotFound("endpoint object was not found")
            if e.binding_mode=="IDENTITY" and (e.object_revision_id is not None or e.object_revision_ordinal is not None):raise ValueError("identity endpoint revision shape is invalid")
            if e.binding_mode=="EXACT_REVISION" and e.object_revision_id is None:raise ValueError("exact endpoint revision shape is invalid")
            if e.object_revision_ordinal is not None and (not isinstance(e.object_revision_ordinal,int) or isinstance(e.object_revision_ordinal,bool) or e.object_revision_ordinal<1):raise ValueError("endpoint revision ordinal is invalid")
            if e.object_revision_id:
                actual=tx.execute("SELECT revision_ordinal FROM object_revisions WHERE object_id=? AND object_revision_id=?",(_b(e.object_id),_b(e.object_revision_id))).fetchone()
                if actual is None:raise SubstrateRevisionConflict("endpoint revision does not belong to endpoint object")
                if e.object_revision_ordinal is not None and actual[0]!=e.object_revision_ordinal:raise SubstrateRevisionConflict("endpoint revision ordinal does not match endpoint object")
    def _revision(self,tx:SubstrateTx,oid:bytes,rid:bytes,ordinal:int,lineage:str,pred:bytes|None,predord:int|None,state:RelationshipState)->None:
        fmt,text=_payload(state);tx.execute("INSERT INTO relationship_revisions(relationship_revision_id,relationship_id,revision_ordinal,lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,governance_state,authority_category,payload_format,payload_text,created_at_ns) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",(rid,oid,ordinal,lineage,pred,predord,_b(state.semantic_scope_id),state.existence_state,state.lifecycle_state,int(state.lifecycle_authoritative),state.governance_state,state.authority_category,fmt,text))
        for e in state.endpoints:tx.execute("INSERT INTO relationship_revision_endpoints VALUES (?,?,?,?,?,?,?,?)",(rid,e.ordinal,e.role,_b(e.semantic_scope_id),_b(e.object_id),e.binding_mode,_b(e.object_revision_id) if e.object_revision_id else None,_endpoint_revision_ordinal(tx,e)))
    def _publish(self,tx:SubstrateTx,oid:bytes,rid:bytes,ordinal:int,tid:bytes)->None:
        tx.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",(tid,tx.operation_id,"RELATIONSHIP_REVISION","NATIVE"));tx.execute("INSERT INTO relationship_revision_effects VALUES (?,?,?,?)",(tid,oid,rid,ordinal));tx.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,relationship_id,relationship_revision_id,relationship_revision_ordinal) VALUES (?,?,?,?,?,?,?)",(tx.operation_id,0,"RELATIONSHIP","RELATIONSHIP",oid,rid,ordinal));tx.execute("UPDATE relationships SET current_revision_id=?,current_revision_ordinal=? WHERE relationship_id=?",(rid,ordinal,oid));tx.transitions.append(tid);tx.relationship_published.append((oid,rid,ordinal))
    def _joint(self,tx:SubstrateTx,object_id:UUID,expected_object:UUID,object_state:ObjectState,relationship_id:UUID,expected_relationship:UUID,relationship_state:RelationshipState,omit:bool)->JointResult:
        oid,old=_b(object_id),_b(expected_object); hid,hold=_b(relationship_id),_b(expected_relationship)
        object_current=tx.execute("SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",(oid,)).fetchone()
        relationship_current=tx.execute("SELECT current_revision_id,current_revision_ordinal FROM relationships WHERE relationship_id=?",(hid,)).fetchone()
        if not object_current or not relationship_current:raise SubstrateObjectNotFound("joint carrier was not found")
        if object_current[0]!=old or relationship_current[0]!=hold:raise SubstrateRevisionConflict("joint expected predecessor is not current")
        self._check(relationship_state,tx)
        object_revision,relationship_revision,transition=_new(),_new(),_new()
        fmt,text=_object_payload(object_state)
        tx.execute("INSERT INTO object_revisions(object_revision_id,object_id,revision_ordinal,lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,governance_state,authority_category,provenance_id,payload_format,payload_text,created_at_ns) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",(object_revision,oid,object_current[1]+1,"NATIVE_ORDINARY",old,object_current[1],_b(object_state.semantic_scope_id),object_state.existence_state,object_state.lifecycle_state,int(object_state.lifecycle_authoritative),object_state.governance_state,object_state.authority_category,_b(object_state.provenance_id) if object_state.provenance_id else None,fmt,text))
        self._revision(tx,hid,relationship_revision,relationship_current[1]+1,"NATIVE_ORDINARY",hold,relationship_current[1],relationship_state)
        tx.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",(transition,tx.operation_id,"JOINT_OBJECT_RELATIONSHIP","NATIVE"))
        tx.execute("INSERT INTO object_revision_effects VALUES (?,?,?,?)",(transition,oid,object_revision,object_current[1]+1))
        if not omit:tx.execute("INSERT INTO relationship_revision_effects VALUES (?,?,?,?)",(transition,hid,relationship_revision,relationship_current[1]+1))
        tx.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,?,?,?,?)",(tx.operation_id,0,"OBJECT","OBJECT",oid,object_revision,object_current[1]+1))
        tx.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,relationship_id,relationship_revision_id,relationship_revision_ordinal) VALUES (?,?,?,?,?,?,?)",(tx.operation_id,1,"RELATIONSHIP","RELATIONSHIP",hid,relationship_revision,relationship_current[1]+1))
        tx.execute("UPDATE objects SET current_revision_id=?,current_revision_ordinal=? WHERE object_id=?",(object_revision,object_current[1]+1,oid));tx.execute("UPDATE relationships SET current_revision_id=?,current_revision_ordinal=? WHERE relationship_id=?",(relationship_revision,relationship_current[1]+1,hid))
        tx.transitions.append(transition);tx.published.append((oid,object_revision,object_current[1]+1));tx.relationship_published.append((hid,relationship_revision,relationship_current[1]+1))
        return JointResult(object_id,UUID(bytes=object_revision),relationship_id,UUID(bytes=relationship_revision),UUID(bytes=transition),UUID(bytes=tx.operation_id))
    @staticmethod
    def _intent(kind:str,s:RelationshipState,oid:UUID|None,expected:UUID|None)->str:return canonical_intent_text({"kind":kind,"relationship_id":str(oid) if oid else None,"expected_revision_id":str(expected) if expected else None,"namespace":str(s.identity_namespace_id),"scope":str(s.semantic_scope_id),"relationship_kind":s.relationship_kind,"payload":s.payload,"payload_format":s.payload_format,"endpoints":[_endpoint_intent(e) for e in s.endpoints]})
    def _result(self,op:bytes)->RelationshipResult|None:
        row=self._connection.execute("SELECT relationship_id,relationship_revision_id,t.transition_id,t.operation_id FROM operation_outputs o JOIN semantic_transitions t ON t.operation_id=o.operation_id WHERE o.operation_id=? AND output_kind='RELATIONSHIP'",(op,)).fetchone();return _result(*row) if row else None
    def _joint_result(self,op:bytes)->JointResult|None:
        rows=self._connection.execute("SELECT output_kind,object_id,object_revision_id,relationship_id,relationship_revision_id,t.transition_id,t.operation_id FROM operation_outputs o JOIN semantic_transitions t ON t.operation_id=o.operation_id WHERE o.operation_id=? ORDER BY output_ordinal",(op,)).fetchall()
        if len(rows)!=2:return None
        a,b=rows
        if a[0]!="OBJECT" or b[0]!="RELATIONSHIP":return None
        return JointResult(UUID(bytes=a[1]),UUID(bytes=a[2]),UUID(bytes=b[3]),UUID(bytes=b[4]),UUID(bytes=a[5]),UUID(bytes=a[6]))
def _payload(s:RelationshipState)->tuple[str,str|None]:
    if s.payload is None and s.payload_format=="NONE":return "NONE",None
    if s.payload_format=="TEXT" and isinstance(s.payload,str):return "TEXT",s.payload
    if s.payload_format=="JSON" and isinstance(s.payload,dict):return "JSON",canonical_intent_text(s.payload)
    raise ValueError("payload does not match frozen format")
def _object_payload(s:ObjectState)->tuple[str,str|None]:
    if s.payload is None and s.payload_format=="NONE":return "NONE",None
    if s.payload_format=="TEXT" and isinstance(s.payload,str):return "TEXT",s.payload
    if s.payload_format=="JSON" and isinstance(s.payload,dict):return "JSON",canonical_intent_text(s.payload)
    raise ValueError("payload does not match frozen format")
def _b(v:UUID)->bytes:return native_id_to_bytes(v)
def _endpoint_intent(e:Endpoint)->dict[str,Any]:
    result={"ordinal":e.ordinal,"role":e.role,"scope":str(e.semantic_scope_id),"object":str(e.object_id),"binding":e.binding_mode,"revision":str(e.object_revision_id) if e.object_revision_id else None}
    if e.object_revision_ordinal is not None:result["revision_ordinal"]=e.object_revision_ordinal
    return result
def _endpoint_revision_ordinal(tx:SubstrateTx,e:Endpoint)->int|None:
    if e.binding_mode=="IDENTITY":return None
    if e.object_revision_id is None:raise ValueError("exact endpoint revision shape is invalid")
    if e.object_revision_ordinal is not None:return e.object_revision_ordinal
    row=tx.execute("SELECT revision_ordinal FROM object_revisions WHERE object_id=? AND object_revision_id=?",(_b(e.object_id),_b(e.object_revision_id))).fetchone()
    if row is None:raise SubstrateRevisionConflict("endpoint revision does not belong to endpoint object")
    return row[0]
def _new()->bytes:return native_id_to_bytes(generate_native_id())
def _result(a:bytes,b:bytes,c:bytes,d:bytes)->RelationshipResult:return RelationshipResult(UUID(bytes=a),UUID(bytes=b),UUID(bytes=c),UUID(bytes=d))
