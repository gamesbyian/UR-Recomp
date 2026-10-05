#!/usr/bin/env python3
"""Test whether SRAM 0x10D1 is sufficient to substitute a Modern challenge tier.

Both cases boot the same checksum-valid medal-0 Crawler/MIKE SRAM. The control
uses the ordinary stock route. The variant waits until stock has confirmed the
tour and reached TRACK_SELECT, then changes only transient SRAM 0x10D1 from 0
to 2 before selecting Dragster.

The result distinguishes:
- full generation seam: GOLD label + GOLDWYN/index 19;
- label-only seam: GOLD label but BRONSEN/index 17;
- no seam: BRONZE + BRONSEN/index 17;
- unexpected mixed state.

Persistent medal/checksum ownership must remain unchanged in every case.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import probe_tier_opponents as tier

ROOT = Path(__file__).resolve().parents[1]
CONTROL_SCRIPT = ROOT / "tests/input/tier-opponent-probe.script"
TRANSIENT_SCRIPT = ROOT / "tests/input/challenge-generation-transient-probe.script"
SNAPSHOT = 0x10D1


def _dump_sram(run: Path, tag: str) -> bytes:
    matches = sorted(run.glob(f"{tag}*.sram*"))
    if not matches:
        raise RuntimeError(f"missing SRAM dump for {tag} in {run}")
    data = matches[0].read_bytes()
    if len(data) != 0x2000:
        raise RuntimeError(f"unexpected SRAM dump size: {len(data)}")
    return data


def classify(control: dict, variant: dict) -> str:
    if control.get("tier_label") != "BRONZE" or control.get("p2_rider_index") != 17:
        return "invalid-control"
    label = variant.get("tier_label")
    opponent = variant.get("p2_rider_index")
    if label == "GOLD" and opponent == 19:
        return "full-generation-seam"
    if label == "GOLD" and opponent == 17:
        return "label-only-seam"
    if label == "BRONZE" and opponent == 17:
        return "no-effect"
    return "mixed-or-unexpected"


def summarize(
    control: dict,
    variant: dict,
    before_sram: bytes,
    variant_sram: bytes,
) -> dict:
    stored_checksum = variant_sram[tier.CHECKSUM_AT] | (
        variant_sram[tier.CHECKSUM_AT + 1] << 8)
    outcome = classify(control, variant)
    checks = {
        "control_is_bronze_bronsen": (
            control["tier_label"] == "BRONZE"
            and control["p2_rider_index"] == 17
            and control["card_opponent_name"] == "BRONSEN"
        ),
        "stock_confirm_snapshot_was_zero": before_sram[SNAPSHOT] == 0,
        "variant_snapshot_is_gold_generation": variant_sram[SNAPSHOT] == 2,
        "only_snapshot_changed_before_track_dump": (
            [
                i for i, (a, b) in enumerate(zip(before_sram, variant_sram))
                if a != b
            ] == [SNAPSHOT]
        ),
        "persistent_medal_remains_zero": variant_sram[tier.MEDAL_CELL] == 0,
        "persistent_medal_checksum_still_valid": (
            tier.checksum(variant_sram) == stored_checksum
        ),
        "variant_reaches_race": variant["in_race"] == 1,
    }
    return {
        "schema_version": 1,
        "question": (
            "Is the transient tour-confirm medal snapshot at SRAM 0x10D1 "
            "sufficient to select a non-current canonical challenge generation?"
        ),
        "control": control,
        "transient_10d1_2": variant,
        "classification": outcome,
        "candidate_is_full_generation_seam": outcome == "full-generation-seam",
        "checks": checks,
        "all_integrity_checks_pass": all(checks.values()),
    }


def _run_case(
    run: Path,
    sram: bytes,
    script: Path,
    snesref: Path,
    core: Path,
    rom: Path,
) -> dict:
    run.mkdir(parents=True, exist_ok=True)
    (run / "in.srm").write_bytes(sram)
    env = dict(
        os.environ,
        SNESREF_HEADLESS="1",
        SNESREF_FAST="1",
        SNESREF_WRAM_FILL="0",
        SNESREF_SRAM_IN=str(run / "in.srm"),
        SNESREF_SCRIPT=str(script),
        SNESREF_DUMP_DIR=str(run),
    )
    with open(run / "snesref.log", "w") as log:
        subprocess.run(
            [str(snesref), str(core), str(rom)],
            env=env,
            cwd=run,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    return tier.observe(run, rom.read_bytes())


def main() -> int:
    tools = ROOT / ".tools/src"
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("clean_sram", type=Path)
    ap.add_argument(
        "--snesref",
        type=Path,
        default=tools / "snesrecomp/build-snesref/snesref")
    ap.add_argument(
        "--core",
        type=Path,
        default=tools / "snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=tier.cast.ROM)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "analysis/generated/challenge-generation-transient-probe.json")
    args = ap.parse_args()

    clean = args.clean_sram.read_bytes()
    if len(clean) != 0x2000:
        raise SystemExit("clean SRAM must be exactly 8 KiB")
    seeded = tier.seeded(clean, 0)
    stored = seeded[tier.CHECKSUM_AT] | seeded[tier.CHECKSUM_AT + 1] << 8
    if tier.checksum(seeded) != stored:
        raise SystemExit("seed SRAM checksum is invalid")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        control = _run_case(
            root / "control",
            seeded,
            CONTROL_SCRIPT,
            args.snesref,
            args.core,
            args.rom)
        variant_run = root / "transient"
        variant = _run_case(
            variant_run,
            seeded,
            TRANSIENT_SCRIPT,
            args.snesref,
            args.core,
            args.rom)
        before_sram = _dump_sram(variant_run, "tier-before")
        variant_sram = _dump_sram(variant_run, "tier-track")

        report = summarize(control, variant, before_sram, variant_sram)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0 if report["all_integrity_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
