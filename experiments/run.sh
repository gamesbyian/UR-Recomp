#!/usr/bin/env bash
set -euo pipefail

# REAL USA retail-ROM source experiment. This tests static call/reachability,
# not a moving-course emulator trace or WIDE-07 acceptance.
ROM=reference/roms/retail/Uniracers_USA.sfc
OUT="$UR_EXPERIMENT_OUTPUT_DIR"
mkdir -p "$OUT"

python3 tools/verify_rom.py "$ROM"
python3 -m unittest tests.unit.test_analyze_native_widescreen_reachability -v

python3 tools/analyze_native_widescreen_reachability.py "$ROM" \
  --json-out "$OUT/usa-wide-course-reachability.json" \
  --md-out "$OUT/usa-wide-course-reachability.md"

python3 - "$ROM" "$OUT/usa-wide-course-reachability.json" "$OUT/observation.json" <<'PY'
import hashlib, json, os, sys
from pathlib import Path
rom = Path(sys.argv[1])
report = json.loads(Path(sys.argv[2]).read_text())
targets = report["targets"]
assert set(targets) == {"long_wrapper", "per_frame_entry"}
assert report["trusted_trace_seeds"] == ["83:CBCC", "81:A52B"]
for role, entry in targets.items():
    assert entry["target"] in ("81:A52B", "81:A52F")
    for group in ("jsr", "jsl"):
        for row in entry[group]:
            assert isinstance(row["file_offset"], int)
            assert isinstance(row["executable"], bool)
result = {
    "schema": "ur-wide07-usa-source-reachability/1",
    "source_sha": os.environ["UR_EXPERIMENT_SOURCE_SHA"],
    "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
    "targets": {
        role: {
            "cpu": entry["target"],
            "jsr_references": len(entry["jsr"]),
            "jsl_references": len(entry["jsl"]),
            "executable_references": sum(row["executable"] for group in ("jsr","jsl")
                                         for row in entry[group]),
        }
        for role, entry in targets.items()
    },
    "direct_reference_count": report["direct_reference_count"],
    "moving_course_pixel_parity_proven": False,
    "usa_course_credit": 0,
    "next_action": "Execute guest moving-course replay with source-consistent scroll and widened margin RGB comparison; use observed caller sites, not synthetic replay states.",
}
Path(sys.argv[3]).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
print("WIDE07_USA_ROM_SOURCE_REACHABILITY", json.dumps(result, sort_keys=True))
PY
