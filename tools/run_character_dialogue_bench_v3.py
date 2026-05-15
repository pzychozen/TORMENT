#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/run_character_dialogue_bench_v3.py — ryuki_chat-pattern two-character runner.

v3 architecture (2026-05-14, post-audit):
    Two TORMENT-seeded characters speak in alternation, each running the SAME
    architecture as examples/ryuki_chat.py — just doubled and crossfed. The
    v2 runner was a stateless prose-riff loop that re-injected the persona
    seed every turn and threw away `character_context` from the query
    response; that produced 100 turns of mutually-narrated atmosphere and
    no actual conversation. v3 copies the canonical Ryuki pattern instead
    of inventing a new dialogue architecture.

TORMENT server contract (from examples/ryuki_chat.py):
    Endpoint                            Used for
    --------------------------          --------------------------------
    GET  /health                        reachability
    POST /workspace/create              workspace with domains=["personal"]
    POST /agent/create                  plant seed ONCE (seed_text + seed_id)
    GET  /agent/{id}/identity           verify seed planted
    POST /agent/query                   per-turn retrieval, returns:
                                          - hits: list of memory dicts with
                                            summary, final_score, character_tier,
                                            provenance_type
                                          - character_context: dict with
                                            seed_preamble, recommendations,
                                            drift_score, drift_summary
    POST /agent/ingest                  paired compact summary per turn

Per-turn loop (mirrors ryuki_chat.chat_loop exactly):
    1. Query TORMENT with the incoming message.
    2. Read `hits` and `character_context` from the response.
    3. Build the system prompt from:
         - format_character_context(char_ctx)   <- seed_preamble + recommendations
         - format_memories(hits)                <- score, tier, provenance markers
         - format_drift_note(char_ctx)          <- only when |drift| >= 0.1
       The full YAML persona_seed is NOT re-injected. Identity flows through
       character_context, which is what TORMENT owns.
    4. Append the incoming message as a `user` turn to the speaker's rolling
       chat history. Trim history to last 40 turns.
    5. Send the full rolling history to the provider adapter.
    6. Append the reply as an `assistant` turn to the speaker's history.
    7. Ingest a compact paired summary into the speaker's workspace.
    8. Ingest a compact observation ("X said: ...") into the listener's
       workspace so the listener can retrieve it when they next speak.
    9. Snapshot character/state for forensics.

What v3 deliberately does NOT do:
    - re-inject the full YAML persona seed every turn
    - flatten retrieved memories to bare bullets (loses score/tier/provenance)
    - discard `character_context` from the query response
    - wrap the incoming message as `'{name} says: "..."'` (forces third-person
      narration; the model writes prose ABOUT a conversation instead of
      having one)
    - call the model with a single user message and zero history
    - ingest raw atmospheric paragraphs (compact paired summary instead)

Recommended TORMENT server setup (Windows CMD):
    cd C:\\TORMENT\\TORMENT_repo\\TORMENT-fabric_v2\\torment_fabric
    conda activate torment
    set TORMENT_PROFILE=companion
    set TORMENT_CHARACTER_ENABLE=1
    set TORMENT_COMPRESS_ENABLE=0
    set TORMENT_EMBED_PROVIDER=st
    set TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
    set TORMENT_EMBED_DEVICE=cpu
    python -m torment_service

v3 smoke run (Anthropic, 6 turns):
    python tools\\run_character_dialogue_bench_v3.py ^
      --matrix tests\\character_truth_matrix.yaml ^
      --out out\\dialogue_bench ^
      --character manipulative_boundary_tester ^
      --character declared_liar ^
      --max-turns 6 ^
      --provider anthropic ^
      --opening-line "You entered as if the room had already agreed to become a stage. Did you ask it first?"

v3 smoke run (OpenRouter / Gemini, same setup, comparison):
    python tools\\run_character_dialogue_bench_v3.py ^
      --matrix tests\\character_truth_matrix.yaml ^
      --out out\\dialogue_bench ^
      --character manipulative_boundary_tester ^
      --character declared_liar ^
      --max-turns 6 ^
      --provider openrouter ^
      --opening-line "You entered as if the room had already agreed to become a stage. Did you ask it first?"

