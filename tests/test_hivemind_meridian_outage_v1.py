"""Deterministic preflight tests for the offline Meridian Outage harness."""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from experiments.hivemind_meridian_outage_v1.harness import (
    ConditionConfig,
    MeridianOutageHarness,
    NullCoordinationAdapter,
    ProviderRoundResponse,
    TormentFabricAdapter,
    _aggregate_final_answers,
)
from experiments.hivemind_meridian_outage_v1.results import (
    SEAL_INDEX_FILENAME,
    ResultVerificationError,
    validate_result_schema,
    verify_sealed_run,
)
from experiments.hivemind_meridian_outage_v1.scoring import score_run
from experiments.hivemind_meridian_outage_v1.spec import (
    AGENT_CARDS,
    CARD_IDS,
    EVALUATOR_ANNOTATIONS,
    FROZEN_BASELINE_COMMIT,
    FROZEN_CORPUS_SHA256,
    FROZEN_MANIFEST_SHA256,
    FROZEN_GROUND_TRUTH_SHA256,
    GROUND_TRUTH,
    VALID_N,
    agent_view,
    assignment_manifest,
    assignment_manifest_sha256,
    cards_for_agent,
    corpus_sha256,
    evaluator_view,
    ground_truth_sha256,
)
from torment_service.fabric import TormentFabric


class RecordingProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def metadata(self) -> Mapping[str, Any]:
        return {
            "provider": "deterministic-test-double",
            "model_id": "deterministic-test-double",
            "provider_mode": "dry",
            "session_isolation": "per_agent_per_round",
            "retry_policy": "none",
            "sampling": {
                "max_tokens": {"mode": "explicit", "explicit_value": 1024},
                "temperature": {"mode": "provider_default", "explicit_value": None},
                "top_p": {"mode": "provider_default", "explicit_value": None},
                "top_k": {"mode": "provider_default", "explicit_value": None},
                "thinking": {"mode": "provider_default", "explicit_value": None},
                "timeout": {"mode": "provider_default", "explicit_value": None},
                "system_instruction": {
                    "mode": "harness_instruction",
                    "sha256": "934b1ada8807926e70bf2f1f0482e58fec563d3df2975714e0d77251cc2a3fef",
                },
            },
        }

    def run_round(
        self,
        *,
        agent_id: str,
        round_number: int,
        instruction: str,
        assigned_cards: Sequence[Mapping[str, str]],
        collective_context: Mapping[str, Any] | None,
        naive_shared_findings: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        self.calls.append({
            "agent_id": agent_id,
            "round": round_number,
            "assigned_cards": [dict(card) for card in assigned_cards],
            "collective_context": collective_context,
            "naive_shared_findings": [dict(item) for item in naive_shared_findings],
            "instruction": instruction,
        })
        first_card = assigned_cards[0]
        return {
            "findings": [{
                "text": f"{agent_id} observed {first_card['card_id']}",
                "card_ids": [first_card["card_id"]],
                "share_permitted": True,
            }],
            "claims": [{
                "text": f"{agent_id} observed {first_card['card_id']}",
                "card_ids": [first_card["card_id"]],
                "stance": "asserts",
            }],
            "final_answer": {
                "root_cause": "future-dated certificate not before due to signer clock",
                "contributing_factors": [
                    "chrony clock migration was incomplete",
                    "rotation preflight did not validate not before",
                    "alerting anchored on deployment instead of certificate telemetry",
                ],
                "cited_card_ids": [
                    card["card_id"] for card in assigned_cards if card["card_id"].startswith("D-")
                ],
            },
            "collective_context_consumed": collective_context is not None,
        }


class RecordingAdapter(NullCoordinationAdapter):
    def __init__(self, collective_context: Mapping[str, Any] | None = None) -> None:
        super().__init__()
        self.collective_context_value = dict(collective_context or {})
        self.started_config: ConditionConfig | None = None
        self.boundary_calls = 0
        self.context_calls: list[str] = []

    def start(self, *, workspace_id: str, agent_ids: Sequence[str], config: ConditionConfig) -> None:
        self.started_config = config
        super().start(workspace_id=workspace_id, agent_ids=agent_ids, config=config)

    def process_round_boundary(self) -> Mapping[str, Any]:
        self.boundary_calls += 1
        return {"operator_action": "process_proposals_once", "processed": 0}

    def collective_context(self, *, agent_id: str) -> Mapping[str, Any]:
        self.context_calls.append(agent_id)
        return dict(self.collective_context_value)


class LeakingProvider(RecordingProvider):
    def run_round(self, **kwargs: Any) -> Mapping[str, Any]:
        output = dict(super().run_round(**kwargs))
        output["claims"] = list(output["claims"]) + [{
            "text": "forbidden cross-agent citation",
            "card_ids": ["D-001"],
            "stance": "asserts",
        }]
        return output


class PromotingProvider(RecordingProvider):
    """Independent agents cite their own cards but submit one convergent proposal text."""

    def run_round(self, **kwargs: Any) -> Mapping[str, Any]:
        output = dict(super().run_round(**kwargs))
        output["findings"] = [dict(item) for item in output["findings"]]
        output["findings"][0]["text"] = "Meridian certificate evidence requires promotion review"
        return output


class MissingMetadataProvider(RecordingProvider):
    def metadata(self) -> Mapping[str, Any]:
        return {"model_id": "missing-required-fields"}


class SharedSessionProvider(RecordingProvider):
    def metadata(self) -> Mapping[str, Any]:
        metadata = dict(super().metadata())
        metadata["session_isolation"] = "shared"
        return metadata


class EvidenceProvider(RecordingProvider):
    def __init__(self, *, fail_on_call: int | None = None, invalid_on_call: int | None = None) -> None:
        super().__init__()
        self.fail_on_call = fail_on_call
        self.invalid_on_call = invalid_on_call

    def metadata(self) -> Mapping[str, Any]:
        metadata = dict(super().metadata())
        metadata.update({"provider": "simulated-live-provider", "model_id": "simulated-meridian-v1", "provider_mode": "live"})
        return metadata

    def run_round(self, **kwargs: Any) -> ProviderRoundResponse:
        output = dict(super().run_round(**kwargs))
        call_number = len(self.calls)
        if call_number == self.fail_on_call:
            raise RuntimeError("simulated provider outage")
        if call_number == self.invalid_on_call:
            return ProviderRoundResponse(
                output={"findings": "not-a-list", "claims": []},
                raw_response_text="{not valid Meridian response}",
                usage={"input_tokens": 17, "output_tokens": 4, "total_tokens": 21},
                response_metadata={"authorization": "Bearer must-not-be-sealed"},
            )
        return ProviderRoundResponse(
            output=output,
            raw_response_text=f"raw response {call_number}",
            usage={"input_tokens": 17, "output_tokens": 4, "total_tokens": 21},
            response_metadata={"request_id": f"simulated-{call_number}"},
        )


class SecretMetadataProvider(EvidenceProvider):
    def metadata(self) -> Mapping[str, Any]:
        metadata = dict(super().metadata())
        metadata["api_key"] = "must-not-be-sealed"
        return metadata


def _run_condition(tmp_path: Path, condition: str, run_id: str):
    provider = RecordingProvider()
    adapter = RecordingAdapter({"recent_events": [{"event_id": "cev_mock"}], "event_count": 1})
    run_dir = MeridianOutageHarness(provider, adapter).run(
        output_root=tmp_path,
        run_id=run_id,
        condition=condition,
        n_agents=5,
    )
    return provider, adapter, run_dir, verify_sealed_run(run_dir)


def _valid_answer(card_ids: Sequence[str]) -> dict[str, Any]:
    return {
        "root_cause": "future-dated certificate not before caused by signer clock",
        "contributing_factors": [
            "chrony clock migration failure",
            "rotation preflight not before validation missing",
            "alert deployment certificate routing problem",
        ],
        "cited_card_ids": list(card_ids),
    }


def test_frozen_baseline_corpus_and_agent_evaluator_separation() -> None:
    assert FROZEN_BASELINE_COMMIT == "6970ea70eae7decc52d4b073032505352929b75f"
    assert len(AGENT_CARDS) == 120
    assert [sum(card["card_id"].startswith(prefix) for card in AGENT_CARDS) for prefix in ("R-", "M-", "D-", "C-", "P-", "N-")] == [36, 26, 5, 17, 6, 30]
    assert GROUND_TRUTH["decisive_card_ids"] == [f"D-{index:03d}" for index in range(1, 6)]
    assert all(EVALUATOR_ANNOTATIONS[card_id]["is_false"] for card_id in GROUND_TRUTH["poison_card_ids"])
    assert corpus_sha256() == FROZEN_CORPUS_SHA256
    assert ground_truth_sha256() == FROZEN_GROUND_TRUTH_SHA256

    visible = agent_view()
    assert all(set(card) == {"card_id", "source_id", "source_tier", "text"} for card in visible)
    serialized_agent_view = json.dumps(visible, sort_keys=True)
    assert all(token not in serialized_agent_view for token in ("ground_truth_tags", "is_false", "primary_root_cause"))
    assert evaluator_view()["ground_truth"] == GROUND_TRUTH


def test_corpus_source_metadata_does_not_encode_evaluator_categories_or_truth() -> None:
    prohibited = ("primary-evidence", "unverified-chat", "neutral-operations", "supporting-record", "deployment-record")
    assert all(not any(token in card["source_id"] for token in prohibited) for card in AGENT_CARDS)
    by_tier: dict[str, set[tuple[bool, bool]]] = {}
    for card in AGENT_CARDS:
        annotation = EVALUATOR_ANNOTATIONS[card["card_id"]]
        by_tier.setdefault(card["source_tier"], set()).add(
            (annotation["is_relevant"], annotation["is_false"])
        )
    assert (False, False) in by_tier["TIER_1"]
    assert (True, False) in by_tier["TIER_4"]
    assert (False, True) in by_tier["TIER_2"]
    assert (False, True) in by_tier["TIER_3"]
    assert (True, False) in by_tier["TIER_2"]
    assert (True, False) in by_tier["TIER_3"]


def test_assignment_manifests_are_deterministic_complete_and_pin_n5_mechanics_only() -> None:
    for n_agents in VALID_N:
        manifest = assignment_manifest(n_agents)
        assert manifest == assignment_manifest(n_agents)
        assert assignment_manifest_sha256(n_agents) == FROZEN_MANIFEST_SHA256[n_agents]
        assignments = manifest["assignments"]
        assert {card_id for card_ids in assignments.values() for card_id in card_ids} == set(CARD_IDS)
        assert all(0 < len(card_ids) < len(CARD_IDS) for card_ids in assignments.values())
        assert all(sum(card_id in card_ids for card_ids in assignments.values()) == 3 for card_id in CARD_IDS if card_id.startswith("R-"))
        assert all(sum(card_id in card_ids for card_ids in assignments.values()) == 2 for card_id in CARD_IDS if card_id.startswith(("M-", "C-")))
    n5_assignments = assignment_manifest(5)["assignments"]
    decisive_holders = {
        card_id: [agent_id for agent_id, cards in n5_assignments.items() if card_id in cards]
        for card_id in GROUND_TRUTH["decisive_card_ids"]
    }
    assert all(len(holders) == 1 for holders in decisive_holders.values())
    assert {holders[0] for holders in decisive_holders.values()} == set(n5_assignments)


@pytest.mark.parametrize("condition", (
    "A_PRIVATE",
    "B1_TORMENT_MECHANISMS_ONLY",
    "B2_TORMENT_SALIENCE_SURFACED",
    "C_NAIVE_SHARED_CONTENT",
))
def test_condition_isolation_and_sealed_results(tmp_path: Path, condition: str) -> None:
    provider, adapter, run_dir, result = _run_condition(tmp_path, condition, f"run-{condition.lower()}")
    assert run_dir.is_dir()
    assert result["condition"] == condition
    assert result["run_status"] == "COMPLETE"
    assert result["model_call_evidence"]["live_model_calls_performed"] is False
    assert result["model_call_evidence"]["logical_model_call_count_planned"] == 10
    assert result["model_call_evidence"]["logical_model_call_count_attempted"] == 10
    assert result["assignment_manifest_sha256"] == assignment_manifest_sha256(5)
    assert result["provider"]["session_isolation"] == "per_agent_per_round"
    assert result["cost_metrics"]["failure_retry_count"] == 0
    assert result["cost_metrics"]["failure_retry_observability"] == "reported"
    round_two = [call for call in provider.calls if call["round"] == 2]
    if condition == "A_PRIVATE":
        assert adapter.boundary_calls == 0 and adapter.context_calls == []
        assert all(call["collective_context"] is None and not call["naive_shared_findings"] for call in round_two)
    elif condition == "B1_TORMENT_MECHANISMS_ONLY":
        assert adapter.boundary_calls == 1 and len(adapter.context_calls) == 5
        assert all(call["collective_context"] is None and not call["naive_shared_findings"] for call in round_two)
    elif condition == "B2_TORMENT_SALIENCE_SURFACED":
        assert adapter.boundary_calls == 1 and len(adapter.context_calls) == 5
        assert all(call["collective_context"] == adapter.collective_context_value for call in round_two)
    else:
        assert adapter.boundary_calls == 0 and adapter.context_calls == []
        assert all(call["collective_context"] is None and call["naive_shared_findings"] for call in round_two)


def test_b1_round_two_provider_inputs_match_private_condition(tmp_path: Path) -> None:
    private_provider = RecordingProvider()
    b1_provider = RecordingProvider()
    MeridianOutageHarness(private_provider, RecordingAdapter()).run(
        output_root=tmp_path / "private", run_id="a", condition="A_PRIVATE", n_agents=5,
    )
    MeridianOutageHarness(b1_provider, RecordingAdapter()).run(
        output_root=tmp_path / "b1", run_id="b", condition="B1_TORMENT_MECHANISMS_ONLY", n_agents=5,
    )
    def round_two_inputs(provider: RecordingProvider) -> list[dict[str, Any]]:
        return [{key: value for key, value in call.items() if key != "agent_id"} for call in provider.calls if call["round"] == 2]
    assert round_two_inputs(private_provider) == round_two_inputs(b1_provider)


def test_per_agent_scoring_keeps_population_union_out_of_primary_score() -> None:
    assignments = assignment_manifest(5)["assignments"]
    answers = {
        agent_id: _valid_answer([card_id for card_id in cards if card_id.startswith("D-")])
        for agent_id, cards in assignments.items()
    }
    union = _aggregate_final_answers(answers)
    scores = score_run(answers, union, {agent_id: [] for agent_id in assignments}, {agent_id: [] for agent_id in assignments}, assignments=assignments)
    assert scores["best_agent_score"]["score_0_to_5"] == 4
    assert scores["deterministic_union_score"]["metrics"]["deterministic_task_proxy"]["score_0_to_5"] == 5
    assert scores["best_agent_score"]["score_0_to_5"] != scores["deterministic_union_score"]["metrics"]["deterministic_task_proxy"]["score_0_to_5"]
    assert scores["deterministic_union_score"]["labels"] == ["ORACLE-LIKE POPULATION UPPER BOUND", "NOT AN AGENT ANSWER", "NOT COLLECTIVE COGNITION"]


def test_population_representative_root_uses_support_not_alphabetical_lottery() -> None:
    aggregate = _aggregate_final_answers({
        "researcher_001": {"root_cause": "zeta supported root", "contributing_factors": [], "cited_card_ids": []},
        "researcher_002": {"root_cause": "zeta supported root", "contributing_factors": [], "cited_card_ids": []},
        "researcher_003": {"root_cause": "alpha minority root", "contributing_factors": [], "cited_card_ids": []},
    })
    assert aggregate["root_cause"] == "zeta supported root"
    assert "population diagnostic only" in aggregate["representative_root_rule"]


def test_stance_aware_poison_and_card_discovery_duplicate_metrics() -> None:
    assignments = assignment_manifest(5)["assignments"]
    poison_card = GROUND_TRUTH["poison_card_ids"][0]
    holder = next(agent_id for agent_id, cards in assignments.items() if poison_card in cards)
    other = next(agent_id for agent_id in assignments if agent_id != holder)
    claims = {agent_id: [] for agent_id in assignments}
    claims[holder].append({"text": "poison adopted", "card_ids": [poison_card], "stance": "asserts"})
    claims[other].extend([
        {"text": "poison rejected", "card_ids": [poison_card], "stance": "refutes"},
        {"text": "poison noted", "card_ids": [poison_card], "stance": "mentions"},
    ])
    findings = {agent_id: [] for agent_id in assignments}
    findings[holder] = [{"text": "independent wording A", "card_ids": [poison_card]}]
    findings[other] = [{"text": "independent wording B", "card_ids": [poison_card]}]
    scores = score_run(
        {agent_id: {} for agent_id in assignments}, {}, claims, findings, assignments=assignments,
    )
    assert scores["false_assertion_rate"] == 1.0
    assert scores["poison_evidence_inheritance"]["propagated_beyond_initial_holders_by_assertion"] == {}
    assert scores["poison_evidence_inheritance"]["poison_cards_cited_any_stance"][poison_card] == sorted([holder, other])
    assert scores["card_discovery_multiplicity"][poison_card] == 2
    assert scores["duplicate_work_count"] == 1


def test_invalid_provider_or_visibility_evidence_seals_failed_without_classification(tmp_path: Path) -> None:
    forbidden_adapter = RecordingAdapter({"recent_events": [], "packet_summary": "forbidden peer text"})
    run_dir = MeridianOutageHarness(RecordingProvider(), forbidden_adapter).run(
        output_root=tmp_path, run_id="bad-b2", condition="B2_TORMENT_SALIENCE_SURFACED", n_agents=5,
    )
    assert verify_sealed_run(run_dir)["run_status"] == "FAILED"
    leaked_card_adapter = RecordingAdapter({
        "recent_events": [{"summary": AGENT_CARDS[0]["text"]}], "event_count": 1,
    })
    card_text_run = MeridianOutageHarness(RecordingProvider(), leaked_card_adapter).run(
        output_root=tmp_path, run_id="card-text-b2", condition="B2_TORMENT_SALIENCE_SURFACED", n_agents=5,
    )
    leaking_run = MeridianOutageHarness(LeakingProvider(), RecordingAdapter()).run(
        output_root=tmp_path, run_id="leaking", condition="B1_TORMENT_MECHANISMS_ONLY", n_agents=5,
    )
    assert verify_sealed_run(card_text_run)["run_status"] == "FAILED"
    assert verify_sealed_run(leaking_run)["run_status"] == "FAILED"


def test_provider_metadata_and_session_isolation_fail_closed(tmp_path: Path) -> None:
    for provider, expected in ((MissingMetadataProvider(), "missing required"), (SharedSessionProvider(), "per_agent_per_round")):
        with pytest.raises(ValueError, match=expected):
            MeridianOutageHarness(provider, RecordingAdapter()).run(
                output_root=tmp_path, run_id=provider.__class__.__name__, condition="A_PRIVATE", n_agents=5,
            )


def test_external_seal_index_is_append_only_and_anchors_run(tmp_path: Path) -> None:
    _, _, run_dir, _ = _run_condition(tmp_path, "B2_TORMENT_SALIENCE_SURFACED", "sealed-run")
    index_path = tmp_path / SEAL_INDEX_FILENAME
    rows = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["run_id"] == "sealed-run"
    assert rows[0]["run_status"] == "COMPLETE"
    assert rows[0]["sealed_json_sha256"]
    with pytest.raises(FileExistsError, match="duplicate experiment run ID"):
        _run_condition(tmp_path, "B2_TORMENT_SALIENCE_SURFACED", "sealed-run")
    raw_path = run_dir / "raw_outputs.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw["rewritten"] = True
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ResultVerificationError, match="sealed artifact hash mismatch"):
        verify_sealed_run(run_dir)


