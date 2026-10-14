#!/usr/bin/env python3
"""Independent read-only review of a *retained* no-args Windows CMD trace.

An already-green native Windows producer only archived two successful booleans
in its launcher report, not its first-racer-autorelaunch.log. Until the actual
source log is retained this checker cannot independently witness the launcher
sequence. Never certify human pads, fresh Records or original event parity.
"""
from __future__ import annotations

import hashlib
import re

BOOT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
    r"profile=mike bytes=8192 fnv=([0-9a-fA-F]{8})\r?$"
)
ROOT = re.compile(r"(?m)^UR_BALDOSA_MODERN_ROOT opened=1\r?$")
STAGES = (
    "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
    "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process",
    "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike activation=next_process",
    "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process",
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
    "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=",
)
ECHO = "UR-BALDOSA-FIRST-RACER: Restarting with newly created racer."
FORBIDDEN = (
    "UR_BALDOSA_NATIVE_RESULT observed=1",
    "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
    "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider",
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-second",
    "UR_BALDOSA_MODERN_ROOT stock_entered",
    "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1",
)


def audit_win32_cmd_first_racer_source(raw_log: bytes) -> dict[str, object]:
    if type(raw_log) is not bytes or not 0 < len(raw_log) <= 2 * 1024 * 1024:
        raise ValueError("missing or oversized real no-arguments Windows launcher log")
    try:
        log = raw_log.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("native Windows launcher trace is not UTF-8") from exc
    positions = []
    for stage in STAGES:
        if log.count(stage) != 1:
            raise ValueError("no-args Windows native CMD trace missing or duplicated stage")
        positions.append(log.index(stage))
    if positions != sorted(positions):
        raise ValueError("CMD trace native profile stages occur out of source order")
    opened = [m.start() for m in ROOT.finditer(log)]
    if (
        len(opened) != 2
        or not positions[0] < opened[0] < positions[1]
        or not positions[4] < opened[1]
        or log.count(ECHO) != 1
    ):
        raise ValueError("CMD did not show exactly two source-root openings and one restart echo")
    boot = BOOT.findall(log)
    if len(boot) != 1 or any(token in log for token in FORBIDDEN):
        raise ValueError("CMD source boot is missing/ambiguous or forged as gameplay")
    if log.count("UR_BALDOSA_NATIVE_PROFILE DEFAULT") != 1:
        raise ValueError("second CMD game incorrectly booted anonymous")
    return {
        "scope": "hosted-extracted-noargs-cmd-native-restart-log-only",
        "hosted_cmd_two_native_roots_one_first_racer_restart_log_consistent": True,
        "hosted_cmd_second_native_guest_sram_fnv32_observed": boot[0].lower(),
        "hosted_cmd_raw_log_sha256": hashlib.sha256(raw_log).hexdigest(),
        "hosted_cmd_log_independently_recomputed": True,
        "hosted_immutable_zip_still_separately_verified": False,
        "hosted_actual_zero_cli_arguments_independently_observed": False,
        "hosted_any_earned_run_created": False,
        "hosted_physical_gamepad_verified": False,
        "strict_original_native_complete_event_accepted": False,
        "release_gate_credit": 0,
        "outcome": "inconclusive_for_release",
    }
