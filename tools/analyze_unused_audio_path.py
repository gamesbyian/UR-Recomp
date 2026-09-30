#!/usr/bin/env python3
"""Reconcile unused-song extended blocks with setup/package reachability evidence."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "analysis/generated/audio-setup-selector-map.json"
PACKAGES = ROOT / "analysis/generated/audio-package-map.json"
EXTENDED = ROOT / "analysis/generated/audio-extended-block-correlation.json"
UPLOAD = ROOT / "analysis/generated/apu-upload-path-summary.json"
JSON_OUT = ROOT / "analysis/generated/audio-unused-path-analysis.json"
MD_OUT = ROOT / "analysis/generated/audio-unused-path-analysis.md"


def build_analysis(setup: dict, packages: dict, extended: dict, upload: dict) -> dict:
    presence = setup["selector_38_42_presence"]
    tables = {row["cpu_address"]: row for row in packages["selector_tables"]}
    tracks = {}
    for block in extended["blocks"]:
        if not (0x38 <= block["id"] <= 0x42):
            continue
        matches = [
            m["track"]
            for m in block["matches"]
            if m["exact_apu_offset_hex"] is not None or m["best_trimmed_match"] is not None
        ]
        tracks[block["id_hex"]] = {
            "cpu_address": block["cpu_address"],
            "matched_tracks": matches,
            "setup_call": presence.get(block["id_hex"], {}).get("setup_call", False),
            "paired_with_known_table": presence.get(block["id_hex"], {}).get("paired_with_known_table", False),
        }

    fad5 = tables["0x03FAD5"]
    fb95 = tables["0x03FB95"]
    fad5_ids = set(fad5["block_ids"])
    fb95_ids = set(fb95["block_ids"])
    differences = []
    for slot, (a, b) in enumerate(zip(bytes.fromhex(fad5["bytes_hex"]), bytes.fromhex(fb95["bytes_hex"]))):
        if a != b:
            differences.append({
                "slot": slot,
                "slot_1based": slot + 1,
                "fad5": f"0x{a:02X}",
                "fb95": f"0x{b:02X}",
            })

    return {
        "schema_version": 1,
        "extended_song_selectors": tracks,
        "missing_setup_selectors": [
            key for key, row in presence.items() if not row["setup_call"]
        ],
        "uncalled_table": {
            "cpu_address": "0x03FB95",
            "direct_caller_count": fb95["direct_caller_count"],
            "block_ids_hex": fb95["block_ids_hex"],
            "relation_to_celebration_table_03FAD5": {
                "is_strict_subset": fb95_ids < fad5_ids,
                "same_shared_slot_positions": all(
                    a == b or b == 0xFF
                    for a, b in zip(bytes.fromhex(fad5["bytes_hex"]), bytes.fromhex(fb95["bytes_hex"]))
                ),
                "removed_block_ids_hex": [f"0x{x:02X}" for x in sorted(fad5_ids - fb95_ids)],
                "different_slots": differences,
            },
        },
        "unused_song_findings": {
            "0x3B": {
                "track": "Unused Song 1",
                "ordinary_setup_reachable": presence["0x3B"]["setup_call"],
                "ordinary_package_pair_reachable": presence["0x3B"]["paired_with_known_table"],
                "structural_table_candidate": "0x03FB95",
                "candidate_basis": (
                    "03:FB95 is the only known 64-byte package table with no direct caller and is "
                    "an exact slot-preserving subset of Celebration table 03:FAD5, differing only "
                    "by three FF substitutions. This is structural evidence, not proof of the lost call pair."
                ),
            },
            "0x3D": {
                "track": "Unused Song 2",
                "ordinary_setup_reachable": presence["0x3D"]["setup_call"],
                "ordinary_package_pair_reachable": presence["0x3D"]["paired_with_known_table"],
                "structural_table_candidate": "0x03FB55",
                "candidate_basis": (
                    "The live first-race 03:FB55 transfer reconstructs APU RAM 0xB0E0-0xBDE0, "
                    "and the preserved Unused Song 2 SPC contains that entire 3,329-byte region "
                    "byte-identically at the same offsets. This makes reuse of the race-family "
                    "package the leading candidate, though a counterfactual load remains to prove it."
                ),
            },
        },
        "interpretation": {
            "confirmed": [
                "Extended block 0x3B byte-matches only Unused Song 1 at APU 0x1D00 among preserved SPC snapshots.",
                "Extended block 0x3D byte-matches only Unused Song 2 at APU 0x1D00 among preserved SPC snapshots.",
                "Neither 0x3B nor 0x3D has an ordinary setup-wrapper call or known setup+package pair.",
                "03:FB95 has zero direct package-transfer callers.",
                "03:FB95 is a slot-preserving strict subset of called Celebration table 03:FAD5.",
            ],
            "hypothesis": (
                "03:FB95 is a plausible orphan package for the 0x3B / Unused Song 1 path, "
                "but current evidence does not prove that pairing."
            ),
            "negative_result": (
                "There is no comparable second orphan table for 0x3D; instead the live 03:FB55 "
                "race-family package produces a 3,329-byte APU region that is byte-identical at "
                "the same offsets in Unused Song 2, favoring package reuse."
            ),
            "unused_song_2_race_package_corroboration": {
                "package": upload["rom_source"]["first_race_source_cpu"],
                "apu_region": upload["spc_correlation"]["recovered_unique_apu_region"],
                "same_offset_tracks": upload["spc_correlation"]["exact_same_offset_tracks"],
                "unused_song_2_same_offset": "Unused Song 2" in upload["spc_correlation"]["exact_same_offset_tracks"],
            },
        },
    }


def render_markdown(report: dict) -> str:
    rows = []
    for selector, row in sorted(report["extended_song_selectors"].items()):
        tracks = ", ".join(row["matched_tracks"]) or "none"
        rows.append(
            f"| `{selector}` | {tracks} | {row['setup_call']} | {row['paired_with_known_table']} |"
        )
    removed = ", ".join(report["uncalled_table"]["relation_to_celebration_table_03FAD5"]["removed_block_ids_hex"])
    return f"""# Unused-song audio path analysis

