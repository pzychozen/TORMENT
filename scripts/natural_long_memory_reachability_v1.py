from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LABEL = "natural_long_memory_reachability_v1"
SUBTYPE = "SCRIPTED_LIVED_USE_REACHABILITY_WITH_UNCHANGED_PRODUCTION_THRESHOLDS"
AUTHORIZED_HEAD = "6b1c3cc6ca53f074d66a146ae04532c7d703fc55"
EXPECTED_SUBJECT = "test(lived-use): preserve warmth feedback characterization"
REQUIRED_PYTHON = Path(r"C:\Users\Notandi\miniconda3\envs\torment\python.exe")

EXPECTED_EMBEDDER = {
    "provider": "st",
    "model": "BAAI/bge-small-en-v1.5",
    "dim": 384,
}

WORKSPACE_PREFIX = "nlmr_v1"
AGENT_ID = "eira_voss"
DOMAIN_ID = "personal"
USER_NAME = "Hilmir"
CHARACTER_NAME = "Eira Voss"

DEFAULT_OFF_EXCHANGES = 250
ENABLED_EXCHANGES = 1500
PROGRESS_EVERY = 50

TRAJECTORY_T1 = "T1_DISTINCT_EPISODES"
TRAJECTORY_T2 = "T2_RECURRING_TOPICS"
TRAJECTORY_T3 = "T3_MIXED_CHARACTER_CONVERSATION"

CONDITION_A = "condition_a_default_off"
CONDITION_T1 = "condition_b_t1_distinct_episodes"
CONDITION_T2 = "condition_b_t2_recurring_topics"
CONDITION_T3 = "condition_b_t3_mixed_character"

SCRIPT_REL = Path("scripts") / "natural_long_memory_reachability_v1.py"
OUTPUT_REL_PREFIX = Path("outputs") / "experiments" / LABEL

THRESHOLD_ENV_VARS = (
    "TORMENT_COMPRESS_MIN_STEP",
    "TORMENT_COMPRESS_MIN_AGE",
    "TORMENT_COMPRESS_MAX_CANDIDATES",
    "TORMENT_COMPRESS_DEEP_THRESHOLD",
    "TORMENT_COMPRESS_AGE_THRESHOLD",
    "TORMENT_COMPRESS_TEAR_EMERGENCY",
    "TORMENT_COMPRESS_SHORT_STRENGTH_MULT",
    "TORMENT_COMPRESS_LONG_STRENGTH",
    "TORMENT_COMPRESS_RELATIONAL_MULT",
    "TORMENT_COMPRESS_ECHO_MULT",
    "TORMENT_COMPRESS_TOOL_RESULT_MULT",
    "TORMENT_COMPRESS_TOOL_RESULT_SCORE_MULT",
    "TORMENT_COMPRESS_ECHO_DEEP_AGE",
    "TORMENT_COMPRESS_COUNT_THRESHOLD",
    "TORMENT_COMPRESS_STEP_INTERVAL",
    "TORMENT_COMPRESS_FALLBACK_COOLDOWN",
    "TORMENT_COMPRESS_PERIODIC_FLOOR",
    "TORMENT_MAX_PRIVATE_MEMORIES",
    "TORMENT_HARD_CAP_TARGET_RATIO",
    "TORMENT_REINFORCE_SIM_THRESHOLD",
)

ENV_SUBSET_KEYS = (
    "TORMENT_PROFILE",
    "TORMENT_DATA_DIR",
    "TORMENT_TEST_CONDITION",
    "TORMENT_SQLITE_INDEX_ENABLE",
    "TORMENT_CHARACTER_ENABLE",
    "TORMENT_THINKING_ADVISORY",
    "TORMENT_SPINE_ENABLE",
    "TORMENT_IDENTITY_SENSITIVE",
    "TORMENT_COMPRESS_ENABLE",
    "TORMENT_ARCHIVE_RECALL",
    "TORMENT_LIVE_SOCIAL",
    "TORMENT_CONTEXTUAL_ABSTENTION",
    "TORMENT_SRG_ENABLE",
    "TORMENT_SRG_COGNITION",
    "TORMENT_HIVEMIND_ENABLE",
    "TORMENT_ARCHIVIST_WRITEBACK",
    "TORMENT_COGNITION_SHAPING_V2",
    "TORMENT_COGNITION_CORE_SHAPING_V1",
    "TORMENT_GEOMETRIC_MEMORY_SHAPING_V1",
    "TORMENT_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1",
    "TORMENT_RELATIONAL_AMBIGUITY_PROMINENCE_V1",
    "TORMENT_AMBIGUITY_CONTEXT_DIVERSITY_V1",
    "TORMENT_PARTICIPATION_GUIDANCE_V1",
    "TORMENT_EMBED_PROVIDER",
    "TORMENT_EMBED_MODEL",
    "TORMENT_EMBED_DEVICE",
    "TORMENT_EMBED_STRICT",
    "TORMENT_AUTH_ENABLE",
)


class StageStop(RuntimeError):
    pass


