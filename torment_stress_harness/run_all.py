import argparse
from common import ensure_workspace, ensure_agent, health

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8787")
    ap.add_argument("--workspace", default="ws_stress")
    ap.add_argument("--agent", default="companion")
    args = ap.parse_args()

    ensure_workspace(args.base_url, args.workspace)
    ensure_agent(args.base_url, args.workspace, args.agent)

    h = health(args.base_url)
    print("Health:")
    print(h)

    print("\nNext:")
    print(f"python stress_liar.py --workspace {args.workspace} --agent {args.agent} --domain creative")
    print(f"python stress_motif_saturation.py --workspace {args.workspace} --agent {args.agent} --domain research --n 1200")
    print(f"python stress_mood_spiral.py --workspace {args.workspace} --agent {args.agent} --domain meta")

if __name__ == '__main__':
    main()
