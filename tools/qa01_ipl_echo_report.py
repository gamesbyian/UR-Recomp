#!/usr/bin/env python3
"""Qualify executed original/native IPL port read, echo and CPU transport logs.

Each emulator retains its OWN SPC age and CPU/beam/frame clock. This does not
infer equality of source and native phase, clock domains, or full-event parity.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

SCHEMA = "UR-QA01-RF030-EXECUTED-IPLCMP-ECHO-PHASE/1"
ORG = "QA01IPLORIG "
NAT = "QA01IPLNATIVE "
ORIG_KEYS = {"side", "kind", "frame", "v", "h", "age", "pc", "op", "value", "ipl"}
NATIVE_KEYS = {"kind", "age", "pc", "value", "q", "in", "out"}
HEX = {"pc", "op", "value", "in", "out"}
MAX_LINES = 4000


def scan(raw: str, prefix: str, required: set[str], allowed: dict[str, set[str]]) -> list[dict]:
    if prefix.rstrip() + "_TRUNCATED" in raw or prefix.rstrip() + "_CPU_TRUNCATED" in raw:
        raise ValueError("bounded IPL tracing exhausted; cannot infer handshake chronology")
    out = []
    for line in raw.splitlines():
        if not line.startswith(prefix):
            continue
        parsed = {}
        for word in line[len(prefix):].split():
            if "=" not in word:
                raise ValueError("malformed IPL key/value field")
            key, value = word.split("=", 1)
            if key in parsed or key not in required or not value:
                raise ValueError("unknown/duplicate/empty IPL field")
            if key in allowed:
                if value not in allowed[key]:
                    raise ValueError(f"unrecognized IPL {key}")
                parsed[key] = value
                continue
            base = 16 if key in HEX else 10
            if not re.fullmatch("[0-9A-F]+" if base == 16 else "[0-9]+", value):
                raise ValueError("malformed IPL numeric field")
            parsed[key] = int(value, base)
        if set(parsed) != required:
            raise ValueError("missing executed IPL trace fields")
        out.append(parsed)
        if len(out) > MAX_LINES:
            raise ValueError("unbounded IPL logs")
    if not out:
        raise ValueError("no genuine source-qualified IPL events for " + prefix)
    if [x["age"] for x in out] != sorted(x["age"] for x in out):
        raise ValueError("IPL events reordered within one emulated SPC clock")
    return out


def first(rows: list[dict], kind: str, value: int) -> dict | None:
    return next((x for x in rows if x["kind"] == kind and x["value"] == value), None)


def summarize(raw_original: str, raw_native: str) -> dict:
    orig = scan(raw_original, ORG, ORIG_KEYS,
                {"side": {"cpu", "spc"}, "kind": {"read", "echo", "poll", "write"}})
    native = scan(raw_native, NAT, NATIVE_KEYS,
                  {"kind": {"read", "echo", "apply", "schedule"}})
    if any(x["frame"] != 0 or
           x["age"] < 103300000 or x["age"] > 103345000 or
           x["v"] > 262 or x["h"] > 1500 or x["ipl"] not in (0, 1)
           for x in orig):
        raise ValueError("original trace outside independently calibrated Zoo SPC age window")
    if any(x["age"] < 103300000 or x["age"] > 103345000 or
           x["q"] > 1024 for x in native):
        raise ValueError("native trace outside bounded RF-028 SPC age")
    reads = [x for x in orig if x["side"] == "spc" and x["kind"] == "read"]
    echoes = [x for x in orig if x["side"] == "spc" and x["kind"] == "echo"]
    nreads = [x for x in native if x["kind"] == "read"]
    nechoes = [x for x in native if x["kind"] == "echo"]
    origcc, origread, origecho = (first(orig, "write", 0xcc),
                               first(reads, "read", 0xcc),
                               first(echoes, "echo", 0xcc))
    natapply, natread, natecho = (first(native, "apply", 0xcc),
                                 first(nreads, "read", 0xcc),
                                 first(nechoes, "echo", 0xcc))
    if any(x is None for x in (origcc, origread, origecho,
                                natapply, natread, natecho)):
        raise ValueError("missing actual CC write, SPC ready read or SPC echo")
    if not (origcc["age"] <= origread["age"] <= origecho["age"] and
            natapply["age"] <= natread["age"] <= natecho["age"]):
        raise ValueError("ready-echo chronology violates own executed clocks")
    if not any(x["side"] == "cpu" and x["kind"] == "poll" for x in orig):
        raise ValueError("missing original CPU $2140 poll")
    if not any(x["kind"] == "schedule" and x["value"] == 0xcc for x in native):
        raise ValueError("missing timestamped native CPU $2140 scheduling")
    if not any(x["side"] == "spc" and x["kind"] == "read" and
               x["op"] == 0x78 and x["pc"] == 0xffd2 for x in orig):
        raise ValueError("Snes9x original IPL $F4 compare instruction unproven")
    if not any(x["kind"] == "read" and x["pc"] == 0xffd2 for x in native):
        raise ValueError("Baldosa IPL compare PC unproven")
    return {
        "schema": SCHEMA,
        "source_and_native_clocks_distinct": True,
        "original_executed_events": len(orig),
        "native_executed_events": len(native),
        "original_spc_read_count": len(reads),
        "original_spc_echo_count": len(echoes),
        "native_spc_read_count": len(nreads),
        "native_spc_echo_count": len(nechoes),
        "original_ipl_first_cc": {
            "cpu_write_age": origcc["age"], "spc_read_age": origread["age"],
            "spc_echo_age": origecho["age"],
            "write_to_read_spc_cycles": origread["age"] - origcc["age"],
            "read_to_echo_spc_cycles": origecho["age"] - origread["age"],
            "original_cpu_frame_at_write": origcc["frame"],
            "original_cpu_beam_v_h_at_write": [origcc["v"], origcc["h"]],
            "first_read_pc": f"{origread['pc']:04X}",
            "first_read_opcode": f"{origread['op']:02X}",
        },
        "native_ipl_first_cc": {
            "cpu_applied_age": natapply["age"], "spc_read_age": natread["age"],
            "spc_echo_age": natecho["age"],
            "apply_to_read_spc_cycles": natread["age"] - natapply["age"],
            "read_to_echo_spc_cycles": natecho["age"] - natread["age"],
            "first_read_pc": f"{natread['pc']:04X}",
        },
        "original_native_independent_clock_phase_aligned": False,
        "all_unsampled_original_native_logic_ticks_proven": False,
        "spc_sound_audio_samples_equivalent_proven": False,
        "release_complete_usa_event_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-log", type=Path, required=True)
    p.add_argument("--native-log", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error("refuse to overwrite exact existing executed IPL receipt")
    result = summarize(a.original_log.read_text(encoding="utf-8"),
                       a.native_log.read_text(encoding="utf-8"))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",
                     encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
