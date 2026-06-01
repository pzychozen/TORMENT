# Cluster 5 §9.3 Path C — Q3-D1 Affect-Attribution Contract v0.1

**Status:** Tracked framing artifact. Advisory design contract. **Not** an
implementation authorization. Ratified for tracked promotion by trio
(pzychozen + GPT/Codex + Claude) on 2026-06-01.
**Date:** 2026-06-01
**Gate:** Cluster 5 §9.3 Path C → Q3 (affect attribution) → Q3-D → **Q3-D1**.
**HEAD at promotion:** `329af0e` (defect #1 affect-state helper restoration closed).
**Mode:** Framing-only. No code, schema, scoring change, reinforcement change,
promotion change, tests, or migration authorized by this artifact. Implementation
(starting at D1-S1) requires separate trio authorization after this artifact is
committed and pushed.
**Lineage:** Promoted from the revised local-only scratch framing draft
`scratch/brainstorming/2026-06-01_q3_d1_affect_attribution_contract_framing.md`
(local-only; not authority on its own).
**Anchors:** `docs/CLUSTER_5_PATH_C_GOVERNANCE_PRESERVATION_FRAMING_v0.1.md`
(invariant + §4.1 acceptance test), Track A v0.1, Cluster 2 v0.1, Track B v0.1,
Cluster 5 v0.1, Ledger Observational-Boundary Doctrine v0.1.

---

## 1. Purpose and problem statement

Q3-A established the structural gap, phrase of record:

> *The system remembers the emotional tag, but not who had the right to say it
> was true.*

Affect today is `Affect(tag, conf)` only — inference-only (keyword classifier),
stored as top-level payload fields **outside `ProvenanceV1`**, with the
`affect_conf` float standing in for attribution. Consumers cannot distinguish
inferred from confirmed, fresh from echoed, or "whose" emotion it is.

**Q3-D1 defines the attribution *contract* only:** the orthogonal dimensions that
record *how* an affect value was produced and *whether* it was confirmed, plus
conservative defaults for every current producer. It does **not** change
behavior, scoring, reinforcement, or promotion. Reinforcement reconciliation (D2)
and archive emotional-promotion authority (D3) are parked and depend on this
contract existing first.

Governing posture:

```
TORMENT is character memory first, agent memory second.
Memory may shape context. Memory may not seize authority.
Audit observes authority. Audit does not become authority.
Automatic is allowed. Autonomous is not.
```

---

## 2. Current affect surface (verified, HEAD 329af0e)

- **Primitive:** `affect.py` `Affect(tag: str, conf: float)`; `classify_affect()`
  keyword-counts → one of `neutral, calm, stressed, excited, sad, angry`;
  `conf = best/(best+1)`. Always inferred. Insufficient signal collapses to
  `neutral, 0.0`; the producer does **not** distinguish "stored neutral",
  "no-signal neutral", and "ambiguous neutral".
- **Ordinary ingest writer:** classifier call at `torment_service/fabric.py:2576`;
  stored affect fields at `torment_service/fabric.py:2794`. Gated by
  `TORMENT_AFFECT_ENABLE` (default on). Ingest may write
  `affect_tag=None`, `affect_conf=None` when no meaningful affect is detected.
- **mood_drift writer:** `torment_service/fabric.py:1571` (within
  `_maybe_emit_mood_drift`); emits a `type="mood_drift"` row carrying affect +
  `mood_from`/`mood_to`, derived from the ingest classification.
- **Behavioral side-state:** `affect_state.json` via `_load_affect_state` /
  `_save_affect_state` (restored at `329af0e`); truncated `last_tag` +
  `drift_hist` point-state for mood-drift / mood-spiral. Not a memory row.
- **Retrieval consumers:** `scoring.py` affect-match bonus, mood-drift bonus,
  mood-spiral penalty; gated on `affect_conf >= 0.40`. (Context-shaping.)
- **Deep export:** `deep_memory.py` carries affect, strips governance/provenance
  (Q1). Deep rows are display-only retrieval echoes under the existing Q1 markers.
- **Generic `user_confirmed` feedback boundary:** `torment_service/fabric.py:4391`;
  confirms *memory usefulness*, disjoint from affect.
- **No producer** writes asserted, confirmed, measured, or "whose" affect.

---

## 3. Orthogonal contract dimensions

Keep these **separate** — never a single flat enum. A value may be
`system / inferred / unconfirmed` at write time and later become `confirmed` by a
`user` while remaining `inferred` in origin. Flattening would lose that.

```
value_state:
- set         a meaningful affect value is stored on the row
- unset       no meaningful stored affect value; affect_tag is missing OR null
              (current ingest may write affect_tag=None, affect_conf=None)
- ambiguous   explicitly announced uncertainty
              RESERVED — not produced until a real producer exposes it
              (the classifier today collapses insufficient signal to neutral,0.0)

origin_kind:
- inferred    produced from content by the classifier
- asserted    an actor structurally stated it        [no producer yet]
- derived     computed from other affect (e.g. a drift transition)
- recovered   legacy fallback OR an actual recovery interpretation ONLY
              (NOT an ordinary deep echo — see §6)
- measured    RESERVED only; no tracked producer exists today

actor:
- user | system | agent | migration | operator

actor_reference:                 (companion identity for the actor)
- optional for system / migration, where the actor class alone is sufficient
- required when a future user / agent / operator assertion must be auditable
- conceptual anchor: existing provenance precedent such as `asserted_by`

subject:                         (whose emotion the value is about)
- user
- unknown                        default for inference: a classifier can detect
                                 emotion in text without knowing whose

confirmation:
- unconfirmed
- confirmed

confirmation_actor:
- actor class for the confirmer (user | system | agent | migration | operator)
- required when confirmation = confirmed

confirmation_actor_reference:
- a stable auditable identity / source reference
- required when confirmation = confirmed
- a generic actor class WITHOUT the stable reference is INVALID
  (e.g. confirmation_actor=user, confirmation_actor_reference=user:<stable-id>)

via:                             (stable producing-method / derivation token)
- required on every posture; stable tokens, not free prose
- known tokens: ingest_affect_classifier, mood_drift_transition,
  legacy_read_fallback; future confirmation events carry a stable via or
  evidence reference

affect_conf:
- the existing certainty float; certainty metadata ONLY; never authority
```

**Binding rules:**

```
origin is not authority
certainty is not authority
asserted is not confirmed
confirmation must bind explicitly (confirmation_actor + confirmation_actor_reference)
deep echoes remain non-authoritative until source-row rehydration
affect_state.json is derived behavioral side-state, never confirmation authority
generic user_confirmed feedback must never silently confirm affect
```

---

## 4. Producer-default table

| Producer | value_state | origin_kind | actor | actor_reference | subject | confirmation | via |
|---|---|---|---|---|---|---|---|
| Ordinary ingest | `set` if affect stored, else `unset` | `inferred` | `system` | none (class sufficient) | `unknown` | `unconfirmed` | `ingest_affect_classifier` |
| mood_drift row | `set` | `derived` | `system` | none (class sufficient) | `unknown` | `unconfirmed` | `mood_drift_transition` |
| Legacy row, affect present | `set` | `recovered` | `migration` | none (class sufficient) | `unknown` | `unconfirmed` | `legacy_read_fallback` |
| Legacy row, affect absent | `unset` | `recovered` | `migration` | none (class sufficient) | `unknown` | `unconfirmed` | `legacy_read_fallback` |

`confirmation_actor` / `confirmation_actor_reference` are unset in all current
producers — nothing confirms affect today, so steady state is `unconfirmed`.

**Prose is not assertion.** A self-report such as `"I feel sad"` must NOT
auto-become `origin_kind=asserted`. There is no structured assertion writer; the
classifier reading that text remains `inferred`. `asserted` is reserved for a
future explicit structured-assertion path that also sets `actor_reference`.

`ambiguous` and `measured` are contractually defined but **not produced** today.
Do not claim distinctions the current producer does not make.

---

## 5. Legacy fallback contract (read-time only, fail-loud on malformed)

Fallback applies **only when attribution is absent or null**. A row with no
attribution fields is interpreted at read time as:

```
origin_kind = recovered
actor       = migration
subject     = unknown
confirmation= unconfirmed
via         = legacy_read_fallback
value_state = set if a meaningful affect value is stored else unset
```

This is a **reader-side default**, NOT a bulk backfill or write migration (bulk
migration is out of scope).

**Fail-loud rule:** a *present but malformed* explicit affect-attribution
envelope must **raise**, not silently downgrade into legacy fallback. Malformed
includes: invalid enum values; missing required keys; inconsistent
`tag`/`value_state` combinations; `confirmation=confirmed` without complete
binding metadata; `confirmed` without BOTH `confirmation_actor` (class) and
`confirmation_actor_reference` (stable reference).

---

## 6. Deep snapshot / rehydrate posture

Reuse the existing **Q1 deep markers exactly** — do NOT invent a second
affect-specific deep-join mechanism:

```
authoritative        = false
requires_rehydration = true
role                 = retrieval_echo
```

Attribution interpretation:

```
routine deep echo:
  display-only, non-authoritative;
  PRESERVES the source-row affect attribution snapshot (does not relabel it);
  must rehydrate before any authority use.

rehydrated source row:
  returns its original attribution unchanged.

recovered:
  reserved for legacy fallback or an actual recovery interpretation — NOT for
  an ordinary deep echo.
```

Relabeling an ordinary deep echo as `origin_kind=recovered` is forbidden: it
would erase the source row's real origin.

---

## 7. mood_drift attribution

`mood_drift` rows are `origin_kind=derived`, `actor=system`, `subject=unknown`,
`confirmation=unconfirmed`, `via=mood_drift_transition`. A legitimate derived
signal, low-authority, never self-confirming. Retrieval consumers are unchanged
by this contract (see §10).

---

## 8. affect_state.json non-authority rule

`affect_state.json` is **derived behavioral point-state** (truncated `last_tag` +
`drift_hist`) feeding mood-drift emission and mood-spiral input. It is fail-soft
and never a memory row. It **may never**:

- populate confirmation fields;
- satisfy confirmation binding;
- override row attribution.

It remains truncated fail-soft behavioral point-state only.

---

## 9. Confirmation-event binding requirements

`confirmation=confirmed` requires an **explicit affect-confirmation event** that:

- names `confirmation_actor` (actor class, required when confirmed);
- carries `confirmation_actor_reference` (stable auditable identity/source
  reference, required when confirmed) — a generic actor class without the stable
  reference is invalid (e.g. `confirmation_actor=user`,
  `confirmation_actor_reference=user:<stable-id>`);
- carries a stable `via` or evidence reference;
- targets a specific affect value/row;
- is distinct from the generic `used_successfully` / `user_confirmed` feedback
  (which confirms memory usefulness, not affect truth).

`asserted ≠ confirmed`. **No confirmation writer is built by this contract.** A
`confirmed` envelope lacking complete binding metadata is malformed and must
raise (§5).

---

## 10. Scoring-invariance guarantee

Introducing the attribution dimensions must **not** change scoring results.
Guarantee is stated as **controlled numerical equality** (not byte-identical
responses) across these parity surfaces, with attribution fields present vs
absent:

```
affect_match_bonus
mood_drift_bonus
mood_spiral_penalty
final retrieval score
trace continuity breakdown
identity-anchor affect-sensitivity behavior
```

Attribution is **recorded and audit-visible only**; it never becomes a scoring or
authority input (Ledger Observational-Boundary Doctrine §3). Any future use of
`confirmation` to influence promotion is Q3-D3, separately ratified.

---

## 11. Staged implementation plan (FRAME ONLY — not authorized by this artifact)

Scoring-invariance guards begin in **S1**.

```
D1-S1: contract validator + read shim + malformed-envelope (fail-loud) tests
       + baseline parity harness (the §10 surfaces captured before any stamping)
D1-S2: ordinary-ingest stamping (system/inferred/unconfirmed/subject=unknown/
       via=ingest_affect_classifier) + parity assertions
D1-S3: mood_drift stamping (system/derived/unconfirmed/via=mood_drift_transition)
       + extension of the restored affect-state regressions (329af0e)
D1-S4: deep-rehydrate conformance using the existing Q1 markers;
       echo preserves source attribution snapshot
D1-S5: cross-surface conformance + generic user_confirmed isolation + full suite
```

Each slice is independently ratifiable; S1 is the foundation. No slice changes
scoring, reinforcement, or promotion behavior. Schema shape (sibling fields vs
nested dict vs `ProvenanceV1` extension) is deferred to S1 design, not chosen
here. **Implementation authorization is a separate gate** after this artifact is
committed and pushed.

---

## 12. Required falsifiers (before any patch lands)

- Ordinary ingest → `system / inferred / unconfirmed / subject=unknown /
  via=ingest_affect_classifier`; `value_state=set` when affect stored, else
  `unset` (affect_tag missing or null).
- mood_drift → `system / derived / unconfirmed / via=mood_drift_transition`.
- Legacy row with affect → `recovered / migration / unconfirmed / set /
  via=legacy_read_fallback`; without affect → same but `unset`.
- Deep echo → Q1 markers; preserves source attribution snapshot; NOT relabeled
  `recovered`; authority use requires rejoin.
- **Fail-loud:** malformed explicit envelopes raise (invalid enums; missing keys;
  inconsistent tag/value_state; `confirmed` without BOTH `confirmation_actor`
  (class) and `confirmation_actor_reference` (stable reference)) — never silent
  downgrade to legacy fallback.
- Generic `user_confirmed` feedback does NOT set affect `confirmation=confirmed`.
- `asserted` never auto-equals `confirmed`; prose `"I feel sad"` stays `inferred`.
- **Scoring-invariance (numerical equality)** across the §10 surfaces.
- `affect_state.json` cannot populate/satisfy confirmation or override row
  attribution.

---

## 13. Explicit exclusions (kept closed)

```
Q3-D2 duplicate changed-affect handling
Q3-D3 archive emotional-promotion authority
promotion.py patches
reinforcement patches
confirmation writers
bulk migration
scoring changes
Track B
Cluster 2 v0.2
Cluster 5 v0.2 mechanisms
atomic-write hardening
```

No code, schema, staging, or commit authorized by this artifact.

---

## 14. Parked D2 / D3 questions (named, not opened)

- **D2 — duplicate changed-affect handling.** When incoming text deduplicates
  into an existing row but inferred affect differs, the candidate options are:
  preserve initial / replace / append observation history / aggregate / force a
  new row / another explicit rule. **Options only — this contract takes no
  position.** Depends on D1 attribution existing. Parked.
- **D3 — archive emotional-promotion authority.** Archive promotion
  **independently classifies raw chunk text; it does not consume the stored row
  affect value** (`evaluate_promotion` calls `classify_affect(chunk_text)`). The
  D3 question is whether that independently-inferred affect stays score-inert
  (current, since `f462b31`), advisory/audit-visible only, or may contribute only
  after confirmation under a bounded authority rule. Inferred affect must not,
  alone, elevate archive→core. Parked.

---

## 15. Doctrine status and notes

This is a tracked framing contract, not a doctrine promotion of the four-doctrine
spine and not an implementation authorization. It sits adjacent to the
governance-preservation framing (`CLUSTER_5_PATH_C_GOVERNANCE_PRESERVATION_FRAMING_v0.1.md`,
which remains locked and unchanged) as the Q3-D1 resolution.

The autonomy boundary that applies is: *Automatic is allowed. Autonomous is not.*

---

*End of Q3-D1 Affect-Attribution Contract v0.1. Tracked framing artifact. No
implementation authorized; D1-S1 authorization is a separate gate after commit
and push.*
