# domain_policies.py
from __future__ import annotations
from typing import Dict, Any

DEFAULT_DOMAIN_POLICIES: Dict[str, Dict[str, Any]] = {
    "research": {
        "auto_propose_max_per_window": 8,
        "auto_propose_min_gap_s": 10,
        "auto_propose_min_promotion": 0.78,
        "auto_propose_min_strength": 0.80,
        "auto_propose_min_confidence": 0.70,
        "auto_propose_require_novelty": False,
        "shared_min_distinct_agents": 2,
        "bridge_peek_requires_approval": False,        "motif_entropy_target_n": 24,
        "motif_entropy_high": 0.72,
        "motif_merge_similarity": 0.93,
        "motif_merge_max_suggestions": 20,
        "auto_merge_motifs": False,
        "auto_merge_entropy_trigger": 0.80,
    },
    "engineering": {
        "auto_propose_max_per_window": 6,
        "auto_propose_min_gap_s": 15,
        "auto_propose_min_promotion": 0.80,
        "auto_propose_min_strength": 0.82,
        "auto_propose_min_confidence": 0.72,
        "auto_propose_require_novelty": False,
        "shared_min_distinct_agents": 2,
        "bridge_peek_requires_approval": False,        "motif_entropy_target_n": 24,
        "motif_entropy_high": 0.72,
        "motif_merge_similarity": 0.93,
        "motif_merge_max_suggestions": 20,
        "auto_merge_motifs": False,
        "auto_merge_entropy_trigger": 0.80,
    },
    "operations": {
        "auto_propose_max_per_window": 3,
        "auto_propose_min_gap_s": 30,
        "auto_propose_min_promotion": 0.85,
        "auto_propose_min_strength": 0.85,
        "auto_propose_min_confidence": 0.80,
        "auto_propose_require_novelty": True,
        "shared_min_distinct_agents": 3,
        "bridge_peek_requires_approval": True,        "motif_entropy_target_n": 24,
        "motif_entropy_high": 0.72,
        "motif_merge_similarity": 0.93,
        "motif_merge_max_suggestions": 20,
        "auto_merge_motifs": False,
        "auto_merge_entropy_trigger": 0.80,
    },
    "creative": {
        "auto_propose_max_per_window": 10,
        "auto_propose_min_gap_s": 8,
        "auto_propose_min_promotion": 0.74,
        "auto_propose_min_strength": 0.78,
        "auto_propose_min_confidence": 0.60,
        "auto_propose_require_novelty": False,
        "shared_min_distinct_agents": 2,
        "bridge_peek_requires_approval": False,        "motif_entropy_target_n": 24,
        "motif_entropy_high": 0.72,
        "motif_merge_similarity": 0.93,
        "motif_merge_max_suggestions": 20,
        "auto_merge_motifs": True,
        "auto_merge_entropy_trigger": 0.80,
    },
    "meta": {
        "auto_propose_max_per_window": 2,
        "auto_propose_min_gap_s": 60,
        "auto_propose_min_promotion": 0.90,
        "auto_propose_min_strength": 0.90,
        "auto_propose_min_confidence": 0.85,
        "auto_propose_require_novelty": True,
        "shared_min_distinct_agents": 3,
        "bridge_peek_requires_approval": True,        "motif_entropy_target_n": 24,
        "motif_entropy_high": 0.72,
        "motif_merge_similarity": 0.93,
        "motif_merge_max_suggestions": 20,
        "auto_merge_motifs": False,
        "auto_merge_entropy_trigger": 0.80,
    },
    # Single-agent / companion default domain.
    # Relaxed thresholds — one agent's memories don't need multi-agent governance.
    "personal": {
        "auto_propose_max_per_window": 12,
        "auto_propose_min_gap_s": 5,
        "auto_propose_min_promotion": 0.70,
        "auto_propose_min_strength": 0.75,
        "auto_propose_min_confidence": 0.55,
        "auto_propose_require_novelty": False,
        "shared_min_distinct_agents": 1,
        "bridge_peek_requires_approval": False,
        "motif_entropy_target_n": 24,
        "motif_entropy_high": 0.72,
        "motif_merge_similarity": 0.93,
        "motif_merge_max_suggestions": 20,
        "auto_merge_motifs": True,
        "auto_merge_entropy_trigger": 0.80,
    },
}


# The posture selects initial policy only. It is never consulted by startup or
# Genesis recovery, and grants no authority to restore a later operator policy.
SOLO_PRIVATE_POSTURE = "solo_private_v1"

