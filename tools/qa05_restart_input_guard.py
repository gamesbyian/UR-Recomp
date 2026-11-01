#!/usr/bin/env python3
"""Check the twelve real guest-input samples immediately after Modern Restart.

This validates a Windows diagnostic log, not an independent guest or audio oracle.
The stock route never intentionally presses Start during this short window.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

EXPECTED_SAMPLES = 12  # g_restart_input_probe_remaining in the native host.
GUEST_START = 0x1000
P2_GUEST_START = 0x0100  # Unshifted 12-bit second-player word.
PROBE = re.compile(
    r"(?m)^UR_RESTART_INPUT raw=([0-9A-Fa-f]+) guest=([0-9A-Fa-f]+) "
    r"return_held=([01]) release_waiting=([01]) host_owned=([01]) "
    r"remaining=([0-9]+)$"
)
P2_PROBE = re.compile(
    r"(?m)^UR_RESTART_INPUT_P2 raw=([0-9A-Fa-f]+) guest=([0-9A-Fa-f]+) "
    r"return_held=([01]) release_waiting=([01]) remaining=([0-9]+)$"
)


def validate_restart_p2_guest_input(
        log: str, *, require_raw_start_witness: bool = False) -> int:
    """Validate P2 when present; allow old P1-only retained logs.

    A P1-only log cannot establish P2 coverage. New native producers emit
    both probes, so every P2 line must parse and the complete P2 countdown
    must exclude its raw 12-bit Start from the guest word. The optional strict
    mode additionally demands a non-vacuous raw P2 Start while Return is held
    and the release latch is active; default mode retains P1-only log support.
    """
    emitted = [line for line in log.splitlines()
               if line.startswith("UR_RESTART_INPUT_P2")]
    if not emitted:
        if require_raw_start_witness:
            raise ValueError('P2 raw Start/held Return witness absent')
        return 0
    probes = list(P2_PROBE.finditer(log))
    if len(emitted) != len(probes):
        raise ValueError(
            f"malformed UR_RESTART_INPUT_P2 diagnostic: "
            f"{len(emitted)} emitted, {len(probes)} parsed"
        )
    if len(probes) != EXPECTED_SAMPLES:
        raise ValueError(
            f"expected {EXPECTED_SAMPLES} P2 post-Restart guest-word samples, "
            f"observed {len(probes)}"
        )
    saw_held_raw_start = False
    for index, match in enumerate(probes):
        raw, guest, held, waiting, remaining = match.groups()
        if (int(raw, 16) & P2_GUEST_START and held == '1'
                and waiting == '1'):
            saw_held_raw_start = True
        expected_remaining = EXPECTED_SAMPLES - index - 1
        if int(remaining) != expected_remaining:
            raise ValueError(
                f"P2 post-Restart sample {index + 1}: expected remaining="
                f"{expected_remaining}, observed {remaining}"
            )
        if int(guest, 16) & P2_GUEST_START:
            raise ValueError(
                f"P2 post-Restart sample {index + 1}: guest Start leaked "
                f"(raw={raw}, guest={guest}, return_held={held}, "
                f"release_waiting={waiting})"
            )
    if require_raw_start_witness and not saw_held_raw_start:
        raise ValueError('P2 raw Start/held Return witness absent')
    return len(probes)


def validate_restart_guest_input(
        log: str, *, require_p2_start_witness: bool = False) -> int:
    """Reject missing/partial samples and *any* leaked Start in the probe window.

    `release_waiting` is diagnostic only: an early-disarmed latch must not
    suppress the negative check. The host emits one countdown per guest sample.
    """
    # A malformed probe must not disappear from the evidence merely because
    # the strict regex cannot parse it. Otherwise twelve valid lines plus a
    # truncated or corrupt guest=1000 line would falsely pass this oracle.
    # The P2 namespace is separately parsed below. All other lines claiming
    # the P1 diagnostic prefix must count, including missing separators,
    # truncated words and unexpected seat suffixes. Counting only the exact
    # prefix with a space would silently discard malformed extra P1 records.
    emitted = [line for line in log.splitlines()
               if line.startswith("UR_RESTART_INPUT")
               and not line.startswith("UR_RESTART_INPUT_P2")]
    probes = list(PROBE.finditer(log))
    if len(emitted) != len(probes):
        raise ValueError(
            f"malformed UR_RESTART_INPUT diagnostic: "
            f"{len(emitted)} emitted, {len(probes)} parsed"
        )
    if len(probes) != EXPECTED_SAMPLES:
        raise ValueError(
            f"expected {EXPECTED_SAMPLES} post-Restart guest-word samples, "
            f"observed {len(probes)}"
        )
    for index, match in enumerate(probes):
        raw, guest, held, waiting, host_owned, remaining = match.groups()
        expected_remaining = EXPECTED_SAMPLES - index - 1
        if int(remaining) != expected_remaining:
            raise ValueError(
                f"post-Restart sample {index + 1}: expected remaining="
                f"{expected_remaining}, observed {remaining}"
            )
        if int(guest, 16) & GUEST_START:
            raise ValueError(
                f"post-Restart sample {index + 1}: guest Start leaked "
                f"(raw={raw}, guest={guest}, return_held={held}, "
                f"release_waiting={waiting}, host_owned={host_owned})"
            )
    validate_restart_p2_guest_input(
        log, require_raw_start_witness=require_p2_start_witness)
    return len(probes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="Native packaged-Windows Restart log")
    parser.add_argument(
        '--require-p2-start-witness', action='store_true',
        help='For a real two-seat Restart acceptance, require observed raw P2 Start while Return is held and its release latch is active')
    args = parser.parse_args()
    log = args.log.read_text(encoding="utf-8", errors="replace")
    count = validate_restart_guest_input(
        log, require_p2_start_witness=args.require_p2_start_witness)
    print(f"UR_QA05_RESTART_GUEST_WORD=passed samples={count}")
    p2_count = validate_restart_p2_guest_input(
        log, require_raw_start_witness=args.require_p2_start_witness)
    if p2_count:
        print(f"UR_QA05_RESTART_P2_GUEST_WORD=passed samples={p2_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
