"""Static E1–E12 plan construction and external-grader result mechanics.

The functions here construct frozen block plans only.  They do not create a
lifecycle manager, call Phase-12 ingress, or execute any qualification arm on
import or while being built.  A separately authorized future runner must
explicitly supply an execution backend before any plan can be administered.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from brainvision_phase13.evidence import EvidenceBuilder
from brainvision_phase13.manifests import (
    SCHEDULE_MANIFEST_PATH,
    load_complete_expected_result_manifest,
    load_manifest,
)
from brainvision_phase13.schemas import (
    BLOCK_IDS,
    BlockExecutionEvidence,
    SyntheticBlockResult,
    TaxonomyDecision,
    TOP_LEVEL_PASS,
    aggregate_taxonomy,
)


# The formal result builder reads the complete frozen section 46 from the
# authority document.  These compact strings are retained only for existing
# synthetic taxonomy unit tests; they are not a formal claim ceiling.
PASS_CLAIM_CEILING = "Synthetic rendering only; the formal renderer emits specification section 46."
MANDATORY_HOLD_PARAGRAPH = "Synthetic rendering only; the formal renderer emits the frozen hold."


@dataclass(frozen=True, kw_only=True)
class QualificationBlockPlan:
    """One frozen E-block's static schedule and expected-predicate authority."""

    block_id: str
    expected: Mapping[str, object]
    schedule: Mapping[str, object]

    def __post_init__(self) -> None:
        if self.block_id not in BLOCK_IDS:
            raise ValueError("block plan requires a frozen E1–E12 identifier")


class QualificationExecutionBackend(Protocol):
    """Future live executor boundary; no implementation runs during preflight."""

    def execute_block(
        self,
        plan: QualificationBlockPlan,
        evidence: EvidenceBuilder,
    ) -> BlockExecutionEvidence:
        """Execute exactly one frozen plan after formal authorization."""


def _load_block_plan(block_id: str) -> QualificationBlockPlan:
    expected_document = load_complete_expected_result_manifest()
    schedule_document = load_manifest(SCHEDULE_MANIFEST_PATH)
    expected_blocks = expected_document["blocks"]
    scheduled_blocks = schedule_document["blocks"]
    if not isinstance(expected_blocks, Mapping) or not isinstance(scheduled_blocks, Mapping):
        raise ValueError("Phase-13 block manifests are malformed")
    expected = expected_blocks[block_id]
    schedule = scheduled_blocks[block_id]
    if not isinstance(expected, Mapping) or not isinstance(schedule, Mapping):
        raise ValueError(f"{block_id} manifest entry must be an object")
    return QualificationBlockPlan(
        block_id=block_id,
        expected=dict(expected),
        schedule={
            **dict(schedule),
            "administered_sink_purity_depth": schedule_document[
                "administered_sink_purity_depth"
            ],
            "observation_defaults": dict(schedule_document["observation_defaults"]),
        },
    )


def build_e1() -> QualificationBlockPlan:
    return _load_block_plan("E1")


def build_e2() -> QualificationBlockPlan:
    return _load_block_plan("E2")


def build_e3() -> QualificationBlockPlan:
    return _load_block_plan("E3")


def build_e4() -> QualificationBlockPlan:
    return _load_block_plan("E4")


def build_e5() -> QualificationBlockPlan:
    return _load_block_plan("E5")


def build_e6() -> QualificationBlockPlan:
    return _load_block_plan("E6")


def build_e7() -> QualificationBlockPlan:
    return _load_block_plan("E7")


def build_e8() -> QualificationBlockPlan:
    return _load_block_plan("E8")


def build_e9() -> QualificationBlockPlan:
    return _load_block_plan("E9")


def build_e10() -> QualificationBlockPlan:
    return _load_block_plan("E10")


def build_e11() -> QualificationBlockPlan:
    return _load_block_plan("E11")


def build_e12() -> QualificationBlockPlan:
    return _load_block_plan("E12")


