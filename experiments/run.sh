#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$UR_EXPERIMENT_OUTPUT_DIR"
python3 -m py_compile tools/wide07_green_lut.py
python3 tools/wide07_green_lut.py --selftest | tee "$UR_EXPERIMENT_OUTPUT_DIR/green-lut-selftest.log"
printf '[[105,107],[134,132],[166,165],[105,107]]\n' > "$UR_EXPERIMENT_OUTPUT_DIR/known-pairs.json"
python3 tools/wide07_green_lut.py --pairs-json "$UR_EXPERIMENT_OUTPUT_DIR/known-pairs.json" --json-out "$UR_EXPERIMENT_OUTPUT_DIR/known-pairs-result.json"
printf 'SOURCE_SHA=%s\n' "$UR_EXPERIMENT_SOURCE_SHA" > "$UR_EXPERIMENT_OUTPUT_DIR/receipt.txt"
