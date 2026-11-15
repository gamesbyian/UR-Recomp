#!/usr/bin/env bash
set -euo pipefail
python3 tests/unit/test_qa02_candidate_identity.py
python3 -m py_compile tools/qa02_candidate_identity.py tools/qa02_exact_owner_win32_seam.py tools/qa02_exact_owner_two_games.py
printf 'QA02_IDENTITY_UNIT_PASS source=%s\n' "$UR_EXPERIMENT_SOURCE_SHA" | tee "$UR_EXPERIMENT_OUTPUT_DIR/identity-unit.txt"
