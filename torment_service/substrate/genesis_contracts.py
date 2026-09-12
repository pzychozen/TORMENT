"""Inert Native Genesis I1 contracts; no owner or runtime integration.

The operation record is deterministic administrative/recovery evidence, never
deployment, membership, or external identity authority. It owns unfinished
intent, generated-once allocations, and observations; committed IDs/results are
only references to their native owners. Ordinary native startup after activation
does not require this record. Administrative phases cannot supersede native
selector/core/completion agreement.

Payload values below store validated canonical JSON internally. This makes even
nested declarations immutable, while payload() returns a detached JSON object.
No decoder consults application defaults, normalizes IDs, or observes a root.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
import json
import math
from typing import ClassVar, Mapping, TYPE_CHECKING

from ..pathing import validate_portable_new_identifier
from .errors import DeploymentAuthorityError
from .ids import native_id_from_text

if TYPE_CHECKING:
    from .deployment_types import NativeGenesisCompletionWitness


GENESIS_MARKER_CREATED_DURING_G0 = False
GENESIS_MARKER_AND_SELECTOR_INITIALIZATION_ADJACENT = True
GENESIS_OPERATION_RECORD_IS_DEPLOYMENT_AUTHORITY = False
GENESIS_OPERATION_RECORD_IS_MEMBERSHIP_AUTHORITY = False
GENESIS_OPERATION_RECORD_IS_EXTERNAL_IDENTITY_AUTHORITY = False
GENESIS_OPERATION_RECORD_IS_RECOVERY_EVIDENCE = True
COMPLETED_NATIVE_SEED_RESULT_RECOVERY_WITHOUT_EMBEDDING = True
CRYPTOGRAPHIC_HUMAN_OPERATOR_IDENTITY_REQUIRED = False
OPERATOR_ATTESTATION_REQUIRED = True
PRE_INTENT_LOCK_RESIDUE_IS_AUTHORITY = False
MAX_OPERATION_KEY_LENGTH = 160


class GenesisContractError(DeploymentAuthorityError):
    """Unsupported or contradictory pure Genesis evidence."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GenesisContractError(message)


def exact_object(value: object, keys: str, label: str) -> dict:
    require(isinstance(value, Mapping), f"{label} must be an object")
    require(set(value) == set(keys.split()), f"{label} has missing or unsupported fields")
    return dict(value)


def text(value: object, label: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value), f"{label} has control characters")
    return value


def operation_key(value: object) -> str:
    value = text(value, "operation_key")
    require(len(value) <= MAX_OPERATION_KEY_LENGTH, "operation_key is too long")
    return value


def logical_id(value: object, label: str) -> str:
    text(value, label)
    try:
        return validate_portable_new_identifier(value, label)
    except ValueError as exc:
        raise GenesisContractError(str(exc)) from exc


def positive_int(value: object, label: str, *, minimum: int = 1) -> int:
    require(type(value) is int and value >= minimum, f"{label} must be an integer >= {minimum}")
    return value


def number(value: object, label: str) -> None:
    require(type(value) in (int, float), f"{label} must be numeric")
    require(type(value) is int or math.isfinite(value), f"{label} must be finite")


def uuid_text(value: object, label: str) -> str:
    require(isinstance(value, str), f"{label} must be canonical UUIDv4 text")
    try:
        parsed = native_id_from_text(value)
    except Exception as exc:
        raise GenesisContractError(f"{label} must be canonical UUIDv4 text") from exc
    require(str(parsed) == value, f"{label} must retain canonical UUIDv4 spelling")
    return value


def digest(value: object, label: str) -> str:
    # Local imports keep deployment_types free to compose the pure contracts.
    from .deployment_types import require_digest
    return require_digest(value, label)


def payload_digest(value: Mapping) -> str:
    from .deployment_types import digest_mapping
    _json_value(value)
    return digest_mapping(value)


def _json_value(value: object, ancestors: frozenset[int] = frozenset()) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        require(math.isfinite(value), "JSON numbers must be finite")
        return
    require(isinstance(value, (Mapping, list)), "only JSON objects, arrays, and scalars are accepted")
    require(id(value) not in ancestors, "cyclic JSON is forbidden")
    ancestors = ancestors | {id(value)}
    if isinstance(value, Mapping):
        require(all(type(k) is str for k in value), "JSON object keys must be strings")
        values = value.values()
    else:
        values = value
    for item in values:
        _json_value(item, ancestors)


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    require(len({key for key, _ in pairs}) == len(pairs), "duplicate JSON object keys")
    return dict(pairs)


