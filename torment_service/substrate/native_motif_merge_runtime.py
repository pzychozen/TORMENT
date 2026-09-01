"""Qualified outer bridge for one authorized native motif merge.

SQLite owns the semantic mutation.  The caller-owned M1 workflow store owns
suggestion status and JSONL events, so this bridge returns after SQLite only
and deliberately has no file-system responsibilities.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from .errors import SubstrateObjectNotFound
from .fabric_native_routing import NativeFabricRoutingScope, NativeMotifProcessOrder
from .motifs import NativeMotifMergeResult, NativeMotifService


class NativeMotifMergeRuntime:
    """Claimed-scope mutation port consumed by native maintenance only."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        routing_scope: NativeFabricRoutingScope,
        domain_id: str,
        process_order: NativeMotifProcessOrder,
    ) -> None:
        if not isinstance(routing_scope, NativeFabricRoutingScope):
            raise ValueError("native motif merge requires a claimed routing scope")
        if not isinstance(domain_id, str) or not domain_id:
            raise ValueError("native motif merge requires a domain_id")
        if not isinstance(process_order, NativeMotifProcessOrder):
            raise ValueError("native motif merge requires the process-order owner")
        self._service = NativeMotifService(connection)
        self._scope = routing_scope
        self._domain_id = domain_id
        self._process_order = process_order

    def merge_suggestion(
        self,
        suggestion: dict[str, Any],
        *,
        note: str,
        _test_fail_after: str | None = None,
    ) -> NativeMotifMergeResult | None:
        """Merge the supplied persisted suggestion or report missing native truth.

        ``created_ts`` is the suggestion's durable decision timestamp.  It is
        carried both in the operation key and canonical semantic intent, so a
        retry after SQLite has committed reconstructs exactly the same result.
        """
        try:
            suggestion_id = _text(suggestion, "suggestion_id")
            a = _text(suggestion, "a")
            b = _text(suggestion, "b")
            timestamp = suggestion.get("created_ts")
            if not isinstance(timestamp, int):
                raise ValueError("native motif merge suggestion requires an integer created_ts")
            key = "|".join((
                "NATIVE_MOTIF_MERGE",
                self._scope.runtime_scope.workspace_id,
                self._scope.runtime_scope.scope_kind,
                self._scope.runtime_scope.qualifier,
                self._domain_id,
                str(self._scope.runtime_scope.legacy_source_namespace_id),
                str(self._scope.runtime_scope.semantic_scope_id),
                a,
                b,
                str(timestamp),
                suggestion_id,
            ))
            result = self._service.merge_motifs(
                idempotency_namespace_id=self._scope.idempotency_namespace_id,
                idempotency_key=key,
                legacy_source_namespace_id=self._scope.runtime_scope.legacy_source_namespace_id,
                motif_identity_namespace_id=self._scope.motif_identity_namespace_id,
                motif_alias_namespace_id=self._scope.motif_alias_namespace_id,
                membership_identity_namespace_id=self._scope.membership_identity_namespace_id,
                semantic_scope_id=self._scope.runtime_scope.semantic_scope_id,
                domain_id=self._domain_id,
                a_runtime_motif_id=a,
                b_runtime_motif_id=b,
                merge_timestamp=timestamp,
                _test_fail_after=(
                    _test_fail_after if _test_fail_after not in {
                        "after_sqlite_commit", "after_workflow_status", "after_workflow_event",
                    } else None
                ),
            )
        except SubstrateObjectNotFound:
            return None
        self._process_order.retire_runtime_id(
            routing_scope=self._scope,
            domain_id=self._domain_id,
            runtime_motif_id=result.drop_runtime_motif_id,
        )
        return result


def _text(suggestion: dict[str, Any], key: str) -> str:
    value = suggestion.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"native motif merge suggestion requires {key}")
    return value
