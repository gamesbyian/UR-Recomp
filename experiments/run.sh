#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$UR_EXPERIMENT_OUTPUT_DIR"
python3 -m py_compile tools/wide07_phase_index.py
python3 tools/wide07_phase_index.py --selftest | tee "$UR_EXPERIMENT_OUTPUT_DIR/phase-index-selftest.txt"
printf '%s\n' "$UR_EXPERIMENT_SOURCE_SHA" > "$UR_EXPERIMENT_OUTPUT_DIR/source-sha.txt"
