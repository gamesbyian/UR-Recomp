#!/usr/bin/env python3
"""Read-only independent hosted Win32 2P result-to-Records log consistency.

The guest publisher's .urrun/.urmatch bytes are not retained by the current
Windows Actions workflow, so even a positive log triple is NOT independently
decoded paired-run bytes, strict original/native parity or L5 hardware QA.
"""
from __future__ import annotations

import hashlib
import json
import re


SHA256 = re.compile(r"[0-9a-f]{64}\Z")
# The same canonical writer used by native 1P emits bounded timestamp
# and collision suffixes for 2P's checksummed .urrun/.urmatch pair.
# A generic "anything.urrun" is not an independently attributable new pair.
BASENAME = re.compile(r"run-[0-9]{16}-[0-9]{4}\.urrun\Z")
CAPTURE = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_MATCH CAPTURED=1 "
    r"profile1=native-ci-rider profile2=native-ci-second "
    r"course=course:01 frames=(\d+) path=([^\r\n]+)\r?$"
)
RESULT = re.compile(
    r"(?m)^UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p "
    r"race_host=(\d+) result_host=(\d+) riders=(\d+),(\d+) "
    r"hundredths=(\d+),(\d+) winner=(\d+) "
    r"input_frames=(\d+) input_runs=(\d+) published=(\d+)\r?$"
)
JOIN = (
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider ",
    "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
    "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
    "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
    "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
)
RECORDS = (
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider ",
    "UR_BALDOSA_MODERN_ROOT records_page=1p",
    "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected ",
    "UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=1 unavailable=0 selected=1",
    "UR_BALDOSA_MODERN_ROOT records_page=2p",
    "UR_BALDOSA_MODERN_ROOT records_last_2p=",
    "UR_BALDOSA_MODERN_ROOT records_page=1p",
    "UR_BALDOSA_MODERN_ROOT records_closed=1",
)


def unique_ordered(text: str, markers: tuple[str, ...]) -> list[int]:
    positions = []
    after = 0
    for marker in markers:
        # Some pages intentionally reappear when the player backs out.
        loc = text.find(marker, after)
        if loc < 0:
            raise ValueError("native 2P journal lacks required ordered event: " + marker)
        positions.append(loc)
        after = loc + len(marker)
    if len(set(positions)) != len(positions):
        raise ValueError("native 2P journal cannot reuse one line for two events")
    return positions


