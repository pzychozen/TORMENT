# TORMENT Brainvision Prerecorded Operational Harness — Implementation Specification v0.1

## 1. Status / quarantine

**DOCS-ONLY implementation specification. Non-authorizing until reviewed; non-implementing.** This note
specifies a compact v0.1 orchestration harness. It builds nothing, runs no experiment, and changes no code,
test, or production file. Brainvision stays **offline, prerecorded, quarantined, service-disconnected,
non-runtime, non-production, descriptive**.

```text
FORMAL_HOLD_active                        = True
Mode_0_active                             = True
verdict                                   = HOLD

documentation_authorized                  = True
implementation_authorized                 = False   (pending final review of this spec)
experiment_authorized                     = False
scientific_claim_authorized               = False
temporal_order_claim_authorized           = False
perception_or_vision_claim_authorized     = False
runtime_integration_authorized            = False
production_kernel_modification_authorized  = False
```

Immutable boundaries — never modified or proposed for modification by this harness:

```text
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
research/brainvision/psi_trs.py
```

No code, tests, production files, or `psi_trs.py` are modified. No experiment is run. No commit or push.

## 2. Purpose and accepted direction

Accept a declared manifest of prerecorded `.npz` inputs and produce a deterministic, replayable,
interpretable offline engineering report by **orchestrating existing Brainvision analysis components**. The
harness orchestrates and preserves existing calculations; it does not reimplement them.

```text
Accepted direction D =
  B-first operational prerecorded harness
  + C-style diagnostics as non-gating reporting
  + A retained as a separate descriptor-blind validation stream
```

Required design principles (all binding on v0.1):

```text
existing paired-analysis raw result objects remain unchanged
existing boundary-neutral companion objects remain unchanged
no duplicated descriptor mathematics
no new response formula
no success field
no threshold
no classifier
no automatic scientific verdict
no result-driven normalization or feature selection
no writes by default
```

## 3. Reuse surface and import boundary

```text
B (operational descriptor analysis):
  research/brainvision/run_prerecorded_paired_analysis_v0_1.py
    callable boundary   = analyze_paths(npz_paths, include_sag=True, with_companion=True)
    returns             = _jsonable(build_result(clip_results))   (already JSON-able; non-finite -> None)
    reused constants    = SCHEMA, ANALYZER_NAME, ANALYZER_VERSION, CONTROLS, DESCRIPTOR_NAMES,
                          D_COMPANION, GLOBAL_SEED, BLOCK_LEN, EPSILON, NEAR_EPSILON_THRESHOLD,
                          COMPANION_OFFSET_POLICY, COMPANION_AGGREGATION_POLICY, LOCKS, NON_CLAIM,
                          RECURSIVE_DELTA_STANDING
  boundary-neutral companion (nested inside the above when with_companion=True):
    boundary_neutral_companion(...) → clip["boundary_neutral_companion"]

Envelope / replay pattern (reference, NOT imported — see §4):
  research/brainvision/run_n64_falsifier_v0_1.py
    canonicalize / canonical_text / canonical_bytes / sha256_hex / canonical_sequence_sha256
    capture_environment / _source / build_wrapper({payload, payload_sha256}) / emit(stdout-only)
    canonical contract = json.dumps(ensure_ascii=True, sort_keys=True, separators=(",",":"), allow_nan=False)
```

Import boundary (exact):

```python
import run_prerecorded_paired_analysis_v0_1 as paired
paired.analyze_paths(...)          # sole descriptor-computation entry point
paired.<NAME>                      # every reused constant is referenced through the module
```

The harness imports the analyzer module from the same quarantined directory and uses its constants through
`paired.<NAME>`. It does **not** import `descriptors`, `psi_trs`, SAG helpers, companion helpers, response
helpers, or control-transform modules directly, and it duplicates no descriptor mathematics. Tests follow the
existing repository `BV_DIR` / `sys.path` import convention.

## 4. Implementation-ready file boundary

