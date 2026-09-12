"""Explicit initial policy setup after Native Genesis activation, before startup.

python -m torment_service.domain_policy_setup prepare|create|verify
    --data-root ROOT --workspace WORKSPACE --posture solo_private_v1|hivemind_initial_v1
    --request EXTERNAL_REQUEST.json

Prepare freezes owner-resolved policy bytes and the active installation identity
outside the data root. Create and verify consume those bytes without consulting
current defaults. All commands are explicit operator actions, never startup or
Genesis recovery hooks. Later policy mutation is outside this initial lane.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from . import domain_policies as policies
from .atomic_publication import publish_if_absent
from .external_owner_json import exact_json, exact_keys, logical_id, owner_bytes, read_optional_owner, require, strict_object
from .substrate.genesis_fence import canonical_genesis_root
from .substrate.genesis_onboarding import _regular_path
from .substrate.genesis_recovery import recover_active_native_genesis


CONTRACT = "TORMENT_INITIAL_DOMAIN_POLICY_SETUP"
VERSION = 1
_FACTS = ("contract", "version", "data_root_identity", "workspace_id", "posture", "genesis_intent_digest",
          "policy_json", "policy_sha256")


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _operation_key(value):
    return "initial-domain-policy-v1:" + _digest(exact_json({k: value[k] for k in _FACTS}).encode("utf-8"))


def _validate_request(value, *, domains=None):
    exact_keys(value, (*_FACTS, "operation_key"), "initial policy setup request")
    require(value["contract"] == CONTRACT and type(value["version"]) is int and value["version"] == VERSION,
        "unsupported policy setup contract")
    logical_id(value["workspace_id"], "workspace_id")
    require(type(value["data_root_identity"]) is str and os.path.isabs(value["data_root_identity"]),
        "explicit absolute data root required")
    require(type(value["genesis_intent_digest"]) is str and len(value["genesis_intent_digest"]) == 64
        and all(c in "0123456789abcdef" for c in value["genesis_intent_digest"]), "invalid installation identity")
    require(type(value["policy_json"]) is str, "frozen policy JSON required")
    raw = value["policy_json"].encode("utf-8")
    policies.validate_initial_policy(raw, value["posture"], domains=domains)
    require(value["policy_sha256"] == _digest(raw), "policy digest conflicts")
    require(value["operation_key"] == _operation_key(value), "policy operation identity conflicts")
    return value


def _active_facts(data_root, workspace_id, posture):
    require(isinstance(data_root, (str, Path)) and os.path.isabs(data_root), "explicit absolute data root required")
    logical_id(workspace_id, "workspace_id")
    require(posture in (policies.SOLO_PRIVATE_POSTURE, policies.HIVEMIND_INITIAL_POSTURE),
        "unsupported initial domain-policy posture")
    root = canonical_genesis_root(data_root)
    # Full existing recovery verifies selector/core/completion agreement and
    # admitted declarations. It does not inspect policy or construct a model.
    authority = recover_active_native_genesis(data_root=root)
    intent = authority.completion.expanded_intent
    value = intent.payload()
    require(value["workspace"]["workspace_id"] == workspace_id, "workspace is not admitted by this installation")
    if posture == policies.SOLO_PRIVATE_POSTURE:
        require(intent.VERSION == 1, "Solo initial posture requires Genesis v1")
        require(value["agent"]["private_motif_domain_id"] == "personal", "private motif domain is not personal")
        domains = None
    else:
        require(intent.VERSION == 2, "Hivemind initial posture requires Genesis v2")
        domains = tuple(value["workspace"]["ordered_domains"])
    policies.initial_policy_path(data_dir=str(root), workspace_id=workspace_id, posture=posture, domains=domains)
    return root, intent.digest, domains


def _bound_request(value, *, root, workspace_id, posture, installation, domains=None):
    _validate_request(value, domains=domains)
    require((value["data_root_identity"], value["workspace_id"], value["posture"], value["genesis_intent_digest"])
        == (str(root), workspace_id, posture, installation), "policy request belongs to another declaration or installation")
    return value


def prepare_policy_setup(*, data_root, workspace_id, posture, request_path):
    root, installation, domains = _active_facts(data_root, workspace_id, posture)
    target = _regular_path(request_path, root=root)
    observed = read_optional_owner(target)
    if observed is not None:
        # The saved request, not today's defaults, supplies replay expectation.
        value = _bound_request(strict_object(observed), root=root, workspace_id=workspace_id,
            posture=posture, installation=installation, domains=domains)
    else:
        raw = policies.resolve_initial_policy(posture, domains=domains)
        value = dict(contract=CONTRACT, version=VERSION, data_root_identity=str(root), workspace_id=workspace_id,
            posture=posture, genesis_intent_digest=installation, policy_json=raw.decode("utf-8"), policy_sha256=_digest(raw))
        value["operation_key"] = _operation_key(value)
        _validate_request(value, domains=domains)
    # A conflicting existing policy cannot be adopted even by prepare.
    path = policies.initial_policy_path(data_dir=str(root), workspace_id=workspace_id, posture=posture, domains=domains)
    if read_optional_owner(path) is not None:
        policies.verify_initial_policy(data_dir=str(root), workspace_id=workspace_id,
            posture=posture, expected=value["policy_json"].encode("utf-8"), domains=domains)
    if observed is None:
        _regular_path(target, root=root)
        publish_if_absent(target, owner_bytes(value))
    saved = _bound_request(strict_object(read_optional_owner(target)), root=root, workspace_id=workspace_id,
        posture=posture, installation=installation, domains=domains)
    require(exact_json(saved) == exact_json(value), "concurrent policy setup request conflicts")
    return saved


def execute_policy_setup(*, data_root, workspace_id, posture, request_path, verify_only=False):
    root, installation, domains = _active_facts(data_root, workspace_id, posture)
    target = _regular_path(request_path, root=root, required=True)
    value = _bound_request(strict_object(read_optional_owner(target)), root=root, workspace_id=workspace_id,
        posture=posture, installation=installation, domains=domains)
    operation = policies.verify_initial_policy if verify_only else policies.create_or_verify_initial_policy
    path = operation(data_dir=str(root), workspace_id=workspace_id, posture=posture,
        expected=value["policy_json"].encode("utf-8"), domains=domains)
    # Re-read active owner truth before reporting success. No policy opinion is
    # added to that owner; this check belongs solely to the explicit command.
    require(_active_facts(root, workspace_id, posture) == (root, installation, domains), "installation changed during policy setup")
    return dict(status="VERIFIED" if verify_only else "CREATED_OR_VERIFIED", operation_key=value["operation_key"],
        policy_sha256=value["policy_sha256"], policy_path=str(path))


def main(argv=None, *, stdout=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("prepare", "create", "verify"))
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--posture", required=True, choices=(policies.SOLO_PRIVATE_POSTURE, policies.HIVEMIND_INITIAL_POSTURE))
    parser.add_argument("--request", required=True, help="Frozen operator request outside the data root; keep for initial retries")
    args = parser.parse_args(argv)
    try:
        kwargs = dict(data_root=args.data_root, workspace_id=args.workspace, posture=args.posture, request_path=args.request)
        if args.command == "prepare":
            value = prepare_policy_setup(**kwargs)
            result = dict(status="PREPARED", operation_key=value["operation_key"], policy_sha256=value["policy_sha256"])
        else:
            result = execute_policy_setup(**kwargs, verify_only=args.command == "verify")
    except Exception:
        result = dict(status="CONFLICT", error="INITIAL_DOMAIN_POLICY_INPUT_OR_EVIDENCE_REFUSED")
    (sys.stdout if stdout is None else stdout).write(json.dumps(result, sort_keys=True) + "\n")
    return 2 if result["status"] == "CONFLICT" else 0


if __name__ == "__main__":
    raise SystemExit(main())
