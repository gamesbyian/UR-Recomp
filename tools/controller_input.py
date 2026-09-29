#!/usr/bin/env python3
"""Shared deterministic controller-stream parser.

Canonical rows are:

    start:duration:p1-mask[:p2-mask]

Masks use the project's 12-bit SNES button layout. The legacy three-field form
is preserved exactly and means P2 is idle. Runs may overlap when they affect
different players, but intervals for the same player may not overlap.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ControllerRun:
    start: int
    duration: int
    p1_mask: int
    p2_mask: int = 0

    @property
    def end(self) -> int:
        return self.start + self.duration


def load_controller_runs(path: Path) -> list[ControllerRun]:
    out: list[ControllerRun] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split(":")
        if len(parts) not in {3, 4}:
            raise ValueError(
                f"{path}:{lineno}: expected start:duration:p1-mask[:p2-mask]"
            )
        try:
            start = int(parts[0], 0)
            duration = int(parts[1], 0)
            p1_mask = int(parts[2], 16)
            p2_mask = int(parts[3], 16) if len(parts) == 4 else 0
        except ValueError as exc:
            raise ValueError(f"{path}:{lineno}: invalid input row {raw!r}") from exc
        if start < 0 or duration < 1:
            raise ValueError(f"{path}:{lineno}: start must be >=0 and duration >=1")
        if p1_mask & ~0xFFF or p2_mask & ~0xFFF:
            raise ValueError(f"{path}:{lineno}: controller masks must fit 12 bits")
        if p1_mask == 0 and p2_mask == 0:
            raise ValueError(f"{path}:{lineno}: row has no controller input")
        out.append(ControllerRun(start, duration, p1_mask, p2_mask))

    out.sort(key=lambda run: (run.start, run.end, run.p1_mask, run.p2_mask))
    for player, attr in ((1, "p1_mask"), (2, "p2_mask")):
        active = [run for run in out if getattr(run, attr)]
        previous_end = 0
        for run in active:
            if run.start < previous_end:
                raise ValueError(
                    f"{path}: overlapping player-{player} input intervals are not supported"
                )
            previous_end = run.end
    return out


def masks_at(runs: list[ControllerRun], frame: int) -> tuple[int, int]:
    p1 = 0
    p2 = 0
    for run in runs:
        if run.start > frame:
            break
        if frame < run.end:
            p1 |= run.p1_mask
            p2 |= run.p2_mask
    return p1, p2
