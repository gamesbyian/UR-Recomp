#!/usr/bin/env python3
"""Keyboard + one pad can form a 2P join; a P2 who leaves is withdrawn (#2225).

Real native game processes, with SDL virtual gamepads seated through the
host's own hotplug path (see the Modern root's test-only key-smoke modes 15
and 16 in ``tools/baldosa_native_modern_root.cpp``):

1. mode 4 creates P1 (Mike) and mode 5 a second racer (Andrew), so the join
   has a verified two-entry roster, as in the second-racer probe;
2. mode 15: the keyboard opens the 2P join and confirms P1; the lone pad's A
   must move it to seat 2 (``join_pad_moved``), its next A confirms P2 and
   the stock 2P route is requested;
3. mode 16: P2's pad confirms and is then unplugged; the keyboard's P1
   confirmation must withdraw P2 (``join_seat_left``) and request no route;
4. mode 17: as 2 up to the move, then Escape closes the join; the moved pad
   must return to seat 1 (``join_pad_returned``) and its next A must drive
   the root again (it reopens the join), never stranding a lone pad on P2;
5. mode 18: two pads, P1's is unplugged at the root; after a short grace the
   remaining P2 pad must be moved to seat 1 (``lone_pad_promoted``) and its
   A must drive the root (it opens the join the keyboard put the cursor on).

Fails closed. Virtual devices only: real pads are physical check C14.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from baldosa_native_first_racer_probe import run_game

QUIET = "turbo on\nwait 900\nquit\n"
JOIN = "wait 400\nquit\n"


def lines(log: str, pattern: str) -> list[str]:
    return re.findall(rf"(?m)^.*{pattern}.*$", log)


def ordered(log: str, stages: tuple[str, ...], label: str) -> None:
    at = []
    for stage in stages:
        if log.count(stage) != 1:
            raise ValueError(f"{label}: expected exactly one {stage!r}")
        at.append(log.index(stage))
    if at != sorted(at):
        raise ValueError(f"{label}: stages out of order")


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int) -> dict:
    exe, rom, out = exe.resolve(strict=True), rom.resolve(strict=True), out.resolve()
    # The product ignores pads while the window is unfocused (#2334); a hosted
    # window may never get focus, so these virtual-pad runs opt back in.
    os.environ["SNESRECOMP_UR_BACKGROUND_PAD_INPUT"] = "1"
    if out.exists():
        raise ValueError("output directory must not pre-exist")
    out.mkdir(parents=True)
    user = out / "user"
    user.mkdir()
    run_game(exe, rom, user, out / "create_p1", "4", QUIET, video, timeout)
    run_game(exe, rom, user, out / "create_p2", "5", QUIET, video, timeout)
    if not (user / "profiles-v1.txt").is_file():
        raise ValueError("the two-racer roster was not created")

    log = run_game(exe, rom, user, out / "keyboard_plus_pad", "15", JOIN, video, timeout)
    ordered(log, ("UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
                  "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
                  "UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2",
                  "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
                  "UR_BALDOSA_MODERN_ROOT stock_requested players=2"), "keyboard+pad")
    if len(lines(log, r"UR_CONTROLLER_SEAT move instance=\d+ from=0 to=1")) != 1:
        raise ValueError("keyboard+pad: the host did not move the pad to seat 2 once")
    if lines(log, "join_rejected") or lines(log, "join_seat_left"):
        raise ValueError("keyboard+pad: a confirmation was rejected or withdrawn")

    log = run_game(exe, rom, user, out / "p2_owner_leaves", "16", JOIN, video, timeout)
    ordered(log, ("UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
                  "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
                  "UR_BALDOSA_MODERN_ROOT join_seat_left seat=2 confirmation_cleared=1",
                  "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1"), "owner leaves")
    if lines(log, "stock_requested players=2"):
        raise ValueError("owner leaves: a 2P race was requested without P2's pad")
    if lines(log, "join_pad_moved"):
        raise ValueError("owner leaves: a pad was moved although P1 confirmed by keyboard "
                         "while seat 2 was held")

    log = run_game(exe, rom, user, out / "join_cancelled", "17", JOIN, video, timeout)
    ordered(log, ("UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2",
                  "UR_BALDOSA_MODERN_ROOT join_closed=1",
                  "UR_BALDOSA_MODERN_ROOT join_pad_returned from=2 to=1"), "join cancelled")
    if len(lines(log, r"UR_CONTROLLER_SEAT move instance=\d+ from=1 to=0")) != 1:
        raise ValueError("join cancelled: the host did not move the pad back to seat 1 once")
    if log.count("UR_BALDOSA_MODERN_ROOT join_opened=1 players=2") != 2 or \
            log.rindex("UR_BALDOSA_MODERN_ROOT join_opened=1 players=2") < \
            log.index("UR_BALDOSA_MODERN_ROOT join_pad_returned"):
        raise ValueError("join cancelled: the returned pad did not drive the root")
    if lines(log, "stock_requested"):
        raise ValueError("join cancelled: a race was requested")

    log = run_game(exe, rom, user, out / "lone_p2_pad", "18", JOIN, video, timeout)
    ordered(log, ("UR_BALDOSA_MODERN_ROOT lone_pad_promoted from=2 to=1",
                  "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2"), "lone P2 pad")
    if len(lines(log, r"UR_CONTROLLER_SEAT move instance=\d+ from=1 to=0")) != 1:
        raise ValueError("lone P2 pad: the host did not move the pad to seat 1 once")
    if lines(log, "stock_requested"):
        raise ValueError("lone P2 pad: a race was requested")

    receipt = {
        "lone_p2_pad": "remaining_p2_pad_promoted_to_p1_and_drives_root",
        "keyboard_plus_pad": "pad_moved_to_p2_and_2p_requested",
        "join_cancelled": "moved_pad_returned_to_p1_and_drives_root",
        "p2_owner_leaves": "p2_confirmation_withdrawn_no_2p",
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "Modern 2P join with SDL virtual gamepads through the native event "
                 "loop; not physical controllers or a completed 2P race",
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    print(json.dumps(run(args.exe, args.rom, args.out, args.video, args.timeout), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
