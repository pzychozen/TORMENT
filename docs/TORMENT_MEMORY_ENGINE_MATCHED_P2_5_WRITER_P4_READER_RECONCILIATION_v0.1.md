# TORMENT Memory Engine — Matched P2.5 Writer / P4 Reader Reconciliation v0.1

**Status:** TRACKED RECONCILIATION ARTIFACT — promoted docs-only 2026-06-15. It pairs P2.5
write-side conformance findings with P4 read-side requirements; records matched pairs, tensions,
and later-owner routing only. Authorizes no implementation, selects no mechanics, opens no
adjacent gate, and amends no registry except the separate §N13 closure registration.
Windows-visible tracked repo state remains authoritative.

**Gate:** Candidate A — Matched P2.5 Writer / P4 Reader Reconciliation was selected as a docs-only
reconciliation gate and is **closed by this promotion**. Active gate after promotion: **none**;
next gate: **unselected**. Promoted at main lineage `3aac6b2` (pre-promotion HEAD; apply-time HEAD
must be confirmed still `3aac6b2` before apply — see apply note).

**Scope red line (load-bearing, verbatim):**

> This artifact may compare writer-side findings with reader-side requirements. It may not fix
> writers, enforce readers, select carriers, answer parked P2.5 questions, or convert
> inspectability into projection.

**Additional scope red line (load-bearing, verbatim):**

> Pairing is not conformance. Routing is not authorization. Later-owner naming does not open the
> later owner's gate.

**Label-evidence boundary (load-bearing):**

> Existing runtime or doctrine labels such as `eid`, `identity_anchor`, `diagnostic_only`,
> `update_payload`, and `embedding_checksum` are cited only as seam evidence. This artifact
> creates no field names, endorses no existing label as a future representation, and selects no
> carrier or schema.

**Lineage:** P2.5 Cross-Contract Reconciliation v0.1 (`...P2_5_CROSS_CONTRACT_RECONCILIATION_v0.1.md`)
+ P4 Reader and Projection Safety Contract v0.1 (`...P4_READER_PROJECTION_SAFETY_CONTRACT_v0.1.md`)
+ pre-P4 reader-dependency trace (registry §N4) + Document A write-side authority obligations →
gate-framing plan (Codex ACCEPT WITH REQUIRED CORRECTIONS, applied) → draft → GPT ACCEPT WITH
REQUIRED CORRECTIONS (applied) → Codex ACCEPT WITH REQUIRED CORRECTIONS (applied) → operator
promotion (this artifact). The framing plan, the working-folder drafts, and the P2.5/P4 framing
reports remain non-load-bearing evidence lineage.

**Tags:** `[FACT]` traced/contract-grounded · `[PAIR]` matched writer↔reader obligation ·
`[TENSION]` · `[PARKED]` owned elsewhere, routed not resolved · `[ROUTING]` later-owner ·
`[DISTINCTION]` controlled non-collapse · `[NON-DECISION]` · `[FINDING]` evidence, not authority.

---

## 0. Status and non-authorization boundary

`[NON-DECISION]` This is a **bounded reconciliation artifact**. It records inspected pairings and
routing only. It is **not** a contract, **not** a writer fix, **not** a reader enforcement layer,
**not** a carrier/schema/store design, **not** an answer to P2.5's parked questions, and **not** a
gate beyond this now-closed docs-only reconciliation. It selects no mechanics and adds no
obligations; it *pairs* obligations that already exist in P2.5, P4, and Document A.

The scope red lines above govern the entire artifact.

## 1. Purpose: pair write-side conformance findings with read-side requirements

`[FACT]` P2.5 established the **write-side** picture: canonical P1/P2 carrier vocabulary is absent
across the inspected `torment_service` surfaces; several durable families carry identity
*analogues*; none is proven conformant (P2.5 §2). P4 established the **read-side** requirement
edge: what a reader or derived writer must prove before *using* a stored reference, and what must
stay visible when it cannot (P4 §2). This artifact answers one bounded question: **for each focus
surface, which P2.5 write-side finding pairs with which P4 read-side obligation, and where does
the unresolved remainder route?** It resolves nothing mechanical and fixes nothing.

## 2. Source contracts and inherited posture

`[FACT]` Inputs (carried, not redefined):

- **P2.5** — tracked reconciliation artifact; "records; it does not rule" (§9). Headline:
  *analogue ≠ canonical carrier* (§2). eid concern classification (§6); `embedding_checksum`
  do-not-promote (§5); later-owner routing (§7); parked Q-2/Q-3/Q-4 (§8).
- **P4** — requirement-level reader/projection contract; five obligations O1–O5 + a contract-wide
  non-coercion invariant (§4–§5); `diagnostic_only` eligibility-posture values layer (§9);
  surface-local / family-bound, no central ReaderPolicy engine (§7).
