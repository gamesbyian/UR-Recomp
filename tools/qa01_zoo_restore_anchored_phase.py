#!/usr/bin/env python3
"""Replay the three source/native Zoo result-presentation transitions from one ZIP.

Uses the already executed, unchanged original Snes9x and Baldosa replay.
Anchors to observed guest WRAM and real zero-frame script dump receipts.
No controller rephase, ROM patch, guest write or complete-event admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

SOURCE_ZIP_SHA256 = "d5ec65c672736fa45f01214134db8598baa840f106729bd2c04ffb8949f1d039"
SOURCE_RUN = 38500427634
SOURCE_ARTIFACT = 11866136501
EVENTS = {
    "original": {"restore": 5158, "clear": 5162, "result_text": 5163},
    "native": {"restore": 5157, "clear": 5161, "result_text": 5162},
}
DIRS = {"original": "original-boundary", "native": "native-boundary/dump"}
HOST_LOGS = {"original": "original-boundary.log",
             "native": "native-boundary/log.txt"}
TRACE_LOGS = {"original": "original-pc.log", "native": "native-menu-writes.log"}
SOURCE_OPCODES = {
    "restore": "ZOOPCWRITE f=6760 v=240 pc=83988A addr=009F old=84 new=16",
    "restore_course": "ZOOPCWRITE f=6760 v=243 pc=83988A addr=00CE old=00 new=01",
    "clear": "ZOOPCWRITE f=6765 v=9 pc=838B85 addr=0313 old=01 new=00",
    "text_buffer": "ZOOPCWRITE f=6766 v=79 pc=80C585 addr=0313 old=00 new=3D",
    "result_text": "ZOOPCWRITE f=6766 v=139 pc=80C5B2 addr=009F old=BB new=BC",
}
NATIVE_STORES = {
    "restore": "f6762   80:009E=1600 w2 Sram_RestoreDirectPage_FastRom_M1X0",
    "restore_course": "f6762   80:00CE=0001 w2 Sram_RestoreDirectPage_FastRom_M1X0",
    "clear": "f6766   80:0312=004C w2 Vram_ClearRegions_M1X0",
    "text_buffer": "f6767   00:0312=3D0A w2 Text_DrawLoop_C3F7_M1X0",
    "result_text": "f6767   00:009F=00BC w2 Text_DrawLoop_C3F7_M1X0",
}
DUMP = re.compile(r"^script f=(\d+) dump ([\w-]+) (.+)$", re.MULTILINE)
ORIGINAL_RECEIPT = re.compile(r"fb=256x224 RGB565 sram=8192 ppuw=\d+(?: \(truncated\))?")
MAX_WRA = 131072


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(z: zipfile.ZipFile, name: str) -> bytes:
    members = z.NameToInfo
    if len([i for i in z.infolist() if i.filename == name]) != 1:
        raise ValueError("missing or duplicate genuine artifact member: " + name)
    info = z.getinfo(name)
    if (info.external_attr >> 16) & 0o170000 == 0o120000:
        raise ValueError("symlink artifact member forbidden: " + name)
    return z.read(name)


def receipts(log: str, side: str) -> tuple[int, dict[int, int]]:
    observations = {}
    for host, tag, descriptor in DUMP.findall(log):
        if side == "original":
            if ORIGINAL_RECEIPT.fullmatch(descriptor) is None:
                raise ValueError("invalid original snesref dump receipt")
        elif descriptor != "ok":
            raise ValueError("native dump was not complete: " + descriptor)
        observations.setdefault(tag, []).append(int(host))
    start = observations.get("scene-entered", [])
    if len(start) != 1 or start[0] <= 0:
        raise ValueError("original/native scene entry must be independently logged exactly once")
    entry = start[0]
    samples = {}
    for frame in range(5156, 5164):
        tag = f"boundary-{frame:05d}"
        hits = observations.get(tag, [])
        if len(hits) != 1 or hits[0] != entry + frame:
            raise ValueError("missing, duplicate or mistimed zero-frame script dump " + tag)
        samples[frame] = hits[0]
    return entry, samples


def unique_trace(trace: str, expected: str) -> None:
    if sum(line.strip() == expected for line in trace.splitlines()) != 1:
        raise ValueError("source/native executed writer witness missing or duplicated: " + expected)


def analyze(archive: Path, *, expected_sha256: str | None = SOURCE_ZIP_SHA256) -> dict:
    raw = archive.read_bytes()
    actual_zip_hash = sha(raw)
    if expected_sha256 is not None and actual_zip_hash != expected_sha256:
        raise ValueError("original/native artifact identity mismatch")
    with zipfile.ZipFile(archive) as z:
        states = {}
        entry = {}
        ticks = {}
        trace_hashes = {}
        for side in ("original", "native"):
            log = read(z, HOST_LOGS[side]).decode("utf-8")
            entry[side], ticks[side] = receipts(log, side)
            trace_raw = read(z, TRACE_LOGS[side])
            trace = trace_raw.decode("utf-8")
            trace_hashes[side] = sha(trace_raw)
            for label in (SOURCE_OPCODES if side == "original" else NATIVE_STORES).values():
                unique_trace(trace, label)
            states[side] = {}
            for relative in range(5156, 5164):
                tag = f"boundary-{relative:05d}.wram.bin"
                wram = read(z, f"{DIRS[side]}/{tag}")
                if len(wram) != MAX_WRA:
                    raise ValueError("incomplete original/native full-WRAM dump: " + tag)
                states[side][relative] = {
                    "menu": wram[0x009F], "track": wram[0x00CE],
                    "race_scratch": wram[0x0313],
                    "p1_laps": int.from_bytes(wram[0x0EF1:0x0EF3], "little"),
                    "p1_checkpoint": int.from_bytes(wram[0x1199:0x119B], "little"),
                    "p1_finish_gate": int.from_bytes(wram[0x119D:0x119F], "little"),
                    "wram_sha256": sha(wram),
                }
    transitions = {}
    for side, landmarks in EVENTS.items():
        state = states[side]
        restore, clear, result = (landmarks[k] for k in
                                  ("restore", "clear", "result_text"))
        before = state[restore - 1]
        if (before["menu"], before["track"], before["race_scratch"]) != (0x84, 0, 1):
            raise ValueError(side + " unqualified pre-restore original guest state")
        for f in range(restore, clear):
            if (state[f]["menu"], state[f]["track"], state[f]["race_scratch"]) != (0x16, 1, 1):
                raise ValueError(side + " changed between restored state and text-clear")
        if (state[clear]["menu"], state[clear]["track"], state[clear]["race_scratch"]) != (0x16, 1, 0):
            raise ValueError(side + " unqualified clear-buffer terminal boundary")
        if (state[result]["menu"], state[result]["track"], state[result]["race_scratch"]) != (0xBC, 1, 0x3D):
            raise ValueError(side + " unqualified genuine result-text boundary")
        for f in range(restore - 1, result + 1):
            fields = state[f]
            if (fields["p1_laps"], fields["p1_checkpoint"],
                    fields["p1_finish_gate"]) != (0, 1, 1):
                raise ValueError(side + " actual course progress changed")
        transitions[side] = {
            name: {
                "scene_relative_frame": frame,
                "actual_script_host_frame": ticks[side][frame],
                "guest_wram_sha256": state[frame]["wram_sha256"],
            }
            for name, frame in landmarks.items()
        }
    from_restore = {}
    absolute_native_minus_original = {}
    for name in ("restore", "clear", "result_text"):
        o = transitions["original"][name]["actual_script_host_frame"]
        n = transitions["native"][name]["actual_script_host_frame"]
        absolute_native_minus_original[name] = n - o
        from_restore[name] = {
            side: (transitions[side][name]["actual_script_host_frame"]
                   - transitions[side]["restore"]["actual_script_host_frame"])
            for side in ("original", "native")
        }
    equal_restore_to_result_cadence = (
        all(v["original"] == v["native"] for v in from_restore.values())
        and list(absolute_native_minus_original.values()) == [1, 1, 1]
    )
    # Deliberately refuse to call a retrospectively inferred coincidence an
    # execution parity pass. This is a bounded *presentation* scheduling test.
    return {
        "schema": "UR-QA01-ZOO-RESTORE-ANCHORED-EXECUTED-PRESENTATION/1",
        "executed_workflow": SOURCE_RUN,
        "original_native_artifact": SOURCE_ARTIFACT,
        "artifact_zip_sha256": actual_zip_hash,
        "artifact_identity_pinned": actual_zip_hash == SOURCE_ZIP_SHA256,
        "source_native_cpu_helper_log_sha256": trace_hashes,
        "independently_reported_scene_entry_host_frames": entry,
        "native_minus_original_entry_host_frames": entry["native"] - entry["original"],
        "original_native_stage_receipts": transitions,
        "native_minus_original_absolute_stage_host_frames": absolute_native_minus_original,
        "elapsed_host_frames_since_observed_restore": from_restore,
        "restoration_to_result_presentation_cadence_equal": equal_restore_to_result_cadence,
        "first_observed_guest_relative_stage_difference_precedes_restoration": (
            transitions["native"]["restore"]["scene_relative_frame"]
            != transitions["original"]["restore"]["scene_relative_frame"]),
        "distinct_original_icpu_and_native_prerun_frame_tags_not_equated": True,
        "source_and_native_genuine_result_both_observed": True,
        "source_native_continuous_instruction_parity_proven": False,
        "source_native_course_finish_decision_instant_proven": False,
        "complete_event_release_credit": 0,
        "next_causal_question": (
            "Why native scene entry is +2 host frames but native restore, clear "
            "and result drawing are +1 absolute host frame. Investigate the "
            "genuine course finish/return decision upstream of DP restoration "
            "and the source/native entry predicate; never globally retime pads."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifact", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--expected-sha256", default=SOURCE_ZIP_SHA256)
    args = ap.parse_args()
    data = analyze(args.artifact, expected_sha256=args.expected_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "restoration_to_result_presentation_cadence_equal":
            data["restoration_to_result_presentation_cadence_equal"],
        "native_minus_original_absolute_stage_host_frames":
            data["native_minus_original_absolute_stage_host_frames"],
        "complete_event_release_credit": data["complete_event_release_credit"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
