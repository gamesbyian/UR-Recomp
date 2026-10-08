#!/usr/bin/env python3
"""Read the original SNES stunt-message boost reward words, not TAS estimates.

The consumer at USA 81:C167 indexes signed little-endian words at 81:C4AA
by 2*(message_id - 1). The containing block is independently identified
across four regional builds by the structural-island analyzer. Its exact
SHA-256 is the admission gate: a different ROM is not silently interpreted
with the USA offsets. Do not commit or copy ROM bytes into evidence output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRUCTURE = ROOT / "analysis/generated/stunt-message-pipeline-structure-island.json"
ALIASES = ROOT / "analysis/generated/dessyreqt-named-boost-messages.json"
BLOCK_NAME = "message_reward_lookup_block"
USA_BLOCK_START = 0xC458
USA_TABLE_START = 0xC4AA
MAX_MESSAGE_ID = 0x15
BUILDS = ("usa-retail", "pal-prototype-1994-11-29", "europe-retail", "legacy-beta")


class RewardEvidenceError(ValueError):
    """Supplied ROM, recovered island or historical mapping is inconsistent."""


def rom_offset(address: str) -> int:
    try:
        bank, cpu = (int(s, 16) for s in address.split(":"))
    except (ValueError, TypeError, AttributeError) as exc:
        raise RewardEvidenceError(f"invalid LoROM address: {address!r}") from exc
    if not 0x80 <= bank <= 0xFF or not 0x8000 <= cpu <= 0xFFFF:
        raise RewardEvidenceError(f"non-ROM LoROM address: {address!r}")
    return (bank & 0x7F) * 0x8000 + (cpu & 0x7FFF)


def extract(rom: bytes, structure: dict, aliases: dict, build: str) -> dict:
    if build not in BUILDS:
        raise RewardEvidenceError(f"unsupported build: {build}")
    if structure.get("island") != "StuntMessageRewardDisplayPipeline":
        raise RewardEvidenceError("unexpected structural-island identity")
    candidates = [r for r in structure.get("regions", []) if r.get("name") == BLOCK_NAME]
    if len(candidates) != 1:
        raise RewardEvidenceError("expected one reward lookup block")
    block = candidates[0]
    if (block.get("usa_start"), block.get("size"), block.get("kind")) != ("81:C458", 282, "data"):
        raise RewardEvidenceError("reward lookup block definition changed")
    build_entry = block.get("builds", {}).get(build)
    if not build_entry:
        raise RewardEvidenceError(f"missing verified data block for {build}")
    offset = rom_offset(build_entry["start"])
    size = block["size"]
    source = rom[offset:offset + size]
    if len(source) != size:
        raise RewardEvidenceError(f"ROM is truncated before {build} reward block")
    digest = hashlib.sha256(source).hexdigest()
    if digest != build_entry["sha256"]:
        raise RewardEvidenceError(f"{build} reward block SHA-256 differs from the established ROM")
    displacement = USA_TABLE_START - USA_BLOCK_START
    if displacement + MAX_MESSAGE_ID * 2 > len(source):
        raise RewardEvidenceError("reward table exceeds established data block")

    # The signed comparison at 81:C167 treats negatives as no boost credit.
    rewards = {}
    for message_id in range(1, MAX_MESSAGE_ID + 1):
        pos = displacement + 2 * (message_id - 1)
        rewards[message_id] = int.from_bytes(source[pos:pos + 2], "little", signed=True)

    if aliases.get("schema_version") != 1 or not isinstance(aliases.get("mapping"), list):
        raise RewardEvidenceError("invalid historical message mapping")
    seen = set()
    comparisons = []
    for item in aliases["mapping"]:
        try:
            message_id = int(item["message_id"], 16)
            expected = item["boost"]
            name = item["name"]
        except (KeyError, TypeError, ValueError) as exc:
            raise RewardEvidenceError("invalid historical reward entry") from exc
        if (message_id not in rewards or message_id in seen or
                type(expected) is not int or not isinstance(name, str) or not name):
            raise RewardEvidenceError("duplicate/out-of-range/malformed historical reward entry")
        seen.add(message_id)
        observed = rewards[message_id]
        comparisons.append({
            "message_id": f"0x{message_id:02X}",
            "historical_name": name,
            "historical_boost_estimate": expected,
            "rom_signed_word": observed,
            "agrees": observed == expected,
        })
    return {
        "schema_version": 1,
        "build": build,
        "source_block": build_entry["start"],
        "source_block_sha256": digest,
        "consumer": "81:C167 (USA); 2*(message_id-1), signed 16-bit lookup",
        "raw_signed_words": [
            {"message_id": f"0x{i:02X}", "value": rewards[i]}
            for i in range(1, MAX_MESSAGE_ID + 1)
        ],
        "historical_comparison": comparisons,
        "historical_disagreements": [r["message_id"] for r in comparisons if not r["agrees"]],
        "interpretation": (
            "ROM lookup words are authoritative source bytes. Message enqueue/consumption "
            "timing and realized player boost still require a deterministic runtime fixture; "
            "historical TAS estimates are comparison leads, not the authority."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="locally available, unmodified ROM")
    parser.add_argument("--build", choices=BUILDS, default="usa-retail")
    parser.add_argument("--structure", type=Path, default=STRUCTURE)
    parser.add_argument("--historical", type=Path, default=ALIASES)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    try:
        result = extract(
            args.rom.read_bytes(),
            json.loads(args.structure.read_text(encoding="utf-8")),
            json.loads(args.historical.read_text(encoding="utf-8")),
            args.build,
        )
    except (RewardEvidenceError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    output = json.dumps(result, indent=2) + "\n"
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