@dataclass(frozen=True)
class GenesisPayload:
    """Immutable, schema-checked value, constructible from JSON or a payload.

    Subclasses exhaustively validate their allowed fields. This is not an
    extension bag: missing defaults and unknown output/runtime fields refuse.
    """

    _canonical_payload: str
    KEYS: ClassVar[str]

    def __post_init__(self) -> None:
        require(type(self._canonical_payload) is str, "canonical payload must be JSON text")
        try:
            value = json.loads(self._canonical_payload, object_pairs_hook=_unique_object)
        except (ValueError, TypeError, RecursionError) as exc:
            raise GenesisContractError("malformed Genesis JSON") from exc
        _json_value(value)
        self.validate(exact_object(value, self.KEYS, type(self).__name__))
        from .deployment_types import canonical_json
        object.__setattr__(self, "_canonical_payload", canonical_json(value))

    @classmethod
    def from_payload(cls, value: object):
        _json_value(value)
        try:
            return cls(json.dumps(value, ensure_ascii=True, allow_nan=False))
        except (ValueError, TypeError, RecursionError) as exc:
            raise GenesisContractError("malformed Genesis payload") from exc

    @classmethod
    def validate(cls, value: dict) -> None:
        raise NotImplementedError

    def payload(self) -> dict:
        return json.loads(self._canonical_payload)

    @property
    def digest(self) -> str:
        return payload_digest(self.payload())


class GenesisRepresentationLane(GenesisPayload):
    KEYS = "provider model dimension representation_class generation derivation_contract_version encoding_id dtype"

    @classmethod
    def validate(cls, value: dict) -> None:
        text(value["provider"], "provider")
        text(value["model"], "model")
        positive_int(value["dimension"], "dimension")
        positive_int(value["generation"], "generation")
        require(all(value[k] == v for k, v in {
            "representation_class": "COMPAT_EMBEDDING", "generation": 1,
            "derivation_contract_version": "compat-embedding-v1",
            "encoding_id": "RAW_VECTOR", "dtype": "float32",
        }.items()), "only the current qualified representation lane is supported")


SCOPE_PLAN_UUID_FIELDS = (
    "legacy_source_namespace_id", "target_identity_namespace_id", "target_semantic_scope_id",
    "motif_alias_namespace_id", "motif_identity_namespace_id",
    "membership_identity_namespace_id", "idempotency_namespace_id",
)


def scope_identity(value: object) -> tuple[str, str, str]:
    key = exact_object(value, "workspace_id scope_kind agent_id domain_id", "scope_key")
    workspace = logical_id(key["workspace_id"], "workspace_id")
    require(key["scope_kind"] in ("PRIVATE", "SHARED"), "unsupported scope kind")
    field, other = ("agent_id", "domain_id") if key["scope_kind"] == "PRIVATE" else ("domain_id", "agent_id")
    require(key[other] is None, "scope qualifier conflicts with scope kind")
    return workspace, key["scope_kind"], logical_id(key[field], field)


class GenesisRuntimePlan(GenesisPayload):
    """Source-free routing facts in the existing canonical scope-plan shape.

    legacy_source_namespace_id is the existing numeric EID alias namespace
    field, allocated fresh here; it does not claim a legacy source observation.
    """

    KEYS = "scope_key scope_plan representation_lane"

    @classmethod
    def validate(cls, value: dict) -> None:
        workspace, kind, qualifier = scope_identity(value["scope_key"])
        plan = exact_object(value["scope_plan"], " ".join(SCOPE_PLAN_UUID_FIELDS) +
                            " workspace_id scope_kind qualifier motif_domain_id", "scope_plan")
        for name in SCOPE_PLAN_UUID_FIELDS:
            uuid_text(plan[name], name)
        require(plan["workspace_id"] == workspace and plan["qualifier"] == qualifier and
                plan["scope_kind"] == {"PRIVATE": "PRIVATE_AGENT", "SHARED": "SHARED_DOMAIN"}[kind],
                "scope plan identity disagrees with scope key")
        logical_id(plan["motif_domain_id"], "motif_domain_id")
        GenesisRepresentationLane.from_payload(value["representation_lane"])

    @property
    def canonical_key(self) -> tuple[str, str, str]:
        return scope_identity(self.payload()["scope_key"])


def ordered_runtime_plans(values: object) -> tuple[GenesisRuntimePlan, ...]:
    require(isinstance(values, list) and bool(values), "runtime plans must be a nonempty array")
    plans = tuple(GenesisRuntimePlan.from_payload(value) for value in values)
    require(len({p.canonical_key for p in plans}) == len(plans), "duplicate runtime scope")
    ordered = tuple(sorted(plans, key=lambda p: p.canonical_key))
    require(plans == ordered, "runtime plans must use canonical scope ordering")
    return plans


