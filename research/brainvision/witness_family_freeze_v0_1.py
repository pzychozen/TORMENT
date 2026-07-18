"""Deterministic descriptor-blind witness family freezer + decision ledger + authoritative replay (offline).

Consumes the frozen candidate_stream_envelope of raw records, invokes the independent verifier itself for every
record (never trusting supplied certificates, summaries, or generator diagnostics), performs deterministic
first-K freeze selection in authoritative stream order, records a complete per-candidate decision ledger, and
gates authoritative family freezing behind two-pass same-environment replay plus source/config/independence/
regression self-checks. Imports only the verifier and the zero-mathematics serializer. No generator, ΨTRS, or
descriptor import or output exists anywhere here. stdlib only otherwise.

Public authoritative operation: freeze_with_replay(). The plain single-pass freeze() is NON-AUTHORITATIVE and
can never report family_frozen=True.

Governing specification:
  docs/TORMENT_BRAINVISION_INDEPENDENT_HIGHER_ORDER_WITNESS_VERIFIER_AND_FREEZE_INFRASTRUCTURE_IMPLEMENTATION_SPECIFICATION_v0.1.md
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import witness_canonical_json_v0_1 as cjson
import witness_family_verifier_v0_1 as verifier

FREEZE_NAME = "witness_family_freeze_v0_1"
FREEZE_VERSION = "0.1"
FREEZE_RESULT_SCHEMA = "brainvision_witness_freeze_result"
FAMILY_MANIFEST_SCHEMA = "brainvision_witness_family_manifest"
K_FAMILY = verifier.K_FAMILY
NOT_EVALUATED_AFTER_K_REACHED = "NOT_EVALUATED_AFTER_K_REACHED"
RESOURCE_POLICY_STATUS = "UNBOUNDED_BY_V0_1_SPECIFICATION"


def serializer_configuration() -> Dict[str, object]:
    return {"serializer_name": cjson.SERIALIZER_NAME, "serializer_version": cjson.SERIALIZER_VERSION,
            "canonical_json_policy": "ensure_ascii_sort_keys_compact_no_nan_no_trailing_newline",
            "envelope_policy": "nonrecursive_external_payload_hash"}


def freeze_configuration() -> Dict[str, object]:
    return {"freeze_name": FREEZE_NAME, "freeze_version": FREEZE_VERSION, "K": K_FAMILY,
            "ordering_policy": "authoritative_stream_order_first_k",
            "post_k_ledger_policy": NOT_EVALUATED_AFTER_K_REACHED,
            "selection_inputs": ["stream_order", "verifier_predicates", "incremental_family_predicates"],
            "replay_policy": "same_environment_two_pass_byte_identity",
            "resource_policy_status": RESOURCE_POLICY_STATUS}


# ------------------------------------------------------------------ incremental family selection
def incremental_family_eligibility(accepted: List[dict], candidate_certificate: dict) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    accepted_members, accepted_keys, accepted_classes = set(), set(), set()
    for certificate in accepted:
        for side in ("member_certificate_A", "member_certificate_B"):
            accepted_members.add(tuple(certificate[side]["raw_support"]))
            accepted_keys.add(tuple(certificate[side]["member_G_equivalence_key"]))
        accepted_classes.add(tuple(certificate["member_certificate_A"]["autocorrelation"]))
    new_members = [tuple(candidate_certificate[side]["raw_support"])
                   for side in ("member_certificate_A", "member_certificate_B")]
    new_keys = [tuple(candidate_certificate[side]["member_G_equivalence_key"])
                for side in ("member_certificate_A", "member_certificate_B")]
    new_class = tuple(candidate_certificate["member_certificate_A"]["autocorrelation"])
    if any(member in accepted_members for member in new_members) or new_members[0] == new_members[1]:
        reasons.append(verifier.FAMILY_MEMBER_REUSED)
    if any(key in accepted_keys for key in new_keys) or new_keys[0] == new_keys[1]:
        reasons.append(verifier.FAMILY_MEMBER_G_EQUIVALENT)
    if new_class in accepted_classes:
        reasons.append(verifier.FAMILY_AUTOCORRELATION_CLASS_REUSED)
    return (len(reasons) == 0, reasons)


def _raw_ab_naming(certificate: dict) -> str:
    support_a = certificate["member_certificate_A"]["raw_support"]
    support_b = certificate["member_certificate_B"]["raw_support"]
    return "A_LEX_SMALLER_OR_EQUAL" if support_a <= support_b else "B_LEX_SMALLER"


# ------------------------------------------------------------------ single-pass (provisional) freeze
def _freeze_once(envelope_obj: object) -> Dict[str, object]:
    """Deterministic single-pass provisional payload. NEVER authoritative: family_frozen stays False here."""
    validation = verifier.validate_stream_envelope(envelope_obj)
    if not validation["valid"]:
        payload = _base_payload(None, None, None)
        payload["failure_record"] = {"failure_code": validation["code"], "stage": "stream_validation",
                                     "ordered_failure_codes": [validation["code"]]}
        return payload

    stream, mode, n = validation["payload"], validation["mode"], validation["n"]
    payload = _base_payload(stream, mode, n)
    ledger: List[dict] = []
    accepted_indices: List[int] = []
    accepted_certificates: List[dict] = []
    failure_record: Optional[dict] = None

    for index, record in enumerate(stream["records"]):
        if len(accepted_certificates) >= K_FAMILY:
            ledger.append({"candidate_generation_index": index, "status": NOT_EVALUATED_AFTER_K_REACHED,
                           "execution_invalid": False, "execution_code": None, "pair_valid": False,
                           "primary_failure_code": None, "ordered_failure_codes": [], "accepted": False,
                           "family_reject_reasons": []})
            continue
        result = verifier.verify_candidate(record, n)
        entry = {"candidate_generation_index": index, "status": "EVALUATED",
                 "execution_invalid": bool(result["execution_invalid"]),
                 "execution_code": result["execution_code"], "pair_valid": bool(result["pair_valid"]),
                 "primary_failure_code": result["primary_failure_code"],
                 "ordered_failure_codes": list(result["ordered_failure_codes"]), "accepted": False,
                 "family_reject_reasons": []}
        if result["execution_invalid"]:
            ledger.append(entry)
            failure_record = {"failure_code": result["execution_code"], "stage": "candidate_verification",
                              "candidate_generation_index": index,
                              "ordered_failure_codes": [result["execution_code"]]}
            break
        if result["pair_valid"]:
            eligible, reasons = incremental_family_eligibility(accepted_certificates, result["pair_certificate"])
            if eligible:
                entry["accepted"] = True
                accepted_indices.append(index)
                accepted_certificates.append(result["pair_certificate"])
            else:
                entry["family_reject_reasons"] = reasons
        ledger.append(entry)

    payload["candidate_decision_ledger"] = ledger
    payload["candidate_decision_ledger_sha256"] = cjson.payload_sha256(ledger)
    payload["accepted_candidate_indices"] = accepted_indices
    payload["accepted_pair_certificate_envelopes"] = [
        cjson.envelope("pair_verifier_certificate", certificate) for certificate in accepted_certificates]

    if failure_record is not None:
        payload["failure_record"] = failure_record
        return payload
    if mode == "REFERENCE_REGRESSION_N12":
        payload["regression_mode_no_primary_manifest"] = True
        return payload
    # PRIMARY_CANDIDATE_N64
    if len(accepted_certificates) == K_FAMILY:
        family = verifier.verify_family(accepted_certificates, n)
        payload["family_certificate"] = cjson.envelope("family_verifier_certificate", {
            "pair_certificate_hashes": [cjson.payload_sha256(c) for c in accepted_certificates],
            "mutual_G_inequivalent": family["mutual_G_inequivalent"],
            "members_non_reused": family["members_non_reused"],
            "distinct_autocorrelation_classes": family["distinct_autocorrelation_classes"],
            "family_valid": family["family_valid"], "ordered_failure_codes": family["ordered_failure_codes"]})
        if family["family_valid"]:
            payload["provisional_k3_valid"] = True
        else:
            payload["failure_record"] = {"failure_code": family["ordered_failure_codes"][0],
                                         "stage": "family_verification",
                                         "ordered_failure_codes": family["ordered_failure_codes"]}
    else:
        payload["failure_record"] = {"failure_code": verifier.FAMILY_NOT_FREEZABLE, "stage": "family_selection",
                                     "ordered_failure_codes": [verifier.FAMILY_NOT_FREEZABLE]}
    return payload


def _base_payload(stream: Optional[dict], mode: Optional[str], n: Optional[int]) -> Dict[str, object]:
    return {
        "schema_name": FREEZE_RESULT_SCHEMA, "schema_version": "0.1",
        "verification_mode": mode, "N": n,
        "candidate_stream_sha256": (cjson.payload_sha256(stream) if stream is not None else None),
        "candidate_count": (stream["candidate_count"] if stream is not None else None),
        "terminal_stream_status": (stream["terminal_status"] if stream is not None else None),
        "generator_identity_hash": (stream["generator_identity_hash"] if stream is not None else None),
        "generator_configuration_hash": (stream["generator_configuration_hash"] if stream is not None else None),
        "budget_identity_hash": (stream["budget_identity_hash"] if stream is not None else None),
        "candidate_decision_ledger": [], "candidate_decision_ledger_sha256": None,
        "accepted_candidate_indices": [], "accepted_pair_certificate_envelopes": [],
        "family_certificate": None, "family_manifest": None,
        "provisional_k3_valid": False, "family_frozen": False, "authoritative_operation": False,
        "regression_mode_no_primary_manifest": False, "resource_policy_status": RESOURCE_POLICY_STATUS,
        "failure_record": None,
    }


# ------------------------------------------------------------------ non-authoritative single pass (public)
def _emit_result(payload: Dict[str, object]) -> Dict[str, object]:
    """Emit the freeze_result envelope through the serialization wrapper; SERIALIZATION_FAILURE on failure."""
    envelope_obj, code = verifier.envelope_or_failure("freeze_result", payload)
    if code is not None:
        minimal = {"schema_name": FREEZE_RESULT_SCHEMA, "schema_version": "0.1", "family_frozen": False,
                   "authoritative_operation": bool(payload.get("authoritative_operation", False))
                   if isinstance(payload, dict) else False, "family_manifest": None,
                   "failure_record": {"failure_code": code, "stage": "result_serialization",
                                      "ordered_failure_codes": [code]}}
        return cjson.envelope("freeze_result", minimal)
    return envelope_obj


def freeze(envelope_obj: object) -> Dict[str, object]:
    """NON-AUTHORITATIVE single pass. family_frozen is forced False; it can never claim an authoritative freeze."""
    payload = _freeze_once(envelope_obj)
    payload["family_frozen"] = False
    payload["authoritative_operation"] = False
    payload["family_manifest"] = None
    return _emit_result(payload)


# ------------------------------------------------------------------ authoritative freeze via replay
def _run_self_checks(source_paths: Optional[Dict[str, str]]) -> Dict[str, object]:
    config = verifier.validate_local_configuration(source_paths=source_paths)
    if not config["valid"]:
        return {"valid": False, "code": config["code"], "stage": "configuration", "config": None}
    independence = verifier.independence_self_check(source_paths)
    if not independence["valid"]:
        return {"valid": False, "code": independence["code"], "stage": "independence", "config": None}
    regression = verifier.regression_self_check()
    if not regression["valid"]:
        return {"valid": False, "code": regression["code"], "stage": "regression", "config": None}
    return {"valid": True, "code": None, "config": config}


def freeze_with_replay(envelope_obj: object, repository_commit_identity: str = "UNSPECIFIED_IN_V0_1",
                       source_paths: Optional[Dict[str, str]] = None) -> Dict[str, object]:
    """Authoritative operation. family_frozen=True only when both passes are byte-identical, produce a valid
    K=3 family, all hashes agree, and every source/config/independence/regression self-check passes."""
    self_checks = _run_self_checks(source_paths)
    run1 = _freeze_once(envelope_obj)
    run2 = _freeze_once(envelope_obj)
    identical = cjson.canonical_json_bytes(run1) == cjson.canonical_json_bytes(run2)

    payload = dict(run1)
    payload["authoritative_operation"] = True
    payload["replay_record"] = {
        "run1_sha256": cjson.payload_sha256(run1), "run2_sha256": cjson.payload_sha256(run2),
        "byte_identical": identical}
    # preserve identities that were safely assembled before any later-stage failure (item 5)
    if self_checks["valid"] and self_checks.get("config"):
        payload["local_source_identities"] = self_checks["config"]["identities"]
        payload["verifier_configuration_sha256"] = self_checks["config"]["verifier_configuration_sha256"]

    if not self_checks["valid"]:
        payload["family_frozen"] = False
        payload["family_manifest"] = None
        payload["failure_record"] = {"failure_code": self_checks["code"], "stage": self_checks["stage"],
                                     "ordered_failure_codes": [self_checks["code"]]}
        return _emit_result(payload)

    if not identical:
        payload["family_frozen"] = False
        payload["family_manifest"] = None
        payload["failure_record"] = {"failure_code": verifier.REPLAY_MISMATCH, "stage": "replay",
                                     "ordered_failure_codes": [verifier.REPLAY_MISMATCH]}
        return _emit_result(payload)

    if payload["verification_mode"] == "PRIMARY_CANDIDATE_N64" and payload.get("provisional_k3_valid") is True:
        manifest = _authoritative_manifest(payload, self_checks["config"], repository_commit_identity)
        payload["family_manifest"] = manifest
        payload["family_frozen"] = True
        payload["failure_record"] = None
    else:
        payload["family_frozen"] = False
        payload["family_manifest"] = None
        # failure_record from the single pass (FAMILY_NOT_FREEZABLE / family_verification / stream) is retained
    return cjson.envelope("freeze_result", payload)


def _authoritative_manifest(payload: dict, config: dict, repository_commit_identity: str) -> Dict[str, object]:
    identities = config["identities"]
    serializer_config = serializer_configuration()
    freeze_config = freeze_configuration()
    manifest_payload = {
        "schema_name": FAMILY_MANIFEST_SCHEMA, "schema_version": "0.1",
        "verification_mode": payload["verification_mode"], "N": payload["N"], "K": K_FAMILY,
        "candidate_stream_sha256": payload["candidate_stream_sha256"],
        "generator_identity_hash": payload["generator_identity_hash"],
        "generator_configuration_hash": payload["generator_configuration_hash"],
        "budget_identity_hash": payload["budget_identity_hash"],
        "repository_commit_identity": repository_commit_identity,
        "verifier_source_path": identities["verifier_source_path"],
        "verifier_source_sha256": identities["verifier_source_sha256"],
        "verifier_configuration_payload": config["verifier_configuration_payload"],
        "verifier_configuration_sha256": config["verifier_configuration_sha256"],
        "serializer_source_path": identities["serializer_source_path"],
        "serializer_source_sha256": identities["serializer_source_sha256"],
        "serializer_configuration_payload": serializer_config,
        "serializer_configuration_sha256": cjson.payload_sha256(serializer_config),
        "freeze_source_path": identities["freeze_source_path"],
        "freeze_source_sha256": identities["freeze_source_sha256"],
        "freeze_configuration_payload": freeze_config,
        "freeze_configuration_sha256": cjson.payload_sha256(freeze_config),
        "verification_terminal_stream_status": payload["terminal_stream_status"],
        "accepted_candidate_indices": payload["accepted_candidate_indices"],
        "accepted_pair_certificate_envelopes": payload["accepted_pair_certificate_envelopes"],
        "family_certificate_envelope": payload["family_certificate"],
        "candidate_decision_ledger_sha256": payload["candidate_decision_ledger_sha256"],
        "accepted_pair_records": [{
            "pair_verifier_certificate_sha256": cjson.payload_sha256(env["pair_verifier_certificate"]),
            "accepted_order_index": order,
            "raw_AB_naming": _raw_ab_naming(env["pair_verifier_certificate"]),
        } for order, env in enumerate(payload["accepted_pair_certificate_envelopes"])],
        "resource_policy_status": RESOURCE_POLICY_STATUS,
    }
    return cjson.envelope("family_manifest", manifest_payload)


# ------------------------------------------------------------------ replay diagnostics / identity checks
def compare_freeze_results(result_a: dict, result_b: dict) -> bool:
    return cjson.canonical_json_bytes(result_a) == cjson.canonical_json_bytes(result_b)


def verify_manifest_identity(manifest_envelope: dict) -> Tuple[bool, Optional[str]]:
    """Recompute the nonrecursive manifest hash from the payload; tampering -> HASH_IDENTITY_FAILURE."""
    if not isinstance(manifest_envelope, dict) or "family_manifest" not in manifest_envelope \
            or "family_manifest_sha256" not in manifest_envelope:
        return False, verifier.HASH_IDENTITY_FAILURE
    return verifier.verify_supplied_hash(manifest_envelope["family_manifest"],
                                         manifest_envelope["family_manifest_sha256"])
