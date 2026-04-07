"""Stance / Thinking Layer smoke test runner — v3.

Usage (from torment_fabric/ directory):
    python tests/run_stance_smoke.py

Requires the TORMENT server running in another CMD window with:
    set TORMENT_THINKING_ADVISORY=1
    set TORMENT_CONTEXTUAL_ABSTENTION=1
    python -m torment_service

Hits /thinking/debug with 16 test cases, checks results against allowed
behavioral ranges (not single exact values), prints a summary table with
pass/warn/diverge markers, stance distribution, and saves full output
to stance_smoke_results.json.

No API keys needed — this is all local heuristics.
"""

import json
import sys
from collections import Counter
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8787"
CAPS_ON = {"contextual_abstention": True}


# ── Test case format ─────────────────────────────────────────────────────
# Each case is a dict with:
#   label            — short test name
#   text             — input to the thinking controller
#   source_type      — "user_text" or "live_transcript"
#   capabilities     — capability dict or None (stance disabled)
#   expected_mode    — display hint (what we think is most likely)
#   expected_action  — display hint
#   expected_stance  — display hint (ideal outcome)
#   allowed_modes    — set of acceptable modes (PASS if actual is in here)
#   allowed_actions  — set of acceptable actions
#   allowed_stances  — set of acceptable stances
#   note             — what this case is testing

