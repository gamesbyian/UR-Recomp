#!/usr/bin/env python3
"""Actual native Windows P1 Quick Practice -> original Dragster source course.

The shipping Baldosa root handles P1 semantic Down/A/A. The stock guest then
consumes ONLY existing product-queued menu masks under QuickPracticeLaunch.
A source decoded-course identity and genuine in-race GO must authorize the
1P handoff; synthetic test input never writes guest memory or creates results.

Not physical gamepad acceptance, full 45-course eligibility or release credit.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from baldosa_native_first_racer_probe import (
    run_game, verify_boot_sram, verify_creation)
from baldosa_windows_native_pause_route import USA_SHA256, sha256


def require_native_practice_source(log: str) -> None:
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT practice_gamepad=DOWN",
        "UR_BALDOSA_MODERN_ROOT practice_opened=1 available=1 "
        "course=0 source_menu_required=1",
        "UR_BALDOSA_MODERN_ROOT practice_gamepad=A",
        "UR_BALDOSA_MODERN_ROOT practice_requested=1 course=0 "
        "name=DRAGSTER source_route=stock",
        "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=0 "
        "original_course=1 race=1 source_identity=verified",
    )
    for part in stages:
        if part not in log:
            raise ValueError("Missing native original course or controller stage: " + part)
    first = log.index(stages[2])
    opened = log.index(stages[3])
    first_a = log.index(stages[4])
    requested = log.index(stages[5])
    admitted = log.index(stages[6])
    if not first < opened < first_a < requested < admitted:
        raise ValueError("Practice source stages were reordered")
    if log.count("UR_BALDOSA_MODERN_ROOT practice_gamepad=") != 3 or (
            log.count("UR_BALDOSA_MODERN_ROOT practice_gamepad=A") != 2 or
            log.count(stages[6]) != 1):
        raise ValueError("Practice did not use exact real native P1 button edges")
    if any(part in log for part in (
        "UR_BALDOSA_MODERN_ROOT practice_rejected=",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=",
        "UR_BALDOSA_NATIVE_RESULT observed=1",
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=",
    )):
        raise ValueError("Practice route bypassed a source gate or forged Records")


PRACTICE_STAY_SCRIPT = (
    "turbo on\n"
    "until16 0053 == F60C\n"
    "wait 900\n"
    "until16 0053 == 8610\n"
    "until 0E1F != 00\n"
    "wait 200000\n"
    "quit\n")


def run_game_hard_killed(exe: Path, rom: Path, user: Path, work: Path,
                         *, video: str, timeout: int) -> str:
    """Start the real Practice route and TerminateProcess it once the source
    Dragster GO ticker is live, so no normal shutdown (and thus no restore of
    the stock SRAM snapshot or native SRAM writer) can run."""
    work.mkdir(parents=True, exist_ok=False)
    (work / "stock-route.txt").write_text(PRACTICE_STAY_SCRIPT, encoding="ascii")
    ini = work / "config.ini"
    ini.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(user),
           "UR_EXECUTION_MODE": "modern",
           "UR_BALDOSA_MODERN_ROOT": "1",
           "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "11",
           "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
           "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
           "UR_BALDOSA_MODERN_INPUT": "1",
           "UR_BALDOSA_PAUSE_SMOKE": "0",
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    log_path = work / "log.txt"
    deadline = time.monotonic() + timeout
    reached = False
    killed_live = False
    with open(log_path, "wb") as sink:
        proc = subprocess.Popen(
            [str(exe), "--no-launcher", "--config", str(ini),
             "--script", str(work / "stock-route.txt"), str(rom)],
            cwd=work, env=env, stdout=sink, stderr=subprocess.STDOUT)
        try:
            while time.monotonic() < deadline and proc.poll() is None:
                time.sleep(0.5)
                text = log_path.read_bytes().decode("utf-8", "replace")
                if "until 00E1F ok" in text:
                    reached = True
                    break
        finally:
            # Fail closed: only a child demonstrably alive at this instant is
            # killed; one that already exited or crashed proves nothing.
            if reached and proc.poll() is None:
                proc.kill()
                killed_live = True
            elif proc.poll() is None:
                proc.kill()
            proc.wait(timeout=30)
    log = log_path.read_bytes().decode("utf-8", "replace")
    # Exit receipt is written before any verdict so a failing route keeps it.
    (work / "kill-receipt.json").write_text(json.dumps({
        "script_token_seen": reached,
        "killed_while_alive": killed_live,
        "kill_method": "subprocess.Popen.kill (TerminateProcess on Windows)",
        "process_returncode": proc.returncode,
        "script_quit_or_normal_shutdown": "practice_sram_restored=1" in log,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not reached:
        raise RuntimeError("Practice never reached live source GO before kill: "
                           + log[-1800:])
    if not killed_live:
        raise RuntimeError("Practice process was no longer live at the kill "
                           "point (exited/crashed after GO): " + log[-1800:])
    # TerminateProcess/SIGKILL always yield a non-zero, non-clean status; a
    # script `quit` or normal shutdown would have returned 0.
    if proc.returncode in (0, None):
        raise RuntimeError("Killed Practice process reported a clean exit")
    if "script f=" in log and " quit" in log.split("until 00E1F ok", 1)[-1]:
        raise RuntimeError("Practice reached script quit/normal shutdown")
    return log


def snapshot(user: Path, names) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for name in names:
        path = user / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Named authority file missing/redirected: " + name)
        out[name] = path.read_bytes()
    return out


def record_boundary(receipts: list, receipt_path: Path, stage: str,
                    user: Path, reference: dict[str, bytes],
                    reference_label: str) -> list[str]:
    """Record SHA-256 and (for the small text typed profile) a bounded line
    diff of every authority file against a reference at one boundary. Written
    immediately so a failing route retains the localizing receipt."""
    now = snapshot(user, reference)
    changed = [n for n in reference if now[n] != reference[n]]
    entry = {"stage": stage, "compared_to": reference_label,
             "changed": changed,
             "sha256": {n: hashlib.sha256(b).hexdigest()
                        for n, b in now.items()},
             "reference_sha256": {n: hashlib.sha256(b).hexdigest()
                                  for n, b in reference.items()}}
    for n in changed:
        if n.endswith("host-profile.txt"):
            diff = list(difflib.unified_diff(
                reference[n].decode("utf-8", "replace").splitlines(),
                now[n].decode("utf-8", "replace").splitlines(),
                "reference", "now", lineterm="", n=0))
            entry["typed_profile_diff"] = diff[:40]
    receipts.append(entry)
    receipt_path.write_text(json.dumps(receipts, indent=2, sort_keys=True)
                            + "\n", encoding="utf-8")
    return changed


def run(exe: Path, rom: Path, out: Path,
        *, timeout: int, video: str) -> dict[str, object]:
    for path in (exe, rom):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing/redirected actual native Practice runner")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Practice guest must be pinned USA retail ROM")
    out.mkdir(parents=True, exist_ok=False)
    user = out / "Fresh Practice Source Guest"
    user.mkdir()
    # Original stock 1P tour/racer/track/Now Playing inputs are intentionally
    # ABSENT. The existing Modern product route must supply them after the
    # two user-confirmed P1 modal A edges and source menu observations.
    log = run_game(
        exe, rom, user, out / "game1_practice_stock_dragster", "11",
        "turbo on\n"
        "until16 0053 == F60C\n"
        "wait 900\n"
        "until16 0053 == 8610\n"
        "until 0E1F != 00\n"
        "dump source_practice_go\n"
        "quit\n",
        video, timeout)
    try:
        require_native_practice_source(log)
    except ValueError as exc:
        # The genuine Win32 test saves the complete log on disk; expose only
        # bounded source-stage tags in CI, never ROM bytes or user paths.
        tags = [line.strip() for line in log.splitlines()
                if line.startswith("UR_BALDOSA_MODERN_ROOT practice_") or
                line.startswith("UR_BALDOSA_NATIVE_PROFILE DEFAULT")]
        raise ValueError(str(exc) + " | source practice trace: " +
                         " ; ".join(tags[-22:])) from exc
    if "UR_BALDOSA_MODERN_ROOT practice_sram_sandbox=1 bytes=8192 " not in log or (
        "UR_BALDOSA_MODERN_ROOT practice_sram_restored=1 bytes=8192 " not in log):
        raise ValueError("Anonymous Practice did not own and restore isolated stock SRAM")

    # Separate actual named profile verifies the high-risk boundary: first
    # native game uses the real P1 controller handler to create Mike, second
    # game starts source Dragster Practice, and shutdown must leave the
    # canonical stock save, typed mirror, catalog and selector byte-identical.
    named_user = out / "Named P1 Practice SRAM Integrity"
    named_user.mkdir()
    created = run_game(
        exe, rom, named_user, out / "named_p1_creation", "8",
        "turbo on\nwait 900\nquit\n", video, timeout)
    verify_creation(created, preset=0)
    from baldosa_native_second_racer_probe import require_native_created_p1_pad_handler
    require_native_created_p1_pad_handler(created, "8")
    named_files = {
        name: (named_user / name).read_bytes()
        for name in (
            "host-state-v1.txt", "profiles-v1.txt",
            "saves/profile-mike/host-profile.txt",
            "saves/profile-mike/save.srm",
        )
    }
    if len(named_files["saves/profile-mike/save.srm"]) != 8192:
        raise ValueError("Original named source SRAM is not 8 KiB")
    # Compare exact actual guest-created profile bytes, with no fixture
    # seeding or data repair; the P1 files must survive a fresh practice game.
    named_log = run_game(
        exe, rom, named_user, out / "named_p1_practice_guest", "11",
        "turbo on\n"
        "until16 0053 == F60C\n"
        "wait 900\n"
        "until16 0053 == 8610\n"
        "until 0E1F != 00\n"
        "dump named_practice_go\n"
        "quit\n",
        video, timeout)
    for required in (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
        "UR_BALDOSA_MODERN_ROOT practice_sram_sandbox=1 bytes=8192 ",
        "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=0 ",
        "UR_BALDOSA_MODERN_ROOT practice_sram_restored=1 bytes=8192 ",
    ):
        if required not in named_log:
            raise ValueError("Named Practice isolation/source stage absent: " + required)
    for name, before in named_files.items():
        p = named_user / name
        if p.is_symlink() or not p.is_file() or p.read_bytes() != before:
            raise ValueError("Practice overwrote authoritative named data: " + name)
    archive = named_user / "runs" / "mike"
    if archive.exists() and (
            archive.is_symlink() or list(archive.rglob("*.urrun"))):
        raise ValueError("Named Practice minted an earned completed run")
    scratch = named_user / "practice-session"
    if scratch.is_symlink() or not scratch.is_dir():
        raise ValueError("Native Practice did not bind disposable save root")
    # Crash lifecycle: hard-kill the process while the Practice SRAM sandbox
    # is live (no restore, no native save). Authoritative named bytes must be
    # untouched, the next ordinary boot must load the exact same stock SRAM,
    # and a stale practice-session directory must not block a new Practice.
    killed = run_game_hard_killed(
        exe, rom, named_user, out / "named_p1_practice_hard_killed",
        video=video, timeout=timeout)
    for required in (
        "UR_BALDOSA_MODERN_ROOT practice_sram_sandbox=1 bytes=8192 ",
        "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=0 ",
    ):
        if required not in killed:
            raise ValueError("Killed Practice never owned the sandbox: " + required)
    if "practice_sram_restored=1" in killed:
        raise ValueError("Hard-kill test unexpectedly shut down normally")
    original_srm = named_files["saves/profile-mike/save.srm"]
    receipts: list = []
    receipt_path = out / "boundary-receipts.json"
    changed = record_boundary(receipts, receipt_path, "after_hard_kill",
                              named_user, named_files, "pre_practice_original")
    if changed:
        raise ValueError("Hard-killed Practice altered named data: " +
                         ", ".join(changed))
    if archive.exists() and list(archive.rglob("*.urrun")):
        raise ValueError("Hard-killed Practice minted an earned run")
    rebooted = run_game(
        exe, rom, named_user, out / "named_p1_boot_after_practice_kill", "0",
        "turbo on\nwait 600\nquit\n", video, timeout)
    verify_boot_sram(rebooted, named_files["saves/profile-mike/save.srm"],
                     profile="mike")
    # Smoke "0" injects no root input: this boot must NOT enter a career
    # game (which would legitimately commit changed SRAM and invalidate the
    # baseline). Fail closed if the guest played anything.
    for forbidden in ("stock_requested", "stock_entered",
                      "UR_BALDOSA_NATIVE_RUN CAPTURED=1"):
        if forbidden in rebooted:
            raise ValueError("Post-kill witness boot entered play: " + forbidden)
    # An ordinary Mike boot enters stock play and ends in the normal native
    # shutdown/typed checkpoint. Record exactly what it changed (typed
    # profile diff included) instead of assuming. Raw SRAM, selector and
    # catalog must always still equal the originals; any typed-profile
    # change here is a receipt-visible ordinary-boot effect, and the
    # post-kill Practice below is judged against these bytes strictly.
    changed = record_boundary(receipts, receipt_path, "after_ordinary_reboot",
                              named_user, named_files, "pre_practice_original")
    stable = {"host-state-v1.txt", "profiles-v1.txt",
              "saves/profile-mike/save.srm"}
    if stable & set(changed):
        raise ValueError("Ordinary boot after kill changed " +
                         ", ".join(sorted(stable & set(changed))))
    post_reboot = snapshot(named_user, named_files)
    retried = run_game(
        exe, rom, named_user, out / "named_p1_practice_after_kill", "11",
        "turbo on\n"
        "until16 0053 == F60C\n"
        "wait 900\n"
        "until16 0053 == 8610\n"
        "until 0E1F != 00\n"
        "dump practice_after_kill_go\n"
        "quit\n",
        video, timeout)
    # The re-admitted Practice must itself boot the exact original career SRAM.
    verify_boot_sram(retried, original_srm, profile="mike")
    for required in (
        "UR_BALDOSA_MODERN_ROOT practice_sram_sandbox=1 bytes=8192 ",
        "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=0 ",
        "UR_BALDOSA_MODERN_ROOT practice_sram_restored=1 bytes=8192 ",
    ):
        if required not in retried:
            raise ValueError("Practice after hard kill failed: " + required)
    record_boundary(receipts, receipt_path,
                    "after_practice_vs_original", named_user, named_files,
                    "pre_practice_original")
    changed = record_boundary(receipts, receipt_path,
                              "after_practice_after_kill", named_user,
                              post_reboot, "post_ordinary_reboot")
    if changed:
        raise ValueError("Practice after kill altered named data: " +
                         ", ".join(changed))
    return {
        "hard_killed_practice_kill_receipt": json.loads(
            (out / "named_p1_practice_hard_killed" /
             "kill-receipt.json").read_text(encoding="utf-8")),
        "boundary_receipts": receipts,
        "hard_killed_practice_named_bytes_unchanged": True,
        "boot_after_practice_kill_exact_sram": True,
        "practice_after_kill_admitted_and_restored": True,
        "scope": "one-real-native-windows-p1-practice-first-course",
        "source_course": "Dragster",
        "source_course_index": 1,
        "p1_gamepad_handler_presses": ["DOWN", "A", "A"],
        "original_stock_menu_inputs_from_source_product_route": True,
        "original_decoded_course_observed_in_race": True,
        "source_go_timer_observed": True,
        "named_active_p1_authoritative_bytes_unchanged": True,
        "native_sram_restored_before_save": True,
        "practice_results_not_published": True,
        "other_44_native_courses_admitted": False,
        "physical_gamepad_certified": False,
        "full_event_parity_or_release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=220)
    args = parser.parse_args()
    report = run(args.exe.resolve(), args.rom.resolve(), args.out.resolve(),
                 timeout=args.timeout, video=args.video)
    (args.out.resolve() / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: actual Windows native P1 Practice source Dragster GO; "
          "45-course availability and physical hardware remain unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
