#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$UR_EXPERIMENT_OUTPUT_DIR"
python3 tools/check_release_quality_ledger_integrity.py --output "$UR_EXPERIMENT_OUTPUT_DIR/qa12-ledger-audit.json"
python3 - <<'PY'
import json, pathlib, subprocess, tempfile
p=pathlib.Path('docs/RELEASE-QUALITY-LEDGER.json')
d=json.loads(p.read_text())
assert d['candidate']['commit_sha']=='1484525fb82c9442611bd472b87d12c38f230a27'
assert d['candidate']['zip_sha256']=='32c3b8679fdf5c598e14a356f49715fc88a1569d4b26adadee1f3835267bd19f'
assert not d['candidate']['physical_hardware_verified']
assert all(g['status']!='passed' for g in d['gates'])
with tempfile.TemporaryDirectory() as t:
  f=pathlib.Path(t)/'invalid.json'
  d['gates'][11]['status']='passed'
  f.write_text(json.dumps(d))
  p=subprocess.run(['python3','tools/check_release_quality_ledger_integrity.py','--ledger',str(f)],capture_output=True,text=True)
  assert p.returncode!=0 and 'QA-12 claims exact acceptance/failure' in p.stderr,(p.returncode,p.stderr)
print('QA12_LEDGER_POSITIVE_AND_FAIL_CLOSED_PASS')
PY
