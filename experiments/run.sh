#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$UR_EXPERIMENT_OUTPUT_DIR"
python3 -m py_compile tools/wide07_rgb_channel_diagnostic.py
python3 tools/wide07_rgb_channel_diagnostic.py --selftest | tee "$UR_EXPERIMENT_OUTPUT_DIR/rgb-diagnostic-test.log"
sha256sum tools/wide07_rgb_channel_diagnostic.py > "$UR_EXPERIMENT_OUTPUT_DIR/source.sha256"
printf 'SOURCE_SHA=%s\n' "$UR_EXPERIMENT_SOURCE_SHA" > "$UR_EXPERIMENT_OUTPUT_DIR/receipt.txt"
