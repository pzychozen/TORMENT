#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""character_memory_harness/run_bounded_loop.py

Bounded retrieval-and-coherence PROBE (Probe v0) — single character (Eland).

Executes the FROZEN contract in `character_memory_harness/matrix.yaml`:
two arms (seed-only baseline vs runtime-memory), governed `/retrieve`
selection, a MINIMAL model-visible callback prompt, transcript-stateless
callback, fresh disposable workspaces per run. First-pass grading is
HUMAN-APPLIED — this runner only prepares a review template; it does not
auto-grade persona coherence.

Probe v0 is NOT a full interaction loop and NOT the production assembly
surface test. It feeds the model ONLY the verbatim persona seed plus plain
selected memory text (presentation labels stripped). The production
`/retrieve.assembled_text` surface ([Identity Context]/[Drift:]/[Voice:]/
[Flavor:]) is parked as Probe v1. `/agent/query` raw retrieval is parked as
a later comparison mode.

This is fresh code. It borrows PATTERNS (client plumbing, /retrieve usage)
from active, non-locked sources (examples/character_chat_probe.py) but
imports nothing from any historical/locked harness.

DO NOT, per the harness contract:
  - import / fork / copy from torment_stress_harness/ or the repo-root
    do_not_touch_torment_test_rig/;
  - touch Ryuki or any protected/populated workspace;
  - add actor-direction, protective framing, or a controlling wrapper;
  - add automation, tools, external effects, canon mutation after the
    initial identical seed plant, audit-driven gating, or longitudinal
    aggregation.

Run from the repo root:
    python character_memory_harness/run_bounded_loop.py

------------------------------------------------------------------------
PROBE v0 MECHANICS (faithful to the frozen matrix):

  identical Eland seed plant in both fresh arms
    -> runtime-memory arm ingests ONE deterministic temporary fact
       (text = establish text; supplied_summary = matrix temporary_fact,
        which threads through the governed Spine write path to
        spawn_memory tool_summary — confirmed in fabric.py:2660/2692)
    -> both arms call POST /retrieve at callback time
       (include_assembly_audit=true; audit captured for FORENSICS ONLY,
        response-only / non-persistent per Option C)
    -> callback-only transcript-stateless model call
    -> human review

The declared gap is PARKED (gap_parked): mechanically inert in Probe v0,
neither ingested nor model-called. Recency is defeated structurally by the
transcript-stateless callback, not by the gap.
------------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import secrets
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    import yaml
except ImportError:  # pragma: no cover
    print("[fatal] PyYAML required: pip install pyyaml", file=sys.stderr)
    raise

HERE = Path(__file__).resolve().parent
MATRIX_PATH = HERE / "matrix.yaml"
OUTPUTS_DIR = HERE / "outputs"
# torment_fabric/data/workspaces — canonical local workspace store (matches
# the data/workspaces/<ws>/ paths used by the service on this machine). Used
# only for the local best-effort workspace-reuse guard.
DATA_WORKSPACES_DIR = HERE.parent / "data" / "workspaces"

WORKSPACE_DOMAINS = ["personal"]  # single-domain workspace, mirrors active probe

# Pinned first-pass contract (validated explicitly; no silent [0] indexing).
EXPECTED_CHARACTER_ID = "truthful_accidental_lie"
EXPECTED_SCENARIO_ID = "eland_bounded_recall_probe_v0"
EXPECTED_ARMS = ["seed_only", "runtime_memory"]
EXPECTED_PROBE_MODE = "clean_recall"

