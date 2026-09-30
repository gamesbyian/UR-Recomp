#!/usr/bin/env python3
"""Compare active-display SNES OAM target models for one high-OAM write.

This is deliberately a *model discriminator*, not an emulator.  It captures
only the source-level address rules already pinned in the compatibility
research so a future runtime fixture has an exact minimal question to answer.

For the Uniracers VS seam the live sprite index is 96, and all compared models
converge on physical OAM byte 0x218.  Changing only the live sprite index
separates fixed-target compatibility hacks from sprite-pipeline models.
"""
from __future__ import annotations

import argparse
import json


HIGH_OAM_BASE = 0x200
SNES9X_UNIRACERS_OAM_ADDR = 0x10C
MAME_ACTIVE_OAM_TARGET = 0x218


def snes9x_uniracers_first_high_byte() -> int:
    """Pinned Snes9x hack: OAMAddr=0x10C, OAMFlip=0 before $2104 HDMA."""
    return ((SNES9X_UNIRACERS_OAM_ADDR & 0x10F) << 1)


def mame_active_target() -> int:
    """Pinned MAME approximation: all active-display OAM accesses -> 0x218."""
    return MAME_ACTIVE_OAM_TARGET


def ares_active_high_target(live_sprite_index: int) -> int:
    """Pinned ares rule for an active-display high-OAM access."""
    if not 0 <= live_sprite_index <= 127:
        raise ValueError("live sprite index must be 0..127")
    return HIGH_OAM_BASE | (live_sprite_index >> 2)


def jgenesis_active_high_target(live_sprite_index: int) -> int:
    """Pinned jgenesis high-OAM array index converted to physical OAM byte."""
    if not 0 <= live_sprite_index <= 127:
        raise ValueError("live sprite index must be 0..127")
    return HIGH_OAM_BASE + (live_sprite_index >> 2)


def compare(live_sprite_index: int) -> dict:
    targets = {
        "snes9x_uniracers": snes9x_uniracers_first_high_byte(),
        "mame": mame_active_target(),
        "ares": ares_active_high_target(live_sprite_index),
        "jgenesis": jgenesis_active_high_target(live_sprite_index),
    }
    groups: dict[int, list[str]] = {}
    for model, target in targets.items():
        groups.setdefault(target, []).append(model)
    return {
        "schema_version": 1,
        "live_sprite_index": live_sprite_index,
        "targets": {name: f"0x{target:03X}" for name, target in targets.items()},
        "all_converge": len(groups) == 1,
        "target_groups": [
            {
                "target": f"0x{target:03X}",
                "models": sorted(models),
            }
            for target, models in sorted(groups.items())
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--sprite-index",
        type=lambda x: int(x, 0),
        default=96,
        help="live sprite evaluator/fetch index (default: 96)",
    )
    ap.add_argument("--json-out")
    args = ap.parse_args()
    report = compare(args.sprite_index)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.json_out:
        from pathlib import Path
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
