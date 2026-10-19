#!/usr/bin/env python3
"""Recompute the existing QA-01 strict result gates from recorded guest rows.

Source semantics remain in probe_original_event_complete.diagnose. This
secondary read-only validator detects missing/misreported observations; it
neither changes those thresholds nor admits a complete USA event.
"""
from __future__ import annotations

import re

COURSE_RESULT_MENU = {"zoom-zoo": 0xBC, "bowl": 0x18, "switcher": 0x99}
RAW_RESULT_GATES = (
    "both_reached_terminal_menu",
    "rendered_result_and_score_text_matched",
    "intermediate_result_text_matched",
    "stunt_positive_score_visible",
    "timed_race_or_circuit_result_visible",
    "circuit_multiple_lap_decrements_sampled",
    "result_outside_active_race_in_both_guests",
    "circuit_zero_remaining_laps_at_onset_and_stable",
)


def positive_mike_result(lines: list[str], stunt: bool) -> bool:
    """Mirror the original archived MIKE/P1 immediately-following-value rule."""
    pattern = r":\s*[1-9]\d*" if stunt else r"\d+:[0-5]\d\.\d\d"
    for index, line in enumerate(lines):
        if line.strip() == "MIKE":
            if index + 1 >= len(lines):
                return False
            value = lines[index + 1].strip()
            if re.fullmatch(pattern, value) is None:
                return False
            return stunt or any(char in "123456789" for char in value)
    return False


def _capture(report: dict, side: str) -> dict:
    value = report.get(side)
    if not isinstance(value, dict):
        raise ValueError("missing original/native guest capture " + side)
    if not isinstance(value.get("samples"), list) or not value["samples"]:
        raise ValueError("missing source guest sampled game-state rows " + side)
    for phase in ("onset", "result"):
        if not isinstance(value.get(phase), dict):
            raise ValueError("missing source guest terminal capture " + side + "/" + phase)
    texts = value.get("result_text")
    if (not isinstance(texts, dict)
            or not isinstance(texts.get("final"), list)
            or any(not isinstance(item, str) for item in texts["final"])):
        raise ValueError("missing source guest result PPU text " + side)
    return value


def recompute(report: dict) -> dict[str, bool]:
    case = report.get("name")
    if case not in COURSE_RESULT_MENU:
        raise ValueError("non-source-qualified event in raw result gate audit")
    original = _capture(report, "reference")
    native = _capture(report, "native")
    menu = COURSE_RESULT_MENU[case]
    stunt = case == "bowl"
    circuit = case == "zoom-zoo"

    both_terminal = all(
        capture[phase].get("menu") == menu
        for capture in (original, native) for phase in ("onset", "result")
    )
    texts_match = original["result_text"]["final"] == native["result_text"]["final"]
    all_texts_match = original["result_text"] == native["result_text"]
    p1_positive = positive_mike_result(original["result_text"]["final"], stunt)
    scored = not stunt or p1_positive
    timed = stunt or p1_positive

    def sampled_lap_decrements(capture: dict) -> int:
        values = [entry.get("p1_laps") for entry in capture["samples"]]
        return sum(
            type(a) is int and type(b) is int and b < a
            for a, b in zip(values, values[1:])
        )

    lap_evidence = not circuit or (
        sampled_lap_decrements(original) >= 2
        and sampled_lap_decrements(native) >= 2
    )
    settled = all(
        type(capture[phase].get("in_race")) is int
        and capture[phase]["in_race"] != 1
        for capture in (original, native) for phase in ("onset", "result")
    )
    laps_zero = not circuit or all(
        type(capture[phase].get("p1_laps")) is int
        and capture[phase]["p1_laps"] == 0
        for capture in (original, native) for phase in ("onset", "result")
    )
    return dict(zip(RAW_RESULT_GATES, (
        both_terminal, texts_match, all_texts_match, scored, timed,
        lap_evidence, settled, laps_zero,
    )))


def validate(report: dict) -> dict[str, bool]:
    """Reject a producer positive *or negative* contradicting raw guest rows."""
    expected = recompute(report)
    claimed = report.get("comparison")
    if not isinstance(claimed, dict):
        raise ValueError("missing original/native producer result comparison")
    for name, actual in expected.items():
        if claimed.get(name) is not actual:
            raise ValueError(
                "producer result gate " + name +
                " contradicts actual retained original/native guest result observations"
            )
    return expected
