# TORMENT F5 future shared pinned-root primitive — design only

## Status

**NO IMPLEMENTATION OF THIS LEVEL-3 PRIMITIVE IN THIS BATCH.**

F5-B uses only bounded Level-2 identity-continuity checks.  A future opt-in
primitive is required when TORMENT operates with filesystem privilege
asymmetry.

## Conceptual construction

Construction accepts a trusted base and requested root, proves canonical
physical containment, opens or otherwise pins the directory root, and records
its identity.  It must fail closed if the root is absent, reparse-redirection is
unexpected, or the final physical path lies outside the approved base.

Its conceptual public operations are:

- `open_child_for_write`
- `remove_child`
- `list_children`
- `revalidate`

Each operation keeps child-name validation and derives children relative to the
pinned root rather than by a fresh absolute-path traversal.

## Platform shape

On POSIX, use a directory file descriptor with `dir_fd` and `openat`/
`unlinkat`-style operations.

On Windows, use a `CreateFileW` directory handle with
`FILE_FLAG_BACKUP_SEMANTICS`; for destructive operations use a short-lived
handle that does not grant `FILE_SHARE_DELETE`, obtain the final physical path
via `GetFinalPathNameByHandleW`, and open reparse points deliberately rather
than following them implicitly.

## Adoption order

Adopt evidence-first in this order:

1. checkpoint prune
2. checkpoint write
3. persisted-job sweep
4. other stores only where evidence demonstrates the same need

Until then, the F5-B Level-2 checks remain bounded detection only and must not
be described as TOCTOU-safe or race-free.
