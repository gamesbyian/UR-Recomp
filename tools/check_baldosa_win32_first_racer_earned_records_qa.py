#!/usr/bin/env python3
"""Independent ROM-free three-game first-racer -> earned 1P -> Records log QA.

Accept only an actual coarchived Windows producer report and three distinct
native guest logs. Producer-reported .urrun SHA/FNV values are NOT independently
rehashed because the generated save/record bytes remain absent. Never promotes
original-emulator event parity, packaged human controller or physical L5 QA.
"""
from __future__ import annotations

import hashlib
import json
import re

from check_baldosa_win32_first_racer_evidence import SOURCE, ordered_unique

SHA256 = re.compile(r"[0-9a-f]{64}\Z")
NAME = re.compile(r"run-[0-9]{16}-[0-9]{4}\.urrun\Z")
RUN = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p "
    r"profile=mike course=course:01 input_frames=(\d+) "
    r"inputs=(\d+) path=([^\r\n]+)\r?$"
)
RESULT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p "
    r"race_host=(\d+) result_host=(\d+) finish_ticks60=(\d+) "
    r"input_frames=(\d+) input_runs=(\d+) published=1\r?$"
)
BOOT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
    r"profile=mike bytes=8192 fnv=([0-9a-fA-F]{8})\r?$"
)
FRESH_RECORDS = re.compile(
    r"(?m)^UR_BALDOSA_MODERN_ROOT records_opened=1 "
    r"profile=selected validated=1 unavailable=0\r?$"
)


def one_boot(log: str, label: str) -> str:
    boots = BOOT.findall(log)
    if (
        len(boots) != 1
        or log.count(
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
            "root=saves/profile-mike"
        ) != 1
        or "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1" in log
    ):
        raise ValueError(f"{label} has no unique fresh named native SRAM boot")
    return boots[0].lower()


