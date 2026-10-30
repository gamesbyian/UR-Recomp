#!/usr/bin/env bash
# One isolated real packaged Windows QA-05 Restart/audio acceptance attempt.
# Each invocation owns its own process tree, SDL PCM file, evidence and user
# state. Only the read-only, already-verified Windows package is shared.
set -euo pipefail
if [[ "$#" -ne 3 || ! "$1" =~ ^[1-5]$ ]]; then
  echo "usage: qa05_restart_attempt.sh <1..5> <launcher-win> <script-win>" >&2
  exit 2
fi
attempt="$1"
LAUNCHER_WIN="$2"
SCRIPT_WIN="$3"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"
ROOT="$RUNNER_TEMP/qa05-restart-user-$attempt"
LOG="$RUNNER_TEMP/qa05-restart-$attempt.log"
PCM="$RUNNER_TEMP/qa05-restart-$attempt.raw"
JSON="$RUNNER_TEMP/qa05-restart-$attempt.json"
# The service desktop can report no foreground focus. Isolate this setting
# per attempt without changing player defaults or other test instances.
rm -rf "$ROOT"
mkdir -p "$ROOT"
printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\n' > "$ROOT/host-state-v1.txt"
printf 'seen-v1\n' > "$ROOT/qa05-onboarding.seen"
ROOT_WIN="$(cygpath -w "$ROOT")"
ONBOARDING_WIN="$(cygpath -w "$ROOT/qa05-onboarding.seen")"
LOG_WIN="$(cygpath -w "$LOG")"
PCM_WIN="$(cygpath -w "$PCM")"
JSON_WIN="$(cygpath -w "$JSON")"
SDL_VIDEODRIVER=windows \
SDL_AUDIO_DRIVER=disk \
SDL_AUDIO_DISK_OUTPUT_FILE="$PCM_WIN" \
SDL_AUDIO_FORMAT=S16LE \
SDL_AUDIO_CHANNELS=2 \
SDL_AUDIO_FREQUENCY=44100 \
SDL_AUDIO_DISK_TIMESCALE=1.0 \
UR_EXECUTION_MODE=modern \
UR_PRODUCT_DIAGNOSTICS=1 \
UR_PAUSE_OPEN_ACCEPTANCE=1 \
UR_ONBOARDING_STATE_PATH="$ONBOARDING_WIN" \
UR_RECOMP_USER_DATA_ROOT="$ROOT_WIN" \
  python -m tools.capture_modern_restart_audio \
    "$LAUNCHER_WIN" "$SCRIPT_WIN" "$LOG_WIN" "$PCM_WIN" \
    --json-out "$JSON_WIN"
python - "$JSON" <<'PY'
import json, pathlib, sys
evidence = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert evidence.get("recovery_confirmed") is True
PY
# Preserve the twelve post-Restart guest samples, not just early happy path.
python -m tools.qa05_restart_input_guard "$LOG"
grep -Eq 'UR_HOST_STATE LOADED .*pause_on_focus_loss=0 ' "$LOG"
grep -Fq 'UR_ONBOARDING HIDDEN first_run=0' "$LOG"
if grep -Fq 'UR_FOCUS_PAUSE APPLIED' "$LOG"; then
  echo "Unexpected focus-loss auto-pause in QA-05" >&2
  exit 1
fi
rm -f "$PCM"
echo "UR_QA05_RESTART_AUDIBLE_ATTEMPT=$attempt/5 passed"
