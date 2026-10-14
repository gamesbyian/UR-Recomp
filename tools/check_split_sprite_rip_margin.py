#!/usr/bin/env python3
"""Check that split-screen sprite ripping stays hidden in the Widescreen margin.

Uniracers' split screen hides each viewport's copy of sprites 96-99 by
rewriting high-OAM byte $18 through HDMA mid-frame: `$A5` from line 0 and
`$5A` from line 112 (WIDESCREEN.md, "split-screen sprite ripping"). In the
top band sprites 96/97 carry X bit 8 with the small size, and in the bottom
band sprites 98/99 do. A hidden copy is therefore drawn at X - 256. Stock
clips it at the left screen edge, but the widened view exposes `margin`
extra pixels there, so a hidden copy whose right edge passes -margin would
leak into the margin.

The input is a `--framedump` directory of per-frame WRAM images. The game's
OAM shadow (low table at $1381, high table at $1581) holds each frame's
positions. Only frames whose high-OAM byte $18 shadow is one of the two rip
values count as split-screen frames.

This is a **WRAM-shadow geometry screening model**, not an actual effective
PPU OAM/OBJ raster validator. The CPU high-OAM shadow alone does not prove
the scanline-112 physical OAMDATA transfer, OBJ winner or final displayed
wide margin. A passing envelope must remain observational and cannot approve
HD racer, source visibility, widescreen OBJ culling or QA-08 fidelity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from tools.evidence_contract import assertion, make_envelope
except ModuleNotFoundError:
    from evidence_contract import assertion, make_envelope

OAM_LOW = 0x1381
OAM_HIGH = 0x1581
RIP_BYTE = 0x18
RIP_VALUES = (0xA5, 0x5A)
SPLIT_LINE = 112
VISIBLE_LINES = 224
SMALL_SIZE = 32  # OBSEL $83: 32x32 small / 64x64 large
DEFAULT_MARGIN = 43  # accepted 16:9 exposure per side (342x224)
WRAM_BYTES = 0x20000
FRAME_FILENAME = re.compile(r"frame_(\d{6})_wram\.bin\Z")

# Sprite -> lines on which the rip hides it (X bit 8 set, small size).
HIDDEN_BAND = {
    96: range(0, SPLIT_LINE),
    97: range(0, SPLIT_LINE),
    98: range(SPLIT_LINE, VISIBLE_LINES),
    99: range(SPLIT_LINE, VISIBLE_LINES),
}


def scan_frame(wram: bytes, margin: int) -> list[dict[str, int]] | None:
    """WRAM-shadow hidden-copy projection, NEVER measured final PPU pixels."""
    if len(wram) != WRAM_BYTES:
        raise ValueError("must read a complete 128 KiB WRAM shadow, not OAM alone")
    if not 0 <= margin <= 128:
        raise ValueError("logical left margin must be in the bounded 0..128 range")
    if wram[OAM_HIGH + RIP_BYTE] not in RIP_VALUES:
        return None
    hidden = []
    for sprite, band in HIDDEN_BAND.items():
        x = wram[OAM_LOW + sprite * 4]
        y = wram[OAM_LOW + sprite * 4 + 1]
        covered = [line for line in ((y + k) & 0xFF for k in range(SMALL_SIZE)) if line in band]
        if not covered:
            continue
        right_edge = x - 256 + SMALL_SIZE
        hidden.append({
            "sprite": sprite, "x": x, "y": y,
            "first_line": min(covered), "last_line": max(covered),
            "right_edge": right_edge,
            "leaks": int(right_edge > -margin),
        })
    return hidden


def scan(frames: Path, margin: int) -> dict[str, Any]:
    split_frames = 0
    hidden = 0
    leaks: list[dict[str, int]] = []
    max_right_edge = None
    seen_ids = set()
    for path in sorted(frames.glob("frame_*_wram.bin")):
        marker = FRAME_FILENAME.fullmatch(path.name)
        if marker is None:
            raise ValueError(f"WRAM filename is not an exact six-digit frame: {path.name}")
        frame = int(marker.group(1))
        if frame in seen_ids:
            raise ValueError(f"duplicate actual guest WRAM frame {frame}")
        seen_ids.add(frame)
        result = scan_frame(path.read_bytes(), margin)
        if result is None:
            continue
        split_frames += 1
        for item in result:
            hidden += 1
            if max_right_edge is None or item["right_edge"] > max_right_edge:
                max_right_edge = item["right_edge"]
            if item["leaks"] and len(leaks) < 16:
                leaks.append({"frame": frame, **item})
    return {
        "split_frames": split_frames,
        "hidden_copies": hidden,
        "source_basis": "WRAM high-OAM shadow and synthetic physical-rip geometry",
        "actual_live_PPU_OAM_HDMA_state_observed": False,
        "final_PPU_visible_sprite_pixels_checked": False,
        "authorizes_widescreen_HD_sprite_admission": False,
        "max_hidden_right_edge": max_right_edge,
        "clearance_px": None if max_right_edge is None else -margin - max_right_edge,
        "leaks": leaks,
    }


def check(route: str, frames: Path, margin: int, min_split_frames: int) -> dict[str, Any]:
    if min_split_frames < 1:
        raise ValueError("at least one independently identified split WRAM frame is required")
    if not 0 <= margin <= 128:
        raise ValueError("logical left margin must be in the bounded 0..128 range")
    metrics = scan(frames, margin)
    return make_envelope(
        evidence_type="split-sprite-rip-margin",
        producer="tools/check_split_sprite_rip_margin.py",
        subject={"route": route},
        inputs={"margin": margin, "min_split_frames": min_split_frames},
        metrics=metrics,
        assertions=[
            assertion(f"{route}-split-coverage",
                      metrics["split_frames"] >= min_split_frames and metrics["hidden_copies"] > 0,
                      {"split_frames": metrics["split_frames"],
                       "hidden_copies": metrics["hidden_copies"]}),
            assertion(f"{route}-WRAM-shadow-projected-hidden-copies-stay-out-of-margin",
                      not metrics["leaks"],
                      {"leaks": metrics["leaks"], "clearance_px": metrics["clearance_px"]}),
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", required=True)
    parser.add_argument("--frames", required=True, type=Path)
    parser.add_argument("--margin", type=int, default=DEFAULT_MARGIN)
    parser.add_argument("--min-split-frames", type=int, default=1)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    envelope = check(args.route, args.frames, args.margin, args.min_split_frames)
    rendered = json.dumps(envelope, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if envelope["outcome"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
