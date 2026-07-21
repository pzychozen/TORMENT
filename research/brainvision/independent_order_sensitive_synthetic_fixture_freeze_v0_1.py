"""Independent order-sensitive synthetic-fixture freeze library (v0.1).

Pure, deterministic, standard-library-only library functions for the S1B
synthetic-fixture infrastructure: canonical manifest construction and hashing,
candidate-pass comparison, deterministic finalization, canonical failure-manifest
construction, and lexical static source-boundary validation.

Importing this module is inert. No function performs disk writes, Git queries,
environment reads, repository discovery, retained-evidence reads, frozen-family
reads, network access, or descriptor contact. Every function returns data objects
or bytes; none writes a manifest to disk. The canonical seed scan is never run here.
"""

from __future__ import annotations

import ast
import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Descriptor-blind pure mathematics is reused from the verifier and the
# construction/seed contract from the generator; no second mathematical
# implementation is created in this module.
import independent_order_sensitive_synthetic_fixture_verifier_v0_1 as _verifier
import independent_order_sensitive_synthetic_fixture_generator_v0_1 as _generator

N = 64
K_SYNTHETIC = 8

MANIFEST_SCHEMA = "torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-manifest-v0.1"
GENERATOR_ID = "independent-order-sensitive-synthetic-fixture-generator-v0.1"
VERIFIER_ID = "independent-order-sensitive-synthetic-fixture-verifier-v0.1"

SEED_ENUMERATION_POLICY = "canonical-lexicographic-c1-lt-c2-d1-lt-d2-mod-64-v0.1"
CONSTRUCTION_POLICY = "c-plus-d-and-c-minus-d-mod-64-collision-collapsed-v0.1"
ELIGIBILITY_POLICY = "first-failure-eight-predicate-descriptor-blind-v0.1"
DUPLICATE_POLICY = "member-orbit-affine-plus-complement-slot-invariant-pair-key-v0.1"

MANIFEST_TOP_LEVEL_KEYS: Tuple[str, ...] = (
    "schema",
    "generator_id",
    "verifier_id",
    "N",
    "K_synthetic",
    "seed_enumeration_policy",
    "construction_policy",
    "eligibility_policy",
    "duplicate_policy",
    "family_frozen",
    "fixed_fixture",
    "accepted_fixtures",
    "search_diagnostics",
    "source_identity",
    "configuration_identity",
    "validation",
    "ordered_failure_codes",
    "manifest_payload_sha256",
)

SOURCE_IDENTITY_KEYS: Tuple[str, ...] = (
    "generator_source_path",
    "generator_git_blob",
    "generator_raw_sha256",
    "verifier_source_path",
    "verifier_git_blob",
    "verifier_raw_sha256",
    "test_source_identities",
    "repository_commit",
    "python_version",
)

SEARCH_DIAGNOSTICS_KEYS: Tuple[str, ...] = (
    "total_seeds_visited",
    "eligibility_rejection_counts",
    "eligible_duplicate_count",
    "accepted_seed_order_positions",
    "terminal_seed_tuple",
    "terminal_status",
)

# The reducer emits accepted records as wrappers with these exact keys, keeping
# acceptance metadata strictly outside the unchanged opaque fixture record.
ACCEPTED_RECORD_WRAPPER_KEYS: Tuple[str, ...] = (
    "family_index",
    "seed_order_position",
    "fixture_record",
)

# The exact committed S1A flat accepted-fixture object (freeze specification
# §10.2), in exact key order. ``build_candidate_manifest`` deterministically
# projects each accepted-record wrapper into this shape for the manifest.
ACCEPTED_FIXTURE_KEYS: Tuple[str, ...] = (
    "family_index",
    "seed_order_position",
    "seed_tuple",
    "C",
    "D",
    "support_A",
    "support_B",
    "binary_A",
    "binary_B",
    "weight_A",
    "weight_B",
    "A2_A",
    "A2_B",
    "transition_table_A",
    "transition_table_B",
    "affine_inequivalence_certificate",
    "affine_complement_inequivalence_certificate",
    "triple_disagreement_count",
    "triple_disagreement_indices",
    "member_orbit_key_A",
    "member_orbit_key_B",
    "pair_duplicate_key",
)

# The fixture-record field order carried inside the wrapper: the flat accepted
# fixture minus its two leading acceptance-metadata keys.
FIXTURE_RECORD_FIELD_KEYS: Tuple[str, ...] = ACCEPTED_FIXTURE_KEYS[2:]

# The exact authorized five-file allowlist (forward-slash, repository-relative).
AUTHORIZED_ALLOWLIST: Tuple[str, ...] = (
    "research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py",
    "research/brainvision/independent_order_sensitive_synthetic_fixture_generator_v0_1.py",
    "research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py",
    "research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_verifier_v0_1.py",
    "research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py",
)

