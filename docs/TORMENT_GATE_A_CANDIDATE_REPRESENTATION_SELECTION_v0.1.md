# TORMENT Gate A — Candidate Representation Selection v0.1

## 1. Status / non-authorization

**Docs-only requirement-level selection record. NON-AUTHORIZING.**
This artifact records the requirement-level representation *principle* selected from
the prior decision frame. It selects a principle only; it builds nothing and names
nothing concrete.

Held true throughout: no code, no tests, no git, no patch plan, no implementation
plan; no class names, module names, fields, serialization, or storage; no candidate
producer; no candidate store; no governed-admission implementation; no promotion
crossing; no persistence / database / substrate; no endpoint / API / schema change;
no AgentRunner expansion; no Gate D runtime / chamber / private cognition; no writer
fixes; no prompt exposure; no retrieval feedback; no audit-to-control feedback; no
Layer 4 wall mechanics; no `PROJECT_ORIENTATION_MAP.md` edit; no §0 pointer.

This artifact may shape context. It must not seize authority.

## 2. Selection statement: constrained A + D blend

> Gate A candidate representation is selected, at requirement level only, as a
> constrained A+D blend:
>
> A candidate-shaped output must be represented as a distinct non-ordinary type
> boundary, and any concrete value of that type must remain sealed/opaque to
> ordinary memory fan-out. The type boundary is what ordinary ingest and ordinary
> write paths must not be able to accept as ordinary memory input; the sealed
> wrapper property is what prevents ordinary code from reading or reinterpreting
> candidate contents as ordinary input.
>
> This selection does not authorize a runtime producer, candidate store, governed
> admission, promotion crossing, persistence, endpoint/API/schema change,
> AgentRunner expansion, Gate D runtime/chamber/private cognition, prompt exposure,
> retrieval feedback, audit-to-control feedback, writer fixes, or Layer 4 wall
> mechanics.
>
> This selection does not choose class names, module names, fields, serialization,
> storage, admission behavior, promotion behavior, endpoint shape, or implementation
> files. It only selects the representation principle needed for a later
> Codex-reviewed mechanics question.

## 3. Why A + D was selected

The two properties are complementary and together cover the two failure modes the
STOP archaeology identified:

- **Type boundary (A)** answers *recognition by construction*: ordinary ingest and
  ordinary writers cannot accept the candidate type, so a candidate cannot enter the
  ordinary fan-out by being mistaken for ordinary input. This is structural, not a
  tag the ordinary lane is trusted to read (A-C2).
- **Sealed/opaque value (D)** answers *non-reinterpretation*: even where a candidate
  value is held, ordinary code cannot unwrap or read its contents as ordinary input.
  Type distinction alone could still leak if contents were reinterpretable; the seal
  closes that.
- **Constrained** because each alone is insufficient — A without D leaves contents
  reinterpretable, D without A leaves no by-construction refusal at the ordinary
  boundary. The blend is the minimal pairing that is structural on both axes while
  selecting no mechanism.

## 4. Why B, C, and E were not selected

- **Style B (separate non-public ingress class)** describes *where* candidates would
  arrive, not *what* makes them structurally candidate-shaped; an ingress class with
  no producer is empty, and it leans toward route/surface questions that are Layer 4
  and beyond. A+D defines the form itself without committing to a surface.
- **Style C (ordinary-ingest inexpressibility boundary)** is largely *entailed* by
  A+D: if the candidate is a distinct non-ordinary type, it already cannot be
  expressed as ordinary ingest input. Selecting C separately would risk reading as a
  runtime narrowing of the ordinary root, which is out of scope; A+D obtains the
  inexpressibility as a consequence, not as a separate boundary.
- **Style E (other non-tag structural boundary)** is an open placeholder for a
  later-proposed primitive (capability/handle/token); it selects nothing concrete
  and would defer the principle rather than fix it. A+D is source-grounded and
  decidable now at requirement level.

None of B, C, or E is rejected as *wrong*; they are simply not the selected
principle. A future authorized mechanics plan may still draw on C's entailment.

## 5. What the selected representation principle means

