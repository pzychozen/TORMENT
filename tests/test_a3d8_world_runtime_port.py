"""A3D8 backend-neutral world-runtime port qualification."""
from __future__ import annotations

from torment_service.world_runtime import LegacyWorldRuntime


def test_legacy_world_port_delegates_to_the_selected_graph_with_frozen_arguments() -> None:
    class Graph:
        calls: list[tuple[int, int, int]] = []

        def step_world(self, *, step: int, classify_every: int, log_every: int) -> None:
            self.calls.append((step, classify_every, log_every))

    graph = Graph()
    LegacyWorldRuntime(graph).advance_for_post_write(step=50)
    assert graph.calls == [(50, 50, 1)]
