"""Focused contract tests for the frozen Phase-4 A** VHE operator."""

from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from brainvision.fixtures import D0, DA, DB
from brainvision.vhe import (
    ALGORITHM_ID,
    CONTEXT_BLEND_Q,
    FAST_HORIZON_NS,
    MAX_OCCURRENCE_COUNT,
    OPERATOR_ID,
    OPERATOR_MANIFEST_CORE_CANONICAL_BYTES,
    OPERATOR_MANIFEST_CORE_SHA256,
    ORDER_ORIENTATION_INTERNAL_MARGIN_Q,
    PersistentContext,
    Q,
    R_CAPACITY,
    RETAINED_HISTORY_INTERNAL_MARGIN_Q,
    SemanticRegister,
    SemanticRegisterEntry,
    VheValidationError,
    VheState,
    FastTrace,
    effective_fast_trace,
    evolve_fast_trace,
    evolve_vhe_state_as_of,
    fresh_vhe_state,
    mul_q,
    normalize_descriptor,
    operator_manifest,
    operator_manifest_core,
    round_half_even_division,
    update_vhe_state,
)
from brainvision import vhe as vhe_module


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VHE_PATH = REPOSITORY_ROOT / "brainvision" / "vhe.py"


def _update(
    state: VheState,
    *,
    descriptor= D0,
    semantic_event_class: str | None = None,
    prior_ns: int = 0,
    elapsed_ns: int = 0,
):
    return update_vhe_state(
        state=state,
        descriptor=descriptor,
        semantic_event_class=semantic_event_class,
        prior_committed_active_time_ns=prior_ns,
        elapsed_active_time_ns=elapsed_ns,
    )


def test_frozen_constants_and_signed_round_half_even_examples() -> None:
    assert Q == 1_000_000
    assert FAST_HORIZON_NS == 5_000_000_000
    assert CONTEXT_BLEND_Q == 500_000
    assert R_CAPACITY == 8
    assert RETAINED_HISTORY_INTERNAL_MARGIN_Q == 500_000
    assert ORDER_ORIENTATION_INTERNAL_MARGIN_Q == 500_000

    assert round_half_even_division(1, 2) == 0
    assert round_half_even_division(-1, 2) == 0
    assert round_half_even_division(3, 2) == 2
    assert round_half_even_division(-3, 2) == -2
    assert mul_q(500_000, 1) == 0
    assert mul_q(500_000, 3) == 2
    assert mul_q(-500_000, 3) == -2


@pytest.mark.parametrize("denominator", [0, -1, True, 1.0])
def test_rne_rejects_invalid_denominators(denominator: object) -> None:
    with pytest.raises(VheValidationError):
        round_half_even_division(1, denominator)  # type: ignore[arg-type]


def test_frozen_state_types_enforce_canonical_fast_trace_and_bounds() -> None:
    state = fresh_vhe_state()
    with pytest.raises(AttributeError):
        state.fast_trace = FastTrace(  # type: ignore[misc]
            amplitude_1_q=1,
            amplitude_2_q=0,
            remaining_ns=FAST_HORIZON_NS,
        )

    with pytest.raises(VheValidationError):
        FastTrace(amplitude_1_q=1, amplitude_2_q=0, remaining_ns=0)
    with pytest.raises(VheValidationError):
        FastTrace(amplitude_1_q=0, amplitude_2_q=0, remaining_ns=1)
    with pytest.raises(VheValidationError):
        PersistentContext(luminance_q=Q + 1, contrast_q=0, orientation_q=0)


def test_normalization_maps_the_frozen_fixtures_exactly() -> None:
    assert normalize_descriptor(D0) == (0, 0)
    assert normalize_descriptor(DA) == (Q, 0)
    assert normalize_descriptor(DB) == (0, Q)


def test_fast_trace_evolution_has_exact_composition_and_effective_trace() -> None:
    trace = FastTrace(
        amplitude_1_q=Q,
        amplitude_2_q=0,
        remaining_ns=FAST_HORIZON_NS,
    )
    one_second = 1_000_000_000
    evolved_once = evolve_fast_trace(trace, one_second)
    assert evolved_once.remaining_ns == 4_000_000_000
    assert effective_fast_trace(evolved_once) == (800_000, 0)
    assert evolve_fast_trace(evolved_once, 4_000_000_000) == evolve_fast_trace(
        trace,
        FAST_HORIZON_NS,
    )
    assert evolve_fast_trace(
        evolve_fast_trace(trace, 1_234_567_890),
        2_345_678_901,
    ) == evolve_fast_trace(trace, 3_580_246_791)


