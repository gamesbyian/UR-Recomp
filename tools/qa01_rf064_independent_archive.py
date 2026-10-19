#!/usr/bin/env python3
"""Independently reopen genuine RF064 source-return archive; zero event credit.

Reads the original Snes9x RF044/045/063/064 outputs, checks their actual
sequencing and returned values, and reports missing getset-observer reads
without claiming that the underlying original game never read the stack.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

SCHEMA = "ur-qa01-rf064-independent-original-source-audit/1"
PULL_PREFIX = "QA01RF064ORIGPULL "
STACK_PREFIX = "QA01RF045ORIGSTACK "
BUS_PREFIX = "QA01RF063ORIGBUS "
BASE_PREFIX = "QA01RF044ORIGBUS "
CHECK_PREFIX = "QA01RF063ORIGCHECKPOINT "
NMI_PREFIX = "QA01RF044ORIGNMI "
REQUIRED = ("rf064-original-pulls.json", "rf064-original-log-sha256.txt",
            "case-result.json", "work/zoom-zoo/replay/reference.log")
PAT = re.compile(r"\b([a-z][a-z0-9]*)=([^\s]+)")


def require(flag: bool, why: str) -> None:
    if not flag:
        raise ValueError(why)


def rows(lines: list[str], prefix: str) -> list[dict[str, str]]:
    result = []
    for line in lines:
        if line.startswith(prefix):
            found = PAT.findall(line)
            parsed = dict(found)
            require(len(found) == len(parsed) and bool(parsed),
                    "duplicate or missing original source fields in " + prefix)
            result.append(parsed)
    return result



def post_nmi_return_witness(lines: list[str], checkpoint: dict[str, str]) -> dict:
    """Check actual returned NMI stack values, never inventing a bus read."""
    target = next((i for i, line in enumerate(lines)
                   if line.startswith(CHECK_PREFIX) and
                   dict(PAT.findall(line)).get("seq") == checkpoint["seq"]), None)
    require(target is not None, "source-local NMI checkpoint absent from log")
    next_bus = next((i for i in range(target + 1, len(lines))
                    if lines[i].startswith(BUS_PREFIX)), len(lines))
    nearby = rows(lines[target + 1:next_bus], PULL_PREFIX)
    result = {
        "source_nmi_frame": int(checkpoint["f"]),
        "source_local_checkpoint_seq": int(checkpoint["seq"]),
        "source_nmi_stack_bytes": checkpoint["stack"],
        "eligible_sequenced_getset_entries_before_next_bus": 0,
        "matched_post_nmi_true_return_sequence": False,
        "return_records": [],
        "actual_underlying_read_bus_entry_proven": False,
        "original_native_executed_pc_equivalence_proven": False,
    }
    saved = checkpoint["stack"]
    require(re.fullmatch(r"[0-9A-F]{10}", saved) is not None,
            "real NMI stack must have five unmasked bytes")
    expected = [
        ("pullB", 0x01ED, 1, int(saved[0:2], 16)),
        ("pullW", 0x01EE, 2,
         int(saved[2:4], 16) | int(saved[4:6], 16) << 8),
        ("pullB", 0x01F0, 1, int(saved[6:8], 16)),
        ("pullB", 0x01F1, 1, int(saved[8:10], 16)),
    ]
    if len(nearby) < len(expected):
        return result
    selected = nearby[:len(expected)]
    timestamps = []
    for row, (kind, base, width, value) in zip(selected, expected):
        require(row.get("kind") == kind and
                int(row["base"], 16) == base and
                int(row["width"]) == width and
                int(row["returned"], 16) == value and
                int(row["before"]) == int(checkpoint["seq"]) and
                int(row["after"]) == int(checkpoint["seq"]) and
                row["unique"] == "0",
                "true post-NMI return bytes disagree with unmasked source stack")
        stamps = (int(row["f"]), int(row["v"]), int(row["h"]))
        timestamps.append(stamps)
        result["return_records"].append({
            "kind": kind, "physical_wram_base": f"7E:{base:04X}",
            "width": width, "actual_returned_value_hex": f"{value:0{width*2}X}",
            "executed_original_pc": row["pc"],
            "original_frame": stamps[0], "original_v": stamps[1],
            "original_h": stamps[2],
        })
    require(timestamps == sorted(timestamps) and
            timestamps[0] >= (int(checkpoint["f"]),
                              int(checkpoint["v"]), int(checkpoint["h"])),
            "true original NMI return clock order invalid")
    result["matched_post_nmi_true_return_sequence"] = True
    return result



def original_nmi_return_series(lines: list[str]) -> dict:
    """Recheck every genuine RF044 NMI, without assigning an RF063 checkpoint.

    RF044 NMI records after the first have no shared checkpoint ordinal.
    Use original log order and the last source-local RF063 getset ordinal only,
    never synthesize extra checkpoint events or cross-native clocks.
    """
    results = []
    for index, line in enumerate(lines):
        if not line.startswith(NMI_PREFIX):
            continue
        nmi = dict(PAT.findall(line))
        saved = nmi.get("new", "")
        require(re.fullmatch(r"[0-9A-F]{10}", saved) is not None,
                "original NMI five raw stack bytes malformed")
        v = [int(saved[i:i+2], 16) for i in range(0, 10, 2)]
        expected = [("pullB", 0x01ED, 1, v[0]),
                    ("pullW", 0x01EE, 2, v[1] | v[2] << 8),
                    ("pullB", 0x01F0, 1, v[3]),
                    ("pullB", 0x01F1, 1, v[4])]
        earlier = [dict(PAT.findall(t)) for t in lines[:index]
                   if t.startswith((BUS_PREFIX, CHECK_PREFIX))]
        require(bool(earlier), "original NMI has no prior local source ordinal")
        seq = int(earlier[-1]["seq"])
        end = next((i for i in range(index+1, len(lines))
                    if lines[i].startswith(BUS_PREFIX)), len(lines))
        picks = rows(lines[index+1:end], PULL_PREFIX)[:4]
        frame = int(nmi["f"])
        matched = len(picks) == 4
        times = []
        for row, (kind, addr, width, value) in zip(picks, expected):
            stamps = (int(row["f"]), int(row["v"]), int(row["h"]))
            times.append(stamps)
            if not (row.get("kind") == kind and
                    int(row["base"], 16) == addr and
                    int(row["width"]) == width and
                    int(row["returned"], 16) == value and
                    int(row["before"]) == seq and
                    int(row["after"]) == seq and
                    row["unique"] == "0" and
                    stamps[0] == frame):
                matched = False
        require(times == sorted(times), "actual original NMI return clocks out of order")
        if len(picks) == 4:
            require(matched, "original NMI actual returned source bytes disagree")
        results.append({
            "original_frame": frame, "actual_nmi_saved_stack": saved,
            "most_recent_observed_source_ordinal": seq,
            "return_count_before_next_sequenced_getset_write": len(picks),
            "four_actual_returned_values_match_saved_nmi_stack": matched,
            "underlying_read_bus_entry_proven": False,
        })
    return {
        "original_nmi_observations": len(results),
        "nmis_with_four_matching_actual_source_returns": sum(
            r["four_actual_returned_values_match_saved_nmi_stack"] for r in results),
        "all_observed_nmis_have_four_matching_returns": bool(results) and all(
            r["four_actual_returned_values_match_saved_nmi_stack"] for r in results),
        "source_nmi_return_sequences": results,
        "native_equivalence_proven": False,
    }


def examine(archive: Path, expected_sha256: str | None = None) -> dict:
    digest = hashlib.sha256()
    with archive.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    archive_hash = digest.hexdigest()
    if expected_sha256 is not None:
        require(archive_hash == expected_sha256, "wrong immutable archive SHA256")
    with zipfile.ZipFile(archive) as z:
        members = z.infolist()
        require(len(members) < 2000 and
                len({m.filename for m in members}) == len(members),
                "excessive or duplicated source archive membership")
        require(set(REQUIRED) <= set(z.namelist()), "missing primary original evidence")
        require(all(not m.filename.startswith("/") and
                    ".." not in Path(m.filename).parts for m in members),
                "unsafe original source archive member")
        def read(name: str, limit: int) -> bytes:
            info = z.getinfo(name)
            require(info.file_size <= limit and not info.is_dir(),
                    "bad source member size: " + name)
            return z.read(name)
        report = json.loads(read("rf064-original-pulls.json", 100_000))
        case = json.loads(read("case-result.json", 250_000))
        claimed_hash = read("rf064-original-log-sha256.txt", 1000).decode().split()
        require(len(claimed_hash) == 2 and
                re.fullmatch(r"[0-9a-f]{64}", claimed_hash[0]) is not None,
                "unrecognized original replay log SHA receipt")
        log = read("work/zoom-zoo/replay/reference.log", 4_000_000)
        require(hashlib.sha256(log).hexdigest() == claimed_hash[0],
                "actual original replay log hash differs from receipt")
    lines = log.decode("utf8").splitlines()
    require(not any("_TRUNCATED" in line and line.startswith("QA01RF0")
                    for line in lines), "original source recorder overflow")
    rf45 = rows(lines, STACK_PREFIX)
    rf64 = rows(lines, PULL_PREFIX)
    rf63 = rows(lines, BUS_PREFIX)
    rf44 = rows(lines, BASE_PREFIX)
    checkpoints = rows(lines, CHECK_PREFIX)
    nmis = rows(lines, NMI_PREFIX)
    pulls = [r for r in rf45 if r.get("kind") in ("pullB", "pullW")]
    pushes = [r for r in rf45 if r.get("kind") in ("pushB", "pushW")]
    require(rf64 and len(rf64) == len(pulls),
            "missing RF064 true post-call pull rows")
    require(len(pushes) == len(rf63) == len(rf44),
            "RF063/044 bus population differs from source push population")
    require(len(checkpoints) == 1 and nmis, "missing real original NMI checkpoint")
    original_order = [dict(PAT.findall(line)) for line in lines
                      if line.startswith((BUS_PREFIX, CHECK_PREFIX))]
    require([int(r["seq"]) for r in original_order] ==
            list(range(1, len(original_order) + 1)),
            "missing or reordered original RF063 local ordinal")
    for a, b in zip(pulls, rf64):
        require(all(a.get(key) == b.get(key)
                    for key in ("f", "v", "h", "kind", "pc"))
                and a.get("value") == b.get("returned")
                and int(a["addr"], 16) == int(b["base"], 16)
                and int(a["width"]) == int(b["width"]),
                "true RF045/064 pull identity or returned data mismatch")
        require(int(b["after"]) >= int(b["before"]) and
                b["unique"] in ("0", "1") and
                (b["unique"] == "1") ==
                (int(b["after"]) == int(b["before"]) + 1),
                "inconsistent source-local pull transaction claim")
    for a, b in zip(rf44, rf63):
        require(all(a.get(key) == b.get(key)
                    for key in ("f", "v", "h", "kind")) and
                a["addr"] == b["addr"] and a["w"] == b["width"] and
                int(a["value"], 16) == int(b["sampled"], 16) and
                a["pb"] + ":" + a["pc"] == b["pc"],
                "RF063 sequenced getset not same genuine RF044 bus entry")
    for c in checkpoints:
        matches = [n for n in nmis if n.get("f") == c.get("f") and
                   n.get("f1") == c.get("f1") and n.get("new") == c.get("stack")]
        require(len(matches) == 1 and c.get("phase") == "post_real_nmi_push",
                "real source NMI checkpoint does not match unmasked RF044 stack")
    unique = sum(r["unique"] == "1" for r in rf64)
    absent = sum(r["before"] == r["after"] for r in rf64)
    require(report.get("schema") == "ur-qa01-rf064-original-consumed-pull-join/1"
            and report.get("post_call_actual_original_pull_count") == len(rf64)
            and report.get("sequenced_original_bus_entries") == len(rf63)
            and report.get("actual_returns_with_unique_source_bus_entry") == unique
            and report.get("ambiguous_or_reentrant_original_pulls") == len(rf64)-unique
            and report.get("accepted_USA_events") == 0,
            "RF064 producer claims do not agree with actual replay log")
    require(case.get("release_credit") == 0 and case.get("source_sha") and
            case.get("evidence", {}).get("rom_sha256"),
            "original producer source identity/release status missing")
    post_nmi = post_nmi_return_witness(lines, checkpoints[0])
    nmi_series = original_nmi_return_series(lines)
    kinds = Counter(r["kind"] for r in rf63)
    read_count = kinds.get("rb", 0) + kinds.get("rw", 0)
    return {
        "schema": SCHEMA, "classification": "diagnostic_HOLD_no_guest_event_credit",
        "archive_sha256": archive_hash,
        "reference_log_sha256": claimed_hash[0],
        "source_sha": case["source_sha"],
        "rom_sha256": case["evidence"]["rom_sha256"],
        "original_pull_returns_qualified_by_rf045": len(rf64),
        "original_pull_byte_count": sum(r["kind"] == "pullB" for r in rf64),
        "original_pull_word_count": sum(r["kind"] == "pullW" for r in rf64),
        "sequenced_getset_kind_counts": dict(sorted(kinds.items())),
        "sequenced_original_getset_reads_observed": read_count,
        "all_pull_returns_without_intervening_sequenced_bus_entry": absent,
        "original_pull_returns_joined_to_unique_getset_event": unique,
        "rf044_and_rf063_original_getset_rows_match": True,
        "rf063_ordinals_complete": True,
        "real_nmi_checkpoint_raw_stack_matches_rf044": True,
        "post_nmi_original_return_witness": post_nmi,
        "all_original_nmi_return_series": nmi_series,
        "source_read_path_status": (
            "no_original_stack_reads_observed_at_current_getset_probe"
            if read_count == 0 else "reads_observed_requires_separate_causal_join"),
        "original_emulator_did_not_read_stack_proven": False,
        "actual_return_proves_specific_underlying_bus_site": False,
        "native_executed_pc_or_clock_equivalence_proven": False,
        "accepted_USA_events": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expect-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verdict = examine(args.archive, args.expect_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(verdict, sort_keys=True, indent=2) + "\n")
    print("RF064 independent true source-return audit: HOLD, 0/45 USA")


if __name__ == "__main__":
    main()
