from __future__ import annotations
from pathlib import Path
import pytest
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id,native_id_to_bytes
from torment_service.substrate.objects import NativeObjectService,ObjectState
from torment_service.substrate.representations import NativeRepresentationService,RepresentationRequest
from torment_service.substrate.schema import create_schema
from torment_service.substrate.errors import SubstrateIdempotencyConflict
from torment_service.substrate.relationships import NativeRelationshipService,RelationshipState,Endpoint
def u():return generate_native_id()
def test_pending_representation_retry_and_exact_source(tmp_path:Path):
 q=open_temporary_test_connection(tmp_path/"r.db")
 try:
  c=q.connection;create_schema(c);ns,scope,idem=u(),u(),u()
  c.execute("INSERT INTO identity_namespaces VALUES (?,?,0)",(native_id_to_bytes(ns),"n"));c.execute("INSERT INTO semantic_scopes VALUES (?,?,0)",(native_id_to_bytes(scope),"s"));c.execute("INSERT INTO idempotency_namespaces VALUES (?,?)",(native_id_to_bytes(idem),"i"))
  o=NativeObjectService(c);source=o.create_object(idempotency_namespace_id=idem,idempotency_key="object",state=ObjectState(ns,scope,"NOTE","EXISTS","LIVE",True,"GOVERNED"))
  r=NativeRepresentationService(c);request=RepresentationRequest("OBJECT_REVISION",source.object_id,source.revision_id,None,None,"SYNTHETIC",1,"v1","raw")
  first=r.create_representation_pending(idempotency_namespace_id=idem,idempotency_key="representation",request=request)
  assert r.create_representation_pending(idempotency_namespace_id=idem,idempotency_key="representation",request=request)==first and first.readiness=="PENDING"
  with pytest.raises(SubstrateIdempotencyConflict):r.create_representation_pending(idempotency_namespace_id=idem,idempotency_key="representation",request=RepresentationRequest("OBJECT_REVISION",source.object_id,source.revision_id,None,None,"OTHER",1,"v1","raw"))
  assert o.get_current_object(source.object_id).revision_id==source.revision_id and c.execute("SELECT count(*) FROM representation_payloads").fetchone()[0]==0
 finally:q.close()

def test_relationship_source_dependency_guards_and_generation_uniqueness(tmp_path:Path):
 q=open_temporary_test_connection(tmp_path/"relationships.db")
 try:
  c=q.connection;create_schema(c);ns,s,idem=u(),u(),u()
  c.execute("INSERT INTO identity_namespaces VALUES (?,?,0)",(native_id_to_bytes(ns),"n"));c.execute("INSERT INTO semantic_scopes VALUES (?,?,0)",(native_id_to_bytes(s),"s"));c.execute("INSERT INTO idempotency_namespaces VALUES (?,?)",(native_id_to_bytes(idem),"i"))
  o=NativeObjectService(c);a=o.create_object(idempotency_namespace_id=idem,idempotency_key="a",state=ObjectState(ns,s,"N","EXISTS","LIVE",True,"G"));b=o.create_object(idempotency_namespace_id=idem,idempotency_key="b",state=ObjectState(ns,s,"N","EXISTS","LIVE",True,"G"))
  rel=NativeRelationshipService(c).create_relationship(idempotency_namespace_id=idem,idempotency_key="r",state=RelationshipState(ns,s,"R","EXISTS","LIVE",True,"G",endpoints=(Endpoint(0,"X",s,a.object_id),Endpoint(1,"X",s,b.object_id))))
  service=NativeRepresentationService(c);one=RepresentationRequest("RELATIONSHIP_REVISION",None,None,rel.relationship_id,rel.revision_id,"EMBEDDING",1,"v","raw")
  first=service.create_representation_pending(idempotency_namespace_id=idem,idempotency_key="one",request=one);assert service.get_representation_metadata(first.representation_id).source_kind=="RELATIONSHIP_REVISION"
  with pytest.raises(Exception):service.create_representation_pending(idempotency_namespace_id=idem,idempotency_key="different-operation",request=one)
  dep=service.create_representation_pending(idempotency_namespace_id=idem,idempotency_key="dep",request=RepresentationRequest("OBJECT_REVISION",a.object_id,a.revision_id,None,None,"DERIVED",1,"v","raw",dependencies=(first.representation_id,)))
  with pytest.raises(Exception):c.execute("DELETE FROM representation_dependencies WHERE representation_id=?",(native_id_to_bytes(dep.representation_id),))
  with pytest.raises(Exception):service.create_representation_pending(idempotency_namespace_id=idem,idempotency_key="missing",request=RepresentationRequest("OBJECT_REVISION",b.object_id,b.revision_id,None,None,"X",1,"v","raw",dependencies=(u(),)))
  with pytest.raises(Exception):service.create_representation_pending(idempotency_namespace_id=idem,idempotency_key="duplicate",request=RepresentationRequest("OBJECT_REVISION",b.object_id,b.revision_id,None,None,"Y",1,"v","raw",dependencies=(first.representation_id,first.representation_id)))
  self_id=u()
  with pytest.raises(Exception):service.create_representation_pending(idempotency_namespace_id=idem,idempotency_key="self",request=RepresentationRequest("OBJECT_REVISION",b.object_id,b.revision_id,None,None,"Z",1,"v","raw",representation_id=self_id,dependencies=(self_id,)))
 finally:q.close()
