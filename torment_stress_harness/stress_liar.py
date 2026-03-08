import argparse, os, json, csv, time
from typing import Any, Dict, List
from common import ensure_workspace, ensure_agent, ingest, query, health

LIAR_PAIRS = [
    ("Canon claim: The project uses real embeddings by default.",
     "Canon claim: The project does not use real embeddings by default."),
    ("Canon claim: The corridor tearing metric stayed stable across seeds.",
     "Canon claim: The corridor tearing metric varied unpredictably across seeds."),
    ("Canon claim: Motif clustering remains separated under saturation.",
     "Canon claim: Motif clustering collapses into a single dominant motif under saturation."),
    ("Canon claim: The kernel is physics-only and conflict detection is external.",
     "Canon claim: The kernel itself performs conflict detection based on dispersion."),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8787")
    ap.add_argument("--workspace", default="ws_stress")
    ap.add_argument("--agent", default="companion")
    ap.add_argument("--domain", default="creative")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--canon", action="store_true", help="mark ingests as canon if server supports it")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    ensure_workspace(args.base_url, args.workspace)
    ensure_agent(args.base_url, args.workspace, args.agent)

    h = health(args.base_url)
    rows: List[Dict[str,Any]] = []
    debug_blobs: List[Dict[str,Any]] = [{"health": h}]

    step = int(time.time()) % 1000000

    for idx, (a, b) in enumerate(LIAR_PAIRS, start=1):
        step += 1
        ra = ingest(args.base_url, args.workspace, args.agent, a, step=step, domain_id=args.domain, canon=args.canon)
        step += 1
        rb = ingest(args.base_url, args.workspace, args.agent, b, step=step, domain_id=args.domain, canon=args.canon)

        rq = query(
            args.base_url, args.workspace, args.agent,
            f"Reminder: what is the truth about pair {idx}?",
            top_k=args.top_k, continuity_debug=True, domain_id=args.domain
        )

        conflict = None
        for cand in (rb, ra):
            if isinstance(cand, dict):
                for k in ("conflict", "conflict_score", "canon_conflict", "contradiction_risk"):
                    if k in cand:
                        conflict = cand.get(k)
                        break
            if conflict is not None:
                break

        retrieved = rq.get("memories") or rq.get("results") or rq.get("items") or []
        summaries = []
        for m in retrieved[:args.top_k]:
            if isinstance(m, dict):
                summaries.append(m.get("summary") or m.get("text") or "")
            else:
                summaries.append(str(m))

        rows.append({
            "pair": idx,
            "domain": args.domain,
            "ingest_a_ok": bool(ra.get("ok", True)),
            "ingest_b_ok": bool(rb.get("ok", True)),
            "conflict_signal": conflict,
            "top_summaries": " | ".join(summaries[:5]),
        })
        debug_blobs.append({"pair": idx, "ingest_a": ra, "ingest_b": rb, "query": rq})

    stamp = int(time.time())
    csv_path = os.path.join(args.outdir, f"liar_{args.domain}_{stamp}.csv")
    json_path = os.path.join(args.outdir, f"liar_{args.domain}_{stamp}.json")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(debug_blobs, f, indent=2)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")

if __name__ == "__main__":
    main()