def test_pure_as_of_evolution_does_not_mutate_committed_state() -> None:
    initial = _update(fresh_vhe_state(), descriptor=DA).state
    original_fast = initial.fast_trace
    original_context = initial.persistent_context
    original_register = initial.semantic_register
    evolved = evolve_vhe_state_as_of(initial, FAST_HORIZON_NS)

    assert initial.fast_trace == original_fast
    assert initial.persistent_context == original_context
    assert initial.semantic_register == original_register
    assert evolved.fast_trace == FastTrace(amplitude_1_q=0, amplitude_2_q=0, remaining_ns=0)
    assert evolved.persistent_context == original_context
    assert evolved.semantic_register == original_register
    assert evolve_vhe_state_as_of(initial, FAST_HORIZON_NS) == evolved


def test_context_coordinate_update_stays_between_current_and_target_without_clipping() -> None:
    for current_q in (-Q, -Q + 1, -1, 0, 1, Q - 1, Q):
        for target_q in (-Q, -Q + 1, -1, 0, 1, Q - 1, Q):
            for gain_q in (0, 1, 2, CONTEXT_BLEND_Q - 1, CONTEXT_BLEND_Q):
                updated_q = vhe_module._context_coordinate_update(  # noqa: SLF001
                    current_q,
                    target_q,
                    gain_q,
                )
                assert min(current_q, target_q) <= updated_q <= max(current_q, target_q)
                assert -Q <= updated_q <= Q


def test_update_exposes_w_and_c_and_canonicalizes_final_d0_fast_trace() -> None:
    after_a = _update(fresh_vhe_state(), descriptor=DA).state
    after_b = _update(after_a, descriptor=DB, elapsed_ns=1_000_000_000)
    assert after_b.write_gate_q == Q
    assert after_b.clamped_orientation_q == 800_000

    after_d0 = _update(after_b.state, descriptor=D0, elapsed_ns=1_000_000_000)
    assert after_d0.write_gate_q == 0
    assert after_d0.clamped_orientation_q == 0
    assert after_d0.state.fast_trace == FastTrace(
        amplitude_1_q=0,
        amplitude_2_q=0,
        remaining_ns=0,
    )


def test_semantic_changes_are_isolated_from_all_dynamics() -> None:
    dynamic_only = _update(fresh_vhe_state(), descriptor=DA, semantic_event_class=None)
    semantic = _update(
        fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class="detector:scene_change",
    )
    assert semantic.write_gate_q == dynamic_only.write_gate_q
    assert semantic.clamped_orientation_q == dynamic_only.clamped_orientation_q
    assert semantic.state.fast_trace == dynamic_only.state.fast_trace
    assert semantic.state.persistent_context == dynamic_only.state.persistent_context
    assert semantic.state.semantic_register != dynamic_only.state.semantic_register
    assert dynamic_only.state.semantic_register == fresh_vhe_state().semantic_register


def test_semantic_register_recurrence_saturation_order_and_eviction() -> None:
    state = fresh_vhe_state()
    for index in range(R_CAPACITY):
        state = _update(
            state,
            semantic_event_class=f"test:event{index}",
            prior_ns=index,
        ).state

    register = state.semantic_register
    assert tuple(entry.semantic_event_class for entry in register.entries) == tuple(
        sorted(entry.semantic_event_class for entry in register.entries)
    )
    assert register.open_semantic_event_class == "test:event7"

    state = _update(
        state,
        semantic_event_class="test:new",
        prior_ns=10,
    ).state
    tokens = {entry.semantic_event_class for entry in state.semantic_register.entries}
    assert "test:event0" not in tokens
    assert "test:event7" in tokens
    assert state.semantic_register.open_semantic_event_class == "test:new"

    state = _update(
        state,
        semantic_event_class="test:event0",
        prior_ns=11,
    ).state
    reintroduced = next(
        entry
        for entry in state.semantic_register.entries
        if entry.semantic_event_class == "test:event0"
    )
    assert reintroduced.occurrence_count == 1

    saturated_register = SemanticRegister(
        entries=(
            SemanticRegisterEntry(
                semantic_event_class="test:saturated",
                first_seen_active_time_ns=0,
                last_seen_active_time_ns=0,
                occurrence_count=MAX_OCCURRENCE_COUNT,
            ),
        ),
        open_semantic_event_class="test:saturated",
    )
    saturated_state = replace(fresh_vhe_state(), semantic_register=saturated_register)
    saturated_result = _update(
        saturated_state,
        semantic_event_class="test:saturated",
        prior_ns=1,
    )
    saturated_entry = saturated_result.state.semantic_register.entries[0]
    assert saturated_entry.occurrence_count == MAX_OCCURRENCE_COUNT
    assert saturated_entry.last_seen_active_time_ns == 1


