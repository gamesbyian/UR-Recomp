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
    # 'call' is a command token *before* the quoted batch pathname.
    # This avoids CMD's /C outer-quote removal rules entirely, while
    # preserving normal quoted arguments and the actual .cmd execution path.
    # Unlike /S /C ""path" args", this cannot be mistaken for a UNC path.
    return subprocess.run(
        ["cmd.exe", "/d", "/c", "call", str(launcher), *extra],
        cwd=launcher.parent, env=env, capture_output=True, text=True,
        errors="replace", timeout=timeout,
    )

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def require_archive_unchanged(archive: Path, starting_sha256: str) -> None:
    # The release candidate bytes must be the SAME after every CMD launch,
    # not merely rehashed once at the end and reported as unchanged.
    require(digest(archive) == starting_sha256,
            "candidate ZIP changed during Windows launcher acceptance")


def verify_first_user_cmd_relaunch_log(log: str) -> None:
    """Accept one actual no-args CMD create -> quit -> native reentry receipt.

    Synthetic fixture strings here are parser-only, never release or physical
    pad credit. The Windows acceptance additionally runs the real two child
    processes, validates on-disk profile data, and hashes the immutable ZIP.
    """
    mandatory = (
        "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
        "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike "
        "activation=next_process",
        "UR_BALDOSA_MODERN_ROOT first_racer_created=1 "
        "activation=next_process",
        "UR-BALDOSA-FIRST-RACER: Restarting with newly created racer.",
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
        "root=saves/profile-mike",
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike ",
    )
    positions = []
    for token in mandatory:
        require(log.count(token) == 1,
                "No unique actual CMD first-racer stage: " + token)
        positions.append(log.index(token))
    require(positions == sorted(positions),
            "Native first-user CMD opened named game before canonical create")
    require(log.count("UR_BALDOSA_MODERN_ROOT opened=1") == 2,
            "CMD must launch exactly two original native game processes")


