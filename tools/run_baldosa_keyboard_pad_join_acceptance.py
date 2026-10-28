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
JOIN = "wait 400\nquit\n"  # Negative controls retain their short bounded window.
# The established native Windows Modern 2P journey uses 1800 turbo frames
# for the actual guest stock-menu transition; 400 can stop before admission.
POSITIVE_JOIN = "turbo on\nwait 1800\nquit\n"
# Mode 31: no guest input commands, only turbo/wait/quit while the SDL P1
# delivers every stock menu and gameplay edge through the native host.
PAD_RACE = "turbo on\nwait 7200\nquit\n"
# Same controller, but allow the source-result menu and return to settle.
PAD_RACE_RETURN = "turbo on\nwait 11000\nquit\n"
# Two distinct SDL pads continue through stock 2P GO and source-scored play.
TWO_PAD_RACE = "turbo on\nwait 10000\nquit\n"


def lines(log: str, pattern: str) -> list[str]:
    return re.findall(rf"(?m)^.*{pattern}.*$", log)


def ordered(log: str, stages: tuple[str, ...], label: str) -> None:
    # The native root emits these milestones as complete, standalone lines.
    # Substring counts could accept e.g. menu=3d0 as menu=3d, awarding a
    # successful 2P guest admission that never actually occurred.
    observed = log.splitlines()
    at = []
    for stage in stages:
        matches = [(i, line) for i, line in enumerate(observed) if stage in line]
        if len(matches) != 1 or matches[0][1] != stage:
            raise ValueError(f"{label}: expected exactly one complete line {stage!r}")
        at.append(matches[0][0])
    if at != sorted(at):
        raise ValueError(f"{label}: stages out of order")


def verify_keyboard_plus_pad(log: str) -> None:
    """Require the real guest's 2P stock admission, not merely a join request."""
    ordered(log, ("UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
                  "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
                  "UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2",
                  "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
                  "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
                  "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d"),
            "keyboard+pad")
    # run_game concatenates the host's stdout before the Modern root's
    # stderr. Offsets between UR_CONTROLLER_SEAT and UR_BALDOSA_MODERN_ROOT
    # therefore are NOT event chronology. The root's join_pad_moved marker
    # is emitted only after the real seat_move succeeds; the root's stock
    # observer checks the confirmed P2 owner through the guest transition.
    # Conservatively reject any other host ownership change in the entire
    # capture. Post-admission teardown cannot be distinguished from earlier
    # churn using these two independently buffered streams.
    moves = list(re.finditer(
        r"(?m)^(?:\[[^\]\r\n]+\]\s*)?UR_CONTROLLER_SEAT "
        r"move instance=(\d+) from=0 to=1\b[^\r\n]*$", log
    ))
    if len(moves) != 1:
        raise ValueError("keyboard+pad: the host did not move the pad to seat 2 once")
    move = moves[0]
    # One real SDL device must have owned host seat 0 before that same
    # instance moved to seat 1. Do not mistake an arbitrary reassignment
    # (or an absent initial seat) for a stable two-player admission.
    initial = list(re.finditer(
        r"(?m)^(?:\[[^\]\r\n]+\]\s*)?UR_CONTROLLER_SEAT "
        r"assign instance=(\d+) seat=0\b[^\r\n]*$", log
    ))
    if (len(initial) != 1 or initial[0].start() >= move.start()
            or initial[0].group(1) != move.group(1)):
        raise ValueError(
            "keyboard+pad: exactly one initial SDL P1 assignment for moved pad required"
        )
    host_events = list(re.finditer(
        r"(?m)^(?:\[[^\]\r\n]+\]\s*)?UR_CONTROLLER_SEAT "
        r"(?:assign|vacate|move|claim)\b[^\r\n]*$", log
    ))
    for event in host_events:
        if event.start() in (move.start(), initial[0].start()):
            continue  # Exactly the one validated initial assignment and move.
        raise ValueError(
            "keyboard+pad: host seat ownership changed during captured join: "
            + event.group(0)
        )
    for forbidden in ("join_rejected", "join_seat_left", "stock_rejected=",
                      "stock_requested players=1", "stock_entered players=1"):
        if forbidden in log:
            raise ValueError(f"keyboard+pad: unexpected {forbidden}")



def verify_two_virtual_pads(log: str) -> None:
    """Require distinct host-seated SDL pads and actual guest 2P admission."""
    stages = (
        "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
        "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
    )
    ordered(log, stages, "two virtual pads")
    assignments = [
        (int(m.group(1)), int(m.group(2)), m.start())
        for m in re.finditer(
            r"(?m)^\[Gamepad\] UR_CONTROLLER_SEAT assign "
            r"instance=(\d+) seat=([01]) reason=[^\r\n]+$", log
        )
    ]
    if (len(assignments) != 2 or
            {seat for _, seat, _ in assignments} != {0, 1} or
            len({instance for instance, _, _ in assignments}) != 2):
        raise ValueError("two virtual pads: two distinct host seats not observed")
    # The concatenated host stdout is not synchronized with root stderr.
    # Keep the canonical stdout-before-stderr grouping as a capture-integrity
    # check, but never infer a guest-time seat lease from string offsets.
    if any(pos >= log.index(stages[0]) for _, _, pos in assignments):
        raise ValueError("two virtual pads: host/root log streams interleaved")
    # A host vacate/move/claim anywhere in this capture is conservatively
    # disqualifying: the combined log cannot establish whether it happened
    # before or after guest stock admission. The source root also checks the
    # P2 owner's actual seat on every frame while stock handoff is pending.
    churn = re.search(
        r"(?m)^(?:\[[^\]\r\n]+\]\s*)?UR_CONTROLLER_SEAT "
        r"(?:vacate|move|claim)\b[^\r\n]*$", log,
    )
    if churn:
        raise ValueError(
            "two virtual pads: host seat ownership changed during capture: "
            + churn.group(0)
        )
    for forbidden in ("join_pad_moved", "join_seat_left", "join_rejected",
                      "stock_rejected=", "stock_requested players=1",
                      "stock_entered players=1", "lone_pad_promoted"):
        if forbidden in log:
            raise ValueError(f"two virtual pads: unexpected {forbidden}")


