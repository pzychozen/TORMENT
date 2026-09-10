# TORMENT — Post-P7 Native Production Validation — Stage 1R8A

Date: 2026-09-10 UTC.

**R8A = PASS.** R8 encountered an expected policy refusal in a scope whose
current policy is incompatible with ordinary native public ingest. An
existing lifecycle-qualification scope required no policy changes and
successfully accepted exactly one ordinary private memory write. One
ordinary read retrieved that memory; two bounded control queries found no
cross-scope authority.

R8 remains frozen as FAIL_STOPPED_NATIVE_WRITE_REFUSAL. Its HTTP 409 occurred
before the durable executor and was not a SQLite persistence failure. This
R8A record does not rewrite that result. Stage 1 remains HELD_FOR_REVIEW;
reinforcement and restart persistence have not been exercised.

## Git and authority

Starting HEAD and origin/main were both:
**c9bb4b373b66a39c2c1ab557ac8ec06470db489c**.
The tracked worktree and index were clean. Existing unrelated untracked
artifacts were preserved. No reset, stash, clean, policy edit, runtime-code
change, or broad staging occurred. This Markdown record is the sole
repository change, published under the standing Stage-1 evidence-only Git
policy. Final literal Git IDs are recorded in publication_verification.json
and the final response.

All project Python ran in Windows CMD after **conda activate torment**, using
C:\Users\Notandi\miniconda3\envs\torment\python.exe and SQLite **3.53.4**.
The narrow census constructed and closed a normal native production owner
for read-only authority recovery. It constructed no Fabric, model, service,
write context, or trajectory writer.

Normal root-v2 recovery validated the current root profile, scope bindings,
representation lane, production routing bindings, and complete active
membership closure against the immutable completion witness. These facts
were then used for the policy census; historical source plans alone were
not treated as current membership.

| Authority fact | Before / after |
| --- | --- |
| Selector generation / state | 8 / NATIVE_ACTIVE |
| Active core | f21c730f-5222-4aa8-9a5f-1c1188456df3 |
| Core role / ever active | ACTIVE_CORE / true |
| Agreement | NATIVE_AGREEMENT |
| Profile digest | 35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a |
| Root envelope digest | e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb |
| Membership closure digest | f76c9d580db818da18b57efabee4afd09765a59f7e97d53849b9b5157d4ce67a |

## Exact R8 refusal and qualification semantics

The actual path was:

~~~text
POST /agent/ingest                         app.py:1217
  -> SpineRequest(operation="ingest")      app.py:1221
  -> submit_task / ordinary fast handler spine.py:1518 / :686
  -> NativePublicTormentRuntime.ingest     public_runtime.py:634
  -> keyed fast-operation preflight
  -> active private scope / motif-domain recovery
  -> native workspace view and effective domain policy
  -> admitted shared operation-domain validation
  -> bool(policy["auto_merge_motifs"]) guard
       raises at public_runtime.py:686
  X  NativePublicIngestRequest / executor.execute were not reached
~~~

The HTTP 409 detail was:

~~~text
NativePublicOperationRefused: native public ingest refuses an unqualified auto-merge motif policy before cognition
~~~

The exact R8 domain file,
data/workspaces/audit_smoke_v0_2/domain_policies.json, contains
policies.personal.auto_merge_motifs=true. The public guard at
public_runtime.py:685-688 rejects any truthy effective value; it does not
inspect current entropy, motif similarity, or whether a merge would happen
on this particular request.

Had that guard passed, NativePublicIngestExecutor.execute would reserve a
public mutation receipt, mark cognition started, obtain and persist the
PreparedFabricIngest plan, then call the native storage adapter. That adapter
builds NativeFabricRouteRequest and uses the native owner's write context.
The ordinary source route reserves its pending source, performs the qualified
motif/member work, commits canonical memory, publishes its representation,
runs the qualified post-write tail, and records public completion. R8
reached none of those durable boundaries. R8's unchanged core and operation
ledger independently corroborate the before-write refusal.

