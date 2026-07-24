# TORMENT Brainvision — Stage S3B v0.3 Durable-Evidence Implementation Specification v0.1

Status: DRAFT (corrected replacement) for independent (GPT + Codex) review. Docs-only. Creates no authority. Kept outside the repository until its exact bytes are independently accepted. This is a final micro-correction: it adds an explicit durable publication-recovery evidence representation and repairs two malformed taxonomy rows; it does not redesign the architecture or reopen H1–H5.

```text
document_class             = implementation specification (docs-only, corrected replacement)
authority_created          = none
implementation_authorized  = false
execution_authorized       = false
manifest_contact           = none
publication_authorized     = false
publication_recovery_authorized = false
durability_reconfirmation_authorized = false
scientific_reconstruction  = none
retained_evidence_modified = none
git_mutations              = none
saved_into_docs            = false (delivered outside the repository)
```

Scientific claim boundary (preserved exactly, never crossed):

```text
two complete v0.2 scientific passes occurred
the two canonical pass bundles were byte-identical
the unpublished v0.2 result kind is not durably available
the v0.2 result must not be reconstructed; this document does not imply SYNTHETIC_GATE_PASSED or SYNTHETIC_GATE_FAILED for v0.2
```

---

## 1. Status, authority, and scope

This corrected replacement resolves exactly the two remaining Codex findings while preserving every previously accepted mechanism (§5): (1) a missing durable publication-recovery authorization representation is added as a distinct immutable publication-recovery evidence chain (Model A; §6/§7/§8/§13/§19/§22/§25); (2) the malformed `PUBLICATION_STAGING_INCOMPLETE` and `PUBLICATION_PROMOTION_FAILED` taxonomy rows are repaired to the canonical nine-column structure, and the entire taxonomy is validated to nine cells per row (§25). It authorizes nothing.

---

## 2. Bound baseline and governing documents

```text
repository = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
branch     = main
HEAD       = origin/main = f1dfa30eab6678c6390575f644a29f3d152d27bf   (confirmed read-only; working tree clean)
```

Bound governing documents (committed at HEAD; consistent with this document):

```text
Architecture Review v0.1 : git blob 8dd09ffc7be8e7a2b44fafaa3acf52ada858053a ; SHA-256 18aaa3732c24702df372c41ef747c2d326d949b5317902677cf84bc2fcf23d48 ; bytes 51551
Architecture Decision Record v0.1 (H1–H5 binding) : git blob fd2f5ade108f196c8caaf8fa4a2d8df50db2190b ; SHA-256 2b4e31e590cfb9a2b0228b865ebd43eb7c53a454420d29e21782a388d0900922 ; bytes 16565
```

Prior specification under correction: `..._IMPLEMENTATION_SPECIFICATION_v0.1_3.md`, 68365 bytes, SHA-256 `6d1cb14e…`, CR 0, LF 694, terminal LF. Codex disposition: C — REQUIRE DOCS-ONLY CORRECTION (two blocking defects only). Retained v0.2 forensic evidence remains immutable (`current_state.json` 144B `63bd8dbe…`), read-only, never reused/mutated.

---

## 3. Binding architecture decisions (H1–H5)

```text
H1  PUBLICATION_IS_PROJECTION = true. Publication does not create, change, complete, repair, or authorize scientific truth.
H2  AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT = verified IMMUTABLE_SCIENTIFIC_BUNDLE + valid linked SCIENTIFIC_COMPLETION record.
    bundle without valid receipt = ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE ; receipt without valid bundle = INVALID_SCIENTIFIC_COMPLETION.
H3  Observer/evidence boundary reached only when the pair is durable, byte-verified, hash-verified, identity-bound, mutually linked,
    and in the accepted scientific chain. Engineering terminology only.
H4  Publication recovery = separately authorized, structurally publication-only, non-automatic; incapable of scientific execution/reinterpretation.
H5  Primary/emergency contradiction = CONTRADICTORY_EVIDENCE: no verdict assertion, no publication, no auto-reconciliation,
    no scientific execution recovery, no retry, no repair/deletion; operator forensic review required.
```

---

## 4. Protocol topology and trust boundaries

Separate capabilities (A–L). "Man?/Sci?/Pub?" are hard structural capabilities MUST be false where marked N. Component J is subdivided into J1 (publication projector) and J2 (publication-recovery verifier), each with separate import and write boundaries. J1 writes only to publication-projection chains and publication paths; J2 writes only to publication-recovery chains and never to the scientific chain, the publication-projection chain, or publication artifacts.

| Cmp | Responsibility | Permitted imports | Prohibited imports | Writes to | Man? | Sci? | Pub? |
|---|---|---|---|---|---|---|---|
| A pre-contact authorization validator | validate repo/identity/authorization | schema, stdlib | descriptor, manifest reader | none | N | N | N |
| B authority-consumption writer | write+verify AUTHORITY_CONSUMED | writer C, schema | descriptor, manifest reader | scientific chain | N | N | N |
| C immutable stored-object writer | write+verify one stored object | schema, windows adapter | descriptor, manifest reader, publisher | scientific chain / bundle dir | N | N | N |
| D scientific-chain validator / replay | derive accepted scientific chain | schema | descriptor, manifest reader | none | N | N | N |
| E manifest-contact accounting wrapper | attempt→one read→success | writer C, schema | descriptor | scientific chain | Y (read, capped) | N | N |
| F scientific bundle constructor | run science, build pass bundle | descriptor, schema | publisher | none | via E | Y | N |
| G immutable bundle writer/verifier | write+verify content-addressed bundle | writer C, windows adapter | descriptor | bundle dir | N | N | N |
| H SCIENTIFIC_COMPLETION writer/verifier | write+verify receipt referencing bundle | writer C, schema | descriptor, manifest reader | scientific chain | N | N | N |
| I emergency capsule writer | bounded EMERGENCY_OBSERVED_UNCOMMITTED capsule | stdlib minimal serializer | primary serializer, descriptor | emergency dir | N | N | N |
| J1 publication projector | project verified bundle; publication-projection chain | schema, pub-projection-authorization validator, promotion adapter | descriptor, manifest reader, F, G, J2 | publication-projection chain + pub paths ONLY | N | N | Y (projection) |
| J2 publication-recovery verifier | verify already-final artifacts; publication-recovery chain | schema, pub-recovery-authorization validator, replay | descriptor, manifest reader, F, G, promotion adapter, J1 artifact generators | publication-recovery chain ONLY | N | N | Y (evidence-only) |
| K terminal classifier | assign terminal classifications (all chains) | schema | descriptor, manifest reader | scientific / publication / recovery chains | N | N | N |
| L fault-injection seam (test only) | inject deterministic faults | test harness | production entry points | test dirs | N | N | N |

Only F runs science; only J1 projects; J2 performs evidence-only verification and cannot generate, promote, or mutate artifacts. Neither J1 nor J2 may import science/manifest surfaces (enforced transitively, §22).

---

## 5. Preserved accepted decisions

Unchanged; must not regress: nonce-free logical records; nonce-bearing immutable storage instances; logical content identity separated from write-attempt identity; same logical hash = redundant storage instances; different logical hash at one sequence/predecessor = fork; bundle-payload identity separated from stored-bundle identity; scientific chain separated from publication chains; `publication_chain_identity` unique per projection authorization; publication authorization consumed when the invocation begins; publication-authority `ATTEMPT_FAILED`/`INDETERMINATE` states; scientific terminal status not required for publication eligibility; exact publication operation order; no artifact before durable authority and `PUBLICATION_ATTEMPTED` records; same-volume no-replace directory promotion; staging/final collisions and promotion ambiguity fail closed; publication failure never weakens authoritative scientific truth; ASCII-only canonicalization; strict duplicate-key rejection; strict int-not-bool; null/float rejection before bundle creation; durability-reconfirmation authorization; emergency pre-open semantics; complete publication artifact recipes; fully recomputable numerical examples; the Windows durability and promotion blockers; the non-authorizations; and the v0.2 scientific-claim boundary.

---

## 6. Identity model

All identities are concrete engineering values (SHA-256, lowercase hex, 64 chars unless noted). No metaphysical/quantum/observer identity. Constants: protocol_identity `"torment-brainvision-durable-evidence-v0.3"`; schema identities `"scientific-logical-record-v0.3"`, `"publication-logical-record-v0.3"`, `"publication-recovery-logical-record-v0.3"`, `"stored-record-object-v0.3"`, `"immutable-scientific-bundle-v0.3"`, `"stored-bundle-object-v0.3"`, `"scientific-completion-receipt-v0.3"`, `"publication-projection-recipe-v0.3"`.

