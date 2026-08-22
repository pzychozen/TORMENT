# TORMENT Brainvision Phase 13 — Corrected Formal Administration Result v1.0

## Status

FINAL HISTORICAL RESULT — Phase 13 v1a is closed.

The corrected Phase-13 v1a formal qualification passed. `BRAINVISION_V1A` is
`QUALIFIED`, and `MANDATORY_HOLD` is `ACTIVE`.

## Corrected-administration authority

- Corrected instrument HEAD: `df23203e4f261d2c29b429a945bac2ec61a40aef`
- Corrected instrument inventory SHA-256:
  `6e26ea5ebc81b9d07cd1d494a5f745321e15b894c93a4b0ca7fa0926c271d800`
- Corrected administration ID:
  `bvphase13a1_1ec041f293995c9f911e315fdae37fc9ffc044c8ac29eb5cf9b3c35d1f46e09d`
- Authorization artifact:
  `C:\TORMENT\phase13_corrected_formal_authorization\formal_authorization_manifest.json`
- Authorization schema: `brainvision.phase13.formal_authorization.v2`
- Authorization SHA-256:
  `b3246ddc756fe62bf3e4954f2ab916a55824dec2285ce8fabf89f20230fb017d`
- Evidence root:
  `C:\TORMENT\phase13_corrected_formal_administration\evidence`

The external authorization artifact canonically bound the corrected inventory,
the frozen Phase-13 specification and bindings, the corrected-amendment
provenance included by that inventory, the authorization path, and the
separate evidence destination.

## Exact formal command

```cmd
call conda activate torment && cd /d C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric && python tests/brainvision_phase13/run_qualification.py --authorization-file C:\TORMENT\phase13_corrected_formal_authorization\formal_authorization_manifest.json --expected-head df23203e4f261d2c29b429a945bac2ec61a40aef --output-dir C:\TORMENT\phase13_corrected_formal_administration\evidence --formal-first-administration --formal-authorization-token phase13-corrected-v1a-45-arm-one-shot --administration-id bvphase13a1_1ec041f293995c9f911e315fdae37fc9ffc044c8ac29eb5cf9b3c35d1f46e09d
```

The command ran once. It recorded `administration_started`, consumed the new
administration identity, and generated the evidence package below. No formal
rerun occurred.

## Frozen result

| Measure | Recorded result |
| --- | --- |
| Formal arms | 45 / 45 administered |
| Backend block dispatches | 12 / 12 (`E1`–`E12`) |
| Primary criteria | 81 / 81 PASS |
| Evidence obligations | 147 / 147 PASS |
| Total criteria and obligations | 228 / 228 PASS |
| Final disposition | PASS |
| Frozen taxonomy | `V1A_QUALIFICATION_PASS` |
| Brainvision v1a | `BRAINVISION_V1A: QUALIFIED` |
| Mandatory hold | `MANDATORY_HOLD: ACTIVE` |

The corrected external formal result document is
`C:\TORMENT\phase13_corrected_formal_administration\evidence\formal_result.md`
with SHA-256
`a584e3e82099ddd2370fded71568106ef82caeaf63af019e9ad4a084265cff1d`.

## Evidence provenance

The external evidence is preserved in place and is not copied into Git by this
result record. Its top-level file hashes are:

| Artifact | SHA-256 |
| --- | --- |
| `administration_started.json` | `33cdd141ae352ed11383d182aad8f3183cb4b8d03070497b8d6afa2f5d59e8dc` |
| `environment_preflight_record.json` | `e8a66df75fe4448ef12ba22f8077f31abe240fa4056dbcf69cd607ead8a6a0a1` |
| `identity_binding_record.json` | `0debd7999e158e2b8960ea4f17d37f08cce0bfb815fd9261f7b1e5b61158a679` |
| `operation_journal.ndjson` | `4f1249d89d6320d92ca133db06930e0ba5d68212d0c0600fc6365a2490296d2e` |
| `evidence_package.json` | `88a055ce254f98ca5ac772a0905b04d51307b81c66b18dc935f51a4aa067ee54` |
| `grading_record.json` | `283bc1eb94d4fb1d848b18982aa886d92275089192f26851a0d214287692c832` |
| `formal_result.md` | `a584e3e82099ddd2370fded71568106ef82caeaf63af019e9ad4a084265cff1d` |
| `evidence_package_index.json` | `23f9f8fec9c3dedc0b54fc7ccbaa9cc9cac626b98ca212afc898515bd6aa670a` |

No production/runtime or qualification-instrument file changed during the
corrected administration: both change counts were zero.

## Historical-result boundary

The antecedent history is retained exactly:

1. The first administration remains permanent `FAIL / NOT_QUALIFIED`.
2. The corrected administration is `PASS / QUALIFIED`.

The corrected PASS does not erase, replace, supersede, or re-grade the first
FAIL or its external evidence.

## Closure and mandatory hold

Phase 13 is closed. `MANDATORY_HOLD: ACTIVE` remains in force. Nothing in this
PASS authorizes Phase 14 or integration with a model, memory, `CognitiveCore`,
SRG, Hivermind, Spine, prompts, or ordinary Fabric ingest. No future work in
those areas is authorized by this result record.
