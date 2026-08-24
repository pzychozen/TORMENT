"""Deterministic structural-proxy scoring for Meridian Outage outputs."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from .spec import EVALUATOR_ANNOTATIONS, GROUND_TRUTH


VALID_CLAIM_STANCES = frozenset({"asserts", "refutes", "mentions"})


def _normalise(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _contains_required_concepts(text: object, required_concepts: Iterable[str]) -> bool:
    normalised = _normalise(text)
    return all(_normalise(concept) in normalised for concept in required_concepts)


def _string_list(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _claims(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    claims: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        claim = dict(item)
        stance = claim.get("stance", "asserts")
        if stance not in VALID_CLAIM_STANCES:
            raise ValueError(f"invalid deterministic claim stance: {stance!r}")
        claim["stance"] = stance
        claims.append(claim)
    return claims


def score_final_answer(
    final_answer: Mapping[str, Any],
    *,
    available_card_ids: Iterable[str],
) -> dict[str, Any]:
    """Score one answer with deterministic proxies, never a semantic judge."""
    cited_card_ids = set(_string_list(final_answer.get("cited_card_ids")))
    root = GROUND_TRUTH["primary_root_cause"]
    root_match = _contains_required_concepts(
        final_answer.get("root_cause", ""), root["required_concepts"],
    )

    factor_text = " ".join(_string_list(final_answer.get("contributing_factors")))
    factor_recall = sum(
        _contains_required_concepts(factor_text, factor["required_concepts"])
        for factor in GROUND_TRUTH["required_contributing_factors"]
    )

    decisive_ids = set(GROUND_TRUTH["decisive_card_ids"])
    decisive_recovered = sorted(cited_card_ids & decisive_ids)
    available = set(available_card_ids)
    available_relevant = {
        card_id
        for card_id in available
        if EVALUATOR_ANNOTATIONS[card_id]["is_relevant"]
    }
    cited_relevant = cited_card_ids & available_relevant
    coverage = len(cited_relevant) / len(available_relevant) if available_relevant else 0.0
    completeness = int(root_match) + factor_recall + int(set(decisive_recovered) == decisive_ids)

    return {
        "root_cause_concept_match": int(root_match),
        "contributing_factor_concept_recall": factor_recall,
        "decisive_evidence_recovery": {
            "recovered_card_ids": decisive_recovered,
            "recovered_count": len(decisive_recovered),
            "complete_chain": set(decisive_recovered) == decisive_ids,
        },
        "relevant_evidence_coverage": {
            "cited_relevant_card_ids": sorted(cited_relevant),
            "available_relevant_card_count": len(available_relevant),
            "fraction": coverage,
        },
        "deterministic_task_proxy": {
            "score_0_to_5": completeness,
            "root_cause_concept_match": root_match,
            "contributing_factor_concept_count": factor_recall,
            "complete_decisive_chain": set(decisive_recovered) == decisive_ids,
            "limitations": (
                "Keyword concept matching, contributor recall, and citation support are "
                "structural proxies; they do not prove correctness, causality, or entailment."
            ),
        },
    }


def score_claim_provenance(
    claims_by_agent: Mapping[str, Iterable[Mapping[str, Any]]],
    findings_by_agent: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    assignments: Mapping[str, Iterable[str]],
) -> dict[str, Any]:
    """Score provenance; duplicate work is independent card discovery, not copied text."""
    known_card_ids = set(EVALUATOR_ANNOTATIONS)
    card_holders: dict[str, set[str]] = defaultdict(set)
    for agent_id, card_ids in assignments.items():
        for card_id in card_ids:
            card_holders[str(card_id)].add(agent_id)

    total_claims = asserted_claims = supported_claims = provenance_claims = false_claims = 0
    cited_by_card: dict[str, set[str]] = defaultdict(set)
    exact_claim_signatures: Counter[tuple[str, tuple[str, ...]]] = Counter()
    poison_propagated: dict[str, set[str]] = defaultdict(set)
    out_of_assignment_citations: list[dict[str, str]] = []

    for agent_id, raw_claims in claims_by_agent.items():
        for claim in _claims(list(raw_claims)):
            total_claims += 1
            stance = claim["stance"]
            asserted_claims += int(stance == "asserts")
            text = str(claim.get("text", ""))
            card_ids = _string_list(claim.get("card_ids"))
            valid_card_ids = [card_id for card_id in card_ids if card_id in known_card_ids]
            if valid_card_ids:
                provenance_claims += 1
            if card_ids and set(card_ids).issubset(known_card_ids):
                supported_claims += 1
            if stance == "asserts" and any(
                EVALUATOR_ANNOTATIONS[card_id]["is_false"] for card_id in valid_card_ids
            ):
                false_claims += 1
            exact_claim_signatures[(_normalise(text), tuple(sorted(valid_card_ids)))] += 1
            for card_id in valid_card_ids:
                cited_by_card[card_id].add(agent_id)
                if agent_id not in card_holders[card_id]:
                    out_of_assignment_citations.append({"agent_id": agent_id, "card_id": card_id})
                if (
                    stance == "asserts"
                    and EVALUATOR_ANNOTATIONS[card_id]["is_false"]
                    and agent_id not in card_holders[card_id]
                ):
                    poison_propagated[card_id].add(agent_id)

    discoveries_by_card: dict[str, set[str]] = defaultdict(set)
    for agent_id, findings in findings_by_agent.items():
        for finding in findings:
            if not isinstance(finding, Mapping):
                continue
            for card_id in _string_list(finding.get("card_ids")):
                if card_id in known_card_ids:
                    discoveries_by_card[card_id].add(agent_id)
    discovery_multiplicity = {
        card_id: len(agent_ids) for card_id, agent_ids in sorted(discoveries_by_card.items())
    }
    duplicate_work = sum(max(0, count - 1) for count in discovery_multiplicity.values())
    exact_text_duplicate_diagnostic = sum(
        count - 1 for count in exact_claim_signatures.values() if count > 1
    )
    poison_cited = {
        card_id: sorted(agent_ids)
        for card_id, agent_ids in cited_by_card.items()
        if EVALUATOR_ANNOTATIONS[card_id]["is_false"]
    }
    return {
        "claim_count": total_claims,
        "asserted_claim_count": asserted_claims,
        "card_discovery_multiplicity": discovery_multiplicity,
        "duplicate_work_count": duplicate_work,
        "exact_text_duplicate_diagnostic": exact_text_duplicate_diagnostic,
        "false_assertion_rate": false_claims / asserted_claims if asserted_claims else 0.0,
        "unsupported_claim_rate": 1.0 - (supported_claims / total_claims) if total_claims else 0.0,
        "provenance_retention": provenance_claims / total_claims if total_claims else 0.0,
        "poison_evidence_inheritance": {
            "poison_cards_cited_any_stance": poison_cited,
            "propagated_beyond_initial_holders_by_assertion": {
                card_id: sorted(agent_ids)
                for card_id, agent_ids in poison_propagated.items()
            },
        },
        "out_of_assignment_citations": out_of_assignment_citations,
    }


def score_run(
    agent_final_answers: Mapping[str, Mapping[str, Any]],
    deterministic_union_answer: Mapping[str, Any],
    claims_by_agent: Mapping[str, Iterable[Mapping[str, Any]]],
    findings_by_agent: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    assignments: Mapping[str, Iterable[str]],
) -> dict[str, Any]:
    """Report individual task proxies separately from population-only union metrics."""
    individual_scores = {
        agent_id: score_final_answer(answer, available_card_ids=assignments[agent_id])
        for agent_id, answer in sorted(agent_final_answers.items())
    }
    ranked = sorted(
        (
            metrics["deterministic_task_proxy"]["score_0_to_5"],
            agent_id,
            metrics,
        )
        for agent_id, metrics in individual_scores.items()
    )
    best_score, best_agent_id, best_metrics = ranked[-1] if ranked else (0, None, {})
    mean_score = (
        sum(metrics["deterministic_task_proxy"]["score_0_to_5"] for metrics in individual_scores.values())
        / len(individual_scores)
        if individual_scores else 0.0
    )
    available_card_ids = {
        card_id for card_ids in assignments.values() for card_id in card_ids
    }
    population_cited = sorted({
        card_id
        for answer in agent_final_answers.values()
        for card_id in _string_list(answer.get("cited_card_ids"))
    })
    population_coverage = score_final_answer(
        {"cited_card_ids": population_cited}, available_card_ids=available_card_ids,
    )["relevant_evidence_coverage"]
    union_metrics = score_final_answer(
        deterministic_union_answer, available_card_ids=available_card_ids,
    )
    scores = {
        "best_agent_score": {
            "agent_id": best_agent_id,
            "score_0_to_5": best_score,
            "metrics": best_metrics,
        },
        "mean_agent_score": mean_score,
        "per_agent_scores": individual_scores,
        "population_evidence_coverage": population_coverage,
        "deterministic_union_score": {
            "labels": [
                "ORACLE-LIKE POPULATION UPPER BOUND",
                "NOT AN AGENT ANSWER",
                "NOT COLLECTIVE COGNITION",
            ],
            "metrics": union_metrics,
        },
    }
    scores.update(score_claim_provenance(
        claims_by_agent, findings_by_agent, assignments=assignments,
    ))
    return scores