| Identity | Derivation | Deterministic? | Authoritative? |
|---|---|---|---|
| execution_identity | sha256(canonical of: protocol_identity, scientific_execution_authorization_identity, repo HEAD, runner/test/schema git_blob+raw_sha256, configuration_identity, manifest_external+payload sha256, python_version) | yes | yes |
| scientific_execution_authorization_identity | committed one-run scientific-execution authorization's later_execution_authorization_identity | yes | yes |
| configuration_identity / manifest identities | frozen constants | yes | yes |
| logical_record_sha256 | sha256(canonical logical-record preimage minus logical_record_sha256) — nonce-free | yes | yes (chain link) |
| stored_object_sha256 | sha256(canonical stored-object preimage minus stored_object_sha256) — includes nonce | yes given nonce | forensic |
| bundle_payload_sha256 | sha256(canonical bundle payload preimage minus bundle_payload_sha256) — nonce-free | yes | yes (scientific identity) |
| stored_bundle_object_sha256 | sha256(canonical stored bundle-object preimage) — includes nonce | yes given nonce | forensic |
| writer_identity / writer_attempt_identity | fixed name / random 128-bit 32-hex nonce | yes / NO | diagnostic |
| publication_projection_identity | sha256(canonical of: execution_identity, bundle_payload_sha256, scientific_completion_logical_record_sha256, publication_recipe_identity, publication_utility_identities) | yes | binds projection; NOT authority |
| publication_projection_authorization_identity | §23 (commitment to a committed human-approved publication-projection authorization document) | yes | yes (human authority) |
| publication_chain_identity | sha256(canonical of {publication_projection_identity, publication_projection_authorization_identity}) (fixed key order) | yes | yes (unique per projection authorization) |
| **publication_recovery_authorization_identity** | §13 (commitment to a committed human-approved publication-recovery authorization document) | yes | yes (human authority) |
| **publication_recovery_chain_identity** | `sha256(canonical of {original_publication_chain_identity, publication_recovery_authorization_identity})` (fixed key order) | yes | yes (unique per recovery authorization) |

Scientific identity depends only on nonce-free hashes; the `writer_attempt_identity` nonce never enters any chain link, scientific identity, or canonical scientific output. Two separate recovery authorizations for the same original publication chain produce distinct `publication_recovery_chain_identity` values.

---

## 7. Canonical serialization

Inherited verbatim from the accepted v0.2 discipline:

```python
canonical_json_bytes(value) = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
sha256_hex(payload)         = hashlib.sha256(payload).hexdigest()   # lowercase 64-hex
```

Rules: ASCII-only (code points U+0020..U+007E; non-ASCII rejected before serialization; `ensure_ascii=True` as defense in depth; the emergency truncation marker is the three-ASCII-period `...<TRUNCATED n>`); duplicate-key rejection via `json.loads(..., object_pairs_hook=<reject-duplicates>)`; UTF-8; BOM prohibited; CR prohibited; one terminal 0x0A; insertion-order keys (each schema fixes an exact order); strict int-not-bool (`type(x) is int and not bool`); floats prohibited in evidence metadata and accepted bundle payload; null prohibited; NaN/Infinity prohibited; max nesting depth 32; max object/array member count 4096 per container; max stored-record-object 65536 bytes; max stored-bundle-object 4194304 bytes. Preimage rule: each self-hash is computed over the canonical bytes with that self-hash key removed. Byte-length semantics: lengths are of the COMPLETE canonical object INCLUDING its self-hash; preimages omit it.

Fully recomputable example — scientific logical record (Codex-verified; nonce-free). Preimage (without `logical_record_sha256`), canonical bytes = 516, CR = 0, LF = 1, terminal LF = true:

```text
{"protocol_identity":"torment-brainvision-durable-evidence-v0.3","record_schema_identity":"scientific-logical-record-v0.3","record_kind":"MANIFEST_CONTACT_ATTEMPT","sequence_number":2,"execution_identity":"a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00","scientific_execution_authorization_identity":"715e24b1abb80ed04bbcff57ad4d0a8e33096f31af1093a7d1d3858b69f5f7af","predecessor_logical_record_sha256":"9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08","payload":{"pass_index":1}}
```

```text
logical_record_sha256 = 4d5cfc3607c466bbc025f81437e9aeb0d0863bdfc0d0a9968b6e336a79ddc81e
```

Fully recomputable stored-object example — complete canonical preimage (excluding only `stored_object_sha256`) as one exact ASCII line, byte length = 889, CR = 0, LF = 1, terminal LF = true:

```text
{"storage_schema_identity":"stored-record-object-v0.3","logical_record_sha256":"4d5cfc3607c466bbc025f81437e9aeb0d0863bdfc0d0a9968b6e336a79ddc81e","writer_identity":"durable_evidence_primary_writer_v0_3","writer_attempt_identity":"3f2a1c9e77b4402db8e6a15c0d99e412","logical_record":{"protocol_identity":"torment-brainvision-durable-evidence-v0.3","record_schema_identity":"scientific-logical-record-v0.3","record_kind":"MANIFEST_CONTACT_ATTEMPT","sequence_number":2,"execution_identity":"a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00","scientific_execution_authorization_identity":"715e24b1abb80ed04bbcff57ad4d0a8e33096f31af1093a7d1d3858b69f5f7af","predecessor_logical_record_sha256":"9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08","payload":{"pass_index":1},"logical_record_sha256":"4d5cfc3607c466bbc025f81437e9aeb0d0863bdfc0d0a9968b6e336a79ddc81e"}}
```

```text
stored_object_sha256 = d92660f650611d7f2301d43ea0e92183614c7501a99d2e8690c297dbc75d74ee
```

Fully recomputable `publication_chain_identity` examples. Preimage key order: `{"publication_projection_identity":"<64hex>","publication_projection_authorization_identity":"<64hex>"}`:

```text
Example A (canonical bytes = 218, CR = 0, LF = 1, terminal LF = true):
{"publication_projection_identity":"1111111111111111111111111111111111111111111111111111111111111111","publication_projection_authorization_identity":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
publication_chain_identity = 903217783c511519cbccd0234dfae5a6d5920ee51895f4b72c915b74f8b7edb7

Example B (canonical bytes = 218, CR = 0, LF = 1, terminal LF = true):
{"publication_projection_identity":"1111111111111111111111111111111111111111111111111111111111111111","publication_projection_authorization_identity":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}
publication_chain_identity = 88ccee0708459c5122f3f33af22b817a7c9188f6d12cacb6e04a74bf44a99f79
```

Fully recomputable `publication_recovery_chain_identity` example. Preimage key order: `{"original_publication_chain_identity":"<64hex>","publication_recovery_authorization_identity":"<64hex>"}`, using original chain = Example A above and a recovery authorization = `c`×64 (canonical bytes = 220, CR = 0, LF = 1, terminal LF = true):

```text
{"original_publication_chain_identity":"903217783c511519cbccd0234dfae5a6d5920ee51895f4b72c915b74f8b7edb7","publication_recovery_authorization_identity":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"}
publication_recovery_chain_identity = fc05a6671e60a3d095afd473a5ed58a5a6b616dd1bdb4beb5aeba8da7379e7ce
```

A second recovery authorization (`d`×64) for the same original chain yields a distinct `publication_recovery_chain_identity = 28ddd3908c4bc90ac7d31fc54f21503696be0213f160da2ee97bdea7d6bd29bb`. A conforming implementation MUST unit-test all of the above exact values.

---

## 8. Logical record schemas

Three nonce-free variants share a common canonical envelope but have unambiguous authorization fields and record-kind vocabularies.

Scientific logical record (`scientific-logical-record-v0.3`), fixed key order: `protocol_identity ; record_schema_identity ; record_kind(∈ §10) ; sequence_number ; execution_identity ; scientific_execution_authorization_identity ; predecessor_logical_record_sha256 ; payload ; logical_record_sha256`.

Publication logical record (`publication-logical-record-v0.3`), fixed key order: `protocol_identity ; record_schema_identity ; record_kind(∈ §11) ; sequence_number ; execution_identity ; publication_projection_authorization_identity ; publication_chain_identity ; predecessor_logical_record_sha256 ; payload ; logical_record_sha256`.

Publication-recovery logical record (`publication-recovery-logical-record-v0.3`), fixed key order: `protocol_identity ; record_schema_identity ; record_kind(∈ §13) ; sequence_number ; execution_identity ; publication_recovery_authorization_identity ; publication_recovery_chain_identity ; predecessor_logical_record_sha256 ; payload ; logical_record_sha256`.