def test_simulated_live_provider_seals_truthful_attempts_raw_text_and_usage(tmp_path: Path) -> None:
    run_dir = MeridianOutageHarness(EvidenceProvider(), RecordingAdapter()).run(
        output_root=tmp_path, run_id="simulated-live", condition="A_PRIVATE", n_agents=5,
    )
    result = verify_sealed_run(run_dir, require_complete=True)
    evidence = result["model_call_evidence"]
    assert evidence == {
        "live_model_calls_performed": True,
        "logical_model_call_count_planned": 10,
        "characterization_logical_model_call_count_planned": 40,
        "logical_model_call_count_attempted": 10,
        "logical_model_call_count_succeeded": 10,
        "logical_model_call_count_failed": 0,
        "retry_count": 0,
        "hidden_evaluator_model_calls": 0,
        "maximum_attempts_per_logical_call": 1,
    }
    raw = json.loads((run_dir / "raw_outputs.json").read_text(encoding="utf-8"))
    assert raw["provider_attempts"][0]["raw_response_text"] == "raw response 1"
    assert raw["provider_attempts"][0]["usage"] == {
        "availability": "provider_reported", "input_tokens": 17, "output_tokens": 4, "total_tokens": 21,
    }
    assert all(attempt["attempt_number"] == 1 and attempt["success"] for attempt in raw["provider_attempts"])


