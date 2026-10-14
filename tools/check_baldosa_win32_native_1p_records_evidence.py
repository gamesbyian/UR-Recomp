#!/usr/bin/env python3
"""Read-only independent consistency check for hosted native 1P Records logs.

The producer's .urrun bytes are intentionally absent from the Actions
artifact. This checker does NOT authenticate that file's SHA or elevate the
result to original-emulator parity, physical hardware or release L4/L5.
"""
from __future__ import annotations

import hashlib
import json
import re


SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CAPTURE = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p "
    r"profile=native-ci-rider course=course:01 input_frames=(\d+) "
    r"inputs=(\d+) path=([^\r\n]+)\r?$"
)
RESULT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p "
    r"race_host=(\d+) result_host=(\d+) finish_ticks60=(\d+) "
    r"input_frames=(\d+) input_runs=(\d+) published=1\r?$"
)
FRESH_RECORDS = re.compile(
    r"(?m)^UR_BALDOSA_MODERN_ROOT records_opened=1 "
    r"profile=selected validated=1 unavailable=0\r?$"
)


def audit_hosted_native_1p_records(
    raw_report: bytes, raw_played: bytes, raw_fresh: bytes,
) -> dict[str, object]:
    """Validate three archived records as *coarchived log evidence* only."""
    try:
        report = json.loads(raw_report.decode("utf-8"))
        played = raw_played.decode("utf-8")
        fresh = raw_fresh.decode("utf-8")
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("hosted native 1P Records witness is not UTF-8 JSON/log text") from exc
    if not isinstance(report, dict):
        raise ValueError("hosted native 1P Records report must be an object")
    expected_true = (
        "first_process_source_result_published",
        "second_native_game_process_reopened_exact_new_record",
        "second_process_reloaded_previous_native_sram",
    )
    if (
        report.get("scope") != "native-windows-modern-real-guest-1p-product-integration"
        or any(report.get(field) is not True for field in expected_true)
        or type(report.get("newly_persisted_urrun_count")) is not int
        or report["newly_persisted_urrun_count"] != 1
        or not isinstance(report.get("new_run_sha256"), str)
        or not SHA256.fullmatch(report["new_run_sha256"])
        or type(report.get("release_gate_credit")) is not int
        or report["release_gate_credit"] != 0
        or report.get("original_native_strict_event_pass") is not False
        or report.get("physical_controller_hardware_tested") is not False
    ):
        raise ValueError("hosted native 1P Records report has contradictory admission claims")
    captures = list(CAPTURE.finditer(played))
    results = list(RESULT.finditer(played))
    if len(captures) != 1 or len(results) != 1:
        raise ValueError("hosted native 1P Records log lacks one canonical captured result")
    c, r = captures[0], results[0]
    race_host, result_host, ticks, input_frames, input_runs = map(int, r.groups())
    if (
        not (0 < race_host < result_host)
        or ticks <= 0 or input_frames <= 0 or input_runs <= 0
        or c.start() >= r.start()
        or int(c[1]) != input_frames
        or int(c[2]) != input_runs
        or played.count("UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c") != 1
        or "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1" in played
        or "UR_BALDOSA_NATIVE_RUN NOT_SAVED=1" in played
    ):
        raise ValueError("hosted native 1P source-result chronology/input receipt inconsistent")
    if (
        len(FRESH_RECORDS.findall(fresh)) != 1
        or len(re.findall(
            r"(?m)^UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider\b",
            fresh,
        )) != 1
        or len(re.findall(
            r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-rider bytes=8192\b",
            fresh,
        )) != 1
        or "UR_BALDOSA_NATIVE_RUN CAPTURED=1" in fresh
        or "UR_BALDOSA_NATIVE_RESULT observed=1" in fresh
        or "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1" in fresh
    ):
        raise ValueError("hosted native fresh-game Records log lacks read-only named profile")
    return {
        "hosted_native_1p_result_to_fresh_records_logs_consistent": True,
        "hosted_new_1p_run_sha256_producer_reported": report["new_run_sha256"],
        "hosted_1p_result_ticks60": ticks,
        "hosted_1p_result_host_frame": result_host,
        "hosted_native_1p_report_sha256": hashlib.sha256(raw_report).hexdigest(),
        "hosted_native_1p_played_log_sha256": hashlib.sha256(raw_played).hexdigest(),
        "hosted_native_1p_fresh_log_sha256": hashlib.sha256(raw_fresh).hexdigest(),
        "hosted_saved_urrun_bytes_independently_reopened": False,
        "hosted_original_emulator_parity_accepted": False,
        "hosted_physical_hardware_accepted": False,
    }