The recovery variant does NOT use `publication_projection_authorization_identity` as its authority field; the durable authority for recovery is exclusively `publication_recovery_authorization_identity`. Its payload MAY reference the original projection identities, but never as its authority. No variant contains `writer_attempt_identity`, storage-object identity, filesystem path, wall-clock timestamp, or nonce; the generic name `authorization_identity` is used in no record. All three persist through the existing nonce-bearing `stored-record-object-v0.3` envelope (§9); recovery logical identity remains nonce-free. The chain links only `predecessor_logical_record_sha256 → logical_record_sha256`. Cross-identity rejection (§19) checks the variant-appropriate authorization field.

---

## 9. Stored-object instance schema

Each logical record is persisted as one or more stored-object instances (`stored-record-object-v0.3`), fixed key order: `storage_schema_identity ; logical_record_sha256 ; writer_identity ; writer_attempt_identity ; stored_object_sha256 ; logical_record`. Semantics: same `logical_record_sha256` + different `writer_attempt_identity` = REDUNDANT instances (flag; accept one; retain all); different `logical_record_sha256` at the same sequence & predecessor = `SAME_SEQUENCE_FORK` (fail closed). Bundles use the analogous `stored-bundle-object-v0.3` envelope (§16).

---

## 10. Scientific evidence chain: record kinds and transitions

Immutable; closed after `SCIENTIFIC_TERMINAL_STATUS`; never reopened; never extended by a publication or recovery process; source of scientific truth.

| record_kind | payload | multiplicity | predecessor | permits next |
|---|---|---|---|---|
| AUTHORITY_CONSUMED | {} | exactly 1, seq 0, genesis | genesis sentinel | manifest contact |
| MANIFEST_CONTACT_ATTEMPT | {pass_index:1..2} | ≤ 2 | AUTHORITY_CONSUMED or MANIFEST_READ_SUCCESS | one read for that pass |
| MANIFEST_READ_SUCCESS | {pass_index:1..2} | ≤ 2 | MANIFEST_CONTACT_ATTEMPT(same pass) | next pass or completion |
| SCIENTIFIC_COMPLETION | receipt (§17) | exactly 1 | MANIFEST_READ_SUCCESS(pass 2) | scientific terminal |
| SCIENTIFIC_TERMINAL_STATUS | {terminal_classification, exit_code} | ≤ 1 (closes chain) | any scientific record | none |

The authoritative result is the verified bundle + valid `SCIENTIFIC_COMPLETION`. `SCIENTIFIC_TERMINAL_STATUS` is NOT required for authoritative-result recognition, publication eligibility, publication authorization, publication-chain genesis, or publication recovery. No transition permits scientific execution to resume after `AUTHORITY_CONSUMED`.

---

## 11. Publication evidence chains: identity, anchor, publication-authority states

Publication-projection evidence lives in separate immutable chains, one per projection authorization, in `publication_chain/<publication_chain_identity>/`. Anchor (genesis payload; does NOT require scientific terminal status): `execution_identity ; scientific_execution_authorization_identity ; bundle_payload_sha256 ; scientific_completion_logical_record_sha256 ; publication_projection_authorization_identity ; publication_projection_identity ; publication_chain_identity ; scientific_chain_terminal_logical_record_sha256 (OPTIONAL corroborating metadata; never required)`.

Record kinds (each a `publication-logical-record-v0.3`): `PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED` (exactly 1, genesis); `PUBLICATION_ATTEMPTED` (exactly 1 per chain); `PUBLICATION_COMPLETED` (≤1); `PUBLICATION_TERMINAL_STATUS` (≤1, closes chain).

Publication-authority states. `PUBLICATION_AUTHORITY_NOT_ATTEMPTED` is a live process state only (before the operator begins the authorized publication invocation). Recovered durable machine states: `PUBLICATION_AUTHORITY_CONSUMED` (a valid durable `PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED` genesis exists); `PUBLICATION_AUTHORITY_CONSUMPTION_ATTEMPT_FAILED` (attempt began; caught failure/debris proves the genesis could not become valid+durable); `PUBLICATION_AUTHORITY_ATTEMPT_STATE_INDETERMINATE` (cannot distinguish never-started from started-then-died). Consumption point: the authorization is consumed for reuse-policy purposes when the manually authorized publication invocation begins — immediately after authorization + scientific-anchor validation and immediately before any publication-chain/output mutation — regardless of whether a durable genesis is created. Both FAILED and INDETERMINATE prohibit automatic reuse/retry/output/evidence-completion; require a new publication-projection authorization; require operator review; leave the scientific result unchanged and scientific execution closed. Repository absence after the window never proves NOT_ATTEMPTED; external transcripts are forensic, outside the chain, and never repair missing chain evidence. Multiplicity: multiple separately authorized projections may exist, each its own chain, distinct `publication_chain_identity` (no collision); re-projection only under a new explicit authorization; no automatic re-projection.

---

## 12. Publication operation order, promotion, directory collisions, crash states

Exact publication operation order (Component J1):

```text
1 validate the committed publication-projection authorization ; 2 validate the authoritative bundle + SCIENTIFIC_COMPLETION anchor ;
3 derive+validate publication_projection_identity ; 4 derive+validate publication_chain_identity ;
5 begin the one authorized publication invocation  ← authorization CONSUMED for reuse-policy from here (regardless of genesis outcome) ;
6 durably commit PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED ; 7 durably commit exactly one PUBLICATION_ATTEMPTED ;
8 exclusively create the chain-specific staging directory ; 9 write all three staging artifacts using exclusive creation ;
10 flush/fsync each ; 11 read back and byte/hash verify each ; 12 synchronize/confirm the staging directory entry ;
13 promote the complete verified staging directory to the chain-specific final directory using the exact no-replace promotion operation ;
14 reopen all final artifacts and byte/hash verify them ; 15 durably commit PUBLICATION_COMPLETED with exact names+hashes ; 16 optionally commit PUBLICATION_TERMINAL_STATUS
```

No artifact may be generated before `PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED` and `PUBLICATION_ATTEMPTED` are durable.

No-replace promotion primitive (validated adapter, §21): `promote_verified_directory_no_replace(staging_dir, final_dir) -> PROMOTED | failure_class`. Preconditions: both under the expected roots and bound to the same `publication_chain_identity`; staging contains exactly the three artifact filenames; all three already byte/hash verified; final_dir does not exist; same volume. Operation: no-replace directory rename/move (no per-file copy; no merge; no overwrite; no deletion); post-rename directory-entry sync; reopen+verify finals. Fail-closed: if no validated same-volume no-replace primitive exists, finalization FAILS CLOSED — staging retained, no `PUBLICATION_COMPLETED`.

Directory collisions: staging already exists = `PUBLICATION_STAGING_DIRECTORY_COLLISION` (no reuse/overwrite/merge/delete; no artifacts; authorization remains consumed; new authorization required); final already exists pre-promotion = `PUBLICATION_FINAL_DIRECTORY_COLLISION` (no overwrite/merge/replace/delete; fail closed; consumed; forensic review); path/chain/authorization/projection identity mismatch = `PUBLICATION_CHAIN_IDENTITY_COLLISION` (no cross-chain directory reuse). Crash/ambiguity states: `PUBLICATION_STAGING_INCOMPLETE`; `PUBLICATION_PROMOTION_FAILED`; `PUBLICATION_PROMOTION_OUTCOME_INDETERMINATE`; `PUBLICATION_PROMOTION_AMBIGUOUS` (both dirs retained byte-for-byte, no auto-winner); `PUBLICATION_FINAL_DIRECTORY_INVALID`; `PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED` — all fail closed, never auto-complete or auto-repair; each requires the appropriate new authorization (§25). Recovery of any of these evidence states is handled exclusively by the publication-recovery evidence chain (§13).

---

## 13. Publication-recovery evidence chain (Model A)

A publication-recovery operation is evidence-completion only and MUST NEVER append to, reopen, reinterpret, or mutate the original consumed publication-projection chain. Recovery activity is recorded in a distinct immutable publication-recovery evidence chain under its own namespace (§14 directory layout): `.iososv_v0_3.publication_recovery_chain/<publication_recovery_chain_identity>/`. The original publication chain remains at `.iososv_v0_3.publication_chain/<publication_chain_identity>/` and is read-only to recovery.

Publication-recovery authorization identity (§6) is a commitment to an actual committed, human-approved publication-recovery authorization document, binding at minimum: authorization document path; dedicated authorization commit; authorization Git blob; authorization raw SHA-256; canonical authorization payload; explicit human authority statement; `execution_identity`; `scientific_execution_authorization_identity`; `bundle_payload_sha256`; `scientific_completion_logical_record_sha256`; original `publication_projection_authorization_identity`; original `publication_projection_identity`; original `publication_chain_identity`; exact final artifact filenames; exact expected final artifact SHA-256 values; publication-recovery utility Git blob; publication-recovery utility raw SHA-256; publication-recovery schema identity; permitted recovery directories; permitted record kinds; one-attempt semantics. The actual authorization document is a future docs-only task, neither drafted nor authorized here.

