#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$UR_EXPERIMENT_OUTPUT_DIR"
python3 -m py_compile tools/wide07_motion_evidence.py
python3 tools/wide07_motion_evidence.py --selftest | tee "$UR_EXPERIMENT_OUTPUT_DIR/wide07-motion-selftest.txt"
printf '%s\n' "$UR_EXPERIMENT_SOURCE_SHA" > "$UR_EXPERIMENT_OUTPUT_DIR/source-sha.txt"
