"""Phase 7E1 PENDING representation metadata only; no payload or integrity path."""
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
import sqlite3
from .canonical_intent import canonical_intent_text
from .errors import SubstrateObjectNotFound,SubstrateRevisionConflict
from .ids import generate_native_id,native_id_to_bytes
from .objects import SubstrateTx,execute_semantic
from .schema import open_schema
@dataclass(frozen=True)
class RepresentationRequest:
 source_kind:str; object_id:UUID|None; object_revision_id:UUID|None; relationship_id:UUID|None; relationship_revision_id:UUID|None; representation_class:str; generation:int; derivation_contract_version:str; encoding_id:str; dtype:str|None=None; dimension:int|None=None; dependencies:tuple[UUID,...]=(); representation_id:UUID|None=None
@dataclass(frozen=True)
class RepresentationMetadata:
 representation_id:UUID; source_kind:str; representation_class:str; generation:int; readiness:str; disposition:str; dependencies:tuple[UUID,...]
class NativeRepresentationService:
 def __init__(self,c:sqlite3.Connection)->None:open_schema(c);self.c=c
 def create_representation_pending(self,*,idempotency_namespace_id:UUID,idempotency_key:str,request:RepresentationRequest)->RepresentationMetadata:
  intent=canonical_intent_text({"kind":"PENDING_REPRESENTATION","representation_id":str(request.representation_id) if request.representation_id else None,"source_kind":request.source_kind,"object_id":str(request.object_id) if request.object_id else None,"object_revision_id":str(request.object_revision_id) if request.object_revision_id else None,"relationship_id":str(request.relationship_id) if request.relationship_id else None,"relationship_revision_id":str(request.relationship_revision_id) if request.relationship_revision_id else None,"class":request.representation_class,"generation":request.generation,"contract":request.derivation_contract_version,"encoding":request.encoding_id,"dtype":request.dtype,"dimension":request.dimension,"dependencies":[str(x) for x in request.dependencies]})
  return execute_semantic(self.c,idempotency_namespace_id,idempotency_key,"CREATE_REPRESENTATION_PENDING",intent,self._result,lambda tx:self._create(tx,request))
 def get_representation_metadata(self,representation_id:UUID)->RepresentationMetadata:
  row=self.c.execute("SELECT r.representation_id,r.source_kind,r.representation_class,r.generation,s.readiness,s.operational_disposition FROM representations r JOIN representation_current_state s USING(representation_id) WHERE r.representation_id=?",(b(representation_id),)).fetchone()
  if not row:raise SubstrateObjectNotFound("representation was not found")
  deps=tuple(UUID(bytes=x[0]) for x in self.c.execute("SELECT dependency_representation_id FROM representation_dependencies WHERE representation_id=? ORDER BY dependency_representation_id",(row[0],)))
  return RepresentationMetadata(UUID(bytes=row[0]),row[1],row[2],row[3],row[4],row[5],deps)
 def _create(self,tx:SubstrateTx,r:RepresentationRequest)->RepresentationMetadata:
  rid=b(r.representation_id) if r.representation_id else new();self._check(r,tx,rid)
  if r.source_kind=="OBJECT_REVISION": tx.execute("INSERT INTO representations(representation_id,source_kind,source_object_id,source_object_revision_id,source_object_revision_ordinal,representation_class,generation,derivation_contract_version,encoding_id,dtype,dimension,created_at_ns) SELECT ?,'OBJECT_REVISION',object_id,object_revision_id,revision_ordinal,?,?,?,?,?,?,0 FROM object_revisions WHERE object_id=? AND object_revision_id=?",(rid,r.representation_class,r.generation,r.derivation_contract_version,r.encoding_id,r.dtype,r.dimension,b(r.object_id),b(r.object_revision_id)))
  else: tx.execute("INSERT INTO representations(representation_id,source_kind,source_relationship_id,source_relationship_revision_id,source_relationship_revision_ordinal,representation_class,generation,derivation_contract_version,encoding_id,dtype,dimension,created_at_ns) SELECT ?,'RELATIONSHIP_REVISION',relationship_id,relationship_revision_id,revision_ordinal,?,?,?,?,?,?,0 FROM relationship_revisions WHERE relationship_id=? AND relationship_revision_id=?",(rid,r.representation_class,r.generation,r.derivation_contract_version,r.encoding_id,r.dtype,r.dimension,b(r.relationship_id),b(r.relationship_revision_id)))
  if tx.execute("SELECT 1 FROM representations WHERE representation_id=?",(rid,)).fetchone() is None:raise SubstrateRevisionConflict("exact representation source does not exist")
  for dep in r.dependencies:tx.execute("INSERT INTO representation_dependencies VALUES (?,?,?)",(rid,b(dep),"DECLARED"))
  tx.execute("INSERT INTO representation_current_state VALUES (?,'PENDING','WITHHELD',NULL)",(rid,));tid=new();tx.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",(tid,tx.operation_id,"REPRESENTATION_PENDING","NATIVE"));tx.execute("INSERT INTO representation_state_effects VALUES (?,?,?, ?,NULL)",(tid,rid,"PENDING","WITHHELD"));tx.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,representation_id) VALUES (?,?,?,?,?)",(tx.operation_id,0,"REPRESENTATION","REPRESENTATION",rid));tx.transitions.append(tid);tx.representation_published.append(rid);return self.get_representation_metadata(UUID(bytes=rid))
 def _check(self,r:RepresentationRequest,tx:SubstrateTx,rid:bytes)->None:
  if r.source_kind not in {"OBJECT_REVISION","RELATIONSHIP_REVISION"} or r.generation<1:raise ValueError("invalid representation source or generation")
  if r.source_kind=="OBJECT_REVISION" and (not r.object_id or not r.object_revision_id or r.relationship_id or r.relationship_revision_id):raise ValueError("invalid object source shape")
  if r.source_kind=="RELATIONSHIP_REVISION" and (not r.relationship_id or not r.relationship_revision_id or r.object_id or r.object_revision_id):raise ValueError("invalid relationship source shape")
  if len(set(r.dependencies))!=len(r.dependencies):raise ValueError("duplicate dependency")
  for d in r.dependencies:
   if b(d)==rid:raise ValueError("self dependency")
   if tx.execute("SELECT 1 FROM representations WHERE representation_id=?",(b(d),)).fetchone() is None:raise SubstrateObjectNotFound("dependency representation was not found")
 def _result(self,op:bytes)->RepresentationMetadata|None:
  row=self.c.execute("SELECT representation_id FROM operation_outputs WHERE operation_id=? AND output_kind='REPRESENTATION'",(op,)).fetchone();return self.get_representation_metadata(UUID(bytes=row[0])) if row else None
def b(v:UUID)->bytes:return native_id_to_bytes(v)
def new()->bytes:return native_id_to_bytes(generate_native_id())