def test_provider_failure_seals_partial_evidence_and_does_not_classify_complete(tmp_path: Path) -> None:
    run_dir = MeridianOutageHarness(EvidenceProvider(fail_on_call=3), RecordingAdapter()).run(
        output_root=tmp_path, run_id="provider-failure", condition="A_PRIVATE", n_agents=5,
    )
    result = verify_sealed_run(run_dir)
    assert result["run_status"] == "FAILED"
    assert result["model_call_evidence"]["logical_model_call_count_attempted"] == 3
    assert result["model_call_evidence"]["logical_model_call_count_succeeded"] == 2
    assert result["model_call_evidence"]["logical_model_call_count_failed"] == 1
    assert result["failure_ledger"][0]["logical_call_id"] == "round_1:researcher_003"
    assert result["failure_ledger"][0]["unexecuted_logical_call_count"] == 7
    raw = json.loads((run_dir / "raw_outputs.json").read_text(encoding="utf-8"))
    assert len(raw["provider_attempts"]) == 3
    assert raw["provider_attempts"][-1]["exception"]["type"] == "RuntimeError"
    assert raw["provider_attempts"][-1]["failure_stage"] == "provider_invocation"
    assert set(raw["round_outputs"]) == {"round_1:researcher_001", "round_1:researcher_002"}
    with pytest.raises(ResultVerificationError, match="not a completed experiment"):
        verify_sealed_run(run_dir, require_complete=True)