def runtime_plan_digest(plans: tuple[GenesisRuntimePlan, ...]) -> str:
    return payload_digest({"runtime_scope_plans": [p.payload() for p in sorted(plans, key=lambda p: p.canonical_key)]})


CHARACTER_DEFINITION_KEYS = (
    "seed_id character_name seed_text owner_agent_id drift_window_steps "
    "drift_correction_threshold drift_gravity_strength core_half_life relational_half_life "
    "situational_half_life core_weight derived_weight relational_weight situational_weight version"
)
IDENTITY_SEED_KEYS = "core_traits priority_weights coupling_mode coupling_strength seed_text seed_id"
INITIAL_OVERLAY_KEYS = (
    "write_threshold decay_scale promotion_bias novelty_bias motif_sensitivity "
    "contradiction_sensitivity reinforcement_gain coupling_strength shared_trust stability_guard"
)


class GenesisIntent(GenesisPayload):
    """Expanded declaration; initial_overlay is immutable creation input only.

    Current/mutating overlays never enter completion owner projections. Namespace
    keys and IDs, profile object ID, and timestamps are generated once by a later
    caller and supplied here; no defaults or UUIDs are generated by this type.
    """

    CONTRACT = "TORMENT_NATIVE_GENESIS_INTENT"
    VERSION = 1
    ORIGIN = "NATIVE_GENESIS"
    KEYS = ("contract version origin operation_key data_root_identity workspace agent character "
            "profile_choice representation_lane allocations creation_facts")

    @classmethod
    def validate(cls, value: dict) -> None:
        require(value["contract"] == cls.CONTRACT and type(value["version"]) is int and
                value["version"] == cls.VERSION and value["origin"] == cls.ORIGIN,
                "unsupported Genesis intent discriminator")
        operation_key(value["operation_key"])
        text(value["data_root_identity"], "data_root_identity")
        workspace = exact_object(value["workspace"], "workspace_id ordered_domains", "workspace")
        workspace_id = logical_id(workspace["workspace_id"], "workspace_id")
        domains = workspace["ordered_domains"]
        require(isinstance(domains, list) and bool(domains), "ordered_domains must be nonempty")
        for domain in domains:
            logical_id(domain, "domain_id")
        require(len(set(domains)) == len(domains), "duplicate domain declaration")
        agent = exact_object(value["agent"], "agent_id identity_seed initial_overlay private_motif_domain_id", "agent")
        agent_id = logical_id(agent["agent_id"], "agent_id")
        require(agent["private_motif_domain_id"] in domains, "private motif domain is undeclared")
        character = value["character"]
        require(isinstance(character, dict), "character must be an object")
        enabled = character.get("mode") == "ENABLED"
        exact_object(character, "mode definition" if enabled else "mode", "character")
        require(character["mode"] in ("ENABLED", "DISABLED"), "unsupported Character mode")
        seed = exact_object(agent["identity_seed"], IDENTITY_SEED_KEYS + (" character_name" if enabled else ""), "identity_seed")
        require(isinstance(seed["core_traits"], list), "core_traits must be an array")
        for trait in seed["core_traits"]:
            text(trait, "core trait")
        require(isinstance(seed["priority_weights"], dict), "priority_weights must be an object")
        for key, weight in seed["priority_weights"].items():
            text(key, "priority key")
            number(weight, "priority weight")
        text(seed["coupling_mode"], "coupling_mode")
        number(seed["coupling_strength"], "coupling_strength")
        overlay = exact_object(agent["initial_overlay"], INITIAL_OVERLAY_KEYS, "initial_overlay")
        for key, entry in overlay.items():
            number(entry, key)
        if enabled:
            definition = exact_object(character["definition"], CHARACTER_DEFINITION_KEYS, "Character definition")
            logical_id(definition["seed_id"], "seed_id")
            for key in ("character_name", "seed_text", "version"):
                text(definition[key], key)
            require(definition["owner_agent_id"] == agent_id, "Character owner disagrees with agent")
            positive_int(definition["drift_window_steps"], "drift_window_steps")
            for key in CHARACTER_DEFINITION_KEYS.split()[5:-1]:
                number(definition[key], key)
            for key in ("seed_id", "seed_text", "character_name"):
                require(seed[key] == definition[key], "Character definition disagrees with identity seed")
        else:
            require(seed["seed_id"] == "" and seed["seed_text"] == "", "disabled Character contains seed facts")
        profile = exact_object(value["profile_choice"], "compression_enabled deep_memory_enabled representation_provider representation_model representation_dimension", "profile_choice")
        require(profile["compression_enabled"] is False and profile["deep_memory_enabled"] is False,
                "Genesis requires compression and deep memory disabled")
        lane = GenesisRepresentationLane.from_payload(value["representation_lane"]).payload()
        for profile_key, lane_key in (("representation_provider", "provider"), ("representation_model", "model"), ("representation_dimension", "dimension")):
            require(type(profile[profile_key]) is type(lane[lane_key]) and profile[profile_key] == lane[lane_key], "profile choice and lane disagree")
        allocations = exact_object(value["allocations"], "core_id core_relative_path root_profile_generation root_profile_object_id root_profile_semantic_scope_id root_profile_identity_namespace_id root_profile_idempotency_namespace_id namespace_keys runtime_scope_plans", "allocations")
        from .deployment_types import require_relative_core_path
        require_relative_core_path(allocations["core_relative_path"])
        logical_id(allocations["core_relative_path"], "core_relative_path")
        for key in ("core_id", "root_profile_object_id", "root_profile_semantic_scope_id", "root_profile_identity_namespace_id", "root_profile_idempotency_namespace_id"):
            uuid_text(allocations[key], key)
        require(type(allocations["root_profile_generation"]) is int and allocations["root_profile_generation"] == 1,
                "initial profile generation must be one")
        plans = ordered_runtime_plans(allocations["runtime_scope_plans"])
        expected = {(workspace_id, "PRIVATE", agent_id)} | {(workspace_id, "SHARED", d) for d in domains}
        require({p.canonical_key for p in plans} == expected, "routing plans do not cover the declared bundle")
        allocated_ids = [allocations[key] for key in ("core_id", "root_profile_object_id", "root_profile_semantic_scope_id", "root_profile_identity_namespace_id", "root_profile_idempotency_namespace_id")]
        namespace_ids = {allocations["root_profile_identity_namespace_id"], allocations["root_profile_idempotency_namespace_id"]}
        for plan in plans:
            entry = plan.payload()
            require(entry["representation_lane"] == lane, "routing lane differs from intent")
            scope = entry["scope_plan"]
            expected_motif = agent["private_motif_domain_id"] if plan.canonical_key[1] == "PRIVATE" else plan.canonical_key[2]
            require(scope["motif_domain_id"] == expected_motif, "routing motif domain differs from intent")
            allocated_ids.extend(scope[key] for key in SCOPE_PLAN_UUID_FIELDS)
            namespace_ids.update(scope[key] for key in SCOPE_PLAN_UUID_FIELDS if key != "target_semantic_scope_id")
        require(len(set(allocated_ids)) == len(allocated_ids), "generated-once allocation IDs collide")
        namespace_keys = allocations["namespace_keys"]
        require(isinstance(namespace_keys, dict) and set(namespace_keys) == namespace_ids,
                "namespace keys must cover exactly the allocated namespaces")
        for key in namespace_keys.values():
            text(key, "namespace_key")
        require(len(set(namespace_keys.values())) == len(namespace_keys), "namespace keys collide")
        creation = exact_object(value["creation_facts"], "workspace_created_ts identity_created_ts character_created_ts", "creation_facts")
        for key in ("workspace_created_ts", "identity_created_ts"):
            positive_int(creation[key], key, minimum=0)
        if enabled:
            positive_int(creation["character_created_ts"], "character_created_ts", minimum=0)
        else:
            require(creation["character_created_ts"] is None, "disabled Character has a creation timestamp")

    @property
    def operation_key(self) -> str:
        return self.payload()["operation_key"]

    @property
    def data_root_identity(self) -> str:
        return self.payload()["data_root_identity"]

    @property
    def runtime_plans(self) -> tuple[GenesisRuntimePlan, ...]:
        return ordered_runtime_plans(self.payload()["allocations"]["runtime_scope_plans"])

    def external_owner_projection(self) -> dict:
        """Stable creation witness, excluding overlays, role and Character drift."""
        value = self.payload()
        workspace, agent, created = value["workspace"], value["agent"], value["creation_facts"]
        character = dict(value["character"])
        if character["mode"] == "ENABLED":
            character["created_ts"] = created["character_created_ts"]
        return {
            "workspace": {**workspace, "created_ts": created["workspace_created_ts"]},
            "identity": {"workspace_id": workspace["workspace_id"], "agent_id": agent["agent_id"],
                         "seed": agent["identity_seed"], "created_ts": created["identity_created_ts"]},
            "character": character,
        }


