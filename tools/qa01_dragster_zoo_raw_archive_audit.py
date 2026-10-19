#!/usr/bin/env python3
"""Independent, read-only Dragster->Zoo primary guest-memory archive audit.

The authoring producer is not imported. Every retained WRAM/SRAM byte is
reopened; a genuine strict negative is evidence, not an artifact failure.
This is not a guest emulator, a clock rephaser, or USA event acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from qa01_bowl_handoff_raw_archive_audit import (
    digest, read_exact, read_logged_frame, raw_wram_pair,
)

SCHEMA = "UR-QA01-INDEPENDENT-DRAGSTER-ZOO-RAW-ARCHIVE/1"
PRODUCER_SCHEMA = "UR-QA01-DRAGSTER-TO-ZOO-FRESH-GUEST-PROGRESSION/1"
OFFSETS = (304, 308, 312, 314, 315, 316, 317, 318, 319, 320, 321, 324, 328, 336)
MOVIE_RESULT, MOVIE_ZOO = 2874, 3190
# Exact original 2014 USA ROM, movie, seed and controller route, independent
# of which separately qualified and actually manifested Snes9x core rebuilt
# for an immutable Actions run. Native/2014 binary *bytes* are not in ZIP.
FROZEN_SOURCE = {
    "rom_sha256": "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
    "original_movie_sha256": "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442",
    "source_sram_sha256": "a6af0ddf25ae5feafba301100938f5ef81137ee76dcdc483a04fb6e961347828",
    "input_sha256": "6bc10df3649717482c96edd1d72c52c62f5f53baeb1a2b142c725fca0d864905",
    "original_movie_window_sha256": "aec7f8850085d662656117303f9daa802e737aca2d12b8af89962acbb206d1c1",
}
# Each value was independently recomputed from the manifest + producer in an
# actual original 2014 USA Dragster Actions ZIP, NOT guessed from a new build:
# 69-member 12154480620 (f754...), 205-member 12155314437 (9310...),
# 206-member 12156438655 (1e36...). Future cores must be separately verified.
QUALIFIED_ORIGINAL_CORES = frozenset({
    "f7548718783409c2636374d0a68c21671e5ea214bcb9d11780c4622e80d96fe0",
    "931094b5772ce832f832809728e4b42f92799109ca62991d44c8f953d4640f31",
    "1e36493285da04109d67d194ba68116f9d3222d3b0866b080a8b12bce87ce683",
})
QUALIFIED_SNESREF_SHA256 = "5fb3cca1f51d13762e7b82e736133cdab702aafbca07b9164d568139a3bcc18a"
QUALIFIED_NATIVE_SHA256 = "439ac76fa8d90f141436dc25426e522561667cb3aa575d5c326a06afc6cb5ba8"
MANIFEST_PATHS = {
    "snesref": "/home/runner/work/_temp/dragster-snesref/snesref",
    "core": "/home/runner/work/UR-Recomp/UR-Recomp/.tools/src/snes9x-libretro/libretro/snes9x_libretro.so",
    "native": "/home/runner/work/UR-Recomp/UR-Recomp/baldosa/build/UniracersSNESRecomp",
}
MANIFEST_LINE = re.compile(r"([0-9a-f]{64})  (/home/runner/work/[^\r\n]+)\Z")
FROZEN_MOVIE_TRACE = "3de122406937fcf839988d7990972e9275b8e7bbd47db1b958fea20113c27c54"
NAME_ADDR = {"menu": 0x9F, "track": 0xCE, "in_race": 0x313, "tour_row": 0xD0}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def verify_executed_binary_manifest(root: Path, report: dict) -> dict:
    """Check the exact retained original build manifest with known real cores.

    These entries are SHA receipts from the original executed build, NOT
    rehashed PE/ELF/source binaries (which this ZIP does not include).
    """
    path = root / "executables.sha256"
    require(path.is_file() and not path.is_symlink(),
            "missing exact source-execution binary SHA256 manifest")
    raw = path.read_bytes()
    require(raw.endswith(b"\n") and len(raw) <= 768 and
            raw.count(b"\n") == 3,
            "source-execution manifest has wrong row population")
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("non-ASCII source-execution manifest") from exc
    entries = {}
    for line in lines:
        match = MANIFEST_LINE.fullmatch(line)
        require(match is not None, "malformed source-execution SHA256 manifest row")
        sha, fullpath = match.groups()
        candidates = [key for key, exact_path in MANIFEST_PATHS.items()
                      if fullpath == exact_path]
        require(len(candidates) == 1 and candidates[0] not in entries,
                "untrusted or duplicated source-execution binary manifest name")
        entries[candidates[0]] = sha
    require(set(entries) == set(MANIFEST_PATHS),
            "source-execution manifest omits original or native binary")
    require(report.get("reference_core_sha256") in QUALIFIED_ORIGINAL_CORES,
            "unknown original Snes9x binary not independently source-qualified")
    require(entries["core"] == report["reference_core_sha256"] and
            entries["snesref"] == QUALIFIED_SNESREF_SHA256 and
            entries["native"] == report.get("native_executable_sha256") ==
                QUALIFIED_NATIVE_SHA256,
            "original/native executed producer binary hashes contradict source manifest")
    return {
        "original_core_sha256": entries["core"],
        "source_snesref_sha256": entries["snesref"],
        "native_executable_sha256": entries["native"],
        "source_execution_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "original_core_on_independently_verified_archive_allowlist": True,
        "compiled_binaries_physically_in_case_zip": False,
    }


def real_dragster_record(sram: bytes) -> tuple[list[dict], bool]:
    require(len(sram) == 8192, "not a complete 8KiB SRAM image")
    word = lambda at: int.from_bytes(sram[at:at + 2], "little")
    ranks = [
        {"rank": rank, "value_word": word(0x422 + 100 * rank),
         "holder_index": sram[0x550 + 50 * rank]}
        for rank in range(3)
    ]
    return ranks, word(0x54E) == sum(word(0x422 + 2 * i) for i in range(150)) & 0xFFFF


def active_zoo(row: dict) -> bool:
    return all(type(row.get(k)) is int for k in ("track", "in_race", "tour_row")) and (
        row["track"], row["in_race"], row["tour_row"]) == (1, 1, 0)


def entry_bracket(samples: list[dict], side: str) -> dict:
    previous = None
    for row in samples:
        off = row["offset"]
        state = row["movie"] if side == "movie" else row[side]
        on = active_zoo(state)
        if on:
            return {
                "first_observed_active_offset": off,
                "last_observed_inactive_offset":
                    previous[0] if previous is not None and not previous[1] else None,
                "exact_adjacent_onset_offset":
                    off if previous is not None and previous == (off - 1, False) else None,
            }
        previous = (off, on)
    return {"first_observed_active_offset": None,
            "last_observed_inactive_offset":
                previous[0] if previous is not None and not previous[1] else None,
            "exact_adjacent_onset_offset": None}


def sha_file(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(), "missing original source trace")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()



def movie_states_from_actual_trace(path: Path) -> dict[int, dict]:
    """Replay original WRAM writes for the complete result→Zoo source window.

    Frame counters in this archived original write trace are the source's
    own `f` domain. They must not be equated to fresh guest frame clocks.
    This is not a second original emulator or a fabricated original image.
    """
    require(path.is_file() and not path.is_symlink(),
            "missing genuine 2014 source memory-write trace")
    start, finish = MOVIE_RESULT, MOVIE_RESULT + max(OFFSETS)
    wanted = range(start, finish + 1)
    values = {at: 0 for at in NAME_ADDR.values()}
    matched = {
        b'"adr":"0x0009f"': 0x9F,
        b'"adr":"0x000ce"': 0xCE,
        b'"adr":"0x00313"': 0x313,
        b'"adr":"0x000d0"': 0xD0,
    }
    out: dict[int, dict] = {}
    frame = None

    def hold(stop: int) -> None:
        if frame is None:
            return
        for n in wanted:
            if frame <= n < stop and n not in out:
                out[n] = {k: values[address] for k, address in NAME_ADDR.items()}

    with path.open("rb") as stream:
        for line in stream:
            match = next((addr for needle, addr in matched.items() if needle in line), None)
            if match is None:
                continue
            row = json.loads(line)
            f = row["f"]
            require(type(f) is int and f >= 1 and
                    (frame is None or f >= frame),
                    "source movie trace frame order not monotonic")
            if frame is not None and f > frame:
                hold(f)
            frame = f
            require(int(row["adr"], 16) == match,
                    "source trace writer address mismatched")
            values[match] = int(row["val"], 16)
    require(frame is not None and frame >= finish,
            "original source trace ends before eight active Zoo frames")
    hold(finish + 1)
    require(len(out) == len(wanted),
            "gaps in original 2014 source frame-state reconstruction")
    return out


def verify_source_movie(source: dict, trace: dict[int, dict]) -> None:
    require(trace[MOVIE_RESULT]["menu"] == 0x99 and
            trace[2935]["track"] == 1 and trace[2935]["in_race"] == 0,
            "historical Dragster result or Zoo selection false")
    require(not active_zoo(trace[MOVIE_ZOO - 1]) and
            all(active_zoo(trace[f]) for f in range(MOVIE_ZOO, MOVIE_ZOO + 8)),
            "original movie does not actually enter eight consecutive Zoo frames")
    for f in range(MOVIE_RESULT + 1, MOVIE_ZOO):
        if active_zoo(trace[f]) and all(
                active_zoo(trace.get(f + k, {})) for k in range(8)):
            require(False, "earlier source Zoo active race omitted")
    for offset in OFFSETS:
        row = source["source_samples"][str(offset)]
        movie_frame = MOVIE_RESULT + offset
        require(row.get("original_movie_host_frame") == movie_frame and
                all(row.get(k) == trace[movie_frame][k] for k in NAME_ADDR),
                "producer historical movie state contradicts real WRAM source trace")


def audit(root: Path) -> dict:
    report_path = root / "dragster-report.json"
    proof_path = root / "dragster/source/dragster-next-zoo-original.json"
    require(report_path.is_file() and proof_path.is_file() and
            not report_path.is_symlink() and not proof_path.is_symlink(),
            "original executed source/guest report not retained")
    report = json.loads(report_path.read_bytes())
    proof = json.loads(proof_path.read_bytes())
    require(isinstance(report, dict) and report.get("course_id") == "course:01" and
            report.get("name") == "dragster" and report.get("family") == "race-a" and
            report.get("native_backend") == "pinned-baldosa" and
            report.get("admission") == "investigative candidate; not a release-ledger pass",
            "unqualified original/native USA Dragster report")
    require(all(report.get(key) == value for key, value in FROZEN_SOURCE.items()) and
            report.get("reference_script_sha256") == FROZEN_SOURCE["input_sha256"],
            "actual 2014 USA ROM/movie/core/seed/controller identity not source-pinned")
    build = verify_executed_binary_manifest(root, report)
    event = report.get("original_source_event")
    require(isinstance(event, dict) and event.get("original_entry_frame") == 794 and
            event.get("original_result_frame") == MOVIE_RESULT and
            event.get("source_active_frames_to_result") == 2080 and
            event.get("source_next_zoo") == proof,
            "original USA Dragster→Zoo source movie event not authenticated")
    require(isinstance(proof, dict) and proof.get("schema") == PRODUCER_SCHEMA and
            proof.get("original_dragster_entry_host_frame") == 794 and
            proof.get("original_dragster_result_host_frame") == MOVIE_RESULT and
            proof.get("original_zoo_active_entry_host_frame") == MOVIE_ZOO and
            proof.get("source_dragster_result_to_zoo_active_frames") == 316 and
            proof.get("original_zoo_eight_consecutive_active_frames") is True and
            proof.get("original_movie_controller_masks_modified") is False and
            proof.get("release_complete_usa_event_credit") == 0 and
            proof.get("sample_offsets") == list(OFFSETS) and
            set(proof.get("source_samples", {})) == set(map(str, OFFSETS)),
            "historical source selected Zoo but did not establish active race")
    trace_sha = proof.get("original_source_trace_sha256")
    require(trace_sha == FROZEN_MOVIE_TRACE and
            trace_sha == sha_file(root / "dragster/source/trace.jsonl"),
            "original 2014 source raw trace digest differs from pinned original")
    movie_trace_states = movie_states_from_actual_trace(root / "dragster/source/trace.jsonl")
    verify_source_movie(proof, movie_trace_states)
    result = report.get("comparison")
    require(isinstance(result, dict) and result.get("paired_event_candidate") is False and
            result.get("terminal_result_frame_matched") is False and
            result.get("bounded_dragster_to_zoo_diagnostic_without_full_event_parity") is True,
            "strict Dragster result difference missing or falsely promoted")
    clock = result.get("terminal_result_guest_frame")
    require(isinstance(clock, dict) and
            all(type(clock.get(k)) is int and clock[k] > 0
                for k in ("reference_relative", "native_relative")) and
            type(report.get("reference_entry")) is int and
            type(report.get("native_entry")) is int and
            report.get("native_frame_shift") ==
                report["native_entry"] - report["reference_entry"],
            "fresh original/native result and entry clocks not independently qualified")
    handoff = report.get("dragster_next_zoo_handoff")
    require(isinstance(handoff, dict) and handoff.get("schema") == PRODUCER_SCHEMA and
            handoff.get("original_movie_dragster_result_frame") == MOVIE_RESULT and
            handoff.get("original_movie_zoo_entry_frame") == MOVIE_ZOO and
            handoff.get("original_movie_zoo_entry_relative_to_dragster_result") == 316 and
            handoff.get("release_complete_usa_event_credit") == 0 and
            handoff.get("source_controller_masks_rephased") is False and
            handoff.get("original_native_complete_dragster_cpu_spc_frame_parity_proven") is False and
            handoff.get("original_native_complete_zoo_event_proven") is False and
            handoff.get("cold_host_disk_persistence_proven") is False and
            handoff.get("shipping_windows_source_identity_proven") is False and
            isinstance(handoff.get("samples"), list) and
            len(handoff["samples"]) == len(OFFSETS),
            "invalid or over-promotional fresh Dragster guest handoff")
    directory = root / "dragster/replay"
    logs = {}
    for side, filename in (("original", "reference.log"), ("native", "native.log")):
        path = directory / filename
        require(path.is_file() and not path.is_symlink(), "missing real guest replay log")
        logs[side] = path.read_text(encoding="utf8", errors="replace")

    observed, differences, sram_offsets = [], [], set()
    earned_records_valid = []
    reported_course_payloads = {"original": [], "native": []}
    for offset, row in zip(OFFSETS, handoff["samples"]):
        require(isinstance(row, dict) and
                row.get("offset_from_respective_dragster_result") == offset and
                row.get("source_original") == proof["source_samples"][str(offset)],
                "misordered or false historical 2014 source frame")
        source = row["source_original"]
        require(source.get("original_movie_host_frame") == MOVIE_RESULT + offset,
                "original source trace host frame rephased")
        guests = row.get("fresh_guests")
        require(isinstance(guests, dict) and set(guests) == {"original", "native"},
                "missing original/native fresh guest")
        raw = {}
        named = {}
        for side, folder, clock_name, entry_key in (
                ("original", "ref", "reference_relative", "reference_entry"),
                ("native", "native", "native_relative", "native_entry")):
            g = guests[side]
            host = report[entry_key] + clock[clock_name] + offset
            tag = f"dragster-next-zoo-{offset:03d}"
            require(read_logged_frame(logs[side], tag) == host and
                    g.get("host_frame") == host,
                    "original/native executed dump host clock contradicts report")
            path = directory / folder
            w = read_exact(path / (tag + ".wram.bin"), 131072)
            s = read_exact(path / (tag + ".sram.bin"), 8192)
            ranks, good = real_dragster_record(s)
            earned_records_valid.append(good and
                                        ranks[0]["rank"] == 0 and
                                        ranks[0]["value_word"] == 2508 and
                                        ranks[0]["holder_index"] == 0)
            state = {k: w[addr] for k, addr in NAME_ADDR.items()}
            reported_course_payloads[side].append(
                active_zoo(state) and g.get("true_source_zoo_payload_loaded") is True)
            require(g.get("full_wram_bytes") == len(w) and
                    g.get("full_wram_sha256") == digest(w) and
                    g.get("full_sram_bytes") == len(s) and
                    g.get("full_sram_sha256") == digest(s) and
                    all(g.get(k) == v for k, v in state.items()) and
                    g.get("dragster_record_three_ranks") == ranks and
                    g.get("ranked_records_checksum_valid") is good and
                    type(g.get("true_source_zoo_payload_loaded")) is bool,
                    "real guest raw memory, ranked record or source state contradicted")
            named[side], raw[side] = state, (w, s)
        delta = [key for key in NAME_ADDR
                 if named["original"][key] != source[key] or
                 named["native"][key] != source[key]]
        require(row.get("source_to_fresh_named_disagreements") == delta,
                "fresh source/guest named divergence concealed")
        diff = raw_wram_pair(raw["original"][0], raw["native"][0])
        require(row.get("unmasked_full_original_native_wram_difference") == diff,
                "original/native full-WRAM byte claims contradict retained guest bytes")
        sdiff = [i for i, (a, b) in enumerate(zip(raw["original"][1], raw["native"][1]))
                 if a != b]
        require(row.get("full_original_native_sram_pair_equal") is (not bool(sdiff)),
                "original/native full 8KiB SRAM equality contradicted")
        sram_offsets.update(sdiff)
        observed.append({"offset": offset, "movie": source,
                         "original": named["original"], "native": named["native"]})
        differences.append({"offset": offset, "unmasked_wram_differing_bytes":
                            diff["differing_byte_count"], "sram_differing_bytes": len(sdiff)})

    brackets = {name: entry_bracket(observed, name)
                for name in ("movie", "original", "native")}
    require(brackets["movie"]["exact_adjacent_onset_offset"] == 316 and
            handoff.get("entry_brackets") == brackets and
            handoff.get("all_three_guest_result_relative_entry_offsets_equal") is
                all(brackets[k]["exact_adjacent_onset_offset"] == 316
                    for k in ("original", "native")) and
            handoff.get("fresh_original_absolute_zoo_onset_host") ==
                (report["reference_entry"] + clock["reference_relative"] +
                 brackets["original"]["exact_adjacent_onset_offset"]
                 if brackets["original"]["exact_adjacent_onset_offset"] is not None else None) and
            handoff.get("fresh_native_absolute_zoo_onset_host") ==
                (report["native_entry"] + clock["native_relative"] +
                 brackets["native"]["exact_adjacent_onset_offset"]
                 if brackets["native"]["exact_adjacent_onset_offset"] is not None else None) and
            handoff.get("first_source_or_guest_named_mismatch_offset") ==
                next((o["offset"] for o in observed
                      if any(o[side][key] != o["movie"][key] for key in NAME_ADDR
                             for side in ("original", "native"))), None) and
            handoff.get("all_full_sram_pairs_equal") is
                all(item["sram_differing_bytes"] == 0 for item in differences) and
            handoff.get("full_wram_difference_offsets") ==
                [x["offset"] for x in differences if x["unmasked_wram_differing_bytes"]] and
            handoff.get("original_native_ranked_checksum_valid_all_samples") is
                all(earned_records_valid) and
            handoff.get("fresh_original_loaded_true_zoo_course_while_active") is
                any(reported_course_payloads["original"]) and
            handoff.get("fresh_native_loaded_true_zoo_course_while_active") is
                any(reported_course_payloads["native"]),
            "raw three-clock entry/bracket, score or course-payload claim disagrees with receipt")

    return {"schema": SCHEMA, "producer_sha256": digest(report_path.read_bytes()),
            "actual_source_executable_manifest": build,
            "historical_source_trace_sha256": trace_sha,
            "full_source_result_to_zoo_raw_trace_movie_frames_rebuilt": len(movie_trace_states),
            "source_2014_8_consecutive_zoo_active_frames_rederived": True,
            "all_14_pairs_rehashed_from_actual_guest_bytes": True,
            "paired_wram_byte_occurrences": sum(x["unmasked_wram_differing_bytes"] for x in differences),
            "paired_sram_byte_occurrences": sum(x["sram_differing_bytes"] for x in differences),
            "unique_persistent_sram_difference_offsets": sorted(sram_offsets),
            "per_offset": differences, "guest_entry_brackets": brackets,
            "source_movie_raw_sram_wram_bytes_in_archive": False,
            "earned_rank0_2508_and_full_checksum_recomputed_for_28_images":
                all(earned_records_valid),
            "guest_course_payload_only_qualified_from_producer_boolean": True,
            "authentic_course_payload_independently_rehashed": False,
            "actual_cpu_spc_or_consumed_input_parity_proven": False,
            "shipping_windows_elf_or_durable_disk_proven": False,
            "independent_usa_event_adjudication": "HOLD",
            "accepted_usa_events": 0}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    try:
        result = audit(args.archive_root)
    except (OSError, TypeError, KeyError, ValueError, json.JSONDecodeError) as exc:
        p.exit(2, "QA01_DRAGSTER_RAW_ARCHIVE_INVALID: " + str(exc) + "\n")
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
