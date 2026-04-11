# torment_service/migration/dry_run.py
"""
Dry-run report generator for WRITE_MIGRATION.

Produces the four-section minimum report ratified in Decision 6:

  1. Per-class counts           — how many rows fell into each gate-1 class
  2. Gate-1 FAIL listing        — every row that gate 1 could not recover,
                                  with class id and a short recovery note
  3. Gate-2 refusal listing     — every row gate 2 refused, with reason
  4. Reproducibility anchor     — the inputs that make the report
                                  deterministic and auditable

**No-write invariant.** The dry-run generator never touches the corpus.
It reads from an iterable of ``(eid, raw_provenance)`` tuples supplied
by the caller, classifies each row through gate 1 + gate 2, and
returns a report dict. It does not call any corpus-mutation API. The
invariant is asserted at test time by a tests-side module that checks
``torment_service.migration.dry_run`` imports zero storage write
functions.

The generator may append to the migration cursor and review queue files
(both under ``.torment_migration/`` in the workspace root) when
``write_cursor=True``. These are the migration's own bookkeeping
files, not corpus state. They exist so repeated dry-runs can resume
after interruption and so operators can inspect them.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .constants import (
    ADMISSION_POLICY_VERSION,
    GATE1_CLASS_ALREADY_CANONICAL,
    GATE1_CLASS_DEPRECATED_VOCABULARY,
    GATE1_CLASS_DICT_INVALID_TYPE,
    GATE1_CLASS_DICT_TRUNCATED,
    GATE1_CLASS_LEGACY_BARE_STRING,
    GATE1_CLASS_NULL_OR_EMPTY,
    GATE1_CLASS_ZERO_EVENT_ARTIFACT,
    GATE1_OUTCOME_FAIL,
    GATE1_OUTCOME_RECOVER,
    GATE1_OUTCOME_SKIP,
    ZERO_EVENT_ARTIFACT_PATTERNS,
)
from .cursor import (
    CURSOR_ACTION_DRY_RUN_CLASSIFIED,
    CURSOR_ACTION_SKIPPED,
    CursorEntry,
    append_entry,
    processed_eids,
)
from .gate1_recovery import Gate1Result, classify_row
from .gate2_admission import Gate2Result, decide_admission


# Class id → human name mapping used only for report rendering. The CI
# drift check asserts these names stay aligned with the constants.
_CLASS_ID_NAMES: Dict[int, str] = {
    GATE1_CLASS_ALREADY_CANONICAL:     "already_canonical",
    GATE1_CLASS_LEGACY_BARE_STRING:    "legacy_bare_string",
    GATE1_CLASS_DICT_TRUNCATED:        "dict_truncated",
    GATE1_CLASS_DICT_INVALID_TYPE:     "dict_invalid_type",
    GATE1_CLASS_NULL_OR_EMPTY:         "null_or_empty",
    GATE1_CLASS_DEPRECATED_VOCABULARY: "deprecated_vocabulary",
    GATE1_CLASS_ZERO_EVENT_ARTIFACT:   "zero_event_artifact",
}


@dataclass
class FailListingEntry:
    eid: int
    class_id: int
    class_name: str
    recovery_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eid": self.eid,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "recovery_notes": self.recovery_notes,
        }


@dataclass
class RefusalListingEntry:
    eid: int
    class_id: int
    class_name: str
    recovered_source_type: Optional[str]
    admission_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eid": self.eid,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "recovered_source_type": self.recovered_source_type,
            "admission_reason": self.admission_reason,
        }


@dataclass
class DryRunReport:
    """Four-section dry-run report ratified in Decision 6.

    This dataclass is the in-memory representation of the report. Call
    ``to_dict`` for JSON serialization — the CLI writes the dict to
    stdout or to a caller-specified output file. The structure is
    stable and the CI drift check asserts its shape.
    """
    # Section 1 — per-class counts
    class_counts: Dict[int, int] = field(default_factory=dict)

    # Section 2 — gate-1 FAIL listing
    gate1_fail_listing: List[FailListingEntry] = field(default_factory=list)

    # Section 3 — gate-2 refusal listing (includes gate-1 FAIL rows
    # because those are also refused, but adds the class-specific
    # refusal reasons for recovered-then-refused rows)
    gate2_refusal_listing: List[RefusalListingEntry] = field(default_factory=list)

    # Section 4 — reproducibility anchor
    policy_version: str = ADMISSION_POLICY_VERSION
    generated_at: Optional[str] = None
    row_count: int = 0
    zero_event_artifact_patterns_empty: bool = True

    def to_dict(self) -> Dict[str, Any]:
        # Convert int-keyed dict to string keys for JSON.
        class_counts_serializable = {
            str(cid): count for cid, count in self.class_counts.items()
        }
        return {
            "class_counts": class_counts_serializable,
            "class_names": _CLASS_ID_NAMES,
            "gate1_fail_listing": [e.to_dict() for e in self.gate1_fail_listing],
            "gate2_refusal_listing": [e.to_dict() for e in self.gate2_refusal_listing],
            "reproducibility_anchor": {
                "policy_version": self.policy_version,
                "generated_at": self.generated_at,
                "row_count": self.row_count,
                "zero_event_artifact_patterns_empty": self.zero_event_artifact_patterns_empty,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def run_dry_run(
    rows: Iterable[Tuple[int, Any]],
    *,
    workspace_root: Optional[str] = None,
    write_cursor: bool = False,
    skip_processed: bool = False,
) -> DryRunReport:
    """Classify every row and produce a dry-run report.

    Parameters
    ----------
    rows
        An iterable of ``(eid, raw_provenance)`` tuples. The caller
        (CLI or test) is responsible for producing this stream; the
        dry-run module itself never queries the corpus.
    workspace_root
        Required when ``write_cursor=True``. The directory under which
        ``.torment_migration/cursor.jsonl`` lives.
    write_cursor
        When True, append a ``DRY_RUN_CLASSIFIED`` cursor entry for
        each non-skip row. This is the mechanism that makes the
        dry-run itself resumable across restarts.
    skip_processed
        When True, rows whose EID already has a cursor entry are
        skipped entirely (neither classified nor counted). Used on
        resume so a partial dry-run can continue from where it left
        off without double-counting.
    """
    report = DryRunReport()
    report.generated_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    report.zero_event_artifact_patterns_empty = (
        ZERO_EVENT_ARTIFACT_PATTERNS == ()
    )

    # Resume state.
    skip_set: set = set()
    if skip_processed:
        if workspace_root is None:
            raise ValueError(
                "skip_processed=True requires workspace_root to be set"
            )
        skip_set = processed_eids(workspace_root)

    for eid, raw in rows:
        if eid in skip_set:
            continue

        g1 = classify_row(raw, eid=eid)
        g2 = decide_admission(g1)
        report.row_count += 1

        # Section 1 — per-class counts.
        report.class_counts[g1.class_id] = (
            report.class_counts.get(g1.class_id, 0) + 1
        )

        # Section 2 — gate-1 FAIL listing.
        if g1.outcome == GATE1_OUTCOME_FAIL:
            report.gate1_fail_listing.append(
                FailListingEntry(
                    eid=eid,
                    class_id=g1.class_id,
                    class_name=_CLASS_ID_NAMES.get(g1.class_id, "unknown"),
                    recovery_notes=g1.recovery_notes,
                )
            )

        # Section 3 — gate-2 refusal listing.
        if not g2.admitted:
            report.gate2_refusal_listing.append(
                RefusalListingEntry(
                    eid=eid,
                    class_id=g1.class_id,
                    class_name=_CLASS_ID_NAMES.get(g1.class_id, "unknown"),
                    recovered_source_type=g1.recovered_source_type,
                    admission_reason=g2.reason,
                )
            )

        # Cursor bookkeeping.
        if write_cursor:
            assert workspace_root is not None
            action = (
                CURSOR_ACTION_SKIPPED
                if g1.outcome == GATE1_OUTCOME_SKIP
                else CURSOR_ACTION_DRY_RUN_CLASSIFIED
            )
            append_entry(
                workspace_root,
                CursorEntry(
                    eid=eid,
                    action=action,
                    gate1_class_id=g1.class_id,
                    gate2_admitted=g2.admitted,
                ),
            )

    return report
