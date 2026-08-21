# TORMENT Brainvision Phase 9 VHE Sidecar Specification v1.0

## Status and authority

**FROZEN PRE-IMPLEMENTATION PHASE-9 SPECIFICATION**

Phase 9 owns recursive VHE continuation persistence only: strict DTO/schema validation, canonical serialization, contained paths, mechanical load/write, a pure fresh builder, and pure configuration/sidecar compatibility classification.

Configuration remains authoritative for lifecycle status and replay watermark. The sidecar is authoritative for recursive continuation state, committed active visual time, and its accepted source-sequence copy. Lifecycle status is not independently authoritative in the sidecar.

Phase 10 owns lifecycle authorization, recovery actions, transaction ordering, known-agent proof, locking, runtime allocation, watermark repair, and orphan deletion. Phase 9 performs no enable/suspend/resume/reset/disable orchestration, recovery action, watermark repair, or orphan deletion. It does not reopen Phases 0-8.

## 1. Sidecar schema

The fixed schema ID is `brainvision.vhe.sidecar.v1`.

The exact complete top-level field set is:

```text
schema_id
configuration_schema_id
stream_identity
adapter_contract_id
accepted_source_sequence
expected_operator_id
expected_projection_id
modulation_schema_id
modulation_mapping_id
modulation_profile_schema_id
theta
modulation_profile_id
committed_active_time_ns
vhe_state
```

No other top-level field is admitted. In particular, no `lifecycle_status`, authoritative configuration watermark, projection field, W/c diagnostic, process-local origin, monotonic source, accumulation flag, or content-derived sidecar identity is admitted.

## 2. Exact nested VHE state

`vhe_state` contains exactly `fast_trace`, `persistent_context`, and `semantic_register`.

`fast_trace` contains exactly `amplitude_1_q`, `amplitude_2_q`, and `remaining_ns`.

`persistent_context` contains exactly `luminance_q`, `contrast_q`, and `orientation_q`.

`semantic_register` contains exactly `entries` and `open_semantic_event_class`.

Each `entries` item contains exactly `semantic_event_class`, `first_seen_active_time_ns`, `last_seen_active_time_ns`, and `occurrence_count`.

Load reconstructs frozen `VheState`, `FastTrace`, `PersistentContext`, `SemanticRegister`, and `SemanticRegisterEntry` values. Recursive state must not be reconstructed from Phase-5 projections.

## 3. Exact numerical representation and encoding

The subsequently frozen Phase-3/4 implementation has no IEEE floating-point continuation values. Persisted continuation numerics are exact Python integers; no float-to-decimal persistence or IEEE bit-pattern encoding is required. Canonical JSON decimal integer encoding preserves exactly the continuation values used by the frozen implementation.

`T_PRODUCT_V1_SECONDS = 300.0` is a non-continuation convenience constant and is not persisted. Durable active time is integer nanoseconds only.

Canonical bytes are ASCII JSON with `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=True`, and `allow_nan=False`.

Every object level has an exact field set. Missing fields, unknown fields, duplicate JSON keys, defaults, coercion, and migration are rejected. Duplicate keys fail closed; no duplicate value may silently win.

## 4. FastTrace F

| Field | Exact type | Range |
| --- | --- | --- |
| `amplitude_1_q` | non-bool integer | -1,000,000 .. +1,000,000 |
| `amplitude_2_q` | non-bool integer | 0 .. 1,000,000 |
| `remaining_ns` | non-bool integer | 0 .. 5,000,000,000 |

The canonical inactive FastTrace is `(0, 0, 0)`. The frozen invariant is `remaining_ns == 0` iff both amplitudes are zero. Load reconstructs `FastTrace` and rejects noncanonical F; it does not normalize invalid F or invent offline decay.

## 5. PersistentContext S

