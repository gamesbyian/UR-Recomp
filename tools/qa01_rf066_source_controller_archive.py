#!/usr/bin/env python3
"""Reopen genuine RF066 original/native Zoo archive and its 2014 pad supply.

This is a source-authentic *input-supply* join, not proof that the guest CPUs
read any inputs. No emulator execution, controller retiming, gameplay patch,
masked raw bytes, 1/45 acceptance, or automatic factory dispatch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import tempfile
import zipfile
from pathlib import Path

import extract_historical_smv_scene_window as smv
import qa01_verify_2014_movie_controller_supply as movie_identity
import qa01_verify_supplied_controller_streams as supplied


SCHEMA = "ur-qa01-rf066-genuine-source-controller-archive/1"
PINNED_CASE_SHA256 = "494737bb6a1c422141c40f7175883f212767c3d774ee63fb0ba82add78cb445f"
PINNED_SOURCE_SHA = "d4a5bc536b22fdf66f5778c3f242a7e1a3468eda"
ROOT = "work/zoom-zoo/replay/"
ORIGINAL_INPUT = ROOT + "ref.input"
NATIVE_INPUT = ROOT + "pinned-baldosa.input"
ORIGINAL_LOG = ROOT + "reference.log"
NATIVE_LOG = ROOT + "native.log"
REPORT = "producer-report.json"


def must(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def success_frame(log: bytes, label: str, guest: str) -> int:
    # A log line merely containing a 'dump LABEL' string is not proof the
    # dump succeeded. Preserve source Snes9x versus native success syntax.
    endings = {
        "original": rb" fb=[0-9]+x[0-9]+ [A-Za-z0-9]+ sram=8192 ppuw=[0-9]+",
        "native": rb" ok",
    }
    expression = (rb"^script f=([0-9]+) dump " +
                  re.escape(label.encode("ascii")) + endings[guest] + rb"$")
    hits = re.findall(expression, log, flags=re.MULTILINE)
    must(len(hits) == 1, "missing/duplicate successful " + guest +
         " actual guest " + label + " dump")
    return int(hits[0])


def original_movie_segments(movie: Path, metadata: Path) -> tuple[dict, list[dict]]:
    must(movie.is_file() and not movie.is_symlink() and
         metadata.is_file() and not metadata.is_symlink(),
         "missing/symlinked immutable original movie or source metadata")
    movie_raw = movie.read_bytes()
    must(digest(movie_raw) == movie_identity.PINNED_MOVIE_CONTAINER_SHA256,
         "genuine original movie ZIP SHA256 changed")
    meta = json.loads(metadata.read_text(encoding="utf-8"))
    must(meta.get("path") ==
         "reference/imported/tas-bots/dessyreqt-4250-submission.smv"
         and meta.get("container") == "zip"
         and meta.get("contained_name") == "100% run.smv"
         and meta.get("container_size_bytes") == len(movie_raw),
         "original movie source metadata identity changed")
    raw_movie, member = smv.read_movie(movie)
    must(member == meta["contained_name"] and
         len(raw_movie) == meta["smv_size_bytes"],
         "decompressed original movie member mismatch")
    window = smv.window(
        raw_movie, meta, movie_identity.MOVIE_RACE_ENTRY,
        movie_identity.SOURCE_WINDOW_FRAMES)
    must(window["raw_controller_window_sha256"] ==
         movie_identity.PINNED_RAW_WINDOW_SHA256 and
         window["movie_frame_range"] ==
         [movie_identity.MOVIE_RACE_ENTRY,
          movie_identity.MOVIE_RACE_ENTRY +
          movie_identity.SOURCE_WINDOW_FRAMES - 1],
         "source original movie controller window changed")
    normalized = [
        {"start_relative_to_actual_guest_entry": row["start"],
         "duration_frames": row["duration"],
         "nonzero_mask_hex": f"{int(row['mask'], 16):03x}"}
        for row in window["relative_input_segments"] if int(row["mask"], 16)
    ]
    return window, normalized


def verify(archive: Path, movie: Path, metadata: Path,
           expected_sha256: str = PINNED_CASE_SHA256) -> dict:
    must(archive.is_file() and not archive.is_symlink(),
         "missing or symlinked RF066 original archive")
    must(re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is not None,
         "invalid expected immutable case archive SHA256")
    must(digest(archive.read_bytes()) == expected_sha256,
         "RF066 genuine case artifact immutable SHA256 mismatch")
    with zipfile.ZipFile(archive) as zipfile_case:
        infos = zipfile_case.infolist()
        names = [member.filename for member in infos]
        must(len(infos) <= 600 and len(names) == len(set(names)) and
             all(not member.is_dir() and
                 not stat.S_ISLNK(member.external_attr >> 16) and
                 not member.filename.startswith("/") and
                 ".." not in Path(member.filename).parts and
                 member.file_size <= 2_000_000 for member in infos) and
             sum(member.file_size for member in infos) <= 65_000_000 and
             zipfile_case.testzip() is None,
             "duplicate/unsafe/corrupt or unexpectedly large source archive")
        required = (REPORT, ORIGINAL_INPUT, NATIVE_INPUT,
                    ORIGINAL_LOG, NATIVE_LOG)
        must(all(path in names for path in required),
             "genuine archive lacks original/native producer or replay input/log bytes")
        report = json.loads(zipfile_case.read(REPORT))
        must(type(report) is dict and report.get("schema_version") == 1 and
             report.get("name") == "zoom-zoo" and
             report.get("course_id") == "course:02" and
             report.get("native_backend") == "pinned-baldosa" and
             report.get("original_movie_sha256") ==
                movie_identity.PINNED_MOVIE_CONTAINER_SHA256 and
             report.get("original_movie_window_sha256") ==
                movie_identity.PINNED_RAW_WINDOW_SHA256 and
             report.get("admission") ==
                "investigative candidate; not a release-ledger pass",
             "wrong source event or unsupported complete-USA acceptance report")
        controller = report.get("qa01_capture_ab_control")
        must(type(controller) is dict and
             controller.get("schema") == supplied.AB and
             controller.get("repository_source_sha") == PINNED_SOURCE_SHA and
             controller.get("controller_movie_window_sha256") ==
                movie_identity.PINNED_RAW_WINDOW_SHA256 and
             controller.get("capturing_continuous_frames") is False and
             controller.get("cpu_joypad_reads_proven") is False and
             controller.get("full_event_accepted") is False and
             report.get("qa01_continuous_memory_capture") is None,
             "source-identity/input-poll or full-event witness overclaim")
        event = report.get("original_source_event")
        must(type(event) is dict and
             event.get("original_entry_frame") ==
                movie_identity.MOVIE_RACE_ENTRY and
             event.get("original_result_frame") ==
                movie_identity.MOVIE_RACE_RESULT and
             event.get("source_active_frames_to_result") ==
                movie_identity.SOURCE_RACE_RESULT_RELATIVE,
             "genuine 2014 Zoom Zoo entry/result chronology differs")
        result = report.get("comparison") or {}
        host = result.get("terminal_result_guest_frame") or {}
        must(host.get("reference_relative") ==
             host.get("native_relative") ==
             movie_identity.SOURCE_RACE_RESULT_RELATIVE and
             report.get("zoo_next_bowl_handoff", {}).get(
                "source_next_bowl_active_entry_offset") == 267,
             "source/native result or original next-event observation changed")
        root = Path(tempfile.mkdtemp(prefix="qa01-rf066-controller-"))
        try:
            parsed = {}
            for guest, file_name, prefix, anchor in (
                ("original", ORIGINAL_INPUT, "reference", "reference_entry"),
                ("native", NATIVE_INPUT, "native", "native_entry")
            ):
                source = zipfile_case.read(file_name)
                must(type(controller.get(prefix + "_supplied_input_sha256")) is str and
                     digest(source) ==
                        controller[prefix + "_supplied_input_sha256"] and
                     len(source) == controller.get(prefix + "_supplied_input_bytes"),
                     "actual source/native input file conflicts with producer SHA/length")
                file_path = root / (guest + ".input")
                file_path.write_bytes(source)
                _, events = supplied.reopen(
                    file_path, native=(guest == "native"), pinned=True,
                    origin=report[anchor])
                parsed[guest] = events
            must(parsed["original"] == parsed["native"],
                 "original/native controller source-relative segments differ")
        finally:
            import shutil
            shutil.rmtree(root)
        seen = {}
        for guest, filename, prefix, origin_key in (
                ("original", ORIGINAL_LOG, "reference", "reference_entry"),
                ("native", NATIVE_LOG, "native", "native_entry")):
            log = zipfile_case.read(filename)
            must(digest(log) == controller[prefix + "_guest_log_sha256"],
                 "actual source/native replay log SHA256 changed")
            origin = report[origin_key]
            must(type(origin) is int and
                 success_frame(log, "race-entered", guest) == origin and
                 success_frame(log, "result-onset", guest) - origin ==
                    movie_identity.SOURCE_RACE_RESULT_RELATIVE and
                 success_frame(log, "result-stable", guest) - origin == 5169,
                 "source/native actual successful dump frame origins or results changed")
            seen[guest] = origin
    window, original_segments = original_movie_segments(movie, metadata)
    must(parsed["original"] == original_segments,
         "original 2014 actual SMV pad segments differ from both replay-supplied inputs")
    serialized = json.dumps(original_segments, sort_keys=True,
                            separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return {
        "schema": SCHEMA,
        "source_case_zip_sha256": expected_sha256,
        "source_research_revision": PINNED_SOURCE_SHA,
        "original_2014_movie_sha256": movie_identity.PINNED_MOVIE_CONTAINER_SHA256,
        "actual_original_movie_window_sha256": window["raw_controller_window_sha256"],
        "original_2014_movie_range": window["movie_frame_range"],
        "original_2014_controller_frames_reopened": window["frames"],
        "original_actual_guest_race_entry_host_frame": seen["original"],
        "native_actual_guest_race_entry_host_frame": seen["native"],
        "both_actual_guest_logs_sha256_verified": True,
        "both_guest_result_dumps_executed_at_relative_5163": True,
        "both_supplied_guest_input_files_independently_reopened": True,
        "source_original_native_segment_population": len(original_segments),
        "source_original_native_segment_sha256": digest(serialized),
        "all_actual_2014_movie_to_supplied_guest_segments_equal": True,
        "actual_CPU_joypad_poll_consumption_proven": False,
        "original_native_instruction_phase_equivalence_proven": False,
        "full_race_Windows_persistence_proven": False,
        "accepted_USA_events": 0,
        "release_QA_gates_awarded": 0,
        "adjudication": "HOLD: controller supply only; actual CPU reads remain unverified",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", required=True, type=Path)
    ap.add_argument("--movie", required=True, type=Path)
    ap.add_argument("--metadata", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    must(not args.output.exists(), "refuse to overwrite independently reviewed result")
    result = verify(args.archive, args.movie, args.metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("Genuine RF066 Zoo: 2014 source movie to original/native supplied inputs verified; CPU reads HOLD")


if __name__ == "__main__":
    main()
