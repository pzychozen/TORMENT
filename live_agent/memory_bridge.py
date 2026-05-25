"""
TORMENT Memory Bridge — HTTP client for the TORMENT Fabric API.

Fetches assembled context (identity + relational + situational + archive)
from a running TORMENT server, then formats it for the base model prompt.
"""

import os
import logging
from typing import Any, Optional

import requests

log = logging.getLogger(__name__)

DEFAULT_TORMENT_URL = "http://127.0.0.1:8787"
DEFAULT_WORKSPACE = "limn"
DEFAULT_AGENT = "limn"
DEFAULT_PROFILE = "companion"
DEFAULT_TOKEN_BUDGET = 2000  # keep small — base model context is precious
DEFAULT_TOP_K = 6


class MemoryBridge:
    """Talks to a running TORMENT Fabric server to retrieve memory context."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        workspace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        self.base_url = (
            base_url
            or os.environ.get("TORMENT_URL", DEFAULT_TORMENT_URL)
        ).rstrip("/")
        self.workspace_id = (
            workspace_id
            or os.environ.get("TORMENT_WORKSPACE", DEFAULT_WORKSPACE)
        )
        self.agent_id = (
            agent_id
            or os.environ.get("TORMENT_AGENT", DEFAULT_AGENT)
        )

    # ── health ──────────────────────────────────────────────────────
    def ping(self) -> bool:
        """Check if the TORMENT server is reachable."""
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    # ── main retrieval ──────────────────────────────────────────────
    def retrieve(
        self,
        query: str,
        *,
        profile: str = DEFAULT_PROFILE,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
        top_k: int = DEFAULT_TOP_K,
        include_assembly_audit: bool = False,
    ) -> dict[str, Any]:
        """Call POST /retrieve for assembled context.

        Returns the full response dict with keys like:
          blocks, character_context, token_count, profile, ...

        When ``include_assembly_audit=True``, the response additionally
        contains an ``assembly_audit`` key per Memory-to-Prompt v0.2
        §4.2 (character-memory observability: what memory shaped the
        character's next response). Default False preserves backward
        compatibility for existing callers.
        """
        payload = {
            "workspace_id": self.workspace_id,
            "agent_id": self.agent_id,
            "query": query,
            "profile": profile,
            "token_budget": token_budget,
            "top_k": top_k,
            "include_assembly_audit": include_assembly_audit,
        }
        try:
            r = requests.post(
                f"{self.base_url}/retrieve",
                json=payload,
                timeout=30,
            )
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            log.warning("Memory retrieval failed: %s", exc)
            return {"blocks": [], "character_context": {}}

    # ── ingest ──────────────────────────────────────────────────────
    def ingest(self, text: str, *, step: Optional[int] = None) -> dict[str, Any]:
        """Ingest new text into TORMENT memory via the Spine."""
        payload: dict[str, Any] = {
            "workspace_id": self.workspace_id,
            "agent_id": self.agent_id,
            "operation": "ingest",
            "payload": {"text": text},
        }
        if step is not None:
            payload["payload"]["step"] = step
        try:
            r = requests.post(
                f"{self.base_url}/spine/submit_task",
                json=payload,
                timeout=30,
            )
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            log.warning("Memory ingest failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    # ── agent state ─────────────────────────────────────────────────
    def get_agent_state(self) -> dict[str, Any]:
        """Query agent state (identity, drift, memory count)."""
        payload = {
            "workspace_id": self.workspace_id,
            "agent_id": self.agent_id,
            "operation": "query_state",
            "payload": {},
        }
        try:
            r = requests.post(
                f"{self.base_url}/spine/submit_task",
                json=payload,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            log.warning("Agent state query failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    # ── formatting ──────────────────────────────────────────────────
    def format_context_for_prompt(self, retrieval_result: dict) -> str:
        """Convert retrieved blocks into a flat text string for the model prompt.

        Produces a character preamble + memory blocks string.
        """
        parts = []

        # Character preamble from seed
        char_ctx = retrieval_result.get("character_context", {})
        preamble = char_ctx.get("seed_preamble", "")
        if preamble:
            parts.append(preamble.strip())

        # Drift status as context signal
        drift = char_ctx.get("drift_score", 0.0)
        if drift and float(drift) > 0.1:
            direction = char_ctx.get("drift_direction", "unknown")
            parts.append(f"[Drift: {drift:.2f} — {direction}]")

        # Spirit return summary if present
        spirit_summary = char_ctx.get("spirit_return_summary", "")
        if spirit_summary:
            parts.append(f"[Spirit: {spirit_summary}]")

        # Memory blocks — /retrieve returns blocks as a dict keyed by
        # block type (identity, relational, situational, archive), each
        # containing a list of dicts with "text" and optional metadata.
        raw_blocks = retrieval_result.get("blocks", {})
        memory_lines = []
        if isinstance(raw_blocks, dict):
            # Dict of lists: {"identity": [...], "relational": [...], ...}
            for category, items in raw_blocks.items():
                if not isinstance(items, list):
                    continue
                for b in items:
                    if isinstance(b, dict):
                        text = b.get("text", "")
                    elif isinstance(b, str):
                        text = b
                    else:
                        continue
                    if text:
                        memory_lines.append(f"[{category}] {text}")
        elif isinstance(raw_blocks, list):
            # Flat list fallback (legacy shape)
            for b in raw_blocks:
                if isinstance(b, dict):
                    text = b.get("text", "")
                    category = b.get("category", "")
                elif isinstance(b, str):
                    text, category = b, ""
                else:
                    continue
                if text:
                    prefix = f"[{category}] " if category else ""
                    memory_lines.append(f"{prefix}{text}")
        if memory_lines:
            parts.append("Memories:\n" + "\n".join(memory_lines))

        return "\n\n".join(parts)

    def get_prompt_context(self, query: str, **kwargs) -> tuple[str, str]:
        """Convenience: retrieve + format in one call.

        Returns (character_preamble, memory_context) for use with
        QwenInference.format_prompt().
        """
        result = self.retrieve(query, **kwargs)
        char_ctx = result.get("character_context", {})
        preamble = char_ctx.get("seed_preamble", "")
        memory_text = self.format_context_for_prompt(result)
        return preamble, memory_text


# ── CLI test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    bridge = MemoryBridge()

    if bridge.ping():
        print("TORMENT server is reachable")
        state = bridge.get_agent_state()
        print(f"Agent state: {json.dumps(state, indent=2)}")

        preamble, context = bridge.get_prompt_context("What do you remember?")
        print(f"\n--- Preamble ---\n{preamble}")
        print(f"\n--- Context ---\n{context}")
    else:
        print("TORMENT server not reachable at", bridge.base_url)
        print("Start it with: cd torment_fabric && python -m torment_service.app")
