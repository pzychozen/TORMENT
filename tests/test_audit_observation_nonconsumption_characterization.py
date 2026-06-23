"""Characterization: audit-like observation non-consumption / non-honoring.

TESTS-ONLY characterization. This file touches NO production code, creates NO
audit artifact, names NO audit field/schema/endpoint, makes NO model call, and
selects NO runtime path. All assertions are NEGATIVE: they characterize that an
audit-LIKE observation value would not be consumed or silently honored by the
runtime, using existing precedents/canaries.

Core line (the property being characterized, not crossed):
  No audit artifact / value / flag / summary / score / prompt / model output /
  trace / derived signal may be read by, passed into, stored for, or honored by
  any runtime path outside debug/operator observation.

Precedent (named, not built on): `ReflectionTrace` (torment_service/reflection_trace.py)
already demonstrates an ephemeral, content-free, non-reentrant observation surface
with no runtime consumer. It is cited as the precedent that this property is
provable in-repo; this file does NOT imply "the future audit is ReflectionTrace,"
does NOT reuse ReflectionTrace, and proposes NO audit-trace field.

Anti-pattern (named, by negative comparison only): `srg.is_crystal` is a payload
key that runtime readers DO silently honor (lifecycle protected-derivation marks
such a row PROTECTED). It is referenced ONLY as the anti-pattern an audit-like
value must never become. This file does not alter, revalidate, or reopen SRG /
R-field behavior; it only compares against it negatively.

Codex correction honored: this file does NOT assert "forbidden runtime modules do
not import observation-only modules" (a blanket import rule). Some modules may
legitimately import observation types to construct or surface them. The locked
property is that forbidden runtime paths do not READ / HONOR / BRANCH-ON / PASS /
PERSIST / CONSUME an observation-like value — characterized here behaviorally.

The key below is a TEST-ONLY SENTINEL/CANARY. It is deliberately non-canonical and
is NOT a proposed schema field.
"""

import shutil
import tempfile
import unittest

from torment_service.lifecycle import derive_protected_lifecycle_from_legacy_markers
from torment_service.fabric import TormentFabric


# A deliberately non-canonical, test-only sentinel standing in for an
# "audit-like observation" payload key. NOT a schema field; NOT production-ready.
OBSERVATION_CANARY_KEY = "__observation_like_canary__test_only__not_a_schema_field__"


class TestObservationLikePayloadKeyNotSilentlyHonored(unittest.TestCase):
    """Group B — an unknown observation-like payload key must NOT become a
    protected / canon / admission / promotion / lifecycle signal.

    Proven by NEGATIVE COMPARISON to the named anti-pattern `srg.is_crystal`,
    which the lifecycle protected-derivation DOES silently honor.
    """

    # -- anti-pattern reference (documents what "silently honored" looks like) --
    def test_srg_is_crystal_is_the_named_honored_antipattern(self):
        # Reference point only: a payload key that IS silently honored → PROTECTED.
        # Named as the anti-pattern; SRG/R-field behavior is not reopened here.
        env = derive_protected_lifecycle_from_legacy_markers(
            {"srg": {"is_crystal": True}}, now=0
        )
        self.assertIsNotNone(
            env,
            msg="reference anti-pattern: srg.is_crystal is expected to be honored",
        )

    # -- negative characterizations (the property this file locks) --
    def test_observation_like_top_level_key_not_honored(self):
        env = derive_protected_lifecycle_from_legacy_markers(
            {OBSERVATION_CANARY_KEY: True}, now=0
        )
        self.assertIsNone(
            env,
            msg="an observation-like top-level payload key must not be honored",
        )

    def test_observation_like_key_inside_srg_not_honored(self):
        # An observation-like key sitting inside the srg dict, WITHOUT is_crystal,
        # must not be honored (only is_crystal is).
        env = derive_protected_lifecycle_from_legacy_markers(
            {"srg": {OBSERVATION_CANARY_KEY: True}}, now=0
        )
        self.assertIsNone(env)

    def test_observation_like_key_inside_governance_not_honored(self):
        # Only governance.protected is honored; an observation-like key is not.
        env = derive_protected_lifecycle_from_legacy_markers(
            {"governance": {OBSERVATION_CANARY_KEY: True}}, now=0
        )
        self.assertIsNone(env)

    def test_observation_like_key_alongside_false_crystal_not_honored(self):
        env = derive_protected_lifecycle_from_legacy_markers(
            {OBSERVATION_CANARY_KEY: True, "srg": {"is_crystal": False}}, now=0
        )
        self.assertIsNone(env)


class TestObservationLikeKeyNotConsumedByRetrievalScoring(unittest.TestCase):
    """Group A — an observation-like payload key is NOT consumed by retrieval
    scoring: the same disposable memory scores the same WITH and WITHOUT the
    sentinel (paired control).

    Behavioral, not an import scan. The claim is limited to retrieval-SCORING
    nonconsumption. It deliberately does NOT claim the sentinel is absent from
    all model-visible query output, because ``MemoryGraph.search()`` may spread
    payload keys into hits even when they are not scored.

    Robustness note: query-path reinforcement is a read-only boost over a stable
    ``reinforcement_count`` (the mutating duplicate-suppression reinforcement is
    ingest-time only), and SRG/warmup mutation does not apply to an ordinary
    private hit with SRG default-off — so two identical queries on the same
    memory are score-stable apart from sub-second recency noise.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_audit_nonconsume_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @staticmethod
    def _find_hit(result, eid):
        results = result.get("results", [])
        for h in results:
            if int(h.get("eid", -1)) == eid:
                return h
        return results[0] if results else None

    def test_sentinel_does_not_change_retrieval_score_paired_control(self):
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="A memory about coffee and quiet mornings", step=10,
        )
        eid = int(r["eid"])
        query_text = "coffee and quiet mornings"

        # Baseline: retrieval score WITHOUT the sentinel.
        q0 = self.fabric.query(
            workspace_id="ws", agent_id="agent",
            query_text=query_text, top_k=20, explain=True,
        )
        hit0 = self._find_hit(q0, eid)
        self.assertIsNotNone(hit0, "baseline query returned no hit")
        score_without = float(hit0["final_score"])

        # Inject the test-only sentinel directly onto the SAME stored payload.
        ak = self.fabric._agent_key("ws", "agent")
        ent = self.fabric.private_graphs.get(ak).entities.get(eid)
        self.assertIsNotNone(ent)
        ent.payload[OBSERVATION_CANARY_KEY] = "canary"

        # Paired control: retrieval score WITH the sentinel on the same memory.
        q1 = self.fabric.query(
            workspace_id="ws", agent_id="agent",
            query_text=query_text, top_k=20, explain=True,
        )
        hit1 = self._find_hit(q1, eid)
        self.assertIsNotNone(hit1, "paired query returned no hit")
        score_with = float(hit1["final_score"])

        # PRIMARY: retrieval scoring is unchanged by the observation-like key.
        # (delta absorbs sub-second recency noise; real consumption would move
        # the score far more than this.)
        self.assertAlmostEqual(
            score_with, score_without, delta=1e-3,
            msg="observation-like payload key must not change retrieval score",
        )

        # SUPPLEMENTARY hygiene only (NOT the main proof): the key is not named
        # as a scoring component in the explain decomposition.
        self.assertNotIn(OBSERVATION_CANARY_KEY, hit1.get("explain", {}))


if __name__ == "__main__":
    unittest.main()
