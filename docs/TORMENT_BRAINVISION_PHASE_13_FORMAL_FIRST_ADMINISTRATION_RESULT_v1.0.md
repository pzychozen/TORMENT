# TORMENT Brainvision Phase-13 Formal First-Administration Result v1.0

## Status

FROZEN HISTORICAL RESULT — FORMAL FIRST ADMINISTRATION

## Authority and administration identity

- Authoritative instrument HEAD: `7cc18da44c9c70a65e47829bd5ba580b56babfae`
- Administration ID: `bvphase13a1_eaf65779adc5ccc5b72fee8e34038aaf75c8c741c50964985f418d0229f8c09b`
- Authorization artifact SHA-256: `88eb5f46ad15be33f8701f5f9ef71213d2c13ebaef41474db22c70776860a1d6`
- Administration started: `YES`
- Administration identity consumed: `YES`, permanently
- Formal command execution count: `1`
- Formal rerun performed: `NO`

The exact frozen command was:

```cmd
call conda activate torment && cd /d C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric && python tests\brainvision_phase13\run_qualification.py --authorization-file C:\TORMENT\phase13_formal_authorization\formal_authorization_manifest.json --expected-head 7cc18da44c9c70a65e47829bd5ba580b56babfae --administration-id bvphase13a1_eaf65779adc5ccc5b72fee8e34038aaf75c8c741c50964985f418d0229f8c09b --output-dir C:\TORMENT\phase13_formal_first_administration\evidence --formal-first-administration --formal-authorization-token phase13-v1a-formal-first-administration
```

## Frozen disposition

```text
PHASE_13_FORMAL_FIRST_ADMINISTRATION:
FAIL

FROZEN_TAXONOMY:
V1A_QUALIFICATION_FAIL / FAIL_IMPLEMENTATION

FORMAL_ARMS_EXPECTED:
45

FORMAL_ARMS_ADMINISTERED:
45

PRIMARY_CRITERIA:
75 / 81

EVIDENCE_OBLIGATIONS:
133 / 147

TOTAL_CRITERIA_OBLIGATIONS:
208 / 228

BRAINVISION_V1A:
NOT_QUALIFIED

FORMAL_RERUN_PERFORMED:
NO
```

## Frozen non-PASS primary criteria

- `E3_contract_projection`: `INVALID / INVALID_ADMINISTRATION`
- `E6_sidecar_bytes`: `FAIL / FAIL_IMPLEMENTATION`
- `E6_receipt`: `FAIL / FAIL_IMPLEMENTATION`
- `E6_active_time`: `FAIL / FAIL_IMPLEMENTATION`
- `E10_suspended_refusal`: `FAIL / FAIL_IMPLEMENTATION`
- `E10_disabled_refusal`: `FAIL / FAIL_IMPLEMENTATION`

## Frozen non-PASS evidence obligations

- `E1_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E2_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E3_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E3_contract_seq1_projection_equal`: `INVALID / INVALID_ADMINISTRATION`
- `E3_contract_seq2_projection_equal`: `INVALID / INVALID_ADMINISTRATION`
- `E4_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E5_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E6_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E7_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E8_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E9_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E10_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E11_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`
- `E12_all_arms_projection_construction_zero`: `FAIL / FAIL_IMPLEMENTATION`

## External evidence provenance

The external raw-evidence root remains authoritative:

`C:\TORMENT\phase13_formal_first_administration\evidence`

- Formal result path: `C:\TORMENT\phase13_formal_first_administration\evidence\formal_result.md`
- Formal result SHA-256: `4bbdb642594c71d20d6bc298d59d86cdc921a14bcd02625a7a2fa62a298d21fa`
- Evidence files: `143`
- Evidence bytes: `3873238`
- Canonical evidence inventory SHA-256: `4810248844d49aee8a17dda30688d988759dab87c6639d2945de87185e9b10d2`

Top-level evidence hashes:

- `administration_started.json`: `b28dec7eb07b8d49c9c872da9c911c61286b9e02da31f764f9155ac97d2019e2`
- `environment_preflight_record.json`: `e400f2a2325026084e6258b953b8da0a2b077366cdadee9d9ef6bc12c9a5e299`
- `evidence_package.json`: `b02961b20567842e6d11eb132afc4e3dd50678af9f29e22e2458882c2e2f206f`
- `evidence_package_index.json`: `52d5fb246e97d6386824cfc3bb8515aa38d02f2e8908fac25c715c52bceaee0e`
- `formal_result.md`: `4bbdb642594c71d20d6bc298d59d86cdc921a14bcd02625a7a2fa62a298d21fa`
- `grading_record.json`: `cb51ec1f65de1611b24adfbfe5fea3ae6e08ff0cb8bbb09d848bcab463b4c0a4`
- `identity_binding_record.json`: `6add1f646c05ff7df5f1eee22775010ee94edf064387d68bbfb84dea141208d6`
- `operation_journal.ndjson`: `8f56cf4203d4b55079fd8b03d3692b750c686baef45eb6fd573d1adeb51f5f5a`

No raw evidence is copied into Git by this result record.

## Hold and boundary

No production/runtime or Phase-13 instrument change was made during the formal
administration. This result records a failure and does not authorize a rerun,
Phase 14, v1b work, or integration with any other TORMENT subsystem. Those
activities remain on hold pending read-only failure review.