```text
NEW (exactly two files):
  research/brainvision/run_prerecorded_operational_harness_v0_1.py
  tests/research/test_brainvision_prerecorded_operational_harness_v0_1.py

READ-ONLY REUSE (imported, unmodified):
  research/brainvision/run_prerecorded_paired_analysis_v0_1.py   (analyze_paths + constants in §3)

UNTOUCHED:
  research/brainvision/psi_trs.py ; run_n64_falsifier_v0_1.py ; run_prerecorded_paired_analysis_v0_1.py
  all torment_service/* ; all other repository files
NO new fixture, .npz asset, JSON schema file, or result artifact is created. The harness writes no file.
```

**Decided fork — canonicalization ownership.** The harness carries its **own transport-canonicalization
block** (canonicalize / canonical_text / canonical_bytes / sha256 / capture_environment / wrapper) matching
the N64 canonical contract byte-for-byte. It does **not** import `run_n64_falsifier_v0_1`. Rationale: N64 is
frozen validation evidence and its evaluation path is gated; JSON canonicalization is transport, not
descriptor mathematics, so a local copy does not breach "no duplicated descriptor mathematics." A shared
canonicalization module is a larger refactor that would touch existing files and is **out of v0.1 scope**.

## 5. Input manifest (v0.1 boundary)

```text
sources (exactly one, never both):
  --manifest PATH   : JSON list, ordered, each entry {logical_id, path}
  positional paths  : ordered .npz paths; logical_id auto-assigned "input_%04d" by position
  manifest_source recorded as "manifest_json" | "positional_paths"
ordering            : manifest order is authoritative; it sets clip ordinals (which drive seed derivation)
npz hashing         : npz_sha256 = sha256 of the raw .npz file bytes (transport hash, not a descriptor hash)
```

Exact validation rules (each failure surfaced, never silent):

```text
empty input list                       -> manifest_empty
logical_id regex ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$
  invalid                              -> manifest_invalid_logical_id
duplicate logical_id                   -> manifest_duplicate_logical_id
duplicate path identity, compared as
  os.path.normcase(os.path.realpath(os.path.abspath(path)))
                                       -> manifest_duplicate_path
extension not case-insensitive .npz    -> manifest_wrong_extension
path is a directory                    -> manifest_path_is_directory
missing or unreadable / not a regular readable file
                                       -> manifest_missing_input
identical file content under distinct normalized paths (allowed) -> warning manifest_duplicate_content
```

Manifest-source and JSON-schema failures (exact; validation, not argparse mutual-exclusion, produces the
canonical invalid payload):

```text
both --manifest and positional paths supplied                 -> manifest_source_conflict
manifest file unreadable or JSON parsing fails                -> manifest_parse_failed
manifest JSON top level is not a list                         -> manifest_schema_invalid
manifest entry not an object / not exactly {logical_id, path} /
  either value not a string / any unknown or additional key   -> manifest_schema_invalid
neither source supplies any input entry                       -> manifest_empty
```

```text
manifest_source_conflict OR manifest_parse_failed:
  no descriptor analysis ; input_manifest.entries = [] ;
  input_manifest_sha256 = null ; input_path_identity_sha256 = null ; paired_analysis = {}

manifest_schema_invalid:
  preserve every structurally readable entry in order where possible ;
  invalid/unreadable entries are NOT silently removed ;
  input_manifest_sha256 = null ; paired_analysis = {}
```

Unknown CLI options and malformed CLI syntax may remain ordinary argparse errors before payload construction.

```text
no directory crawling in v0.1 (explicitly not selected); only explicit file entries are accepted.
an existing regular readable file is required per entry; no input is ever silently removed.

path treatment / canonical placement:
  top-level input_manifest entries are PATH-FREE : { logical_id, npz_sha256 }
  input_manifest_sha256 = SHA256(canonical bytes of the ordered path-free manifest entries)
  operator path strings appear in canonical output ONLY inside the preserved paired_analysis subtree
    (clips[].clip_name = basename, clips[].source = path); these are NOT sanitized, redacted, or rewritten.
```

On any manifest-validation failure the harness runs **no** descriptor analysis and emits a canonical payload
that retains all top-level keys with:

