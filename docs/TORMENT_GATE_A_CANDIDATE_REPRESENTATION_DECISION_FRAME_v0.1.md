# TORMENT Gate A — Candidate Representation Decision Frame v0.1

## 1. Status / non-authorization

**Docs-only requirement-level decision frame. NON-AUTHORIZING. SELECTS NOTHING.**
This artifact defines the *decision space* for what a candidate-shaped
representation may be at requirement level, **before** any Gate A Layer 4 wall
mechanics could be considered. It compares representation styles without choosing
one; any selection is explicitly a **future operator / Codex decision, not made
here.**

Held true throughout: no code, no tests, no git, no patch plan, no implementation
plan; no selected representation; no candidate store; no governed-admission
implementation; no promotion crossing; no persistence / database / substrate; no
endpoint / API / schema change; no AgentRunner expansion; no Gate D runtime /
chamber / private cognition; no writer fixes; no prompt exposure; no retrieval
feedback; no audit-to-control feedback; no `PROJECT_ORIENTATION_MAP.md` edit; no §0
pointer.

This artifact may shape context. It must not seize authority.

## 2. Why this frame exists

A read-only source archaeology of a candidate first Layer 4 mechanic — a deny-only
containment guard at the ordinary ingest fan-out root (`TormentFabric.ingest`) —
returned **STOP — PATCH PLAN NOT SAFE**. The finding:

- The ordinary ingest root today accepts ordinary input (`text` plus ordinary
  metadata); there is no channel by which a candidate-shaped output could be
  expressed, so a deny-guard has nothing structural to deny.
- A guard that recognized candidate-shaped input **by a payload tag, metadata
  marker, ordinary dict field, provenance label, or a `do_not_admit`-style flag**
  would violate A-C2 (containment must hold by construction) and would regress the
  existing no-tag-dependence characterization.
- A guard that recognized candidate-shaped input **by a type / parameter / object
  boundary** would *be* a candidate representation decision — which must be framed
  first.

This frame is that prior step. It does not build the guard; it defines the
requirement-level space in which a representation could later be chosen so that a
structural (non-tag) boundary becomes *possible to specify* under separate
authorization.

## 3. Doctrine filter

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

A representation that could only be recognized or enforced by violating this filter
is out of scope by definition.

## 4. What candidate representation is allowed to mean at this layer

At requirement level, a candidate representation is **the structural form by which a
candidate-shaped output is distinguishable from ordinary memory input — by what it
is, not by a label it carries.** Allowed meaning is limited to:

- a **structural distinction** (type, surface, object shape, or sealed wrapper)
  such that ordinary fan-out cannot mistake a candidate for ordinary input;
- a distinction **recognizable by construction** — i.e., the ordinary lane cannot
  even express a candidate, rather than the ordinary lane choosing to honor a flag;
- a **requirement**, not a built thing: this frame states what such a form must
  satisfy, and selects no form.

That is the whole of what "representation" means here.

## 5. What candidate representation must not be

A candidate representation, at this layer, must never be — and choosing one must
not be read as — any of:

- a **store / container** for candidates;
- a **governed admission** decision or its implementation;
- a **promotion crossing** or any authority increase;
- **persistence / database / substrate**;
- **writer authority** (which class may write what) — that is a separate layer;
- **retrieval eligibility**, **prompt exposure**, or **caller/cognition
  visibility**;
- **Gate D runtime / private cognition**;
- a **tag, marker, payload key, metadata flag, provenance label, or
  `do_not_admit` filter** (see §6).

Representation answers only "what makes something candidate-shaped, structurally."
It answers nothing about where it lives, how it moves, or who may act on it.

## 6. Why tag / marker / payload-key containment is forbidden

Tag-based containment fails on two independent grounds, both source-grounded:

- **Doctrine (A-C2).** Containment must hold *by construction*, not by every
  downstream reader/writer remembering to honor an exclusion tag. A flag that says
  "do not admit me" relies on each fan-out site choosing to respect it; the
  `ws_section_2a_v1` lesson is that once material enters the ordinary fan-out,
  auto-emitted pressure can occur even when the material was never meant to bear
  it. A label is not a wall.
- **Existing guardrail.** The resting-state no-tag-dependence characterization
  already locks that no live fan-out root branches, filters, routes, promotes, or
  suppresses on reflection-exclusion / reflection-source tags. A tag-honoring
  containment guard would both break that characterization and re-introduce the
  exact fragility A-C2 forbids.

Therefore any admissible representation must be a **structural** boundary, not a
value the ordinary lane is trusted to read and obey.

## 7. Representation styles to compare (without selecting)

The following are candidate *styles*, recorded for comparison only. **None is
selected; no blend is selected.** For each: what it would mean, why its recognition
is structural rather than tag-based, what it explicitly does not decide, and why it
is not sufficient alone.

### Style A — type boundary
- **Meaning:** a candidate-shaped output is a distinct type that the ordinary
  ingest root cannot accept; recognition is "this is not the ordinary input type."
- **Structural, not tag:** the distinction is the type itself, not a field on a
  shared type.
- **Does not decide:** any store, admission, persistence, or writer rule.
- **Not sufficient alone:** does not close the direct-writer bypasses (§8) and
  presupposes no Gate D producer exists yet.