- **Document A** — write-side containment wall; A-O1 class-bound writer authority (authorization
  not inferred from payload flags or source presence); A-O4 writer-authority pairs with P4's
  read-side obligations. (Cited as the write-side requirement frame P2.5 findings sit under.)
- **P1/P2 vocabulary** — local `eid` is a reusable handle, never sufficient sameness;
  memory-lineage identity; record-revision identity; revision fingerprint; `era_ref` (P4 §2).

`[DISTINCTION]` This artifact is the *matched pair* of P2.5 and P4; it does not re-do identity
vocabulary (P1/P2), is not a storage-design phase (P4 §2), and is not a writer slice (P2.5 §7).

## 3. Controlled distinctions carried

`[DISTINCTION]` Carried verbatim from the inputs; collapsing any is drift:

```
presence ≠ sameness                              (P4 §3)
analogue ≠ canonical carrier                      (P2.5 §2)
caller-visible ≠ automatically prompt-visible     (P4 §3)
diagnostic intent ≠ guaranteed non-reentry        (P4 §3)
diagnostic_only (eligibility posture) ≠ projection instruction   (P4 §9)
inspection ≠ projection                           (Document A A-I1; P4 O3/O4)
persistence ≠ cognition eligibility               (Document A §2; P4 O1/O5)
audit visibility ≠ audit authority                (P4 §3; Ledger)
audit observes authority; audit does not become authority   (P4 §5; Ledger)
writer authority ≠ payload-flag / source presence (Document A A-O1)
```

## 4. The matched-pair map

`[PAIR]` Writer-side finding (P2.5 / Document A) ↔ read-side obligation (P4). Working inventory,
not a conformance verdict.

| Surface | Write-side finding | Read-side obligation | Matched status (working) |
|---|---|---|---|
| DeepMemoryEcho | borrowed source `eid` + presence-only validation = **confirmed durable-sameness overload** (P2.5 §6; SE absent §4) | **O1** echo source-sameness before ordinary cognition; presence insufficient | paired; both name the same seam from opposite sides |
| Motif-derived identity anchor | derived path resolves member eids by presence (P2.5 §6 family C / registry §N4) | **O2** source-membership sameness under family-bound adequacy standard | paired; derived-writer ↔ reader-membership |
| Writer authority / write-site | canonical carriers absent; analogues unproven; *analogue ≠ canonical carrier* (P2.5 §2/§4) | Document A **A-O1/A-O4** class-bound writer authority, matched to P4 read-side | paired at requirement level; conformance unproven, **stamping not in scope** |
| Projection surfaces | caller-visible payload spread; operational/audit ledgers (P2.5 §4 class D; Q-3) | **O3** intent+capability classification; **O4** explicit projection gating | paired; both forbid accidental default exposure |
| Orphan / mismatch / unprovable | eid concern classification; suspected `update_payload` lineage gap (P2.5 §6) | **O5** observability (no silent entry, no invisible disappearance, operator-auditable) + **§9** `diagnostic_only` default | paired; write-side gap ↔ read-side observability + eligibility posture |

## 5. Surface-by-surface reconciliation

### 5.1 DeepMemoryEcho `[PAIR]` `[FACT]`
P2.5 §6 names "borrowed eid + presence-only validation" as the **confirmed durable-sameness
overload** (the H-1 revival surface); P2.5 §4 records source-evidence (SE) absent (source eid
only). P4 **O1** requires source-sameness proven before an echo contributes to ordinary cognition,
presence of a reusable `eid` being insufficient. **Match:** the write-side overload is exactly the
condition O1 forbids relying on; the two contracts describe one seam. `[NON-DECISION]` Neither the
evidence carrier nor the comparison mechanism is selected here (P4 O1 explicit; P2.5 §9).

### 5.2 Motif-derived identity-anchor emission `[PAIR]` `[FACT]`
Registry §N4 / P2.5 §6 (family C adjacency) establish a *separate, derived* cognition-affecting
reusable-eid path: motif member eids resolved by presence, distilled into a durable
`identity_anchor`. P4 **O2** requires source-membership sameness "under the applicable
family-bound source-sameness adequacy standard," with no central mechanism and no motif redesign.
**Match:** derived-writer membership resolution ↔ reader-side membership-sameness requirement.
`[TENSION]` derived anchors reach cognition through ordinary tiering (registry §N4) — so the pair
must be read together with the §6 non-coercion invariant, not as a standalone fix. `[ROUTING]`
any motif/anchor *code* change is out of scope (gate red line; P4 "no motif redesign").

