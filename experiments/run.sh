#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$UR_EXPERIMENT_OUTPUT_DIR"
python3 -m py_compile tools/wide07_real_frame_lut.py
python3 tools/wide07_real_frame_lut.py --selftest | tee "$UR_EXPERIMENT_OUTPUT_DIR/real-frame-lut-selftest.log"
printf 'SOURCE_SHA=%s\n' "$UR_EXPERIMENT_SOURCE_SHA" > "$UR_EXPERIMENT_OUTPUT_DIR/receipt.txt"
