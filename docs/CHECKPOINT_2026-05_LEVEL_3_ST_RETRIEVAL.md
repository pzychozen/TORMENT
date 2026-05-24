# Checkpoint — Level 3 ST Retrieval-Quality Smoke

**Date:** 2026-05-24
**Status:** Closed / Ratified — PASS
**Cluster:** 5 § 9.3 Path C (Q2 lifecycle envelope) — operational follow-up
**Source changes:** None. Operator-run smoke only. No commits in scope.

---

## Summary

This checkpoint closes the Level 3 ST retrieval-quality smoke, the only
deferred item left after the Q2-D tool-result doctrine arc
(`CHECKPOINT_2026-05_Q2D_TOOL_RESULT_DOCTRINE.md`). It proves that an
external provider response written through `POST /tool/ingest` becomes
**semantically retrievable** via `POST /agent/query` when the service
runs with the SentenceTransformers embedder, while the Q2-D doctrine
invariants (lifecycle envelope, provenance preservation,
non-canonization of tool-result rows) remain intact.

The smoke ran in a fresh ST workspace (`default_st`) under a fresh agent
(`external_inference_smoke_st`) to avoid the silent
mixed-hash/ST-embedder failure mode discovered during the survey — a
mode in which dim-only guards at three layers (`embedding_store.py`,
`Workspace.__init__`, `fabric.query`) coincide at dim=384 for both
`HashEmbedding` default and `BAAI/bge-small-en-v1.5`, allowing
cross-space cosine scores that are mathematically defined but
semantically meaningless. The fresh-workspace design eliminates that
mode by construction.

Verdict: **Level 3 ST retrieval-quality smoke passes — external
tool-result rows written through `/tool/ingest` remain
non-canonical/unprotected while becoming semantically retrievable under
ST embeddings in a clean ST workspace.**

---

## Goal (recap from plan v0.2)

Prove a `/tool/ingest`-written external provider response is
semantically retrievable via `/agent/query` under
`TORMENT_EMBED_PROVIDER=st`, `TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5`,
`TORMENT_EMBED_DEVICE=cpu`, while the row's lifecycle envelope remains
`state=unset / set_by.via=ingest_unmarked / lifecycle_disagreement=null`
and its provenance is preserved through retrieval as
`source_type=tool_result / write_path=tool_ingest`.

Discrimination design: ingest three semantically-rich prompts on
distinct topics (biology / astronomy / history); query each topic with a
zero-or-low-token-overlap probe; assert the resulting 3×3 cosine matrix
is diagonal-dominant.

---

## Environment / embedder preflight

`/health` on the running service confirmed the active embedder:

```
provider                 = st
model                    = BAAI/bge-small-en-v1.5
dim                      = 384
embedder_degraded        = false
```

`/embedder/check` (probe call):

```
ok           = true
provider     = st
model        = BAAI/bge-small-en-v1.5
dim          = 384
degraded     = false
error        = ""
hint         = ""
elapsed_ms   = 14.826...
```

---

## Workspace and agent

Fresh artifacts, no contact with the pre-existing `default` workspace or
its hash-embedded eid=1..4 rows in `default/external_inference_smoke`.

```
workspace_id = default_st
agent_id     = external_inference_smoke_st
```

---

## Ingest receipts

Three independent invocations of `tests/run_external_inference_smoke.py`,
each `--ingest` POSTing to `/tool/ingest` with a distinct prompt and the
fresh workspace/agent IDs. Provider: OpenRouter, model
`google/gemini-2.5-flash`.

```
eid=1 biology
  Prompt:           plants / sunlight / chloroplasts / glucose
  stored:           true
  promotion_score:  0.8679967448
  summary starts:   "Plants capture sunlight using chlorophyll within
                    their chloroplasts..."

eid=2 astronomy
  Prompt:           black hole / event horizons / gravitational lensing
  stored:           true
  promotion_score:  0.8789545367
  summary starts:   "A black hole bends light due to its incredibly
                    strong gravitational field..."

eid=3 history
  Prompt:           printing press / Gutenberg / movable type
  stored:           true
  promotion_score:  0.8720208944
  summary starts:   "Gutenberg's invention of the printing press with
                    movable type..."
```

---

## Lifecycle invariant — all three rows

