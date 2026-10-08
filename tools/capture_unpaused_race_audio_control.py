#!/usr/bin/env python3
"""Control: ordinary uninterrupted 1P race through the Restart audio fixture.

No Modern pause, rewind, or Restart is enabled. An independent real Windows
process runs the identical stock guest script, reaches the later checkpoint,
then produces four further wall-clock seconds of SDL playback. The comparison
separates an ordinary quiet portion of the song from rollback-induced silence.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time

from tools.capture_modern_paused_audio import _stop_entire_tree
from tools.analyze_sdl_disk_audio import analyze
from tools.analyze_sdl_audio_envelope import extract_envelope

RACE = re.compile(r"(?m)^script f=(\d+) dump race-entered ok\s*$")
LATER = re.compile(r"(?m)^script f=(\d+) dump audio-restart-guest ok\s*$")


def verify_unpaused_control_log(log: str) -> dict:
    race = list(RACE.finditer(log))
    later = list(LATER.finditer(log))
    if len(race) != 1 or len(later) != 1:
        raise ValueError("missing or ambiguous original-game race control checkpoints")
    if race[0].start() >= later[0].start():
        raise ValueError("control checkpoints out of chronology")
    before, after = int(race[0].group(1)), int(later[0].group(1))
    if before <= 0 or after - before < 200:
        raise ValueError("control guest did not play at least 200 further frames")
    if "UR_PAUSE_ACCEPTANCE OPENED" in log or "UR_PAUSE_STATE paused=1" in log:
        raise ValueError("uninterrupted control cannot enter Modern host pause")
    return {"race_entered_frame": before, "later_unpaused_frame": after}


def capture(launcher: Path, script: Path, log: Path, pcm: Path, *,
            deadline_seconds: float = 100, hold_seconds: float = 4) -> dict:
    if os.name != "nt":
        raise RuntimeError("real Windows game required for audio control")
    if not 20 <= deadline_seconds <= 180 or not 3 <= hold_seconds <= 10:
        raise ValueError("invalid bounded audio-control duration")
    if not launcher.is_file() or not script.is_file():
        raise ValueError("missing verified packaged launcher or unchanged guest script")
    log.parent.mkdir(parents=True, exist_ok=True)
    quote = lambda p: str(p).replace("'", "''")
    command = f"& '{quote(launcher)}' --script '{quote(script)}'; exit $LASTEXITCODE"
    with log.open("wb") as sink:
        proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            stdout=sink, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        try:
            started = time.monotonic()
            while time.monotonic() - started < deadline_seconds:
                if proc.poll() is not None:
                    raise RuntimeError("normal Windows race exited before control checkpoint")
                recorded = log.read_text(encoding="utf-8", errors="replace")
                if LATER.search(recorded):
                    verify_unpaused_control_log(recorded)
                    break
                time.sleep(0.2)
            else:
                raise RuntimeError("control did not reach ordinary race checkpoint")
            until = time.monotonic() + hold_seconds
            while time.monotonic() < until:
                if proc.poll() is not None:
                    raise RuntimeError("normal race exited before audio observation")
                time.sleep(0.2)
        finally:
            _stop_entire_tree(proc)

    witness = verify_unpaused_control_log(
        log.read_text(encoding="utf-8", errors="replace")
    )
    # Windows SDL holds an exclusive writer handle until its process exits.
    report = analyze(
        log, pcm, min_duration_seconds=15, min_channel_rms=50,
        tail_seconds=1.0, min_tail_rms=0, min_tail_channel_rms=0,
        min_nonzero_fraction=0,
    )
    envelope = extract_envelope(log, pcm, last_seconds=8, window_ms=100)
    if report["sample_rate"] != 44100:
        raise ValueError("unexpected Windows SDL control sample rate")
    return {
        "schema_version": 1,
        "authority": "real unchanged one-player race, without Modern rewind",
        "device_origin": report["audio_origin"],
        **witness,
        "tail_one_second_channel_rms": report["tail_channel_rms"],
        "tail_one_second_combined_rms": report["tail_rms"],
        "tail_one_second_nonzero_fraction": report["tail_nonzero_fraction"],
        "last_eight_seconds_envelope": envelope,
        "note": "descriptive control; independently assess whether expected race music persists",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("windows_launcher", type=Path)
    parser.add_argument("windows_script", type=Path)
    parser.add_argument("capture_log", type=Path)
    parser.add_argument("device_pcm", type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    a = parser.parse_args()
    result = capture(
        a.windows_launcher, a.windows_script, a.capture_log, a.device_pcm
    )
    a.json_out.parent.mkdir(parents=True, exist_ok=True)
    a.json_out.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print("WINDOWS_UNPAUSED_RACE_AUDIO_CONTROL PASS "
          f"tail_rms={result['tail_one_second_combined_rms']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
