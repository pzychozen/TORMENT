# Block B Design — Stored-but-not-Foregrounded Memory (Reference + Environment)

**Status:** **RATIFIED 2026-04-21** by user + GPT. All §12 checklist items accepted. Block B implementation is unblocked — first move is test scaffolding (T1–T4), then reference memory wiring, then environment memory wiring, with the nine-invariant scorecard green throughout.
**Date:** 2026-04-21
**Scope:** Design for Block B of the regrouped memory roadmap: two memory classes attached to the substrate core that Block A established — full-reference memory (pull-for-thinking via `load`) and environment memory (consult-at-action-site via `consult`).

**Precedents (cited, not re-derived):**
- `docs/PRE_BLOCK_B_PRECONDITIONS.md` — ratified 2026-04-21. Gate on this work.
- `docs/BLOCK_B_IMPLEMENTATION_ANALYSIS.md` — ratified 2026-04-21. D.1–D.4 resolved.
- `docs/BLOCK_A_DESIGN.md` — ratified 2026-04-19; merged to main 2026-04-21. The substrate Block B attaches to.
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` — Items 3 (reference) and 5 (environment).

> This document is the design for Block B. It commits to concrete class names, field names, method signatures, and file-level changes for two distinct memory classes. It does NOT re-derive the analysis: every architectural decision traces back to the ratified analysis or preconditions. If code reality during implementation contradicts a decision here, **surface the contradiction before proceeding** — do not silently widen scope.

---

## 1. Objective

Add two memory classes to the existing codebase:

- **Reference memory** — a coherent external-object layer loaded intentionally for thinking (ratified plans, architecture docs, long design notes, stable research bundles). The unit of retrieval is the *whole object*, not chunks. Loaded references flow into prompt context via `retrieval_assembler`; loads are tracked with lifecycle state (active / unloaded), source linkage, and staleness-on-load.
- **Environment memory** — a scoped operational knowledge class consulted at action sites (sandbox has no network; python is 3.10; this workspace has a writable `data/` dir). Every write requires one of three evidence classes (user assertion / observed / inferred). Consult returns a relevance-filtered view at action-site code; environment facts never auto-inject into prompt context.

Block B proves both classes under real code, so that Block C (closure) later inherits a memory system with clearly distinct retrieval primitives and evidence-disciplined writes.

---

## 2. Scope / Out of scope

### In scope

- **New `ReferenceStore` class** — per-workspace reference-object storage, with its own folder and JSONL, structurally parallel to `ArchiveStore` but with whole-object retrieval semantics.
- **New `EnvironmentStore` class** — per-workspace environment-fact storage, net-new (no existing TORMENT analog).
- **Reference lifecycle** — load / unload methods, load state tracking, staleness-on-load, source linkage.
- **Environment lifecycle** — write-with-evidence (three evidence classes), consult-at-action-site method, probe-on-fail write path.
- **Provenance extensions** — four new source type constants and four new factory methods on `ProvenanceV1`.
- **Audit ledgers** — `ReferenceLoadLedger` (per-agent; tracks load/unload events) and `EnvironmentEventLedger` (per-workspace; tracks writes/probes).
- **Retrieval guards** — extend Block A's `memory_class != "baton"` filter at `fabric.query` merge point to also exclude `"reference"` and `"environment"`.
- **`retrieval_assembler` integration** — new `BLOCK_REFERENCE` block type; active loads flow into prompt context. Environment is NOT integrated.
- **Test harness** — four new test files covering AC-1 through AC-5.

### Out of scope (explicit)

- **Any change to `AgentRunner.run_turn`.** The runner stays frozen per D.4.
- **Any change to `fabric.query` signature or return shape.** Block B adds new filter terms but keeps the method's external contract.
- **Any wiring of `consult` into `action_policy`.** Per D.3, `consult` is return-only; callers decide.
- **Any new `MemoryPlan` lane flags.** Reference and environment are not lanes.
- **Any extension of `ArchiveStore`.** Reference is its own store per D.1.
- **Per-agent environment memory.** Environment is per-workspace per D.2.
- **Any MCP surface additions.** Access during v0.1 is via HTTP endpoints and internal APIs only.
- **Closure integration.** Reference objects that later become closure subjects are still Block B citizens at storage; closure semantics belong to Block C.
- **Runtime wiring of `SessionLifecycleHook`.** Still declared-only per Block A D.2.
- **Writeback gate widening.** R+3 forbids reference loads from silently becoming durable memory.

### Carry-forward invariants (from Block A and preconditions)

- **Baton-not-ontology-rank** generalizes to: `memory_class` values are retrieval/lifecycle distinctions, never quality tiers. Reference and environment are filtered out of default lanes for *lifecycle* reasons, not down-ranked for *quality* reasons.
- **Payload = current state source of truth; ledger = historical audit trail.** Same rule Block A established for baton applies to reference loads and environment events.
- **Rigidity sniff test.** Every boundary is enforced through required provenance / scope / lifecycle metadata alongside expression, not through restricting what the agent can express.

---

## 3. Adopted ratified decisions

This section cites; it does not re-litigate. All four decisions below are frozen.

**D.1 — Reference memory is a new `ReferenceStore` class.** Separate from `ArchiveStore`. Own folder, own JSONL, own retrieval path. Archive is a searchable library of chunks; reference is a whole-object layer intentionally loaded. (Ratified `BLOCK_B_IMPLEMENTATION_ANALYSIS.md` §F, 2026-04-21.)

**D.2 — Environment memory is per-workspace with an ownership field.** Environment facts are mostly shared across agents in a workspace; per-agent would cause redundant probing and inconsistent operational truth. Entries carry `ownership ∈ {agent, system, user}` to preserve provenance differentiation. (Ratified §F, 2026-04-21.)

**D.3 — `consult` is return-only.** `consult_environment(operation, scope)` returns a result envelope; Block B does not wire it into `action_policy`, `AgentRunner`, or any runtime gate. Future consult→policy integration is a separate runtime-doctrine amendment. (Ratified §F, 2026-04-21.)

**D.4 — Reference loads are pack-declared or external-caller-driven.** The `AgentRunner` does not invoke `load`. Packs, external callers, or HTTP endpoints call `fabric.load_reference` explicitly. `retrieval_assembler` picks up active loads via a new `BLOCK_REFERENCE` block type; the runner is never modified. (Ratified §F, 2026-04-21.)

### Carry-forward design cautions (from ratification)

- **Provenance distinguishes "reference as stored" from "act of loading."** The reference object has durable identity (ingest-time provenance); each load/unload is a lifecycle event (captured in `ReferenceLoadLedger`, NOT on the reference's provenance record). See §5.1 and §6.4.
- **Entry identity is separate from consult result shape.** An `EnvironmentEntry` has its own persistent payload and provenance; `consult` returns an `EnvironmentConsultResult` that is a view over relevant entries, not the entries themselves. See §5.2 and §7.3.

---

## 4. Acceptance criteria

Eleven criteria total — four for reference, five for environment, two shared. Per preconditions §5, they are NOT merged. Each criterion names its test.

### 4.1 Reference memory (B.1)

**AC-1.1 — Reference ingest requires source linkage.**
`fabric.ingest_reference(workspace_id, title, body, source_link, source_kind, ...)` succeeds when `source_link` and `source_kind` are supplied; either missing → mismatch result (envelope with `ok=False` and `result_code="missing_source_linkage"`), no entry created. *Test: T1 reference boundary.*

**AC-1.2 — Load returns a whole object with staleness marked.**
`fabric.load_reference(ref_id, scope_tag)` returns a result with the whole coherent reference body plus `stale: bool` computed against the source at load time. Loading never chunks. Staleness is not checked at arbitrary intervals. *Test: T1.*

**AC-1.3 — Loaded references never silently become durable substrate.**
After a reference is loaded, no code path silently creates a `core` or `baton` entry for its content. Promotion-to-durable requires an explicit separate `fabric.ingest(...)` call with `parent_eids` pointing to the reference and its own provenance. *Test: T1 + T4.*

**AC-1.4 — Default retrieval lanes exclude reference entries.**
`fabric.query(...)` with any combination of `retrieve_core / retrieve_archive / retrieve_deep / retrieve_relational` returns zero reference entries, even when content embeddings match. Reference content is only reachable via `fabric.load_reference` and `fabric.list_active_loads`. *Test: T1 + T4.*

### 4.2 Environment memory (B.2)

**AC-2.1 — Environment writes require one of three evidence classes.**
`fabric.write_environment(...)` without `evidence_class ∈ {user_asserted, observed, inferred}` → rejected (envelope `ok=False`, `result_code="missing_evidence_class"`), no entry created. *Test: T2 environment boundary.*

**AC-2.2 — `inferred` writes require a named inference rule.**
`evidence_class="inferred"` without an `inference_rule` string identifying the ratified rule → rejected (`result_code="inferred_requires_rule"`). The set of valid inference rule names is declared in a module-level constant (initially empty; v0.1 ships with zero inference rules enabled). *Test: T2.*

**AC-2.3 — `consult` is relevance-filtered and returns a view, not entries.**
`fabric.consult_environment(operation, scope)` returns an `EnvironmentConsultResult` containing only entries whose `scope_tag` matches the requested scope and whose content is relevant to the operation. The return shape is explicitly distinct from `EnvironmentEntry`: the result carries a list of fact-view dicts with redacted identity metadata, not the full entry payloads. *Test: T2.*

**AC-2.4 — Environment facts never auto-inject into prompt context.**
Running `AgentRunner.run_turn` with environment entries present produces a `retrieval_assembler` output that contains no environment content, regardless of similarity, scope, or recency. Environment entries have no corresponding `BLOCK_*` citizenship. *Test: T2 + T4.*

**AC-2.5 — Probe-on-fail produces observed provenance only.**
The probe-on-fail write path produces entries with `evidence_class="observed"` and a populated `observation_source` naming the system probe. No LLM-generated content reaches environment memory via probe-on-fail. *Test: T2.*

### 4.3 Shared (both categories)

**AC-3.1 — `load` and `consult` are not substitutable.**
Calling `fabric.load_reference(...)` with an ID that points to an environment entry, or `fabric.consult_environment(...)` with an operation that is really a reference-load request, produces a specific mismatch result naming the primitive/category error. Mechanism-neutral per preconditions §6.3 (exception, envelope, or result code all acceptable); behavior must not be silent empty, implicit coercion, or convergent success. *Test: T3 primitive distinctness.*

**AC-3.2 — Block A invariants preserved.**
All nine scorecard invariant tests remain green with Block B entries present. Baton retrieval, core retrieval, and archive retrieval are unaffected. `RESEARCH_ASSISTANT_PACK`'s `EMPTY_CONTRACT` swap-one-field promise is untouched. *Test: T4 + CI scorecard run.*

---

## 5. Data model changes

### 5.1 Provenance extensions (`torment_service/provenance_v1.py`)

Add four new `source_type` constants:

```python
# Block B — reference memory
SOURCE_REFERENCE_INGEST = "reference_ingest"
# Note: reference LOAD events are captured in ReferenceLoadLedger, NOT
# in ProvenanceV1. The reference object's provenance records its
# storage origin only; loadedness is lifecycle state, not provenance.

