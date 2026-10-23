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
PROBE = re.compile(
    r"(?m)^UR_RESTART_INPUT raw=([0-9A-Fa-f]+) guest=([0-9A-Fa-f]+) "
    r"return_held=([01]) release_waiting=([01]) host_owned=([01]) "
    r"remaining=([0-9]+)$"
)


def validate_restart_guest_input(log: str) -> int:
    """Reject missing/partial samples and *any* leaked Start in the probe window.

    `release_waiting` is diagnostic only: an early-disarmed latch must not
    suppress the negative check. The host emits one countdown per guest sample.
    """
    # A malformed probe must not disappear from the evidence merely because
    # the strict regex cannot parse it. Otherwise twelve valid lines plus a
    # truncated or corrupt guest=1000 line would falsely pass this oracle.
    emitted = [line for line in log.splitlines()
               if line.startswith("UR_RESTART_INPUT")]
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
    return len(probes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="Native packaged-Windows Restart log")
    args = parser.parse_args()
    count = validate_restart_guest_input(
        args.log.read_text(encoding="utf-8", errors="replace")
    )
    print(f"UR_QA05_RESTART_GUEST_WORD=passed samples={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
