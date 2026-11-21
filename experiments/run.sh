#!/usr/bin/env bash
set -euo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"
mkdir -p "$OUT"
printf 'source=%s\n' "$UR_EXPERIMENT_SOURCE_SHA" > "$OUT/receipt.txt"
sudo apt-get -o Acquire::Retries=3 update
sudo apt-get -o Acquire::Retries=3 install -y --no-install-recommends pkg-config libgl-dev libx11-dev libxext-dev libxrandr-dev libxcursor-dev libxi-dev libxfixes-dev libxkbcommon-dev libwayland-dev libasound2-dev libpulse-dev libxss-dev libxtst-dev xvfb xauth
python3 tools/verify_rom.py reference/roms/retail/Uniracers_USA.sfc
python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only
FRAMEWORK="$PWD/.tools/src/snesrecomp"
TMP="$(mktemp -d)"
SNESRECOMP_ROOT="$FRAMEWORK" sh "$FRAMEWORK/tools/new_project/setup_project.sh" --rom "$PWD/reference/roms/retail/Uniracers_USA.sfc" --dir "$TMP" --name Uniracers --players 2 --yes --no-ci --no-fetch-boxart --no-recomp-ui --no-netplay --no-github --no-submodules --no-generate --no-build
ROOT="$TMP/UniracersSNESRecomp"
python3 tools/prepare_native_widescreen_product.py --framework "$FRAMEWORK" --project "$ROOT" --rom "$PWD/reference/roms/retail/Uniracers_USA.sfc" --json-out "$OUT/prepare.json"
python3 tools/patch_modern_product_host.py "$ROOT/src/main.c" --game-rtl "$ROOT/src/game_rtl.c" --cmake "$ROOT/CMakeLists.txt"
python3 tools/bootstrap_toolchain.py --offline --tool sdl3 --clone-only
cmake -S "$ROOT" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DSNESRECOMP_ROOT="$FRAMEWORK" -DSNESRECOMP_SDL_BACKEND=SDL3 -DSNESRECOMP_SDL3_FETCH=ON -DSNESRECOMP_SDL3_SOURCE_DIR="$PWD/.tools/src/sdl3/SDL3-3.4.10"
cmake --build "$ROOT/build" -j4
EXE="$ROOT/build/UniracersSNESRecomp"
test -x "$EXE"
SAVE="$TMP/fresh-dragster-save"
mkdir -p "$SAVE" "$TMP/dumps"
printf '[General]\nDisableFrameDelay = 1\n' > "$SAVE/config.ini"
# Real shipping guest/controller script. Preserve only bounded non-ROM diagnostics.
set +e
SNESRECOMP_USER_DATA_DIR="$SAVE" SNESRECOMP_DUMP_DIR="$TMP/dumps" SDL_AUDIODRIVER=dummy timeout 170s xvfb-run -a "$EXE" "$PWD/reference/roms/retail/Uniracers_USA.sfc" --script "$PWD/experiments/dragster-advance.script" > "$OUT/player.log" 2>&1
status=$?
set -e
printf 'route_exit=%s\n' "$status" >> "$OUT/receipt.txt"
grep -E 'config dir anchored|script|timeout|error|result' "$OUT/player.log" | tail -100 > "$OUT/route-signals.txt" || true
python3 - "$TMP/dumps" "$OUT" <<'PY'
import json,sys,hashlib,pathlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
records=[]
for f in sorted(root.glob("*.wram.bin")):
    data=f.read_bytes()
    def u16(addr): return int.from_bytes(data[addr:addr+2], "little") if len(data) >= addr+2 else None
    records.append(dict(
        name=f.stem, size=len(data), sha256=hashlib.sha256(data).hexdigest(),
        menu=data[0x9f], track=data[0xce], in_race=data[0x313],
        guest_state_word_0053=u16(0x53),
        direct_page_c6=u16(0xc6), direct_page_c8=u16(0xc8),
        direct_page_c0_cf=data[0xc0:0xd0].hex(),
    ))
(out/"checkpoints.json").write_text(json.dumps(records,indent=2))
print(json.dumps(records))
PY
# Fail explicitly when real result checkpoint is absent. Do not confuse the terminal
# driving dump with scored result or progression.
test -s "$TMP/dumps/race-results.wram.bin" || { echo "DRAGSTER_RESULT_NOT_REACHED" | tee -a "$OUT/receipt.txt"; exit 21; }

test -s "$TMP/dumps/after-results-ack.wram.bin" || { echo "RESULT_ACK_NOT_CAPTURED" | tee -a "$OUT/receipt.txt"; exit 22; }
python3 - "$TMP/dumps" "$OUT" <<'PY'
import pathlib,json,sys,hashlib
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2])
a=(root/"race-results.wram.bin").read_bytes();b=(root/"after-results-ack.wram.bin").read_bytes()
p={"results_menu":a[0x9f],"after_ack_menu":b[0x9f],"changed_wram_bytes":sum(x!=y for x,y in zip(a,b)),"after_ack_sha256":hashlib.sha256(b).hexdigest()}
(out/"advance.json").write_text(json.dumps(p,indent=2))
PY
mkdir -p "$TMP/cold-dumps"
set +e
SNESRECOMP_USER_DATA_DIR="$SAVE" SNESRECOMP_DUMP_DIR="$TMP/cold-dumps" SDL_AUDIODRIVER=dummy timeout 90s xvfb-run -a "$EXE" "$PWD/reference/roms/retail/Uniracers_USA.sfc" --script "$PWD/experiments/dragster-cold.script" > "$OUT/cold.log" 2>&1
cold_status=$?
set -e
printf 'cold_exit=%s\n' "$cold_status" >> "$OUT/receipt.txt"
test "$cold_status" -eq 0 || { echo "COLD_PROCESS_FAILED" | tee -a "$OUT/receipt.txt"; exit 23; }
test -s "$TMP/cold-dumps/cold-main-menu.wram.bin" || { echo "COLD_CHECKPOINT_ABSENT" | tee -a "$OUT/receipt.txt"; exit 24; }
python3 - "$TMP/cold-dumps/cold-main-menu.wram.bin" "$SAVE" "$OUT" <<'PY'
import pathlib,json,sys,hashlib
w=pathlib.Path(sys.argv[1]).read_bytes();save=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3])
files=[{"path":str(p.relative_to(save)),"size":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(save.rglob("*")) if p.is_file() and p.name!="config.ini"]
(out/"cold.json").write_text(json.dumps({"cold_menu":w[0x9f],"cold_wram_sha256":hashlib.sha256(w).hexdigest(),"persistent_files":files},indent=2))
PY
echo "DRAGSTER_RESULT_ACK_AND_COLD_PROCESS_OBSERVED_ORIGINAL_PARITY_PENDING" | tee -a "$OUT/receipt.txt"

echo "DRAGSTER_RESULT_OBSERVED_SOURCE_AND_COLD_SAVE_UNQUALIFIED" | tee -a "$OUT/receipt.txt"
