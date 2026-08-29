"""Focused Phase 7G1 native-only compatibility read tests."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import pytest
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import NativeLegacyObjectAdmissionService
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.schema import create_schema

def _id(): return generate_native_id()
def _database(tmp_path: Path):
    q=open_temporary_test_connection(tmp_path/'compat.db'); create_schema(q.connection); c=q.connection
    obj,scope,idem=_id(),_id(),_id()
    c.execute('INSERT INTO identity_namespaces VALUES (?,?,0)',(native_id_to_bytes(obj),'compat-objects'))
    c.execute('INSERT INTO semantic_scopes VALUES (?,?,0)',(native_id_to_bytes(scope),'compat-scope'))
    c.execute('INSERT INTO idempotency_namespaces VALUES (?,?)',(native_id_to_bytes(idem),'compat-idempotency'))
    return q,obj,scope,idem
def _migrate(tmp_path:Path, c, obj, scope, idem, source:str, eid:int=17):
    cap=tmp_path/source; root=cap/'snapshot'; root.mkdir(parents=True)
    row={'eid':eid,'text':'R1 text','summary':'R1 summary','strength':0.7,'born_step':5,'lifecycle_state':'PAYLOAD_LIE','governance_state':'PAYLOAD_LIE','authority_category':'ACTIVE_AUTHORIZATION'}
    (root/'nodes.jsonl').write_text(json.dumps(row)+'\n',encoding='utf-8')
    mp=cap/'manifest.json'; m=create_snapshot_manifest(snapshot_root=root,manifest_path=mp,legacy_source_namespace_id=_id(),legacy_source_namespace_key=source)
    result=NativeLegacyObjectAdmissionService(c).admit_nodes_current_state(snapshot_root=root,manifest_path=mp,idempotency_namespace_id=idem,object_identity_namespace_id=obj,unknown_semantic_scope_id=scope).results[0]
    return root,mp,m,result

def test_namespaced_eid_projection_is_native_structural_and_read_only(tmp_path:Path, monkeypatch):
    q,obj,scope,idem=_database(tmp_path)
    try:
      c=q.connection; root,_mp,m,r1=_migrate(tmp_path,c,obj,scope,idem,'source-a'); f=NativeMemoryCompatibilityFacade(c)
      rep=_id(); c.execute('INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(native_id_to_bytes(rep),'OBJECT_REVISION',native_id_to_bytes(r1.object_id),native_id_to_bytes(r1.revision_id),1,None,None,None,'LEGACY_EMBEDDING_CAPTURE',1,'LEGACY_UNSPECIFIED','NUMPY_NPY','float32',3,12,0)); c.execute('INSERT INTO representation_current_state VALUES (?,?,?,NULL)',(native_id_to_bytes(rep),'UNKNOWN','RECONCILIATION_REQUIRED'))
      before=(c.execute('select count(*) from semantic_transitions').fetchone()[0],c.execute('select count(*) from operations').fetchone()[0])
      v=f.get_memory_by_eid(legacy_source_namespace_id=m.legacy_source_namespace_id,eid=17)
      assert f.resolve_memory_eid(legacy_source_namespace_id=m.legacy_source_namespace_id,eid=17)==r1.object_id
      assert f.resolve_native_memory_legacy_eid(legacy_source_namespace_id=m.legacy_source_namespace_id,native_object_id=r1.object_id)==17
      d=v.to_legacy_dict(); assert d['summary']=='R1 summary' and d['strength']==0.7 and d['born_step']==5
      assert d['lifecycle_state']=='UNKNOWN' and d['governance_state']=='UNKNOWN' and d['authority_category']=='NOT_APPLICABLE'
      assert d['representation_refs']==[{'representation_class':'LEGACY_EMBEDDING_CAPTURE','generation':1,'readiness':'UNKNOWN','operational_disposition':'RECONCILIATION_REQUIRED','usable':False}]
      assert before==(c.execute('select count(*) from semantic_transitions').fetchone()[0],c.execute('select count(*) from operations').fetchone()[0])
      moved=root.with_name('removed-after-migration'); root.rename(moved)
      monkeypatch.setattr(Path, 'open', lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError('compatibility read opened a legacy file')))
      assert f.get_memory_by_eid(legacy_source_namespace_id=m.legacy_source_namespace_id,eid=17).object_id==r1.object_id
    finally: q.close()

def test_stable_eid_follows_current_native_revision_and_exact_old_revision_remains_readable(tmp_path:Path):
    q,obj,scope,idem=_database(tmp_path)
    try:
      c=q.connection; _root,_mp,m,r1=_migrate(tmp_path,c,obj,scope,idem,'source-r1'); f=NativeMemoryCompatibilityFacade(c)
      r2=NativeObjectService(c).transition_object(idempotency_namespace_id=idem,idempotency_key='compat-r2',object_id=r1.object_id,expected_revision_id=r1.revision_id,state=ObjectState(obj,scope,'LEGACY_CORE_NODE','EXISTS','RETIRED',False,'REVIEWED','NOT_APPLICABLE',{'summary':'R2 summary','strength':0.2},'JSON'))
      current=f.get_memory_by_eid(legacy_source_namespace_id=m.legacy_source_namespace_id,eid=17)
      old=f.get_memory_revision(legacy_source_namespace_id=m.legacy_source_namespace_id,eid=17,revision_id=r1.revision_id)
      assert current.revision_id==r2.revision_id and current.summary=='R2 summary' and current.lifecycle_state=='RETIRED'
      assert old.revision_id==r1.revision_id and old.summary=='R1 summary'
      assert f.resolve_memory_eid(legacy_source_namespace_id=m.legacy_source_namespace_id,eid=17)==r1.object_id
    finally: q.close()

def test_same_eid_is_safe_across_namespaces_and_missing_or_wrong_carrier_fails_closed(tmp_path:Path):
    q,obj,scope,idem=_database(tmp_path)
    try:
      c=q.connection; _,_,a,ra=_migrate(tmp_path,c,obj,scope,idem,'source-a',7); _,_,b,rb=_migrate(tmp_path,c,obj,scope,idem,'source-b',7); f=NativeMemoryCompatibilityFacade(c)
      assert f.get_memory_by_eid(legacy_source_namespace_id=a.legacy_source_namespace_id,eid=7).object_id==ra.object_id
      assert f.get_memory_by_eid(legacy_source_namespace_id=b.legacy_source_namespace_id,eid=7).object_id==rb.object_id and ra.object_id!=rb.object_id
      count=c.execute('select count(*) from objects').fetchone()[0]
      with pytest.raises(SubstrateObjectNotFound): f.get_memory_by_eid(legacy_source_namespace_id=a.legacy_source_namespace_id,eid=999)
      assert c.execute('select count(*) from objects').fetchone()[0]==count
      nonmemory=NativeObjectService(c).create_object(idempotency_namespace_id=idem,idempotency_key='identity',state=ObjectState(obj,scope,'LEGACY_AGENT_IDENTITY','EXISTS','UNKNOWN',False,'UNKNOWN','NOT_APPLICABLE',{'x':1},'JSON'))
      c.execute('INSERT INTO legacy_object_aliases VALUES (?,?,?,?)',(native_id_to_bytes(a.legacy_source_namespace_id),'EID','8',native_id_to_bytes(nonmemory.object_id)))
      with pytest.raises(SubstrateInvariantViolation): f.get_memory_by_eid(legacy_source_namespace_id=a.legacy_source_namespace_id,eid=8)
    finally: q.close()

def test_facade_has_no_search_or_write_surface(tmp_path:Path):
    q,obj,scope,idem=_database(tmp_path)
    try:
      f=NativeMemoryCompatibilityFacade(q.connection)
      assert not hasattr(f,'search') and not hasattr(f,'spawn_memory') and not hasattr(f,'update_payload') and not hasattr(f,'flush_node')
    finally: q.close()
