"""Frozen Phase-13 descriptor-fixture authority helpers.

Formal observation envelopes are intentionally *not* represented here.  The
frozen bindings and the executable schedule are their sole authorities.
"""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Final

from brainvision.fixtures import D0, DA, DB
from brainvision.observation import DESCRIPTOR_SCHEMA_ID


PACKAGE_DIR: Final = Path(__file__).resolve().parent
FIXTURE_MANIFEST_PATH: Final = PACKAGE_DIR / "fixture_manifest.json"
def _descriptor_record(name: str, descriptor: object) -> dict[str, object]:
    raw = descriptor.to_canonical_json_bytes()
    return {
        "canonical_bytes_ascii": raw.decode("ascii"),
        "descriptor": descriptor.to_dict(),
        "name": name,
        "sha256": sha256(raw).hexdigest(),
    }


def frozen_fixture_manifest_data() -> dict[str, object]:
    """Return the complete fixture content without creating an observation."""
    return {
        "descriptor_schema_id": DESCRIPTOR_SCHEMA_ID,
        "descriptors": {
            "d0": _descriptor_record("d0", D0),
            "dA": _descriptor_record("dA", DA),
            "dB": _descriptor_record("dB", DB),
        },
        "schema_id": "brainvision.phase13.fixture_manifest.v1",
    }


def validate_fixture_manifest(payload: Mapping[str, object]) -> None:
    """Prove the committed manifest is still derived from Phase-2 authority."""
    if payload != frozen_fixture_manifest_data():
        raise ValueError("fixture manifest differs from frozen Phase-2 authority")


__all__ = (
    "FIXTURE_MANIFEST_PATH",
    "frozen_fixture_manifest_data",
    "validate_fixture_manifest",
)
