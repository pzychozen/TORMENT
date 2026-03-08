# TORMENT Memory Fabric — v2.1

A dynamical **memory substrate** for AI agents, built around a TriOcta coupled-oscillator kernel that stabilizes memory formation, prevents drift, and maintains identity over long horizons.

Designed for local AI companions, multi-agent hive-minds (200+ bots), persistent identity experiments, and research environments.

TORMENT does not control personality. It stores and retrieves context in a stable way — and provides a living character identity layer that lets personality emerge from memory rather than static prompts, with a complete memory lifecycle through event-gated compression and spirit return.

---

## What's New in v2.1

**Event-Gated Memory Compression** — memories compress at discrete corridor transitions (not continuously). J→Z two-channel scoring (relational 60%, geometric 40%) with two-path routing: short-path fades, long-path exports to deep store. Protected classes (canon, identity, seeds) are never touched. Memories born during sustained corridors resist compression. See `docs/PROJECT_OVERVIEW.md` §6.

**Spirit Return with Symbolic Resonance** — compressed memories return through a 19-rule symbol interaction matrix with three modes: resonance (rare, vivid), surfacing (gentle, present-tense), and recollection (past-tense, distilled). Warmup mechanics prevent cold returns — warmth accumulates gradually with repeated retrieval. See `docs/PROJECT_OVERVIEW.md` §7.

**Character Prompt Layer** — spirit return hits flow into the character context with voice cues, flavor text, and tier classification. The character doesn't just recall memories — it recognizes them. See `docs/CHARACTER_SYSTEM.md`.

**Phase-Cycle Time** — explicit duration tracking of phases and corridors feeds into compression resistance and warmth boost. Sustained experience is structurally protected.

**185 Tests** — full coverage from unit through integration. The e2e suite walks a synthetic conversation through the entire pipeline: ingest → kernel → compression → deep memory → spirit return → character prompt.

## What Was New in v2.0

**Living Character System** — characters are gravitational basins in memory space. A minimal seed establishes the deepest attractor. Memory does the work. Drift protection keeps the character centered.

**Kernel-Character Unification** — character seeds modulate TriOcta oscillator physics. Different characters produce different memory dynamics from the same input.

**Symbolic Code Overhaul** — symbols.py and resonance.py rewritten with geometric projection and cycle detection.

---

## Docs

| Document | Description |
|----------|-------------|
| `docs/QUICKSTART.md` | 5-minute setup guide |
| `docs/GUIDE.md` | Detailed system guide |
| `docs/CHARACTER_SYSTEM.md` | Living character identity + spirit return voice layer |
| `docs/COMPANION_CONTRACT.md` | Philosophy — what TORMENT does and does not do |
| `docs/TUNING.md` | Configuration tuning (includes compression + spirit return) |
| `docs/TROUBLESHOOTING.md` | Operational fixes (includes compression + spirit return) |
| `docs/MEMORY_KERNEL_ARCHITECTURE.md` | Internal kernel design + compression gating + warmup mechanics |
| `docs/PROJECT_OVERVIEW.md` | Comprehensive architecture reference |

---

## Run

```bash
python -m pip install -r requirements.txt
bash run.sh
```

Service: `http://127.0.0.1:8787`

## Tests

```bash
python -m pip install -r requirements.txt
make test

# Or run directly with unittest (no pytest required):
python -m unittest discover -s tests -v

# Ship gate (compile + tests + deterministic sim replay)
make verify
```

---

## Architecture

TORMENT has four layers:

**Layer 1 — The Kernel** (`torment_service/kernel/`): a TriOcta phase-lock model (three coupled oscillators on Mexican-hat potentials with D24 phase scaffold). Produces stability signals — coherence, corridor alignment, identity state — that govern memory behavior. Accepts per-character modulation of coupling strength and phase angles.

**Layer 2 — The Fabric** (`torment_service/fabric.py` + modules): governance and orchestration. Routes observations through the kernel, manages memory graphs, motif registries, coherence fields, proposals, bridges, phase-cycle timing, and the character identity layer.

**Layer 3 — Compression + Spirit Return** (`compression.py`, `deep_memory.py`, `spirit_return.py`, `phase_timer.py`, `retrieval_assembler.py`): event-gated memory lifecycle. Compression fires at corridor transitions, deep memories return through symbolic resonance with warmth and voice cues.

