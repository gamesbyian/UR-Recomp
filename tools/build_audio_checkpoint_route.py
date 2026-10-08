#!/usr/bin/env python3
"""Slice the existing first-race route at a named dump without changing inputs.

A fresh-process SDL disk capture can then stop at the same semantic boundary
as the independent Snes9x/Beetle audio references. This is a route-prefix
materializer, not a new game input model or an audio sample clock.
"""
from __future__ import annotations

import argparse
from pathlib import Path

CHECKPOINTS = ("main-menu-ready", "now-playing-ready", "race-entered")


def checkpoint_route(source: str, checkpoint: str) -> str:
    if checkpoint not in CHECKPOINTS:
        raise ValueError(f"unsupported native audio checkpoint {checkpoint!r}")
    lines = source.splitlines()
    target = "dump " + checkpoint
    matches = [i for i, line in enumerate(lines) if line.strip() == target]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {target!r} in canonical route")
    index = matches[0]
    commands = []
    for line in lines[:index + 1]:
        token = line.split("#", 1)[0].strip()
        if not token:
            continue
        if token == "quit":
            raise ValueError(f"route quits before checkpoint {checkpoint}")
        if token.startswith("dump "):
            # Retain earlier named checkpoints as observable source evidence.
            pass
        commands.append(token)
    if not commands or commands[-1] != target:
        raise ValueError("checkpoint extraction did not end at the required dump")
    return (
        "# Derived from canonical tests/input/reach-first-race.script.\n"
        f"# Audio capture stops after observed {checkpoint}, no guest pokes.\n"
        + "\n".join(commands) + "\nquit\n"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("checkpoint", choices=CHECKPOINTS)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    script = checkpoint_route(args.source.read_text(encoding="utf-8"), args.checkpoint)
    args.output.write_text(script, encoding="utf-8")
    print(f"NATIVE_AUDIO_ROUTE checkpoint={args.checkpoint} commands={len(script.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