### 5.3 Writer authority / write-site conformance `[PAIR]` `[TENSION]`
P2.5 §2/§4: canonical P1/P2 carriers absent; analogues present but unproven; *analogue ≠ canonical
carrier*. Document A **A-O1** requires writer authorization by *class*, never inferred from payload
flags or source presence; **A-O4** makes write-side the matched pair of P4's read-side. **Match:**
the write-side absence P2.5 found is the unresolved requirement-level gap A-O1/A-O4 require later
owners to account for. `[TENSION]` "write-site conformance" must not be read as authorizing write-site stamping:
P2.5 §7 binds stamping to *after carrier design* (P6). This artifact pairs the obligation; it does
not stamp, fix, or enforce. `[NON-DECISION]` no carrier; `embedding_checksum` stays
do-not-promote (P2.5 §5).

### 5.4 Projection surfaces `[PAIR]` `[DISTINCTION]`
P2.5 §4 records caller-visible payload spread and a class-D ledger population whose
record-vs-audit status is parked (Q-3). P4 **O3** requires classification by *both* intent and
re-entry capability (a diagnostic/trace label is not a safety boundary); **O4** requires identity/
substrate fields to become prompt- or caller-visible only through explicit, surface-classified
projection, never by default payload spread; **§9** defines `diagnostic_only` as an **eligibility
posture, not a projection instruction**. **Match:** write-side default-exposure risk ↔ read-side
explicit-gating requirement. `[DISTINCTION]` inspection ≠ projection; no diagnostic label and no
`diagnostic_only` posture converts to model visibility (gate red line). `[PARKED → P4/Q-3]` which
class-D ledgers are governed records vs audit evidence is **not answered here**.

### 5.5 Orphan / mismatch / sameness-unprovable `[PAIR]` `[FACT]`
P2.5 §6: allocator reconstruction (`max_eid+1`) enables handle reuse after trailing-row loss;
`update_payload` same-eid re-append is a suspected lineage gap (reader trace required before any
stronger claim). P4 **O5**: an unresolved/mismatched/unprovable reference must not silently enter
cognition, must not invisibly disappear, and must remain operator-auditable; **§9** defaults such
a reference to `diagnostic_only` eligibility until an explicit audited governance action restores
it. **Match:** the write-side reuse/lineage hazards are exactly the references O5 must keep visible
and §9 must keep non-cognition-eligible-by-default. `[NON-COERCION]` withholding from context is
allowed; output-blocking, invisible deletion, and permanent lock are not (P4 §5). `[ROUTING]`
recovery/quarantine/edge-repair mechanics → P5a; the `update_payload` reader trace → P4/Q-4 lane.

## 6. Cross-cutting non-coercion invariant check

`[FACT]` P4 §5 governs O1–O5 and is applied here to **both** sides at once: a write-side gap may
be handled by *withholding* an unverified reference from cognition (allowed), but never by silent
output blocking, invisible deletion of evidence, covert suppression of evidence/eligibility state,
authority seizure, or personality lock. `[DISTINCTION]` An audit/observability surface (P4 O5;
P2.5 class-D ledgers) may witness authority but may not become authority over cognition. This
check is the single anchor that keeps "matching writer and reader" from sliding into "enforcing"
either: the artifact pairs requirements; satisfaction stays family-by-family and later-owned.

## 7. Tensions and parked questions

`[TENSION]`
1. **Write-side timing vs read-side requirement.** P4 read-side obligations are stated now;
   P2.5 §7 binds write-site stamping to after-carrier (P6). The pair is real; the *later-work*
   sequence is reader-requirement-first, writer-stamping-after-carrier. Recorded, not resolved.
2. **Derived anchors reach cognition via ordinary tiering** (§5.2) — O2 + non-coercion must be
   read jointly; not a standalone obligation.
3. **`diagnostic_only` overload** across P4 §9 / registry §H / Stage A — eligibility posture only;
   easy to collapse into a status value. Anti-drift wording carried (§3).

`[PARKED]` Owned elsewhere; **this artifact routes, it does not answer** (gate red line):
- **Q-2** (closure `closure_id`/`version_id` — prior art or later reference shape?) → P2.5/P6 lane.
- **Q-3** (which class-D ledgers are P2-governed records vs audit evidence?) → P2.5/P4 lane.
- **Q-4** (any reader beyond DeepMemoryEcho relying on eid sameness?) → P4 lane (its own trace).

## 8. Matched-obligation inventory (working inventory only)

`[FINDING]` Not authority, not a conformance matrix.

