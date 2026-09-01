"""Backend-neutral motif-maintenance workflow over current motif geometry.

The current motif aggregate remains owned by its selected backend.  This
module owns neither aggregate mutation nor a shadow copy of it: it projects
the exact legacy entropy and merge-suggestion laws over caller-provided
current geometry, then persists only the established external workflow files.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Protocol, Sequence, Tuple
import json
import os
import time

import numpy as np

from .embedding_store import _canonical_storage_root, _child_path
from .motif_decision import cosine
from .pathing import safe_slug


def _now_ts() -> int:
    return int(time.time())


class MotifMaintenancePort(Protocol):
    """Suggestion-only maintenance available after a motif write is complete."""

    def update_entropy_and_suggest(
        self,
        *,
        target_n: int,
        entropy_high: float,
        sim_threshold: float,
        max_suggestions: int,
        auto_merge: bool,
        auto_merge_trigger: float,
    ) -> Dict[str, Any]: ...


class NativeMotifAutoMergeRefused(RuntimeError):
    """M1 deliberately has no authority to rewrite native motif truth."""


def entropy_report_for_geometry(motifs: Sequence[Any], *, target_n: int = 24) -> Dict[str, Any]:
    """The exact current ``MotifRegistry.entropy_report`` calculation."""
    n = len(motifs)
    if n <= 1:
        return {"motif_count": n, "shannon": 0.0, "fragmentation": 0.0, "entropy_score": 0.0}
    strengths = np.asarray(
        [max(1e-6, float(item.strength)) for item in motifs], dtype=np.float64,
    )
    p = strengths / (strengths.sum() + 1e-12)
    shannon = float(-(p * np.log(p + 1e-12)).sum() / (np.log(n + 1e-12)))
    fragmentation = float(min(1.0, n / float(max(1, target_n))))
    entropy_score = float(min(1.0, 0.55 * shannon + 0.45 * fragmentation))
    return {
        "motif_count": n,
        "shannon": shannon,
        "fragmentation": fragmentation,
        "entropy_score": entropy_score,
    }


def merge_candidates_for_geometry(
    motifs: Sequence[Any], *, sim_threshold: float = 0.93,
) -> List[Tuple[float, str, str]]:
    """The exact current candidate iteration, threshold, and stable ordering law."""
    candidates: List[Tuple[float, str, str]] = []
    for i in range(len(motifs)):
        mi = motifs[i]
        ci = _centroid_np(mi)
        for j in range(i + 1, len(motifs)):
            mj = motifs[j]
            cj = _centroid_np(mj)
            if ci.size == 0 or cj.size == 0 or ci.size != cj.size:
                continue
            similarity = cosine(ci, cj)
            if similarity >= sim_threshold:
                candidates.append((similarity, _runtime_motif_id(mi), _runtime_motif_id(mj)))
    # Python's stable sort intentionally retains the original nested geometry
    # order for equal similarities, matching the registry implementation.
    candidates.sort(reverse=True, key=lambda item: item[0])
    return candidates


class MotifSuggestionWorkflowStore:
    """The retained JSON/JSONL owner for merge suggestions and diagnostic events."""

    def __init__(self, data_dir: str, workspace_id: str, domain_id: str) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.domain_id = safe_slug(domain_id, "domain_id")
        self.data_dir = _canonical_storage_root(data_dir)
        motif_dir = os.path.realpath(
            os.path.join(self.data_dir, "workspaces", self.workspace_id, "domains", self.domain_id)
        )
        if not motif_dir.startswith(self.data_dir + os.sep):
            raise ValueError(f"Motif workflow path escapes base: {motif_dir!r}")
        os.makedirs(motif_dir, exist_ok=True)
        self._base = motif_dir
        self.events_path = _child_path(motif_dir, "motif_events.jsonl")
        self.merges_path = _child_path(motif_dir, "motif_merges.json")
        self._merge_suggestions: Dict[str, Dict[str, Any]] = {}
        self._load_merges()

    @property
    def suggestions(self) -> Dict[str, Dict[str, Any]]:
        """Current in-process suggestion map, including legacy's unsaved updates."""
        return self._merge_suggestions

    def _guard(self, path: str) -> str:
        resolved = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if resolved != base and not resolved.startswith(base + os.sep):
            raise ValueError(f"Path escapes motif workflow root: {resolved!r}")
        return resolved

    def _load_merges(self) -> None:
        if not os.path.exists(self.merges_path):
            return
        try:
            with open(self._guard(self.merges_path), "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self._merge_suggestions = dict(payload.get("suggestions", {}))
        except Exception:
            # Exact legacy restart behavior: malformed side-store data starts
            # with an empty in-memory suggestion map; motif truth is untouched.
            self._merge_suggestions = {}

    def log_event(self, event: Dict[str, Any]) -> None:
        item = dict(event)
        item.setdefault("ts", _now_ts())
        item.setdefault("workspace_id", self.workspace_id)
        item.setdefault("domain_id", self.domain_id)
        with open(self._guard(self.events_path), "a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    def save_merges(self) -> None:
        with open(self._guard(self.merges_path), "w", encoding="utf-8") as handle:
            json.dump({"suggestions": self._merge_suggestions}, handle, indent=2, sort_keys=True)

    def suggest_merges(
        self,
        motifs: Sequence[Any],
        *,
        sim_threshold: float,
        max_suggestions: int,
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for similarity, a, b in merge_candidates_for_geometry(
            motifs, sim_threshold=sim_threshold,
        )[:max_suggestions]:
            suggestion_id = f"merge_{a}__{b}"
            if suggestion_id in self._merge_suggestions:
                # Current legacy behavior updates the live map but does not
                # save it unless this call also creates at least one new item.
                self._merge_suggestions[suggestion_id]["sim"] = float(similarity)
                continue
            suggestion = {
                "suggestion_id": suggestion_id,
                "a": a,
                "b": b,
                "sim": float(similarity),
                "status": "suggested",
                "created_ts": _now_ts(),
                "updated_ts": _now_ts(),
            }
            self._merge_suggestions[suggestion_id] = suggestion
            self.log_event({
                "type": "MOTIF_MERGE_SUGGESTED",
                "suggestion_id": suggestion_id,
                "a": a,
                "b": b,
                "sim": float(similarity),
            })
            out.append(suggestion)
        if out:
            self.save_merges()
        return out

    def list_merge_suggestions(
        self, status: str = "suggested", limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Retain the registry's status/similarity/update ordering law."""
        items = list(self._merge_suggestions.values())
        if status and status != "any":
            items = [item for item in items if item.get("status") == status]
        items.sort(
            key=lambda item: (
                item.get("status"), float(item.get("sim", 0.0)),
                int(item.get("updated_ts", 0)),
            ),
            reverse=True,
        )
        return items[:limit]

    def mark_merge_approved(self, suggestion_id: str, *, note: str) -> Dict[str, Any]:
        """Persist only the external decision state, after native truth commits.

        Retrying a successfully persisted approval leaves its timestamp and
        JSON bytes alone.  That fact lets the outer layer recover a lost
        response without inventing a second cross-store decision.
        """
        suggestion = self._require_suggestion(suggestion_id)
        if suggestion.get("status") == "approved":
            return suggestion
        suggestion["status"] = "approved"
        suggestion["updated_ts"] = _now_ts()
        suggestion["note"] = note
        self.save_merges()
        return suggestion

    def mark_merge_rejected_missing_native(self, suggestion_id: str) -> Dict[str, Any]:
        """The frozen legacy missing-motif failure decision and event."""
        suggestion = self._require_suggestion(suggestion_id)
        suggestion["status"] = "rejected"
        suggestion["updated_ts"] = _now_ts()
        self.save_merges()
        self.log_event({
            "type": "MOTIF_MERGE_FAILED",
            "suggestion_id": suggestion_id,
            "reason": "missing motif",
        })
        return suggestion

    def decide_without_motif_mutation(
        self, suggestion_id: str, decision: str, *, note: str = "",
    ) -> Dict[str, Any]:
        """Apply the retained side-store-only reject/reset workflow.

        ``approve`` remains deliberately unavailable here: callers with
        native truth must first execute their atomic storage mutation.
        """
        suggestion = self._require_suggestion(suggestion_id)
        decision = decision.strip().lower()
        if decision not in ("reject", "reset"):
            raise ValueError("side-store-only decision must be reject or reset")
        if decision == "reject":
            suggestion["status"] = "rejected"
            suggestion["updated_ts"] = _now_ts()
            suggestion["note"] = note
            self.save_merges()
            self.log_event({
                "type": "MOTIF_MERGE_REJECTED", "suggestion_id": suggestion_id, "note": note,
            })
            return suggestion
        suggestion["status"] = "suggested"
        suggestion["updated_ts"] = _now_ts()
        self.save_merges()
        self.log_event({"type": "MOTIF_MERGE_RESET", "suggestion_id": suggestion_id})
        return suggestion

    def log_merged_once(
        self, suggestion_id: str, *, keep: str, drop: str) -> bool:
        """Append the native merge event exactly once across lost responses.

        The M1 JSONL stream has no operation table.  Recovery is therefore
        grounded in the durable approved status plus this precise, existing
        event shape; a matching event is evidence that its append completed.
        """
        for event in self._events():
            if (
                event.get("type") == "MOTIF_MERGED"
                and event.get("suggestion_id") == suggestion_id
                and event.get("keep") == keep and event.get("drop") == drop
            ):
                return False
        self.log_event({
            "type": "MOTIF_MERGED", "suggestion_id": suggestion_id,
            "keep": keep, "drop": drop,
        })
        return True

    def _require_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        if suggestion_id not in self._merge_suggestions:
            raise ValueError("unknown suggestion_id")
        return self._merge_suggestions[suggestion_id]

    def _events(self) -> Iterable[Dict[str, Any]]:
        if not os.path.exists(self.events_path):
            return ()
        events: list[Dict[str, Any]] = []
        try:
            with open(self._guard(self.events_path), "r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(event, dict):
                        events.append(event)
        except OSError:
            return ()
        return tuple(events)


class LegacyMotifMaintenanceAdapter:
    """Retain the legacy registry's existing maintenance and mutation authority."""

    def __init__(self, registry: Any) -> None:
        if not hasattr(registry, "update_entropy_and_suggest"):
            raise ValueError("legacy motif maintenance requires MotifRegistry semantics")
        self._registry = registry

    def update_entropy_and_suggest(self, **kwargs: Any) -> Dict[str, Any]:
        return self._registry.update_entropy_and_suggest(**kwargs)


class NativeMotifMaintenanceAdapter:
    """Suggestion-only maintenance over qualified native current geometry.

    The adapter never opens, instantiates, or populates a legacy
    ``MotifRegistry``.  It reads only the caller's qualified geometry port and
    writes only the legacy-owned diagnostic/suggestion workflow side-store.
    """

    def __init__(
        self,
        geometry: Any,
        *,
        data_dir: str,
        workspace_id: str,
        domain_id: str,
        merge_mutator: Any | None = None,
    ) -> None:
        if not hasattr(geometry, "list_motifs") or not hasattr(geometry, "domain_ids"):
            raise ValueError("native motif maintenance requires motif geometry semantics")
        if domain_id not in tuple(geometry.domain_ids()):
            raise ValueError("native motif maintenance domain is not represented by its geometry")
        self._geometry = geometry
        self._domain_id = domain_id
        self._workflow = MotifSuggestionWorkflowStore(data_dir, workspace_id, domain_id)
        if merge_mutator is not None and not hasattr(merge_mutator, "merge_suggestion"):
            raise ValueError("native motif merge mutator requires merge_suggestion semantics")
        self._merge_mutator = merge_mutator

    @property
    def workflow_store(self) -> MotifSuggestionWorkflowStore:
        """Inspection seam for qualification tests; it contains no motif truth."""
        return self._workflow

    def update_entropy_and_suggest(
        self,
        *,
        target_n: int,
        entropy_high: float,
        sim_threshold: float,
        max_suggestions: int,
        auto_merge: bool,
        auto_merge_trigger: float,
    ) -> Dict[str, Any]:
        if auto_merge and self._merge_mutator is None:
            raise NativeMotifAutoMergeRefused(
                "native motif auto-merge remains unqualified until 7G5E4D-M2"
            )
        motifs = self._geometry.list_motifs(self._domain_id)
        report = entropy_report_for_geometry(motifs, target_n=target_n)
        self._workflow.log_event({"type": "MOTIF_ENTROPY", **report})
        if report.get("entropy_score", 0.0) >= entropy_high:
            self._workflow.suggest_merges(
                motifs,
                sim_threshold=sim_threshold,
                max_suggestions=max_suggestions,
            )
        if auto_merge and report.get("entropy_score", 0.0) >= auto_merge_trigger:
            suggestions = self._workflow.list_merge_suggestions(status="suggested", limit=5)
            approved = 0
            for suggestion in suggestions:
                if approved >= 2:
                    break
                if float(suggestion.get("sim", 0.0)) >= (sim_threshold + 0.01):
                    self.decide_merge(
                        str(suggestion["suggestion_id"]), "approve", note="auto-merge",
                    )
                    # Exact legacy behavior counts an eligible attempted
                    # decision even when the second suggestion has become
                    # missing after the first merge.
                    approved += 1
            report["auto_merged"] = approved
        return report

    def decide_merge(
        self,
        suggestion_id: str,
        decision: str,
        note: str = "",
        *,
        _test_fail_after: str | None = None,
    ) -> Dict[str, Any]:
        """Apply a native proposal decision without consulting legacy truth."""
        suggestion = self._workflow._require_suggestion(suggestion_id)
        decision = decision.strip().lower()
        if decision not in ("approve", "reject", "reset"):
            raise ValueError("invalid decision")
        if decision != "approve":
            return self._workflow.decide_without_motif_mutation(
                suggestion_id, decision, note=note,
            )
        if self._merge_mutator is None:
            raise NativeMotifAutoMergeRefused(
                "native motif merge mutation remains unqualified until 7G5E4D-M2"
            )
        result = self._merge_mutator.merge_suggestion(
            suggestion, note=note, _test_fail_after=_test_fail_after,
        )
        if result is None:
            return self._workflow.mark_merge_rejected_missing_native(suggestion_id)
        if _test_fail_after == "after_sqlite_commit":
            raise RuntimeError("forced native motif merge failure after SQLite commit")
        approved = self._workflow.mark_merge_approved(suggestion_id, note=note)
        if _test_fail_after == "after_workflow_status":
            raise RuntimeError("forced native motif merge failure after workflow status")
        self._workflow.log_merged_once(
            suggestion_id,
            keep=result.keep_runtime_motif_id,
            drop=result.drop_runtime_motif_id,
        )
        if _test_fail_after == "after_workflow_event":
            raise RuntimeError("forced native motif merge failure after workflow event")
        return approved


def _runtime_motif_id(motif: Any) -> str:
    value = getattr(motif, "runtime_motif_id", getattr(motif, "motif_id", None))
    if not isinstance(value, str) or not value:
        raise ValueError("motif geometry requires a non-empty runtime motif ID")
    return value


def _centroid_np(motif: Any) -> np.ndarray:
    method = getattr(motif, "centroid_np", None)
    if callable(method):
        return np.asarray(method(), dtype=np.float32)
    return np.asarray(getattr(motif, "centroid", ()), dtype=np.float32)


__all__ = [
    "LegacyMotifMaintenanceAdapter",
    "MotifMaintenancePort",
    "MotifSuggestionWorkflowStore",
    "NativeMotifAutoMergeRefused",
    "NativeMotifMaintenanceAdapter",
    "entropy_report_for_geometry",
    "merge_candidates_for_geometry",
]