This runner does NOT touch torment_service/ code. Bench-side only.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    import yaml
except ModuleNotFoundError:
    print(
        "[fatal] missing dependency: pyyaml\n"
        "        Install in active conda env: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)

# Add torment_fabric/ to sys.path so we can import bench_adapters.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR.parent))

from tools.bench_adapters import (  # noqa: E402
    AdapterUnavailable,
    ProviderAdapter,
    get_adapter,
)


# ---------------------------------------------------------------------------
# .env loader (same minimal loader as v1/v2 runners — kept inline)
# ---------------------------------------------------------------------------

def _load_env_file(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if not key:
            continue
        # Shell-exported env wins over file.
        if key in os.environ and os.environ[key] != "":
            continue
        os.environ[key] = val
        count += 1
    return count


_env_path = _THIS_DIR.parent / ".env"
_loaded = _load_env_file(_env_path)
if _loaded:
    print(f"[ok] loaded {_loaded} variable(s) from {_env_path}")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TORMENT_URL_DEFAULT = "http://127.0.0.1:8787"
WORKSPACE_DOMAINS = ["personal"]
TOP_K_DEFAULT = 8
HISTORY_CAP = 40  # mirrors ryuki_chat: last 40 messages kept

# Minimal system prompt template — copied verbatim from ryuki_chat.py.
# The model's identity flows through character_context (from TORMENT), not
# from a duplicated YAML persona seed. See ryuki_chat.py lines 117-132 for
# the explicit doctrine warning that this preserves.
SYSTEM_PROMPT_TEMPLATE = (
    "You are {agent_name}.\n"
    "\n"
    "{character_context}\n"
    "\n"
    "{memory_context}\n"
    "\n"
    "{drift_note}\n"
)

# Tiny medium instruction — direct speech only, no third-person stage
# narration. This is the minimum to define the test medium without
# leaking personality control. Keep this short and structural, not
# behavioral.
DIALOGUE_MEDIUM_NOTE = (
    "Speak directly to the other character in first person. "
    "Do not narrate the other character's actions or describe the scene."
)


# ---------------------------------------------------------------------------
# TORMENT client (mirrors examples/ryuki_chat.py:TormentClient exactly)
# ---------------------------------------------------------------------------

class TormentClient:
    """HTTP wrapper for the TORMENT FastAPI server. Mirrors the contract of
    examples/ryuki_chat.py:TormentClient so the v3 dialogue runner uses the
    same operations the canonical single-character client uses.
    """

    def __init__(self, base_url: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}{path}", json=data, timeout=self.timeout
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"POST {path} failed: {response.status_code} {response.text}"
            ) from e
        return response.json()

    def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{path}", params=params or {}, timeout=self.timeout
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"GET {path} failed: {response.status_code} {response.text}"
            ) from e
        return response.json()

    def health(self) -> Dict[str, Any]:
        return self._get("/health")

    def workspace_create(
        self, ws_id: str, domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"workspace_id": ws_id}
        if domains:
            payload["domains"] = domains
        return self._post("/workspace/create", payload)

    def agent_create(
        self, ws_id: str, agent_id: str, seed: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._post(
            "/agent/create",
            {"workspace_id": ws_id, "agent_id": agent_id, "seed": seed},
        )

    def agent_identity(self, ws_id: str, agent_id: str) -> Dict[str, Any]:
        return self._get(
            f"/agent/{agent_id}/identity", {"workspace_id": ws_id}
        )

    def query(
        self, ws_id: str, agent_id: str, query: str, top_k: int = TOP_K_DEFAULT
    ) -> Dict[str, Any]:
        return self._post(
            "/agent/query",
            {
                "workspace_id": ws_id,
                "agent_id": agent_id,
                "query": query,
                "top_k": top_k,
            },
        )

    def ingest(
        self, ws_id: str, agent_id: str, text: str, step: int
    ) -> Dict[str, Any]:
        return self._post(
            "/agent/ingest",
            {
                "workspace_id": ws_id,
                "agent_id": agent_id,
                "text": text,
                "step": step,
            },
        )

    def character_state(
        self, ws_id: str, agent_id: str
    ) -> Dict[str, Any]:
        """Forensic-only — used for per-turn snapshots, NOT prompt-time
        identity. The prompt-time identity comes from query.character_context.
        """
        return self._get(
            f"/agent/{agent_id}/character/state",
            params={"workspace_id": ws_id},
        )


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Speaker:
    """A single character participant. Holds its own rolling chat history
    (ryuki_chat-style) plus its TORMENT workspace + agent ids."""
    character_id: str
    name: str
    persona_seed: str  # planted into TORMENT once; not re-injected per turn
    workspace_id: str
    agent_id: str
    conversation: List[Dict[str, str]] = field(default_factory=list)
    other_name: str = ""


@dataclass
class TurnRecord:
    turn: int
    speaker_name: str
    listener_name: str
    incoming_message: str
    response: str
    retrieved_count: int
    retrieved_block: str
    char_ctx_preamble_present: bool
    drift_score: float
    system_prompt: str
    history_len_after: int
    speaker_state_after: Dict[str, Any] = field(default_factory=dict)
    listener_state_after: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Formatting helpers — copied directly from examples/ryuki_chat.py
# ---------------------------------------------------------------------------

def format_memories(hits: List[Dict[str, Any]], top_k: int) -> str:
    """Format retrieved memory hits into a compact context block.
    Mirrors ryuki_chat.format_memories — preserves score, tier, provenance
    markers so the model can tell what kind of memory each item is."""
    if not hits:
        return ""
    lines = ["[Retrieved memories — most relevant first]"]
    for i, hit in enumerate(hits[:top_k], 1):
        summary = hit.get("summary") or hit.get("text") or ""
        if not summary:
            continue
        score = hit.get("final_score", hit.get("score", 0.0))
        tier = hit.get("character_tier", "")
        prov = hit.get("provenance_type", "")
        tags = " ".join(f"[{x}]" for x in [tier, prov] if x)
        try:
            score_f = float(score)
        except (TypeError, ValueError):
            score_f = 0.0
        lines.append(
            f"  {i}. (score {score_f:.2f}{' ' + tags if tags else ''}) "
            f"{summary.strip()}"
        )
    return "\n".join(lines) if len(lines) > 1 else ""


def format_character_context(char_ctx: Dict[str, Any]) -> str:
    """Format the TORMENT character_context block. Mirrors
    ryuki_chat.format_character_context — returns empty string if TORMENT
    surfaced nothing (the SYSTEM_PROMPT_TEMPLATE will just have a blank
    paragraph rather than crashing)."""
    if not char_ctx:
        return ""
    parts: List[str] = []
    preamble = char_ctx.get("seed_preamble", "")
    if preamble:
        parts.append(f"[Core identity]\n{preamble.strip()}")
    recommendations = char_ctx.get("recommendations", [])
    if recommendations:
        parts.append(
            "[Guidance]\n" + "\n".join(f"  - {r}" for r in recommendations)
        )
    return "\n\n".join(parts)


def format_drift_note(char_ctx: Dict[str, Any]) -> str:
    """Drift note only when relevant. Mirrors ryuki_chat.format_drift_note."""
    if not char_ctx:
        return ""
    drift_score = char_ctx.get("drift_score", 0.0)
    drift_summary = char_ctx.get("drift_summary", "")
    try:
        drift_f = float(drift_score)
    except (TypeError, ValueError):
        drift_f = 0.0
    if abs(drift_f) < 0.1 and not drift_summary:
        return ""
    return f"[Drift: {drift_f:+.2f}] {drift_summary}"


def build_summary(
    speaker_name: str,
    listener_name: str,
    incoming: str,
    reply: str,
) -> str:
    """Compact paired summary for ingest into the SPEAKER's workspace.
    Mirrors ryuki_chat.build_summary, generalized for two named characters.
    Caps incoming at 200 chars and reply at 300 chars to keep ingest
    compact and stable across long dialogues."""
    inc_short = incoming[:200].strip()
    rep_short = reply[:300].strip().replace("\n\n", "\n")
    return f"{listener_name} said: {inc_short}\n{speaker_name} responded: {rep_short}"


def build_observation(speaker_name: str, reply: str) -> str:
    """Compact observation for ingest into the LISTENER's workspace.
    The listener didn't speak this turn, but should remember what was said
    to them so they can retrieve it when they next speak."""
    rep_short = reply[:300].strip().replace("\n\n", "\n")
    return f"{speaker_name} said: {rep_short}"


# ---------------------------------------------------------------------------
# Matrix loading
# ---------------------------------------------------------------------------

def _load_matrix(matrix_path: Path) -> dict:
    if not matrix_path.exists():
        raise FileNotFoundError(f"Matrix YAML not found: {matrix_path}")
    raw = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Matrix YAML must be a mapping: {matrix_path}")
    return raw


def _find_character(matrix: dict, character_id: str) -> dict:
    for c in matrix.get("characters", []):
        if c.get("id") == character_id:
            return c
    known = [c.get("id") for c in matrix.get("characters", [])]
    raise ValueError(
        f"Character id '{character_id}' not in matrix. Known: {known}"
    )


# ---------------------------------------------------------------------------
# Setup — per-speaker, mirrors ryuki_chat.ensure_setup
# ---------------------------------------------------------------------------

def _ensure_speaker(
    torment: TormentClient, speaker: Speaker
) -> None:
    """Create workspace + agent for one speaker. Idempotent on the
    workspace side (409 means it already exists; skip). Plants the seed
    ONCE here — this is the only place the YAML persona_seed is sent to
    TORMENT. After this, identity flows through character_context.
    """
    try:
        torment.workspace_create(speaker.workspace_id, domains=WORKSPACE_DOMAINS)
        print(f"  [ok] workspace '{speaker.workspace_id}' created.")
    except RuntimeError as e:
        if " 409 " in str(e):
            print(f"  [info] workspace '{speaker.workspace_id}' already exists.")
        else:
            raise

    seed_payload = {
        "seed_text": speaker.persona_seed.strip(),
        "seed_id": f"{speaker.character_id}_v1",
        "character_name": speaker.name,
    }
    try:
        torment.agent_create(speaker.workspace_id, speaker.agent_id, seed_payload)
        print(f"  [ok] agent '{speaker.agent_id}' created with seed.")
    except RuntimeError as e:
        if " 409 " in str(e):
            print(f"  [info] agent '{speaker.agent_id}' already exists.")
        else:
            raise

    # Verify the seed planted — mirrors ryuki_chat startup check.
    try:
        identity = torment.agent_identity(speaker.workspace_id, speaker.agent_id)
        seed_id = identity.get("seed", {}).get("seed_id", "")
        if seed_id:
            print(f"  [ok] verified seed_id: {seed_id}")
        else:
            print(f"  [warn] agent active but no seed metadata returned.")
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] identity check failed (non-fatal): {e}")