# Frozen v1 document shape, not another set of semantic defaults. Saved setup
# requests retain their full policy bytes when default values change later.
_SOLO_V1_FIELD_TYPES = {
    "auto_propose_max_per_window": int,
    "auto_propose_min_gap_s": int,
    "auto_propose_min_promotion": float,
    "auto_propose_min_strength": float,
    "auto_propose_min_confidence": float,
    "auto_propose_require_novelty": bool,
    "shared_min_distinct_agents": int,
    "bridge_peek_requires_approval": bool,
    "motif_entropy_target_n": int,
    "motif_entropy_high": float,
    "motif_merge_similarity": float,
    "motif_merge_max_suggestions": int,
    "auto_merge_motifs": bool,
    "auto_merge_entropy_trigger": float,
}


def validate_initial_policy(raw: bytes, posture: str) -> dict:
    """Validate frozen initial evidence without re-resolving live defaults."""
    from .external_owner_json import exact_keys, require, strict_object

    require(posture == SOLO_PRIVATE_POSTURE, "unsupported initial domain-policy posture")
    value = strict_object(raw)
    exact_keys(value, ("policies",), "domain policy document")
    exact_keys(value["policies"], ("personal",), "posture domains")
    personal = exact_keys(value["policies"]["personal"], _SOLO_V1_FIELD_TYPES, "complete personal policy")
    for field, kind in _SOLO_V1_FIELD_TYPES.items():
        require(type(personal[field]) is kind, f"invalid personal policy field: {field}")
    require(personal["auto_merge_motifs"] is False, "initial Solo posture requires auto-merge disabled")
    return value


def resolve_initial_policy(posture: str) -> bytes:
    """Materialize all current personal defaults once, changing only auto-merge."""
    from .external_owner_json import owner_bytes, require

    require(posture == SOLO_PRIVATE_POSTURE, "unsupported initial domain-policy posture")
    personal = dict(DEFAULT_DOMAIN_POLICIES["personal"])
    personal["auto_merge_motifs"] = False
    raw = owner_bytes({"policies": {"personal": personal}})
    validate_initial_policy(raw, posture)
    return raw


def initial_policy_path(*, data_dir: str, workspace_id: str):
    """Read existing workspace declarations; never create a workspace or domain."""
    import os
    from pathlib import Path
    from .external_owner_json import logical_id, read_optional_owner, require, require_exact_owner_path, strict_object
    from .pathing import approved_subdir, stable_filename
    from .workspace_declaration import validate_domains, validate_workspace_meta

    logical_id(workspace_id, "workspace_id")
    root = os.path.realpath(data_dir)
    workspace = approved_subdir(root, "workspaces", workspace_id, mkdir=False)

    def child(name):
        return Path(require_exact_owner_path(stable_filename(workspace, name),
            os.path.join(root, "workspaces", workspace_id, name)))

    metadata = read_optional_owner(child("workspace_meta.json"))
    domains = read_optional_owner(child("domains.json"))
    require(metadata is not None and domains is not None, "existing workspace declaration required")
    require(validate_workspace_meta(strict_object(metadata))["workspace_id"] == workspace_id,
        "workspace identity conflicts")
    require(validate_domains(strict_object(domains))["domains"] == ["personal"],
        "Solo posture requires exactly the declared personal domain")
    return child("domain_policies.json")


def verify_initial_policy(*, data_dir: str, workspace_id: str, posture: str, expected: bytes):
    """Explicit initial replay only; differing bytes refuse, including formatting."""
    from .external_owner_json import read_optional_owner, require

    validate_initial_policy(expected, posture)
    path = initial_policy_path(data_dir=data_dir, workspace_id=workspace_id)
    observed = read_optional_owner(path)
    require(observed is not None, "initial domain policy is absent")
    validate_initial_policy(observed, posture)
    require(observed == expected, "initial domain policy conflicts with frozen setup request")
    return path


def create_or_verify_initial_policy(*, data_dir: str, workspace_id: str, posture: str, expected: bytes):
    """Create complete bytes without replacement; an existing target must match."""
    from .atomic_publication import publish_if_absent
    from .external_owner_json import read_optional_owner

    validate_initial_policy(expected, posture)
    path = initial_policy_path(data_dir=data_dir, workspace_id=workspace_id)
    if read_optional_owner(path) is None:
        publish_if_absent(path, expected)
    return verify_initial_policy(data_dir=data_dir, workspace_id=workspace_id, posture=posture, expected=expected)
