"""Supported local operator entry point: python -m torment_service.native_genesis.

plan --request REQUEST.json --intent INTENT.json
apply --intent INTENT.json --operator-attestation TEXT --issuer-reference TEXT
      --confirm-all-offline-conditions --public-listener http://HOST:PORT
create combines plan and apply; --request and --intent are both required.
status --data-root ROOT is read-only. apply/create accept --profile-out FILE.

Confirmation covers the entire operation: service, MCP, other direct tools and
Fabric hosts are stopped, root jobs and the named public listener are absent. This is
human confirmation, not an automatic process census. All operator artifacts
must be regular files outside ROOT with existing, non-redirected parents.
"""
from __future__ import annotations

import argparse
import json
import sys

from .substrate import genesis_onboarding as onboarding
from .substrate.genesis_administration import _noop


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # Arguments can include private attestation text. Do not echo them.
        raise onboarding.NativeGenesisOnboardingRefused("invalid operator command inputs")


class _EnvironmentEmbedder:
    """Only an enabled planting path touches this explicit CLI dependency."""
    def __init__(self):
        self._delegate = None

    def __getattr__(self, name):
        if self._delegate is None:
            from .embeddings import build_embedder_from_env
            self._delegate = build_embedder_from_env()
        return getattr(self._delegate, name)


def _parser():
    parser = _Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for command in ("plan", "apply", "create"):
        child = commands.add_parser(command)
        child.add_argument("--intent", required=True, help="Frozen external GenesisIntent file; never inside the data root")
        if command != "apply":
            child.add_argument("--request", required=True, help="Strict version-1 or version-2 operator declaration JSON")
        if command != "plan":
            child.add_argument("--operator-attestation", required=True)
            child.add_argument("--issuer-reference", required=True)
            child.add_argument("--public-listener", required=True, help="Configured public TORMENT listener, including scheme, host and port")
            child.add_argument("--confirm-all-offline-conditions", action="store_true", required=True,
                help="For the entire operation I confirm service, MCP, other direct tools and Fabric hosts STOPPED, root jobs ABSENT, and the named public listener ABSENT")
            child.add_argument("--profile-out", help="Optional external seven-field startup profile JSON; no overwrite")
    status = commands.add_parser("status")
    status.add_argument("--data-root", required=True)
    return parser


def _execute(args, *, fault=_noop, embedder_factory=_EnvironmentEmbedder):
    if args.command == "status":
        return onboarding.native_genesis_status(data_root=args.data_root)
    if args.command in ("plan", "create"):
        request = onboarding.read_onboarding_request(args.request)
        intent = onboarding.prepare_intent_plan(request, intent_path=args.intent, request_path=args.request)
        fault("after-intent-publication")
        if args.command == "plan":
            return dict(status="PLANNED", data_root=intent.data_root_identity, operation_key=intent.operation_key,
                intent_digest=intent.digest, intent_path=str(onboarding._regular_path(args.intent, required=True)))
    else:
        intent = onboarding.read_intent_plan(args.intent)
    observer = onboarding.LocalOperatorConfirmation(*([args.confirm_all_offline_conditions] * 6), args.public_listener)
    onboarding.g.text(args.operator_attestation, "operator attestation")
    onboarding.g.text(args.issuer_reference, "issuer reference")
    onboarding._profile_target(intent, args.profile_out)
    # Constructing this proxy selects no provider and loads no model. The
    # driver accesses it only when unfinished enabled planting needs embedding.
    embedder = embedder_factory() if onboarding.onboarding_needs_embedding(intent) else None
    return onboarding.run_native_genesis_onboarding(intent=intent, intent_path=args.intent, observer=observer,
        operator_attestation=args.operator_attestation, issuer_reference=args.issuer_reference,
        embedder=embedder, profile_out=args.profile_out, fault=fault)


def main(argv=None, *, stdout=None, fault=_noop, embedder_factory=_EnvironmentEmbedder):
    output = sys.stdout if stdout is None else stdout
    try:
        args = _parser().parse_args(argv)
        result = _execute(args, fault=fault, embedder_factory=embedder_factory)
    except Exception:
        # Never expose request/identity text, observations, credentials or the
        # environment through a nested exception or traceback.
        result = dict(status="CONFLICT", error="OFFLINE_GENESIS_INPUT_OR_EVIDENCE_REFUSED")
    output.write(json.dumps(result, sort_keys=True, allow_nan=False) + "\n")
    return 2 if result["status"] == "CONFLICT" else 0


if __name__ == "__main__":
    raise SystemExit(main())