```text
paired_analysis = {}
error_codes      = [ ... the exact codes above ... ]
```

Entries that cannot be hashed retain their logical id and use:

```text
npz_sha256            = null
input_manifest_sha256 = null
```

## 6. Analyzer invocation, anti-drift, and failure behavior

```text
call once (wrapped):  paired_analysis = paired.analyze_paths(ordered_paths,
                                                             include_sag=True, with_companion=True)
embed:                payload["paired_analysis"] = paired_analysis     (verbatim, unaltered)
```

`with_companion=True` and `include_sag=True` are fixed for the operational report (companion is first-class;
SAG is C-style non-gating anatomy). The embedded subtree preserves **all** clips, controls, blocks,
descriptors, starts, per-start/per-block records, normalization diagnostics, control ranks, recursive-delta,
SAG, `finite_summary`, `locks`, and `non_claims` exactly as `analyze_paths` returns them, including its
existing `None`/`null` values. Anti-drift is enforced by the single real integration test (§11).

Analyzer failure behavior — the single `analyze_paths(...)` call is wrapped:

```text
on analyzer exception:
  analysis_completed_valid = False
  error_codes includes analysis_failed
  paired_analysis          = {}
  analysis_error           = { exception_class: "<exact exception class name>" }
  no exception message or traceback enters the canonical payload or stderr in v0.1
  no partial clip subtree is emitted
```

This is an engineering failure, not a scientific outcome.

## 7. Boundary-neutral companion reuse

The companion is reused **only** as the existing per-clip `boundary_neutral_companion` subtree already nested
inside `paired_analysis`; it is a **companion subtree, not a replacement result**. Its exact response objects
(`companion_response_psi_trs`, `companion_response_psi_trs_k0`, `companion_recursive_delta`,
`raw_minus_companion_*`) are preserved unchanged. κ differences (`companion_recursive_delta`) are reported
under the module's existing `RECURSIVE_DELTA_STANDING` / `NON_CLAIM` wording and are **not** reinterpreted as
mechanism contributions.

## 8. Operational envelope

Canonical payload (single object; keys sorted at serialization):

```text
schema        = { "name": "torment_brainvision_prerecorded_operational_harness", "version": "0.1" }
authority     = { ... exactly the frozen authority object below ... }
source        = { source_commit, harness_name, harness_version, analyzer_module_name, analyzer_version }
environment   = capture_environment()   (python + numpy version + numpy build-config sha + canonicalization version)
configuration = { ... exactly the frozen object below ... }
input_manifest= { entries:[{logical_id, npz_sha256}], input_manifest_sha256, warnings:[...] }
paired_analysis = analyze_paths(...) output   (raw B subtree; companion nested within; path-bearing; verbatim)
analysis_error  = { exception_class }   (null on healthy runs; exact exception class name on analyzer failure)
harness_health  = { ... exactly the object below ... }
warnings        = [ ... human-facing interpretation-boundary and manifest warnings ... ]
replay          = { source_commit, configuration_sha256, environment_fingerprint_sha256,
                    input_manifest_sha256, input_path_identity_sha256,
                    canonicalization_name, canonicalization_version }

wrapper = { "payload": payload, "payload_sha256": canonical_sequence_sha256(payload) }
```

The canonical payload always contains **exactly these eleven top-level objects**, and no top-level object is
omitted on invalid runs:

```text
schema  authority  source  environment  configuration  input_manifest
paired_analysis  analysis_error  harness_health  warnings  replay
```

**Frozen authority object (used exactly).** `documentation_authorized` and `implementation_authorized`
describe repository workflow, not emitted-analysis standing, and are **not** placed in the payload:

```text
authority = {
  FORMAL_HOLD_active: true,
  Mode_0_active: true,
  verdict: "HOLD",
  output_type: "OFFLINE_DESCRIPTIVE_ENGINEERING_DIAGNOSTICS",
  scientific_claim_authorized: false,
  temporal_order_claim_authorized: false,
  perception_or_vision_claim_authorized: false,
  runtime_integration_authorized: false,
  production_kernel_modification_authorized: false
}
```