def verify_owner_disconnect(log: str) -> None:
    """Require a distinct SDL P2 host detach and root-level withdrawal.

    run_game captures stdout and stderr separately, then concatenates them.
    The SDL host emits UR_CONTROLLER_SEAT to stdout; the Modern root emits
    join_* to stderr. Cross-stream string offsets therefore DO NOT encode
    real event order. Enforce each stream's independent order, exact device
    identity, and the root's causal source-owner guard instead.
    """
    stages = (
        "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
        "UR_BALDOSA_MODERN_ROOT join_seat_left seat=2 confirmation_cleared=1",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
    )
    ordered(log, stages, "owner leaves")
    assignments = [
        (int(m.group(1)), int(m.group(2)), m.start())
        for m in re.finditer(
            r"(?m)^\[Gamepad\] UR_CONTROLLER_SEAT assign "
            r"instance=(\d+) seat=([01]) reason=[^\r\n]+$", log
        )
    ]
    if (len(assignments) != 2 or
            {seat for _, seat, _ in assignments} != {0, 1} or
            len({instance for instance, _, _ in assignments}) != 2):
        raise ValueError("owner leaves: distinct initial host seats not observed")
    p2_instance = next(instance for instance, seat, _ in assignments if seat == 1)
    vacates = [
        (int(m.group(1)), int(m.group(2)), m.start())
        for m in re.finditer(
            r"(?m)^\[Gamepad\] UR_CONTROLLER_SEAT vacate "
            r"instance=(\d+) seat=([01]) key=[0-9a-fA-F]+$", log
        )
    ]
    if (len(vacates) != 1 or
            vacates[0][0] != p2_instance or vacates[0][1] != 1 or
            vacates[0][2] <= max(pos for _, _, pos in assignments)):
        raise ValueError("owner leaves: actual assigned P2 SDL seat vacate missing")
    # A synthetic join marker cannot substitute for the native host's
    # unique P2 detach. Seat moves/claims would also invalidate continuity.
    churn = re.findall(
        r"(?m)^\[Gamepad\] UR_CONTROLLER_SEAT (?:move|claim)\b[^\r\n]*$",
        log,
    )
    if churn:
        raise ValueError("owner leaves: unexpected host seat move/claim")
    reject_unexpected_stock_route(log, "owner leaves")
    if lines(log, "join_pad_moved"):
        raise ValueError("owner leaves: a pad moved while keyboard P1 held seat 1")


def require_single_pad_seat_continuity(log: str, label: str) -> None:
    """Reject seat loss/replacement in a claimed continuous one-pad journey.

    Host SDL seat logs arrive on stdout and product milestones on stderr.
    Their concatenated order is not a clock, so check the entire native log.
    """
    host_assignments = re.findall(
        r"(?m)^\[Gamepad\] UR_CONTROLLER_SEAT assign "
        r"instance=(\d+) seat=([01]) reason=[^\r\n]+$", log
    )
    if len(host_assignments) != 1 or host_assignments[0][1] != "0":
        raise ValueError(f"{label}: exactly one SDL P1 assignment required")
    if re.search(
        r"(?m)^\[Gamepad\] UR_CONTROLLER_SEAT (?:move|claim|vacate)\b", log
    ):
        raise ValueError(f"{label}: unexpected SDL ownership change")


def verify_five_destination_pad_journey(log: str) -> None:
    """One SDL P1 device, one native process, all five Modern destinations.

    SDL seat logs are stdout and product/view logs are stderr, so enforce
    chronology only among product/view markers, not across the two streams.
    This establishes native title/root/modal/stock entry, NOT a finished
    original race, returned result, physical controller, or release gate.
    """
    require_single_pad_seat_continuity(log, "five destinations")

    selections = re.findall(
        r"(?m)^UR_BALDOSA_MODERN_ROOT selected=(\d+)$", log
    )
    if selections != ["1", "2", "3", "4", "3", "2", "1", "0"]:
        raise ValueError(f"five destinations: actual root selections differ: {selections}")

    # All these source-owned events share stderr ordering. In particular,
    # the painted destination receipt must follow opening the actual modal.
    stages = (
        r"^UR_BALDOSA_MODERN_TITLE entered_root=1 frame=\d+ input_owned=1$",
        r"^UR_BALDOSA_MODERN_ROOT practice_opened=1 available=\d+ course=\d+ source_menu_required=1$",
        r"^UR_BALDOSA_MODERN_DESTINATION stage=practice-picker raster=342x224 root=11,10,320,204 source=modern_product_view$",
        r"^UR_BALDOSA_MODERN_ROOT practice_closed=1$",
        r"^UR_BALDOSA_MODERN_ROOT join_opened=1 players=2$",
        r"^UR_BALDOSA_MODERN_DESTINATION stage=multiplayer-join raster=342x224 root=11,10,320,204 source=modern_product_view$",
        r"^UR_BALDOSA_MODERN_ROOT join_closed=1$",
        r"^UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=\d+ unavailable=\d+$",
        r"^UR_BALDOSA_MODERN_DESTINATION stage=records-1p raster=342x224 root=11,10,320,204 source=modern_product_view$",
        r"^UR_BALDOSA_MODERN_ROOT records_closed=1$",
        r"^UR_BALDOSA_MODERN_ROOT options_opened row=[^\r\n]+$",
        r"^UR_BALDOSA_MODERN_DESTINATION stage=options raster=342x224 root=11,10,320,204 source=modern_product_view$",
        r"^UR_BALDOSA_MODERN_ROOT options_closed row=[^\r\n]+$",
        r"^UR_BALDOSA_MODERN_ROOT stock_requested players=1$",
        r"^UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c$",
    )
    positions = []
    for stage in stages:
        matches = list(re.finditer(stage, log, re.MULTILINE))
        if len(matches) != 1:
            raise ValueError(f"five destinations: missing/duplicate native stage {stage!r}")
        positions.append(matches[0].start())
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise ValueError("five destinations: native modal/guest stages out of order")
    # Controller navigation is not visible acceptance if title/root never
    # rendered. Keep these witnesses in the same native product stream.
    title_paint = list(re.finditer(
        r"(?m)^UR_BALDOSA_MODERN_TITLE painted=1 raster=342x224 host=modern$", log))
    root_paint = list(re.finditer(
        r"(?m)^UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared$", log))
    if len(title_paint) != 1 or len(root_paint) != 1:
        raise ValueError("five destinations: native title/root paint missing or duplicated")
    first_selection = re.search(r"(?m)^UR_BALDOSA_MODERN_ROOT selected=1$", log)
    if first_selection is None or not (title_paint[0].start() < positions[0] <
            root_paint[0].start() < first_selection.start()):
        raise ValueError("five destinations: controller navigated before native title/root paint")
    # A list of eight cursor indices alone could be spliced from a different
    # route. Bind each selection to the specific modal it actually opened.
    cursor_positions = [
        m.start() for m in re.finditer(
            r"(?m)^UR_BALDOSA_MODERN_ROOT selected=\d+$", log
        )
    ]
    expected_windows = (
        (positions[0], positions[1]),   # title -> Practice
        (positions[3], positions[4]),   # Practice back -> Multiplayer
        (positions[6], positions[7]),   # Multiplayer back -> Records
        (positions[9], positions[10]),  # Records back -> Options
    )
    if any(not (lo < cursor_positions[i] < hi)
           for i, (lo, hi) in enumerate(expected_windows)):
        raise ValueError("five destinations: root selection not bound to opened modal")
    if not all(positions[12] < pos < positions[13]
               for pos in cursor_positions[4:]):
        raise ValueError("five destinations: Play return cursor path misplaced")
    for forbidden in ("UR_BALDOSA_MODERN_DESTINATION paint_refused=1",
                      "practice_unavailable=1", "join_unavailable=1",
                      "stock_requested players=2", "stock_entered players=2",
                      "stock_rejected=", "stock_aborted=", "active_profile_stale=1",
                      "join_pad_moved", "join_seat_left"):
        if forbidden in log:
            raise ValueError(f"five destinations: unexpected {forbidden}")




