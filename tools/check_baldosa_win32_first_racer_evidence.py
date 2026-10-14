#!/usr/bin/env python3
"""Read-only hosted Win32 first-racer creation -> fresh native boot QA.

This consumes exactly the proposed PR #1439 three-file CI diagnostic group.
It does not authenticate absent SRAM/catalog bytes, a physical controller,
the Windows launcher auto-restart, an earned 1P/2P result or a release gate.
"""
from __future__ import annotations

import hashlib
import json
import re


SHA256 = re.compile(r"[0-9a-f]{64}\Z")
BOOT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
    r"profile=mike bytes=8192 fnv=([0-9a-fA-F]{8})\r?$"
)
SOURCE = (
    "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
    "UR_BALDOSA_MODERN_ROOT opened=1",
    "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process",
    "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike activation=next_process",
    "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process",
)
NEXT = (
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
    "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=",
    "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
)
HASH_KEYS = frozenset((
    "save.srm", "host-profile.txt", "profiles-v1.txt", "host-state-v1.txt",
))
MAX_REPORT = 64 * 1024
MAX_LOG = 2 * 1024 * 1024


def ordered_unique(log: str, markers: tuple[str, ...], name: str) -> None:
    positions = []
    for marker in markers:
        if log.count(marker) != 1:
            raise ValueError(f"{name} missing or duplicated stage: {marker}")
        positions.append(log.index(marker))
    if positions != sorted(positions):
        raise ValueError(f"{name} native stages out of source order")


def audit_hosted_win32_first_racer(
    report_bytes: bytes, created_log: bytes, fresh_log: bytes,
) -> dict[str, object]:
    if (
        any(type(item) is not bytes for item in (
            report_bytes, created_log, fresh_log,
        ))
        or not 0 < len(report_bytes) <= MAX_REPORT
        or not 0 < len(created_log) <= MAX_LOG
        or not 0 < len(fresh_log) <= MAX_LOG
    ):
        raise ValueError("missing/oversized native first-racer Windows logs")
    try:
        report = json.loads(report_bytes.decode("utf-8"))
        created = created_log.decode("utf-8")
        fresh = fresh_log.decode("utf-8")
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("first-racer evidence is not UTF-8 JSON or text") from exc
    if not isinstance(report, dict):
        raise ValueError("first-racer report must be JSON object")
    reported_hashes = report.get("before_reboot_sha256")
    if (
        report.get("scope") != "first-anonymous-modern-root-stock-racer-next-process-boot"
        or report.get("first_native_guest_creation") is not True
        or report.get("fresh_native_guest_named_profile_applied") is not True
        or report.get("existing_stock_sram_root") != "saves/profile-mike"
        or report.get("physical_pad_acceptance") is not False
        or report.get("independent_original_native_event_pass") is not False
        or type(report.get("release_gate_credit")) is not int
        or report["release_gate_credit"] != 0
        or not isinstance(reported_hashes, dict)
        or set(reported_hashes) != HASH_KEYS
        or any(type(v) is not str or not SHA256.fullmatch(v)
               for v in reported_hashes.values())
    ):
        raise ValueError("first-racer report carries unsupported release or save claims")

    ordered_unique(created, SOURCE, "first anonymous guest")
    if any(token in created for token in (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike",
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike",
        "UR_BALDOSA_MODERN_ROOT stock_entered",
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
        "UR_BALDOSA_NATIVE_RESULT observed=1",
    )):
        raise ValueError("first-racer creation incorrectly reused live anonymous guest")

    ordered_unique(fresh, NEXT, "second named guest")
    boots = BOOT.findall(fresh)
    if (
        len(boots) != 1
        or any(token in fresh for token in (
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT",
            "UR_BALDOSA_NATIVE_FIRST_RACER status=0",
            "UR_BALDOSA_MODERN_ROOT first_racer_created=1",
            "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
            "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
            "UR_BALDOSA_NATIVE_RESULT observed=1",
        ))
    ):
        raise ValueError("second named guest is not a single clean, read-only boot")

    return {
        "scope": "hosted-source-first-racer-to-fresh-native-boot-logs-only",
        "hosted_first_racer_anonymous_creation_to_fresh_named_boot_consistent": True,
        "hosted_first_racer_preset_index": 0,
        "hosted_fresh_game_stock_players": 1,
        "hosted_fresh_boot_sram_fnv32_observed": boots[0].lower(),
        "hosted_before_reboot_sha256_producer_reported": dict(reported_hashes),
        "hosted_first_racer_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "hosted_first_racer_creation_log_sha256": hashlib.sha256(created_log).hexdigest(),
        "hosted_first_racer_fresh_log_sha256": hashlib.sha256(fresh_log).hexdigest(),
        "hosted_created_profile_bytes_independently_rehashed": False,
        "hosted_one_shot_packaged_launcher_restart_verified": False,
        "hosted_earned_result_or_fresh_records_verified": False,
        "hosted_physical_controller_verified": False,
        "strict_original_native_complete_event_accepted": False,
        "release_gate_credit": 0,
        "outcome": "inconclusive_for_release",
    }
