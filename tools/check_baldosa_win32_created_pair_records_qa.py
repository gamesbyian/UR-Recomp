#!/usr/bin/env python3
"""Independent read-only source-log admission for native-created 0/2 2P pair.

Require five DIFFERENT Windows guest process logs: native frontend creation
of MIKE and MARTIN, real source-settled original 2P Race and independent
fresh-game MIKE/MARTIN read-only Records. The existing-P2 selector is a
test-only backend caller; raw .urrun/.urmatch bytes are not in this contract.
Synthetic unit fixtures must NEVER count as release acceptance.
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
    SECOND, THIRD, BOOT, ordered_exact_source_lines,
)

MAX_LOG = 2 * 1024 * 1024
MAX_REPORT = 64 * 1024
PREFIX = "UR Baldosa Win32 Pause Route/native_player_created_2p_records/"
FILES = (
    "report.json", "first_P1_mike/log.txt", "named_P1_adds_P2/log.txt",
    "played_native_2p/log.txt", "fresh_mike_records/log.txt",
    "fresh_martin_records/log.txt",
)
UI_FILES = FILES[:-1] + ("mike_ui_selects_martin/log.txt", FILES[-1])
RECEIPT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p "
    r"race_host=(\d+) result_host=(\d+) riders=(\d+),(\d+) "
    r"hundredths=(\d+),(\d+) winner=(\d+) "
    r"input_frames=(\d+) input_runs=(\d+) published=(\d+)\r?$"
)
MATCH = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_MATCH CAPTURED=1 profile1=mike "
    r"profile2=martin course=course:01 frames=(\d+) path=([^\r\n]+\.urrun)\r?$"
)
VIEW = re.compile(
    r"(?m)^UR_BALDOSA_MODERN_ROOT records_last_2p=LAST 01 "
    r"(WIN|LOSS|DRAW) (\d\d:\d\d\.\d\d) source=historical_paired_archive\r?$"
)
ROOT = re.compile(
    r"(?m)^\[Launcher\] Config/saves anchored to '([^'\r\n]+)'\.\r?$"
)
HEX = re.compile(r"[a-f0-9]{64}\Z")
BOOT_NAME = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
    r"profile=(mike|martin) bytes=8192 fnv=([0-9a-fA-F]{8})\r?$"
)
WAIT = re.compile(r"(?m)^script f=(\d+) until 00053 ok after (\d+) frames\r?$")
TICKER = re.compile(r"(?m)^script f=(\d+) until 00E1F ok after (\d+) frames\r?$")
GO = re.compile(r"(?m)^script f=(\d+) dump go ok\r?$")
NO_CREATION_RESULT = (
    "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
    "UR_BALDOSA_NATIVE_RESULT observed=1",
    "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
)


def require(value: bool, problem: str) -> None:
    if not value:
        raise ValueError("created-player source 2P QA: " + problem)


def sole(regex: re.Pattern, log: str, source: str) -> re.Match:
    matches = list(regex.finditer(log))
    require(len(matches) == 1, "missing/duplicate " + source)
    return matches[0]


def positive_integer(value: object) -> bool:
    return type(value) is int and value > 0


def clock(hundredths: int) -> str:
    return f"{hundredths // 6000:02d}:{(hundredths // 100) % 60:02d}.{hundredths % 100:02d}"


def read_source_evidence_zip(path: Path, *, require_ui: bool = False) -> tuple[bytes, ...]:
    require(path.is_file() and not path.is_symlink() and
            0 < path.stat().st_size <= 8 * 1024 * 1024,
            "unsafe or missing evidence archive")
    with zipfile.ZipFile(path) as archive:
        names = [entry.filename for entry in archive.infolist()]
        require(len(names) == len(set(names)), "duplicate ZIP name")
        buffers = []
        for part in (UI_FILES if require_ui else FILES):
            key = PREFIX + part
            require(key in names, "incomplete original five-process source group: " + key)
            info = archive.getinfo(key)
            limit = MAX_REPORT if part.endswith("report.json") else MAX_LOG
            require(0 < info.file_size <= limit and
                    ((info.external_attr >> 16) & 0o170000) != 0o120000,
                    "oversized/linked archive member: " + key)
            buffers.append(archive.read(key))
        return tuple(buffers)


def audit(raw_report: bytes, *raw_logs: bytes) -> dict[str, object]:
    require(type(raw_report) is bytes and 0 < len(raw_report) <= MAX_REPORT and
            len(raw_logs) in (5, 6), "missing producer report or process")
    require(all(type(x) is bytes and 0 < len(x) <= MAX_LOG for x in raw_logs),
            "non-source or oversized Win32 process log")
    try:
        report = json.loads(raw_report.decode("utf-8"))
        logs = [x.decode("utf-8") for x in raw_logs]
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid Win32 native five-process evidence encoding") from exc
    ui = len(raw_logs) == 6
    expected_report_fields = {
        "scope", "actual_frontend_created_profiles", "observed_stock_riders",
        "observed_source_guest_result", "canonical_one_pair_sha256",
        "fresh_native_records_for_each",
        "p2_existing_profile_select_via_fixture_not_player_UI",
        "native_existing_p1_profile_selector_UI_proved",
        "physical_pad_hardware_accepted", "original_native_strict_event_accepted",
        "release_gate_credit",
    }
    anonymous_source_fields = {
        "anonymous_first_boot_sram_present",
        "anonymous_bootstrap_bytes_unchanged_by_all_named_games",
    }
    if ui or (type(report) is dict and
              bool(anonymous_source_fields & set(report))):
        expected_report_fields |= anonymous_source_fields
    require(type(report) is dict and set(report) == expected_report_fields,
            "unexpected producer report claim or missing canonical field")
    require(type(report) is dict and
            report.get("scope") ==
            ("two-native-ui-created-players-played-source-2p-and-both-ui-selected-records"
             if ui else
             "two-native-controller-created-profiles-played-source-2p-and-both-records") and
            report.get("actual_frontend_created_profiles") == ["mike", "martin"] and
            report.get("observed_stock_riders") == [0, 2] and
            report.get("fresh_native_records_for_each") is True and
            report.get("p2_existing_profile_select_via_fixture_not_player_UI") is (not ui) and
            report.get("native_existing_p1_profile_selector_UI_proved") is ui and
            report.get("physical_pad_hardware_accepted") is False and
            report.get("original_native_strict_event_accepted") is False and
            type(report.get("release_gate_credit")) is int and
            report["release_gate_credit"] == 0,
            "producer report claimed new riders, profile UI or release gate")
    if anonymous_source_fields <= set(report):
        require(type(report["anonymous_first_boot_sram_present"]) is bool and
                report["anonymous_bootstrap_bytes_unchanged_by_all_named_games"] is True,
                "anonymous legacy boot source preservation not attested")
    if ui:
        first, second, played, mike_view, ui_switch, martin_view = logs
    else:
        first, second, played, mike_view, martin_view = logs

    # All five must use the EXACT SAME independently created OS user root.
    roots = [sole(ROOT, log, "per-user Windows root").group(1) for log in logs]
    root = PureWindowsPath(roots[0])
    require(all(x == roots[0] for x in roots) and root.is_absolute() and
            ".." not in root.parts and
            "New Player-Created Named Racers" in root.parts,
            "different/relative/traversing user root across guest processes")
    ordered_exact_source_lines(first, SOURCE, "genuine anonymous P1 creation")
    require("UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1" in first and
            not any(x in first for x in NO_CREATION_RESULT),
            "P1 first game was provisioned or raced")
    ordered_exact_source_lines(second, SECOND[:3] + ("UR_BALDOSA_MODERN_ROOT second_racer_preset=2", SECOND[3].replace("preset=1", "preset=2").replace("id=andrew", "id=martin"), SECOND[4]), "P1 creates separate MARTIN P2")
    require(not any(x in second for x in NO_CREATION_RESULT) and
            len(list(BOOT.finditer(second))) == 1,
            "P2 was hot swapped or race-published")
    ordered_exact_source_lines(played, THIRD, "separately created P1/P2 guest race")
    joined_one = "UR_BALDOSA_MODERN_ROOT synthetic_join_edge seat=1"
    joined_two = "UR_BALDOSA_MODERN_ROOT synthetic_join_edge seat=2"
    require(played.count(joined_one) == played.count(joined_two) == 1 and
            played.index("UR_BALDOSA_MODERN_ROOT join_confirmed seat=1") <
            played.index(joined_one) <
            played.index("UR_BALDOSA_MODERN_ROOT join_confirmed seat=2") <
            played.index(joined_two) <
            played.index("UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d"),
            "virtual pad smoke route did not confirm source-owned seats in order")
    require(len(list(BOOT.finditer(played))) == 1,
            "MIKE's named native 2P guest boot was not observed")
    require(not any(x in played for x in (
        "UR_BALDOSA_MODERN_ROOT join_unavailable=1",
        "UR_BALDOSA_MODERN_ROOT unbound_2p_consented=1",
        "UR_BALDOSA_NATIVE_MATCH SAVE_PENDING=1",
        "UR_BALDOSA_NATIVE_MATCH PUBLISH_REJECTED",
        "script until timed out",
    )), "unbound or incomplete native 2P result")
    wait, ticker, go = (
        list(WAIT.finditer(played)),
        list(TICKER.finditer(played)),
        list(GO.finditer(played)),
    )
    require(len(wait) == 2 and len(ticker) == len(go) == 1 and
            wait[0].start() < played.index(THIRD[-1]) < wait[1].start() <
            ticker[0].start() < go[0].start() and
            0 < int(wait[0][1]) < int(wait[1][1]) < int(ticker[0][1]) and
            int(ticker[0][1]) == int(go[0][1]),
            "original guest NMI/GO script wait barrier absent")
    source = sole(RECEIPT, played, "genuine scored 2P source result")
    scored = tuple(int(x) for x in source.groups())
    race_host, result_host, p1, p2, t1, t2, winner, frames, runs, published = scored
    require(race_host > 0 and result_host > int(go[0][1]) and
            result_host > race_host and
            (p1, p2) == (0, 2) and
            t1 <= 60000 and t2 <= 60000 and
            winner in (0, 1, 2) and
            frames > 0 and runs > 0 and published == 1,
            "source result did not settle with new 0/2 player identities")
    match = sole(MATCH, played, "single source-owned paired .urrun")
    require(int(match[1]) == frames and match.end() < source.start() and
            match.start() > played.index(THIRD[-1]),
            "one source match could not be tied to played guest result")
    run = PureWindowsPath(match[2])
    require(run.is_absolute() and ".." not in run.parts and
            run.parent.name == "multiplayer-runs" and
            run.parent.parent == root and
            run.suffix == ".urrun" and run.name.startswith("run-"),
            "match published to untrusted path or name")
    term = list(re.finditer(r"(?m)^script f=(\d+) quit\r?$", played))
    require(len(term) == 1 and term[0].start() > source.end()
            and int(term[0][1]) >= result_host,
            "source race quit or finished before captured scored event")
    observed = report.get("observed_source_guest_result")
    require(type(observed) is dict and
            observed == {
                "source_result_host": result_host,
                "source_input_frames": frames,
                "p1_hundredths": t1, "p2_hundredths": t2,
                "winner": winner,
            }, "reported scored event does not match real native result log")
    pair = report.get("canonical_one_pair_sha256")
    require(type(pair) is dict and len(pair) == 2 and
            set(pair) == {run.name, run.name + ".urmatch"} and
            all(type(v) is str and HEX.fullmatch(v) for v in pair.values()),
            "missing canonical single pair hash report")

    if ui:
        stages = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
            "UR_BALDOSA_MODERN_ROOT opened=1",
            "UR_BALDOSA_MODERN_ROOT existing_p1_opened=1 from=mike to=martin activation=next_process",
            "UR_BALDOSA_NATIVE_P1_SWITCH status=0 from=mike to=martin activation=next_process",
            "UR_BALDOSA_MODERN_ROOT existing_p1_saved=1 activation=next_process",
            "UR_BALDOSA_MODERN_ROOT existing_p1_closed=1",
            "UR_BALDOSA_MODERN_ROOT existing_p1_stale_race_blocked=1",
        )
        ordered_exact_source_lines(ui_switch, stages, "real next-boot MARTIN UI selector")
        boot = sole(BOOT_NAME, ui_switch, "selected MIKE guest before MARTIN switch")
        require(boot[1] == "mike" and ui_switch.index(stages[1]) <
                boot.start() < ui_switch.index(stages[2]),
                "native controller profile switch hot-swapped current running guest")
        edges = list(re.finditer(
            r"(?m)^UR_BALDOSA_MODERN_ROOT synthetic_p1_switch_gamepad=(\\d+)\\r?$",
            ui_switch,
        ))
        require([edge[1] for edge in edges] == ["2", "0", "1", "0"]
                and ui_switch.index(stages[2]) < edges[0].start() <
                ui_switch.index(stages[3]) <
                ui_switch.index(stages[4]) < edges[1].start() <
                ui_switch.index(stages[5]) < edges[2].start() <
                edges[3].start() < ui_switch.index(stages[6])
                and "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=martin" not in ui_switch
                and "UR_BALDOSA_MODERN_ROOT stock_entered players=" not in ui_switch
                and not any(x in ui_switch for x in NO_CREATION_RESULT)
                and "UR_BALDOSA_NATIVE_PROFILE PREFLIGHT_REJECTED status=3" in ui_switch,
                "controller switch lacked source-real X/A/B/A order or next-boot stale safety")
    for profile, log, cents, seat in (
        ("mike", mike_view, t1, 1),
        ("martin", martin_view, t2, 2),
    ):
        ordered_exact_source_lines(
            log, (f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile} "
                  f"root=saves/profile-{profile}",
                  "UR_BALDOSA_MODERN_ROOT opened=1",
                  "UR_BALDOSA_MODERN_ROOT selected=3",
                  "UR_BALDOSA_MODERN_ROOT records_page=2p",
                  "UR_BALDOSA_MODERN_ROOT records_closed=1"),
            "fresh named source read-only " + profile,
        )
        boots = list(BOOT_NAME.finditer(log))
        require(len(boots) == 1 and boots[0][1] == profile,
                "fresh Records process booted incorrect player")
        require(log.count("UR_BALDOSA_MODERN_ROOT records_opened=1 "
                          "profile=selected") == 1 and
                log.count("UR_BALDOSA_MODERN_ROOT matches_readonly=1 "
                          "paired=1 unavailable=0 selected=1") == 1 and
                log.count("UR_BALDOSA_MODERN_ROOT records_page=1p") == 2 and
                log.count("UR_BALDOSA_MODERN_ROOT records_page=2p") == 1 and
                not any(x in log for x in NO_CREATION_RESULT),
                "fresh record was duplicated, unavailable or created in viewer")
        # Require the matching participant's own clock and mirror WIN/LOSS,
        # not merely 'paired=1' from an unrelated historical match.
        view = sole(VIEW, log, "participant-specific match outcome")
        expected_result = "DRAW" if winner == 0 else (
            "WIN" if winner == seat else "LOSS")
        require(view[1] == expected_result and view[2] == clock(cents),
                "fresh record display swapped winner, profile or time")
        first_page = log.find("UR_BALDOSA_MODERN_ROOT records_page=1p")
        second_page = log.find(
            "UR_BALDOSA_MODERN_ROOT records_page=1p", first_page + 1)
        opened = log.index("UR_BALDOSA_MODERN_ROOT records_opened=1 ")
        matched = log.index("UR_BALDOSA_MODERN_ROOT matches_readonly=1 ")
        last_page = log.index("UR_BALDOSA_MODERN_ROOT records_page=2p")
        closed = log.index("UR_BALDOSA_MODERN_ROOT records_closed=1")
        require(0 <= first_page < opened < matched < last_page <
                view.start() < second_page < closed,
                "view was not rendered in chronological read-only Records pages")

    require(all("SDL reports 0 joystick(s)" in log and "audio=dummy" in log
                for log in logs),
            "historical CI's synthetic pad/dummy audio scope not explicit")
    return {
        "source_scope": (
            "hosted-native-six-game-new-mike-martin-0-2-result-and-both-real-ui-views"
            if ui else
            "hosted-native-five-game-new-mike-martin-0-2-result-and-both-views"
        ),
        "first_p1_and_p2_created_in_distinct_native_processes": True,
        "genuine_played_source_result_published": True,
        "source_rider_pair": [0, 2],
        "scored_source_winner": winner,
        "scored_source_hundredths": [t1, t2],
        "source_result_host": result_host,
        "fresh_mike_and_martin_records_display_source_consistent": True,
        "reported_one_pair_digests": pair,
        "archived_run_and_match_bytes_independently_verified": False,
        "per_user_catalog_and_SRAM_bytes_independently_verified": False,
        "martin_selection_via_backend_fixture_not_shipping_UI": not ui,
        "martin_selection_via_real_native_ui_controller_semantics": ui,
        "real_physical_2p_controllers_or_audio_verified": False,
        "original_emulator_vs_native_scored_event_parity_verified": False,
        "original_USA_course_release_credit": 0,
        "release_gate_credit": 0,
        "report_sha256": hashlib.sha256(raw_report).hexdigest(),
        "native_process_log_sha256": [
            hashlib.sha256(x).hexdigest() for x in raw_logs],
        "outcome": "hosted_integrated_scored_pair_consistent_not_release_accepted",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--require-real-selector-ui", action="store_true")
    args = parser.parse_args()
    result = audit(*read_source_evidence_zip(
        args.evidence, require_ui=args.require_real_selector_ui))
    require(result["martin_selection_via_real_native_ui_controller_semantics"]
            is args.require_real_selector_ui,
            "requested real native UI source evidence was not present")
    result["outer_runtime_archive_sha256"] = hashlib.sha256(
        args.evidence.read_bytes()).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