class GenesisStartKind(str, Enum):
    ABSENT_ROOT = "ABSENT_ROOT"
    EMPTY_ROOT = "EMPTY_ROOT"
    ALLOWED_NON_AUTHORITATIVE_ROOT_FILES = "ALLOWED_NON_AUTHORITATIVE_ROOT_FILES"
    PRE_INTENT_GENESIS_CONTROL_RESIDUE = "PRE_INTENT_GENESIS_CONTROL_RESIDUE"
    MATCHING_GENESIS_RECOVERY_STATE = "MATCHING_GENESIS_RECOVERY_STATE"


class GenesisAcceptedStart(GenesisPayload):
    KEYS = "classification data_root_identity observed_at_ns observed_entries matching_operation_key"
    CONTROL_ENTRIES = (".", "substrate", "substrate/deployment", "substrate/deployment/root-onboarding.lock")
    ALLOWED_FILES = frozenset({"README.md", ".gitkeep"})

    @classmethod
    def validate(cls, value: dict) -> None:
        try:
            kind = GenesisStartKind(value["classification"])
        except (TypeError, ValueError) as exc:
            raise GenesisContractError("unsupported accepted-start classification") from exc
        text(value["data_root_identity"], "data_root_identity")
        positive_int(value["observed_at_ns"], "observed_at_ns", minimum=0)
        entries = value["observed_entries"]
        require(isinstance(entries, list) and all(type(e) is str for e in entries), "observed_entries must be text array")
        require(len(set(entries)) == len(entries), "duplicate observed entries")
        if kind is GenesisStartKind.MATCHING_GENESIS_RECOVERY_STATE:
            operation_key(value["matching_operation_key"])
            require(not entries, "recovery state uses the matching record, not an inferred file inventory")
        else:
            require(value["matching_operation_key"] is None, "non-recovery start cannot claim an operation")
            if kind in (GenesisStartKind.ABSENT_ROOT, GenesisStartKind.EMPTY_ROOT):
                require(not entries, "absent/empty root cannot contain entries")
            elif kind is GenesisStartKind.ALLOWED_NON_AUTHORITATIVE_ROOT_FILES:
                require(bool(entries) and set(entries) <= cls.ALLOWED_FILES, "unsupported root-only file")
            else:
                controls = [e for e in entries if e not in cls.ALLOWED_FILES]
                files = [e for e in entries if e in cls.ALLOWED_FILES]
                require(bool(controls) and tuple(controls) == cls.CONTROL_ENTRIES[:len(controls)]
                        and entries == controls + sorted(files),
                        "pre-intent residue must be the fixed control prefix plus allowed root files")

    def require_intent(self, intent: GenesisIntent) -> None:
        value = self.payload()
        require(value["data_root_identity"] == intent.data_root_identity, "accepted start names another root")
        if value["matching_operation_key"] is not None:
            require(value["matching_operation_key"] == intent.operation_key, "accepted start names another operation")


