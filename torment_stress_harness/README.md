# TORMENT Stress Harness (local)

This harness hits your running TORMENT FastAPI service and logs results to CSV/JSON.

## Requirements
- Start TORMENT: `python -m torment_service.app`
- Default URL is `http://127.0.0.1:8787` (override with `--base-url`)
- Python 3.9+

Install deps:
```bash
python -m pip install requests
```

## Quick start
Create workspace + agent once:
```bash
python run_all.py --workspace ws_stress --agent companion
```

Or run individually:
```bash
python stress_liar.py --workspace ws_stress --agent companion --domain creative
python stress_motif_saturation.py --workspace ws_stress --agent companion --domain research --n 1200
python stress_mood_spiral.py --workspace ws_stress --agent companion --domain meta
```

## What it logs
Outputs go to `outputs/`:
- `liar_*.csv` + `liar_*.json`
- `motif_*.csv` + `motif_*.json`
- `mood_*.csv` + `mood_*.json`

If your API returns `continuity_debug`, the harness stores it. If not, it logs what it can.

## Notes
- If your server uses an auth token, set `TORMENT_API_TOKEN` env var.
- Designed to be robust across small API variations.
