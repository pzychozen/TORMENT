"""tests/test_dream_inert_staging_boundary_non_authorization.py

Dream inert-staging boundary NON-AUTHORIZATION guard — tests-only,
source/AST characterization.

This file COMPLEMENTS, and deliberately does NOT duplicate,
``tests/test_regime_b_dream_absence_characterization.py``, which OWNS the
dream / incubation / chamber / Regime-B *runtime / scheduler / entrypoint*
absence surface (no dream module/class/def, no scheduler library, no asyncio
background task, no dream-scoped thread / ``while True``, no dream wiring in
``app.py`` / ``spine.py`` / ``agent_loop.py`` / ``mcp_server.py``). This guard
does not re-assert any of that.

It is narrowly scoped to the **inert-staging boundary non-authorization**
concern established by the Dream-readiness / inert-staging boundary frame
(``docs/TORMENT_DREAM_READINESS_INERT_STAGING_BOUNDARY_FRAME_v0.1.md``). It
proves, by source + AST scan (no production import, no execution):

  1. No NON-dream-named inert-staging **store / producer** surface exists in
     production *names* — the compound nouns the dream-token matcher would miss
     (``staging_store`` / ``candidate_store`` / ``footprint_store`` /
     ``dream_producer`` / ``incubation_producer`` / ``incubation_loop`` /
     ``chamber_store`` / ``chamber_runtime``).
  2. The Dream-readiness inert-staging boundary frame exists as a **docs-only,
     NON-authorizing** artifact (carries its verdict / non-authorization anchor).
  3. Production modules do **not** import the boundary doc or otherwise treat it
     as runtime input.
  4. The matcher has **teeth** (flags synthetic forbidden names).
  5. The matcher does **not** false-positive on existing benign candidate
     vocabulary (``CandidateShapedValue`` / ``candidate_types`` /
     ``CompressionCandidate``).

Scope: tests-only. Source/AST scan only — no production import, no execution,
no production code change. OPENS NOTHING: it builds no dream material, producer,
store, chamber, runtime, scheduler, memory write, admission mechanism,
model/provider path, or wiring; it only asserts **absence / non-authorization**.
It is an anti-drift floor, NOT a gate and NOT a design decision, and it does not
forbid a future separately-authorized producer.
"""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SERVICE_DIR = _REPO / "torment_service"
_DOCS_DIR = _REPO / "docs"

_BOUNDARY_DOC_NAME = "TORMENT_DREAM_READINESS_INERT_STAGING_BOUNDARY_FRAME_v0.1.md"
_BOUNDARY_DOC = _DOCS_DIR / _BOUNDARY_DOC_NAME

# Compound inert-staging store/producer nouns. NARROW by design: a
# staging/footprint/candidate/chamber/dream/incubation QUALIFIER must be fused
# (optionally with one "_"/" ") to a store/producer/loop/runtime noun. Bare
# "candidate" / "store" / "staging" — which appear in benign production names
# (CandidateShapedValue, ReferenceStore, ...) and in comments — must NOT match.
_FORBIDDEN_NAME_RE = re.compile(
    r"(?:staging|footprint|candidate|chamber|dream|incubation)"
    r"[_ ]?"
    r"(?:store|producer|loop|runtime)",
    re.I,
)


def _read(path: Path) -> str:
    # utf-8-sig tolerates the BOM some kernel/*.py files carry.
    return path.read_text(encoding="utf-8-sig")


def _prod_files():
    return sorted(p for p in _SERVICE_DIR.rglob("*.py"))


def _prod_trees():
    return [(p, ast.parse(_read(p), filename=p.name)) for p in _prod_files()]


# --- reusable detectors (shared by the production scan and the teeth test) ---

def _forbidden_named_defs(tree: ast.AST):
    """class/def/async-def names that look like an inert-staging store/producer."""
    return sorted(
        n.name for n in ast.walk(tree)
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and _FORBIDDEN_NAME_RE.search(n.name)
    )


def _forbidden_module_stems(files):
    return sorted(p.stem for p in files if _FORBIDDEN_NAME_RE.search(p.stem))


# ---------------------------------------------------------------------------
# 1. No non-dream-named inert-staging store/producer surface in production names
# ---------------------------------------------------------------------------

class TestNoInertStagingStoreOrProducerSurface(unittest.TestCase):
    def test_no_production_module_named_for_inert_staging_store(self):
        offenders = _forbidden_module_stems(_prod_files())
        self.assertEqual(
            offenders, [],
            f"inert-staging store/producer-named production module(s): {offenders!r}",
        )

    def test_no_production_class_or_def_named_for_inert_staging_store(self):
        offenders = {}
        for p, tree in _prod_trees():
            names = _forbidden_named_defs(tree)
            if names:
                offenders[str(p.relative_to(_REPO))] = names
        self.assertEqual(
            offenders, {},
            f"inert-staging store/producer-named class/def in production: {offenders!r}",
        )


