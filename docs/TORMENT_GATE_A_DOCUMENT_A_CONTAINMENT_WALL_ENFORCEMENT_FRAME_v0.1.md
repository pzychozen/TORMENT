# TORMENT Gate A — Document A Containment Wall Enforcement Frame v0.1

## 1. Status and authority boundary

**Docs/design only. Enforcement DESIGN FRAME. Authorizes no implementation.** This
artifact defines *what an enforced Document A containment wall must be and must
prove* before any private-cognition / Gate D runtime could be considered. It
selects **no mechanics** — no store, lane, schema, field, carrier, tag format,
scheduler, or runtime — and changes no production code, no tests, and no behavior.
Opening the wall's enforcement (or Gate D) requires separate, explicit
Codex/operator authorization.

Anchors carried (not re-opened):

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Source-of-truth contracts this frame is subordinate to: Document A — Candidate
Containment + Writer Authority (`docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md`,
esp. A-O2 / A-O3 / A-C1 / A-C2 / A-C3 and §8 admission / §9 inspection≠projection);
Document B — Private Cognition + Unified Reflection blueprint (the would-be
inhabitant); the cognition roadmap sequencing (A-wall → P4 gates → Document B
interior). This frame neither amends nor implements them.

**Holding-move note.** The tests-only *containment resting-state lock* (option C
from orientation) remains a safe holding move, but it does **not** retire this
blocker. This enforcement design frame is the next strategic gate.

## 2. Wall boundary

`[DEFINITION]` **Document A containment** is the requirement that **unadmitted
reflection artifacts cannot influence or re-enter any live cognition-shaping,
retrieval-shaping, prompt-shaping, affect-shaping, identity-shaping, or
projection-reentry path until an explicit governed admission crossing.** The
*enforced wall* is the structural realization of that requirement: a boundary
that holds **by construction**, not by every downstream reader/writer remembering
to honor an exclusion tag (Document A A-C2).

**What it separates.** On the *contained* side: private thread-continuity state,
reflection synthesis, and unadmitted reflection candidates (staged syntheses,
proposed writes, contradiction/risk flags, unresolved questions). On the *live*
side: ordinary memory, the ingest fan-out, retrieval/assembly, prompt projection,
write/promotion/authority surfaces. The wall is the single governed crossing
between them.

**What the wall must prevent from silently leaking into the live side:**

- into **live cognition**: a contained artifact biasing mode/action/intent,
  drift/mood/affect, role inference, or stance;
- into **prompt projection**: a contained artifact becoming model-visible context
  (assembled_text, voice/flavor/drift cues, identity blocks);
- into **write paths**: a contained artifact producing an ordinary-memory write,
  motif/anchor emission, or reinforcement;
- into **persistence**: a contained artifact being durably stored as ordinary
  memory by any side path;
- into **promotion**: a contained artifact gaining retrieval-count, archive→core,
  or promotion-suggestion signals;
- into **authority surfaces**: a contained artifact producing `canon=True`,
  identity-tier, seed, or long-half-life identity material (Document A A-O2).

**Admission is the sole exit** (A-O3): no side path may convert a contained
artifact to ordinary memory; the only legitimate route is a governed admission
crossing to **at most** released / low-authority.

## 3. Live fan-out roots and leak paths to guard

`[FACT]` Per Document A, the **ordinary-ingest entry is the fan-out root** into
the rest of cognition, so non-reachability must hold *at the ingest entry itself*,
not only at the graph. The enforced wall must guard every root below. (Files cited
read-only as the surfaces a future enforcement path and its guards must cover;
**no mechanics are selected and no file is edited here.**)

- **Ordinary ingest fan-out** — `torment_service/fabric.py` ingest entry (the
  root that feeds motif / drift / mood / role / deep / SRG / retrieval).
- **Private / memory graph writes** — `fabric.py` graph write sites.
- **Motif emission** — `motifs.py` and motif-member references.
- **Drift / gravity** — `mood_drift → centroid → gravity_correction` path and
  `gravity_correction` (the parked `canon=True` non-conformance).
- **Identity-anchor cadence** — `_maybe_emit_identity_anchor` (parked derived
  identity writer).
- **Mood / affect** — mood/drift soft-state inputs.
- **Role inference** — `roles.py` (`dominant_role` → identity-anchor cadence).
- **Deep memory** — `deep_memory.py` / `_query_deep_lane` enrichment.
- **SRG** — `srg_engine.py` and SRG scoring/spirit-return inputs.
- **Reinforcement** — retrieval-count / usage reinforcement signals.
- **Promotion** — `promotion.py` and `POST /promote` (the parked force-bypass
  non-conformance) in `app.py`.
- **Retrieval / assembly** — `retrieval_assembler.py` (classification, ordering,
  inclusion).
- **Prompt projection / generation** — `agent_loop.py` (the 8-phase
  `AgentRunner`, currently **test/demo-only, not live-wired**) and the
  `/agent/query` / `/retrieve` / `/thinking/debug` surfaces in `app.py`.

`[FACT]` **Precedent — `ws_section_2a_v1`.** Once material enters the ordinary
fan-out, auto-emitted identity pressure can occur even when the material was not
intended as identity-bearing. The wall must therefore stop a contained artifact
*before* the ingest root, structurally.

`[FACT]` **Precedent — sealed audit owner/bridge.** The selected-items runner
bridge (`audit_selected_items_runner_bridge.py`) and the private generation owner
(`audit_private_generation_owner.py`) are the existing model of by-construction
non-reachability: both are unwired (called only by tests), observation-only,
packet-blind, and feed no control path. The enforced wall should reuse that
posture (structural dead-end, observation-only, no control feedback), not invent
a tag-honoring scheme.

