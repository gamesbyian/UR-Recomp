#!/usr/bin/env python3
"""Reopen authentic RF054 Zoom Zoo stack evidence without inventing bus causality.

Read-only bounded ZIP verifier. Cross-guest clocks remain independent. Never
admit complete USA events, infer native executed PCs or mask raw differences.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

SOURCE = "work/zoom-zoo/replay/reference.log"
NATIVE = "work/zoom-zoo/replay/native.log"
FRAMES = tuple(range(1017, 1026))
ARCHIVE_SHA = "3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def fields(line: str) -> dict:
    return dict(part.split("=", 1) for part in line.split()[1:] if "=" in part)


def verify(case: Path, receipt: dict | None = None, *, expected_sha: str = ARCHIVE_SHA) -> dict:
    raw = case.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == expected_sha, "original/native archive SHA256 mismatch")
    with zipfile.ZipFile(case) as z:
        require(SOURCE in z.namelist() and NATIVE in z.namelist(),
                "original/native replay log absent")
        a, b = z.read(SOURCE), z.read(NATIVE)
        producer = json.loads(z.read("producer-report.json"))
        decision = json.loads(z.read("case-result.json"))
    original, native = a.decode("utf8"), b.decode("utf8")
    require(decision.get("source_sha") and decision.get("release_credit") == 0 and
            decision.get("disposition") == "strict_candidate",
            "case source identity / acceptance changed")
    mesh = producer["zoo_race_mesh"]
    require(mesh["mesh_checkpoint_count"] == 78 and
            mesh["raw_byte_exact_sample_count"] == 51 and
            mesh["masked_or_excluded_wram_bytes"] == 0 and
            sum(row["original_native_full_wram_byte_difference"]["differing_byte_count"]
                for row in mesh["samples"]) == 92,
            "unmasked full-WRAM controls changed")
    require("QA01RF045ORIGSTACK_TRUNCATED" not in original and
            "QA01RF047NATIVE_TRUNCATED" not in native,
            "original/native actual stack observer overflowed")
    orig_nmis, orig_returns = {}, defaultdict(list)
    orig_macros = orig_bus = 0
    for line in original.splitlines():
        if line.startswith("QA01RF044ORIGNMI "):
            x = fields(line)
            frame = int(x["f"])
            require(frame in FRAMES and frame not in orig_nmis,
                    "source NMI calendar missing or duplicated")
            require(x["f1"] == x["f"] and x["S0"] == "01F0" and
                    x["S1"] == "01EC" and
                    x["pc"] in ("82D4EE", "82D4F0"),
                    "original NMI interrupted state changed")
            orig_nmis[frame] = x
        elif line.startswith("QA01RF045ORIGSTACK "):
            orig_macros += 1
            x = fields(line)
            if x.get("kind") == "pullB" and x.get("addr") == "01ED" and \
               x.get("width") == "1" and x.get("value") == "0026" and \
               x.get("pc") == "80:B0EB":
                orig_returns[int(x["f"])].append(x)
        elif line.startswith("QA01RF044ORIGBUS "):
            orig_bus += 1
    require(orig_macros == 1806 and orig_bus == 903 and
            set(orig_nmis) == set(FRAMES),
            "original RF044/RF045 genuine recorder count changed")
    native_records = []
    for line in native.splitlines():
        pos = line.find("QA01RF047NATIVE ")
        if pos >= 0:
            row = fields(line[pos:])
            require(all(x in row for x in ("seq", "stage", "f")),
                    "native event header malformed")
            native_records.append(row)
    require(len(native_records) == 2741 and
            sorted(int(x["seq"]) for x in native_records) == list(range(1, 2742)),
            "native actual recorder ordinal missing, duplicated or truncated")
    frames = defaultdict(list)
    for row in native_records:
        frames[int(row["f"])].append(row)
    paired = []
    for frame in FRAMES:
        require(len(orig_returns[frame]) == 1,
                "genuine original status return pull absent or duplicated")
        rows = sorted(frames[frame], key=lambda x: int(x["seq"]))
        for stage in ("entry", "after_push", "compiled_rti", "handler_return"):
            require(sum(x["stage"] == stage for x in rows) == 1,
                    "native NMI boundary missing or duplicated")
        entry, pushed, rti, returned = (
            next(x for x in rows if x["stage"] == stage)
            for stage in ("entry", "after_push", "compiled_rti", "handler_return")
        )
        require(entry["resume"] == pushed["resume"] == returned["resume"] == "82D4EE" and
                entry["S"] == "01F0" and pushed["S"] == "01EC" and
                returned["S"] == rti["S"] == "01F0" and
                pushed["stack"] == "26EED482",
                "native actual interrupt push/return state changed")
        push_seq = int(pushed["seq"])
        readers = [x for x in rows if int(x["seq"]) == push_seq + 1]
        require(len(readers) == 1 and readers[0]["stage"] == "read" and
                readers[0]["bank"] == "00" and readers[0]["addr"] == "01ED" and
                readers[0]["width"] == "1" and readers[0]["value"] == "0026" and
                readers[0].get("nmi") == "1" and
                int(rti["seq"]) > push_seq + 1 and
                int(returned["seq"]) > int(rti["seq"]),
                "native first real post-push status consumer is missing or different")
        orig = orig_nmis[frame]
        # True original NMI writes status, saved PC low/high, bank in order.
        expected = "26" + orig["pc"][4:6] + orig["pc"][2:4] + "82" + "26"
        require(orig["new"] == expected,
                "original actual NMI stack bus writer state changed")
        paired.append({"frame": frame, "original_resume": orig["pc"],
                       "native_resume": pushed["resume"],
                       "native_after_push_seq": push_seq,
                       "native_status_read_seq": push_seq + 1,
                       "consumed_status_original": "26",
                       "consumed_status_native": "26"})
    require(sum(x["stage"] == "read" for x in native_records) == 2705,
            "native true read-helper population changed")
    result = {
        "schema": "ur-qa01-rf061-archive-verified/1",
        "case_zip_sha256": digest,
        "original_log_sha256": hashlib.sha256(a).hexdigest(),
        "native_log_sha256": hashlib.sha256(b).hexdigest(),
        "source_sha": decision["source_sha"],
        "verified_real_status_reads_matching": len(paired),
        "native_real_bus_helper_reads": 2705,
        "original_resume_counts": dict(Counter(x["original_resume"] for x in paired)),
        "native_resume_counts": dict(Counter(x["native_resume"] for x in paired)),
        "per_frame": paired,
        "all_original_native_clocks_independent": True,
        "native_bus_read_executed_PC_proven": False,
        "first_consumed_different_byte_proven": False,
        "causal_window_eligible": False,
        "complete_USA_events_accepted": 0,
    }
    if receipt is not None:
        meta, nmi = receipt["provenance"], receipt["original_native_NMI"]
        require(meta["case_zip_sha256"] == digest and
                meta["original_reference_log_sha256"] == result["original_log_sha256"] and
                meta["native_replay_log_sha256"] == result["native_log_sha256"],
                "stored immutable ZIP/member digest mismatch")
        for key, actual in (("source_core_sha256", producer["reference_core_sha256"]),
                            ("native_elf_sha256", producer["native_executable_sha256"]),
                            ("rom_sha256", producer["rom_sha256"]),
                            ("expanded_input_sha256", producer["input_sha256"]),
                            ("original_movie_sha256", producer["original_movie_sha256"])):
            require(meta[key] == actual, "stored source/input identity mismatch: " + key)
        require(meta["case_source_sha"] == decision["source_sha"] and
                nmi["nine_of_nine_status_values_match"] and
                nmi["native_after_push_status_read_ordinal_pairs"] ==
                [[x["native_after_push_seq"], x["native_status_read_seq"]] for x in paired] and
                all(nmi["original_guest_resume_by_frame"][str(x["frame"])] ==
                    x["original_resume"] for x in paired),
                "stored source-NMI observation unsupported by raw logs")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", type=Path)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = verify(args.case,
                    json.loads(args.receipt.read_text()) if args.receipt else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("RF061 genuine nine-NMI status equivalence only; causal-window HOLD, 0 events")


if __name__ == "__main__":
    main()
