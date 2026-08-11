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

## Release Scope

This release updates the current public release identity from 2.4.7 to 2.5.0 and refreshes the security communication around GHSA-9j44-4v2c-3hp2. No memory behavior or security architecture changes are introduced by this release hygiene update.