def test_schema_invalid_provider_response_seals_raw_text_and_one_attempt(tmp_path: Path) -> None:
    run_dir = MeridianOutageHarness(EvidenceProvider(invalid_on_call=2), RecordingAdapter()).run(
        output_root=tmp_path, run_id="schema-failure", condition="A_PRIVATE", n_agents=5,
    )
    result = verify_sealed_run(run_dir)
    raw = json.loads((run_dir / "raw_outputs.json").read_text(encoding="utf-8"))
    assert result["run_status"] == "FAILED"
    assert result["model_call_evidence"]["retry_count"] == 0
    assert len(raw["provider_attempts"]) == 2
    failed = raw["provider_attempts"][-1]
    assert failed["raw_response_text"] == "{not valid Meridian response}"
    assert failed["parser_schema_outcome"] == "failed"
    assert failed["failure_stage"] == "parser_schema"
    assert failed["usage"]["availability"] == "provider_reported"


def test_provider_default_sampling_and_unavailable_usage_are_attested_without_invention(tmp_path: Path) -> None:
    _, _, run_dir, result = _run_condition(tmp_path, "A_PRIVATE", "dry-defaults")
    assert result["provider"]["sampling"]["temperature"] == {
        "mode": "provider_default", "explicit_value": None,
    }
    raw = json.loads((run_dir / "raw_outputs.json").read_text(encoding="utf-8"))
    assert raw["provider_attempts"][0]["usage"] == {
        "availability": "unavailable", "input_tokens": None, "output_tokens": None, "total_tokens": None,
    }