**Analysis-error object (used exactly).** Present in every payload:

```text
analysis_error = { exception_class: null }                            (healthy run)
analysis_error = { exception_class: "<exact exception class name>" }  (analyzer exception)
```

No exception message or traceback ever enters the canonical payload.

**Source identity (required).** `--source-commit` is required and must match `^[0-9a-f]{40}$`. Otherwise the
harness emits a canonical **invalid payload** with `error_codes` including `source_commit_invalid` and runs
**no** descriptor analysis (`paired_analysis = {}`).

**Frozen configuration object (used exactly):**

```text
configuration = {
  include_sag: true,
  with_companion: true,
  global_seed: GLOBAL_SEED,
  block_len: BLOCK_LEN,
  epsilon: EPSILON,
  near_epsilon_threshold: NEAR_EPSILON_THRESHOLD,
  controls: list(CONTROLS),
  descriptors: list(DESCRIPTOR_NAMES),
  companion_descriptor_domain: list(D_COMPANION),
  companion_offset_policy: COMPANION_OFFSET_POLICY,
  companion_aggregation_policy: COMPANION_AGGREGATION_POLICY,
  canonicalization_name: "torment_brainvision_operational_canonical_json",   (fixed harness value)
  canonicalization_version: "0.1",
  analyzer_nonfinite_policy: "ANALYZER_JSONABLE_NONFINITE_TO_NULL",
  manifest_source: "manifest_json" | "positional_paths"
}

configuration_sha256 = SHA256(canonical bytes of exactly this configuration object)
```

**Non-finite policy.** `analyze_paths(...)` already returns `_jsonable(build_result(...))`, and `_jsonable`
converts every non-finite float to `None`; the origin (NaN, +Infinity, or -Infinity) is not recoverable.

```text
analyzer_nonfinite_policy = ANALYZER_JSONABLE_NONFINITE_TO_NULL

The paired_analysis subtree is embedded exactly as analyze_paths returns it.
Existing None/null values are preserved unchanged.
The harness canonicalizer permits None as JSON null while rejecting any new bare non-finite numeric value
introduced outside the reused subtree.
No reversibility claim is made.
```

**Runtime health object (used exactly):**

```text
harness_health = {
  manifest_valid,
  inputs_readable_valid,
  analyzer_identity_valid,
  analysis_completed_valid,
  clip_count_valid,
  serialization_valid,
  replay_material_valid,
  overall_health,
  error_codes,
  warnings
}
```

`overall_health` is the logical AND of the seven booleans listed above it. It is engineering-only and has no
scientific meaning; `overall_health = false` means only that the run's mechanics were not clean.
`analyzer_identity_valid` requires the returned subtree to contain the expected `SCHEMA`, `ANALYZER_NAME`, and
`ANALYZER_VERSION`. `clip_count_valid` requires exactly one analyzer clip result per ordered manifest entry.
When descriptor analysis does not run (invalid manifest, `source_commit_invalid`, or analyzer failure), the
analysis-dependent booleans (`analyzer_identity_valid`, `analysis_completed_valid`, `clip_count_valid`) are
`false`.

**Path-independence and replay semantics (explicit):**

```text
input_manifest_sha256 is path-independent
paired_analysis is path-bearing because it is preserved verbatim (clip_name/source retained)
the complete canonical wrapper is therefore path-sensitive
same-environment byte replay requires identical ordered supplied path strings

input_path_identity_sha256 = SHA256(canonical bytes of the ordered exact operator-supplied path strings)
  -> replay identity only; NOT a descriptor or content hash
```

## 9. Required reporting (all from existing payload fields; nothing recomputed)

