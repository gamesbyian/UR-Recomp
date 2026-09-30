#!/usr/bin/env python3
"""Reconcile unused-song extended blocks with setup/package reachability evidence."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "analysis/generated/audio-setup-selector-map.json"
PACKAGES = ROOT / "analysis/generated/audio-package-map.json"
EXTENDED = ROOT / "analysis/generated/audio-extended-block-correlation.json"
BLOCK_CORR = ROOT / "analysis/generated/audio-block-spc-correlation.json"
UPLOAD = ROOT / "analysis/generated/apu-upload-path-summary.json"
JSON_OUT = ROOT / "analysis/generated/audio-unused-path-analysis.json"
MD_OUT = ROOT / "analysis/generated/audio-unused-path-analysis.md"


def correlated_package_ids(block_corr: dict) -> tuple[int, ...]:
    return tuple(sorted(block["id"] for block in block_corr["blocks"] if block["id"] < 0x32))


def marker_profiles(packages: dict, block_corr: dict, track: str) -> tuple[dict, list[dict]]:
    marker_ids = correlated_package_ids(block_corr)
    observed = {}
    for block in block_corr["blocks"]:
        if block["id"] not in marker_ids:
            continue
        match = next(item for item in block["matches"] if item["track"] == track)
        observed[block["id_hex"]] = bool(
            match["exact_apu_offset_hex"] is not None or match["best_trimmed_match"] is not None
        )

    rows = []
    for table in packages["selector_tables"]:
        signature = {
            f"0x{marker:02X}": marker in table["block_ids"]
            for marker in marker_ids
        }
        mismatches = [
            marker for marker in observed
            if signature[marker] != observed[marker]
        ]
        rows.append({
            "table": table["cpu_address"],
            "direct_caller_count": table["direct_caller_count"],
            "marker_signature": signature,
            "mismatches": mismatches,
            "mismatch_count": len(mismatches),
        })
    rows.sort(key=lambda row: (row["mismatch_count"], -row["direct_caller_count"], row["table"]))
    return observed, rows


def build_analysis(
    setup: dict,
    packages: dict,
    extended: dict,
    upload: dict,
    block_corr: dict,
) -> dict:
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

    song1_markers, song1_candidates = marker_profiles(packages, block_corr, "Unused Song 1")
    song2_markers, song2_candidates = marker_profiles(packages, block_corr, "Unused Song 2")
    marker_ids = correlated_package_ids(block_corr)

    package_pairs: dict[str, list[str]] = {}
    for row in setup["setup_package_pairs"]:
        key = f"0x{row['selector']:02X}"
        package_pairs.setdefault(key, [])
        if row["table_cpu"] not in package_pairs[key]:
            package_pairs[key].append(row["table_cpu"])

    song_package_matrix = []
    package_reuse_summary: dict[str, dict] = {}
    for selector in range(0x38, 0x43):
        key = f"0x{selector:02X}"
        tables_for_selector = package_pairs.get(key, [])
        song_package_matrix.append({
            "selector": key,
            "track_matches": tracks[key]["matched_tracks"] or ["unidentified in preserved SPC set"],
            "package_tables": tables_for_selector,
        })
        for table in tables_for_selector:
            package_reuse_summary.setdefault(table, {"selectors": [], "count": 0})
            package_reuse_summary[table]["selectors"].append(key)
            package_reuse_summary[table]["count"] += 1

    return {
        "schema_version": 3,
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
        "reachable_song_package_matrix": song_package_matrix,
        "package_reuse_summary": package_reuse_summary,
        "package_marker_analysis": {
            "marker_ids": [f"0x{x:02X}" for x in marker_ids],
            "marker_count": len(marker_ids),
            "guardrail": (
                "Block presence in an SPC snapshot can reflect retained APU RAM from earlier loads; "
                "matching correlated package blocks ranks candidates but does not prove which package was loaded."
            ),
            "Unused Song 1": {
                "observed_marker_presence": song1_markers,
                "ranked_tables": song1_candidates,
                "zero_mismatch_tables": [
                    row["table"] for row in song1_candidates if row["mismatch_count"] == 0
                ],
            },
            "Unused Song 2": {
                "observed_marker_presence": song2_markers,
                "ranked_tables": song2_candidates,
                "zero_mismatch_tables": [
                    row["table"] for row in song2_candidates if row["mismatch_count"] == 0
                ],
            },
        },
        "unused_song_findings": {
            "0x3B": {
                "track": "Unused Song 1",
                "ordinary_setup_reachable": presence["0x3B"]["setup_call"],
                "ordinary_package_pair_reachable": presence["0x3B"]["paired_with_known_table"],
                "leading_table_candidates": [
                    row["table"] for row in song1_candidates[:2]
                ],
                "candidate_basis": (
                    "The package ranking is computed from every package block present in the committed "
                    "SPC-correlation corpus. With the current three-block corpus, called Demo package "
                    "03:FB15 exactly matches Unused Song 1 while orphan 03:FB95 does not. The same "
                    "analysis automatically expands when the full 0x00..0x31 correlation is promoted."
                ),
            },
            "0x3D": {
                "track": "Unused Song 2",
                "ordinary_setup_reachable": presence["0x3D"]["setup_call"],
                "ordinary_package_pair_reachable": presence["0x3D"]["paired_with_known_table"],
                "leading_table_candidates": [
                    row["table"] for row in song2_candidates[:2]
                ],
                "candidate_basis": (
                    "Package-block correlation currently ties 03:FB55 and 03:FBD5 on the three committed "
                    "markers. Live first-race 03:FB55 transfer evidence is stronger: it reconstructs APU "
                    "RAM 0xB0E0-0xBDE0, and Unused Song 2 contains that entire 3,329-byte region "
                    "byte-identically at the same offsets."
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
                "Package reuse is normal in reachable content: selectors 0x3E-0x42 for all five numbered race songs share package table 03:FB55.",
            ],
            "hypothesis": (
                "Package reuse is at least as plausible as orphan-table use for Unused Song 1. "
                "The ranking should be recomputed from the full package-block correlation before "
                "controlled reconstruction chooses between candidate tables."
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
    removed = ", ".join(
        report["uncalled_table"]["relation_to_celebration_table_03FAD5"]["removed_block_ids_hex"]
    )
    markers = report["package_marker_analysis"]
    song1 = markers["Unused Song 1"]
    song2 = markers["Unused Song 2"]
    package_rows = []
    for row in report["reachable_song_package_matrix"]:
        packages = ", ".join(f"`{table.replace('0x', '')[:2]}:{table.replace('0x', '')[2:]}`" for table in row["package_tables"]) or "none"
        package_rows.append(
            f"| `{row['selector']}` | {', '.join(row['track_matches'])} | {packages} |"
        )
    return f"""# Unused-song audio path analysis