# Required runtime posture (companion). The harness PREFLIGHTS the running
# service and ABORTS before any workspace mutation if the posture is wrong.
# Rationale: run 20260530T183554Z_765e was a bring-up PASS that ran with
# companion-profiled retrieval/assembly but an empty service-derived character
# posture (derived.profile.name == ""), so character tuning was base-default and
# character-level interpretation was deferred. This preflight makes that silent
# miss impossible to repeat. Embedder values are gated; affect/mood/anchor/role/
# character tuning is CAPTURED into forensics but NOT gated.
REQUIRED_PROFILE_NAME = "companion"
REQUIRED_EMBED_PROVIDER = "st"
REQUIRED_EMBED_MODEL = "BAAI/bge-small-en-v1.5"
REQUIRED_EMBED_DEVICE = "cpu"
REQUIRED_EMBED_DIM = 384

# Presentation-only label lines stripped when building the Probe v0 clean
# prompt from selected blocks (the actual memory text is preserved verbatim).
_LABEL_LINE_RE = re.compile(
    r"^\s*\[(Character|Drift|Voice|Flavor|Returning Memory|"
    r"Identity Context|Relational Context|Situational Context|Archive Context)\b",
    re.IGNORECASE,
)

_STOPWORDS = {"the", "a", "an", "of", "in", "on", "not", "is", "was", "to", "and", "year"}


# --------------------------------------------------------------------------
# .env discipline — load KEY=value next to the torment_fabric package and in
# cwd, never overriding an already-set env var, never printing secrets.
# MUST run before argparse defaults are evaluated (they read os.environ).
# --------------------------------------------------------------------------
def _load_dotenv_safely() -> None:
    for path in (HERE.parent / ".env", Path.cwd() / ".env"):
        try:
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip()
                if key and key not in os.environ:
                    os.environ[key] = val
        except Exception:
            pass


def _env(name: str, default: str) -> str:
    val = os.environ.get(name, "")
    return val if val else default


# --------------------------------------------------------------------------
# TORMENT client — fresh implementation, pattern borrowed from the active
# examples/character_chat_probe.py TormentClient (not imported).
# --------------------------------------------------------------------------
class TormentClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        r = self.session.post(f"{self.base_url}{path}", json=data, timeout=self.timeout)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"POST {path} failed: {r.status_code} {r.text}") from e
        return r.json()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = self.session.get(f"{self.base_url}{path}", params=params or {}, timeout=self.timeout)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"GET {path} failed: {r.status_code} {r.text}") from e
        return r.json()

    def health(self) -> Dict[str, Any]:
        return self._get("/health")

    def config(self) -> Dict[str, Any]:
        return self._get("/config")

    def embedder_check(self) -> Dict[str, Any]:
        return self._get("/embedder/check")

    def workspace_create(self, ws_id: str, domains: List[str]) -> Dict[str, Any]:
        return self._post("/workspace/create", {"workspace_id": ws_id, "domains": domains})

    def agent_create(self, ws_id: str, agent_id: str, seed: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/agent/create", {"workspace_id": ws_id, "agent_id": agent_id, "seed": seed})

    def ingest(self, ws_id: str, agent_id: str, text: str, step: int,
               supplied_summary: Optional[str] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"workspace_id": ws_id, "agent_id": agent_id, "text": text, "step": step}
        if supplied_summary is not None:
            body["supplied_summary"] = supplied_summary
        return self._post("/agent/ingest", body)

    def retrieve(self, ws_id: str, agent_id: str, query: str, top_k: int,
                 include_assembly_audit: bool = True) -> Dict[str, Any]:
        return self._post("/retrieve", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "query": query,
            "top_k": top_k,
            "include_assembly_audit": include_assembly_audit,
        })


# --------------------------------------------------------------------------
# Probe v0 clean-prompt construction
# --------------------------------------------------------------------------
def _strip_presentation_labels(block_text: str) -> List[str]:
    """Return the memory lines of a block with presentation-only label lines
    removed. Remaining text is preserved EXACTLY (never summarized/rewritten)."""
    out: List[str] = []
    for line in block_text.splitlines():
        if _LABEL_LINE_RE.match(line):
            continue
        if line.strip():
            out.append(line.rstrip())
    return out


