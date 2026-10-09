#!/usr/bin/env python3
"""Opt into the SNESRecomp span renderer in one disposable Baldosa route config.

UR's source OBJ capture is implemented in the modern PPU raster. Baldosa's
stock config chooses legacy rendering, which accepts the HD host callback but
returns a transparent overlay. This changes the host PPU raster policy only;
the original guest program, ROM and saved-player root remain untouched.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

KEY = re.compile(r"(?m)^(?P<prefix>\s*NewRenderer\s*=\s*)[^\r\n]*(?P<eol>\r?)$")
SECTION = re.compile(r"(?m)^\[Graphics\]\s*$")


def enable(config: Path) -> bool:
    contents = config.read_text(encoding="utf-8")
    if KEY.search(contents):
        updated = KEY.sub(lambda m: m.group("prefix") + "1" + m.group("eol"),
                          contents)
    else:
        match = SECTION.search(contents)
        if match:
            updated = contents[:match.end()] + "\nNewRenderer = 1" + contents[match.end():]
        else:
            updated = contents.rstrip() + "\n\n[Graphics]\nNewRenderer = 1\n"
    if updated != contents:
        config.write_text(updated, encoding="utf-8")
    return updated != contents


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--config", type=Path, required=True)
    args = a.parse_args()
    print("UR_BALDOSA_SOURCE_OBJ_CONFIG modern_ppu=1 changed=", int(enable(args.config)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
