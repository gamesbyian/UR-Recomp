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
import re
import zipfile
from pathlib import Path

SCHEMA = "ur-qa01-rf062-same-executable-logging-ab/1"
IMMUTABLE = ("rom_sha256", "original_movie_sha256",
             "original_movie_window_sha256", "input_sha256",
             "reference_core_sha256", "reference_script_sha256",
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



# Only these exact three reporter path lines are host-directory metadata.
# Preserve the original input count, script command count, SRAM byte count,
# and every other source line verbatim. No native instructions are excluded.
PATH_META = (
    (re.compile(r"^(\\[input\\] loaded [0-9]+ event\\(s\\) from )(/\\S+)$"),
     "/zoom-zoo/replay/ref.input", "original_supplied_input_path"),
    (re.compile(r"^(script: loaded [0-9]+ command\\(s\\) from )(/\\S+)$"),
     "/zoom-zoo/replay/complete.script", "original_script_path"),
    (re.compile(r"^(\\[memory\\] loaded [0-9]+ SRAM bytes from )(/\\S+)$"),
     "/zoom-zoo/anchored.srm", "original_sram_path"),
)


def strictly_qualified_original_path_variation(off: bytes, on: bytes) -> dict:
    left = off.decode("utf8").splitlines()
    right = on.decode("utf8").splitlines()
    changed = []
    clean = len(left) == len(right)
    observed = set()
    if clean:
        for i, (a, b) in enumerate(zip(left, right)):
            if a == b:
                continue
            qualified = None
            for pattern, tail, name in PATH_META:
                match_a, match_b = pattern.fullmatch(a), pattern.fullmatch(b)
                if (match_a is not None and match_b is not None and
                        match_a.group(1) == match_b.group(1) and
                        match_a.group(2).endswith(tail) and
                        match_b.group(2).endswith(tail) and
                        name not in observed):
                    qualified = name
                    break
            if qualified is None:
                clean = False
                break
            observed.add(qualified)
            changed.append({"line_zero_based": i, "metadata_field": qualified})
    return {
        "exact_log_bytes_equal": off == on,
        "different_lines_only_qualified_host_path_metadata": clean,
        "allowed_path_metadata_changes": changed if clean else [],
        "source_log_line_counts_off_on": [len(left), len(right)],
        "source_nonpath_log_equality_proven": clean,
    }


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
    # The extra ten RF062 rows must be actual *returned* operations, each
    # uniquely present in RF054's separately instrumented paced CPU helper
    # at the identical native-local master clock and register context.
    for read in present:
        hits = [row for row in on_bus if all(
            row[k] == read[k] for k in ("addr", "master", "A", "Y", "D"))]
        must(len(hits) == 1, "RF062 direct record was not a real same-clock RF054 helper read")
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
    original_control = strictly_qualified_original_path_variation(
        off_logs["original"], on_logs["original"])
    same_original = original_control["source_nonpath_log_equality_proven"]
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
        "original_complete_log_byte_identical": original_control["exact_log_bytes_equal"],
        "original_qualified_source_log_path_differences": original_control,
        "rf062_actual_native_read_count_off_on": [len(absent),len(present)],
        "native_real_sound_helper_count_off_on": [len(a),len(b)],
        "native_sound_helper_matching_ordered_observations": matches,
        "native_sound_helper_edit_blocks": edits,
        "native_actual_RF054_address_and_register_rows_equal": same_operand,
        "native_actual_RF054_CPU_master_clocks_equal": same_cpu_clock,
        "original_native_whole_mesh_and_followthrough_equal": same_outputs,
        "runtime_RF062_logging_noninterference_supported": (
            same_original and same_operand and same_cpu_clock and same_outputs),
        "wrapper_replacement_noninterference_proven": False,
        "original_native_opcode_clock_equivalence_proven": False,
        "actual_CPU_joypad_poll_equivalence_proven": False,
        "USA_events_accepted": 0,
    }




