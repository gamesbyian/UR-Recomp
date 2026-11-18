#!/usr/bin/env bash
set -euo pipefail
python3 -m unittest tests.unit.test_find_exact_experiment_run -v 2>&1 | tee "$UR_EXPERIMENT_OUTPUT_DIR/exact-run-discovery-tests.log"
python3 tools/find_exact_experiment_run.py a31ec269a0034a8e4412ab8c438583a012a2f6a2 | tee "$UR_EXPERIMENT_OUTPUT_DIR/known-push-run.json"
python3 tools/find_exact_experiment_run.py 30a80522e6257fd784e5eae57d3d736696686a08 | tee "$UR_EXPERIMENT_OUTPUT_DIR/attempt3-push-run.json"
