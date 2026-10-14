#!/usr/bin/env python3
"""Independent bounded 3-game Windows source-LOG review of new MIKE/ANDREW P2.

The in-flight product #1490's CI artifact is currently RED/absent. This
consumer is deliberately prospective. Stock 2P menu entry is not source GO,
a settled match, fresh Records, physical buttons or original parity.
"""
from __future__ import annotations

import hashlib
import json
import re

from check_baldosa_win32_first_racer_evidence import SOURCE

MAX_LOG = 2 * 1024 * 1024
MAX_REPORT = 64 * 1024
BOOT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
    r"profile=mike bytes=8192 fnv=([0-9a-fA-F]{8})\r?$"
)
SECOND = (
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
    "UR_BALDOSA_MODERN_ROOT opened=1",
    "UR_BALDOSA_MODERN_ROOT second_racer_opened=1 preset=1 activation=next_process",
    "UR_BALDOSA_NATIVE_SECOND_RACER status=0 preset=1 id=andrew activation=next_process",
    "UR_BALDOSA_MODERN_ROOT second_racer_created=1 activation=next_process",
)
THIRD = (
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
    "UR_BALDOSA_MODERN_ROOT opened=1",
    "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared",
    "UR_BALDOSA_MODERN_ROOT selected=2",
    "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
    "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
    "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
    "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
    "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
)
NO_RESULT = (
    "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
    "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
    "UR_BALDOSA_NATIVE_RESULT observed=1",
    "UR_BALDOSA_MODERN_ROOT records_opened=1",
)
NO_UNBOUND = (
    "UR_BALDOSA_MODERN_ROOT join_unavailable=1",
    "UR_BALDOSA_MODERN_ROOT unbound_2p_consented=1",
    "UR_BALDOSA_MODERN_ROOT stock_rejected=",
    "UR_BALDOSA_MODERN_ROOT second_racer_created=0",
)



def ordered_exact_source_lines(log: str, markers: tuple[str, ...], label: str) -> None:
    """Admit only complete, individual native log lines in source order.

    A copied marker in a comment, quoted diagnostic, truncated line or a
    different source event must not stand in for an emitted Win32 receipt.
    LF and CRLF are both legitimate native Windows log formats.
    """
    lines = log.splitlines()
    positions = []
    for marker in markers:
        exact = [i for i, line in enumerate(lines) if line == marker]
        shadowed = [i for i, line in enumerate(lines)
                    if marker in line and line != marker]
        if len(exact) != 1 or shadowed:
            raise ValueError(f"{label} missing, duplicate or shadowed native line: {marker}")
        positions.append(exact[0])
    if positions != sorted(positions):
        raise ValueError(f"{label} native lines out of source order")