| # | Write-side (P2.5 / Document A) | Read-side (P4) | Later owner of the *mechanics* |
|---|---|---|---|
| M-1 | DeepMemoryEcho borrowed-eid overload | O1 echo source-sameness | P6 carrier; P5a recovery adjacency |
| M-2 | motif member presence resolution | O2 membership sameness | family slice after carrier (P6); P4 reader trace |
| M-3 | analogue ≠ canonical carrier; A-O1/A-O4 | read-side pairing of writer authority | P6 carrier question; separately authorized family write-site conformance slices only after carrier design |
| M-4 | caller-visible payload spread; class-D ledgers | O3 intent+capability; O4 explicit projection | P4 later runtime conformance to O3/O4; P6 carrier mechanics only if separately opened |
| M-5 | allocator reuse; `update_payload` lineage gap | O5 observability; §9 `diagnostic_only` default | P5a recovery; P4 trace; P9 migration (cursor) |

## 9. Later-owner routing (what this gate does NOT do)

`[ROUTING]`
```
carrier / fingerprint / identity-token / serialization / allocator mechanics → P6
write-site stamping (per family)                                             → family slices, AFTER carrier (P6)
recovery / reconciliation / quarantine / edge-repair                         → P5a
migration execution / cursor-semantics transition                            → P9
runtime reader/projection conformance to O1–O5                               → later P4-owned runtime conformance
update_payload reader trace; Q-4                                             → P4 lane
gravity_correction automatic-canon                                          → its own audit-first slice (untouched here)
embedding_checksum ↔ fingerprint relationship                                → P6 (stays do-not-promote)
```

## 10. Findings (evidence, not authority)

`[FINDING]`
- **The five focus surfaces pair cleanly.** Each P2.5 write-side finding has a matching P4
  read-side obligation (M-1…M-5); no contradiction between the two contracts was found.
- **The match is requirement-level only.** Every pair resolves to "must be proven / must be
  classified / must stay observable" — none selects a carrier or mechanism, consistent with both
  source contracts.
- **The reconciliation is reader-requirement-first.** P4 obligations stand now; writer stamping
  is carrier-gated (P6). Any later work, if separately opened, must preserve this dependency
  order: requirement-pairing before any carrier proposal; any carrier proposal before family
  write-site conformance; and reader/projection runtime conformance remains separately authorized.
- **No new obligation is created**, and the three parked P2.5 questions remain owned elsewhere.

## 11. Non-authorizations and red lines

`[NON-DECISION]`
```
No implementation, no tests, no runtime patch, no executable probe.
No carrier / schema / store / field / enum / serialization design or selection.
No fingerprint algorithm; no identity-token / UUID / ULID; no allocator mechanics.
No migration. No write-site stamping (carrier-gated → P6).
No carrier promoted from any analogue; embedding_checksum stays do-not-promote.
No ReaderPolicy implementation or centralized reader/writer engine.
No model visibility derived from inspectability; no projection from a diagnostic label.
No audit-derived authority.
No gravity_correction / mood_drift / promote_chunk / identity-anchor code touched.
No Stage B, no database design, no MCP action surface, no automation, no autonomy.
No adjacent gate opened by this artifact beyond the closure of Candidate A; the separate §N13
  registry entry records that closure and this promotion authorizes none of the later owners' gates.
No answer to parked P2.5 Q-2 / Q-3 / Q-4 (routed, not resolved).
All classifications are working reconciliation labels, not frozen taxonomy or conformance verdicts.
```

Scope red line restated: *This artifact may compare writer-side findings with reader-side
requirements. It may not fix writers, enforce readers, select carriers, answer parked P2.5
questions, or convert inspectability into projection.*

## 12. Sequencing recommendation (advisory only)

`[ROUTING]`
```
this matched reconciliation is closed docs-only
→ active gate none; next gate unselected
→ any later P6 carrier design, family write-site conformance, runtime reader/projection conformance,
  gravity_correction audit-first slice, Stage B, database design, or migration requires its own
  separate bounded decision
```
Advisory only. This artifact is no authority over gate selection; naming a later owner opens no
later owner's gate.

## 13. Evidence lineage

`[FACT]` Read at `3aac6b2`: P4 Reader and Projection Safety Contract v0.1 (full); P2.5
Cross-Contract Reconciliation v0.1 (full); pre-P4 reader-dependency trace findings via registry
§N4; Document A A-O1/A-O4; the gate-framing plan and working-folder drafts. Framing reports, the
framing plan, and the working-folder drafts remain non-load-bearing evidence. This artifact
authorizes nothing further and opens nothing; runtime conformance and all substrate mechanics are
later-owned.

*End — Matched P2.5 Writer / P4 Reader Reconciliation v0.1. Promoted docs-only 2026-06-15; closure
registered at registry §N13. docs-only, reconciliation-only. No writer fix, no reader enforcement,
no carrier selection, no parked-question answer, no inspectability→projection. Subsequent versions
require their own trio ratification.*