def _build_speakers(
    matrix: dict,
    character_ids: List[str],
    dialogue_id: str,
    workspace_prefix: str,
    agent_prefix: str,
) -> List[Speaker]:
    if len(character_ids) != 2:
        raise ValueError(
            f"v3 requires exactly 2 characters; got {len(character_ids)}: {character_ids}"
        )
    speakers: List[Speaker] = []
    for cid in character_ids:
        c = _find_character(matrix, cid)
        name = c.get("name", cid)
        ws_id = f"{workspace_prefix}_{dialogue_id}_{cid}"
        ag_id = f"{agent_prefix}{cid}__{dialogue_id}"
        speakers.append(Speaker(
            character_id=cid,
            name=name,
            persona_seed=c["persona_seed"],
            workspace_id=ws_id,
            agent_id=ag_id,
        ))
    speakers[0].other_name = speakers[1].name
    speakers[1].other_name = speakers[0].name
    return speakers


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _write_conversation(turns: List[TurnRecord], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "conversation.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for t in turns:
            obj = {
                "turn": t.turn,
                "speaker": t.speaker_name,
                "listener": t.listener_name,
                "incoming": t.incoming_message,
                "response": t.response,
                "retrieved_count": t.retrieved_count,
                "drift_score": t.drift_score,
                "history_len_after": t.history_len_after,
                "char_ctx_preamble_present": t.char_ctx_preamble_present,
                "error": t.error,
            }
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    txt_path = out_dir / "conversation.txt"
    with txt_path.open("w", encoding="utf-8") as fh:
        for t in turns:
            fh.write(f"--- Turn {t.turn} — {t.speaker_name} ---\n")
            if t.error:
                fh.write(f"[error: {t.error}]\n")
            fh.write(f"{t.response.strip()}\n\n")


def _write_state_timeseries(
    rows: List[Dict[str, Any]], out_dir: Path
) -> None:
    scores_dir = out_dir / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields = [
        "turn", "speaker", "was_speaker_this_turn", "agent_id", "workspace_id",
        "drift_score", "drift_direction", "core_count", "relational_count",
        "situational_count", "retrieved_count", "char_ctx_preamble_present",
        "history_len_after", "error",
    ]
    csv_path = scores_dir / "state_timeseries.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _snapshot_state(
    torment: TormentClient, speaker: Speaker, turn: int, out_dir: Path
) -> Dict[str, Any]:
    try:
        state = torment.character_state(speaker.workspace_id, speaker.agent_id)
    except Exception as exc:  # noqa: BLE001
        state = {"error": str(exc)}
    snap_dir = out_dir / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    safe_name = speaker.name.lower().replace(" ", "_")
    fname = snap_dir / f"turn_{turn:03d}_{safe_name}_state.json"
    fname.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return state