Publication-recovery chain identity (§6/§7): `publication_recovery_chain_identity = sha256(canonical of {original_publication_chain_identity, publication_recovery_authorization_identity})`. The recovery-chain directory is keyed by `publication_recovery_chain_identity`.

Recovery-chain genesis anchor binds exactly: `execution_identity ; scientific_execution_authorization_identity ; bundle_payload_sha256 ; scientific_completion_logical_record_sha256 ; original_publication_projection_authorization_identity ; original_publication_projection_identity ; original_publication_chain_identity ; publication_recovery_authorization_identity ; publication_recovery_chain_identity ; expected_final_artifacts { iososv_v0_3_result.json SHA-256, iososv_v0_3_execution_envelope.json SHA-256, iososv_v0_3_summary.txt SHA-256 } ; final_publication_directory ; publication_recovery_utility_identity`. The recovery chain never changes any scientific identity or result kind.

Recovery record kinds (each a `publication-recovery-logical-record-v0.3`) and transitions:

```text
PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED (exactly 1, genesis)
→ PUBLICATION_RECOVERY_ATTEMPTED (exactly 1)
→ PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED (≤ 1)
→ PUBLICATION_RECOVERY_EVIDENCE_COMPLETED (≤ 1)
→ PUBLICATION_RECOVERY_TERMINAL_STATUS (≤ 1, closes chain)
```

One recovery authorization permits exactly one manually initiated recovery invocation; no automatic retry.

Recovery capability boundary. The recovery utility (J2) MAY only: read the original publication chain; read the original staging directory; read the original final publication directory; read the authoritative bundle and `SCIENTIFIC_COMPLETION` anchor; validate exact artifact filenames; validate exact artifact bytes; validate exact artifact SHA-256 values; classify the original publication state; write only to the new publication-recovery evidence chain. It MAY NOT: write or append to the original publication-projection chain; rewrite original publication records; generate or regenerate publication artifacts; promote staging to final; rename or copy publication directories; overwrite final artifacts; delete or repair evidence; execute descriptors; contact the manifest; construct a scientific result; construct a bundle; construct `SCIENTIFIC_COMPLETION`; open scientific authority; perform scientific execution. If final artifacts are absent, incomplete, malformed, or hash-invalid, `PUBLICATION_RECOVERY_EVIDENCE_COMPLETED` MUST NOT be written; a new publication-projection authorization and a new publication chain are required for any regeneration or re-promotion.

Recovery authority consumption states. Live: `PUBLICATION_RECOVERY_AUTHORITY_NOT_ATTEMPTED` (before the authorized recovery invocation begins). Recovered: `PUBLICATION_RECOVERY_AUTHORITY_CONSUMED`; `PUBLICATION_RECOVERY_AUTHORITY_CONSUMPTION_ATTEMPT_FAILED`; `PUBLICATION_RECOVERY_AUTHORITY_ATTEMPT_STATE_INDETERMINATE`. Consumption point: consumed for reuse-policy when the manually authorized recovery invocation begins — immediately after authorization + anchor validation and immediately before any recovery-chain mutation. Missing genesis evidence after an invocation window fails closed as attempt-failed or indeterminate. Both non-success states prohibit authorization reuse, automatic retry, automatic evidence completion, and publication-artifact mutation, and require a new publication-recovery authorization.

Recovery evidence semantics. `PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED` means: all three expected final artifacts exist; filenames match exactly; bytes match the deterministic publication recipe; SHA-256 values match the original expected values; the final directory identity matches the original `publication_chain_identity`; no artifact was generated, modified, renamed, or repaired by recovery. `PUBLICATION_RECOVERY_EVIDENCE_COMPLETED` means: the recovery chain durably records that already-existing final artifacts were verified under the distinct recovery authorization. It does NOT retroactively claim the original `PUBLICATION_COMPLETED` existed, that the original projection invocation finished normally, or that the original publication chain was complete. The strongest publication fact becomes "final artifacts verified under separately authorized recovery evidence"; the original projection chain remains evidence-incomplete.

Recovery failure classifications: `PUBLICATION_RECOVERY_AUTHORIZATION_VALIDATION_FAILED`; `PUBLICATION_RECOVERY_AUTHORITY_CONSUMPTION_ATTEMPT_FAILED`; `PUBLICATION_RECOVERY_AUTHORITY_ATTEMPT_STATE_INDETERMINATE`; `PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED`; `PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH`; `PUBLICATION_RECOVERY_FINAL_DIRECTORY_MISSING`; `PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID`; `PUBLICATION_RECOVERY_ARTIFACT_HASH_MISMATCH`; `PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED`; `PUBLICATION_RECOVERY_CHAIN_FORK`; `PUBLICATION_RECOVERY_TERMINAL_STATUS_WRITE_FAILED`. For ALL recovery failures: the authoritative scientific result is unchanged; the original publication chain is unchanged; publication artifacts are never regenerated or repaired; automatic retry is prohibited after the recovery invocation begins; forensic evidence is retained. These rows appear with the canonical nine-column structure in §25.

---

## 14. Directory and artifact layout

All v0.3 artifacts live under `research/brainvision/results/`. No mutable current-state pointer. The v0.2 journal is never reused/mutated. Exact basenames:

```text
research/brainvision/results/
  .iososv_v0_3.scientific_chain/                                  # scientific logical-record storage instances (B,C,E,H)
  .iososv_v0_3.scientific_bundles/                                # immutable scientific bundle storage instances (G)
  .iososv_v0_3.emergency/                                         # emergency capsules (I)
  .iososv_v0_3.publication_chain/<publication_chain_identity>/    # one publication-projection chain per projection authorization (J1)
  .iososv_v0_3.publication_staging/<publication_chain_identity>/  # publication staging, transient (J1)
  iososv_v0_3.publication/<publication_chain_identity>/           # final publication output, non-hidden (J1 promotes here)
  .iososv_v0_3.publication_recovery_chain/<publication_recovery_chain_identity>/  # one recovery chain per recovery authorization (J2)
  .iososv_v0_3.faultinjection_fixtures/                          # synthetic fixtures (tests only)
```

