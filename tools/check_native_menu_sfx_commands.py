#!/usr/bin/env python3
"""Check actual native original-game menu SFX commands against pinned SNES reference.

The reference corpus is produced by tools/probe_menu_sfx_ids.py from actual
stock guest WRAM command ring. The native run must execute the same three
input events and yield identical command identities in its own real WRAM
dumps. This establishes dispatch/identity, not decoded BRR or acoustic parity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from probe_menu_sfx_ids import classify, new_commands
from build_native_menu_sfx_route import EVENT_NAMES

NATIVE_DUMPS = ("e00-start", "e01", "e02", "e03")
EXPECTED_MENU_STATES = (0xD7, 0xD7, 0xD7, 0x3C)
WRAM_BYTES = 0x20000
MATCH = re.compile(r"(?m)^script f=(\d+) dump (e00-start|e01|e02|e03) ok\s*$")


def verify(dumps: dict[str, bytes], log: str, reference: dict) -> dict:
    if set(dumps) != set(NATIVE_DUMPS):
        raise ValueError("native original-menu SFX route lacks exactly four WRAM dumps")
    if any(not isinstance(dumps[name], bytes) or len(dumps[name]) != WRAM_BYTES
           for name in NATIVE_DUMPS):
        raise ValueError("native sound-command provenance requires complete 128KiB guest WRAM")
    if (reference.get("schema_version") != 1
        or reference.get("all_checks_pass") is not True
        or not isinstance(reference.get("events"), dict)):
        raise ValueError("untrusted reference sound command inventory")
    marks = list(MATCH.finditer(log))
    if len(marks) != len(NATIVE_DUMPS):
        raise ValueError("native script must observe exactly four authoritative checkpoints")
    if tuple(m.group(2) for m in marks) != NATIVE_DUMPS:
        raise ValueError("native menu SFX checkpoints out of guest-observed order")
    frames = [int(m.group(1)) for m in marks]
    if frames[0] <= 0 or any(b <= a for a, b in zip(frames, frames[1:])):
        raise ValueError("native guest did not advance between SFX checkpoints")
    actual_menus = tuple(dumps[name][0x009F] for name in NATIVE_DUMPS)
    if actual_menus != EXPECTED_MENU_STATES:
        raise ValueError("native menu SFX experiment deviated from stock frontend route")

    events = {}
    for i, name in enumerate(EVENT_NAMES, 1):
        before, after = (dumps[NATIVE_DUMPS[i - 1]],
                         dumps[NATIVE_DUMPS[i]])
        observed = new_commands(before, after)
        expected = reference["events"].get(name)
        if not isinstance(expected, dict) or not isinstance(expected.get("commands"), list):
            raise ValueError(f"reference missing known stock event {name}")
        if len(observed) != len(expected["commands"]) or observed != expected["commands"]:
            raise ValueError(
                f"native {name} sound-command mismatch: "
                f"actual={observed}, reference={expected['commands']}"
            )
        sfx = classify(observed)
        if sfx != expected.get("sfx"):
            raise ValueError(f"native {name} SFX selector mismatch")
        if f"0x{actual_menus[i]:02X}" != expected.get("menu_after"):
            raise ValueError(f"native {name} destination menu differs from reference")
        events[name] = {
            "guest_start_frame": frames[i - 1],
            "guest_after_frame": frames[i],
            "commands": observed,
            "sfx_id": sfx,
            "guest_menu_after": f"0x{actual_menus[i]:02X}",
        }
    return {
        "schema_version": 1,
        "authority": "live native stock menu WRAM command ring vs pinned independent SNES reference",
        "reference": "analysis/generated/menu-sfx-ids.json",
        "events": events,
        "all_three_commands_match": True,
        "limitations": "command queue identity only; SPC consumption, PCM sample identity and exact device latency are not established",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dump_directory", type=Path)
    ap.add_argument("native_log", type=Path)
    ap.add_argument("reference_json", type=Path)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()
    dumps = {name: (args.dump_directory / f"{name}.wram.bin").read_bytes()
             for name in NATIVE_DUMPS}
    report = verify(
        dumps,
        args.native_log.read_text(encoding="utf-8", errors="replace"),
        json.loads(args.reference_json.read_text(encoding="utf-8")),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                             encoding="utf-8")
    print("NATIVE_MENU_SFX_COMMAND_PARITY PASS events=3 "
          "sfx=03,03,02 all_exact_source_commands=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
