# Rollback Procedure: Archivist Writeback

**Applies to:** `TORMENT_ARCHIVIST_WRITEBACK=1` (opt-in activation)
**Reference:** `docs/ARCHIVIST_WRITEBACK_GATE_FRAMING_v2.4.x.md` §6.4, §7 D5

---

## When to roll back

Roll back if any of the following occur after enabling writeback:

- The recursion guard admits a proposal it should have rejected (ancestry laundering).
- Writeback memories contain degenerate, repetitive, or identity-destabilizing content.
- Drift enforcement fails to block proposals during hard-block conditions.
- Unexpected provenance shapes appear in writeback memories.
- Any operational concern the operator judges warrants reverting.

The gate is designed to be flipped back instantly with no schema migration.

---

## Step 1 — Disable the gate

Set the environment variable to `0` and restart the service:

```
TORMENT_ARCHIVIST_WRITEBACK=0
```

On Windows (cmd):
```
set TORMENT_ARCHIVIST_WRITEBACK=0
```

Restart the TORMENT service. The gate check is at `cognition/pipeline.py` line 115 — once `0`, no new writeback proposals will be ingested regardless of archivist approvals.

This step is instant and sufficient to stop the bleeding. Steps 2–3 are optional recovery.

---

## Step 2 — Inspect writeback memories (optional)

List all memories produced by writeback to assess scope:

```
py -3 scripts/writeback_quarantine.py --list --data-dir data/
```

This scans every workspace and agent for entities with `write_path: "cognition_writeback"` or `source_role: "archivist_writeback"`. It prints EID, provenance fields, and a truncated summary for each.

If no writeback memories exist (gate was on briefly or no cognition ran), the output will show zero entities and no further action is needed.

---

## Step 3 — Quarantine or remove (optional)

If writeback produced bad memories that should be neutralized:

**Tag as quarantined** (non-destructive — marks provenance with `quarantined: true`):
```
py -3 scripts/writeback_quarantine.py --tag --data-dir data/ --confirm
```

**Remove via tombstone** (appends a `payload=null, alive=false` record — the entity disappears from the live graph on next load):
```
py -3 scripts/writeback_quarantine.py --remove --data-dir data/ --confirm
```

Both commands support dry-run by omitting `--confirm`. Always dry-run first.

Tagging is preferred when the memories are merely suspicious — it preserves them for inspection while preventing the recursion guard from admitting them as parents (the guard rejects quarantined provenance as unknown/malformed).

Removal is for confirmed bad content. The original JSONL records are still in the append log for forensics, but the tombstone makes them invisible to the live graph.

---

## What does NOT need to happen

- **No schema migration.** Writeback memories use the same `ProvenanceV1` schema as all other memories. Rolling back is a gate flip, not a data migration.
- **No Spine changes.** The Spine path is intentionally read-only (D1) and never produced writeback in the first place.
- **No identity state cleanup.** Writeback does not touch identity state, bands, or the coupled-oscillator kernel. Rolling back the gate does not require any kernel-level recovery.
- **No code revert.** The writeback code path remains in the codebase behind the gate. Setting `TORMENT_ARCHIVIST_WRITEBACK=0` is sufficient.

---

## Verification after rollback

After disabling the gate and optionally quarantining, verify the corpus is clean:

```
py -3 scripts/writeback_guard_reverify.py --data-dir data/
```

This runs the recursion guard against every entity in every workspace. Expect zero failures. If any quarantined or tombstoned writeback entities cause guard rejections, that is correct behavior — the guard is fail-closed on unknown or malformed provenance.