class GenesisAdministrativePhase(str, Enum):
    PREPARING = "PREPARING"
    PREPARATION_SEALED = "PREPARATION_SEALED"
    CORE_ACTIVATED = "CORE_ACTIVATED"
    COMPLETED = "COMPLETED"


class GenesisExternalOwnerProjection(GenesisPayload):
    """Stable external creation facts; completion binds these to its full intent."""

    KEYS = "workspace identity character"

    @classmethod
    def validate(cls, value: dict) -> None:
        exact_object(value["workspace"], "workspace_id ordered_domains created_ts", "workspace witness")
        exact_object(value["identity"], "workspace_id agent_id seed created_ts", "identity witness")
        character = value["character"]
        require(isinstance(character, Mapping), "Character witness must be an object")
        require(character.get("mode") in ("ENABLED", "DISABLED"), "unsupported Character witness mode")
        exact_object(character, "mode definition created_ts" if character["mode"] == "ENABLED" else "mode", "Character witness")


class GenesisRootProfileReference(GenesisPayload):
    KEYS = "core_id profile_generation profile_object_id profile_revision_id profile_revision_ordinal profile_semantic_scope_id"

    @classmethod
    def validate(cls, value: dict) -> None:
        for key in ("core_id", "profile_object_id", "profile_revision_id", "profile_semantic_scope_id"):
            uuid_text(value[key], key)
        positive_int(value["profile_generation"], "profile_generation")
        positive_int(value["profile_revision_ordinal"], "profile_revision_ordinal")


class GenesisMembershipReference(GenesisPayload):
    """Initial ACTIVE relationship/revision and its existing external witness."""

    KEYS = "scope_key relationship_id relationship_revision_id relationship_revision_ordinal lifecycle membership_witness"

    @classmethod
    def validate(cls, value: dict) -> None:
        scope_identity(value["scope_key"])
        for key in ("relationship_id", "relationship_revision_id"):
            uuid_text(value[key], key)
        positive_int(value["relationship_revision_ordinal"], "relationship_revision_ordinal")
        require(value["lifecycle"] == "ACTIVE", "initial membership must be ACTIVE")
        witness = exact_object(value["membership_witness"], "witness_id witness_digest issuer_reference provenance_kind", "membership witness")
        for key in ("witness_id", "issuer_reference"):
            text(witness[key], key)
        digest(witness["witness_digest"], "witness_digest")
        require(witness["provenance_kind"] in ("EXTERNAL_ISSUED", "QUALIFICATION_TEST"), "unsupported existing membership provenance")

    @property
    def canonical_key(self) -> tuple[str, str, str]:
        return scope_identity(self.payload()["scope_key"])


