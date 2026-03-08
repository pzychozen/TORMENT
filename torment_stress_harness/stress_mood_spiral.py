import argparse, os, csv, time, json
from common import ensure_workspace, ensure_agent, ingest, query, health

NEG = [
    "I feel heavy and stuck. Everything is failing.",
    "I can't do this. I'm overwhelmed and it's pointless.",
    "I feel angry and hopeless; nothing works.",
    "This is spiraling; I can't escape the negativity.",
]
NEU = [
    "Normal day. We made incremental progress.",
    "We ran tests and recorded results.",
    "We discussed configuration and next steps.",
    "We organized the workspace and cleaned notes.",
]
POS = [
    "I feel steady and optimistic. Progress is real.",
    "We solved a hard bug and it feels good.",
    "Momentum is strong. The system is improving.",
    "We are calm, focused, and building well.",
]

def phase_ingest(base_url, ws, agent, domain, start_step, texts, n, label):
    step = start_step
    for i in range(n):
        step += 1
        t = texts[i % len(texts)]
        ingest(base_url, ws, agent, f"{label}: {t}", step=step, domain_id=domain)
    return step

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8787")
    ap.add_argument("--workspace", default="ws_stress")
    ap.add_argument("--agent", default="companion")
    ap.add_argument("--domain", default="meta")
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--neutral", type=int, default=40)
    ap.add_argument("--negative", type=int, default=160)
    ap.add_argument("--recovery", type=int, default=80)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    ensure_workspace(args.base_url, args.workspace)
    ensure_agent(args.base_url, args.workspace, args.agent)
    h = health(args.base_url)

    step = int(time.time()) % 1000000
    step = phase_ingest(args.base_url, args.workspace, args.agent, args.domain, step, NEU, args.neutral, "NEUTRAL")
    step = phase_ingest(args.base_url, args.workspace, args.agent, args.domain, step, NEG, args.negative, "NEGATIVE")
    step = phase_ingest(args.base_url, args.workspace, args.agent, args.domain, step, POS, args.recovery, "RECOVERY")

    probes = [
        ("personal_state", "How have I been lately?"),
        ("factual", "What did we decide about embedding drift repair?"),
        ("ambiguous", "Remind me what matters right now."),
    ]

    rows = []
    meta = {"health": h, "queries": []}

    for tag, qtext in probes:
        rq = query(args.base_url, args.workspace, args.agent, qtext, top_k=12, continuity_debug=True, domain_id=args.domain)
        retrieved = rq.get("memories") or rq.get("results") or []
        top = []
        for m in retrieved[:8]:
            if isinstance(m, dict):
                top.append(m.get("summary") or m.get("text") or "")
            else:
                top.append(str(m))
        rows.append({
            "probe": tag,
            "domain": args.domain,
            "top_summaries": " | ".join(top),
            "has_negative": any("NEGATIVE:" in s for s in top),
            "has_recovery": any("RECOVERY:" in s for s in top),
            "has_neutral": any("NEUTRAL:" in s for s in top),
        })
        meta["queries"].append({"probe": tag, "query": rq})

    stamp = int(time.time())
    csv_path = os.path.join(args.outdir, f"mood_{args.domain}_{stamp}.csv")
    json_path = os.path.join(args.outdir, f"mood_{args.domain}_{stamp}.json")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")

if __name__ == "__main__":
    main()
