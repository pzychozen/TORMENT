"""Frozen K=3 family identity for the algebraic N=64 PRIMARY_V0_1 F3 evaluator (constants-only; offline).

This module is a compact committed binding of the immutable witness family selected by the completed
authoritative freezer at candidate indices (478, 479, 480). It contains CONSTANTS ONLY: no logic, no I/O, no
descriptor contact, no evaluation. It imports nothing but typing helpers. It is NOT a replacement for the
canonical freezer result; production evaluation must require both the local canonical freeze result AND exact
agreement with these constants.

Governing documents:
  docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FROZEN_K3_FAMILY_EVIDENCE_AND_F3_EVALUATION_BINDING_v0.1.md
  docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATOR_IMPLEMENTATION_SPECIFICATION_v0.1.md

FORMAL_HOLD and Mode_0 remain active. Offline, quarantined, non-runtime, non-production, descriptive-only.
"""
from __future__ import annotations

from typing import Dict, Tuple

# --- core dimensions ---
N: int = 64
K: int = 3
MEMBER_WEIGHT: int = 12

# --- frozen family order ---
accepted_candidate_indices: Tuple[int, int, int] = (478, 479, 480)
accepted_order_indices: Tuple[int, int, int] = (0, 1, 2)
raw_ab_naming: str = "A_LEX_SMALLER_OR_EQUAL"
verification_mode: str = "PRIMARY_CANDIDATE_N64"

# --- freezer execution binding ---
execution_commit_identity: str = "6ddd02f9f6fdf74721dc9cd620cbb2a0aa0fecc8"

# --- canonical freezer evidence identities ---
freeze_result_payload_sha256: str = "35e03a83fee83b7fc13514397e10115b3f6b99f847bf17d20772a0e61376796e"
freeze_result_whole_file_sha256: str = "97af61ea4debf9d66146f3e33f035c17c60965c1d9fed0ebbf3d09ead58cbca5"
summary_whole_file_sha256: str = "d20002382f877ad91df8d27e8943ac90881bdf5c30b2f9b65bf4299841274066"
family_manifest_sha256: str = "352a49bc8d06a35b41b8783f8a869a1645d93c76ddb91df379492b37106d8151"
candidate_decision_ledger_sha256: str = "151af61422e34829dd8043bdb4308c1ad775b991eab223b74607db69f8bd9bfb"
family_verifier_certificate_sha256: str = "416d32bba578856b5122402186860643071070c946829020799138da13ee764e"
candidate_stream_payload_sha256: str = "70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5"

# --- frozen input scalars for the freezer preflight ---
candidate_count: int = 20000
terminal_stream_status: str = "budget_exhausted"

# --- three ordered pair-verifier certificate hashes (frozen family order 0, 1, 2) ---
pair_certificate_sha256: Tuple[str, str, str] = (
    "51e72030237da850757979588b4c4107de69a6098ce7c9a3559243b5545edf2b",
    "3b3475fc9bd2264fd17035f62ddbbc03d584a1fa94f5f28db712941f6e683408",
    "d4bbb7d8d8958cca261728721115de21efa154c50930bf787e4153fcb28ddfd9",
)

# --- exact raw supports, frozen A/B order, per candidate ---
raw_support_478_A: Tuple[int, ...] = (0, 1, 2, 4, 5, 6, 7, 9, 11, 12, 13, 15)
raw_support_478_B: Tuple[int, ...] = (0, 1, 3, 4, 5, 7, 9, 10, 11, 60, 62, 63)
raw_support_479_A: Tuple[int, ...] = (0, 1, 2, 4, 5, 6, 7, 9, 12, 13, 14, 16)
raw_support_479_B: Tuple[int, ...] = (0, 1, 3, 4, 5, 8, 10, 11, 12, 60, 62, 63)
raw_support_480_A: Tuple[int, ...] = (0, 1, 2, 4, 5, 6, 7, 9, 13, 14, 15, 17)
raw_support_480_B: Tuple[int, ...] = (0, 1, 3, 4, 5, 9, 11, 12, 13, 60, 62, 63)

# --- frozen supports keyed by candidate index and role (A, B) ---
frozen_supports: Dict[int, Dict[str, Tuple[int, ...]]] = {
    478: {"A": raw_support_478_A, "B": raw_support_478_B},
    479: {"A": raw_support_479_A, "B": raw_support_479_B},
    480: {"A": raw_support_480_A, "B": raw_support_480_B},
}

# --- six member identities, in frozen order ---
member_ids: Tuple[str, str, str, str, str, str] = (
    "candidate_478_A", "candidate_478_B",
    "candidate_479_A", "candidate_479_B",
    "candidate_480_A", "candidate_480_B",
)

# (member_id, candidate_index, pair_order_index, raw_role, support) in frozen order
frozen_members: Tuple[Tuple[str, int, int, str, Tuple[int, ...]], ...] = (
    ("candidate_478_A", 478, 0, "A", raw_support_478_A),
    ("candidate_478_B", 478, 0, "B", raw_support_478_B),
    ("candidate_479_A", 479, 1, "A", raw_support_479_A),
    ("candidate_479_B", 479, 1, "B", raw_support_479_B),
    ("candidate_480_A", 480, 2, "A", raw_support_480_A),
    ("candidate_480_B", 480, 2, "B", raw_support_480_B),
)

# (candidate_index, pair_order_index, A_support, B_support, pair_certificate_sha256) in frozen order
frozen_pairs: Tuple[Tuple[int, int, Tuple[int, ...], Tuple[int, ...], str], ...] = (
    (478, 0, raw_support_478_A, raw_support_478_B, pair_certificate_sha256[0]),
    (479, 1, raw_support_479_A, raw_support_479_B, pair_certificate_sha256[1]),
    (480, 2, raw_support_480_A, raw_support_480_B, pair_certificate_sha256[2]),
)
