# Frozen coherence contract — Phase 1B

`G_coherence_closure.json` is the exact, unmodified 55-case candidate subset of
the accepted external Phase 1A freeze. Its SHA-256 is
`fb64ddb6e41f390de5daac6eb2e3d1ede192f115a42a68920eb87ffb6fbbcead`.
The adjacent `.gitattributes` disables text conversion for these frozen bytes.
[provenance.json](provenance.json) identifies the production-before commit,
external manifest, origin, admission date and numerical environment.

The [candidate tests](../../test_coherence_cleanup_frozen_contract.py) compare
each existing coherence function independently with its own inert expected
record. They do not calculate expectations from scientific helpers or from the
other function. A negative control replaces both helpers in memory with the
same wrong result and proves that the frozen oracle rejects both.

The tests cover all 55 source cases: 32 direct inputs tested against each entry
point, seven memory-debug fallback cases, 15 emission cases and both signatures.
They preserve exact float/complex bits, NumPy/Python scalar types, warnings,
exception type/message, shape/dtype/strides/writeability and input nonmutation.
Zero Omega has coherence magnitude **1**. The memory fallback catches
RuntimeError/ValueError/TypeError and emits zeros, propagates KeyboardInterrupt,
and passes NaN results through.

Only the pure candidate modules are imported. Memory telemetry is exercised by
compiling its current bounded debug `try/except` block from the source AST.
Static assertions protect the known imports/calls and debug dictionary fields;
the original oracle's bare import is exercised without running its model.
`apply_phase_triad_sync` is a separate function outside this cleanup. The full
service, memory processing, embeddings, databases and external models are not
required or invoked.

The original fixture also records absolute capture paths, line numbers, AST
hashes and `sampler_source_only`. Those fields remain unchanged in the file as
provenance. They do not constrain current source bytes or locations and do not
cause the sampler to execute. Behavioral expectations, including signatures,
remain exact. A future authorized refactor may change implementation source
while preserving these expectations and existing interfaces.

From Command Prompt at the production repository root:

```bat
conda activate torment
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python -I -B -X utf8 -m pytest -q -p no:cacheprovider tests/test_coherence_cleanup_frozen_contract.py
```

The captured numerical environment is Python 3.11.15 / NumPy 2.4.4 on Windows
AMD64. The tests use the recorded NumPy warning policy. They do not silently
skip, apply tolerance, or rewrite expectations on another environment; any
failure requires investigation. Do not run broader memory/service suites as a
substitute for this bounded admission proof.

Baseline source hashes are provenance, **not** repository test conditions.
Never regenerate this fixture from an implementation under test. No production
implementation change is part of this admission.
