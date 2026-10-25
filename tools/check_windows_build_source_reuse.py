#!/usr/bin/env python3
"""Reject drift between source-preserved Windows build and build-only producer."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
REUSE = ROOT / ".github/workflows/windows-exact-build-only.yml"
BUILD_STEPS = (
    "Guard guest CRC, pause witness and Modern mutable-root stage",
    "Verify immutable native source pins",
    "Stage only the verified UR native boundary",
    "Use Baldosa's already-proven Windows clang toolchain path",
    "Build real native AOT Windows x64 title plus UR host bridges",
)


def get_body(data: str, name: str) -> str:
    lines = data.splitlines()
    header = "      - name: " + name
    matches = [i for i, line in enumerate(lines) if line == header]
    if len(matches) != 1:
        raise ValueError(f"{name}: missing/duplicate source step")
    index = matches[0] + 1
    if lines[index] != "        run: |":
        raise ValueError(f"{name}: build step changed to non-shell or conditional")
    body = []
    for line in lines[index + 1:]:
        if line.startswith("          "):
            body.append(line[10:])
        elif line.strip():
            break
        else:
            body.append("")
    while body and not body[-1].strip():
        body.pop()
    result = "\n".join(body) + "\n"
    if not result.strip():
        raise ValueError("empty original build source step " + name)
    return result


def audit(source: str, reuse: str) -> None:
    for name in BUILD_STEPS:
        old = get_body(source, name)
        new = get_body(reuse, name)
        if old != new:
            raise ValueError("build-only producer silently diverged from original native Windows step: " + name)
    if not reuse.count("name: qa-baldosa-native-export") == 1:
        raise ValueError("expected exactly one shared candidate export")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--reuse", type=Path, default=REUSE)
    args = p.parse_args()
    audit(args.source.read_text(encoding="utf-8"),
          args.reuse.read_text(encoding="utf-8"))
    print("PASS: exact original Windows bridge build scripts reused without drift")


if __name__ == "__main__":
    main()
