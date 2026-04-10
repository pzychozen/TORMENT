# cognition/router.py
"""
Deterministic Router — mode detection + role/aperture/constraint selection.

v0.1 uses keyword matching on user_input to classify mode.
No LLM calls, no learned weights. Must remain testable and predictable.

See docs/archive/AGENT_SPINE_PLAN.md §6 for the routing table and §15 for design decisions.

Routing table (v0.1):
  engineering  → [interpreter, engineer, skeptic, archivist], narrow,  drift=no
  strategic    → [interpreter, engineer, skeptic, archivist], broad,   drift=no
  identity     → [interpreter, skeptic, archivist],           protected, drift=yes
  auto         → falls through to engineering (safe default)
"""
from __future__ import annotations

import re
from typing import List, Optional

from cognition.task_models import (
    TaskPacket,
    RoutingDecision,
    MODE_AUTO,
    MODE_ENGINEERING,
    MODE_STRATEGIC,
    MODE_IDENTITY,
    APERTURE_NARROW,
    APERTURE_BROAD,
    APERTURE_PROTECTED,
    SCOPE_PRIVATE,
)


# ============================================================================
# Keyword banks for mode detection
# ============================================================================
# Each bank is a list of patterns (compiled as case-insensitive regexes).
# Patterns can be multi-word ("who am i") or single words.
# Order of checking: identity first (most restrictive), then strategic, then
# engineering. This ensures identity-sensitive requests are never misrouted.

_IDENTITY_PATTERNS: List[str] = [
    r"\bidentity\b",
    r"\brewrite\b",
    r"\bcore\b",
    r"\bseed\b",
    r"\bwho am i\b",
    r"\bcollective submission\b",
    r"\bchange personality\b",
    r"\bgovernance\b",
    r"\bdrift\b",
    r"\bpersona\b",
    r"\bself[- ]?concept\b",
    r"\bcharacter seed\b",
]

_STRATEGIC_PATTERNS: List[str] = [
    r"\bwhat should\b",
    r"\broadmap\b",
    r"\bdirection\b",
    r"\bfuture\b",
    r"\bnext step\b",
    r"\bbecome\b",
    r"\bevolve\b",
    r"\bstrategy\b",
    r"\blong[- ]?term\b",
    r"\bprioritize\b",
    r"\bwhat next\b",
    r"\bplanning\b",
]

_ENGINEERING_PATTERNS: List[str] = [
    r"\bimplement\b",
    r"\badd\b",
    r"\bfix\b",
    r"\bbuild\b",
    r"\bcode\b",
    r"\bcreate\b",
    r"\brefactor\b",
    r"\bmodule\b",
    r"\bendpoint\b",
    r"\bfunction\b",
    r"\bmethod\b",
    r"\bclass\b",
    r"\btest\b",
    r"\bdebug\b",
    r"\bpatch\b",
    r"\bfeature\b",
    r"\barchitect\b",
]

# Pre-compile all patterns
_IDENTITY_RE = [re.compile(p, re.IGNORECASE) for p in _IDENTITY_PATTERNS]
_STRATEGIC_RE = [re.compile(p, re.IGNORECASE) for p in _STRATEGIC_PATTERNS]
_ENGINEERING_RE = [re.compile(p, re.IGNORECASE) for p in _ENGINEERING_PATTERNS]


# ============================================================================
# Mode detection
# ============================================================================

def detect_mode(user_input: str) -> str:
    """Classify user input into a mode using keyword matching.

    Priority order (highest first):
      1. identity — most restrictive, must catch sensitive requests
      2. strategic — broader planning requests
      3. engineering — implementation/build requests
      4. auto fallback → treated as engineering at routing time

    Returns one of: MODE_IDENTITY, MODE_STRATEGIC, MODE_ENGINEERING, MODE_AUTO.
    """
    if not user_input or not user_input.strip():
        return MODE_AUTO

    text = user_input.strip()

    # Identity check first — highest priority
    for pat in _IDENTITY_RE:
        if pat.search(text):
            return MODE_IDENTITY

    # Strategic check second
    for pat in _STRATEGIC_RE:
        if pat.search(text):
            return MODE_STRATEGIC

    # Engineering check third
    for pat in _ENGINEERING_RE:
        if pat.search(text):
            return MODE_ENGINEERING

    # No keywords matched — auto
    return MODE_AUTO


# ============================================================================
# Route table
# ============================================================================

# Roles activated per mode
_ROLES_ENGINEERING = ["interpreter", "engineer", "skeptic", "archivist"]
_ROLES_STRATEGIC = ["interpreter", "engineer", "skeptic", "archivist"]
_ROLES_IDENTITY = ["interpreter", "skeptic", "archivist"]

# Route table: mode → (roles, aperture, drift_check, skeptic_pass)
_ROUTE_TABLE = {
    MODE_ENGINEERING: (_ROLES_ENGINEERING, APERTURE_NARROW, False, False),
    MODE_STRATEGIC:   (_ROLES_STRATEGIC,   APERTURE_BROAD,  False, False),
    MODE_IDENTITY:    (_ROLES_IDENTITY,    APERTURE_PROTECTED, True, True),
}


def route(task: TaskPacket, primary_domains: Optional[List[str]] = None) -> RoutingDecision:
    """Produce a RoutingDecision from a TaskPacket.

    1. Resolve effective mode (if task.mode is 'auto', detect from user_input).
    2. Look up route table for roles, aperture, drift/skeptic flags.
    3. Build and return RoutingDecision.

    Parameters
    ----------
    task : TaskPacket
        The incoming request.
    primary_domains : list[str], optional
        Domain ranking from fabric.query(). Defaults to empty list.

    Returns
    -------
    RoutingDecision
    """
    if primary_domains is None:
        primary_domains = []

    # Resolve effective mode
    effective_mode = task.mode
    if effective_mode == MODE_AUTO:
        effective_mode = detect_mode(task.user_input)
    # If still auto after detection (no keywords matched), default to engineering
    if effective_mode == MODE_AUTO:
        effective_mode = MODE_ENGINEERING

    roles, aperture, drift_check, skeptic_pass = _ROUTE_TABLE[effective_mode]

    return RoutingDecision(
        roles_to_activate=list(roles),  # copy so caller can't mutate table
        primary_domains=list(primary_domains),
        aperture=aperture,
        archival_scope=SCOPE_PRIVATE,
        require_skeptic_pass=skeptic_pass,
        require_drift_check=drift_check,
        require_archival_review=True,  # always true in v0.1
    )
