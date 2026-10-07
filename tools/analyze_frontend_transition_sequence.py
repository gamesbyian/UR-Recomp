#!/usr/bin/env python3
"""Characterize a dense frontend transition from retained BGRX8888 frames.

This is evidence tooling, not a renderer. It reports exact per-frame pixel
change plus a sampled horizontal-translation discriminator. A non-zero shift is
only evidence when it improves agreement over the zero-shift baseline.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

DEFAULT_WIDTH = 256
BYTES_PER_PIXEL = 4
FRAME_RE = re.compile(r"^(?P<prefix>.+)-(?P<index>\d+)\.fb\.bgrx$")


def load_sequence(
    directory: Path,
    *,
    prefix: str = "title-motion",
    width: int = DEFAULT_WIDTH,
) -> list[tuple[int, bytes]]:
    if width <= 0:
        raise ValueError("width must be positive")
    rows: list[tuple[int, bytes]] = []
    for path in directory.glob(f"{prefix}-*.fb.bgrx"):
        match = FRAME_RE.match(path.name)
        if not match or match.group("prefix") != prefix:
            continue
        payload = path.read_bytes()
        row_bytes = width * BYTES_PER_PIXEL
        if not payload or len(payload) % row_bytes:
            raise ValueError(
                f"{path.name}: frame size {len(payload)} is not "
                f"whole-row BGRX for width {width}"
            )
        rows.append((int(match.group("index")), payload))
    rows.sort(key=lambda row: row[0])
    if len(rows) < 2:
        raise ValueError("need at least two transition frames")
    for (left, _), (right, _) in zip(rows, rows[1:]):
        if right != left + 1:
            raise ValueError(
                f"transition frame indices are not consecutive: {left} -> {right}"
            )
    frame_size = len(rows[0][1])
    if any(len(payload) != frame_size for _, payload in rows):
        raise ValueError("transition frame geometry changed inside sequence")
    return rows


def changed_metrics(
    before: bytes,
    after: bytes,
    *,
    width: int,
) -> dict:
    if len(before) != len(after):
        raise ValueError("frame sizes differ")
    row_bytes = width * BYTES_PER_PIXEL
    if width <= 0 or not before or len(before) % row_bytes:
        raise ValueError("invalid frame geometry")
    height = len(before) // row_bytes

    changed = 0
    x0 = width
    y0 = height
    x1 = -1
    y1 = -1
    for y in range(height):
        row = y * row_bytes
        for x in range(width):
            pos = row + x * BYTES_PER_PIXEL
            if before[pos : pos + BYTES_PER_PIXEL] == after[pos : pos + BYTES_PER_PIXEL]:
                continue
            changed += 1
            x0 = min(x0, x)
            y0 = min(y0, y)
            x1 = max(x1, x)
            y1 = max(y1, y)

    return {
        "changed_pixels": changed,
        "changed_fraction": changed / (width * height),
        "bbox_inclusive": None if changed == 0 else [x0, y0, x1, y1],
    }


def horizontal_agreement(
    before: bytes,
    after: bytes,
    *,
    width: int,
    shift: int,
    sample_step: int = 4,
) -> float:
    """Agreement if content in before moved horizontally by shift.

    Positive shift means content moved right: after(x,y) is compared to
    before(x-shift,y). Sampling is deterministic and excludes newly exposed
    edge columns.
    """
    if len(before) != len(after):
        raise ValueError("frame sizes differ")
    if width <= 0 or sample_step <= 0:
        raise ValueError("width/sample_step must be positive")
    row_bytes = width * BYTES_PER_PIXEL
    if not before or len(before) % row_bytes:
        raise ValueError("invalid frame geometry")
    if abs(shift) >= width:
        return 0.0

    height = len(before) // row_bytes
    x_start = max(0, shift)
    x_end = min(width, width + shift)
    matched = 0
    total = 0
    for y in range(0, height, sample_step):
        row = y * row_bytes
        for x in range(x_start, x_end, sample_step):
            before_x = x - shift
            a = row + before_x * BYTES_PER_PIXEL
            b = row + x * BYTES_PER_PIXEL
            total += 1
            if before[a : a + BYTES_PER_PIXEL] == after[b : b + BYTES_PER_PIXEL]:
                matched += 1
    return matched / total if total else 0.0



def vertical_agreement(
    before: bytes,
    after: bytes,
    *,
    width: int,
    shift: int,
    sample_step: int = 4,
) -> float:
    """Agreement if content in before moved vertically by shift.

    Positive shift means content moved down: after(x,y) is compared to
    before(x,y-shift). Sampling is deterministic and excludes newly exposed
    edge rows.
    """
    if len(before) != len(after):
        raise ValueError("frame sizes differ")
    if width <= 0 or sample_step <= 0:
        raise ValueError("width/sample_step must be positive")
    row_bytes = width * BYTES_PER_PIXEL
    if not before or len(before) % row_bytes:
        raise ValueError("invalid frame geometry")

    height = len(before) // row_bytes
    if abs(shift) >= height:
        return 0.0
    y_start = max(0, shift)
    y_end = min(height, height + shift)
    matched = 0
    total = 0
    for y in range(y_start, y_end, sample_step):
        before_y = y - shift
        before_row = before_y * row_bytes
        after_row = y * row_bytes
        for x in range(0, width, sample_step):
            a = before_row + x * BYTES_PER_PIXEL
            b = after_row + x * BYTES_PER_PIXEL
            total += 1
            if before[a : a + BYTES_PER_PIXEL] == after[b : b + BYTES_PER_PIXEL]:
                matched += 1
    return matched / total if total else 0.0


def best_vertical_shift(
    before: bytes,
    after: bytes,
    *,
    width: int,
    max_shift: int = 16,
    sample_step: int = 4,
) -> dict:
    if max_shift < 0:
        raise ValueError("max_shift must be non-negative")
    row_bytes = width * BYTES_PER_PIXEL
    if width <= 0 or not before or len(before) % row_bytes:
        raise ValueError("invalid frame geometry")
    height = len(before) // row_bytes
    bounded = min(max_shift, max(0, height - 1))
    scores = {
        shift: vertical_agreement(
            before,
            after,
            width=width,
            shift=shift,
            sample_step=sample_step,
        )
        for shift in range(-bounded, bounded + 1)
    }
    best = max(
        scores,
        key=lambda shift: (scores[shift], -abs(shift), -shift),
    )
    zero = scores.get(0, 0.0)
    return {
        "best_vertical_shift_pixels": best,
        "best_vertical_agreement": scores[best],
        "zero_vertical_shift_agreement": zero,
        "vertical_agreement_gain": scores[best] - zero,
    }

def best_horizontal_shift(
    before: bytes,
    after: bytes,
    *,
    width: int,
    max_shift: int = 16,
    sample_step: int = 4,
) -> dict:
    if max_shift < 0:
        raise ValueError("max_shift must be non-negative")
    scores = {
        shift: horizontal_agreement(
            before,
            after,
            width=width,
            shift=shift,
            sample_step=sample_step,
        )
        for shift in range(-max_shift, max_shift + 1)
    }
    best = max(
        scores,
        key=lambda shift: (scores[shift], -abs(shift), -shift),
    )
    zero = scores.get(0, 0.0)
    return {
        "best_shift_pixels": best,
        "best_agreement": scores[best],
        "zero_shift_agreement": zero,
        "agreement_gain": scores[best] - zero,
    }


def analyze_sequence(
    frames: list[tuple[int, bytes]],
    *,
    width: int = DEFAULT_WIDTH,
    max_shift: int = 16,
    sample_step: int = 4,
) -> dict:
    if len(frames) < 2:
        raise ValueError("need at least two transition frames")

    pairs: list[dict] = []
    for (left_index, before), (right_index, after) in zip(frames, frames[1:]):
        if right_index != left_index + 1:
            raise ValueError("frame indices must be consecutive")
        change = changed_metrics(before, after, width=width)
        motion = best_horizontal_shift(
            before,
            after,
            width=width,
            max_shift=max_shift,
            sample_step=sample_step,
        )
        vertical_motion = best_vertical_shift(
            before,
            after,
            width=width,
            max_shift=max_shift,
            sample_step=sample_step,
        )
        pairs.append({
            "from_index": left_index,
            "to_index": right_index,
            **change,
            **motion,
            **vertical_motion,
        })

    useful_motion = [
        row for row in pairs
        if row["best_shift_pixels"] != 0 and row["agreement_gain"] >= 0.05
    ]
    useful_vertical_motion = [
        row for row in pairs
        if row["best_vertical_shift_pixels"] != 0
        and row["vertical_agreement_gain"] >= 0.05
    ]
    histogram = Counter(row["best_shift_pixels"] for row in useful_motion)
    vertical_histogram = Counter(
        row["best_vertical_shift_pixels"] for row in useful_vertical_motion
    )
    changed_pairs = [row for row in pairs if row["changed_pixels"] > 0]
    dominant = None
    dominant_vertical = None
    if histogram:
        dominant = sorted(
            histogram.items(),
            key=lambda item: (-item[1], abs(item[0]), item[0]),
        )[0][0]
    if vertical_histogram:
        dominant_vertical = sorted(
            vertical_histogram.items(),
            key=lambda item: (-item[1], abs(item[0]), item[0]),
        )[0][0]

    return {
        "schema_version": 1,
        "frame_count": len(frames),
        "pair_count": len(pairs),
        "changed_pair_count": len(changed_pairs),
        "first_changed_pair": (
            changed_pairs[0]["from_index"] if changed_pairs else None
        ),
        "last_changed_pair": (
            changed_pairs[-1]["to_index"] if changed_pairs else None
        ),
        "motion_candidate_pair_count": len(useful_motion),
        "vertical_motion_candidate_pair_count": len(useful_vertical_motion),
        "dominant_horizontal_shift_pixels": dominant,
        "dominant_vertical_shift_pixels": dominant_vertical,
        "motion_shift_histogram": {
            str(key): value for key, value in sorted(histogram.items())
        },
        "vertical_motion_shift_histogram": {
            str(key): value
            for key, value in sorted(vertical_histogram.items())
        },
        "pairs": pairs,
        "interpretation": (
            "Non-zero horizontal or vertical shift is only a candidate when "
            "sampled agreement improves over that axis's zero-shift baseline "
            "by >= 0.05. Palette/layer changes may still require separate "
            "interpretation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--prefix", default="title-motion")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--max-shift", type=int, default=16)
    parser.add_argument("--sample-step", type=int, default=4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    frames = load_sequence(
        args.directory,
        prefix=args.prefix,
        width=args.width,
    )
    report = analyze_sequence(
        frames,
        width=args.width,
        max_shift=args.max_shift,
        sample_step=args.sample_step,
    )
    payload = json.dumps(report, indent=2) + "\n"
    print(payload, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
