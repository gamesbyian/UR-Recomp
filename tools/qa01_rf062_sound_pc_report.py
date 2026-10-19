#!/usr/bin/env python3
"""RF062 real native CPU operand consumption with decoded original opcode PC.

Require real RF062 direct-wrapper rows to join true RF054 paced CPU helper
reads, and the authentic original RF049 LDA and RF050 port publication.
No original/native clock rebasing, no WRAM masks or event promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ORIG = "work/zoom-zoo/replay/reference.log"
NATIVE = "work/zoom-zoo/replay/native.log"
BASELINE_SHA = "3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c"
CONTROLS = ("zoo_race_mesh", "zoo_next_bowl_handoff", "source_terminal_followthrough")
LIVE = "Snd_UploadBlockList_82EF_M1X0"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def fields(line: str) -> dict:
    return dict(part.split("=", 1) for part in line.split()[1:] if "=" in part)


def capture(text: str, prefix: str) -> list[dict]:
    return [fields(line[line.index(prefix):])
            for line in text.splitlines() if prefix in line]


def report(candidate: Path, baseline: Path) -> dict:
    base_data = baseline.read_bytes()
    require(hashlib.sha256(base_data).hexdigest() == BASELINE_SHA,
            "RF062 original authentic baseline ZIP SHA changed")
    case_data = candidate.read_bytes()
    with zipfile.ZipFile(candidate) as z, zipfile.ZipFile(baseline) as prior:
        old_p = json.loads(prior.read("producer-report.json"))
        p = json.loads(z.read("producer-report.json"))
        c = json.loads(z.read("case-result.json"))
        # Original RF049/050 authoritatively executed in the rehashed prior
        # archive. It need not be *reinstrumented* just to observe native
        # direct-PC source. Changed original core/movie/input/control forbids
        # this reuse; no source/native clock rebasing is permitted.
        original_bytes = prior.read(ORIG)
        candidate_original_bytes, native_bytes = z.read(ORIG), z.read(NATIVE)
    require(c["disposition"] == "strict_candidate" and c["release_credit"] == 0,
            "candidate was inappropriately promoted")
    require(all(p[name] == old_p[name] for name in CONTROLS),
            "RF062 original/native strict whole-WRAM, result, Bowl or SRAM control changed")
    require(all(p[name] == old_p[name] for name in
                ("rom_sha256", "original_movie_sha256", "input_sha256")),
            "RF062 source ROM/movie/controller input identity changed")
    original = original_bytes.decode("utf8")
    native = native_bytes.decode("utf8")
    require("QA01RF062NATIVE_TRUNCATED" not in native and
            "QA01RF054NATIVEBUS_TRUNCATED" not in native,
            "RF062/RF054 native source recorder overflow")
    direct = capture(native, "QA01RF062NATIVE ")
    real = capture(native, "QA01RF054NATIVEBUS ")
    reads = [x for x in real if x.get("kind") == "read8"]
    require(len(reads) == 656 and
            [int(x["seq"]) for x in reads] == list(range(1, 657)),
            "RF054 independent actual native sound helper census incomplete")
    require(len(direct) == 10 and
            [int(x["seq"]) for x in direct] == list(range(1, 11)),
            "RF062 native actual sound reader missing/repeated/gapped")
    original_lda = [x for x in capture(original, "QA01RF049LDA ")
                    if x.get("ea") == "11C774"]
    require(len(original_lda) == 1, "original real 11:C774 opcode operand absent/duplicated")
    lda = original_lda[0]
    require(lda["pc"] == "82:82F0" and lda["frame"] == "6124" and
            lda["d"] == "0000" and lda["ptr"] == "110000" and
            lda["y"] == "C774" and lda["a0"] == "630D" and
            lda["a1"] == "63D0",
            "original true 82:82F0 LDA source operand/consumed value changed")
    ports = capture(original, "QA01RF050ORIGAPU ")
    pub = [x for x in ports if x.get("seq") in ("21", "22")]
    require([(x["seq"], x["port"], x["val"]) for x in pub] ==
            [("21", "3", "D0"), ("22", "2", "63")] and
            int(pub[1]["age"]) > int(pub[0]["age"]),
            "original actual CPU->APU source port publication missing/changed")
    independent = {}
    for row in reads:
        key = (row["addr"], row["master"], row["A"], row["Y"], row["D"])
        require(key not in independent, "RF054 actual helper call signature duplicated")
        independent[key] = row
    proven = []
    for i, row in enumerate(direct):
        addr = "11" + f"{0xC770+i:04X}"
        require(row["f"] == "6124" and row["executedPC"] == "8282F0" and
                row["addr"] == addr and row["Y"] == addr[2:] and
                row["D"] == "0000" and row["dp65"] == "11" and
                re.fullmatch(r"[0-9A-F]{2}", row["value"]),
                "RF062 executed decoded opcode, bank or exact indexed operand changed")
        key = (row["addr"], row["master"], row["A"], row["Y"], row["D"])
        ref = independent.get(key)
        require(ref is not None and ref["scope"] == LIVE,
                "RF062 decoded PC has no matching actual RF054 CPU helper call")
        proven.append({
            "native_local_read_ordinal": int(row["seq"]),
            "source_opcode_guest_PC": row["executedPC"],
            "native_physical_operand": row["addr"],
            "native_real_returned_byte": row["value"],
            "native_independent_CPU_master": int(row["master"]),
            "independent_rf054_real_helper_ordinal": int(ref["seq"]),
        })
    target = proven[4]
    require(target["native_physical_operand"] == "11C774" and
            target["native_real_returned_byte"] == lda["a1"][-2:] and
            target["independent_rf054_real_helper_ordinal"] == 492,
            "first real original/native 11:C774 instruction-consumed byte mismatch")
    return {
        "schema": "ur-qa01-rf062-source-opcode-direct-native-bus/1",
        "candidate_zip_sha256": hashlib.sha256(case_data).hexdigest(),
        "baseline_zip_sha256": BASELINE_SHA,
        "candidate_source_sha": c["source_sha"],
        "original_baseline_log_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "candidate_original_log_sha256": hashlib.sha256(candidate_original_bytes).hexdigest(),
        "original_sound_opcode_provenance": "immutable genuine RF054 baseline only",
        "native_log_sha256": hashlib.sha256(native_bytes).hexdigest(),
        "actual_native_decoder_bound_read_count": 10,
        "actual_source_and_native_11C774_consumed_byte_same": True,
        "actual_native_opcode_pc": "8282F0",
        "original_cpu_port3_port2_actual_publication": ["D0", "63"],
        "original_guest_clock_age_at_port3": int(pub[0]["age"]),
        "native_11C774_independent_CPU_master": target["native_independent_CPU_master"],
        "native_reads": proven,
        "original_native_clock_epochs_equivalent": False,
        "sound_PCM_equivalence_proven": False,
        "first_consumed_original_native_difference_proven": False,
        "complete_USA_events_accepted": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    value = report(args.candidate, args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print("RF062 actual native decoded 82:82F0 read PC qualified; event credit stays 0")


if __name__ == "__main__":
    main()