# Committed S1A §16 failure-code vocabulary order (for first-applicable selection).
S1A_FAILURE_CODE_ORDER: Tuple[str, ...] = (
    "FIXED_FIXTURE_RECONSTRUCTION_FAILURE",
    "FIXED_FIXTURE_LOWER_ORDER_CERTIFICATE_FAILURE",
    "FIXED_FIXTURE_AFFINE_CERTIFICATE_FAILURE",
    "FIXED_FIXTURE_AFFINE_COMPLEMENT_CERTIFICATE_FAILURE",
    "FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE",
    "GENERATOR_CONFIGURATION_INVALID",
    "SEED_ENUMERATION_FAILURE",
    "CONSTRUCTION_FAILURE",
    "ELIGIBILITY_CERTIFICATE_FAILURE",
    "DUPLICATE_KEY_FAILURE",
    "INSUFFICIENT_UNIQUE_FIXTURES",
    "MANIFEST_SCHEMA_FAILURE",
    "SERIALIZATION_FAILURE",
    "HASH_IDENTITY_FAILURE",
    "REPLAY_MISMATCH",
    "FORBIDDEN_IMPORT_DETECTED",
    "SOURCE_OWNERSHIP_FAILURE",
    "PROHIBITED_CHALLENGER_CONTACT",
    "PROHIBITED_FROZEN_FAMILY_CONTACT",
    "PRODUCTION_BOUNDARY_VIOLATION",
    "UNAUTHORIZED_EXECUTION",
)

MISMATCH_REASON_ORDER: Tuple[str, ...] = (
    "canonical_payload_bytes_mismatch",
    "manifest_payload_sha256_mismatch",
    "canonical_manifest_bytes_mismatch",
    "external_manifest_sha256_mismatch",
    "accepted_fixture_order_mismatch",
    "search_diagnostics_mismatch",
)

CANDIDATE_BUNDLE_KEYS: Tuple[str, ...] = (
    "canonical_payload_bytes",
    "manifest_payload_sha256",
    "canonical_manifest_bytes",
    "external_manifest_sha256",
    "accepted_fixture_order",
    "search_diagnostics",
)


class SyntheticFixtureProcessFailure(Exception):
    """Single dedicated process-level failure exception.

    Exposes a canonical §16 ``failure_code`` and a machine-readable
    ``failure_stage``. No free-form exception text may be serialized into a
    manifest or treated as scientific evidence.
    """

    def __init__(self, failure_code: str, failure_stage: str, detail: str = "") -> None:
        super().__init__("%s@%s" % (failure_code, failure_stage))
        self.failure_code = failure_code
        self.failure_stage = failure_stage
        self.detail = detail


# --------------------------------------------------------------------------- #
# Canonical serialization and hashing
# --------------------------------------------------------------------------- #

def _canonical_json_bytes(value: Any, failure_stage: str) -> bytes:
    """Compact fixed-key-order UTF-8 JSON with exactly one terminal LF."""
    try:
        text = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise SyntheticFixtureProcessFailure("SERIALIZATION_FAILURE", failure_stage, str(exc))
    return text.encode("utf-8") + b"\n"