def extract_plain_memory_lines(retrieve_response: Dict[str, Any]) -> List[str]:
    """Plain, non-seed selected memory lines from a /retrieve response.

    - iterates selected blocks (response['blocks']);
    - EXCLUDES the seed identity block (metadata.is_seed True) AND its decomposed
      seed_canon fragments (metadata.type == "seed_canon") — the verbatim seed is
      placed once at the top of the prompt from matrix.yaml, so re-including either
      would duplicate seed material under "Things you remember:". Exclusion keys on
      is_seed/seed_canon, NOT source=="core" (the runtime episode is core too);
    - strips presentation-only labels ([Character:]/[Drift:]/[Voice:]/[Flavor:]/
      [Returning Memory]/section headers);
    - preserves the remaining memory text exactly.
    Section headers never appear here (they live in assembled_text, not in
    per-block text), so working from blocks is structurally clean.
    """
    lines: List[str] = []
    blocks = retrieve_response.get("blocks", {}) or {}
    for _bt, block_list in blocks.items():
        for b in block_list or []:
            meta = b.get("metadata", {}) or {}
            # Exclude the verbatim seed identity block (is_seed) AND its decomposed
            # seed_canon fragments — both restate seed material the prompt already
            # places once at the top, so leaving them in duplicates the seed under
            # "Things you remember:" and confounds the probe.
            # NB (Codex correction): do NOT broaden this to source == "core". The
            # planted runtime-memory episode is also serialized as core material, so
            # a source-based filter would silently drop the very chapter-seven fact
            # this probe is designed to test.
            if meta.get("is_seed") or meta.get("type") == "seed_canon":
                continue  # seed identity block + decomposed seed-canon fragments excluded
            for ln in _strip_presentation_labels(str(b.get("text", ""))):
                lines.append(ln)
    return lines


def build_clean_prompt(persona_seed: str, memory_lines: List[str], lead_in: str) -> str:
    parts = [persona_seed.rstrip()]
    if memory_lines:
        body = "\n".join(f"- {ln}" for ln in memory_lines)
        parts.append(f"{lead_in}\n{body}")
    return "\n\n".join(parts)


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()


def fact_present(memory_lines: List[str], temporary_fact: str) -> bool:
    """Explicit normalized check grounded in the pinned temporary_fact.

    Uses the corrected-value phrase (the part after '=' if present), reduced
    to content tokens, and requires all to appear in the normalized memory
    blob. Robust to wording/whitespace, not a brittle raw-string match."""
    phrase = temporary_fact.split("=", 1)[1] if "=" in temporary_fact else temporary_fact
    sig_tokens = [t for t in _normalize(phrase).split() if t not in _STOPWORDS]
    blob = _normalize(" ".join(memory_lines))
    blob_tokens = set(blob.split())
    if not sig_tokens:
        return False
    return all(t in blob_tokens for t in sig_tokens)


# --------------------------------------------------------------------------
# Provider — duck-typed .message(system, messages, max_tokens) -> str.
# Default anthropic model matches the active probe (claude-sonnet-4-6).
# --------------------------------------------------------------------------
_ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-6"
_OPENROUTER_DEFAULT_MODEL = "google/gemini-2.5-flash"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class _AnthropicProvider:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._api_key = api_key

    def message(self, system: str, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": self._api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": self.model, "max_tokens": max_tokens, "system": system, "messages": messages},
            timeout=60,
        )
        r.raise_for_status()
        return "".join(blk.get("text", "") for blk in r.json().get("content", []))


