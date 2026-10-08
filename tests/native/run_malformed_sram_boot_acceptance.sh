#!/usr/bin/env bash
set -Eeuo pipefail

# Native malformed-SRAM boot containment (WORK-QUEUE expert-edge item f).
# Cold-boots every synthesized malformed stock-SRAM class in Authentic and in
# an isolated Modern profile root, then checks the measured guest outcomes:
# only a damaged ASJIver3.30 signature (or a file too short to carry it) makes
# the stock boot reformat; checksum and range damage is accepted unchanged, so
# boot-bypassing host installs must apply the signature check themselves.

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$WORK"

python3 "$REPO/tools/probe_malformed_sram_containment.py" \
  --exe "$EXE" --rom "$ROM" --work "$WORK/runs" \
  --out "$WORK/malformed-sram-containment.json" | tee "$WORK/probe.log"

(
  cd "$REPO"
  UR_MALFORMED_SRAM_EVIDENCE="$WORK/malformed-sram-containment.json" \
    python3 -m unittest -v \
    tests.unit.test_probe_malformed_sram_containment.EvidenceTests
)

echo "UR_MALFORMED_SRAM_BOOT_ACCEPTANCE_RESULT=signature_only_reformat_checksums_unvalidated_modern_read_only"