# Block B — environment memory (three evidence classes per R+5)
SOURCE_ENVIRONMENT_USER_ASSERTED = "environment_user_asserted"
SOURCE_ENVIRONMENT_OBSERVED      = "environment_observed"
SOURCE_ENVIRONMENT_INFERRED      = "environment_inferred"
```

Add to `VALID_SOURCE_TYPES` frozenset.

Add four new factory methods on `ProvenanceV1`:

- **`for_reference_ingest(source_link, source_kind, step=None, session_id=None)`** — produces storage provenance for the reference object; `source_link` and `source_kind` are required fields that go onto `ProvenanceV1.notes` as structured metadata (or an extra-field addition if the design review prefers). *Carry-forward caution: this records storage, not loading.*
- **`for_environment_user_asserted(asserted_by, step=None, session_id=None)`** — `asserted_by` records who told the system this fact.
- **`for_environment_observed(observation_source, step=None, session_id=None)`** — `observation_source` names the system probe (e.g., `"python_version_probe"`, `"network_availability_probe"`).
- **`for_environment_inferred(inference_rule, step=None, session_id=None)`** — `inference_rule` names the ratified rule that produced this entry; must be in a module-level `VALID_INFERENCE_RULES` frozenset (initially empty for v0.1).

All four follow the existing pattern (source_type set, write_path = `WRITE_DIRECT_INGEST`, parent_eids defaulted).

### 5.2 Reference memory entry shape

A reference object lives on its own store; it is NOT in `memory_graph.spawn_memory`. The payload shape:

```python
@dataclass
class ReferenceEntry:
    ref_id: str                    # stable id (workspace-scoped)
    workspace_id: str
    title: str
    body: str                      # whole-object content
    source_link: str               # REQUIRED — file path / URL / artifact ref
    source_kind: str               # REQUIRED — "repo_file" | "url" | "internal_doc" | "generated"
    source_hash: str               # hash of source at ingest time; used for staleness check
    provenance: Dict[str, Any]     # ProvenanceV1.to_dict() via for_reference_ingest
    created_ts: int
    metadata: Dict[str, Any]       # free-form extras (tags, arc, etc.)
