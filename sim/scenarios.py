from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
import random

DEFAULT_DOMAINS = ["research","engineering","operations","creative","meta"]

@dataclass
class ScenarioEvent:
    domain_hint: str
    text: str
    kind: str  # "fact"|"project"|"episode" etc.

class BaseScenario:
    name: str = "base"
    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def stream(self, steps: int) -> Iterable[ScenarioEvent]:
        raise NotImplementedError

class ResearchHeavy(BaseScenario):
    name = "research_heavy"
    TOPICS = [
        "Tri-Octa kernel gating",
        "SRG stability surfaces",
        "motif corridor alignment",
        "parameter sweeps and runaway fractions",
        "phase triad synchronization",
        "domain partitioning and bridge governance",
    ]
    def stream(self, steps: int):
        for i in range(steps):
            topic = self.rng.choice(self.TOPICS)
            text = f"[Research log #{i}] Working on {topic}. Found a new invariant-like pattern and want to store a distilled summary."
            yield ScenarioEvent(domain_hint="research", text=text, kind="episode")

class OpsHeavy(BaseScenario):
    name = "ops_heavy"
    TASKS = [
        "backup the workspace data directory",
        "rotate logs and prune stale proposals",
        "review bridge queue and approve only high-confidence",
        "run golden tests and export metrics",
        "update domain policies for meta/ops to be conservative",
    ]
    def stream(self, steps: int):
        for i in range(steps):
            task = self.rng.choice(self.TASKS)
            text = f"[Ops #{i}] TODO: {task}. Record the checklist outcome and any warnings."
            yield ScenarioEvent(domain_hint="operations", text=text, kind="task")

class CreativeChaos(BaseScenario):
    name = "creative_chaos"
    SEEDS = [
        "island covered in flowers, abandoned research facility",
        "dark villain anthem chorus concept",
        "a memory fabric that dreams",
        "collective kernel as a storm field",
        "glyph recursion as language",
    ]
    def stream(self, steps: int):
        for i in range(steps):
            seed = self.rng.choice(self.SEEDS)
            twist = self.rng.choice(["make it quieter", "make it cinematic", "make it absurd", "make it tender", "make it terrifying"])
            text = f"[Creative #{i}] Idea: {seed}. Variation: {twist}. Capture motifs and links."
            yield ScenarioEvent(domain_hint="creative", text=text, kind="idea")



class EngineeringHeavy(BaseScenario):
    name = "engineering_heavy"
    ISSUES = [
        "fixing sim export path binding",
        "adding pytest regression tests",
        "optimizing vector search scoring",
        "repairing indentation and method scoping bugs",
        "implementing event sourcing for proposals and canon",
    ]
    def stream(self, steps: int):
        for i in range(steps):
            issue = self.rng.choice(self.ISSUES)
            text = f"[Eng #{i}] Debug/Build: {issue}. Patch, run tests, and store the resolution summary."
            yield ScenarioEvent(domain_hint="engineering", text=text, kind="task")

class MetaHeavy(BaseScenario):
    name = "meta_heavy"
    TOPICS = [
        "domain policy defaults and governance",
        "conflict-aware scoring rules",
        "privacy boundaries: private-write/shared-read",
        "bridge approval workflow in strict domains",
        "deterministic replay lock and golden emergent tests",
    ]
    def stream(self, steps: int):
        for i in range(steps):
            topic = self.rng.choice(self.TOPICS)
            text = f"[Meta #{i}] Policy/Rules: {topic}. Specify constraints and acceptance criteria."
            yield ScenarioEvent(domain_hint="meta", text=text, kind="policy")

class CollaborativeMixed200(BaseScenario):
    """Balanced domain stream designed to activate shared proposals in large-agent runs."""
    name = "collaborative_mixed_200"
    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self.scenarios = [
            ResearchHeavy(seed+1),
            EngineeringHeavy(seed+2),
            OpsHeavy(seed+3),
            CreativeChaos(seed+4),
            MetaHeavy(seed+5),
        ]
        # deterministic round-robin domain emphasis with mild randomness
        self._idx = 0

    def stream(self, steps: int):
        for i in range(steps):
            # round-robin across the 5 scenario streams to ensure domain diversity
            sc = self.scenarios[self._idx % len(self.scenarios)]
            self._idx += 1
            ev = next(sc.stream(1))
            # Occasionally inject a cross-domain "bridge-like" phrasing
            if i % 10 == 0:
                ev = ScenarioEvent(
                    domain_hint=ev.domain_hint,
                    text=ev.text + " (Cross-domain note: link this to related motifs in other domains if useful.)",
                    kind=ev.kind
                )
            yield ev


class Mixed(BaseScenario):
    name = "mixed"
    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self.scenarios = [ResearchHeavy(seed+1), OpsHeavy(seed+2), CreativeChaos(seed+3)]
    def stream(self, steps: int):
        for i in range(steps):
            sc = self.rng.choice(self.scenarios)
            ev = next(sc.stream(1))
            yield ev

SCENARIOS = {
    "research": ResearchHeavy,
    "ops": OpsHeavy,
    "creative": CreativeChaos,
    "mixed": Mixed,
    "engineering": EngineeringHeavy,
    "meta": MetaHeavy,
    "collaborative_mixed_200": CollaborativeMixed200,
}
