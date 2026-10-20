#!/usr/bin/env bash
# Native capture experiment runner. Requires explicit legally supplied USA ROM,
# complete pinned Baldosa + SNESRecomp checkout, installed SDL2/Xvfb/FFmpeg.
# Writes all footage OUTSIDE the repo. No GitHub Actions or Git writes.
set -euo pipefail
if [ "$#" != 3 ]; then
  echo "Usage: bash tools/showcase/run_dynamic_native_capture.sh BALDOSA_CHECKOUT USA_ROM OUT_DIRECTORY" >&2
  exit 2
fi
UR_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BALDOSA="$(realpath "$1")"
ROM="$(realpath "$2")"
OUT="$(realpath -m "$3")"
export GITHUB_WORKSPACE="$UR_ROOT"
export USA_ROM_SHA256=859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478
test "$(git -C "$BALDOSA" rev-parse HEAD)" = "10b864b9d14a7b7416dd909eb7b054c88faef101"
test "$(git -C "$BALDOSA/snesrecomp" rev-parse HEAD)" = "075fbe4c8e0d97b0013be541795c39cb644a9709"
printf '%s  %s\n' "$USA_ROM_SHA256" "$ROM" | sha256sum -c -
python3 "$UR_ROOT/tools/verify_rom.py" "$ROM"
python3 "$UR_ROOT/tools/showcase/build_dynamic_2p_routes.py" --self-test
python3 "$UR_ROOT/tools/select_three_project_reuse.py" --lane baldosa-integration --include-conditional --limit 3
mkdir -p "$OUT"/{routes,published,working}
export RUNNER_TEMP="$OUT/working"
export SDL_AUDIODRIVER=dummy
export PIXELS=0 KEEP_WRAM=0 TMO=300
export UR_BALDOSA_HD=1 UR_BALDOSA_HD_DENSITY=1 UR_BALDOSA_WS342=1
export UR_BALDOSA_WS342_LIVE=1 UR_RACER_HD=0
export SNESRECOMP_ROM="$ROM"
python3 "$UR_ROOT/tools/baldosa_guest_adapter_spike.py" --game "$BALDOSA" --ur-root "$UR_ROOT"
python3 "$UR_ROOT/tools/baldosa_single_presentation_scale_patch.py" --root "$UR_ROOT" --framework "$BALDOSA/snesrecomp"
python3 "$UR_ROOT/tools/baldosa_hd_host_spike.py" --game "$BALDOSA" --ur-root "$UR_ROOT"
python3 "$UR_ROOT/tools/baldosa_ws24_framework_split_patch.py" --root "$UR_ROOT" --framework "$BALDOSA/snesrecomp"
python3 "$UR_ROOT/tools/baldosa_ws24_host_spike.py" --game "$BALDOSA" --ur-root "$UR_ROOT"
python3 "$UR_ROOT/tools/showcase/stage_continuous_native_capture.py" --framework "$BALDOSA/snesrecomp"
python3 "$UR_ROOT/tools/showcase/build_dynamic_2p_routes.py" \
  --source "$BALDOSA/tests/routes/race_2p_split.txt" --output "$OUT/routes"
cmake -S "$BALDOSA" -B "$BALDOSA/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DSNESRECOMP_SDL_BACKEND=SDL2 -DSNESRECOMP_SDL3_FETCH=OFF -DRECOMP_UI_SDL3=OFF
cmake --build "$BALDOSA/build" --target UniracersSNESRecomp -j 3
export BALDOSA_REAL_BIN="$BALDOSA/build/UniracersSNESRecomp"
test -x "$BALDOSA_REAL_BIN"
if [ ! -f "$BALDOSA/build/config.ini" ]; then
  printf '%s\n' '[Sound]' 'EnableAudio = 0' > "$BALDOSA/build/config.ini"
fi
sha256sum "$BALDOSA_REAL_BIN" > "$OUT/working/native-binary-sha256.txt"
cp "$UR_ROOT/tools/showcase/native_dynamic_media_wrapper.sh" "$OUT/working/host-wrapper"
chmod +x "$OUT/working/host-wrapper"
export BIN="$OUT/working/host-wrapper"
if ! xdpyinfo -display "${DISPLAY:-:99}" >/dev/null 2>&1; then
  Xvfb :99 -screen 0 1280x720x24 -ac > "$OUT/working/xvfb.log" 2>&1 &
  trap 'kill $! 2>/dev/null || true' EXIT
  export DISPLAY=:99
  sleep 2
fi
xdpyinfo -display "$DISPLAY" >/dev/null
for name in p1-leads p2-leads; do
  script="$OUT/routes/$name.txt"
  bash "$BALDOSA/tools/run_route.sh" "$script" "$OUT/working/$name-control"
  UR_NATIVE_VIDEO_START=2100 UR_NATIVE_VIDEO_COUNT=900 \
    UR_NATIVE_VIDEO_OUTPUT="native-$name-lossless.mkv" \
    bash "$BALDOSA/tools/run_route.sh" "$script" "$OUT/working/$name-recorded"
  rec="$OUT/working/$name-recorded"
  cmp "$OUT/working/$name-control/fd/crc.txt" "$rec/fd/crc.txt"
  python3 "$UR_ROOT/tools/showcase/validate_continuous_native_capture.py" \
    --master "$rec/native-$name-lossless.mkv" \
    --frames "$rec/native-$name-lossless.mkv.frames.tsv" \
    --log "$rec/log.txt" \
    --control-crc "$OUT/working/$name-control/fd/crc.txt" \
    --recorded-crc "$rec/fd/crc.txt" \
    --count 900 --rom-sha256 "$USA_ROM_SHA256" \
    --git-sha "$(git -C "$UR_ROOT" rev-parse HEAD)" \
    --route "dynamic-$name" --out "$OUT/published/verified-$name.json"
  ffmpeg -nostdin -hide_banner -loglevel error -y -i "$rec/native-$name-lossless.mkv" \
    -vf scale=1920:1080:flags=neighbor -an -c:v libx264 \
    -preset veryfast -crf 17 -pix_fmt yuv420p -movflags +faststart \
    "$OUT/published/native-$name-900f.mp4"
done
python3 "$UR_ROOT/tools/showcase/audit_dynamic_native_2p.py" \
  --publish "$OUT/published" \
  --route-manifest "$OUT/routes/controller-provenance.json" \
  --native-sha "$OUT/working/native-binary-sha256.txt" \
  --rom-sha "$USA_ROM_SHA256" \
  --source-sha "$(git -C "$UR_ROOT" rev-parse HEAD)"
echo "Both source-verified candidate videos and contact sheets: $OUT/published"
echo "No airborne/trick claim accepted until independent visual review."
