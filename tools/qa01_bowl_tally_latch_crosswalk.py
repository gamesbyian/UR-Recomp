#!/usr/bin/env python3
"""QA-01: read-only, two-artifact Bowl scored-tally residue crosswalk.

Reconcile *existing* independent count-only and exact offset-only original /
native Snes9x/Baldosa Bowl artifacts. No emulator run, guest input rebase,
source/consumer attribution, shipping-candidate verdict or release admission.
Address membership alone does not identify the original CPU writer or prove
a different controller mask reached the two guests.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFSETS = ROOT / "analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json"
COUNTS = ROOT / "analysis/data/bowl-tally-full-guest-same-host-eight-frame-20261009.json"
SCHEMA = "UR-QA01-BOWL-EXISTING-TALLY-LATCH-ADDRESS-CROSSWALK/1"
HOST_OFFSETS = (54, 60, 64, 65, 66, 67, 68, 69)
ADDRESS = re.compile(r"0x[0-9A-F]{5}\Z")


def classify_address(offset: int) -> str:
    """Named spans are more specific than the 65816's generic stack page."""
    if offset in (0x72, 0x73):
        return "joy1_held_word_bytes"
    if offset in (0x89, 0x8A, 0x8B):
        return "menu_timing_bytes"
    if 0x187 <= offset <= 0x18E:
        return "named_menu_animation_frames"
    if offset == 0x191:
        return "named_menu_animation_phase"
    if 0x100 <= offset <= 0x1FF:
        return "unattributed_stack_page_bytes"
    if 0xB00 <= offset < 0xD00:
        return "oam_shadow_region_bytes"
    return "other_unattributed_bytes"


def canonical_offsets(profile: dict, expected: int, kind: str) -> list[int]:
    if not isinstance(profile, dict):
        raise ValueError(f"{kind}: no original/native offset profile")
    addresses = profile.get("addresses")
    if (profile.get("total") != expected or
            profile.get("truncated") is not False or
            not isinstance(addresses, list) or len(addresses) != expected):
        raise ValueError(f"{kind}: incomplete or contradictory offset census")
    values = []
    for address in addresses:
        if not isinstance(address, str) or not ADDRESS.fullmatch(address):
            raise ValueError(f"{kind}: malformed or noncanonical address")
        v = int(address[2:], 16)
        if kind == "wram" and v >= 0x20000:
            raise ValueError("WRAM offset outside actual 128-KiB guest dump")
        if kind == "vram" and v >= 0x10000:
            raise ValueError("VRAM offset outside actual 64-KiB guest dump")
        if kind == "cgram" and v >= 0x200:
            raise ValueError("CGRAM offset outside actual 512-byte guest dump")
        values.append(v)
    if values != sorted(set(values)):
        raise ValueError(f"{kind}: address list reordered or duplicated")
    return values