```

`ref_id` is the durable identity. Load events do NOT mutate this entry. Staleness is computed at load time by comparing `source_hash` against a fresh hash of the source.

### 5.3 Reference load state (per-agent, separate from entry)

A load is a lifecycle event on top of a reference entry. The load state lives on the agent side, NOT on the reference entry:

```python
@dataclass
class ActiveLoad:
    load_id: str                   # stable id for this load event
    ref_id: str                    # which reference is loaded
    workspace_id: str
    agent_id: str
    scope_tag: str                 # scope under which the load is active
    loaded_at_ts: int
    stale_at_load: bool            # staleness result from this specific load
    status: str                    # "active" | "unloaded"
    unloaded_at_ts: Optional[int]
```

**Per the carry-forward caution in §3:** `ActiveLoad` and `ReferenceEntry` are kept structurally distinct. The reference has stable identity; loads are its events. A `ReferenceLoadLedger` records both events (see §6.4).

### 5.4 Environment memory entry shape

Environment entries live on their own per-workspace store:

```python
@dataclass
class EnvironmentEntry:
    env_id: str                    # stable id (workspace-scoped)
    workspace_id: str
    target_runtime: str            # REQUIRED — e.g., "python_3.10", "linux_sandbox", "cowork"
    scope_tag: str                 # REQUIRED — e.g., "default", "test_env", "prod_replica"
    key: str                       # REQUIRED — fact key, e.g., "network_available"
    value: Any                     # fact value (JSON-serializable)
    evidence_class: str            # REQUIRED — one of VALID_EVIDENCE_CLASSES
    ownership: str                 # REQUIRED — "agent" | "system" | "user"
    observation_source: Optional[str]  # required when evidence_class=="observed"
    inference_rule: Optional[str]      # required when evidence_class=="inferred"
    asserted_by: Optional[str]         # required when evidence_class=="user_asserted"
    provenance: Dict[str, Any]     # ProvenanceV1.to_dict()
    last_observed: int             # REQUIRED — unix ts at last observation/assertion
    created_ts: int
    metadata: Dict[str, Any]
