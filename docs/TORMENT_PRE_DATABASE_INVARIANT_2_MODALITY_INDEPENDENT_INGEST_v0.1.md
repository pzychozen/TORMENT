# TORMENT Pre-Database Invariant 2 — Modality-Independent Ingest v0.1

> **STATUS: REQUIREMENT-LEVEL / PRE-DATABASE INVARIANT / NON-IMPLEMENTING.**
>
> This document freezes semantic constraints only. It implements no audio path, provenance schema, database design, adapter registry, media store, observation framework, or runtime mode, and opens no implementation lane.

## 1. Purpose and factual verdict

This invariant records the reconciled archaeology conclusion:

`CURRENT_INGRESS_IS_MODALITY_BLIND_AND_PROVENANCE_LOSSY`

This wording deliberately supersedes the earlier provisional phrase:

`CURRENT_INGRESS_IS_MODALITY_AGNOSTIC_BUT_PROVENANCE_LOSSY`

Current ingest is implementation-independent only because it discards modality information. That is blindness, not the desired form of agnosticism. The desired future property is **adapter implementation independence without provenance blindness**.

The present voice path is compactly:

```text
microphone
→ audio samples
→ Whisper
→ transcript string
→ ordinary TORMENT text boundary
```

When optional conversation storage is enabled, it further becomes:

```text
"Human said: ..."
+
"Agent responded: ..."
→ one ordinary ingest
```

By durable ingest time, TORMENT cannot structurally distinguish typed human text, spoken human text transcribed by STT, or the human portion from the model-generated portion of that flattened exchange. This document does not repair that client or historical state.

## 2. Present provenance lesson

`ProvenanceV1` currently answers storage-level questions such as origin class, write path, and stored-memory ancestry. Its `source_type` vocabulary already spans several different conceptual categories. This invariant neither condemns nor redesigns that schema.

The pre-database lesson is:

> **Future substrate design must not continue solving new provenance dimensions by placing every new meaning into one overloaded classification axis.**

The current naming collision reinforces the point: `ArchiveDocument.source_type` denotes representation/file format such as markdown, text, PDF, or HTML. Origin and representation format must therefore remain conceptually distinguished in future substrate design. No existing name is changed here.

## 3. Binding conceptual distinctions

### 3.1 Origin / authority

Origin/authority means who or what supplied, produced, asserted, inferred, generated, or otherwise introduced information in TORMENT's provenance/authority sense. Human input, tool output, model/role output, and observed environment information are illustrative origin classes. Origin/authority remains distinct from the physical or information channel. No new enum is defined.

### 3.2 Source channel / modality

Source channel/modality means the kind of channel through which source information arrived, when known. Text, audio, visual, document, sensor, and other channels are explanatory examples only; this invariant freezes no vocabulary. Unknown modality is valid. A modality grants no authority.

### 3.3 Representation

Representation means the form of information TORMENT currently possesses or stores. For example:

```text
audio source → textual transcript
visual source → numeric descriptor
document source → extracted text
```

> **Source channel and current representation are separate concepts.**

No `representation_format` field or other schema choice is selected.

### 3.4 Derivation status

The substrate must distinguish received representation, known derived representation, and derivation unknown. These terms do not claim epistemic "firsthandness" for ordinary memory, and Brainvision's `FIRSTHAND_VISUAL` label is not adopted as a generic TORMENT memory term.

Existing records whose derivation cannot be established remain unknown. Provenance must never be inferred or manufactured merely to populate a future representation. Unknown is a legitimate permanent state.

### 3.5 Material derivation provenance

> **Semantically material derivations must be representable without requiring every implementation transformation to become durable lineage.**

A derivation is material when knowing it would materially change what a reasonable consumer believes the stored representation is evidence of. Audio to transcript and image to descriptor are representative material cases; resampling, denoising, buffering, and low-level DSP are usually not material by themselves. These examples are not exhaustive categories.

Where a material derivation producer is known, future substrate design must be capable of preserving producing agency, adapter/interpreter identity, and applicable contract/version identity where meaningful. These are capability requirements, not mandatory values. Unknown remains valid. No adapter registry is designed here.

## 4. Lineage, time, identity, and uncertainty

### Lineage constraint

> **Future substrate design must not be structurally limited to memory-to-memory ancestry or to exactly one derivation step.**

Existing `parent_eids` remain existing MemoryGraph lineage and are not redefined or overloaded with observation/media lineage. Detailed lineage representation is deferred to substrate design; this does not freeze a universal transformation graph.

### Temporal truthfulness

> **Storage/ingest time must never masquerade as source-event or source-capture time.**

Where source, capture, or event time is known and material, future substrate design must be capable of preserving it separately. Where unknown, it remains unknown. No timestamp categories, field names, clock format, temporal schema, or backfill from ingest time is authorized.

### Source / participant attribution

> **When source or participant identity is known and semantically material, the substrate must not require it to be flattened into content text.**

