#!/usr/bin/env python3
"""Readiness gate for RF045/RF047 raw logs before QA01 causal-window admission.

Examines ACTUAL original/native recorder streams without making up a PC,
writer, checkpoint, clock offset or missing event. Deliberately does not turn
legacy RF054 evidence into qa01_causal_window input: the two separate recorder
ordinals and actual raw checkpoint bytes do not share a single bus timeline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

import qa01_causal_window as causal

SOURCE = "work/zoom-zoo/replay/reference.log"
NATIVE = "work/zoom-zoo/replay/native.log"
SOURCE_TAG = "QA01RF045ORIGSTACK "
NATIVE_TAG = "QA01RF047NATIVE "
LATE_TAG = "QA01RF047NATIVEPC "
SEQ = re.compile(r"(?:^| )seq=(\d+)(?: |$)")
PC = re.compile(r"[0-9A-F]{6}\Z")


def rows(text: str, tag: str) -> list[dict]:
    result = []
    for line in text.splitlines():
        # Existing native WRAM writer stdout/stderr fragments can precede
        # an RF047 atomic line; they do not establish guest instruction order.
        pos = line.find(tag)
        if pos < 0:
            continue
        d = {}
        for chunk in line[pos + len(tag):].split():
            if "=" in chunk:
                k, value = chunk.split("=", 1)
                d[k] = value
        result.append(d)
    return result


def contiguous(events: list[dict], label: str) -> bool:
    seq = [e.get("seq") for e in events]
    if not seq:
        return False
    if any(x is None for x in seq):
        if any(x is not None for x in seq):
            raise ValueError(label + ": partially missing ordinals")
        return False
    try:
        values = [int(x) for x in seq]
    except ValueError as exc:
        raise ValueError(label + ": malformed ordinal") from exc
    if sorted(values) != list(range(1, len(events) + 1)):
        raise ValueError(label + ": ordinal gap/duplicate/overflow")
    return True


def inspect(source: str, native: str) -> dict:
    for marker in ("QA01RF045ORIGSTACK_TRUNCATED",
                   "QA01RF044ORIGBUS_TRUNCATED"):
        if marker in source:
            raise ValueError("original recorder truncated: " + marker)
    for marker in ("QA01RF047NATIVE_TRUNCATED",
                   "QA01RF047NATIVEPC_TRUNCATED"):
        if marker in native:
            raise ValueError("native recorder truncated: " + marker)

    macros = rows(source, SOURCE_TAG)
    bus = rows(source, "QA01RF044ORIGBUS ")
    nmis = rows(source, "QA01RF044ORIGNMI ")
    events = rows(native, NATIVE_TAG)
    late = rows(native, LATE_TAG)
    orig_seq = contiguous(macros, "original RF045 macro")
    native_seq = contiguous(events, "native RF047 NMI/read/opcode")
    late_seq = contiguous(late, "native RF047 late-PC")

    for event in events:
        if event.get("stage") == "opcode":
            if not PC.fullmatch(event.get("guestPC", "")) or event.get("tier") not in ("aot", "interp"):
                raise ValueError("native executed opcode marker incomplete")
        elif event.get("stage") == "read":
            # Most RF047 authentic reader rows presently lack guestPC.
            # A hint from g_interp816_cur_pc is NOT proof of executed code.
            if "guestPC" in event and (not PC.fullmatch(event["guestPC"]) or
                                        event.get("pcEvidence") != "executed"):
                raise ValueError("native reader PC has no executed proof")
    for event in late:
        if not PC.fullmatch(event.get("guestPC", "")) or event.get("tier") not in ("aot", "interp"):
            raise ValueError("late native executed PC marker incomplete")

    # Avoid pretending that source macro ordinals order RF044 getset writes,
    # that an NMI entry is the producer's full-WRAM snapshot checkpoint, or
    # that source CPU beam/VH is the native CPU master clock.
    native_reads = [x for x in events if x.get("stage") == "read"]
    native_proved_read_pcs = sum(
        x.get("pcEvidence") == "executed" and PC.fullmatch(x.get("guestPC", ""))
        for x in native_reads)
    return {
        "schema": "ur-qa01-rf045-rf047-raw-readiness/1",
        "consumer_schema": causal.SCHEMA,
        "original_macro_records": len(macros),
        "original_macro_local_seq_contiguous": orig_seq,
        "original_bus_records_without_shared_ordinal": len(bus),
        "original_nmi_markers_without_snapshot_phase_ordinal": len(nmis),
        "native_rf047_rows": len(events),
        "native_rf047_seq_contiguous": native_seq,
        "native_actual_opcode_pc_markers": sum(x.get("stage") == "opcode" for x in events),
        "native_late_opcode_pc_markers": len(late),
        "native_late_pc_seq_contiguous": late_seq,
        "native_actual_bus_reads": len(native_reads),
        "native_reads_with_executed_guest_pc": native_proved_read_pcs,
        "original_shared_bus_checkpoint_seq_proven": False,
        "checkpoint_unmasked_actual_raw_bytes_reopened": False,
        "native_bus_pc_instruction_lifetime_proven": False,
        "original_native_clock_offsets_inferred": False,
        "eligible_for_causal_window_assess": False,
        "accepted_USA_events": 0,
        "next_discriminator": (
            "Produce one shared original read/write/checkpoint ordinal and a "
            "true native opcode-to-helper read correlation on the same immutable "
            "source-authentic bounded Zoom Zoo replay; retain unmasked raw "
            "checkpoint images and independently re-open them."
        ),
    }


def from_case(path: Path) -> dict:
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as z:
        if SOURCE not in z.namelist() or NATIVE not in z.namelist():
            raise ValueError("real source/native replay logs missing from case")
        a, b = z.read(SOURCE), z.read(NATIVE)
    result = inspect(a.decode("utf8"), b.decode("utf8"))
    result.update({
        "case_zip_sha256": hashlib.sha256(raw).hexdigest(),
        "original_log_sha256": hashlib.sha256(a).hexdigest(),
        "native_log_sha256": hashlib.sha256(b).hexdigest(),
        "source_identity_independently_authenticated": False,
    })
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip", type=Path, help="actual immutable original/native Zoo case archive")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    report = from_case(args.case_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("RF045/RF047 raw readiness HOLD: never fabricate causal-window rows")


if __name__ == "__main__":
    main()