def _payload_projection(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """The manifest with only ``manifest_payload_sha256`` removed, order preserved."""
    projection: Dict[str, Any] = {}
    for key in manifest.keys():
        if key == "manifest_payload_sha256":
            continue
        projection[key] = manifest[key]
    return projection


def canonical_payload_bytes(manifest: Dict[str, Any]) -> bytes:
    return _canonical_json_bytes(_payload_projection(manifest), "serialization")


def populate_manifest_payload_hash(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of the manifest with ``manifest_payload_sha256`` populated."""
    payload_bytes = canonical_payload_bytes(manifest)
    try:
        digest = hashlib.sha256(payload_bytes).hexdigest()
    except Exception as exc:  # noqa: BLE001 - defensive; hashlib failure is a hash-identity fault
        raise SyntheticFixtureProcessFailure("HASH_IDENTITY_FAILURE", "hash_identity", str(exc))
    if not (isinstance(digest, str) and len(digest) == 64):
        raise SyntheticFixtureProcessFailure("HASH_IDENTITY_FAILURE", "hash_identity", "bad digest length")
    populated: Dict[str, Any] = {}
    for key in manifest.keys():
        populated[key] = manifest[key]
    populated["manifest_payload_sha256"] = digest
    return populated


def canonical_manifest_bytes(manifest: Dict[str, Any]) -> bytes:
    if manifest.get("manifest_payload_sha256") is None:
        raise SyntheticFixtureProcessFailure(
            "SERIALIZATION_FAILURE", "serialization", "manifest_payload_sha256 not populated")
    return _canonical_json_bytes(manifest, "serialization")


def external_manifest_sha256(manifest: Dict[str, Any]) -> str:
    manifest_bytes = canonical_manifest_bytes(manifest)
    try:
        digest = hashlib.sha256(manifest_bytes).hexdigest()
    except Exception as exc:  # noqa: BLE001
        raise SyntheticFixtureProcessFailure("HASH_IDENTITY_FAILURE", "hash_identity", str(exc))
    return digest


def canonical_configuration_sha256(configuration_payload: Any) -> str:
    config_bytes = _canonical_json_bytes(configuration_payload, "serialization")
    return hashlib.sha256(config_bytes).hexdigest()


# --------------------------------------------------------------------------- #
# Ordered sub-object builders
# --------------------------------------------------------------------------- #

def build_configuration_identity(configuration_payload: Any) -> Dict[str, Any]:
    return {
        "configuration_payload": configuration_payload,
        "configuration_sha256": canonical_configuration_sha256(configuration_payload),
    }


def _ordered_source_identity(source_identity: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(source_identity, dict) or set(source_identity.keys()) != set(SOURCE_IDENTITY_KEYS):
        raise SyntheticFixtureProcessFailure(
            "MANIFEST_SCHEMA_FAILURE", "replay_comparison", "source_identity key set invalid")
    ordered: Dict[str, Any] = {}
    for key in SOURCE_IDENTITY_KEYS:
        ordered[key] = source_identity[key]
    return ordered


def _ordered_search_diagnostics(search_diagnostics: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(search_diagnostics, dict) or set(search_diagnostics.keys()) != set(SEARCH_DIAGNOSTICS_KEYS):
        raise SyntheticFixtureProcessFailure(
            "MANIFEST_SCHEMA_FAILURE", "replay_comparison", "search_diagnostics key set invalid")
    ordered: Dict[str, Any] = {}
    for key in SEARCH_DIAGNOSTICS_KEYS:
        ordered[key] = search_diagnostics[key]
    return ordered


# --------------------------------------------------------------------------- #
# Manifest construction
# --------------------------------------------------------------------------- #

def _assemble_manifest(
    family_frozen: bool,
    fixed_fixture: Dict[str, Any],
    accepted_fixtures: List[Dict[str, Any]],
    search_diagnostics: Dict[str, Any],
    source_identity: Dict[str, Any],
    configuration_identity: Dict[str, Any],
    validation: Dict[str, Any],
    ordered_failure_codes: List[str],
) -> Dict[str, Any]:
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "generator_id": GENERATOR_ID,
        "verifier_id": VERIFIER_ID,
        "N": N,
        "K_synthetic": K_SYNTHETIC,
        "seed_enumeration_policy": SEED_ENUMERATION_POLICY,
        "construction_policy": CONSTRUCTION_POLICY,
        "eligibility_policy": ELIGIBILITY_POLICY,
        "duplicate_policy": DUPLICATE_POLICY,
        "family_frozen": bool(family_frozen),
        "fixed_fixture": fixed_fixture,
        "accepted_fixtures": accepted_fixtures,
        "search_diagnostics": _ordered_search_diagnostics(search_diagnostics),
        "source_identity": _ordered_source_identity(source_identity),
        "configuration_identity": configuration_identity,
        "validation": validation,
        "ordered_failure_codes": list(ordered_failure_codes),
        "manifest_payload_sha256": None,
    }
    return manifest


_AFFINE_CERT_KEYS: Tuple[str, ...] = ("equivalent", "search_space_size", "first_equivalence_mapping")


def _is_strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_strict_nonneg_int(value: Any) -> bool:
    return _is_strict_int(value) and value >= 0


def _schema_fault(detail: str) -> "SyntheticFixtureProcessFailure":
    return SyntheticFixtureProcessFailure("MANIFEST_SCHEMA_FAILURE", "replay_comparison", detail)


def _valid_support_list(support: Any) -> bool:
    """Exactly nine strictly-ascending distinct in-range strict-integer residues."""
    if not isinstance(support, list) or len(support) != 9:
        return False
    previous = -1
    for element in support:
        if not _is_strict_int(element) or not (0 <= element < N):
            return False
        if element <= previous:   # strictly ascending => sorted and distinct
            return False
        previous = element
    return True


def _valid_binary_list(bits: Any) -> bool:
    if not isinstance(bits, list) or len(bits) != N:
        return False
    return all(_is_strict_int(bit) and bit in (0, 1) for bit in bits)


def _valid_int_list(values: Any, length: int) -> bool:
    if not isinstance(values, list) or len(values) != length:
        return False
    return all(_is_strict_int(value) for value in values)


def _valid_transition_table(table: Any) -> bool:
    if not isinstance(table, list) or len(table) != 2:
        return False
    for row in table:
        if not isinstance(row, list) or len(row) != 2:
            return False
        if not all(_is_strict_int(cell) for cell in row):
            return False
    return True


def _valid_affine_certificate(cert: Any, search_space_size: int) -> bool:
    if not isinstance(cert, dict) or tuple(cert.keys()) != _AFFINE_CERT_KEYS:
        return False
    if cert["equivalent"] is not False:
        return False
    if not _is_strict_int(cert["search_space_size"]) or cert["search_space_size"] != search_space_size:
        return False
    return cert["first_equivalence_mapping"] is None


def _validate_carried_fixture_record(fixture_record: Any) -> None:
    """Fully validate the opaque carried fixture record against the committed
    schema and against direct recomputation from verifier-owned mathematics.

    Raises MANIFEST_SCHEMA_FAILURE / replay_comparison on any defect. The
    fixture record is read only; it is never mutated.
    """
    if not isinstance(fixture_record, dict) or \
            tuple(fixture_record.keys()) != FIXTURE_RECORD_FIELD_KEYS:
        raise _schema_fault("carried fixture-record key set/order invalid")
    fr = fixture_record

    # seed_tuple: exact tuple contract (reuses the generator's seed validator).
    seed = fr["seed_tuple"]
    if not _generator.validate_seed_tuple(seed)["valid"]:
        raise _schema_fault("fixture seed_tuple violates the exact tuple contract")

    # C and D agree with the seed's construction supports.
    if fr["C"] != [0, seed[0], seed[1]] or fr["D"] != [0, seed[2], seed[3]]:
        raise _schema_fault("C/D do not agree with seed_tuple")

    # support_A / support_B: well-formed, and agree with the declared
    # C+D / C-D construction (reuses the generator's construction).
    if not _valid_support_list(fr["support_A"]) or not _valid_support_list(fr["support_B"]):
        raise _schema_fault("support_A/support_B not valid weight-9 supports")
    support_a = fr["support_A"]
    support_b = fr["support_B"]
    constructed_a, constructed_b = _generator.construct_pair_from_seed(seed)
    if support_a != list(constructed_a) or support_b != list(constructed_b):
        raise _schema_fault("support_A/support_B do not agree with C+D/C-D construction")

    # binary evidence agrees with supports.
    if not _valid_binary_list(fr["binary_A"]) or not _valid_binary_list(fr["binary_B"]):
        raise _schema_fault("binary_A/binary_B not valid 64-length 0/1 arrays")
    if fr["binary_A"] != list(_verifier.support_to_binary(support_a)) or \
            fr["binary_B"] != list(_verifier.support_to_binary(support_b)):
        raise _schema_fault("binary evidence disagrees with supports")

    # weights.
    if not (_is_strict_int(fr["weight_A"]) and fr["weight_A"] == 9) or \
            not (_is_strict_int(fr["weight_B"]) and fr["weight_B"] == 9):
        raise _schema_fault("weight_A/weight_B are not the strict integer 9")

    # A2 evidence agrees with direct recomputation.
    if not _valid_int_list(fr["A2_A"], N) or not _valid_int_list(fr["A2_B"], N):
        raise _schema_fault("A2 evidence malformed")
    if fr["A2_A"] != list(_verifier.periodic_autocorrelation(support_a)) or \
            fr["A2_B"] != list(_verifier.periodic_autocorrelation(support_b)):
        raise _schema_fault("A2 evidence disagrees with direct recomputation")

    # transition evidence agrees with direct recomputation.
    if not _valid_transition_table(fr["transition_table_A"]) or \
            not _valid_transition_table(fr["transition_table_B"]):
        raise _schema_fault("transition table evidence malformed")
    if fr["transition_table_A"] != _verifier.step_one_transition_table(support_a) or \
            fr["transition_table_B"] != _verifier.step_one_transition_table(support_b):
        raise _schema_fault("transition evidence disagrees with direct recomputation")

    # affine and affine-complement certificates: exact shape, types, values.
    if not _valid_affine_certificate(fr["affine_inequivalence_certificate"], 2048):
        raise _schema_fault("affine certificate shape/values invalid")
    if not _valid_affine_certificate(fr["affine_complement_inequivalence_certificate"], 4096):
        raise _schema_fault("affine-complement certificate shape/values invalid")

    # triple evidence agrees with direct recomputation.
    count = fr["triple_disagreement_count"]
    indices = fr["triple_disagreement_indices"]
    if not (_is_strict_int(count) and count > 0):
        raise _schema_fault("triple_disagreement_count not a strict positive integer")
    if not isinstance(indices, list) or len(indices) != count:
        raise _schema_fault("triple_disagreement_count does not equal the index count")
    expected_indices = _verifier.triple_disagreement_indices(support_a, support_b)
    if indices != expected_indices:
        raise _schema_fault("triple evidence disagrees with direct recomputation")

    # orbit keys agree with direct recomputation.
    if fr["member_orbit_key_A"] != _verifier.member_orbit_key(support_a) or \
            fr["member_orbit_key_B"] != _verifier.member_orbit_key(support_b):
        raise _schema_fault("member orbit keys disagree with direct recomputation")

    # pair key: exact valid tuple, agreeing with the certified member-key result.
    pair_key = fr["pair_duplicate_key"]
    if type(pair_key) is not tuple or len(pair_key) != 2 or \
            not all(isinstance(k, str) and len(k) == N and set(k) <= {"0", "1"} for k in pair_key) or \
            not pair_key[0] < pair_key[1]:
        raise _schema_fault("pair_duplicate_key is not an exact valid tuple")
    if pair_key != _verifier.pair_duplicate_key(support_a, support_b):
        raise _schema_fault("pair_duplicate_key disagrees with direct recomputation")


def project_accepted_record(accepted_record: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministically validate and project one reducer accepted-record wrapper
    into the exact committed S1A flat accepted-fixture object (§10.2).

    The complete wrapper and carried fixture structure are validated (strict
    integer-not-bool checks; direct recomputation via verifier-owned pure
    mathematics). Acceptance metadata leads; the opaque fixture fields are copied
    unchanged, in the committed §10.2 order, with their exact values. The input
    wrapper and fixture record are not mutated, and no wrapper-only
    ``fixture_record`` key survives into the flat object. Any defect raises
    MANIFEST_SCHEMA_FAILURE / replay_comparison.
    """
    if not isinstance(accepted_record, dict) or \
            tuple(accepted_record.keys()) != ACCEPTED_RECORD_WRAPPER_KEYS:
        raise _schema_fault("accepted-record wrapper key set/order invalid")
    if not _is_strict_nonneg_int(accepted_record["family_index"]):
        raise _schema_fault("family_index is not a strict nonnegative integer")
    if not _is_strict_nonneg_int(accepted_record["seed_order_position"]):
        raise _schema_fault("seed_order_position is not a strict nonnegative integer")
    _validate_carried_fixture_record(accepted_record["fixture_record"])

    fixture_record = accepted_record["fixture_record"]
    flat: Dict[str, Any] = {
        "family_index": accepted_record["family_index"],
        "seed_order_position": accepted_record["seed_order_position"],
    }
    for key in FIXTURE_RECORD_FIELD_KEYS:
        flat[key] = fixture_record[key]
    return flat


def _project_accepted_records(accepted_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(accepted_records, list):
        raise _schema_fault("accepted records must be a list")
    if len(accepted_records) > K_SYNTHETIC:
        raise _schema_fault("accepted count exceeds K_synthetic = 8")
    projected: List[Dict[str, Any]] = []
    previous_seed_order_position: Optional[int] = None
    for position, record in enumerate(accepted_records):
        flat = project_accepted_record(record)
        if flat["family_index"] != position:
            raise _schema_fault("family_index is not gap-free / equal to accepted-list position")
        seed_order_position = flat["seed_order_position"]
        if previous_seed_order_position is not None and \
                not seed_order_position > previous_seed_order_position:
            raise _schema_fault("seed_order_position values are not strictly increasing")
        previous_seed_order_position = seed_order_position
        projected.append(flat)
    return projected


def build_candidate_manifest(
    fixed_fixture: Dict[str, Any],
    accepted_records: List[Dict[str, Any]],
    search_diagnostics: Dict[str, Any],
    source_identity: Dict[str, Any],
    configuration_identity: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a candidate manifest with ``family_frozen = false`` and populated hash.

    ``accepted_records`` are the reducer's accepted-record wrappers; each is
    projected into the exact committed S1A flat accepted-fixture object.
    """
    validation = {"valid": True, "failure_stage": None, "detail": None}
    manifest = _assemble_manifest(
        family_frozen=False,
        fixed_fixture=fixed_fixture,
        accepted_fixtures=_project_accepted_records(accepted_records),
        search_diagnostics=search_diagnostics,
        source_identity=source_identity,
        configuration_identity=configuration_identity,
        validation=validation,
        ordered_failure_codes=[],
    )
    return populate_manifest_payload_hash(manifest)


def build_fixed_fixture_failure_manifest(
    fixed_fixture: Dict[str, Any],
    source_identity: Dict[str, Any],
    configuration_identity: Dict[str, Any],
) -> Dict[str, Any]:
    """Canonical fixed-fixture failure manifest (family_frozen = false)."""
    failure_code = fixed_fixture.get("validation", {}).get("failure_code")
    ordered_failure_codes = [failure_code] if failure_code else ["FIXED_FIXTURE_RECONSTRUCTION_FAILURE"]
    search_diagnostics = {
        "total_seeds_visited": 0,
        "eligibility_rejection_counts": _empty_rejection_counts(),
        "eligible_duplicate_count": 0,
        "accepted_seed_order_positions": [],
        "terminal_seed_tuple": None,
        "terminal_status": "FIXED_FIXTURE_FAILURE",
    }
    validation = {"valid": False, "failure_stage": "fixed_fixture", "detail": None}
    manifest = _assemble_manifest(
        family_frozen=False,
        fixed_fixture=fixed_fixture,
        accepted_fixtures=[],
        search_diagnostics=search_diagnostics,
        source_identity=source_identity,
        configuration_identity=configuration_identity,
        validation=validation,
        ordered_failure_codes=ordered_failure_codes,
    )
    return populate_manifest_payload_hash(manifest)


def build_seed_exhaustion_failure_manifest(
    fixed_fixture: Dict[str, Any],
    accepted_records: List[Dict[str, Any]],
    search_diagnostics: Dict[str, Any],
    source_identity: Dict[str, Any],
    configuration_identity: Dict[str, Any],
) -> Dict[str, Any]:
    """Canonical seed-space-exhaustion failure manifest (family_frozen = false).

    ``accepted_records`` are the reducer's accepted-record wrappers (a partial
    family), projected into the exact committed S1A flat accepted-fixture shape.
    """
    normalized_diagnostics = _ordered_search_diagnostics(search_diagnostics)
    normalized_diagnostics = dict(normalized_diagnostics)
    normalized_diagnostics["terminal_status"] = "SEED_SPACE_EXHAUSTED"
    validation = {"valid": False, "failure_stage": "seed_exhaustion", "detail": None}
    manifest = _assemble_manifest(
        family_frozen=False,
        fixed_fixture=fixed_fixture,
        accepted_fixtures=_project_accepted_records(accepted_records),
        search_diagnostics=normalized_diagnostics,
        source_identity=source_identity,
        configuration_identity=configuration_identity,
        validation=validation,
        ordered_failure_codes=["INSUFFICIENT_UNIQUE_FIXTURES"],
    )
    return populate_manifest_payload_hash(manifest)


def _empty_rejection_counts() -> Dict[str, int]:
    return {
        "A_CARDINALITY_NOT_9": 0,
        "B_CARDINALITY_NOT_9": 0,
        "IDENTICAL_SUPPORTS": 0,
        "A2_MISMATCH": 0,
        "TRANSITION_TABLE_MISMATCH": 0,
        "AFFINE_EQUIVALENT": 0,
        "AFFINE_COMPLEMENT_EQUIVALENT": 0,
        "TRIPLE_ARRAY_EQUAL": 0,
    }


# --------------------------------------------------------------------------- #
# Candidate-pass comparison and finalization
# --------------------------------------------------------------------------- #

def build_candidate_pass_bundle(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Derive the six-field candidate-pass comparison bundle from a populated manifest."""
    accepted_fixture_order = [af["pair_duplicate_key"] for af in manifest["accepted_fixtures"]]
    return {
        "canonical_payload_bytes": canonical_payload_bytes(manifest),
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "canonical_manifest_bytes": canonical_manifest_bytes(manifest),
        "external_manifest_sha256": external_manifest_sha256(manifest),
        "accepted_fixture_order": accepted_fixture_order,
        "search_diagnostics": manifest["search_diagnostics"],
    }


def _validate_bundle(bundle: Any) -> None:
    if not isinstance(bundle, dict) or set(bundle.keys()) != set(CANDIDATE_BUNDLE_KEYS):
        raise SyntheticFixtureProcessFailure(
            "MANIFEST_SCHEMA_FAILURE", "replay_comparison", "candidate-pass bundle schema invalid")
    if not isinstance(bundle["canonical_payload_bytes"], (bytes, bytearray)):
        raise SyntheticFixtureProcessFailure(
            "MANIFEST_SCHEMA_FAILURE", "replay_comparison", "canonical_payload_bytes not bytes")
    if not isinstance(bundle["canonical_manifest_bytes"], (bytes, bytearray)):
        raise SyntheticFixtureProcessFailure(
            "MANIFEST_SCHEMA_FAILURE", "replay_comparison", "canonical_manifest_bytes not bytes")
    if not isinstance(bundle["manifest_payload_sha256"], str):
        raise SyntheticFixtureProcessFailure(
            "MANIFEST_SCHEMA_FAILURE", "replay_comparison", "manifest_payload_sha256 not str")
    if not isinstance(bundle["external_manifest_sha256"], str):
        raise SyntheticFixtureProcessFailure(
            "MANIFEST_SCHEMA_FAILURE", "replay_comparison", "external_manifest_sha256 not str")
    if not isinstance(bundle["accepted_fixture_order"], list):
        raise SyntheticFixtureProcessFailure(
            "MANIFEST_SCHEMA_FAILURE", "replay_comparison", "accepted_fixture_order not list")
    if not isinstance(bundle["search_diagnostics"], dict):
        raise SyntheticFixtureProcessFailure(
            "MANIFEST_SCHEMA_FAILURE", "replay_comparison", "search_diagnostics not dict")


def compare_candidate_passes(bundle_a: Any, bundle_b: Any) -> Dict[str, Any]:
    """Compare two structurally valid candidate-pass bundles.

    Returns one deterministic comparison result object. An ordinary, structurally
    valid mismatch is reported (not raised). A malformed bundle raises the single
    process exception with MANIFEST_SCHEMA_FAILURE / replay_comparison.
    """
    _validate_bundle(bundle_a)
    _validate_bundle(bundle_b)

    checks = [
        ("canonical_payload_bytes_mismatch",
         bytes(bundle_a["canonical_payload_bytes"]) != bytes(bundle_b["canonical_payload_bytes"])),
        ("manifest_payload_sha256_mismatch",
         bundle_a["manifest_payload_sha256"] != bundle_b["manifest_payload_sha256"]),
        ("canonical_manifest_bytes_mismatch",
         bytes(bundle_a["canonical_manifest_bytes"]) != bytes(bundle_b["canonical_manifest_bytes"])),
        ("external_manifest_sha256_mismatch",
         bundle_a["external_manifest_sha256"] != bundle_b["external_manifest_sha256"]),
        ("accepted_fixture_order_mismatch",
         bundle_a["accepted_fixture_order"] != bundle_b["accepted_fixture_order"]),
        ("search_diagnostics_mismatch",
         bundle_a["search_diagnostics"] != bundle_b["search_diagnostics"]),
    ]
    mismatch_reasons = [name for name in MISMATCH_REASON_ORDER
                        for (candidate_name, differs) in checks
                        if candidate_name == name and differs]

    if not mismatch_reasons:
        return {"matches": True, "failure_code": None, "failure_stage": None, "mismatch_reasons": []}
    return {
        "matches": False,
        "failure_code": "REPLAY_MISMATCH",
        "failure_stage": "replay_comparison",
        "mismatch_reasons": mismatch_reasons,
    }


SUCCESS_COMPARISON_KEYS: Tuple[str, ...] = (
    "matches",
    "failure_code",
    "failure_stage",
    "mismatch_reasons",
)


def _is_exact_success_comparison(comparison_result: Any) -> bool:
    """The sole accepted finalization input is exactly the ordered success
    comparison object: matches True, failure_code None, failure_stage None,
    mismatch_reasons an empty list, with exactly these keys in this order."""
    if not isinstance(comparison_result, dict):
        return False
    if tuple(comparison_result.keys()) != SUCCESS_COMPARISON_KEYS:
        return False
    if comparison_result["matches"] is not True:
        return False
    if comparison_result["failure_code"] is not None:
        return False
    if comparison_result["failure_stage"] is not None:
        return False
    mismatch_reasons = comparison_result["mismatch_reasons"]
    return isinstance(mismatch_reasons, list) and mismatch_reasons == []


def finalize_authoritative_manifest(
    candidate_manifest: Dict[str, Any],
    comparison_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Deterministic finalization.

    Accepts only the exact successful comparison object; every other comparison
    raises REPLAY_MISMATCH / finalization. Changes only ``family_frozen``
    (false -> true) and recomputes the derived payload/manifest bytes and hashes.
    Any failure of the final recomputation boundary (payload/manifest
    serialization, hash population, or external hashing) is exposed by this API
    as HASH_IDENTITY_FAILURE / hash_identity; SERIALIZATION_FAILURE /
    serialization is not permitted to escape finalization. The direct canonical
    serialization helpers retain their own SERIALIZATION_FAILURE / serialization
    behavior when called independently. Returns an in-memory bundle only.
    """
    if not _is_exact_success_comparison(comparison_result):
        raise SyntheticFixtureProcessFailure(
            "REPLAY_MISMATCH", "finalization", "finalization requires the exact successful comparison")
    try:
        final_manifest: Dict[str, Any] = {}
        for key in candidate_manifest.keys():
            final_manifest[key] = candidate_manifest[key]
        final_manifest["family_frozen"] = True                  # the only field changed
        final_manifest["manifest_payload_sha256"] = None
        final_manifest = populate_manifest_payload_hash(final_manifest)
        payload_bytes = canonical_payload_bytes(final_manifest)
        manifest_bytes = canonical_manifest_bytes(final_manifest)
        external_sha = external_manifest_sha256(final_manifest)
    except SyntheticFixtureProcessFailure as exc:
        raise SyntheticFixtureProcessFailure(
            "HASH_IDENTITY_FAILURE", "hash_identity",
            "final identities could not be recomputed (%s@%s)" % (exc.failure_code, exc.failure_stage))
    return {
        "final_manifest_object": final_manifest,
        "canonical_payload_bytes": payload_bytes,
        "manifest_payload_sha256": final_manifest["manifest_payload_sha256"],
        "canonical_manifest_bytes": manifest_bytes,
        "external_manifest_sha256": external_sha,
    }


# --------------------------------------------------------------------------- #
# Static source-boundary validation
# --------------------------------------------------------------------------- #

_FORBIDDEN_IMPORT_ROOTS = frozenset({
    "numpy", "scipy", "pandas", "requests", "urllib", "http", "socket",
    "subprocess", "importlib", "random", "secrets", "time", "datetime",
    "uuid", "locale", "platform",
    "cv2", "mss", "pyautogui", "PIL",
})
_CHALLENGER_MODULE = "independent_order_sensitive_descriptor_v0_1"
_PRODUCTION_ROOTS = frozenset({"torment_service"})
# Assembled from fragments so these markers never appear verbatim in this source
# (which prevents the boundary checker from flagging its own vocabulary).
# Generic historical / frozen / retained tokens. Substring matching means each
# base token also covers its ``_module`` form and longer compounds (e.g.
# ``asymmetry_audit`` covers ``historical_asymmetry_audit``). Assembled from
# fragments so no full token appears verbatim in this source.
_GENERIC_FROZEN_TOKENS = (
    "historical" + "_f3",
    "frozen" + "_family",
    "retained" + "_family",
    "retained" + "_evidence",
    "asymmetry" + "_audit",
)
_FROZEN_MODULE_MARKERS = (
    "psi" + "_trs",
    "run_n64" + "_falsifier",
    "algebraic_n64_f3" + "_evaluator",
    "analyze_algebraic_n64_f3" + "_asymmetry",
) + _GENERIC_FROZEN_TOKENS
# Retained-evidence directories assembled from fragments so no full marker
# appears verbatim in this source.
_RETAINED_RESULTS_DIR = "research/brainvision/" + "results" + "/"
_RETAINED_GENERIC_DIRS = tuple(
    "research/brainvision/" + token + "/" for token in _GENERIC_FROZEN_TOKENS
)
_FROZEN_PATH_MARKERS = (
    "algebraic_n64_primary_v0_1_f3_" + "evaluation",
    "algebraic_n64_primary_v0_1_f3_" + "asymmetry" + "_audit",
    _RETAINED_RESULTS_DIR,                       # the retained results directory (covers 478/479/480)
    _RETAINED_RESULTS_DIR + "results.csv",
    _RETAINED_RESULTS_DIR + "results.json",
) + _GENERIC_FROZEN_TOKENS + _RETAINED_GENERIC_DIRS
# os-module attributes whose access is an environment-gate read.
_ENVIRONMENT_ATTRS = frozenset({"environ", "getenv"})


class _NormalizationReject(Exception):
    pass


def _lexical_normalize(path: Any) -> str:
    """Platform-independent lexical repository-relative path normalization (§9)."""
    if not isinstance(path, str) or path == "":
        raise _NormalizationReject("empty or non-string path")
    working = path.replace("\\", "/")
    if working.startswith("/"):
        raise _NormalizationReject("absolute path")
    if working.startswith("//"):
        raise _NormalizationReject("UNC-like path")
    if len(working) >= 2 and working[1] == ":" and (
            ("a" <= working[0] <= "z") or ("A" <= working[0] <= "Z")):
        raise _NormalizationReject("drive-prefixed path")
    retained: List[str] = []
    for segment in working.split("/"):
        if segment == "" or segment == ".":
            continue
        if segment == "..":
            if not retained:
                raise _NormalizationReject("root-escaping path")
            retained.pop()
            continue
        retained.append(segment)
    result = "/".join(retained)
    if result == "":
        raise _NormalizationReject("empty normalized result")
    return result


def _collect_import_roots(tree: ast.AST) -> List[str]:
    """Every imported module token, including relative-import forms.

    Handles ``import x``, ``from m import y`` (module ``m``), and relative
    imports ``from . import m`` / ``from .m import y`` / ``from ..m import y``
    (whose ``node.module`` may be empty), so an aliased relative import of a
    prohibited module is not overlooked.
    """
    modules: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
            if node.level and node.level > 0:
                # Relative import: the imported names may themselves be submodules.
                for alias in node.names:
                    modules.append(alias.name)
    return modules


def _has_dynamic_import(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "__import__":
                return True
            if isinstance(func, ast.Attribute) and func.attr in ("import_module", "__import__"):
                return True
    return False


def _has_environment_read(tree: ast.AST) -> bool:
    """Detect environment-gate reads, including aliased and assignment-aliased forms.

    Covers ``os.environ`` / ``os.environ[...]`` / ``os.environ.get(...)`` /
    ``os.getenv(...)``; aliased ``import os as x`` then ``x.environ`` /
    ``x.getenv``; ``from os import environ`` / ``from os import getenv``; and
    straightforward Name-to-Name assignment aliases derived from a known os alias
    (``alias = os``; ``alias2 = alias``; multi-step chains). Only bounded AST
    analysis over simple assignments is performed -- no general data-flow.
    """
    os_aliases: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os" or alias.name.split(".")[0] == "os":
                    os_aliases.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module == "os" and (node.level or 0) == 0:
                for alias in node.names:
                    if alias.name in _ENVIRONMENT_ATTRS:
                        return True

    # Collect simple ``Name = Name`` (and ``a = b = Name``) assignments once.
    simple_assignments: List[Tuple[List[str], str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name):
            target_names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if target_names:
                simple_assignments.append((target_names, node.value.id))

    # Propagate os aliases through those assignments to a fixpoint. A left-hand
    # name becomes an os alias only when its right-hand name is already a known
    # os alias, so unrelated values are never treated as aliases.
    changed = True
    while changed:
        changed = False
        for target_names, right_hand_name in simple_assignments:
            if right_hand_name in os_aliases:
                for name in target_names:
                    if name not in os_aliases:
                        os_aliases.add(name)
                        changed = True

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in os_aliases and node.attr in _ENVIRONMENT_ATTRS:
                return True
    return False


def _has_main_block(tree: ast.AST) -> bool:
    """Detect an ``if __name__ == "__main__":`` guard in either operand order
    (parenthesization does not change the AST)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            operands = [node.test.left] + list(node.test.comparators)
            has_name = any(isinstance(op, ast.Name) and op.id == "__name__" for op in operands)
            has_main = any(
                isinstance(op, ast.Constant) and isinstance(op.value, str) and op.value == "__main__"
                for op in operands)
            if has_name and has_main:
                return True
    return False


def _string_constants(tree: ast.AST) -> List[str]:
    out: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def validate_source_boundary(
    source_path: Any,
    source_text: Any,
    allowlist: Sequence[str],
) -> Dict[str, Any]:
    """Lexical + AST static boundary validation.

    Operates only on the supplied normalized source path, source text, and exact
    five-element allowlist. Performs no filesystem resolution, symlink following,
    directory traversal, Git query, environment read, or repository read. On a
    violation it raises the single process exception with the first applicable
    §16 code; otherwise it returns a pass result.
    """
    codes: set = set()

    if tuple(allowlist) != AUTHORIZED_ALLOWLIST:
        codes.add("SOURCE_OWNERSHIP_FAILURE")

    normalized: Optional[str] = None
    try:
        normalized = _lexical_normalize(source_path)
    except _NormalizationReject:
        codes.add("SOURCE_OWNERSHIP_FAILURE")
    if normalized is not None and normalized not in AUTHORIZED_ALLOWLIST:
        codes.add("SOURCE_OWNERSHIP_FAILURE")

    if not isinstance(source_text, str):
        codes.add("SOURCE_OWNERSHIP_FAILURE")
    else:
        try:
            tree: Optional[ast.AST] = ast.parse(source_text)
        except SyntaxError:
            # Fail closed: unparseable source cannot be cleared. The raw
            # exception is not leaked.
            codes.add("FORBIDDEN_IMPORT_DETECTED")
            tree = None
        if tree is not None:
            for module in _collect_import_roots(tree):
                root = module.split(".")[0]
                if module == _CHALLENGER_MODULE or root == _CHALLENGER_MODULE:
                    codes.add("PROHIBITED_CHALLENGER_CONTACT")
                elif root in _PRODUCTION_ROOTS:
                    codes.add("PRODUCTION_BOUNDARY_VIOLATION")
                elif any(marker in module for marker in _FROZEN_MODULE_MARKERS):
                    codes.add("PROHIBITED_FROZEN_FAMILY_CONTACT")
                elif root in _FORBIDDEN_IMPORT_ROOTS:
                    codes.add("FORBIDDEN_IMPORT_DETECTED")
            if _has_dynamic_import(tree):
                codes.add("FORBIDDEN_IMPORT_DETECTED")
            if _has_environment_read(tree):
                codes.add("PRODUCTION_BOUNDARY_VIOLATION")
            if _has_main_block(tree):
                codes.add("PRODUCTION_BOUNDARY_VIOLATION")
            for literal in _string_constants(tree):
                if any(marker in literal for marker in _FROZEN_PATH_MARKERS):
                    codes.add("PROHIBITED_FROZEN_FAMILY_CONTACT")

    if codes:
        selected = min(codes, key=lambda code: S1A_FAILURE_CODE_ORDER.index(code))
        raise SyntheticFixtureProcessFailure(selected, "source_boundary", "source-boundary violation")

    return {
        "valid": True,
        "failure_code": None,
        "failure_stage": None,
        "normalized_path": normalized,
    }