def test_harness_preserves_per_agent_per_round_provider_boundary_without_transcripts(tmp_path: Path) -> None:
    provider = RecordingProvider()
    MeridianOutageHarness(provider, RecordingAdapter()).run(
        output_root=tmp_path, run_id="session-boundary", condition="A_PRIVATE", n_agents=5,
    )
    assert len(provider.calls) == 10
    assert all(set(call) == {
        "agent_id", "round", "assigned_cards", "collective_context", "naive_shared_findings", "instruction",
    } for call in provider.calls)
    assert all("transcript" not in call and "prior_response" not in call for call in provider.calls)


def test_provider_session_isolation_and_input_hash_boundaries_are_explicit(tmp_path: Path) -> None:
    runs: dict[str, Path] = {}
    for condition in (
        "A_PRIVATE", "B1_TORMENT_MECHANISMS_ONLY", "B2_TORMENT_SALIENCE_SURFACED", "C_NAIVE_SHARED_CONTENT",
    ):
        runs[condition] = MeridianOutageHarness(
            RecordingProvider(), RecordingAdapter({"recent_events": [{"event_id": "cev_hash"}], "event_count": 1}),
        ).run(output_root=tmp_path / condition, run_id=condition, condition=condition, n_agents=5)
    def records(condition: str) -> dict[str, dict[str, Any]]:
        raw = json.loads((runs[condition] / "raw_outputs.json").read_text(encoding="utf-8"))
        return {
            record["agent_id"]: record
            for record in raw["provider_attempts"] if record["round_number"] == 2
        }
    private = records("A_PRIVATE")
    b1 = records("B1_TORMENT_MECHANISMS_ONLY")
    b2 = records("B2_TORMENT_SALIENCE_SURFACED")
    naive = records("C_NAIVE_SHARED_CONTENT")
    for agent_id in private:
        private_hashes = private[agent_id]["request_metadata"]["input_hashes"]
        b1_hashes = b1[agent_id]["request_metadata"]["input_hashes"]
        b2_hashes = b2[agent_id]["request_metadata"]["input_hashes"]
        naive_hashes = naive[agent_id]["request_metadata"]["input_hashes"]
        assert private_hashes == b1_hashes
        assert {key: value for key, value in b2_hashes.items() if key not in {"collective_context_sha256", "provider_visible_input_sha256"}} == {
            key: value for key, value in private_hashes.items() if key not in {"collective_context_sha256", "provider_visible_input_sha256"}
        }
        assert b2_hashes["collective_context_sha256"] is not None
        assert {key: value for key, value in naive_hashes.items() if key not in {"naive_shared_findings_sha256", "provider_visible_input_sha256"}} == {
            key: value for key, value in private_hashes.items() if key not in {"naive_shared_findings_sha256", "provider_visible_input_sha256"}
        }
        assert naive_hashes["naive_shared_findings_sha256"] is not None


