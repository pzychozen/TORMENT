# TORMENT — Quick Start

v2.1

TORMENT is a **local memory service** you attach to any local LLM/character. It stores and retrieves **context** so your character can stay consistent. In v2.0, it also provides a living character identity layer — your character's personality emerges from memory, not just a static prompt. In v2.1, memory compression and spirit return give the system a complete lifecycle — memories form, compress, and return with warmth and voice.

## 1) Install and run

```bash
python -m pip install -r requirements.txt
python -m torment_service.app
```

Service defaults to: `http://127.0.0.1:8787`

### Optional: real embeddings (recommended)
```bash
python -m pip install sentence-transformers
```

Then set:

```bash
# Windows PowerShell
$env:TORMENT_EMBED_PROVIDER="st"
$env:TORMENT_EMBED_MODEL="BAAI/bge-small-en-v1.5"
$env:TORMENT_EMBED_DEVICE="cpu"
```

```bash
# Linux/Mac
export TORMENT_EMBED_PROVIDER=st
export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
export TORMENT_EMBED_DEVICE=cpu
```

## 2) Create a workspace and agent

```bash
curl -X POST http://127.0.0.1:8787/workspace/create \
  -H "Content-Type: application/json" \
  -d '{"workspace_id":"ws1"}'
```

### Without character (plain memory store)
```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{"workspace_id":"ws1","agent_id":"companion"}'
```

### With character seed (v2.0 — recommended)
```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id":"ws1",
    "agent_id":"aria",
    "seed": {
      "seed_text": "Aria is warm and curious, with a deep bond to her companion. She approaches problems with playful enthusiasm and genuine empathy.",
      "seed_id": "aria_v1"
    }
  }'
```

This plants the seed as deep canon memories, establishes a gravitational basin, and tunes the kernel physics to match the character.

## 3) The integration loop (what your client does)

### Before your model answers
1. Call TORMENT to retrieve memories:

```bash
curl -X POST http://127.0.0.1:8787/agent/query \
  -H "Content-Type: application/json" \
  -d '{"workspace_id":"ws1","agent_id":"aria","query":"What did we decide about X?","top_k":8}'
```

2. Inject returned memories into your model prompt (system or tool context). If using the character layer, the response includes a `character_context` block with the seed preamble, tier breakdown, drift summary, and recommendations.

### After your model answers
Summarize the turn (2-6 lines, stable) and ingest it:

```bash
curl -X POST http://127.0.0.1:8787/agent/ingest \
  -H "Content-Type: application/json" \
  -d '{"workspace_id":"ws1","agent_id":"aria","text":"Summary: ...","step":1}'
```

## 4) Enable compression and spirit return (v2.1 — optional)

To enable the full memory lifecycle (compression at corridor transitions + spirit return for deep memories):

```bash
export TORMENT_COMPRESS_ENABLE=1
```

This is all you need. Compression fires automatically at corridor transition events during ingest. Deep memories resurface during sparse queries with voice cues and warmth. No additional endpoints to call — the system is event-gated by design.

For tuning options, see `docs/TUNING.md`.

## 5) Recommended profile (one switch)

```bash
export TORMENT_PROFILE=companion
```

Check what's active with `GET /health`, `GET /profiles`, `GET /config`.

## 6) If something feels "off"

- `GET /embedder/check` — is embedding working?
- `POST /agent/query` with `continuity_debug=true` — why did it pick these memories?

See `docs/TROUBLESHOOTING.md` and `docs/TUNING.md` for detailed guidance.

For the full character system guide, see `docs/CHARACTER_SYSTEM.md`.