Persist exactly `luminance_q`, `contrast_q`, and `orientation_q`. Each is a non-bool exact integer in `-1,000,000 .. +1,000,000`; fresh S is `(0, 0, 0)`. Persistence neither clips nor quantizes S and never substitutes Phase-5 projection values.

## 6. SemanticRegister R

The loaded register restores tuple semantics. It has at most eight entries; tokens are unique and entries are lexicographically sorted by `semantic_event_class`.

| Entry field | Exact type and invariant |
| --- | --- |
| `semantic_event_class` | valid frozen namespaced token string |
| `first_seen_active_time_ns` | non-bool exact integer, `>= 0` |
| `last_seen_active_time_ns` | non-bool exact integer, `>= first_seen_active_time_ns` |
| `occurrence_count` | non-bool exact integer, `1 .. 9223372036854775807` |

`open_semantic_event_class` is `null` iff entries are empty; otherwise it must reference a stored token. R must not be reconstructed from open-event or recurrence projection codes.

For every entry, `first_seen_active_time_ns <= committed_active_time_ns` and `last_seen_active_time_ns <= committed_active_time_ns`. This sidecar-level invariant prevents a durable snapshot from containing an event after committed active visual time.

## 7. Active time and accepted sequence

The sole persisted visual-time field is `committed_active_time_ns`. It requires `type(value) is int`, rejects `bool`, and has range `>= 0`; Phase 3 freezes no arbitrary signed-64 upper bound.

The sidecar never persists `process_local_origin_ns`, `monotonic_ns_source`, or `is_accumulating`. Phase 10 later constructs and rebases process-local clock state under lifecycle authority.

`accepted_source_sequence` is a non-bool exact integer in `-1 .. 9223372036854775807`. It is the sidecar copy, not the authoritative configuration watermark. The fresh builder copies `configuration.last_accepted_source_sequence` exactly, including `-1` for a new lineage and a larger retained watermark after reset.

## 8. Lineage and continuation identities

The sidecar persists and strictly validates `configuration_schema_id`, `stream_identity`, `adapter_contract_id`, `expected_operator_id`, `expected_projection_id`, `modulation_schema_id`, `modulation_mapping_id`, `modulation_profile_schema_id`, `theta`, and `modulation_profile_id`.

`configuration_schema_id` equals `brainvision.configuration.v1`. `stream_identity` establishes replay/order lineage. `adapter_contract_id` establishes descriptor-measurement semantic lineage. Both are copied from and must exactly match configuration.

The frozen continuation identities are:

```text
expected_operator_id = bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb
expected_projection_id = bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f
modulation_schema_id = brainvision.character_modulation.v1
modulation_mapping_id = bvmodmap1_f8b41a1987437410613157ae403d10ac12fbce3b34cc760f0cc8376193206aeb
modulation_profile_schema_id = brainvision.character_modulation.profile.v1
```

`theta` is a non-bool exact integer in `{-1, 0, +1}`. The stored profile ID must match the exact frozen profile derived from theta:

| theta | `modulation_profile_id` |
| ---: | --- |
| -1 | `bvmodprof1_95cf73f228a5c02a16e13b90cf17aa46d31bbc312643f7dbf374d33816d9ad49` |
| 0 | `bvmodprof1_9f65a350c2526bc63733e9267d7846ce4eace56a6c4ec3261bfc748a18287abc` |
| +1 | `bvmodprof1_ceeb161b2dcb510601d85fc7b5a64eb023827bb044220b046b2c61b98be422f5` |

Every sidecar identity copy matches configuration before sequence comparison. No F/S/R produced under profile A may continue under profile B.

## 9. Sidecar path, read, and write

The sole Phase-9 sidecar path is `<data_root>/workspaces/<workspace_id>/agents/<agent_id>/brainvision/vhe_state.json`.

Path derivation creates nothing and uses the Phase-8 configuration-path boundary or an equivalent contained construction. A sidecar write requires the existing Brainvision directory. It must not create data root, workspace, ordinary-agent directory, or Brainvision directory. Missing Brainvision directory causes write failure without creating ordinary-agent filesystem state.