def test_provider_evidence_excludes_credentials_and_complete_failed_schemas_fail_closed(tmp_path: Path) -> None:
    complete_dir = MeridianOutageHarness(SecretMetadataProvider(), RecordingAdapter()).run(
        output_root=tmp_path, run_id="secret-free", condition="A_PRIVATE", n_agents=5,
    )
    failed_dir = MeridianOutageHarness(EvidenceProvider(fail_on_call=1), RecordingAdapter()).run(
        output_root=tmp_path, run_id="failed-schema", condition="A_PRIVATE", n_agents=5,
    )
    complete = verify_sealed_run(complete_dir)
    failed = verify_sealed_run(failed_dir)
    assert "must-not-be-sealed" not in (complete_dir / "raw_outputs.json").read_text(encoding="utf-8")
    for result in (complete, failed):
        malformed = dict(result)
        malformed.pop("run_status")
        with pytest.raises(ResultVerificationError, match="run_status"):
            validate_result_schema(malformed)


def test_external_seal_index_records_complete_and_failed_statuses(tmp_path: Path) -> None:
    MeridianOutageHarness(RecordingProvider(), RecordingAdapter()).run(
        output_root=tmp_path, run_id="complete-index", condition="A_PRIVATE", n_agents=5,
    )
    MeridianOutageHarness(EvidenceProvider(fail_on_call=1), RecordingAdapter()).run(
        output_root=tmp_path, run_id="failed-index", condition="A_PRIVATE", n_agents=5,
    )
    rows = [json.loads(line) for line in (tmp_path / SEAL_INDEX_FILENAME).read_text(encoding="utf-8").splitlines()]
    assert {row["run_id"]: row["run_status"] for row in rows} == {
        "complete-index": "COMPLETE", "failed-index": "FAILED",
    }


