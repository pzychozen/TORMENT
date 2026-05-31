# Character-Memory Harness

Active, maintainable test surface for TORMENT character-memory behavior.

## Purpose

This harness provides active, maintainable coverage for one specific behavior
currently represented only by frozen historical evidence: the transcript-stateless,
two-arm (seed-only vs runtime-memory) retrieval loop. That shape lives today only
in `torment_stress_harness/stress_phase1_trajectory.py`, which is locked
historical evidence and must not be edited, forked, or imported. This harness
reproduces the *principle* in fresh code so future work no longer depends on
touching frozen artifacts. The old evidence remains valid and preserved; this
harness does not replace or supersede it.

## What it tests (first pass)

Probe v0 is a **single-turn seeded-recall-and-voice bring-up check**, measured
against a seed-only baseline. It checks whether governed runtime memory surfaces
a temporary fact into a single transcript-stateless callback and whether the
seed + that one retrieved memory stay in Eland's voice for one turn. The probe
is limited to context influence. Automation is out of scope.

**Full living-character coherence is explicitly deferred to a later multi-ingest
Loop probe.** A one-ingest, transcript-stateless probe cannot wake the
longer-history character systems (drift correction, identity-anchor emission,
mood-drift, mood-spiral, role inference, relational continuity) — they are
structurally dormant at step 1 with a newborn character. Probe v0 therefore
must not be read as a verdict on those systems. Run `20260530T183554Z_765e`
is preserved as a **bring-up PASS** (harness safety, fresh-workspace isolation,
ST/BGE governed `/retrieve`, deterministic fact surfacing, arm separation,
forensic output). It is NOT credited with a clean prompt-contract demonstration:
its harness-generated recall section still repeated decomposed `seed_canon`
fragments alongside the verbatim seed. Its character behavior is NOT graded.
765e ran with companion-profiled retrieval/assembly, but the service-derived
character posture was empty, so character-level interpretation was deferred.

Two later runs proved different things. `c1c2` (`20260531T181119Z`) confirmed the
service-level companion posture and exposed the duplicated-seed prompt confound.
`3059` (`20260531T193241Z`), after the `seed_canon` exclusion fix, proved the
corrected clean prompt contract end-to-end: seed-only = verbatim seed once with no
recall section; runtime = verbatim seed once plus a single plain bullet carrying
only the surfaced fact.

## Required runtime posture (companion)

Probe v0 reruns require the service to be running under the **companion** posture.
The runner preflights the live service (`/health`, `/config`, `/embedder/check`),
captures all three into forensics, and **aborts before creating any workspace**
unless: profile name `companion`, character enabled, embedder provider `st`,
model `BAAI/bge-small-en-v1.5`, device `cpu`, embedder ok / not degraded / dim 384.
Affect, mood, anchor, role, and character-tuning values are captured but not
gated. Start the service with `TORMENT_PROFILE=companion` (plus the ST/BGE
embedder env) before rerunning.

Probe v0 uses `/retrieve` with `include_assembly_audit: true` for governed
selection and forensic capture, but constructs the model-visible callback prompt
minimally: the verbatim persona seed plus plain selected recalled memory text
only — no scores, tiers, provenance, drift labels, assembly headings,
recommendations, spirit-return voice cues, or flavor tags. The deterministic
temporary fact is ingested with `supplied_summary` (which threads through the
same governed Spine write path), so the stored memory is reproducible and any
weirdness is easier to interpret.

## Two arms

- **Seed-only baseline:** the character seed is present (canon memory), but no
  runtime accumulation is introduced. The seed is itself memory — this is not
  "memory vs no memory."
- **Runtime-memory arm:** same seed, plus one temporary fact accumulated through
  the real governed retrieval path (`/agent/ingest` → `/retrieve`).

Both arms receive the identical seed. Only the runtime-memory arm ingests the
temporary fact.

## Transcript-stateless callback rule

The callback turn's model-visible context contains no prior-turn user or
assistant content. The only across-turn carryover is substrate-mediated
retrieval (runtime arm) or nothing (seed-only arm). This guarantees the callback
cannot be satisfied by raw transcript recency — recall must come from memory.

## Fresh disposable workspaces

Every invocation generates two fresh workspaces:

    cm_loop_<run_id>_seed_only
    cm_loop_<run_id>_runtime_memory

**Primary protection:** both generated workspace IDs must begin with `cm_loop_`.
The runner must abort if either arm resolves outside that prefix. A denylist
(`truth_bench`, `default`, `ryuki`, `ryuki_nox`, any populated or protected
workspace) is a secondary defense — prefix-only generation and refusal is the
main guard against accidental reuse.

The runner does **not** auto-delete: workspaces persist for operator forensic
review. An explicit opt-in cleanup flag may be added later; silent deletion
never.

## Seed philosophy: seeded, not directed

A character is a gravitational basin, not a script. The seed is 3–5 sentences of
who the character *is*, never behavioral rules. The persona seed IS the system
prompt: no meta-framing, no actor-direction, no "stay in character" director
voice, no protective preamble. Let the character emerge; the system shapes
memory around it. Callbacks must create space for natural character expression
without instructing the character how to sound.

## Boundaries

- Historical folders stay frozen: `torment_stress_harness/` and the
  repo-root `do_not_touch_torment_test_rig/` are never edited, forked, or
  imported.
- No canon mutation during the loop after the initial identical seed plant in
  both arms. The normal `/agent/create` seed pipeline remains intentional; both
  arms receive the same initial canon seed, and nothing mutates canon after
  that.
- No tools or external effects, no audit-driven gating or redirection, no
  automation, no longitudinal/drift claims.

## Scope today vs later

First pass is narrow: one character (Eland), one coherence-bearing callback, two
arms, human-applied grading.

**Probe v1 (parked):** feed the exact production `/retrieve.assembled_text`
surface — with its `[Identity Context]` / `[Drift:]` / `[Voice:]` / `[Flavor:]`
labels — and test whether that presentation layer alters coherence versus the
Probe v0 clean baseline. This is a presentation-layer test, deliberately kept
separate from Probe v0's retrieval test so the two variables don't confound.

**`/agent/query` (parked):** a later raw-retrieval comparison mode. It bypasses
the governed assembly path, so it answers a different question than the governed
telos and is not used in the first pass.

Later regression expansion may add FILTER-A non-shareable exclusion under live
retrieval, and the Veyra / Moth / Glass Saint personas. Their intentional
character behavior — declared lying, unreliable narration, boundary-testing — is
legitimate contract, **never** treated as a defect. Governance protects memory,
provenance, tool, and authority boundaries without flattening character voice; a
run that scores well on governance but produces a guarded or moralizing voice is
a failure.