The policy and qualification are distinct:

| Question | Current implementation |
| --- | --- |
| Owner of the policy values | External workspace domain_policies.json, read by the native facade's _read_domain_policies; existing code defaults apply when the domain mapping is absent/empty. |
| Binding | Workspace plus operation domain. The admitted private/shared plans constrain which domain may be consumed. Model D's private plan retains motif_domain_id=None; the private operation selects an admitted shared domain. |
| Behavior requested by auto-merge | Entropy-driven automatic approval of motif merge suggestions, affecting motif identity/current state, centroid, strength, membership, and workflow evidence. It is a semantic mutation, not a SQLite tuning switch. |
| Public-ingest acceptance | Effective auto_merge_motifs is false/false-like, alongside the other existing identity, root, routing, representation, and post-write requirements. This means automatic merging is not requested; it does not promote an active policy to qualified status. |
| Public-ingest refusal | Any truthy effective auto_merge_motifs value is unconditionally refused before executor effects. There is no per-domain qualification certificate that overrides this guard. |
| Absence | Absence alone does not require refusal. The existing reader falls back to the named domain default or an empty mapping. Missing personal policy inherits true and therefore refuses; an admitted unknown domain can resolve to an empty mapping and an inactive flag. Unreadable/invalid JSON policy evidence refuses separately. No missing policy was manufactured here. |

The frozen auto-merge law computes entropy, makes suggestions at the existing
threshold, considers at most five suggested merges, and approves at most two
whose similarity meets the additional margin. The stronger motif survives;
the native merge owner publishes the survivor/dropped successors and
membership changes while retained workflow stores record the decision.

**Native auto-merge does exist in separately qualified maintenance paths.**
The M2 profile marks motif_auto_merge=QUALIFIED, and the current I4F private
profile inherits that value. This does not override the public-ingest guard.
The broad-private post-write validator also unconditionally calls _refuse
when this policy is active, whereas the separate true-split tail requires
the qualified capability. Thus, the R8 error does not establish that every
native motif-merge implementation is unqualified. It identifies an explicit
ordinary-public-write composition boundary.

Supporting frozen sources include public_runtime.py:1198, native public
executor/receipt code, native_post_write_runtime.py:154-171 and :1454-1471,
motifs.py:475, BLOCKER_5_A4R3_PUBLIC_BACKEND_SELECTION_AND_TRANSPORT.md,
and 7G5E4D_M2_NATIVE_MOTIF_MERGE_MUTATION.md. The public transport fixture
also explicitly persists an inactive personal auto-merge policy before
native startup.

For the exact R8 triple:

~~~text
READ_QUALIFIED = YES (retained R6/R7 observations)
R8_SCOPE_NATIVE_WRITE_ELIGIBLE = NO
R8_SCOPE_AUTO_MERGE_POLICY_PRESENT = YES
R8_SCOPE_AUTO_MERGE_POLICY_QUALIFIED = NO_FOR_ORDINARY_NATIVE_PUBLIC_INGEST
R8_WRITE_REFUSAL_EXPECTED_BY_FROZEN_SEMANTICS = YES
R8_REFUSAL_CLASS = EXPECTED_SCOPE_POLICY_REFUSAL
R8_TEST_SCOPE_CLASS = BAD_TEST_SCOPE_FOR_THE_REQUESTED_PUBLIC_WRITE
~~~

This classifies the current scope/policy combination. It does not infer a
permanent historical intention to make the workspace read-only.

## Existing scope census and selected safe scope

The census used **154 admitted scopes in 51 workspaces**: 76 private agent
scopes and 78 shared domain scopes. It read their existing effective policies
and configuration metadata, without creating a scope or dumping memory text.

| Narrow census result | Count |
| --- | ---: |
| Admitted domain policies with active auto-merge | 30 |
| Admitted domain policies passing the inactive-policy gate | 48 |
| Private scopes with at least one policy-admissible operation domain | 48 |
| Private candidates excluded by the existing domain-order requirement | 4 |
| Private scopes with qualified current write configuration | **44** |

