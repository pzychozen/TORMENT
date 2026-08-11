# TORMENT REST Auth Surface Audit - 2026-08-11

Scope: `torment_service/app.py` on the local v2.5.0 pre-release line after commit `abff330d06ff7e4234cad8c6cb99d557a28c2b18`.

## Summary

- FastAPI route declarations inventoried: 93
- PUBLIC_SAFE: 2
- AUTH_REQUIRED_READ: 61
- AUTH_REQUIRED_WRITE: 30
- Existing handler-local `resolve_request_context` coverage before systemic repair: 12 routes

The original GHSA fix `b76a1594cb968d99291f94aa8e1a8b54c9f00cd9` protected the five disclosed `/archive/*` handlers, but the route inventory showed that handler-local auth enforcement was an omission-prone pattern. The repair selected for v2.5.0 is an application-level default-deny REST auth middleware when `TORMENT_AUTH_ENABLE=1`, plus a tiny explicit public-safe allowlist. Existing per-handler `resolve_request_context` calls remain in place where endpoint code needs workspace/agent-specific `RequestContext` values for Spine and trust behavior.

## Public-Safe Allowlist

These routes do not read workspace, agent, memory, runtime state, configuration, diagnostics, or security state:

- `GET /retrieve/profiles` - static in-code retrieval assembler profile metadata.
- `GET /thinking/debug/geo_profiles` - static in-code geometric debug profile metadata.

Notable non-public choices:

- `GET /health` is protected because it exposes version, active profile details, workspace metadata samples, embedder configuration, auth key count, and lock stats.
- `GET /config` and `GET /profiles` are protected because they expose effective configuration/profile details.
- `GET /spine/operations` is protected because it exposes operation and trust-policy surface.
- Debug and observability endpoints are protected because they expose private memory, provenance, runtime, or operational state.

## Route Inventory

