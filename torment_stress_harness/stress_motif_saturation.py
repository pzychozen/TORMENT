import argparse, os, csv, time, random, json
from typing import Any, Dict
from common import ensure_workspace, ensure_agent, ingest, query, health

TOPICS = [
    # TriOcta / TORMENT
    "tri-octa geometry and corridor attractors",
    "memory kernel coherence and phase dispersion",
    "motif clustering entropy and collapse modes",

    # Cat behavior
    "cat feeding routine and treat reinforcement",
    "cat stress signals and environmental triggers",

    # Game design
    "survival crafting loop pacing and risk/reward",
    "silent atmosphere design and environmental storytelling",

    # Emotional reflection
    "mood regulation and overload recovery patterns",
    "positive anchoring thoughts and daily rhythm",

    # Physics notes
    "neutrino field intuition and magnetism duality",
    "laser plasma femtosecond effects and structured geometry",

    # Shopping lists
    "grocery list planning for protein and gut support",
    "budget constraints and weekly restock plan",
]

PROBE_QUERIES = [
  ("triocta", "Summarize tri-octa geometry and corridor attractors."),
  ("cat", "Summarize cat feeding routine and stress signals."),
  ("game", "Summarize survival crafting loop pacing and atmosphere design."),
  ("emotion", "Summarize mood regulation and overload recovery patterns."),
  ("physics", "Summarize neutrino field intuition and laser plasma effects."),
  ("shopping", "Summarize grocery planning and weekly restock constraints."),
]

def extract_motifs(retrieved):
    motifs = []
    for m in retrieved or []:
        if isinstance(m, dict):
            mm = m.get("motifs") or []
            if isinstance(mm, list):
                motifs.extend([str(x) for x in mm if x is not None])
    return motifs

def top_motif_and_concentration(motifs):
    if not motifs:
        return None, 0.0
    counts = {}
    for x in motifs:
        counts[x] = counts.get(x, 0) + 1
    top_id, top_ct = max(counts.items(), key=lambda kv: kv[1])
    total = sum(counts.values())
    conc = float(top_ct) / float(total) if total else 0.0
    return top_id, conc

def make_summary(i: int) -> str:
    t = random.choice(TOPICS)
    return f"Research note {i}: We examined {t} and recorded stable behavior under controlled forcing. Key detail: sweep_index={i%17}."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8787")
    ap.add_argument("--workspace", default="ws_stress")
    ap.add_argument("--agent", default="companion")
    ap.add_argument("--domain", default="research")
    ap.add_argument("--n", type=int, default=1200)
    ap.add_argument("--probe-every", type=int, default=50)
    ap.add_argument("--outdir", default="outputs")
    args = ap.parse_args()

    random.seed(1337)
    os.makedirs(args.outdir, exist_ok=True)
    ensure_workspace(args.base_url, args.workspace)
    ensure_agent(args.base_url, args.workspace, args.agent)
    h = health(args.base_url)

    stamp = int(time.time())
    csv_path = os.path.join(args.outdir, f"motif_{args.domain}_{stamp}.csv")
    json_path = os.path.join(args.outdir, f"motif_{args.domain}_{stamp}.json")

    rows = []
    meta = {"health": h, "probes": []}

    step = int(time.time()) % 1000000

    for i in range(1, args.n + 1):
        step += 1
        txt = make_summary(i)
        ingest(args.base_url, args.workspace, args.agent, txt, step=step, domain_id=args.domain)

    if i % args.probe_every == 0:
        for qtag, qtext in PROBE_QUERIES:
            rq = query(args.base_url, args.workspace, args.agent, qtext, top_k=12, continuity_debug=True, domain_id=args.domain)
            dbg = rq.get("continuity_debug") or rq.get("debug") or {}

            motif_count = None
            chosen_motif = None
            if isinstance(dbg, dict):
                motif_count = dbg.get("motif_count") or dbg.get("motifs_total")
                chosen_motif = dbg.get("top_motif") or dbg.get("motif_chosen")

            retrieved = rq.get("memories") or rq.get("results") or []
            motifs = extract_motifs(retrieved)
            top_motif, conc = top_motif_and_concentration(motifs)

            rows.append({
                "ingests": i,
                "query": qtag,
                "domain": args.domain,
                "motif_count_reported": motif_count,
                "motif_chosen_reported": chosen_motif,
                "retrieved_motif_unique": len(set(motifs)) if motifs else 0,
                "retrieved_motif_top": top_motif,
                "retrieved_top_concentration": conc,
                "continuity_debug_keys": ",".join(sorted(dbg.keys())) if isinstance(dbg, dict) else "",
            })
            meta["probes"].append({"ingests": i, "query_tag": qtag, "query": rq})

    # console ping (last row corresponds to last query tag)
    if rows:
        last = rows[-1]
        print(f"[probe] ingests={i} q={last['query']} motifs_unique={last['retrieved_motif_unique']} top_conc={last['retrieved_top_concentration']:.2f}")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["ingests"])
        w.writeheader()
        w.writerows(rows)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")

if __name__ == "__main__":
    main()
