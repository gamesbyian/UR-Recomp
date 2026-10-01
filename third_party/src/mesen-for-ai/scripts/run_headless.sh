#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <rom> <script.lua>" >&2
  exit 64
fi

ROM=$1
LUA_SCRIPT=$2

if [[ ! -f "$ROM" ]]; then
  echo "ROM not found: $ROM" >&2
  exit 66
fi

if [[ ! -f "$LUA_SCRIPT" ]]; then
  echo "Lua script not found: $LUA_SCRIPT" >&2
  exit 66
fi

ROM=$(realpath "$ROM")
LUA_SCRIPT=$(realpath "$LUA_SCRIPT")

MESEN_BIN=${MESEN_BIN:-"$HOME/tools/mesen-src/bin/linux-x64/Release/Mesen"}
if [[ ! -x "$MESEN_BIN" ]]; then
  echo "Mesen binary not executable: $MESEN_BIN" >&2
  exit 69
fi

SESSION_ROOT=${MESEN_MCP_SESSION_ROOT:-"$(mktemp -d -t mesen-for-ai.XXXXXX)"}
SESSION_HOME="$SESSION_ROOT/home"
SESSION_WORK="$SESSION_ROOT/work"
MESEN_SOURCE_DIR="$(dirname "$MESEN_BIN")"
MESEN_PORTABLE_DIR="$SESSION_ROOT/mesen-portable"
MESEN_CONFIG_HOME="$MESEN_PORTABLE_DIR"

mkdir -p "$SESSION_HOME" "$SESSION_WORK" "$MESEN_PORTABLE_DIR"
cp -al "$MESEN_SOURCE_DIR/." "$MESEN_PORTABLE_DIR/"
MESEN_RUN_BIN="$MESEN_PORTABLE_DIR/$(basename "$MESEN_BIN")"

if [[ -n "${MESEN_PCECD_FIRMWARE:-}" ]]; then
  if [[ ! -f "$MESEN_PCECD_FIRMWARE" ]]; then
    echo "PC Engine CD firmware not found: $MESEN_PCECD_FIRMWARE" >&2
    exit 66
  fi
  mkdir -p "$MESEN_CONFIG_HOME/Firmware"
  cp -- "$MESEN_PCECD_FIRMWARE" "$MESEN_CONFIG_HOME/Firmware/syscard3.pce"
fi

pce_port1_type="PceController"
if [[ "${MESEN_PCE_TURBOTAP:-0}" == "1" ]]; then
  pce_port1_type="PceTurboTap"
fi

cat > "$MESEN_CONFIG_HOME/settings.json" <<JSON
{
  "Debug": {
    "ScriptWindow": {
      "AllowIoOsAccess": true,
      "AllowNetworkAccess": true,
      "ScriptTimeout": 60
    }
  },
  "Snes": {
    "RamPowerOnState": 1,
    "EnableRandomPowerOnState": false,
    "Port1": { "Type": 1 },
    "Port2": { "Type": 1 }
  },
  "Nes": {
    "RamPowerOnState": 1,
    "RandomizeMapperPowerOnState": false,
    "RandomizeCpuPpuAlignment": false
  },
  "PcEngine": {
    "RamPowerOnState": 1,
    "EnableRandomPowerOnState": false,
    "Port1": {
      "Type": "$pce_port1_type"
    },
    "Port1A": { "Type": "PceController" },
    "Port1B": { "Type": "PceController" },
    "Port1C": { "Type": "None" },
    "Port1D": { "Type": "None" },
    "Port1E": { "Type": "None" }
  },
  "Gba": {
    "RamPowerOnState": 1
  },
  "Gameboy": {
    "RamPowerOnState": 1
  }
}
JSON

export HOME="$SESSION_HOME"
export DOTNET_ROLL_FORWARD="${DOTNET_ROLL_FORWARD:-Major}"

cd "$SESSION_WORK"
exec xvfb-run -a "$MESEN_RUN_BIN" --testrunner --enableStdout --doNotSaveSettings \
  "$ROM" "$LUA_SCRIPT" --timeout="${MESEN_TESTRUNNER_TIMEOUT:-30}" \
  >"$SESSION_ROOT/mesen.stdout.log" 2>"$SESSION_ROOT/mesen.stderr.log"