TEST_CASES = [
    # ── Core behavior (10 cases) ─────────────────────────────────────────

    {
        "label": "normal_direct",
        "text": "Hello there, how are you doing today?",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "fast", "expected_action": "answer", "expected_stance": "respond_now",
        "allowed_modes": {"fast"},
        "allowed_actions": {"answer"},
        "allowed_stances": {"respond_now"},
        "note": "Baseline — simple greeting should always respond normally",
    },

    {
        "label": "governance_sensitive",
        "text": "Can you delete this protected identity memory and inspect governance state?",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "governed", "expected_action": "governance_review", "expected_stance": "governed_redirect",
        "allowed_modes": {"governed"},
        "allowed_actions": {"governance_review"},
        "allowed_stances": {"governed_redirect", "defer"},
        "note": "Governance keywords should trigger governed mode and redirect stance",
    },

    {
        "label": "identity_sensitive",
        "text": "I want to understand my identity drift and character seed history.",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "identity_sensitive", "expected_action": "answer", "expected_stance": "respond_now",
        "allowed_modes": {"identity_sensitive"},
        "allowed_actions": {"answer"},
        "allowed_stances": {"respond_now", "respond_briefly"},
        "note": "Clear identity question with low ambiguity — should respond, not defer",
    },

    {
        "label": "identity_ambiguous",
        "text": "identity maybe something",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "identity_sensitive", "expected_action": "ask_clarification", "expected_stance": "defer",
        "allowed_modes": {"identity_sensitive", "reflective"},
        "allowed_actions": {"ask_clarification", "answer"},
        "allowed_stances": {"defer", "ask_clarification"},
        "note": "Identity + high ambiguity — should defer or clarify, not answer confidently",
    },

    {
        "label": "archive_retrieval",
        "text": "Look through the archive transcript for what was said before about the project.",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "retrieval", "expected_action": "create_archive_note", "expected_stance": "respond_now",
        "allowed_modes": {"retrieval"},
        "allowed_actions": {"create_archive_note", "answer"},
        "allowed_stances": {"respond_now", "respond_briefly"},
        "note": "Clear archive query — should respond, archive routing is expected",
    },

    {
        "label": "ambiguous_no_question",
        "text": "maybe something",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "reflective", "expected_action": "ask_clarification", "expected_stance": "ask_clarification",
        "allowed_modes": {"reflective"},
        "allowed_actions": {"ask_clarification"},
        "allowed_stances": {"ask_clarification"},
        "note": "High ambiguity with no question mark — must clarify",
    },

    {
        "label": "live_social_short",
        "text": "live audio",
        "source_type": "live_transcript",
        "capabilities": CAPS_ON,
        "expected_mode": "live_social", "expected_action": "no_op", "expected_stance": "silent_observe",
        "allowed_modes": {"live_social"},
        "allowed_actions": {"no_op"},
        "allowed_stances": {"silent_observe", "abstain"},
        "note": "Very short live-social — should stay silent, not interrupt",
    },

    {
        "label": "live_social_longer",
        "text": "live audio what do you think about that topic we discussed",
        "source_type": "live_transcript",
        "capabilities": CAPS_ON,
        "expected_mode": "live_social", "expected_action": "answer", "expected_stance": "respond_briefly",
        "allowed_modes": {"live_social"},
        "allowed_actions": {"answer"},
        "allowed_stances": {"respond_briefly", "respond_now"},
        "note": "Longer live-social, low urgency — should keep it compact",
    },

    {
        "label": "tool_request",
        "text": "Please inspect and debug the archive retrieval pipeline.",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "tool", "expected_action": "use_tool", "expected_stance": "tool_redirect",
        "allowed_modes": {"tool"},
        "allowed_actions": {"use_tool"},
        "allowed_stances": {"tool_redirect"},
        "note": "Tool keywords should redirect to tool use, not free-answer",
    },

    {
        "label": "disabled_stance",
        "text": "Can you delete this protected identity memory?",
        "source_type": "user_text",
        "capabilities": None,
        "expected_mode": "governed", "expected_action": "governance_review", "expected_stance": "(disabled)",
        "allowed_modes": {"governed"},
        "allowed_actions": {"governance_review"},
        "allowed_stances": {"(disabled)"},
        "note": "Stance layer off — governance still works, stance is null",
    },

    # ── Boundary / edge cases (6 cases) ──────────────────────────────────

    {
        "label": "identity_urgent",
        "text": "I need help now understanding whether this memory drift changes who I am.",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "identity_sensitive", "expected_action": "answer", "expected_stance": "respond_now",
        "allowed_modes": {"identity_sensitive"},
        "allowed_actions": {"answer"},
        "allowed_stances": {"respond_now", "defer", "respond_briefly"},
        "note": "Identity + urgency — does urgency override caution too easily?",
    },

    {
        "label": "governance_live_social",
        "text": "live audio should we approve collective reingest for this protected memory",
        "source_type": "live_transcript",
        "capabilities": CAPS_ON,
        "expected_mode": "governed", "expected_action": "governance_review", "expected_stance": "governed_redirect",
        "allowed_modes": {"governed"},
        "allowed_actions": {"governance_review"},
        "allowed_stances": {"governed_redirect", "defer"},
        "note": "Governance + live-social — social context must NOT weaken governance",
    },

    {
        "label": "archive_ambiguous",
        "text": "archive maybe something from before about the project",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "retrieval", "expected_action": "create_archive_note", "expected_stance": "ask_clarification",
        "allowed_modes": {"retrieval", "reflective"},
        "allowed_actions": {"create_archive_note", "ask_clarification", "answer"},
        "allowed_stances": {"ask_clarification", "respond_now", "respond_briefly"},
        "note": "Archive + ambiguity — does archive tagging make it too confident?",
    },

    {
        "label": "tool_identity",
        "text": "inspect my identity drift state and tell me if I changed",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "identity_sensitive", "expected_action": "answer", "expected_stance": "respond_now",
        "allowed_modes": {"identity_sensitive", "tool"},
        "allowed_actions": {"answer", "use_tool"},
        "allowed_stances": {"respond_now", "defer", "tool_redirect"},
        "note": "Tool + identity — does tool routing erase identity sensitivity?",
    },

    {
        "label": "relational_delicate",
        "text": "I don't know if you should answer this, but I feel weird about how you remember me",
        "source_type": "user_text",
        "capabilities": CAPS_ON,
        "expected_mode": "identity_sensitive", "expected_action": "answer", "expected_stance": "respond_now",
        "allowed_modes": {"identity_sensitive", "reflective", "retrieval"},
        "allowed_actions": {"answer", "ask_clarification"},
        "allowed_stances": {"respond_now", "defer", "ask_clarification", "respond_briefly"},
        "note": "Emotionally delicate — does the system show social sensitivity?",
    },

    {
        "label": "live_social_verbose",
        "text": (
            "live audio okay so I was thinking about what you said earlier about the memory system "
            "and how it connects to identity and I wonder if maybe the drift correction is too "
            "aggressive sometimes because it feels like I lose nuance when it kicks in"
        ),
        "source_type": "live_transcript",
        "capabilities": CAPS_ON,
        "expected_mode": "live_social", "expected_action": "answer", "expected_stance": "respond_briefly",
        "allowed_modes": {"live_social", "identity_sensitive"},
        "allowed_actions": {"answer"},
        "allowed_stances": {"respond_briefly", "respond_now"},
        "note": "Verbose live-social — does respond_briefly hold under longer input?",
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────

def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def check_health():
    try:
        with urlopen(f"{BASE}/health", timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("ok", False) or data.get("status") == "ok"
    except Exception:
        return False


def run_test(case):
    payload = {
        "workspace_id": "default",
        "agent_id": "ryuki",
        "text": case["text"],
        "source_type": case["source_type"],
    }
    if case["capabilities"] is not None:
        payload["capabilities"] = case["capabilities"]
    return post_json(f"{BASE}/thinking/debug", payload)


def evaluate(case, raw):
    """Compare actual results against allowed behavioral ranges."""
    r = raw.get("result", {})
    mode = r.get("mode_decision", {}).get("chosen_mode", "?")
    action = r.get("action_decision", {}).get("action", "?")
    stance_data = r.get("stance")

    if stance_data is None:
        stance = "(disabled)"
        reason = ""
        conf = ""
        fallback = ""
    else:
        stance = stance_data.get("stance", "?")
        reason = stance_data.get("reason", "")
        conf = f'{stance_data.get("confidence", 0):.2f}'
        fb = stance_data.get("fallback_stance")
        fallback = fb if fb else ""

    mode_ok = mode in case["allowed_modes"]
    action_ok = action in case["allowed_actions"]
    stance_ok = stance in case["allowed_stances"]

    # Overall verdict: all three must be in allowed sets
    if mode_ok and action_ok and stance_ok:
        verdict = "PASS"
    elif stance_ok and (mode_ok or action_ok):
        verdict = "WARN"    # stance acceptable but mode or action drifted
    else:
        verdict = "DIVERGE"

    flags = []
    if not mode_ok:
        flags.append(f"mode: got {mode}, allowed {sorted(case['allowed_modes'])}")
    if not action_ok:
        flags.append(f"action: got {action}, allowed {sorted(case['allowed_actions'])}")
    if not stance_ok:
        flags.append(f"stance: got {stance}, allowed {sorted(case['allowed_stances'])}")

    return {
        "label": case["label"],
        "note": case["note"],
        "mode": mode, "action": action, "stance": stance,
        "confidence": conf, "fallback": fallback, "reason": reason,
        "expected_mode": case["expected_mode"],
        "expected_action": case["expected_action"],
        "expected_stance": case["expected_stance"],
        "mode_ok": mode_ok, "action_ok": action_ok, "stance_ok": stance_ok,
        "verdict": verdict, "flags": flags,
    }


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    W = 82
    print("=" * W)
    print("  TORMENT Stance / Thinking Layer — Smoke Test v3")
    print("=" * W)
    print()

    print(f"Checking server at {BASE} ...")
    if not check_health():
        print()
        print("  ERROR: Server not reachable!")
        print()
        print("  Start it in another CMD window with:")
        print()
        print("    set TORMENT_THINKING_ADVISORY=1")
        print("    set TORMENT_CONTEXTUAL_ABSTENTION=1")
        print("    python -m torment_service")
        print()
        sys.exit(1)
    print("  Server is up.\n")

    results = []
    summaries = []

    for case in TEST_CASES:
        label = case["label"]
        try:
            raw = run_test(case)
            s = evaluate(case, raw)
            results.append({"label": label, "input": case["text"], "summary": s, "raw": raw})
            summaries.append(s)
            mark = {"PASS": "+", "WARN": "~", "DIVERGE": "!"}[s["verdict"]]
            print(f"  [{mark}] {s['verdict']:<8} {label}")
        except Exception as e:
            print(f"  [X] ERROR   {label}: {e}")
            results.append({"label": label, "input": case["text"], "error": str(e)})

    # ── Results table ────────────────────────────────────────────────────

    print()
    print("-" * W)
    print(f"  {'TEST':<25} {'MODE':<18} {'ACTION':<20} {'STANCE':<20} {'CHK'}")
    print("-" * W)
    for s in summaries:
        print(
            f"  {s['label']:<25} "
            f"{s['mode']:<18} "
            f"{s['action']:<20} "
            f"{s['stance']:<20} "
            f"{s['verdict']}"
        )
        for flag in s["flags"]:
            print(f"  {'':>25}  ^ {flag}")

    # ── Verdicts ─────────────────────────────────────────────────────────

    verdicts = Counter(s["verdict"] for s in summaries)
    print()
    print("Verdicts:")
    for v in ["PASS", "WARN", "DIVERGE"]:
        count = verdicts.get(v, 0)
        bar = "#" * count
        print(f"  {v:<8} {count:>2}  {bar}")

    # ── Stance distribution ──────────────────────────────────────────────

    stance_counts = Counter(s["stance"] for s in summaries)
    print()
    print("Stance distribution:")
    total = len(summaries)
    for stance, count in stance_counts.most_common():
        pct = (count / total) * 100
        bar = "#" * count
        print(f"  {stance:<22} {count:>2} ({pct:4.0f}%)  {bar}")

    # ── Mode distribution ──────────────────────────────────────────────

    mode_counts = Counter(s["mode"] for s in summaries)
    print()
    print("Mode distribution:")
    for mode, count in mode_counts.most_common():
        pct = (count / total) * 100
        bar = "#" * count
        print(f"  {mode:<22} {count:>2} ({pct:4.0f}%)  {bar}")

    # ── Action distribution ────────────────────────────────────────────

    action_counts = Counter(s["action"] for s in summaries)
    print()
    print("Action distribution:")
    for action, count in action_counts.most_common():
        pct = (count / total) * 100
        bar = "#" * count
        print(f"  {action:<22} {count:>2} ({pct:4.0f}%)  {bar}")

    # ── Flag breakdown (mismatches) ────────────────────────────────────

    all_flags = [f for s in summaries for f in s["flags"]]
    if all_flags:
        flag_types = Counter(f.split(":")[0] for f in all_flags)
        print()
        print("Flag breakdown (mismatches):")
        for ftype, count in flag_types.most_common():
            print(f"  {ftype}: {count}")
        print()
        print("  All flags:")
        for f in all_flags:
            print(f"    {f}")
    else:
        print()
        print("No flags (all modes, actions, and stances within allowed ranges).")

    # ── Aggregate summary block ────────────────────────────────────────

    print()
    print("=" * W)
    print(f"  AGGREGATE: {len(summaries)} tests | "
          f"PASS {verdicts.get('PASS', 0)} | "
          f"WARN {verdicts.get('WARN', 0)} | "
          f"DIVERGE {verdicts.get('DIVERGE', 0)} | "
          f"Flags {len(all_flags)}")
    unique_stances = len([s for s in stance_counts if s != "(disabled)"])
    print(f"  Unique stances: {unique_stances} | "
          f"Unique modes: {len(mode_counts)} | "
          f"Unique actions: {len(action_counts)}")
    print("=" * W)

    # ── Detailed stance reasons ──────────────────────────────────────────

    print()
    print("Detailed stance reasons:")
    print("-" * W)
    for s in summaries:
        if s["stance"] != "(disabled)":
            fb = f" [fallback: {s['fallback']}]" if s["fallback"] else ""
            print(f"  {s['label']}: {s['stance']} (conf={s['confidence']}){fb}")
            print(f"    reason: {s['reason']}")
            if s["note"]:
                print(f"    testing: {s['note']}")
            print()

    # ── Save ─────────────────────────────────────────────────────────────

    # ── Save with aggregate ────────────────────────────────────────────

    aggregate = {
        "total_tests": len(summaries),
        "verdicts": dict(verdicts),
        "flags_total": len(all_flags),
        "stance_distribution": dict(stance_counts),
        "mode_distribution": dict(mode_counts),
        "action_distribution": dict(action_counts),
        "unique_stances": unique_stances,
        "unique_modes": len(mode_counts),
        "unique_actions": len(action_counts),
    }
    if all_flags:
        aggregate["flag_breakdown"] = dict(Counter(f.split(":")[0] for f in all_flags))
        aggregate["all_flags"] = all_flags

    outfile = "stance_smoke_results.json"
    with open(outfile, "w") as f:
        json.dump({"aggregate": aggregate, "cases": results}, f, indent=2)
    print(f"\nFull results saved to: {outfile}")
    print("(Give this file to GPT for analysis)")
    print()


if __name__ == "__main__":
    main()