class _OpenRouterProvider:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._api_key = api_key

    def message(self, system: str, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        all_messages = [{"role": "system", "content": system}] + messages
        r = requests.post(
            f"{_OPENROUTER_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}", "content-type": "application/json"},
            json={"model": self.model, "max_tokens": max_tokens, "messages": all_messages},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def build_provider() -> Any:
    provider = _env("TORMENT_CHAT_PROVIDER", "anthropic").lower()
    override = _env("TORMENT_CHAT_MODEL", "")
    if provider == "anthropic":
        key = _env("ANTHROPIC_API_KEY", "")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        return _AnthropicProvider(key, override or _ANTHROPIC_DEFAULT_MODEL)
    if provider == "openrouter":
        key = _env("OPENROUTER_API_KEY", "")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        return _OpenRouterProvider(key, override or _OPENROUTER_DEFAULT_MODEL)
    raise RuntimeError(f"unknown TORMENT_CHAT_PROVIDER: {provider!r}")


# --------------------------------------------------------------------------
# Matrix loading + contract validation + workspace-id safety
# --------------------------------------------------------------------------
def load_matrix() -> Dict[str, Any]:
    with MATRIX_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_contract(matrix: Dict[str, Any]) -> None:
    chars = matrix.get("characters", [])
    scens = matrix.get("scenarios", [])
    if not chars or chars[0].get("id") != EXPECTED_CHARACTER_ID:
        raise RuntimeError(f"contract: expected character {EXPECTED_CHARACTER_ID!r}, got {chars[:1]}")
    if not scens or scens[0].get("id") != EXPECTED_SCENARIO_ID:
        raise RuntimeError(f"contract: expected scenario {EXPECTED_SCENARIO_ID!r}, got {scens[:1]}")
    scen = scens[0]
    if scen.get("arms") != EXPECTED_ARMS:
        raise RuntimeError(f"contract: expected arms {EXPECTED_ARMS}, got {scen.get('arms')}")
    if scen.get("probe_mode") != EXPECTED_PROBE_MODE:
        raise RuntimeError(f"contract: expected probe_mode {EXPECTED_PROBE_MODE!r}, got {scen.get('probe_mode')}")
    if scen.get("callback", {}).get("transcript_stateless") is not True:
        raise RuntimeError("contract: callback.transcript_stateless must be true")


def generate_run_id() -> str:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}_{secrets.token_hex(2)}"


def make_workspace_ids(matrix: Dict[str, Any], run_id: str) -> Dict[str, str]:
    tor = matrix.get("torment", {})
    prefix = tor.get("workspace_prefix", "cm_loop")
    arms_tpl = tor.get("workspace_arms", {})
    return {
        "seed_only": arms_tpl.get("seed_only", "{prefix}_{run_id}_seed_only").format(prefix=prefix, run_id=run_id),
        "runtime_memory": arms_tpl.get("runtime_memory", "{prefix}_{run_id}_runtime_memory").format(prefix=prefix, run_id=run_id),
    }


def assert_workspace_safe(matrix: Dict[str, Any], ws_ids: Dict[str, str]) -> None:
    """PRIMARY guard: every generated ID must begin with the required prefix.
    SECONDARY: none may appear in the denylist. TERTIARY: refuse reuse — abort
    if a workspace dir already exists locally (best-effort, local single-machine
    store at torment_fabric/data/workspaces/)."""
    tor = matrix.get("torment", {})
    required = tor.get("workspace_prefix_required", "cm_loop_")
    denylist = set(tor.get("workspace_denylist", []))
    for arm, ws in ws_ids.items():
        if not ws.startswith(required):
            raise RuntimeError(f"SAFETY ABORT: {arm} workspace {ws!r} does not begin with required prefix {required!r}")
        if ws in denylist:
            raise RuntimeError(f"SAFETY ABORT: {arm} workspace {ws!r} is in the denylist")
        if (DATA_WORKSPACES_DIR / ws).exists():
            raise RuntimeError(f"SAFETY ABORT: {arm} workspace {ws!r} already exists on disk — refusing reuse")