def verify_controller_only_two_pad_root(log: str) -> None:
    """Title -> painted Practice -> painted 2P join -> genuine stock 2P.

    Both pads must be native SDL virtual devices, with independent host seats
    and P1/P2 confirmations. Host seat stdout is concatenated before product
    stderr, so only compare order within the product stream. This remains
    hosted acceptance, never physical-controller or release-gate evidence.
    """
    verify_two_virtual_pads(log)
    selections = re.findall(
        r"(?m)^UR_BALDOSA_MODERN_ROOT selected=(\d+)\r?$", log
    )
    if selections != ["1", "2"]:
        raise ValueError(f"controller-only 2P root: wrong selections {selections}")
    stages = (
        r"^UR_BALDOSA_MODERN_TITLE painted=1 raster=342x224 host=modern\r?$",
        r"^UR_BALDOSA_MODERN_TITLE entered_root=1 frame=\d+ input_owned=1\r?$",
        r"^UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared\r?$",
        r"^UR_BALDOSA_MODERN_ROOT selected=1\r?$",
        r"^UR_BALDOSA_MODERN_ROOT practice_opened=1 available=\d+ course=\d+ source_menu_required=1\r?$",
        r"^UR_BALDOSA_MODERN_DESTINATION stage=practice-picker raster=342x224 root=11,10,320,204 source=modern_product_view\r?$",
        r"^UR_BALDOSA_MODERN_ROOT practice_closed=1\r?$",
        r"^UR_BALDOSA_MODERN_ROOT selected=2\r?$",
        r"^UR_BALDOSA_MODERN_ROOT join_opened=1 players=2\r?$",
        r"^UR_BALDOSA_MODERN_DESTINATION stage=multiplayer-join raster=342x224 root=11,10,320,204 source=modern_product_view\r?$",
        r"^UR_BALDOSA_MODERN_ROOT join_confirmed seat=1\r?$",
        r"^UR_BALDOSA_MODERN_ROOT join_confirmed seat=2\r?$",
        r"^UR_BALDOSA_MODERN_ROOT stock_requested players=2\r?$",
        r"^UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\r?$",
    )
    positions = []
    for stage in stages:
        matches = list(re.finditer(stage, log, re.MULTILINE))
        if len(matches) != 1:
            raise ValueError(
                f"controller-only 2P root: missing/duplicate stage {stage!r}"
            )
        positions.append(matches[0].start())
    if positions != sorted(set(positions)):
        raise ValueError("controller-only 2P root: source route out of order")
    for forbidden in (
        "UR_BALDOSA_MODERN_ROOT join_closed=1",
        "UR_BALDOSA_MODERN_ROOT practice_unavailable=1",
        "UR_BALDOSA_MODERN_ROOT join_unavailable=1",
        "UR_BALDOSA_MODERN_DESTINATION paint_refused=1",
        "UR_BALDOSA_MODERN_ROOT stock_requested players=1",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1",
    ):
        if forbidden in log:
            raise ValueError(f"controller-only 2P root: unexpected {forbidden}")


def verify_controller_only_two_pad_race(log: str) -> dict:
    """Same two SDL pads: painted title/2P join -> stock GO -> earned match.

    Original 2P result and canonical match publication remain separate
    source-owned witnesses. A synthetic route marker alone never passes.
    """
    verify_controller_only_two_pad_root(log)
    stock = log.index("UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d")
    patterns = (
        r"^UR_BALDOSA_MODERN_TWO_PAD_RACE source_stock_setup=1 menu=3d phase=f60c\r?$",
        r"^UR_BALDOSA_MODERN_TWO_PAD_RACE source_p2_picker=right seat=2\r?$",
        r"^UR_BALDOSA_MODERN_TWO_PAD_RACE source_start_pulses=5 seats=1,2\r?$",
        r"^UR_BALDOSA_MODERN_TWO_PAD_RACE source_go=1 phase=8610 ticker=[1-9][0-9]*\r?$",
        r"^UR_BALDOSA_MODERN_TWO_PAD_RACE source_input_completed=1 frames=3190\r?$",
    )
    positions = []
    for pattern in patterns:
        matches = list(re.finditer(pattern, log, re.MULTILINE))
        if len(matches) != 1:
            raise ValueError(f"two-pad race: missing/duplicate source stage {pattern!r}")
        positions.append(matches[0].start())
    if not (stock < positions[0] < positions[1] < positions[2] < positions[3] < positions[4]):
        raise ValueError("two-pad race: stock setup, source GO or SDL drive out of order")
    # This existing native observer independently checks source result,
    # P1/P2 rider identity, input history and actual paired publication.
    from baldosa_native_2p_records_probe import source_match_published
    result = source_match_published(
        log, p1_profile="mike", p2_profile="andrew", p1_rider=0, p2_rider=1,
    )
    if log.index("UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p") <= positions[3]:
        raise ValueError("two-pad race: result preceded source GO")
    return result


