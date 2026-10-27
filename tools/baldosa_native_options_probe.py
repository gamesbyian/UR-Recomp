#!/usr/bin/env python3
"""Actual native Modern OPTIONS: controller journey, persistence, damage.

Real native game processes drive the production P1 semantic gamepad handler
(Down x4, A, LEFT/RIGHT, B). Checked claims, each from a fresh process:

1. Display, VSync and Volume change live, are saved (options-v1.txt through
   the existing typed HostSettings codec; config.ini [Sound] Volume), and the
   racer selector host-state-v1.txt is never created or touched by Options.
2. A new process restores them before its window exists, DEFAULTS restores
   all three, and a further process boots the defaults.
3. A damaged options-v1.txt is reported, not forced onto the host, kept aside
   as .damaged on the first explicit change, and the game still starts.
4. A fifth cold process reopens the newly written file under a non-ACP Unicode
   user root without altering the preserved damaged bytes.

Semantic pad edges, not physical-controller acceptance; no release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from baldosa_native_first_racer_probe import run_game
from baldosa_windows_native_pause_route import USA_SHA256, sha256

IDLE = "turbo on\nwait 600\nquit\n"
LINE = re.compile(
    r"UR_BALDOSA_MODERN_ROOT (options_[a-z_]+) row=(\w+) display=(\w+) "
    r"vsync=(\w+) volume=(\d+) status=(.*?) help=(\d) load=(\w+)")


def events(log: str) -> list[tuple[str, ...]]:
    return [m.groups() for m in LINE.finditer(log)]


def require(log: str, event: str, **expected: str) -> None:
    keys = ("event", "row", "display", "vsync", "volume", "status",
            "help", "load")
    for found in events(log):
        row = dict(zip(keys, found))
        if row["event"] == event and all(
                row[k] == v for k, v in expected.items()):
            return
    raise ValueError(f"Missing native Options event {event} {expected}; "
                     f"saw {events(log)[-6:]}")


def gamepad_count(log: str) -> int:
    return log.count("UR_BALDOSA_MODERN_ROOT options_gamepad frame=")


def config_volume(work: Path) -> int:
    match = re.search(r"(?m)^Volume\s*=\s*(\d+)\s*$",
                      (work / "config.ini").read_text(encoding="utf-8"))
    if not match:
        raise ValueError("Framework config.ini did not record Volume")
    return int(match.group(1))


def settings_of(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep:
            out[key] = value
    return out


def digest(path: Path):
    """Bounded receipt for one small settings file: size and SHA-256 only."""
    if not path.is_file() or path.is_symlink():
        return None
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def options_probe_user_root(out: Path) -> Path:
    """Exercise the real Win32 user-root seam beyond the active ANSI codepage."""
    return out / "Fresh Options User 漢字"


def verify_post_quarantine_cold_reopen(
        log: str, options: Path, saved: bytes, damaged_bytes: bytes) -> None:
    """A second process must reload the fresh state without touching either file."""
    require(log, "options_boot", display="BORDERLESS", vsync="ON",
            volume="100", load="loaded")
    if not options.is_file() or options.read_bytes() != saved:
        raise ValueError("Cold Options reopen altered fresh saved bytes")
    damaged = Path(str(options) + ".damaged")
    if not damaged.is_file() or damaged.read_bytes() != damaged_bytes:
        raise ValueError("Cold Options reopen altered quarantined bytes")


def run(exe: Path, rom: Path, out: Path, *, timeout: int, video: str) -> dict:
    for path in (exe, rom):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing/redirected native Options runner input")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Options probe requires the pinned USA retail ROM")
    out.mkdir(parents=True, exist_ok=False)
    user = options_probe_user_root(out)
    user.mkdir()
    options = user / "options-v1.txt"
    receipts: list[dict] = []

    def receipt(stage: str, work: Path | None = None) -> None:
        entry = {"stage": stage,
                 "options_v1": digest(options),
                 "options_v1_damaged": digest(Path(str(options) + ".damaged")),
                 "host_state_v1_present": (user / "host-state-v1.txt").exists()}
        if work is not None:
            ini = work / "config.ini"
            match = re.search(r"(?m)^Volume\s*=\s*(\d+)", ini.read_text(
                encoding="utf-8")) if ini.is_file() else None
            entry["config_ini_volume"] = int(match.group(1)) if match else None
        receipts.append(entry)

    receipt("before_game1")

    # Game 1: change all three through the real P1 pad handler.
    work1 = out / "game1_change"
    g1 = run_game(exe, rom, user, work1, "12", IDLE, video, timeout)
    require(g1, "options_boot", display="WINDOWED", vsync="ON",
            volume="100", load="missing")
    require(g1, "options_opened")
    require(g1, "options_adjusted", row="DISPLAY", display="BORDERLESS",
            status="SAVED", load="loaded")
    require(g1, "options_adjusted", row="VSYNC", vsync="ADAPTIVE",
            status="SAVED")
    require(g1, "options_adjusted", row="VOLUME", volume="90",
            status="SAVED")
    require(g1, "options_activated", row="CONTROLS", help="1")
    require(g1, "options_help_closed", help="0")
    require(g1, "options_closed")
    if gamepad_count(g1) != 16:
        raise ValueError("Options route did not use the exact pad edges")
    if (user / "host-state-v1.txt").exists():
        raise ValueError("Options touched the racer selector file")
    saved = settings_of(options)
    if (saved.get("display_mode"), saved.get("vsync")) != (
            "borderless", "adaptive") or saved.get("profile") not in ("", None):
        raise ValueError(f"Unexpected persisted Options state: {saved}")
    if config_volume(work1) != 90:
        raise ValueError("Volume was not made durable in config.ini")
    receipt("after_game1_change", work1)

    # Game 2: restored before play; DEFAULTS restores all three.
    work2 = out / "game2_restore_defaults"
    work2.mkdir()
    g2 = run_game_with_config(exe, rom, user, work2, "13", video, timeout,
                              volume=90)
    require(g2, "options_boot", display="BORDERLESS", vsync="ADAPTIVE",
            volume="90", load="loaded")
    require(g2, "options_activated", row="DEFAULTS", display="WINDOWED",
            vsync="ON", volume="100", status="DEFAULTS RESTORED")
    saved = settings_of(options)
    if (saved["display_mode"], saved["vsync"]) != ("windowed", "on"):
        raise ValueError("DEFAULTS did not persist")
    if config_volume(work2) != 100:
        raise ValueError("DEFAULTS did not restore Volume")
    receipt("after_game2_restore_defaults", work2)

    # Game 3: defaults boot. Game 4: damaged file is reported and kept.
    g3 = run_game(exe, rom, user, out / "game3_defaults_boot", "0", IDLE,
                  video, timeout)
    require(g3, "options_boot", display="WINDOWED", vsync="ON",
            volume="100", load="loaded")
    receipt("after_game3_defaults_boot")
    damaged_bytes = b"UR-HOST-STATE/6\nthis is not valid\n"
    options.write_bytes(damaged_bytes)
    g4 = run_game(exe, rom, user, out / "game4_damaged", "12", IDLE,
                  video, timeout)
    require(g4, "options_boot", load="damaged")
    require(g4, "options_adjusted", row="DISPLAY",
            status="OLD FILE KEPT .damaged", load="loaded")
    if (user / "options-v1.txt.damaged").read_bytes() != damaged_bytes:
        raise ValueError("Damaged Options bytes were not preserved")
    if settings_of(options).get("display_mode") != "borderless":
        raise ValueError("Fresh Options file not written after quarantine")
    receipt("after_game4_damaged_quarantine")

    # Game 4b: cold boot the same non-ACP root. A second process must load
    # the replacement and leave both the fresh and quarantined files intact.
    saved_after_quarantine = options.read_bytes()
    g4b = run_game(exe, rom, user, out / "game4b_cold_reopen", "0",
                   IDLE, video, timeout)
    verify_post_quarantine_cold_reopen(
        g4b, options, saved_after_quarantine, damaged_bytes)
    receipt("after_game4b_cold_reopen")

    # Game 5: a config.ini the OS will not let the game rewrite. The volume
    # change must be refused and rolled back, never shown as SAVED. Skipped
    # (and recorded) where the account can write read-only files anyway.
    probe_ini = out / "readonly_probe.ini"
    probe_ini.write_text("x", encoding="ascii")
    import stat
    probe_ini.chmod(stat.S_IREAD)
    try:
        with open(probe_ini, "ab"):
            enforced = False
    except OSError:
        enforced = True
    probe_ini.chmod(stat.S_IREAD | stat.S_IWRITE)
    if enforced:
        work5 = out / "game5_readonly_config"
        work5.mkdir()
        user5 = out / "Read Only Config User"
        user5.mkdir()
        g5 = run_game_with_config(exe, rom, user5, work5, "12", video,
                                  timeout, volume=100, read_only=True)
        require(g5, "options_adjusted", row="VOLUME", volume="100",
                status="NOT APPLIED")
        if "options_adjusted row=VOLUME" in g5 and re.search(
                r"row=VOLUME .*volume=90 status=SAVED", g5):
            raise ValueError("Unwritable config was reported as SAVED")
    return {
        "scope": "native-windows-options-semantic-pad-journey",
        "readonly_config_case": "enforced_and_refused" if enforced
        else "skipped_account_can_write_readonly_files",
        "games": 5 + (1 if enforced else 0),
        "non_acp_unicode_root_exercised": True,
        "post_quarantine_cold_reopen_verified": True,
        "source_binding": {
            "github_sha": os.environ.get("GITHUB_SHA"),
            "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
            "rom_sha256": USA_SHA256,
        },
        "file_receipts": receipts,
        "persisted_after_change": {"display": "borderless",
                                   "vsync": "adaptive", "volume": 90},
        "defaults_restored": True,
        "damaged_file_preserved_aside": True,
        "racer_selector_untouched": True,
        "physical_gamepad_certified": False,
        "release_gate_credit": 0,
    }


def run_game_with_config(exe, rom, user, work, smoke, video, timeout, *,
                         volume, read_only=False):
    """run_game() rewrites config.ini; carry the prior volume forward the way
    the real launcher's persistent config.ini would."""
    import os
    import subprocess
    route = work / "stock-route.txt"
    route.write_text(IDLE, encoding="ascii")
    ini = work / "config.ini"
    ini.write_text(f"[Sound]\nEnableAudio = 0\nVolume = {volume}\n",
                   encoding="ascii")
    if read_only:
        import stat
        ini.chmod(stat.S_IREAD)
    env = {**os.environ, "SNESRECOMP_USER_DATA_DIR": str(user),
           "UR_EXECUTION_MODE": "modern", "UR_BALDOSA_MODERN_ROOT": "1",
           "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": smoke,
           "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
           "UR_BALDOSA_MODERN_INPUT": "1", "UR_BALDOSA_PAUSE_SMOKE": "0",
           "SDL_VIDEODRIVER": video, "SDL_AUDIODRIVER": "dummy"}
    try:
        proc = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(ini),
             "--script", str(route), str(rom)],
            cwd=work, env=env, capture_output=True, text=True,
            errors="replace", timeout=timeout)
    finally:
        if read_only:
            import stat
            ini.chmod(stat.S_IREAD | stat.S_IWRITE)
    log = proc.stdout + "\n" + proc.stderr
    (work / "log.txt").write_text(log, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError("Native Options guest returned "
                           f"{proc.returncode}: {log[-2000:]}")
    return log


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    report = run(args.exe.resolve(), args.rom.resolve(), args.out.resolve(),
                 timeout=args.timeout, video=args.video)
    (args.out.resolve() / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: native Windows Options non-ACP root, change/restore/defaults/"
          "damaged-file quarantine and cold reopen; physical pads and "
          "release gates remain unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
