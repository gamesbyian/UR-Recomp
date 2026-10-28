#!/usr/bin/env python3
"""RF094: inspect executed DSP writes in each *own* Bowl-relative time domain.

Never infer PCM/audio equivalence, cross-core clock conversion or a completed
event from matching DSP register bytes. Empty or unequal write streams are
recorded as adverse/unknown evidence rather than masked or fabricated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROW = re.compile(
    r"^QA01RF094(ORIG|NATIVE) seq=(\d+) frame=(\d+) "
    r"reg=([0-9A-F]{2}) val=([0-9A-F]{2}) spc_ticks=(\d+) "
    r"spc_next_pc=([0-9A-F]{4}) clock=(original_spc|native_spc)$"
)
WINDOW = {"ORIG": (6445, 6451, 6447, "original_spc"),
          "NATIVE": (6447, 6453, 6449, "native_spc")}

def audit(raw: bytes, side: str) -> dict:
    start, end, entry, clock = WINDOW[side]
    text = raw.decode("utf-8", errors="strict")
    if "QA01RF094" + side + "_TRUNCATED" in text:
        raise ValueError("RF094 " + side + " DSP observation truncated")
    rows = []
    for line in text.splitlines():
        if not line.startswith("QA01RF094" + side):
            continue
        m = ROW.fullmatch(line)
        if not m or m.group(1) != side or m.group(8) != clock:
            raise ValueError("RF094 malformed or cross-clock " + side + " row")
        seq, frame, reg, value, ticks = (int(m.group(i), base) for i, base in
                                         ((2, 10), (3, 10), (4, 16),
                                          (5, 16), (6, 10)))
        if (seq != len(rows) + 1 or not start <= frame <= end or reg >= 0x80
                or (rows and (frame < rows[-1]["frame"] or
                              ticks < rows[-1]["spc_ticks"]))):
            raise ValueError("RF094 impossible frame/seq/DSP/SPC chronology")
        rows.append({"frame": frame, "entry_offset": frame - entry,
                     "reg": reg, "value": value, "spc_ticks": ticks,
                     "spc_next_pc": int(m.group(7), 16)})
        if len(rows) > 16384:
            raise ValueError("RF094 DSP row budget exceeded")
    return {"log_sha256": hashlib.sha256(raw).hexdigest(),
            "clock": clock, "entry_frame": entry, "frame_window": [start, end],
            "executed_dsp_writes": len(rows), "first": rows[0] if rows else None,
            "last": rows[-1] if rows else None, "rows": rows,
            "no_dsp_write_observed": not rows}

def analyze(original: bytes, native: bytes) -> dict:
    orig = audit(original, "ORIG")
    nat = audit(native, "NATIVE")
    return {"schema": "ur-qa01-rf094-spc-dsp-followthrough/1",
            "original": orig, "native": nat,
            "same_ordered_register_values": (
                [(x["reg"], x["value"]) for x in orig["rows"]] ==
                [(x["reg"], x["value"]) for x in nat["rows"]]),
            "same_ordered_register_values_proves_audio_parity": False,
            "cross_core_clock_conversion_proven": False,
            "full_guest_event_admitted": False,
            "usa_event_credit": 0, "windows_release_gate_credit": 0}

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-log", type=Path, required=True)
    p.add_argument("--native-log", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    for path in (args.original_log, args.native_log):
        if not path.is_file() or path.is_symlink():
            p.error("actual non-symlinked replay log required")
    result = analyze(args.original_log.read_bytes(), args.native_log.read_bytes())
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("RF094 executed original/native DSP observations captured; "
          "PCM and event parity not proven.")

if __name__ == "__main__":
    main()
