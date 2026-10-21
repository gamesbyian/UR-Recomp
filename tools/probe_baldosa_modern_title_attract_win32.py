#!/usr/bin/env python3
"""Observe real original idle attract beneath native Modern title, without guest writes.

Diagnostic only: this never claims that the modern host displays the original
attract or can safely wake from it. The original guest supplies every marker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

EXPECTED_USA_ROM = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"

MARKER = re.compile(
    r"^UR_MODERN_TITLE_ORIGINAL_SOURCE "
    r"phase=(main_menu|attract_title|demo_race) "
    r"frame=(\d+) menu=([0-9a-f]{2}) race=([0-9a-f]{2}) "
    r"overlay_title=([01])$", re.MULTILINE
)
EXPECTED = ("main_menu", "attract_title", "demo_race")


def verify_original_source_attract(log: str) -> list[dict[str, int | str]]:
    if "UR_BALDOSA_MODERN_ROOT opened=1" not in log:
        raise ValueError("no real Modern native host opening in guest log")
    markers = [
        {"phase": m[1], "frame": int(m[2]), "menu": m[3],
         "race": m[4], "overlay_title": int(m[5])}
        for m in MARKER.finditer(log)
    ]
    if tuple(m["phase"] for m in markers) != EXPECTED:
        raise ValueError("missing, duplicated or reordered authentic guest states")
    a, b, c = markers
    if (a["menu"] != "d7" or b["menu"] != "84" or c["race"] != "01"
            or any(m["overlay_title"] != 1 for m in markers)):
        raise ValueError("wrong original source state or Modern title not covering guest")
    if not (a["frame"] > 0 and a["frame"] < b["frame"] < c["frame"] <= 1800):
        raise ValueError("invalid actual original guest event chronology")
    # The independent pinned Snes9x+Beetle reference measures 503 frames
    # MAIN->TITLE and 588 frames TITLE->DEMO in the first untouched cycle.
    # Fail closed if the native guest takes a different route. No timer in
    # production may be derived from this diagnostic alone.
    if b["frame"] - a["frame"] != 503:
        raise ValueError("native original main-to-title frame interval differs")
    if c["frame"] - b["frame"] != 588:
        raise ValueError("native original title-to-demo frame interval differs")
    if not (a["frame"] == 440 and b["frame"] == 943 and c["frame"] == 1531):
        raise ValueError("native original guest first-cycle timestamps differ")
    return markers


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--script", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--timeout", type=int, default=120)
    args = p.parse_args()
    if os.name != "nt":
        p.error("native original-guest attract requires real Windows AOT")
    if not 30 <= args.timeout <= 150:
        p.error("timeout must be 30..150 seconds")
    exe, rom, script = (path.resolve(strict=True) for path in
                        (args.exe, args.rom, args.script))
    if hashlib.sha256(rom.read_bytes()).hexdigest() != EXPECTED_USA_ROM:
        raise ValueError("unexpected original USA ROM SHA256")
    binary = exe.read_bytes()
    if not binary.startswith(b"MZ"):
        raise ValueError("no genuine native Windows executable")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    user = out / "player"
    user.mkdir()
    cfg = out / "config.ini"
    cfg.write_text("[Sound]\nEnableAudio = 0\n", encoding="utf-8")
    env = dict(os.environ)
    env.pop("UR_BALDOSA_MODERN_ROOT_KEY_SMOKE", None)
    env.update({
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "SNESRECOMP_USER_DATA_DIR": str(user),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
        "UR_BALDOSA_MODERN_TITLE_ATTRACT_PROBE": "1",
        "UR_REDUCED_MOTION": "0",
    })
    cmd = [str(exe), "--no-launcher", "--config", str(cfg),
           "--script", str(script), str(rom)]
    try:
        run = subprocess.run(
            cmd, cwd=out, env=env, timeout=args.timeout,
            capture_output=True, text=True, errors="replace")
    except subprocess.TimeoutExpired as exc:
        (out / "native-attract-timeout.txt").write_text(str(exc))
        raise
    log = run.stdout + "\n" + run.stderr
    (out / "native-attract.log").write_text(log, encoding="utf-8")
    if run.returncode:
        raise ValueError(f"real Windows native attract process exited {run.returncode}")
    observed = verify_original_source_attract(log)
    receipt = {
        "schema_version": 1,
        "candidate_executable_sha256": hashlib.sha256(binary).hexdigest(),
        "pinned_original_usa_rom_sha256": EXPECTED_USA_ROM,
        "actual_guest_source_markers": observed,
        "log_sha256": hashlib.sha256(log.encode("utf-8")).hexdigest(),
        "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "diagnostic_guest_writes": False,
        "human_button_actions": 0,
        "modern_host_title_remained_visible": True,
        "original_attract_displayed": False,
        "wake_input_tested": False,
        "final_sdl_capture": False,
        "release_gate_credit": 0,
    }
    (out / "native-attract-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("UR_MODERN_TITLE_GENUINE_ATTRACT_SOURCE=passed")
    for m in observed:
        print(f"{m['phase']}={m['frame']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
