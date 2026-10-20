#!/usr/bin/env python3
"""Source-authentic four-ZIP RF062 *script provenance*, never a cold proof.

The strict four-ZIP gameplay/replay audit must remain RED: its raw-capture
script SHA differs. This consumer independently explains the delta using the
actual archived script bytes and preserves explicit noninterference HOLD.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import zipfile

import qa01_rf062_real_read_raw_archive as strict

SCHEMA = "ur-qa01-rf062-four-archive-replay-script-difference/1"
SCRIPT = "work/zoom-zoo/replay/complete.script"
INPUTS = ("work/zoom-zoo/replay/ref.input",
          "work/zoom-zoo/replay/pinned-baldosa.input")
REQUIRED_EXTRA_DUMPS = (
    "dump qa01-frame-005105",
    "dump qa01-frame-005106",
    "dump qa01-frame-005107",
)
BASE_SCRIPT_SHA = "1eb3e8416b7fa40935d097c78d281ca98537c9a555e23f1906a99912dcdb2c52"
RAW_SCRIPT_SHA = "92012c94af3a27c54144e34c9d1d7a6cdb97ddf3e519d3f24c375c7c76bf6bc2"


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def source_commands(raw: bytes) -> list[str]:
    need(0 < len(raw) < 100000 and raw.endswith(b"\n") and b"\r" not in raw,
         "noncanonical or incomplete source replay script bytes")
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise ValueError("non-ASCII source replay script") from exc
    need(all(line and line == line.strip() for line in lines),
         "ambiguous or blank source replay command")
    return lines


def comparable_script(early: bytes, later: bytes) -> dict:
    """Compare actual literal commands, not a producer's script summary.

    Collapse consecutive waits only after the exact 3 added dump operations
    are removed; a substituted reset, controller event or until condition
    cannot be hidden by this operation.
    """
    commands0, commands1 = source_commands(early), source_commands(later)
    need(strict.sha(early) == BASE_SCRIPT_SHA and strict.sha(later) == RAW_SCRIPT_SHA,
         "archived original RF062 cold/raw replay script SHA differs")
    extra = [x for x in commands1 if x.startswith("dump qa01-frame-")]
    need(tuple(extra) == REQUIRED_EXTRA_DUMPS and
         not any(x.startswith("dump qa01-frame-") for x in commands0),
         "raw observer inserted missing, extra or shifted dump labels")
    # Name alone is NOT proof of capture host time. Assert the literal wait
    # schedule at each inserted site from two existing genuine scene anchors.
    # A total of 20 frames with shifted individual dump positions is invalid.
    first_anchor, last_anchor = "dump scene-05100", "dump scene-05120"
    need(commands0.count(first_anchor) == commands1.count(first_anchor) == 1 and
         commands0.count(last_anchor) == commands1.count(last_anchor) == 1,
         "missing or duplicated original script observation anchors")
    original_window = commands0[commands0.index(first_anchor)+1:
                                commands0.index(last_anchor)]
    raw_window = commands1[commands1.index(first_anchor)+1:
                           commands1.index(last_anchor)]
    need(original_window == ["wait 20"] and raw_window == [
        "wait 5", REQUIRED_EXTRA_DUMPS[0],
        "wait 1", REQUIRED_EXTRA_DUMPS[1],
        "wait 1", REQUIRED_EXTRA_DUMPS[2],
        "wait 13",
    ], "raw image dump commands are not at genuine relative +5105/+5106/+5107")

    def collapse(commands, allow_extra):
        normalized = []
        waits = 0
        for cmd in commands:
            if cmd in REQUIRED_EXTRA_DUMPS and allow_extra:
                continue
            found = re.fullmatch(r"wait ([1-9][0-9]*)", cmd)
            if found:
                waits += int(found.group(1))
                continue
            if waits:
                normalized.append(f"wait {waits}")
                waits = 0
            normalized.append(cmd)
        if waits:
            normalized.append(f"wait {waits}")
        return normalized
    first = collapse(commands0,False)
    second = collapse(commands1,True)
    need(first == second, "raw replay includes more than qualified dump/wait partition")
    return {
        "baseline_script_sha256": strict.sha(early),
        "raw_capture_script_sha256": strict.sha(later),
        "source_script_sha_changed": True,
        "raw_additional_script_dump_commands": list(REQUIRED_EXTRA_DUMPS),
        "normalized_original_control_command_sequence_equal": True,
        "unchanged_20_frame_wait_total_around_added_dump_commands": True,
        "added_dumps_at_exact_declared_script_relative_frames": [5105, 5106, 5107],
        "actual_guest_acknowledgment_clocks_independently_reopened": False,
        "extra_script_commands_are_CPU_invisible_proven": False,
    }


def audit(baseline: Path, native: Path, binaries: Path, raw_pair: Path) -> dict:
    sources = (
        (baseline,strict.BASELINE_SHA,"historic original"),
        (native,strict.NATIVE_CASE_SHA,"executed native"),
        (binaries,strict.NATIVE_BINARIES_SHA,"compiled binaries"),
        (raw_pair,strict.RAW_PAIR_CASE_SHA,"source/native raw"),
    )
    qualified = {title: strict.qualified_zip_snapshot(path,expected,title)
                 for path,expected,title in sources}
    pins = {title: verified[0] for title,verified in qualified.items()}
    with zipfile.ZipFile(io.BytesIO(qualified["historic original"][1])) as b, \
         zipfile.ZipFile(io.BytesIO(qualified["executed native"][1])) as n, \
         zipfile.ZipFile(io.BytesIO(qualified["source/native raw"][1])) as r:
        p0, p1, p2 = (json.loads(z.read("producer-report.json"))
                      for z in (b,n,r))
        case1, case2 = (json.loads(z.read("case-result.json")) for z in (n,r))
        control = ("rom_sha256","original_movie_sha256",
                   "original_movie_window_sha256", "source_sram_sha256")
        need(all(p0[k] == p1[k] == p2[k] for k in control) and
             p0["input_sha256"] == p1["input_sha256"] == BASE_SCRIPT_SHA and
             p2["input_sha256"] == RAW_SCRIPT_SHA and
             all(p["reference_entry"] == p["native_entry"] == 1017
                 for p in (p0,p1,p2)),
             "historical movie, original SRAM, guest race-frame origins or replay script source moved")
        need(all(case["disposition"] == "strict_candidate" and
                 case["release_credit"] == 0 and
                 case["evidence"]["original_movie_window_sha256"] ==
                    p0["original_movie_window_sha256"]
                 for case in (case1,case2)),
             "new raw replay cannot claim finished game or changed source controller movie")
        original_input_files = []
        for name,prefix in ((INPUTS[0],"reference"),(INPUTS[1],"native")):
            first,second=n.read(name),r.read(name)
            need(first == second and
                 len(first) == p1["qa01_capture_ab_control"][
                     prefix+"_supplied_input_bytes"] ==
                     p2["qa01_capture_ab_control"][
                         prefix+"_supplied_input_bytes"] and
                 strict.sha(first) ==
                    p1["qa01_capture_ab_control"][
                        prefix+"_supplied_input_sha256"] ==
                    p2["qa01_capture_ab_control"][
                        prefix+"_supplied_input_sha256"],
                 "actual Snes9x/Baldosa supplied controller bytes or pinned SHA changed")
            original_input_files.append({
                "member":name, "actual_SHA256":strict.sha(first),
                "actual_bytes":len(first),
                "same_exact_native_and_original_guest_file_across_replays":True,
            })
        script = comparable_script(n.read(SCRIPT),r.read(SCRIPT))
    return {
        "schema":SCHEMA,
        "four_independently_pinned_original_ZIP_sha256":pins,
        "source_movie_ROM_seed_origin_controls_qualified":True,
        "real_original_and_native_controller_input_files":original_input_files,
        **script,
        "strict_original_raw_guest_script_SHA_equivalence_proven":False,
        "cold_process_reload_proven_for_changed_script":False,
        "observer_noninterference_proven":False,
        "native_helper_population_656_vs_655_explained_as_benign":False,
        "same_phase_original_native_actual_read_value_parity_proven":False,
        "accepted_USA_events":0,
        "release_QA_gates":0,
        "adjudication":"HOLD: three source raw dumps split waits without changing supplied guest controller files; script SHA and instrumentation effects differ",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("baseline","native","binaries","raw-pair","output"):
        parser.add_argument("--"+arg,type=Path,required=True)
    args=parser.parse_args()
    need(not args.output.exists(),"refuse to overwrite independently reviewed source receipt")
    report=audit(args.baseline,args.native,args.binaries,args.raw_pair)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("RF062 authentic script difference identified; strict cold evidence remains HOLD")


if __name__=="__main__":
    main()