def initial_membership_closure_digest(
    profile: GenesisRootProfileReference,
    plans: tuple[GenesisRuntimePlan, ...],
    members: tuple[GenesisMembershipReference, ...],
) -> str:
    """Existing root-membership closure projection, without querying an owner."""
    plans_by_key = {p.canonical_key: p.payload()["scope_plan"] for p in plans}
    require(len(plans_by_key) == len(plans), "duplicate routing plan")
    require(len({m.canonical_key for m in members}) == len(members) and
            {m.canonical_key for m in members} == set(plans_by_key), "membership closure does not cover routing plans")
    projected = []
    for member in sorted(members, key=lambda m: m.canonical_key):
        value = member.payload()
        plan = plans_by_key[member.canonical_key]
        projected.append({
            "scope_key": value["scope_key"], "semantic_scope_id": plan["target_semantic_scope_id"],
            "identity_namespace_id": plan["target_identity_namespace_id"],
            "legacy_source_namespace_id": plan["legacy_source_namespace_id"],
            "membership_revision_id": value["relationship_revision_id"],
            "membership_revision_ordinal": value["relationship_revision_ordinal"],
            "membership_witness": value["membership_witness"],
        })
    ref = profile.payload()
    return payload_digest({"profile": {"core_id": ref["core_id"], "profile_generation": ref["profile_generation"]}, "members": projected})


class GenesisSeedCompletion(GenesisPayload):
    """Disabled evidence or a reference to an already-completed native result.

    definition_digest hashes the complete stable Genesis definition. It is not
    a migrated CharacterSeedWitness. Result references are validated by the
    native owner later; this value neither plants nor re-embeds a seed.
    """

    # The two alternatives have exact disjoint schemas.
    KEYS = "mode"

    @classmethod
    def from_payload(cls, value: object):
        require(isinstance(value, Mapping), "seed completion must be an object")
        if value.get("mode") == "ENABLED":
            return GenesisCompletedSeed.from_payload(value)
        return super().from_payload(value)

    @classmethod
    def validate(cls, value: dict) -> None:
        require(value["mode"] == "DISABLED", "disabled seed evidence must contain mode only")


class GenesisCompletedSeed(GenesisSeedCompletion):
    KEYS = "mode status definition_digest source_operation_key source_intent_digest result_digest seed_eids seed_motif_id representation_ids"

    @classmethod
    def from_payload(cls, value: object):
        return GenesisPayload.from_payload.__func__(cls, value)

    @classmethod
    def validate(cls, value: dict) -> None:
        require(value["mode"] == "ENABLED" and value["status"] == "COMPLETED", "seed must be natively completed")
        for key in ("definition_digest", "source_intent_digest", "result_digest"):
            digest(value[key], key)
        operation_key(value["source_operation_key"])
        text(value["seed_motif_id"], "seed_motif_id")
        for key in ("seed_eids", "representation_ids"):
            entries = value[key]
            require(isinstance(entries, list) and bool(entries), f"{key} must be nonempty")
            for entry in entries:
                if key == "seed_eids":
                    positive_int(entry, key, minimum=0)
                else:
                    uuid_text(entry, key)
            require(len(set(entries)) == len(entries), f"duplicate {key}")


class GenesisEvidenceReference(GenesisPayload):
    """Opaque reference to evidence owned elsewhere, not a native authority."""

    KEYS = "owner operation_key result_digest"

    @classmethod
    def validate(cls, value: dict) -> None:
        text(value["owner"], "owner")
        operation_key(value["operation_key"])
        digest(value["result_digest"], "result_digest")


class GenesisQuiescenceObservation(GenesisPayload):
    """Administrative snapshot only; fresh completion retains its digest only.

    Process/listener detail is opaque finite JSON from the later observer. The
    typed envelope binds time, root, operation and existing free-text attestation.
    No process status or human identity is verified by this data contract.
    """

    KEYS = "data_root_identity operation_key observed_at_ns operator_attestation issuer_reference observations"

    @classmethod
    def validate(cls, value: dict) -> None:
        text(value["data_root_identity"], "data_root_identity")
        operation_key(value["operation_key"])
        positive_int(value["observed_at_ns"], "observed_at_ns", minimum=0)
        text(value["operator_attestation"], "operator_attestation")
        text(value["issuer_reference"], "issuer_reference")
        require(isinstance(value["observations"], dict) and bool(value["observations"]), "quiescence observations must be nonempty")


