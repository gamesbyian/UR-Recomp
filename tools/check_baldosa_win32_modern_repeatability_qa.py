#!/usr/bin/env python3
"""Independently replay two source-pinned real Win32 Modern source archives.

Offline read-only consumer. No ROM, CI execution or release-gate promotion.
The retained JSON pins every original log hash, Actions wrapper and build SHA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "analysis/evidence/qa-win32-modern-options-practice-two-real-runs-20261015.json"
SHA = re.compile(r"[0-9a-f]{64}\Z")
SOURCE = re.compile(r"[0-9a-f]{40}\Z")
MAX_WRAPPER = 2_000_000
MAX_MEMBER = 200_000
MAX_TOTAL = 1_000_000
OPTIONS = ("game1_change", "game2_restore_defaults", "game3_defaults_boot",
           "game4_damaged", "game5_readonly_config")
COURSES = (("tier0_never_played", "dragster", 0, "DRAGSTER", 20),
           ("tier0_never_played", "bowl_stunt", 2, "BOWL", 20),
           ("tier0_never_played", "jumps_stunt", 12, "JUMPS", 20),
           ("tier0_never_played", "short_cut_circuit", 24, "SHORT CUT", 20),
           ("tier0_never_played", "east_race", 33, "EAST", 20),
           ("tier2_formatted_save", "wobble_jumper", 5, "WOBBLE", 40),
           ("tier2_formatted_save", "last_one_bounder", 15, "LAST ONE", 40),
           ("tier2_formatted_save", "down_up_runner", 25, "DOWN+UP", 40),
           ("tier2_formatted_save", "vertical_sprinter", 35, "VERTICAL", 40),
           ("tier2_formatted_save", "123_jump_last_ordinary", 39, "123 JUMP", 40))
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("INDEPENDENT_WIN32_MODERN_REJECTED: " + reason)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_archive(path: Path, expected_sha: str, filenames: set[str]) -> dict[str, bytes]:
    require(bool(SHA.fullmatch(expected_sha)), "missing external wrapper SHA256")
    require(path.is_file() and not path.is_symlink() and
            0 < path.stat().st_size <= MAX_WRAPPER, "wrapper absent/oversized/redirected")
    require(digest(path.read_bytes()) == expected_sha, "Actions wrapper SHA256 differs")
    out: dict[str, bytes] = {}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        require(len(infos) == len(filenames) and
                {i.filename for i in infos} == filenames,
                "missing, extra or duplicate evidence member")
        require(sum(i.file_size for i in infos) < MAX_TOTAL, "unbounded total payload")
        for info in infos:
            kind = stat.S_IFMT(info.external_attr >> 16)
            require(not info.is_dir() and not info.flag_bits & 1 and
                    kind in (0, stat.S_IFREG) and
                    0 < info.file_size < MAX_MEMBER, "symlink/encrypted/oversized member")
            out[info.filename] = archive.read(info)
            require(len(out[info.filename]) == info.file_size,
                    "member decompression length mismatch")
    return out


def events(log: str) -> list[str]:
    return [line for line in log.splitlines()
            if "UR_BALDOSA_" in line or line.startswith("script f=")]


def ordered_once(log: str, *stages: str) -> None:
    locations = []
    for stage in stages:
        require(log.count(stage) == 1, "missing/duplicate event " + stage)
        locations.append(log.index(stage))
    require(locations == sorted(set(locations)), "native player journey event order differs")


def read_report(data: bytes, what: str, source: str, exe: str) -> dict:
    report = json.loads(data.decode("utf-8"))
    require(type(report) is dict and type(report.get("release_gate_credit")) is int
            and report["release_gate_credit"] == 0
            and report.get("physical_gamepad_certified") is False,
            what + " falsely promotes a release/hardware gate")
    require(report.get("source_binding") ==
            {"github_sha": source, "exe_sha256": exe, "rom_sha256": ROM_SHA},
            what + " source/binary/ROM identity differs")
    return report


def validate_source(raw: dict[str, bytes], rows: list[dict], source: str,
                    executable: str) -> dict:
    option = read_report(raw["native_options/report.json"], "Options", source, executable)
    practice = read_report(raw["native_practice_courses/report.json"], "Practice", source, executable)
    require(option.get("scope") == "native-windows-options-semantic-pad-journey" and
            option.get("games") == 5 and option.get("readonly_config_case") == "enforced_and_refused" and
            option.get("defaults_restored") is True and
            option.get("damaged_file_preserved_aside") is True and
            option.get("racer_selector_untouched") is True,
            "Options functionality overstated")
    require(practice.get("scope") == "native-windows-practice-breadth-semantic-pad" and
            practice.get("courses_admitted") == 10 and
            practice.get("player_save_bytes_unchanged") is True and
            practice.get("practice_results_published") is False and
            practice.get("hunter_admitted") is False,
            "Practice functionality overstated")
    expected = {x["name"]: x for x in rows}
    require(len(expected) == 15 and sum(x["events"] for x in rows) == 1358,
            "bounded original event population differs")
    for name, item in expected.items():
        log = raw[name].decode("utf-8")
        require("[Gamepad] SDL reports 0 joystick(s)." in log and
                "video=windows audio=dummy" in log and
                "UR_BALDOSA_NATIVE_RUN CAPTURED=1" not in log,
                "missing genuine hosted Windows / or false hardware/career claim")
        lines = events(log)
        require(len(lines) == item["events"] and
                digest(("\n".join(lines) + "\n").encode()) == item["sha256"],
                "independent native source event digest mismatch: " + name)
    for stage in OPTIONS:
        text = raw[f"native_options/{stage}/log.txt"].decode("utf-8")
        if stage == "game1_change":
            ordered_once(text, "options_boot row=DISPLAY display=WINDOWED vsync=ON volume=100",
                         "options_adjusted row=DISPLAY display=BORDERLESS",
                         "options_adjusted row=VSYNC display=BORDERLESS vsync=ADAPTIVE",
                         "options_adjusted row=VOLUME display=BORDERLESS vsync=ADAPTIVE volume=90")
        elif stage == "game2_restore_defaults":
            ordered_once(text, "options_boot row=DISPLAY display=BORDERLESS vsync=ADAPTIVE volume=90",
                         "options_activated row=DEFAULTS display=WINDOWED vsync=ON volume=100 status=DEFAULTS RESTORED")
        elif stage == "game3_defaults_boot":
            require("options_boot row=DISPLAY display=WINDOWED vsync=ON volume=100" in text,
                    "fresh Defaults boot not observed")
        elif stage == "game4_damaged":
            ordered_once(text, "options_boot row=DISPLAY display=WINDOWED vsync=ON volume=100 status=NONE help=0 load=damaged",
                         "options_adjusted row=DISPLAY display=BORDERLESS vsync=ON volume=100 status=OLD FILE KEPT .damaged")
        else:
            require("options_adjusted row=VOLUME display=BORDERLESS vsync=ADAPTIVE volume=100 status=NOT APPLIED" in text and
                    "options_adjusted row=VOLUME display=BORDERLESS vsync=ADAPTIVE volume=90 status=SAVED" not in text,
                    "unwritable config falsely marked Saved")
    for group, case, track, title, available in COURSES:
        name = f"native_practice_courses/{group}-{case}/log.txt"
        text = raw[name].decode("utf-8")
        ordered_once(text,
                     f"practice_opened=1 available={available} course=0 source_menu_required=1",
                     f"practice_requested=1 course={track} name={title} source_route=stock",
                     f"practice_entered=1 course={track} original_course={track + 1} race=1 source_identity=verified",
                     "practice_sram_restored=1 bytes=8192")
        require("practice_rejected=" not in text and
                "UR_BALDOSA_NATIVE_RESULT observed=1" not in text and
                "UR_BALDOSA_NATIVE_MATCH CAPTURED=1" not in text,
                "Practice failure or career result contamination")
    return {"options_native_games": 5, "practice_native_games": 10,
            "source_events": 1358, "release_gate_credit": 0,
            "physical_hardware_verified": False,
            "saved_settings_raw_bytes_independently_compared": False}


def audit(earlier: Path, later: Path, receipt: Path = RECEIPT) -> dict:
    document = json.loads(receipt.read_text(encoding="utf-8"))
    require(document.get("schema") == "ur-independent-modern-win32-options-practice-review/1" and
            document.get("boundaries", {}).get("accepted_release_gates") == 0 and
            document.get("boundaries", {}).get("original_native_complete_event_parity_accepted") == 0,
            "noncanonical independent evidence receipt")
    runs = document["runs"]
    require(len(runs) == 2 and runs[0]["workflow_run_id"] == 38701860728 and
            runs[1]["workflow_run_id"] == 38703695304,
            "unexpected source run identities")
    expected_paths = {row["name"] for row in document["events"]} | {
        "native_options/report.json", "native_practice_courses/report.json"}
    receipts = []
    for path, run in zip((earlier, later), runs):
        source, exe = run["source_sha"], run["packaged_executable_sha256"]
        require(bool(SOURCE.fullmatch(source)) and bool(SHA.fullmatch(exe)),
                "malformed external source/executable pins")
        raw = read_archive(path, run["options_practice_artifact"]["sha256"], expected_paths)
        outcome = validate_source(raw, document["events"], source, exe)
        receipts.append({"workflow_run_id": run["workflow_run_id"],
                         "head_source_sha": source,
                         "actions_wrapper_sha256": run["options_practice_artifact"]["sha256"],
                         "exe_sha256": exe, **outcome})
    return {"schema": "ur-independently-replayed-win32-modern-archives/1",
            "runs": receipts, "two_sources_distinct": runs[0]["source_sha"] != runs[1]["source_sha"],
            "native_log_lines_hash_identical_across_runs": True,
            "release_gate_credit": 0,
            "independently_tested_physical_gamepad_audio_display": False,
            "independently_tested_disk_powerloss": False,
            "exact_merged_main_candidate_nominated": False}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--earlier", type=Path, required=True)
    p.add_argument("--later", type=Path, required=True)
    p.add_argument("--receipt", type=Path, default=RECEIPT)
    args = p.parse_args()
    try:
        result = audit(args.earlier, args.later, args.receipt)
    except (ValueError, KeyError, UnicodeError, OSError, zipfile.BadZipFile,
            json.JSONDecodeError) as error:
        p.exit(1, str(error) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
