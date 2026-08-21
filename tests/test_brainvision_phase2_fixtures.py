"""Frozen-fixture evidence tests for Brainvision Phase 2."""

from __future__ import annotations

from hashlib import sha256

from brainvision.fixtures import (
    D0,
    D0_CANONICAL_BYTES,
    D0_SHA256,
    DA,
    DA_CANONICAL_BYTES,
    DA_SHA256,
    DB,
    DB_CANONICAL_BYTES,
    DB_SHA256,
    descriptor_fixture_hashes,
)
from brainvision.observation import LowLevelVisualDescriptorV1


def test_fixtures_have_the_exact_frozen_values_and_no_semantic_class() -> None:
    assert D0 == LowLevelVisualDescriptorV1(
        mean_luminance_q=500_000,
        mean_adjacent_luminance_difference_q=0,
    )
    assert DA == LowLevelVisualDescriptorV1(
        mean_luminance_q=750_000,
        mean_adjacent_luminance_difference_q=0,
    )
    assert DB == LowLevelVisualDescriptorV1(
        mean_luminance_q=500_000,
        mean_adjacent_luminance_difference_q=250_000,
    )
    for descriptor in (D0, DA, DB):
        assert "semantic_event_class" not in descriptor.to_dict()


def test_fixtures_are_pairwise_distinguishable() -> None:
    assert D0 != DA
    assert D0 != DB
    assert DA != DB
    assert len({D0_CANONICAL_BYTES, DA_CANONICAL_BYTES, DB_CANONICAL_BYTES}) == 3


def test_fixture_canonical_bytes_are_exact() -> None:
    assert D0_CANONICAL_BYTES == (
        b'{"mean_adjacent_luminance_difference_q":0,"mean_luminance_q":500000,'
        b'"schema_id":"brainvision.low_level_descriptor.v1"}'
    )
    assert DA_CANONICAL_BYTES == (
        b'{"mean_adjacent_luminance_difference_q":0,"mean_luminance_q":750000,'
        b'"schema_id":"brainvision.low_level_descriptor.v1"}'
    )
    assert DB_CANONICAL_BYTES == (
        b'{"mean_adjacent_luminance_difference_q":250000,"mean_luminance_q":500000,'
        b'"schema_id":"brainvision.low_level_descriptor.v1"}'
    )


def test_fixture_hashes_are_independently_recomputed_from_canonical_bytes() -> None:
    assert sha256(D0_CANONICAL_BYTES).hexdigest() == D0_SHA256
    assert sha256(DA_CANONICAL_BYTES).hexdigest() == DA_SHA256
    assert sha256(DB_CANONICAL_BYTES).hexdigest() == DB_SHA256
    assert descriptor_fixture_hashes() == {
        "d0": D0_SHA256,
        "dA": DA_SHA256,
        "dB": DB_SHA256,
    }


def test_da_and_db_are_equal_magnitude_orthogonal_displacements_from_d0() -> None:
    displacement_a = (
        DA.mean_luminance_q - D0.mean_luminance_q,
        DA.mean_adjacent_luminance_difference_q - D0.mean_adjacent_luminance_difference_q,
    )
    displacement_b = (
        DB.mean_luminance_q - D0.mean_luminance_q,
        DB.mean_adjacent_luminance_difference_q - D0.mean_adjacent_luminance_difference_q,
    )
    assert displacement_a == (250_000, 0)
    assert displacement_b == (0, 250_000)
    assert sum(component * component for component in displacement_a) == sum(
        component * component for component in displacement_b
    )
    assert sum(a * b for a, b in zip(displacement_a, displacement_b, strict=True)) == 0
