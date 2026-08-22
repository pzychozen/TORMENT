# TORMENT Brainvision Phase-13 Instrument Amendment 1: External Formal Authorization Artifact

## Status

PRE-FREEZE PHASE-13 INSTRUMENT AMENDMENT 1

## Scope and discovery

This amendment applies to the frozen Phase-13 qualification instrument commit
`51d13a36c4b952ed27f9efaaa53834f38472d490`. It was discovered before any
formal administration: `FORMAL_E1_E12_ADMINISTRATION_RUNS` remains `0`.

The frozen runner required an untracked in-repository authorization artifact
while its frozen preflight required `git status --porcelain` to be empty. Those
requirements cannot both hold. This amendment changes only authorization-file
placement and input wiring. It changes no scientific authority, E1-E12 arm,
fixture, sequence, clock value, expected result, evidence obligation,
taxonomy, or claim ceiling.

## External authorization input

Formal mode requires exactly one explicit input:

```text
--authorization-file <absolute-path>
```

There is no implicit default, fallback, alias, or accepted in-repository
authorization path. The resolved authorization file must be outside the
authoritative Git repository root. The formal-first-administration location is
reserved as:

```text
C:\TORMENT\phase13_formal_authorization\formal_authorization_manifest.json
```

This is administrative authorization data, not instrument content. It is not
part of the instrument inventory and must not be committed. No `.gitignore`,
`git/info/exclude`, `assume-unchanged`, `skip-worktree`, temporary staging,
temporary commit, hidden-worktree, or Git-status-filtering workaround is
authorized.

## Read-once and provenance rule

Before an administration start, the runner resolves the external absolute
path, reads the file once, validates the unchanged strict
`brainvision.phase13.formal_authorization.v2` schema, requires canonical JSON
bytes, and binds the resulting SHA-256. The dispatcher receives only that
immutable loaded artifact and does not reread the file after start.

Identity and preflight evidence record:

- `authorization_artifact_path`
- `authorization_artifact_sha256`
- `authorization_schema_id`

The evidence-package index records the same external authorization binding.
The path is administrative provenance only; it is not scientific evidence.

## Command and administration identity

The existing administration-ID builder remains unchanged. Its existing
`command_identity` input is now required to equal canonical ASCII JSON with
schema `brainvision.phase13.formal_command_identity.v1`. Its fixed argument
order is:

```text
python
tests/brainvision_phase13/run_qualification.py
--authorization-file <normalized-external-path>
--expected-head <expected-head>
--output-dir <normalized-output-path>
--formal-first-administration
--formal-authorization-token <token>
```

The self-derived `--administration-id` is deliberately excluded from this
pre-derivation representation. The external authorization-file path is
therefore bound deterministically without making the administration identity
self-referential. The authorization artifact SHA-256 is recorded in evidence
but is not an administration-ID input because the artifact itself contains the
administration ID.

## Clean-worktree and output rules

The Git preflight remains exactly strict: `git status --porcelain` must be
empty. The external authorization file has no effect on repository cleanliness.
The separately reserved formal evidence target is:

```text
C:\TORMENT\phase13_formal_first_administration\evidence
```

It is external, deterministic, and must be absent/fresh before formal
administration. Neither reserved external path is created by this amendment.

## Preserved boundaries

Formal execution still refuses before start when the authorization-file
argument is absent, missing, inside the repository, noncanonical, schema
invalid, or inconsistent with CLI token, expected HEAD, canonical command
identity, inventory, or canonical administration identity. Such refusal
dispatches no backend arm, consumes no administration identity, creates no
`administration_started.json`, and emits no formal taxonomy result.

This amendment authorizes no administration. Production/runtime code remains
unchanged. The frozen Phase-13 specification and bindings remain unchanged.