def audit_hosted_first_racer_earned_1p(
    raw_report: bytes, raw_created: bytes, raw_played: bytes,
    raw_records: bytes,
) -> dict[str, object]:
    for item, limit in (
        (raw_report, 64 * 1024),
        (raw_created, 2 * 1024 * 1024),
        (raw_played, 2 * 1024 * 1024),
        (raw_records, 2 * 1024 * 1024),
    ):
        if type(item) is not bytes or not 0 < len(item) <= limit:
            raise ValueError("three-game CI source evidence is absent or oversized")
    try:
        report = json.loads(raw_report.decode("utf-8"))
        created, played, records = (
            item.decode("utf-8") for item in
            (raw_created, raw_played, raw_records)
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("three-game CI evidence is not UTF-8 JSON/text") from exc
    if not isinstance(report, dict):
        raise ValueError("three-game CI producer report must be an object")
    fields = (
        "first_game_created_first_named_racer",
        "second_game_loaded_named_sram_and_finished_real_source_race",
        "third_game_reopened_exact_earned_run_read_only",
        "active_selector_and_catalog_preserved",
        "anonymous_sram_preserved",
    )
    sha = report.get("one_canonical_run_sha256")
    if (
        report.get("scope") != "actual-native-windows-first-racer-to-earned-one-player-records"
        or any(report.get(field) is not True for field in fields)
        or report.get("physical_gamepad_verified") is not False
        or report.get("strict_original_native_event_pass") is not False
        or type(report.get("release_gate_credit")) is not int
        or report["release_gate_credit"] != 0
        or type(sha) is not str or not SHA256.fullmatch(sha)
    ):
        raise ValueError("three-game CI report has missing result or inflated release claims")

    ordered_unique(created, SOURCE, "first anonymous guest")
    if any(marker in created for marker in (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike",
        "UR_BALDOSA_NATIVE_RESULT observed=1",
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
        "UR_BALDOSA_MODERN_ROOT stock_entered",
    )):
        raise ValueError("first anonymous process acquired forbidden played result")

    playing_boot = one_boot(played, "second played guest")
    markers = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p profile=mike",
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p",
    )
    ordered_unique(played, markers, "played source guest")
    captures, results = list(RUN.finditer(played)), list(RESULT.finditer(played))
    if len(captures) != 1 or len(results) != 1:
        raise ValueError("played guest did not capture and settle one exact 1P result")
    capture, result = captures[0], results[0]
    capture_frames, capture_runs = int(capture[1]), int(capture[2])
    first, last, ticks, frames, runs = map(int, result.groups())
    path = capture[3].replace("\\", "/")
    basename = path.rsplit("/", 1)[-1]
    # A matching claimed hash and an arbitrary path fragment such as
    # relative/../../runs/mike/name.urrun do not prove the native named
    # writer's canonical Windows capture. Bind this to an absolute drive
    # path with no traversing, empty or redirected interior components.
    path_segments = path[3:].split("/") if re.match(r"^[A-Za-z]:/", path) else []
    canonical_capture_path = (
        len(path_segments) >= 3
        and all(segment not in ("", ".", "..") and ":" not in segment
                and not any(ord(ch) < 32 for ch in segment)
                for segment in path_segments)
        and path_segments[-3:-1] == ["runs", "mike"]
        and path_segments[-1] == basename
        and NAME.fullmatch(basename) is not None
    )
    if (
        not canonical_capture_path
        or played.count("UR_BALDOSA_NATIVE_RUN CAPTURED=1") != 1
        or played.count("UR_BALDOSA_NATIVE_RESULT observed=1") != 1
        or not (first > 0 and first < last and ticks > 0)
        or last - first != frames
        or frames <= 0 or runs <= 0
        or capture_frames != frames or capture_runs != runs
        or capture.start() >= result.start()
        or any(marker in played for marker in (
            "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1",
            "UR_BALDOSA_NATIVE_RUN NOT_SAVED=1",
            "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
        ))
        or played.count(
            "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=committed"
        ) != 1
    ):
        raise ValueError("played guest captured path, source timebase or named SRAM checkpoint contradicts")

    records_boot = one_boot(records, "third records guest")
    ordered_unique(records, (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192",
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=1 unavailable=0",
        "UR_BALDOSA_MODERN_ROOT records_closed=1",
    ), "third fresh Records guest")
    if (
        len(FRESH_RECORDS.findall(records)) != 1
        or records.count(
            "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=committed"
        ) != 1
        or any(marker in records for marker in (
            "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
            "UR_BALDOSA_NATIVE_RESULT observed=1",
            "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
            "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1",
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
            "UR_BALDOSA_NATIVE_FIRST_RACER status=0",
        ))
    ):
        raise ValueError("third game did not read one earned run without publishing another")
    # The SRAM fingerprint is intentionally not required to remain identical:
    # the second guest's *actual* race legitimately commits a new checkpoint.
    return {
        "scope": "hosted-win32-first-racer-earned-1p-three-game-logs-only",
        "hosted_first_racer_earned_1p_three_game_logs_consistent": True,
        "hosted_played_1p_capture_basename": basename,
        "hosted_played_1p_finish_ticks60": ticks,
        "hosted_played_1p_input_frames": frames,
        "hosted_played_guest_boot_fnv_observed": playing_boot,
        "hosted_fresh_records_guest_boot_fnv_observed": records_boot,
        "hosted_one_canonical_urrun_sha256_producer_reported": sha,
        "hosted_report_sha256": hashlib.sha256(raw_report).hexdigest(),
        "hosted_created_log_sha256": hashlib.sha256(raw_created).hexdigest(),
        "hosted_played_log_sha256": hashlib.sha256(raw_played).hexdigest(),
        "hosted_records_log_sha256": hashlib.sha256(raw_records).hexdigest(),
        "hosted_saved_urrun_bytes_independently_decoded": False,
        "hosted_packaged_cmd_auto_relaunch_verified": False,
        "hosted_physical_controller_verified": False,
        "strict_original_native_complete_event_accepted": False,
        "release_gate_credit": 0,
        "outcome": "inconclusive_for_release",
    }
