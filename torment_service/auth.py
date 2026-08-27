# auth.py — Authentication and trust resolution for TORMENT
#
# Maps API keys to client identities and trust tiers.
# This is the outermost security boundary.
#
# Design:
#   - API keys are loaded from env var or config file
#   - Each key maps to a client_id and trust_tier
#   - Auth is OPTIONAL and controlled by TORMENT_AUTH_ENABLE
#   - When disabled, all requests get a default system-level context
#   - When enabled, missing or invalid keys are rejected
#
# Key format (env var):
#   TORMENT_API_KEYS="key1:client_id1:trust_tier1,key2:client_id2:trust_tier2"
#
# Example:
#   TORMENT_API_KEYS="sk-abc123:claude-mcp:0.6,sk-xyz789:operator:1.0"
#
# The auth middleware creates a RequestContext and attaches it to the
# FastAPI request state for downstream handlers.
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request

from .request_context import (
    RequestContext,
    TRUST_OPERATOR,
    InsufficientTrustError,
)

logger = logging.getLogger("torment.auth")

# ---------------------------------------------------------------------------
# API key store
# ---------------------------------------------------------------------------

@dataclass
class ClientRecord:
    """A registered API key and its associated permissions."""
    client_id: str
    trust_tier: float
    description: str = ""


class APIKeyStore:
    """In-memory store of API key -> ClientRecord mappings.

    Loaded from environment variable or JSON file on startup.
    """

    def __init__(self) -> None:
        self._keys: Dict[str, ClientRecord] = {}
        self._load_from_env()
        self._load_from_file()

    def _load_from_env(self) -> None:
        """Parse TORMENT_API_KEYS env var.

        Format: "key:client_id:trust_tier,key:client_id:trust_tier,..."
        """
        raw = os.environ.get("TORMENT_API_KEYS", "").strip()
        if not raw:
            return
        for entry in raw.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":")
            if len(parts) < 3:
                logger.warning("Skipping malformed API key entry (need key:client:tier format)")
                continue
            key, client_id, tier_str = parts[0], parts[1], parts[2]
            try:
                tier = float(tier_str)
            except ValueError:
                logger.warning("Skipping API key with invalid (non-numeric) trust tier")
                continue
            self._keys[key] = ClientRecord(
                client_id=client_id,
                trust_tier=max(0.0, min(1.0, tier)),
            )
        if self._keys:
            logger.info("Loaded %d API key(s) from environment", len(self._keys))

    def _load_from_file(self) -> None:
        """Load API keys from JSON file if TORMENT_API_KEYS_FILE is set.

        File format:
        [
            {"key": "sk-...", "client_id": "claude", "trust_tier": 0.6, "description": "..."},
            ...
        ]
        """
        path = os.environ.get("TORMENT_API_KEYS_FILE", "").strip()
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
            for entry in entries:
                key = entry.get("key", "").strip()
                client_id = entry.get("client_id", "").strip()
                tier = float(entry.get("trust_tier", 0.0))
                if key and client_id:
                    self._keys[key] = ClientRecord(
                        client_id=client_id,
                        trust_tier=max(0.0, min(1.0, tier)),
                        description=entry.get("description", ""),
                    )
            logger.info("Loaded %d API key(s) from file: %s", len(entries), path)
        except Exception:
            logger.error("Failed to load configured API key file")

    def lookup(self, key: str) -> Optional[ClientRecord]:
        """Look up a client record by API key. Returns None if not found."""
        return self._keys.get(key)

    @property
    def has_keys(self) -> bool:
        """Return True if any API keys are configured."""
        return bool(self._keys)

    def stats(self) -> Dict[str, Any]:
        """Return diagnostic info (never exposes actual keys)."""
        return {
            "configured_keys": len(self._keys),
            "clients": [
                {"client_id": r.client_id, "trust_tier": r.trust_tier}
                for r in self._keys.values()
            ],
        }


# ---------------------------------------------------------------------------
# Singleton store and config
# ---------------------------------------------------------------------------

_key_store: Optional[APIKeyStore] = None

AUTH_ENABLED = os.environ.get("TORMENT_AUTH_ENABLE", "0").strip().lower() in ("1", "true", "yes", "on")

# Default context when auth is disabled — full operator access
_DEFAULT_CLIENT_ID = os.environ.get("TORMENT_DEFAULT_CLIENT_ID", "__local__")


def get_key_store() -> APIKeyStore:
    """Get or create the global API key store."""
    global _key_store
    if _key_store is None:
        _key_store = APIKeyStore()
    return _key_store


# ---------------------------------------------------------------------------
# FastAPI integration
# ---------------------------------------------------------------------------

def resolve_request_context(
    request: Request,
    workspace_id: str = "default",
    agent_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> RequestContext:
    """Resolve a RequestContext from the incoming request.

    When auth is enabled:
      - Reads X-API-Key header (or api_key parameter)
      - Looks up client_id and trust_tier from the key store
      - Rejects unknown keys with 401

    When auth is disabled:
      - Returns a default operator-level context
      - Useful for local development and existing deployments

    This function is called by the REST auth middleware for the outer
    boundary and by endpoint handlers that need workspace/agent-specific
    RequestContext values for Spine trust checks.
    """
    if not AUTH_ENABLED:
        return RequestContext(
            client_id=_DEFAULT_CLIENT_ID,
            trust_tier=TRUST_OPERATOR,
            workspace_id=workspace_id,
            agent_id=agent_id,
        )

    # Try to get key from parameter, then from header
    key = api_key
    if not key:
        key = request.headers.get("x-api-key", "").strip()
    if not key:
        # Check query param as fallback
        key = request.query_params.get("api_key", "").strip()

    if not key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header or api_key parameter.",
        )

    store = get_key_store()
    record = store.lookup(key)
    if record is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    return RequestContext(
        client_id=record.client_id,
        trust_tier=record.trust_tier,
        workspace_id=workspace_id,
        agent_id=agent_id,
    )


def handle_trust_error(e: InsufficientTrustError) -> None:
    """Convert a trust error to an HTTP 403 response."""
    raise HTTPException(
        status_code=403,
        detail=str(e),
    )
