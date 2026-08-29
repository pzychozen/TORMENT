from __future__ import annotations
from pathlib import Path
import pytest
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id,native_id_to_bytes
from torment_service.substrate.objects import NativeObjectService,ObjectState
from torment_service.substrate.relationships import NativeRelationshipService,RelationshipState,Endpoint
from torment_service.substrate.schema import create_schema
from torment_service.substrate.errors import SubstrateRevisionConflict

def _u():return generate_native_id()
def _state(ns,scope,payload=None):return ObjectState(ns,scope,"NOTE","EXISTS","LIVE",True,"GOVERNED",payload=payload,payload_format="TEXT" if payload else "NONE")
def test_relationship_create_retry_binding_cross_scope_and_successor(tmp_path:Path):
 q=open_temporary_test_connection(tmp_path/"relationship.db")
 try:
  c=q.connection;create_schema(c);ns,s1,s2,idem=_u(),_u(),_u(),_u()
  c.execute("INSERT INTO identity_namespaces VALUES (?,?,0)",(native_id_to_bytes(ns),"ns"))
  for value,key in ((s1,"s1"),(s2,"s2")):c.execute("INSERT INTO semantic_scopes VALUES (?,?,0)",(native_id_to_bytes(value),key))
  c.execute("INSERT INTO idempotency_namespaces VALUES (?,?)",(native_id_to_bytes(idem),"idem"))
  o=NativeObjectService(c);a=o.create_object(idempotency_namespace_id=idem,idempotency_key="a",state=_state(ns,s1));b=o.create_object(idempotency_namespace_id=idem,idempotency_key="b",state=_state(ns,s2))
  r=NativeRelationshipService(c);state=RelationshipState(ns,s1,"GROUP","EXISTS","LIVE",True,"GOVERNED",endpoints=(Endpoint(0,"MEMBER",s1,a.object_id,"EXACT_REVISION",a.revision_id),Endpoint(1,"MEMBER",s2,b.object_id)))
  first=r.create_relationship(idempotency_namespace_id=idem,idempotency_key="rel",state=state);assert r.create_relationship(idempotency_namespace_id=idem,idempotency_key="rel",state=state)==first
  assert [e.role for e in r.get_current_relationship(first.relationship_id).endpoints]==["MEMBER","MEMBER"]
  second=r.transition_relationship(idempotency_namespace_id=idem,idempotency_key="rel2",relationship_id=first.relationship_id,expected_revision_id=first.revision_id,state=state)
  with pytest.raises(SubstrateRevisionConflict):r.transition_relationship(idempotency_namespace_id=idem,idempotency_key="stale",relationship_id=first.relationship_id,expected_revision_id=first.revision_id,state=state)
  assert r.get_relationship_revision(first.revision_id).endpoints[0].object_revision_id==a.revision_id and r.get_current_relationship(first.relationship_id).revision_id==second.revision_id
 finally:q.close()

def test_joint_operation_is_atomic_idempotent_and_requires_both_effects(tmp_path:Path):
 q=open_temporary_test_connection(tmp_path/"joint.db")
 try:
  c=q.connection;create_schema(c);ns,s,idem=_u(),_u(),_u()
  c.execute("INSERT INTO identity_namespaces VALUES (?,?,0)",(native_id_to_bytes(ns),"ns"));c.execute("INSERT INTO semantic_scopes VALUES (?,?,0)",(native_id_to_bytes(s),"s"));c.execute("INSERT INTO idempotency_namespaces VALUES (?,?)",(native_id_to_bytes(idem),"idem"))
  o=NativeObjectService(c);a=o.create_object(idempotency_namespace_id=idem,idempotency_key="a",state=_state(ns,s));b=o.create_object(idempotency_namespace_id=idem,idempotency_key="b",state=_state(ns,s));r=NativeRelationshipService(c);rs=RelationshipState(ns,s,"PAIR","EXISTS","LIVE",True,"GOVERNED",endpoints=(Endpoint(0,"MEMBER",s,a.object_id),Endpoint(1,"MEMBER",s,b.object_id)))
  base=r.create_relationship(idempotency_namespace_id=idem,idempotency_key="rel",state=rs)
  joint=r.transition_object_and_relationship(idempotency_namespace_id=idem,idempotency_key="joint",object_id=a.object_id,expected_object_revision_id=a.revision_id,object_state=_state(ns,s,"two"),relationship_id=base.relationship_id,expected_relationship_revision_id=base.revision_id,relationship_state=rs)
  assert r.transition_object_and_relationship(idempotency_namespace_id=idem,idempotency_key="joint",object_id=a.object_id,expected_object_revision_id=a.revision_id,object_state=_state(ns,s,"two"),relationship_id=base.relationship_id,expected_relationship_revision_id=base.revision_id,relationship_state=rs)==joint
  assert o.get_current_object(a.object_id).revision_id==joint.object_revision_id and r.get_current_relationship(base.relationship_id).revision_id==joint.relationship_revision_id
  with pytest.raises(SubstrateRevisionConflict):r.transition_object_and_relationship(idempotency_namespace_id=idem,idempotency_key="stale",object_id=b.object_id,expected_object_revision_id=b.revision_id,object_state=_state(ns,s),relationship_id=base.relationship_id,expected_relationship_revision_id=base.revision_id,relationship_state=rs)
  with pytest.raises(Exception):r.transition_object_and_relationship(idempotency_namespace_id=idem,idempotency_key="missing-effect",object_id=b.object_id,expected_object_revision_id=b.revision_id,object_state=_state(ns,s),relationship_id=base.relationship_id,expected_relationship_revision_id=joint.relationship_revision_id,relationship_state=rs,_omit_relationship_effect=True)
  assert c.execute("SELECT count(*) FROM semantic_transitions WHERE transition_kind='JOINT_OBJECT_RELATIONSHIP'").fetchone()[0]==1
 finally:q.close()
