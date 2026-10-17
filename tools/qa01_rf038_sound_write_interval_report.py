#!/usr/bin/env python3
"""Read RF038 real Zoo case ZIP; attribute a *single* CPU writer interval.

Never interprets sampled SPC ages as actual receiver clocks, does not patch
timing, and never admits any USA course or Windows candidate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from qa01_rf037_port_writer_report import (
    ORIGINAL_LOG, NATIVE_LOG, logs, canonical_original_equal_age_pairs,
)

TARGET_ORDINAL = 24390
EXPECTED_ORIGINAL = ((116, 442, 2, "24"), (116, 972, 3, "02"))
EXPECTED_NATIVE = ((6091, 2176886834, 0x2142, "24"),
                   (6091, 2176887208, 0x2143, "02"))


def parse_event(line: str, tag: str) -> dict[str, str] | None:
    if not line.startswith(tag + " "):
        return None
    return dict(cell.split("=", 1) for cell in line.split()[1:] if "=" in cell)


def inspect(original_ports: list[dict], native_ports: list[dict],
            opcode_events: list[dict], paced_events: list[dict],
            *, ordinal: int = TARGET_ORDINAL, truncated: tuple[str, ...] = ()) -> dict:
    if truncated:
        raise ValueError("RF038 recorder truncated: " + ",".join(truncated))
    canon = canonical_original_equal_age_pairs(original_ports)["rows"]
    if ordinal < 1 or len(canon) <= ordinal or len(native_ports) <= ordinal:
        raise ValueError("missing source/native writer ordinal")
    original = canon[ordinal-1:ordinal+1]
    native = native_ports[ordinal-1:ordinal+1]
    for a, b in zip(original, native):
        if int(a["port"]) != (int(b["reg"], 16) & 3) or (
                a["val"].upper() != b["val"].upper()):
            raise ValueError("original/native port value mismatch at target")
    original_bounds = [(int(x["v"]), int(x["h"]), int(x["port"]),
                        x["val"].upper()) for x in original]
    native_bounds = [(int(x["frame"]), int(x["master"]), int(x["reg"], 16),
                      x["val"].upper()) for x in native]
    if ordinal == TARGET_ORDINAL:
        if tuple(original_bounds) != EXPECTED_ORIGINAL:
            raise ValueError("wrong immutable original RF037 target clock/port")
        if tuple(native_bounds) != EXPECTED_NATIVE:
            raise ValueError("wrong immutable native RF037 target clock/port")
    orig_gap = original_bounds[1][1] - original_bounds[0][1]
    nat_gap = native_bounds[1][1] - native_bounds[0][1]
    selected = [x for x in opcode_events
                if int(x.get("frame", "-1")) == 6091
                and int(x.get("v", "-1")) == 116
                and int(x["pre_h"]) <= original_bounds[1][1]
                and int(x["post_h"]) >= original_bounds[0][1]]
    selected.sort(key=lambda x: int(x["pre_h"]))
    brackets = [
        [x for x in selected if int(x["pre_h"]) <= h <= int(x["post_h"])]
        for _, h, _, _ in original_bounds]
    between = [x for x in paced_events
               if native_bounds[0][1] < int(x["master"]) <= native_bounds[1][1]
               and int(x.get("frame", "-1")) == native_bounds[0][0]]
    total_charge = sum(int(x["charge"]) for x in between)
    original_echo_cmp = [x for x in selected
                         if x.get("pc", "").upper() == "82:8301"
                         and x.get("opcode", "").upper() == "CD"
                         and original_bounds[0][1] < int(x["post_h"])
                         < original_bounds[1][1]]
    native_echo_bus_reads = [x for x in between
                             if x.get("op") in ("read8", "read16")
                             and x.get("addr", "").upper() == "2142"]
    return {
        "schema": "rf038-executed-source-writer-interval-v1",
        "ordinal": ordinal,
        "source_port_publications": original,
        "native_port_publications": native,
        "source_original_cpu_v_and_h": original_bounds,
        "native_host_and_master": native_bounds,
        "original_elapsed_master": orig_gap,
        "native_elapsed_master": nat_gap,
        "original_minus_native_master": orig_gap - nat_gap,
        "source_opcode_rows_overlapping_interval": selected,
        "original_executed_cmp_abs_82_8301_between_writes": {
            "count": len(original_echo_cmp),
            "post_h": [int(x["post_h"]) for x in original_echo_cmp],
            "opcodes": original_echo_cmp,
        },
        "native_paced_port2142_read_helper_rows_between_writes": {
            "count": len(native_echo_bus_reads),
            "rows": native_echo_bus_reads,
            "paced_helper_row_is_not_proven_65816_opcode_count": True,
        },
        # Compare counts only when executed original opcodes bracket both
        # actual writer clocks; absent opcode coverage is not zero polls.
        "source_minus_native_executed_port2142_poll_count": (
            len(original_echo_cmp) - len(native_echo_bus_reads)
            if brackets[0] and brackets[1] else None
        ),
        "native_observed_port2142_poll_spacing_master": [
            int(b["master"]) - int(a["master"])
            for a, b in zip(native_echo_bus_reads, native_echo_bus_reads[1:])
        ],
        "poll_count_delta_is_not_spc_receiver_timing_proof": True,
        "opcode_brackets_source_port_before_after": [
            {"count": len(x), "opcodes": x[:5]} for x in brackets],
        "original_opcode_both_port_clocks_covered": bool(brackets[0] and brackets[1]),
        "native_paced_bus_transfer_rows_between_writes": between,
        "native_paced_bus_master_charge_between_writes": total_charge,
        "native_interval_master_minus_logged_paced_charge": nat_gap-total_charge,
        "native_remaining_master_is_not_proven_AOT_block_const": True,
        "original_opcode_and_native_paced_rows_are_not_one_to_one_instructions": True,
        "receiver_read_equivalence_proven": False,
        "clock_fix_justified": False,
        "complete_usa_events_admitted": 0,
    }


def report(case_zip: Path, ordinal: int = TARGET_ORDINAL) -> dict:
    with zipfile.ZipFile(case_zip) as z:
        orig_writer = [f for tag, f in logs(z, ORIGINAL_LOG)
                       if tag == "QA01RF037ORIGCPU2"]
        native_writer = [f for tag, f in logs(z, NATIVE_LOG)
                         if tag == "QA01RF037NATIVEUP" and
                         f.get("kind") == "rtl-apu-enter"]
        original_ops, native_paced, truncated = [], [], []
        for path, tag, holder, sentinel in (
                (ORIGINAL_LOG, "QA01RF038ORIGOP", original_ops,
                 "QA01RF038ORIGOP_TRUNCATED"),
                (NATIVE_LOG, "QA01RF038NATIVEPACE", native_paced,
                 "QA01RF038NATIVEPACE_TRUNCATED")):
            with z.open(path) as raw:
                for line in raw:
                    txt = line.decode("utf8", errors="replace")
                    if txt.startswith(sentinel + " "):
                        truncated.append(sentinel)
                    e = parse_event(txt, tag)
                    if e:
                        holder.append(e)
        out = inspect(orig_writer, native_writer, original_ops, native_paced,
                      ordinal=ordinal, truncated=tuple(truncated))
    out["case_zip_sha256"] = hashlib.sha256(case_zip.read_bytes()).hexdigest()
    out["case_zip_file"] = case_zip.name
    out["original_opcode_total_observed"] = len(original_ops)
    out["native_paced_total_observed"] = len(native_paced)
    out["scope"] = ("Executed original/natively scoped bus evidence only. "
                    "No original/SPC receiver or full-game admission.")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip", type=Path)
    p.add_argument("--json-out", type=Path)
    args = p.parse_args()
    if not args.case_zip.is_file():
        p.error("missing case ZIP")
    data = json.dumps(report(args.case_zip), sort_keys=True, indent=2)+"\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(data, encoding="utf8")
    else:
        print(data, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
