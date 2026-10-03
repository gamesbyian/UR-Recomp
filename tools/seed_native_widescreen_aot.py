#!/usr/bin/env python3
"""Seed Uniracers' accepted Widescreen preparation wrapper into native AOT generation.

The pinned SNESRecomp revision consumes bank*.cfg directly during generation.
Keep symbols.toml in sync for newer framework revisions, but make the live bank-03
race-frame root explicit so this project's pinned toolchain remains deterministic.
"""
from __future__ import annotations

import argparse
from pathlib import Path

CALLER_BANK = 3
CALLER_ADDR = "CBCC"
CALLER_NAME = "RaceFrameOrchestratorLoop"
CALLER_SYMBOL_MARKER = 'name = "RaceFrameOrchestratorLoop"'

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
    bank_caller = cfg_dir / f"bank{CALLER_BANK:02d}.cfg"
    caller_marker = f"func {CALLER_NAME} {CALLER_ADDR}"
    caller_entry = f"# UR-Recomp accepted race-frame orchestrator seed.\n{caller_marker}\n"
    caller_symbol_entry = (
        f"\n[[func]]\nname = \"{CALLER_NAME}\"\naddr = \"{CALLER_ADDR}\"\n"
        f"bank = {CALLER_BANK}\nemit = true\n"
        "note = \"Trusted race-frame orchestrator entry containing 83:CD55 -> 81:A52B\"\n"
    )
    symbol_caller = _append_once(symbols, CALLER_SYMBOL_MARKER, caller_symbol_entry)
    return {
        "symbols": symbol_caller,
        "bank03": _append_once(
            bank_caller,
            caller_marker,
            caller_entry,
            prefix=f"bank = {CALLER_BANK}\ntier_down_stubs\n",
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