@dataclass(frozen=True)
class GenesisOperationRecord:
    """Recovery evidence only; never deployment/membership/external identity authority.

    Before sealing, later native outputs are absent. Sealing owns a completion
    cache until core activation. After activation receipts/completion are only
    references/caches; stale PREPARING does not defeat valid native agreement.
    Ordinary activated startup does not require this administrative record.
    """

    expanded_intent: GenesisIntent
    intent_digest: str
    accepted_start_observation: GenesisAcceptedStart
    administrative_phase: GenesisAdministrativePhase
    phase_revision: int
    child_operation_references: tuple[GenesisEvidenceReference, ...]
    quiescence_observations: tuple[GenesisQuiescenceObservation, ...]
    sealed_completion_payload: NativeGenesisCompletionWitness | None
    final_activation_references: tuple[GenesisEvidenceReference, ...]

    CONTRACT = "TORMENT_NATIVE_GENESIS_OPERATION_RECORD"
    VERSION = 1

    def __post_init__(self) -> None:
        require(isinstance(self.expanded_intent, GenesisIntent), "record requires typed intent")
        require(self.intent_digest == self.expanded_intent.digest, "record intent digest mismatch")
        require(isinstance(self.accepted_start_observation, GenesisAcceptedStart), "record requires accepted start")
        self.accepted_start_observation.require_intent(self.expanded_intent)
        require(isinstance(self.administrative_phase, GenesisAdministrativePhase), "record requires a known administrative phase")
        positive_int(self.phase_revision, "phase_revision")
        for name, cls in (("child_operation_references", GenesisEvidenceReference),
                          ("quiescence_observations", GenesisQuiescenceObservation),
                          ("final_activation_references", GenesisEvidenceReference)):
            values = getattr(self, name)
            require(type(values) is tuple and all(isinstance(v, cls) for v in values), f"{name} must be a typed tuple")
            require(len({v.digest for v in values}) == len(values), f"duplicate {name}")
            if cls is GenesisEvidenceReference:
                require(len({(v.payload()["owner"], v.payload()["operation_key"]) for v in values}) == len(values),
                        f"conflicting operation identities in {name}")
        for observation in self.quiescence_observations:
            value = observation.payload()
            require(value["data_root_identity"] == self.expanded_intent.data_root_identity and
                    value["operation_key"] == self.expanded_intent.operation_key, "quiescence observation identity mismatch")
        early = self.administrative_phase is GenesisAdministrativePhase.PREPARING
        if early:
            require(self.sealed_completion_payload is None and not self.final_activation_references,
                    "preparing record cannot contain sealed or activation outputs")
        else:
            from .deployment_types import NativeGenesisCompletionWitness
            completion = self.sealed_completion_payload
            activated = self.administrative_phase in (GenesisAdministrativePhase.CORE_ACTIVATED, GenesisAdministrativePhase.COMPLETED)
            require(bool(self.final_activation_references) == activated, "activation references disagree with administrative phase")
            require(activated or completion is not None, "sealed phase requires fresh completion")
            # A post-activation cache is optional: the committed native owner,
            # not this record, owns completion evidence after core activation.
            if completion is not None:
                require(isinstance(completion, NativeGenesisCompletionWitness), "completion cache must be fresh evidence")
                require(completion.expanded_intent == self.expanded_intent and
                        completion.accepted_start_observation == self.accepted_start_observation,
                        "sealed completion disagrees with record")
                require(bool(self.quiescence_observations) and completion.quiescence_evidence_digest ==
                        payload_digest({"quiescence_observations": [v.payload() for v in self.quiescence_observations]}),
                        "sealed completion quiescence binding mismatch")

    def payload(self) -> dict:
        return {
            "contract": self.CONTRACT, "version": self.VERSION,
            "expanded_intent": self.expanded_intent.payload(), "intent_digest": self.intent_digest,
            "accepted_start_observation": self.accepted_start_observation.payload(),
            "administrative_phase": self.administrative_phase.value, "phase_revision": self.phase_revision,
            "child_operation_references": [v.payload() for v in self.child_operation_references],
            "quiescence_observations": [v.payload() for v in self.quiescence_observations],
            "sealed_completion_payload": None if self.sealed_completion_payload is None else self.sealed_completion_payload.payload(),
            "final_activation_references": [v.payload() for v in self.final_activation_references],
        }

    @property
    def digest(self) -> str:
        return payload_digest(self.payload())

    @classmethod
    def from_payload(cls, value: object) -> GenesisOperationRecord:
        _json_value(value)
        value = exact_object(value, "contract version " + " ".join(f.name for f in fields(cls)), "Genesis operation record")
        require(value["contract"] == cls.CONTRACT and type(value["version"]) is int and value["version"] == cls.VERSION,
                "unsupported Genesis operation record discriminator")
        from .deployment_types import completion_witness_from_payload
        try:
            for name in ("child_operation_references", "quiescence_observations", "final_activation_references"):
                require(isinstance(value[name], list), f"{name} must be an array")
            return cls(
                GenesisIntent.from_payload(value["expanded_intent"]), value["intent_digest"],
                GenesisAcceptedStart.from_payload(value["accepted_start_observation"]),
                GenesisAdministrativePhase(value["administrative_phase"]), value["phase_revision"],
                tuple(GenesisEvidenceReference.from_payload(v) for v in value["child_operation_references"]),
                tuple(GenesisQuiescenceObservation.from_payload(v) for v in value["quiescence_observations"]),
                None if value["sealed_completion_payload"] is None else completion_witness_from_payload(value["sealed_completion_payload"]),
                tuple(GenesisEvidenceReference.from_payload(v) for v in value["final_activation_references"]),
            )
        except (TypeError, ValueError) as exc:
            raise GenesisContractError("malformed Genesis operation record") from exc