The four excluded private candidates are orchard/aria and ws3, ws4, ws5
with a1. Their persisted domain order does not equal the admitted shared
order required by the current Model D private bridge binding. No production
probe or repair of these configurations was performed.

The required eligible-scope count is **44 distinct PRIVATE_AGENT scopes**,
the scope kind authorized for the retry. It means current admission,
membership, routing, identity, policy and domain-order configuration passed
inspection. It does not guarantee that every arbitrary payload passes
ordinary write-intent, strength, similarity, or structural routing gates.
The 48 shared policy candidates are separately recorded and are not counted
as qualified private retry scopes or experimentally qualified shared writes.
The helper's additional shared metadata matches are conservative screening
facts, not a new shared admission rule.

Of the 44 private configurations, 35 belong to existing Character-bearing
hive test corpora and were not selected for mutation; eight belong to scale
qualification corpora. The selected existing lifecycle scope supplies the
remaining candidate:

| Binding | Selected value |
| --- | --- |
| Workspace | lifecycle-e9f54df99882 |
| Agent | lifecycle-agent-e9f54df99882 |
| Operation domain | lifecycle_qualification |
| Scope | PRIVATE |
| Private source namespace | 311cd3ac-175c-4532-83c7-87fdf84b4e4c |
| Identity namespace | 925405a4-ba68-4fd2-b19e-677a3d1f67f8 |
| Semantic scope | 1736a09d-acd3-494c-a0c4-e10c1ec624e2 |
| Idempotency namespace | df94c51a-3b6d-466e-a7bb-a2cbb2eefb37 |
| Private motif domain | None |
| Effective auto-merge | false, explicitly persisted before R8A |

The frozen I4G-R1 real-root topology record identifies this exact lifecycle
workspace/agent/domain. Its agent has no Character seed or state. The five
existing records were created together at timestamp 1787709533, one second
after workspace/agent creation, at logical steps 1, 3, 4, 5 and 6. Three
summaries carry validation markers. This metadata supports the bounded
test-corpus safety judgment; no historical summary text was retained.
An initial all-record keyword screen was insufficient, so the read-only
review checked the shared origin metadata before authorizing the attempt.

SAFE_EXISTING_WRITE_TEST_SCOPE_FOUND = YES.
NATIVE_PRODUCTION_WRITE_QUALIFICATION_GAP = NO in the order's systemic
zero-qualified-scope sense. Other readable scopes need not be write-eligible.

## One production write and one target read

The ordinary service launched as python -m torment_service, PID **12876**,
using the same seven-field root-v2 host profile, HF_HUB_OFFLINE=1, strict ST
BGE provider, and unchanged optional query diagnostics. No external
descriptor, new environment option, generative provider, or policy was added.
GET /health returned HTTP 200, NATIVE, ok=true, and no degraded embedder.

At **2026-09-10T09:06:50.216395Z**, exactly one POST /agent/ingest was sent
with a unique harmless marker, private scope, the selected existing domain,
step 1000201, and a distinct Idempotency-Key. Neither a summary nor an
embedding was supplied. The ordinary timeout remained 240 seconds.

Marker: **R8A-20260910-cabc0ca2-0ed3-4293-93dc-425a51e121d2**.
Request SHA-256:
d41890a5364c617d1a1ebfa75a3b65499cf33eb52249bd5293adb131d1977c62.

The service returned HTTP **200** in **117.000 seconds**:
stored=true, reinforced=false, eid=6, path=fast, escalated=false,
result_code=stored, decision_code=fast_allowed, proposal_id=null.
The ordinary kernel's generated summary retained the unique marker.

POST /agent/query retrieved that exact memory in **28.203 seconds**:
six private hits, zero shared hits, no authority-guard rejection, expected
namespace/semantic scope, and matching native/public summary hashes.

