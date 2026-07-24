# TORMENT Brainvision — Stage S3B v0.3 Durable-Evidence Architecture Decision Record v0.1

Status: DRAFT decision record for independent review. Docs-only. Creates no authority.

```text
document_class            = architecture decision record (docs-only)
resolves                  = conceptual decisions H1–H5 of the accepted v0.3 architecture review
authority_created         = none
implementation_authorized = false
execution_authorized      = false
manifest_contact          = none
publication_authorized    = false
scientific_reconstruction = none
retained_evidence_modified = none
git_mutations             = none
```

---

## 1. Status and scope

This decision record formally resolves the five conceptual decisions (H1–H5) that the accepted Stage S3B v0.3 Durable Evidence Architecture Review left to Hilmir, and binds them as authoritative architecture decisions. Hilmir has explicitly approved all five.

This record is binding on any future v0.3 implementation specification: the resolved decisions may not be reinterpreted downstream. It does not duplicate the architecture review, does not add new architecture beyond fixing these five decisions and their direct consequences, and creates no implementation, execution, manifest-contact, or publication authority. It removes H1–H5 from the unresolved conceptual-decision set; all other gates the review named remain open (§12).

The scientific claim boundary and all permanent boundaries are preserved unchanged (§11, §14).

---

## 2. Authoritative baseline

```text
repository = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
branch     = main
HEAD       = origin/main = 72c7edd0566e86e51e4b632b8bbfd8171326f5f8
milestone  = 72c7edd docs(research): specify durable evidence architecture v0.3
working tree = clean (expected)
```

Bound architecture review (the accepted authority this record resolves):

```text
path        = docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_ARCHITECTURE_REVIEW_v0.1.md
committed at = 72c7edd0566e86e51e4b632b8bbfd8171326f5f8
git blob    = 8dd09ffc7be8e7a2b44fafaa3acf52ada858053a
whole-file SHA-256 = 18aaa3732c24702df372c41ef747c2d326d949b5317902677cf84bc2fcf23d48
byte length = 51551
```

Retained v0.2 forensic evidence remains immutable and was reconfirmed unchanged (`current_state.json` 144B `63bd8dbe…`; `current_state.json.tmp` 136B `b0910c0e…`).

---

## 3. Relationship to the architecture review

The bound review (§2) is accepted as the authoritative v0.3 durable-evidence architecture. Its §16 flagged five conceptual/state-model decisions (H1–H5) as requiring Hilmir before implementation. This record resolves exactly those five and nothing else. Where this record and the review both speak, this record governs the *decision*; the review governs the surrounding *architecture* and *invariants*, which are unchanged. This record does not restate the review's full invariant set, candidate comparison, crash tables, or fault-injection matrix; it references them.

Effect on the review's open-decision set: H1–H5 move from "requires Hilmir" to RESOLVED. The review's architectural, implementation, and test-design decisions (§12 here) remain open. The review's verdict — implementation-ready-with-named-decisions, and explicitly *not yet implementation-ready* — is unchanged by this record except that the conceptual subset is now closed.

---

## 4. Decision H1 — publication as projection

RESOLVED:

```text
PUBLICATION_IS_PROJECTION = true
```

Publication is a downstream representation (projection) of an already-authoritative durable scientific result. Publication does not create scientific truth, does not change the scientific result, does not complete scientific computation, does not repair incomplete evidence, and does not authorize scientific execution.

Architectural consequence: the source of scientific truth is the authoritative durable evidence pair (H2), never the publication artifacts. Publication is a function of committed evidence to projected bytes; it has no authority to originate, alter, or complete a result. Any design in which a result becomes "real" only upon publication is prohibited.

---

## 5. Decision H2 — authoritative bundle-plus-receipt result

RESOLVED: the authoritative durable scientific result is exactly the verified pair, and neither component is independently sufficient.

```text
IMMUTABLE_SCIENTIFIC_BUNDLE + linked SCIENTIFIC_COMPLETION receipt = AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
bundle without a valid matching receipt                            = ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE
receipt without a valid matching bundle                            = INVALID_SCIENTIFIC_COMPLETION
```

Architectural consequence: the result is a two-part evidence object. An orphan bundle and an invalid completion are non-results: retained for forensics, never authoritative, never publishable, never grounds to reopen execution. Only the verified, mutually linked pair asserts a durable scientific result. The bundle stores the canonical result bytes (evidence storage, not automatic public exposure); the receipt is the bounded, hash-linked reference that binds them.

---

## 6. Decision H3 — observer/evidence boundary

RESOLVED: the observer/evidence boundary — the instant at which "the run has a durable determinate scientific result" becomes an asserted fact — occurs only when the bundle and receipt are all of:

