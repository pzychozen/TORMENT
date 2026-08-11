# Security Policy

## Supported Versions

Only the current supported release line receives routine security updates.

| Version / tag | Status |
| --- | --- |
| 2.5.x | Current supported release line |
| v2.4.7-security | Historical first security-fixed marker for GHSA-9j44-4v2c-3hp2; not the current feature/support line |
| v2.1.1 through v2.4.6-proof-slice-complete | Unsupported and mechanically verified affected by GHSA-9j44-4v2c-3hp2 |
| Older unverified versions | Unsupported; not included in the mechanically verified affected range above |

Older unsupported versions may contain known issues and may not receive fixes.

## GHSA-9j44-4v2c-3hp2

GHSA-9j44-4v2c-3hp2 was reported on July 8, 2026.

- Severity: HIGH. Do not describe this advisory as Critical unless the advisory is formally rescored.
- CWE: CWE-306, Missing Authentication for Critical Function.
- Affected behavior: five archive REST operations could bypass configured API-key authentication while `TORMENT_AUTH_ENABLE=1`.
- Affected operations: archive document ingest, archive query, archive document list, archive document read, and archive document delete.
- Mechanically verified affected tagged releases: `v2.1.1`, `v2.2.0`, `v2.3.0`, `v2.4.0`, `v2.4.2`, `v2.4.3`, `v2.4.4`, `v2.4.5`, and `v2.4.6-proof-slice-complete`.
- Fix commit: `b76a1594cb968d99291f94aa8e1a8b54c9f00cd9` (`fix(security): require auth on archive REST endpoints`).
- First fixed tag: `v2.4.7-security`.
- Current fixed release: `v2.5.0`.

Users running any affected release should upgrade to `v2.5.0`. If you cannot upgrade immediately, move at least to `v2.4.7-security` and plan a full upgrade to the current supported line. `v2.4.7-security` is the first marker for the originally disclosed archive endpoint fix; `v2.5.0` is the first release intended to enforce the configured REST authentication boundary consistently across sensitive REST surfaces.

TORMENT is commonly deployed as a local or controlled HTTP service. That deployment context does not change the severity or validity of an authentication bypass when authentication is configured.

## 2026-08-11 Pre-release REST Auth Surface Audit

During final review of the unpushed v2.5.0 release, maintainers found that handler-local authentication enforcement left additional sensitive REST routes unauthenticated when `TORMENT_AUTH_ENABLE=1`. This was broader than the original GHSA disclosure, which specifically covered five `/archive/*` handlers.

The pre-release audit inventoried 93 FastAPI route declarations in `torment_service/app.py`:

- 2 routes were classified `PUBLIC_SAFE`.
- 61 routes were classified `AUTH_REQUIRED_READ`.
- 30 routes were classified `AUTH_REQUIRED_WRITE`.

The repair for v2.5.0 adds a default-deny REST authentication middleware when `TORMENT_AUTH_ENABLE=1`, with a tiny explicit public-safe allowlist. Existing per-handler `resolve_request_context` calls remain in place where endpoints need workspace/agent-specific `RequestContext` values for Spine trust checks.

Current v2.5.0 intent: every externally exposed REST endpoint that reads private TORMENT memory/state or mutates TORMENT state requires a valid API key when REST auth is enabled. When `TORMENT_AUTH_ENABLE=0`, existing local/no-auth behavior is preserved.

Audit record: `docs/TORMENT_REST_AUTH_SURFACE_AUDIT_2026_08_11.md`.

## Reporting a Vulnerability

If you believe you have found a security vulnerability in TORMENT, please report it responsibly.

Please **do not open a public GitHub issue** for suspected security vulnerabilities.

Instead, email: **[pzychozen@gmail.com](mailto:pzychozen@gmail.com)**

Please include as much of the following as possible:

- a clear description of the issue
- steps to reproduce it
- affected version / commit / branch
- whether the issue is local-only or exposed over a network
- proof-of-concept, request sample, or test case if available
- relevant logs or configuration details, with secrets redacted

## What to Expect

- acknowledgment within **72 hours** when possible
- triage and validation for credible reports
- a fix, mitigation, or decision note for confirmed issues
- credit in release notes if a fix is shipped, unless you prefer to remain anonymous

Response times may vary depending on severity, complexity, and maintainer availability.

## Scope

TORMENT primarily runs as a local HTTP service on **127.0.0.1:8787** by default.

Security concerns may include:

- unauthorized access to memory data, workspace state, or agent state
- path traversal, path injection, or unsafe filesystem access
- unintended data exposure through API endpoints
- unsafe handling of archive, deep memory, checkpoint, or embedding storage
- vulnerabilities involving promotion, compression, or collective-memory flows
- issues involving authentication, authorization, or trust boundaries
- issues involving embedding providers or external service calls

## Out of Scope

The following are generally out of scope unless they directly cause a security impact in TORMENT itself:

- feature requests
- performance-only issues
- crashes without security impact
- issues only affecting unsupported versions
- insecure deployments that intentionally expose TORMENT to public networks without additional hardening
- vulnerabilities in third-party software or local system configuration unless TORMENT introduces or worsens the risk

## Deployment Notice

TORMENT is designed primarily for local or otherwise controlled environments.

If you choose to expose TORMENT on a public or untrusted network, you are responsible for additional safeguards such as:

- reverse proxy hardening
- authentication and access control
- firewall / network restrictions
- TLS / transport protection
- host-level isolation and monitoring

## Disclosure

Please allow reasonable time for validation and mitigation before public disclosure.

Reports that are incomplete, non-reproducible, abusive, or clearly automated spam may be closed without action.
