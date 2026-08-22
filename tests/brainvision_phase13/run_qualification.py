"""Safety-latched Phase-13 runner with a complete future formal dispatch path."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

TESTS_DIRECTORY = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = TESTS_DIRECTORY.parent
if str(TESTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TESTS_DIRECTORY))
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from brainvision_phase13.manifests import validate_all_manifests


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase-13 qualification instrument")
    parser.add_argument("--validate-instrument", action="store_true")
    parser.add_argument("--authorization-file", type=Path)
    parser.add_argument("--expected-head")
    parser.add_argument("--administration-id")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--formal-first-administration", action="store_true")
    parser.add_argument("--formal-authorization-token")
    return parser


def validate_cli_authorization(args: argparse.Namespace) -> None:
    """Reject every partial authorization before any future E-block contact."""
    formal_values = (
        args.authorization_file,
        args.expected_head,
        args.administration_id,
        args.output_dir,
        args.formal_authorization_token,
    )
    if args.formal_first_administration:
        if any(value is None for value in formal_values):
            raise ValueError("formal execution requires every frozen authorization argument")
        return
    if any(value is not None for value in formal_values):
        raise ValueError("formal authorization values require --formal-first-administration")


def dispatch_formal_administration(args: argparse.Namespace) -> int:
    """Load the explicit external artifact before the non-consuming preflight."""
    from brainvision_phase13.orchestrator import (
        dispatch_authorized_qualification,
        load_external_formal_authorization_artifact,
    )

    authorization_artifact = load_external_formal_authorization_artifact(args.authorization_file)
    dispatch_authorized_qualification(args=args, authorization_artifact=authorization_artifact)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validate_cli_authorization(args)
    if args.validate_instrument:
        if args.formal_first_administration:
            raise ValueError("--validate-instrument cannot accompany formal execution")
        for name, digest in validate_all_manifests().items():
            print(f"{name}={digest}")
        print("PHASE13_INSTRUMENT_VALIDATION_ONLY")
        return 0
    if args.formal_first_administration:
        return dispatch_formal_administration(args)
    raise ValueError("choose --validate-instrument; no implicit qualification execution exists")


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = (
    "build_parser",
    "dispatch_formal_administration",
    "main",
    "validate_cli_authorization",
)
