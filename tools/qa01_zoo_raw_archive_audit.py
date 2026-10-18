#!/usr/bin/env python3
"""Independent raw 128-KiB Zoo mesh / 8-KiB Zoo->Bowl artifact audit.

Executed original/native guest memory is mandatory. This reuses the separate
QA-01 Bowl raw-byte reader, NOT the event producer's result comparator. It
neither runs a guest nor awards original USA course/release acceptance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa01_bowl_handoff_raw_archive_audit import (
    digest, read_exact, read_logged_frame, raw_wram_pair,
)

SCHEMA = "UR-QA01-ZOO-RAW-MESH-AND-NEXT-BOWL-INDEPENDENT/1"
CHECKPOINT_COUNT = 78
BOWL_OFFSETS = (259, 263, 264, 265, 266, 267, 268, 269, 272, 276, 280)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def rank_and_checksum(data: bytes, track: int = 1) -> dict:
    """Independently recalculate source-earned rank 0 and the full table sum."""
    require(len(data) == 8192, "guest SRAM must contain entire 8192-byte battery")
    w = lambda at: int.from_bytes(data[at:at + 2], "little")
    return {
        "rank": 0,
        "value_word": w(0x0422 + 2 * track),
        "holder_index": data[0x0550 + track],
        "checksum_stored": w(0x054E),
        "checksum_calculated": sum(w(0x0422 + 2 * i) for i in range(150)) & 0xFFFF,
    }


def guest_bytes(root: Path, side: str, tag: str, log: str, host: int) -> tuple[bytes, bytes]:
    require(type(host) is int and host >= 0, "invalid observed guest host clock")
    require(read_logged_frame(log, tag) == host,
            "missing/altered/duplicate authentic guest dump host clock: " + side + "/" + tag)
    directory = root / "work" / "zoom-zoo" / "replay" / side
    return (read_exact(directory / (tag + ".wram.bin"), 131072),
            read_exact(directory / (tag + ".sram.bin"), 8192))


def verify_wram_pair(raw: dict[str, tuple[bytes, bytes]], expected: dict) -> dict:
    audit = raw_wram_pair(raw["ref"][0], raw["native"][0])
    require(expected == audit, "raw 128KiB guest WRAM contradicts producer's unmasked byte census")
    return audit


def audit(root: Path) -> dict:
    case = root / "case-result.json"
    producer = root / "producer-report.json"
    require(case.is_file() and producer.is_file()
            and not case.is_symlink() and not producer.is_symlink(),
            "missing original executed producer and classified case receipts")
    raw_producer = producer.read_bytes()
    classification = json.loads(case.read_bytes())
    report = json.loads(raw_producer)
    require(classification.get("case") == "zoom-zoo" and
            classification.get("course_id") == "course:02" and
            classification.get("evidence", {}).get("producer_sha256") == digest(raw_producer) and
            classification.get("release_credit") == 0 and
            classification.get("disposition") in ("strict_candidate", "strict_divergence"),
            "not the exact classified source-bound executed USA Zoo producer")
    require(report.get("name") == "zoom-zoo" and
            report.get("native_backend") == "pinned-baldosa" and
            report.get("course_id") == "course:02" and
            report.get("reference_entry") is not None and
            type(report.get("reference_entry")) is int and
            type(report.get("native_entry")) is int,
            "unknown original/native Zoo guest provenance")
    source = report.get("original_source_event")
    require(isinstance(source, dict) and
            source.get("original_entry_frame") == 3190 and
            source.get("original_result_frame") == 8353 and
            source.get("source_active_frames_to_result") == 5163,
            "original 2014 USA Zoo source identity altered")
    mesh = report.get("zoo_race_mesh")
    require(isinstance(mesh, dict) and
            mesh.get("mesh_checkpoint_count") == CHECKPOINT_COUNT and
            mesh.get("all_128k_wram_bytes_examined_per_pair") == 131072 and
            mesh.get("masked_or_excluded_wram_bytes") == 0 and
            mesh.get("release_complete_usa_event_credit") == 0,
            "missing/modified real full-race unmasked Zoo mesh")
    rows = mesh.get("samples")
    require(isinstance(rows, list) and len(rows) == CHECKPOINT_COUNT,
            "missing actual 78 original/native full-WRAM checkpoint observations")
    offsets = [x.get("race_relative_frame") for x in rows if isinstance(x, dict)]
    require(len(offsets) == CHECKPOINT_COUNT and
            all(type(f) is int and f >= 0 for f in offsets) and
            offsets == sorted(set(offsets)) and offsets[0] == 0 and
            offsets[-1] == 5120 and
            set(range(5034, 5047)).issubset(offsets),
            "not the exact intact dense USA Zoo checkpoint mesh")
    base = root / "work" / "zoom-zoo" / "replay"
    logs = {}
    for side, logfile in (("ref", "reference.log"), ("native", "native.log")):
        path = base / logfile
        require(path.is_file() and not path.is_symlink(), "missing original guest execution log " + logfile)
        logs[side] = path.read_text(encoding="utf-8", errors="replace")

    exact, occurrences = 0, 0
    by_address = {}
    for row in rows:
        offset = row["race_relative_frame"]
        tag = "race-entered" if offset == 0 else f"scene-{offset:05d}"
        original_host = report["reference_entry"] + offset
        native_host = report["native_entry"] + offset
        require(row.get("original_absolute_host_frame") == original_host and
                row.get("native_absolute_host_frame") == native_host,
                "mesh host frame contradicts independent observed guest entry clocks")
        actual = {
            side: guest_bytes(root, side, tag, logs[side], host)
            for side, host in (("ref", original_host), ("native", native_host))
        }
        row_diff = verify_wram_pair(actual, row.get("original_native_full_wram_byte_difference"))
        exact += int(row_diff["byte_exact"])
        occurrences += row_diff["differing_byte_count"]
        for item in row_diff["first_24_differences"]:
            address = item["snes_address"]
            by_address[address] = by_address.get(address, 0) + 1
    require(exact == mesh.get("raw_byte_exact_sample_count"),
            "reported Zoo full-WRAM exact checkpoints disagree with independently reopened bytes")
    first = next((r for r in rows
                  if r["original_native_full_wram_byte_difference"]["differing_byte_count"]), None)
    if first:
        f = first["original_native_full_wram_byte_difference"]
        require(mesh.get("first_nonidentical_raw_wram_pair") == {
            "race_relative_frame": first["race_relative_frame"],
            "original_absolute_host_frame": first["original_absolute_host_frame"],
            "native_absolute_host_frame": first["native_absolute_host_frame"],
            "first_differing_address": f["first_differing_address"],
            "differing_byte_count": f["differing_byte_count"],
        }, "reported first real Zoo original/native byte divergence altered")

    handoff = report.get("zoo_next_bowl_handoff")
    require(isinstance(handoff, dict) and
            handoff.get("sample_offsets") == list(BOWL_OFFSETS) and
            handoff.get("sample_count") == len(BOWL_OFFSETS) and
            handoff.get("release_complete_event_credit") == 0 and
            isinstance(handoff.get("samples"), list) and
            len(handoff["samples"]) == len(BOWL_OFFSETS),
            "source-authentic Zoo next Bowl proof absent")
    unequal_sram = []
    handoff_wram_unequal = []
    for offset, row in zip(BOWL_OFFSETS, handoff["samples"]):
        require(row.get("offset_from_observed_zoo_result") == offset,
                "misregistered or reordered real Zoo next-Bowl sample")
        tag = f"zoo-next-bowl-{offset:03d}"
        guests = row.get("fresh_guests")
        require(isinstance(guests, dict) and set(guests) == {"original", "native"},
                "incomplete two-guest Zoo next-Bowl evidence")
        actual = {}
        for side, name in (("ref", "original"), ("native", "native")):
            host = report[{"ref": "reference_entry", "native": "native_entry"}[side]] + 5163 + offset
            actual[side] = guest_bytes(root, side, tag, logs[side], host)
            g = guests[name]
            wram, sram = actual[side]
            rank = rank_and_checksum(sram)
            require(g.get("actual_host_frame") == host and
                    g.get("full_wram_bytes") == len(wram) and
                    g.get("wram_sha256") == digest(wram) and
                    g.get("sram_sha256") == digest(sram) and
                    g.get("source_earned_zoo_best_lap") == {
                        k: rank[k] for k in ("rank", "value_word", "holder_index")} and
                    g.get("record_checksum_stored") == rank["checksum_stored"] and
                    g.get("record_checksum_calculated") == rank["checksum_calculated"] and
                    g.get("record_checksum_matches") is
                        (rank["checksum_stored"] == rank["checksum_calculated"]),
                    "raw original/native ranked Zoo record or full guest hash contradicted")
        pair = verify_wram_pair(actual, row.get("original_native_full_wram_byte_difference"))
        same_sram = actual["ref"][1] == actual["native"][1]
        differences = [i for i, (a, b) in enumerate(zip(actual["ref"][1], actual["native"][1]))
                       if a != b]
        require(row.get("original_native_full_sram_equal") is same_sram and
                row.get("battery_sram_differing_byte_count") == len(differences) and
                row.get("battery_first_differences") == [
                    {"offset": i, "original_byte": actual["ref"][1][i],
                     "native_byte": actual["native"][1][i]}
                    for i in differences[:8]],
                "raw original/native 8KiB SRAM differ from actual producer claim")
        if differences:
            unequal_sram.append(offset)
        if not pair["byte_exact"]:
            handoff_wram_unequal.append(offset)
    require(handoff.get("all_original_native_full_sram_pairs_equal") is not bool(unequal_sram) and
            handoff.get("all_original_native_full_wram_pairs_equal") is not bool(handoff_wram_unequal),
            "producer Zoo next-Bowl aggregate hides actual raw guest differences")
    return {
        "schema": SCHEMA,
        "producer_sha256": digest(raw_producer),
        "original_native_guest_same_source_proven_only_in_receipt": True,
        "full_zoo_mesh_rehashed_original_native_128k_pairs": len(rows),
        "full_zoo_mesh_exact_pairs": exact,
        "full_zoo_mesh_nonexact_pairs": len(rows) - exact,
        "full_zoo_mesh_unmasked_differing_byte_occurrences": occurrences,
        "full_zoo_mesh_reported_difference_address_occurrences": by_address,
        "next_bowl_full_wram_and_sram_pairs_rehashed": len(BOWL_OFFSETS),
        "next_bowl_wram_unequal_offsets": handoff_wram_unequal,
        "next_bowl_sram_unequal_offsets": unequal_sram,
        "source_movie_raw_memory_rehashed": False,
        "all_frame_cpu_spc_gameplay_equivalence_proven": False,
        "exact_windows_shipping_candidate_proven": False,
        "cold_windows_disk_durability_proven": False,
        "independent_usa_event_adjudication": "HOLD",
        "accepted_usa_events": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-root", type=Path, required=True)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    try:
        result = audit(a.artifact_root)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        p.exit(2, "QA01_ZOO_REAL_MEMORY_INVALID: " + str(exc) + "\n")
    data = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(data, encoding="utf-8")
    print(data, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