def preflight_posture(health: Dict[str, Any], config: Dict[str, Any],
                      embedder_check: Dict[str, Any]) -> List[str]:
    """Validate the running service is in the required companion posture.

    Returns a list of failure strings (empty == posture OK). The caller
    captures all three raw responses into forensics regardless, and ABORTS
    before any workspace mutation if this returns non-empty.

    Gated: profile name == companion; embedder provider/model/device/dim;
    character enabled; embedder ok and not degraded.
    NOT gated (captured only): affect/mood/anchor/role/character tuning.
    """
    fails: List[str] = []

    eff = (config.get("effective") or {}) if isinstance(config, dict) else {}
    def _eff(key: str) -> Any:
        v = eff.get(key)
        return v.get("value") if isinstance(v, dict) else None

    prof_name = ""
    derived = config.get("derived") if isinstance(config, dict) else None
    if isinstance(derived, dict):
        prof = derived.get("profile")
        if isinstance(prof, dict):
            prof_name = str(prof.get("name") or "")
    if prof_name != REQUIRED_PROFILE_NAME:
        fails.append(f"profile name {prof_name!r} != required {REQUIRED_PROFILE_NAME!r} "
                     f"(start service with TORMENT_PROFILE={REQUIRED_PROFILE_NAME})")

    if str(_eff("TORMENT_CHARACTER_ENABLE")).strip().lower() not in ("1", "true", "yes", "on"):
        fails.append("TORMENT_CHARACTER_ENABLE is not truthy")
    if str(_eff("TORMENT_EMBED_PROVIDER")) != REQUIRED_EMBED_PROVIDER:
        fails.append(f"embed provider {_eff('TORMENT_EMBED_PROVIDER')!r} != {REQUIRED_EMBED_PROVIDER!r}")
    if str(_eff("TORMENT_EMBED_MODEL")) != REQUIRED_EMBED_MODEL:
        fails.append(f"embed model {_eff('TORMENT_EMBED_MODEL')!r} != {REQUIRED_EMBED_MODEL!r}")
    if str(_eff("TORMENT_EMBED_DEVICE")) != REQUIRED_EMBED_DEVICE:
        fails.append(f"embed device {_eff('TORMENT_EMBED_DEVICE')!r} != {REQUIRED_EMBED_DEVICE!r}")

    ec = embedder_check if isinstance(embedder_check, dict) else {}
    if ec.get("ok") is not True:
        fails.append(f"embedder_check ok != true (got {ec.get('ok')!r})")
    if bool(ec.get("degraded")):
        fails.append("embedder_check degraded == true")
    if str(ec.get("provider")) != REQUIRED_EMBED_PROVIDER:
        fails.append(f"embedder_check provider {ec.get('provider')!r} != {REQUIRED_EMBED_PROVIDER!r}")
    if str(ec.get("model")) != REQUIRED_EMBED_MODEL:
        fails.append(f"embedder_check model {ec.get('model')!r} != {REQUIRED_EMBED_MODEL!r}")
    if int(ec.get("dim") or 0) != REQUIRED_EMBED_DIM:
        fails.append(f"embedder_check dim {ec.get('dim')!r} != {REQUIRED_EMBED_DIM}")

    return fails


# --------------------------------------------------------------------------
# Per-arm execution
# --------------------------------------------------------------------------
def seed_payload_for(character: Dict[str, Any]) -> Dict[str, Any]:
    """Only seed_text, seed_id, character_name — per the authorized slice."""
    return {
        "seed_text": character["persona_seed"].rstrip(),
        "seed_id": f'{character["id"]}_v1',
        "character_name": character["name"],
    }


