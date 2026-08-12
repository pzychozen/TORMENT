"""Append-only Archive document lifecycle replay."""
from __future__ import annotations

import json
import os
from typing import Dict


DOCUMENT_INGESTED = "DOCUMENT_INGESTED"
DOCUMENT_DELETED = "DOCUMENT_DELETED"


def replay_document_lifecycle(events_path: str) -> Dict[str, bool]:
    """Return the final active state for each Archive document event.

    Events are processed in file order: an ingest activates a document and a
    deletion deactivates it. Documents absent from the returned mapping have
    no lifecycle event and remain active for legacy compatibility.
    """
    lifecycle: Dict[str, bool] = {}
    if not events_path or not os.path.exists(events_path):
        return lifecycle

    with open(events_path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue

            doc_id = event.get("doc_id")
            event_type = event.get("type")
            if not isinstance(doc_id, str) or not doc_id:
                continue
            if event_type == DOCUMENT_INGESTED:
                lifecycle[doc_id] = True
            elif event_type == DOCUMENT_DELETED:
                lifecycle[doc_id] = False

    return lifecycle