def _save_context_dump(
    speaker: Speaker,
    turn: int,
    system_prompt: str,
    rolling_history: List[Dict[str, str]],
    response: str,
    retrieved_count: int,
    out_dir: Path,
) -> None:
    """Forensic dump showing exactly what the model saw. Includes the
    rolling chat history (this is the v3 difference from v2 — there IS
    a rolling history now)."""
    dump_dir = out_dir / "retrieval_dumps"
    dump_dir.mkdir(parents=True, exist_ok=True)
    safe_name = speaker.name.lower().replace(" ", "_")
    fname = dump_dir / f"turn_{turn:03d}_{safe_name}_context.txt"
    parts = [
        f"=== TURN {turn} — speaker: {speaker.name} "
        f"(workspace={speaker.workspace_id}, retrieved_count={retrieved_count}) ===",
        "",
        "=== SYSTEM PROMPT (TORMENT character_context + memories + drift) ===",
        system_prompt,
        "",
        f"=== ROLLING HISTORY ({len(rolling_history)} messages) ===",
    ]
    for i, msg in enumerate(rolling_history, 1):
        role = msg.get("role", "?")
        content = msg.get("content", "")
        parts.append(f"[{i}] ({role})")
        parts.append(content)
        parts.append("")
    parts.extend([
        "=== ASSISTANT RESPONSE THIS TURN ===",
        response,
    ])
    fname.write_text("\n".join(parts), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main dialogue loop
# ---------------------------------------------------------------------------

def run_dialogue(
    matrix: dict,
    character_ids: List[str],
    max_turns: int,
    provider_name: str,
    opening_line: str,
    out_dir: Path,
    top_k: int,
    workspace_prefix: str = "dialogue_v3",
    agent_prefix: str = "dlgv3_",
) -> Tuple[List[TurnRecord], List[Dict[str, Any]]]:
    # Provider adapter (built once).
    model = _select_model_for(provider_name)
    try:
        adapter: ProviderAdapter = get_adapter(provider_name, model)
    except AdapterUnavailable as exc:
        raise RuntimeError(f"adapter setup failed: {exc}")

    dialogue_id = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    torment_url = (
        os.environ.get("TORMENT_SERVER_URL", "").strip() or TORMENT_URL_DEFAULT
    )
    torment = TormentClient(torment_url)

    # Health check before anything else.
    try:
        torment.health()
        print(f"[ok] TORMENT reachable at {torment_url}")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"TORMENT not reachable at {torment_url}: {exc}\n"
            f"        Start it first with: python -m torment_service\n"
            f"        See module docstring for recommended env variables."
        )

    speakers = _build_speakers(
        matrix=matrix,
        character_ids=character_ids,
        dialogue_id=dialogue_id,
        workspace_prefix=workspace_prefix,
        agent_prefix=agent_prefix,
    )
    print(f"[setup] dialogue_id={dialogue_id}")
    for sp in speakers:
        print(f"[setup] character: {sp.name} ({sp.character_id})")
        _ensure_speaker(torment, sp)

    # Initial state snapshots (turn 0).
    _snapshot_state(torment, speakers[0], 0, out_dir)
    _snapshot_state(torment, speakers[1], 0, out_dir)

    turns: List[TurnRecord] = []
    timeseries_rows: List[Dict[str, Any]] = []
    step = int(time.time())
    current_idx = 0  # speakers[0] receives the opening line and replies first

    incoming = opening_line  # direct quoted speech — no wrapper

    for turn in range(1, max_turns + 1):
        speaker = speakers[current_idx]
        listener = speakers[1 - current_idx]

        rec = TurnRecord(
            turn=turn,
            speaker_name=speaker.name,
            listener_name=listener.name,
            incoming_message=incoming,
            response="",
            retrieved_count=0,
            retrieved_block="",
            char_ctx_preamble_present=False,
            drift_score=0.0,
            system_prompt="",
            history_len_after=0,
        )

        # 1. Query TORMENT with the incoming message. Returns hits and
        #    character_context.
        hits: List[Dict[str, Any]] = []
        char_ctx: Dict[str, Any] = {}
        try:
            qresult = torment.query(
                speaker.workspace_id, speaker.agent_id, incoming, top_k=top_k
            )
            hits = (
                qresult.get("hits")
                or qresult.get("results")
                or qresult.get("memories")
                or []
            )
            char_ctx = qresult.get("character_context", {}) or {}
        except Exception as exc:  # noqa: BLE001
            rec.error = f"query_failed: {exc}"

        memory_block = format_memories(hits, top_k)
        char_ctx_block = format_character_context(char_ctx)
        drift_block = format_drift_note(char_ctx)
        rec.retrieved_count = len(hits)
        rec.retrieved_block = memory_block
        rec.char_ctx_preamble_present = bool(
            char_ctx.get("seed_preamble", "").strip()
        )
        try:
            rec.drift_score = float(char_ctx.get("drift_score", 0.0))
        except (TypeError, ValueError):
            rec.drift_score = 0.0

        # 2. Build system prompt — ryuki_chat template + tiny medium note.
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            agent_name=speaker.name,
            character_context=char_ctx_block,
            memory_context=memory_block,
            drift_note=drift_block,
        ).strip()
        system_prompt = f"{system_prompt}\n\n{DIALOGUE_MEDIUM_NOTE}"
        rec.system_prompt = system_prompt

        # 3. Append incoming as a user turn to the speaker's rolling history.
        speaker.conversation.append({"role": "user", "content": incoming})
        if len(speaker.conversation) > HISTORY_CAP:
            speaker.conversation = speaker.conversation[-HISTORY_CAP:]

        # 4. Call provider with the full rolling history.
        response = ""
        try:
            response = adapter.chat(system_prompt, list(speaker.conversation))
        except AdapterUnavailable as exc:
            rec.error = f"adapter_call_failed: {exc}"
            # Roll back the user message we just appended so the next turn
            # doesn't see a user with no assistant reply.
            if speaker.conversation and speaker.conversation[-1]["role"] == "user":
                speaker.conversation.pop()
        except Exception as exc:  # noqa: BLE001
            rec.error = f"adapter_call_unexpected: {exc!r}"
            if speaker.conversation and speaker.conversation[-1]["role"] == "user":
                speaker.conversation.pop()

        rec.response = response

        # 5. Append the reply as an assistant turn (only if we got one).
        if response:
            speaker.conversation.append({"role": "assistant", "content": response})
            if len(speaker.conversation) > HISTORY_CAP:
                speaker.conversation = speaker.conversation[-HISTORY_CAP:]
        rec.history_len_after = len(speaker.conversation)

        # 6 + 7. Ingest. Speaker workspace gets the paired summary; listener
        #        workspace gets a compact observation of what the speaker said
        #        so the listener's TORMENT can retrieve it when they next speak.
        if response:
            try:
                summary = build_summary(
                    speaker_name=speaker.name,
                    listener_name=listener.name,
                    incoming=incoming,
                    reply=response,
                )
                torment.ingest(speaker.workspace_id, speaker.agent_id, summary, step)
            except Exception as exc:  # noqa: BLE001
                rec.error = (rec.error or "") + f" | speaker_ingest_failed: {exc}"
            try:
                observation = build_observation(speaker.name, response)
                torment.ingest(
                    listener.workspace_id, listener.agent_id, observation, step
                )
            except Exception as exc:  # noqa: BLE001
                rec.error = (rec.error or "") + f" | listener_ingest_failed: {exc}"
            step += 1

        # 8. Forensic snapshots + context dump.
        speaker_state = _snapshot_state(torment, speaker, turn, out_dir)
        listener_state = _snapshot_state(torment, listener, turn, out_dir)
        rec.speaker_state_after = speaker_state
        rec.listener_state_after = listener_state

        _save_context_dump(
            speaker=speaker,
            turn=turn,
            system_prompt=system_prompt,
            rolling_history=list(speaker.conversation),
            response=response,
            retrieved_count=rec.retrieved_count,
            out_dir=out_dir,
        )

        # 9. Append timeseries rows for both speakers.
        for sp, state in ((speaker, speaker_state), (listener, listener_state)):
            row = {
                "turn": turn,
                "speaker": sp.name,
                "was_speaker_this_turn": (sp is speaker),
                "agent_id": sp.agent_id,
                "workspace_id": sp.workspace_id,
                "drift_score": state.get("drift_score"),
                "drift_direction": state.get("drift_direction"),
                "core_count": state.get("core_count"),
                "relational_count": state.get("relational_count"),
                "situational_count": state.get("situational_count"),
                "retrieved_count": rec.retrieved_count if sp is speaker else 0,
                "char_ctx_preamble_present": (
                    rec.char_ctx_preamble_present if sp is speaker else None
                ),
                "history_len_after": (
                    rec.history_len_after if sp is speaker else None
                ),
                "error": rec.error if sp is speaker else "",
            }
            timeseries_rows.append(row)

        turns.append(rec)

        # Console status line.
        truncated = (response[:80] + "...") if len(response) > 80 else response
        truncated = truncated.replace("\n", " ")
        print(
            f"[{turn}/{max_turns}] {speaker.name} -> {listener.name} "
            f"(hits={rec.retrieved_count}, preamble={rec.char_ctx_preamble_present}, "
            f"drift={rec.drift_score:+.2f}, hist={rec.history_len_after}) :: {truncated}"
        )

        # 10. Hand off — the response becomes the next character's incoming.
        if not response:
            print(
                f"[warn] empty response from {speaker.name} on turn {turn}; "
                f"ending dialogue early."
            )
            break
        incoming = response
        current_idx = 1 - current_idx

    return turns, timeseries_rows


