#!/usr/bin/env python3
"""Independently qualify QA01 frame pilots against archived *genuine* Bowl bytes.

No emulator replay, new USA event, inferred input consumption or phase fix.
The pinned original Actions artifact is SHA-rehashed before any member is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import time
import zipfile
from pathlib import Path

import qa01_frame_capture_replay as capture

ARCHIVE_SHA256 = "2924534f2700714c655647b43e2453c54d4e76f0e258566bcf500439d962ea79"
SOURCE_SHA = "9ee3b8cb876f630d259882dde62da07ba6217c8d"
EXPECTED_CHAIN = "e7629d3bd6f99a919ee6db53dd7f802778bcd05683ef39e03408d6b21eec729d"
EXPECTED_WRAM = (2, 33, 666, 688, 671, 289, 214, 184)
START, END = 339, 346
WRAM, SRAM = 131072, 8192


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def result_frame(log: str) -> int:
    matches = re.findall(r"^script f=(\d+) dump result-onset(?=\s|$)",
                         log, re.MULTILINE)
    need(len(matches) == 1, "source result-onset acknowledgment missing or duplicated")
    return int(matches[0])


def qualify(archive: Path, output: Path) -> dict:
    need(archive.is_file() and not archive.is_symlink(),
         "missing/symlinked pinned genuine Bowl archive")
    archive_bytes = archive.read_bytes()
    need(sha(archive_bytes) == ARCHIVE_SHA256,
         "genuine Bowl Actions archive SHA-256 changed")
    need(not output.exists(), "qualification output root must be new")
    t0 = time.perf_counter()
    with zipfile.ZipFile(archive) as z, tempfile.TemporaryDirectory(
            prefix="qa01-authentic-bowl-") as d:
        names = z.namelist()
        need(len(names) == len(set(names)), "duplicated ZIP member")
        for item in z.infolist():
            need(not item.filename.startswith("/") and
                 ".." not in Path(item.filename).parts and
                 item.file_size <= 16 * 1024 * 1024,
                 "unsafe/oversized archival member")
        report = json.loads(z.read("bowl-report.json"))
        need(report.get("name") == "bowl" and
             report.get("course_id") == "course:03" and
             report.get("native_backend") == "pinned-baldosa",
             "archive is not the original genuine scored Bowl source case")
        need(report.get("rom_sha256") ==
             "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478" and
             report.get("input_sha256") ==
             "3ae5e12c664033f6299a97cf40cb0f8a576d6fed6b73a4d8c600512c72eb9422",
             "source ROM or supplied script identity contradicts pinned archive")
        root = Path(d)
        logs, frames = {}, {}
        for guest, member in (("original", "ref"), ("native", "native")):
            folder = root / guest
            folder.mkdir()
            prefix = f"bowl/replay/{member}/bowl-next-switcher-"
            for offset in range(START, END+1):
                for kind, size in (("wram", WRAM), ("sram", SRAM)):
                    name = f"{prefix}{offset:03d}.{kind}.bin"
                    data = z.read(name)
                    need(len(data) == size,
                         "truncated genuine source memory image: " + name)
                    (folder / Path(name).name).write_bytes(data)
            log_name = ("bowl/replay/reference.log" if guest == "original"
                        else "bowl/replay/native.log")
            path = root / (guest + ".log")
            path.write_bytes(z.read(log_name))
            logs[guest] = path
            frames[guest] = result_frame(path.read_text(errors="replace"))
        identity = {
            "source_sha": SOURCE_SHA,
            "rom_sha256": report["rom_sha256"],
            "movie_sha256": report["original_movie_sha256"],
            # The historical report's input_sha256 names the replay script.
            # The original movie window is the actual controller provenance.
            "input_sha256": report["original_movie_window_sha256"],
            "observation_phase": "post-script-dump",
            "original_frame_origin": frames["original"],
            "native_frame_origin": frames["native"],
            "masked_wram_bytes": 0,
            "masked_sram_bytes": 0,
        }
        need(frames["original"] == 4349 and frames["native"] == 4349,
             "archived Bowl result host clocks differ from immutable evidence")
        extracted = time.perf_counter()
        output.mkdir(parents=True)
        metrics = capture.audit_replay(
            original_root=root/"original", native_root=root/"native",
            original_log=logs["original"], native_log=logs["native"],
            identity=identity, start=START, end=END,
            prefix="bowl-next-switcher-", width=3,
            report=output/"frame-fingerprints.json",
            retained=output/"retained", review=output/"independent-review.json",
            max_retained=8)
        rec = json.loads((output/"frame-fingerprints.json").read_text())
        observed = [x["types"]["wram"]["unmasked_differing_byte_count"]
                    for x in rec["rows"]]
        need(tuple(observed) == EXPECTED_WRAM and
             rec["full_unmasked_differing_byte_occurrences"] ==
             {"wram": 2747, "sram": 24} and
             rec["frame_pair_digest_chain_sha256"] == EXPECTED_CHAIN,
             "actual archived raw memory disagrees with independent eight-frame census")
        result = {
            "schema": "ur-qa01-authentic-bowl-eight-frame-pilot-qualification/1",
            "archive_sha256_independently_rehashed": sha(archive_bytes),
            "genuine_source_sha_from_archival_receipt": SOURCE_SHA,
            "original_2014_movie_sha256_from_archival_report":
                report["original_movie_sha256"],
            "original_snes9x_core_sha256_reported_not_reopened":
                report["reference_core_sha256"],
            "native_elf_sha256_reported_not_reopened":
                report["native_executable_sha256"],
            "source_original_and_native_actual_result_frame": frames,
            "genuine_consecutive_raw_frame_pairs": END - START + 1,
            "full_raw_images_independently_reopened": (END-START+1)*4,
            "archived_raw_bytes": (END-START+1)*2*(WRAM+SRAM),
            "unmasked_wram_byte_difference_occurrences": 2747,
            "unmasked_sram_byte_difference_occurrences": 24,
            "digest_chain": EXPECTED_CHAIN,
            "source_zip_extract_seconds": round(extracted-t0, 6),
            "offline_audit_metrics": metrics,
            "new_emulator_execution_performed": False,
            "actual_guest_input_poll_consumption_proven": False,
            "whole_race_continuous_coverage": False,
            "original_native_observation_phase_equivalence_proven": False,
            "USA_events_accepted": 0,
        }
        (output/"qualification.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(qualify(args.archive, args.output),
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