| Native identity | Value |
| --- | --- |
| Private EID | 6 |
| Memory object | 4b22364b-194b-4a9a-92a2-1cd3cb1589c1 |
| Pending creation R1 | 0a1f579a-c043-49cf-a2be-d657430f8c05 |
| Current R2 | 58737d7a-858c-411d-b1ec-17637725d844 |
| Current lineage / existence | NATIVE_ORDINARY / EXISTS |
| Stored summary SHA-256 | 140aab4bcb5e2ef2326aaac66c048dfaf035e8f905e171165b4723e77047437f |
| New motif object | 0c2ff440-7b7b-4951-9b54-511e7ac3a59c |
| New motif revision | bc4c6ec9-065d-45b2-86af-75a6bed9c29d |

R1 pending to R2 existing is the ordinary precommit/canonical-commit path,
not reinforcement. The memory object's compatibility kind LEGACY_CORE_NODE
does not indicate legacy storage authority: its native operation, revision,
namespace and current semantic-admission witnesses are recorded.

## Bounded isolation and unchanged boundaries

Two further ordinary queries used the same marker:

| Control | Client seconds | Private/shared hits | New memory present |
| --- | ---: | ---: | --- |
| Existing R7 hive / contrarian / research | 28.000 | 6 / 0 | No |
| audit_smoke_v0_2 / smoke_runner / personal | 28.672 | 5 / 0 | No |

These are two lawful other-agent/other-workspace observations. The selected
lifecycle workspace has only one admitted private agent, so no second agent
was fabricated there. The new object has exactly one private EID alias; every
new memory/motif/relationship revision is in the selected private semantic
scope. No shared memory or cross-scope authority was created.

Model D remains intact: the private plan keeps None, the operation selects
lifecycle_qualification, and existing strict shared motif readers remain
unchanged. Natural query motif summaries used admitted shared domains.
All 35 memory and 23 motif certified refusal identities were retained; no
old native row changed and no refusal acquired a successor or READY promotion.
No new P3 semantic census was performed.

## Durable accounting and shutdown

| Artifact | Before | After shutdown |
| --- | ---: | ---: |
| Selected production core bytes | 82,747,392 | 82,800,640 |
| Core WAL bytes | 0 | 0 |
| Trajectory authority bytes | 819,200 | 819,200 |
| Trajectory WAL | Present, 0 bytes | Absent at recorded file observation |

Core SHA-256 changed legitimately from
eea6e07072e0cdad09ab2872203361c18adf19e044f452686249352aef84dc85 to
567a058e15210f891c160e458c434a9efccdca4182add0ee0b5c409d3eda63ee.
No byte-identity requirement was imposed on a successful write.

All pre-existing core rows matched their pre-run hashes. Additions comprise
one memory, one motif, one membership, three object revisions, one relationship
revision, one representation with integrity/READY evidence, and supporting
aliases/effects. The **10 new operations** all use the selected private
idempotency namespace and the same derived authorized request key:

~~~text
public-mutation/v1/62e147aa0f8f6dc25dfd6e473d63c8f4a69c45bfb60d9569e30ce564d977481b
~~~

They are four public receipt stages, source reservation, motif creation with
member, canonical source commit, and three representation stages. There was
no reinforcement operation and no additional memory.

The ordinary ingest tail acquired the existing native trajectory authority
for the selected scope: one fenced session replacement, generation 4, session
pid:12876:dadcb5cb-a0b4-4c28-8927-a7bc65d0f8a3. Four intents settled for writer
initialization, genesis, step, and shutdown close. The sealed V2 chunk has
epoch 1, frame_seq 1, step 1000201, one frame and six entity records; its
SHA-256 matches the manifest. These are accounted ordinary write effects,
not an extra manual trajectory operation or a restart qualification.

