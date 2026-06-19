# Checkpoint — Role-Inference / Identity-Anchor Cadence Influence Trace (read-only)

**READ-ONLY CHARACTERIZATION — docs-only consolidated influence map. No code, no tests, no
implementation, no runtime execution, no remedy, no Writer-Authority continuation, no identity-anchor
behavior change, no role tuning, no registry amendment.**

**Date:** 2026-06-19. **Baseline HEAD = origin/main = `ce337fa`** (*docs(seed): checkpoint authored
seed-content stability lock*).

> Memory may shape context. Memory may not seize authority.

---

## 1. Status and scope

This is a **static, source-grounded characterization** of how **soft role inference** originates,
persists, is scored, and modulates the **cadence** of derived identity-anchor emission — and how that
reaches memory/prompt only **indirectly**. It is **characterization, not implementation**: it changes no
behavior, proposes no remedy, tunes no constant, and does not continue Writer Authority or touch the H2
identity-anchor emitter. **Nothing was executed** — no ingest, no query, no endpoint call, no service
start.

## 2. Source surfaces

- `torment_service/roles.py` — `RoleStore`, `RoleStore.load`, `RoleStore.save`, `update_from_text`,
  `dominant_role`, `role_multipliers`.
- `torment_service/fabric.py` — ordinary-ingest role update from summary text (~2573-2580);
  `_maybe_emit_identity_anchor` (1382); the role-modulated cadence thresholds (1404-1410); derived
  identity-anchor emission (1519-1550).
- Read surfaces (source-confirmed): the `GET /agent/{agent_id}/roles` endpoint (`app.py:600-615`);
  `fabric.query()["role_context"]` (`fabric.py:4458`, via `_role_context` at 1353-1362); the
  continuity / query-signature debug field `qsig["dominant_role"]` (`fabric.py:4351-4352`).

## 3. Origin / update

Role state is **not** created only by ingest. `RoleStore.load()` (roles.py:87-103) **may create and
save a default `roles.json`** if none exists, returning an explorer-biased default profile. Ordinary
ingest then **updates the role profile from the ingest summary text** (not the raw input text):
`fabric.py:2573-2580` loads the profile, calls `update_from_text(_rp, summary)`, and saves — wrapped in
try/except (non-fatal).

Role inference is **deterministic, offline, and model-free** keyword scoring over lowercased text.
`update_from_text` (roles.py:112-144) tallies keyword hits per role, normalizes to a distribution, and
folds it into the stored scores via a slow EMA. Roles: **planner, explorer, reflector, tinkerer,
storyteller, minimalist**. A **default explorer bias** exists (default scores 0.30 for explorer vs 0.10
for others; an unmatched sample counts as explorer). The EMA rate is `TORMENT_ROLE_EMA` with **default
0.18**, **clamped to 0.02–0.5**.

## 4. Durability

Persisted **per agent** at `data/workspaces/<ws>/agents/<ag>/roles.json` (path-validated via
`safe_slug` + `ensure_within_base`). It is a **durable-soft point-state** file — its current contents
are the latest state.

**Storage caveat (preserved):** `RoleStore.save` uses a raw `open("w") + json.dump` (roles.py:105-110),
which truncates to zero bytes at open time; this is the **`IDENTITY-NON-ATOMIC-SAVE`** class covered in
`docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md`. **Durable-soft does not imply crash-safe, pinned,
protected, or canon.**

## 5. Scoring

`dominant_role` (roles.py:146-149) is the **argmax** of the score map, with an **explorer fallback** for
an empty/missing profile. `role_multipliers` (roles.py:151-169) maps the dominant role to
`{anchor_count_mult, anchor_gap_mult}`:

| dominant role | anchor_count_mult | anchor_gap_mult |
|---|---|---|
| minimalist | 1.35 | 1.40 |
| planner | 1.15 | 1.10 |
| reflector | 0.90 | 0.90 |
| storyteller | 0.95 | 1.00 |
| tinkerer | 1.05 | 1.05 |
| explorer / default | 0.95 | 0.95 |

Higher `count_mult` → fewer anchors; higher `gap_mult` → anchors less often.

## 6. Influence path

`_maybe_emit_identity_anchor` (fabric.py:1382) reads the dominant role and its multipliers. Base cadence
comes from env: `TORMENT_ID_ANCHOR_MIN_COUNT = 3`, `TORMENT_ID_ANCHOR_MIN_GAP_STEPS = 50`. Role
modulation **scales the base count/gap thresholds** (fabric.py:1404-1410):

- `min_count = max(2, round(min_count * anchor_count_mult))`
- `min_gap = max(10, round(min_gap * anchor_gap_mult))`

So the role multipliers set the **base** count/gap thresholds (with hard floors count ≥ 2, gap ≥ 10),
in a try/except that falls back to unmodulated on failure. Those thresholds then gate emission
(agent_count < `_min_count` → skip; step − last_step < `_min_gap` → skip).