At requirement level, the selection means exactly two joined obligations on any
future candidate-shaped output:

- it must be of a **distinct non-ordinary type** such that the ordinary ingest root
  and ordinary writers cannot accept it; and
- any concrete value of that type must be **sealed/opaque** so ordinary fan-out
  cannot read or reinterpret its contents as ordinary input.

The first is a refusal-by-construction at the ordinary boundary; the second is a
non-reinterpretation guarantee on the value. Together they are the *representation
principle* — what a candidate is, structurally — and nothing more.

## 6. What it does not authorize

This selection authorizes none of, and must not be read as authorizing by
implication: a runtime producer; a candidate store; governed admission or its
implementation; a promotion crossing; persistence / database / substrate; an
endpoint / API / schema change; AgentRunner expansion; Gate D runtime / chamber /
private cognition; prompt exposure; retrieval feedback; audit-to-control feedback;
writer fixes; or Layer 4 wall mechanics. It selects no class names, module names,
fields, serialization, storage, admission behavior, promotion behavior, endpoint
shape, or implementation files. The four parked writer non-conformances remain
parked.

## 7. Relationship to the candidate representation decision frame

This artifact is the selection step the decision frame deferred. The frame compared
Styles A–E and chose none; this note records the requirement-level choice — a
constrained A+D blend — without altering the frame's boundaries. Where this note and
the frame appear to differ, the frame's non-authorization boundaries still hold; the
only thing added here is *which principle* is selected.

## 8. Relationship to Gate A Layer 4 mechanics

**Gate A Layer 4 wall mechanics remain unauthorized.** Selecting the representation
principle makes a *structural* deny boundary **possible to specify** — it removes the
blocker the STOP identified — but does not authorize building anything. A Layer 4
mechanics plan is a separate decision, with its own Codex review against Document A,
and would still also require the writer-authority layer to address the documented
direct-writer bypasses a single ingest-side boundary cannot reach. Representation
selection ≠ mechanics authorization.

## 9. Relationship to the Gate D dependency map

The Gate D dependency map records that the containment wall remains unbuilt, that
Layers 1–3 are requirements only, and that Layer 4 mechanics are not authorized.
This selection answers, at requirement level only, the representation-selection
question adjacent to that wall dependency, but changes none of the runtime facts:
the wall is still unbuilt and Layer 4 is still unauthorized. **It does not open
Gate D**; Gate D runtime / private cognition stays parked, with a built wall
remaining its precondition.

## 10. Tests / code posture

**Still premature until a separate Layer 4 patch-plan review.** A selected
representation principle is not a built type and not a guard; no production deny
boundary exists. The three existing Gate A characterizations continue to lock the
resting state. No tests and no code are proposed here; both wait on a separately
authorized Layer 4 patch plan.

## 11. Possible future Codex-reviewed question

A possible future question, **not** opened here, is narrow and boundary-shaped:

> Can a separately authorized, test-local object exhibiting the A+D principle
> (a distinct non-ordinary sealed type) demonstrate that the ordinary ingest root
> cannot accept it as ordinary memory input, without introducing a candidate store,
> governed admission, promotion crossing, persistence, runtime producer, or any
> Layer 4 wall mechanics?

This is posed only as a possible future review question. It is not a plan, not a
test authorization, and not a commitment to write one.

## 12. Anti-drift footer

CANDIDATE REPRESENTATION SELECTION / REQUIREMENT-LEVEL ONLY / NON-AUTHORIZING. It
records the selected representation principle — a constrained A+D blend: a distinct
non-ordinary type boundary that ordinary ingest and ordinary write paths must not be
able to accept as ordinary memory input, whose concrete values stay sealed/opaque
to ordinary fan-out — and selects no class, module, field, serialization, storage,
admission, promotion, endpoint, or implementation. Gate A Layer 4 mechanics stay
unauthorized; Gate D stays parked; tests stay premature until a separate Layer 4
patch-plan review; the parked writer non-conformances stay parked. Any mechanics
needs explicit Hilmir authorization plus Codex review. Guidance not control; audit
observes authority and does not become authority; nothing rewrites identity / canon
/ seed / soul.
