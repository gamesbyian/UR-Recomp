#!/usr/bin/env python3
"""Real packaged Windows SDL audio after Modern Exit-to-Frontend from a race.

The existing shipping host acceptance requests actual Exit to Frontend
after a canonical guest-observed race; the input script then re-enters the
stock rider selector. Observe sound from the *returned* frontend before
intentionally terminating the process and decoding closed SDL device PCM.
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

RACE = re.compile(r"(?m)^script f=(\d+) dump race-entered ok\s*$")
RETURN_MAIN = re.compile(r"(?m)^script f=(\d+) dump audio-returned-main ok\s*$")
RETURN_RIDER = re.compile(r"(?m)^script f=(\d+) dump audio-returned-rider ok\s*$")
TRIGGER = re.compile(r"(?m)^UR_EXIT_FRONTEND ACCEPTANCE_TRIGGER surface=1 pause=\d+ exit=\d+\s*$")
REQUEST = re.compile(r"(?m)^UR_EXIT_FRONTEND REQUESTED source=\d+ sram=[0-9A-Fa-f]+ practice=\d+\s*$")
READY = re.compile(r"(?m)^UR_EXIT_FRONTEND FRONTEND_READY menu=D7 sram=[0-9A-Fa-f]+\s*$")
USABLE = re.compile(r"(?m)^UR_EXIT_FRONTEND FRONTEND_USABLE menu=3C sram=[0-9A-Fa-f]+\s*$")


def verify_exit_log(log: str) -> dict:
    phases = {
        "race": RACE, "trigger": TRIGGER, "request": REQUEST,
        "ready": READY, "main": RETURN_MAIN, "usable": USABLE,
        "rider": RETURN_RIDER,
    }
    found = {}
    for name, pattern in phases.items():
        matches = list(pattern.finditer(log))
        if len(matches) != 1:
            raise ValueError(f"missing or duplicate authoritative frontend audio phase {name}")
        found[name] = matches[0]

    def before(first: str, second: str) -> bool:
        return found[first].start() < found[second].start()

    if (not all(before("race", step) for step in ("trigger", "request"))
        or not before("trigger", "ready") or not before("request", "ready")
        or not before("ready", "main") or not before("main", "usable")
        or not before("usable", "rider")):
        raise ValueError("frontend audio transition milestones out of order")
    race_frame = int(found["race"].group(1))
    main_frame = int(found["main"].group(1))
    rider_frame = int(found["rider"].group(1))
    if not 0 < race_frame < main_frame < rider_frame:
        raise ValueError("invalid stock race-to-frontend guest frame chronology")
    if "UR_EXIT_FRONTEND RESET_REQUEST_FAILED" in log:
        raise ValueError("host failed to reset guest to frontend")
    return {
        "race_entered_guest_frame": race_frame,
        "frontend_main_guest_frame": main_frame,
        "frontend_rider_guest_frame": rider_frame,
        "authoritative_exit_requested": 1,
        "frontend_usable": 1,
    }


def capture(launcher: Path, script: Path, log: Path, pcm: Path, *,
            deadline_seconds: float = 110, hold_seconds: float = 4) -> dict:
    if os.name != "nt":
        raise RuntimeError("packaged frontend audio probe requires native Windows")
    if not 30 <= deadline_seconds <= 180 or not 3 <= hold_seconds <= 10:
        raise ValueError("invalid frontend audio hold/deadline")
    if not launcher.is_file() or not script.is_file():
        raise ValueError("missing real packaged Windows launcher or guest script")
    log.parent.mkdir(parents=True, exist_ok=True)
    literal = lambda p: str(p).replace("'", "''")
    cmd = f"& '{literal(launcher)}' --script '{literal(script)}'; exit $LASTEXITCODE"
    with log.open("wb") as sink:
        proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd],
            stdout=sink, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        try:
            started = time.monotonic()
            while time.monotonic() - started < deadline_seconds:
                if proc.poll() is not None:
                    raise RuntimeError("packaged Windows game exited before frontend return")
                text = log.read_text(encoding="utf-8", errors="replace")
                if USABLE.search(text) and RETURN_RIDER.search(text):
                    verify_exit_log(text)
                    break
                time.sleep(0.2)
            else:
                raise RuntimeError("timed out before authentic usable frontend return")
            end_hold = time.monotonic() + hold_seconds
            while time.monotonic() < end_hold:
                if proc.poll() is not None:
                    raise RuntimeError("game exited while frontend audio was playing")
                time.sleep(0.2)
        finally:
            _stop_entire_tree(proc)
    observed = verify_exit_log(log.read_text(encoding="utf-8", errors="replace"))
    # On Windows the SDL device PCM file can be exclusively locked until
    # the process exits. Never open it while the producer is still running.
    output = analyze(
        log, pcm, min_duration_seconds=15,
        min_channel_rms=50,
        tail_seconds=1.0, min_tail_rms=50, min_tail_channel_rms=50,
    )
    if output["sample_rate"] != 44100 or output["channels"] != 2:
        raise ValueError("frontend output is not the negotiated 44.1k stereo SDL device")
    return {
        "schema_version": 1,
        "authority": "packaged-Windows first race -> actual host Exit-to-Frontend",
        "device_origin": output["audio_origin"],
        **observed,
        "frontend_last_second_channel_rms": output["tail_channel_rms"],
        "frontend_last_second_combined_rms": output["tail_rms"],
        "frontend_last_second_nonzero_fraction": output["tail_nonzero_fraction"],
        "whole_capture_pcm_frames": output["pcm_frames"],
        "whole_capture_rms": output["rms"],
        "limits": "real device playback after usable stock rider select; not calibrated guest/DSP note parity",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("windows_launcher", type=Path)
    parser.add_argument("windows_script", type=Path)
    parser.add_argument("capture_log", type=Path)
    parser.add_argument("device_pcm", type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    args = parser.parse_args()
    report = capture(
        args.windows_launcher, args.windows_script, args.capture_log, args.device_pcm
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "WINDOWS_EXIT_FRONTEND_AUDIO PASS "
        f"race_f={report['race_entered_guest_frame']} "
        f"rider_f={report['frontend_rider_guest_frame']} "
        f"stereo_tail_rms={report['frontend_last_second_channel_rms']} "
        "source=packaged-sdl3"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
