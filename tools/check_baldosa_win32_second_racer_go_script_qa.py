#!/usr/bin/env python3
"""Independently bind logged Win32 guest GO-script waits to stock source code.

The #1498 four-file consumer covers frontend creation and joined stock entry.
This read-only second stage recognizes observed native script wait receipts.
No original-emulator execution, raw WRAM readback, scored result or L4/L5
release gate is inferred from scripted smoke input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from check_baldosa_win32_second_racer_go_qa import (
    audit_win32_second_created_racer_go,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/baldosa_windows_native_pause_route.py"
PREFIX = "UR Baldosa Win32 Pause Route/native_real_second_racer/"
FILES = (
    "report.json",
    "first_P1_mike/log.txt",
    "named_P1_adds_P2/log.txt",
    "fresh_two_seat_source_go/log.txt",
)
MAX_ARCHIVE_BYTES = 8 * 1024 * 1024

# The CLI script prints the same source address for its two DIFFERENT
# conditions. In the original 2P route: title readiness F60C first,
# live race NMI readiness 8610 second, then guest GO ticker 0E1F != 0.
MENU_WAIT = re.compile(
    r"(?m)^script f=(\d+) until 00053 ok after (\d+) frames\r?$"
)
GO_WAIT = re.compile(
    r"(?m)^script f=(\d+) until 00E1F ok after (\d+) frames\r?$"
)
GO_DUMP = re.compile(r"(?m)^script f=(\d+) dump go ok\r?$")
QUIT = re.compile(r"(?m)^script f=(\d+) quit\r?$")
SOURCE_TOKENS = (
    '"until16 0053 == F60C"',
    '"until16 0053 == 8610"',
    '"until 0E1F != 00"',
    '"dump go"',
    '"quit"',
)


def audited_source_function(raw_source: bytes) -> str:
    if type(raw_source) is not bytes or not 0 < len(raw_source) <= 256 * 1024:
        raise ValueError("source script missing or unbounded")
    try:
        source = raw_source.decode("utf-8")
        start = source.index("def native_modern_race_entry_script(")
        end = source.index("\ndef run_native_modern_race_entry(", start)
        function = source[start:end]
    except (UnicodeError, ValueError) as exc:
        raise ValueError("no bounded stock native guest GO script authority") from exc
    positions = []
    for token in SOURCE_TOKENS:
        if function.count(token) != 1:
            raise ValueError("original source GO control is missing or duplicated: " + token)
        positions.append(function.index(token))
    if positions != sorted(positions):
        raise ValueError("stock source guest script reordered its GO barriers")
    return hashlib.sha256(raw_source).hexdigest()


def audit_guest_script(
    report: bytes, first: bytes, second: bytes, third: bytes, source: bytes,
) -> dict[str, object]:
    result = audit_win32_second_created_racer_go(report, first, second, third)
    source_digest = audited_source_function(source)
    try:
        log = third.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("not a UTF-8 native guest source log") from exc
    menu, ticker, dumped, quit = (
        list(regex.finditer(log))
        for regex in (MENU_WAIT, GO_WAIT, GO_DUMP, QUIT)
    )
    # Every successful original guest condition must be observed exactly
    # once, except for $0053, where title and race are different assertions.
    if tuple(map(len, (menu, ticker, dumped, quit))) != (2, 1, 1, 1):
        raise ValueError("native stock GO script lacks its two menu, one ticker, dump and exit receipts")
    title, race = menu
    tick, dump, end = ticker[0], dumped[0], quit[0]
    source_entry = "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d"
    if (
        not (log.index(source_entry) < race.start() < tick.start() <
             dump.start() < end.start())
        or title.start() >= race.start()
        or not (0 < int(title[1]) < int(race[1]) < int(tick[1]))
        or int(title[2]) <= 0 or int(race[2]) <= 0 or int(tick[2]) <= 0
        or int(tick[1]) != int(dump[1]) or int(dump[1]) != int(end[1])
        or "SDL reports 0 joystick(s)" not in log
        or "audio=dummy" not in log
    ):
        raise ValueError("native guest source GO script chronology or hosted-only scope invalid")
    result.update({
        "hosted_native_guest_source_script_wait_receipts_consistent": True,
        "hosted_guest_go_script_nmi_frame": int(race[1]),
        "hosted_guest_go_script_ticker_frame": int(tick[1]),
        "hosted_guest_go_script_source_sha256": source_digest,
        "guest_go_register_bytes_independently_archived": False,
        "original_emulator_GO_parity_independently_accepted": False,
        "source_settled_scored_2p_result": False,
        "player_created_pair_fresh_records_reopened": False,
        "actual_physical_controller_or_audio_accepted": False,
        "release_gate_credit": 0,
        "outcome": "bounded_hosted_source_script_GO_only",
    })
    return result


def read_bounded_runtime(path: Path) -> tuple[bytes, bytes, bytes, bytes]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("no bounded independent native Windows artifact archive")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)):
            raise ValueError("duplicated Windows evidence ZIP member")
        for name in (PREFIX + part for part in FILES):
            if name not in names:
                raise ValueError("absent exact source-owned P1/P2 Win32 evidence: " + name)
        return tuple(archive.read(PREFIX + part) for part in FILES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    observed = audit_guest_script(*read_bounded_runtime(args.runtime),
                                  args.source.read_bytes())
    observed["runtime_evidence_archive_sha256"] = hashlib.sha256(
        args.runtime.read_bytes()).hexdigest()
    print(json.dumps(observed, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