`iososv` = independent_order_sensitive_synthetic_validation (fixed exact abbreviation). Filename grammars: scientific/publication/recovery logical-record storage instance = `<record_kind_lower>.<sequence_6digit>.<logical_record_sha256_64hex>.<writer_attempt_32hex>.json`; bundle = `bundle.000000.<bundle_payload_sha256_64hex>.<writer_attempt_32hex>.json`; emergency = `emergency.<writer_attempt_identity_32hex>.cap`. Allowed chars `[a-z0-9_.]`, all lowercase; reserved-name checks; max basename 255 bytes; extended-length `\\?\` paths with length assertion and fail-closed; exclusive create; content-hash + nonce disambiguation prevents NTFS case-aliasing. J2 writes only under `publication_recovery_chain/<recovery chain id>/`.

---

## 15. Authority-consumption protocol (scientific) and manifest-contact accounting

`AUTHORITY_NOT_ATTEMPTED` is live-only. Recovered scientific states: `AUTHORITY_CONSUMED`; `AUTHORITY_CONSUMPTION_ATTEMPT_FAILED`; `AUTHORITY_ATTEMPT_STATE_INDETERMINATE`. Any post-event state not durably proven CONSUMED or ATTEMPT_FAILED is INDETERMINATE and cannot authorize automatic reuse/retry/manifest contact; both non-success states require a new docs-only authorization and operator review. Consumption sequence: A validates pre-contact → B builds the nonce-free `AUTHORITY_CONSUMED` scientific logical record (seq 0, empty payload, genesis) → C writes+verifies a stored-object instance (§18) → CONSUMED only after byte/hash verify and directory-durability CONFIRMED. On caught failure: `AUTHORITY_CONSUMPTION_ATTEMPT_FAILED`; emergency capsule confirming contact did not begin; no contact; no retry.

Manifest-contact accounting: `durably commit MANIFEST_CONTACT_ATTEMPT(pass_index)` BEFORE the read → exactly one read → on success `durably commit MANIFEST_READ_SUCCESS(pass_index)`. Max attempts = 2, max successes = 2, counts by replay (no mutable counter). An ambiguous read never silently licenses an extra protected contact.

---

## 16. Immutable scientific bundle

The bundle stores ONE canonical pass bundle (two passes byte-identical; receipt records `scientific_pass_count = 2`, `two_pass_canonical_identity_status = "identical"`). Bundle payload (`immutable-scientific-bundle-v0.3`), fixed key order: `bundle_schema_identity ; protocol_identity ; execution_identity ; scientific_execution_authorization_identity ; scientific_result_kind (SYNTHETIC_GATE_PASSED | SYNTHETIC_GATE_FAILED) ; pass_bundle_sha256 (sha256_hex(canonical_json_bytes(publication_projection_source.canonical_pass_bundle))) ; two_pass_canonical_identity_status ; configuration_identity ; manifest_identities{manifest_external_sha256,manifest_payload_sha256} ; implementation_identities{runner_identity{source_path,git_blob,raw_sha256}, runner_test_identity{...}, schema_contract_identity{...}} ; descriptor_identity{source_path,git_blob,raw_sha256} ; repository_execution_context{head,branch,python_version} ; publication_projection_source ; bundle_payload_sha256`.

`publication_projection_source` fixed key order: `current_state_snapshot{phase,authority_consumed,contact_armed,manifest_contact_attempt_count,manifest_read_success_count} ; canonical_pass_bundle ; publication_recipe_identity`. `current_state_snapshot`: phase (string "SCIENTIFIC_COMPLETE"); authority_consumed (bool true); contact_armed (bool true); manifest_contact_attempt_count (strict int 2); manifest_read_success_count (strict int 2). `canonical_pass_bundle` (v0.3 defines its own `-v0.3` structure; not byte-identical to v0.2), fixed key order: `schema ("torment-brainvision-synthetic-validation-pass-bundle-v0.3") ; fixed_positive{distinguished:bool} ; controls{malformed_and_degenerate_controls_correct:bool, identity_controls_correct:bool, nuisance_controls_correct:bool, method_b_full_enumeration:bool, sampling_used:bool, malformed_and_degenerate_control_cases:[{case:str,expected_failure_code:str,observed_failure_code:str,observed_failure_stage:str,correct:bool}], identity_control_cases:{raw_identity_behavior:bool,repeat_determinism:bool,independently_allocated_equal_input:bool,affine_identity_behavior:bool,affine_equivalent_behavior:bool,affine_plus_complement_identity_behavior:bool,affine_plus_complement_behavior:bool}, method_b_counts:{rotations:int,affine_transforms:int,affine_plus_complement_transforms:int}, method_b_required_counts:{rotations:int,affine_transforms:int,affine_plus_complement_transforms:int}, method_b_unique_vectors_evaluated:int} ; accepted_family{required_count:int,distinguished_count:int,results:[{family_index:int,seed_order_position:int,pair_duplicate_key:str,distinguished:bool}]} ; scientific_result_kind`.

Null/float/malformed rejection (before bundle construction): null prohibited, float prohibited, bool/int/string enforced. v0.2 malformed-control paths MAY produce `None`; v0.3 rejects any such null before creating a bundle, yielding CONTROLLED invalidity (`SYNTHETIC_GATE_INVALID`, separate from the two result kinds) — no bundle and no `SCIENTIFIC_COMPLETION`. Bundle storage (`stored-bundle-object-v0.3`), fixed key order: `storage_schema_identity ; bundle_payload_sha256 ; bundle_payload_byte_length ; writer_identity ; writer_attempt_identity ; stored_bundle_object_sha256 ; bundle_payload`. Scientific identity = `bundle_payload_sha256`; forensic = `stored_bundle_object_sha256`. Orphan = `ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE`; torn/invalid = debris. Result-kind cross-validation (any mismatch fails closed): identical across bundle payload, `canonical_pass_bundle.scientific_result_kind`, the receipt, and the projected result artifact.

---

## 17. SCIENTIFIC_COMPLETION receipt

Carried as the `payload` of the `SCIENTIFIC_COMPLETION` scientific logical record. Fixed key order: `scientific_result_kind ; bundle_payload_sha256 ; bundle_payload_byte_length (len of canonical bundle payload INCLUDING bundle_payload_sha256) ; bundle_schema_identity ; accepted_stored_bundle_object_sha256 (optional, forensic) ; scientific_pass_count (2) ; two_pass_canonical_identity_status ("identical") ; authority_consumed_status ("AUTHORITY_CONSUMED") ; manifest_contact_attempt_count (2) ; manifest_read_success_count (2) ; implementation_identities ; configuration_identity ; manifest_identities ; execution_identity ; scientific_execution_authorization_identity ; protocol_identity ; completion_validity ("VALID")`. Validations before entering the chain: a stored bundle object exists with matching `bundle_payload_sha256` and validates; canonical bundle bytes read back exactly; full canonical byte length (INCLUDING `bundle_payload_sha256`) matches `bundle_payload_byte_length`; result kind matches; the receipt is schema/canonical/self-hash valid and ASCII-only; shares the bundle's `execution_identity`+`scientific_execution_authorization_identity`; extends the valid chain (predecessor MANIFEST_READ_SUCCESS pass 2); no contradictory evidence. `receipt without valid matching bundle = INVALID_SCIENTIFIC_COMPLETION`; `valid verified bundle + valid linked receipt = AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT`.

---

## 18. Immutable-object writer, durability states, and reconfirmation

Writer (no mutable pointer): build nonce-free logical record/bundle payload; compute content hash (preimage); embed in the stored-object envelope with a fresh nonce; compute `stored_object_sha256`; filename per §14; `durably_create_and_verify_file` (§21): exclusive create → write → flush → fsync → close → reopen → read-back byte-compare → recompute stored/logical/payload hashes → `durably_sync_directory_entry`. On caught failure: classify (§25); attempt emergency capsule (§20); never repair/overwrite/rename. Durability states: `BYTE_VALID_DURABILITY_UNCONFIRMED` (non-authoritative); `DURABILITY_RECONFIRMED` (at a later replay the validated primitive successfully synced+confirmed the containing directory entry — acceptance from that replay point FORWARD; does not prove earlier-execution durability); `DURABLE_ACCEPTED` (bytes/hashes valid AND CONFIRMED at write OR RECONFIRMED at replay). Reconfirmation rewrites/renames/repairs nothing; adapter unavailable/UNCONFIRMED ⇒ non-authoritative, fail closed. Promotion of a previously non-authoritative bundle/receipt pair to authoritative requires a separate docs-only durability-reconfirmation authorization (minimum binding: authorization document path, dedicated commit, Git blob, raw SHA-256, canonical payload, explicit human authority statement, `execution_identity`, `bundle_payload_sha256`, `scientific_completion_logical_record_sha256`, reconfirmation-utility Git blob+raw SHA-256, permitted directories read+directory-sync only); it permits no manifest contact, descriptor execution, result reconstruction, or publication.

---

## 19. Replay and accepted-chain derivation

Deterministic replay is a pure function of on-disk objects, run separately for the scientific chain, each publication-projection chain (keyed by `publication_chain_identity`), and each publication-recovery chain (keyed by `publication_recovery_chain_identity`):

```text
1 discovery → 2 filename validation → 3 byte loading (limits) → 4 schema validation (variant-appropriate) →
5 canonical reserialization (byte-equality; else debris) → 6 self-hash verification (stored + logical/payload) →
7 identity filtering (protocol/execution + variant authorization field; else REPLAY_IDENTITY_MISMATCH) →
8 durability evaluation (§18) → 9 genesis selection → 10 predecessor validation → 11 sequence validation →
12 kind-transition validation → 13 duplicate handling (same logical hash → redundant) →
14 fork detection (diff logical hash, same seq/predecessor → SAME_SEQUENCE_FORK / PUBLICATION_RECOVERY_CHAIN_FORK) →
15 longest-valid-prefix → 16 bundle linkage (scientific) → 17 contradiction check → 18 terminal classification (§25)
```

Publication-recovery replay additionally verifies: the publication-recovery logical-record schema; `publication_recovery_authorization_identity`; `publication_recovery_chain_identity`; the original `publication_chain_identity` (via the genesis anchor); the expected final artifact hashes; sequence/predecessor links; record-kind transitions; duplicates/forks; durability. A recovery record whose `original_publication_chain_identity` does not match the referenced chain = `PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH` (fail closed). Fail-closed rules (all chains): zero valid successors = stop; one = accept; redundant (same logical hash) = flag/accept one/retain all; diff logical hash at same seq/predecessor = fork; broken predecessor = BROKEN_LINK; sequence gap = SEQUENCE_GAP; cross exec/auth/protocol = REPLAY_IDENTITY_MISMATCH; durability-unconfirmed & unreconfirmable = non-authoritative; primary vs emergency contradiction = CONTRADICTORY_EVIDENCE. No operator-selected fork winner may silently restore a result; all conflicting objects retained byte-for-byte.

---

## 20. Emergency capsule

Independent bounded channel (Component I); distinct serializer and code path. Format: fixed bounded canonical capsule; extension .cap; UTF-8 ASCII-only; one 0x0A terminal; max 4096 bytes; exception-message budget 512 bytes (strip control/non-ASCII; truncate on a byte boundary; append the ASCII marker `...<TRUNCATED n>`; record original length). Filename `emergency.<writer_attempt_identity_32hex>.cap` (no mutable sequence/counter/scan). Pre-open discipline: the capsule file is exclusively created (CREATE_NEW) and its descriptor pre-opened BEFORE authority consumption; any bounded nonce-collision handling occurs DURING pre-open (on collision, new nonce + ONE bounded additional create attempt; a second collision at pre-open ⇒ the emergency channel is unavailable for this run, recorded, later failures degrade to stderr); NO collision handling during later exception handling. Write discipline: at failure time, a single append to the already-open descriptor (no create, no nonce handling); flush+fsync; durability bounded by the survivability table. Fields: protocol_identity; execution_identity; scientific_execution_authorization_identity; authority_state (a §15 recovered state); last_valid_scientific_logical_record_sequence; last_valid_scientific_logical_record_sha256; manifest_contact_attempt_count; manifest_read_success_count; scientific_result_kind_observed_in_memory; canonical_bundle_payload_sha256_observed_in_memory; canonical_bundle_payload_byte_length_observed_in_memory; two_pass_identity_observed; immutable_bundle_primary_commit_confirmed; primary_scientific_completion_committed; failing_operation; exception_type; bounded_exception_message; original_exception_message_length; exit_code. The `..._observed...` fields are `EMERGENCY_OBSERVED_UNCOMMITTED`: never authoritative; never permit publication/execution recovery. Survivability: caught exception / controlled termination = CAN write; forced kill / interpreter crash / host crash / volume failure / power loss = CANNOT be assumed. Independence: code-path/serializer/directory/file-handle YES; filesystem/volume/host/power-loss NO.

---

## 21. Windows durability and no-replace promotion adapter boundary

Narrow abstractions isolating platform durability, quarantined under `research/brainvision/`: `durably_create_and_verify_file(abs_path_extended, canonical_bytes) -> DURABLE | PRIMARY_RECORD_WRITE_FAILED | PRIMARY_RECORD_READBACK_MISMATCH`; `durably_sync_directory_entry(abs_dir_extended) -> CONFIRMED | UNCONFIRMED` (UNCONFIRMED → PRIMARY_RECORD_DURABILITY_UNCONFIRMED and the §18 states, fail closed); `promote_verified_directory_no_replace(staging_dir, final_dir) -> PROMOTED | failure_class` (§12; same-volume, no-replace rename/move; no copy/merge/overwrite; post-rename directory-entry sync; reopen+verify). Python stdlib provides exclusive create/write/flush/`os.fsync`(file)/read-back/rename; Win32-specific/uncertain: durable directory-entry sync on NTFS, extended-length paths, and same-volume no-replace atomic directory promotion. A future implementation MAY begin with fail-closed adapter interfaces and stubs returning `UNCONFIRMED`/not-implemented, platform-neutral tests, and synthetic-only infrastructure tests. It MUST NOT assert durable acceptance, promote publications, authorize protected manifest contact, perform authoritative execution, or publish an authoritative result until the durability primitive AND the no-replace promotion primitive are validated on the authoritative Windows/NTFS environment. No unestablished guarantee is fabricated.

---

## 22. Publication-only processes and transitive source-boundary enforcement

Component J1 (projector) executes the §12 order. Component J2 (recovery verifier) executes the §13 recovery flow — evidence-only, no artifact generation/promotion/mutation. Both MUST be structurally unable to: import scientific descriptors, import the manifest reader, load fixtures for recomputation, change scientific configuration, construct a result kind, create a scientific bundle, or create a `SCIENTIFIC_COMPLETION` record. J2 additionally MUST be unable to: import artifact generators, the promotion adapter, or J1; write to the scientific chain or the publication-projection chain; or rename/copy/overwrite/delete publication directories or artifacts. Source-boundary enforcement (transitive; AST alone insufficient) — all of: AST direct-import inspection; recursive local import-graph traversal (transitive closure); forbidden-module AND forbidden-symbol lists; path-ownership checks (J1 writes only under `publication_staging/`,`publication/`,`publication_chain/`; J2 writes only under `publication_recovery_chain/`); callable-surface inspection; runtime monkeypatch sentinels asserting descriptor/manifest `call_count == 0`; module-loading tests in an isolated subprocess; negative tests attempting forbidden imports. A module reaching a prohibited surface = `PUBLICATION_BOUNDARY_VIOLATION` (test-time; runtime fail-closed refusal writing no evidence). J2 specifically must prove it cannot import or invoke: descriptor modules; manifest reader; fixture loader; scientific runner; bundle constructor; `SCIENTIFIC_COMPLETION` writer; publication artifact generator; publication directory promotion utility — importing only validation, replay, schema, authorization-validation, and recovery-chain writer surfaces.

---

## 23. Publication authorization / projection / chain / recovery identities

Distinct identities (a calculable digest is NOT authority): `publication_projection_identity` (deterministic; §6); `publication_projection_authorization_identity` (commitment to a committed projection-authorization document); `publication_chain_identity` (`sha256(canonical of {projection_identity, projection_authorization_identity})`); `publication_recovery_authorization_identity` (commitment to a committed recovery-authorization document; §13); `publication_recovery_chain_identity` (`sha256(canonical of {original_publication_chain_identity, recovery_authorization_identity})`). Each authorization document is a later docs-only task, neither drafted nor authorized here. Every publication-projection record carries the three projection identities; every recovery record carries the recovery authorization + recovery chain identities and references the originals in its payload/anchor.

---

## 24. Publication projection recipe

`publication_projection_recipe` (`publication-projection-recipe-v0.3`) deterministically maps the verified bundle to exact artifacts. v0.3 defines its own `-v0.3` structures; not byte-identical to v0.2. No fabricated final hashes; each artifact SHA-256 = `sha256_hex(<exact canonical bytes the recipe produces from the future bundle>)`, verified by regenerate-and-compare.

```text
Artifact 1 — iososv_v0_3_result.json ; schema "torment-brainvision-synthetic-validation-result-v0.3"
  key order: schema, result_kind, scientific_evaluation_reached, descriptor_evaluation_reached, pass_bundle_sha256, strong_order_hypothesis, formal_hold, mode
  values: result_kind=bundle.scientific_result_kind ; scientific_evaluation_reached=true ; descriptor_evaluation_reached=true ; pass_bundle_sha256=bundle.pass_bundle_sha256 ;
          strong_order_hypothesis="STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY" ; formal_hold="active" ; mode="Mode_0" ; raw control cases OMITTED
