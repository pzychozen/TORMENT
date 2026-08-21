"""Frozen synthetic descriptor fixtures for Phase-2 qualification work."""

from __future__ import annotations

from hashlib import sha256
from typing import Final

from brainvision.observation import LowLevelVisualDescriptorV1


D0: Final = LowLevelVisualDescriptorV1(
    mean_luminance_q=500_000,
    mean_adjacent_luminance_difference_q=0,
)
DA: Final = LowLevelVisualDescriptorV1(
    mean_luminance_q=750_000,
    mean_adjacent_luminance_difference_q=0,
)
DB: Final = LowLevelVisualDescriptorV1(
    mean_luminance_q=500_000,
    mean_adjacent_luminance_difference_q=250_000,
)

D0_CANONICAL_BYTES: Final = D0.to_canonical_json_bytes()
DA_CANONICAL_BYTES: Final = DA.to_canonical_json_bytes()
DB_CANONICAL_BYTES: Final = DB.to_canonical_json_bytes()

D0_SHA256: Final = "c08e4b0cf384c20b126ea4466ab2122811f5ad2328e2c482bcfea5471d526544"
DA_SHA256: Final = "9fdd9ce03853911b050565684b0432079cc4cf3f7e51a4dc035b7423762e7583"
DB_SHA256: Final = "2caa7c6d89da394da758f26ada91658cabb1969639fffd7767130d789c152517"


def descriptor_fixture_hashes() -> dict[str, str]:
    """Recompute the evidence hashes from the frozen canonical descriptor bytes."""
    return {
        "d0": sha256(D0_CANONICAL_BYTES).hexdigest(),
        "dA": sha256(DA_CANONICAL_BYTES).hexdigest(),
        "dB": sha256(DB_CANONICAL_BYTES).hexdigest(),
    }


__all__ = (
    "D0",
    "D0_CANONICAL_BYTES",
    "D0_SHA256",
    "DA",
    "DA_CANONICAL_BYTES",
    "DA_SHA256",
    "DB",
    "DB_CANONICAL_BYTES",
    "DB_SHA256",
    "descriptor_fixture_hashes",
)
