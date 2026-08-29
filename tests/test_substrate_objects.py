from __future__ import annotations
import sqlite3
from pathlib import Path
import pytest
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.objects import NativeObjectService,ObjectState
from torment_service.substrate.schema import create_schema
from torment_service.substrate.errors import SubstrateIdempotencyConflict,SubstrateRevisionConflict

def _u(): return generate_native_id()
def _state(ns,scope,payload="one"): return ObjectState(ns,scope,"NOTE","EXISTS","LIVE",True,"GOVERNED",payload=payload,payload_format="TEXT")
def test_create_retry_successor_stale_and_history(tmp_path:Path):
 q=open_temporary_test_connection(tmp_path/"semantic.db")
 try:
  c=q.connection;create_schema(c);ns,scope,idem=_u(),_u(),_u()
  c.execute("INSERT INTO identity_namespaces VALUES (?,?,0)",(native_id_to_bytes(ns),"ns"));c.execute("INSERT INTO semantic_scopes VALUES (?,?,0)",(native_id_to_bytes(scope),"scope"));c.execute("INSERT INTO idempotency_namespaces VALUES (?,?)",(native_id_to_bytes(idem),"idem"))
  s=NativeObjectService(c);r1=s.create_object(idempotency_namespace_id=idem,idempotency_key="create",state=_state(ns,scope));assert s.create_object(idempotency_namespace_id=idem,idempotency_key="create",state=_state(ns,scope))==r1
  assert c.execute("SELECT count(*) FROM objects").fetchone()[0]==1 and c.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0]==1
  with pytest.raises(SubstrateIdempotencyConflict):s.create_object(idempotency_namespace_id=idem,idempotency_key="create",state=_state(ns,scope,"different"))
  r2=s.transition_object(idempotency_namespace_id=idem,idempotency_key="update",object_id=r1.object_id,expected_revision_id=r1.revision_id,state=_state(ns,scope,"two"));assert s.transition_object(idempotency_namespace_id=idem,idempotency_key="update",object_id=r1.object_id,expected_revision_id=r1.revision_id,state=_state(ns,scope,"two"))==r2
  assert s.get_current_object(r1.object_id).revision_id==r2.revision_id and s.get_object_revision(r1.revision_id).payload=="one"
  with pytest.raises(SubstrateRevisionConflict):s.transition_object(idempotency_namespace_id=idem,idempotency_key="stale",object_id=r1.object_id,expected_revision_id=r1.revision_id,state=_state(ns,scope,"three"))
  assert c.execute("PRAGMA foreign_key_check").fetchall()==[] and c.execute("SELECT count(*) FROM object_revision_effects").fetchone()[0]==2
  with pytest.raises(sqlite3.IntegrityError):c.execute("UPDATE object_revisions SET payload_text='x' WHERE object_revision_id=?",(native_id_to_bytes(r1.revision_id),))
 finally:q.close()
