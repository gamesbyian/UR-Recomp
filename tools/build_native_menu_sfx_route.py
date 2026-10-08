#!/usr/bin/env python3
"""Exact three-event stock-menu SFX route shared with the pinned SNES reference.

Reuse the existing reference probe's original controller events rather than
maintaining a second interpretation of menu actions. All events are guest
input; the modern frontend and sound assets remain completely untouched.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from probe_menu_sfx_ids import FRONTEND, SETTLE, script

EVENT_NAMES = (
    "main_cursor_down",
    "main_cursor_up",
    "main_confirm_1p_slide",
)


def build() -> str:
    events = FRONTEND[:len(EVENT_NAMES)]
    if tuple(name for name, _ in events) != EVENT_NAMES:
        raise ValueError("reference SFX route no longer has the validated three-event prefix")
    route = script(events, SETTLE)
    if "poke " in route or route.count("quit") != 1:
        raise ValueError("original menu SFX route unexpectedly mutates guest state")
    return route


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(), encoding="utf-8")
    print("NATIVE_MENU_SFX_ROUTE PASS source=stock_reference_probe events=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