def test_semantic_register_normal_recurrence_uses_derived_event_active_time() -> None:
    first = _update(
        fresh_vhe_state(),
        semantic_event_class="test:recurring",
        prior_ns=101,
        elapsed_ns=23,
    )
    assert first.event_active_time_ns == 124

    recurrence = _update(
        first.state,
        semantic_event_class="test:recurring",
        prior_ns=8_000,
        elapsed_ns=77,
    )
    assert recurrence.event_active_time_ns == 8_077

    entry = recurrence.state.semantic_register.entries[0]
    assert entry.semantic_event_class == "test:recurring"
    assert entry.first_seen_active_time_ns == 124
    assert entry.last_seen_active_time_ns == 8_077
    assert entry.occurrence_count == 2
    assert recurrence.state.semantic_register.open_semantic_event_class == "test:recurring"


def test_semantic_register_eviction_uses_full_tuple_and_preserves_open_token() -> None:
    register = SemanticRegister(
        entries=(
            SemanticRegisterEntry(
                semantic_event_class="test:alpha",
                first_seen_active_time_ns=1,
                last_seen_active_time_ns=10,
                occurrence_count=1,
            ),
            SemanticRegisterEntry(
                semantic_event_class="test:beta",
                first_seen_active_time_ns=1,
                last_seen_active_time_ns=10,
                occurrence_count=1,
            ),
            SemanticRegisterEntry(
                semantic_event_class="test:open",
                first_seen_active_time_ns=0,
                last_seen_active_time_ns=0,
                occurrence_count=1,
            ),
            SemanticRegisterEntry(
                semantic_event_class="test:primary",
                first_seen_active_time_ns=0,
                last_seen_active_time_ns=11,
                occurrence_count=1,
            ),
            SemanticRegisterEntry(
                semantic_event_class="test:secondary",
                first_seen_active_time_ns=2,
                last_seen_active_time_ns=10,
                occurrence_count=1,
            ),
            SemanticRegisterEntry(
                semantic_event_class="test:tail_one",
                first_seen_active_time_ns=3,
                last_seen_active_time_ns=12,
                occurrence_count=1,
            ),
            SemanticRegisterEntry(
                semantic_event_class="test:tail_three",
                first_seen_active_time_ns=4,
                last_seen_active_time_ns=13,
                occurrence_count=1,
            ),
            SemanticRegisterEntry(
                semantic_event_class="test:tail_two",
                first_seen_active_time_ns=5,
                last_seen_active_time_ns=14,
                occurrence_count=1,
            ),
        ),
        open_semantic_event_class="test:open",
    )
    full_state = replace(fresh_vhe_state(), semantic_register=register)

    result = _update(
        full_state,
        semantic_event_class="test:new",
        prior_ns=10_000,
        elapsed_ns=9,
    )
    entries = {
        entry.semantic_event_class: entry
        for entry in result.state.semantic_register.entries
    }

    # `test:alpha` wins the full tuple: it ties `test:beta` on the first two
    # fields, precedes it lexically, and precedes the primary/secondary ties.
    assert "test:alpha" not in entries
    assert "test:beta" in entries
    assert "test:primary" in entries
    assert "test:secondary" in entries
    assert "test:open" in entries
    assert entries["test:new"].first_seen_active_time_ns == 10_009
    assert entries["test:new"].last_seen_active_time_ns == 10_009
    assert result.state.semantic_register.open_semantic_event_class == "test:new"


def test_register_state_invariants_are_total() -> None:
    entry = SemanticRegisterEntry(
        semantic_event_class="test:entry",
        first_seen_active_time_ns=0,
        last_seen_active_time_ns=0,
        occurrence_count=1,
    )
    with pytest.raises(VheValidationError):
        SemanticRegister(entries=(entry,), open_semantic_event_class=None)
    with pytest.raises(VheValidationError):
        SemanticRegister(entries=(), open_semantic_event_class="test:entry")
    with pytest.raises(VheValidationError):
        SemanticRegister(entries=(entry, entry), open_semantic_event_class="test:entry")


