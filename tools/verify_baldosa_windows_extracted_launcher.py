#!/usr/bin/env python3
"""Exercise the extracted ROM-free native ZIP's *actual* CMD launcher on Win32.

Runs only on Windows CI after the real guest/build/inbox-DLL acceptance.
Only our test extraction receives the CI's original verified ROM. Neither
that ROM nor generated profiles/saves are included in the published ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from assemble_baldosa_windows_candidate import (
    EXE, LAUNCHER, MANIFEST, PREFIX, README, ROM, USA_SHA256,
)

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for data in iter(lambda: fp.read(1 << 20), b""):
            h.update(data)
    return h.hexdigest()

def invoke_launcher(launcher: Path, env: dict[str, str], extra: list[str],
                    timeout: int) -> subprocess.CompletedProcess[str]:
    # One path: use the same CMD entrypoint a user double-clicks. Supplying
    # arguments tests real forwarding rather than bypassing the launcher.
    # CMD's /S /C rule removes exactly the outermost quote pair.
    # The *inner* pair must remain around the extracted .cmd pathname.
    # Passing the launcher as a separate argv after /C causes CMD to
    # misidentify the command boundary when later arguments are quoted.
    command = f'""{launcher}" {subprocess.list2cmdline(extra)}"'
    return subprocess.run(
        ["cmd.exe", "/d", "/s", "/c", command],
        cwd=launcher.parent, env=env, capture_output=True, text=True,
        errors="replace", timeout=timeout,
    )

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def run(archive: Path, personal_rom: Path, output: Path, timeout: int) -> dict:
    if os.name != "nt":
        raise ValueError("actual Windows CMD executable is required")
    if output.exists():
        raise ValueError("do not reuse/erase an existing test root")
    require(digest(personal_rom) == USA_SHA256,
            "must test with the exact pinned original USA retail ROM")
    require(archive.is_file(), "candidate archive absent")
    output.mkdir(parents=True)
    installed = output / "Extracted Baldosa Candidate With Spaces"
    installed.mkdir()
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.namelist()
        expected = {PREFIX + name for name in (EXE, LAUNCHER, README, MANIFEST)}
        require(set(members) == expected and len(members) == 4,
                "candidate ZIP has unexpected missing or additional payload")
        for name in members:
            require(not name.endswith("/"), "unexpected ZIP directory payload")
            (installed / name.removeprefix(PREFIX)).write_bytes(bundle.read(name))
    # Test the original launcher with a drive-letter path and physical spaces.
    launcher = installed / LAUNCHER
    require(launcher.is_file(), "extracted launcher not found")
    config = output / "silent.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    script = output / "bounded-guest.txt"
    script.write_text("turbo on\nwait 240\nquit\n", encoding="ascii")

    user_root = output / "Actual Modern Profile Root With Spaces"
    env = os.environ.copy()
    env.update({
        "UR_RECOMP_USER_DATA_ROOT": str(user_root),
        "SDL_AUDIODRIVER": "dummy",
        "SDL_VIDEODRIVER": "windows",
    })
    args = ["--config", str(config), "--script", str(script)]

    # A double-click with missing ROM must reject before touching user state.
    missing = invoke_launcher(launcher, env, args, timeout)
    require(missing.returncode != 0 and
            "UR-BALDOSA-STARTUP-ROM-MISSING" in
            (missing.stdout + missing.stderr),
            f"missing ROM did not fail via actual CMD entrypoint: "
            f"rc={missing.returncode} stdout={missing.stdout[-1200:]!r} "
            f"stderr={missing.stderr[-1200:]!r}")
    require(not user_root.exists(), "missing ROM created user state")

    installed_rom = installed / ROM
    installed_rom.write_bytes(b"not a valid original ROM")
    wrong = invoke_launcher(launcher, env, args, timeout)
    require(wrong.returncode != 0 and
            "UR-BALDOSA-STARTUP-PREFLIGHT" in wrong.stderr,
            "wrong ROM did not fail the actual PowerShell SHA-256 gate")
    require(not user_root.exists(), "wrong ROM created user state")

    # A valid ROM cannot authorize package-local or relative profile storage.
    installed_rom.write_bytes(personal_rom.read_bytes())
    require(digest(installed_rom) == USA_SHA256, "CI test ROM changed during copy")
    for root in (str(installed / "Injected Save Root"), "relative-save-root"):
        bad_env = {**env, "UR_RECOMP_USER_DATA_ROOT": root}
        bad = invoke_launcher(launcher, bad_env, args, timeout)
        require(bad.returncode != 0 and
                "UR-BALDOSA-STARTUP-PREFLIGHT" in bad.stderr,
                "unsafe data root was accepted by actual CMD launcher")
    require(not (installed / "Injected Save Root").exists(),
            "package-local user state was created")
    require(not user_root.exists(), "invalid root created valid profile state")

    # Real guest execution: options forwarded, Modern root opened and painted,
    # cartridge SRAM written under the same canonical user root.
    good = invoke_launcher(launcher, env, args, timeout)
    log = good.stdout + "\n" + good.stderr
    (output / "valid-launch.log").write_text(log, encoding="utf-8")
    require(good.returncode == 0,
            f"extracted CMD launcher returned {good.returncode}: {log[-2500:]}")
    for marker in ("UR_BALDOSA_MODERN_ROOT opened=1",
                   "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared"):
        require(log.count(marker) == 1,
                f"real extracted launcher did not reach shared Modern painter: {marker}")
    save = user_root / "saves" / "save.srm"
    require(save.is_file() and save.stat().st_size == 8192,
            "real installed process did not publish exact 8KiB user SRAM")
    require((user_root / "keybinds.ini").is_file(),
            "real installed process did not create canonical user config")
    require(not (installed / "saves").exists() and
            not (installed / "keybinds.ini").exists(),
            "native guest leaked writable state into extracted package")
    require(digest(installed / EXE) ==
            next(x["sha256"] for x in json.loads((installed / MANIFEST).read_text(
                encoding="utf-8"))["immutable_files"] if x["path"] == EXE),
            "tested installed executable differs from immutable manifest")

    # The ROM is never retained in evidence, and source ZIP was not modified.
    installed_rom.unlink()
    report = {
        "verified_rom_used_temporarily": True,
        "rom_not_in_archive": True,
        "missing_rom_rejected_before_user_data": True,
        "wrong_rom_rejected_before_user_data": True,
        "package_local_and_relative_root_rejected": True,
        "real_extracted_launcher_accepted": True,
        "native_root_drawn": True,
        "canonical_8192_byte_save_outside_package": True,
        "published_zip_unchanged": True,
        "archive_sha256": digest(archive),
    }
    (output / "launcher-acceptance.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, type=Path)
    ap.add_argument("--rom", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--timeout", type=int, default=80)
    args = ap.parse_args()
    if args.timeout <= 0:
        raise ValueError("positive timeout required")
    print(json.dumps(run(args.zip.resolve(), args.rom.resolve(),
                         args.out.resolve(), args.timeout), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
