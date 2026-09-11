"""Canonical workspace_meta/domains payload owner and onboarding publication.

Workspace uses these same payload builders for its ordinary persistence path.
Its existing permissive loading/default behavior is unchanged. Only onboarding
uses strict verification. Publication order is metadata, then domains; matching
metadata alone is the only permitted two-file precursor. No legacy stores,
policies, graphs, registries or suggestions are initialized here.
"""

from dataclasses import dataclass
import os

from .atomic_publication import publish_if_absent
from .external_owner_json import (
    exact_json, exact_keys, integer, logical_id, nonempty_text, owner_bytes,
    read_optional_owner, require, require_exact_owner_path, strict_object,
)
from .pathing import approved_subdir, stable_filename


def workspace_meta_payload(*, workspace_id, created_ts, embed_dim, embed_provider, embed_model):
    """Existing five-field format, without adding defaults or coercing values."""
    return dict(workspace_id=workspace_id, created_ts=created_ts, embed_dim=embed_dim,
                embed_provider=embed_provider, embed_model=embed_model)


def domains_payload(domains):
    """Existing ordered declaration format; order is semantic."""
    return {"domains": list(domains)}


def validate_workspace_meta(value):
    exact_keys(value, ("workspace_id", "created_ts", "embed_dim", "embed_provider", "embed_model"), "workspace metadata")
    logical_id(value["workspace_id"], "workspace_id")
    integer(value["created_ts"], "created_ts")
    integer(value["embed_dim"], "embed_dim", minimum=1)
    nonempty_text(value["embed_provider"], "embed_provider")
    nonempty_text(value["embed_model"], "embed_model")
    return value


def validate_domains(value):
    exact_keys(value, ("domains",), "domain declaration")
    domains = value["domains"]
    require(type(domains) is list and bool(domains), "domains must be a nonempty ordered array")
    for domain in domains:
        logical_id(domain, "domain_id")
    require(len(set(domains)) == len(domains), "duplicate domain declaration")
    return value


@dataclass(frozen=True)
class WorkspaceDeclaration:
    """Already-expanded stable I1 facts; this type supplies no defaults."""

    workspace_id: str
    workspace_created_ts: int
    representation_dimension: int
    representation_provider: str
    representation_model: str
    ordered_domains: tuple[str, ...]

    def __post_init__(self):
        require(type(self.ordered_domains) is tuple, "ordered_domains must be an immutable tuple")
        validate_workspace_meta(self.metadata_payload())
        validate_domains(self.domain_payload())

    def metadata_payload(self):
        return workspace_meta_payload(workspace_id=self.workspace_id, created_ts=self.workspace_created_ts,
                                      embed_dim=self.representation_dimension, embed_provider=self.representation_provider,
                                      embed_model=self.representation_model)

    def domain_payload(self):
        return domains_payload(self.ordered_domains)


def create_or_verify_workspace_declaration(*, data_dir: str, expected: WorkspaceDeclaration) -> WorkspaceDeclaration:
    """Create the two owners in order, or strictly verify without rewriting."""
    require(isinstance(expected, WorkspaceDeclaration), "expected declaration must be typed")
    root = os.path.realpath(data_dir)
    workspace = approved_subdir(root, "workspaces", expected.workspace_id, mkdir=False)
    paths = [require_exact_owner_path(stable_filename(workspace, name),
                                     os.path.join(root, "workspaces", expected.workspace_id, name))
             for name in ("workspace_meta.json", "domains.json")]
    wanted = (expected.metadata_payload(), expected.domain_payload())
    validators = (validate_workspace_meta, validate_domains)
    observed = [read_optional_owner(path) for path in paths]
    require(observed[0] is not None or observed[1] is None, "domains without metadata is not an onboarding precursor")
    for raw, value, validate in zip(observed, wanted, validators):
        if raw is not None:
            require(exact_json(validate(strict_object(raw))) == exact_json(value), "workspace declaration conflicts with intent")
    for path, raw, value, validate in zip(paths, observed, wanted, validators):
        if raw is None:
            # Sink-local containment recheck before creating owner directories.
            parent = os.path.realpath(os.path.dirname(path))
            require(parent.startswith(root + os.sep), "workspace owner escaped data root")
            os.makedirs(parent, exist_ok=True)
            publish_if_absent(path, owner_bytes(value))
        current = read_optional_owner(path)
        require(current is not None and exact_json(validate(strict_object(current))) == exact_json(value),
                "workspace publication conflicts with intent")
    return expected
