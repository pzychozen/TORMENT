# TORMENT F5 filesystem residual-risk acceptance v0.1

## Decision

F5-A fixed deterministic static junction defects in REST archive ingestion,
`ProposalRegistry` sink derivation, and Trajectory V2 discovery.  F5-B adds
bounded Level-2 identity-continuity detection to checkpoint write/pruning and
persisted-job sweep paths.

The Level-2 token is the canonical physical directory path plus `st_dev` and
`st_ino`.  Before a checkpoint write, checkpoint prune victim, or persisted-job
deletion, the code re-establishes physical containment and compares the
captured root/parent identities.  A mismatch fails closed, records the stable
`filesystem_containment_substitution` security incident, and discards the
cached identity so a later normal operation can rederive it after restoration.

This is **identity continuity detection**, not handle pinning and not a claim
of race-free filesystem access.  A same-user actor can still replace a path
after the final check and before the operating-system sink.

## Deployment acceptance

Current disposition: **ACCEPT_LOCAL_RACE**.  Severity is **LOW** only for the
current loopback, single-operator deployment in which TORMENT and anyone able
to alter its data directory run under the same OS principal.  That actor
already has direct read/write authority over TORMENT's persistent state.

This decision makes no remote-path-traversal claim and does not treat the
residual local race as fixed.

The acceptance expires immediately if TORMENT runs as a service, under a
different account than the interactive/local user, elevated, or with any
privilege asymmetry between TORMENT and a user who can modify its data
directory.  In those deployments, Level-3 pinned-handle containment is
mandatory before the affected destructive paths are used.

## Observability boundary

The existing incident log is a Spine-decision ring buffer and may optionally
append to a separately configured file.  Low-level filesystem guards do not
call it, avoiding a new persistence/recursion hazard.  They instead emit a
stable error-level security incident; persisted-job sweep additionally retains
a process-local structured incident record.  Neither record includes path
contents, API keys, or raw attacker-controlled exception text.