## 4. Non-reachability proof obligations by artifact class

For each class, the frame states **what a future enforcement path plus its
tests/source guards must prove** before Gate D — no mechanism is selected here.

- **Private thread-continuity state** — must prove it is *not a candidate by
  existing*; it may shape only its own later synthesis inside the bounded chamber
  and must not reach any §3 root. Soft, inspectable, contestable, resettable;
  never pinned, never authority-bearing.
- **Reflection synthesis (chamber artifact)** — must prove it becomes a candidate
  *only when explicitly staged*; until staged it is inert and §3-unreachable.
- **Unadmitted reflection candidate** (staged synthesis / proposed write /
  contradiction / risk flag / question) — must prove the full A-C1 non-reachability
  set: cannot reach ingest fan-out, motif/drift/gravity/mood/role/deep/SRG,
  reinforcement, archive→core or any promotion signal, retrieval shaping, prompt
  projection, or any `canon=True` / identity-tier / seed write (A-O2). Must prove
  this **structurally** (A-C2), not by exclusion-tag honoring, and that
  **admission is the sole exit** (A-O3).
- **Admitted released / low-authority memory** — must prove the admission *ceiling*
  holds: queryable/retainable but with no identity-shaping weight and no
  unrestricted promotion rights; any upgrade requires a *separate* governed
  promotion crossing.
- **Promoted (identity / canon) memory** — must prove it is reachable **only**
  through a governed promotion crossing, never by a cognition/reflection writer
  directly and never via the four parked non-conformances.
- **Inspection / audit surfaces** — must prove inspection observes candidates
  read-only and is **not projection** (§9): inspectability must not itself be a
  re-entry path (A-C3).

## 5. Staging vs admission vs promotion vs live visibility

The wall's correctness depends on never collapsing these (Document A §4/§8):

- **Staged artifact** — explicitly staged *for a possible crossing*; still fully
  contained; a *recommendation* to cross is staging only, never application
  (stage ≠ authority).
- **Admitted artifact** — has crossed a governed admission crossing into ordinary
  memory at **no higher than** released / low-authority; admission is a *ceiling*,
  not a guarantee of ordinary-memory entry, and not promotion.
- **Promoted artifact** — has crossed a *separate* governed promotion crossing to
  a higher authority class (identity-shaping / canon); distinct from admission.
- **Live cognition / retrieval / projection visibility** — being visible to the
  live cognition/retrieval/prompt path. Distinct from all three above: creation ≠
  admission, admission ≠ promotion, inspection ≠ projection, caller-visible ≠
  prompt-visible. The wall must keep staged artifacts out of live visibility, and
  must keep admitted (released/low-authority) artifacts out of identity-shaping /
  promotion visibility.

## 6. Future test / code proof bars

A future enforcement slice (separately authorized) must land, **tests/source
first**, at least:

- a **structural non-reachability proof** that an unadmitted candidate cannot
  reach any §3 root — by construction, demonstrated at the ingest entry, not only
  at the graph;
- a **no-tag-dependence proof** (A-C2): non-reachability does not rely on
  downstream readers honoring an exclusion tag;
- an **admission-sole-exit proof** (A-O3): no side path converts a candidate to
  ordinary memory;
- a **no-silent-canon/identity proof** (A-O2): no cognition/reflection writer
  emits `canon=True` / identity-tier / seed / long-half-life material;
- an **inspection-≠-projection proof** (§9): audit/inspection surfaces are
  read-only and non-reentrant;
- a **staging-≠-authority / admission-≠-promotion proof** (§5 boundaries hold);
- a **deliberation-room containment proof**: any future private-thinking room is
  reachable only inside the wall, and `AgentRunner` / the live `/agent/query`
  path gains no contained-artifact input — the existing "owner/bridge unwired,
  observation-only" posture is preserved.

These are **proof requirements only.** This slice creates no tests and no code.

## 7. Gate D dependency

`[OBLIGATION]` **No private-cognition runtime / Gate D runtime is admissible
until this containment wall has an approved enforcement path** — i.e., until the
§6 proof bars can be (and are, in a later authorized slice) satisfied by
construction. Document B's interior (private thinking, continued thought,
envelope audit, chamber continuity) presupposes the wall; building the inhabitant
before the wall would place unadmitted reflection one step from the live fan-out
root. The roadmap order — **A-wall → P4 gates → Document B interior** — is a
dependency, not merely a preference.

## 8. Explicit no-go list

This frame authorizes none of, and the wall design must not smuggle in, any of:

- Gate D runtime / private-cognition runtime;
- Envelope Audit runtime;
- private-owner live wiring;
- Shape B (runner delegation seam);
- endpoint / schema / API changes;
- prompt-request exposure;
- `AgentRunner` ownership expansion;
- database / substrate mechanics;
- carrier / schema / field selection;
- writer-path fixes (including the four parked non-conformances as *fixes*);
- P4 O1/O2 source-sameness mechanics;
- Seed-Governance mechanics;
- retrieval feedback;
- persistence changes;
- autonomy;
- audit-to-control feedback.

## 9. What this frame does not authorize (anti-drift footer)

DESIGN FRAME — NON-AUTHORIZING. It names the wall boundary, the live source
surfaces to guard, the non-reachability proof obligations, the staging/admission/
promotion/visibility boundaries, the future proof bars, the Gate D dependency,
and the no-go list. It selects no mechanics, opens no gate, writes no code or
tests, and changes no runtime behavior. Building the enforcement path, or opening
Gate D, requires separate trio/operator authorization. Guidance not control;
audit observes authority and does not become authority; nothing rewrites
identity / canon / seed / soul.