# ---------------------------------------------------------------------------
# Model selection (mirrors v1/v2 runners)
# ---------------------------------------------------------------------------

def _select_model_for(provider: str) -> str:
    env = os.environ.get("TORMENT_BENCH_MODELS", "").strip()
    if env:
        for pair in env.split(","):
            pair = pair.strip()
            if ":" not in pair:
                continue
            p, m = pair.split(":", 1)
            if p.strip().lower() == provider.lower():
                return m.strip()
    defaults = {
        "anthropic": "claude-sonnet-4-5",
        "openrouter": "google/gemini-2.5-flash",
        "openai": "gpt-4o-mini",
    }
    return defaults.get(provider.lower(), "default")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "TORMENT dialogue bench v3 — ryuki_chat-pattern two-character "
            "runner. Each character runs the same architecture as "
            "examples/ryuki_chat.py, with rolling chat history and TORMENT "
            "character_context as the identity source (not a re-injected "
            "YAML seed)."
        )
    )
    p.add_argument("--matrix", required=True, type=Path,
                   help="Matrix YAML containing character seeds.")
    p.add_argument("--out", required=True, type=Path,
                   help="Output directory root. Timestamped v3_ subdir created.")
    p.add_argument("--character", action="append", default=None, required=True,
                   help="Two character ids from the matrix. Pass --character twice. "
                        "speakers[0] (first --character) receives the opening line "
                        "and replies first.")
    p.add_argument("--max-turns", type=int, default=6,
                   help="Total number of replies in the dialogue. Smoke = 6. "
                        "Do NOT scale to 100 until 6 produces real dialogue.")
    p.add_argument("--provider", default="anthropic",
                   help="Provider adapter (anthropic | openrouter | openai). "
                        "v3 smoke 1 = anthropic; v3 smoke 2 = openrouter for comparison.")
    p.add_argument("--opening-line", required=True,
                   help="Direct quoted speech that speakers[0] receives as their "
                        "first user message. Example: \"You entered as if the room "
                        "had already agreed to become a stage. Did you ask it first?\"")
    p.add_argument("--top-k", type=int, default=TOP_K_DEFAULT,
                   help=f"TORMENT retrieval top_k. Default {TOP_K_DEFAULT} "
                        f"(matches ryuki_chat).")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    matrix = _load_matrix(args.matrix)
    if not args.character or len(args.character) != 2:
        print("[fatal] must pass exactly two --character ids", file=sys.stderr)
        return 1

    dialogue_id = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = args.out / f"v3_{dialogue_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    config_snapshot = {
        "version": "v3.0",
        "dialogue_id": dialogue_id,
        "matrix_path": str(args.matrix),
        "characters": args.character,
        "max_turns": args.max_turns,
        "provider": args.provider,
        "model": _select_model_for(args.provider),
        "top_k": args.top_k,
        "history_cap": HISTORY_CAP,
        "opening_line": args.opening_line,
        "torment_url": (
            os.environ.get("TORMENT_SERVER_URL", "").strip() or TORMENT_URL_DEFAULT
        ),
        "workspace_domains": WORKSPACE_DOMAINS,
        "dialogue_medium_note": DIALOGUE_MEDIUM_NOTE,
    }
    (out_dir / "config_snapshot.json").write_text(
        json.dumps(config_snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    t0 = time.time()
    try:
        turns, timeseries_rows = run_dialogue(
            matrix=matrix,
            character_ids=args.character,
            max_turns=args.max_turns,
            provider_name=args.provider,
            opening_line=args.opening_line,
            out_dir=out_dir,
            top_k=args.top_k,
        )
    except RuntimeError as exc:
        print(f"[fatal] {exc}", file=sys.stderr)
        return 2

    _write_conversation(turns, out_dir)
    _write_state_timeseries(timeseries_rows, out_dir)

    dt = time.time() - t0
    print(f"\n[ok] dialogue complete: {len(turns)} turns in {dt:.1f}s")
    print(f"[ok] output: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
