# TORMENT Memory Substrate 7G5D1G — Core formal executor

Status: experiment-local executor glue only. This phase does not administer
formal D1.

`formal_core_executor.py` loads only the frozen `CORE_ONLY` concrete fixture,
requires its exact protocol, fixture, and tolerance hashes, and retains the
fixture-generation witness `35b6a3101190b3a75dcd404cbbbcb20881ce2cba`.
That historical witness is distinct from the future formal-administration
HEAD, which must be supplied by a future authorization.

The executor has exactly six arms: M1, M2, M3, M4, M5, and sequential. It
refuses the Character fixture and its old lock, requires separate mutable
legacy and native roots for every arm, forwards exact frozen requests through
the injected normal HTTP legacy boundary, and forwards only storage-facing
facts to the injected qualified native STAGING boundary. Legacy selection data
is not admitted to a native request.

M5 uses its dedicated no-write path and verifies that the durable native
snapshot is unchanged. Other native failures propagate without retry or
fallback. Restart characterization and retrieval characterization are bounded
to injected arm sessions; retrieval uses the same frozen float32 query vector
on each side and never claims closed-loop query parity.

The executor returns `FormalResultSchema` only. It owns no authorization,
marker, result root, administration ID, or command-line entry point.
`FormalAdministrationRunner` remains the sole marker-first one-shot envelope.
Synthetic temporary tests cover runner success/failure sealing; they do not
contact the real frozen formal root or perform an administration.

The Character result is explicitly unadministered with
`DEFERRED_PENDING_PROVENANCE_VOCABULARY`. No production selector, native
activation, dual read/write, cutover, migration behavior, or provenance
vocabulary is changed here.