def crosswalk(offset_record: dict, count_record: dict) -> dict:
    if (offset_record.get("schema") != "UR-QA01-BOWL-SOURCED-OFFSET-CAPTURE/1" or
            offset_record.get("provenance", {}).get("workflow_run_id") != 38025090532 or
            offset_record["provenance"].get("artifact_id") != 11659973901 or
            count_record.get("schema") != "UR-QA01-BOWL-TALLY-SOURCE-PHASE-WITNESS/1" or
            count_record.get("source", {}).get("run_id") != 38024468581 or
            count_record["source"].get("artifact_id") != 11659683037):
        raise ValueError("wrong independently executed Bowl artifact identities")
    phase = offset_record.get("tally_anchored_guest_phase")
    if not isinstance(phase, dict) or phase.get("schema") != "UR-QA01-BOWL-TALLY-ANCHORED-PHASE/1":
        raise ValueError("incorrect genuine Bowl tally phase schema")
    if (phase.get("reference_and_native_tally_host_frame") != 4279 or
            phase.get("reference_and_native_result_host_frame") != 4349 or
            phase.get("offset_profile_cap_per_memory_class") != 128 or
            phase.get("retains_raw_guest_memory") is not False or
            phase.get("release_complete_event_credit") != 0 or
            count_record.get("release_complete_usa_courses_credited") != 0):
        raise ValueError("Bowl source/result anchors, truncation or release credit changed")
    score = count_record.get("scored_stunt", {})
    if (score.get("source_tally_host_frame") != 4279 or
            score.get("source_result_host_frame") != 4349 or
            score.get("score") != 764 or
            score.get("complete_event_frame_parity") is not False):
        raise ValueError("not the original source scored-stunt candidate")
    newer = phase.get("same_host_frame_samples")
    older = count_record.get("phase_samples")
    if (not isinstance(newer, list) or not isinstance(older, list) or
            len(newer) != len(older) or len(newer) != len(HOST_OFFSETS)):
        raise ValueError("Bowl source artifacts lack the eight preserved hosts")

    rows = []
    for offset, o, c in zip(HOST_OFFSETS, newer, older):
        host = 4279 + offset
        if (o.get("absolute_host_frame") != host or
                c.get("host_frame") != host or
                o.get("offset_from_actual_tally_host_frame") != offset or
                c.get("tally_offset") != offset):
            raise ValueError("Bowl source input/result host clocks drifted")
        totals = o.get("different_guest_bytes", {})
        old_totals = c.get("guest_different_bytes")
        if (not isinstance(old_totals, dict) or totals != old_totals or
                set(totals) != {"wram", "vram", "cgram"} or
                any(type(n) is not int or n < 0 for n in totals.values())):
            raise ValueError("independent guest memory disagreement counts differ")
        profiles = o.get("differing_byte_offsets_by_memory_class", {})
        if not isinstance(profiles, dict):
            raise ValueError("no source-derived actual address offsets")
        fields = {kind: canonical_offsets(profiles.get(kind), totals[kind], kind)
                  for kind in ("wram", "vram", "cgram")}
        common = c.get("both_original_and_native", {})
        # The old independent count capture says "course"; the newer
        # address capture says "track" for the exact same 7E:00CE byte.
        if any(o.get("original_" + k) != common.get(
                   "course" if k == "track" else k) or
               o.get("native_" + k) != common.get(
                   "course" if k == "track" else k)
               for k in ("menu", "track", "race_flag")):
            raise ValueError("original/native source stage fields not comparable")

        groups: dict[str, list[str]] = {}
        for word_offset in fields["wram"]:
            label = classify_address(word_offset)
            groups.setdefault(label, []).append(f"0x{word_offset:05X}")
        rows.append({
            "tally_relative": offset,
            "absolute_host": host,
            "stage_menu": common["menu"],
            "stage_track": common["course"],
            "stage_race_flag": common["race_flag"],
            "different_guest_bytes": totals,
            "wram_regions": groups,
            "vram_different_offsets": [f"0x{x:05X}" for x in fields["vram"]],
            "cgram_different_offsets": [f"0x{x:05X}" for x in fields["cgram"]],
            "named_joypad_word_different_low": 0x72 in fields["wram"],
            "named_joypad_word_different_high": 0x73 in fields["wram"],
        })
    first_word = next((row for row in rows if
                       row["named_joypad_word_different_low"] or
                       row["named_joypad_word_different_high"]), None)
    first_nonunattributed = next((row for row in rows if
                                 any(k not in ("unattributed_stack_page_bytes",
                                               "other_unattributed_bytes")
                                     for k in row["wram_regions"])), None)
    if not first_word:
        raise ValueError("archived Bowl input-latch byte lead disappeared")
    return {
        "schema": SCHEMA,
        "provenance": {
            "offset_capture_run": 38025090532,
            "offset_capture_artifact": 11659973901,
            "independent_count_run": 38024468581,
            "independent_count_artifact": 11659683037,
        },
        "original_native_same_absolute_host_tally": 4279,
        "original_native_same_absolute_host_result": 4349,
        "real_scored_stunt": 764,
        "frames": rows,
        "first_observed_changed_joy1_held_word_host": first_word["absolute_host"],
        "first_observed_named_or_oam_region_host": (
            first_nonunattributed["absolute_host"] if first_nonunattributed else None),
        "earlier_two_samples_only_unattributed_stack_page_offsets": all(
            set(row["wram_regions"]) == {"unattributed_stack_page_bytes"}
            for row in rows[:2]),
        "same_six_unattributed_stack_page_offsets_at_4345_and_4346": (
            rows[4]["wram_regions"].get("unattributed_stack_page_bytes") ==
            rows[5]["wram_regions"].get("unattributed_stack_page_bytes")
            and rows[4]["different_guest_bytes"]["wram"] == 6
            and rows[5]["different_guest_bytes"]["wram"] == 6),
        "original_native_controller_masks_consumed_equal_proven": False,
        "original_native_guest_cpu_nmi_phase_equivalent_proven": False,
        "source_original_writer_or_consumer_pc_identified": False,
        "archived_nonexecuted_joy1_word_writer_candidate": {
            "source": "Nitrodon bank 80 and imported Baldosa original symbols",
            "routine": "Input_ReadPads",
            "routine_bank_pc": "80:D1DB",
            "source_hardware_read_pc": "80:D1DE",
            "source_hardware_read": "LDX $4218",
            "source_wram_store_pc": "80:D1E1",
            "source_wram_store": "STX $72",
            "static_store_x_width_verified_at_runtime": False,
            "usa_original_executed_pc_verified": False,
        },
        "all_samples_have_equal_named_stage": True,
        "raw_guest_memory_retained": False,
        "strict_complete_event_accepted": False,
        "release_credit": 0,
        "caveat": (
            "Two independent archived offset/count witnesses: sampled same-host "
            "address differences, no actual differing byte values, held mask "
            "consumption, NMI phase or gameplay causality. Named symbols are "
            "provisional; stack-page membership does not prove an actual push."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offset-report", type=Path, default=OFFSETS)
    ap.add_argument("--count-report", type=Path, default=COUNTS)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    result = crosswalk(json.loads(args.offset_report.read_text()),
                       json.loads(args.count_report.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "first_observed_changed_held_word_host":
            result["first_observed_changed_joy1_held_word_host"],
        "sampled_hosts": len(result["frames"]),
        "strict_complete_event_accepted": False,
        "release_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
