# cognition/apertures.py
"""
Aperture Builder — determines what memory each role sees.

The aperture controls the memory slice available to roles during execution.
Each memory lane (private, shared, deep) is retrieved independently so that
roles receive truly scope-separated context.

Aperture Configuration (from docs/archive/AGENT_SPINE_PLAN.md §8):
  narrow    → private top_k=6,  shared top_k=3,  deep top_k=2, character=seed_only
  broad     → private top_k=12, shared top_k=8,  deep top_k=4, character=full
  protected → private top_k=4,  shared top_k=2,  deep top_k=0, character=full+drift

The aperture builder is decoupled from fabric — it receives a LaneQueryProvider
(or legacy query_fn mock) so it can be tested without a running server.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional

from torment_service.scoring import derive_provenance_type as _derive_prov_type


# ============================================================================
# Aperture configuration table
# ============================================================================

@dataclass(frozen=True)
class ApertureConfig:
    """Immutable configuration for a single aperture type."""
    name: str
    private_top_k: int
    shared_top_k: int
    deep_top_k: int = 0         # deep/spirit-return budget (v2.4.4)
    depth: int = 1              # memory retrieval depth (layer count)
    character_mode: str = "seed_only"  # "seed_only" | "full" | "full_drift"

    @property
    def include_drift(self) -> bool:
        return self.character_mode == "full_drift"

    @property
    def include_full_character(self) -> bool:
        return self.character_mode in ("full", "full_drift")


APERTURE_CONFIGS: Dict[str, ApertureConfig] = {
    "narrow": ApertureConfig(
        name="narrow",
        private_top_k=6,
        shared_top_k=3,
        deep_top_k=2,
        depth=1,
        character_mode="seed_only",
    ),
    "broad": ApertureConfig(
        name="broad",
        private_top_k=12,
        shared_top_k=8,
        deep_top_k=4,
        depth=2,
        character_mode="full",
    ),
    "protected": ApertureConfig(
        name="protected",
        private_top_k=4,
        shared_top_k=2,
        deep_top_k=0,       # conservative: no compressed/lossy memories
        depth=1,             # for identity-sensitive routes
        character_mode="full_drift",
    ),
}


# ============================================================================
# Memory context — the output of the aperture builder
# ============================================================================

@dataclass
class MemoryContext:
    """Structured memory context assembled by the aperture builder.

    This is what roles receive as their 'view' of memory.
    Roles cannot query memory directly — they only see what the aperture grants.
    (Invariant D: aperture is bounded.)

    Since v2.4.4, private_memories, shared_memories, and deep_memories
    are truly lane-separated when built via LaneQueryProvider.
    """
    aperture_name: str
    config: ApertureConfig
    private_memories: List[Dict[str, Any]] = field(default_factory=list)
    shared_memories: List[Dict[str, Any]] = field(default_factory=list)
    deep_memories: List[Dict[str, Any]] = field(default_factory=list)
    character_context: Optional[Dict[str, Any]] = None  # seed or full
    drift_snapshot: Optional[Dict[str, Any]] = None     # only for protected
    domain_id: Optional[str] = None
    query_text: str = ""

    @property
    def total_memories(self) -> int:
        return len(self.private_memories) + len(self.shared_memories) + len(self.deep_memories)

    @property
    def has_character_context(self) -> bool:
        return self.character_context is not None

    @property
    def has_drift_snapshot(self) -> bool:
        return self.drift_snapshot is not None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "aperture_name": self.aperture_name,
            "config": asdict(self.config),
            "private_memories": self.private_memories,
            "shared_memories": self.shared_memories,
            "deep_memories": self.deep_memories,
            "character_context": self.character_context,
            "drift_snapshot": self.drift_snapshot,
            "domain_id": self.domain_id,
            "query_text": self.query_text,
            "total_memories": self.total_memories,
        }
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryContext":
        if not d:
            raise ValueError("Cannot create MemoryContext from empty dict")
        config_d = d.get("config", {})
        config = ApertureConfig(**{
            k: v for k, v in config_d.items()
            if k in {f.name for f in ApertureConfig.__dataclass_fields__.values()}
        }) if config_d else APERTURE_CONFIGS.get(d.get("aperture_name", "narrow"),
                                                  APERTURE_CONFIGS["narrow"])
        return cls(
            aperture_name=d.get("aperture_name", "narrow"),
            config=config,
            private_memories=d.get("private_memories", []),
            shared_memories=d.get("shared_memories", []),
            deep_memories=d.get("deep_memories", []),
            character_context=d.get("character_context"),
            drift_snapshot=d.get("drift_snapshot"),
            domain_id=d.get("domain_id"),
            query_text=d.get("query_text", ""),
        )


# ============================================================================
# Lane query provider (v2.4.4)
# ============================================================================

@dataclass
class LaneQueryProvider:
    """Provides lane-specific memory retrieval for aperture building.

    Each callable returns a list of hit dicts scoped to its lane.
    If a callable is None, that lane returns empty results.

    Signatures:
        private_fn(workspace_id, agent_id, query_text, top_k) -> list[dict]
        shared_fn(workspace_id, agent_id, query_text, top_k, domain_id) -> (list[dict], list[str])
        deep_fn(workspace_id, agent_id, query_text, top_k) -> list[dict]

    shared_fn returns a tuple of (hits, bridge_peek_domains).
    """
    private_fn: Optional[Callable] = None
    shared_fn: Optional[Callable] = None
    deep_fn: Optional[Callable] = None


# ============================================================================
# Legacy query function type (backward compat for tests)
# ============================================================================
# The aperture builder still accepts a legacy query function with this signature:
#   query_fn(workspace_id, agent_id, query_text, top_k, domain_id) -> dict
# In production, use LaneQueryProvider instead. The legacy path calls
# query_fn twice and returns mixed results (pre-v2.4.4 behavior).

QueryFn = Callable[..., Dict[str, Any]]


# ============================================================================
# Aperture builder
# ============================================================================

def get_config(aperture_name: str) -> ApertureConfig:
    """Look up aperture config by name. Raises ValueError if unknown."""
    if aperture_name not in APERTURE_CONFIGS:
        raise ValueError(
            f"Unknown aperture '{aperture_name}'. "
            f"Must be one of: {sorted(APERTURE_CONFIGS.keys())}"
        )
    return APERTURE_CONFIGS[aperture_name]


def build_memory_context(
    aperture_name: str,
    workspace_id: str,
    agent_id: str,
    query_text: str,
    domain_id: Optional[str] = None,
    lane_provider: Optional[LaneQueryProvider] = None,
    query_fn: Optional[QueryFn] = None,
    character_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    drift_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> MemoryContext:
    """Build a MemoryContext by querying memory through the aperture lens.

    Parameters
    ----------
    aperture_name : str
        One of "narrow", "broad", "protected".
    workspace_id, agent_id, query_text : str
        Required context for memory queries.
    domain_id : str, optional
        Target domain for queries. If None, fabric decides routing.
    lane_provider : LaneQueryProvider, optional
        Lane-specific query provider (v2.4.4). When provided, each
        memory lane is retrieved independently — private_memories,
        shared_memories, and deep_memories are truly scope-separated.
        Takes precedence over query_fn.
    query_fn : callable, optional
        Legacy memory query function — wraps fabric.query() in older
        callers. Both calls return mixed private+shared+deep results.
        Only used if lane_provider is None.
        Signature: (workspace_id, agent_id, query_text, top_k, domain_id) -> dict
    character_fn : callable, optional
        Character context retrieval function.
        Signature: (workspace_id, agent_id) -> dict
        If None, character_context will be None.
    drift_fn : callable, optional
        Drift snapshot retrieval function (only called for protected aperture).
        Signature: (workspace_id, agent_id) -> dict
        If None, drift_snapshot will be None.

    Returns
    -------
    MemoryContext
    """
    config = get_config(aperture_name)

    private_memories: List[Dict[str, Any]] = []
    shared_memories: List[Dict[str, Any]] = []
    deep_memories: List[Dict[str, Any]] = []
    character_context: Optional[Dict[str, Any]] = None
    drift_snapshot: Optional[Dict[str, Any]] = None

    # --- Lane-aware retrieval (v2.4.4) ---
    if lane_provider is not None:
        # Private lane
        if lane_provider.private_fn is not None:
            try:
                private_memories = lane_provider.private_fn(
                    workspace_id, agent_id, query_text,
                    config.private_top_k,
                )
                private_memories = private_memories[:config.private_top_k]
            except Exception:
                private_memories = []

        # Shared lane
        if lane_provider.shared_fn is not None:
            try:
                result = lane_provider.shared_fn(
                    workspace_id, agent_id, query_text,
                    config.shared_top_k, domain_id,
                )
                # shared_fn returns (hits, bridge_peek_domains)
                if isinstance(result, tuple):
                    shared_memories = result[0][:config.shared_top_k]
                else:
                    shared_memories = result[:config.shared_top_k]
            except Exception:
                shared_memories = []

        # Deep lane
        if lane_provider.deep_fn is not None and config.deep_top_k > 0:
            try:
                deep_memories = lane_provider.deep_fn(
                    workspace_id, agent_id, query_text,
                    config.deep_top_k,
                )
                deep_memories = deep_memories[:config.deep_top_k]
            except Exception:
                deep_memories = []

    # --- Legacy path (pre-v2.4.4): query_fn returns mixed results ---
    elif query_fn is not None:
        try:
            private_result = query_fn(
                workspace_id, agent_id, query_text,
                config.private_top_k, domain_id,
            )
            private_memories = _extract_memories(private_result, config.private_top_k)
        except Exception:
            private_memories = []

        try:
            shared_result = query_fn(
                workspace_id, agent_id, query_text,
                config.shared_top_k, domain_id,
            )
            shared_memories = _extract_memories(shared_result, config.shared_top_k)
        except Exception:
            shared_memories = []

    # Character context
    if config.include_full_character and character_fn is not None:
        try:
            character_context = character_fn(workspace_id, agent_id)
        except Exception:
            character_context = None
    elif not config.include_full_character and character_fn is not None:
        # seed_only mode — request character but mark as seed-only
        try:
            full = character_fn(workspace_id, agent_id)
            if full is not None:
                character_context = {"seed_only": True, "data": full}
        except Exception:
            character_context = None

    # Drift snapshot — only for protected aperture
    if config.include_drift and drift_fn is not None:
        try:
            drift_snapshot = drift_fn(workspace_id, agent_id)
        except Exception:
            drift_snapshot = None

    # --- Provenance classification stamp (v2.4.4 read-surface audit) ---
    # Lane functions return raw hits with payload-level 'provenance' but
    # no extracted 'provenance_type' badge.  Stamp it here so roles can
    # distinguish collective echoes from organic autobiographical memory.
    private_memories = _stamp_provenance_type(private_memories)
    shared_memories = _stamp_provenance_type(shared_memories)
    deep_memories = _stamp_provenance_type(deep_memories)

    return MemoryContext(
        aperture_name=aperture_name,
        config=config,
        private_memories=private_memories,
        shared_memories=shared_memories,
        deep_memories=deep_memories,
        character_context=character_context,
        drift_snapshot=drift_snapshot,
        domain_id=domain_id,
        query_text=query_text,
    )


def _stamp_provenance_type(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Stamp a ``provenance_type`` badge on lane hits that lack one.

    Lane functions return raw search results with a payload-level
    ``provenance`` field but no extracted ``provenance_type``.  This
    helper derives the compact badge via the canonical
    ``derive_provenance_type`` rule in ``scoring.py`` so downstream
    consumers (roles, assembler) can distinguish collective echoes
    from organic memory without parsing the raw provenance dict.

    Mutates hits in place for efficiency; also returns the list.
    """
    for h in hits:
        if "provenance_type" in h:
            continue  # already badged (e.g. came from fabric.query())
        h["provenance_type"] = _derive_prov_type(h.get("provenance"))
    return hits


def _extract_memories(query_result: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    """Extract memory entries from a fabric.query() result dict.

    fabric.query() returns a dict with various keys. We look for
    'results' or 'memories' list and cap at `limit`.

    Used by the legacy query_fn path only.
    """
    if not isinstance(query_result, dict):
        return []

    # Try common result keys from fabric.query()
    for key in ("results", "memories", "entries", "blocks"):
        items = query_result.get(key)
        if isinstance(items, list):
            return items[:limit]

    return []