def verify_five_destination_pad_return(log: str) -> None:
    """Require the same SDL pad to back out of genuine stock 1P into Modern.

    The original X backtrack is delivered to the guest while it owns input;
    only a later fresh B at observed MAIN D7 may reopen the shared root.
    This does not claim a completed race, result or physical controller.
    """
    reopened = "UR_BALDOSA_MODERN_ROOT reopened=1 menu=d7 guest_writes=0"
    if log.count(reopened) != 1:
        raise ValueError("pad return: missing/duplicate source-admitted root reentry")
    # Before the source reentry the existing strict five-destination
    # acceptance must still pass with exactly one seated SDL P1 device.
    verify_five_destination_pad_journey(log[:log.index(reopened)])
    # Prefix-only validation misses unplug/reassignment after root reentry.
    require_single_pad_seat_continuity(log, "pad return")
    stages = (
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
        "UR_BALDOSA_MODERN_PAD_RETURN guest_back_x=1 source_menu=3c",
        "UR_BALDOSA_MODERN_PAD_RETURN root_back_b=1 source_menu=d7",
        reopened,
    )
    witnesses = stages + (
        "UR_BALDOSA_MODERN_PAD_RETURN reopened=1 source_menu=d7",
        "UR_BALDOSA_MODERN_ROOT reopened_painted=1 renderer=shared",
    )
    positions = {}
    for stage in witnesses:
        matches = [m.start() for m in re.finditer(
            rf"(?m)^{re.escape(stage)}$", log)]
        if len(matches) != 1:
            raise ValueError(f"pad return: missing/duplicate native stage {stage!r}")
        positions[stage] = matches[0]
    if (list(map(positions.get, stages)) !=
            sorted(positions[stage] for stage in stages)):
        raise ValueError("pad return: source X/B/MAIN/root reentry out of order")
    # SDL presentation may occur between the host B edge and the next
    # simulated guest frame. Both repaint and post-event acknowledgement
    # must follow actual source-admitted reentry, but neither is ordered
    # relative to the other.
    if any(positions[stage] <= positions[reopened] for stage in witnesses[4:]):
        raise ValueError("pad return: root repaint/ack preceded source reentry")
    if "UR_BALDOSA_MODERN_ROOT stock_entered players=2" in log:
        raise ValueError("pad return: unintended 2P admission")

    # A repainted root can still be unusable if guest->host controller focus
    # was not restored. Require the same SDL pad to navigate from Play to
    # Records, open a genuinely painted archive and close it with B.
    tail = log[positions[reopened] + len(reopened):]
    post_stages = (
        r"^UR_BALDOSA_MODERN_ROOT selected=1$",
        r"^UR_BALDOSA_MODERN_ROOT selected=2$",
        r"^UR_BALDOSA_MODERN_ROOT selected=3$",
        r"^UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=\d+ unavailable=\d+$",
        r"^UR_BALDOSA_MODERN_DESTINATION stage=records-1p raster=342x224 root=11,10,320,204 source=modern_product_view$",
        r"^UR_BALDOSA_MODERN_ROOT records_closed=1$",
    )
    post_positions = []
    for stage in post_stages:
        matches = list(re.finditer(stage, tail, re.MULTILINE))
        if len(matches) != 1:
            raise ValueError(f"pad return: missing/duplicate post-return Records stage {stage!r}")
        post_positions.append(matches[0].start())
    if post_positions != sorted(post_positions) or len(set(post_positions)) != len(post_positions):
        raise ValueError("pad return: post-return controller Records journey out of order")
    # The root and its selection events share the product stderr stream.
    # A late compositor repaint must not satisfy a controller journey that
    # already navigated an unpainted root. The previous check required a
    # repaint after reentry, but did not bind it before the first selection.
    repaint = "UR_BALDOSA_MODERN_ROOT reopened_painted=1 renderer=shared"
    if positions[repaint] >= positions[reopened] + len(reopened) + post_positions[0]:
        raise ValueError("pad return: controller navigated before root repaint")
    if "UR_BALDOSA_MODERN_ROOT stock_requested" in tail:
        raise ValueError("pad return: unexpected stock relaunch after reentry")


def verify_five_destination_pad_race(log: str) -> None:
    """Require source-settled 1P after one uninterrupted SDL controller route.

    The original guest result observer and saved archive remain authorities.
    This does not yet establish controller navigation AFTER the result.
    """
    verify_five_destination_pad_journey(log)
    require_single_pad_seat_continuity(log, "pad earned race")
    # Root/fixture markers share product stderr. The native result observer
    # may use another stream; run_game concatenates stdout before stderr, so
    # no cross-stream offset is a legitimate chronology witness.
    markers = (
        r"^UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c$",
        r"^UR_BALDOSA_MODERN_PAD_RACE source_stock_setup=1 menu=3c$",
        r"^UR_BALDOSA_MODERN_PAD_RACE source_start_pulses=4$",
        r"^UR_BALDOSA_MODERN_PAD_RACE source_go=1 phase=8610 ticker=[1-9][0-9]*$",
    )
    found = [list(re.finditer(marker, log, re.MULTILINE)) for marker in markers]
    if any(len(matches) != 1 for matches in found):
        raise ValueError("pad earned race: source GO milestones missing or duplicated")
    positions = [matches[0].start() for matches in found]
    if positions != sorted(positions):
        raise ValueError("pad earned race: stock/GO ordering invalid")
    result = re.findall(
        r"(?m)^UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p "
        r"race_host=([0-9]+) result_host=([0-9]+) "
        r"finish_ticks60=([0-9]+) input_frames=([0-9]+) "
        r"input_runs=([0-9]+) published=([01])$", log)
    if len(result) != 1:
        raise ValueError("pad earned race: genuine native result missing or duplicated")
    race_host, result_host, ticks, input_frames, input_runs, published = (
        int(value) for value in result[0]
    )
    if (race_host >= result_host or ticks <= 0 or input_frames <= 0 or
            input_runs <= 0 or published != 1):
        raise ValueError("pad earned race: source result not settled/published")
    if len(re.findall(
            r"(?m)^UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p "
            r"profile=mike course=course:01 ", log)) != 1:
        raise ValueError("pad earned race: actual Mike course:01 capture missing")
    if ("UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1" in log or
            "UR_BALDOSA_NATIVE_RUN NOT_SAVED=1" in log):
        raise ValueError("pad earned race: canonical run not durably published")



