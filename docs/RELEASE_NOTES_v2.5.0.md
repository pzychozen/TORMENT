# TORMENT Memory Fabric — v2.5.0

v2.5.0 is the current supported TORMENT release line. It represents the current repository line after extensive development beyond the older `v2.4.7-security` marker, without attempting to exhaustively summarize the intervening work.

## Security

### GHSA-9j44-4v2c-3hp2

GHSA-9j44-4v2c-3hp2 was reported on July 8, 2026.

This HIGH-severity issue was an archive REST authentication bypass: five archive REST operations could bypass configured API-key authentication while `TORMENT_AUTH_ENABLE=1`.

Affected operations:

- archive document ingest
- archive query
- archive document list
- archive document read
- archive document delete

Mechanically verified affected tagged releases:

- `v2.1.1`
- `v2.2.0`
- `v2.3.0`
- `v2.4.0`
- `v2.4.2`
- `v2.4.3`
- `v2.4.4`
- `v2.4.5`
- `v2.4.6-proof-slice-complete`

The fix first landed in commit `b76a1594cb968d99291f94aa8e1a8b54c9f00cd9` (`fix(security): require auth on archive REST endpoints`) and was first marked by tag `v2.4.7-security`.

v2.5.0 contains and preserves that fix. Users running an affected release should upgrade to `v2.5.0`. If an immediate upgrade to `v2.5.0` is not possible, move at least to `v2.4.7-security` while planning the full upgrade.

Credit: EQSTLab and yym8538.

### 2026-08-11 pre-release REST auth-surface audit

During final review of the unpushed v2.5.0 release, maintainers found that the handler-local auth pattern left additional sensitive REST surfaces unauthenticated when `TORMENT_AUTH_ENABLE=1`. This finding is distinct from GHSA-9j44-4v2c-3hp2: the GHSA reporter disclosed the five archive REST endpoints listed above, not the broader route-surface issue.

The v2.5.0 pre-release audit inventoried 93 FastAPI route declarations in `torment_service/app.py` and classified them as:

- `PUBLIC_SAFE`: 2
- `AUTH_REQUIRED_READ`: 61
- `AUTH_REQUIRED_WRITE`: 30

v2.5.0 adds a default-deny REST authentication middleware when `TORMENT_AUTH_ENABLE=1`, with a tiny explicit public-safe allowlist. Existing per-handler `resolve_request_context` calls remain in place where endpoints need workspace/agent-specific RequestContext values for Spine trust checks.

v2.5.0 is the first release intended to enforce the configured REST authentication boundary consistently across sensitive REST read/write surfaces while preserving existing local/no-auth behavior when `TORMENT_AUTH_ENABLE=0`.

Audit record: `docs/TORMENT_REST_AUTH_SURFACE_AUDIT_2026_08_11.md`.

## Release Scope

This release updates the current public release identity from 2.4.7 to 2.5.0, refreshes the security communication around GHSA-9j44-4v2c-3hp2, and hardens the REST authentication boundary before publication. No memory behavior, Spine governance, trust model, or cognition architecture changes are introduced by this release.
