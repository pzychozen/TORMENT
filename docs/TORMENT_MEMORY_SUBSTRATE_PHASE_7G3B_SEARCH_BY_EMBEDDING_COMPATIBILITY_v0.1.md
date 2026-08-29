# TORMENT Memory Substrate — Phase 7G3B Search-by-Embedding Compatibility v0.1

## Scope

Phase 7G3B adds a native-only, read-only compatibility equivalent of the
storage/ranking portion of `MemoryGraph.search_by_embedding`. It accepts an
already-derived numeric query vector. It does not import or construct
`MemoryGraph`, call an embedder, read legacy embedding files, create a durable
vector/ANN index, change semantic state, or alter MemoryGraph/Fabric/Character
live wiring.

The boundary is `NativeMemoryCompatibilityFacade.search_by_embedding`. A caller
must supply a compatibility source namespace, vector, and explicit dimension.
The only qualified lane in this slice is frozen to the 7G2B contract:

```text
representation_class = COMPAT_EMBEDDING
generation = 1
derivation_contract_version = compat-embedding-v1
encoding_id = RAW_VECTOR
dtype = float32
dimension = caller-supplied positive integer
```

The class, generation, contract, encoding, and dtype defaults are explicit
constants, not inference from arbitrary READY representations. Other lanes,
including `LEGACY_EMBEDDING_CAPTURE`, are not searched by this API.

## Eligibility and currentness

The bounded SQL metadata scan considers only object-revision representations
whose source object is an admissible `LEGACY_CORE_NODE` and whose source revision
equals the object’s current revision. It additionally requires:

- `READY` readiness and `USABLE` operational disposition;
- one native representation integrity expectation;
- a selected current integrity measurement with result `MATCH`;
- no current non-usable reconciliation state;
- exact requested lane metadata; and
- one unique EID alias in the caller’s source namespace.

Bytes are then loaded only through `NativeRepresentationService`’s usable-payload
read boundary. The decoder verifies the frozen `float32` dtype, exact dimension,
metadata byte length, actual byte length, finite values, and nonzero candidate
norm. A bad/zero candidate is locally excluded where possible; an incompatible
byte-length/metadata shape raises an invariant failure rather than reshaping.

An R1-derived E1 remains immutable historical evidence when the object advances
to R2, but it is excluded from current compatibility search. Publishing a valid
R2-derived E2 restores eligibility. A later selected `MISMATCH` changes current
disposition to reconciliation-required and withdraws the representation from the
next search. Pending, failed/withheld, unknown/reconciliation-required, and legacy
migration-captured representations are never ordinary compatibility candidates.

## Query geometry and ranking

The query is flattened to one dimension, must be non-empty, finite, have positive
norm, and exactly match the declared lane dimension. Unlike legacy MemoryGraph,
7G3B deliberately does **not** pad or truncate mismatched dimensions. A mismatch
is a `ValueError`; this is intentional semantic tightening rather than a hidden
physical-storage compatibility workaround.

Scoring is exact deterministic cosine over the bounded SQL scan. Results use this
frozen order:

1. enumerate eligible namespace-resolvable candidates and calculate raw cosine;
2. sort raw score descending, then EID and representation ID; take `top_k`;
3. apply `min_score` to raw cosine, then canon/user/type filters;
4. apply pure half-life decay and re-sort effective score descending, then EID and
   representation ID.

`top_k` accepts an integer and retains current compatibility coercion of zero or
negative values to one. Filters deliberately occur after raw top-k selection, so
they may return fewer than `top_k` results. `min_score` is raw cosine, not decayed
score. `canon_only` reads the payload’s epistemic canon marker only; it never
creates authority. `user_id` is an exact payload filter, not authorization.

Decay is pure and never persisted: non-positive half-life, missing/invalid
`last_reinforced_ts`/`created_ts`, or a future anchor yield factor `1.0`; otherwise
the factor is `max(0.03, 2 ** (-age_days / half_life))`. 7G2A rows without a valid
wall-clock anchor therefore retain factor `1.0` and no timestamp is fabricated.

The immutable result DTO supplies `to_legacy_dict()` with `eid`, `score`,
`raw_score`, `decay_factor`, `summary`, `type`, `strength`, `confidence`, `step`,
and `ts`, plus flexible payload. Native structural values are applied last, so
payload cannot overwrite the result EID, scores, scope, lifecycle/governance, or
`authority_category` (`NOT_APPLICABLE` for ordinary compatibility memories).

## Boundaries and deferrals

Search creates zero operations, transitions, revisions, representations,
measurements, reconciliation records, or authorization. It has no dual read/write,
no legacy JSONL/shard/`.npy`/sidecar access, and no search acceleration/index/table.
It is qualified only on the STAGING core. Text search, additional representation
lanes, scalable acceleration, live caller adaptation, production-core creation,
and cutover remain deferred.

`SEARCH_ACCELERATION_IMPLEMENTED = NO`.
`COMPAT_TEXT_SEARCH_SUPPORTED = NO`.
`DUAL_READ_IMPLEMENTED = NO`.
`DUAL_WRITE_IMPLEMENTED = NO`.
