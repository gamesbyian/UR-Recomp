#!/usr/bin/env python3
"""Diagnostic native RF062 sound trace ON/OFF, exactly one unchanged binary.

Do not mistake a successful source/movie/supplied-control check for proven
CPU joypad consumption or guest timing parity. Always retain differences.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

SCHEMA = "ur-qa01-rf062-same-executable-logging-ab/1"
IMMUTABLE = ("rom_sha256", "original_movie_sha256",
             "original_movie_window_sha256", "input_sha256",
             "native_executable_sha256")
COMPARE = ("addr", "A", "Y", "D", "dp63", "dp64", "dp65")


def must(value: bool, why: str) -> None:
    if not value:
        raise ValueError(why)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def events(log: bytes, prefix: str) -> list[dict[str, str]]:
    entries = []
    for line in log.decode("utf8").splitlines():
        if not line.startswith(prefix):
            continue
        fields = [token.split("=", 1) for token in line.split()[1:] if "=" in token]
        row = dict(fields)
        must(len(fields) == len(row), "duplicated guest record field")
        entries.append(row)
    return entries


def control(off: dict, on: dict, off_logs: dict[str, bytes],
            on_logs: dict[str, bytes], off_inputs: dict[str, bytes],
            on_inputs: dict[str, bytes]) -> dict:
    for k in IMMUTABLE:
        must(type(off.get(k)) is str and off[k] == on.get(k),
             "different actual source/guest identity: " + k)
    must(set(off_logs) == set(on_logs) == {"original", "native"} and
         set(off_inputs) == set(on_inputs) == {"original", "native"},
         "missing original/native comparison population")
    for guest in ("original", "native"):
        must(off_inputs[guest] and
             off_inputs[guest] == on_inputs[guest],
             "actual supplied " + guest + " controller input changed")
    must("QA01RF054NATIVEBUS_TRUNCATED" not in off_logs["native"].decode("utf8") and
         "QA01RF054NATIVEBUS_TRUNCATED" not in on_logs["native"].decode("utf8") and
         "QA01RF062NATIVE_TRUNCATED" not in on_logs["native"].decode("utf8"),
         "actual guest observer trace overflow")
    absent = events(off_logs["native"], "QA01RF062NATIVE ")
    present = events(on_logs["native"], "QA01RF062NATIVE ")
    must(not absent and len(present) == 10 and
         [int(x["seq"]) for x in present] == list(range(1, 11)) and
         all(x["executedPC"] == "8282F0" and x["f"] == "6124"
             and x["addr"] == f"11{0xC770+i:04X}"
             for i, x in enumerate(present)) and
         present[4]["value"] == "D0",
         "native RF062 actual on/off observation control not qualified")
    off_bus = events(off_logs["native"], "QA01RF054NATIVEBUS ")
    on_bus = events(on_logs["native"], "QA01RF054NATIVEBUS ")
    for name, rows in (("off", off_bus), ("on", on_bus)):
        must(bool(rows) and
             [int(x["seq"]) for x in rows] == list(range(1, len(rows)+1)) and
             all(x["scope"] == "Snd_UploadBlockList_82EF_M1X0" and
                 x["frame"] == "6124" and x["kind"] == "read8" for x in rows),
             "actual RF054 native helper trace invalid: " + name)
    a = [tuple(x[k] for k in COMPARE) for x in off_bus]
    b = [tuple(x[k] for k in COMPARE) for x in on_bus]
    changes = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    matches = sum(j-i for tag,i,j,k,l in changes if tag == "equal")
    edits = [{"kind":tag, "off_range":[i,j], "on_range":[k,l],
              "off_first":off_bus[i]["addr"] if i<j else None,
              "on_first":on_bus[k]["addr"] if k<l else None}
             for tag,i,j,k,l in changes if tag != "equal"]
    same_operand = len(a) == len(b) == matches
    same_cpu_clock = same_operand and all(
        x["master"] == y["master"] for x,y in zip(off_bus,on_bus))
    same_outputs = all(off.get(k) == on.get(k) for k in
                       ("zoo_race_mesh", "source_terminal_followthrough",
                        "zoo_next_bowl_handoff"))
    return {
        "schema": SCHEMA, "source_identity_matches": True,
        "same_binaries": True,
        "actual_supplied_input_sha256": {
            guest: sha(off_inputs[guest]) for guest in ("original", "native")},
        "original_log_sha256_off_on": [sha(off_logs["original"]),
                                       sha(on_logs["original"])],
        "native_log_sha256_off_on": [sha(off_logs["native"]),
                                     sha(on_logs["native"])],
        "original_complete_log_byte_identical": (
            off_logs["original"] == on_logs["original"]),
        "rf062_actual_native_read_count_off_on": [len(absent),len(present)],
        "native_real_sound_helper_count_off_on": [len(a),len(b)],
        "native_sound_helper_matching_ordered_observations": matches,
        "native_sound_helper_edit_blocks": edits,
        "native_actual_RF054_address_and_register_rows_equal": same_operand,
        "native_actual_RF054_CPU_master_clocks_equal": same_cpu_clock,
        "original_native_whole_mesh_and_followthrough_equal": same_outputs,
        "runtime_RF062_logging_noninterference_supported": (
            same_operand and same_cpu_clock and same_outputs),
        "wrapper_replacement_noninterference_proven": False,
        "original_native_opcode_clock_equivalence_proven": False,
        "actual_CPU_joypad_poll_equivalence_proven": False,
        "USA_events_accepted": 0,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--off", type=Path, required=True)
    p.add_argument("--on", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    def collect(path: Path):
        report = json.loads((path/"producer-report.json").read_text())
        logs = {guest:(path/"work/zoom-zoo/replay"/name).read_bytes()
                for guest,name in (("original","reference.log"),
                                   ("native","native.log"))}
        inp = {guest:(path/"work/zoom-zoo/replay"/name).read_bytes()
               for guest,name in (("original","ref.input"),
                                  ("native","pinned-baldosa.input"))}
        return report,logs,inp
    off,off_logs,off_input=collect(args.off)
    on,on_logs,on_input=collect(args.on)
    result=control(off,on,off_logs,on_logs,off_input,on_input)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(result["schema"],"read probes",result["rf062_actual_native_read_count_off_on"],
          "independent native helper agreement",
          result["native_actual_RF054_CPU_master_clocks_equal"],
          "; USA 0/45, wrapper noninterference unproven")


if __name__ == "__main__":
    main()
