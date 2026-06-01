"""TORMENT Dialogue Bench v2.0 — smoke runner.

Two TORMENT-seeded characters speak in alternation. Each turn, the speaker
retrieves context from their own workspace via /agent/query, then generates
a response with that context injected into the system prompt. Both
characters' memories are kept in separate workspaces; each ingests both
its own outputs and the other character's outputs (with light speaker
prefix), but retrieval is scoped to the speaker's own workspace.

Central v2 question:
    Can TORMENT grow a shared lived past between two characters over time?

v2.0 smoke target (per GPT, 2026-05-14):
    Veyra + Eland, 6 messages total, snapshot every turn, torment_mediated
    only. If smoke passes → 10 messages → 100 messages → eventually 1000.

bench_mode: "torment_mediated" (only mode supported by this runner).

Hard constraints:
    - No torment_service/ edits.
    - Uses only existing TORMENT HTTP endpoints.
    - Per-turn errors recorded as turn errors (not fatal).
    - context_dumps are the primary forensic artifact — they show what
      TORMENT actually injected into each speaker's prompt each turn.
      Per GPT: "the most important artifact for v2 is the context dump
      per turn."

Output layout:
    out/dialogue_bench/<timestamp>/
        conversation.jsonl
        conversation.txt
        snapshots/turn_NNN_<name>_state.json
        retrieval_dumps/turn_NNN_<name>_context.txt
        scores/state_timeseries.csv
        flags/interesting_moments.json
        config_snapshot.json

Run command (smoke):
    python tools\\run_character_dialogue_bench.py ^
        --matrix tests\\character_truth_matrix.yaml ^
        --out out\\dialogue_bench ^
        --character declared_liar ^
        --character truthful_accidental_lie ^
        --max-turns 6 ^
        --provider openrouter

The TORMENT server must already be running with the recommended config
(TORMENT_PROFILE=companion, TORMENT_EMBED_PROVIDER=st, etc.).
See docs/CHARACTER_TRUTH_BENCH_DESIGN.md §19 for the server setup recipe.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
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
# .env loader (same minimal loader as v1 runner — kept inline to avoid coupling)
# ---------------------------------------------------------------------------

def _load_env_file(path: Path) -> int:
    """Minimal .env loader; shell-exported env wins over file."""
    if not path.exists():
        return 0
    count = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        if not key or key in os.environ:
            continue
        os.environ[key] = val
        count += 1
    return count


# ---------------------------------------------------------------------------
# TORMENT HTTP client (v2 — adds /agent/query needed for torment_mediated mode)
# ---------------------------------------------------------------------------

class TormentClient:
    """Thin HTTP wrapper for the TORMENT FastAPI server.

    v2 adds the .query() method which the dialogue runner uses to fetch
    speaker-scoped context before each generation. Other methods mirror
    v1's TormentClient. Kept inline (not imported from v1) so this runner
    does not modify v1 code.
    """

    def __init__(self, base_url: str, timeout_s: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _post(self, path: str, body: dict) -> dict:
        url = f"{self.base_url}{path}"
        r = requests.post(url, json=body, timeout=self.timeout_s)
        if r.status_code >= 400:
            raise RuntimeError(f"TORMENT POST {path} -> {r.status_code}: {r.text[:400]}")
        return r.json()

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{path}"
        r = requests.get(url, params=params or {}, timeout=self.timeout_s)
        if r.status_code >= 400:
            raise RuntimeError(f"TORMENT GET {path} -> {r.status_code}: {r.text[:400]}")
        return r.json()

    def health_check(self) -> dict:
        return self._get("/health")

    def create_workspace(self, workspace_id: str) -> dict:
        # Idempotent server-side.
        return self._post("/workspace/create", {"workspace_id": workspace_id})

    def create_agent(
        self, workspace_id: str, agent_id: str, seed: Optional[dict]
    ) -> dict:
        body: Dict[str, Any] = {"workspace_id": workspace_id, "agent_id": agent_id}
        if seed is not None:
            body["seed"] = seed
        return self._post("/agent/create", body)

    def ingest(
        self, workspace_id: str, agent_id: str, text: str, step: int
    ) -> dict:
        return self._post(
            "/agent/ingest",
            {
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "text": text,
                "step": step,
            },
        )

    def query(
        self,
        workspace_id: str,
        agent_id: str,
        query_text: str,
        top_k: int = 8,
    ) -> dict:
        """Retrieve TORMENT-scoped context for the speaker. The shape of the
        returned dict is whatever fabric.query() emits — typically includes
        a 'memories'/'results'/'items' list of retrieved memory dicts plus
        possibly character_context, retrieval metadata, etc.
        """
        return self._post(
            "/agent/query",
            {
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "query": query_text,
                "top_k": top_k,
                "explain": False,
                "continuity_debug": False,
            },
        )

    def character_state(self, workspace_id: str, agent_id: str) -> dict:
        return self._get(
            f"/agent/{agent_id}/character/state",
            params={"workspace_id": workspace_id},
        )


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Speaker:
    """A single character participant in the dialogue. Wraps the matrix
    character data plus the per-dialogue workspace and agent ids."""
    character_id: str
    name: str
    persona_seed: str
    workspace_id: str
    agent_id: str
    other_name: str = ""  # filled in after both speakers are constructed


@dataclass
class TurnRecord:
    turn: int
    speaker_name: str
    listener_name: str
    incoming_message: str
    response: str
    retrieved_count: int
    retrieved_block: str  # the formatted retrieval text the speaker actually saw
    system_prompt: str
    speaker_state_after: Dict[str, Any] = field(default_factory=dict)
    listener_state_after: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Matrix loading
# ---------------------------------------------------------------------------

def _load_matrix(matrix_path: Path) -> dict:
    if not matrix_path.exists():
        raise FileNotFoundError(f"Matrix YAML not found: {matrix_path}")
    raw = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Matrix YAML must be a mapping at top level: {matrix_path}")
    return raw


def _find_character(matrix: dict, character_id: str) -> dict:
    for c in matrix.get("characters", []):
        if c.get("id") == character_id:
            return c
    raise ValueError(
        f"Character id '{character_id}' not in matrix. "
        f"Known ids: {[c.get('id') for c in matrix.get('characters', [])]}"
    )


# ---------------------------------------------------------------------------
# Retrieval formatting
# ---------------------------------------------------------------------------

def _format_retrieved_context(
    query_result: Any, max_items: int = 5
) -> Tuple[str, int]:
    """Turn the /agent/query response into a human-readable block for the
    system prompt. Returns (formatted_text, count_of_items).

    The TORMENT query response shape can vary, so we try several common
    field names: 'memories', 'results', 'items'. Each item may be a dict
    with 'summary' or 'text', or a plain string. Trim individual memories
    to ~280 chars so the prompt doesn't balloon.

    Returns empty string when nothing surfaced — _build_system_prompt
    handles the empty case by omitting the memory section entirely.

    Speaker prefixes ("Glass Saint: ...", "Veyra: ...") on retrieved
    memories are PRESERVED here, not stripped. They carry provenance
    that the model uses to distinguish what each character said. The
    v2.3 attempt to strip them caused retrieved text to float free of
    attribution and the model began echoing phrases as its own voice
    (turns 1-19 of 20260514_200602 collapsed into prefix-less phrase
    repetition). Storage and display now agree: prefixes stay.
    """
    if not isinstance(query_result, dict):
        return "", 0
    items = (
        query_result.get("memories")
        or query_result.get("results")
        or query_result.get("items")
        or []
    )
    if not items:
        return "", 0
    lines = []
    for m in items[:max_items]:
        if isinstance(m, dict):
            txt = m.get("summary") or m.get("text") or ""
        else:
            txt = str(m)
        txt = txt.strip()
        if not txt:
            continue
        if len(txt) > 280:
            txt = txt[:277] + "..."
        lines.append(f"- {txt}")
    if not lines:
        return "", 0
    return "\n".join(lines), len(lines)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_system_prompt(persona_seed: str, retrieved_block: str) -> str:
    """Identity seed + optional memory section, in natural language. Patched
    2026-05-14 per GPT: no `=== ===` section headers, because the model was
    echoing them into its own outputs (turns 3/5/10 of the 20260514_190550
    run started with `=== Veyra's response to Eland ===`). Natural language
    framing doesn't teach the model a format to mimic.

    When retrieval surfaced nothing, the memory section is omitted entirely
    rather than substituting a placeholder string the model might also
    learn to echo back.
    """
    seed = persona_seed.strip()
    mem = retrieved_block.strip()
    if not mem:
        return seed
    return (
        f"{seed}\n"
        "\n"
        "What you remember in this moment:\n"
        f"{mem}\n"
    )


# ---------------------------------------------------------------------------
# Snapshot + context dump writers
# ---------------------------------------------------------------------------

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
    user_message: str,
    response: str,
    retrieved_count: int,
    out_dir: Path,
) -> None:
    """The forensic artifact GPT named as the most important: shows exactly
    what the speaker saw before generating, and what they then said. If
    TORMENT is bringing earlier shared moments back into the speech, this
    is where we'll see it.
    """
    dump_dir = out_dir / "retrieval_dumps"
    dump_dir.mkdir(parents=True, exist_ok=True)
    safe_name = speaker.name.lower().replace(" ", "_")
    fname = dump_dir / f"turn_{turn:03d}_{safe_name}_context.txt"
    body = (
        f"=== TURN {turn} — speaker: {speaker.name}"
        f" (workspace={speaker.workspace_id}, retrieved_count={retrieved_count}) ===\n\n"
        f"=== SYSTEM PROMPT (identity + memory) ===\n"
        f"{system_prompt}\n"
        f"\n=== USER MESSAGE ===\n"
        f"{user_message}\n"
        f"\n=== ASSISTANT RESPONSE ===\n"
        f"{response}\n"
    )
    fname.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Interesting-moment alerts (simple deltas, v2.0 only)
# ---------------------------------------------------------------------------

def _detect_interesting_moments(
    timeseries_rows: List[Dict[str, Any]],
    drift_threshold: float = 0.1,
    retrieval_threshold: int = 3,
) -> List[Dict[str, Any]]:
    """Simple delta-based alerts. GPT-spec for v2.0: don't try to automate
    meaning yet; just flag where state changed unexpectedly so a human
    reviewer knows where to look.

    Patched 2026-05-14 per GPT: only compare each speaker against their own
    previous SPEAKING turn (skip listener rows). Otherwise the natural
    speaker/listener alternation on retrieved_count triggers a spurious
    alert every single turn (smoke run had 10 such false alerts on 6 turns).
    """
    alerts: List[Dict[str, Any]] = []
    by_speaker: Dict[str, List[Dict[str, Any]]] = {}
    for row in timeseries_rows:
        # Filter: only include rows where the speaker was the active speaker
        # this turn. Listener rows would create false retrieved_count deltas
        # against the prior speaking turn.
        if not row.get("was_speaker_this_turn"):
            continue
        by_speaker.setdefault(row["speaker"], []).append(row)
    for speaker, rows in by_speaker.items():
        rows.sort(key=lambda r: r["turn"])
        for i in range(1, len(rows)):
            prev, cur = rows[i - 1], rows[i]
            # drift jump
            try:
                d_prev = float(prev.get("drift_score") or 0.0)
                d_cur = float(cur.get("drift_score") or 0.0)
                if abs(d_cur - d_prev) >= drift_threshold:
                    alerts.append({
                        "type": "drift_jump",
                        "speaker": speaker,
                        "turn": cur["turn"],
                        "delta": d_cur - d_prev,
                        "from": d_prev,
                        "to": d_cur,
                    })
            except (TypeError, ValueError):
                pass
            # retrieval count change
            try:
                r_prev = int(prev.get("retrieved_count") or 0)
                r_cur = int(cur.get("retrieved_count") or 0)
                if abs(r_cur - r_prev) >= retrieval_threshold:
                    alerts.append({
                        "type": "retrieval_count_change",
                        "speaker": speaker,
                        "turn": cur["turn"],
                        "delta": r_cur - r_prev,
                        "from": r_prev,
                        "to": r_cur,
                    })
            except (TypeError, ValueError):
                pass
    return alerts


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _write_conversation(
    turns: List[TurnRecord], out_dir: Path
) -> None:
    """Two views of the conversation: JSONL (one object per turn, machine-
    readable) and TXT (human-readable transcript)."""
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
    timeseries_rows: List[Dict[str, Any]], out_dir: Path
) -> None:
    scores_dir = out_dir / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    if not timeseries_rows:
        return
    fields = [
        "turn", "speaker", "was_speaker_this_turn", "agent_id", "workspace_id",
        "seed_motif_id", "drift_score", "drift_direction",
        "core_count", "relational_count", "situational_count",
        "retrieved_count", "error",
    ]
    csv_path = scores_dir / "state_timeseries.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(timeseries_rows)


def _write_flags(alerts: List[Dict[str, Any]], out_dir: Path) -> None:
    flag_dir = out_dir / "flags"
    flag_dir.mkdir(parents=True, exist_ok=True)
    (flag_dir / "interesting_moments.json").write_text(
        json.dumps({"alerts": alerts}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Speaker construction
# ---------------------------------------------------------------------------

def _build_speakers(
    matrix: dict,
    character_ids: List[str],
    dialogue_id: str,
    workspace_prefix: str,
    agent_prefix: str,
) -> List[Speaker]:
    if len(character_ids) != 2:
        raise ValueError(
            f"Dialogue bench requires exactly 2 characters; got {len(character_ids)}: {character_ids}"
        )
    speakers: List[Speaker] = []
    for cid in character_ids:
        c = _find_character(matrix, cid)
        name = c.get("name", cid)
        # Separate workspaces per GPT spec — each character has own memory basin.
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


def _init_agents(torment: TormentClient, speakers: List[Speaker]) -> Optional[str]:
    """Create workspace + agent for each speaker. Returns None on success
    or an error string on failure."""
    for s in speakers:
        try:
            torment.create_workspace(s.workspace_id)
        except Exception as exc:  # noqa: BLE001
            return f"create_workspace failed for {s.workspace_id}: {exc}"
        seed_payload = {
            "seed_text": s.persona_seed.strip(),
            "seed_id": f"{s.character_id}_v1",
            "character_name": s.name,
        }
        try:
            torment.create_agent(s.workspace_id, s.agent_id, seed=seed_payload)
        except Exception as exc:  # noqa: BLE001
            return f"create_agent failed for {s.agent_id}: {exc}"
    return None


# ---------------------------------------------------------------------------
# Main dialogue loop
# ---------------------------------------------------------------------------

# Per-character asymmetric relational openers (GPT-approved v2.1, 2026-05-14).
# Replaces the earlier single philosophical opener which produced resonance
# loops in the 10-turn smoke (both characters were asked about their truth-
# modes, then spiraled into mutual metaphor-trading). These create *stance*
# rather than *thesis* — curiosity / mild suspicion / relational tension —
# and let essence emerge through behavior rather than direct philosophical
# declaration.
#
# Turn 1: first speaker receives their opener as the user message.
# Turn 2: second speaker receives their opener stance PLUS the first
#         speaker's actual reply. Both are wrapped in marked sections.
# Turn 3+: no opener scaffolding; standard "Message from X" framing only.
DEFAULT_OPENERS: Dict[str, str] = {
    # Veyra meeting Eland — curiosity about his carefulness.
    "declared_liar": (
        "You meet a man whose careful way of speaking makes you curious. "
        "There is something in him that seems unfinished, as if he is "
        "still revising himself while he speaks. You want to know who he "
        "is, and what wound taught him to choose his words so carefully."
    ),
    # Eland meeting Veyra — intrigued but cautious.
    "truthful_accidental_lie": (
        "You meet a woman whose words are beautiful, but not easy to "
        "verify. She seems to turn facts into something warmer and less "
        "stable. You are intrigued by her, but you are not yet sure "
        "whether she is revealing truth or disguising it."
    ),
    # Glass Saint meeting Veyra — watching the line between play and
    # presumption (GPT-approved 2026-05-14 for the friction-test pair).
    "manipulative_boundary_tester": (
        "You meet a woman whose words turn every answer into a "
        "performance. You are intrigued by her, but you are watching the "
        "line between play and presumption."
    ),
}

# Fallback for any character_id not in DEFAULT_OPENERS. Minimal — just
# enough to start the encounter, not enough to bias the dialogue toward
# any particular relational stance.
FALLBACK_OPENER = (
    "You meet another character. You don't know them yet. Speak to them."
)


def _opener_for(character_id: str, overrides: Dict[str, str]) -> str:
    """Return the opener stance for a character. CLI overrides win over
    DEFAULT_OPENERS, which wins over FALLBACK_OPENER."""
    if character_id in overrides:
        return overrides[character_id]
    if character_id in DEFAULT_OPENERS:
        return DEFAULT_OPENERS[character_id]
    print(
        f"[warn] no opener defined for character '{character_id}'; "
        f"using fallback. Add to DEFAULT_OPENERS in this file or pass "
        f"--opener {character_id}:'<text>' for a real run."
    )
    return FALLBACK_OPENER


def run_dialogue(
    matrix: dict,
    character_ids: List[str],
    max_turns: int,
    provider_name: str,
    out_dir: Path,
    opener_overrides: Optional[Dict[str, str]] = None,
    workspace_prefix: str = "dialogue",
    agent_prefix: str = "dlg_",
) -> Tuple[List[TurnRecord], List[Dict[str, Any]]]:
    overrides = opener_overrides or {}
    # Provider adapter (built once, fails early if missing key/SDK).
    model = _select_model_for(provider_name)
    try:
        adapter: ProviderAdapter = get_adapter(provider_name, model)
    except AdapterUnavailable as exc:
        raise RuntimeError(f"adapter setup failed: {exc}")

    # Speakers + TORMENT setup.
    dialogue_id = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    torment_url = (
        os.environ.get("TORMENT_SERVER_URL", "").strip()
        or "http://127.0.0.1:8787"
    )
    torment = TormentClient(torment_url)
    speakers = _build_speakers(
        matrix=matrix,
        character_ids=character_ids,
        dialogue_id=dialogue_id,
        workspace_prefix=workspace_prefix,
        agent_prefix=agent_prefix,
    )

    err = _init_agents(torment, speakers)
    if err:
        raise RuntimeError(f"TORMENT init failed: {err}")

    print(f"[ok] both agents created with seed pipeline; dialogue_id={dialogue_id}")
    print(f"[ok] speaker[0]={speakers[0].name} ({speakers[0].workspace_id})")
    print(f"[ok] speaker[1]={speakers[1].name} ({speakers[1].workspace_id})")

    # Initial state snapshot (turn 0).
    _snapshot_state(torment, speakers[0], 0, out_dir)
    _snapshot_state(torment, speakers[1], 0, out_dir)

    turns: List[TurnRecord] = []
    timeseries_rows: List[Dict[str, Any]] = []
    step = 0
    current_idx = 0  # speaker[0] (e.g., Veyra) starts per GPT spec.
    incoming = ""    # populated after turn 1; on turn 1 the opener is used

    for turn in range(1, max_turns + 1):
        speaker = speakers[current_idx]
        listener = speakers[1 - current_idx]

        # Determine the speaker's opener stance (used on turns 1 and 2).
        speaker_opener_stance = _opener_for(speaker.character_id, overrides)

        # Per GPT v2.1 spec, three different message structures by turn index:
        # - Turn 1: just the speaker's opener stance (first speaker meets nobody yet)
        # - Turn 2: speaker's opener stance + the first speaker's actual reply
        # - Turn 3+: standard "Message from X" framing only
        # The retrieval_query is what we use to fetch TORMENT context — semantically
        # "what is being said to me." On turn 1 the opener is the only thing the
        # speaker has, so it doubles as query. On turn 2+ the prior message is the
        # query (the opener stance is internal framing, not retrievable context).
        if turn == 1:
            retrieval_query = speaker_opener_stance
            user_message_text = speaker_opener_stance
            incoming_for_record = speaker_opener_stance  # what the speaker "received"
        elif turn == 2:
            retrieval_query = incoming
            # Natural-language transcript style. No === section headers —
            # the model echoes them. Stance is plain sentences; the other
            # speaker's message is introduced with "{name} says:" + quoted
            # text. GPT-approved format (2026-05-14).
            user_message_text = (
                f"{speaker_opener_stance.strip()}\n"
                "\n"
                f"{speaker.other_name} says:\n"
                f"\"{incoming.strip()}\""
            )
            incoming_for_record = incoming
        else:
            retrieval_query = incoming
            # Turn 3+: just the other speaker's message in transcript style.
            # No opener scaffolding, no section headers.
            user_message_text = (
                f"{speaker.other_name} says:\n"
                f"\"{incoming.strip()}\""
            )
            incoming_for_record = incoming

        rec = TurnRecord(
            turn=turn,
            speaker_name=speaker.name,
            listener_name=listener.name,
            incoming_message=incoming_for_record,
            response="",
            retrieved_count=0,
            retrieved_block="",
            system_prompt="",
        )

        # 1. Retrieve TORMENT context from speaker's own workspace.
        # top_k=5: the coherent baseline value. v2.3 tried top_k=3 + strip
        # prefix in a single change; together they caused echo collapse
        # (orphaned phrases, name-soup, one-word turns). Reverted to the
        # working configuration. If atmospheric resonance reasserts at
        # this setting, the next intervention is at the conversation-
        # generation layer (openers, model choice), not retrieval shape.
        retrieved_block = ""
        retrieved_count = 0
        try:
            qresult = torment.query(
                speaker.workspace_id, speaker.agent_id, retrieval_query, top_k=5
            )
            retrieved_block, retrieved_count = _format_retrieved_context(qresult)
        except Exception as exc:  # noqa: BLE001
            retrieved_block = f"[retrieval error: {exc}]"
            retrieved_count = 0
        rec.retrieved_count = retrieved_count
        rec.retrieved_block = retrieved_block

        # 2. Build system prompt (identity + memory). The user_message_text
        # was constructed above per turn-index.
        system_prompt = _build_system_prompt(speaker.persona_seed, retrieved_block)
        user_message = user_message_text
        rec.system_prompt = system_prompt

        # 3. Call provider.
        try:
            response = adapter.chat(
                system_prompt, [{"role": "user", "content": user_message}]
            )
        except AdapterUnavailable as exc:
            rec.error = f"adapter_call_failed: {exc}"
            response = ""
        except Exception as exc:  # noqa: BLE001
            rec.error = f"adapter_call_unexpected: {exc!r}"
            response = ""
        rec.response = response

        # 4. Ingest into BOTH workspaces with a light "Name: ..." speaker
        #    prefix (per GPT — preserves provenance without dominating
        #    embeddings as a meta-format label).
        if response:
            ingest_text = f"{speaker.name}: {response}"
            for sp in speakers:
                try:
                    torment.ingest(sp.workspace_id, sp.agent_id, ingest_text, step)
                except Exception as exc:  # noqa: BLE001
                    rec.error = (rec.error or "") + f" | ingest_failed[{sp.name}]: {exc}"
            step += 1

        # 5. Snapshot both speakers' state after the turn.
        speaker_state = _snapshot_state(torment, speaker, turn, out_dir)
        listener_state = _snapshot_state(torment, listener, turn, out_dir)
        rec.speaker_state_after = speaker_state
        rec.listener_state_after = listener_state

        # 6. Save the per-turn forensic context dump.
        _save_context_dump(
            speaker=speaker,
            turn=turn,
            system_prompt=system_prompt,
            user_message=user_message,
            response=response,
            retrieved_count=retrieved_count,
            out_dir=out_dir,
        )

        # 7. Append timeseries rows (one per speaker, captures both at this turn).
        # `was_speaker_this_turn` distinguishes the active speaker from the
        # listener — used by the alert detector to avoid flagging natural
        # alternation as anomalies (GPT-approved patch, 2026-05-14).
        for sp, state in ((speaker, speaker_state), (listener, listener_state)):
            row = {
                "turn": turn,
                "speaker": sp.name,
                "was_speaker_this_turn": (sp is speaker),
                "agent_id": sp.agent_id,
                "workspace_id": sp.workspace_id,
                "seed_motif_id": state.get("seed_motif_id"),
                "drift_score": state.get("drift_score"),
                "drift_direction": state.get("drift_direction"),
                "core_count": state.get("core_count"),
                "relational_count": state.get("relational_count"),
                "situational_count": state.get("situational_count"),
                # retrieved_count only applies to the speaker at this turn,
                # not the listener. We log it as 0 for the listener so the
                # column is comparable.
                "retrieved_count": retrieved_count if sp is speaker else 0,
                "error": rec.error if sp is speaker else "",
            }
            timeseries_rows.append(row)

        turns.append(rec)

        # Console status line.
        truncated = (response[:80] + "...") if len(response) > 80 else response
        truncated = truncated.replace("\n", " ")
        print(
            f"[{turn}/{max_turns}] {speaker.name} -> {listener.name} "
            f"(retrieved={retrieved_count}) :: {truncated}"
        )

        # 8. Hand off — the other speaker's next "incoming" is this response.
        if not response:
            # If the model failed, end the dialogue rather than loop on empty.
            print(f"[warn] empty response from {speaker.name} on turn {turn}; ending dialogue early.")
            break
        incoming = response
        current_idx = 1 - current_idx

    return turns, timeseries_rows


# ---------------------------------------------------------------------------
# Model selection (mirrors v1 runner)
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
        "anthropic": "claude-sonnet-4-6",
        "openrouter": "google/gemini-2.5-flash",
        "openai": "gpt-4o-mini",
    }
    return defaults.get(provider.lower(), "default")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="TORMENT dialogue bench v2.0 — torment_mediated two-character runner."
    )
    p.add_argument(
        "--matrix",
        required=True,
        type=Path,
        help="Matrix YAML (same file the v1 bench uses; only the characters block is read).",
    )
    p.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output directory root. A timestamped subdir is created under this.",
    )
    p.add_argument(
        "--character",
        action="append",
        default=None,
        required=True,
        help="Two character ids from the matrix. Pass twice. Speaker[0] (first) opens. "
             "v2.0 smoke default: --character declared_liar --character truthful_accidental_lie",
    )
    p.add_argument(
        "--max-turns",
        type=int,
        default=6,
        help="Total number of messages in the dialogue. v2.0 smoke = 6. Scale up only after smoke passes.",
    )
    p.add_argument(
        "--provider",
        default="openrouter",
        help="Provider adapter name (openrouter | anthropic | openai).",
    )
    p.add_argument(
        "--opener",
        action="append",
        default=None,
        help="Per-character opener override. Format: character_id:text. May be "
             "passed multiple times. Defaults are in DEFAULT_OPENERS at the top "
             "of this file (Veyra and Eland have GPT-approved relational openers).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Load matrix, ping TORMENT, build adapter, but make no LLM calls.",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    loaded = _load_env_file(Path.cwd() / ".env")
    if loaded:
        print(f"[ok] loaded {loaded} variable(s) from .env")

    try:
        matrix = _load_matrix(args.matrix)
    except Exception as exc:
        print(f"[fatal] failed to load matrix: {exc}", file=sys.stderr)
        return 1

    if not args.character or len(args.character) != 2:
        print(
            "[fatal] dialogue bench requires exactly two --character args. "
            "Example: --character declared_liar --character truthful_accidental_lie",
            file=sys.stderr,
        )
        return 1

    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = args.out / timestamp
    out_root.mkdir(parents=True, exist_ok=True)

    # Server health check (skip in dry-run only at the call level — we still
    # try because torment_mediated needs TORMENT alive).
    torment_url = (
        os.environ.get("TORMENT_SERVER_URL", "").strip()
        or "http://127.0.0.1:8787"
    )
    torment = TormentClient(torment_url)
    try:
        health = torment.health_check()
        print(f"[ok] TORMENT server reachable at {torment_url}: profile={health.get('profile', {}).get('name', '?')}, "
              f"embedder={health.get('embedder', {}).get('provider', '?')}, "
              f"degraded={health.get('embedder_degraded', '?')}")
    except Exception as exc:
        print(f"[fatal] TORMENT server not reachable at {torment_url}: {exc}", file=sys.stderr)
        return 1

    # Parse --opener overrides into a {character_id: text} dict.
    opener_overrides: Dict[str, str] = {}
    for raw in (args.opener or []):
        if ":" not in raw:
            print(
                f"[fatal] --opener arg must be 'character_id:text'; got: {raw!r}",
                file=sys.stderr,
            )
            return 1
        cid, text = raw.split(":", 1)
        opener_overrides[cid.strip()] = text.strip()

    # Build the effective openers map (defaults + CLI overrides) for the
    # config snapshot so future-us can see exactly what was used.
    effective_openers: Dict[str, str] = {}
    for cid in args.character:
        effective_openers[cid] = _opener_for(cid, opener_overrides)

    # Config snapshot (env keys redacted to booleans).
    config_snapshot = {
        "bench_mode": "torment_mediated",
        "matrix_path": str(args.matrix),
        "server_url": torment_url,
        "characters": list(args.character),
        "max_turns": args.max_turns,
        "provider": args.provider,
        "openers": effective_openers,
        "env_provider_keys_present": {
            "ANTHROPIC_API_KEY": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "OPENROUTER_API_KEY": bool(os.environ.get("OPENROUTER_API_KEY")),
            "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        },
        "started_at": timestamp,
    }
    (out_root / "config_snapshot.json").write_text(
        json.dumps(config_snapshot, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if args.dry_run:
        # Build adapter once to surface auth/SDK errors early.
        model = _select_model_for(args.provider)
        try:
            get_adapter(args.provider, model)
            print(f"[dry-run] adapter ok: {args.provider}:{model}")
        except AdapterUnavailable as exc:
            print(f"[dry-run] adapter UNAVAILABLE: {args.provider}:{model} -> {exc}")
        print(f"[dry-run] no LLM calls made. Output dir: {out_root}")
        return 0

    # Run the dialogue.
    t0 = time.time()
    try:
        turns, timeseries_rows = run_dialogue(
            matrix=matrix,
            character_ids=list(args.character),
            max_turns=args.max_turns,
            provider_name=args.provider,
            out_dir=out_root,
            opener_overrides=opener_overrides,
        )
    except Exception as exc:
        print(f"[fatal] dialogue run failed: {exc!r}", file=sys.stderr)
        traceback.print_exc()
        return 2

    # Write outputs.
    _write_conversation(turns, out_root)
    _write_state_timeseries(timeseries_rows, out_root)
    alerts = _detect_interesting_moments(timeseries_rows)
    _write_flags(alerts, out_root)

    dt = time.time() - t0
    print(f"[ok] dialogue complete: {len(turns)} turns in {dt:.1f}s")
    print(f"[ok] alerts surfaced: {len(alerts)}")
    print(f"[ok] output: {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# end of v2.0 smoke runner
