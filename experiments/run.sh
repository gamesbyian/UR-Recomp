#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$UR_EXPERIMENT_OUTPUT_DIR"
bash experiments/dragster-original.sh
bash experiments/dragster-native.sh
python3 - "$UR_EXPERIMENT_OUTPUT_DIR" <<'PY'
import pathlib,json,sys
p=pathlib.Path(sys.argv[1])
native=json.loads((p/'native/checkpoints.json').read_text())
for tag in ('race-results','result-ack-one','result-ack-two'):
 f=p/'original/dumps'/ (tag+'.wram.bin')
 if not f.exists(): raise SystemExit('Missing original '+tag)
 b=f.read_bytes()
 n=next((x for x in native if x['name']==tag+'.wram'),None)
 print(tag, 'original', b[0x9f],b[0xce],b[0x313], 'native',n)
 if n is None: raise SystemExit('Missing native '+tag)
 if (b[0x9f],b[0xce],b[0x313]) != (n['menu'],n['track'],n['in_race']): raise SystemExit('State divergence '+tag)
PY
