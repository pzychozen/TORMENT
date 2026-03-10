# consolidator.py
from __future__ import annotations
from typing import Dict, List
import os, json
from .memory_graph import MemoryGraph

def build_cold_archive(graph: MemoryGraph, user_id: str = "default") -> str:
    """
    Deterministic cold archive: only canon nodes.
    """
    canon=[]
    for eid, ent in graph.entities.items():
        if ent.payload.get("user_id") != user_id:
            continue
        if bool(ent.payload.get("canon", False)):
            canon.append((int(ent.payload.get("last_reinforced",0)), eid, ent.payload))
    canon.sort(reverse=True)
    lines=[f"# Torment Cold Archive ({user_id})", ""]
    for _, eid, p in canon:
        lines.append(f"- [{eid}] ({p.get('type','')}, strength={p.get('strength',0):.3f}, conf={p.get('confidence',0):.3f}) {p.get('summary','')}")
    return "\n".join(lines) + "\n"

def write_cold_archive(graph: MemoryGraph, path: str, user_id: str = "default") -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    txt = build_cold_archive(graph, user_id=user_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return path