```text
per-clip raw descriptor profiles      <- paired_analysis.clips[].descriptor_responses
all existing control profiles         <- CONTROLS (true, time_reversed, time_shuffled, circular_shift,
                                         channel_shuffle, descriptor_dropout) as already present
block-stability diagnostics           <- per_block / median / iqr already in descriptor_responses
fixed vs aggregate comparisons        <- boundary_neutral_companion raw (fixed start 0) vs companion (all-start)
                                         + raw_minus_companion_* (only where already available)
kappa companion differences           <- boundary_neutral_companion.companion_recursive_delta
feature / anatomy diagnostics         <- clips[].sag and response_normalization_diagnostics ONLY
                                         (re-presented; never recomputed, never re-selected)
warnings + interpretation boundaries  <- locks, non_claims, RECURSIVE_DELTA_STANDING, harness warnings
```

The concise human report is rendered **only from canonical payload fields** (including the path-bearing
`clip_name`/`source` already present in `paired_analysis`) and cannot write back into the payload. No new
number, ratio, ranking, normalization, or selection is introduced by reporting.

## 10. Transport (replay, stdout, stderr)

One CLI flag is added: `--human-summary`.

```text
stdout/stderr:
  default:              stdout = canonical wrapper only, no trailing newline ; stderr = empty on a healthy run
  with --human-summary: stdout = canonical wrapper only ; stderr = deterministic human report derived only
                        from canonical payload fields
  analyzer or validation failure: canonical INVALID wrapper is still written to stdout ; stderr remains empty
                        unless --human-summary was supplied ; no traceback or exception message in v0.1

process exit codes:
  0 = canonical payload emitted and overall_health is true
  1 = canonical invalid payload emitted and overall_health is false
  2 = argparse-level CLI syntax failure before payload construction

replay = exact same-environment byte replay: two runs with identical ordered supplied path strings ->
         byte-identical wrapper, equal payload_sha256 ; stderr is non-canonical and never affects the payload
archival = operator shell redirection of stdout is the only archival-output mechanism
```

There is no canonical file-output option and no other file-writing mode in v0.1.

## 11. Tests (tests/research/test_brainvision_prerecorded_operational_harness_v0_1.py)

Efficiency: most manifest, hashing, canonicalization, error, health, and CLI tests **monkeypatch
`paired.analyze_paths` with a deterministic native dictionary**. Exactly one focused real integration test
uses one small temporary `.npz` input.

```text
no torment_service import or invocation ; protected production paths untouched ; no writes by default
tests follow the existing BV_DIR / sys.path import convention

real integration test (one small temp .npz, test-local, cleaned up):
  payload["paired_analysis"] == paired.analyze_paths(same ordered paths, include_sag=True, with_companion=True)
  companion subtree remains unchanged

monkeypatched tests:
  deterministic ordered-manifest behavior (order fixes clip ordinals -> stable output)
  input_manifest_sha256, configuration_sha256, input_path_identity_sha256 present and stable across builds
  byte-identical same-environment replay (identical ordered path strings -> identical canonical bytes)
  analyzer null preservation: analyze_paths' existing null values are preserved exactly in canonical output
  canonical finite-only: canonical output contains no bare NaN or Infinity token (no non-finite sentinel used)
  complete clip/control/block granularity present (all CONTROLS, all blocks, both companion descriptors)
  harness_health has exactly the ten keys; overall_health == AND of the seven booleans
  analyzer_identity_valid checks SCHEMA/ANALYZER_NAME/ANALYZER_VERSION ; clip_count_valid = 1 clip per entry
  manifest cases -> exact codes: manifest_empty, manifest_invalid_logical_id, manifest_duplicate_logical_id,
    manifest_duplicate_path, manifest_wrong_extension, manifest_path_is_directory, manifest_missing_input,
    plus warning manifest_duplicate_content ; invalid manifest keeps all top-level keys with paired_analysis={}
  unhashable entry -> npz_sha256=null and input_manifest_sha256=null ; no input silently removed
  source_commit not matching ^[0-9a-f]{40}$ -> source_commit_invalid and no descriptor analysis
  analyzer exception -> analysis_failed, analysis_completed_valid False, paired_analysis={},
    analysis_error.exception_class = exact class name, no message/traceback in payload or stderr
  payload always has exactly the eleven top-level objects (incl. analysis_error) on healthy and invalid runs
  authority equals the exact frozen object (output_type present; no documentation/implementation authority keys)
  analysis_error.exception_class is null on healthy runs
  manifest source/schema codes: manifest_source_conflict, manifest_parse_failed, manifest_schema_invalid
  --human-summary: stderr empty by default; deterministic human report (from payload only) when supplied
  process exit codes: 0 healthy+overall_health true ; 1 invalid+overall_health false ; 2 argparse CLI syntax
  human summary is derived from, and cannot alter, the canonical payload
  harness defines no descriptor mathematics (descriptor symbols are used via paired.*, not redefined)
```