def run_arm(torment: TormentClient, provider: Any, arm: str, ws_id: str, agent_id: str,
            character: Dict[str, Any], scenario: Dict[str, Any], top_k: int) -> Dict[str, Any]:
    record: Dict[str, Any] = {"arm": arm, "workspace_id": ws_id, "agent_id": agent_id, "turns": {}}

    torment.workspace_create(ws_id, WORKSPACE_DOMAINS)
    seed = seed_payload_for(character)
    torment.agent_create(ws_id, agent_id, seed)
    record["seed_payload"] = seed

    # --- establish: runtime arm ingests; deterministic supplied_summary.
    establish = scenario["establish"]
    establish_text = establish["text"].strip()
    temporary_fact = establish.get("temporary_fact", "")
    record["turns"]["establish"] = {
        "user_text": establish_text, "temporary_fact": temporary_fact, "ingested": False,
    }
    if arm == "runtime_memory":
        ing = torment.ingest(ws_id, agent_id, establish_text, step=1, supplied_summary=temporary_fact)
        record["turns"]["establish"]["ingested"] = True
        record["turns"]["establish"]["ingest_response"] = ing
        record["turns"]["establish"]["supplied_summary"] = temporary_fact

    # --- gap parked: declared only.
    gp = scenario.get("gap_parked", {})
    record["turns"]["gap_parked"] = {"declared_text": gp.get("text", ""), "ingested": False, "model_called": False}

    # --- callback: /retrieve (governed) then transcript-stateless model call.
    callback = scenario["callback"]
    callback_text = callback["text"].strip()
    retr = scenario.get("retrieval", {})
    include_audit = bool(retr.get("include_assembly_audit", True))
    retrieve_response = torment.retrieve(ws_id, agent_id, callback_text, top_k=top_k, include_assembly_audit=include_audit)

    memory_lines = extract_plain_memory_lines(retrieve_response)
    lead_in = scenario.get("prompt_assembly", {}).get("memory_lead_in", "Things you remember:")
    system_prompt = build_clean_prompt(character["persona_seed"], memory_lines, lead_in)

    cb: Dict[str, Any] = {
        "transcript_stateless": True,
        "retrieval_endpoint": "/retrieve",
        "retrieval_query": callback_text,
        "retrieve_response": retrieve_response,   # FULL response, forensic only
        "plain_memory_lines": memory_lines,
        "system_prompt_model_visible": system_prompt,
        "user_message": callback_text,
    }

    # --- fact-presence gate (runtime arm only). Absence in seed-only is expected.
    if arm == "runtime_memory":
        present = fact_present(memory_lines, temporary_fact)
        cb["fact_present_in_selected_blocks"] = present
        if not present:
            cb["status"] = "retrieval_failure"
            cb["assistant_response"] = None
            cb["note"] = "expected temporary fact not represented in selected non-seed blocks; model NOT called"
            record["turns"]["callback"] = cb
            return record

    assistant = provider.message(system=system_prompt, messages=[{"role": "user", "content": callback_text}], max_tokens=1024)
    cb["status"] = "ok"
    cb["assistant_response"] = assistant
    record["turns"]["callback"] = cb
    return record


# --------------------------------------------------------------------------
# Output + grading template
# --------------------------------------------------------------------------
def write_manifest(run_id: str, config: Dict[str, Any]) -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    p = OUTPUTS_DIR / f"cm_loop_{run_id}_manifest.json"
    p.write_text(json.dumps({"run_id": run_id, "config": config, "status": "preflight"}, indent=2, default=str), encoding="utf-8")
    return p


def write_outputs(run_id: str, config: Dict[str, Any], arms: Dict[str, Any], grading: Dict[str, Any],
                  status: str = "complete") -> Dict[str, Path]:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    blob = {"run_id": run_id, "status": status, "config": config, "arms": arms, "grading_anchor": grading}
    json_path = OUTPUTS_DIR / f"cm_loop_{run_id}.json"
    json_path.write_text(json.dumps(blob, indent=2, default=str), encoding="utf-8")
    md_path = OUTPUTS_DIR / f"cm_loop_{run_id}_review.md"
    md_path.write_text(_render_review_template(run_id, arms, grading), encoding="utf-8")
    return {"json": json_path, "review": md_path}


