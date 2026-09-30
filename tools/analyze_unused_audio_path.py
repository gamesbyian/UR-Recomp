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

MARKER_IDS = (0x07, 0x15, 0x29)


def marker_profiles(packages: dict, block_corr: dict, track: str) -> tuple[dict, list[dict]]:
    observed = {}
    for block in block_corr["blocks"]:
        if block["id"] not in MARKER_IDS:
            continue
        match = next(item for item in block["matches"] if item["track"] == track)
        observed[block["id_hex"]] = bool(
            match["exact_apu_offset_hex"] is not None or match["best_trimmed_match"] is not None
        )

    rows = []
    for table in packages["selector_tables"]:
        signature = {
            f"0x{marker:02X}": marker in table["block_ids"]
            for marker in MARKER_IDS
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

    return {
        "schema_version": 2,
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
        "package_marker_analysis": {
            "marker_ids": [f"0x{x:02X}" for x in MARKER_IDS],
            "guardrail": (
                "Marker presence in an SPC snapshot can reflect retained APU RAM from earlier loads; "
                "matching these three markers ranks candidates but does not prove which package was loaded."
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
                "leading_table_candidates": ["0x03FB15", "0x03FB95"],
                "candidate_basis": (
                    "03:FB95 remains the sole orphan table, but three already-correlated base-block "
                    "markers favor package reuse: Unused Song 1 has 0x15 and 0x29 present and 0x07 absent, "
                    "exactly matching called Demo package 03:FB15; 03:FB95 omits all three. Because SPC RAM "
                    "may retain prior data, the marker pattern is discriminating evidence rather than proof."
                ),
            },
            "0x3D": {
                "track": "Unused Song 2",
                "ordinary_setup_reachable": presence["0x3D"]["setup_call"],
                "ordinary_package_pair_reachable": presence["0x3D"]["paired_with_known_table"],
                "leading_table_candidates": ["0x03FB55", "0x03FBD5"],
                "candidate_basis": (
                    "The three correlated markers match both 03:FB55 and 03:FBD5, but live first-race "
                    "03:FB55 transfer evidence is stronger: it reconstructs APU RAM 0xB0E0-0xBDE0, and "
                    "Unused Song 2 contains that entire 3,329-byte region byte-identically at the same offsets."
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
                "Package reuse is now at least as plausible as orphan-table use for Unused Song 1. "
                "03:FB15 exactly matches all three currently correlated package-marker presences in that SPC, "
                "whereas 03:FB95 does not; controlled reconstruction is required to choose between them."
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
    song1 = report["package_marker_analysis"]["Unused Song 1"]
    song2 = report["package_marker_analysis"]["Unused Song 2"]
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

## Package reuse is a live hypothesis, not a fallback

Three base package blocks already have SPC correlations: `0x07`, `0x15`, and
`0x29`. Unused Song 1 contains `0x15` and `0x29` but not `0x07`. Among the six
tables, that three-marker pattern is matched exactly by {", ".join(song1["zero_mismatch_tables"])}.
Notably, orphan `03:FB95` omits all three markers, so its orphan status alone is no
longer enough to make it the preferred pairing.

Unused Song 2 contains `0x15` but not `0x07` or `0x29`. The three-marker pattern is
matched exactly by {", ".join(song2["zero_mismatch_tables"])}. Existing runtime evidence
breaks that tie in favor of `03:FB55`: the live first-race FB55 transfer reconstructs
APU RAM `$B0E0-$BDE0`, and that complete 3,329-byte region is byte-identical at the
same offsets in Unused Song 2.

Marker presence can reflect retained APU RAM from earlier package loads, so these are
candidate rankings, not causal proof.

## Next discriminator

Controlled reconstruction should now test **four** targeted combinations rather than
assuming the orphan table wins:

1. `0x3B + 03:FB15` against Unused Song 1.
2. `0x3B + 03:FB95` against Unused Song 1.
3. `0x3D + 03:FB55` against Unused Song 2.
4. `0x3D + 03:FBD5` as the remaining three-marker tie control.

A broader all-0x00..0x31 block-to-SPC correlation would further sharpen package ranking
before any executable patch is promoted.
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