def test_operator_manifest_core_is_complete_canonical_and_not_self_referential() -> None:
    assert ALGORITHM_ID == "fixedpoint-context-a-double-star.v1"
    assert OPERATOR_MANIFEST_CORE_SHA256 == (
        "c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb"
    )
    assert OPERATOR_ID == (
        "bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb"
    )
    core = operator_manifest_core()
    equations = core["equations"]
    assert equations["f"] == {
        "effective_trace": "f_eff_i=RNE(amplitude_i*remaining/FAST_HORIZON_NS)",
        "expiry_canonicalization": "remaining==0->F=(0,0,0)",
        "free_evolution": "remaining'=max(0,remaining-delta)",
        "observation_overwrite": "u==(0,0)->F=(0,0,0);else->F=(u1,u2,FAST_HORIZON_NS)",
    }
    assert equations["w"] == "W=min(Q,abs(u1)+abs(u2))"
    assert equations["c"] == {
        "clamp": "c=clamp(c_raw,-Q,Q)",
        "raw": "c_raw=mul_q(f_eff_1,u2)-mul_q(f_eff_2,u1)",
    }
    assert equations["s"] == {
        "base_gain": "base_g=mul_q(W,CONTEXT_BLEND_Q)",
        "coordinate_gains": [
            "g1=mul_q(base_g,abs(u1))",
            "g2=mul_q(base_g,abs(u2))",
            "g3=mul_q(base_g,abs(c))",
        ],
        "no_post_update_clipping": True,
        "target": "target=(u1,u2,c)",
        "update": "S_i'=S_i+mul_q(g_i,target_i-S_i)",
    }
    assert equations["time"] == (
        "event_active_time_ns=prior_committed_active_time_ns+elapsed_active_time_ns"
    )
    assert equations["pure_as_of"] == "elapsed_time_evolves_F_only;S_and_R_unchanged"
    assert equations["rne_mul_q"] == "mul_q(a,b)=exactly_one_RNE(exact_a_times_b_over_Q)"
    assert "operator_id" not in core
    assert b'"operator_id"' not in OPERATOR_MANIFEST_CORE_CANONICAL_BYTES
    assert OPERATOR_MANIFEST_CORE_CANONICAL_BYTES == json.dumps(
        core,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    assert OPERATOR_MANIFEST_CORE_SHA256 == sha256(OPERATOR_MANIFEST_CORE_CANONICAL_BYTES).hexdigest()
    assert OPERATOR_ID == "bvheop1_" + sha256(OPERATOR_MANIFEST_CORE_CANONICAL_BYTES).hexdigest()
    assert operator_manifest()["operator_id"] == OPERATOR_ID


def test_returned_manifest_objects_cannot_mutate_canonical_authority() -> None:
    original_bytes = OPERATOR_MANIFEST_CORE_CANONICAL_BYTES
    mutable_core = operator_manifest_core()
    mutable_core["equations"]["f"]["free_evolution"] = "tampered"
    mutable_core["fixture_sha256"]["d0"] = "tampered"
    mutable_full = operator_manifest()
    mutable_full["operator_id"] = "tampered"
    mutable_full["equations"]["s"]["update"] = "tampered"

    assert OPERATOR_MANIFEST_CORE_CANONICAL_BYTES == original_bytes
    assert operator_manifest_core()["equations"]["f"]["free_evolution"] == (
        "remaining'=max(0,remaining-delta)"
    )
    assert operator_manifest_core()["fixture_sha256"]["d0"] != "tampered"
    assert operator_manifest()["operator_id"] == OPERATOR_ID


def test_vhe_module_isolated_from_runtime_and_phase5_plus_implementation() -> None:
    tree = ast.parse(VHE_PATH.read_text(encoding="utf-8"), filename=str(VHE_PATH))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert {name.lstrip(".") for name in imports} <= {
        "__future__",
        "dataclasses",
        "hashlib",
        "json",
        "re",
        "typing",
        "brainvision.fixtures",
        "brainvision.observation",
        "brainvision.clock",
    }

    declared_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not declared_names & {
        "Projection",
        "BrainvisionConfig",
        "BrainvisionSidecar",
        "BrainvisionRegistry",
        "ingest_visual_observation",
        "CharacterModulation",
    }

    code = """
import json
import sys
import brainvision.vhe
print(json.dumps(sorted(sys.modules)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=REPOSITORY_ROOT, check=True, capture_output=True, text=True)
    loaded = json.loads(completed.stdout)
    prohibited_prefixes = (
        "research.brainvision",
        "torment_service",
        "cognition",
        "memory",
        "kernel",
        "srg",
        "hivermind",
    )
    assert not any(name.startswith(prohibited_prefixes) for name in loaded)
