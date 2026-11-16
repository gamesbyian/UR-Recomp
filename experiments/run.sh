#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$UR_EXPERIMENT_OUTPUT_DIR"
python3 -m py_compile tools/wide07_motion_mask.py
python3 tools/wide07_motion_mask.py --selftest | tee "$UR_EXPERIMENT_OUTPUT_DIR/motion-mask-selftest.log"
printf 'SOURCE_SHA=%s\n' "$UR_EXPERIMENT_SOURCE_SHA" > "$UR_EXPERIMENT_OUTPUT_DIR/receipt.txt"