```text
durable
byte-verified
hash-verified
identity-bound (execution identity, authorization identity, protocol/schema identity)
mutually linked (receipt references the exact bundle by SHA-256 and byte length)
part of the accepted primary evidence chain
```

Before that boundary, an in-memory result, an emergency observation, an orphan bundle, or an invalid completion is **not** an authoritative durable scientific result.

Terminology constraint (binding): "observer boundary" is architectural terminology for *when evidence becomes authoritative*. It does not imply consciousness, quantum measurement, metaphysical observer identity, or security correctness derived from physics. The boundary is defined entirely by the verifiable engineering conditions listed above and by nothing else. No downstream specification may import a metaphysical, quantum, or observer-theoretic reading as a requirement.

---

## 7. Decision H4 — separately authorized publication recovery

RESOLVED: publication recovery is permitted only through a process that is separately authorized, structurally publication-only, and non-automatic.

Publication recovery is not scientific execution, not execution recovery, not authorization reuse, not manifest contact, not descriptor invocation, not scientific recomputation, and not result reinterpretation.

The publication-only process may **only**:

```text
verify the existing immutable bundle
verify the linked completion receipt
project the exact committed evidence bytes
verify the projected bytes
record publication-attempt and publication-completion evidence
```

It must be structurally **incapable** of:

```text
contacting the manifest
importing or invoking the scientific descriptor
changing fixtures
changing thresholds or tolerances
constructing a new result kind
altering the immutable scientific bundle
creating a new SCIENTIFIC_COMPLETION receipt
opening scientific execution authority
```

Publication recovery must require a new docs-only authorization specific to publication projection, and must never occur automatically after a crash. This authorization is distinct from any scientific-execution authorization and cannot be satisfied by one.

---

## 8. Decision H5 — contradictory-evidence policy

RESOLVED: any contradiction between primary and emergency evidence is classified `CONTRADICTORY_EVIDENCE`, with required consequences:

```text
scientific verdict assertion   = prohibited
automatic reconciliation       = prohibited
publication                    = prohibited
scientific execution recovery  = prohibited
automatic retry                = prohibited
evidence deletion or repair    = prohibited
operator forensic review       = required
```

The strongest mutually supported conservative facts may still be stated (e.g., authority consumed, contact counts that both channels agree on), but no disputed scientific result may be asserted. Both conflicting channels are retained byte-for-byte; neither may be silently discarded to restore a clean result.

---

## 9. Result-state consequences

The approved decisions fix the following major result states and their capabilities. Scientific execution recovery is prohibited in every state once authority has been consumed; a corrected evaluation is only ever a new lineage.

| Result state | Scientific-result assertion | Publication eligible | Publication recovery | Scientific-execution recovery |
|---|---|---|---|---|
| COMPUTATION_IN_PROGRESS | No | No | No | No |
| COMPUTED_IN_MEMORY_NOT_DURABLE | No | No | No | No |
| EMERGENCY_OBSERVED_UNCOMMITTED | No (observation only) | No | No | No |
| ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE | No | No | No | No |
| INVALID_SCIENTIFIC_COMPLETION | No | No | No | No |
| AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT | Yes | Yes | Yes (via §7 process + new pub authorization) | No |
| PUBLICATION_INCOMPLETE | Yes (result already authoritative) | Yes | Yes (via §7 process + new pub authorization) | No |
| PUBLICATION_COMPLETED | Yes | n/a (done) | n/a (idempotent re-projection only, via §7) | No |
| CONTRADICTORY_EVIDENCE | No (only conservative mutually-supported facts) | No | No | No |

Only `AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT` (and the post-authoritative publication states derived from it) may support a scientific-result assertion or publication. `EMERGENCY_OBSERVED_UNCOMMITTED`, `ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE`, and `INVALID_SCIENTIFIC_COMPLETION` never do. `CONTRADICTORY_EVIDENCE` supports neither assertion nor publication.

---

## 10. Publication eligibility and recovery boundary

Publication eligibility (fail closed on anything less):

```text
valid immutable bundle
valid matching completion receipt
matching execution identity
matching authorization identity
matching protocol/schema identity
verified bundle byte length
verified bundle SHA-256
valid primary-chain position
no contradictory evidence
```

Publication-only process boundary (a separate capability and authorization surface, per H4). The process must have:

```text
no descriptor imports
no manifest reader
no fixture loader capable of recomputation
no scientific-threshold configuration
no result-kind constructor
no scientific execution entry point
read-only access to accepted evidence
write access ONLY to publication projection and publication evidence
```