def independent_binaries(artifact: Path, report: dict,
                         pinned_sha256: str | None = None) -> dict:
    """Reopen *actual* original/native emulator bytes, not only report SHAs."""
    digest = hashlib.sha256()
    with artifact.open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
    file_sha = digest.hexdigest()
    if pinned_sha256 is not None:
        must(file_sha == pinned_sha256, "immutable RF062 binary artifact changed")
    with zipfile.ZipFile(artifact) as zip_file:
        paths = zip_file.namelist()
        must(len(paths) == len(set(paths)) and
             {"native","snes9x_libretro.so","snesref","SHA256SUMS"} <= set(paths),
             "missing/duplicated native or reference binary")
        entries = zip_file.read("SHA256SUMS").decode().splitlines()
        pairs = [line.split() for line in entries]
        must(len(pairs) == 3 and
             all(len(pair) == 2 and len(pair[0]) == 64 for pair in pairs),
             "unrecognized actual emulator binary SHA receipt")
        known = {name:digest for digest,name in pairs}
        must(set(known) == {"native","snes9x_libretro.so","snesref"},
             "incomplete or duplicate emulator binary digest listing")
        for name,want in known.items():
            size=zip_file.getinfo(name).file_size
            must(0 < size <= 30_000_000 and
                 sha(zip_file.read(name)) == want,
                 "actual source/native emulator binary digest mismatch: "+name)
        must(known["native"] == report["native_executable_sha256"] and
             known["snes9x_libretro.so"] == report["reference_core_sha256"],
             "real emulator binary bytes disagree with original/native A/B")
    return {
        "binary_artifact_SHA256":file_sha,
        "actual_native_binary_SHA256":known["native"],
        "actual_original_core_SHA256":known["snes9x_libretro.so"],
        "all_three_emulator_tool_binaries_rehashed":True,
    }


def archived(zip_path: Path, expected_sha256: str | None = None,
             binary_artifact: Path | None = None,
             binary_sha256: str | None = None) -> dict:
    """Reopen one *completed* genuine Actions ON/OFF archive without emulator.

    Artifacts sometimes have one additional upload common-root prefix. Resolve
    exactly one copy of every member under a matched qa01-rf062-ab root.
    Reject duplicates, wrong byte sizes and incomplete original/native files.
    """
    h = hashlib.sha256()
    with zip_path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    artifact_sha = h.hexdigest()
    if expected_sha256 is not None:
        must(artifact_sha == expected_sha256,
             "authenticated RF062 ON/OFF artifact SHA256 changed")
    with zipfile.ZipFile(zip_path) as z:
        members = z.infolist()
        paths = [m.filename for m in members]
        must(len(members) < 1000 and len(paths) == len(set(paths)) and
             sum(m.file_size for m in members) <= 100_000_000 and
             all(not p.startswith("/") and ".." not in Path(p).parts
                 for p in paths),
             "duplicate/unsafe/unbounded authentic A/B archive members")
        name = "/qa01-rf062-ab/off/producer-report.json"
        roots = {p[:-len(name)] for p in paths if p.endswith(name)}
        if "qa01-rf062-ab/off/producer-report.json" in paths:
            roots.add("")
        must(len(roots) == 1, "ambiguous actual A/B archive root")
        root = next(iter(roots))
        prefix = root + "/qa01-rf062-ab" if root else "qa01-rf062-ab"
        def member(where: str, limit: int) -> bytes:
            target = prefix + "/" + where
            must(target in paths and
                 z.getinfo(target).file_size <= limit,
                 "missing or unbounded original/native A/B source: " + where)
            return z.read(target)
        population = []
        for mode in ("off", "on"):
            report = json.loads(member(mode+"/producer-report.json", 2_000_000))
            logs = {
                "original":member(mode+"/work/zoom-zoo/replay/reference.log", 12_000_000),
                "native":member(mode+"/work/zoom-zoo/replay/native.log", 30_000_000)
            }
            supplied = {
                "original":member(mode+"/work/zoom-zoo/replay/ref.input", 100_000),
                "native":member(mode+"/work/zoom-zoo/replay/pinned-baldosa.input", 100_000)
            }
            population.append((report,logs,supplied))
        off, off_logs, off_inputs = population[0]
        on, on_logs, on_inputs = population[1]
        result = control(off, on, off_logs, on_logs, off_inputs, on_inputs)
    if binary_artifact is not None:
        result["independently_reopened_compiled_binaries"] = independent_binaries(
            binary_artifact, off, binary_sha256)
    else:
        result["independently_reopened_compiled_binaries"] = None
    result["authenticated_evidence_archive_sha256"] = artifact_sha
    result["zip_archive_raw_byte_reopened"] = True
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--off", type=Path)
    p.add_argument("--on", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--expect-sha256")
    p.add_argument("--binary-artifact", type=Path)
    p.add_argument("--expect-binary-sha256")
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
    if args.archive is not None:
        must(args.off is None and args.on is None,
             "use only archive or off/on directories")
        result=archived(args.archive,args.expect_sha256,
                        args.binary_artifact,args.expect_binary_sha256)
    else:
        must(args.off is not None and args.on is not None and
             args.binary_artifact is None,
             "missing or mixed A/B input population")
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
