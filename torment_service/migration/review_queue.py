# torment_service/migration/review_queue.py
"""
Append-only JSONL review queue for block-and-review loosening decisions.

When the re-run policy returns ``BLOCK_AND_REVIEW`` (a stored refusal
would loosen to admission under the current policy), the affected row
is enqueued here. A human reviews each entry and either ratifies the
loosening (in which case the next migration run applies it) or
rejects it (in which case the stored refusal remains in place).

Commit A ships the file format and the writer. Commit A's dry-run
path can populate this file with predicted loosenings so the operator
can preview them before commit B's writer goes live. Commit B adds
the consume-path that translates ratified entries into actual row
writes.

File format
-----------

One JSON object per line:

    {
      "eid": 12345,
      "enqueued_at": "2026-04-11T09:00:00Z",
      "stored_decision": {
        "admission_refused": true,
        "admission_reason": "gate1_unrecoverable",
        "admission_policy_version": "v2.4.x-step6-a"
      },
      "current_decision": {
        "admission_refused": false,
        "admission_reason": "",
        "admission_policy_version": "v2.4.x-step6-b"
      },
      "recovered_source_type": "memory",
      "gate1_class_id": 3
    }

``stored_decision`` is what the row currently carries.
``current_decision`` is what gate 2 would decide under the current
policy. The queue contains both so reviewers can see the delta without
re-running gate 2 themselves.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .constants import CURSOR_DIRNAME, REVIEW_QUEUE_FILENAME


@dataclass
class ReviewEntry:
    eid: int
    stored_admission_refused: bool
    stored_admission_reason: str
    stored_admission_policy_version: str
    current_admission_refused: bool
    current_admission_reason: str
    current_admission_policy_version: str
    recovered_source_type: Optional[str]
    gate1_class_id: int
    enqueued_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.enqueued_at is None:
            self.enqueued_at = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

    def to_json_line(self) -> str:
        obj: Dict[str, Any] = {
            "eid": int(self.eid),
            "enqueued_at": self.enqueued_at,
            "stored_decision": {
                "admission_refused": bool(self.stored_admission_refused),
                "admission_reason": self.stored_admission_reason,
                "admission_policy_version": self.stored_admission_policy_version,
            },
            "current_decision": {
                "admission_refused": bool(self.current_admission_refused),
                "admission_reason": self.current_admission_reason,
                "admission_policy_version": self.current_admission_policy_version,
            },
            "recovered_source_type": self.recovered_source_type,
            "gate1_class_id": int(self.gate1_class_id),
        }
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> "ReviewEntry":
        obj = json.loads(line)
        stored = obj["stored_decision"]
        current = obj["current_decision"]
        return cls(
            eid=obj["eid"],
            stored_admission_refused=stored["admission_refused"],
            stored_admission_reason=stored["admission_reason"],
            stored_admission_policy_version=stored["admission_policy_version"],
            current_admission_refused=current["admission_refused"],
            current_admission_reason=current["admission_reason"],
            current_admission_policy_version=current["admission_policy_version"],
            recovered_source_type=obj.get("recovered_source_type"),
            gate1_class_id=obj["gate1_class_id"],
            enqueued_at=obj.get("enqueued_at"),
        )


def review_queue_path(workspace_root: str) -> str:
    return os.path.join(workspace_root, CURSOR_DIRNAME, REVIEW_QUEUE_FILENAME)


def append_review(workspace_root: str, entry: ReviewEntry) -> None:
    path = review_queue_path(workspace_root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry.to_json_line())
        f.write("\n")
        f.flush()
        try:
            os.fsync(f.fileno())
        except (AttributeError, OSError):
            pass


def read_reviews(workspace_root: str) -> List[ReviewEntry]:
    path = review_queue_path(workspace_root)
    if not os.path.exists(path):
        return []
    out: List[ReviewEntry] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(ReviewEntry.from_json_line(line))
    return out
