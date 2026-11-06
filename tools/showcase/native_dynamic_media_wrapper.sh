#!/usr/bin/env bash
# Disposable media-only host wrapper. Sets exact real SDL readback viewport.
set -euo pipefail
export SDL_VIDEODRIVER=x11
args=("$@")
config=""
for ((i=0; i+1<${#args[@]}; i++)); do
  if [ "${args[i]}" = "--config" ]; then
    config="${args[i+1]}"
    break
  fi
done
test -n "$config"
test -n "${BALDOSA_REAL_BIN:-}"
python3 "$GITHUB_WORKSPACE/tools/baldosa_hd_enable_renderer.py" --config "$config"
cat >> "$config" <<'CFG'
[Graphics]
WindowSize = 960x540
OutputMethod = SDL-Software
LinearFiltering = 0
Fullscreen = 0
CFG
exec "$BALDOSA_REAL_BIN" "$@"
