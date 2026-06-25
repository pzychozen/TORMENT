"""Gate A Layer 4 — inert candidate representation type (first containment brick).

``CandidateShapedValue`` is the smallest production realization of the selected
constrained **A + D** candidate-representation principle:

  * **A — distinct non-ordinary TYPE boundary.** It is not a ``str`` / ``bytes`` /
    mapping, so ordinary ingest and ordinary write paths cannot accept it as
    ordinary memory input by mistaking it for ordinary text.
  * **D — sealed / opaque VALUE.** The wrapped value lives in a private slot with
    no public accessor, no ``to_dict``, no iteration, no item access, and a
    contents-free ``__repr__`` — so ordinary code cannot read or reinterpret the
    contents as ordinary input.

**INERT BY CONSTRUCTION.** This type has NO producer, NO store, NO governed
admission, NO promotion, NO serialization, and NO persistence behavior. Nothing
in production constructs it; it exists only so the ordinary-ingest boundary has a
structural thing to refuse, and so tests can construct one. It imports nothing
from the TORMENT package (dependency-free) to avoid any import cycle.

**This module is not wall completion.** The ordinary-ingest deny check that
refuses this type covers only the ``text`` parameter; the non-text ingest
parameters (``supplied_summary``, ``extra_payload``, ``supplied_embedding``,
``provenance``, ...) and the known direct-writer bypasses remain UNRESOLVED and
out of scope.
"""

__all__ = ["CandidateShapedValue"]


class CandidateShapedValue:
    """Sealed, opaque, distinct non-ordinary candidate-shaped value.

    Holds exactly one opaque value in a private slot. Exposes no accessor, no
    serialization, no iteration, and no item access; ``__repr__`` never reveals
    the contents. This is a structural marker only — it carries no behavior that
    could move, store, admit, or promote anything.
    """

    __slots__ = ("_sealed",)

    def __init__(self, value=None):
        # The wrapped value is sealed: stored privately, never exposed by this
        # type. No public accessor is provided, by design.
        self._sealed = value

    def __repr__(self):
        # Contents-free: type identity only, never the wrapped value.
        return "<CandidateShapedValue sealed>"