Anonymous and unknown source identity remain legitimate. This does not design speakers, users, participants, conversation turns, or multi-party identity.

### Interpretation uncertainty

> **Uncertainty about an interpretation or derivation is not the same thing as TORMENT's memory confidence, coherence, strength, or retrieval score. Neither may silently substitute for the other.**

Absence of interpretation-uncertainty information does not mean certainty. No confidence fields, scales, calibration, or STT metrics are selected.

## 5. Role and presentation orthogonality

> **Source modality/channel is orthogonal to memory role/type/tier.**

Audio, visual, text, and other channels do not inherently mean identity, relational, situational, archive/reference, canon, or non-canon. Any modality may ultimately produce any memory role or no durable memory at all.

> **Presentation modality is not evidence/source modality.**

Speaking a model response does not make memory audio-originated, and displaying information visually does not make it visual evidence. An agent-generated response retains the origin semantics of model generation regardless of TTS or display presentation.

## 6. Mixed-origin content

The current optional voice-client conversation row contains at least two conceptually different origins under one provenance envelope. The client is not redesigned here.

> **A future memory substrate must not require content of materially different origin to share one indivisible provenance claim.**

This selects no conversation row, event schema, turn schema, splitting strategy, or runtime repair.

## 7. Raw-source / media principle

> **Truthful modality and derivation provenance must not require retention of raw source bytes.**

Raw source material may eventually be retained, referenced elsewhere, deliberately discarded, or unavailable/unknown. The exact representation is not selected.

> **Source-artifact availability and provenance truth are separate concepts.**

Deleting or not retaining source media may reduce later verifiability, but it does not erase the truthful fact that a derived representation originated through that channel. No blob-store requirement is created.

## 8. Brainvision precedent, not integration

Brainvision demonstrates that observation provenance, adapter/contract identity, optional source capture time, confidence, and a bounded derived representation can be separated without retaining raw visual media.

Brainvision remains isolated. Its DTO is not selected as a universal observation model; its identifiers, sequence model, quantization, and schema are neither reused nor generalized here. No Brainvision integration is authorized.

## 9. Audio deferral

`AUDIO_IMPLEMENTATION_CAN_WAIT`

The following are not prerequisites for Memory Substrate design:

- Better STT or TTS.
- Streaming, barge-in, or multilingual speech.
- Prosody, speaker recognition, emotional speech, or multiple microphones.
- Raw-audio storage or native audio-language models.
- Voice-client provenance repair or voice-client auth repair.

> Voice-originated memories written under the present client remain historically ambiguous because source modality and transcription derivation are not durably recorded. This ambiguity may be irreversible for those rows. It is accepted current debt, not a blocker to database design.

No retroactive classification is authorized.

## 10. Binding invariant

> **PRE-DATABASE INVARIANT 2 — MODALITY-INDEPENDENT INGEST**
>
> Canonical TORMENT memory meaning must be independent of the implementation used to observe or interpret information without becoming blind to its known provenance.
>
> Origin/authority, source channel, current representation, derivation status, and memory role are distinct semantic concerns. Where a semantically material derivation is known, the system must be capable of preserving that relationship and its producing agency without requiring every internal transformation to become durable history. Unknown provenance must remain representable and must never be guessed.
>
> Storage time is not event time; interpretation uncertainty is not memory confidence; presentation modality is not source modality; source modality does not determine memory role.
>
> Truthful provenance must not require retention of raw source media, and the future substrate must not require materially mixed-origin content to share one indivisible provenance claim.

## 11. Constraints carried into future Memory Substrate design

1. Do not overload origin/authority with modality or representation format.
2. Preserve source channel separately from current representation where known.
3. Preserve received-versus-derived-versus-unknown semantics without guessing legacy state.
4. Allow material derivation provenance and producing agency/contract where known.
5. Do not structurally limit derivation to a single transformation or only memory EIDs.
6. Keep ingest/storage time distinct from source/event time.
7. Preserve known material source/participant attribution without forcing identity onto anonymous observations.
8. Keep derivation uncertainty separate from memory confidence.
9. Keep modality separate from memory role and presentation.
10. Do not require raw-media retention or a blob store to preserve provenance truth.
11. Do not force mixed-origin content into one indivisible provenance envelope.

These are semantic constraints only. No physical or logical schema is selected.

## 12. What remains deferred

- Modality vocabulary, field names, table names, and SQL schema.
- `ProvenanceV2`.
- Source object IDs, observation IDs, adapter registries, and contract-registry representation.
- Derivation-graph design and source-artifact reference representation.
- Participant/speaker model and conversation/turn model.
- Uncertainty scale and media storage.
- Migration mechanics and legacy-row classification policy beyond "do not guess".
- Brainvision integration and audio runtime repair.

## 13. Closure posture

This invariant is closed at requirement level only. It opens no audio implementation, provenance-schema implementation, database-design lane, or runtime repair.