def verify_five_destination_pad_post_result(log: str) -> None:
    """Require the source-documented result-to-MAIN path and earned Records.

    Host controller stdout and product stderr are concatenated, not one
    synchronized clock. Order only the product's own stderr markers.
    """
    reopened = "UR_BALDOSA_MODERN_ROOT reopened=1 menu=d7 guest_writes=0"
    if log.count(reopened) != 1:
        raise ValueError("pad earned return: missing/duplicate source reentry")
    # The original five-destination verifier requires exactly eight root
    # selections and one Records open; post-return navigation adds more.
    verify_five_destination_pad_race(log[:log.index(reopened)])
    require_single_pad_seat_continuity(log, "pad earned return")
    # These markers share the product stderr stream, so the original RESULT
    # observation must occur after controller race input finishes and before
    # the A press that advances from RESULT to TRACK. A late/duplicate RESULT
    # observation is not evidence of a valid source-driven transition.
    observed_results = list(re.finditer(
        r"(?m)^UR_BALDOSA_MODERN_PAD_POST source_observed "
        r"frame=\d+ menu=99 race=[0-9a-f]{2} stage=0$", log))
    if len(observed_results) != 1:
        raise ValueError("pad earned return: missing/duplicate original result observation")
    # The documented original source route is RESULT 99 -> TRACK F6 (A),
    # then TOUR 6D -> RIDER 3C -> MAIN D7 (X each). Only a fresh B
    # from MAIN may reopen Modern. Never accept a direct host teleport.
    stages = (
        "UR_BALDOSA_MODERN_PAD_RACE source_input_completed=1",
        "UR_BALDOSA_MODERN_PAD_POST result_continue_a=1 source_menu=99",
        "UR_BALDOSA_MODERN_PAD_POST track_back_x=1 source_menu=f6",
        "UR_BALDOSA_MODERN_PAD_POST tour_back_x=1 source_menu=6d",
        "UR_BALDOSA_MODERN_PAD_POST rider_back_x=1 source_menu=3c",
        "UR_BALDOSA_MODERN_PAD_POST root_back_b=1 source_menu=d7",
        reopened,
    )
    positions = []
    for marker in stages:
        matches = list(re.finditer(rf"(?m)^{re.escape(marker)}$", log))
        if len(matches) != 1:
            raise ValueError(f"pad earned return: missing/duplicate {marker!r}")
        positions.append(matches[0].start())
    if positions != sorted(positions):
        raise ValueError("pad earned return: source menu return order invalid")
    if not positions[0] < observed_results[0].start() < positions[1]:
        raise ValueError("pad earned return: original result observed outside source transition")
    tail_start = positions[-1] + len(stages[-1])
    tail = log[tail_start:]
    acknowledgements = (
        "UR_BALDOSA_MODERN_PAD_POST reopened=1 source_menu=d7",
        "UR_BALDOSA_MODERN_ROOT reopened_painted=1 renderer=shared",
    )
    for marker in acknowledgements:
        matches = list(re.finditer(rf"(?m)^{re.escape(marker)}$", log))
        if len(matches) != 1 or matches[0].start() <= positions[-1]:
            raise ValueError(f"pad earned return: missing/early {marker!r}")
    # Repaint and controller-ack may be interleaved by SDL. Neither can
    # occur before source reentry, and repaint must precede navigation.
    paint_pos = log.index(acknowledgements[1])
    post = (
        r"^UR_BALDOSA_MODERN_ROOT selected=1$",
        r"^UR_BALDOSA_MODERN_ROOT selected=2$",
        r"^UR_BALDOSA_MODERN_ROOT selected=3$",
        r"^UR_BALDOSA_MODERN_ROOT records_opened=1 "
        r"profile=selected validated=([1-9][0-9]*) unavailable=[0-9]+$",
        r"^UR_BALDOSA_MODERN_DESTINATION stage=records-1p\b"
        r"[^\r\n]*source=modern_product_view$",
        r"^UR_BALDOSA_MODERN_ROOT records_closed=1$",
    )
    last = -1
    first_selection = None
    for marker in post:
        matches = list(re.finditer(marker, tail, re.MULTILINE))
        if len(matches) != 1 or matches[0].start() <= last:
            raise ValueError(f"pad earned return: missing/reordered {marker!r}")
        last = matches[0].start()
        if first_selection is None:
            first_selection = tail_start + last
    if first_selection is None or paint_pos >= first_selection:
        raise ValueError("pad earned return: controller navigated before repaint")
    # The native Modern root must still accept this P1 after 900 guest
    # frames of idle time; source gameplay may advance underneath it.
    idle = "UR_BALDOSA_MODERN_PAD_POST idle_completed=1 frames=900 modern_visible=1"
    idle_matches = list(re.finditer(rf"(?m)^{re.escape(idle)}$", log))
    if (len(idle_matches) != 1 or not paint_pos < idle_matches[0].start() < first_selection):
        raise ValueError("pad earned return: idle Modern focus not witnessed before navigation")
    # Native Quit must be explicitly queued by the same SDL controller
    # after Records closes, never satisfied by the script's fallback quit.
    quit_markers = (
        "UR_BALDOSA_MODERN_PAD_POST quit_prompt_b=1",
        "UR_BALDOSA_MODERN_PAD_POST quit_confirm_a=1 prompt=1",
        "UR_BALDOSA_MODERN_ROOT quit_confirmed=1 native_sdl_quit_queued=1",
    )
    last_quit = tail_start + last
    for marker in quit_markers:
        matches = list(re.finditer(rf"(?m)^{re.escape(marker)}$", log))
        if len(matches) != 1 or matches[0].start() <= last_quit:
            raise ValueError(f"pad earned return: missing/reordered native Quit {marker!r}")
        last_quit = matches[0].start()
    if "UR_BALDOSA_MODERN_ROOT quit_event_rejected" in log:
        raise ValueError("pad earned return: SDL quit event was rejected")
    if "UR_BALDOSA_MODERN_ROOT stock_requested" in tail:
        raise ValueError("pad earned return: unexpected stock relaunch")
    # Product stderr contains actual mapped-human-word filter samples.
    # The guest may advance under Modern; its human button bits may not.
    isolation = list(re.finditer(
        r"(?m)^UR_BALDOSA_PRODUCT_INPUT_ISOLATION sample=(\d+) frame=(\d+) "
        r"incoming=([0-9a-f]{8}) guest=([0-9a-f]{8}) "
        r"queued=([0-9a-f]{4}) host_owns=1\r?$", log))
    window = [m for m in isolation if positions[-1] < m.start() < last_quit]
    counts = [int(m.group(1)) for m in window]
    if not counts or counts != sorted(set(counts)):
        raise ValueError("pad earned return: missing/duplicate/out-of-order host input samples")
    idle_counts = {int(m.group(1)) for m in window if m.start() < first_selection}
    if not {180, 360, 540, 720, 900}.issubset(idle_counts):
        raise ValueError("pad earned return: incomplete 900-sample native input isolation")
    for sample in window:
        incoming = int(sample.group(3), 16)
        guest = int(sample.group(4), 16)
        queued = int(sample.group(5), 16)
        if queued or guest != (incoming & 0xff000000):
            raise ValueError("pad earned return: host-owned human input leaked to guest")
    # SDL Modern handles its controller events before the mapped-human-word
    # guest seam. A zero button word here is expected, not absent controller
    # activity: the ordered Records/Quit events above prove navigation.
    # Demand later native filter calls to establish that no guest buttons or
    # queued stock edges leak while those events are processed.
    post_idle = [m for m in window if idle_matches[0].start() < m.start() < last_quit]
    if not {930, 960}.issubset({int(m.group(1)) for m in post_idle}):
        raise ValueError("pad earned return: missing post-idle native input isolation")
    # The fallback script also quits cleanly at frame 11000. A product
    # "quit queued" receipt alone cannot establish that its SDL_QUIT was
    # actually consumed. Require the native host's exit witness strictly
    # before the script's termination deadline; stdout/stderr are separate
    # streams, so do not infer their relative order from concatenation.
    exits = re.findall(
        r"(?m)^\[host \+[0-9]+(?:\.[0-9]+)?s\] exit: SDL_QUIT event after ([0-9]+) frames\r?$", log)
    if len(exits) != 1 or not (0 < int(exits[0]) < 11000):
        raise ValueError("pad earned return: native SDL Quit not witnessed before script fallback")