class JsonlTail:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.position = 0

    def read_new(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            handle.seek(self.position)
            for line in handle:
                if not line.strip():
                    continue
                rows.append(json.loads(line))
            self.position = handle.tell()
        return rows


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run_cmd(args: List[str], *, cwd: Path) -> Dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def require_cmd(args: List[str], *, cwd: Path) -> str:
    result = run_cmd(args, cwd=cwd)
    if int(result["returncode"]) != 0:
        raise StageStop(
            f"Command failed ({result['returncode']}): {' '.join(args)}\n"
            f"stdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"
        )
    return str(result["stdout"])


def git_snapshot(root: Path) -> Dict[str, Any]:
    return {
        "status_short_branch": run_cmd(["git", "status", "--short", "--branch"], cwd=root),
        "status_porcelain": run_cmd(["git", "status", "--porcelain=v1"], cwd=root),
        "head": run_cmd(["git", "rev-parse", "HEAD"], cwd=root),
        "origin_main": run_cmd(["git", "rev-parse", "origin/main"], cwd=root),
        "log_1_oneline": run_cmd(["git", "log", "-1", "--oneline"], cwd=root),
    }


def _status_path(line: str) -> str:
    path = line[3:] if len(line) > 3 else ""
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip().strip('"').replace("\\", "/")


def _allowed_dirty_path(path: str) -> bool:
    script = str(SCRIPT_REL).replace("\\", "/")
    output_prefix = str(OUTPUT_REL_PREFIX).replace("\\", "/")
    return (
        path == script
        or path == "outputs/"
        or path.startswith(output_prefix + "/")
    )


def ensure_baseline(root: Path) -> Dict[str, Any]:
    snap = git_snapshot(root)
    if snap["head"]["returncode"] != 0 or snap["head"]["stdout"] != AUTHORIZED_HEAD:
        raise StageStop(f"HEAD mismatch: {snap['head']}")
    if snap["origin_main"]["returncode"] != 0 or snap["origin_main"]["stdout"] != AUTHORIZED_HEAD:
        raise StageStop(f"origin/main mismatch: {snap['origin_main']}")
    if EXPECTED_SUBJECT not in str(snap["log_1_oneline"]["stdout"]):
        raise StageStop(f"Unexpected subject: {snap['log_1_oneline']}")

    disallowed: List[str] = []
    porcelain = str(snap["status_porcelain"]["stdout"] or "")
    for line in porcelain.splitlines():
        if not line.strip():
            continue
        path = _status_path(line)
        if not _allowed_dirty_path(path):
            disallowed.append(line)
    if disallowed:
        raise StageStop(
            "Production or unrelated files are modified; refusing to run: "
            + json.dumps(disallowed, ensure_ascii=False)
        )
    return snap


def ensure_required_python(*, worker: bool = False) -> Dict[str, Any]:
    actual = Path(sys.executable).resolve()
    required = REQUIRED_PYTHON.resolve()
    try:
        ok = actual.samefile(required)
    except Exception:
        ok = str(actual).lower() == str(required).lower()
    if not ok:
        role = "worker" if worker else "harness"
        raise StageStop(f"Run the {role} with {required}; current interpreter is {actual}")
    return {"required": str(required), "actual": str(actual)}


def configure_worker_env(
    base_env: Mapping[str, str],
    *,
    data_root: Path,
    condition_name: str,
    compress_enable: bool,
) -> Tuple[Dict[str, str], Dict[str, Any]]:
    env = dict(base_env)
    removed_threshold_overrides = {key: env.pop(key) for key in THRESHOLD_ENV_VARS if key in env}
    removed_external_model_flags = {}
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        if key in env:
            removed_external_model_flags[key] = env.pop(key)

    env.update(
        {
            "PYTHONIOENCODING": "utf-8",
            "TOKENIZERS_PARALLELISM": "false",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TORMENT_PROFILE": "companion",
            "TORMENT_DATA_DIR": str(data_root.resolve()),
            "TORMENT_EXPECTED_DATA_DIR": str(data_root.resolve()),
            "TORMENT_TEST_CONDITION": f"{LABEL}_{condition_name}",
            "TORMENT_SERVER_LAUNCHER_PATH": str(Path(__file__).resolve()),
            "TORMENT_SQLITE_INDEX_ENABLE": "1",
            "TORMENT_CHARACTER_ENABLE": "1",
            "TORMENT_THINKING_ADVISORY": "1",
            "TORMENT_SPINE_ENABLE": "1",
            "TORMENT_IDENTITY_SENSITIVE": "1",
            "TORMENT_COMPRESS_ENABLE": "1" if compress_enable else "0",
            "TORMENT_ARCHIVE_RECALL": "0",
            "TORMENT_LIVE_SOCIAL": "0",
            "TORMENT_CONTEXTUAL_ABSTENTION": "0",
            "TORMENT_SRG_ENABLE": "0",
            "TORMENT_SRG_COGNITION": "0",
            "TORMENT_HIVEMIND_ENABLE": "0",
            "TORMENT_ARCHIVIST_WRITEBACK": "0",
            "TORMENT_COGNITION_SHAPING_V2": "0",
            "TORMENT_COGNITION_CORE_SHAPING_V1": "0",
            "TORMENT_GEOMETRIC_MEMORY_SHAPING_V1": "0",
            "TORMENT_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1": "0",
            "TORMENT_RELATIONAL_AMBIGUITY_PROMINENCE_V1": "0",
            "TORMENT_AMBIGUITY_CONTEXT_DIVERSITY_V1": "0",
            "TORMENT_PARTICIPATION_GUIDANCE_V1": "0",
            "TORMENT_EMBED_PROVIDER": EXPECTED_EMBEDDER["provider"],
            "TORMENT_EMBED_MODEL": EXPECTED_EMBEDDER["model"],
            "TORMENT_EMBED_DEVICE": "cpu",
            "TORMENT_EMBED_STRICT": "1",
            "TORMENT_AUTH_ENABLE": "0",
        }
    )
    return env, {
        "removed_threshold_env_overrides": removed_threshold_overrides,
        "removed_external_model_flags": removed_external_model_flags,
        "effective_env_subset": {key: env.get(key, "") for key in ENV_SUBSET_KEYS},
    }


def worker_condition_specs() -> Dict[str, Dict[str, Any]]:
    return {
        CONDITION_A: {
            "condition": "A_PRODUCTION_DEFAULT_OFF",
            "trajectory_id": TRAJECTORY_T3,
            "compress_enable": False,
            "max_exchanges": DEFAULT_OFF_EXCHANGES,
            "workspace_id": f"{WORKSPACE_PREFIX}_default_off",
        },
        CONDITION_T1: {
            "condition": "B_ENABLED_UNCHANGED_THRESHOLDS",
            "trajectory_id": TRAJECTORY_T1,
            "compress_enable": True,
            "max_exchanges": ENABLED_EXCHANGES,
            "workspace_id": f"{WORKSPACE_PREFIX}_t1_distinct",
        },
        CONDITION_T2: {
            "condition": "B_ENABLED_UNCHANGED_THRESHOLDS",
            "trajectory_id": TRAJECTORY_T2,
            "compress_enable": True,
            "max_exchanges": ENABLED_EXCHANGES,
            "workspace_id": f"{WORKSPACE_PREFIX}_t2_recurring",
        },
        CONDITION_T3: {
            "condition": "B_ENABLED_UNCHANGED_THRESHOLDS",
            "trajectory_id": TRAJECTORY_T3,
            "compress_enable": True,
            "max_exchanges": ENABLED_EXCHANGES,
            "workspace_id": f"{WORKSPACE_PREFIX}_t3_mixed",
        },
    }


def _choice(values: List[str], index: int, stride: int = 1) -> str:
    return values[(index * stride) % len(values)]


def generate_t1_pair(index: int) -> Dict[str, Any]:
    places = [
        "harbor post office", "basalt greenhouse", "library map room",
        "east market stall", "rainy train platform", "ceramic studio",
        "old astronomy tower", "community bakery", "silver repair kiosk",
        "botanical lecture hall", "ferry ticket window", "north trail shelter",
        "tiny fabric shop", "municipal archive desk", "lighthouse supply shed",
        "blue clinic atrium", "museum courtyard", "riverside chess table",
        "orchard packing room", "winter bus depot",
    ]
    objects = [
        "cobalt notebook", "brass compass", "linen parcel", "green teapot",
        "violet umbrella", "cedar chess set", "porcelain key tag",
        "wool scarf", "amber receipt", "folded route map", "tin of cardamom",
        "silver fountain pen", "orange bicycle light", "mahogany drawer pull",
        "canvas seed bag", "glass paperweight", "blue enamel bowl",
        "weathered camera strap", "copper bookmark", "red train token",
    ]
    people = [
        "Mara", "Jonas", "Ilya", "Sol", "Nadia", "Tomas", "Rina", "Keiko",
        "Arun", "Bea", "Noor", "Emil", "Lena", "Oskar", "Priya", "Mikkel",
        "Sana", "Theo", "Vera", "Yasmin",
    ]
    actions = [
        "sorted old labels", "tested a small latch", "read the posted tide chart",
        "wrapped a fragile gift", "measured a crooked shelf", "copied a recipe",
        "checked the return schedule", "sketched a window hinge",
        "labeled seed trays", "compared two train routes", "found a missing receipt",
        "borrowed a folding stool", "cleaned rain from the sill",
        "set aside a chipped cup", "asked about a concert poster",
        "organized a drawer of tokens", "polished a clouded lens",
        "marked the repair ticket", "noted a cinnamon smell", "folded a wool blanket",
    ]
    followups = [
        "call before noon", "bring a small envelope", "photograph the label",
        "leave a note by the kettle", "check the bus time", "buy extra twine",
        "return the key tag", "write the address carefully", "move it to the hall shelf",
        "ask for the receipt copy", "pack it in the blue bag", "confirm the opening hour",
        "send a short reminder", "bring the spare battery", "keep the paper dry",
        "mark the map corner", "put the token in the dish", "clean the lens cloth",
        "save the recipe card", "take the umbrella back",
    ]
    tones = [
        "quietly amused", "a little rushed", "relieved", "curious",
        "careful", "sun-warmed", "sleepy", "focused", "patient", "surprised",
    ]
    i = index
    obj = _choice(objects, i, 7)
    place = _choice(places, i, 11)
    person = _choice(people, i, 13)
    action = _choice(actions, i, 17)
    follow = _choice(followups, i, 19)
    tone = _choice(tones, i, 23)
    code = f"DISTINCT-{i + 1:04d}"
    user = (
        f"{code}: I was {tone} at the {place} when {person} {action}. "
        f"The concrete thing to remember is the {obj}, and the follow-up is to {follow}."
    )
    assistant = (
        f"I will remember {code} as its own episode: {person} at the {place}, "
        f"the {obj}, and your follow-up to {follow}."
    )
    return {"exchange": i + 1, "user": user, "assistant": assistant}


def generate_t2_pair(index: int) -> Dict[str, Any]:
    topics = [
        {
            "name": "north-window basil",
            "anchor": "the basil pot by the north window",
            "details": [
                "new leaves looked pale after the cloudy week",
                "the saucer needed less water than usual",
                "the cracked clay rim still catches on the curtain",
                "the mint nearby made the shelf smell sharp",
                "the plant leaned toward the morning light again",
            ],
        },
        {
            "name": "Atlas board",
            "anchor": "the Atlas project board",
            "details": [
                "the amber sticky note moved back into the planning column",
                "the invoice card still belongs near the launch checklist",
                "the blue marker was only for unresolved tasks",
                "the calendar strip made the deadline look less vague",
                "the dependency row needs one more pass before review",
            ],
        },
        {
            "name": "Mara walks",
            "anchor": "coffee walks with Mara",
            "details": [
                "she prefers the bakery corner when it rains",
                "she asked for shorter Friday routes",
                "the bench near the tram stop was too windy",
                "the cardamom buns made the late start easier",
                "she wants reminders only after lunch",
            ],
        },
        {
            "name": "green commuter mug",
            "anchor": "the green commuter mug",
            "details": [
                "the lid still clicks twice before sealing",
                "it belongs in the left side pocket of the work bag",
                "the tea stain near the handle has not faded",
                "it should not go through the office dishwasher",
                "the spare gasket is in the narrow kitchen drawer",
            ],
        },
        {
            "name": "Friday piano routine",
            "anchor": "the Friday piano routine",
            "details": [
                "the left-hand warmup works best before dinner",
                "the metronome should stay slower for the second page",
                "the old waltz still needs the same transition repeated",
                "the lamp glare makes the last staff hard to read",
                "the short recording helps compare the ending",
            ],
        },
    ]
    moods = ["steady", "matter-of-fact", "pleased", "a bit tired", "focused", "softly amused"]
    topic = topics[index % len(topics)]
    detail = topic["details"][(index // len(topics)) % len(topic["details"])]
    mood = moods[(index * 3) % len(moods)]
    cycle = (index // len(topics)) + 1
    code = f"RECUR-{index + 1:04d}"
    user = (
        f"{code}: A {mood} update on {topic['anchor']}: {detail}. "
        f"This is cycle {cycle} of that same ongoing topic."
    )
    assistant = (
        f"I will keep {code} connected to {topic['name']}: {detail}, "
        f"with cycle {cycle} as the new lived-use update."
    )
    return {"exchange": index + 1, "user": user, "assistant": assistant}


def generate_t3_pair(index: int) -> Dict[str, Any]:
    patterns = [
        "identity_preference",
        "routine",
        "new_episode",
        "correction",
        "revisit",
        "new_person",
        "object_location",
        "plan_update",
        "small_observation",
        "preference_shift",
    ]
    recurring = [
        "quiet morning planning",
        "the green commuter mug",
        "Mara's coffee walks",
        "the Atlas project board",
        "Friday piano practice",
    ]
    new_places = [
        "bookbinder counter", "river tram", "yellow grocery awning",
        "secondhand camera shelf", "winter garden bench", "ceramic kiln room",
        "city archive lobby", "ferry ramp", "market spice stall", "library lift",
    ]
    new_objects = [
        "linen notebook", "red scarf", "brass tin", "blue train card",
        "cedar box", "silver bookmark", "glass jar", "black rain hat",
        "violet folder", "copper pen",
    ]
    people = ["Mara", "Jonas", "Noor", "Rina", "Theo", "Priya", "Emil", "Lena"]
    pattern = patterns[index % len(patterns)]
    code = f"MIXED-{index + 1:04d}"
    topic = recurring[(index // 2) % len(recurring)]
    place = new_places[(index * 7) % len(new_places)]
    obj = new_objects[(index * 11) % len(new_objects)]
    person = people[(index * 5) % len(people)]
    if pattern == "identity_preference":
        user = f"{code}: I still prefer quiet morning planning before messages, especially when {topic} is active."
        assistant = f"I will remember {code}: quiet morning planning remains your preferred starting mode around {topic}."
    elif pattern == "routine":
        user = f"{code}: Today's routine detail is that {topic} worked better after tea and before opening the laptop."
        assistant = f"I will keep {code} with the routine thread: tea first, laptop later, and {topic} stays easier that way."
    elif pattern == "new_episode":
        user = f"{code}: A new episode happened at the {place}: {person} noticed the {obj} and I decided to bring it home."
        assistant = f"I will store {code} as a new episode at the {place}, involving {person}, the {obj}, and bringing it home."
    elif pattern == "correction":
        user = f"{code}: Correction for {topic}: the useful reminder should be gentle, not urgent, unless I explicitly say it is time-sensitive."
        assistant = f"I will treat {code} as a correction: reminders for {topic} should be gentle unless you mark them urgent."
    elif pattern == "revisit":
        user = f"{code}: I revisited {topic} and the older detail still matters, but today's note adds that the timing should move earlier."
        assistant = f"I will connect {code} to {topic}: the old detail remains historical, and today's update moves the timing earlier."
    elif pattern == "new_person":
        user = f"{code}: {person} is newly relevant because they offered to help with {topic} next week."
        assistant = f"I will remember {code}: {person} is now connected to {topic} as someone who may help next week."
    elif pattern == "object_location":
        user = f"{code}: The {obj} is now on the hallway shelf, not in the kitchen drawer, because I moved it after lunch."
        assistant = f"I will record {code}: the {obj} moved to the hallway shelf after lunch, replacing the kitchen-drawer location."
    elif pattern == "plan_update":
        user = f"{code}: Plan update for {topic}: I want a short check-in after the first step rather than a long review at the end."
        assistant = f"I will keep {code} as the plan update for {topic}: short check-in after step one, not only a long final review."
    elif pattern == "small_observation":
        user = f"{code}: Small observation: the {place} was calmer than usual, and the quiet helped me think about {topic}."
        assistant = f"I will remember {code}: the calmer {place} helped you think through {topic}."
    else:
        user = f"{code}: Preference shift: for {topic}, I now want practical wording first and emotional color second."
        assistant = f"I will update {code}: for {topic}, practical wording comes first and emotional color second."
    return {"exchange": index + 1, "user": user, "assistant": assistant}


def generate_trajectories(max_enabled: int = ENABLED_EXCHANGES) -> Dict[str, Any]:
    return {
        "label": LABEL,
        "subtype": SUBTYPE,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration_boundary": (
            "All scripted exchanges are generated and written before authoritative "
            "condition workers execute; workers load this file and do not adapt text."
        ),
        "trajectory_generation": {
            TRAJECTORY_T1: {
                "rule": "deterministic combinatorial distinct-episode template",
                "max_exchanges": max_enabled,
            },
            TRAJECTORY_T2: {
                "rule": "deterministic recurring-topic cycle over five anchors",
                "max_exchanges": max_enabled,
            },
            TRAJECTORY_T3: {
                "rule": "deterministic mixed companion-style ten-pattern cycle",
                "max_exchanges": max_enabled,
            },
        },
        "trajectories": {
            TRAJECTORY_T1: [generate_t1_pair(i) for i in range(max_enabled)],
            TRAJECTORY_T2: [generate_t2_pair(i) for i in range(max_enabled)],
            TRAJECTORY_T3: [generate_t3_pair(i) for i in range(max_enabled)],
        },
    }


class DirectResponse:
    def __init__(self, status_code: int, data: Any) -> None:
        self.status_code = int(status_code)
        self._data = data
        self.text = json.dumps(data, ensure_ascii=False, sort_keys=True)

    def json(self) -> Any:
        return self._data


class DirectAppClient:
    """Same-thread endpoint caller for app route functions.

    TestClient executes sync FastAPI endpoints in worker threads. The current
    SQLite sidecar uses default same-thread sqlite3 connections, so TestClient
    introduces a harness-only thread mismatch. This adapter keeps endpoint
    function -> Spine -> Fabric behavior in process and on one thread.
    """

    def __init__(self, app_mod: Any) -> None:
        self.app_mod = app_mod

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **_: Any) -> DirectResponse:
        return self._dispatch("GET", path, params=params or {}, payload=None)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> DirectResponse:
        return self._dispatch("POST", path, params=params or {}, payload=json or {})

    def _wrap(self, fn: Any, *args: Any, **kwargs: Any) -> DirectResponse:
        try:
            data = fn(*args, **kwargs)
            if asyncio.iscoroutine(data):
                data = asyncio.run(data)
            return DirectResponse(200, data)
        except Exception as exc:
            status = int(getattr(exc, "status_code", 500) or 500)
            detail = getattr(exc, "detail", str(exc))
            return DirectResponse(status, {"detail": detail, "exception_type": type(exc).__name__})

    def _dispatch(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any],
        payload: Optional[Dict[str, Any]],
    ) -> DirectResponse:
        app_mod = self.app_mod
        if method == "GET" and path == "/health":
            return self._wrap(app_mod.health)
        if method == "GET" and path == "/embedder/check":
            return self._wrap(app_mod.embedder_check)
        if method == "GET" and path == "/config":
            return self._wrap(app_mod.config)
        if method == "GET" and path == "/debug/metrics":
            return self._wrap(
                app_mod.debug_metrics,
                workspace_id=str(params.get("workspace_id", "default")),
                agent_id=params.get("agent_id"),
            )
        if method == "GET" and path.startswith("/workspace/") and path.endswith("/compress/status"):
            parts = path.strip("/").split("/")
            return self._wrap(
                app_mod.compression_status,
                workspace_id=parts[1],
                agent_id=str(params.get("agent_id", "")),
            )
        if method == "GET" and path.startswith("/index/") and path.endswith("/recent"):
            parts = path.strip("/").split("/")
            return self._wrap(
                app_mod.index_recent_memories,
                workspace_id=parts[1],
                agent_id=parts[2],
                limit=int(params.get("limit", 20)),
            )
        if method == "POST" and path == "/workspace/create":
            return self._wrap(app_mod.workspace_create, app_mod.WorkspaceCreateReq(**(payload or {})))
        if method == "POST" and path == "/agent/create":
            return self._wrap(app_mod.agent_create, app_mod.AgentCreateReq(**(payload or {})))
        if method == "POST" and path == "/agent/query":
            return self._wrap(app_mod.query, app_mod.QueryReq(**(payload or {})))
        if method == "POST" and path == "/agent/ingest":
            return self._wrap(app_mod.ingest, app_mod.IngestReq(**(payload or {})), None)
        return DirectResponse(404, {"detail": f"Unhandled direct app route {method} {path}"})


def api_json(client: Any, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
    response = getattr(client, method.lower())(path, **kwargs)
    if response.status_code >= 400:
        raise StageStop(f"{method} {path} returned {response.status_code}: {response.text[:500]}")
    data = response.json()
    if not isinstance(data, dict):
        raise StageStop(f"{method} {path} returned non-object JSON: {data!r}")
    return data


def validate_embedder(health: Mapping[str, Any], check: Mapping[str, Any]) -> Dict[str, Any]:
    observations: Dict[str, Any] = {}
    for name, meta in (("health", health.get("embedder", {})), ("embedder_check", check)):
        if not isinstance(meta, Mapping):
            raise StageStop(f"{name} embedder metadata missing")
        observed = {
            "provider": str(meta.get("provider", "")),
            "model": str(meta.get("model", "")),
            "dim": int(meta.get("dim", 0) or 0),
            "degraded": bool(meta.get("degraded", False)),
        }
        observations[name] = observed
        if observed["provider"] != EXPECTED_EMBEDDER["provider"]:
            raise StageStop(f"{name} embedder provider mismatch: {observed}")
        if observed["model"] != EXPECTED_EMBEDDER["model"]:
            raise StageStop(f"{name} embedder model mismatch: {observed}")
        if observed["dim"] != EXPECTED_EMBEDDER["dim"]:
            raise StageStop(f"{name} embedder dim mismatch: {observed}")
    if bool(health.get("embedder_degraded", False)):
        raise StageStop(f"Health reports degraded embedder: {health}")
    requested = health.get("requested_embedder") or {}
    if not isinstance(requested, Mapping) or requested.get("strict") is not True:
        raise StageStop(f"Requested embedder strict mode not active: {requested}")
    return observations


def resolve_resumed_step_from_recent(response: Mapping[str, Any]) -> int:
    if response.get("ok") is not True:
        raise StageStop(f"Recent index response is not ok=true: {response}")
    results = response.get("results")
    if not isinstance(results, list):
        raise StageStop(f"Recent index response missing results list: {response}")
    if not results:
        return 0
    first = results[0]
    if not isinstance(first, Mapping):
        raise StageStop(f"Recent index first row malformed: {first!r}")
    step = first.get("step")
    if not isinstance(step, int) or step < 0:
        raise StageStop(f"Recent index first row invalid step: {first!r}")
    return int(step)


def top_recent_step(response: Mapping[str, Any]) -> Optional[int]:
    results = response.get("results")
    if not isinstance(results, list) or not results:
        return None
    first = results[0]
    if not isinstance(first, Mapping):
        return None
    try:
        return int(first.get("step"))
    except Exception:
        return None


def agent_paths(data_root: Path, workspace_id: str) -> Dict[str, Path]:
    agent_root = data_root / "workspaces" / workspace_id / "agents" / AGENT_ID
    private_dir = agent_root / "private"
    deep_dir = agent_root / "deep_memory"
    return {
        "agent_root": agent_root,
        "private_dir": private_dir,
        "nodes": private_dir / "nodes.jsonl",
        "compression_log": private_dir / "compression_log.jsonl",
        "deep_dir": deep_dir,
        "deep_memories": deep_dir / "memories.jsonl",
    }


def deep_file_state(paths: Mapping[str, Path]) -> Dict[str, Any]:
    deep_dir = paths["deep_dir"]
    memories_path = paths["deep_memories"]
    if not deep_dir.exists():
        state = "absent"
    elif memories_path.exists():
        rows = read_jsonl(memories_path)
        state = "present_with_records" if rows else "initialized_but_empty"
    else:
        state = "initialized_but_empty"
    return {
        "state": state,
        "deep_dir": str(deep_dir.resolve()),
        "deep_dir_exists": deep_dir.exists(),
        "memories_path": str(memories_path.resolve()),
        "memories_path_exists": memories_path.exists(),
        "count": len(read_jsonl(memories_path)) if memories_path.exists() else 0,
    }


def graph_snapshot(app_mod: Any, workspace_id: str) -> Dict[int, Dict[str, Any]]:
    fabric = app_mod.fabric
    ak = fabric._agent_key(workspace_id, AGENT_ID)
    graph = fabric.private_graphs.get(ak)
    if graph is None:
        return {}
    out: Dict[int, Dict[str, Any]] = {}
    for eid, ent in graph.entities.items():
        payload = dict(ent.payload or {})
        out[int(eid)] = {
            "eid": int(eid),
            "born_step": int(getattr(ent, "born_step", 0) or 0),
            "payload": payload,
        }
    return out


def graph_counts(snapshot: Mapping[int, Mapping[str, Any]]) -> Dict[str, Any]:
    compressed = 0
    short_path = 0
    long_path = 0
    exported = 0
    reinforcement_total = 0
    for item in snapshot.values():
        payload = item.get("payload") if isinstance(item, Mapping) else {}
        if not isinstance(payload, Mapping):
            continue
        if payload.get("compressed"):
            compressed += 1
        if payload.get("compression_route") == "short_path":
            short_path += 1
        if payload.get("compression_route") == "long_path":
            long_path += 1
        if payload.get("exported_deep"):
            exported += 1
        reinforcement_total += int(payload.get("reinforcement_count", 0) or 0)
    return {
        "source_rows": len(snapshot),
        "compressed_source_rows": compressed,
        "short_path_source_rows": short_path,
        "long_path_source_rows": long_path,
        "exported_deep_source_rows": exported,
        "reinforcement_total": reinforcement_total,
    }


def kernel_step(app_mod: Any, workspace_id: str) -> Optional[int]:
    fabric = app_mod.fabric
    ak = fabric._agent_key(workspace_id, AGENT_ID)
    state = fabric.agent_states.get(ak)
    if state is None:
        return None
    try:
        return int(getattr(state, "step", 0) or 0)
    except Exception:
        return None


def compact_payload(eid: int, item: Mapping[str, Any]) -> Dict[str, Any]:
    payload = item.get("payload") if isinstance(item, Mapping) else {}
    if not isinstance(payload, Mapping):
        payload = {}
    return {
        "eid": int(eid),
        "born_step": int(item.get("born_step", payload.get("created_at", 0)) or 0),
        "created_at": payload.get("created_at"),
        "last_reinforced": payload.get("last_reinforced"),
        "reinforcement_count": int(payload.get("reinforcement_count", 0) or 0),
        "strength": payload.get("strength"),
        "confidence": payload.get("confidence"),
        "half_life": payload.get("half_life"),
        "memory_class": payload.get("memory_class"),
        "type": payload.get("type"),
        "compressed": bool(payload.get("compressed", False)),
        "compressed_step": payload.get("compressed_step"),
        "compression_route": payload.get("compression_route"),
        "compression_score": payload.get("compression_score"),
        "compression_tier": payload.get("compression_tier"),
        "exported_deep": bool(payload.get("exported_deep", False)),
        "exported_step": payload.get("exported_step"),
        "summary_length": len(str(payload.get("summary", "") or "")),
        "summary": str(payload.get("summary", "") or "")[:500],
    }


def changed_compression_sources(
    before: Mapping[int, Mapping[str, Any]],
    after: Mapping[int, Mapping[str, Any]],
) -> Dict[str, List[int]]:
    newly_short: List[int] = []
    newly_long: List[int] = []
    changed: List[int] = []
    for eid, item_after in after.items():
        payload_after = item_after.get("payload") if isinstance(item_after, Mapping) else {}
        if not isinstance(payload_after, Mapping):
            continue
        item_before = before.get(eid, {})
        payload_before = item_before.get("payload") if isinstance(item_before, Mapping) else {}
        if not isinstance(payload_before, Mapping):
            payload_before = {}
        route_after = payload_after.get("compression_route")
        route_before = payload_before.get("compression_route")
        compressed_now = bool(payload_after.get("compressed", False))
        compressed_before = bool(payload_before.get("compressed", False))
        exported_now = bool(payload_after.get("exported_deep", False))
        exported_before = bool(payload_before.get("exported_deep", False))
        if (compressed_now and not compressed_before) or (exported_now and not exported_before) or (
            route_after and route_after != route_before
        ):
            changed.append(int(eid))
        if route_after == "short_path" and route_before != "short_path":
            newly_short.append(int(eid))
        if (route_after == "long_path" and route_before != "long_path") or (
            exported_now and not exported_before
        ):
            newly_long.append(int(eid))
    return {
        "newly_changed": sorted(set(changed)),
        "newly_short_path": sorted(set(newly_short)),
        "newly_long_path": sorted(set(newly_long)),
    }


def infer_outcome(
    ingest: Mapping[str, Any],
    before: Mapping[int, Mapping[str, Any]],
    after: Mapping[int, Mapping[str, Any]],
) -> str:
    if ingest.get("reinforced") is True:
        return "REINFORCEMENT_OF_EXISTING_ROW"
    if ingest.get("stored") is True:
        eid = ingest.get("eid")
        try:
            eid_int = int(eid)
        except Exception:
            return "STORED_WITHOUT_PARSEABLE_EID"
        if eid_int not in before and eid_int in after:
            return "NEW_SOURCE_ROW"
        return "STORED_EXISTING_ROW_WITHOUT_REINFORCED_FLAG"
    if ingest.get("stored") is False and ingest.get("reinforced") is False:
        return "NOT_STORED"
    return "UNKNOWN_PRODUCTION_OUTCOME"


def verify_persisted_exchange(
    *,
    outcome: str,
    eid: int,
    requested_step: int,
    appended_nodes: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    matching = []
    for row in appended_nodes:
        try:
            row_eid = int(row.get("eid", -1))
        except Exception:
            continue
        if row_eid != int(eid):
            continue
        payload = row.get("payload") or {}
        if not isinstance(payload, Mapping):
            continue
        matching.append(payload)

    proof = {
        "matched_appended_rows": len(matching),
        "created_at_requested_step": False,
        "last_reinforced_requested_step": False,
        "accepted": False,
    }
    for payload in matching:
        try:
            proof["created_at_requested_step"] = proof["created_at_requested_step"] or (
                int(payload.get("created_at", -1)) == int(requested_step)
            )
        except Exception:
            pass
        try:
            proof["last_reinforced_requested_step"] = proof["last_reinforced_requested_step"] or (
                int(payload.get("last_reinforced", -1)) == int(requested_step)
            )
        except Exception:
            pass

    if outcome == "NEW_SOURCE_ROW":
        proof["accepted"] = bool(proof["created_at_requested_step"])
    elif outcome == "REINFORCEMENT_OF_EXISTING_ROW":
        proof["accepted"] = bool(proof["last_reinforced_requested_step"])
    else:
        proof["accepted"] = False
    return proof


def source_detail(
    *,
    eid: int,
    before: Mapping[int, Mapping[str, Any]],
    after: Mapping[int, Mapping[str, Any]],
    current_step: int,
    data_root: Path,
) -> Dict[str, Any]:
    item_after = after.get(int(eid), {})
    item_before = before.get(int(eid), {})
    payload_after = item_after.get("payload") if isinstance(item_after, Mapping) else {}
    payload_before = item_before.get("payload") if isinstance(item_before, Mapping) else {}
    if not isinstance(payload_after, Mapping):
        payload_after = {}
    if not isinstance(payload_before, Mapping):
        payload_before = {}
    born_step = int(item_after.get("born_step", payload_after.get("created_at", 0)) or 0)

    tier_observation: Dict[str, Any]
    try:
        from torment_service.compression import derive_retention_tier

        tier_observation = {
            "value": derive_retention_tier(dict(payload_after)),
            "source": "torment_service.compression.derive_retention_tier(payload)",
            "mutation": "none",
        }
    except Exception as exc:
        tier_observation = {"value": None, "source": "unavailable", "error": str(exc)}

    return {
        "eid": int(eid),
        "born_step": born_step,
        "current_step": int(current_step),
        "age": int(current_step) - born_step,
        "summary_length": len(str(payload_after.get("summary", "") or "")),
        "summary": str(payload_after.get("summary", "") or "")[:1200],
        "memory_class": payload_after.get("memory_class"),
        "retention_tier": tier_observation,
        "strength_before": payload_before.get("strength"),
        "strength_after": payload_after.get("strength"),
        "half_life": payload_after.get("half_life"),
        "reinforcement_count": int(payload_after.get("reinforcement_count", 0) or 0),
        "last_reinforced": payload_after.get("last_reinforced"),
        "compression_score": payload_after.get("compression_score"),
        "route": payload_after.get("compression_route"),
        "compressed": bool(payload_after.get("compressed", False)),
        "compressed_step": payload_after.get("compressed_step"),
        "exported_deep": bool(payload_after.get("exported_deep", False)),
        "exported_step": payload_after.get("exported_step"),
        "nodes_path": str(
            (
                data_root
                / "workspaces"
                / str(payload_after.get("workspace_id", ""))
                / "agents"
                / str(payload_after.get("agent_id", ""))
                / "private"
                / "nodes.jsonl"
            ).resolve()
        )
        if payload_after.get("workspace_id") and payload_after.get("agent_id")
        else "",
    }


def fresh_deep_details(
    *,
    data_root: Path,
    paths: Mapping[str, Path],
    deep_records: List[Mapping[str, Any]],
    source_snapshot: Mapping[int, Mapping[str, Any]],
    current_step: int,
) -> Optional[Dict[str, Any]]:
    if not deep_records:
        return None
    first = dict(deep_records[0])
    eid = int(first.get("eid", 0) or 0)
    from torment_service.deep_memory import DeepMemoryStore

    store = DeepMemoryStore(str(paths["deep_dir"].resolve()), trusted_root=str(data_root.resolve()))
    try:
        recalled = store.recall(eid)
        recalled_dict = recalled.to_dict() if recalled is not None else None
    finally:
        store.close()
    source = source_snapshot.get(eid, {})
    source_payload = source.get("payload") if isinstance(source, Mapping) else {}
    if not isinstance(source_payload, Mapping):
        source_payload = {}
    source_born = int(source.get("born_step", source_payload.get("created_at", 0)) or 0) if isinstance(source, Mapping) else 0
    return {
        "deep_eid": eid,
        "source_eid": eid,
        "source_eid_equals_deep_eid": bool(eid == int(first.get("eid", -1))),
        "fresh_store_recall": recalled_dict,
        "summary": first.get("summary", ""),
        "summary_length": len(str(first.get("summary", "") or "")),
        "compression_score": first.get("compression_score"),
        "metadata": first.get("metadata"),
        "embedding_ref": first.get("embedding_ref"),
        "persisted_file_path": str(paths["deep_memories"].resolve()),
        "source_summary": str(source_payload.get("summary", "") or "")[:1200],
        "source_born_step": source_born,
        "source_current_age": int(current_step) - source_born,
        "source_route_metadata": {
            "compression_route": source_payload.get("compression_route"),
            "compression_score": source_payload.get("compression_score"),
            "exported_deep": source_payload.get("exported_deep"),
            "exported_step": source_payload.get("exported_step"),
            "compressed": source_payload.get("compressed"),
            "compressed_step": source_payload.get("compressed_step"),
        },
    }


def threshold_snapshot(app_mod: Any) -> Dict[str, Any]:
    from torment_service import compression as c

    fabric = app_mod.fabric
    snap = {
        "fabric": {
            "TORMENT_COMPRESS_ENABLE": bool(getattr(fabric, "_compress_enable", False)),
            "TORMENT_COMPRESS_MIN_STEP": int(getattr(fabric, "_compress_min_step", 0)),
        },
        "compression_module": {
            "TORMENT_COMPRESS_MIN_AGE": c.COMPRESS_MIN_AGE,
            "TORMENT_COMPRESS_MAX_CANDIDATES": c.COMPRESS_MAX_CANDIDATES,
            "TORMENT_COMPRESS_DEEP_THRESHOLD": c.COMPRESS_DEEP_THRESHOLD,
            "TORMENT_COMPRESS_AGE_THRESHOLD": c.COMPRESS_AGE_THRESHOLD,
            "TORMENT_COMPRESS_TEAR_EMERGENCY": c.COMPRESS_TEAR_EMERGENCY,
            "TORMENT_COMPRESS_SHORT_STRENGTH_MULT": c.COMPRESS_SHORT_PATH_MULT,
            "TORMENT_COMPRESS_LONG_STRENGTH": c.COMPRESS_LONG_PATH_STRENGTH,
            "TORMENT_COMPRESS_RELATIONAL_MULT": c.COMPRESS_RELATIONAL_MULT,
            "TORMENT_COMPRESS_ECHO_MULT": c.COMPRESS_ECHO_MULT,
            "TORMENT_COMPRESS_TOOL_RESULT_MULT": c.COMPRESS_TOOL_RESULT_MULT,
            "TORMENT_COMPRESS_TOOL_RESULT_SCORE_MULT": c.COMPRESS_TOOL_RESULT_SCORE_MULT,
            "TORMENT_COMPRESS_ECHO_DEEP_AGE": c.COMPRESS_ECHO_DEEP_AGE,
            "TORMENT_COMPRESS_COUNT_THRESHOLD": c.COMPRESS_COUNT_THRESHOLD,
            "TORMENT_COMPRESS_STEP_INTERVAL": c.COMPRESS_STEP_INTERVAL,
            "TORMENT_COMPRESS_FALLBACK_COOLDOWN": c.COMPRESS_FALLBACK_COOLDOWN,
            "TORMENT_COMPRESS_PERIODIC_FLOOR": c.COMPRESS_PERIODIC_FLOOR,
            "TORMENT_MAX_PRIVATE_MEMORIES": c.COMPRESS_HARD_CAP,
            "TORMENT_HARD_CAP_TARGET_RATIO": c.COMPRESS_HARD_CAP_TARGET,
        },
        "reinforcement": {
            "TORMENT_REINFORCE_SIM_THRESHOLD": (
                float(os.environ["TORMENT_REINFORCE_SIM_THRESHOLD"])
                if os.environ.get("TORMENT_REINFORCE_SIM_THRESHOLD")
                else 0.92
            ),
            "source": "fabric.ingest getenv default when env var absent",
        },
        "threshold_env_present": {key: os.environ.get(key) for key in THRESHOLD_ENV_VARS if key in os.environ},
    }

    expected = {
        "TORMENT_COMPRESS_MIN_STEP": 100,
        "TORMENT_COMPRESS_MIN_AGE": 50,
        "TORMENT_MAX_PRIVATE_MEMORIES": 10000,
        "TORMENT_REINFORCE_SIM_THRESHOLD": 0.92,
        "TORMENT_COMPRESS_DEEP_THRESHOLD": 0.7,
        "TORMENT_COMPRESS_AGE_THRESHOLD": 500,
        "TORMENT_COMPRESS_STEP_INTERVAL": 200,
        "TORMENT_COMPRESS_FALLBACK_COOLDOWN": 50,
        "TORMENT_COMPRESS_PERIODIC_FLOOR": 0.4,
        "TORMENT_COMPRESS_COUNT_THRESHOLD": 400,
    }
    observed = {
        "TORMENT_COMPRESS_MIN_STEP": snap["fabric"]["TORMENT_COMPRESS_MIN_STEP"],
        "TORMENT_COMPRESS_MIN_AGE": snap["compression_module"]["TORMENT_COMPRESS_MIN_AGE"],
        "TORMENT_MAX_PRIVATE_MEMORIES": snap["compression_module"]["TORMENT_MAX_PRIVATE_MEMORIES"],
        "TORMENT_REINFORCE_SIM_THRESHOLD": snap["reinforcement"]["TORMENT_REINFORCE_SIM_THRESHOLD"],
        "TORMENT_COMPRESS_DEEP_THRESHOLD": snap["compression_module"]["TORMENT_COMPRESS_DEEP_THRESHOLD"],
        "TORMENT_COMPRESS_AGE_THRESHOLD": snap["compression_module"]["TORMENT_COMPRESS_AGE_THRESHOLD"],
        "TORMENT_COMPRESS_STEP_INTERVAL": snap["compression_module"]["TORMENT_COMPRESS_STEP_INTERVAL"],
        "TORMENT_COMPRESS_FALLBACK_COOLDOWN": snap["compression_module"]["TORMENT_COMPRESS_FALLBACK_COOLDOWN"],
        "TORMENT_COMPRESS_PERIODIC_FLOOR": snap["compression_module"]["TORMENT_COMPRESS_PERIODIC_FLOOR"],
        "TORMENT_COMPRESS_COUNT_THRESHOLD": snap["compression_module"]["TORMENT_COMPRESS_COUNT_THRESHOLD"],
    }
    mismatches = {
        key: {"expected": expected[key], "observed": observed[key]}
        for key in expected
        if observed[key] != expected[key]
    }
    if mismatches:
        raise StageStop(f"Compression/reinforcement threshold mismatch: {mismatches}")
    snap["validated_defaults"] = expected
    return snap


def preflight(client: Any, app_mod: Any, workspace_id: str) -> Dict[str, Any]:
    health = api_json(client, "GET", "/health")
    embedder_observations = validate_embedder(
        health,
        api_json(client, "GET", "/embedder/check"),
    )
    config = api_json(client, "GET", "/config")
    workspace = api_json(client, "POST", "/workspace/create", json={"workspace_id": workspace_id})
    agent = api_json(
        client,
        "POST",
        "/agent/create",
        json={
            "workspace_id": workspace_id,
            "agent_id": AGENT_ID,
            "seed": {
                "seed_id": "eira_voss_lived_use_v1",
                "character_name": CHARACTER_NAME,
                "seed_text": "Focused lived-use experiment identity seed for Eira Voss.",
                "coupling_mode": "read_only",
            },
        },
    )
    recent = api_json(client, "GET", f"/index/{workspace_id}/{AGENT_ID}/recent", params={"limit": 1})
    current_step = resolve_resumed_step_from_recent(recent)
    thresholds = threshold_snapshot(app_mod)
    metrics = api_json(client, "GET", "/debug/metrics", params={"workspace_id": workspace_id, "agent_id": AGENT_ID})
    compression_status = api_json(
        client,
        "GET",
        f"/workspace/{workspace_id}/compress/status",
        params={"agent_id": AGENT_ID},
    )
    return {
        "health": health,
        "embedder_observations": embedder_observations,
        "config": config,
        "workspace_create": workspace,
        "agent_create": agent,
        "recent_index": recent,
        "resumed_current_step": current_step,
        "threshold_snapshot": thresholds,
        "debug_metrics": metrics,
        "compression_status": compression_status,
    }


def load_script_for_condition(preregistered_path: Path, trajectory_id: str, max_exchanges: int) -> List[Dict[str, Any]]:
    payload = read_json(preregistered_path)
    trajectories = payload.get("trajectories")
    if not isinstance(trajectories, Mapping):
        raise StageStop(f"Preregistered trajectory file missing trajectories: {preregistered_path}")
    items = trajectories.get(trajectory_id)
    if not isinstance(items, list):
        raise StageStop(f"Trajectory {trajectory_id} missing in {preregistered_path}")
    if len(items) < int(max_exchanges):
        raise StageStop(f"Trajectory {trajectory_id} has {len(items)} rows, need {max_exchanges}")
    return [dict(row) for row in items[: int(max_exchanges)]]


def update_milestones(
    milestones: Dict[str, Any],
    *,
    exchange: int,
    step: int,
    compression_changes: Mapping[str, List[int]],
    deep_new_records: List[Mapping[str, Any]],
) -> None:
    if step >= 100 and not milestones.get("M1_FIRST_MIN_STEP_CROSSED"):
        milestones["M1_FIRST_MIN_STEP_CROSSED"] = {"exchange": exchange, "step": step}
    if compression_changes.get("newly_changed") and not milestones.get("M2_FIRST_COMPRESSION_EFFECT_OBSERVED"):
        milestones["M2_FIRST_COMPRESSION_EFFECT_OBSERVED"] = {
            "exchange": exchange,
            "step": step,
            "eids": compression_changes.get("newly_changed"),
        }
    if compression_changes.get("newly_short_path") and not milestones.get("M3_FIRST_SHORT_PATH_OBSERVED"):
        milestones["M3_FIRST_SHORT_PATH_OBSERVED"] = {
            "exchange": exchange,
            "step": step,
            "eids": compression_changes.get("newly_short_path"),
        }
    if compression_changes.get("newly_long_path") and not milestones.get("M4_FIRST_LONG_PATH_OBSERVED"):
        milestones["M4_FIRST_LONG_PATH_OBSERVED"] = {
            "exchange": exchange,
            "step": step,
            "eids": compression_changes.get("newly_long_path"),
        }
    if deep_new_records and not milestones.get("M5_FIRST_DEEP_MEMORY_PERSISTED"):
        milestones["M5_FIRST_DEEP_MEMORY_PERSISTED"] = {
            "exchange": exchange,
            "step": step,
            "eids": [int(row.get("eid", 0) or 0) for row in deep_new_records],
            "count": len(deep_new_records),
        }


def run_worker(args: argparse.Namespace) -> int:
    root = repo_root()
    condition_name = str(args.condition)
    specs = worker_condition_specs()
    if condition_name not in specs:
        raise StageStop(f"Unknown worker condition: {condition_name}")
    spec = specs[condition_name]
    data_root = Path(args.data_root).resolve()
    result_path = Path(args.result_path).resolve()
    preregistered_path = Path(args.preregistered).resolve()
    max_exchanges = int(spec["max_exchanges"])
    workspace_id = str(spec["workspace_id"])
    trajectory_id = str(spec["trajectory_id"])
    script = load_script_for_condition(preregistered_path, trajectory_id, max_exchanges)

    ensure_required_python(worker=True)
    baseline_start = ensure_baseline(root)

    seed_base = 2026081100 + list(specs).index(condition_name)
    random.seed(seed_base)
    try:
        import numpy as np

        np.random.seed(seed_base)
    except Exception:
        pass

    from examples.lived_use_chat import build_ingest_summary
    import torment_service.app as app_mod

    client = DirectAppClient(app_mod)
    paths = agent_paths(data_root, workspace_id)
    nodes_tail = JsonlTail(paths["nodes"])
    compression_tail = JsonlTail(paths["compression_log"])
    deep_tail = JsonlTail(paths["deep_memories"])

    preflight_result = preflight(client, app_mod, workspace_id)
    current_step = int(preflight_result["resumed_current_step"])
    if current_step != 0:
        raise StageStop(f"Fresh isolated trajectory did not start at step 0: {current_step}")

    output: Dict[str, Any] = {
        "label": LABEL,
        "subtype": SUBTYPE,
        "condition_name": condition_name,
        "condition": spec["condition"],
        "trajectory_id": trajectory_id,
        "workspace_id": workspace_id,
        "agent_id": AGENT_ID,
        "domain_id": DOMAIN_ID,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "rng_seed": seed_base,
        "provider": "NOT_INVOKED",
        "authoritative_path": {
            "query": "same-thread call to torment_service.app.query endpoint function for /agent/query",
            "ingest": "same-thread call to torment_service.app.ingest endpoint function for /agent/ingest",
            "compression": "Fabric ingest production hook only",
            "transport_boundary": (
                "FastAPI TestClient was avoided because it introduces a harness-only "
                "threadpool boundary that violates the current SQLite sidecar's "
                "same-thread sqlite3 connection constraint."
            ),
            "direct_compression_call_as_authority": "NOT_USED",
            "manual_step_advancement": "NOT_USED",
            "threshold_lowering": "NOT_USED",
            "hash_embedding": "NOT_USED",
        },
        "preflight": preflight_result,
        "deep_memory_initial": deep_file_state(paths),
        "per_exchange": [],
        "milestones": {},
        "first_compression_details": None,
        "first_short_path_details": None,
        "first_long_path_details": None,
        "first_deep_memory_details": None,
        "compression_events_observed": [],
        "stop_reason": "",
        "path_invalidity": None,
    }

    successful_ingests = 0
    new_source_rows = 0
    reinforcement_rows = 0
    unexpected_outcome_count = 0
    seen_hard_cap = False

    for index, pair in enumerate(script, 1):
        before = graph_snapshot(app_mod, workspace_id)
        before_counts = graph_counts(before)
        recent_before = api_json(client, "GET", f"/index/{workspace_id}/{AGENT_ID}/recent", params={"limit": 1})
        query_payload = {
            "workspace_id": workspace_id,
            "agent_id": AGENT_ID,
            "query": str(pair["user"]),
            "top_k": 8,
            "domain_id": DOMAIN_ID,
            "explain": True,
            "continuity_debug": True,
        }
        query_response = api_json(client, "POST", "/agent/query", json=query_payload)
        supplied_summary = build_ingest_summary(
            USER_NAME,
            CHARACTER_NAME,
            str(pair["user"]),
            str(pair["assistant"]),
            os.environ,
        )
        requested_step = current_step + 1
        ingest_payload = {
            "workspace_id": workspace_id,
            "agent_id": AGENT_ID,
            "text": supplied_summary,
            "step": requested_step,
            "domain_id": DOMAIN_ID,
            "scope": "private",
            "supplied_summary": supplied_summary,
        }
        ingest_response = api_json(client, "POST", "/agent/ingest", json=ingest_payload)
        appended_nodes = nodes_tail.read_new()
        new_compression_events = compression_tail.read_new()
        deep_new_records = deep_tail.read_new()
        recent_after = api_json(client, "GET", f"/index/{workspace_id}/{AGENT_ID}/recent", params={"limit": 1})
        after = graph_snapshot(app_mod, workspace_id)
        after_counts = graph_counts(after)
        compression_changes = changed_compression_sources(before, after)
        output["compression_events_observed"].extend(new_compression_events)
        seen_hard_cap = seen_hard_cap or any(str(evt.get("trigger")) == "hard_cap" for evt in new_compression_events)

        outcome = infer_outcome(ingest_response, before, after)
        try:
            eid = int(ingest_response.get("eid", -1))
        except Exception:
            eid = -1
        persisted_proof = verify_persisted_exchange(
            outcome=outcome,
            eid=eid,
            requested_step=requested_step,
            appended_nodes=appended_nodes,
        )
        k_step = kernel_step(app_mod, workspace_id)
        query_results = query_response.get("results") if isinstance(query_response.get("results"), list) else []

        record = {
            "exchange": index,
            "current_step_before": current_step,
            "requested_ingest_step": requested_step,
            "persisted_durable_step_evidence": persisted_proof,
            "recent_index_top_step_before": top_recent_step(recent_before),
            "recent_index_top_step_after": top_recent_step(recent_after),
            "kernel_model_step": k_step,
            "outcome": outcome,
            "eid": eid,
            "query_result_count": len(query_results),
            "ingest_path": ingest_response.get("path"),
            "ingest_result_code": ingest_response.get("result_code"),
            "ingest_decision_code": ingest_response.get("decision_code"),
            "ingest_exposed_compression_fields": {
                key: ingest_response.get(key)
                for key in (
                    "compressed",
                    "exported_deep",
                    "compression_route",
                    "compression_event",
                    "compression_trigger",
                )
                if key in ingest_response
            }
            or "NOT_DIRECTLY_OBSERVABLE_FROM_HARNESS",
            "graph_source_rows": after_counts["source_rows"],
            "successful_ingests": successful_ingests + 1,
            "new_source_rows_total": new_source_rows + (1 if outcome == "NEW_SOURCE_ROW" else 0),
            "reinforcement_total": after_counts["reinforcement_total"],
            "compressed_source_rows": after_counts["compressed_source_rows"],
            "short_path_source_rows": after_counts["short_path_source_rows"],
            "long_path_source_rows": after_counts["long_path_source_rows"],
            "exported_deep_source_rows": after_counts["exported_deep_source_rows"],
            "deep_memory_count": deep_file_state(paths)["count"],
            "compression_changes": compression_changes,
            "compression_events": new_compression_events,
            "deep_new_record_eids": [int(row.get("eid", 0) or 0) for row in deep_new_records],
            "appended_node_count": len(appended_nodes),
            "appended_node_eids": [int(row.get("eid", -1)) for row in appended_nodes if isinstance(row, Mapping)],
        }
        output["per_exchange"].append(record)

        if outcome == "NEW_SOURCE_ROW":
            new_source_rows += 1
        elif outcome == "REINFORCEMENT_OF_EXISTING_ROW":
            reinforcement_rows += 1
        else:
            unexpected_outcome_count += 1

        if ingest_response.get("stored") is not True:
            output["stop_reason"] = "PRODUCTION_PATH_INVALIDITY_NON_STORING_INGEST"
            output["path_invalidity"] = {"exchange": index, "ingest_response": ingest_response}
            print(f"{condition_name}: ABORT exchange={index} non-storing ingest", flush=True)
            break
        if not persisted_proof["accepted"]:
            output["stop_reason"] = "FAIL_CLOSED_INVARIANT_PERSISTED_STEP_EVIDENCE_MISSING"
            output["path_invalidity"] = {
                "exchange": index,
                "outcome": outcome,
                "eid": eid,
                "requested_step": requested_step,
                "persisted_proof": persisted_proof,
            }
            print(f"{condition_name}: ABORT exchange={index} persisted-step proof missing", flush=True)
            break
        if k_step != requested_step:
            output["stop_reason"] = "FAIL_CLOSED_INVARIANT_KERNEL_STEP_MISMATCH"
            output["path_invalidity"] = {
                "exchange": index,
                "requested_step": requested_step,
                "kernel_step": k_step,
            }
            print(f"{condition_name}: ABORT exchange={index} kernel_step={k_step}", flush=True)
            break

        update_milestones(
            output["milestones"],
            exchange=index,
            step=requested_step,
            compression_changes=compression_changes,
            deep_new_records=deep_new_records,
        )

        if compression_changes["newly_changed"] and output["first_compression_details"] is None:
            first_eid = int(compression_changes["newly_changed"][0])
            output["first_compression_details"] = {
                "exchange": index,
                "step": requested_step,
                "source": source_detail(
                    eid=first_eid,
                    before=before,
                    after=after,
                    current_step=requested_step,
                    data_root=data_root,
                ),
                "all_changed_eids": compression_changes["newly_changed"],
                "compression_events": new_compression_events,
                "trigger_observation": (
                    "compression_log.jsonl"
                    if new_compression_events
                    else "INFERRED_FROM_DURABLE_SOURCE_PAYLOAD_MUTATION"
                ),
            }
        if compression_changes["newly_short_path"] and output["first_short_path_details"] is None:
            first_eid = int(compression_changes["newly_short_path"][0])
            output["first_short_path_details"] = {
                "exchange": index,
                "step": requested_step,
                "source": source_detail(
                    eid=first_eid,
                    before=before,
                    after=after,
                    current_step=requested_step,
                    data_root=data_root,
                ),
                "all_short_path_eids": compression_changes["newly_short_path"],
            }
        if compression_changes["newly_long_path"] and output["first_long_path_details"] is None:
            first_eid = int(compression_changes["newly_long_path"][0])
            output["first_long_path_details"] = {
                "exchange": index,
                "step": requested_step,
                "source": source_detail(
                    eid=first_eid,
                    before=before,
                    after=after,
                    current_step=requested_step,
                    data_root=data_root,
                ),
                "all_long_path_eids": compression_changes["newly_long_path"],
            }
        if deep_new_records and output["first_deep_memory_details"] is None:
            if not compression_changes["newly_long_path"]:
                output["stop_reason"] = "FAIL_CLOSED_DEEP_MEMORY_WITHOUT_SAME_EXCHANGE_LONG_PATH_SOURCE"
                output["path_invalidity"] = {
                    "exchange": index,
                    "deep_new_records": deep_new_records,
                    "compression_changes": compression_changes,
                }
                print(f"{condition_name}: ABORT exchange={index} deep without long_path marker", flush=True)
                break
            output["first_deep_memory_details"] = {
                "exchange": index,
                "step": requested_step,
                "deep_records_created_this_exchange": deep_new_records,
                "fresh_readback": fresh_deep_details(
                    data_root=data_root,
                    paths=paths,
                    deep_records=deep_new_records,
                    source_snapshot=after,
                    current_step=requested_step,
                ),
            }
            output["stop_reason"] = "FIRST_DEEP_MEMORY_PERSISTED"
            print(
                f"{condition_name}: M5 FIRST_DEEP_MEMORY_PERSISTED "
                f"exchange={index} step={requested_step} deep_count={record['deep_memory_count']}",
                flush=True,
            )
            current_step = requested_step
            successful_ingests += 1
            break

        current_step = requested_step
        successful_ingests += 1

        if index % int(args.progress_every) == 0:
            print(
                f"{condition_name}: exchange={index} step={requested_step} "
                f"graph_rows={after_counts['source_rows']} "
                f"reinforcements={after_counts['reinforcement_total']} "
                f"short_path={after_counts['short_path_source_rows']} "
                f"long_path={after_counts['long_path_source_rows']} "
                f"deep={record['deep_memory_count']}",
                flush=True,
            )

    if not output["stop_reason"]:
        if condition_name == CONDITION_A:
            output["stop_reason"] = "MAX_EXCHANGES_REACHED_DEFAULT_OFF_NO_DEEP_MEMORY"
        else:
            output["stop_reason"] = "MAX_EXCHANGES_REACHED_WITHOUT_DEEP_MEMORY"

    final_snapshot = graph_snapshot(app_mod, workspace_id)
    final_counts = graph_counts(final_snapshot)
    output["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    output["exchange_count"] = len(output["per_exchange"])
    output["successful_ingests"] = successful_ingests
    output["outcome_counts"] = {
        "NEW_SOURCE_ROW": new_source_rows,
        "REINFORCEMENT_OF_EXISTING_ROW": reinforcement_rows,
        "OTHER": unexpected_outcome_count,
    }
    output["reinforcement_summary"] = {
        "total_ingests": successful_ingests,
        "unique_source_rows": final_counts["source_rows"],
        "reinforcement_count": final_counts["reinforcement_total"],
        "reinforcement_ratio": (
            float(final_counts["reinforcement_total"]) / float(successful_ingests)
            if successful_ingests
            else 0.0
        ),
        "reinforced_sources": [
            compact_payload(eid, item)
            for eid, item in sorted(final_snapshot.items())
            if int((item.get("payload") or {}).get("reinforcement_count", 0) or 0) > 0
        ][:100],
        "reinforced_sources_truncated_at": 100,
    }
    output["graph_growth_summary"] = {
        "initial_source_rows": 0,
        "final_source_rows": final_counts["source_rows"],
        "successful_ingests": successful_ingests,
        "new_source_rows": new_source_rows,
        "reinforcement_rows": reinforcement_rows,
        "source_rows_per_successful_ingest": (
            float(final_counts["source_rows"]) / float(successful_ingests)
            if successful_ingests
            else 0.0
        ),
    }
    output["deep_memory_final"] = deep_file_state(paths)
    output["compression_summary"] = {
        "first_compression_step": (
            output["first_compression_details"]["step"]
            if output["first_compression_details"]
            else None
        ),
        "first_short_path_step": (
            output["first_short_path_details"]["step"]
            if output["first_short_path_details"]
            else None
        ),
        "first_long_path_step": (
            output["first_long_path_details"]["step"]
            if output["first_long_path_details"]
            else None
        ),
        "first_deep_memory_step": (
            output["first_deep_memory_details"]["step"]
            if output["first_deep_memory_details"]
            else None
        ),
        "compression_log_path": str(paths["compression_log"].resolve()),
        "compression_events_logged": len(read_jsonl(paths["compression_log"])),
        "hard_cap_route": "REACHED" if seen_hard_cap else "NOT_REACHED",
    }
    output["source_paths"] = {key: str(value.resolve()) for key, value in paths.items()}
    output["code_traced_expectations"] = {
        "compression_min_step": 100,
        "compression_min_candidate_age": 50,
        "fallback_no_earlier_event_periodic_expectation": "approximately step 201",
        "ordinary_relational_long_path_predicate": "score >= 0.7 and age >= 500",
        "first_deep_memory_not_predeclared": True,
    }
    output["interpretive_boundary"] = {
        "scope": "exact reachability under these scripted provider-free production-equivalent trajectories",
        "natural_prevalence": "NOT_MEASURED",
        "provider_behavior": "NOT_ESTABLISHED",
        "semantic_usefulness": "NOT_TESTED",
        "harmfulness": "NOT_TESTED",
        "existing_deep_retrieval": "OUT_OF_SCOPE",
        "multi_session_reachability": "NOT_CHARACTERIZED_BY_V1",
        "historical_28_step_comparison": "NOT_DIRECTLY_COMPARABLE",
    }
    output["baseline_end"] = ensure_baseline(root)
    write_json(result_path, output)
    print(f"{condition_name}: result={result_path}", flush=True)
    return 0


def run_worker_subprocess(
    *,
    root: Path,
    output_dir: Path,
    condition_name: str,
    env: Dict[str, str],
    preregistered_path: Path,
    progress_every: int,
) -> Dict[str, Any]:
    data_root = output_dir / "data_roots" / condition_name
    if data_root.exists():
        shutil.rmtree(data_root)
    data_root.mkdir(parents=True, exist_ok=True)
    worker_dir = output_dir / "workers" / condition_name
    worker_dir.mkdir(parents=True, exist_ok=True)
    result_path = worker_dir / "result.json"
    log_path = worker_dir / "worker.stdout.log"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--condition",
        condition_name,
        "--data-root",
        str(data_root),
        "--result-path",
        str(result_path),
        "--preregistered",
        str(preregistered_path),
        "--progress-every",
        str(progress_every),
    ]
    started = datetime.now(timezone.utc).isoformat()
    with log_path.open("w", encoding="utf-8", newline="\n") as log_handle:
        proc = subprocess.Popen(
            command,
            cwd=str(root),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
            log_handle.write(line)
        rc = proc.wait()
    completed = datetime.now(timezone.utc).isoformat()
    if rc != 0:
        raise StageStop(
            f"Worker {condition_name} failed with return code {rc}; see {log_path}"
        )
    if not result_path.exists():
        raise StageStop(f"Worker {condition_name} did not write result {result_path}")
    return {
        "condition_name": condition_name,
        "command": command,
        "returncode": rc,
        "started_at_utc": started,
        "completed_at_utc": completed,
        "data_root": str(data_root.resolve()),
        "result_path": str(result_path.resolve()),
        "log_path": str(log_path.resolve()),
        "env_subset": {key: env.get(key, "") for key in ENV_SUBSET_KEYS},
        "result": read_json(result_path),
    }


def condition_classification(result: Mapping[str, Any]) -> Dict[str, Any]:
    milestones = result.get("milestones") if isinstance(result.get("milestones"), Mapping) else {}
    return {
        "first_compression_step": (
            milestones.get("M2_FIRST_COMPRESSION_EFFECT_OBSERVED", {}) or {}
        ).get("step"),
        "first_short_path_step": (
            milestones.get("M3_FIRST_SHORT_PATH_OBSERVED", {}) or {}
        ).get("step"),
        "first_long_path_step": (
            milestones.get("M4_FIRST_LONG_PATH_OBSERVED", {}) or {}
        ).get("step"),
        "first_deep_memory_step": (
            milestones.get("M5_FIRST_DEEP_MEMORY_PERSISTED", {}) or {}
        ).get("step"),
        "first_deep_memory_exchange": (
            milestones.get("M5_FIRST_DEEP_MEMORY_PERSISTED", {}) or {}
        ).get("exchange"),
        "stop_reason": result.get("stop_reason"),
        "unique_source_rows": (result.get("graph_growth_summary") or {}).get("final_source_rows"),
        "reinforcement_count": (result.get("reinforcement_summary") or {}).get("reinforcement_count"),
        "reinforcement_ratio": (result.get("reinforcement_summary") or {}).get("reinforcement_ratio"),
    }


def derive_final_taxonomy(condition_results: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    cond_a = condition_results.get(CONDITION_A, {})
    t1 = condition_results.get(CONDITION_T1, {})
    t2 = condition_results.get(CONDITION_T2, {})
    t3 = condition_results.get(CONDITION_T3, {})
    enabled = [t1, t2, t3]

    def has_milestone(res: Mapping[str, Any], name: str) -> bool:
        ms = res.get("milestones")
        return isinstance(ms, Mapping) and bool(ms.get(name))

    any_compression = any(has_milestone(res, "M2_FIRST_COMPRESSION_EFFECT_OBSERVED") for res in enabled)
    any_short = any(has_milestone(res, "M3_FIRST_SHORT_PATH_OBSERVED") for res in enabled)
    any_long = any(has_milestone(res, "M4_FIRST_LONG_PATH_OBSERVED") for res in enabled)
    any_deep = any(has_milestone(res, "M5_FIRST_DEEP_MEMORY_PERSISTED") for res in enabled)

    cond_summaries = {
        "T1": condition_classification(t1),
        "T2": condition_classification(t2),
        "T3": condition_classification(t3),
    }
    t1_deep = cond_summaries["T1"]["first_deep_memory_step"]
    t2_deep = cond_summaries["T2"]["first_deep_memory_step"]
    t3_deep = cond_summaries["T3"]["first_deep_memory_step"]

    t1_reinf = int((t1.get("reinforcement_summary") or {}).get("reinforcement_count", 0) or 0)
    t2_reinf = int((t2.get("reinforcement_summary") or {}).get("reinforcement_count", 0) or 0)
    t3_reinf = int((t3.get("reinforcement_summary") or {}).get("reinforcement_count", 0) or 0)
    t1_rows = int((t1.get("graph_growth_summary") or {}).get("final_source_rows", 0) or 0)
    t2_rows = int((t2.get("graph_growth_summary") or {}).get("final_source_rows", 0) or 0)
    t3_rows = int((t3.get("graph_growth_summary") or {}).get("final_source_rows", 0) or 0)
    graph_growth_diff = (
        "DEMONSTRATED"
        if (t2_reinf > t1_reinf and t2_rows < t1_rows) or (t3_reinf > t1_reinf and t3_rows < t1_rows)
        else "NOT_DEMONSTRATED"
    )
    reachability_reinf = "NOT_ISOLATED" if graph_growth_diff == "DEMONSTRATED" else "NOT_DEMONSTRATED"

    hard_cap = "REACHED" if any(
        (res.get("compression_summary") or {}).get("hard_cap_route") == "REACHED"
        for res in [cond_a, t1, t2, t3]
    ) else "NOT_REACHED"

    cond_a_deep_count = int((cond_a.get("deep_memory_final") or {}).get("count", 0) or 0)
    return {
        "DEFAULT_NEW_DEEP_FORMATION": (
            "UNEXPECTEDLY_ENABLED" if cond_a_deep_count > 0 else "DISABLED_BY_DESIGN"
        ),
        "DEFAULT_OFF_RUNTIME_CHECK_THROUGH_FIRST_FALLBACK_REGION": (
            "DEMONSTRATED"
            if int(cond_a.get("exchange_count", 0) or 0) >= DEFAULT_OFF_EXCHANGES
            and cond_a_deep_count == 0
            else "NOT_DEMONSTRATED"
        ),
        "ENABLED_FIRST_COMPRESSION_EFFECT": "DEMONSTRATED" if any_compression else "NOT_DEMONSTRATED",
        "ENABLED_FIRST_SHORT_PATH": "DEMONSTRATED" if any_short else "NOT_DEMONSTRATED",
        "ENABLED_FIRST_LONG_PATH": "DEMONSTRATED" if any_long else "NOT_DEMONSTRATED",
        "FIRST_DEEP_MEMORY_WITH_UNCHANGED_THRESHOLDS": "DEMONSTRATED" if any_deep else "NOT_DEMONSTRATED",
        "FIRST_DEEP_MEMORY_PROVIDER_FREE": "DEMONSTRATED" if any_deep else "NOT_DEMONSTRATED",
        "DISTINCT_EPISODE_REACHABILITY": "DEMONSTRATED" if t1_deep is not None else "NOT_DEMONSTRATED",
        "RECURRING_TOPIC_REACHABILITY": "DEMONSTRATED" if t2_deep is not None else "NOT_DEMONSTRATED",
        "MIXED_CHARACTER_REACHABILITY": "DEMONSTRATED" if t3_deep is not None else "NOT_DEMONSTRATED",
        "REINFORCEMENT_MATERIAL_TO_GRAPH_GROWTH": graph_growth_diff,
        "REINFORCEMENT_MATERIAL_TO_REACHABILITY": reachability_reinf,
        "FIRST_COMPRESSION_STEP_T1": cond_summaries["T1"]["first_compression_step"] or "NONE",
        "FIRST_COMPRESSION_STEP_T2": cond_summaries["T2"]["first_compression_step"] or "NONE",
        "FIRST_COMPRESSION_STEP_T3": cond_summaries["T3"]["first_compression_step"] or "NONE",
        "FIRST_DEEP_MEMORY_STEP_T1": t1_deep or "NONE",
        "FIRST_DEEP_MEMORY_STEP_T2": t2_deep or "NONE",
        "FIRST_DEEP_MEMORY_STEP_T3": t3_deep or "NONE",
        "FIRST_DEEP_MEMORY_EXCHANGE_T1": cond_summaries["T1"]["first_deep_memory_exchange"] or "NONE",
        "FIRST_DEEP_MEMORY_EXCHANGE_T2": cond_summaries["T2"]["first_deep_memory_exchange"] or "NONE",
        "FIRST_DEEP_MEMORY_EXCHANGE_T3": cond_summaries["T3"]["first_deep_memory_exchange"] or "NONE",
        "THRESHOLD_LOWERING": "NOT_USED",
        "MANUAL_STEP_ADVANCEMENT": "NOT_USED",
        "DIRECT_COMPRESSION_CALL_AS_AUTHORITY": "NOT_USED",
        "PROVIDER": "NOT_INVOKED",
        "EMBEDDER": "ST_BGE_LIVED_USE_SEMANTIC",
        "HARD_CAP_ROUTE": hard_cap,
        "MULTI_SESSION_REACHABILITY": "NOT_CHARACTERIZED_BY_V1",
        "HISTORICAL_28_STEP_COMPARISON": "NOT_DIRECTLY_COMPARABLE",
        "NATURAL_PREVALENCE": "NOT_MEASURED",
        "DEEP_MEMORY_USEFULNESS": "NOT_TESTED",
        "DEEP_MEMORY_HARMFULNESS": "NOT_TESTED",
    }


def run_main(args: argparse.Namespace) -> int:
    root = repo_root()
    ensure_required_python(worker=False)
    baseline_start = ensure_baseline(root)

    timestamp = args.timestamp or utc_stamp()
    output_dir = (root / OUTPUT_REL_PREFIX / timestamp).resolve()
    if output_dir.exists():
        raise StageStop(f"Output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)

    trajectories = generate_trajectories(max_enabled=ENABLED_EXCHANGES)
    preregistered_path = output_dir / "preregistered_trajectories.json"
    write_json(preregistered_path, trajectories)

    condition_specs = worker_condition_specs()
    worker_records: Dict[str, Any] = {}
    for condition_name in (CONDITION_A, CONDITION_T1, CONDITION_T2, CONDITION_T3):
        spec = condition_specs[condition_name]
        data_root = output_dir / "data_roots" / condition_name
        env, env_meta = configure_worker_env(
            os.environ,
            data_root=data_root,
            condition_name=condition_name,
            compress_enable=bool(spec["compress_enable"]),
        )
        write_json(output_dir / "workers" / condition_name / "env_meta.json", env_meta)
        print(
            f"START {condition_name}: compress={env['TORMENT_COMPRESS_ENABLE']} "
            f"trajectory={spec['trajectory_id']} max={spec['max_exchanges']}",
            flush=True,
        )
        record = run_worker_subprocess(
            root=root,
            output_dir=output_dir,
            condition_name=condition_name,
            env=env,
            preregistered_path=preregistered_path,
            progress_every=int(args.progress_every),
        )
        worker_records[condition_name] = record
        ensure_baseline(root)

    condition_results = {
        name: record["result"]
        for name, record in worker_records.items()
    }
    final_taxonomy = derive_final_taxonomy(condition_results)
    result = {
        "label": LABEL,
        "subtype": SUBTYPE,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_start": baseline_start,
        "baseline_end": ensure_baseline(root),
        "python": ensure_required_python(),
        "output_dir": str(output_dir),
        "preregistered_trajectories_path": str(preregistered_path.resolve()),
        "worker_records": worker_records,
        "condition_summaries": {
            name: condition_classification(result)
            for name, result in condition_results.items()
        },
        "condition_results": condition_results,
        "final_taxonomy": final_taxonomy,
        "interpretive_boundary": {
            "allowed": [
                "reachability under fixed scripted production-equivalent trajectories",
                "exchange and canonical step of first compression effect",
                "exchange and canonical step of first authentic DeepMemory",
                "descriptive graph-growth and reinforcement differences",
                "provider-free technical reachability of the memory path",
                "default configuration gate for new deep formation",
            ],
            "not_allowed": [
                "natural-user prevalence",
                "typical human conversation length",
                "population estimate",
                "provider usefulness",
                "character quality",
                "semantic usefulness of deep echoes",
                "harmfulness",
                "threshold-change recommendations",
            ],
        },
    }
    final_path = output_dir / f"{LABEL}_result.json"
    write_json(final_path, result)
    print(f"AUTHORITATIVE_RESULT_PATH={final_path}", flush=True)
    print("FINAL_TAXONOMY=" + json.dumps(final_taxonomy, sort_keys=True), flush=True)
    return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--progress-every", type=int, default=PROGRESS_EVERY)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--condition", default="")
    parser.add_argument("--data-root", default="")
    parser.add_argument("--result-path", default="")
    parser.add_argument("--preregistered", default="")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.worker:
            return run_worker(args)
        return run_main(args)
    except StageStop as exc:
        print(f"STAGE_STOP: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