`tools/inspect_lifecycle.py --workspace-id default_st
 --agent-id external_inference_smoke_st`:

```
rows_total: 3

eid=1:
  source_type             = tool_result
  write_path              = tool_ingest
  lifecycle_status.state  = unset
  is_authoritative_on_row = true
  set_by.actor            = system
  set_by.via              = ingest_unmarked
  lifecycle_disagreement  = null

eid=2:
  source_type             = tool_result
  write_path              = tool_ingest
  lifecycle_status.state  = unset
  is_authoritative_on_row = true
  set_by.actor            = system
  set_by.via              = ingest_unmarked
  lifecycle_disagreement  = null

eid=3:
  source_type             = tool_result
  write_path              = tool_ingest
  lifecycle_status.state  = unset
  is_authoritative_on_row = true
  set_by.actor            = system
  set_by.via              = ingest_unmarked
  lifecycle_disagreement  = null

Summary:
  all_lifecycle_unset_system_ingest_unmarked = true
  any_disagreement_detected                  = false
```

---

## Retrieval — 3×3 cosine matrix

Each query was a separate `POST /agent/query` with `top_k=5`. Each
response was inspected for diagonal placement and embedder-context
invariants.

```
Query 1: "How do leaves create food from light?"

  eid=1 biology    score=0.7835524948  raw=0.7837446928  rank #1
  eid=2 astronomy  score=0.5740256281  raw=0.5741460323  rank #2
  eid=3 history    score=0.5184170362  raw=0.5185049772  rank #3
  Result: PASS — biology row ranks above astronomy and history.

Query 2: "What happens to starlight near a singularity?"

  eid=2 astronomy  score=0.6913325651  raw=0.6914839149  rank #1
  eid=1 biology    score=0.5194604602  raw=0.5195926428  rank #2
  eid=3 history    score=0.5166320318  raw=0.5167244077  rank #3
  Result: PASS — astronomy row ranks above biology and history.

Query 3: "How did mechanical text duplication affect medieval education?"

  eid=3 history    score=0.7259236305  raw=0.7260575891  rank #1
  eid=2 astronomy  score=0.4981719456  raw=0.4982838631  rank #2
  eid=1 biology    score=0.4090683333  raw=0.4091747701  rank #3
  Result: PASS — history row ranks above astronomy and biology.
```

Compact form:

```
                   eid=1 bio    eid=2 astro    eid=3 history
bio query           0.78355      0.57403        0.51842
astro query         0.51946      0.69133        0.51663
history query       0.40907      0.49817        0.72592
```

Diagonal dominance is unambiguous. Margins of the matched row over its
nearest competitor:

```
bio query:        0.78355 - 0.57403 = 0.20952
astro query:      0.69133 - 0.51946 = 0.17187
history query:    0.72592 - 0.49817 = 0.22775
```

A hash-fallback corpus would produce near-random scores on these
zero-token-overlap queries, not 0.17-0.23 margins on the matched
row. The matrix shape is decisive evidence that ST retrieval is
operating as intended.

---

## Embedder-context invariant (in every query response)

```
embed_context.embedder.provider           = st
embed_context.embedder.model              = BAAI/bge-small-en-v1.5
embed_context.embedder.dim                = 384

embed_context.workspace_lock.workspace_id = default_st
embed_context.workspace_lock.embed_provider = st
embed_context.workspace_lock.embed_model    = BAAI/bge-small-en-v1.5
embed_context.workspace_lock.embed_dim      = 384
```

Running embedder and workspace lock agree. No silent drift between
runtime and persisted identity.

---

## Provenance invariant (matched rows in query response)

```
provenance.source_type     = tool_result
provenance.write_path      = tool_ingest
provenance.tool_name       = external_inference_smoke:openrouter:google/gemini-2.5-flash
```

Also surfaced via the flattened mirrors:

```
provenance_type            = tool_result
provenance_tool_name       = external_inference_smoke:openrouter:google/gemini-2.5-flash
```

Provenance survives the full
`POST /tool/ingest → spawn_memory → /agent/query → results[]` round trip.

---

## Cross-doctrine confirmation: Q2-D suppression holds under ST

A second piece of evidence emerged that was not part of the Level 3
exit criteria but is worth recording.