def reject_unexpected_stock_route(log: str, label: str) -> None:
    """A withdrawn/cancelled join must not request OR enter a stock route."""
    for marker in ("UR_BALDOSA_MODERN_ROOT stock_requested",
                   "UR_BALDOSA_MODERN_ROOT stock_entered"):
        if marker in log:
            raise ValueError(f"{label}: unexpected {marker}")


def route_milestones(log: str) -> list[str]:
    """Retain a bounded native route trace in CI errors without dumping the log."""
    return [
        line for line in log.splitlines()
        if line.startswith("UR_BALDOSA_MODERN_ROOT ") and
        (" join_" in line or " stock_" in line)
    ][-20:]


def retain_two_pad_ci_pair(new_pairs: set[Path], run: Path, out: Path) -> dict[str, str]:
    """Retain only the two bounded CI-earned match files for external byte QA.

    The run is generated from fresh synthetic Mike/Andrew CI profiles, never
    from a user's save directory. No ROM, SRAM, catalog or profile is copied.
    """
    sidecar = run.with_name(run.name + ".urmatch")
    if {p.name for p in new_pairs} != {run.name, sidecar.name}:
        raise ValueError("two-pad evidence: canonical pair names required")
    evidence = out / "controller_only_two_pad_race" / "earned_pair"
    evidence.mkdir(parents=True, exist_ok=False)
    digests: dict[str, str] = {}
    manifest: dict[str, dict[str, str | int]] = {}
    for source, retained in ((run, "source.urrun"),
                             (sidecar, "source.urrun.urmatch")):
        if source.is_symlink() or not source.is_file():
            raise ValueError("two-pad evidence: source must be a regular file")
        data = source.read_bytes()
        if not 0 < len(data) <= 1024 * 1024:
            raise ValueError("two-pad evidence: source size outside CI limit")
        digest = hashlib.sha256(data).hexdigest()
        destination = evidence / retained
        destination.write_bytes(data)
        if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
            raise ValueError("two-pad evidence: retained byte mismatch")
        digests[source.name] = digest
        manifest[retained] = {
            "original_name": source.name,
            "sha256": digest,
            "size": len(data),
        }
    (evidence / "manifest.json").write_text(
        json.dumps({"scope": "CI synthetic two-controller source-earned match",
                    "files": manifest}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return digests


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

    log = run_game(exe, rom, user, out / "keyboard_plus_pad", "15", POSITIVE_JOIN, video, timeout)
    try:
        verify_keyboard_plus_pad(log)
    except ValueError as exc:
        # The runner's work/log.txt survives locally but CI does not upload
        # it on failure. Surface only source-owned route markers so the next
        # native failure distinguishes timeout/rejection from late admission.
        raise ValueError(
            f"{exc}; native route milestones: {route_milestones(log)!r}"
        ) from exc

    # Two actual host seats and two distinct virtual-device A edges.
    log = run_game(exe, rom, user, out / "two_virtual_pads", "19",
                   POSITIVE_JOIN, video, timeout)
    try:
        verify_two_virtual_pads(log)
    except ValueError as exc:
        raise ValueError(
            f"{exc}; native route milestones: {route_milestones(log)!r}"
        ) from exc

    log = run_game(exe, rom, user, out / "p2_owner_leaves", "16", JOIN, video, timeout)
    try:
        verify_owner_disconnect(log)
    except ValueError as exc:
        # Preserve the native host's exact seat evidence beside the root's
        # join markers. stdout (host) and stderr (root) are separately captured
        # and concatenated, so log offsets cannot establish cross-stream
        # chronology; inspect both native event streams independently.
        evidence = [line for line in log.splitlines()
                    if "UR_CONTROLLER_SEAT " in line or
                    "UR_BALDOSA_MODERN_ROOT join_" in line]
        raise ValueError(
            f"{exc}; host/root seat evidence (log order, max 40): "
            f"{evidence[:40]!r}; inspect retained p2_owner_leaves/log.txt"
        ) from exc

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
    reject_unexpected_stock_route(log, "join cancelled")

    log = run_game(exe, rom, user, out / "lone_p2_pad", "18", JOIN, video, timeout)
    ordered(log, ("UR_BALDOSA_MODERN_ROOT lone_pad_promoted from=2 to=1",
                  "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2"), "lone P2 pad")
    if len(lines(log, r"UR_CONTROLLER_SEAT move instance=\d+ from=1 to=0")) != 1:
        raise ValueError("lone P2 pad: the host did not move the pad to seat 1 once")
    reject_unexpected_stock_route(log, "lone P2 pad")

    # Unlike separate 15-19/24-28 receipts, this is a single continuous
    # SDL virtual-pad title -> five destinations -> original stock admission.
    log = run_game(exe, rom, user, out / "five_destination_pad", "29",
                   POSITIVE_JOIN, video, timeout)
    try:
        verify_five_destination_pad_journey(log)
    except ValueError as exc:
        raise ValueError(
            f"{exc}; native route milestones: {route_milestones(log)!r}; "
            "inspect retained five_destination_pad/log.txt"
        ) from exc

    # Mode 33 closes the keyboard-free 2P gap left by mode 19: the same
    # real SDL P1 enters title, painted Practice and painted Multiplayer;
    # a distinct SDL P2 then confirms and the ORIGINAL guest admits 0x3d.
    log = run_game(exe, rom, user, out / "controller_only_two_pad_root", "33",
                   POSITIVE_JOIN, video, timeout)
    try:
        verify_controller_only_two_pad_root(log)
    except ValueError as exc:
        raise ValueError(
            f"{exc}; native route milestones: {route_milestones(log)!r}; "
            "inspect retained controller_only_two_pad_root/log.txt"
        ) from exc

    # Mode 34 continues the very same keyboard-free two-pad journey into
    # original source GO, drives both players through actual SDL events and
    # requires a real source-scored paired result. No guest-input script.
    pair_archive = user / "multiplayer-runs"
    prior_pairs = set(pair_archive.iterdir()) if pair_archive.is_dir() else set()
    log = run_game(exe, rom, user, out / "controller_only_two_pad_race", "34",
                   TWO_PAD_RACE, video, max(timeout, 360))
    try:
        two_pad_source_result = verify_controller_only_two_pad_race(log)
    except ValueError as exc:
        source = [line for line in log.splitlines()
                  if line.startswith("UR_BALDOSA_MODERN_TWO_PAD_RACE ")
                  or line.startswith("UR_BALDOSA_NATIVE_RESULT ")
                  or line.startswith("UR_BALDOSA_NATIVE_MATCH ")]
        raise ValueError(
            f"{exc}; 2P source trace: {source[-25:]!r}; "
            "inspect retained controller_only_two_pad_race/log.txt"
        ) from exc
    after_pairs = set(pair_archive.iterdir()) if pair_archive.is_dir() else set()
    new_pairs = after_pairs - prior_pairs
    new_runs = [p for p in new_pairs if p.name.endswith(".urrun")]
    if (len(new_pairs) != 2 or len(new_runs) != 1 or prior_pairs - after_pairs
            or {p.name for p in new_pairs} !=
            {new_runs[0].name, new_runs[0].name + ".urmatch"}
            or any(p.is_symlink() or not p.is_file() or p.stat().st_size == 0
                   for p in new_pairs)):
        raise ValueError("two-pad race: one new canonical source-earned pair required")
    # Retain the exact synthetic CI pair so an independent reviewer can
    # recompute the hashes and inspect both raw canonical records.
    two_pad_pair_sha256 = retain_two_pad_ci_pair(
        new_pairs, new_runs[0], out
    )

    # Separate CI-only mode 30 uses the same SDL virtual-pad route and
    # probes original X backtrack followed by physical B reentry at MAIN D7.
    # Keep mode 29's previously qualified admission receipt independently.
    log = run_game(exe, rom, user, out / "five_destination_return", "30",
                   POSITIVE_JOIN, video, timeout)
    try:
        verify_five_destination_pad_return(log)
    except ValueError as exc:
        source = [line for line in log.splitlines()
                  if line.startswith("UR_BALDOSA_MODERN_PAD_RETURN ") or
                  "UR_BALDOSA_MODERN_ROOT reopened" in line]
        raise ValueError(
            f"{exc}; guest return source trace: {source[-25:]!r}; "
            "inspect retained five_destination_return/log.txt"
        ) from exc

    # Unlike the old stock GO script, this native guest receives every
    # original stock/race button edge from the same SDL virtual P1.
    archive = user / "runs" / "mike"
    existing = set(archive.glob("*.urrun")) if archive.is_dir() else set()
    log = run_game(exe, rom, user, out / "five_destination_earned_race", "31",
                   PAD_RACE, video, max(timeout, 300))
    try:
        verify_five_destination_pad_race(log)
    except ValueError as exc:
        raise ValueError(
            f"{exc}; inspect retained five_destination_earned_race/log.txt"
        ) from exc
    after = set(archive.glob("*.urrun")) if archive.is_dir() else set()
    new_runs = after - existing
    if (len(new_runs) != 1 or existing - after or
            any(path.is_symlink() or not path.is_file() or
                path.stat().st_size == 0 for path in new_runs)):
        raise ValueError("pad earned race: exactly one new canonical .urrun required")
    earned_sha256 = hashlib.sha256(next(iter(new_runs)).read_bytes()).hexdigest()

    # Run the stricter post-result journey in its own fresh canonical user
    # directory. Two source-earned races may produce identical archive names;
    # sharing the first user's directory could falsely report no new record.
    # Exercise a REAL Windows non-ACP user root on the full original guest
    # P1/P2 named-profile cold boots and source-earned return-to-Records.
    # This is isolated from the earlier ASCII acceptance journeys; no player
    # save or test-generated score is copied between the two roots.
    return_user = out / "user_earned_return_漢字-🚲"
    return_user.mkdir()
    run_game(exe, rom, return_user, out / "return_create_p1",
             "4", QUIET, video, timeout)
    run_game(exe, rom, return_user, out / "return_create_p2",
             "5", QUIET, video, timeout)
    return_archive = return_user / "runs" / "mike"
    return_existing = (set(return_archive.glob("*.urrun"))
                       if return_archive.is_dir() else set())
    # Only mode 32 needs the bounded actual mapped-input isolation witness.
    # Keep the diagnostic disabled for every other native acceptance mode.
    prior_isolation = os.environ.get("UR_BALDOSA_PRODUCT_INPUT_ISOLATION_DIAGNOSTICS")
    try:
        os.environ["UR_BALDOSA_PRODUCT_INPUT_ISOLATION_DIAGNOSTICS"] = "1"
        return_log = run_game(exe, rom, return_user,
                              out / "five_destination_earned_return", "32",
                              PAD_RACE_RETURN, video, max(timeout, 360))
    finally:
        if prior_isolation is None:
            os.environ.pop("UR_BALDOSA_PRODUCT_INPUT_ISOLATION_DIAGNOSTICS", None)
        else:
            os.environ["UR_BALDOSA_PRODUCT_INPUT_ISOLATION_DIAGNOSTICS"] = prior_isolation
    try:
        verify_five_destination_pad_post_result(return_log)
    except ValueError as exc:
        source = [line for line in return_log.splitlines()
                  if line.startswith("UR_BALDOSA_MODERN_PAD_POST ")
                  or line.startswith("UR_BALDOSA_MODERN_ROOT reopened")
                  or line.startswith("UR_BALDOSA_MODERN_ROOT records_")]
        raise ValueError(
            f"{exc}; source return trace: {source[-35:]!r}; "
            "inspect retained five_destination_earned_return/log.txt"
        ) from exc
    return_after = (set(return_archive.glob("*.urrun"))
                    if return_archive.is_dir() else set())
    return_new = return_after - return_existing
    if (len(return_new) != 1 or return_existing - return_after or
            any(p.is_symlink() or not p.is_file() or p.stat().st_size == 0
                for p in return_new)):
        raise ValueError("pad earned return: exactly one new canonical .urrun required")
    return_earned_sha256 = hashlib.sha256(
        next(iter(return_new)).read_bytes()).hexdigest()

    # Fresh OS process, same real Windows native PE, same non-ACP user root.
    # An earned Records panel in the scoring process alone cannot prove that
    # the archived result survives a cold boot and the full native menu path.
    cold_log = run_game(exe, rom, return_user,
                        out / "earned_return_cold_records", "29",
                        POSITIVE_JOIN, video, timeout)
    try:
        verify_five_destination_pad_journey(cold_log)
        visible = re.findall(
            r"(?m)^UR_BALDOSA_MODERN_ROOT records_opened=1 "
            r"profile=selected validated=([0-9]+) unavailable=([0-9]+)\r?$",
            cold_log)
        if visible != [("1", "0")]:
            raise ValueError(
                "cold earned Records: one source-earned record must reopen "
                f"as validated=1 unavailable=0, got {visible!r}")
    except ValueError as exc:
        raise ValueError(
            f"{exc}; inspect retained earned_return_cold_records/log.txt"
        ) from exc
    cold_runs = (set(return_archive.glob("*.urrun"))
                 if return_archive.is_dir() else set())
    if cold_runs != return_after or hashlib.sha256(
            next(iter(return_new)).read_bytes()).hexdigest() != return_earned_sha256:
        raise ValueError(
            "cold earned Records: the guest boot/navigation changed the "
            "immutable source-earned run archive")

    # Retain the *actual source-earned* run bytes from the live Windows PE,
    # not a synthetic replacement. The replay-stage verifier runs against
    # the original Unicode path; this evidence copy is only for independent
    # after-the-fact hash/format inspection and contains no ROM/player data.
    earned_evidence = (out / "earned_return_cold_records" /
                       "earned_run" / "source.urrun")
    earned_evidence.parent.mkdir(parents=True, exist_ok=False)
    earned_bytes = next(iter(return_new)).read_bytes()
    if hashlib.sha256(earned_bytes).hexdigest() != return_earned_sha256:
        raise ValueError("earned replay source changed before retention")
    earned_evidence.write_bytes(earned_bytes)
    if hashlib.sha256(earned_evidence.read_bytes()).hexdigest() != return_earned_sha256:
        raise ValueError("retained source-earned replay evidence not byte-identical")

    receipt = {
        "five_destination_earned_race": "one_sdl_p1_real_original_go_source_settled_1p_record",
        "five_destination_earned_return": "one_sdl_p1_source_earned_1p_post_result_root_records",
        "earned_return_run_sha256": return_earned_sha256,
        "source_earned_unicode_replay_archive_retained_sha256": return_earned_sha256,
        "earned_return_unicode_root": "real_win32_non_acp_named_p1_p2_cold_boot_source_earned_records",
        "earned_return_cold_records": "fresh_native_process_unicode_root_validated_one_unchanged_urrun",
        "earned_run_sha256": earned_sha256,
        "five_destination_return": "one_sdl_p1_stock_x_back_then_main_b_reopens_painted_root",
        "controller_only_two_pad_root": "two_sdl_pads_title_practice_multiplayer_original_2p_admission",
        "controller_only_two_pad_race": "two_sdl_pads_original_2p_go_and_source_earned_pair",
        "controller_only_two_pad_race_result": two_pad_source_result,
        "controller_only_two_pad_race_pair_sha256": two_pad_pair_sha256,
        "lone_p2_pad": "remaining_p2_pad_promoted_to_p1_and_drives_root",
        "five_destination_pad": "one_sdl_p1_title_practice_multiplayer_records_options_play_stock_1p",
        "keyboard_plus_pad": "pad_moved_to_p2_and_stock_2p_entered",
        "two_virtual_pads": "distinct_host_seats_and_guest_2p_entry",
        "join_cancelled": "moved_pad_returned_to_p1_and_drives_root",
        "p2_owner_leaves": "p2_confirmation_withdrawn_no_2p",
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "Modern 2P join and one continuous five-destination title-to-stock "
                 "journey, actual two-pad source-scored match and stock-to-Modern return with SDL virtual "
                 "gamepads; mode 31 additionally earns a source-settled 1P "
                 "record; mode 32 attempts the same-controller post-result "
                 "root/earned-Records return. Physical controllers, genuine "
                 "Repeat, physical 2P, and release acceptance remain outstanding",
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