**Affect-sensitive motif tightening (fabric.py:1440-1468) is a later, independent modifier inside the
same identity-anchor emitter** — it can further raise the thresholds for affect-toned motifs. **Role
modulation and affect-sensitivity are kept separate**; they are distinct mechanisms that happen to act
on the same gates.

## 7. Emission posture

Role inference itself **writes no graph memory and no canon**, and **emits no model-visible prompt text
by itself**. Its only memory/prompt-shaping pathway is the cadence modulation above.

It does have **diagnostic / read-surface exposure**: `GET /agent/{agent_id}/roles`;
`fabric.query()["role_context"]`; the continuity / query-signature debug `dominant_role`. These are
reporting surfaces, not authority crossings.

Stated precisely: **role inference's memory/prompt-shaping effect is indirect, through derived
identity-anchor cadence; it additionally has diagnostic / read-surface exposure.**

The modulated identity anchor is emitted **separately** by the H2 derived-anchor emitter
(fabric.py:1519-1550) as:

- `mtype="identity_anchor"`
- `canon=False`
- `anchor_origin="derived"`
- `anchor_source="motif_cluster"`

## 8. Boundary classification (evidence language)

Durable-soft. Non-canon. Deterministic / offline / model-free. Identity-pressure / cadence-shaping.
H2 / Writer-Authority-adjacent (it is an **input** to the H2 derived-anchor emitter, not itself the
writer). No authority decision by itself. No safety / unsafe verdict. No remedy. No Writer Authority
continuation.

## 9. Prior coverage

This is **not wholly untraced.** The **Pre-Substrate Framing family G**
(`docs/TORMENT_PRE_SUBSTRATE_ARCHITECTURE_FRAMING_v0.1.md`) already states the conclusion — "implemented
(`roles.json`, updated from ingest text); modulates identity-anchor cadence (count/gap) → indirectly
retrieval/prompt; non-canonical; durable-soft; ungoverned soft writer modulating identity cadence." Role
scores also appear among the signals in the Private-Cognition blueprint
(`docs/TORMENT_PRIVATE_COGNITION_UNIFIED_REFLECTION_BLUEPRINT_v0.1.md`). `roles.json` storage durability
is covered in `docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md` under the `IDENTITY-NON-ATOMIC-SAVE` class.
The **H2 derived identity-anchor emitter** is covered by the Gate B writer-authority hazard inventory and
the writer-path / Seam characterization.

The **new value** here is the **consolidated, line-anchored, end-to-end influence map**: default/load →
ingest-summary update → `roles.json` / EMA → dominant role / multipliers → identity-anchor cadence
thresholds → derived non-canon anchor emission → indirect memory/prompt-shaping effect (plus diagnostic
read-surface exposure) — in one place, parallel to the mood_drift and spirit-warmth consolidated traces.

## 10. Anti-drift notes and tuned constants

Do not overstate. The dominant role is **not identity authority**. Role scores are **not persona / voice
writing** (roles.py header: "guidance signals only, never dominance… never persona writing").
Diagnostic / read-surface exposure is **not prompt authority**. Role inference is **not direct prompt
text**, **not canon / admission / promotion**, and **not H2 remediation**. Tracing it must **not open
Writer Authority** — characterizing the cadence modulation is observing the H2-adjacent input path, not
reconciling or changing the H2 emitter.

**Tuned constants — do not tune:** the EMA (0.18, clamp 0.02–0.5), the keyword tables, the default
explorer bias (0.30 / 0.10), the role multipliers, the cadence floors (count ≥ 2, gap ≥ 10), and the env
cadence values (3 / 50). Any future change requires **provenance archaeology** (source / tests / docs /
history / operator context) first — the same discipline as the ambiguity-clarify thresholds, the scoring
buckets, and the spirit-return warmth constants.

## 11. Lane posture

This **completes the last individually untraced durable identity-pressure path at consolidated-map
granularity** (alongside gravity_correction, identity anchors, mood_drift, spirit-return warmth, and
authored seed-content stability). After this artifact, the remaining items are **deliberate heavy-gate
decisions**, not small slices:

- chamber representation / private continuity boundary;
- seed-revision boundary construction;
- governed admission crossing mechanism;
- the runtime-conformance gap for the old automatic identity-pressure paths.

Database / substrate remains last.

---

*Read-only characterization checkpoint only. Static source/docs inspection; no runtime executed, no
state mutated, no behavior changed, no remedy, no registry amendment, no role tuning. Role inference is a
durable-soft, non-canon, deterministic identity-pressure signal that modulates derived identity-anchor
cadence (count/gap) and has diagnostic read-surface exposure — no authority decision by itself, no
canon/admission/promotion, no safety verdict. Audit observes authority and does not become authority.
Memory may shape context. Memory may not seize authority. Database / substrate remains last.*