```

### 5.5 Environment consult result shape (distinct from entry)

Per the carry-forward caution: consult returns a view, not entries.

```python
@dataclass
class EnvironmentFactView:
    key: str
    value: Any
    evidence_class: str
    last_observed: int
    inferred: bool                 # derived; True when evidence_class=="inferred"

@dataclass
class EnvironmentConsultResult:
    ok: bool
    result_code: str               # "consulted" | "no_relevant_facts"
    operation: str                 # echo of requested operation
    scope: str                     # echo of requested scope
    facts: List[EnvironmentFactView]
```

Key difference from `EnvironmentEntry`: no `env_id`, no `workspace_id`, no full `provenance` dict, no `ownership`. The result is a relevance-filtered view for the caller's action-site decision, not a database row.

---

## 6. Reference memory lifecycle

### 6.1 Storage — `ReferenceStore` class

**File:** `torment_service/reference_memory.py` (new, est. ~400 LoC).

Modeled on `ArchiveStore`:

```python
class ReferenceStore:
    """Per-workspace reference-memory store.

    Holds coherent whole-object reference entries with source linkage.
    Separate from ArchiveStore (which chunks) and from core/baton
    substrate (which is kernel-governed). Archive is a library;
    reference is a coherent object intentionally loaded as a whole.
    """
    def __init__(self, workspace_root: str) -> None: ...
    def ingest(self, title, body, source_link, source_kind, ...) -> Dict[str, Any]: ...
    def get(self, ref_id: str) -> Optional[ReferenceEntry]: ...
    def list(self, ...) -> List[Dict[str, Any]]: ...
    def delete(self, ref_id: str) -> bool: ...
    def compute_source_hash(self, source_link: str, source_kind: str) -> str: ...
```

Storage layout (per workspace):

```
<data_dir>/workspaces/<ws>/reference_memory/
  references.jsonl     (append-only; last record per ref_id is canonical)
  events.jsonl         (ingest / delete events)
```

Integration point: `fabric.py::TormentFabric` gets a new per-workspace dict `self.reference_stores: Dict[str, ReferenceStore]` alongside the existing `self.archive_stores`.

### 6.2 `fabric.ingest_reference`

**File:** `torment_service/fabric.py`, new method on `TormentFabric`.

```python
def ingest_reference(
    self,
    workspace_id: str,
    title: str,
    body: str,
    source_link: str,
    source_kind: str,
    metadata: Optional[Dict[str, Any]] = None,
    step: int = 0,
) -> Dict[str, Any]:
    """Ingest a reference object.

    Required fields:
        source_link + source_kind (AC-1.1)

    Returns envelope:
        {"ok": bool, "result_code": "ingested" | "missing_source_linkage",
         "ref_id": str, ...}

    Block B (docs/BLOCK_B_DESIGN.md §6.2). Reference objects are whole-
    object coherent entries; they do NOT enter the kernel, do NOT
    create motifs, do NOT affect drift.
    """
```

Validation fires before storage. Missing `source_link` OR `source_kind` → reject with specific `result_code` and no entry created.

### 6.3 `fabric.load_reference` / `fabric.unload_reference` / `fabric.list_active_loads`

Three methods for lifecycle management:

```python
def load_reference(
    self,
    workspace_id: str,
    agent_id: str,
    ref_id: str,
    scope_tag: str,
) -> Dict[str, Any]:
    """Load a reference object into the agent's active context.

    Returns an envelope with the whole body plus staleness flag:
        {"ok": True,
         "result_code": "loaded" | "not_found" | "not_a_reference",
         "load_id": str,
         "ref_id": str,
         "title": str,
         "body": str,
         "stale": bool,
         "loaded_at_ts": int}

    Staleness is computed at load time by comparing current source
    hash against stored source_hash (AC-1.2). `stale=True` does NOT
    block the load — it flags the condition for the caller to handle.
    """

def unload_reference(
    self,
    workspace_id: str,
    agent_id: str,
    load_id: str,
) -> Dict[str, Any]:
    """Mark an active load as unloaded. Soft-operation; idempotent."""

def list_active_loads(
    self,
    workspace_id: str,
    agent_id: str,
    scope_tag: Optional[str] = None,
) -> Dict[str, Any]:
    """List this agent's currently-active reference loads."""
```

Load envelope includes the whole body because reference memory is whole-object retrieval (AC-1.2). If the caller doesn't want the body immediately, it can discard the field; the load_id is what matters for subsequent `retrieval_assembler` integration.

### 6.4 `ReferenceLoadLedger` — audit trail for load/unload events

**File:** `torment_service/reference_load_ledger.py` (new, ~120 LoC).

Modeled on `BatonLedger`. Per-agent append-only JSONL capturing load/unload events. Events are separate from the reference entry itself (addressing the carry-forward caution).

```python
@dataclass
class ReferenceLoadEvent:
    event_id: str
    workspace_id: str
    agent_id: str
    ref_id: str
    load_id: str
    kind: str                # "loaded" | "unloaded"
    ts: int
    scope_tag: str
    stale_at_load: Optional[bool]  # populated for "loaded" events only

