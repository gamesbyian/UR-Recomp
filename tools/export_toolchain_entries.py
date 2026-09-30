#!/usr/bin/env python3
"""Materialize per-tool toolchain snapshots used for precise CI path triggers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "toolchain.json"
OUT_DIR = ROOT / "tools" / "toolchain-entries"


def render(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def expected_files() -> dict[str, str]:
    data = json.loads(MANIFEST.read_text())
    global_data = {key: value for key, value in data.items() if key != "tools"}
    expected = {"_global.json": render(global_data)}
    for tool in data["tools"]:
        tool_id = tool["id"]
        expected[f"{tool_id}.json"] = render(tool)
    return expected


def check() -> int:
    expected = expected_files()
    actual_names = {p.name for p in OUT_DIR.glob("*.json")} if OUT_DIR.exists() else set()
    expected_names = set(expected)
    ok = True
    for name in sorted(expected_names | actual_names):
        path = OUT_DIR / name
        if name not in expected:
            print(f"unexpected toolchain snapshot: {path.relative_to(ROOT)}")
            ok = False
        elif not path.exists():
            print(f"missing toolchain snapshot: {path.relative_to(ROOT)}")
            ok = False
        elif path.read_text() != expected[name]:
            print(f"stale toolchain snapshot: {path.relative_to(ROOT)}")
            ok = False
    return 0 if ok else 1


def write() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    expected = expected_files()
    for old in OUT_DIR.glob("*.json"):
        if old.name not in expected:
            old.unlink()
    for name, content in expected.items():
        (OUT_DIR / name).write_text(content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return check()
    write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