This reconciles extended ROM audio blocks, CPU setup calls, package tables,
preserved SPC snapshots, and the live first-race APU transfer.

| Extended selector | SPC byte match | Setup call exists | Known package pair |
|---|---|---|---|
{chr(10).join(rows)}

## Closed reachability facts

`0x3B` and `0x3D` are the only gaps in the otherwise populated `0x38..0x42`
song-selector range. They respectively byte-match **Unused Song 1** and **Unused Song 2**
at APU `0x1D00`, yet neither has an ordinary `JSL $82:807E` setup call.

The known package family contains six 64-byte tables. Five have direct callers.
`03:FB95` is the sole orphan. It is a strict, slot-preserving subset of called
Celebration table `03:FAD5`, replacing base blocks {removed} with `FF`.

## Reachable song/package architecture

The known direct setup/package pairs already disprove any one-song/one-package model:

| Selector | Preserved SPC identity | Package table |
|---|---|---|
{chr(10).join(package_rows)}

Most importantly, selectors `0x3E..0x42`, which map to all five numbered race songs,
share the single package table `03:FB55`. Package reuse is therefore an established
retail design pattern, not a special assumption introduced for the unused songs.

## Package reuse is a live hypothesis, not a fallback

The committed package/SPC correlation currently covers **{markers["marker_count"]}**
package blocks: {", ".join(markers["marker_ids"])}. The ranking code consumes this
corpus dynamically, so promoting the full `0x00..0x31` correlation requires no new
interpretation logic.

Unused Song 1's current correlated-block pattern is matched exactly by
{", ".join(song1["zero_mismatch_tables"]) or "no table"}. Unused Song 2's current
pattern is matched exactly by {", ".join(song2["zero_mismatch_tables"]) or "no table"}.
Existing runtime evidence further favors `03:FB55` for Unused Song 2: the live
first-race FB55 transfer reconstructs APU RAM `$B0E0-$BDE0`, and that complete
3,329-byte region is byte-identical at the same offsets in the preserved SPC.

Block presence can reflect retained APU RAM from earlier package loads, so these are
candidate rankings, not causal proof.

## Next discriminator

Promote the all-`0x00..0x31` block/SPC correlation, regenerate this report, then
reconstruct the leading package combinations in a reference harness. The orphan
`03:FB95` remains a required control even if a called package ranks better.
"""


def main() -> None:
    report = build_analysis(
        json.loads(SETUP.read_text(encoding="utf-8")),
        json.loads(PACKAGES.read_text(encoding="utf-8")),
        json.loads(EXTENDED.read_text(encoding="utf-8")),
        json.loads(UPLOAD.read_text(encoding="utf-8")),
        json.loads(BLOCK_CORR.read_text(encoding="utf-8")),
    )
    JSON_OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    MD_OUT.write_text(render_markdown(report), encoding="utf-8")


if __name__ == "__main__":
    main()
