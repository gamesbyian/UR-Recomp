#!/usr/bin/env python3
"""Seed Uniracers' accepted Widescreen preparation wrapper into native AOT generation.

The pinned SNESRecomp revision consumes bank*.cfg directly during generation.
Keep symbols.toml in sync for newer framework revisions, but make the bank-01
root explicit so this project's pinned toolchain remains deterministic.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SYMBOL_MARKER = 'name = "WidescreenPrepareWrapper"'
SYMBOL_ENTRY = """
[[func]]
name = "WidescreenPrepareWrapper"
addr = "A52F"
bank = 1
emit = true
note = "Presentation-only strip preparation wrapper; native +8 hook seam at 81:A597..A59E"
""".lstrip()

CFG_MARKER = "func WidescreenPrepareWrapper A52F"
CFG_ENTRY = """
# UR-Recomp Widescreen presentation-only AOT root.
func WidescreenPrepareWrapper A52F
""".lstrip()

EXTRA_BANK = 2
EXTRA_ADDR = "D2" + "D1"
EXTRA_NAME = "WidescreenPostConsume"
EXTRA_SYMBOL_MARKER = 'name = "WidescreenPostConsume"'

def _append_once(path: Path, marker: str, entry: str, *, prefix: str = "") -> bool:
    text = path.read_text(encoding="utf-8") if path.exists() else prefix
    if marker in text:
        return False
    if text and not text.endswith("\n"):
        text += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + ("\n" if text else "") + entry, encoding="utf-8")
    return True

def ensure_seed(cfg_dir: Path) -> dict[str, bool]:
    symbols = cfg_dir / "symbols.toml"
    bank01 = cfg_dir / "bank01.cfg"
    bank_extra = cfg_dir / f"bank{EXTRA_BANK:02d}.cfg"
    extra_marker = f"func {EXTRA_NAME} {EXTRA_ADDR}"
    extra_entry = f"# UR-Recomp Widescreen presentation-only consume root.\n{extra_marker}\n"
    extra_symbol_entry = (
        f"\n[[func]]\nname = \"{EXTRA_NAME}\"\naddr = \"{EXTRA_ADDR}\"\n"
        f"bank = {EXTRA_BANK}\nemit = true\n"
        "note = \"Presentation-only post-consume cleanup seam for native Widescreen staging\"\n"
    )
    symbol_prepare = _append_once(symbols, SYMBOL_MARKER, SYMBOL_ENTRY)
    symbol_extra = _append_once(symbols, EXTRA_SYMBOL_MARKER, extra_symbol_entry)
    return {
        "symbols": symbol_prepare or symbol_extra,
        "bank01": _append_once(
            bank01,
            CFG_MARKER,
            CFG_ENTRY,
            prefix="bank = 1\ntier_down_stubs\n",
        ),
        "bank02": _append_once(
            bank_extra,
            extra_marker,
            extra_entry,
            prefix=f"bank = {EXTRA_BANK}\ntier_down_stubs\n",
        ),
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cfg_dir", type=Path)
    args = ap.parse_args()
    changed = ensure_seed(args.cfg_dir)
    states = ", ".join(f"{k}={'seeded' if v else 'present'}" for k, v in changed.items())
    print(f"{args.cfg_dir}: {states}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
