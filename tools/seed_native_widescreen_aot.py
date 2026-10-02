#!/usr/bin/env python3
"""Seed the accepted Uniracers Widescreen preparation wrapper into native AOT generation."""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = 'name = "WidescreenPrepareWrapper"'
ENTRY = """
[[func]]
name = "WidescreenPrepareWrapper"
addr = "A52F"
bank = 1
emit = true
note = "Presentation-only strip preparation wrapper; native +8 hook seam at 81:A597..A59E"
""".lstrip()

def ensure_seed(symbols: Path) -> bool:
    text = symbols.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    if text and not text.endswith("\n"):
        text += "\n"
    symbols.write_text(text + "\n" + ENTRY, encoding="utf-8")
    return True

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", type=Path)
    args = ap.parse_args()
    changed = ensure_seed(args.symbols)
    print(f"{args.symbols}: {'seeded' if changed else 'already seeded'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
