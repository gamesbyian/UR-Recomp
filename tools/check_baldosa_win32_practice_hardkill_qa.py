#!/usr/bin/env python3
"""Read-only, SHA-pinned independent Win32 Practice hard-kill source audit.

The archived process/kill source can establish a real TerminateProcess and
source-consistent reboot, never independent raw named-profile byte equality.
An intervening ordinary career game makes a pre-game comparison ambiguous.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

FILES = (
    "game1_practice_stock_dragster/log.txt",
    "named_p1_creation/log.txt",
    "named_p1_practice_guest/log.txt",
    "named_p1_practice_hard_killed/log.txt",
    "named_p1_practice_hard_killed/kill-receipt.json",
    "named_p1_boot_after_practice_kill/log.txt",
    "named_p1_practice_after_kill/log.txt",
)
IDLE = ("ordinary_idle_boot_1_normalizes/log.txt",
        "ordinary_idle_boot_2_control/log.txt")
EXTRAS = {"report.json", "boundary-receipts.json", *IDLE}
SHA = re.compile(r"[a-f0-9]{64}\Z")
BOOT = re.compile(r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=([0-9a-f]{8})\r?$")
ROOT = re.compile(r"(?m)^\[Launcher\] Config/saves anchored to '([^'\r\n]+)'\.\r?$")
GO = re.compile(r"(?m)^script f=\d+ until 00E1F ok after \d+ frames\r?$")
SOURCEMARK = "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=0 original_course=1 race=1 source_identity=verified"
SANDBOX = "UR_BALDOSA_MODERN_ROOT practice_sram_sandbox=1 bytes=8192 root=practice-session publication=disabled"
RESTORE = "UR_BALDOSA_MODERN_ROOT practice_sram_restored=1 bytes=8192 original_root=1"
FORGED_AWARD = ("UR_BALDOSA_NATIVE_RESULT observed=1",
                "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
                "UR_BALDOSA_NATIVE_RUN CAPTURED=1")


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError("independent Windows Practice QA: " + detail)


def sole(pattern: re.Pattern[str], value: str, description: str) -> str:
    matches = pattern.findall(value)
    require(len(matches) == 1, "missing/duplicate " + description)
    return matches[0]


def audit_archive(path: Path, *, expected_sha256: str) -> dict:
    require(bool(SHA.fullmatch(expected_sha256)), "missing expected full Actions SHA256")
    require(path.is_file() and not path.is_symlink() and
            0 < path.stat().st_size <= 256 * 1024, "unsafe/missing archive")
    require(hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha256,
            "archive SHA256 mismatch")
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        require(len(names) == len(set(names)) and
                set(FILES) <= set(names) <= set(FILES) | EXTRAS,
                "missing, duplicated or unexpected artifact files")
        files = {}
        for name in names:
            info = z.getinfo(name)
            mode = (info.external_attr >> 16) & 0o170000
            require(not info.is_dir() and mode != 0o120000 and
                    0 < info.file_size <= 48 * 1024, "unsafe file " + name)
            files[name] = z.read(name)
            require(len(files[name]) == info.file_size, "incomplete file " + name)
    # Two optional actual native idle-control logs must arrive together.
    # One missing log cannot prove source chronology or no-Play behavior.
    idle_present = any(name in files for name in IDLE)
    require(not idle_present or all(name in files for name in IDLE),
            "incomplete ordinary idle-control source pair")
    logs = {name: files[name].decode("utf-8", "strict")
            for name in (*FILES, *IDLE) if name.endswith("log.txt") and name in files}
    for name, log in logs.items():
        require("[Gamepad] SDL reports 0 joystick(s)" in log and
                not any(marker in log for marker in FORGED_AWARD),
                "not semantic-input-only or career award emitted " + name)
    anonymous = logs[FILES[0]]
    require(SANDBOX in anonymous and SOURCEMARK in anonymous and
            RESTORE in anonymous and bool(GO.search(anonymous)),
            "anonymous source Practice not proven")
    create = logs[FILES[1]]
    require("UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1" in create and
            "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike activation=next_process" in create,
            "named rider not native-created")
    first, killed, reboot, retried = (logs[FILES[i]] for i in (2, 3, 5, 6))
    for name, log in ((FILES[2], first), (FILES[3], killed), (FILES[6], retried)):
        require("UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike" in log and
                SANDBOX in log and SOURCEMARK in log and bool(GO.search(log)),
                "missing source-confirmed named Practice " + name)
    require(RESTORE in first and RESTORE in retried,
            "normal Practice exit lacks SRAM restoration")
    require(RESTORE not in killed and
            not re.search(r"(?m)^script f=\d+ quit\r?$", killed),
            "hard-killed source had normal shutdown")
    named_roots = [sole(ROOT, logs[x], x + " root")
                   for x in (*FILES[1:], *IDLE) if x.endswith("log.txt") and x in logs]
    require(len(set(named_roots)) == 1, "different named user roots in one journey")
    receipt = json.loads(files[FILES[4]])
    require(type(receipt) is dict and set(receipt) == {
            "kill_method", "killed_while_alive", "process_returncode",
            "script_quit_or_normal_shutdown", "script_token_seen"} and
            receipt["kill_method"] == "subprocess.Popen.kill (TerminateProcess on Windows)" and
            receipt["killed_while_alive"] is True and
            receipt["script_token_seen"] is True and
            receipt["script_quit_or_normal_shutdown"] is False and
            type(receipt["process_returncode"]) is int and
            receipt["process_returncode"] != 0, "delivered live Windows kill not proven")
    a = sole(BOOT, first, "original source BOOT_SRAM")
    k = sole(BOOT, killed, "killed source BOOT_SRAM")
    b = sole(BOOT, reboot, "fresh ordinary source BOOT_SRAM")
    c = sole(BOOT, retried, "retried Practice source BOOT_SRAM")
    require(a == k == b, "postkill fresh boot did not read original MIKE source SRAM")
    idle_control_fvn = None
    if idle_present:
        expected_idle_tokens = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
            "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=",
        )
        for name in IDLE:
            idle_log = logs[name]
            require(all(token in idle_log for token in expected_idle_tokens) and
                    "stock_requested" not in idle_log and
                    "stock_entered" not in idle_log and
                    RESTORE not in idle_log,
                    "idle-control source entered stock play or lacked named closure")
            require(len(BOOT.findall(idle_log)) == 1 and
                    re.search(r"(?m)^script f=\d+ quit\r?$", idle_log) is not None,
                    "idle-control process boot and quit not source-verified")
        idle_control_fvn = sole(BOOT, logs[IDLE[1]], "second idle control SRAM")
        require(idle_control_fvn == a,
                "second idle-control source SRAM disagrees with stable Practice baseline")
    require("UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike" in reboot,
            "fresh boot did not load named player")
    require("UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=unchanged" in first,
            "normal prekill Practice altered typed profile")
    career = "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c" in reboot
    committed = "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=committed" in reboot
    if career and committed and c != b:
        classification = "intervening_normal_career_game_changed_SRAM_before_Practice"
    elif c == b and not career:
        classification = "readmitted_Practice_boots_same_source_SRAM"
    else:
        classification = "postreboot_storage_change_cause_not_independently_resolved"
    boundary = None
    if "boundary-receipts.json" in files:
        boundary = json.loads(files["boundary-receipts.json"])
        require(type(boundary) is list and len(boundary) >= 1,
                "malformed stage hash receipt")
        if idle_present:
            labels = [row.get("stage") for row in boundary if isinstance(row, dict)]
            require(len(labels) == len(boundary) and
                    labels[:2] == ["ordinary_idle_boot_1_normalizes",
                                   "ordinary_idle_boot_2_control"] and
                    "after_hard_kill" in labels,
                    "missing ordered named idle and kill boundary receipts")
            for name in ("ordinary_idle_boot_2_control", "after_hard_kill"):
                row = boundary[labels.index(name)]
                require(row.get("changed") == [] and
                        isinstance(row.get("sha256"), dict) and
                        isinstance(row.get("reference_sha256"), dict),
                        "idempotent idle control or killed named bytes not source-stable")
    elif idle_present:
        raise ValueError("independent Windows Practice QA: missing idle-control byte receipts")
    if "report.json" in files:
        report = json.loads(files["report.json"])
        require(type(report) is dict and report.get("physical_gamepad_certified") is False
                and report.get("full_event_parity_or_release_gate_credit") == 0,
                "forged release claims in source report")
    return {
        "schema": "ur-independent-win32-practice-hardkill-audit-v1",
        "source_zip_sha256": expected_sha256,
        "source_member_count": len(files),
        "actual_live_Windows_TerminateProcess_logged": True,
        "new_named_P1_original_source_Practice_GO": True,
        "postkill_fresh_process_source_FNV_equal": True,
        "original_boot_sram_fnv": a,
        "fresh_boot_sram_fnv": b,
        "readmitted_practice_boot_sram_fnv": c,
        "readmitted_Practice_original_source_GO_and_restore_logged": True,
        "intervening_ordinary_career_play": career,
        "intervening_ordinary_career_save_committed": committed,
        "stage_hash_receipts_archived": boundary is not None,
        "both_idle_control_source_logs_retained": idle_present,
        "idle_control_source_boot_fingerprint": idle_control_fvn,
        "idle_control_producer_hashes_show_idempotence": idle_present and boundary is not None,
        "source_classification": classification,
        "independently_archived_actual_prepost_8192_byte_SRAM": False,
        "independently_proven_full_named_byte_immutability": False,
        "physical_gamepads": False,
        "original_USA_strict_complete_event_pass": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip", type=Path, required=True)
    p.add_argument("--expected-source-sha256", required=True)
    p.add_argument("--out-json", type=Path)
    args = p.parse_args()
    result = audit_archive(args.source_zip, expected_sha256=args.expected_source_sha256)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out_json:
        args.out_json.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