This reconciles three already-reproducible evidence surfaces: extended ROM audio blocks,
CPU setup calls, and 64-byte package-table callers.

| Extended selector | SPC byte match | Setup call exists | Known package pair |
|---|---|---|---|
{chr(10).join(rows)}

## Closed reachability facts

`0x3B` and `0x3D` are the only gaps in the otherwise populated `0x38..0x42`
song-selector range. They respectively byte-match **Unused Song 1** and **Unused Song 2**
at APU `0x1D00`, yet neither has an ordinary `JSL $82:807E` setup call. The scanner
also finds no hidden immediate `LDX #$003B/#$003D` setup form and no unbound setup-wrapper
calls.

The known package family contains six 64-byte tables. Five have direct callers.
`03:FB95` is the sole orphan.

## What 03:FB95 is

`03:FB95` is a strict, slot-preserving subset of called table `03:FAD5`, the table
paired with selector `0x3A` whose extended block matches **Celebration**. The tables
differ at exactly three slots: `03:FB95` replaces base blocks {removed} with `FF`.

That makes `03:FB95` a strong **structural candidate** for a removed audio path, and
`0x3B / Unused Song 1` is the natural first pairing to test because both the selector
and table are orphaned. It is not yet proof that the original code paired them.

## Important negative result

There is only one orphan package table but two unreachable song selectors. Current
static evidence therefore cannot assign a unique package table to `0x3D / Unused Song 2`.
Any model requiring one distinct missing table per unused song is ruled out by the known
six-table corpus.

## Next discriminator

The useful next experiment is a controlled reconstruction, not more pattern searching:
invoke the ordinary setup path with selector `0x3B` and package table `03:FB95` in a
reference harness, then compare resulting APU RAM to the preserved Unused Song 1 SPC.
Test `0x3D` separately against reused package candidates rather than inventing a seventh
table.
"""


def main() -> None:
    report = build_analysis(
        json.loads(SETUP.read_text(encoding="utf-8")),
        json.loads(PACKAGES.read_text(encoding="utf-8")),
        json.loads(EXTENDED.read_text(encoding="utf-8")),
        json.loads(UPLOAD.read_text(encoding="utf-8")),
    )
    JSON_OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    MD_OUT.write_text(render_markdown(report), encoding="utf-8")


if __name__ == "__main__":
    main()