def audit_win32_second_created_racer_go(
    raw_report: bytes, raw_first: bytes, raw_second: bytes, raw_third: bytes,
) -> dict[str, object]:
    for raw, bound in (
        (raw_report, MAX_REPORT), (raw_first, MAX_LOG),
        (raw_second, MAX_LOG), (raw_third, MAX_LOG),
    ):
        if type(raw) is not bytes or not 0 < len(raw) <= bound:
            raise ValueError("missing or oversized source-owned Win32 second-racer group")
    try:
        report = json.loads(raw_report.decode("utf-8"))
        first, second, third = (
            x.decode("utf-8") for x in (raw_first, raw_second, raw_third)
        )
    except (ValueError, UnicodeError) as exc:
        raise ValueError("second-racer source group is not UTF-8 JSON/text") from exc
    if (
        not isinstance(report, dict)
        or report.get("scope") != "native-real-first-p1-created-p2-then-both-seats-stock-go"
        or report.get("P1_source_profile") != "mike"
        or report.get("P2_source_profile") != "andrew"
        or report.get("original_p1_selector_unchanged") is not True
        or type(report.get("P2_canonical_raw_bytes")) is not int
        or report["P2_canonical_raw_bytes"] != 8192
        or type(report.get("P2_source_rider")) is not int
        or report["P2_source_rider"] != 1
        or report.get("third_native_process_two_named_seats_confirmed") is not True
        or report.get("actual_stock_two_player_go") is not True
        or report.get("completed_two_player_result") is not False
        or report.get("reopened_paired_records") is not False
        or report.get("strict_original_native_event_pass") is not False
        or report.get("physical_gamepad_acceptance") is not False
        or type(report.get("release_gate_credit")) is not int
        or report["release_gate_credit"] != 0
    ):
        raise ValueError("second-racer source report contains unsupported release or identity claim")

    ordered_exact_source_lines(first, SOURCE, "first anonymous P1 creation guest")
    if (
        first.count("UR_BALDOSA_MODERN_ROOT opened=1") != 1
        or any(word in first for word in NO_RESULT + (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=",
            "UR_BALDOSA_NATIVE_SECOND_RACER status=0",
            "UR_BALDOSA_MODERN_ROOT stock_entered",
        ))
    ):
        raise ValueError("first P1 creation guest hot-swapped or played stock race")

    ordered_exact_source_lines(second, SECOND, "named P1 creates isolated P2")
    second_boot = list(BOOT.finditer(second))
    if (
        len(second_boot) != 1
        or not second.index(SECOND[0]) < second_boot[0].start() < second.index(SECOND[1])
        or second.count("UR_BALDOSA_MODERN_ROOT opened=1") != 1
        or any(word in second for word in NO_RESULT + NO_UNBOUND + (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew",
            "UR_BALDOSA_MODERN_ROOT first_racer_created=1",
            "UR_BALDOSA_MODERN_ROOT stock_entered",
        ))
    ):
        raise ValueError("P2 creation guest lacks selected MIKE boot or hot-swapped/raced")
    ordered_exact_source_lines(third, THIRD, "two named profiles join native stock 2P")
    third_boot = list(BOOT.finditer(third))
    if (
        len(third_boot) != 1
        or not third.index(THIRD[0]) < third_boot[0].start() < third.index(THIRD[1])
        or third.count("UR_BALDOSA_MODERN_ROOT opened=1") != 1
        or any(word in third for word in NO_RESULT + NO_UNBOUND + (
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew",
            "UR_BALDOSA_MODERN_ROOT second_racer_created=1",
            "UR_BALDOSA_MODERN_ROOT first_racer_created=1",
        ))
    ):
        raise ValueError("third fresh game lacks source-ordered P1 boot/two-seat stock path")

    return {
        "scope": "hosted-win32-three-game-first-created-p1-p2-stock-handoff-logs-only",
        "hosted_new_mike_and_andrew_to_two_seat_stock_entry_logs_consistent": True,
        "hosted_named_p1_during_p2_creation_boot_fnv_observed": second_boot[0].group(1).lower(),
        "hosted_fresh_two_seat_game_p1_boot_fnv_observed": third_boot[0].group(1).lower(),
        "hosted_first_guest_sha256": hashlib.sha256(raw_first).hexdigest(),
        "hosted_second_guest_sha256": hashlib.sha256(raw_second).hexdigest(),
        "hosted_third_guest_sha256": hashlib.sha256(raw_third).hexdigest(),
        "hosted_producer_report_sha256": hashlib.sha256(raw_report).hexdigest(),
        "hosted_p2_catalog_and_sram_bytes_independently_rehashed": False,
        "hosted_original_guest_stock_two_player_go_barrier_independently_observed": False,
        "hosted_actual_two_player_settled_result": False,
        "hosted_earned_2p_match_reopened_in_fresh_records": False,
        "hosted_physical_two_pad_accepted": False,
        "strict_original_native_complete_event_accepted": False,
        "release_gate_credit": 0,
        "outcome": "inconclusive_for_release",
    }
