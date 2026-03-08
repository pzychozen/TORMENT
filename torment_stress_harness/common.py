import os
from typing import Any, Dict, Optional
import requests

def _hdrs() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    tok = os.getenv("TORMENT_API_TOKEN", "").strip()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h

def ensure_workspace(base_url: str, workspace_id: str) -> None:
    url = f"{base_url.rstrip('/')}/workspace/create"
    try:
        r = requests.post(url, headers=_hdrs(), json={"workspace_id": workspace_id}, timeout=30)
        if r.ok or r.status_code in (400, 409):
            return
    except Exception:
        return

def ensure_agent(base_url: str, workspace_id: str, agent_id: str) -> None:
    url = f"{base_url.rstrip('/')}/agent/create"
    try:
        r = requests.post(url, headers=_hdrs(), json={"workspace_id": workspace_id, "agent_id": agent_id}, timeout=30)
        if r.ok or r.status_code in (400, 409):
            return
    except Exception:
        return

def ingest(base_url: str, workspace_id: str, agent_id: str, text: str, step: int,
           domain_id: Optional[str]=None, canon: Optional[bool]=None, extra: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
    url = f"{base_url.rstrip('/')}/agent/ingest"
    payload: Dict[str,Any] = {"workspace_id": workspace_id, "agent_id": agent_id, "text": text, "step": step}
    if domain_id is not None:
        payload["domain_id"] = domain_id
    if canon is not None:
        payload["canon"] = canon
    if extra:
        payload.update(extra)
    r = requests.post(url, headers=_hdrs(), json=payload, timeout=60)
    try:
        return r.json()
    except Exception:
        return {"ok": r.ok, "status_code": r.status_code, "text": r.text[:5000]}

def query(base_url: str, workspace_id: str, agent_id: str, q: str, top_k: int = 8,
          continuity_debug: bool = True, domain_id: Optional[str]=None, extra: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
    url = f"{base_url.rstrip('/')}/agent/query"
    payload: Dict[str,Any] = {"workspace_id": workspace_id, "agent_id": agent_id, "query": q, "top_k": top_k}
    if continuity_debug:
        payload["continuity_debug"] = True
    if domain_id is not None:
        payload["domain_id"] = domain_id
    if extra:
        payload.update(extra)
    r = requests.post(url, headers=_hdrs(), json=payload, timeout=60)
    try:
        return r.json()
    except Exception:
        return {"ok": r.ok, "status_code": r.status_code, "text": r.text[:5000]}

def health(base_url: str) -> Dict[str,Any]:
    url = f"{base_url.rstrip('/')}/health"
    r = requests.get(url, headers=_hdrs(), timeout=30)
    try:
        return r.json()
    except Exception:
        return {"ok": r.ok, "status_code": r.status_code, "text": r.text[:5000]}