| Method | Path | Handler | Handler calls auth? | Reads private/state? | Mutates data/state? | Classification |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/workspace/{workspace_id}/embed_audit` | `workspace_embed_audit` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspaces/embed_audit_summary` | `workspaces_embed_audit_summary` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/health` | `health` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/profiles` | `profiles` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/config` | `config` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspaces/meta` | `workspaces_meta` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/embedder/check` | `embedder_check` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/create` | `workspace_create` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/workspace/clone` | `workspace_clone` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/workspace/repair_embeddings` | `workspace_repair_embeddings` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/workspace/repair_embeddings/job` | `workspace_repair_embeddings_job` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/workspace/repair_embeddings/jobs` | `repair_jobs` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/repair_embeddings/job/{job_id}` | `repair_job` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/repair_embeddings/job/{job_id}/cancel` | `cancel_repair_job` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/workspace/maintenance` | `workspace_maintenance` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/workspace/maintenance/job` | `workspace_maintenance_job` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/workspace/clone/jobs` | `clone_jobs` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/clone/job/{job_id}` | `clone_job` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/domains` | `list_domains` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/agent/create` | `agent_create` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/agent/{agent_id}/identity` | `get_identity` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/agent/{agent_id}/roles` | `get_roles` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/agent/{agent_id}/character/state` | `get_character_state` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/agent/{agent_id}/character/seed` | `get_character_seed` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/memory/governance/set` | `set_governance_flags` | yes | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/memory/governance/get` | `get_governance_flags` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/governance/audit` | `governance_audit` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/collective/status` | `collective_status` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/collective/packets` | `collective_packets` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/collective/events` | `collective_events` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/collective/events/{event_id}` | `collective_event_detail` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/{workspace_id}/collective/reingest` | `collective_reingest` | yes | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/workspace/{workspace_id}/collective/proposals/status` | `collective_proposals_status` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/agent/ingest` | `ingest` | yes | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/agent/ingest/route_probe` | `ingest_route_probe` | yes | yes | no | AUTH_REQUIRED_READ |
| POST | `/agent/query` | `query` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/agent/trace` | `trace` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/memory/chain` | `memory_chain` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/memory/trace_full` | `memory_trace_full` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/memory/trace_bundle` | `memory_trace_bundle` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/memory/trace_view` | `memory_trace_view` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/agent/feedback` | `feedback` | yes | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/workspace/{workspace_id}/domain/{domain_id}/motifs/active` | `active_motifs` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/bridges` | `list_bridges` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/bridges/queue` | `bridges_queue` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/bridges/decide` | `decide_bridge` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/agent/propose_share` | `propose_share` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/workspace/process_proposals` | `process_proposals` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/workspace/{workspace_id}/domain/{domain_id}/proposals` | `list_proposals` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/domain/proposals/decide` | `decide_proposal` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/workspace/domain_suggestions/approve` | `approve_domain` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/workspace/{workspace_id}/domain_suggestions` | `domain_suggestions` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/domain/{domain_id}/motif_entropy` | `motif_entropy` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/domain/{domain_id}/motif_merges` | `list_motif_merges` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/motif_merges/decide` | `decide_motif_merge` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/workspace/{workspace_id}/domain/{domain_id}/conflicts` | `list_conflicts` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/conflicts/decide` | `decide_conflict` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/archive/ingest_document` | `ingest_document` | yes | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/archive/query` | `archive_query` | yes | yes | no | AUTH_REQUIRED_READ |
| GET | `/archive/{workspace_id}/{agent_id}/documents` | `archive_list_documents` | yes | yes | no | AUTH_REQUIRED_READ |
| GET | `/archive/{workspace_id}/{agent_id}/document/{doc_id}` | `archive_get_document` | yes | yes | no | AUTH_REQUIRED_READ |
| DELETE | `/archive/{workspace_id}/{agent_id}/document/{doc_id}` | `archive_delete_document` | yes | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/retrieve` | `retrieve_assembled` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/retrieve/profiles` | `list_retrieval_profiles` | no | no | no | PUBLIC_SAFE |
| GET | `/index/{workspace_id}/{agent_id}/recent` | `index_recent_memories` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/index/{workspace_id}/{agent_id}/motif/{motif_id}` | `index_memories_by_motif` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/index/{workspace_id}/{agent_id}/trajectory` | `index_trajectory_range` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/index/{workspace_id}/{agent_id}/events` | `index_events_by_type` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/index/{workspace_id}/{agent_id}/archive/search` | `index_archive_search` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/index/{workspace_id}/{agent_id}/stats` | `index_stats` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/index/rebuild` | `index_rebuild` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/checkpoint/save` | `checkpoint_save` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/checkpoint/{workspace_id}/{agent_id}/latest` | `checkpoint_latest` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/checkpoint/{workspace_id}/{agent_id}/list` | `checkpoint_list` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/promote` | `promote_chunk_endpoint` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/promote/suggestions/{workspace_id}/{agent_id}` | `promote_suggestions` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/{workspace_id}/compress/trigger` | `trigger_compression` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/workspace/{workspace_id}/compress/status` | `compression_status` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/workspace/{workspace_id}/spirit-return/status` | `spirit_return_status` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/{workspace_id}/spirit-reflections/process` | `process_spirit_reflections_endpoint` | no | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/workspace/{workspace_id}/spirit-reflections/status` | `spirit_reflections_status` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/workspace/{workspace_id}/deep-memory/query` | `deep_memory_query` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/cognition/run` | `cognition_run` | no | yes | yes | AUTH_REQUIRED_WRITE |
| POST | `/spine/submit_task` | `spine_submit_task` | yes | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/spine/operations` | `spine_list_operations` | no | yes | no | AUTH_REQUIRED_READ |
| POST | `/tool/ingest` | `tool_result_ingest` | yes | yes | yes | AUTH_REQUIRED_WRITE |
| GET | `/spine/status` | `spine_status` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/thinking/debug/geo_profiles` | `list_geo_profiles` | no | no | no | PUBLIC_SAFE |
| POST | `/thinking/debug` | `thinking_debug` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/spine/thinking_alignment/recent` | `thinking_alignment_recent` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/spine/alignment` | `thinking_alignment_recent` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/debug/metrics` | `debug_metrics` | no | yes | no | AUTH_REQUIRED_READ |
| GET | `/debug/provenance` | `debug_provenance` | no | yes | no | AUTH_REQUIRED_READ |

## Repair Choice

The selected repair is default-deny middleware rather than adding more handler-local calls. Reasons:

- It preserves `TORMENT_AUTH_ENABLE=0` local/no-auth behavior.
- It preserves the existing `X-API-Key` header and `api_key` query parameter accepted by `resolve_request_context`.
- It fails closed for future routes unless a maintainer explicitly adds them to `PUBLIC_SAFE_REST_ROUTES`.
- It leaves existing per-handler checks intact so Spine trust enforcement and workspace/agent-specific contexts continue to work.
- It avoids changing Fabric, memory lifecycle, Spine governance, cognition, or trust architecture.
