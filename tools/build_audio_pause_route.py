#!/usr/bin/env python3
"""Derive stock Start pause/resume audio phase probes from an existing guest route.

This is NOT the Modern host-owned pause menu, which freezes guest execution.
Only the existing authoritative ui-pause-route.script and its guest Start
edges are allowed as inputs; no invented pause policy or WRAM writes.
"""
from __future__ import annotations

import argparse
from pathlib import Path

CHECKPOINTS = ("ui-pause-before", "ui-pause-after-start", "ui-pause-after-resume")
POST_CHECKPOINT_FRAMES = 30
EXPECTED_START_PRESSES = {
    "ui-pause-before": 0,
    "ui-pause-after-start": 1,
    "ui-pause-after-resume": 2,
}


def pause_checkpoint_route(source: str, checkpoint: str) -> str:
    if checkpoint not in CHECKPOINTS:
        raise ValueError(f"unsupported stock pause audio checkpoint {checkpoint!r}")
    lines = source.splitlines()
    target = f"dump {checkpoint}"
    matches = [i for i, line in enumerate(lines) if line.strip() == target]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {target!r} in canonical pause route")
    prefix = []
    for line in lines[: matches[0] + 1]:
        command = line.split("#", 1)[0].strip()
        if not command:
            continue
        if command == "quit" or command.startswith("poke "):
            raise ValueError("stock pause route may not quit/poke before checkpoint")
        prefix.append(command)
    if not prefix or prefix[-1] != target:
        raise ValueError("stock pause route does not end at observed checkpoint")
    count = prefix.count("press start 2")
    if count != EXPECTED_START_PRESSES[checkpoint]:
        raise ValueError(
            f"{checkpoint}: expected {EXPECTED_START_PRESSES[checkpoint]} "
            f"stock Start presses, found {count}"
        )
    if "until 0313 == 01 1800" not in prefix:
        raise ValueError("stock pause route must reach observed active race before Start")
    return (
        "# Prefix of tests/input/ui-pause-route.script. Only original guest Start input.\n"
        "# Diagnostic stock Start pause/resume; NOT Modern host freeze/resume.\n"
        + "\n".join(prefix)
        + f"\nwait {POST_CHECKPOINT_FRAMES}\n"
        + f"dump {checkpoint}-audio-post\nquit\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("checkpoint", choices=CHECKPOINTS)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    script = pause_checkpoint_route(args.source.read_text(encoding="utf-8"), args.checkpoint)
    args.output.write_text(script, encoding="utf-8")
    print(f"STOCK_PAUSE_AUDIO_ROUTE checkpoint={args.checkpoint} start_presses={EXPECTED_START_PRESSES[args.checkpoint]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