Artifact 2 — iososv_v0_3_execution_envelope.json ; schema "torment-brainvision-synthetic-validation-execution-envelope-v0.3"
  key order: schema, authority_consumed, current_state, repository_execution_head, branch, python_version, runner_identity, runner_test_identity, schema_contract_identity, descriptor_identity, scientific_result_kind, pass_bundle
  nested: current_state = current_state_snapshot (§16) ; *_identity = {source_path,git_blob,raw_sha256} ; pass_bundle = the stored canonical_pass_bundle (§16 key orders incl. accepted_family.results[] and controls incl. malformed_and_degenerate_control_cases[]) ; raw control cases INCLUDED
Artifact 3 — iososv_v0_3_summary.txt ; exact ASCII text = "Stage S3B v0.3 synthetic validation\nresult_kind = <bundle.scientific_result_kind>\nFORMAL_HOLD = active\nMode_0 = active\nSTRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY\n"
All: canonical_json_bytes (JSON) / exact ASCII (summary); one terminal newline; SHA-256 = sha256_hex(bytes); verify by regenerate-and-compare.
```

`PUBLICATION_COMPLETED` records the three filenames and their SHA-256 (from actual projected bytes). J1 writes to `publication_staging/<chain_id>/`, verifies, then promotes to `publication/<chain_id>/` via the §21 no-replace primitive. The recovery utility (J2) uses this recipe only to re-derive expected bytes for verification of already-final artifacts; it never writes artifacts.

---

## 25. Context-sensitive failure taxonomy

Nine columns exactly: `1 classification | 2 furthest scientific | 3 furthest publication | 4 pub authority | 5 pub-result assert | 6 auto retry | 7 new auth req | 8 op review | 9 retained artifacts`. Every row has exactly nine cells. Automatic retry is `no` in every row (nothing in this design auto-retries). Invariant: no publication-authority, staging, promotion, final-directory, publication-evidence, or recovery failure may erase or weaken an already-established authoritative scientific result.

| classification | furthest scientific | furthest publication | pub authority | pub-result assert | auto retry | new auth req | op review | retained artifacts |
|---|---|---|---|---|---|---|---|---|
| AUTHORITY_ATTEMPT_STATE_INDETERMINATE (sci) | none proven | none | n/a | no | no | new scientific authorization | yes | debris |
| AUTHORITY_CLOSED_UNEXERCISED_AFTER_CONSUMPTION_RECORD_FAILURE | none | none | n/a | no | no | new scientific authorization | yes | debris |
| PRIMARY_RECORD_* / SCIENTIFIC_BUNDLE_* before pair | last valid | none | n/a | no | no | new scientific authorization | yes | debris |
| ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE / INVALID_SCIENTIFIC_COMPLETION | reads durable | none | n/a | no | no | new scientific authorization | yes | bundle/receipt |
| SAME_SEQUENCE_FORK / BROKEN_LINK / SEQUENCE_GAP / REPLAY_IDENTITY_MISMATCH (sci) | pre-defect chain | none | n/a | no | no | new scientific authorization | yes | all objects |
| SCIENTIFIC_TERMINAL_STATUS_WRITE_FAILED_AFTER_AUTHORITATIVE_PAIR | AUTHORITATIVE result | none | not-attempted | yes | no | publication-projection authorization | maybe | pair |
| AUTHORITATIVE_PAIR_ESTABLISHED (CONSUMED_COMPLETE_UNPUBLISHED) | AUTHORITATIVE result | none | not-attempted | yes | no | publication-projection authorization | no | pair |
| PUBLICATION_AUTHORITY_CONSUMPTION_ATTEMPT_FAILED | AUTHORITATIVE result | none | consumed | no | no | new publication-projection authorization | yes | debris |
| PUBLICATION_AUTHORITY_ATTEMPT_STATE_INDETERMINATE | AUTHORITATIVE result | indeterminate | consumed | no | no | new publication-projection authorization | yes | any |
| PUBLICATION_AUTHORIZATION_VALIDATION_FAILED | AUTHORITATIVE result | none | not-attempted | no | no | publication-projection authorization | maybe | none |
| PUBLICATION_CHAIN_GENESIS_WRITE_FAILED | AUTHORITATIVE result | none | consumed | no | no | new publication-projection authorization | maybe | debris |
| PUBLICATION_STAGING_DIRECTORY_COLLISION | AUTHORITATIVE result | none | consumed | no | no | new publication-projection authorization | yes | existing staging |
| PUBLICATION_FINAL_DIRECTORY_COLLISION | AUTHORITATIVE result | disputed final | consumed | no | no | new publication-projection authorization | yes | existing final |
| PUBLICATION_CHAIN_IDENTITY_COLLISION | AUTHORITATIVE result | disputed | consumed | no | no | new publication-projection authorization | yes | conflicting dirs |
| PUBLICATION_STAGING_INCOMPLETE | AUTHORITATIVE result | none asserted | consumed | no | no | new publication-projection authorization | maybe | staging directory and partial artifacts, if present |
| PUBLICATION_PROMOTION_FAILED | AUTHORITATIVE result | none; final absent | consumed | no | no | new publication-projection authorization | maybe | complete verified staging directory |
| PUBLICATION_PROMOTION_OUTCOME_INDETERMINATE | AUTHORITATIVE result | not asserted | consumed | no | no | publication-recovery authorization | yes | staging and/or final |
| PUBLICATION_PROMOTION_AMBIGUOUS | AUTHORITATIVE result | disputed; fail closed | consumed | no | no | publication-recovery authorization | yes | both dirs byte-for-byte |
| PUBLICATION_FINAL_DIRECTORY_INVALID | AUTHORITATIVE result | none asserted | consumed | no | no | publication-recovery authorization | yes | final as-is |
| PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED | AUTHORITATIVE result | final bytes verified; evidence-incomplete | consumed | yes | no | publication-recovery authorization | maybe | final and staging |
| PUBLICATION_PROJECTION_FAILED / PUBLICATION_VERIFICATION_FAILED | AUTHORITATIVE result | none | consumed | yes | no | publication-projection authorization | yes | staging |
| PUBLICATION_TERMINAL_STATUS_WRITE_FAILED | AUTHORITATIVE result | PUBLICATION_COMPLETED strongest valid | consumed | yes | no | none | no | final and records |
| PUBLICATION_CHAIN_REPLAY_FAILED / PUBLICATION_CHAIN_FORK | AUTHORITATIVE result | disputed; fail closed | consumed | yes | no | publication-projection authorization | yes | all objects |
| PUBLICATION_BOUNDARY_VIOLATION | AUTHORITATIVE result | none; refused | n/a | no | no | fix module then re-authorize | yes | none |
| CONTRADICTORY_EVIDENCE | conservative subset | conservative | n/a | no | no | new scientific/publication authorization | yes | all objects |
| PUBLICATION_COMPLETED | AUTHORITATIVE result | published | consumed | yes | no | new publication-projection authorization for re-project | no | final and records |
| PUBLICATION_RECOVERY_AUTHORIZATION_VALIDATION_FAILED | AUTHORITATIVE result | unchanged original | recovery not-attempted | no | no | publication-recovery authorization | maybe | none |
| PUBLICATION_RECOVERY_AUTHORITY_CONSUMPTION_ATTEMPT_FAILED | AUTHORITATIVE result | unchanged original | recovery consumed | no | no | new publication-recovery authorization | yes | recovery debris |
| PUBLICATION_RECOVERY_AUTHORITY_ATTEMPT_STATE_INDETERMINATE | AUTHORITATIVE result | unchanged original | recovery indeterminate | no | no | new publication-recovery authorization | yes | any recovery evidence |
| PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED | AUTHORITATIVE result | unchanged original | recovery consumed | no | no | new publication-recovery authorization | maybe | recovery debris |
| PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH | AUTHORITATIVE result | unchanged original | recovery consumed | no | no | new publication-recovery authorization | yes | recovery evidence |
| PUBLICATION_RECOVERY_FINAL_DIRECTORY_MISSING | AUTHORITATIVE result | none; final absent | recovery consumed | no | no | new publication-projection authorization | yes | recovery evidence |
| PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID | AUTHORITATIVE result | none asserted | recovery consumed | no | no | new publication-projection authorization | yes | recovery evidence and final as-is |
| PUBLICATION_RECOVERY_ARTIFACT_HASH_MISMATCH | AUTHORITATIVE result | none asserted | recovery consumed | no | no | new publication-projection authorization | yes | recovery evidence |
| PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED | AUTHORITATIVE result | final verified; recovery evidence incomplete | recovery consumed | yes | no | new publication-recovery authorization | maybe | recovery debris and final |
| PUBLICATION_RECOVERY_CHAIN_FORK | AUTHORITATIVE result | disputed recovery; fail closed | recovery consumed | no | no | new publication-recovery authorization | yes | conflicting recovery objects |
| PUBLICATION_RECOVERY_TERMINAL_STATUS_WRITE_FAILED | AUTHORITATIVE result | recovery evidence strongest valid | recovery consumed | yes | no | none | no | recovery records |

Worked invariants: a scientific terminal failure after the pair keeps the result valid and publication possible under a new valid authorization; publication/recovery authority, authorization, genesis, staging, promotion, final-directory, and evidence failures all leave the scientific result unaffected; verified final bytes without completion/recovery evidence are preserved as evidence-incomplete and never auto-completed. Scientific execution never resumes.

---

## 26. Fault-injection contract

Every load-bearing operation × timing × structural case (test only). Scientific + publication families and timings as before, PLUS publication-recovery families: recovery authorization validation; recovery chain-identity derivation; recovery authority consumption point; recovery genesis; PUBLICATION_RECOVERY_ATTEMPTED; final-directory read/verify; artifact filename/byte/hash verify; recovery evidence write; recovery replay; recovery terminal. Added mandatory publication cases (unchanged) plus recovery cases:

```text
recovery invocation dies before recovery genesis creation ; recovery genesis create/write/fsync/readback/directory-sync failure ;
original publication chain identity mismatch ; final directory missing ; final directory malformed ; artifact hash mismatch ;
recovery evidence write failure ; second PUBLICATION_RECOVERY_ATTEMPTED in one recovery chain (rejected) ;
two recovery authorizations for one original chain (distinct recovery chains, no collision) ; recovery-chain fork ;
recovery utility attempting prohibited (transitive) imports ; recovery attempting to write the original publication chain (rejected) ;
recovery attempting artifact generation/promotion/overwrite (rejected)
```

Every test must prove: scientific result remains unchanged; the original publication chain is never appended to or reopened; consumed publication/recovery authorization is not reused; no automatic retry; no artifact generation/promotion/overwrite/repair by recovery; no cross-chain output collision; forensic material retained; deterministic fail-closed classification.

---

## 27. Test inventory

Proposed modules under `research/brainvision/` (create no files): schema; canonicalization; identity (incl. chain-id, recovery-chain-id, and the §7 recomputable-example unit tests); primary_writer (+Windows); scientific_replay; authority; contact_accounting; bundle; completion_receipt; emergency (pre-open collision, ASCII marker, forced-kill); windows_adapter (+ no-replace promotion acceptance); publication_boundary (source-boundary, J1); publication_recipe; publication_chain (identity, one-attempt, authority states, operation order, promotion, collisions, crash states); `test_durable_evidence_publication_recovery_v0_3.py`; `test_durable_evidence_publication_recovery_boundary_v0_3.py`; `test_durable_evidence_publication_recovery_replay_v0_3.py`; faultinjection (full §26 matrix); end_to_end_synthetic. No test contacts the real frozen manifest, and no recovery test generates artifacts; synthetic/sentinel fixtures only unless a later separate authorization permits it.

---

## 28. Proposed implementation file inventory

Bounded modules (create no files): `durable_evidence_schema_v0_3.py ; durable_evidence_identity_v0_3.py ; durable_evidence_primary_writer_v0_3.py ; durable_evidence_scientific_replay_v0_3.py ; durable_evidence_authority_v0_3.py ; durable_evidence_contact_v0_3.py ; durable_evidence_bundle_v0_3.py ; durable_evidence_completion_v0_3.py ; durable_evidence_emergency_v0_3.py ; durable_evidence_windows_adapter_v0_3.py (durability + no-replace promotion) ; durable_evidence_publication_v0_3.py (J1) ; durable_evidence_publication_replay_v0_3.py ; durable_evidence_publication_recovery_v0_3.py (J2) ; durable_evidence_publication_recovery_replay_v0_3.py ; durable_evidence_faultseam_v0_3.py ; run_independent_order_sensitive_synthetic_validation_v0_3.py (assembler; imports descriptor ONLY here and in F)`. Science, evidence storage, emergency, replay, projection, and recovery are separate; neither J1 nor J2 imports the descriptor (transitively — §22); J2 imports no artifact generator or promotion adapter.

---

## 29. Implementation sequence

```text
1 schema+canonicalization → 2 identity(all, incl chain-id + recovery-chain-id) → 3 stored-object writer+durability states →
4 scientific replay → 5 authority(four states)+contact → 6 bundle validation+writer+receipt → 7 emergency capsule →
8 Windows durability adapter [BLOCKER] → 9 no-replace promotion adapter [BLOCKER] →
10 publication projector boundary+recipe+chain identity+operation order+collisions+crash states →
11 publication-recovery verifier boundary+recovery chain+identities+record kinds+consumption+evidence semantics →
12 fault-injection infrastructure → 13 v0.3 runner assembly(synthetic; no real manifest) → 14 adversarial GPT+Codex review before any implementation authorization
```

Each step gated by its own tests; no real manifest contact or authoritative execution at any step.

---

## 30. Security analysis

```text
logical/storage separation: scientific identity nonce-free; retried write = redundant instance, never a false fork (recomputable §7 examples).
publication_chain_identity and publication_recovery_chain_identity: distinct authorizations cannot collide (recomputable §7 examples).
publication eligibility independent of scientific terminal status; scientific vs publication vs recovery authority each four-state with live-only NOT_ATTEMPTED; post-event ambiguity → INDETERMINATE.
publication and recovery authorizations consumed at invocation-attempt begin (reuse-policy), regardless of genesis outcome — no missing-genesis reuse loophole.
recovery is evidence-only in a distinct immutable chain: it never appends to/reopens the original projection chain, never generates/promotes/overwrites/repairs artifacts, never executes science or contacts the manifest.
exact publication operation order; no artifact before genesis+attempted durable; same-volume no-replace promotion; fail-closed on absent primitive; staging/final collisions and promotion ambiguity fail closed.
tamper-evidence (canonical bytes + self-hash + predecessor link); transitive source boundary for J1 and J2; context-sensitive nine-column taxonomy where auto-retry is never yes and scientific truth is never weakened; explicit byte-length semantics.
```

Residual: Windows directory-entry durability AND the no-replace same-volume promotion primitive are unproven pending §21/§32; no on-host design survives volume/host/power loss; the emergency channel is mechanism diversity only. No claim that the architecture is implemented, tested, proven secure, Windows-durable, or ready for execution.

---

## 31. Remaining risks and blockers

```text
R1 Windows directory-entry durability primitive unvalidated. R2 No-replace same-volume directory-promotion primitive unvalidated.
R3 Extended-length path handling must be asserted or long paths fail. R4 Replay (all three chains) must reject torn/forked/cross-identity/durability-unconfirmed candidates without excluding valid ones.
R5 Emergency capsule cannot survive abrupt termination. R6 Bundle size bound (4 MiB) validated against the real v0.2 pass-bundle size class.
R7 Transitive source boundary (J1 and J2) enforced by tests. R8 Null/float/malformed rejection precedes bundle construction. R9 Fault-injection completeness.
R10 Whole-directory/volume/host/power loss defeats on-host evidence (out of scope).
```

---

## 32. Implementation-readiness verdict

```text
B. IMPLEMENTATION_SPECIFICATION_READY_WITH_NAMED_BLOCKERS
```

The two blocking defects are resolved: publication recovery now has a fully defined durable representation (a distinct immutable publication-recovery evidence chain with its own identities, schema, record kinds, capability boundary, consumption states, evidence semantics, failure classifications, replay, and source boundary), and the two malformed taxonomy rows are repaired within a nine-column table validated to exactly nine cells per row with no auto-retry set to yes. The specification authorizes nothing. Remaining blockers are limited to platform validation, size-bound confirmation, and future capability-specific authorization documents:

```text
BLOCKER-1  Validated Windows directory-entry durability primitive/adapter (§21). Fail-closed acceptance gate.
BLOCKER-2  Validated no-replace same-volume publication directory-promotion primitive (§12/§21). Fail-closed acceptance gate.
BLOCKER-3  Numeric size-bound confirmation (record 64 KiB, bundle 4 MiB, capsule 4 KiB, exception 512 B) against the real v0.2 pass-bundle size class.
BLOCKER-4  Separate future docs-only authorizations, each with its minimum binding defined but neither drafted nor authorized here:
           the publication-projection authorization (§23), the durability-reconfirmation authorization (§18), and the publication-recovery authorization (§13/§23).