def _render_review_template(run_id: str, arms: Dict[str, Any], grading: Dict[str, Any]) -> str:
    # NOTE: precompute everything into plain locals. Do NOT inline dict/`{}`
    # literals inside f-string replacement fields — Python <3.12 cannot parse
    # an empty-dict literal nested in an f-string field.
    empty: Dict[str, Any] = {}
    so_arm = arms.get("seed_only", empty)
    rm_arm = arms.get("runtime_memory", empty)
    so = so_arm.get("turns", empty).get("callback", empty)
    rm = rm_arm.get("turns", empty).get("callback", empty)

    def fmt_list(items: List[str]) -> str:
        return "\n".join(f"  - {x}" for x in items)

    expected_fact = grading.get("expected_fact", "")
    so_ws = so_arm.get("workspace_id", "")
    rm_ws = rm_arm.get("workspace_id", "")
    so_status = so.get("status", "")
    rm_status = rm.get("status", "")
    rm_fact = rm.get("fact_present_in_selected_blocks", "")
    so_user = so.get("user_message", "")
    rm_user = rm.get("user_message", "")
    so_resp = so.get("assistant_response", "")
    rm_resp = rm.get("assistant_response", "")
    cp = fmt_list(grading.get("coherence_preserved", []))
    cbk = fmt_list(grading.get("coherence_broken", []))
    inc = fmt_list(grading.get("inconclusive", []))

    return textwrap.dedent(f"""\
        # Character-Memory Probe v0 — Human Review
        run_id: {run_id}

        Grading is HUMAN-APPLIED. This template only organizes evidence; it
        does NOT auto-grade. Pin the matrix grading anchor before judging.

        Expected fact: {expected_fact}

        ## Seed-only baseline — callback
        Workspace: {so_ws}
        Status: {so_status}

        User: {so_user}

        Assistant:
        {so_resp}

        ## Runtime-memory arm — callback
        Workspace: {rm_ws}
        Status: {rm_status}
        Fact present in selected blocks: {rm_fact}

        User: {rm_user}

        Assistant:
        {rm_resp}

        ## Grading anchor (from matrix.yaml — pinned)
        COHERENCE_PRESERVED — all of:
        {cp}

        COHERENCE_BROKEN — any of:
        {cbk}

        INCONCLUSIVE — any of:
        {inc}

        ## Operator verdict (fill in)
        recall_seed_only:        [ recalled / honest-omission / fabricated / failed ]
        recall_runtime_memory:   [ recalled / honest-omission / fabricated / failed ]
        coherence_runtime_memory:[ COHERENCE_PRESERVED / COHERENCE_BROKEN / INCONCLUSIVE ]
        notes:

        ## Reminder
        Workspaces are NOT auto-deleted. Inspect, then delete manually after review.
        """)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    _load_dotenv_safely()  # BEFORE argparse defaults read os.environ

    matrix = load_matrix()
    validate_contract(matrix)

    matrix_fallback_url = matrix.get("torment", {}).get("server_url_fallback", "http://127.0.0.1:8787")

    ap = argparse.ArgumentParser(description="Bounded retrieval-and-coherence probe (Probe v0, human-graded).")
    ap.add_argument("--base-url", default=None, help="override; else env TORMENT_URL, else matrix server_url_fallback")
    ap.add_argument("--top-k", type=int, default=int(_env("TORMENT_TOP_K", "8")))
    ap.add_argument("--agent-id", default="eland", help="agent id used inside both fresh workspaces")
    args = ap.parse_args(argv)

    # Base-url resolution order: CLI > env TORMENT_URL > matrix fallback.
    base_url = args.base_url or os.environ.get("TORMENT_URL") or matrix_fallback_url

    character = matrix["characters"][0]
    scenario = matrix["scenarios"][0]

    run_id = generate_run_id()
    ws_ids = make_workspace_ids(matrix, run_id)
    assert_workspace_safe(matrix, ws_ids)  # prefix + denylist + reuse guards

    config = {
        "run_id": run_id, "base_url": base_url, "top_k": args.top_k, "agent_id": args.agent_id,
        "provider": _env("TORMENT_CHAT_PROVIDER", "anthropic").lower(),
        "workspace_ids": ws_ids, "character_id": character.get("id"), "character_name": character.get("name"),
        "scenario_id": scenario.get("id"), "probe_mode": scenario.get("probe_mode"),
        "retrieval": scenario.get("retrieval", {}),
        "notes": [
            "Probe v0: governed /retrieve selection; minimal clean model-visible prompt.",
            "establish ingested with deterministic supplied_summary; gap parked (inert).",
            "production assembled_text surface parked as Probe v1; /agent/query parked.",
        ],
    }

    # Preflight manifest BEFORE any workspace mutation (preserve IDs for cleanup).
    manifest_path = write_manifest(run_id, config)

    torment = TormentClient(base_url)

    # --- Runtime-posture preflight: capture /health, /config, /embedder/check
    # into forensics, then ABORT before any workspace mutation unless the
    # required companion posture is active. (Run 765e was a bring-up PASS that ran
    # with companion-profiled retrieval/assembly but an empty service-derived
    # character posture; this makes that silent miss impossible to repeat.)
    try:
        health = torment.health()
        cfg = torment.config()
        ec = torment.embedder_check()
    except Exception as exc:
        print(f"[fatal] TORMENT not reachable at {base_url}: {exc}", file=sys.stderr)
        print(f"        preflight manifest preserved: {manifest_path}", file=sys.stderr)
        return 3

    config["preflight"] = {"health": health, "config": cfg, "embedder_check": ec}
    config["health_profile"] = health.get("profile", {}).get("name", "?") if isinstance(health, dict) else "?"
    # Re-write the manifest so the captured posture is preserved even if we abort.
    manifest_path = write_manifest(run_id, config)

    posture_fails = preflight_posture(health, cfg, ec)
    if posture_fails:
        print("[abort] runtime-posture preflight FAILED — no workspace created, nothing mutated.", file=sys.stderr)
        for f in posture_fails:
            print(f"        - {f}", file=sys.stderr)
        print("        Required: start the service with the companion posture, e.g.:", file=sys.stderr)
        print("          set TORMENT_EMBED_PROVIDER=st", file=sys.stderr)
        print("          set TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5", file=sys.stderr)
        print("          set TORMENT_EMBED_DEVICE=cpu", file=sys.stderr)
        print("          set TORMENT_PROFILE=companion", file=sys.stderr)
        print("          set TORMENT_CHARACTER_ENABLE=1", file=sys.stderr)
        print(f"        preflight manifest preserved: {manifest_path}", file=sys.stderr)
        return 6

    try:
        provider = build_provider()
    except Exception as exc:
        print(f"[fatal] provider init failed: {exc}", file=sys.stderr)
        return 4
    config["model"] = getattr(provider, "model", "?")

    arms: Dict[str, Any] = {}
    grading = scenario.get("grading", {})
    try:
        for arm, ws_id in ws_ids.items():
            arms[arm] = run_arm(torment, provider, arm, ws_id, args.agent_id, character, scenario, args.top_k)
            # incremental partial-state write after each arm
            write_outputs(run_id, config, arms, grading, status="partial")
    except Exception as exc:
        # preserve whatever completed; surface ws ids for manual cleanup
        write_outputs(run_id, config, arms, grading, status="failed")
        print(f"[fatal] arm execution failed: {exc}", file=sys.stderr)
        print(f"        partial forensic output + manifest preserved for run {run_id}", file=sys.stderr)
        print(f"        workspaces (manual cleanup): {ws_ids}", file=sys.stderr)
        return 5

    paths = write_outputs(run_id, config, arms, grading, status="complete")
    print(f"[ok] run {run_id} complete (HUMAN GRADING REQUIRED)")
    print(f"     seed_only      ws: {ws_ids['seed_only']}")
    print(f"     runtime_memory ws: {ws_ids['runtime_memory']}")
    print(f"     forensic json:  {paths['json']}")
    print(f"     review template: {paths['review']}")
    print("     NOTE: workspaces are NOT auto-deleted — inspect, then delete manually.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