def audit_hosted_native_2p_records(
    raw_report: bytes, raw_played: bytes, raw_fresh: bytes,
) -> dict[str, object]:
    """Admit a coarchived three-file *log* witness, never an unarchived match."""
    try:
        report = json.loads(raw_report.decode("utf-8"))
        played = raw_played.decode("utf-8")
        fresh = raw_fresh.decode("utf-8")
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("native 2P evidence requires UTF-8 JSON and guest logs") from exc
    if not isinstance(report, dict):
        raise ValueError("native 2P report must be an object")
    required_true = (
        "played_guest_2p_result_published",
        "new_native_process_reopened_paired_2p_records",
        "p2_named_profile_sram_preserved",
    )
    if (
        report.get("scope") != "actual-source-2p-baldosa-modern-records-integration"
        or report.get("p1_profile") != "native-ci-rider"
        or report.get("p2_profile") != "native-ci-second"
        or any(report.get(key) is not True for key in required_true)
        or report.get("original_native_strict_event_pass") is not False
        or report.get("physical_gamepads_tested") is not False
        or type(report.get("release_gate_credit")) is not int
        or report["release_gate_credit"] != 0
    ):
        raise ValueError("native 2P report conflicts with hosted-only product evidence")
    pair = report.get("canonical_match_artifact_sha256")
    if not isinstance(pair, dict) or len(pair) != 2:
        raise ValueError("native 2P report lacks exactly two paired artifact hashes")
    run_names = [
        name for name in pair
        if isinstance(name, str) and BASENAME.fullmatch(name)
    ]
    if len(run_names) != 1 or set(pair) != {
        run_names[0], run_names[0] + ".urmatch"
    } or any(
        not isinstance(value, str) or not SHA256.fullmatch(value)
        for value in pair.values()
    ):
        raise ValueError("native 2P report's run/sidecar hash pair is invalid")
    observed = report.get("source_result")
    needed = (
        "source_result_host", "source_input_frames", "p1_hundredths",
        "p2_hundredths", "winner",
    )
    if not isinstance(observed, dict) or any(
        type(observed.get(field)) is not int for field in needed
    ):
        raise ValueError("native 2P source result fields are missing or noninteger")

    if any(played.count(key) != 1 for key in JOIN):
        raise ValueError("native 2P played log lacks unique joined source entry")
    early = unique_ordered(played, JOIN)
    captures, results = list(CAPTURE.finditer(played)), list(RESULT.finditer(played))
    if len(captures) != 1 or len(results) != 1:
        raise ValueError("native 2P played log lacks one authoritative pair/result")
    c, r = captures[0], results[0]
    first, last, p1, p2, t1, t2, winner, frames, runs, published = (
        int(value) for value in r.groups()
    )
    correct_winner = 0 if t1 == t2 else (1 if t1 < t2 else 2)
    # The producer advertises an exact two-file pair. The native capture
    # must have written THAT same canonical .urrun, not an unrelated
    # successful run whose stored digest happens to appear in a JSON report.
    captured_path = c[2].replace("\\", "/")
    captured_name = captured_path.rsplit("/", 1)[-1]
    source_capture_bound = (
        int(c[1]) == frames
        and captured_name == run_names[0]
        and re.match(r"^[A-Za-z]:/", captured_path) is not None
        and "/multiplayer-runs/" in captured_path.lower()
        and "/../" not in captured_path and "/./" not in captured_path
    )
    if (
        not source_capture_bound
        or not (0 < first < last)
        or (p1, p2) != (0, 2)
        or not (0 < t1 <= 60000 and 0 < t2 <= 60000)
        or (t1 == 60000 and t2 == 60000)
        or winner != correct_winner or published != 1
        or frames <= 0 or runs <= 0
        or not (early[-1] < c.start() < r.start())
        or int(c[1]) <= 0
        or observed["source_result_host"] != last
        or observed["source_input_frames"] != frames
        or observed["p1_hundredths"] != t1
        or observed["p2_hundredths"] != t2
        or observed["winner"] != winner
        or any(key in played for key in (
            "UR_BALDOSA_NATIVE_MATCH SAVE_PENDING=1",
            "UR_BALDOSA_NATIVE_MATCH PUBLISH_REJECTED",
            "UR_BALDOSA_NATIVE_MATCH NOT_SAVED=1",
        ))
    ):
        raise ValueError("native 2P result/participant/hash receipt chronology inconsistent")
    if (
        played.count("UR_BALDOSA_NATIVE_MATCH CAPTURED=1") != 1
        or played.count("UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p") != 1
    ):
        raise ValueError("native 2P publisher emitted duplicate or ambiguous credit")

    unique_ordered(fresh, RECORDS)
    last_lines = re.findall(
        r"(?m)^UR_BALDOSA_MODERN_ROOT records_last_2p=([^\r\n]+)\r?$", fresh
    )
    # Records are displayed from the SELECTED P1 profile's perspective.
    # Cross-check the exact player-visible result text against the original
    # native settled result, including WIN/LOSS/DRAW and DNF formatting.
    # A log containing "source=historical_paired_archive" is not enough:
    # an incorrect outcome or an opponent's time must fail independent QA.
    p1_outcome = "DRAW" if winner == 0 else ("WIN" if winner == 1 else "LOSS")
    p1_clock = (
        "DNF" if t1 >= 60000
        else f"{t1 // 6000:02d}:{(t1 // 100) % 60:02d}.{t1 % 100:02d}"
    )
    expected_display = (
        f"LAST 01 {p1_outcome} {p1_clock} "
        "source=historical_paired_archive"
    )
    if (
        len(last_lines) != 1
        or last_lines[0] != expected_display
        or len(re.findall(
            r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
            r"profile=native-ci-rider bytes=8192\b", fresh
        )) != 1
        or fresh.count("UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=1 ") != 1
        or any(key in fresh for key in (
            "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
            "UR_BALDOSA_NATIVE_RESULT observed=1",
            "UR_BALDOSA_NATIVE_MATCH SAVE_PENDING=1",
        ))
    ):
        raise ValueError("native 2P fresh-game Records log lacks unique read-only pair")
    return {
        "hosted_native_2p_result_to_fresh_records_logs_consistent": True,
        "hosted_native_2p_source_riders": [p1, p2],
        "hosted_native_2p_source_times_hundredths": [t1, t2],
        "hosted_native_2p_source_winner": winner,
        "hosted_native_2p_result_host_frame": last,
        "hosted_native_2p_saved_run_capture_basename": captured_name,
        "hosted_native_2p_player1_records_display_verified": expected_display,
        "hosted_new_2p_pair_sha256_producer_reported": dict(pair),
        "hosted_native_2p_report_sha256": hashlib.sha256(raw_report).hexdigest(),
        "hosted_native_2p_played_log_sha256": hashlib.sha256(raw_played).hexdigest(),
        "hosted_native_2p_fresh_log_sha256": hashlib.sha256(raw_fresh).hexdigest(),
        "hosted_saved_2p_pair_bytes_independently_reopened": False,
        "hosted_original_emulator_2p_parity_accepted": False,
        "hosted_physical_gamepads_verified": False,
    }
