# Security Hardening Summary

TORMENT v2.2

---

## Scope

A behavior-preserving security hardening pass was applied across the codebase. No features were changed, no APIs were modified, no tests were broken. The hardening focuses on safe path handling and input validation.

---

## Path Handling

All file system operations that accept user-influenced paths now use a consistent pattern:

1. **`_ensure_within_base(path, base_dir)`** — resolves both paths via `os.path.realpath()` and verifies the resolved path is inside the base directory. Raises `ValueError` on traversal attempts (CWE-22 mitigation).

2. Applied to: `DeepMemoryStore`, `WarmupTracker`, `SpiritReflectionStore`, and all per-agent storage paths.

3. Pattern:
```python
base = os.path.realpath(base_dir)
resolved = os.path.realpath(str(path))
if resolved != base and not resolved.startswith(base + os.sep):
    raise ValueError("Path escapes base directory")
```

---

## Input Validation

**API layer:** `_validate_path_component(name, label)` rejects workspace/agent IDs containing path separators (`/`, `\\`) or traversal sequences (`..`). Applied to all endpoints that accept workspace_id or agent_id.

**Storage layer:** all JSONL deserialization uses defensive `d.get()` with explicit defaults and type casting. Malformed records are skipped with logging, never crash the loader.

---

## Tamper Resistance

**Spirit reflection:** `eligible_for_spirit_return` is forced to `False` in `SpiritReflectionEvent.from_dict()` regardless of what's stored on disk. Even if someone edits the JSONL file, deserialization enforces the constraint. Tested explicitly in `test_spirit_reflection_integration.py::test_tampering_eligible_field_on_disk`.

---

## Behavior Preservation

All hardening changes are behavior-preserving:

- No API signatures changed
- No response formats changed
- No new dependencies added
- Full test suite passes (1266+ tests, same as before hardening)
- Hardening is invisible to callers unless they attempt path traversal or invalid input

---

## What Is NOT Covered

- Network-level hardening (TLS, firewall) — TORMENT is designed for local deployment
- Authentication bypass testing — auth is optional and covered by `auth.py`
- Denial of service — no rate limiting on endpoints (local-first design)
- Embedding provider security — external API calls are out of scope

For vulnerability reporting, see `SECURITY.md`.
