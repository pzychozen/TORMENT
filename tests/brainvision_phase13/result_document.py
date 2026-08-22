"""Frozen Phase-13 formal-result renderer; it makes no scientific inference."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from brainvision_phase13.grader import GradingRecord
from brainvision_phase13.schemas import TOP_LEVEL_INVALID, TOP_LEVEL_PASS, canonical_json_bytes, sha256_hex


_PACKAGE_DIRECTORY = Path(__file__).resolve().parent
_REPOSITORY_ROOT = _PACKAGE_DIRECTORY.parents[1]
_SPECIFICATION_PATH = _REPOSITORY_ROOT / (
    "docs/TORMENT_BRAINVISION_PHASE_13_COMPLETE_V1A_QUALIFICATION_SPECIFICATION_v1.0.md"
)
_SECTION_46_START = "# 46. Claim ceiling for PASS\n"
_SECTION_47_START = "# 47. Inherited claim ceilings\n"
_HALF_LIFE_BOUNDARY = "retained_300_seconds_is_minimum_survival_not_half_life"
_MANDATORY_HOLD = """BRAINVISION_V1A:
QUALIFIED

MANDATORY_HOLD:
ACTIVE
"""
_NONAUTHORIZATION = (
    "Phase 14 and beyond are NOT AUTHORIZED. This qualification authorizes no "
    "memory, cognitive, character, kernel, or model integration work, and no "
    "design, specification, prototyping, or implementation toward such "
    "integration. `MANDATORY_HOLD: ACTIVE` may be cleared only by an explicit, "
    "separately recorded authorization naming the specific scope released. "
    "Nothing in this result, and no absence of a finding in it, constitutes "
    "such authorization."
)


def frozen_section_46_claim_ceiling() -> str:
    """Return the complete frozen section 46 verbatim from the authority file."""
    source = _SPECIFICATION_PATH.read_text(encoding="utf-8")
    try:
        start = source.index(_SECTION_46_START)
        end = source.index(_SECTION_47_START, start)
    except ValueError as error:
        raise RuntimeError("frozen Phase-13 section 46 is unavailable") from error
    section = source[start:end].rstrip()
    if "emotion" not in section or "universal cross-platform determinism" not in section:
        raise RuntimeError("frozen Phase-13 section 46 is incomplete")
    if _HALF_LIFE_BOUNDARY not in source:
        raise RuntimeError("frozen inherited half-life boundary is unavailable")
    return (
        section
        + "\n\nFrozen inherited boundary from specification section 47:\n\n```text\n"
        + _HALF_LIFE_BOUNDARY
        + "\n```"
    )


def render_formal_result_document(
    *,
    identity_binding_record: Mapping[str, object],
    preflight_record: Mapping[str, object],
    administration_identity: str,
    evidence_package: Mapping[str, object],
    grading: GradingRecord,
    evidence_index_path: str,
) -> str:
    """Render one immutable-evidence result without deriving claims from data."""
    if type(administration_identity) is not str or not administration_identity:
        raise ValueError("formal result requires an exact administration identity")
    evidence_sha256 = sha256_hex(canonical_json_bytes(evidence_package))
    grading_sha256 = sha256_hex(grading.to_canonical_bytes())
    header = (
        "# TORMENT Brainvision Phase-13 Formal Qualification Result\n\n"
        "## Administration identity\n\n"
        f"administration_identity: `{administration_identity}`\n\n"
        f"identity_binding_record: `{canonical_json_bytes(dict(identity_binding_record)).decode('ascii')}`\n\n"
        "## Environment and preflight\n\n"
        f"preflight_record: `{canonical_json_bytes(dict(preflight_record)).decode('ascii')}`\n\n"
        "## Administration status\n\n"
        f"administration_started: `{evidence_package.get('administration_started')}`\n\n"
        "no_retry_or_rerun: `true`\n\n"
        f"evidence_sha256: `{evidence_sha256}`\n\n"
        f"grading_sha256: `{grading_sha256}`\n\n"
        f"evidence_package_index: `{evidence_index_path}`\n\n"
    )
    block_lines = ["## E1-E12 block outcomes", ""]
    for block in grading.blocks:
        block_lines.extend(
            (
                f"### {block.block_id}", "",
                f"presentation_status: `{block.presentation_status}`", "",
                f"grading_status: `{block.status}`", "",
                f"subcode: `{block.subcode}`", "",
                f"criteria_count: `{len(block.criterion_results)}`", "",
                f"evidence_refs: `{canonical_json_bytes(list(block.evidence_refs)).decode('ascii')}`", "",
            )
        )
    block_section = "\n".join(block_lines)
    taxonomy_section = (
        "## Top-level taxonomy\n\n"
        f"top_level: `{grading.taxonomy.top_level}`\n\n"
        f"subcode: `{grading.taxonomy.subcode}`\n\n"
    )
    if grading.taxonomy.top_level == TOP_LEVEL_PASS:
        return (
            header
            + block_section
            + "\n\n"
            + taxonomy_section
            + "V1A_QUALIFICATION_PASS\n\n"
            + frozen_section_46_claim_ceiling()
            + "\n\n"
            + _MANDATORY_HOLD
            + "\n"
            + _NONAUTHORIZATION
        )
    result = grading.taxonomy.top_level or TOP_LEVEL_INVALID
    subcode = grading.taxonomy.subcode or "INVALID_ADMINISTRATION"
    return header + block_section + "\n\n" + taxonomy_section + f"{result}\n\nsubcode: `{subcode}`\n"


__all__ = (
    "frozen_section_46_claim_ceiling",
    "render_formal_result_document",
)
