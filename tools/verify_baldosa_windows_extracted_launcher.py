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
import re
from pathlib import Path
import subprocess
import sys
import zipfile

from assemble_baldosa_windows_candidate import (
    EXE, LAUNCHER, MANIFEST, PREFIX, README, ROM, USA_SHA256,
)
from audit_baldosa_romless_candidate import inspect as audit_candidate_archive

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for data in iter(lambda: fp.read(1 << 20), b""):
            h.update(data)
    return h.hexdigest()

LOG_RETAIN_LIMIT = 1 << 20  # bytes of each retained raw process transcript


def bounded_log(text: str) -> str:
    """Retain at most ~1 MiB of a raw transcript: the head and the tail with an
    explicit marker, so chronology survives and the artifact stays bounded."""
    raw = text.encode("utf-8", "replace")
    if len(raw) <= LOG_RETAIN_LIMIT:
        return text
    half = LOG_RETAIN_LIMIT // 2
    head = raw[:half].decode("utf-8", "replace")
    tail = raw[-half:].decode("utf-8", "replace")
    return (head + f"\n[... {len(raw) - 2 * half} bytes elided by the "
            "verifier's bounded retention ...]\n" + tail)



# Retain process evidence for the two subtle rooted-but-not-fully-qualified
# negative CMD inputs. The actual launcher, ROM and game are unchanged.
# The CI runner already executed these subprocesses; this only preserves
# bounded decoded stdout/stderr and their observed exit codes.
ROOTED_RELATIVE_NEGATIVE_CASES = {
    "C:qa-drive-relative-root": ("drive-relative-root-refusal.log", "drive_relative"),
    "\\qa-current-drive-root-relative": (
        "current-drive-root-refusal.log", "current_drive_root_relative"),
}


def retain_rooted_relative_rejection(output: Path, supplied_root: str,
                                     result: subprocess.CompletedProcess[str]) -> dict:
    log_name, key = ROOTED_RELATIVE_NEGATIVE_CASES[supplied_root]
    transcript = ("STDOUT (actual cmd.exe subprocess):\n" + result.stdout +
                  "\nSTDERR (actual cmd.exe subprocess):\n" + result.stderr)
    (output / log_name).write_bytes(bounded_log(transcript).encode("utf-8"))
    return {
        "case": key,
        "supplied_root": supplied_root,
        "process_returncode": result.returncode,
        "expected_exit_code": 3,
        "root_rejection_marker_seen": "UR-BALDOSA-STARTUP-SAVE-ROOT" in result.stderr,
        "stdout_utf8_sha256": hashlib.sha256(
            result.stdout.encode("utf-8", "replace")).hexdigest(),
        "stderr_utf8_sha256": hashlib.sha256(
            result.stderr.encode("utf-8", "replace")).hexdigest(),
        "retained_subprocess_transcript": log_name,
    }


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
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
        "root=saves/profile-mike",
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike ",
    )
    positions = []
    for token in mandatory:
        require(log.count(token) == 1,
                "No unique actual CMD first-racer stage: " + token)
        positions.append(log.index(token))
    # Native AOT diagnostics are emitted to stderr while the .cmd launcher
    # restart echo is printed to stdout. subprocess captures those streams
    # separately and then concatenates them for the retained log, so stdout
    # position has NO cross-process chronological significance. Require the
    # exact restart echo once, and require ordered *native* source receipts.
    require(log.count(
        "UR-BALDOSA-FIRST-RACER: Restarting with newly created racer.") == 1,
        "Actual native CMD never issued exactly one launcher restart")
    require(positions == sorted(positions),
            "Native first-user game opened selected profile before creation")
    require(log.count("UR_BALDOSA_MODERN_ROOT opened=1") == 2,
            "CMD must launch exactly two original native game processes")
    # The no-arguments launcher now proves actual native P1 gamepad-handler
    # edges for create and both quits, not merely SDL keyboard equivalents.
    # The first guest is anonymous; the second is source-booted named Mike.
    observed = re.findall(
        r"(?m)^UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad "
        r"profile=(anonymous|mike) button=(X|A|B)\r?$", log)
    expected = [
        ("anonymous", "X"), ("anonymous", "A"),
        ("anonymous", "B"), ("anonymous", "B"),
        ("anonymous", "A"), ("mike", "B"), ("mike", "A"),
    ]
    require(observed == expected and
            log.count("UR_BALDOSA_MODERN_ROOT noargs_launcher_gamepad ") == 7,
            "No-args CMD did not execute unique ordered native P1 gamepad "
            "create, quit and cold-restart quit actions")



