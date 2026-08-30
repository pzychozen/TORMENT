# TORMENT Memory Substrate — Phase 7G5A3B Native Motif Runtime Read / Geometry v0.1

## Scope

Starting commit: `b6c40522b23c84032a7535369f7a0d572827874f`.

This read-only qualification slice adds `NativeMotifRuntimeReader` for live
native `DERIVED_MOTIF` objects. It accepts an already-open qualified STAGING
connection and creates no operations, transitions, revisions, representations,
measurements, reconciliation records, or authority state.

## Ordering and membership

Catalog reads require an explicit motif alias namespace, domain, and semantic
scope. Restart order is ordinary Python lexicographic ordering of scoped
`MOTIF_ID` alias values. Every live `DERIVED_MOTIF` in that semantic scope must
have exactly one matching alias in the supplied namespace; disagreement or a
missing alias refuses the read. No persistent motif ordinal is introduced. A
future write phase may append newly created motifs to a process-local catalog,
but this reader does not create motifs or maintain such a catalog.

Membership remains relationship-backed truth. For live runtime motifs, member
append order is recovered from the current membership relationship revision's
effect transition and that transition's motif object-revision effect ordinal.
The reader fails closed if the evidence is missing or ambiguous. This contract
does not apply to `LEGACY_DERIVED_MOTIF` migration evidence.

## Geometry

Current geometry follows:

```text
memory identity → current revision → qualified current COMPAT_EMBEDDING
→ current qualified raw float32 embedding → legacy-compatible motif _unit()
→ shared radius calculation
```

The exact lane is `COMPAT_EMBEDDING/1`, `compat-embedding-v1`, `RAW_VECTOR`,
`float32`, and caller-supplied dimension. It requires current-source binding,
READY/USABLE state, one integrity expectation, selected MATCH measurement, and
no non-usable current reconciliation state. Zero vectors are returned raw; no
normalization is performed by the representation reader. The native radius
caller separately applies the existing motif `_unit()` semantics before passing
each qualified raw vector to the shared radius calculation.

A member without current qualified geometry remains a member and contributes to
member count, but is absent from the radius sample. Native coherence rows use
the integer count for `members`, which `compute_coherence_field()` already
supports without exposing UUIDs or fabricated EIDs.

The common mathematical function now serves legacy and native radius callers.
Legacy member lookup itself remains unchanged. In particular, its domain
registry uses shared-graph EID resolution for private ingest too: this is a
**PRE-EXISTING LEGACY GEOMETRY-RESOLUTION AMBIGUITY**. Native UUID-bound member
identity resolution intentionally does not reproduce graph-local EID ambiguity.
Thus radius mathematics are parity-preserved while member resolution is a
native structural correction; no live legacy behavior changes here.

## Deferrals

Fabric routing, DomainRouter routing, Character routing, write composition,
runtime motif-ID allocation, binding expansion, native split, native merge,
migration conversion, dual read/write, activation, and cutover remain deferred.
The legacy runtime remains authoritative.