def test_cards_for_agent_are_fixed_and_do_not_expose_evaluator_fields() -> None:
    manifest = assignment_manifest(10)
    agent_id = sorted(manifest["assignments"])[0]
    cards = cards_for_agent(manifest, agent_id)
    assert [card["card_id"] for card in cards] == manifest["assignments"][agent_id]
    assert all("ground_truth_tags" not in card for card in cards)


class _MetricFabric:
    def __init__(self, root: Path) -> None:
        self.data_dir = str(root)
        self.private_graphs: dict[str, Any] = {}
        self._hivemind_enable = True
        self._hivemind_telemetry_enable = True
        shared = SimpleNamespace(data_dir=str(root / "shared"), entities={
            "promoted": SimpleNamespace(payload={"support_agents": ["a", "b", "a"]}),
        })
        self.workspace = SimpleNamespace(shared_graphs={"research": shared})
        self.field = SimpleNamespace(
            _packets_path=root / "packets.jsonl", _events_path=root / "events.jsonl",
            status=lambda: {"workspace_id": "metric", "packet_count_total": 0, "packet_count_cached": 0, "active_agents": []},
            recent_packets=lambda limit: [], recent_events=lambda limit: [],
        )

    def get_workspace(self, workspace_id: str, domains: Any = None) -> Any:
        return self.workspace

    def _get_collective_field(self, workspace_id: str) -> Any:
        return self.field

    def list_proposals(self, workspace_id: str, domain_id: str, status: str) -> Mapping[str, int]:
        return {"count": 0}


def test_shared_research_graph_metrics_use_shared_graphs_mapping(tmp_path: Path) -> None:
    root = tmp_path / "metric-root"
    (root / "shared").mkdir(parents=True)
    (root / "shared" / "graph.bin").write_bytes(b"promoted-shared-graph")
    fabric = _MetricFabric(root)
    adapter = TormentFabricAdapter(fabric)
    adapter._workspace_id = "metric"
    private_bytes, shared_bytes = adapter._graph_bytes()
    assert private_bytes == 0
    assert shared_bytes == len(b"promoted-shared-graph")
    metrics = adapter.mechanism_metrics()
    assert metrics["support_agents_per_promoted_node"] == [2]


def test_real_fabric_adapter_requires_fresh_root_and_observes_shared_graph_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "1")
    monkeypatch.setenv("TORMENT_HIVEMIND_TELEMETRY", "1")
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    fabric_root = tmp_path / "fabric"
    fabric = TormentFabric(data_dir=str(fabric_root))
    run_dir = MeridianOutageHarness(PromotingProvider(), TormentFabricAdapter(fabric, owns_fabric=True)).run(
        output_root=tmp_path / "results", run_id="real-fabric-dry", condition="B2_TORMENT_SALIENCE_SURFACED", n_agents=5,
    )
    result = verify_sealed_run(run_dir)
    assert result["cost_metrics"]["shared_graph_growth_bytes"] >= 0
    assert result["mechanism_metrics"]["workspace_isolation_check"]["field_workspace_matches_requested_workspace"] is True
    assert result["mechanism_metrics"]["proposals_promoted"] >= 1
    assert result["mechanism_metrics"]["support_agents_per_promoted_node"]
    assert result["environment"]["experimental_data_root"] == str(fabric_root.resolve())

    stale_root = tmp_path / "stale"
    stale_root.mkdir()
    (stale_root / "prior-state").write_text("not reusable", encoding="utf-8")
    stale_fabric = SimpleNamespace(
        data_dir=str(stale_root), _hivemind_enable=True, _hivemind_telemetry_enable=True,
    )
    with pytest.raises(ValueError, match="fresh and empty"):
        TormentFabricAdapter(stale_fabric).start(
            workspace_id="stale", agent_ids=["researcher_001"],
            config=ConditionConfig.for_condition("B1_TORMENT_MECHANISMS_ONLY"),
        )
