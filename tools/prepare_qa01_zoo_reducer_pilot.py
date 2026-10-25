#!/usr/bin/env python3
"""Private, fail-closed first Zoo +5039/+5040 replay reducer intake.

Consumes existing authentic QA01 producer bytes. Does not emulate, invent
source controller timing, publish ROM/movie/SRAM, or grant any release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from controller_input import load_controller_runs
from qa01_reducer_clock_rebase import paired_streams
from qa01_reducer_paired_oracle import ROM_USA_SHA256, checkpoint_only_observer
from reduce_controller_fixture import encode

SOURCE_MOVIE_SHA256 = "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"
SOURCE_SRAM_SHA256 = "a6af0ddf25ae5feafba301100938f5ef81137ee76dcdc483a04fb6e961347828"
HEX40 = re.compile(r"[a-f0-9]{40}\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
TAG = "scene-05040"
BEFORE = "scene-05039"
BINARY_SIZE = 0x20000


def require(condition, error):
    if not condition:
        raise ValueError(error)


def sha(path: Path):
    require(path.is_file() and not path.is_symlink(),
            "source-qualified input missing or redirected: " + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_tag_frame(log: Path, tag: str) -> int:
    rows = re.findall(r"\bscript f=(\d+) dump " + re.escape(tag) + r"(?:\s|$)",
                      log.read_text(encoding="utf-8"))
    require(len(rows) == 1, "missing or duplicate authentic guest dump " + tag)
    return int(rows[0])


def checkpoint(path: Path) -> bytes:
    require(path.is_file() and not path.is_symlink() and path.stat().st_size == BINARY_SIZE,
            "missing original 128 KiB source checkpoint " + str(path))
    return path.read_bytes()


def prepare(*, producer: Path, case: Path, binaries: Path, rom: Path, movie: Path,
            source_sha: str, expected_movie_sha: str = SOURCE_MOVIE_SHA256,
            expected_sram_sha: str = SOURCE_SRAM_SHA256) -> tuple[bytes, dict, dict]:
    require(bool(HEX40.fullmatch(source_sha)), "source commit must be exact SHA")
    report = json.loads(producer.read_text(encoding="utf-8"))
    require(report.get("name") == "zoom-zoo" and report.get("course_id") == "course:02"
            and report.get("native_backend") == "pinned-baldosa",
            "not the authentic first-party pinned Zoo producer")
    control = report.get("qa01_capture_ab_control")
    require(type(control) is dict and control.get("repository_source_sha") == source_sha,
            "producer source commit differs from actual checked-out source")
    require(report.get("admission", "").startswith("investigative candidate"),
            "producer did not retain source-only QA credit boundary")
    require(sha(rom) == ROM_USA_SHA256 == report.get("rom_sha256"),
            "wrong original retail ROM")
    require(sha(movie) == expected_movie_sha == report.get("original_movie_sha256"),
            "different original 2014 movie")
    seed = case / "anchored.srm"
    require(seed.is_file() and seed.stat().st_size == 8192
            and sha(seed) == expected_sram_sha == report.get("source_sram_sha256"),
            "original movie 8192-byte source SRAM missing/changed")
    executable = binaries / "native"
    snesref = binaries / "snesref"
    core = binaries / "snes9x_libretro.so"
    require(sha(executable) == report.get("native_executable_sha256")
            and sha(core) == report.get("reference_core_sha256"),
            "producer binaries do not match source report")
    source_executable_hash = sha(snesref)
    replay = case / "replay"
    observer = replay / "complete.script"
    reference_input = replay / "ref.input"
    native_input = replay / "pinned-baldosa.input"
    script_hash = sha(observer)
    require(script_hash == report.get("reference_script_sha256")
            == control.get("reference_script_sha256")
            == control.get("native_script_sha256"),
            "original/native observation script identity differs")
    require(observer.read_text(encoding="utf-8").splitlines().count("dump " + TAG) == 1,
            "source observer must include one selected post-Zoo sound dump")
    require(sha(reference_input) == control.get("reference_supplied_input_sha256")
            and sha(native_input) == control.get("native_supplied_input_sha256"),
            "real original/native guest inputs changed after producer")
    runs = load_controller_runs(reference_input)
    native_runs = load_controller_runs(native_input)
    rf, nf = report.get("reference_entry"), report.get("native_entry")
    require(type(rf) is int and type(nf) is int and 0 < rf < 200000 and 0 < nf < 200000
            and nf - rf == report.get("native_frame_shift"),
            "unqualified original/native race entry clocks")
    original_bytes, native_bytes = paired_streams(runs, rf, nf)
    require(encode(native_runs) == native_bytes,
            "native supplied input is not source-authentic host-shifted stream")
    reference_log = replay / "reference.log"
    native_log = replay / "native.log"
    require(sha(reference_log) == control.get("reference_guest_log_sha256")
            and sha(native_log) == control.get("native_guest_log_sha256"),
            "actual source-guest logs are not producer-bound")
    require(exact_tag_frame(reference_log, "race-entered") == rf
            and exact_tag_frame(native_log, "race-entered") == nf,
            "original/native entry not corroborated by executable log")
    rf_obs = exact_tag_frame(reference_log, TAG)
    nf_obs = exact_tag_frame(native_log, TAG)
    require(rf_obs - rf == nf_obs - nf == 5040,
            "original/native observation differs from source-earned Zoo +5040 phase")
    before_ref = checkpoint(replay / "ref" / (BEFORE + ".wram.bin"))
    before_native = checkpoint(replay / "native" / (BEFORE + ".wram.bin"))
    after_ref = checkpoint(replay / "ref" / (TAG + ".wram.bin"))
    after_native = checkpoint(replay / "native" / (TAG + ".wram.bin"))
    require(before_ref == before_native, "source +5039 was not full-byte identical")
    offsets = [i for i, (a, b) in enumerate(zip(after_ref, after_native)) if a != b]
    require(offsets == [0x63, 0x69],
            "current source has a different +5040 first-sound discrepancy: stop and requalify")
    require(after_ref[0x00CE] == after_native[0x00CE] == 1
            and after_ref[0x0313] == after_native[0x0313] == 1,
            "source no longer reaches true Zoo active race")
    anchors = [{"offset": offset, "value": after_ref[offset]}
               for offset in (0x009F, 0x00CE, 0x0313)]
    manifest = {
        "schema": "ur-qa01-reducer-paired-commands/1",
        "source_sha": source_sha,
        "reference_engine": "Snes9x-libretro-firstparty-2014-source-Zoo",
        "rom": {"path": str(rom.resolve()), "sha256": ROM_USA_SHA256},
        "source_sram": {"path": str(seed.resolve()), "sha256": expected_sram_sha},
        "reference_binary": {"path": str(snesref.resolve()), "sha256": source_executable_hash},
        "reference_core": {"path": str(core.resolve()), "sha256": sha(core)},
        "native_binary": {"path": str(executable.resolve()), "sha256": sha(executable)},
        "observation_script": {"path": str(observer.resolve()), "sha256": script_hash},
        "pre_target": {"dump": BEFORE + ".wram.bin",
                       "sha256": hashlib.sha256(before_ref).hexdigest()},
        "after_target_pair": [
            {"offset": offset, "original_byte": after_ref[offset],
             "native_byte": after_native[offset]}
            for offset in (0x63, 0x69)
        ],
        "native_xvfb": True,
        "guest_clocks": {
            "reference_entry_frame": rf, "native_entry_frame": nf,
            "reference_observation_frame": rf_obs, "native_observation_frame": nf_obs,
        },
        "reference": {
            "argv": [str(snesref.resolve()), "%CORE%", "%ROM%"],
            "environment": {
                "SNESREF_HEADLESS": "1", "SNESREF_WRAM_FILL": "0",
                "SNESREF_INPUT_FILE": "%CANDIDATE%", "SNESREF_SRAM_IN": "%SRAM%",
                "SNESREF_DUMP_DIR": "%DUMP_DIR%", "SNESREF_SCRIPT": "%OBSERVER%",
            },
            "dump": TAG + ".wram.bin",
        },
        "native": {
            "argv": [str(executable.resolve()), "--no-launcher", "--config",
                     "%CONFIG%", "--script", "%OBSERVER%", "%ROM%"],
            "environment": {
                "SDL_AUDIODRIVER": "dummy", "SNESRECOMP_FRAMEDUMP_PIXELS": "0",
                "SNESRECOMP_DUMP_DIR": "%DUMP_DIR%",
                "SNESRECOMP_ROM": "%ROM%",
                "UR_QA_SCENE_INPUT_FILE": "%CANDIDATE%",
            },
            "dump": TAG + ".wram.bin",
        },
        "discrepancy": {
            "id": "original-zoo-first-sound-dp-0063-after-byte-identical-5039",
            "phase": "source-Zoo-race-guest-relative+5040-postscript-dump",
            "offset": 0x63, "original_byte": after_ref[0x63],
            "native_byte": after_native[0x63],
        },
        "anchors": anchors,
    }
    receipt = {
        "schema": "ur-qa01-source-zoo-reducer-intake/1",
        "source_sha": source_sha,
        "movie_sha256": expected_movie_sha,
        "historical_sram_sha256": expected_sram_sha,
        "original_supplied_input_sha256": sha(reference_input),
        "native_supplied_input_sha256": sha(native_input),
        "normalized_reducer_input_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "original_before_wram_sha256": hashlib.sha256(before_ref).hexdigest(),
        "native_before_wram_sha256": hashlib.sha256(before_native).hexdigest(),
        "original_after_wram_sha256": hashlib.sha256(after_ref).hexdigest(),
        "native_after_wram_sha256": hashlib.sha256(after_native).hexdigest(),
        "original_and_native_equal_before": True,
        "current_first_sound_mismatch_offsets": offsets,
        "guest_relative_discrepancy": 5040, "release_gate_credit": 0,
    }
    return original_bytes, manifest, receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("producer", "case", "binaries", "rom", "movie",
                "output-manifest", "output-input", "output-receipt"):
        p.add_argument("--" + key, type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    args = p.parse_args()
    destinations = (args.output_manifest.resolve(), args.output_input.resolve(),
                    args.output_receipt.resolve())
    require(len(set(destinations)) == 3 and all(not path.exists() for path in destinations),
            "output must use three new private paths")
    data, manifest, receipt = prepare(producer=args.producer, case=args.case,
        binaries=args.binaries, rom=args.rom, movie=args.movie, source_sha=args.source_sha)
    for path in destinations:
        path.parent.mkdir(parents=True, exist_ok=True)
    # The full source observer remains SHA-bound. Reducer predicates end at
    # +5040, so executing the later 9000-frame result-screen gate only turns
    # wrong-route candidates into expensive unrelated native/Xvfb timeouts.
    bounded_path = destinations[0].parent / "qa01-zoo-through-05040.script"
    require(not bounded_path.exists() and bounded_path not in destinations,
            "checkpoint-only observer must be a new private path")
    source = Path(manifest["observation_script"]["path"])
    script = checkpoint_only_observer(source.read_text(encoding="utf-8"), TAG)
    bounded_path.write_text(script, encoding="utf-8")
    manifest["bounded_observer_script"] = {
        "path": str(bounded_path),
        "sha256": hashlib.sha256(script.encode("utf-8")).hexdigest(),
    }
    destinations[0].write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    destinations[1].write_bytes(data)
    destinations[2].write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
