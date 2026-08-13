"""Non-mutating trusted-current projection for Closure persistence.

``ClosureStore`` and ``ClosureLedger`` deliberately retain raw, append-only
evidence.  This module does not repair, truncate, or otherwise modify either
source.  It derives the strongest lifecycle claim jointly supported by their
rows so Fabric mutation gates can fail closed when the two files disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .closure_ledger import ClosureEvent
from .closure_memory import ClosureEntry


_VALID_EVENT_KINDS = frozenset({"proposed", "ratified", "committed", "revised"})


@dataclass(frozen=True)
class ClosureReconciliation:
    """Trusted projection plus bounded diagnostics over raw closure evidence.

    ``current_entry`` remains an internal helper for Fabric's lifecycle gates.
    Callers should use :meth:`as_current_dict`, which exposes serialized data
    and diagnostics rather than persistence objects.
    """

    valid_versions: Tuple[ClosureEntry, ...]
    orphan_versions: Tuple[ClosureEntry, ...]
    valid_events: Tuple[ClosureEvent, ...]
    orphan_events: Tuple[ClosureEvent, ...]
    current_state: Optional[str]
    current_version_id: Optional[str]
    current_entry: Optional[ClosureEntry]
    has_ratification: bool
    has_committed: bool
    diagnostics: Tuple[Dict[str, Any], ...]

    @property
    def healthy(self) -> bool:
        return not self.diagnostics

    def as_current_dict(self) -> Dict[str, Any]:
        """Return the explicit operational/current API shape.

        Raw store and ledger reads remain available through their existing
        APIs.  This shape is intentionally named and diagnostic-bearing so it
        cannot be mistaken for raw forensic history.
        """
        from dataclasses import asdict

        return {
            "closure_id": (
                self.current_entry.closure_id
                if self.current_entry is not None
                else None
            ),
            "workspace_id": (
                self.current_entry.workspace_id
                if self.current_entry is not None
                else None
            ),
            "current_state": self.current_state,
            "current_version_id": self.current_version_id,
            "closure": asdict(self.current_entry)
            if self.current_entry is not None
            else None,
            "healthy": self.healthy,
            "reconciled_with_orphans": bool(
                self.orphan_versions or self.orphan_events
            ),
            "valid_version_ids": [entry.version_id for entry in self.valid_versions],
            "orphan_version_ids": [entry.version_id for entry in self.orphan_versions],
            "valid_event_ids": [event.event_id for event in self.valid_events],
            "orphan_event_ids": [event.event_id for event in self.orphan_events],
            "diagnostics": [dict(item) for item in self.diagnostics],
        }


def reconcile_closure_history(
    entries: Iterable[ClosureEntry],
    events: Iterable[ClosureEvent],
    *,
    workspace_id: str,
    closure_id: str,
) -> ClosureReconciliation:
    """Project one closure's trustworthy lifecycle from raw append history.

    Append order is the only ordering input.  No timestamps are interpreted.
    A payload joins the trusted chain only through a valid ``proposed`` or
    ``revised`` event; a later invalid row cannot displace prior trusted state.
    Ratification remains closure-bound and intentionally versionless.
    """
    all_entries = list(entries)
    target_entries = [
        entry
        for entry in all_entries
        if entry.workspace_id == workspace_id and entry.closure_id == closure_id
    ]
    diagnostics: List[Dict[str, Any]] = []

    versions_by_id: Dict[str, List[ClosureEntry]] = {}
    for entry in target_entries:
        versions_by_id.setdefault(entry.version_id, []).append(entry)
    target_by_id = {
        version_id: candidates[0]
        for version_id, candidates in versions_by_id.items()
        if len(candidates) == 1
    }
    duplicate_version_ids = {
        version_id
        for version_id, candidates in versions_by_id.items()
        if len(candidates) != 1
    }
    for version_id in sorted(duplicate_version_ids):
        diagnostics.append({
            "kind": "duplicate_version_id",
            "version_id": version_id,
        })

    all_versions_by_id: Dict[str, List[ClosureEntry]] = {}
    for entry in all_entries:
        all_versions_by_id.setdefault(entry.version_id, []).append(entry)

    valid_versions: List[ClosureEntry] = []
    valid_events: List[ClosureEvent] = []
    orphan_events: List[ClosureEvent] = []
    paired_version_ids: set[str] = set()
    seen_event_ids: set[str] = set()
    current_state: Optional[str] = None
    current_entry: Optional[ClosureEntry] = None
    has_ratification = False
    has_committed = False

    def reject(event: ClosureEvent, kind: str, **details: Any) -> None:
        orphan_events.append(event)
        diagnostics.append({
            "kind": kind,
            "event_id": event.event_id,
            "event_kind": event.kind,
            "version_id": event.version_id,
            **details,
        })

    def resolve_target_version(event: ClosureEvent) -> Optional[ClosureEntry]:
        version_id = event.version_id
        if version_id is None:
            reject(event, "missing_version_reference")
            return None
        if version_id in duplicate_version_ids:
            reject(event, "ambiguous_version_reference")
            return None
        entry = target_by_id.get(version_id)
        if entry is not None:
            return entry
        if version_id in all_versions_by_id:
            reject(event, "foreign_version_reference")
        else:
            reject(event, "missing_version_reference")
        return None

    for event in events:
        if event.closure_id != closure_id:
            continue
        if event.workspace_id != workspace_id:
            reject(event, "foreign_workspace_event")
            continue
        if event.event_id in seen_event_ids:
            reject(event, "duplicate_event_id")
            continue
        seen_event_ids.add(event.event_id)
        if event.kind not in _VALID_EVENT_KINDS:
            reject(event, "unknown_event_kind")
            continue

        if event.kind == "proposed":
            entry = resolve_target_version(event)
            if entry is None:
                continue
            if entry.parent_version_id is not None:
                reject(event, "proposal_has_parent")
            elif current_state is not None or entry.version_id in paired_version_ids:
                reject(event, "invalid_lifecycle_transition")
            else:
                paired_version_ids.add(entry.version_id)
                valid_versions.append(entry)
                valid_events.append(event)
                current_entry = entry
                current_state = "proposed"
            continue

        if event.kind == "ratified":
            if event.version_id is not None:
                reject(event, "ratification_must_be_versionless")
            elif current_state not in {"proposed", "ratified", "revised"}:
                reject(event, "invalid_lifecycle_transition")
            else:
                valid_events.append(event)
                has_ratification = True
                current_state = "ratified"
            continue

        entry = resolve_target_version(event)
        if entry is None:
            continue

        if event.kind == "committed":
            if not has_ratification:
                reject(event, "missing_valid_ratification")
            elif current_state not in {"ratified", "revised"}:
                reject(event, "invalid_lifecycle_transition")
            elif current_entry is None or entry.version_id != current_entry.version_id:
                reject(event, "commit_not_current_version")
            else:
                valid_events.append(event)
                current_state = "committed"
                has_committed = True
            continue

        # A revision has its own stored payload, linked to the trusted current
        # version.  A prior committed chain is required; ratification remains
        # a closure-level fact and is never rebound to a version.
        if not has_committed:
            reject(event, "missing_valid_commit")
        elif current_state not in {"committed", "ratified", "revised"}:
            reject(event, "invalid_lifecycle_transition")
        elif current_entry is None or entry.parent_version_id != current_entry.version_id:
            reject(event, "revision_parent_not_current")
        elif entry.version_id in paired_version_ids:
            reject(event, "duplicate_revision_version")
        else:
            paired_version_ids.add(entry.version_id)
            valid_versions.append(entry)
            valid_events.append(event)
            current_entry = entry
            current_state = "revised"

    orphan_versions: List[ClosureEntry] = []
    for entry in target_entries:
        if entry.version_id not in paired_version_ids:
            orphan_versions.append(entry)
            diagnostics.append({
                "kind": "store_only_version",
                "version_id": entry.version_id,
                "parent_version_id": entry.parent_version_id,
            })

    return ClosureReconciliation(
        valid_versions=tuple(valid_versions),
        orphan_versions=tuple(orphan_versions),
        valid_events=tuple(valid_events),
        orphan_events=tuple(orphan_events),
        current_state=current_state,
        current_version_id=(
            current_entry.version_id if current_entry is not None else None
        ),
        current_entry=current_entry,
        has_ratification=has_ratification,
        has_committed=has_committed,
        diagnostics=tuple(diagnostics),
    )
