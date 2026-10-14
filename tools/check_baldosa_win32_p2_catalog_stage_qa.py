#!/usr/bin/env python3
"""Independent read-only Windows source + five-stage P2 catalog recovery audit.

Only real, separately downloaded, SHA-pinned Actions artifacts can establish
source observations. The ROM-free unit tests merely exercise rejection logic.
This reader does not certify OS crash durability, controller hardware, scored
race results, original/native parity or a final release candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from check_baldosa_win32_created_pair_raw_qa import _typed_profile

STAGES = (
    "after-p1-created",
    "after-p2-created",
    "catalog-row-lost",
    "after-p2-recovered",
    "after-source-go",
)
ROOT_FILES = ("host-state-v1.txt", "profiles-v1.txt")
P1_FILES = ("saves/profile-mike/host-profile.txt", "saves/profile-mike/save.srm")
P2_FILES = ("saves/profile-martin/host-profile.txt", "saves/profile-martin/save.srm")
P2_MUTEX = "saves/profile-martin/host-profile.txt.urmutex"
SOURCE_LOGS = (
    "first_native_mike/log.txt", "second_native_martin/log.txt",
    "third_native_p2_recovers/log.txt", "fourth_native_two_seat_go/log.txt",
)
SOURCE_FILES = ("report.json",) + SOURCE_LOGS
SCHEMA = "baldosa-native-p2-catalog-recovery-stage-v1"
MAX_ZIP_BYTES = 8 * 1024 * 1024
MAX_MEMBER = 64 * 1024
MAX_TOTAL = 2 * 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SINGLE_CATALOG = b"UR-PROFILE-CATALOG/1\nmike|0|MIKE\n"
DOUBLE_CATALOG = SINGLE_CATALOG + b"martin|2|MARTIN\n"
ROOT_RX = re.compile(r"(?m)^\[Launcher\] Config/saves anchored to '([^'\r\n]+)'\.\r?$")
# A strict source-ordered finite state machine; not merely a producer report.
EVENTS = (
    ("UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
     "UR_BALDOSA_MODERN_ROOT first_racer_opened=1",
     "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=8 button=X",
     "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike",
     "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=8 button=A"),
    ("UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike",
     "UR_BALDOSA_MODERN_ROOT second_racer_opened=1",
     "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 button=X",
     "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 button=DPAD_DOWN",
     "UR_BALDOSA_NATIVE_SECOND_RACER status=0 preset=2 id=martin",
     "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 button=A"),
    ("UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike",
     "UR_BALDOSA_MODERN_ROOT second_racer_opened=1",
     "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 button=X",
     "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 button=DPAD_DOWN",
     "UR_BALDOSA_NATIVE_SECOND_RACER_RECOVERY restored=1 catalog_only=1 p1_unchanged=1",
     "UR_BALDOSA_NATIVE_SECOND_RACER status=4 preset=2 id=martin",
     "UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad mode=9 button=A",
     "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=unchanged"),
    ("UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike",
     "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
     "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
     "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
     "script f=2353 until 00E1F ok",
     "script f=2353 dump go ok"),
)


def require(ok: bool, detail: str) -> None:
    if not ok:
        raise ValueError("Independent P2 catalog stage QA: " + detail)


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def exact_archive(path: Path, expected_sha: str, maximum: int) -> zipfile.ZipFile:
    require(isinstance(expected_sha, str) and SHA256.fullmatch(expected_sha) is not None,
            "missing expected full Actions SHA-256")
    require(path.is_file() and not path.is_symlink() and
            0 < path.stat().st_size <= maximum,
            "missing/redirected/unbounded Actions archive")
    require(digest(path.read_bytes()) == expected_sha,
            "downloaded Actions ZIP differs from independently pinned SHA-256")
    return zipfile.ZipFile(path)


def bounded_member(z: zipfile.ZipFile, name: str, cap: int,
                   allow_empty: bool = False) -> bytes:
    info = z.getinfo(name)
    mode = (info.external_attr >> 16) & 0o170000
    require(not info.is_dir() and mode != 0o120000 and
            0 <= info.file_size <= cap and
            (allow_empty or info.file_size > 0),
            "ZIP member linked, directory, missing content or oversized: " + name)
    data = z.read(info)
    require(len(data) == info.file_size, "ZIP decompression size mismatch: " + name)
    return data


def _read_json(raw: bytes, why: str) -> dict:
    try:
        val = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid UTF-8 JSON " + why) from exc
    require(type(val) is dict, "expected JSON object: " + why)
    return val


def source_audit(z: zipfile.ZipFile) -> dict:
    require(len(z.namelist()) == len(set(z.namelist())) and
            set(z.namelist()) == set(SOURCE_FILES),
            "source ZIP must contain precisely report and four distinct native game logs")
    report = _read_json(bounded_member(z, "report.json", MAX_MEMBER), "source report")
    expected_fields = {
        "scope", "fault_cut", "source_created_named_profiles",
        "first_and_second_real_p1_pad_handler",
        "third_real_p1_pad_handler_catalog_only_recovery",
        "fourth_real_guest_two_seat_stock_go",
        "unmodified_p2_typed_raw_mutex", "original_p1_selector_unchanged",
        "physical_os_crash_proven", "genuine_completed_match_proven_by_this_route",
        "physical_controller_hardware_proven", "release_gate_credit",
        # The new producer identifies exactly the raw snapshot stage contract.
        "raw_source_archive", "source_stage_manifest_names",
    }
    require(set(report) == expected_fields and
            report["scope"] == "four-real-windows-games-native-created-martin-recovered-catalog"
            and report["fault_cut"] == "ci-only-restore-original-single-row-catalog"
            and report["source_created_named_profiles"] == ["mike", "martin"]
            and report["raw_source_archive"] == "ci-owned-p2-recovery-raw"
            and report["source_stage_manifest_names"] == list(STAGES)
            and all(report[k] is True for k in (
                "first_and_second_real_p1_pad_handler",
                "third_real_p1_pad_handler_catalog_only_recovery",
                "fourth_real_guest_two_seat_stock_go",
                "unmodified_p2_typed_raw_mutex",
                "original_p1_selector_unchanged"))
            and all(report[k] is False for k in (
                "physical_os_crash_proven", "genuine_completed_match_proven_by_this_route",
                "physical_controller_hardware_proven"))
            and type(report["release_gate_credit"]) is int and report["release_gate_credit"] == 0,
            "source report incomplete, forged or claims unearned acceptance")
    logs = [bounded_member(z, name, 2 * 1024 * 1024).decode("utf-8")
            for name in SOURCE_LOGS]
    roots = []
    for i, log in enumerate(logs):
        matches = list(ROOT_RX.finditer(log))
        require(len(matches) == 1, "missing/duplicate Windows game source root")
        roots.append(matches[0].group(1))
        require("[Gamepad] SDL reports 0 joystick(s)." in log and
                "video=windows audio=dummy" in log,
                "physical hardware/audio producer claim inconsistent")
        previous = -1
        for needle in EVENTS[i]:
            require(log.count(needle) == 1,
                    "missing/duplicate original native stage in " + SOURCE_LOGS[i] + ": " + needle)
            position = log.index(needle)
            require(position > previous, "native source stage order changed")
            previous = position
        require("UR_BALDOSA_NATIVE_MATCH CAPTURED=1" not in log and
                "UR_BALDOSA_NATIVE_RUN CAPTURED=1" not in log,
                "recovery-only source route manufactured game result")
    require(len(set(roots)) == 1 and
            roots[0].endswith("Interrupted Native P2 Catalog Test Only"),
            "four native Windows games did not use the same disposable root")
    return {
        "source_logs": len(logs),
        "logged_root_consistent": True,
        "original_guest_stock_go_frame": 2353,
        "physical_controller_count_logged": 0,
    }


def stage_audit(z: zipfile.ZipFile) -> dict:
    expected = set()
    for stage in STAGES:
        paths = ROOT_FILES + P1_FILES
        if stage != STAGES[0]:
            paths += P2_FILES + (P2_MUTEX,)
        expected.update(f"{stage}/{name}" for name in ("manifest.json",) + paths)
    names = z.namelist()
    require(len(names) == len(set(names)) and set(names) == expected,
            "missing/extra/duplicated five-stage canonical CI-owned raw ZIP member")
    require(sum(info.file_size for info in z.infolist()) <= MAX_TOTAL,
            "unbounded decompressed snapshot population")
    snapshots = {}
    profiles = {}
    for stage in STAGES:
        prefix = stage + "/"
        raw_manifest = bounded_member(z, prefix + "manifest.json", MAX_MEMBER)
        manifest = _read_json(raw_manifest, "stage manifest")
        paths = ROOT_FILES + P1_FILES
        if stage != STAGES[0]:
            paths += P2_FILES + (P2_MUTEX,)
        require(set(manifest) == {
                    "schema", "stage", "scope", "source_profiles",
                    "members", "includes_rom", "includes_executable",
                    "release_gate_credit"
                } and manifest["schema"] == SCHEMA and manifest["stage"] == stage
                and manifest["scope"] == "one-throwaway-Windows-CI-user-only"
                and manifest["source_profiles"] == (
                    ["mike"] if stage == STAGES[0] else ["mike", "martin"])
                and manifest["includes_rom"] is False
                and manifest["includes_executable"] is False
                and type(manifest["release_gate_credit"]) is int
                and manifest["release_gate_credit"] == 0
                and type(manifest["members"]) is dict
                and set(manifest["members"]) == set(paths),
                "untrusted snapshot manifest identity or membership")
        files = {}
        for path in paths:
            data = bounded_member(
                z, prefix + path, MAX_MEMBER,
                allow_empty=(path == P2_MUTEX))
            claim = manifest["members"][path]
            require(type(claim) is dict and set(claim) == {"sha256", "bytes"} and
                    type(claim["bytes"]) is int and claim["bytes"] == len(data)
                    and type(claim["sha256"]) is str
                    and SHA256.fullmatch(claim["sha256"]) is not None
                    and digest(data) == claim["sha256"],
                    "raw file and typed manifest hash/size disagree: " + path)
            files[path] = data
        require(files[ROOT_FILES[0]].startswith(b"UR-HOST-STATE/6\n")
                and files[ROOT_FILES[0]].count(b"profile=mike\n") == 1
                and b"profile=martin\n" not in files[ROOT_FILES[0]],
                "P1 active selector absent or changed to P2")
        require(files[ROOT_FILES[1]] == (
                    SINGLE_CATALOG if stage in (STAGES[0], STAGES[2])
                    else DOUBLE_CATALOG),
                "stage catalog does not represent exact one-row / two-row fault")
        p1 = _typed_profile(files[P1_FILES[0]], files[P1_FILES[1]], "mike", 0)
        if stage != STAGES[0]:
            p2 = _typed_profile(files[P2_FILES[0]], files[P2_FILES[1]], "martin", 2)
            require(files[P2_MUTEX] == b"", "P2 typed CAS mutex is not zero bytes")
            profiles[stage] = {"mike": p1, "martin": p2}
        else:
            profiles[stage] = {"mike": p1}
        snapshots[stage] = files
    # Compare ORIGINAL archived bytes, not the report's "unchanged" assertions.
    ref = snapshots[STAGES[1]]
    for stage in STAGES[2:]:
        current = snapshots[stage]
        require(all(ref[p] == current[p] for p in P2_FILES + (P2_MUTEX,)),
                "existing native P2 typed/raw SRAM or OS mutex was rewritten")
    require(all(snapshots[STAGES[0]][ROOT_FILES[0]] == snapshots[stage][ROOT_FILES[0]]
                for stage in STAGES[1:]),
            "original P1 active selector changed across independent processes")
    require(all(snapshots[STAGES[1]][p] == snapshots[STAGES[2]][p] for p in P1_FILES),
            "catalog-only injected rollback unexpectedly altered original P1")
    require(snapshots[STAGES[1]][ROOT_FILES[1]] ==
            snapshots[STAGES[3]][ROOT_FILES[1]] ==
            snapshots[STAGES[4]][ROOT_FILES[1]],
            "native P2 recovery did not preserve exact two-row catalog bytes")
    return {
        "stages_independently_decoded": list(STAGES),
        "stage_member_count": len(expected),
        "original_p1_selector_bytes_equal_across_five_stages": True,
        "native_p2_typed_raw_and_empty_mutex_equal_across_four_later_stages": True,
        "catalog_only_cut_preserves_existing_p1_bytewise": True,
        "original_one_row_then_two_row_then_loss_then_recovery_then_go_verified": True,
        "typed_original_stock_rider_ids": [0, 2],
        "typed_profile_generations_by_stage": profiles,
    }


def audit_pair(source_zip: Path, stage_zip: Path, *,
               expected_source_sha256: str, expected_stage_sha256: str) -> dict:
    with exact_archive(source_zip, expected_source_sha256, MAX_ZIP_BYTES) as source:
        source_result = source_audit(source)
    with exact_archive(stage_zip, expected_stage_sha256, MAX_ZIP_BYTES) as stage:
        stage_result = stage_audit(stage)
    return {
        "scope": "independent-genuine-Windows-native-catalog-stage-source-and-raw-consistency",
        "source_actions_artifact_sha256": expected_source_sha256,
        "raw_stages_actions_artifact_sha256": expected_stage_sha256,
        **source_result, **stage_result,
        "source_stage_capture_wall_clock_independently_timestamped": False,
        "same_GitHub_Actions_run_verified_from_external_metadata": False,
        "power_loss_or_real_process_crash_verified": False,
        "physical_two_gamepads_or_audible_audio_verified": False,
        "original_USA_complete_source_event_parity_accepted": 0,
        "one_final_merged_main_Windows_candidate_accepted": False,
        "release_gate_credit": 0,
        "outcome": "native_process_source_plus_five_retained_recovery_stages_no_release_credit",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--stage-zip", type=Path, required=True)
    parser.add_argument("--expected-source-sha256", required=True)
    parser.add_argument("--expected-stage-sha256", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit_pair(
        args.source_zip, args.stage_zip,
        expected_source_sha256=args.expected_source_sha256,
        expected_stage_sha256=args.expected_stage_sha256)
    body = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out is None:
        print(body, end="")
    else:
        with args.out.open("x", encoding="utf-8") as output:
            output.write(body, )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
