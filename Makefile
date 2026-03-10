.PHONY: test verify py_compile sim_verify

test:
	pytest -q

# Ship gate: compile + tests + deterministic sim record/replay check.
verify: py_compile test sim_verify

py_compile:
	python -m py_compile \
		torment_service/app.py \
		torment_service/fabric.py \
		torment_service/memory_graph.py \
		torment_service/memory_kernel.py \
		torment_service/scoring.py \
		torment_service/embeddings.py \
		torment_service/roles.py \
		torment_service/config_view.py \
		sim/run_sim.py \
		sim/metrics.py \
		sim/scenarios.py

sim_verify:
	python tools/verify.py
