#!/usr/bin/env python3
"""Report oversized work-queue blocks so current-state routing stays compact."""

from __future__ import annotations
import argparse
import re
from pathlib import Path

def oversized_blocks(text: str, threshold: int = 3500) -> list[tuple[str, int]]:
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for block in blocks:
        stripped = block.strip()
        if len(stripped) <= threshold:
            continue
        first = stripped.splitlines()[0][:120]
        out.append((first, len(stripped)))
    return sorted(out, key=lambda item: -item[1])

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=Path("docs/WORK-QUEUE.md"))
    parser.add_argument("--threshold", type=int, default=3500)
    parser.add_argument("--fail", action="store_true")
    args = parser.parse_args()
    rows = oversized_blocks(args.path.read_text(errors="replace"), args.threshold)
    if not rows:
        print("WORK_QUEUE_DENSITY_OK")
        return 0
    print("Oversized current-state blocks:")
    for first, size in rows:
        print(f"{size:6d}  {first}")
    return 1 if args.fail else 0

if __name__ == "__main__":
    raise SystemExit(main())