**Layer 4 — Interfaces** (`app.py`, `sim/`, `tests/`): FastAPI REST service, simulation harness, stress tests, 185-test suite.

---

## Key Endpoints

**Health & config:**
- `GET /health`
- `GET /profiles` — preset definitions
- `GET /config` — effective configuration view
- `GET /embedder/check` — embedding diagnostic

**Workspace:**
- `POST /workspace/create` `{ workspace_id }`
- `GET /workspace/{workspace_id}/domains`
- `POST /workspace/clone` `{ source_workspace_id, target_workspace_id, reembed?, reembed_mode? }`
- `POST /workspace/maintenance` `{ workspace_id, mode }` — scan/repair/compact

**Agents:**
- `POST /agent/create` `{ workspace_id, agent_id, seed? }` — seed can include `seed_text` and `seed_id` for character layer
- `GET /agent/{agent_id}/identity?workspace_id=...`
- `GET /agent/{agent_id}/roles?workspace_id=...`
- `POST /agent/ingest` `{ workspace_id, agent_id, text, step, domain_id?, scope? }`
- `POST /agent/query` `{ workspace_id, agent_id, query, top_k, continuity_debug? }` — returns `character_context` when character is active
- `POST /agent/feedback` `{ workspace_id, agent_id, retrieved_ids, ... }`

**Compression & spirit return (v2.1):**
- `GET /workspace/{workspace_id}/spirit-return/status` — spirit return status

**Proposals & governance:**
- `GET /workspace/{workspace_id}/domain/{domain_id}/proposals`
- `POST /workspace/domain/proposals/decide`

---

## Embeddings

TORMENT defaults to deterministic hash embeddings for replay and testing. For production, enable real embeddings:

**SentenceTransformers (recommended):**
```bash
pip install sentence-transformers
export TORMENT_EMBED_PROVIDER=st
export TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
export TORMENT_EMBED_DEVICE=cpu
```

**Ollama:**
```bash
export TORMENT_EMBED_PROVIDER=ollama
export TORMENT_EMBED_MODEL=nomic-embed-text
export TORMENT_OLLAMA_URL=http://127.0.0.1:11434
```

Each workspace locks its embedding dimension. Switching embedders requires cloning to a new workspace.

---

## Enable Compression (v2.1)

```bash
export TORMENT_COMPRESS_ENABLE=1
```

That's it. Compression fires automatically at corridor transition events during ingest. Deep memories resurface during sparse queries with voice cues and warmth. See `docs/TUNING.md` for fine-tuning.

---

## Character System

Create agents with a character seed to activate living identity:

```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "ws1",
    "agent_id": "aria",
    "seed": {
      "seed_text": "Aria is warm and curious, with a deep bond to her companion. She approaches problems with playful enthusiasm and genuine empathy.",
      "seed_id": "aria_v1"
    }
  }'
```

This automatically plants seed memories, establishes a gravitational basin, and tunes the kernel physics to match the character. See `docs/CHARACTER_SYSTEM.md` for the full guide.

---

## Simulation

```bash
python -m sim.run_sim --workspace sim-ws --agents 50 --steps 400 --scenario mixed --out sim_out
```

Scenarios: `research`, `ops`, `creative`, `mixed`, `collaborative_mixed_200`.

---

## Defaults

- Workspaces have default domains: `research`, `engineering`, `operations`, `creative`, `meta`
- Agents: private-write, shared-read (shared-write requires proposal/governance)
- Character layer: enabled by default when `seed_text` is provided
- Compression: disabled by default (`TORMENT_COMPRESS_ENABLE=0`), enable for full lifecycle
- Kernel modulation: automatic when character is active

---

## Notes

- If you have a real summarizer/embedder, pass `supplied_summary` and/or `supplied_embedding` to `/agent/ingest`
- Otherwise TORMENT uses deterministic placeholders (hash-embed + simple summary fallback)
- Character seeds work best with real embeddings — hash embeddings produce orthogonal vectors so seed concepts don't cluster naturally, but the system still functions correctly
- The `data/` directory contains workspace state and should not be committed to version control