_BUILDERS = (
    build_e1,
    build_e2,
    build_e3,
    build_e4,
    build_e5,
    build_e6,
    build_e7,
    build_e8,
    build_e9,
    build_e10,
    build_e11,
    build_e12,
)


def build_all_block_plans() -> tuple[QualificationBlockPlan, ...]:
    """Construct every frozen plan; this is static manifest work only."""
    plans = tuple(builder() for builder in _BUILDERS)
    if tuple(plan.block_id for plan in plans) != BLOCK_IDS:
        raise AssertionError("Phase-13 block plan order must remain E1 through E12")
    return plans


def _execute_one(
    block_id: str,
    backend: QualificationExecutionBackend,
    evidence: EvidenceBuilder,
) -> BlockExecutionEvidence:
    """Delegate exactly one frozen plan to the separately authorized backend."""
    return backend.execute_block(_load_block_plan(block_id), evidence)


def execute_e1(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E1", backend, evidence)


def execute_e2(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E2", backend, evidence)


def execute_e3(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E3", backend, evidence)


def execute_e4(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E4", backend, evidence)


def execute_e5(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E5", backend, evidence)


def execute_e6(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E6", backend, evidence)


def execute_e7(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E7", backend, evidence)


def execute_e8(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E8", backend, evidence)


def execute_e9(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E9", backend, evidence)


def execute_e10(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E10", backend, evidence)


def execute_e11(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E11", backend, evidence)


def execute_e12(backend: QualificationExecutionBackend, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
    return _execute_one("E12", backend, evidence)


_EXECUTORS = (
    execute_e1,
    execute_e2,
    execute_e3,
    execute_e4,
    execute_e5,
    execute_e6,
    execute_e7,
    execute_e8,
    execute_e9,
    execute_e10,
    execute_e11,
    execute_e12,
)


def execute_authorized_qualification(
    *,
    backend: QualificationExecutionBackend,
    evidence: EvidenceBuilder,
) -> tuple[BlockExecutionEvidence, ...]:
    """Run all plans once; a separate grader alone assigns the taxonomy."""
    return tuple(executor(backend, evidence) for executor in _EXECUTORS)


def stimulate_runtime_snapshot(manager: object, workspace_id: str, agent_id: str) -> None:
    """Issue the one E9 scheduling stimulus and discard its raw return value."""
    manager.runtime_snapshot(workspace_id, agent_id)
    return None


def render_final_result(decision: TaxonomyDecision) -> str:
    """Render only synthetic verdicts; PASS terminates with the frozen HOLD."""
    if decision.top_level == TOP_LEVEL_PASS:
        return (
            f"{TOP_LEVEL_PASS}\n\n"
            f"{PASS_CLAIM_CEILING}\n\n"
            "BRAINVISION_V1A:\n"
            "QUALIFIED\n\n"
            "MANDATORY_HOLD:\n"
            f"ACTIVE\n\n{MANDATORY_HOLD_PARAGRAPH}"
        )
    if decision.top_level is None:
        return "NO_FORMAL_TAXONOMY"
    return f"{decision.top_level}\n{decision.subcode}"


__all__ = (
    "MANDATORY_HOLD_PARAGRAPH",
    "PASS_CLAIM_CEILING",
    "QualificationBlockPlan",
    "QualificationExecutionBackend",
    "build_all_block_plans",
    "build_e1",
    "build_e2",
    "build_e3",
    "build_e4",
    "build_e5",
    "build_e6",
    "build_e7",
    "build_e8",
    "build_e9",
    "build_e10",
    "build_e11",
    "build_e12",
    "execute_authorized_qualification",
    "execute_e1",
    "execute_e2",
    "execute_e3",
    "execute_e4",
    "execute_e5",
    "execute_e6",
    "execute_e7",
    "execute_e8",
    "execute_e9",
    "execute_e10",
    "execute_e11",
    "execute_e12",
    "render_final_result",
    "stimulate_runtime_snapshot",
)