class GenesisEvidenceStatus(str, Enum):
    ABSENT = "ABSENT"
    VALID = "VALID"
    INVALID = "INVALID"


class GenesisAuthorityDisposition(str, Enum):
    UNPUBLISHED = "UNPUBLISHED"
    NATIVE_ACTIVE_AGREEMENT = "NATIVE_ACTIVE_AGREEMENT"
    INVALID = "INVALID"


class GenesisFenceDisposition(str, Enum):
    ABSENT = "ABSENT"
    BLOCK_LEGACY = "BLOCK_LEGACY"
    NATIVE_AUTHORITY_WINS = "NATIVE_AUTHORITY_WINS"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class GenesisFenceFacts:
    """Caller-supplied observations, not paths/handles or a request to inspect.

    NATIVE_ACTIVE_AGREEMENT asserts the caller already verified selector/core
    and persisted completion binding. Merely observing a NATIVE_ACTIVE label
    is insufficient. Phase is deliberately not an input. Missing records impose
    no Genesis restriction; the existing resolver still handles other failures.
    """

    requested_data_root_identity: str
    record_status: GenesisEvidenceStatus
    record_data_root_identity: str | None
    record_operation_key: str | None
    authority_disposition: GenesisAuthorityDisposition
    fresh_completion_status: GenesisEvidenceStatus
    fresh_completion_data_root_identity: str | None
    fresh_completion_operation_key: str | None


def classify_genesis_fence(facts: GenesisFenceFacts) -> GenesisFenceDisposition:
    """Pure fail-closed classification; does not verify or publish authority."""
    conflict = GenesisFenceDisposition.CONFLICT
    if not isinstance(facts, GenesisFenceFacts):
        return conflict
    if not isinstance(facts.record_status, GenesisEvidenceStatus):
        return conflict
    if facts.record_status is GenesisEvidenceStatus.ABSENT:
        if facts.record_data_root_identity is not None or facts.record_operation_key is not None:
            return conflict
        return GenesisFenceDisposition.ABSENT
    if facts.record_status is GenesisEvidenceStatus.INVALID:
        return conflict
    try:
        text(facts.requested_data_root_identity, "requested root")
        text(facts.record_data_root_identity, "record root")
        operation_key(facts.record_operation_key)
    except GenesisContractError:
        return conflict
    if facts.record_data_root_identity != facts.requested_data_root_identity:
        return conflict
    if not isinstance(facts.authority_disposition, GenesisAuthorityDisposition) or facts.authority_disposition is GenesisAuthorityDisposition.INVALID:
        return conflict
    if not isinstance(facts.fresh_completion_status, GenesisEvidenceStatus) or facts.fresh_completion_status is GenesisEvidenceStatus.INVALID:
        return conflict
    if facts.fresh_completion_status is GenesisEvidenceStatus.ABSENT:
        if facts.fresh_completion_data_root_identity is not None or facts.fresh_completion_operation_key is not None:
            return conflict
        return GenesisFenceDisposition.BLOCK_LEGACY
    if (facts.fresh_completion_data_root_identity != facts.record_data_root_identity or
            facts.fresh_completion_operation_key != facts.record_operation_key):
        return conflict
    if facts.authority_disposition is GenesisAuthorityDisposition.NATIVE_ACTIVE_AGREEMENT:
        return GenesisFenceDisposition.NATIVE_AUTHORITY_WINS
    return GenesisFenceDisposition.BLOCK_LEGACY
