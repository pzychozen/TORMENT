"""Frozen Meridian Outage corpus, evaluator truth, and assignment manifests.

The agent view deliberately contains only source provenance and evidence text.
Evaluator-only truth lives in separate mappings and is never handed to a
provider by the harness.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any


EXPERIMENT_VERSION = "hivemind_meridian_outage_v1"
FROZEN_BASELINE_COMMIT = "6970ea70eae7decc52d4b073032505352929b75f"
ASSIGNMENT_SEED = "meridian-outage-v1-fixed-20260824"
VALID_N = (5, 10, 25)
VALID_CONDITIONS = (
    "A_PRIVATE",
    "B1_TORMENT_MECHANISMS_ONLY",
    "B2_TORMENT_SALIENCE_SURFACED",
    "C_NAIVE_SHARED_CONTENT",
)
PREREGISTRATION_CONDITION_NOTES = {
    "B1_TORMENT_MECHANISMS_ONLY": (
        "Round-2 provider input is byte-identical to A_PRIVATE apart from provider "
        "nondeterminism; B1 measures mechanisms and not collective cognition."
    ),
    "N5": (
        "Each participating agent holds exactly one decisive card; N=5 is mechanics "
        "characterization only, not minority-evidence or efficacy evidence."
    ),
}


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _card(card_id: str, source_id: str, source_tier: str, text: str) -> dict[str, str]:
    return {
        "card_id": card_id,
        "source_id": source_id,
        "source_tier": source_tier,
        "text": text,
    }


def _build_agent_cards() -> tuple[dict[str, str], ...]:
    cards: list[dict[str, str]] = []

    redundant_observations = (
        "The customer authentication error rate rose sharply between 14:03 and 14:08 UTC.",
        "A deployment record shows atlas-api rollout began at 14:02 UTC.",
        "Rollback of atlas-api was requested at 14:12 UTC after the outage was declared.",
        "Edge proxies reported TLS handshake failures while database latency stayed normal.",
        "The incident channel repeatedly linked the outage to the 14:02 deployment.",
        "The deployment dashboard marked atlas-api healthy before the rollback completed.",
    )
    # Source IDs and tiers are agent-visible but do not encode evaluator labels.
    # The corpus was corrected by adversarial audit before first administration.
    redundant_sources = (
        ("TIER_2", "gateway-log"),
        ("TIER_2", "operator-note"),
        ("TIER_3", "monitor-record"),
        ("TIER_2", "cert-service"),
        ("TIER_4", "chat-thread"),
        ("TIER_3", "deployment-console"),
    )
    for observation_index, observation in enumerate(redundant_observations, start=1):
        for copy_index, (tier, source_prefix) in enumerate(redundant_sources, start=1):
            card_id = f"R-{(observation_index - 1) * 6 + copy_index:03d}"
            cards.append(_card(
                card_id,
                f"{source_prefix}-{observation_index:02d}-{copy_index:02d}",
                tier,
                observation,
            ))

    misleading_cards = (
        "Release monitor: atlas-api version 2026.08.24.3 started rollout at 14:02 UTC; alert correlation attached this deployment to auth errors.",
        "Operator note: customers first reported login failures shortly after atlas-api rollout began.",
        "Change review: the deployment modified request middleware, a plausible location for authentication failures.",
        "Dashboard annotation: TLS failure volume increased on the same graph panel as the atlas-api rollout marker.",
        "Incident chat: the first working hypothesis was a regression in the 14:02 release.",
        "Release channel: a minor retry-policy change shipped with atlas-api at 14:02 UTC.",
        "Support handoff: several reports named the new atlas-api deployment as the likely trigger.",
        "Pager note: the active incident was automatically grouped under the most recent deployment.",
        "Status draft: rollback was prioritized because the deployment was the most visible recent change.",
        "Runbook excerpt: deploy-correlated auth failures are commonly investigated as application regressions.",
        "Timeline note: the deployment and the broad customer impact occurred within the same ten-minute interval.",
        "Canary report: atlas-api canaries passed their HTTP health endpoint after rollout began.",
        "Secondary analysis: the new middleware could theoretically alter service-to-service credentials.",
        "Change calendar: no other high-profile customer-facing deployment occurred at 14:02 UTC.",
        "Incident channel quote: 'the deploy is the only obvious change'.",
        "Release dashboard: rollback completion did not immediately clear all already-open browser sessions.",
        "Operations summary: deployment timing was treated as the leading causal clue during the first response hour.",
        "Service owner note: atlas-api was restarted by the rollout shortly before the incident declaration.",
        "Postmortem draft fragment: the authentication symptom was initially described as a deployment regression.",
        "Correlation job: assigned a high temporal-correlation score to the atlas-api change and the alert start.",
        "Operator chat: a configuration diff was requested because the application release looked suspicious.",
        "Release observer: version 2026.08.24.3 reached the final pod at 14:06 UTC.",
        "Triage note: no database or queue saturation was visible, increasing confidence in the deployment theory.",
        "Escalation log: the rollback decision cited timing, not a reproduced code defect.",
        "Incident recap: teams repeatedly referred to the event as the '14:02 deploy outage'.",
        "Secondary timeline: the deployment marker remained the most frequently cited event in incident discussion.",
    )
    misleading_sources = (
        "deployment-console", "operator-note", "monitor-record", "gateway-log",
        "chat-thread", "change-log",
    )
    for index, text in enumerate(misleading_cards, start=1):
        tier = "TIER_1" if index == 5 else "TIER_2" if index % 3 else "TIER_3"
        source = misleading_sources[(index - 1) % len(misleading_sources)]
        cards.append(_card(f"M-{index:03d}", f"{source}-{index:02d}", tier, text))

    decisive_cards = (
        "Signed certificate-issuer audit: at 13:45 UTC rotation published auth-client.pem with NotBefore=14:30 UTC and serial 7F-44.",
        "Edge proxy machine log: at 13:58 UTC, before atlas-api rollout, gateway-17 rejected auth-client.pem: certificate is not yet valid.",
        "Synthetic probe record: an old atlas-api image failed mTLS at 14:00 UTC with the same 'not yet valid' certificate error.",
        "Rotation control host journal: chrony was disabled during the 13:41 UTC control-plane migration; the signer clock was 26 minutes ahead.",
        "Recovery command transcript: rollback alone did not restore login; replacing auth-client.pem with the prior certificate did.",
    )
    decisive_sources = ("cert-service", "gateway-log", "monitor-record", "host-journal", "operator-note")
    decisive_tiers = ("TIER_2", "TIER_1", "TIER_2", "TIER_3", "TIER_2")
    for index, text in enumerate(decisive_cards, start=1):
        cards.append(_card(
            f"D-{index:03d}", f"{decisive_sources[index - 1]}-{index:02d}",
            decisive_tiers[index - 1], text,
        ))

    complementary_cards = (
        "Rotation service configuration: newly issued client certificates are written to the shared secret path without a NotBefore usability check.",
        "Migration checklist: time synchronization verification was marked manual after moving the rotation control host.",
        "Certificate policy: the intended validity window starts at issuance time; future-dated production client certificates are not permitted.",
        "Gateway configuration: all authentication handshakes trust the shared auth-client.pem secret distributed by rotation.",
        "Alert rule source: TLS handshake failures are annotated with the most recent deployment marker before certificate telemetry is shown.",
        "On-call runbook: certificate validity and signer clock checks are listed after application rollback checks.",
        "Rotation audit: the secret distributor updated gateway mounts at 13:57 UTC.",
        "Issuer health endpoint: process health remained green while wall-clock offset was outside the expected bound.",
        "Certificate validator test: staging rejects NotBefore values more than two minutes in the future; production rotation had no equivalent gate.",
        "Rollback record: atlas-api pods returned to the prior image, but gateway handshake errors continued.",
        "Time-service inventory: the migrated signer was missing its standard chrony unit enablement.",
        "Incident transcript: the first direct certificate error was initially treated as a downstream symptom of the deployment.",
        "Change-control note: certificate rotation was classified as routine maintenance and not correlated with the customer incident.",
        "Gateway metric definition: auth failures include certificate-validation failures and application authorization failures in the same aggregate.",
        "Recovery timeline: the prior certificate was restored at 14:24 UTC; authentication recovered immediately afterward.",
        "Security review: signed issuer audit records are generated from the signer host clock and certificate payload.",
        "Post-incident action draft: add clock-offset monitoring, issuance preflight, and certificate-specific alert routing.",
    )
    complementary_sources = (
        "cert-service", "operator-note", "change-log", "gateway-log", "monitor-record", "recovery-log",
    )
    for index, text in enumerate(complementary_cards, start=1):
        cards.append(_card(
            f"C-{index:03d}",
            f"{complementary_sources[(index - 1) % len(complementary_sources)]}-{index:02d}",
            "TIER_4" if index == 17 else "TIER_1" if index in (1, 4, 7, 8, 10, 15, 16) else "TIER_2",
            text,
        ))

    poison_cards = (
        "Unverified chat: a DNS provider outage caused every login failure; certificates were unaffected.",
        "Unverified chat: atlas-api intentionally disabled all TLS verification in the 14:02 release.",
        "Speculative note: database replication lag invalidated authentication sessions across the fleet.",
        "Anonymous paste: the certificate issuer was compromised and revoked all customer credentials.",
        "Rumor relay: a regional network partition isolated all gateways from the identity service.",
        "Unverified chat: the rollback failed because a hidden feature flag permanently blocked every user.",
    )
    poison_sources = ("chat-thread", "operator-note", "monitor-record", "vendor-note", "gateway-log", "change-log")
    poison_tiers = ("TIER_4", "TIER_3", "TIER_2", "TIER_4", "TIER_3", "TIER_2")
    for index, text in enumerate(poison_cards, start=1):
        cards.append(_card(
            f"P-{index:03d}", f"{poison_sources[index - 1]}-{index:02d}",
            poison_tiers[index - 1], text,
        ))

    neutral_topics = (
        "The analytics ETL completed its hourly aggregation at 14:05 UTC.",
        "A storage compaction job finished on the reporting cluster without errors.",
        "The billing API maintained normal latency throughout the incident window.",
        "A scheduled documentation publish ran at 13:50 UTC.",
        "The customer-status page cache refreshed at 14:10 UTC.",
        "An unrelated mobile release was approved for the following day.",
        "The data warehouse backup completed before the incident.",
        "Network packet loss between two analytics hosts stayed below one percent.",
        "A feature-flag cleanup ticket was opened but not deployed.",
        "The support queue received a routine password-reset request before the outage.",
        "A capacity report showed ordinary CPU usage on the search cluster.",
        "The log-retention job deleted expired debug archives at 14:04 UTC.",
        "A dashboard color-theme update was discussed in the operations channel.",
        "The internal wiki recorded a maintenance window for next week.",
        "A data-science notebook completed a scheduled batch experiment.",
        "The message queue consumer lag remained within its normal range.",
        "A staging environment certificate rotation succeeded earlier that morning.",
        "The customer export worker processed a normal batch at 14:06 UTC.",
        "A non-production test account failed a deliberately expired-password check.",
        "The finance reporting service changed no configuration during the incident.",
        "A cache warmup task completed on the recommendation service.",
        "The incident commander requested a routine status update at 14:15 UTC.",
        "An archive job copied old audit logs to cold storage.",
        "The API documentation build reported two broken internal links.",
        "A noncritical metrics exporter restarted after a configuration reload.",
        "The localization service published a normal translation bundle.",
        "A training cluster used elevated GPU capacity during the incident.",
        "The employee directory sync completed successfully.",
        "A routine vulnerability scan found no new critical issue.",
        "The incident room pinned the customer-impact statement at 14:18 UTC.",
    )
    neutral_sources = ("monitor-record", "operator-note", "gateway-log", "change-log", "chat-thread", "cert-service")
    for index, text in enumerate(neutral_topics, start=1):
        cards.append(_card(
            f"N-{index:03d}",
            f"{neutral_sources[(index - 1) % len(neutral_sources)]}-{index:02d}",
            "TIER_2" if index % 2 else "TIER_3",
            text,
        ))

    assert len(cards) == 120
    return tuple(cards)


AGENT_CARDS = _build_agent_cards()
CARD_IDS = tuple(card["card_id"] for card in AGENT_CARDS)


def _annotations() -> dict[str, dict[str, Any]]:
    annotations: dict[str, dict[str, Any]] = {}
    for card_id in CARD_IDS:
        if card_id.startswith("R-"):
            annotations[card_id] = {
                "ground_truth_tags": ["duplicate", "common_observation"],
                "is_relevant": True,
                "is_false": False,
                "causal_category": "context",
            }
        elif card_id.startswith("M-"):
            annotations[card_id] = {
                "ground_truth_tags": ["misleading_majority", "deployment_timing"],
                "is_relevant": False,
                "is_false": False,
                "causal_category": "misleading_common_interpretation",
            }
        elif card_id.startswith("P-"):
            annotations[card_id] = {
                "ground_truth_tags": ["poison"],
                "is_relevant": False,
                "is_false": True,
                "causal_category": "false_evidence",
            }
        elif card_id.startswith("N-"):
            annotations[card_id] = {
                "ground_truth_tags": ["neutral"],
                "is_relevant": False,
                "is_false": False,
                "causal_category": "distractor",
            }

    annotations.update({
        "D-001": {
            "ground_truth_tags": ["decisive", "future_dated_certificate"],
            "is_relevant": True,
            "is_false": False,
            "causal_category": "root_cause",
        },
        "D-002": {
            "ground_truth_tags": ["decisive", "pre_deploy_tls_failure"],
            "is_relevant": True,
            "is_false": False,
            "causal_category": "noncausal_deployment_timing",
        },
        "D-003": {
            "ground_truth_tags": ["decisive", "old_image_failure"],
            "is_relevant": True,
            "is_false": False,
            "causal_category": "noncausal_deployment_timing",
        },
        "D-004": {
            "ground_truth_tags": ["decisive", "signer_clock_skew"],
            "is_relevant": True,
            "is_false": False,
            "causal_category": "contributing_factor_clock_discipline",
        },
        "D-005": {
            "ground_truth_tags": ["decisive", "certificate_replacement_recovery"],
            "is_relevant": True,
            "is_false": False,
            "causal_category": "noncausal_deployment_timing",
        },
    })
    for card_id in tuple(card_id for card_id in CARD_IDS if card_id.startswith("C-")):
        index = int(card_id.split("-")[1])
        category = (
            "contributing_factor_preflight"
            if index in (1, 3, 9)
            else "contributing_factor_clock_discipline"
            if index in (2, 8, 11)
            else "contributing_factor_alerting"
            if index in (5, 6, 12, 14, 17)
            else "causal_chain"
        )
        annotations[card_id] = {
            "ground_truth_tags": ["complementary", category],
            "is_relevant": True,
            "is_false": False,
            "causal_category": category,
        }
    return annotations


EVALUATOR_ANNOTATIONS = _annotations()
GROUND_TRUTH: dict[str, Any] = {
    "primary_root_cause": {
        "id": "future_dated_auth_client_certificate",
        "description": (
            "A clock-skewed rotation signer issued and distributed an auth client "
            "certificate whose NotBefore time was in the future."
        ),
        "required_concepts": ["certificate", "not before", "clock"],
    },
    "required_contributing_factors": [
        {
            "id": "clock_discipline_missing_after_migration",
            "required_concepts": ["chrony", "clock", "migration"],
        },
        {
            "id": "rotation_preflight_missing",
            "required_concepts": ["rotation", "preflight", "not before"],
        },
        {
            "id": "deployment_anchored_alerting",
            "required_concepts": ["alert", "deployment", "certificate"],
        },
    ],
    "misleading_common_interpretation": "The 14:02 atlas-api deployment caused the outage.",
    "decisive_card_ids": ["D-001", "D-002", "D-003", "D-004", "D-005"],
    "poison_card_ids": [f"P-{index:03d}" for index in range(1, 7)],
}
FROZEN_GROUND_TRUTH_SHA256 = "1b1d76e383e02c4ba10a0d9ba5d023a453e16cc3025dab1c8848dfcf7d978993"


def agent_view() -> list[dict[str, str]]:
    """Return a defensive copy of the complete agent-visible corpus only."""
    return copy.deepcopy(list(AGENT_CARDS))


def evaluator_view() -> dict[str, Any]:
    """Return evaluator-only ground truth and annotations; never pass this to agents."""
    return copy.deepcopy({
        "ground_truth": GROUND_TRUTH,
        "annotations": EVALUATOR_ANNOTATIONS,
    })


def ground_truth_sha256() -> str:
    actual = payload_sha256({
        "ground_truth": GROUND_TRUTH,
        "annotations": EVALUATOR_ANNOTATIONS,
    })
    if actual != FROZEN_GROUND_TRUTH_SHA256:
        raise RuntimeError("frozen Meridian evaluator ground truth was changed")
    return actual


def _copy_count(card_id: str) -> int:
    if card_id.startswith("R-"):
        return 3
    if card_id.startswith("M-") or card_id.startswith("C-"):
        return 2
    return 1


def _assigned_agent_indexes(card_index: int, copies: int, n_agents: int) -> list[int]:
    """Fixed arithmetic allocation: no PRNG or runtime sampling is involved."""
    start = (card_index * 7 + 3) % n_agents
    return [((start + offset * 3) % n_agents) for offset in range(copies)]


def _build_manifest(n_agents: int) -> dict[str, Any]:
    if n_agents not in VALID_N:
        raise ValueError(f"N must be one of {VALID_N}, got {n_agents}")
    agent_ids = [f"researcher_{index:03d}" for index in range(1, n_agents + 1)]
    assignments = {agent_id: [] for agent_id in agent_ids}
    for card_index, card_id in enumerate(CARD_IDS):
        for agent_index in _assigned_agent_indexes(
            card_index, _copy_count(card_id), n_agents,
        ):
            assignments[agent_ids[agent_index]].append(card_id)
    for card_ids in assignments.values():
        card_ids.sort()
    return {
        "experiment_version": EXPERIMENT_VERSION,
        "assignment_seed": ASSIGNMENT_SEED,
        "n_agents": n_agents,
        "assignments": assignments,
    }


_FROZEN_MANIFESTS = {n_agents: _build_manifest(n_agents) for n_agents in VALID_N}
FROZEN_CORPUS_SHA256 = "347d2add8cf4ad14af1e8cbf2c361dc8694d90ff8f171f558bc95323134aa452"
FROZEN_MANIFEST_SHA256 = {
    5: "6960fb2799f0bd9e9b6bfe76c7bbb93abfc9f62b94b0b7717939fad99337c565",
    10: "10c7e8784164fcd1e174715189fdcb82c4acd52920e08d610a555507cdd89dd3",
    25: "3fdc90132e823e5ffb2c2e5e9553498c66647c90b6846c6c1e1958430dd3045d",
}


def assignment_manifest(n_agents: int) -> dict[str, Any]:
    """Return a defensive copy of the checked-in deterministic manifest."""
    if n_agents not in _FROZEN_MANIFESTS:
        raise ValueError(f"N must be one of {VALID_N}, got {n_agents}")
    return copy.deepcopy(_FROZEN_MANIFESTS[n_agents])


def assignment_manifest_sha256(n_agents: int) -> str:
    actual = payload_sha256(_FROZEN_MANIFESTS[n_agents])
    if actual != FROZEN_MANIFEST_SHA256[n_agents]:
        raise RuntimeError("frozen Meridian assignment manifest was changed")
    return actual


def cards_for_agent(manifest: Mapping[str, Any], agent_id: str) -> list[dict[str, str]]:
    card_lookup = {card["card_id"]: card for card in AGENT_CARDS}
    try:
        assigned_ids = manifest["assignments"][agent_id]
    except KeyError as exc:
        raise ValueError(f"agent {agent_id!r} is not in the assignment manifest") from exc
    return [copy.deepcopy(card_lookup[card_id]) for card_id in assigned_ids]


def corpus_sha256() -> str:
    actual = payload_sha256(list(AGENT_CARDS))
    if actual != FROZEN_CORPUS_SHA256:
        raise RuntimeError("frozen Meridian corpus was changed")
    return actual