# ---------------------------------------------------------------------------
# 2. The boundary frame exists as a docs-only, non-authorizing artifact
# ---------------------------------------------------------------------------

class TestBoundaryFrameIsDocsOnlyNonAuthorizing(unittest.TestCase):
    def test_boundary_frame_exists(self):
        self.assertTrue(
            _BOUNDARY_DOC.is_file(),
            f"missing boundary frame doc: {_BOUNDARY_DOC.name}",
        )

    def test_boundary_frame_carries_non_authorization_anchor(self):
        text = _read(_BOUNDARY_DOC)
        # Verdict anchor + explicit non-authorization / non-production posture.
        self.assertIn("INERT STAGING BOUNDARY FRAMED", text)
        self.assertIn("NO DREAM MATERIAL PRODUCED", text)
        self.assertRegex(text, r"[Nn]on-authoriz")
        self.assertIn("existence ≠ authorization", text)


# ---------------------------------------------------------------------------
# 3. Production does not import / treat the boundary doc as runtime input
# ---------------------------------------------------------------------------

class TestBoundaryDocNotRuntimeInput(unittest.TestCase):
    def test_no_production_source_references_the_boundary_doc(self):
        # The doc is evidence/anchor, never a runtime input: its filename (and
        # its dream-readiness stem) must not appear anywhere in production source
        # (no open(), no path constant, no import-style reference).
        stem = _BOUNDARY_DOC_NAME[:-3]  # drop ".md"
        offenders = {}
        for p in _prod_files():
            src = _read(p)
            if _BOUNDARY_DOC_NAME in src or stem in src:
                offenders[str(p.relative_to(_REPO))] = True
        self.assertEqual(
            offenders, {},
            f"production source references the boundary doc as input: {offenders!r}",
        )

    def test_no_production_import_of_a_dream_readiness_module(self):
        # There is no importable Dream-readiness module; assert none appears.
        offenders = {}
        for p, tree in _prod_trees():
            hits = []
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    hits += [a.name for a in n.names
                             if "dream_readiness" in a.name.lower()
                             or "inert_staging" in a.name.lower()]
                elif isinstance(n, ast.ImportFrom) and n.module:
                    m = n.module.lower()
                    if "dream_readiness" in m or "inert_staging" in m:
                        hits.append(n.module)
            if hits:
                offenders[str(p.relative_to(_REPO))] = hits
        self.assertEqual(
            offenders, {},
            f"production imports a dream-readiness/inert-staging module: {offenders!r}",
        )


# ---------------------------------------------------------------------------
# 4/5. Teeth + symmetry — matcher flags synthetics, spares benign candidate names
# ---------------------------------------------------------------------------

_TEETH_SNIPPET = '''
class StagingStore:
    pass


class DreamProducer:
    pass


class ChamberRuntime:
    pass


def incubation_loop():
    pass


def make_candidate_store():
    pass


def footprint_store_writer():
    pass
'''

# Benign vocabulary mirroring the real production candidate surface.
_BENIGN_SNIPPET = '''
class CandidateShapedValue:
    pass


class CompressionCandidate:
    pass


class ReferenceStore:
    pass


class EnvironmentStore:
    pass


def select_candidates():
    pass


def extract_spirit_return_candidates():
    pass
'''


class TestMatcherHasTeeth(unittest.TestCase):
    def setUp(self):
        self.teeth = ast.parse(_TEETH_SNIPPET)

    def test_flags_forbidden_class_and_def_names(self):
        names = _forbidden_named_defs(self.teeth)
        for expected in (
            "StagingStore", "DreamProducer", "ChamberRuntime",
            "incubation_loop", "make_candidate_store", "footprint_store_writer",
        ):
            self.assertIn(expected, names, f"teeth: {expected!r} not flagged")

    def test_flags_forbidden_module_stem(self):
        class _Stub:
            def __init__(self, stem):
                self.stem = stem
        stubs = [_Stub("staging_store"), _Stub("footprint_store"), _Stub("dream_producer")]
        self.assertEqual(
            _forbidden_module_stems(stubs),
            ["dream_producer", "footprint_store", "staging_store"],
        )


class TestMatcherHasNoFalsePositives(unittest.TestCase):
    def test_benign_candidate_vocabulary_not_flagged(self):
        benign = ast.parse(_BENIGN_SNIPPET)
        self.assertEqual(
            _forbidden_named_defs(benign), [],
            "benign candidate/store vocabulary was wrongly flagged",
        )

    def test_benign_module_stems_not_flagged(self):
        class _Stub:
            def __init__(self, stem):
                self.stem = stem
        stubs = [_Stub("candidate_types"), _Stub("reference_memory"), _Stub("environment_memory")]
        self.assertEqual(_forbidden_module_stems(stubs), [])


if __name__ == "__main__":
    unittest.main()
