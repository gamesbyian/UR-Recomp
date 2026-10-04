#!/usr/bin/env python3
"""Collapse Switch guest/runtime objects and report the remaining link surface."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "analysis/switch-s2-link-surface-contract.json"


def load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text())


def collect_objects(paths: list[Path]) -> list[Path]:
    objects: list[Path] = []
    for path in paths:
        objects.extend(sorted(path.glob("*.o")))
    return objects


def relocatable_link(objects: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = ["aarch64-none-elf-ld", "-r", "-o", str(output), *map(str, objects)]
    subprocess.run(command, check=True)


def undefined_symbols(linked: Path) -> list[str]:
    proc = subprocess.run(
        ["aarch64-none-elf-nm", "-u", str(linked)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    symbols: set[str] = set()
    for line in proc.stdout.splitlines():
        match = re.search(r"\bU\s+(.+)$", line.strip())
        if match:
            symbols.add(match.group(1).strip())
    return sorted(symbols)


def classify(symbols: list[str], contract: dict) -> dict:
    standard = set(contract["classification"]["standard_symbols"])
    libc_or_toolchain: list[str] = []
    host_or_runtime: list[str] = []
    for symbol in symbols:
        if symbol in standard or symbol.startswith("__"):
            libc_or_toolchain.append(symbol)
        else:
            host_or_runtime.append(symbol)
    return {
        "libc_or_toolchain": libc_or_toolchain,
        "host_or_runtime": host_or_runtime,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guest-objects", type=Path, required=True)
    parser.add_argument("--runtime-objects", type=Path, required=True)
    parser.add_argument("--linked-out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    contract = load_contract()
    objects = collect_objects([args.guest_objects, args.runtime_objects])
    if not objects:
        raise SystemExit("SWITCH_S2_LINK_ERROR: no objects found")

    relocatable_link(objects, args.linked_out)
    symbols = undefined_symbols(args.linked_out)
    classes = classify(symbols, contract)
    result = {
        "schema_version": 1,
        "gate": contract["gate"],
        "object_count": len(objects),
        "linked_object_bytes": args.linked_out.stat().st_size,
        "unresolved_count": len(symbols),
        "unresolved_symbols": symbols,
        "classification": classes,
    }
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(payload)
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
