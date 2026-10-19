#!/usr/bin/env python3
"""Re-pair archived Dragster→Zoo original/native RAW images at equal guest host frames.

Read-only, exact SHA-bound ZIP verifier. No replay, input rephase or event credit.
Historical source-movie frames remain a separate clock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

SCHEMA = "UR-QA01-DRAGSTER-SAME-ABSOLUTE-HOST-RAW-ARCHIVE/1"
OFFSETS = (304, 308, 312, 314, 315, 316, 317, 318, 319, 320, 321, 324, 328, 336)
SIZES = {"wram": 131072, "sram": 8192}
HEX = re.compile(r"^[0-9a-f]{64}$")


class EvidenceError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact_raw(archive: ZipFile, name: str, size: int) -> bytes:
    info = archive.getinfo(name)
    if info.file_size != size or (info.external_attr >> 16) & 0o170000 == 0o120000:
        raise EvidenceError(f"missing full regular memory image {name}")
    data = archive.read(info)
    if len(data) != size:
        raise EvidenceError(f"truncated memory image {name}")
    return data


def log_frame(log: str, label: str) -> int:
    matches = re.findall(r"(?m)^script f=(\d+) dump " + re.escape(label)
                         + r"(?:\s|$)", log)
    if len(matches) != 1:
        raise EvidenceError(f"missing or duplicated executed guest dump {label}")
    return int(matches[0])


def differences(a: bytes, b: bytes) -> dict:
    if len(a) != len(b):
        raise EvidenceError("cannot compare unequal whole memory image sizes")
    changed = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    return {
        "all_bytes_compared": len(a), "excluded_bytes": 0,
        "differing_bytes": len(changed), "byte_exact": not changed,
        "first_12_differences": [
            {"offset": i, "original_byte": a[i], "native_byte": b[i]}
            for i in changed[:12]],
    }


def analyze(path: Path, expected_zip_sha256: str) -> dict:
    if not HEX.fullmatch(expected_zip_sha256):
        raise EvidenceError("expected ZIP SHA256 is mandatory")
    if digest(path.read_bytes()) != expected_zip_sha256:
        raise EvidenceError("original archive ZIP SHA256 mismatch")
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(
                n.startswith("/") or ".." in Path(n).parts for n in names):
            raise EvidenceError("unsafe or duplicated archive member name")
        report_bytes = archive.read("dragster-report.json")
        report = json.loads(report_bytes)
        event = report.get("original_source_event") or {}
        hand = report.get("dragster_next_zoo_handoff") or {}
        if (
            report.get("name") != "dragster"
            or report.get("course_id") != "course:01"
            or event.get("original_entry_frame") != 794
            or event.get("original_result_frame") != 2874
            or event.get("source_next_zoo", {}).get("sample_offsets") != list(OFFSETS)
            or hand.get("original_movie_zoo_entry_frame") != 3190
            or hand.get("original_movie_zoo_entry_relative_to_dragster_result") != 316
            or hand.get("release_complete_usa_event_credit") != 0
            or hand.get("source_controller_masks_rephased") is not False
            or hand.get("all_three_guest_result_relative_entry_offsets_equal") is not False
            or report.get("comparison", {}).get("paired_event_candidate") is not False
        ):
            raise EvidenceError("source event, offsets or negative outcome inconsistent")
        rows = hand.get("samples")
        if (not isinstance(rows, list) or len(rows) != len(OFFSETS)
                or [r.get("offset_from_respective_dragster_result") for r in rows]
                != list(OFFSETS)):
            raise EvidenceError("missing genuine ordered event samples")
        logs = {
            "original": archive.read("dragster/replay/reference.log").decode("utf8"),
            "native": archive.read("dragster/replay/native.log").decode("utf8"),
        }
        observations = {"original": {}, "native": {}}
        frames = report.get("comparison", {}).get("terminal_result_guest_frame") or {}
        for side, directory, guest_entry, guest_result in (
            ("original", "ref", "reference_entry", "reference_relative"),
            ("native", "native", "native_entry", "native_relative"),
        ):
            entry, result = report.get(guest_entry), frames.get(guest_result)
            if type(entry) is not int or type(result) is not int or min(entry, result) < 0:
                raise EvidenceError("invalid independently observed guest clocks")
            for row in rows:
                offset = row["offset_from_respective_dragster_result"]
                guest = row["fresh_guests"][side]
                label = f"dragster-next-zoo-{offset:03d}"
                host = log_frame(logs[side], label)
                if host != entry + result + offset or guest.get("host_frame") != host:
                    raise EvidenceError("real guest host timestamp mismatch")
                raw = {}
                for kind, size in SIZES.items():
                    image = exact_raw(
                        archive, f"dragster/replay/{directory}/{label}.{kind}.bin", size)
                    if digest(image) != guest.get(f"full_{kind}_sha256"):
                        raise EvidenceError("reported memory SHA256 differs from executed bytes")
                    raw[kind] = image
                named = {"menu": raw["wram"][0x9F], "track": raw["wram"][0xCE],
                         "in_race": raw["wram"][0x313], "tour_row": raw["wram"][0xD0]}
                if any(guest.get(k) != value for k, value in named.items()):
                    raise EvidenceError("claimed named state differs from real guest")
                observations[side][host] = {
                    "offset": offset, "named": named, "raw": raw,
                }
        common_hosts = sorted(
            set(observations["original"]) & set(observations["native"]))
        if not common_hosts:
            raise EvidenceError("no actual same-host observations")
        comparisons = []
        for host in common_hosts:
            a, b = observations["original"][host], observations["native"][host]
            comparisons.append({
                "absolute_guest_host_frame": host,
                "original_result_relative_offset": a["offset"],
                "native_result_relative_offset": b["offset"],
                "original_named_state": a["named"],
                "native_named_state": b["named"],
                "named_state_equal": a["named"] == b["named"],
                "full_wram": differences(a["raw"]["wram"], b["raw"]["wram"]),
                "full_sram": differences(a["raw"]["sram"], b["raw"]["sram"]),
            })
        onsets = {}
        brackets = hand.get("entry_brackets") or {}
        for side, entry_key, result_key in (
            ("original", "reference_entry", "reference_relative"),
            ("native", "native_entry", "native_relative"),
        ):
            onset_offset = brackets.get(side, {}).get("exact_adjacent_onset_offset")
            if type(onset_offset) is not int:
                raise EvidenceError("guest lacks an exact observed next-Zoo entry")
            host = report[entry_key] + frames[result_key] + onset_offset
            if (host not in observations[side]
                    or observations[side][host]["named"]["in_race"] != 1):
                raise EvidenceError("claimed entry lacks observed guest race-active state")
            onsets[side] = host
        return {
            "schema": SCHEMA,
            "original_zip_sha256": expected_zip_sha256,
            "producer_report_sha256": digest(report_bytes),
            "source_2014_zoo_entry_movie_frame": 3190,
            "source_result_relative_zoo_entry": 316,
            "fresh_guest_absolute_zoo_onsets": onsets,
            "same_host_frame_count": len(comparisons),
            "same_host_frames": common_hosts,
            "samples": comparisons,
            "all_full_wram_pairs_equal": all(
                x["full_wram"]["byte_exact"] for x in comparisons),
            "all_full_sram_pairs_equal": all(
                x["full_sram"]["byte_exact"] for x in comparisons),
            "historical_movie_clock_not_equated_to_guest": True,
            "controller_input_rephased": False,
            "cpu_spc_timing_causality_proven": False,
            "full_usa_event_accepted": False,
            "windows_disk_persistence_proven": False,
            "release_complete_event_credit": 0,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--zip-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.archive, args.zip_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Independently re-paired {len(result['samples'])} genuine same-host guest snapshots; no USA event credit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