All three ingested rows reported `promotion_score` between **0.8679 and
0.8790** — well above the 0.78 auto-canon threshold in
`fabric.ingest`'s coherence path. Under pre-Q2-D-doctrine behavior, each
of these rows would have been stamped `canon=True` and given the
PROTECTED / SYSTEM / CANON_SET lifecycle envelope.

Under the ratified Q2-D suppression doctrine (`8733662`) all three rows
instead landed as `canon=false` and `UNSET / SYSTEM / INGEST_UNMARKED`,
confirmed both by the lifecycle inspector and by the `canon: false`
field on every matched item in the query responses.

This is independent confirmation that
`_fast_tool_result_ingest`'s `suppress_canon=True` flag continues to
override the kernel's auto-canon decision under a different embedder
backend. The Q2-D doctrine is embedder-agnostic, as designed.

---

## Documentation / wording notes (not blockers)

- **Response key is `results[]`, not `items[]`.** The Level 3 plan
  v0.2 referred to `items[]` in pass criterion (d). The actual
  `/agent/query` response uses `results[]`, defined at
  `fabric.py:4262` and explicitly called out by the comment at
  `fabric.py:4153` ("the returned 'results' key. One filter, four
  protected surfaces"). The smoke passed regardless because the
  operator read the actual response shape. This note is for future
  alignment of plan text with the API contract.
- **`/agent/trace` does use `items[]`** (`fabric.py:6540`). The two
  endpoints' return-key conventions differ. Worth keeping straight
  when writing new operator scripts.
- **QUICKSTART entrypoint discrepancy still open.** `docs/QUICKSTART.md`
  line 11 documents `python -m torment_service.app`; the canonical
  entrypoint is `python -m torment_service`. Not Level 3 work; flagged
  in `NEXT_CHAT_HANDOFF_2026-05-24.md` and remains a future doc-fix
  candidate.

---

## Ratified decisions (additive to the Q2-D checkpoint)

1. **ST retrieval is operationally proven** for the
   `BAAI/bge-small-en-v1.5` model at dim=384, device=cpu, with
   external tool-result rows written through `/tool/ingest`.
2. **Fresh-workspace pattern is the canonical way to introduce a new
   embedder regime**, until and unless an explicit re-embedding
   migration (`fabric.clone_workspace(..., reembed=True)`) is ratified
   as a slice. Reusing an existing workspace under a new embedder
   provider is an unsupported configuration.
3. **`default_st / external_inference_smoke_st` is the canonical ST
   smoke target.** Future ST retrieval work can extend this
   workspace/agent rather than create new ones, so long as embedder
   identity is preserved.
4. **Q2-D suppression doctrine is embedder-agnostic** under direct
   live evidence. No further action needed on this front.

---

## Non-goals preserved through this checkpoint

- No Slice 6 (hard migration of legacy protected markers).
- No retroactive migration of `default/external_inference_smoke`
  eid=1..4 (still hash-embedded; intentional historical evidence).
- No new write paths beyond `/tool/ingest`.
- No HTTP lifecycle parity (MCP `resource_provenance` + local
  inspector remain the lifecycle-envelope inspection surfaces).
- No autonomy loops, no scheduled tasks, no background sweeps.
- No multi-turn or streaming on the external smoke.
- No real provider calls from pytest (operator-run scripts only).
- No new env vars, no new endpoints, no broad refactor.
- No code changes in this arc: this checkpoint records an
  operator-run proof and a written audit trail. No commits in scope.

---

## References

- Plan: in-chat `Level 3 ST Retrieval-Quality Smoke — Plan v0.2`
  (2026-05-24)
- Predecessor: `docs/CHECKPOINT_2026-05_Q2D_TOOL_RESULT_DOCTRINE.md`
- Doctrine: `docs/TOOL_RESULT_LIFECYCLE_POLICY.md` §0
- Smoke script: `tests/run_external_inference_smoke.py`
- Inspector: `tools/inspect_lifecycle.py`
- Embedder factory: `torment_service/embeddings.py` (`build_embedder_from_env`)
- Workspace lock: `torment_service/fabric.py` (`Workspace.__init__`,
  `_embed_context`)
- Embedding store dim guard: `torment_service/embedding_store.py`
  (`EmbeddingShardWriter.__init__`)
- Handoff: `NEXT_CHAT_HANDOFF_2026-05-24.md`
