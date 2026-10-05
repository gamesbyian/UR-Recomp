#!/usr/bin/env python3
"""Patch the one stock tour-confirm generation snapshot store in generated C.

The canonical ROM has one stock writer to SRAM $77:10D1 at $80:E6BF.
SNESRecomp v2 emits an 8-bit long store as:

    cpu_write8(cpu, 0x77, (uint16)(0x10d1), _vN);

This patcher accepts a generated source file or directory, requires exactly one
matching store across all C sources, and wraps only its value through the
title-owned challenge-generation bridge. Zero or multiple matches fail closed.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

STORE_RE = re.compile(
    r"cpu_write8\(cpu,\s*0x77,\s*\(uint16\)\(0x10d1\),\s*"
    r"(?P<value>_v\d+)\);"
)
INCLUDE = '#include "uniracers_challenge_generation_bridge.h"\n'
MARKER = "ur_uniracers_challenge_generation_filter("


def candidate_files(root: pathlib.Path) -> list[pathlib.Path]:
    if root.is_file():
        return [root]
    return sorted(p for p in root.rglob("*.c") if p.is_file())


def patch_sources(root: pathlib.Path) -> pathlib.Path:
    matches: list[tuple[pathlib.Path, re.Match[str]]] = []
    for path in candidate_files(root):
        text = path.read_text(encoding="utf-8")
        if MARKER in text:
            # Idempotence is accepted only when there is exactly one already
            # patched generated store across the supplied source set.
            if "0x10d1" in text:
                matches.append((path, None))  # type: ignore[arg-type]
            continue
        for match in STORE_RE.finditer(text):
            matches.append((path, match))

    if len(matches) != 1:
        raise ValueError(
            "expected exactly one generated SRAM 77:10D1 byte store; "
            f"found {len(matches)}"
        )

    path, match = matches[0]
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return path

    assert match is not None
    value = match.group("value")
    replacement = (
        "cpu_write8(cpu, 0x77, (uint16)(0x10d1), "
        f"ur_uniracers_challenge_generation_filter({value}));"
    )
    text = text[:match.start()] + replacement + text[match.end():]

    if INCLUDE not in text:
        # Generated units have their include block at the top. Keep this
        # title-owned dependency explicit and deterministic.
        text = INCLUDE + text

    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("generated", type=pathlib.Path)
    args = ap.parse_args()
    try:
        patched = patch_sources(args.generated)
    except (OSError, ValueError) as exc:
        print(f"challenge-generation generated patch failed: {exc}",
              file=sys.stderr)
        return 2
    print(patched)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