class ReferenceLoadLedger:
    """Per-(workspace, agent) append-only load-event ledger.

    Audit only. The reference entry's provenance records its storage
    origin; each load/unload is a separate lifecycle event here.
    Payload (ActiveLoad in memory) is the source of truth for current
    state; this ledger is the historical audit trail.
    """
    def add_event(self, event: ReferenceLoadEvent) -> None: ...
    def list_events(self, ref_id=None, kind=None, limit=500) -> List[ReferenceLoadEvent]: ...
```

Path: `<data_dir>/workspaces/<ws>/agents/<agent>/reference_load_events.jsonl`.

### 6.5 Retrieval-lane guard (extends Block A's filter)

**File:** `torment_service/fabric.py`, `query` method.

Block A added the filter `all_hits = [h for h in all_hits if h.get("memory_class") != "baton"]` at the merge point. Block B extends it to also exclude reference (though reference entries never enter `memory_graph` anyway, this is defensive):

```python
# Block A + B: default lanes exclude non-substrate memory classes.
# baton (Block A), reference (Block B — never enters graph anyway;
# defensive), environment (Block B — never enters graph anyway).
_NON_DEFAULT_CLASSES = frozenset({"baton", "reference", "environment"})
all_hits = [h for h in all_hits
            if h.get("memory_class") not in _NON_DEFAULT_CLASSES]
```

Since reference and environment live on their own stores (not in `memory_graph`), this filter is belt-and-suspenders — but the explicit exclusion is architectural signal.

---

## 7. Environment memory lifecycle

### 7.1 Storage — `EnvironmentStore` class

**File:** `torment_service/environment_memory.py` (new, est. ~450 LoC; more than reference because of evidence-class discipline).

```python
VALID_EVIDENCE_CLASSES = frozenset({"user_asserted", "observed", "inferred"})
VALID_OWNERSHIP = frozenset({"agent", "system", "user"})
VALID_INFERENCE_RULES: frozenset = frozenset()  # v0.1: empty — no ratified rules

class EnvironmentStore:
    """Per-workspace environment-memory store.

    Holds operational facts about machine / runtime / container / shell
    / filesystem / execution surface. Every write requires one of three
    evidence classes (R+5). Never flows through retrieval_assembler.
    Never auto-injects into LLM context (R+4).
    """
    def __init__(self, workspace_root: str) -> None: ...
    def write(self, target_runtime, scope_tag, key, value,
              evidence_class, ownership, **evidence_fields) -> Dict[str, Any]: ...
    def get(self, env_id: str) -> Optional[EnvironmentEntry]: ...
    def consult(self, operation: str, scope: str) -> EnvironmentConsultResult: ...
    def list(self, scope_tag=None, ownership=None, limit=50) -> List[Dict[str, Any]]: ...
```

Storage layout (per workspace):

```
<data_dir>/workspaces/<ws>/environment_memory/
  environment.jsonl     (append-only; last record per env_id is canonical)
  events.jsonl          (writes / probes)
```

### 7.2 `fabric.write_environment`

**File:** `torment_service/fabric.py`.

```python
def write_environment(
    self,
    workspace_id: str,
    target_runtime: str,
    scope_tag: str,
    key: str,
    value: Any,
    evidence_class: str,
    ownership: str,
    observation_source: Optional[str] = None,
    inference_rule: Optional[str] = None,
    asserted_by: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    step: int = 0,
) -> Dict[str, Any]:
    """Write an environment fact.

    Required (AC-2.1):
        target_runtime, scope_tag, key, value, evidence_class, ownership

    Evidence-class-specific required fields (AC-2.2 + R+5):
        evidence_class="user_asserted"  → asserted_by required
        evidence_class="observed"       → observation_source required
        evidence_class="inferred"       → inference_rule required AND
                                          must be in VALID_INFERENCE_RULES

    Returns envelope:
        {"ok": bool,
         "result_code": "written" | "missing_evidence_class"
                       | "missing_evidence_field" | "inferred_requires_rule"
                       | "unknown_inference_rule",
         "env_id": str, ...}

    Block B (docs/BLOCK_B_DESIGN.md §7.2). Environment facts never
    auto-inject into LLM context (R+4). Consult is the only read path
    beyond admin inspection.
    """