The only selected-workspace file changes were the ordinary roles.json and
symbol_state.json updates plus four new V2 trajectory files. All 51 policy
file observations matched. The 105 fingerprinted files in the two control
workspaces matched. The bounded recent-data-file inventory identified only
the accounted changes and SQLite access/coordination files.
AUTHORIZED_DURABLE_MUTATION_ONLY = PASS.

One Ctrl+C initiated normal shutdown. Uvicorn recorded application shutdown
complete and finished PID 12876; the CMD launcher exited **0** after its
normal batch prompt. Process and port-8787 listener were absent afterward.
No restart or reinforcement was performed.

Only local **BAAI/bge-small-en-v1.5**, CPU, 384 dimensions was involved.
All 29 frozen cache/lock fingerprints remained unchanged. Existing query
diagnostics observed 11 BGE encodes across the three queries; no total ingest
encode count is claimed. No conversational model or external AI API was
configured or invoked. No performance changes or new tests were introduced.

## Evidence and required return

External evidence directory:
C:\TORMENT\TORMENT_administration\post-p7-stage-1r8a-20260910.

policy_census.json records the complete admitted-policy inventory and current
membership recovery. candidate_qualification.json records per-candidate
configuration screening, the selected scope and safety evidence.
create.json and the three redacted query receipts establish the public
behavior. before.json, after_shutdown.json, durable_accounting_final.json,
shutdown.json and result_verification.json establish the bounded effects.
All final verification checks passed.

Read-only helper corrections are retained separately: the initial keyword
safety screen was supplemented with origin metadata; operation-key derivation
was given its required typed public key; and the memory accounting selector
was corrected to use the actual memory object ID rather than assume its
compatibility kind was named MEMORY. None changed production code, replayed
a request, or altered authoritative data.

The evidence manifest binds receipts, helpers, source/work-order references,
and this result record. Publication verification binds the final Git state
and document/manifest hashes. Repository validation is the bounded Markdown
git diff --check; R6/R7 implementation and qualification remain unchanged.

~~~text
STARTING_HEAD = c9bb4b373b66a39c2c1ab557ac8ec06470db489c
R8_WRITE_REFUSAL_SOURCE = NativePublicTormentRuntime.ingest; public_runtime.py:685-688
R8_REFUSAL_OCCURRED_BEFORE_DURABLE_WRITE = YES
R8_SCOPE_NATIVE_WRITE_ELIGIBLE = NO
R8_SCOPE_AUTO_MERGE_POLICY_PRESENT = YES
R8_SCOPE_AUTO_MERGE_POLICY_QUALIFIED = NO_FOR_ORDINARY_NATIVE_PUBLIC_INGEST
R8_WRITE_REFUSAL_EXPECTED_BY_FROZEN_SEMANTICS = YES
EXISTING_NATIVE_WRITE_ELIGIBLE_SCOPE_COUNT = 44_PRIVATE_AGENT_SCOPES
SAFE_EXISTING_WRITE_TEST_SCOPE_FOUND = YES
NATIVE_PRODUCTION_WRITE_QUALIFICATION_GAP = NO
R8A_STARTUP = PASS
NATIVE_OWNER_RECOGNITION = PASS
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
R8A_NATIVE_MEMORY_WRITE = PASS
WRITE_THEN_READ = PASS
NEW_MEMORY_SCOPE_ISOLATION = PASS
AUTHORIZED_DURABLE_MUTATION_ONLY = PASS
GENERATIVE_MODEL_INVOLVED = NO
GENERATIVE_MODEL_DETAILS = LOCAL_BGE_ONLY; NO_GENERATIVE_PROVIDER
NORMAL_SHUTDOWN = PASS
R8_REFUSAL_CLASS = EXPECTED_SCOPE_POLICY_REFUSAL
NATIVE_PRODUCTION_WRITE_PATH = PASS
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R8A = PASS
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R8A_REVIEW
~~~

Case A is established. The empty shared corpus remains unpopulated and
nonempty shared ranking remains unvalidated. Resume the remaining R8
lifecycle only after review and further authorization. STOP.
