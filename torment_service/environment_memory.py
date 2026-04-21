# torment_service/environment_memory.py
"""
Block B — environment memory module.

Per docs/BLOCK_B_DESIGN.md §7. The higher-risk half of Block B:
operational facts about the machine / runtime / container / shell /
filesystem / execution surface the agent is acting inside of.

=== DESIGN DISCIPLINE ===
Environment memory differs from reference memory on every dimension:

    - Net-new category: no existing TORMENT code resembles it.
    - Action-site consultation, NOT prompt-context retrieval. Consult
      returns a relevance-filtered view; environment facts NEVER
      auto-inject into retrieval_assembler (R+4).
    - Strict evidence discipline at write-time: every entry declares
      one of three classes — user_asserted / observed / inferred.
      "LLM guessed" is not a valid origin (R+5).
    - Consult returns a VIEW, not the underlying entries. The view
      shape (EnvironmentFactView) is explicitly distinct from the
      stored entry (EnvironmentEntry) — entry identity is separate
      from consult result shape (carry-forward caution ratified
      2026-04-21).
    - Consult is return-only. No wiring into action_policy, no
      runner hook, no automatic policy integration (D.3).
    - v0.1 ships with VALID_INFERENCE_RULES EMPTY. Any inferred write
      is rejected until rules are explicitly ratified.
=== END DESIGN DISCIPLINE ===

Design references:
    - docs/PRE_BLOCK_B_PRECONDITIONS.md §3 (red lines R+3–R+6)
    - docs/BLOCK_B_IMPLEMENTATION_ANALYSIS.md §2 (higher-risk pass)
    - docs/BLOCK_B_DESIGN.md §5.4, §5.5, §7
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


log = logging.getLogger("torment.environment_memory")


# ---------------------------------------------------------------------------
# Constants — evidence / ownership / inference-rule vocabulary
# ---------------------------------------------------------------------------

ENVIRONMENT_MEMORY_CLASS = "environment"  # Never changes. Defensive-filter anchor.

VALID_EVIDENCE_CLASSES = frozenset({
    "user_asserted",  # explicit user statement
    "observed",       # directly probed; observation_source names the probe
    "inferred",       # produced by a ratified inference rule (see below)
})

VALID_OWNERSHIP = frozenset({
    "agent",   # agent-observed or agent-owned operational knowledge
    "system",  # system-probed; typically the probe-on-fail path
    "user",    # user-asserted
})

# v0.1 ships EMPTY. No inference rules are pre-declared; no inferred
# environment writes are accepted until a rule is explicitly ratified
# through a separate preconditions-style doc (see open question Q2 in
# docs/BLOCK_B_DESIGN.md §11). Strict v0.1 posture: R+5 forbids
# "the LLM guessed" as a valid origin.
VALID_INFERENCE_RULES: frozenset = frozenset()


def _now_ts() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# Data structures — entry (stored) vs view (consulted) kept distinct
# ---------------------------------------------------------------------------


@dataclass
class EnvironmentEntry:
    """A stored environment fact.

    Identity is durable: `env_id` is assigned at write and never
    changes. This is the PERSISTED record shape — full provenance,
    full ownership, full evidence metadata. Consult callers receive
    an EnvironmentFactView (below), NOT this entry.
    """
    env_id: str
    workspace_id: str
    target_runtime: str
    scope_tag: str
    key: str
    value: Any
    evidence_class: str
    ownership: str
    provenance: Dict[str, Any]
    last_observed: int
    created_ts: int
    observation_source: Optional[str] = None   # required when evidence_class==observed
    inference_rule: Optional[str] = None        # required when evidence_class==inferred
    asserted_by: Optional[str] = None           # required when evidence_class==user_asserted
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvironmentFactView:
    """A consult-time view over an environment fact.

    CARRY-FORWARD CAUTION (ratified 2026-04-21): this shape is
    explicitly DIFFERENT from EnvironmentEntry. Consult returns a
    narrow action-site view, not the full persisted record.

    Fields present: just enough for the caller's action-site decision.
    Fields ABSENT (compared to EnvironmentEntry):
        - env_id       (identity metadata)
        - workspace_id (scoping metadata)
        - ownership    (governance metadata)
        - provenance   (full origin dict)
        - target_runtime, scope_tag, created_ts, metadata

    If a future caller needs access to the fuller shape, they should
    query the entry directly — consult is not the path for that.
    """
    key: str
    value: Any
    evidence_class: str
    last_observed: int
    inferred: bool  # derived convenience — True when evidence_class=="inferred"


@dataclass
class EnvironmentConsultResult:
    """Return envelope for fabric.consult_environment.

    A view-over-list shape, NOT a single-object shape. The distinction
    from reference memory's load result is structural — `load`
    returns body+load_id (single object); `consult` returns facts
    (list of views).
    """
    ok: bool
    result_code: str               # "consulted" | "no_relevant_facts"
    operation: str                 # echo of requested operation
    scope: str                     # echo of requested scope
    facts: List[EnvironmentFactView] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "result_code": self.result_code,
            "operation": self.operation,
            "scope": self.scope,
            "facts": [asdict(f) for f in self.facts],
        }


# ---------------------------------------------------------------------------
# EnvironmentStore
# ---------------------------------------------------------------------------


class EnvironmentStore:
    """Per-workspace environment memory store.

    Holds operational facts with strict evidence-class discipline.
    Every write validates evidence_class + ownership + class-specific
    required field. Consult is relevance-filtered and returns a
    narrow view.
    """

    def __init__(
        self,
        data_dir: str,
        workspace_id: str,
    ) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.data_dir = _canonical_storage_root(data_dir)

        workspace_root = os.path.realpath(
            os.path.join(self.data_dir, "workspaces", self.workspace_id,
                         "environment_memory")
        )
        if not workspace_root.startswith(self.data_dir + os.sep):
            raise ValueError(
                f"Workspace environment-memory path escapes base: "
                f"{workspace_root!r}"
            )
        os.makedirs(workspace_root, exist_ok=True)
        self._base = workspace_root

        self.entries_path = _child_path(workspace_root, "environment.jsonl")
        self.events_path = _child_path(workspace_root, "events.jsonl")

        # In-memory index: env_id -> EnvironmentEntry.
        self._entries: Dict[str, EnvironmentEntry] = {}
        self._load()

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes environment root: {rp!r}")
        return rp

    def _append_jsonl(self, path: str, obj: Dict[str, Any]) -> None:
        with open(self._guard(path), "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def _load(self) -> None:
        """Load entries from JSONL. Last record per env_id wins."""
        if not os.path.exists(self.entries_path):
            return
        with open(self._guard(self.entries_path), "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    entry = EnvironmentEntry(
                        env_id=obj["env_id"],
                        workspace_id=obj["workspace_id"],
                        target_runtime=obj.get("target_runtime", ""),
                        scope_tag=obj.get("scope_tag", ""),
                        key=obj.get("key", ""),
                        value=obj.get("value"),
                        evidence_class=obj.get("evidence_class", ""),
                        ownership=obj.get("ownership", ""),
                        provenance=obj.get("provenance", {}),
                        last_observed=int(obj.get("last_observed", 0)),
                        created_ts=int(obj.get("created_ts", 0)),
                        observation_source=obj.get("observation_source"),
                        inference_rule=obj.get("inference_rule"),
                        asserted_by=obj.get("asserted_by"),
                        metadata=obj.get("metadata", {}),
                    )
                    self._entries[entry.env_id] = entry
                except (json.JSONDecodeError, KeyError):
                    continue

    # ------------------------------------------------------------------
    # Evidence-class validation — the R+5 gate.
    # Returns (ok, result_code). Empty result_code means validation passed.
    # ------------------------------------------------------------------

    @staticmethod
    def validate_evidence(
        evidence_class: str,
        ownership: str,
        observation_source: Optional[str] = None,
        inference_rule: Optional[str] = None,
        asserted_by: Optional[str] = None,
    ) -> (bool, str):
        """Validate a proposed environment write at the evidence gate.

        Returns a tuple (ok, result_code).

        Result codes on reject:
            missing_evidence_class    — evidence_class empty or unknown
            missing_evidence_field    — class-specific required field missing
            inferred_requires_rule    — inferred without inference_rule
            unknown_inference_rule    — inference_rule not in VALID_INFERENCE_RULES
        """
        # (1) evidence_class must be in vocabulary
        if not evidence_class or evidence_class not in VALID_EVIDENCE_CLASSES:
            return False, "missing_evidence_class"

        # (2) ownership must be in vocabulary
        if not ownership or ownership not in VALID_OWNERSHIP:
            return False, "missing_evidence_field"

        # (3) evidence-class-specific required field
        if evidence_class == "user_asserted":
            if not asserted_by:
                return False, "missing_evidence_field"
        elif evidence_class == "observed":
            if not observation_source:
                return False, "missing_evidence_field"
        elif evidence_class == "inferred":
            if not inference_rule:
                return False, "inferred_requires_rule"
            if inference_rule not in VALID_INFERENCE_RULES:
                return False, "unknown_inference_rule"

        return True, ""

    # ------------------------------------------------------------------
    # Write — creates a new entry after evidence-class validation
    # ------------------------------------------------------------------

    def write(
        self,
        target_runtime: str,
        scope_tag: str,
        key: str,
        value: Any,
        evidence_class: str,
        ownership: str,
        provenance: Dict[str, Any],
        observation_source: Optional[str] = None,
        inference_rule: Optional[str] = None,
        asserted_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Write an environment fact after validating the evidence class.

        Returns the same envelope shape fabric.write_environment uses;
        caller passes this through unchanged.
        """
        ok, code = self.validate_evidence(
            evidence_class=evidence_class,
            ownership=ownership,
            observation_source=observation_source,
            inference_rule=inference_rule,
            asserted_by=asserted_by,
        )
        if not ok:
            return {"ok": False, "result_code": code, "env_id": ""}

        # Validate the other structural fields — target_runtime/scope_tag/key
        # are required per AC-2.1. Empty values are rejected the same way.
        if not target_runtime or not scope_tag or not key:
            return {"ok": False, "result_code": "missing_evidence_field",
                    "env_id": ""}

        env_id = f"env_{uuid.uuid4().hex[:16]}"
        ts = _now_ts()
        entry = EnvironmentEntry(
            env_id=env_id,
            workspace_id=self.workspace_id,
            target_runtime=target_runtime,
            scope_tag=scope_tag,
            key=key,
            value=value,
            evidence_class=evidence_class,
            ownership=ownership,
            provenance=provenance,
            last_observed=ts,
            created_ts=ts,
            observation_source=observation_source,
            inference_rule=inference_rule,
            asserted_by=asserted_by,
            metadata=metadata or {},
        )
        self._entries[env_id] = entry
        self._append_jsonl(self.entries_path, asdict(entry))
        self._append_jsonl(self.events_path, {
            "type": "ENVIRONMENT_WRITTEN",
            "ts": ts,
            "env_id": env_id,
            "key": key,
            "scope_tag": scope_tag,
            "evidence_class": evidence_class,
        })
        return {"ok": True, "result_code": "written", "env_id": env_id}

    # ------------------------------------------------------------------
    # Read — get single entry (admin / audit / testing only)
    # ------------------------------------------------------------------

    def get(self, env_id: str) -> Optional[EnvironmentEntry]:
        return self._entries.get(env_id)

    def list_entries(
        self,
        scope_tag: Optional[str] = None,
        ownership: Optional[str] = None,
        limit: int = 50,
    ) -> List[EnvironmentEntry]:
        """Admin-level listing. Consult is the normal read path."""
        result: List[EnvironmentEntry] = []
        for e in self._entries.values():
            if scope_tag is not None and e.scope_tag != scope_tag:
                continue
            if ownership is not None and e.ownership != ownership:
                continue
            result.append(e)
        result.sort(key=lambda e: e.last_observed, reverse=True)
        return result[:limit]

    # ------------------------------------------------------------------
    # Consult — returns a VIEW, not entries.
    #
    # Scope-match is strict (exact scope_tag equality). relevance_fields,
    # if supplied, narrows the key set. Operation is echoed for audit
    # but not otherwise used for filtering in v0.1.
    # ------------------------------------------------------------------

    def consult(
        self,
        operation: str,
        scope: str,
        relevance_fields: Optional[List[str]] = None,
    ) -> EnvironmentConsultResult:
        """Return a relevance-filtered view of environment facts for
        a specific operation at a scope.

        CARRY-FORWARD CAUTION: the returned shape is
        EnvironmentConsultResult -> List[EnvironmentFactView], NOT
        List[EnvironmentEntry]. Entry identity is separate from
        consult result shape.
        """
        facts: List[EnvironmentFactView] = []
        fields_filter = set(relevance_fields) if relevance_fields else None
        for entry in self._entries.values():
            if entry.scope_tag != scope:
                continue
            if fields_filter is not None and entry.key not in fields_filter:
                continue
            facts.append(EnvironmentFactView(
                key=entry.key,
                value=entry.value,
                evidence_class=entry.evidence_class,
                last_observed=entry.last_observed,
                inferred=(entry.evidence_class == "inferred"),
            ))
        # Sort freshest first (Q3 recommendation from BLOCK_B_DESIGN §11)
        facts.sort(key=lambda f: f.last_observed, reverse=True)

        return EnvironmentConsultResult(
            ok=True,
            result_code="consulted" if facts else "no_relevant_facts",
            operation=operation,
            scope=scope,
            facts=facts,
        )

    @property
    def entry_count(self) -> int:
        return len(self._entries)