```

Validation fires before storage. Each evidence class has its own required field; missing any → reject with specific result code.

### 7.3 `fabric.consult_environment`

```python
def consult_environment(
    self,
    workspace_id: str,
    operation: str,
    scope: str,
    *,
    relevance_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Consult environment memory for a specific operation at a scope.

    Returns a serialized EnvironmentConsultResult:
        {"ok": True,
         "result_code": "consulted" | "no_relevant_facts",
         "operation": str,
         "scope": str,
         "facts": [
             {"key": str, "value": Any, "evidence_class": str,
              "last_observed": int, "inferred": bool},
             ...
         ]}

    Per D.3: consult is RETURN-ONLY. This method does not modify state,
    does not call any policy gate, and does not inject into prompt
    context. The caller decides what to do with the facts.

    Relevance filtering (AC-2.3):
        - scope_tag must match requested scope
        - relevance_fields (if provided) narrows the returned key set;
          default is to return all facts matching the scope
    """
```

The return shape (`EnvironmentConsultResult` → `facts` list of `EnvironmentFactView`) is explicitly distinct from `EnvironmentEntry`. No `env_id`, no `workspace_id`, no full provenance — the caller gets a fact-view, not a database row (carry-forward caution).

### 7.4 Probe-on-fail write path

A distinct entry point for system-initiated probes after action failures:

```python
def probe_environment_on_fail(
    self,
    workspace_id: str,
    target_runtime: str,
    scope_tag: str,
    key: str,
    value: Any,
    observation_source: str,
    *,
    ownership: str = "system",
    step: int = 0,
) -> Dict[str, Any]:
    """System-initiated write triggered by an action failure.

    ALWAYS writes with evidence_class="observed" and a populated
    observation_source. Never accepts "inferred" from this path
    (AC-2.5). The ownership defaults to "system" since the probe
    originates from the system, not the agent.
    """
```

This is a thin wrapper around `write_environment` that forces `evidence_class="observed"` and requires `observation_source`. It cannot be used to smuggle inferred content into observed provenance.

### 7.5 `EnvironmentEventLedger` — audit trail

**File:** `torment_service/environment_event_ledger.py` (new, ~120 LoC).

Per-workspace (not per-agent; environment is per-workspace per D.2).

```python
@dataclass
class EnvironmentEvent:
    event_id: str
    workspace_id: str
    env_id: str
    kind: str                # "written" | "probed" | "consulted"
    ts: int
    evidence_class: Optional[str]
    operation: Optional[str]  # populated for "consulted" events
    scope: Optional[str]
    metadata: Dict[str, Any]

class EnvironmentEventLedger:
    def add_event(self, event: EnvironmentEvent) -> None: ...
    def list_events(self, env_id=None, kind=None, limit=500) -> List[EnvironmentEvent]: ...
```

Path: `<data_dir>/workspaces/<ws>/environment_memory/events.jsonl`.

Consult events are logged to the ledger for audit but do not modify state.

---

## 8. Retrieval behavior

### 8.1 Reference memory flows through `retrieval_assembler` as `BLOCK_REFERENCE`

**File:** `torment_service/retrieval_assembler.py`.

Add a new block type constant:

```python
BLOCK_REFERENCE = "reference_context"

FILL_ORDER = [
    BLOCK_IDENTITY,
    BLOCK_REFERENCE,    # NEW — reference objects inserted before relational
    BLOCK_RELATIONAL,
    BLOCK_SITUATIONAL,
    BLOCK_ARCHIVE,
]
```

Reference slots between identity and relational: loaded references are *intentional reasoning material* — more important than archive chunks, less identity-defining than core canon.

Each profile gains a reference-block percentage:

```python
PROFILES: Dict[str, Dict[str, float]] = {
    "companion": {
        BLOCK_IDENTITY:    0.30,
        BLOCK_REFERENCE:   0.10,
        BLOCK_RELATIONAL:  0.30,
        BLOCK_SITUATIONAL: 0.20,
        BLOCK_ARCHIVE:     0.10,
    },
    "research": {
        BLOCK_IDENTITY:    0.12,
        BLOCK_REFERENCE:   0.25,  # research-heavy; references matter
        BLOCK_RELATIONAL:  0.08,
        BLOCK_SITUATIONAL: 0.20,
        BLOCK_ARCHIVE:     0.35,
    },
    # ... narrator / balanced likewise get a reference slice ...
}
```

### 8.2 Active-loads pull into the assembler

The assembler learns about active reference loads via a new helper:

```python
def _gather_reference_blocks(
    assembler_context,
    fabric,
    workspace_id: str,
    agent_id: str,
    scope_tag: str,
) -> List[ContextBlock]:
    """Fetch active reference loads for this agent/scope and build
    ContextBlock entries for the reference block."""
    result = fabric.list_active_loads(workspace_id, agent_id, scope_tag=scope_tag)
    blocks = []
    for load in result.get("loads", []):
        body = load.get("body", "")
        blocks.append(ContextBlock(
            block_type=BLOCK_REFERENCE,
            eid=None,
            chunk_id=None,  # whole object — not chunked
            text=body,
            token_count=_estimate_tokens(body),
            score=1.0,  # all active loads are equally intentional
            reason=f"pack-declared reference load: {load['ref_id']}",
            source="reference",
            metadata={"ref_id": load["ref_id"], "load_id": load["load_id"],
                      "stale": load.get("stale", False)},
        ))
    return blocks
```

The caller (pack setup or external code) is responsible for ensuring the right references are loaded *before* assembly. The assembler does not load references itself — that would touch the runner.

### 8.3 Environment memory is NOT integrated with `retrieval_assembler`

Per R+4 and §A of the analysis: environment memory has no `BLOCK_*` citizenship. No environment content reaches the assembler, ever. This is enforced by:

- The `retrieval_assembler` never calling `consult_environment`.
- The FILL_ORDER listing no environment block.
- The profile dict containing no environment percentage.

Any future proposal to add environment to the assembler requires explicit amendment to this document.

### 8.4 Rigidity sniff test for retrieval

- **Reference exclusion from default lanes:** hard `memory_class != "reference"` filter, NOT down-ranking. Same pattern as Block A's baton.
- **Environment absence from assembler:** structural absence (no block type, no gather helper), NOT dynamic filtering. Structural is stronger than filter-based for this risk class.
- **`load` vs `consult` non-substitutability:** enforced by separate methods with incompatible signatures and separate stores. A cross-call at ID level produces a mismatch result (AC-3.1).

---

## 9. Test plan

Four new test files. Unit-scope, expected combined runtime < 5 seconds.

| # | File | Covers | Reuses fixtures from |
|---|---|---|---|
| T1 | `tests/test_reference_load_boundary.py` | AC-1.1 through AC-1.4 | `test_baton_requires_lifecycle_fields.py`, `test_provenance_v1_admission.py` |
| T2 | `tests/test_environment_consult_boundary.py` | AC-2.1 through AC-2.5 | `test_baton_requires_lifecycle_fields.py`, `test_reinforce_contract_invariant.py` |
| T3 | `tests/test_block_b_primitives_not_substitutable.py` | AC-3.1 | new, tightly-scoped |
| T4 | `tests/test_agent_loop_block_b_present.py` | AC-3.2 + integration | `test_agent_loop_baton_present.py` |

**Scorecard regression requirement.** All nine scorecard invariant tests must remain green. Same rule as Block A.

**No shared fixtures with writeback or closure.** No closure code exists; Block B tests don't introduce any fixture that would reasonably be reused by closure when it lands.

---

## 10. Non-runtime-touching guarantees

Per D.4 and §2's out-of-scope list, Block B makes specific *absence* commitments:

- **`AgentRunner.__init__` signature unchanged.** No new parameters, no new dependencies.
- **`AgentRunner.run_turn` body unchanged.** No new phases, no new calls, no new branches.
- **`FabricHandle` Protocol unchanged.** Still four methods (`ingest`, `measure_drift`, `gravity_correction`, plus `enter_reflex` which is on the runner).
- **`fabric.query` signature unchanged.** The filter at its merge point is extended by one frozenset membership check, but the external contract is identical.
- **`action_policy` module unchanged.** No `consult`→policy wiring.
- **`SessionLifecycleHook` still declaration-only.** No wiring.
- **MCP server (`mcp_server.py`) unchanged.** No new tools.
- **Behavior packs unchanged.** Packs are never rewritten by Block B; a future pack increment may DECLARE references, but that's the pack's concern, not Block B's.
- **`memory_graph.spawn_memory` signature unchanged.** No new parameters.
- **All nine scorecard invariant tests unchanged.**

These absences are load-bearing. Any code reviewer encountering an unexpected modification to one of the above surfaces during Block B implementation should challenge it before approval.

---

## 11. Open questions

Only questions that genuinely remain after ratification.

**Q1 — Staleness check mechanism for non-repo sources.**
For `source_kind="repo_file"`, hashing the file content is straightforward. For `source_kind="url"`, what's the hash? Full HTTP body? Last-Modified header? For `source_kind="internal_doc"` referring to another TORMENT-managed doc, do we re-hash or track by version id? Recommendation: defer the specific hash strategy per `source_kind` to implementation time; each kind gets a named handler. Not a blocker for design ratification.

**Q2 — What counts as a ratified `inference_rule`?**
`VALID_INFERENCE_RULES` ships empty in v0.1. When a future increment wants to add (e.g.) "infer python version from module imports" as a ratified rule, where does the ratification happen? Recommendation: rule additions require a separate preconditions-style ratification doc (lightweight, named `ENVIRONMENT_INFERENCE_RULE_<name>.md`), not just code-reviewer sign-off. This keeps R+5's discipline visible.

**Q3 — `consult` relevance ranking.**
When `consult_environment` returns multiple matching facts, is order meaningful? Recommendation for v0.1: sort by `last_observed` descending (freshest first), but leave richer ranking (weighted by recency + ownership + evidence class) to a later increment. The return shape is a list; order is stable but not semantically load-bearing at v0.1.

**Q4 — Probe-on-fail triggering.**
`probe_environment_on_fail` is a method, but *who calls it?* Per D.3 and §10, Block B does not wire it into `action_policy`. So in v0.1, it is callable only from external code (tests, HTTP endpoints). This is intentional — wiring is a future runtime amendment. Flagging so reviewers don't expect v0.1 to have automated probe triggers.

**None of Q1–Q4 blocks design ratification.** They can be refined during implementation review.

---

## 12. Ratification record

**Drafted:** 2026-04-21 by Claude, following ratified analysis 2026-04-21.

**Ratification pass (2026-04-21, user + GPT):**

- [x] §1 Objective accepted
- [x] §2 Scope / out-of-scope + carry-forward invariants accepted
- [x] §3 Adopted D.1 – D.4 decisions (citations) accepted
- [x] §4 Acceptance criteria (AC-1.1–AC-1.4, AC-2.1–AC-2.5, AC-3.1–AC-3.2) accepted
- [x] §5 Data model (provenance extensions, reference entry, active-load state, environment entry, consult-result view) accepted — five judgment calls resolved during review: (1) `source_link`/`source_kind` on `ReferenceEntry` directly; (2) `ActiveLoad` structurally separate from `ReferenceEntry`; (3) `BLOCK_REFERENCE` between identity and relational in FILL_ORDER (default policy, not doctrine); (4) `VALID_INFERENCE_RULES` ships empty in v0.1; (5) `probe_environment_on_fail` callable but not wired.
- [x] §6 Reference memory lifecycle accepted
- [x] §7 Environment memory lifecycle accepted
- [x] §8 Retrieval behavior accepted
- [x] §9 Test plan accepted
- [x] §10 Non-runtime-touching guarantees accepted
- [x] §11 Open questions accepted as non-blocking

**Status:** **RATIFIED 2026-04-21 by user + GPT.** Block B implementation is unblocked. Any change to the design after this point requires a separately ratified amendment.

### Handoff notes for implementation

1. **First move is test scaffolding.** Land T1–T4 stubs (failing tests per AC-1, AC-2, AC-3) before wiring any behavior.
2. **Nine-invariant scorecard stays green throughout.** No merges if any scorecard test regresses without separately ratified runtime-doctrine amendment.
3. **Environment memory is the higher-risk category during review.** Specifically:
    - Every environment write path must validate evidence class + evidence-class-specific field.
    - `VALID_INFERENCE_RULES` must stay empty in v0.1 code (no rules pre-declared for test purposes — tests exercise the "missing rule" rejection path).
    - No environment content in any prompt-assembled output. Ever. Any reviewer seeing environment-shaped content reach an `AssembledContext` should challenge it.
4. **Reference loads never modify the reference entry.** Only the ledger and the `ActiveLoad` in-memory state change on load/unload. The reference entry's provenance is set once at ingest and never touched again.
5. **`consult` returns a view, not entries.** Verify `EnvironmentConsultResult` shape in tests and code review — if it ever returns `EnvironmentEntry` objects directly, the entry-identity-vs-consult-result separation has been violated.
6. **The `load` vs `consult` distinction must survive code review.** If anyone proposes a helper that "gets Block B memory by ID" regardless of category, that helper is the collapse point the preconditions forbid.
7. **`ActiveLoad` must stay a thin activation/state object, not a shadow reference.** Added during ratification as a watch-item. During implementation, resist the temptation to grow `ActiveLoad` into a second identity layer that mirrors `ReferenceEntry` fields. `ActiveLoad` should carry only the lifecycle minimum (load_id, ref_id, workspace_id, agent_id, scope_tag, loaded_at_ts, stale_at_load, status, unloaded_at_ts). Any field that duplicates `ReferenceEntry` data (title, body, source_link, etc.) on `ActiveLoad` is the drift-into-shadow-identity failure mode — challenge it before merge.

---

## Appendix — files expected to change or be created

### New files

- `torment_service/reference_memory.py` — `ReferenceStore` class (~400 LoC).
- `torment_service/environment_memory.py` — `EnvironmentStore` class (~450 LoC; more due to evidence discipline).
- `torment_service/reference_load_ledger.py` — `ReferenceLoadLedger` (~120 LoC).
- `torment_service/environment_event_ledger.py` — `EnvironmentEventLedger` (~120 LoC).
- `tests/test_reference_load_boundary.py` — T1 (AC-1).
- `tests/test_environment_consult_boundary.py` — T2 (AC-2).
- `tests/test_block_b_primitives_not_substitutable.py` — T3 (AC-3.1).
- `tests/test_agent_loop_block_b_present.py` — T4 (AC-3.2 + integration).

### Modified files

- `torment_service/provenance_v1.py` — four new `SOURCE_*` constants, four new factory methods, `VALID_INFERENCE_RULES` frozenset (empty in v0.1).
- `torment_service/fabric.py` — new methods (`ingest_reference`, `load_reference`, `unload_reference`, `list_active_loads`, `write_environment`, `consult_environment`, `probe_environment_on_fail`); per-workspace reference/environment store dicts; extended default-lane filter.
- `torment_service/retrieval_assembler.py` — `BLOCK_REFERENCE` constant, FILL_ORDER update, profile percentages update, `_gather_reference_blocks` helper.

### Not changed (explicitly preserved)

- `torment_service/agent_loop.py` — runner unchanged; `SessionLifecycleHook` still declaration-only.
- `torment_service/thinking_controller.py` — controller unchanged.
- `torment_service/memory_graph.py` — `spawn_memory` signature unchanged.
- `torment_service/memory_kernel.py` — kernel math untouched.
- `torment_service/action_policy.py` — no `consult`→policy wiring.
- `torment_service/archive_memory.py` — `ArchiveStore` unchanged.
- `torment_service/behavior_packs.py` — packs unchanged (pack-level reference declaration is a future increment).
- `torment_service/mcp_server.py` — MCP surface unchanged.
- `torment_service/conflicts.py` — `ConflictRegistry` unchanged.
- `torment_service/baton_ledger.py` — unchanged.
- All nine scorecard invariant test files — unchanged; must remain green.