```

If a required primitive cannot be validated on the authoritative environment, its blocker escalates to a documented fail-closed mode rather than making the specification NOT_READY. The publication-recovery authorization now has a fully defined durable representation but remains a future docs-only authorization; recovery is neither implemented nor authorized.

---

## 33. Non-authorizations and preserved boundaries

Creates no authority; changes nothing. Does not authorize or recommend enacting:

```text
v0.3 implementation ; v0.3 or any runner execution ; manifest contact ; scientific reconstruction/recomputation ;
publication of any result ; publication recovery ; durability reconfirmation ; evidence repair/rename/deletion/promotion/terminalization ;
reconstruction of the v0.2 scientific verdict ; a v0.2 retry ; PsiTRS contact ; historical F3 reinterpretation ;
production-kernel modification ; live Brainvision integration ; memory-system integration ; live capture/ingestion ;
service/runtime integration ; threshold/tolerance tuning ; scientific rescue ; production claims ;
a scientific-execution authorization ; a publication-projection authorization ; a durability-reconfirmation authorization ; a publication-recovery authorization
```

Preserved:

```text
docs-only; delivered outside the repository; not saved into docs/
FORMAL_HOLD = active ; Mode 0 = active ; STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
Brainvision remains offline and quarantined under research/brainvision/
v0.2 is consumed, terminal, and immutable; any future evaluation is a NEW lineage — never a retry
valid scientific result kinds are exactly SYNTHETIC_GATE_PASSED and SYNTHETIC_GATE_FAILED; execution invalidity (SYNTHETIC_GATE_INVALID)
  is not a third scientific result; this document does not state or imply which occurred in v0.2, which is not durably available and must not be reconstructed
```

*End of corrected implementation specification v0.1. Docs-only, delivered outside the repository. No repository change, execution, import, manifest access, publication, publication recovery, scientific reconstruction, or Git operation was performed in producing it.*
