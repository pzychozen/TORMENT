"""Static Stage S3B v0.2 synthetic-validation schema contract.

This module is intentionally inert: it imports no Brainvision provider, performs
no filesystem discovery, reads no environment, runs no Git command, and contains
no descriptor or execution authority.  The key contracts mirror the committed
Stage S1 frozen-source schema reviewed for the v0.2 correction.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


N = 64
K_SYNTHETIC = 8
REQUIRED_WEIGHT = 9

MANIFEST_SCHEMA = (
    "torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-"
    "manifest-v0.1"
)
GENERATOR_ID = "independent-order-sensitive-synthetic-fixture-generator-v0.1"
VERIFIER_ID = "independent-order-sensitive-synthetic-fixture-verifier-v0.1"

SEED_ENUMERATION_POLICY = "canonical-lexicographic-c1-lt-c2-d1-lt-d2-mod-64-v0.1"
CONSTRUCTION_POLICY = "c-plus-d-and-c-minus-d-mod-64-collision-collapsed-v0.1"
ELIGIBILITY_POLICY = "first-failure-eight-predicate-descriptor-blind-v0.1"
DUPLICATE_POLICY = "member-orbit-affine-plus-complement-slot-invariant-pair-key-v0.1"

FROZEN_CONFIGURATION_SCHEMA = (
    "torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-"
    "configuration-v0.1"
)
FROZEN_CONFIGURATION_SHA256 = (
    "5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263"
)

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

MANIFEST_PAYLOAD_KEYS: Tuple[str, ...] = MANIFEST_TOP_LEVEL_KEYS[:-1]

FIXED_FIXTURE_KEYS: Tuple[str, ...] = (
    "C",
    "D",
    "support_H0",
    "support_H1",
    "binary_H0",
    "binary_H1",
    "weight_H0",
    "weight_H1",
    "A2_H0",
    "A2_H1",
    "transition_table_H0",
    "transition_table_H1",
    "affine_inequivalence_certificate",
    "affine_complement_inequivalence_certificate",
    "triple_disagreement_count",
    "triple_disagreement_indices",
    "member_orbit_key_H0",
    "member_orbit_key_H1",
    "pair_duplicate_key",
    "validation",
)

FIXED_MEMBER_BINARY_KEYS: Tuple[str, str] = ("binary_H0", "binary_H1")
FIXED_SUPPORT_KEYS: Tuple[str, str] = ("support_H0", "support_H1")
FIXED_WEIGHT_KEYS: Tuple[str, str] = ("weight_H0", "weight_H1")
FIXED_A2_KEYS: Tuple[str, str] = ("A2_H0", "A2_H1")
FIXED_TRANSITION_TABLE_KEYS: Tuple[str, str] = (
    "transition_table_H0",
    "transition_table_H1",
)
FIXED_MEMBER_ORBIT_KEY_KEYS: Tuple[str, str] = (
    "member_orbit_key_H0",
    "member_orbit_key_H1",
)

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

ACCEPTED_MEMBER_BINARY_KEYS: Tuple[str, str] = ("binary_A", "binary_B")
ACCEPTED_SUPPORT_KEYS: Tuple[str, str] = ("support_A", "support_B")
ACCEPTED_WEIGHT_KEYS: Tuple[str, str] = ("weight_A", "weight_B")
ACCEPTED_A2_KEYS: Tuple[str, str] = ("A2_A", "A2_B")
ACCEPTED_TRANSITION_TABLE_KEYS: Tuple[str, str] = (
    "transition_table_A",
    "transition_table_B",
)
ACCEPTED_MEMBER_ORBIT_KEY_KEYS: Tuple[str, str] = (
    "member_orbit_key_A",
    "member_orbit_key_B",
)

AFFINE_CERTIFICATE_KEYS: Tuple[str, ...] = (
    "equivalent",
    "search_space_size",
    "first_equivalence_mapping",
)
AFFINE_SEARCH_SPACE_SIZE = 2048
AFFINE_COMPLEMENT_SEARCH_SPACE_SIZE = 4096

FIXED_VALIDATION_KEYS: Tuple[str, ...] = ("valid", "failure_code", "detail")
MANIFEST_VALIDATION_KEYS: Tuple[str, ...] = ("valid", "failure_stage", "detail")

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
TEST_SOURCE_IDENTITY_KEYS: Tuple[str, ...] = (
    "source_path",
    "git_blob",
    "raw_sha256",
)

SEARCH_DIAGNOSTICS_KEYS: Tuple[str, ...] = (
    "total_seeds_visited",
    "eligibility_rejection_counts",
    "eligible_duplicate_count",
    "accepted_seed_order_positions",
    "terminal_seed_tuple",
    "terminal_status",
)
ELIGIBILITY_REJECTION_ORDER: Tuple[str, ...] = (
    "A_CARDINALITY_NOT_9",
    "B_CARDINALITY_NOT_9",
    "IDENTICAL_SUPPORTS",
    "A2_MISMATCH",
    "TRANSITION_TABLE_MISMATCH",
    "AFFINE_EQUIVALENT",
    "AFFINE_COMPLEMENT_EQUIVALENT",
    "TRIPLE_ARRAY_EQUAL",
)

CONFIGURATION_IDENTITY_KEYS: Tuple[str, ...] = (
    "configuration_payload",
    "configuration_sha256",
)
CONFIGURATION_PAYLOAD_KEYS: Tuple[str, ...] = (
    "configuration_schema",
    "configuration_version",
    "N",
    "K_synthetic",
    "seed_enumeration_policy",
    "construction_policy",
    "eligibility_policy",
    "duplicate_policy",
    "fixed_fixture_duplicate_key_seeding",
    "selection_rule",
    "descriptor_blind_selection",
    "pass_count",
    "parallelism",
    "backtracking",
    "challenger_contact",
    "frozen_F3_contact",
)
CONFIGURATION_PAYLOAD_VALUES: Mapping[str, Any] = MappingProxyType({
    "configuration_schema": FROZEN_CONFIGURATION_SCHEMA,
    "configuration_version": "0.1",
    "N": N,
    "K_synthetic": K_SYNTHETIC,
    "seed_enumeration_policy": SEED_ENUMERATION_POLICY,
    "construction_policy": CONSTRUCTION_POLICY,
    "eligibility_policy": ELIGIBILITY_POLICY,
    "duplicate_policy": DUPLICATE_POLICY,
    "fixed_fixture_duplicate_key_seeding": True,
    "selection_rule": "first-eight-unique-eligible-pairs",
    "descriptor_blind_selection": True,
    "pass_count": 2,
    "parallelism": 1,
    "backtracking": False,
    "challenger_contact": False,
    "frozen_F3_contact": False,
})

ORDERED_FAILURE_CODES: Tuple[str, ...] = (
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


@dataclass(frozen=True)
class SchemaValidationResult:
    valid: bool
    failure_code: Optional[str] = None
    detail: Optional[str] = None


class SchemaContractViolation(ValueError):
    def __init__(self, detail: str, failure_code: str = "MANIFEST_SCHEMA_FAILURE") -> None:
        super().__init__(detail)
        self.detail = detail
        self.failure_code = failure_code


def canonical_json_bytes(value: Any) -> bytes:
    text = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return text.encode("utf-8") + b"\n"


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def is_lower_hex(value: Any, length: int) -> bool:
    if not isinstance(value, str) or len(value) != length:
        return False
    return all(character in "0123456789abcdef" for character in value)


def is_strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def ordered_dict_from_keys(keys: Sequence[str], source: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: source[key] for key in keys}


def frozen_configuration_payload() -> Dict[str, Any]:
    return ordered_dict_from_keys(CONFIGURATION_PAYLOAD_KEYS, CONFIGURATION_PAYLOAD_VALUES)


def canonical_configuration_sha256() -> str:
    return sha256_hex(canonical_json_bytes(frozen_configuration_payload()))


def payload_projection(manifest: Mapping[str, Any]) -> Dict[str, Any]:
    projection: Dict[str, Any] = {}
    for key in manifest.keys():
        if key != "manifest_payload_sha256":
            projection[key] = manifest[key]
    return projection


def manifest_payload_sha256(manifest: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json_bytes(payload_projection(manifest)))


def support_to_binary(support: Iterable[int]) -> List[int]:
    bits = [0] * N
    for index in support:
        bits[index] = 1
    return bits


def binary_to_support(bits: Sequence[int]) -> List[int]:
    return [index for index, bit in enumerate(bits) if bit == 1]


def binary_key(bits: Sequence[int]) -> str:
    return "".join(str(bit) for bit in bits)


def _fail(detail: str, failure_code: str = "MANIFEST_SCHEMA_FAILURE") -> None:
    raise SchemaContractViolation(detail, failure_code)


def _require_key_order(value: Any, expected: Sequence[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail("%s is not an object" % label)
    if tuple(value.keys()) != tuple(expected):
        _fail("%s key set/order invalid" % label)
    return value


def _require_strict_int(value: Any, label: str) -> int:
    if not is_strict_int(value):
        _fail("%s is not a strict integer" % label)
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str):
        _fail("%s is not a string" % label)
    return value


def _require_optional_string(value: Any, label: str) -> None:
    if value is not None and not isinstance(value, str):
        _fail("%s is not null or string" % label)


def _require_int_list(value: Any, label: str, length: Optional[int] = None) -> List[int]:
    if not isinstance(value, list):
        _fail("%s is not a list" % label)
    if length is not None and len(value) != length:
        _fail("%s length invalid" % label)
    for index, element in enumerate(value):
        if not is_strict_int(element):
            _fail("%s[%d] is not a strict integer" % (label, index))
    return value


def _require_support(value: Any, label: str) -> List[int]:
    support = _require_int_list(value, label, REQUIRED_WEIGHT)
    previous = -1
    for element in support:
        if not 0 <= element < N:
            _fail("%s contains out-of-range residue" % label)
        if element <= previous:
            _fail("%s is not strictly ascending" % label)
        previous = element
    return support


def _require_binary_vector(value: Any, label: str) -> List[int]:
    bits = _require_int_list(value, label, N)
    for index, bit in enumerate(bits):
        if bit not in (0, 1):
            _fail("%s[%d] is not binary" % (label, index))
    return bits


def _require_transition_table(value: Any, label: str) -> List[List[int]]:
    if not isinstance(value, list) or len(value) != 2:
        _fail("%s is not a 2x2 table" % label)
    for row_index, row in enumerate(value):
        if not isinstance(row, list) or len(row) != 2:
            _fail("%s[%d] is not a length-2 row" % (label, row_index))
        for cell_index, cell in enumerate(row):
            if not is_strict_int(cell) or cell < 0:
                _fail("%s[%d][%d] is not a nonnegative strict integer" % (
                    label,
                    row_index,
                    cell_index,
                ))
    return value


def _require_pair_key(value: Any, label: str) -> List[str]:
    if not isinstance(value, list) or len(value) != 2:
        _fail("%s is not a two-entry list" % label)
    for index, element in enumerate(value):
        if not isinstance(element, str) or len(element) != N:
            _fail("%s[%d] is not a 64-character key" % (label, index))
        if set(element) - {"0", "1"}:
            _fail("%s[%d] is not binary text" % (label, index))
    return value


def _require_affine_certificate(value: Any, label: str, search_space_size: int) -> None:
    cert = _require_key_order(value, AFFINE_CERTIFICATE_KEYS, label)
    if cert["equivalent"] is not False:
        _fail("%s.equivalent is not false" % label)
    if not is_strict_int(cert["search_space_size"]) or (
            cert["search_space_size"] != search_space_size):
        _fail("%s.search_space_size invalid" % label)
    if cert["first_equivalence_mapping"] is not None:
        _fail("%s.first_equivalence_mapping is not null" % label)


def _require_triple_indices(value: Any, count: int, label: str) -> None:
    if not isinstance(value, list):
        _fail("%s is not a list" % label)
    if len(value) != count:
        _fail("%s length disagrees with triple_disagreement_count" % label)
    for index, entry in enumerate(value):
        if not isinstance(entry, list) or len(entry) != 2:
            _fail("%s[%d] is not a two-entry lag list" % (label, index))
        for coordinate in entry:
            if not is_strict_int(coordinate) or not (1 <= coordinate < N):
                _fail("%s[%d] contains invalid lag" % (label, index))


def _validate_lower_order_pair(record: Mapping[str, Any], label: str,
                               support_keys: Tuple[str, str],
                               binary_keys: Tuple[str, str],
                               weight_keys: Tuple[str, str],
                               a2_keys: Tuple[str, str],
                               table_keys: Tuple[str, str]) -> None:
    supports = []
    binaries = []
    for support_key, binary_key, weight_key, a2_key, table_key in zip(
            support_keys, binary_keys, weight_keys, a2_keys, table_keys):
        support = _require_support(record[support_key], "%s.%s" % (label, support_key))
        bits = _require_binary_vector(record[binary_key], "%s.%s" % (label, binary_key))
        if bits != support_to_binary(support):
            _fail("%s.%s disagrees with %s" % (label, binary_key, support_key))
        weight = _require_strict_int(record[weight_key], "%s.%s" % (label, weight_key))
        if weight != REQUIRED_WEIGHT or weight != len(support):
            _fail("%s.%s invalid" % (label, weight_key))
        _require_int_list(record[a2_key], "%s.%s" % (label, a2_key), N)
        _require_transition_table(record[table_key], "%s.%s" % (label, table_key))
        supports.append(support)
        binaries.append(bits)
    if supports[0] == supports[1]:
        _fail("%s member supports are identical" % label)
    if binaries[0] == binaries[1]:
        _fail("%s member binaries are identical" % label)


def _validate_common_certificates(record: Mapping[str, Any], label: str) -> None:
    _require_affine_certificate(
        record["affine_inequivalence_certificate"],
        "%s.affine_inequivalence_certificate" % label,
        AFFINE_SEARCH_SPACE_SIZE,
    )
    _require_affine_certificate(
        record["affine_complement_inequivalence_certificate"],
        "%s.affine_complement_inequivalence_certificate" % label,
        AFFINE_COMPLEMENT_SEARCH_SPACE_SIZE,
    )
    count = _require_strict_int(
        record["triple_disagreement_count"],
        "%s.triple_disagreement_count" % label,
    )
    if count <= 0:
        _fail("%s.triple_disagreement_count is not positive" % label)
    _require_triple_indices(
        record["triple_disagreement_indices"],
        count,
        "%s.triple_disagreement_indices" % label,
    )
    _require_pair_key(record["pair_duplicate_key"], "%s.pair_duplicate_key" % label)


def _validate_fixed_validation(value: Any, label: str) -> None:
    validation = _require_key_order(value, FIXED_VALIDATION_KEYS, label)
    if validation["valid"] is not True:
        _fail("%s.valid is not true" % label)
    if validation["failure_code"] is not None:
        _fail("%s.failure_code is not null" % label)
    if validation["detail"] is not None:
        _fail("%s.detail is not null" % label)


def _validate_manifest_validation(value: Any, label: str) -> None:
    validation = _require_key_order(value, MANIFEST_VALIDATION_KEYS, label)
    if validation["valid"] is not True:
        _fail("%s.valid is not true" % label)
    if validation["failure_stage"] is not None:
        _fail("%s.failure_stage is not null" % label)
    if validation["detail"] is not None:
        _fail("%s.detail is not null" % label)


def validate_fixed_fixture(fixed_fixture: Any) -> SchemaValidationResult:
    try:
        record = _require_key_order(fixed_fixture, FIXED_FIXTURE_KEYS, "fixed_fixture")
        _require_int_list(record["C"], "fixed_fixture.C", 3)
        _require_int_list(record["D"], "fixed_fixture.D", 3)
        _validate_lower_order_pair(
            record,
            "fixed_fixture",
            FIXED_SUPPORT_KEYS,
            FIXED_MEMBER_BINARY_KEYS,
            FIXED_WEIGHT_KEYS,
            FIXED_A2_KEYS,
            FIXED_TRANSITION_TABLE_KEYS,
        )
        _validate_common_certificates(record, "fixed_fixture")
        for key in FIXED_MEMBER_ORBIT_KEY_KEYS:
            _require_string(record[key], "fixed_fixture.%s" % key)
        _validate_fixed_validation(record["validation"], "fixed_fixture.validation")
    except SchemaContractViolation as exc:
        return SchemaValidationResult(False, exc.failure_code, exc.detail)
    return SchemaValidationResult(True)


def validate_accepted_fixture(accepted_fixture: Any,
                              expected_family_index: Optional[int] = None,
                              previous_seed_order_position: Optional[int] = None
                              ) -> SchemaValidationResult:
    try:
        record = _require_key_order(
            accepted_fixture,
            ACCEPTED_FIXTURE_KEYS,
            "accepted_fixture",
        )
        family_index = _require_strict_int(record["family_index"], "family_index")
        if expected_family_index is not None and family_index != expected_family_index:
            _fail("family_index is not gap-free / equal to accepted-list position")
        seed_position = _require_strict_int(
            record["seed_order_position"],
            "seed_order_position",
        )
        if previous_seed_order_position is not None and seed_position <= previous_seed_order_position:
            _fail("seed_order_position values are not strictly increasing")
        seed_tuple = _require_int_list(record["seed_tuple"], "seed_tuple", 4)
        for seed_value in seed_tuple:
            if not 0 <= seed_value < N:
                _fail("seed_tuple contains out-of-range residue")
        _require_int_list(record["C"], "accepted_fixture.C", 3)
        _require_int_list(record["D"], "accepted_fixture.D", 3)
        _validate_lower_order_pair(
            record,
            "accepted_fixture",
            ACCEPTED_SUPPORT_KEYS,
            ACCEPTED_MEMBER_BINARY_KEYS,
            ACCEPTED_WEIGHT_KEYS,
            ACCEPTED_A2_KEYS,
            ACCEPTED_TRANSITION_TABLE_KEYS,
        )
        _validate_common_certificates(record, "accepted_fixture")
        for key in ACCEPTED_MEMBER_ORBIT_KEY_KEYS:
            _require_string(record[key], "accepted_fixture.%s" % key)
    except SchemaContractViolation as exc:
        return SchemaValidationResult(False, exc.failure_code, exc.detail)
    return SchemaValidationResult(True)


def _validate_search_diagnostics(value: Any) -> None:
    diagnostics = _require_key_order(value, SEARCH_DIAGNOSTICS_KEYS, "search_diagnostics")
    total = _require_strict_int(
        diagnostics["total_seeds_visited"],
        "search_diagnostics.total_seeds_visited",
    )
    if total < K_SYNTHETIC:
        _fail("search_diagnostics.total_seeds_visited invalid")
    rejection_counts = _require_key_order(
        diagnostics["eligibility_rejection_counts"],
        ELIGIBILITY_REJECTION_ORDER,
        "search_diagnostics.eligibility_rejection_counts",
    )
    for key in ELIGIBILITY_REJECTION_ORDER:
        count = _require_strict_int(
            rejection_counts[key],
            "search_diagnostics.eligibility_rejection_counts.%s" % key,
        )
        if count < 0:
            _fail("negative rejection count")
    duplicate_count = _require_strict_int(
        diagnostics["eligible_duplicate_count"],
        "search_diagnostics.eligible_duplicate_count",
    )
    if duplicate_count < 0:
        _fail("eligible_duplicate_count is negative")
    positions = _require_int_list(
        diagnostics["accepted_seed_order_positions"],
        "search_diagnostics.accepted_seed_order_positions",
        K_SYNTHETIC,
    )
    previous = -1
    for position in positions:
        if position <= previous:
            _fail("accepted_seed_order_positions not strictly increasing")
        previous = position
    terminal_seed = diagnostics["terminal_seed_tuple"]
    if terminal_seed is not None:
        _require_int_list(terminal_seed, "search_diagnostics.terminal_seed_tuple", 4)
    if diagnostics["terminal_status"] != "ACCEPTED_EIGHT":
        _fail("search_diagnostics.terminal_status is not ACCEPTED_EIGHT")


def _validate_source_identity(value: Any) -> None:
    identity = _require_key_order(value, SOURCE_IDENTITY_KEYS, "source_identity")
    path_keys = ("generator_source_path", "verifier_source_path")
    git_keys = ("generator_git_blob", "verifier_git_blob", "repository_commit")
    raw_keys = ("generator_raw_sha256", "verifier_raw_sha256")
    for key in path_keys:
        _require_string(identity[key], "source_identity.%s" % key)
    for key in git_keys:
        if not is_lower_hex(identity[key], 40):
            _fail("source_identity.%s is not a 40-hex identity" % key)
    for key in raw_keys:
        if not is_lower_hex(identity[key], 64):
            _fail("source_identity.%s is not a 64-hex identity" % key)
    if not isinstance(identity["test_source_identities"], list) or (
            len(identity["test_source_identities"]) != 3):
        _fail("source_identity.test_source_identities invalid")
    for index, test_identity in enumerate(identity["test_source_identities"]):
        entry = _require_key_order(
            test_identity,
            TEST_SOURCE_IDENTITY_KEYS,
            "source_identity.test_source_identities[%d]" % index,
        )
        _require_string(entry["source_path"], "test source_path")
        if not is_lower_hex(entry["git_blob"], 40):
            _fail("test git_blob invalid")
        if not is_lower_hex(entry["raw_sha256"], 64):
            _fail("test raw_sha256 invalid")
    if identity["python_version"] != "3.11.15":
        _fail("source_identity.python_version invalid")


def _validate_configuration_identity(value: Any) -> None:
    identity = _require_key_order(
        value,
        CONFIGURATION_IDENTITY_KEYS,
        "configuration_identity",
    )
    payload = _require_key_order(
        identity["configuration_payload"],
        CONFIGURATION_PAYLOAD_KEYS,
        "configuration_identity.configuration_payload",
    )
    if dict(payload) != frozen_configuration_payload():
        _fail("configuration_payload is not the frozen 16-field object",
              "HASH_IDENTITY_FAILURE")
    if identity["configuration_sha256"] != FROZEN_CONFIGURATION_SHA256:
        _fail("configuration_sha256 does not match the frozen identity",
              "HASH_IDENTITY_FAILURE")
    if canonical_configuration_sha256() != FROZEN_CONFIGURATION_SHA256:
        _fail("local frozen configuration contract digest mismatch",
              "HASH_IDENTITY_FAILURE")


def validate_manifest_payload(manifest: Any) -> SchemaValidationResult:
    try:
        record = _require_key_order(manifest, MANIFEST_TOP_LEVEL_KEYS, "manifest")
        if record["schema"] != MANIFEST_SCHEMA:
            _fail("manifest.schema invalid")
        if record["generator_id"] != GENERATOR_ID:
            _fail("manifest.generator_id invalid")
        if record["verifier_id"] != VERIFIER_ID:
            _fail("manifest.verifier_id invalid")
        if record["N"] != N or isinstance(record["N"], bool):
            _fail("manifest.N invalid")
        if record["K_synthetic"] != K_SYNTHETIC or isinstance(record["K_synthetic"], bool):
            _fail("manifest.K_synthetic invalid")
        if record["seed_enumeration_policy"] != SEED_ENUMERATION_POLICY:
            _fail("manifest.seed_enumeration_policy invalid")
        if record["construction_policy"] != CONSTRUCTION_POLICY:
            _fail("manifest.construction_policy invalid")
        if record["eligibility_policy"] != ELIGIBILITY_POLICY:
            _fail("manifest.eligibility_policy invalid")
        if record["duplicate_policy"] != DUPLICATE_POLICY:
            _fail("manifest.duplicate_policy invalid")
        if record["family_frozen"] is not True:
            _fail("manifest.family_frozen is not true")

        fixed_result = validate_fixed_fixture(record["fixed_fixture"])
        if not fixed_result.valid:
            _fail("fixed_fixture invalid: %s" % fixed_result.detail,
                  fixed_result.failure_code or "MANIFEST_SCHEMA_FAILURE")

        accepted = record["accepted_fixtures"]
        if not isinstance(accepted, list) or len(accepted) != K_SYNTHETIC:
            _fail("accepted_fixtures count is not 8")
        previous_seed_order_position: Optional[int] = None
        pair_keys = set()
        for index, fixture in enumerate(accepted):
            accepted_result = validate_accepted_fixture(
                fixture,
                expected_family_index=index,
                previous_seed_order_position=previous_seed_order_position,
            )
            if not accepted_result.valid:
                _fail("accepted_fixtures[%d] invalid: %s" % (
                    index,
                    accepted_result.detail,
                ), accepted_result.failure_code or "MANIFEST_SCHEMA_FAILURE")
            previous_seed_order_position = fixture["seed_order_position"]
            pair_key = tuple(fixture["pair_duplicate_key"])
            if pair_key in pair_keys:
                _fail("accepted_fixtures pair_duplicate_key duplicate")
            pair_keys.add(pair_key)

        _validate_search_diagnostics(record["search_diagnostics"])
        _validate_source_identity(record["source_identity"])
        _validate_configuration_identity(record["configuration_identity"])
        _validate_manifest_validation(record["validation"], "manifest.validation")
        if not isinstance(record["ordered_failure_codes"], list):
            _fail("ordered_failure_codes is not a list")
        for code in record["ordered_failure_codes"]:
            if code not in ORDERED_FAILURE_CODES:
                _fail("ordered_failure_codes contains an unknown code")
        if not is_lower_hex(record["manifest_payload_sha256"], 64):
            _fail("manifest_payload_sha256 is not a 64-hex identity")
        if record["manifest_payload_sha256"] != manifest_payload_sha256(record):
            _fail("manifest_payload_sha256 does not match payload projection",
                  "HASH_IDENTITY_FAILURE")
    except SchemaContractViolation as exc:
        return SchemaValidationResult(False, exc.failure_code, exc.detail)
    return SchemaValidationResult(True)