### Style B — separate non-public ingress class
- **Meaning:** candidate-shaped outputs are expressible only through a distinct
  non-public ingress class that is not the ordinary ingest fan-out root; recognition
  is "this arrived through a conceptually separate candidate-only ingress class."
- **Structural, not tag:** the ordinary root has no candidate channel.
- **Does not decide:** any endpoint, API, route, procedure, store, admission
  surface, or what the separate ingress class would later do.
- **Not sufficient alone:** an ingress class with no producer is empty, and other
  writers still bypass the ordinary root.

### Style C — ordinary-ingest inexpressibility boundary
- **Meaning:** the future representation is defined so that a candidate-shaped
  output cannot be expressed as ordinary ingest input at all; recognition is
  inexpressibility at the requirement level.
- **Structural, not tag:** containment is "cannot be expressed in the ordinary
  lane," not "expressed and then filtered."
- **Does not decide:** any runtime narrowing of `TormentFabric.ingest`, endpoint,
  API, schema, parameter, representation elsewhere, or movement.
- **Not sufficient alone:** inexpressibility at ordinary ingest does not by itself
  define every candidate boundary obligation, and does not cover bypass writers.

### Style D — sealed in-memory wrapper
- **Meaning:** a candidate is held inside an opaque wrapper whose *identity* is the
  boundary; ordinary fan-out cannot unwrap or read it as ordinary input.
- **Structural, not tag:** the seal is the object, not a readable marker on a
  shared payload.
- **Does not decide:** persistence (it is explicitly in-memory framing only),
  admission, or promotion.
- **Not sufficient alone:** a wrapper presupposes something to wrap (no producer
  today) and says nothing about writer authority.

### Style E — other non-tag structural boundary (if source-grounded)
- **Meaning:** another source-grounded structural distinction may be proposed later
  if it is not a tag, marker, payload key, metadata flag, provenance label, or
  ordinary-lane value.
- **Structural, not tag:** the distinction must be in the boundary shape itself,
  not in content the ordinary lane is trusted to read and obey.
- **Does not decide:** any capability system, handle, token, security primitive,
  endpoint, API, store, admission, or mechanics.
- **Not sufficient alone:** any concrete structural primitive is later, separately
  authorized work.

**Cross-cutting:** every style above recognizes a candidate *structurally* and none
closes the documented direct-writer bypass surface on its own — that is
writer-authority territory, a separate layer. Single-style vs blended is **not**
decided here.

## 8. Relationship to Gate A Layer 4 mechanics

This frame is the precondition the STOP identified, not the mechanics. **Gate A
Layer 4 wall mechanics remain unauthorized.** Selecting a representation later would
make a *structural* deny boundary **possible to specify** — but would not authorize
building it, and would still require: (a) a separate Layer 4 mechanics
authorization, and (b) the writer-authority layer to address the bypass writers a
single ingest-side boundary cannot reach. Representation selection ≠ mechanics
authorization.

## 9. Relationship to the Gate D dependency map

The Gate D dependency map records that the containment wall remains unbuilt, that
Layers 1–3 are requirements only, and that Layer 4 mechanics are not authorized.
This frame sits in the gap between "candidate boundary / admission requirements"
(requirement-level) and any Layer 4 mechanic: it supplies the missing
representation question that a real wall depends on. **It does not open Gate D**;
Gate D runtime / private cognition stays parked, and a built wall remains its
precondition.

## 10. Tests / code posture

**Premature until a representation is selected and authorized.** The three existing
Gate A characterizations already lock the resting state (non-reachability, no-tag
dependence, inspection non-reentry). A deny-guard test cannot be written now without
constructing candidate-shaped input the guard recognizes — which would require
committing to a representation (or a forbidden tag). Therefore no tests and no code
are proposed here; both wait on a selected, authorized representation.

## 11. Future operator / Codex decision needed

Before any selection or mechanics:

- **Selecting a representation style** (or a blend) requires **explicit Hilmir
  authorization plus Codex review**; this frame names the styles but chooses none.
- **Opening Layer 4 mechanics** is a *separate* decision after a representation is
  selected, with its own Codex review against Document A.
- Roles for whichever fork is chosen: Claude may provide read-only, source-grounded
  observations when separately authorized; GPT steers; Codex challenges
  boundary-bearing choices; Hilmir resolves the fork and holds authority.

Until then Gate A stays paused and Gate D stays parked.

## 12. Anti-drift footer

CANDIDATE REPRESENTATION DECISION FRAME / NON-AUTHORIZING / SELECTS NOTHING. It
defines, at requirement level, what a candidate-shaped representation may and must
not mean, explains why tag / marker / payload-key / metadata / provenance /
`do_not_admit` containment is forbidden (A-C2 + the no-tag characterization), and
compares structural styles (type boundary, separate non-public ingress class,
ordinary-ingest inexpressibility boundary, sealed in-memory wrapper, other non-tag
boundary) **without choosing one**. Representation is not a store, admission,
promotion, persistence, writer authority, retrieval eligibility, prompt exposure,
or Gate D runtime. Gate A Layer 4 mechanics stay unauthorized; Gate D stays parked;
tests stay premature; the parked writer non-conformances stay parked. Any selection
or mechanics needs explicit Hilmir authorization plus Codex review. Guidance not
control; audit observes authority and does not become authority; nothing rewrites
identity / canon / seed / soul.