def run(archive: Path, personal_rom: Path, output: Path, timeout: int) -> dict:
    if os.name != "nt":
        raise ValueError("actual Windows CMD executable is required")
    if output.exists():
        raise ValueError("do not reuse/erase an existing test root")
    require(digest(personal_rom) == USA_SHA256,
            "must test with the exact pinned original USA retail ROM")
    require(archive.is_file(), "candidate archive absent")
    approved_archive_sha256 = digest(archive)
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
            "UR-BALDOSA-STARTUP-ROM-INVALID" in wrong.stderr,
            "wrong ROM did not fail the actual PowerShell SHA-256 gate")
    require(not user_root.exists(), "wrong ROM created user state")

    # A valid ROM cannot authorize package-local or relative profile storage.
    installed_rom.write_bytes(personal_rom.read_bytes())
    require(digest(installed_rom) == USA_SHA256, "CI test ROM changed during copy")
    for root in (str(installed / "Injected Save Root"), "relative-save-root"):
        bad_env = {**env, "UR_RECOMP_USER_DATA_ROOT": root}
        bad = invoke_launcher(launcher, bad_env, args, timeout)
        require(bad.returncode != 0 and
                "UR-BALDOSA-STARTUP-SAVE-ROOT" in bad.stderr,
                "unsafe data root was accepted by actual CMD launcher")
    require(not (installed / "Injected Save Root").exists(),
            "package-local user state was created")
    require(not user_root.exists(), "invalid root created valid profile state")

    # On real NTFS a junction *outside* the game folder can point inside.
    # GetFullPath's lexical check alone cannot detect that alias. Exercise
    # the actual CMD->PowerShell launcher on the same extracted Windows ZIP.
    junction = output / "Outside User Root Junction"
    created = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(installed)],
        cwd=output, capture_output=True, text=True, errors="replace",
        timeout=timeout,
    )
    require(created.returncode == 0 and junction.is_dir(),
            "Windows junction fixture unavailable: " +
            (created.stdout + created.stderr)[-900:])
    junction_root = junction / "Redirected Profile Data"
    aliased_env = {**env, "UR_RECOMP_USER_DATA_ROOT": str(junction_root)}
    aliased = invoke_launcher(launcher, aliased_env, args, timeout)
    require(aliased.returncode == 3 and
            "UR-BALDOSA-STARTUP-SAVE-ROOT" in aliased.stderr,
            "junction-backed user-data root bypassed actual launcher preflight")
    require(not (installed / "Redirected Profile Data").exists(),
            "reparse alias created mutable state inside immutable extracted ZIP")
    junction.rmdir()
    require(not junction.exists(), "test junction was not unlinked")
    require(not user_root.exists(),
            "junction refusal unexpectedly initialized genuine user data")

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

    # The exact extracted .cmd launcher must ALSO complete a first-run
    # identity transition without ANY synthetic --script CLI argument. Only
    # the native Modern root's explicitly test-gated SDL key events drive
    # this first process to Create -> Quit. The launcher itself must detect
    # the newly durable selector and relaunch the SAME PE exactly once.
    first_user = output / "First Modern Racer Through CMD With Spaces"
    first_env = {
        **env,
        "UR_RECOMP_USER_DATA_ROOT": str(first_user),
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "4",
        "UR_BALDOSA_LAUNCHER_RESTART_SMOKE": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
    }
    first_launch = invoke_launcher(launcher, first_env, [], timeout)
    first_log = first_launch.stdout + "\n" + first_launch.stderr
    (output / "first-racer-autorelaunch.log").write_text(
        first_log, encoding="utf-8")
    require(first_launch.returncode == 0,
            "Actual no-argument extracted launcher failed first-racer "
            f"handoff: rc={first_launch.returncode} tail={first_log[-2000:]}")
    verify_first_user_cmd_relaunch_log(first_log)
    for artifact in (
        first_user / "host-state-v1.txt",
        first_user / "profiles-v1.txt",
        first_user / "saves/profile-mike/host-profile.txt",
        first_user / "saves/profile-mike/save.srm",
    ):
        require(artifact.is_file() and not artifact.is_symlink(),
                "No-args launcher did not publish canonical first-racer data")
    require((first_user / "saves/profile-mike/save.srm").stat().st_size == 8192,
            "Relaunched first racer lost canonical 8192-byte saved SRAM")
    require(not list(first_user.rglob("*.urrun")),
            "First-run launcher smoke minted a synthetic completed race")
    require(not (installed / "saves").exists(),
            "First-run native CMD wrote mutable SRAM into ROM-free package")
    require_archive_unchanged(archive, approved_archive_sha256)

    # Actual CMD forwarding: a malformed Modern selector is refused by the
    # native after_config BEFORE gameplay. The batch file must preserve the
    # original exit 7, explain the refusal, and never create/overwrite SRAM.
    original_sram = save.read_bytes()
    selector = user_root / "host-state-v1.txt"
    if selector.exists():
        raise ValueError("Unexpected host selector in anonymous launcher fixture")
    selector.write_text("corrupt selected Modern profile fixture\n", encoding="utf-8")
    rejected = invoke_launcher(launcher, env, args, timeout)
    rejected_log = rejected.stdout + "\n" + rejected.stderr
    (output / "profile-rejected-launch.log").write_text(
        rejected_log, encoding="utf-8")
    require(
        rejected.returncode == 7 and
        rejected.stderr.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED") == 1 and
        "UR_BALDOSA_NATIVE_PROFILE REJECTED reason=host_state_invalid" in
        rejected_log,
        f"actual CMD entrypoint lost native profile refusal: "
        f"rc={rejected.returncode} tail={rejected_log[-1800:]}")
    require(save.read_bytes() == original_sram and
            selector.read_text(encoding="utf-8") ==
                "corrupt selected Modern profile fixture\n" and
            not list(user_root.rglob("*.urrun")),
            "Rejected packaged launch mutated previously saved data")

    # The ROM is never retained in evidence. Prove the *source archive*
    # is byte-for-byte unchanged from before extraction and all game launches.
    installed_rom.unlink()
    require_archive_unchanged(archive, approved_archive_sha256)
    report = {
        "verified_rom_used_temporarily": True,
        "rom_not_in_archive": True,
        "missing_rom_rejected_before_user_data": True,
        "wrong_rom_rejected_before_user_data": True,
        "package_local_and_relative_root_rejected": True,
        "external_junction_to_package_rejected": True,
        "real_extracted_launcher_accepted": True,
        "no_argument_first_racer_cmd_one_shot_restart_accepted": True,
        "fresh_named_game_after_actual_cmd_restart": True,
        "exact_native_profile_refusal_code_and_guidance": True,
        "rejected_profile_save_unchanged": True,
        "native_root_drawn": True,
        "canonical_8192_byte_save_outside_package": True,
        "published_zip_unchanged": True,
        "archive_sha256": approved_archive_sha256,
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