These structural properties must later be enforced through source-boundary tests and adversarial review; this record states the requirement, and does not implement or authorize the process. Publication recovery follows the same boundary and additionally requires the separate publication-projection authorization named in H4.

---

## 11. Security and scientific claim boundaries

Security claims permitted by this record — the selected state model, as *decided* (not as implemented):

```text
separates scientific completion from publication
defines the authoritative result as a verified evidence pair
prevents publication from becoming a source of scientific truth
prohibits automatic publication recovery
fails closed on contradictory evidence
```

This record does not claim the architecture is implemented, tested, proven secure, Windows-durable, or ready for execution.

Scientific claim boundary (preserved exactly):

```text
two complete v0.2 scientific passes occurred
the two canonical pass bundles were byte-identical
the unpublished v0.2 result kind is not durably available
the v0.2 result must not be reconstructed
```

This record does not state or imply whether the v0.2 result was `SYNTHETIC_GATE_PASSED` or `SYNTHETIC_GATE_FAILED`; those two enum values are named only to fix that the record kind is exactly one of them and that which one is not durably available.

---

## 12. Remaining unresolved implementation decisions

Hilmir's conceptual approval of H1–H5 does not resolve any of the following; they remain open for the next phase (a docs-only implementation specification):

```text
final immutable scientific bundle schema
final completion-receipt schema
record canonicalization format
content-addressed filename format
writer-attempt identity format
same-sequence duplicate handling details
same-sequence fork detection implementation
Windows directory-durability primitive or adapter
emergency capsule exact byte format and budget
publication-only authorization document format
complete fault-injection test matrix
```

---

## 13. Readiness effect

```text
conceptual architecture decisions H1–H5 = RESOLVED
implementation specification              = NOT YET COMPLETE
implementation authorized                 = false
execution authorized                      = false
manifest contact authorized               = false
publication authorized                    = false
```

The next legitimate phase, after independent acceptance of this decision record, is a **docs-only v0.3 durable-evidence implementation specification** covering the remaining schemas, the Windows durability mechanism, object naming and fork rules, the emergency capsule, the publication-only source boundary, and the fault-injection contract. That specification is **not** created by this record.

---

## 14. Non-authorizations and preserved boundaries

This record creates no authority and changes nothing. It does not authorize or recommend enacting:

```text
implementation of the v0.3 protocol            runner execution
manifest contact                               scientific reconstruction or recomputation
publication of any result                      automatic publication or automatic publication recovery
evidence repair, rename, deletion, promotion, or terminalization
reconstruction of the v0.2 scientific verdict  a v0.2 retry
PsiTRS contact                                 historical F3 reinterpretation
production-kernel modification                 live Brainvision integration
memory-system integration                      live capture or ingestion
service/runtime integration                    threshold or tolerance tuning
scientific rescue                              production claims
a new one-run scientific-execution authorization
```

Preserved:

```text
docs-only; no implementation, execution, manifest-contact, or publication authority
FORMAL_HOLD = active
Mode 0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
Brainvision remains offline and quarantined under research/brainvision/
v0.2 is consumed, terminal, and immutable; any future evaluation is a NEW lineage — never a retry
```

---

## Binding summary — H1–H5

```text
H1  PUBLICATION_IS_PROJECTION = true. Publication is a downstream projection of an already-authoritative result;
    it never creates, changes, completes, repairs, or authorizes scientific truth.
H2  The authoritative durable scientific result is exactly the verified IMMUTABLE_SCIENTIFIC_BUNDLE plus its linked
    valid SCIENTIFIC_COMPLETION receipt. Bundle-alone = ORPHAN; receipt-alone = INVALID; only the verified pair is authoritative.
H3  The observer/evidence boundary is reached only when the pair is durable, byte-verified, hash-verified, identity-bound,
    mutually linked, and in the accepted primary chain. It is engineering terminology only — no consciousness, quantum,
    metaphysical, or physics-derived security meaning.
H4  Publication recovery is permitted only via a separately authorized, structurally publication-only, non-automatic process
    that can verify and project committed evidence but is structurally incapable of any scientific execution; it requires a new
    docs-only publication-projection authorization and never runs automatically after a crash.
H5  Contradiction between primary and emergency evidence = CONTRADICTORY_EVIDENCE: no verdict assertion, no auto-reconciliation,
    no publication, no execution recovery, no auto-retry, no evidence deletion/repair; both channels retained byte-for-byte;
    operator forensic review required; only conservative mutually-supported facts may be stated.
```

*End of decision record v0.1. Docs-only. No repository change, execution, manifest access, publication, or scientific reconstruction was performed in producing this record.*