Low-level load returns `None` only when `vhe_state.json` is absent; it creates nothing. Existing malformed or incompatible bytes raise. Phase 9 does not inspect lifecycle status to interpret absence; Phase 10 later interprets disabled-plus-absence as valid and active/suspended-plus-absence as a hard failure.

Write uses a unique same-directory temporary file: validate sidecar; derive target; require Brainvision directory; create temp; validate target/temp containment; write canonical ASCII bytes; flush; file-`fsync`; close; then `os.replace(temp, target)`. If failure occurs before replacement commits, the prior valid target remains authoritative. Phase 9 makes no directory-`fsync` or stronger crash-durability claim.

## 10. Fresh builder and compatibility

`fresh_vhe_sidecar(configuration)` is pure. It returns copied configuration lineage and identities, `accepted_source_sequence` copied from configuration watermark, `committed_active_time_ns = 0`, and `fresh_vhe_state()`. It neither authorizes enable/reset nor writes a file. Phase 10 decides when it is used.

The exact pure compatibility vocabulary is `EQUAL`, `SIDECAR_AHEAD`, and `CONFIG_AHEAD`.

`validate_configuration_sidecar_compatibility(configuration, sidecar)` first requires exact equality of configuration schema, stream identity, adapter contract, operator identity, projection identity, modulation schema, modulation mapping, modulation profile schema, theta, and modulation profile ID. Only then it compares `sidecar.accepted_source_sequence` with `configuration.last_accepted_source_sequence`: equal yields `EQUAL`; sidecar greater yields `SIDECAR_AHEAD`; configuration greater yields `CONFIG_AHEAD`.

The helper mutates, repairs, deletes, creates, and authorizes nothing. It ignores lifecycle policy.

## 11. Phase-9 / Phase-10 boundary

Phase 9 owns mechanical DTO, strict validation, canonical serialization, path derivation, load, write, fresh builder, and pure compatibility classification.

Phase 10 owns known-agent proof, `AgentLockManager`, enable, suspend, resume, reset, disable, orphan deletion, watermark repair, recovery decisions, sidecar/config transaction ordering, runtime allocation, and shutdown flush.

Phase 9 must not implement policy for configuration absent plus sidecar present, disabled orphan deletion, missing active/suspended sidecar, watermark repair, configuration-ahead hard failure, replay admission, or lifecycle changes.

## 12. Architectural import boundary

The later Phase-9 implementation may depend narrowly on stdlib, `brainvision.vhe`, `brainvision.clock`, `brainvision.configuration`, `brainvision.character_modulation`, and `torment_service.pathing`.

It must not import `torment_service.fabric`, `torment_service.agent_locks`, memory, kernel, cognition, SRG, Hivermind, model/prompt systems, or acquire locks.

## 13. Frozen implementation test plan

The later bounded Phase-9 suite covers exact top-level/nested field sets; canonical bytes; strict round trip; duplicate-key rejection; FastTrace bounds/canonical inactive form; PersistentContext bounds; R ordering, uniqueness, open-token/null rules, counts, and time ordering; semantic times no later than committed active time; exact active-time and accepted-sequence bounds; lineage/continuation identity copies; theta/profile mismatch rejection; fresh-builder watermark/F/S/R/time behavior; contained non-mutating paths/reads; write refusal for absent Brainvision directory; no agent/config creation; atomic replacement; failed temporary-write preservation; all three compatibility classifications; identity mismatch rejection; compatibility non-mutation; no lifecycle/projection fields; and no Fabric/lock/cognition/memory/kernel imports.

## 14. Claim ceiling

This specification does not establish Phase-10 lifecycle correctness, recovery-orchestration correctness, transaction-order correctness, known-agent locking correctness, direct ingress, sinks, full v1a qualification, or v1b integration.