def verify_no_input_modern_paint(log: str) -> str:
    """Require exactly one actual painted host surface on a cold CMD launch.

    Pre-title builds paint the five-destination root immediately. The
    integrated Modern title intentionally waits for a *new* physical confirm
    edge before painting that root. Neither route may silently pass with no
    paint, two surfaces, or an arbitrary/partial title diagnostic. A separate
    controller-driven test must prove title -> root on title-enabled builds.
    """
    opened = re.findall(r"(?m)^UR_BALDOSA_MODERN_ROOT opened=1\r?$", log)
    # Count *all* anchored Modern paint attempts, not only valid receipts.
    # Otherwise one valid root/title plus a malformed second surface could
    # silently pass as an unambiguous cold boot.
    paint_attempts = re.findall(
        r"(?m)^UR_BALDOSA_MODERN_(?:ROOT|TITLE) painted[^\r\n]*\r?$", log)
    require(len(opened) == 1,
            "actual CMD did not open exactly one native Modern host")
    require(len(paint_attempts) == 1,
            "no-input CMD must emit exactly one Modern root or title paint receipt")
    attempt = paint_attempts[0].removesuffix("\r")
    if re.fullmatch(
        r"UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared",
        attempt,
    ):
        return "root"
    if re.fullmatch(
        r"UR_BALDOSA_MODERN_TITLE painted=1 raster=(256|342)x224 host=modern",
        attempt,
    ):
        return "title"
    raise ValueError("no-input CMD emitted a malformed Modern paint receipt")