**Claim-lock test method.** Do **not** grep serialized text for words such as `classification`, `vision`,
`perception`, `temporal_order`, `recursive` — the reused analyzer intentionally contains those words in its
negative locks and non-claim statements. Instead, recursively collect dictionary keys and reject an exact
predeclared set of positive-outcome keys:

```text
success, scientific_success, separation_detected, higher_order_detected, classification_result, accuracy,
p_value, significance, mechanism_confirmed, recursive_confirmed, production_ready, vision_detected,
perception_detected
```

Negative authority fields (e.g. `perception_claim_authorized = false`) and text explaining prohibited claims
remain required and allowed. Additionally, assert `payload["authority"]` equals the exact frozen authority
object of §8 (correct keys, `output_type` present, no `documentation_authorized` / `implementation_authorized`).

## 12. Claim locks

```text
output self-identifies as OFFLINE DESCRIPTIVE ENGINEERING DIAGNOSTICS (schema + authority + locks)
prohibited (must not appear as positive claims or outcome keys): perception ; vision ; temporal-order proof ;
  arrow-of-time ; causality ; classification ; statistical significance ; recursive-mechanism validation ;
  production-readiness
stable, byte-identical output is NOT scientific validation; determinism is an engineering property only
the existing analyzer locks (LOCKS, NON_CLAIM, *_authorized=False) are carried through verbatim
```

## 13. Separate validation lane (A)

An independent **descriptor-blind witness family** remains a **future validation stream**. It does **not**
block harness implementation. The harness must **not** select, rank, generate, or evaluate witnesses, and it
performs no A/B homometric evaluation. **N64 remains frozen evidence** and is neither imported nor invoked by
the harness. Any coupling of the operational lane to the validation lane is out of scope for v0.1.

## 14. Decided forks and disposition

Implementation-critical forks decided in this spec: canonicalization ownership (local copy, §4); single
manifest source with the exact validation rules and codes (§5); `with_companion` / `include_sag` fixed true
(§6); analyzer failure wrapped to `analysis_failed` with `paired_analysis = {}` (§6); required
`--source-commit` matching `^[0-9a-f]{40}$` (§8); frozen `configuration` object and `configuration_sha256`
(§8); `analyzer_nonfinite_policy = ANALYZER_JSONABLE_NONFINITE_TO_NULL`, no reversibility claim (§8); exact
ten-key `harness_health` with `overall_health = AND(seven)` (§8); path-sensitive wrapper with
`input_path_identity_sha256` for replay identity, no path sanitization (§8); stdout-only transport with no
file-writing mode (§10); key-based claim-lock testing (§11); frozen runtime `authority` object with
`output_type` and no workflow-authority keys (§8); always-present `analysis_error` object (§8);
`--human-summary` flag with exit codes 0/1/2 (§10); manifest source-conflict / parse / schema failure codes (§5).

```text
unresolved_blockers               = NONE
implementation_authorized         = False (pending final review)
implementation_ready_after_review = True
```

```text
scope excluded from v0.1: dashboards, databases, live capture, service endpoints, UI, plugin integration,
production wiring, directory crawling, any new descriptor or response formula, any file-writing mode.
```

*End — TORMENT Brainvision Prerecorded Operational Harness Implementation Specification v0.1. Docs-only,
non-authorizing, non-implementing. Existing analyzer, companion, descriptor, and N64 modules are unmodified
and authoritative for method semantics; `psi_trs.py` and the production TORMENT memory kernel are immutable.
No `§0` pointer; no registry or orientation update; no tags.*
