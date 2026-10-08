#!/usr/bin/env python3
"""Admit the stock Last Lap message-to-boost path using canonical ROM bytes.

USA 81:81B4..81CA tests the newly remaining lap count, then the low byte
of SRAM play mode, before sending message 0x0F to the ordinary queue helper.
This is deliberately a static gate proof, not a claim of observed award timing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from extract_stunt_message_rewards import BUILDS, rom_offset

ROOT = Path(__file__).resolve().parents[1]
ISLAND = ROOT / "analysis/generated/checkpoint-finish-structure-island.json"
REWARDS = ROOT / "analysis/generated/stunt-message-reward-rom-verification.json"
REGION = "lap_hud"
# C5AF is a wrapper; the checkpoint code calls C5B3, the underlying queue helper.
QUEUE_JSR = {
    "usa-retail": 0xC5B3,
    "legacy-beta": 0xC5B3,
    "pal-prototype-1994-11-29": 0xC594,
    "europe-retail": 0xC5A0,
}
# 65c816: LDA $0EF1,Y; CMP #1; BNE; LDA.l $77074B;
# AND #$00FF; BEQ; LDA #$000F; JSR [the regional helper].
GATE = re.compile(
    rb"\xb9\xf1\x0e\xc9\x01\x00\xd0(.)"
    rb"\xaf\x4b\x07\x77\x29\xff\x00\xf0(.)"
    rb"\xa9\x0f\x00\x20(..)", re.DOTALL
)


class LastLapEvidenceError(ValueError):
    """ROM identity, instruction shape, or reward evidence is not admissible."""


def extract(rom: bytes, island: dict, reward_report: dict, build: str) -> dict:
    if build not in BUILDS:
        raise LastLapEvidenceError(f"unsupported ROM build: {build}")
    if island.get("island") != "Race_HandleCheckpointFinish":
        raise LastLapEvidenceError("wrong checkpoint/finish structural island")
    regions = [r for r in island.get("regions", []) if r.get("name") == REGION]
    if len(regions) != 1 or regions[0].get("usa_start") != "81:8195" or regions[0].get("size") != 63:
        raise LastLapEvidenceError("ambiguous/changed lap-HUD structure")
    record = regions[0].get("builds", {}).get(build)
    if not record:
        raise LastLapEvidenceError(f"unverified lap-HUD region for {build}")
    start = rom_offset(record["start"])
    block = rom[start:start + regions[0]["size"]]
    if len(block) != 63:
        raise LastLapEvidenceError(f"truncated {build} lap-HUD block")
    sha = hashlib.sha256(block).hexdigest()
    if sha != record.get("sha256"):
        raise LastLapEvidenceError(f"{build} lap-HUD SHA-256 mismatch")
    matches = list(GATE.finditer(block))
    if len(matches) != 1:
        raise LastLapEvidenceError(f"{build}: expected one stock Last Lap enqueue gate, found {len(matches)}")
    match = matches[0]
    skip_lap, skip_mode = match.group(1)[0], match.group(2)[0]
    jsr = int.from_bytes(match.group(3), "little")
    # A changed branch shape must not be called the same semantic proof.
    if (skip_lap, skip_mode) != (0x17, 0x06):
        raise LastLapEvidenceError(f"{build}: branch offsets no longer implement the recovered gate")
    if jsr != QUEUE_JSR[build]:
        raise LastLapEvidenceError(f"{build}: enqueue destination differs (JSR ${jsr:04X})")
    rows = reward_report.get("signed_words")
    if not isinstance(rows, list) or len(rows) < 0x0F:
        raise LastLapEvidenceError("incomplete signed reward table")
    entry = rows[0x0F - 1]
    if entry.get("message_id") != "0x0F" or type(entry.get("value")) is not int:
        raise LastLapEvidenceError("message-to-reward identity drift")
    if entry["value"] != 152:
        raise LastLapEvidenceError("unexpected Last Lap reward magnitude")

    return {
        "schema_version": 1,
        "build": build,
        "lap_gate": f"{record['start']} + 0x{match.start():02X}",
        "lap_region_sha256": sha,
        "lap_condition": "7E:0EF1+2*current_player == 1 after decrement",
        "mode_condition": "(77:074B & 0x00FF) != 0",
        "queued_message": "0x0F (Last Lap)",
        "enqueue_jsr": f"81:{jsr:04X}",
        "signed_reward_lookup": 152,
        "runtime_status": "unmeasured: exact queue delivery, boost credit and speed change are not established",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--build", choices=BUILDS, default="usa-retail")
    p.add_argument("--island", type=Path, default=ISLAND)
    p.add_argument("--rewards", type=Path, default=REWARDS)
    p.add_argument("--json-out", type=Path)
    args = p.parse_args(argv)
    try:
        result = extract(
            args.rom.read_bytes(),
            json.loads(args.island.read_text(encoding="utf-8")),
            json.loads(args.rewards.read_text(encoding="utf-8")),
            args.build,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        p.error(str(exc))
    content = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(content, encoding="utf-8")
    print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
