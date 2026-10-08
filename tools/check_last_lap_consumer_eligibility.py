#!/usr/bin/env python3
"""Check whether the game can consume the Last Lap (0x0F) boost table entry.

USA bank 81 C10C..C136 loads byte [81:C521+(message_id-1)] and branches
to display-only when it equals FF. It then tests per-message enable at
7E:20E8+(message_id-1) and skips reward/score when zero. Only then does
81:C167 index the positive signed boost word. This probe reads the
fingerprinted original ROM data, rather than assuming any message with a
positive reward word must produce a bonus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from extract_last_lap_reward_gate import (
    extract as check_lap, LastLapEvidenceError, ISLAND, REWARDS
)
from extract_stunt_message_rewards import BUILDS, rom_offset

ROOT = Path(__file__).resolve().parents[1]
STUNT_ISLAND = ROOT / "analysis/generated/stunt-message-pipeline-structure-island.json"
MESSAGE_ID = 0x0F
DATA_NAME = "message_reward_lookup_block"
TABLE_ORIGINAL = 0xC521
BLOCK_ORIGINAL = 0xC458
BLOCK_SIZE = 282


class ConsumerEvidenceError(ValueError):
    """The original ROM consumer mapping is absent or untrustworthy."""


def check(rom: bytes, lap_island: dict, reward_report: dict,
          stunt_island: dict, build: str) -> dict:
    try:
        entry = check_lap(rom, lap_island, reward_report, build)
    except LastLapEvidenceError as exc:
        raise ConsumerEvidenceError(str(exc)) from exc
    if stunt_island.get("island") != "StuntMessageRewardDisplayPipeline":
        raise ConsumerEvidenceError("wrong message consumer structural island")
    candidates = [r for r in stunt_island.get("regions", [])
                  if r.get("name") == DATA_NAME]
    if len(candidates) != 1:
        raise ConsumerEvidenceError("expected exactly one verified consumer data block")
    block = candidates[0]
    if (block.get("usa_start"), block.get("size"), block.get("kind")) != (
            "81:C458", BLOCK_SIZE, "data"):
        raise ConsumerEvidenceError("reward data block definition drifted")
    desc = block.get("builds", {}).get(build)
    if not desc:
        raise ConsumerEvidenceError(f"{build}: missing verified consumer data")
    addr = rom_offset(desc["start"])
    source = rom[addr:addr + BLOCK_SIZE]
    if len(source) != BLOCK_SIZE:
        raise ConsumerEvidenceError(f"{build}: truncated verified consumer data")
    digest = hashlib.sha256(source).hexdigest()
    if digest != desc.get("sha256"):
        raise ConsumerEvidenceError(f"{build}: original consumer data SHA-256 mismatch")
    offset = TABLE_ORIGINAL - BLOCK_ORIGINAL + MESSAGE_ID - 1
    stat_map_byte = source[offset]
    enable_addr = 0x20E8 + MESSAGE_ID - 1

    return {
        "schema_version": 1,
        "build": build,
        "queued_message": "0x0F (Last Lap)",
        "checkpoint_mode_gate": entry["mode_condition"],
        "lap_condition": entry["lap_condition"],
        "consumer_data_sha256": digest,
        "message_mapping_byte": f"0x{stat_map_byte:02X}",
        "message_mapping_lookup": f"{desc['start']} + 0x{offset:02X} (message ID 0x0F)",
        "consumer_first_gate": "mapping != 0xFF (81:C110..C11B, USA)",
        "p2_mirrored_first_gate": "mapping != 0xFF (81:C253..C260, USA)",
        "per_message_enable_gate": f"7E:{enable_addr:04X} != 0 (81:C12D..C136, USA)",
        "signed_reward_if_gates_allow": 152,
        "static_reachability": (
            "blocked_by_0xFF_mapping" if stat_map_byte == 0xFF
            else "conditional_on_runtime_per_message_enable"
        ),
        "runtime_award_status": (
            "unreachable_through_this_consumer: mapping FF branches to display-only before boost"
            if stat_map_byte == 0xFF
            else "conditional: runtime enable and consumption still unmeasured"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--build", choices=BUILDS, default="usa-retail")
    p.add_argument("--lap-island", type=Path, default=ISLAND)
    p.add_argument("--stunt-island", type=Path, default=STUNT_ISLAND)
    p.add_argument("--rewards", type=Path, default=REWARDS)
    p.add_argument("--json-out", type=Path)
    args = p.parse_args(argv)
    try:
        report = check(
            args.rom.read_bytes(),
            json.loads(args.lap_island.read_text(encoding="utf-8")),
            json.loads(args.rewards.read_text(encoding="utf-8")),
            json.loads(args.stunt_island.read_text(encoding="utf-8")),
            args.build,
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        p.error(str(exc))
    output = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
