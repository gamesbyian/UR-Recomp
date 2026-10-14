#!/usr/bin/env python3
"""Read-only independent five-native-process existing-P1 selector QA.

The evidence is SDL scripted native Win32, not physical pad acceptance.
The saved selector/SRAM bytes were not uploaded; printed status isn't bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import zipfile

from check_baldosa_win32_first_racer_evidence import SOURCE
from check_baldosa_win32_second_racer_go_qa import (
    SECOND, ordered_exact_source_lines,
)

PREFIX = "UR Baldosa Win32 Pause Route/native_existing_p1_switch/"
FILES = (
    "report.json",
    "first_creates_mike/log.txt",
    "named_mike_adds_andrew/log.txt",
    "mike_switches_to_andrew_next_boot/log.txt",
    "andrew_switches_to_mike_next_boot/log.txt",
    "fresh_mike_reboot/log.txt",
)
ROOT = re.compile(r"(?m)^\[Launcher\] Config/saves anchored to '([^'\r\n]+)'\.\r?$")
BOOT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
    r"profile=(mike|andrew) bytes=8192 fnv=([a-fA-F0-9]{8})\r?$"
)
FORBID = (
    "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
    "UR_BALDOSA_NATIVE_RESULT observed=1",
    "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
)


def require(ok: bool, text: str) -> None:
    if not ok:
        raise ValueError("existing P1 Win32 source evidence: " + text)


def only(regex: re.Pattern, data: str, name: str) -> re.Match:
    matches = list(regex.finditer(data))
    require(len(matches) == 1, "missing or duplicated " + name)
    return matches[0]


def read_archive(path: Path) -> tuple[bytes, ...]:
    require(not path.is_symlink() and path.is_file() and
            0 < path.stat().st_size <= 8 * 1024 * 1024,
            "unsafe or missing bounded native Windows artifact")
    with zipfile.ZipFile(path) as z:
        all_names = [i.filename for i in z.infolist()]
        require(len(all_names) == len(set(all_names)), "duplicate ZIP member")
        out = []
        for index, part in enumerate(FILES):
            name = PREFIX + part
            require(name in all_names, "incomplete source process: " + name)
            entry = z.getinfo(name)
            require(0 < entry.file_size <= (65536 if index == 0 else 2097152)
                    and (entry.external_attr >> 16) & 0o170000 != 0o120000,
                    "linked or oversized Win32 source process")
            out.append(z.read(name))
        return tuple(out)


def audit(report_bytes: bytes, *logs_raw: bytes) -> dict:
    require(type(report_bytes) is bytes and 0 < len(report_bytes) <= 65536
            and len(logs_raw) == 5 and all(type(raw) is bytes and
                                            0 < len(raw) <= 2097152
                                            for raw in logs_raw),
            "report or five independent process logs missing")
    try:
        report = json.loads(report_bytes.decode("utf-8"))
        logs = [raw.decode("utf-8") for raw in logs_raw]
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid native Win32 profile selector log bytes") from exc
    require(type(report) is dict and set(report) == {
        "scope", "canonical_catalog_sha256",
        "controller_root_p1_switches", "created_in_actual_frontend",
        "fresh_native_boot_restored_mike",
        "paired_guest_result_accepted_by_this_probe",
        "physical_gamepad_hardware_accepted", "release_gate_credit",
        "source_guest_hot_swap",
    }, "unexpected producer report authority")
    require(
        report["scope"] == "native-p1-existing-profile-selector-real-controller-root-next-boot"
        and report["controller_root_p1_switches"] == ["mike->andrew", "andrew->mike"]
        and report["created_in_actual_frontend"] == ["mike", "andrew"]
        and report["fresh_native_boot_restored_mike"] is True
        and report["paired_guest_result_accepted_by_this_probe"] is False
        and report["physical_gamepad_hardware_accepted"] is False
        and report["source_guest_hot_swap"] is False
        and type(report["release_gate_credit"]) is int
        and report["release_gate_credit"] == 0
        and re.fullmatch(r"[a-f0-9]{64}", report["canonical_catalog_sha256"]) is not None,
        "profile selector producer report overclaims integration")
    first, second, mike_switch, andrew_switch, final = logs
    roots = [only(ROOT, l, "Windows user root")[1] for l in logs]
    root = PureWindowsPath(roots[0])
    require(root.is_absolute() and ".." not in root.parts
            and "Switch Two Real Stock Racers" in root.parts
            and len(set(roots)) == 1, "five native processes used different/unsafe roots")
    for i, log in enumerate(logs):
        require("SDL reports 0 joystick(s)" in log and "audio=dummy" in log
                and not any(tok in log for tok in FORBID),
                "physical device or result incorrectly claimed by source-log stage")
        require(log.count("script f=0 turbo on") == 1,
                "native guest process script source missing/duplicated")

    ordered_exact_source_lines(first, SOURCE, "anonymous MIKE creation")
    require("UR_BALDOSA_NATIVE_PROFILE APPLIED" not in first,
            "first racer artificially provisioned")
    ordered_exact_source_lines(second, SECOND, "named MIKE creates ANDREW")
    require(only(BOOT, second, "MIKE after creation")[1] == "mike",
            "second process did not boot own P1 save")

    def switch(log: str, profile: str, target: str) -> str:
        stages = (
            f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile} "
            f"root=saves/profile-{profile}",
            "UR_BALDOSA_MODERN_ROOT opened=1",
            f"UR_BALDOSA_MODERN_ROOT existing_p1_opened=1 from={profile} "
            f"to={target} activation=next_process",
            f"UR_BALDOSA_NATIVE_P1_SWITCH status=0 from={profile} "
            f"to={target} activation=next_process",
            "UR_BALDOSA_MODERN_ROOT existing_p1_saved=1 activation=next_process",
            "UR_BALDOSA_MODERN_ROOT existing_p1_closed=1",
            "UR_BALDOSA_MODERN_ROOT existing_p1_stale_race_blocked=1",
        )
        ordered_exact_source_lines(log, stages, "next-boot real controller modal")
        boot = only(BOOT, log, "one current named SRAM before switch")
        require(boot[1] == profile and log.index(stages[0]) <
                log.index(stages[1]) < boot.start() <
                log.index(stages[2]),
                "source boot/selector changed before real native switch")
        require(log.count("UR_BALDOSA_NATIVE_PROFILE PREFLIGHT_REJECTED status=3") == 1
                and log.count("UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed") == 1
                and log.index("UR_BALDOSA_MODERN_ROOT existing_p1_stale_race_blocked=1") <
                log.index("UR_BALDOSA_NATIVE_PROFILE PREFLIGHT_REJECTED status=3")
                and not any(token in log for token in (
                    "UR_BALDOSA_MODERN_ROOT stock_entered players=",
                    "UR_BALDOSA_MODERN_ROOT stock_requested players=",
                )),
                "switch failed to lock out stale guest before restart")
        return boot[2].lower()

    first_mike_fingerprint = switch(mike_switch, "mike", "andrew")
    andrew_fingerprint = switch(andrew_switch, "andrew", "mike")
    require(first_mike_fingerprint != andrew_fingerprint,
            "different created rider identity not preserved across boots")
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=0 unavailable=0",
        "UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=0 unavailable=0 selected=0",
        "UR_BALDOSA_MODERN_ROOT records_closed=1",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
    )
    ordered_exact_source_lines(final, stages, "fresh real MIKE boot after two switches")
    final_boot = only(BOOT, final, "one newly restored MIKE boot")
    require(final_boot[1] == "mike" and final_boot[2].lower() == first_mike_fingerprint
            and "UR_BALDOSA_NATIVE_PROFILE PREFLIGHT_REJECTED" not in final,
            "fresh source boot failed to restore MIKE")
    return {
        "scope": "hosted-win32-five-real-process-controller-semantic-existing-P1-switch",
        "five_native_process_log_sha256": [hashlib.sha256(x).hexdigest() for x in logs_raw],
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "p1_source_switch_mike_to_andrew_then_back_to_mike_observed": True,
        "fresh_mike_boot_matches_pre_switch_source_fingerprint": True,
        "source_confirmed_stale_race_block_for_both_switches": True,
        "saved_catalog_selector_or_SRAM_bytes_independently_decoded": False,
        "newly_earned_source_scored_2p_result_accepted": False,
        "both_source_earned_records_from_new_2p_result": False,
        "physical_two_gamepads_or_audio_accepted": False,
        "strict_original_USA_course_acceptance": 0,
        "release_gate_credit": 0,
        "outcome": "hosted_new_profile_switch_source_consistent_only",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", type=Path, required=True)
    options = ap.parse_args()
    out = audit(*read_archive(options.evidence))
    out["runtime_zip_sha256"] = hashlib.sha256(options.evidence.read_bytes()).hexdigest()
    print(json.dumps(out, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
