# torment_service/provenance_v1.py
"""
ProvenanceV1 — ingest-level lineage metadata for every stored memory.

First-pass schema (v2.4.x) per DOCTRINE_v2.4.x.md rule #5:
"Provenance is a hard boundary."

This is NOT the spine-level Provenance (schemas/provenance.py) which tracks
role outputs and derivation depth through the cognition pipeline.
ProvenanceV1 lives at the storage layer and answers:
  - where did this memory come from?
  - what path wrote it?
  - what memories did it derive from?
  - is this safe to write again?

See ROADMAP_v2.4.x.md §2.2 for design goals.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ── Enum constants ──────────────────────────────────────────────────

SOURCE_USER_INPUT   = "user_input"
SOURCE_ROLE_OUTPUT  = "role_output"
# NOTE: These are intentionally retained as schema states.
# They may be produced by future/interop flows even if current producers are limited.
SOURCE_DERIVED      = "derived"
SOURCE_MEMORY       = "memory"
SOURCE_TOOL_RESULT      = "tool_result"
SOURCE_COLLECTIVE_ECHO  = "collective_echo"

# Block A — baton as a cross-session attention-bounded intent. Origin class
# only; baton lifecycle state (owner, expires_when, resolution_condition,
# status) lives on the memory entity's extra_payload["baton_lifecycle"],
# not on ProvenanceV1. See docs/BLOCK_A_DESIGN.md §5.1.
SOURCE_BATON_INTENT = "baton_intent"

# Block B — reference memory origin. Records that a reference object was
# stored; the reference's source_link / source_kind live on ReferenceEntry
# (not on provenance), per docs/BLOCK_B_DESIGN.md §3 carry-forward caution
# (storage-vs-loading separation).
SOURCE_REFERENCE_INGEST = "reference_ingest"

# Block B — environment memory, three evidence classes per R+5
# (docs/PRE_BLOCK_B_PRECONDITIONS.md §3). Every environment write MUST
# declare exactly one. "inferred" additionally requires a ratified rule
# name validated at fabric level against
# environment_memory.VALID_INFERENCE_RULES (empty in v0.1).
SOURCE_ENVIRONMENT_USER_ASSERTED = "environment_user_asserted"
SOURCE_ENVIRONMENT_OBSERVED      = "environment_observed"
SOURCE_ENVIRONMENT_INFERRED      = "environment_inferred"

# Block C — closure synthesis origin classes. Each names an EVENT origin,
# not a lifecycle state. Lifecycle state is derived by literal event-kind
# lookup in ClosureLedger — provenance does NOT carry lifecycle state.
# See docs/BLOCK_C_DESIGN.md §5.1 + §7 (writeback-vs-closure structural
# separation — these source_types are distinct from the archivist/writeback
# origin classes; they never substitute SOURCE_ROLE_OUTPUT).
SOURCE_CLOSURE_COMMIT       = "closure_commit"
SOURCE_CLOSURE_RATIFICATION = "closure_ratification"
SOURCE_CLOSURE_REVISION     = "closure_revision"

# Storage sentinel for rows that fail the WRITE_MIGRATION gate-1 recovery
# predicate. NOT an admissible origin class — see
# ``torment_service/migration/constants.py::SOURCE_GATE1_UNRECOVERABLE``
# module docstring and ``docs/ADMISSION_POLICY_v2.4.x.md``. Registered here
# only so gate-1 FAIL rows can be stored in the uniform ProvenanceV1 schema
# (rather than left in a pre-migration shape). Live ingest paths MUST NEVER
# emit this value; only the WRITE_MIGRATION writer produces it. The
# bounded-DFS recursion guard rejects it at any depth via
# ``_REJECTED_SOURCE_TYPES_IN_WALK``.
SOURCE_GATE1_UNRECOVERABLE = "gate1_unrecoverable"

VALID_SOURCE_TYPES = frozenset({
    SOURCE_USER_INPUT,
    SOURCE_ROLE_OUTPUT,
    SOURCE_DERIVED,
    SOURCE_MEMORY,
    SOURCE_TOOL_RESULT,
    SOURCE_COLLECTIVE_ECHO,
    SOURCE_GATE1_UNRECOVERABLE,
    SOURCE_BATON_INTENT,                # Block A
    SOURCE_REFERENCE_INGEST,            # Block B — reference memory
    SOURCE_ENVIRONMENT_USER_ASSERTED,   # Block B — environment (user-asserted)
    SOURCE_ENVIRONMENT_OBSERVED,        # Block B — environment (observed)
    SOURCE_ENVIRONMENT_INFERRED,        # Block B — environment (inferred)
    SOURCE_CLOSURE_COMMIT,              # Block C — closure commit event
    SOURCE_CLOSURE_RATIFICATION,        # Block C — closure ratification event
    SOURCE_CLOSURE_REVISION,            # Block C — closure revision event
})

WRITE_DIRECT_INGEST       = "direct_ingest"
WRITE_COGNITION_WRITEBACK = "cognition_writeback"
# NOTE: Reserved write paths remain valid for forward compatibility and
# migration/import workflows. Do not remove without provenance migration plan.
WRITE_REFLECTION_WRITEBACK = "reflection_writeback"
WRITE_TOOL_INGEST         = "tool_ingest"
WRITE_MIGRATION           = "migration"
WRITE_SYSTEM_IMPORT       = "system_import"
WRITE_COLLECTIVE_REINGEST = "collective_reingest"

# Block C — closure commit/revision write path. STRUCTURALLY DISTINCT from
# WRITE_COGNITION_WRITEBACK and WRITE_REFLECTION_WRITEBACK per the
# writeback-vs-closure guardrail (docs/BLOCK_C_DESIGN.md §7.1). Closure
# commits are author-ratified arc syntheses, NOT archivist writeback
# products. The two must never share a write_path value.
WRITE_CLOSURE_COMMIT      = "closure_commit"

VALID_WRITE_PATHS = frozenset({
    WRITE_DIRECT_INGEST,
    WRITE_COGNITION_WRITEBACK,
    WRITE_REFLECTION_WRITEBACK,
    WRITE_TOOL_INGEST,
    WRITE_MIGRATION,
    WRITE_SYSTEM_IMPORT,
    WRITE_COLLECTIVE_REINGEST,
    WRITE_CLOSURE_COMMIT,               # Block C — closure commit / revision
})

SCHEMA_VERSION = "1.0"


# ── Dataclass ───────────────────────────────────────────────────────

@dataclass
class ProvenanceV1:
    """Ingest-level provenance for stored memories.

    Required fields (all have sensible defaults for plain user ingest):
        schema_version, source_type, source_role, write_path,
        parent_eids, created_at_step, created_at_ts

    Optional fields:
        tool_name, session_id, notes
    """

    schema_version: str = SCHEMA_VERSION
    source_type: str = SOURCE_USER_INPUT
    source_role: Optional[str] = None
    write_path: str = WRITE_DIRECT_INGEST
    parent_eids: List[int] = field(default_factory=list)
    created_at_step: Optional[int] = None
    created_at_ts: Optional[str] = None

    # Optional fields — cheap to support now
    tool_name: Optional[str] = None
    session_id: Optional[str] = None
    notes: Optional[str] = None

    # Block B — evidence-class-specific origin fields. Each maps to exactly
    # one of the three SOURCE_ENVIRONMENT_* values; factory methods populate
    # the appropriate field (the others stay None). These are origin/lineage
    # metadata, not runtime-behavior: they record WHO asserted or WHAT
    # probed or WHICH rule inferred, nothing more. See docs/BLOCK_B_DESIGN.md
    # §5.1.
    asserted_by: Optional[str] = None        # populated when source_type=user_asserted
    observation_source: Optional[str] = None  # populated when source_type=observed
    inference_rule: Optional[str] = None      # populated when source_type=inferred

    # ── WRITE_MIGRATION admission fields (v2.4.x step 6) ───────────
    #
    # These three fields record the gate-2 admission decision separately
    # from the source_type origin class, so that "what something is" and
    # "what we decided to do with it" remain cleanly separated.
    #
    # Default values (False / "" / "") encode the "no admission decision
    # on file" state that every live ingest path produces. Only the
    # WRITE_MIGRATION writer ever sets these to non-default values.
    #
    # ``admission_refused`` is the load-bearing flag: when True, the
    # recursion guard rejects the row at any depth with
    # REASON_MIGRATION_REFUSED, regardless of source_type or source_role.
    # ``admission_reason`` names the specific gate-2 rule that fired
    # (one of ``migration.constants.ADMISSION_REASONS``).
    # ``admission_policy_version`` records the doctrine revision the
    # decision was made under, enabling the monotonic-in-tightness
    # re-run policy to detect stale decisions and re-evaluate them.
    #
    # See ``docs/ADMISSION_POLICY_v2.4.x.md`` and
    # ``docs/WRITE_MIGRATION_FRAMING_v2.4.x.md`` Decision 1.
    admission_refused: bool = False
    admission_reason: str = ""
    admission_policy_version: str = ""

    # ── Validation (Rule 3, 4, 5, 6) ───────────────────────────────

    def __post_init__(self) -> None:
        # Rule 6: reject unknown enum values
        if self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError(
                f"Invalid source_type '{self.source_type}'. "
                f"Must be one of: {sorted(VALID_SOURCE_TYPES)}"
            )
        if self.write_path not in VALID_WRITE_PATHS:
            raise ValueError(
                f"Invalid write_path '{self.write_path}'. "
                f"Must be one of: {sorted(VALID_WRITE_PATHS)}"
            )
        # Rule 3: role_output requires source_role
        if self.source_type == SOURCE_ROLE_OUTPUT and not self.source_role:
            raise ValueError(
                "source_role must not be null when source_type is 'role_output'"
            )
        # Rule 5: parent_eids must exist (default factory handles this,
        # but guard against None assignment)
        if self.parent_eids is None:
            self.parent_eids = []
        # Deduplicate parent_eids, preserve order
        seen: set = set()
        deduped: List[int] = []
        for eid in self.parent_eids:
            eid_int = int(eid)
            if eid_int not in seen:
                seen.add(eid_int)
                deduped.append(eid_int)
        self.parent_eids = deduped
        # Auto-fill timestamp if not provided
        if self.created_at_ts is None:
            self.created_at_ts = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        # WRITE_MIGRATION admission-field invariants (v2.4.x step 6).
        # These catch half-formed admission records at construction time
        # so malformed rows cannot be written to storage and later
        # confuse the recursion guard or the re-run policy.
        if self.admission_refused and not self.admission_reason:
            raise ValueError(
                "admission_reason must not be empty when admission_refused=True"
            )
        if (self.admission_refused or self.admission_reason) and not self.admission_policy_version:
            raise ValueError(
                "admission_policy_version must not be empty when any admission "
                "decision is recorded"
            )
        # Sentinel source_type pairs with an explicit refusal record.
        # Without this invariant, a row could carry the sentinel (which
        # the guard rejects via _REJECTED_SOURCE_TYPES_IN_WALK) while
        # claiming admission_refused=False, which would be an
        # internally contradictory state.
        if self.source_type == SOURCE_GATE1_UNRECOVERABLE and not self.admission_refused:
            raise ValueError(
                "source_type=SOURCE_GATE1_UNRECOVERABLE requires admission_refused=True"
            )

    # ── Serialization ───────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-safe dict. Omits None optional fields and
        default-valued WRITE_MIGRATION admission fields.

        The admission fields (``admission_refused``, ``admission_reason``,
        ``admission_policy_version``) are stripped when they carry their
        defaults. This keeps payloads written by live ingest paths
        byte-compatible with the pre-step-6 shape, so the v2.4.x schema
        addition is additive and invisible to rows the migration has not
        touched. ``from_dict`` and the recursion guard both treat missing
        admission fields as "no admission decision on file", which is the
        correct reading for any row produced outside the migration.
        """
        d = asdict(self)
        # Strip None optional fields to keep payloads compact. Block B
        # additions (asserted_by, observation_source, inference_rule)
        # strip the same way so live ingest paths that don't use them
        # serialize byte-compatibly with pre-Block-B rows.
        for k in ("tool_name", "session_id", "notes",
                  "asserted_by", "observation_source", "inference_rule"):
            if d.get(k) is None:
                del d[k]
        # Strip default-valued admission fields so pre-step-6 rows and
        # fresh live-ingest rows serialize identically.
        if d.get("admission_refused") is False:
            del d["admission_refused"]
        if d.get("admission_reason") == "":
            del d["admission_reason"]
        if d.get("admission_policy_version") == "":
            del d["admission_policy_version"]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProvenanceV1":
        """Deserialize from dict, ignoring unknown keys."""
        if not d:
            raise ValueError("Cannot create ProvenanceV1 from empty dict")
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)

    # ── Factory methods ─────────────────────────────────────────────

    @classmethod
    def for_user_ingest(
        cls,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Default provenance for plain user input (Rule 2)."""
        return cls(
            source_type=SOURCE_USER_INPUT,
            source_role=None,
            write_path=WRITE_DIRECT_INGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
        )

    @classmethod
    def for_cognition_writeback(
        cls,
        source_role: str,
        parent_eids: Optional[List[int]] = None,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for archivist / cognition pipeline write-back."""
        return cls(
            source_type=SOURCE_ROLE_OUTPUT,
            source_role=source_role,
            write_path=WRITE_COGNITION_WRITEBACK,
            parent_eids=parent_eids or [],
            created_at_step=step,
            session_id=session_id,
            notes=notes,
        )

    @classmethod
    def for_tool_result(
        cls,
        tool_name: str,
        parent_eids: Optional[List[int]] = None,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for content produced by an external MCP/tool call."""
        return cls(
            source_type=SOURCE_TOOL_RESULT,
            source_role=None,
            write_path=WRITE_TOOL_INGEST,
            parent_eids=parent_eids or [],
            created_at_step=step,
            tool_name=tool_name,
            session_id=session_id,
        )

    # ── Block B factories ──────────────────────────────────────────
    #
    # Four factories. for_reference_ingest records a plain storage
    # event (reference identity lives on ReferenceEntry, not here).
    # The three environment factories each populate exactly one
    # evidence-specific field; the others stay None.
    # See docs/BLOCK_B_DESIGN.md §5.1.

    @classmethod
    def for_reference_ingest(
        cls,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for a reference-object storage event.

        The reference object's source_link and source_kind live on
        the ReferenceEntry payload, not on provenance (per the
        ratified carry-forward caution: storage identity is on the
        entry; provenance records the storage EVENT only).
        """
        return cls(
            source_type=SOURCE_REFERENCE_INGEST,
            source_role=None,
            write_path=WRITE_DIRECT_INGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=notes,
        )

    @classmethod
    def for_environment_user_asserted(
        cls,
        asserted_by: str,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for an environment fact supplied by the user.

        `asserted_by` records the user identity who told the system
        this operational fact.
        """
        return cls(
            source_type=SOURCE_ENVIRONMENT_USER_ASSERTED,
            source_role=None,
            write_path=WRITE_DIRECT_INGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=notes,
            asserted_by=asserted_by,
        )

    @classmethod
    def for_environment_observed(
        cls,
        observation_source: str,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for an environment fact produced by direct probe.

        `observation_source` names the probe that produced the
        observation (e.g., "python_version_probe",
        "network_availability_probe"). The probe-on-fail path always
        uses this factory; LLM guesswork must not reach environment
        memory through it (R+5).
        """
        return cls(
            source_type=SOURCE_ENVIRONMENT_OBSERVED,
            source_role=None,
            write_path=WRITE_DIRECT_INGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=notes,
            observation_source=observation_source,
        )

    @classmethod
    def for_environment_inferred(
        cls,
        inference_rule: str,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for an environment fact produced by a ratified
        inference rule.

        `inference_rule` names the ratified rule that produced the
        entry. v0.1 ships with zero rules in
        environment_memory.VALID_INFERENCE_RULES, so any caller
        attempting this factory will be rejected at the fabric layer
        during write_environment validation. The factory itself does
        not validate the rule — it records origin; validation is
        fabric-level doctrine per R+5.
        """
        return cls(
            source_type=SOURCE_ENVIRONMENT_INFERRED,
            source_role=None,
            write_path=WRITE_DIRECT_INGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=notes,
            inference_rule=inference_rule,
        )

    @classmethod
    def for_baton_ingest(
        cls,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for a baton — cross-session attention-bounded intent.

        Block A (docs/BLOCK_A_DESIGN.md §5.1). Baton lifecycle fields
        (owner, expires_when, resolution_condition, status) live on the
        memory entity's extra_payload["baton_lifecycle"], NOT on
        ProvenanceV1. Provenance records origin/lineage only; lifecycle
        state mutates over the baton's life and belongs in payload.

        The write_path remains WRITE_DIRECT_INGEST — baton is WHAT the
        write is (source_type), not a new HOW (write_path).
        """
        return cls(
            source_type=SOURCE_BATON_INTENT,
            source_role=None,
            write_path=WRITE_DIRECT_INGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=notes,
        )

    @classmethod
    def for_collective_echo(
        cls,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for a collective/hivemind echo reingested into an agent."""
        return cls(
            source_type=SOURCE_COLLECTIVE_ECHO,
            source_role=None,
            write_path=WRITE_COLLECTIVE_REINGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=notes,
        )

    # ── Block C factories ──────────────────────────────────────────
    #
    # Three factories, one per closure lifecycle event kind (commit /
    # ratification / revision). Each records event ORIGIN ONLY — never
    # lifecycle state. Lifecycle state lives in ClosureLedger events and
    # is derived by literal event-kind lookup (no inference layer).
    #
    # STRUCTURAL SEPARATION from writeback (docs/BLOCK_C_DESIGN.md §7 +
    # handoff note 4):
    #   - None of these factories calls or reuses for_cognition_writeback.
    #   - They do NOT set write_path=WRITE_COGNITION_WRITEBACK.
    #   - Their source_type values (SOURCE_CLOSURE_*) do NOT substitute
    #     for SOURCE_ROLE_OUTPUT. Archivist authorship and closure
    #     authorship are different authorship classes.
    #   - commit / revision use the dedicated WRITE_CLOSURE_COMMIT path.
    #   - ratification uses WRITE_DIRECT_INGEST because a ratification
    #     event is just a lifecycle event (not a content commit).
    #
    # The `arc_name` + `ratifier` arguments are ORIGIN LINEAGE DATA
    # stored in `notes` — the factory does not introduce new provenance
    # fields for them (keeping ProvenanceV1 narrow; closure-specific
    # fields live on ClosureEntry / ClosureEvent, not here).

    @classmethod
    def for_closure_commit(
        cls,
        arc_name: str,
        ratifier: str,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for a closure commit event.

        `arc_name` names the arc being closed (free-form per D.4).
        `ratifier` records who ratified the commit (agent_id, "user",
        or a dual identifier). Distinct from archivist authorship —
        a closure commit is NOT a cognition writeback (R+9).

        Uses WRITE_CLOSURE_COMMIT write_path per §7.1 (structurally
        distinct from WRITE_COGNITION_WRITEBACK).
        """
        origin = f"closure_commit(arc={arc_name!r}, ratifier={ratifier!r})"
        return cls(
            source_type=SOURCE_CLOSURE_COMMIT,
            source_role=None,
            write_path=WRITE_CLOSURE_COMMIT,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=f"{origin}" if notes is None else f"{origin}; {notes}",
        )

    @classmethod
    def for_closure_ratification(
        cls,
        arc_name: str,
        ratifier: str,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for a closure ratification event.

        A proposal can be ratified without being committed yet, so
        ratification is a distinct event class from commit. `ratifier`
        records who approved the proposal.

        Uses WRITE_DIRECT_INGEST because the ratification record is a
        lifecycle event, not a content commit — only commits and
        revisions carry WRITE_CLOSURE_COMMIT.
        """
        origin = f"closure_ratification(arc={arc_name!r}, ratifier={ratifier!r})"
        return cls(
            source_type=SOURCE_CLOSURE_RATIFICATION,
            source_role=None,
            write_path=WRITE_DIRECT_INGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=f"{origin}" if notes is None else f"{origin}; {notes}",
        )

    @classmethod
    def for_closure_revision(
        cls,
        arc_name: str,
        ratifier: str,
        parent_closure_id: str,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for a closure revision event.

        `parent_closure_id` records the closure being revised. The
        prior version remains readable (R+8: no silent overwrite) —
        revision produces a new `version_id` entry alongside the
        original. Provenance does NOT carry lifecycle state; it only
        records that this revision event was authored by `ratifier`
        on top of `parent_closure_id`.

        Uses WRITE_CLOSURE_COMMIT write_path like commit — both are
        content-emitting closure events and share the dedicated path.
        """
        origin = (
            f"closure_revision(arc={arc_name!r}, ratifier={ratifier!r}, "
            f"parent_closure_id={parent_closure_id!r})"
        )
        return cls(
            source_type=SOURCE_CLOSURE_REVISION,
            source_role=None,
            write_path=WRITE_CLOSURE_COMMIT,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=f"{origin}" if notes is None else f"{origin}; {notes}",
        )

    # ── Normalization ───────────────────────────────────────────────

    @staticmethod
    def normalize_parent(raw: Any) -> Optional[Dict[str, Any]]:
        """Normalize a raw parent-provenance value into a canonical dict shape.

        Storage-layer-only helper. Reduces the four input shapes the recursion
        guard can encounter on an old corpus down to a single canonical form so
        downstream code never has to branch on raw provenance type.

        Handled shapes:
          - None                  → None
          - legacy bare ``str``   → ``{"source_type": "memory", "notes": ...}``
                                    (consistent with the read-path normalization
                                    in ``torment_service/{app,mcp_server,fabric}.py``
                                    established in step 4; see
                                    ``docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md §7``)
          - ``dict`` with valid ``source_type`` → passed through unchanged
          - ``dict`` missing / invalid ``source_type`` → None (fail-closed)
          - ``ProvenanceV1`` instance → ``.to_dict()``

        Any other value (int, list, arbitrary object) → None.

        Returning ``None`` MUST be treated by callers as "unknown /
        non-admissible" — this helper is fail-closed by design, matching the
        corridor-tearing posture of Rule C in the Recursion-Safety Policy.

        This helper does NOT determine admissibility. It only produces a
        canonical shape that a guard (such as
        ``cognition.recursion_guard.recursion_guard_check``) can inspect
        without defensive type-checking.
        """
        if raw is None:
            return None
        if isinstance(raw, ProvenanceV1):
            return raw.to_dict()
        if isinstance(raw, str):
            # Legacy bare-string provenance (pre-ProvenanceV1 artifact).
            # Preserve the raw value in notes so migration tooling can
            # recover original intent later.
            return {
                "source_type": SOURCE_MEMORY,
                "notes": f"legacy_bare_string={raw!r}",
            }
        if isinstance(raw, dict):
            st = raw.get("source_type")
            if st not in VALID_SOURCE_TYPES:
                # Malformed / missing / undeclared vocabulary → fail-closed.
                return None
            return raw
        # Anything else (int, list, object) → not a provenance shape.
        return None

    # ── Safety checks ───────────────────────────────────────────────
    #
    # Recursion safety for archivist writeback is enforced by
    # ``cognition/recursion_guard.py::recursion_guard_check``, which
    # walks the ancestor graph to a bounded depth. The prior one-hop
    # helpers (``is_archivist_writeback``, ``check_recursion_safe``)
    # were removed in step 5 commit B of the v2.4.x tactical provenance
    # pass — they described a one-hop check that was neither the live
    # enforcement shape nor the policy shape, and leaving them in place
    # would have been actively misleading to future readers.
    # See ``docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md §7.3`` for the
    # removal rationale and the safety asymmetry note preserved there
    # for historical context.
