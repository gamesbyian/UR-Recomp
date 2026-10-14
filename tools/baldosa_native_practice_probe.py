#!/usr/bin/env python3
"""Actual native Windows P1 Quick Practice -> original Dragster source course.

The shipping Baldosa root handles P1 semantic Down/A/A. The stock guest then
consumes ONLY existing product-queued menu masks under QuickPracticeLaunch.
A source decoded-course identity and genuine in-race GO must authorize the
1P handoff; synthetic test input never writes guest memory or creates results.

Not physical gamepad acceptance, full 45-course eligibility or release credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from baldosa_native_first_racer_probe import run_game
from baldosa_windows_native_pause_route import USA_SHA256, sha256


def require_native_practice_source(log: str) -> None:
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT practice_gamepad=DOWN",
        "UR_BALDOSA_MODERN_ROOT practice_opened=1 available=1 "
        "course=0 source_menu_required=1",
        "UR_BALDOSA_MODERN_ROOT practice_gamepad=A",
        "UR_BALDOSA_MODERN_ROOT practice_requested=1 course=0 "
        "name=DRAGSTER source_route=stock",
        "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=0 "
        "original_course=1 race=1 source_identity=verified",
    )
    for part in stages:
        if part not in log:
            raise ValueError("Missing native original course or controller stage: " + part)
    first = log.index(stages[2])
    opened = log.index(stages[3])
    first_a = log.index(stages[4])
    requested = log.index(stages[5])
    admitted = log.index(stages[6])
    if not first < opened < first_a < requested < admitted:
        raise ValueError("Practice source stages were reordered")
    if log.count("UR_BALDOSA_MODERN_ROOT practice_gamepad=") != 3 or (
            log.count("UR_BALDOSA_MODERN_ROOT practice_gamepad=A") != 2 or
            log.count(stages[6]) != 1):
        raise ValueError("Practice did not use exact real native P1 button edges")
    if any(part in log for part in (
        "UR_BALDOSA_MODERN_ROOT practice_rejected=",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=",
        "UR_BALDOSA_NATIVE_RESULT observed=1",
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=",
    )):
        raise ValueError("Practice route bypassed a source gate or forged Records")


def run(exe: Path, rom: Path, out: Path,
        *, timeout: int, video: str) -> dict[str, object]:
    for path in (exe, rom):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing/redirected actual native Practice runner")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Practice guest must be pinned USA retail ROM")
    out.mkdir(parents=True, exist_ok=False)
    user = out / "Fresh Practice Source Guest"
    user.mkdir()
    # Original stock 1P tour/racer/track/Now Playing inputs are intentionally
    # ABSENT. The existing Modern product route must supply them after the
    # two user-confirmed P1 modal A edges and source menu observations.
    log = run_game(
        exe, rom, user, out / "game1_practice_stock_dragster", "11",
        "turbo on\n"
        "until16 0053 == F60C\n"
        "wait 900\n"
        "until16 0053 == 8610\n"
        "until 0E1F != 00\n"
        "dump source_practice_go\n"
        "quit\n",
        video, timeout)
    require_native_practice_source(log)
    return {
        "scope": "one-real-native-windows-p1-practice-first-course",
        "source_course": "Dragster",
        "source_course_index": 1,
        "p1_gamepad_handler_presses": ["DOWN", "A", "A"],
        "original_stock_menu_inputs_from_source_product_route": True,
        "original_decoded_course_observed_in_race": True,
        "source_go_timer_observed": True,
        "other_44_native_courses_admitted": False,
        "physical_gamepad_certified": False,
        "full_event_parity_or_release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=220)
    args = parser.parse_args()
    report = run(args.exe.resolve(), args.rom.resolve(), args.out.resolve(),
                 timeout=args.timeout, video=args.video)
    (args.out.resolve() / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: actual Windows native P1 Practice source Dragster GO; "
          "45-course availability and physical hardware remain unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
