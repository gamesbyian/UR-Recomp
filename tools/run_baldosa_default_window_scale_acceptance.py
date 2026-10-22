#!/usr/bin/env python3
"""An unset window scale follows the display's DPI and fits on it.

Windows makes the host per-monitor DPI aware and SDL3 window sizes are
pixels, so the framework's fixed default (scale 2) opened a 640x480 window
on a 200% or 4K panel. ``tools/baldosa_sdl_display_lifecycle_spike.py`` now
asks ``ur_display_default_window_scale`` when nobody chose a scale.

Real launches of the exact built game report through the placement smoke:

1. ``SNESRECOMP_UR_DISPLAY_CONTENT_SCALE=1`` (test override): scale 2, the
   window exactly twice the game's base size;
2. ``...=2``: the scale the policy gives for the usable area the game logged
   (4 on a large enough desktop, clamped down on a small one);
3. an explicit ``WindowScale = 1`` is kept and the display is not asked;
4. the in-game launcher opened and closed over the DPI default must leave
   ``WindowScale`` unset and the window size alone (recorded as refused
   where the machine has no usable OpenGL);
5. the display's content scale changing under a running game (placement
   smoke ``dpi:F``, with a test-only usable area so a hosted 1024x768
   desktop can hold 3x) must re-derive the unchosen size both ways, 2x->3x
   and 3x->2x, centred and never written to ``config.ini``;
6. the same change must leave an explicit ``WindowScale`` alone.

Fails closed. Real 150%/200% panels and moving between them are physical
checks (D18), not covered here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

DEFAULT = re.compile(r"^UR_DISPLAY default_window_scale content_scale=([\d.]+) "
                     r"usable=(\d+)x(\d+) scale=(\d+)$", re.MULTILINE)
SIZE = re.compile(r"^UR_DISPLAY_SIZE_SMOKE window=(\d+)x(\d+) scale=(\d+) "
                  r"config_scale=(\d+)$", re.MULTILINE)
FOLLOW = re.compile(r"^UR_DISPLAY reconcile reason=display_scale_changed action=follow_dpi "
                    r"scale=(\d+)->(\d+) size=(\d+)x(\d+)$", re.MULTILINE)
# Room for 3x of a 320x240 base and no more, on any desktop of at least 1024x768.
USABLE = "1100x810"
REPORT = re.compile(r"^UR_DISPLAY_PLACEMENT_SMOKE mode=", re.MULTILINE)
ACTION = re.compile(r"in-game launcher: action=(\d+)")
UNAVAILABLE = "2"
MAX_SCALE = 10  # the framework's kMaxWindowScale


def policy_scale(content: float, base_w: int, base_h: int, usable_w: int,
                 usable_h: int, max_scale: int = MAX_SCALE) -> int:
    """Mirror of ur_display_default_window_scale."""
    scale = int(2.0 * content + 0.5) if content > 0 else 2
    scale = max(scale, 2)
    if max_scale >= 2:
        scale = min(scale, max_scale)
    while (scale > 2 and usable_w > 0 and usable_h > 0 and
           (scale * base_w * 10 > usable_w * 9 or scale * base_h * 10 > usable_h * 9)):
        scale -= 1
    return scale


def launch(exe: Path, rom: Path, root: Path, label: str, video: str, timeout: int,
           config: str, smoke: str, extra: dict) -> str:
    work = root / label
    (work / "user").mkdir(parents=True)
    (work / "config.ini").write_text(config, encoding="ascii")
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(work / "user"),
           "SNESRECOMP_UR_DISPLAY_PLACEMENT_SMOKE": smoke,
           "LNG_SMOKE_FRAMES": "20",
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    env.pop("SNESRECOMP_UR_DISPLAY_CONTENT_SCALE", None)
    env.pop("SNESRECOMP_UR_DISPLAY_USABLE_OVERRIDE", None)
    env.update(extra)
    proc = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(work / "config.ini"), str(rom)],
        cwd=work, env=env, timeout=timeout, text=True, capture_output=True,
        errors="replace")
    log = proc.stdout + "\n" + proc.stderr
    (work / "game.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise ValueError(f"{label}: native game exited {proc.returncode}: {log[-1500:]}")
    if len(REPORT.findall(log)) != 1 or len(SIZE.findall(log)) != 1:
        raise ValueError(f"{label}: expected one smoke report")
    return log


def sizes(log: str) -> tuple[int, int, int, int]:
    return tuple(int(v) for v in SIZE.findall(log)[0])  # type: ignore[return-value]


def default(log: str, label: str) -> tuple[float, int, int, int]:
    found = DEFAULT.findall(log)
    if len(found) != 1:
        raise ValueError(f"{label}: expected one default-scale decision, got {found}")
    c, w, h, s = found[0]
    return float(c), int(w), int(h), int(s)


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int) -> dict:
    exe, rom, out = exe.resolve(strict=True), rom.resolve(strict=True), out.resolve()
    if out.exists():
        raise ValueError("output directory must not pre-exist")
    out.mkdir(parents=True)
    plain = "[Sound]\nEnableAudio = 0\n"

    log = launch(exe, rom, out, "content-1x", video, timeout, plain, "report",
                 {"SNESRECOMP_UR_DISPLAY_CONTENT_SCALE": "1"})
    _, usable_w, usable_h, decided = default(log, "content-1x")
    w1, h1, scale1, cfg1 = sizes(log)
    if (decided, scale1, cfg1) != (2, 2, 0) or w1 % 2 or h1 % 2:
        raise ValueError(f"content 1.0: decided={decided} scale={scale1} "
                         f"config={cfg1} window={w1}x{h1}")
    base_w, base_h = w1 // 2, h1 // 2

    log = launch(exe, rom, out, "content-2x", video, timeout, plain, "report",
                 {"SNESRECOMP_UR_DISPLAY_CONTENT_SCALE": "2"})
    _, usable_w, usable_h, decided = default(log, "content-2x")
    expected = policy_scale(2.0, base_w, base_h, usable_w, usable_h)
    w2, h2, scale2, cfg2 = sizes(log)
    if (decided, scale2, cfg2) != (expected, expected, 0) or \
            (w2, h2) != (expected * base_w, expected * base_h):
        raise ValueError(f"content 2.0 on {usable_w}x{usable_h}: decided={decided} "
                         f"scale={scale2} window={w2}x{h2}, expected {expected}")

    log = launch(exe, rom, out, "explicit-1", video, timeout,
                 plain + "\n[Graphics]\nWindowScale = 1\n", "report",
                 {"SNESRECOMP_UR_DISPLAY_CONTENT_SCALE": "2"})
    if DEFAULT.search(log):
        raise ValueError("an explicit WindowScale was overridden by the display")
    if sizes(log) != (base_w, base_h, 1, 1):
        raise ValueError(f"explicit WindowScale=1 opened {sizes(log)}")

    # Audio on (dummy driver) and both players on pads, so committing the
    # launcher's settings is not a change that restarts the process.
    log = launch(exe, rom, out, "launcher", video, timeout,
                 "[Sound]\nEnableAudio = 1\n\n[Controller]\nSourceP1 = 2\nSourceP2 = 2\n",
                 "launcher", {"SNESRECOMP_UR_DISPLAY_CONTENT_SCALE": "2"})
    actions = ACTION.findall(log)
    if len(actions) != 1:
        raise ValueError(f"launcher: expected one in-game launcher return, got {actions}")
    wl, hl, scalel, cfgl = sizes(log)
    if actions[0] != UNAVAILABLE and ((wl, hl, scalel, cfgl) != (w2, h2, scale2, 0) or
                                      re.search(r"^WindowScale\s*=\s*[1-9]",
                                                (out / "launcher" / "config.ini")
                                                .read_text(encoding="utf-8"),
                                                re.MULTILINE)):
        raise ValueError(f"the launcher turned the DPI default into a choice: "
                         f"window={wl}x{hl} scale={scalel} config={cfgl}")

    follows = {}
    for label, start, change, before, after in (("follow-up", "1", "1.5", 2, 3),
                                                ("follow-down", "1.5", "1", 3, 2)):
        log = launch(exe, rom, out, label, video, timeout, plain, f"dpi:{change}",
                     {"SNESRECOMP_UR_DISPLAY_CONTENT_SCALE": start,
                      "SNESRECOMP_UR_DISPLAY_USABLE_OVERRIDE": USABLE})
        if default(log, label)[3] != before:
            raise ValueError(f"{label}: started at {default(log, label)[3]}, expected {before}")
        found = FOLLOW.findall(log)
        want = (str(before), str(after), str(after * base_w), str(after * base_h))
        if found != [want]:
            raise ValueError(f"{label}: expected one follow {want}, got {found}")
        if sizes(log) != (after * base_w, after * base_h, after, 0):
            raise ValueError(f"{label}: window after the scale change {sizes(log)}")
        if re.search(r"^WindowScale\s*=\s*[1-9]",
                     (out / label / "config.ini").read_text(encoding="utf-8"), re.MULTILINE):
            raise ValueError(f"{label}: a followed scale was written to config.ini")
        follows[label] = f"{before}->{after}"

    log = launch(exe, rom, out, "follow-explicit", video, timeout,
                 plain + "\n[Graphics]\nWindowScale = 1\n", "dpi:1.5",
                 {"SNESRECOMP_UR_DISPLAY_USABLE_OVERRIDE": USABLE})
    if FOLLOW.search(log) or sizes(log) != (base_w, base_h, 1, 1):
        raise ValueError(f"an explicit WindowScale followed the display: {sizes(log)}")

    receipt = {
        "content_1x_scale": 2,
        "content_2x_scale": expected,
        "usable_area": f"{usable_w}x{usable_h}",
        "base_window": f"{base_w}x{base_h}",
        "explicit_window_scale_kept": True,
        "follow_display_scale": follows,
        "follow_explicit_kept": True,
        "launcher_round_trip": "refused_unavailable" if actions[0] == UNAVAILABLE
                               else "default_kept",
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "default-scale decision, run-time follow and window size from "
                 "overridden content scale and usable area; not a real "
                 "high-DPI panel or monitor move",
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    print(json.dumps(run(args.exe, args.rom, args.out, args.video, args.timeout), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
