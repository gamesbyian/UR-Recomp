#!/usr/bin/env python3
"""Independent read-only admission of a genuine Zoo capture on/off Actions ZIP.

This tool reopens the raw memory images, not the original/native executables or
the absent guest replay stdout logs. No result can award complete-event credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import qa01_verify_frame_capture as raw_verifier

PINNED_SHA = "be72834ac617da8dfb96c591e06efaa18adbfe7d872cc64f6a306d3db8db0765"
ROOT = "qa01-zoo-ab/"
RAW = ROOT + "on/zoom-zoo/replay/qa01-frame-evidence/"
DOC = {
    "off": ROOT + "off/producer-report.json",
    "on": ROOT + "on/producer-report.json",
    "ab": ROOT + "independent-ab-review.json",
    "frames": RAW + "fingerprints.json",
    "review": RAW + "independent-review.json",
    "metrics": RAW + "metrics.json",
}
SEMANTIC_EXCLUSIONS = frozenset((
    "reference_script_sha256", "input_sha256", "qa01_capture_ab_control",
    "qa01_continuous_memory_capture",
))


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def stable_guest_semantics(d: dict) -> dict:
    return {key: val for key, val in d.items()
            if key not in SEMANTIC_EXCLUSIONS}


def verify(archive: Path, expected_sha: str = PINNED_SHA) -> dict:
    data = archive.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected_sha,
            "source ZIP SHA256 differs from pinned original")
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [item.filename for item in infos]
        require(len(infos) <= 2000 and len(names) == len(set(names))
                and all(not it.is_dir() and not it.filename.startswith("/")
                        and ".." not in Path(it.filename).parts
                        and it.file_size <= 2_000_000 for it in infos)
                and sum(x.file_size for x in infos) <= 30_000_000
                and z.testzip() is None, "unsafe, duplicated or corrupt archive members")
        require(all(n in names for n in DOC.values())
                and all(ROOT + side + "/exit-code.txt" in names
                        for side in ("off", "on")),
                "missing original/native A/B primary report or exit status")
        d = {k: json.loads(z.read(n)) for k, n in DOC.items()}
        on, off = d["on"], d["off"]
        require(on.get("name") == off.get("name") == "zoom-zoo"
                and stable_guest_semantics(on) == stable_guest_semantics(off),
                "capture-on/off changed original/native game state or result")
        a, b = (obj["qa01_capture_ab_control"] for obj in (off, on))
        keys = ("repository_source_sha", "controller_movie_window_sha256",
                "reference_supplied_input_sha256", "native_supplied_input_sha256",
                "reference_supplied_input_bytes", "native_supplied_input_bytes")
        require(a["capturing_continuous_frames"] is False
                and b["capturing_continuous_frames"] is True
                and a["schema"] == b["schema"] ==
                    "ur-qa01-capture-ab-replay-control/1"
                and all(a[k] == b[k] for k in keys)
                # This producer names the *replay command script* hash
                # "input_sha256"; it is NOT the independently tracked movie
                # controller-window hash. Adding dump tags changes this.
                and off["input_sha256"] == off["reference_script_sha256"] ==
                    a["reference_script_sha256"]
                and on["input_sha256"] == on["reference_script_sha256"] ==
                    b["reference_script_sha256"]
                and a["reference_script_sha256"] != b["reference_script_sha256"],
                "capture test altered guest input or failed to toggle dump scripts")
        exits = {side: int(z.read(ROOT + side + "/exit-code.txt").strip())
                 for side in ("off", "on")}
        require(exits["on"] == exits["off"],
                "capture changed the producer's strict gameplay exit status")
        require(on["comparison"]["paired_event_candidate"] is False
                and on["comparison"]["terminal_result_frame_matched"] is False
                and on["zoo_race_mesh"]["masked_or_excluded_wram_bytes"] == 0
                and on["zoo_race_mesh"]["every_gameplay_frame_compared"] is False
                and on["zoo_next_bowl_handoff"]["release_complete_event_credit"] == 0,
                "bounded research case is incorrectly claimed as accepted game")
        frames = d["frames"]
        ident = frames["source_identity"]
        require(ident["source_sha"] == b["repository_source_sha"]
                and ident["input_sha256"] == b["controller_movie_window_sha256"]
                and ident["rom_sha256"] == on["rom_sha256"]
                and ident["movie_sha256"] == on["original_movie_sha256"],
                "frame images do not belong to the supplied ROM/movie/input case")
        capture = on["qa01_continuous_memory_capture"]
        require(capture["fingerprints_sha256"] ==
                    hashlib.sha256(z.read(DOC["frames"])).hexdigest()
                and capture["independent_review_sha256"] ==
                    hashlib.sha256(z.read(DOC["review"])).hexdigest()
                and capture["metrics"] == d["metrics"],
                "producer capture report's exact evidence hashes changed")
        require(d["ab"]["admitted_usa_events"] == 0
                and d["ab"]["existing_semantic_observations_unchanged"] is True
                and d["ab"]["same_supplied_original_native_input_bytes_digest"] is True
                and d["ab"]["same_source_controller_and_binaries"] is True
                and d["metrics"]["accepted_USA_events"] == 0
                and d["metrics"]["original_guest_acknowledged_frames"] ==
                    d["metrics"]["native_guest_acknowledged_frames"] ==
                    frames["coverage"]["required_frames"] ==
                    d["ab"]["actual_complete_consecutive_frame_acknowledgments"],
                "on/off self-report contradicts zero-credit bounded capture")
        begin, end = frames["coverage"]["start"], frames["coverage"]["end"]
        require((begin, end) ==
                    (d["ab"]["bounded_capture_start"],
                     d["ab"]["bounded_capture_end"]),
                "frame capture window does not match review")
        prefix = RAW + "retained/"
        present = {n[len(prefix):] for n in names if n.startswith(prefix)}
        manifest = frames["raw_retained_members"]
        require(present == {m["member"] for m in manifest},
                "raw original/native memory members are missing or unlisted")
        with tempfile.TemporaryDirectory(prefix="qa01-zoo-ab-audit-") as td:
            root = Path(td)
            for name in present:
                require(name == Path(name).name, "unsafe raw memory filename")
                (root / name).write_bytes(z.read(prefix + name))
            independently = raw_verifier.verify(frames, root)
        require(independently == d["review"],
                "independently reopened raw memory contradicts submitted receipt")
        require(d["ab"]["retained_evidence_bytes"] ==
                    d["metrics"]["retained_full_raw_image_bytes"] ==
                    len(present) // 4 * 2 * (131072 + 8192),
                "actual retained original/native image length disagrees with reports")
        result = on["comparison"]["terminal_result_guest_frame"]
        handoff = on["zoo_next_bowl_handoff"]
        return {
            "schema": "ur-qa01-independent-zoo-capture-ab-archive/1",
            "source_zip_sha256": expected_sha,
            "archive_members_crc_verified": len(infos),
            "source_identity": ident,
            "capture_off_producer_exit": exits["off"],
            "capture_on_producer_exit": exits["on"],
            "reported_game_state_unchanged_by_dump_insertion": True,
            "retained_raw_files_independently_reopened":
                independently["verified_raw_files"],
            "digest_only_frames_not_reopened":
                independently["digest_only_equal_frames_not_independently_reopened"],
            "actual_unmasked_byte_differences":
                independently["verified_differing_byte_occurrences"],
            "original_result_frame": result["reference_relative"],
            "native_result_frame": result["native_relative"],
            "original_next_bowl": handoff["fresh_reference_next_bowl_entry_offset"],
            "native_next_bowl": handoff["fresh_native_next_bowl_entry_offset"],
            "original_native_sram_equal":
                handoff["all_original_native_full_sram_pairs_equal"],
            "guest_acknowledgment_log_bytes_reopened": False,
            "guest_cpu_controller_polls_proven": False,
            "actual_compiled_binaries_reopened": False,
            "accepted_USA_events": 0,
            "release_QA_gates": 0,
            "adjudication": "HOLD",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("Genuine Zoom Zoo A/B verified: capture stable; gameplay HOLD, 0/45")


if __name__ == "__main__":
    main()