def run(archive: Path, personal_rom: Path, output: Path, timeout: int,
        *, expected_revision: str | None = None,
        save_fault_fixture: Path | None = None,
        save_fault_seed: Path | None = None,
        save_fault_script: Path | None = None) -> dict:
    if os.name != "nt":
        raise ValueError("actual Windows CMD executable is required")
    if output.exists():
        raise ValueError("do not reuse/erase an existing test root")
    require(digest(personal_rom) == USA_SHA256,
            "must test with the exact pinned original USA retail ROM")
    require(archive.is_file(), "candidate archive absent")
    # Fail closed on the complete immutable ZIP before creating even the
    # disposable extraction root, let alone executing the native PE.
    audit = audit_candidate_archive(archive, expected_revision=expected_revision)
    approved_archive_sha256 = digest(archive)
    require(approved_archive_sha256 == audit["zip_sha256"],
            "candidate ZIP changed between manifest validation and extraction")
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
    for filename, key in ((EXE, "exe_sha256"),
                          (LAUNCHER, "launcher_sha256"),
                          (README, "readme_sha256")):
        require(digest(installed / filename) == audit[key],
                "extracted immutable member differs from validated source ZIP")
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
        # Scripted refusals must return at once; the interactive hold that
        # keeps a double-clicked window readable is opted out here.
        "UR_BALDOSA_NO_HOLD": "1",
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
    # Rooted-but-not-fully-qualified Windows spellings (drive-relative and
    # current-drive-root-relative) are admitted by IsPathRooted and resolve
    # against process state; the launcher must refuse them with exit 3 before
    # any save, catalog or folder is created.
    drive_relative = "C:qa-drive-relative-root"
    root_relative = "\\qa-current-drive-root-relative"
    rooted_refusals = []
    for root in (str(installed / "Injected Save Root"), "relative-save-root",
                 drive_relative, root_relative):
        bad_env = {**env, "UR_RECOMP_USER_DATA_ROOT": root}
        bad = invoke_launcher(launcher, bad_env, args, timeout)
        if root in (drive_relative, root_relative):
            rooted_refusals.append(retain_rooted_relative_rejection(output, root, bad))
        require(bad.returncode != 0 and
                "UR-BALDOSA-STARTUP-SAVE-ROOT" in bad.stderr,
                "unsafe data root was accepted by actual CMD launcher")
        if root in (drive_relative, root_relative):
            require(bad.returncode == 3,
                    f"rooted-relative data root {root!r} did not exit 3: "
                    f"rc={bad.returncode}")
    for leaked in (installed / "qa-drive-relative-root",
                   Path(installed.anchor) / "qa-drive-relative-root",
                   Path(installed.anchor) / "qa-current-drive-root-relative",
                   Path.cwd() / "qa-drive-relative-root"):
        require(not leaked.exists(),
                f"rooted-relative data root created state at {leaked}")
    require(not (installed / "Injected Save Root").exists(),
            "package-local user state was created")
    require(not user_root.exists(), "invalid root created valid profile state")

    # These two source-bound refusals have already passed the existing exit-3
    # and no-mutable-root assertions. Keep their distinct process evidence
    # separate from the strict fixed-member native-pause QA-12 artifact.
    require(len(rooted_refusals) == 2 and
            all(x["process_returncode"] == 3 and x["root_rejection_marker_seen"]
                for x in rooted_refusals),
            "rooted-relative negative subprocess evidence incomplete")
    (output / "rooted-relative-rejections.json").write_text(
        json.dumps({
            "schema": "ur-win32-extracted-cmd-rooted-relative-negative/1",
            "source_revision": expected_revision,
            "candidate_zip_sha256": approved_archive_sha256,
            "embedded_exe_sha256": audit["exe_sha256"],
            "all_candidate_mutable_roots_absent": True,
            "release_gate_credit": 0,
            "independent_review_complete": False,
            "cases": rooted_refusals,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")

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
    (output / "valid-launch.log").write_text(
        bounded_log(log), encoding="utf-8")
    require(good.returncode == 0,
            f"extracted CMD launcher returned {good.returncode}: {log[-2500:]}")
    no_input_surface = verify_no_input_modern_paint(log)
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
    # test-gated P1 native gamepad semantic edges (never physical hardware) drive
    # this first process to Create -> Quit. The launcher itself must detect
    # the newly durable selector and relaunch the SAME PE exactly once.
    first_user = output / "First Modern Racer Through CMD With Spaces"
    first_env = {
        **env,
        "UR_RECOMP_USER_DATA_ROOT": str(first_user),
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "10",
        "UR_BALDOSA_LAUNCHER_RESTART_SMOKE": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
    }
    first_launch = invoke_launcher(launcher, first_env, [], timeout)
    first_log = first_launch.stdout + "\n" + first_launch.stderr
    (output / "first-racer-autorelaunch.log").write_text(
        bounded_log(first_log), encoding="utf-8")
    require(first_launch.returncode == 0,
            "Actual no-argument extracted launcher failed first-racer "
            f"handoff: rc={first_launch.returncode} tail={first_log[-2000:]}")
    try:
        verify_first_user_cmd_relaunch_log(first_log)
    except ValueError as exc:
        # Keep source-host diagnostics visible on a red Windows job even
        # if its optional evidence artifact is not retained.
        raise ValueError(
            "Actual no-args native CMD restart log was rejected: "
            f"{exc}; retained log tail={first_log[-2800:]!r}") from exc
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

    # One additional real-player package acceptance, separate from the
    # flat/independent QA02 archive. The same packaged PE that just passed
    # the immutable ROM and clean launcher checks must report a real
    # mid-save Win32 atomic-replacement failure as EXIT 8 to the CMD
    # launcher, not clean exit 0 or mistaken startup repair code 7.
    supplied = (save_fault_fixture, save_fault_seed, save_fault_script)
    require(all(x is None for x in supplied) or all(x is not None for x in supplied),
            "packaged native save-failure witness requires fixture, seed and script together")
    packaged_save_failure = None
    if all(x is not None for x in supplied):
        from baldosa_win32_live_postraw_sharing_denial import (
            run_native_win32_live_postraw_typed_denial,
        )
        require(all(x.is_file() for x in supplied),
                "packaged save-failure witness needs actual existing pinned inputs")
        witness_root = output / "Packaged Actual Source Save Failure"
        witness_root.mkdir()
        packaged_save_failure = run_native_win32_live_postraw_typed_denial(
            installed / EXE, installed_rom, save_fault_script,
            witness_root, save_fault_fixture, save_fault_seed,
            video="windows", timeout=timeout, packaged_launcher=launcher)
        require(
            packaged_save_failure["native_denied_process_return_code"] == 8 and
            packaged_save_failure["native_source_pe_sha256"] == audit["exe_sha256"] and
            packaged_save_failure["packaged_launcher_sha256"] == audit["launcher_sha256"] and
            packaged_save_failure["real_extracted_package_cmd_exercised"] and
            packaged_save_failure["packaged_cmd_save_failure_warning_verified"] and
            packaged_save_failure["source_cold_recovered_original_guest_SRAM"] and
            packaged_save_failure["second_original_source_boot_idempotent"],
            "actual extracted Windows CMD did not report original denied save")
        require_archive_unchanged(archive, approved_archive_sha256)
        require(digest(installed / EXE) == audit["exe_sha256"],
                "actual packaged failure test changed tested Windows PE")

    # Packaged Options through the exact CMD launcher, no --script argument:
    # real P1 semantic pad edges change Display/VSync/Volume and quit. State
    # must land under the user root (never in the immutable package), a
    # second launch must restore it, and a damaged options file must be
    # reported without stopping the game or being forced onto the host.
    options_user = output / "Packaged Options Through CMD With Spaces"
    options_env = {**env, "UR_RECOMP_USER_DATA_ROOT": str(options_user),
                   "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "12"}
    opt_first = invoke_launcher(launcher, options_env, [], timeout)
    opt_first_log = opt_first.stdout + "\n" + opt_first.stderr
    (output / "packaged-options-first.log").write_text(
        bounded_log(opt_first_log), encoding="utf-8")
    require(opt_first.returncode == 0,
            f"packaged Options launch failed: rc={opt_first.returncode} "
            f"tail={opt_first_log[-1800:]}")
    for token in (
            "options_boot row=DISPLAY display=WINDOWED vsync=ON volume=100 "
            "status=NONE help=0 load=missing",
            "options_adjusted row=DISPLAY display=BORDERLESS",
            "options_adjusted row=VSYNC display=BORDERLESS vsync=ADAPTIVE",
            "options_adjusted row=VOLUME display=BORDERLESS vsync=ADAPTIVE "
            "volume=90 status=SAVED"):
        require(token in opt_first_log,
                f"packaged Options journey missing stage: {token}")
    options_file = options_user / "options-v1.txt"
    require(options_file.is_file() and not options_file.is_symlink() and
            "display_mode=borderless" in options_file.read_text(
                encoding="utf-8") and
            not (options_user / "host-state-v1.txt").exists(),
            "packaged Options did not persist only options-v1.txt")
    require(not (installed / "options-v1.txt").exists() and
            not (installed / "config.ini").exists() and
            not (installed / "saves").exists(),
            "packaged Options leaked mutable state into the immutable package")
    opt_second = invoke_launcher(launcher, {
        **options_env, "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "14"}, [], timeout)
    opt_second_log = opt_second.stdout + "\n" + opt_second.stderr
    (output / "packaged-options-second.log").write_text(
        bounded_log(opt_second_log), encoding="utf-8")
    require(opt_second.returncode == 0 and
            "options_boot row=DISPLAY display=BORDERLESS vsync=ADAPTIVE "
            "volume=90 status=NONE help=0 load=loaded" in opt_second_log,
            "packaged relaunch did not restore saved Options before play")
    damaged_bytes = b"UR-HOST-STATE/6\nnot a valid options file\n"
    options_file.write_bytes(damaged_bytes)
    opt_third = invoke_launcher(launcher, {
        **options_env, "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "14"}, [], timeout)
    opt_third_log = opt_third.stdout + "\n" + opt_third.stderr
    (output / "packaged-options-damaged.log").write_text(
        bounded_log(opt_third_log), encoding="utf-8")
    require(opt_third.returncode == 0 and
            "options_boot" in opt_third_log and "load=damaged" in opt_third_log,
            "a damaged options file stopped or was hidden from the packaged game")
    require(options_file.read_bytes() == damaged_bytes,
            "merely booting rewrote or discarded the damaged options file")
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
        bounded_log(rejected_log), encoding="utf-8")
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
        "packaged_options_persist_outside_package": True,
        "packaged_damaged_options_reported_not_forced": True,
        "exact_native_profile_refusal_code_and_guidance": True,
        "packaged_live_original_save_failure_exit_8": packaged_save_failure is not None,
        "packaged_live_original_save_failure_source_witness": packaged_save_failure,
        "rejected_profile_save_unchanged": True,
        "native_root_drawn": no_input_surface == "root",
        "native_title_drawn": no_input_surface == "title",
        "no_input_modern_surface": no_input_surface,
        "canonical_8192_byte_save_outside_package": True,
        "published_zip_unchanged": True,
        "archive_sha256": approved_archive_sha256,
        "candidate_source_revision": audit["source_revision"],
        "candidate_executable_sha256": audit["exe_sha256"],
        "candidate_manifest_verified_before_extraction": True,
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
    ap.add_argument("--expected-revision", help="exact checked-out source commit")
    ap.add_argument("--save-fault-fixture", type=Path,
                    help="exact same-commit original native profile fixture")
    ap.add_argument("--save-fault-seed", type=Path,
                    help="actual original native 8192 SRAM, never manufactured")
    ap.add_argument("--save-fault-script", type=Path,
                    help="source-authenticated original frame-1952 race route")
    args = ap.parse_args()
    if args.timeout <= 0:
        raise ValueError("positive timeout required")
    print(json.dumps(run(args.zip.resolve(), args.rom.resolve(),
                         args.out.resolve(), args.timeout,
                         expected_revision=args.expected_revision,
                         save_fault_fixture=args.save_fault_fixture.resolve()
                             if args.save_fault_fixture else None,
                         save_fault_seed=args.save_fault_seed.resolve()
                             if args.save_fault_seed else None,
                         save_fault_script=args.save_fault_script.resolve()
                             if args.save_fault_script else None), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
