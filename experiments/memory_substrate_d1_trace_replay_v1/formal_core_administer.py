"""Explicit operator surface for a future, one-shot CORE_ONLY D1 run.

Merely importing this module, parsing its arguments, or constructing an
operator plan does not create a marker, result root, mutable arm root, or
formal event.  Only ``main`` crosses the pre-existing runner authorization
boundary after the operator has supplied every authority-bearing value.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable

from .formal import (
    FormalAdministrationAuthorization,
    FormalAdministrationRefused,
    FormalAdministrationRunner,
    FormalResultSchema,
)
from .formal_core_executor import (
    CORE_ARM_ORDER,
    CORE_FIXTURE_SHA256,
    CORE_PROTOCOL_SHA256,
    CORE_TOLERANCES_SHA256,
    CoreFormalAdministrationExecutor,
    CoreFrozenFixture,
    require_core_formal_inputs,
)
from .formal_core_ports import ConcreteCoreFormalExecutionPorts, validate_frozen_core_input_contract
from .protocol import FrozenAdministrationInputs
from .side_store_observation import (
    CORE_CHARACTER_FREE_L0_FINGERPRINT,
    CORE_SIDE_STORE_OBSERVATION_DIGEST,
)


@dataclass(frozen=True)
class CoreFormalOperatorPlan:
    authorization: FormalAdministrationAuthorization
    inputs: FrozenAdministrationInputs
    runner: FormalAdministrationRunner
    executor: CoreFormalAdministrationExecutor
    verify_baselines_and_fixture: Callable[[], None]

    def run(self) -> FormalResultSchema:
        return self.runner.run(
            authorization=self.authorization,
            inputs=self.inputs,
            protocol_sha256=self.authorization.protocol_sha256,
            fixture_sha256=self.authorization.fixture_sha256,
            verify_baselines_and_fixture=self.verify_baselines_and_fixture,
            contact_formal_trace=lambda: self.executor.execute(
                administration_id=self.authorization.administration_id,
            ),
        )


def _current_head(repository_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository_root,
        check=True, capture_output=True, text=True,
    )
    return completed.stdout.strip()


def build_formal_operator_plan(
    *,
    administration_id: str,
    expected_repository_head: str,
    protocol_sha256: str,
    fixture_sha256: str,
    tolerances_sha256: str,
    administration_work_root: str | Path,
    result_root: str | Path,
    repository_root: str | Path | None = None,
    ports_factory: Callable[..., ConcreteCoreFormalExecutionPorts] = ConcreteCoreFormalExecutionPorts,
) -> CoreFormalOperatorPlan:
    """Build, but do not run, the exact one-shot formal-administration stack."""
    values = (
        administration_id, expected_repository_head, protocol_sha256, fixture_sha256,
        tolerances_sha256, str(administration_work_root), str(result_root),
    )
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise FormalAdministrationRefused("all formal administration authority values are required")
    repository = Path(repository_root or Path(__file__).resolve().parents[2]).resolve()
    work_root, output_root = Path(administration_work_root).resolve(), Path(result_root).resolve()
    if not work_root.is_absolute() or not output_root.is_absolute():
        raise FormalAdministrationRefused("formal administration roots must be absolute")
    if expected_repository_head != _current_head(repository):
        raise FormalAdministrationRefused("operator expected repository HEAD does not match the current checkout")
    if (protocol_sha256, fixture_sha256, tolerances_sha256) != (
        CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256, CORE_TOLERANCES_SHA256,
    ):
        raise FormalAdministrationRefused("operator hashes do not match the frozen CORE_ONLY lock")
    fixture = CoreFrozenFixture.load()
    require_core_formal_inputs(fixture.inputs)
    authorization = FormalAdministrationAuthorization(
        administration_id, expected_repository_head, protocol_sha256, fixture_sha256,
        tolerances_sha256, str(output_root), True,
    )
    runner = FormalAdministrationRunner(repository_root=repository, expected_repository_head=expected_repository_head)
    ports = ports_factory(administration_work_root=work_root, repository_root=repository)
    executor = CoreFormalAdministrationExecutor(fixture=fixture, ports=ports)

    def verify_baselines_and_fixture() -> None:
        reread = CoreFrozenFixture.load()
        require_core_formal_inputs(reread.inputs)
        if (
            tuple(arm.arm_id for arm in reread.arms) != CORE_ARM_ORDER
            or reread.l0_fingerprint_sha256 != CORE_CHARACTER_FREE_L0_FINGERPRINT
            or reread.side_store_observation_digest != CORE_SIDE_STORE_OBSERVATION_DIGEST
        ):
            raise FormalAdministrationRefused("CORE_ONLY frozen fixture no longer names the established core boundary")
        if (protocol_sha256, fixture_sha256, tolerances_sha256) != (
            CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256, CORE_TOLERANCES_SHA256,
        ):
            raise FormalAdministrationRefused("operator lock changed before formal marker creation")
        validate_frozen_core_input_contract(reread)
        ports.verify_frozen_sources()

    return CoreFormalOperatorPlan(
        authorization=authorization, inputs=fixture.inputs, runner=runner,
        executor=executor, verify_baselines_and_fixture=verify_baselines_and_fixture,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="administer the already-authorized CORE_ONLY D1 formal experiment")
    parser.add_argument("--administration-id", required=True)
    parser.add_argument("--expected-repository-head", required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--fixture-sha256", required=True)
    parser.add_argument("--tolerances-sha256", required=True)
    parser.add_argument("--administration-work-root", required=True)
    parser.add_argument("--result-root", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    plan = build_formal_operator_plan(
        administration_id=args.administration_id,
        expected_repository_head=args.expected_repository_head,
        protocol_sha256=args.protocol_sha256,
        fixture_sha256=args.fixture_sha256,
        tolerances_sha256=args.tolerances_sha256,
        administration_work_root=args.administration_work_root,
        result_root=args.result_root,
    )
    plan.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
