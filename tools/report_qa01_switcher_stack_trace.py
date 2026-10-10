#!/usr/bin/env python3
"""Adjudicate bounded original-only Switcher stack opcode observations.

The instrumented Snes9x replay must preserve the *entire* original guest
source-horizon and source-entry WRAM snapshots and source-event identity.
An opcode-scope write is not necessarily a CPU stack push: synchronous
emulator side effects and ordinary direct RAM stores remain possibilities.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

BEGIN = re.compile(
    r"^QASTACKBEGIN f=(\d+) v=(\d+) pc=([0-9A-F]{6}) sp=([0-9A-F]{4})$",
    re.MULTILINE,
)
WRITE = re.compile(
    r"^QASTACKWRITE f=(\d+) v=(\d+) pc=([0-9A-F]{6}) op=([0-9A-F]{2}) "
    r"sp0=([0-9A-F]{4}) sp1=([0-9A-F]{4}) addr=([0-9A-F]{4}) "
    r"old=([0-9A-F]{2}) new=([0-9A-F]{2})$",
    re.MULTILINE,
)
TARGETS = {0x01DD, 0x01E6, 0x01E7, 0x01EF, 0x01F0, 0x01F1, 0x01F2, 0x01F3}
# Canonical 65816 opcodes that directly initiate stack pushes or subroutine
# return-address pushes; classification is only a lead, never a writer proof.
# Candidate widths follow the documented 65816 push instructions;
# PHA/PHX/PHY depend on active M/X width, which this trace does not sample.
# These tests are consistency screens, never verified writer attribution.
PUSH_WIDTHS = {
    0x08: (1,), 0x0B: (2,), 0x20: (2,), 0x22: (3,),
    0x48: (1, 2), 0x4B: (1,), 0x5A: (1, 2),
    0x62: (2,), 0x8B: (1,), 0xD4: (2,),
    0xDA: (1, 2), 0xF4: (2,), 0xFC: (2,),
}


def stack_push_compatible(opcode: int, sp_before: int, sp_after: int,
                          address: int) -> bool:
    """Possible CPU stack push, including 8/16-bit register-width variants.

    A post-opcode byte delta can instead arise from a synchronous side
    effect. This predicate cannot prove the writer instruction or intent.
    """
    return any(
        sp_after == (sp_before - width) & 0xFFFF and
        address in {((sp_before - n) & 0xFFFF) for n in range(width)}
        for width in PUSH_WIDTHS.get(opcode, ())
    )
SCHEMA = "UR-QA01-SWITCHER-ORIGINAL-STACK-OPCODE-TRACE/1"
LIMIT = 5000


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_replay(baseline: Path, replay: Path) -> dict:
    a = json.loads(baseline.read_text(encoding="utf-8"))
    b = json.loads(replay.read_text(encoding="utf-8"))
    if a.get("schema") != "UR-QA01-ORIGINAL-SWITCHER-SOURCE-QUALIFICATION/1":
        raise ValueError("baseline is not an original Switcher qualification")
    for source in (a, b):
        if (source.get("schema") != a["schema"]
                or source.get("status") != "source_event_and_entry_verified"
                or source.get("release_complete_event_credit") != 0
                or source.get("original_source_horizon_frames") != 22000
                or source.get("source_result", {}).get("original_result_frame") is None):
            raise ValueError("missing genuine bounded original source event")
    for name in ("rom_sha256", "archived_movie_sha256", "source_sram_sha256",
                 "source_result", "source_event_diagnostic",
                 "original_source_horizon_frames"):
        if a[name] != b[name]:
            raise ValueError(f"disposable original instrumentation changed {name}")
    if a["original_core_sha256"] == b["original_core_sha256"]:
        raise ValueError("expected independently rebuilt instrumented original core")
    result = a["source_result"]["original_result_frame"]
    if type(result) is not int or not 100 < result < 22000:
        raise ValueError("invalid independent source result host frame")
    base_dir = baseline.parent / "source-switcher" / "source"
    replay_dir = replay.parent / "source-switcher" / "source"
    matched = {}
    for name in ("source-race-entered.wram.bin", "source-horizon.wram.bin"):
        p, q = base_dir / name, replay_dir / name
        if p.stat().st_size != 131072 or q.stat().st_size != 131072:
            raise ValueError(f"invalid 128-KiB original WRAM dump: {name}")
        before, after = file_hash(p), file_hash(q)
        if before != after:
            raise ValueError(f"instrumented original changed source WRAM: {name}")
        matched[name] = before
    return {
        "source_result_frame": result,
        "rom_sha256": a["rom_sha256"],
        "archived_movie_sha256": a["archived_movie_sha256"],
        "source_sram_sha256": a["source_sram_sha256"],
        "original_core_sha256": a["original_core_sha256"],
        "instrumented_core_sha256": b["original_core_sha256"],
        "unchanged_original_wram_sha256": matched,
    }


def parse_trace(log: str, source_result_frame: int) -> dict:
    if type(source_result_frame) is not int or source_result_frame <= 20:
        raise ValueError("need independently observed original result frame")
    begins = list(BEGIN.finditer(log))
    if len(begins) != 1:
        raise ValueError(f"expected one instrumented CPU gate entry, found {len(begins)}")
    first, vcounter, begin_pc, sp = begins[0].groups()
    first = int(first)
    if abs(first - (source_result_frame - 16)) > 2:
        raise ValueError("instrumented CPU frame not aligned with original result")
    if not 0 <= int(vcounter) < 263:
        raise ValueError("invalid SNES PPU V-counter")
    rows = []
    matches = list(WRITE.finditer(log))
    if len(matches) > LIMIT:
        raise ValueError("bounded stack write trace exceeded cap")
    for entry in matches:
        f, v, pc, op, sp0, sp1, addr, old, new = entry.groups()
        frame, addr_num, opcode = int(f), int(addr, 16), int(op, 16)
        if (addr_num not in TARGETS or not first <= frame <= source_result_frame + 5
                or not 0 <= int(v) < 263 or old == new):
            raise ValueError("unrecognized opcode-scope WRAM difference")
        rows.append({
            "icpu_frame": frame,
            "ppu_vcounter": int(v),
            "original_pc": f"{pc[:2]}:{pc[2:]}",
            "opcode": op,
            "sp_before": sp0,
            "sp_after": sp1,
            "wram_address": f"7E:{addr}",
            "old": old,
            "new": new,
            "push_opcode_candidate": opcode in PUSH_WIDTHS,
            "stack_pointer_address_compatible": stack_push_compatible(
                opcode, int(sp0, 16), int(sp1, 16), addr_num),
        })
    if [r["icpu_frame"] for r in rows] != sorted(r["icpu_frame"] for r in rows):
        raise ValueError("original opcode observations not chronological")
    by_pc = Counter(row["original_pc"] for row in rows)
    by_address = Counter(row["wram_address"] for row in rows)
    return {
        "schema": SCHEMA,
        "original_source_result_host_frame": source_result_frame,
        "observed_cpu_gate": {
            "icpu_frame": first,
            "ppu_vcounter": int(vcounter),
            "pc": f"{begin_pc[:2]}:{begin_pc[2:]}",
            "sp": sp,
        },
        "opcode_scope_events": rows,
        "event_count": len(rows),
        "pc_counts": dict(sorted(by_pc.items())),
        "address_counts": dict(sorted(by_address.items())),
        "untouched_targets": [
            f"7E:{addr:04X}" for addr in sorted(TARGETS)
            if f"7E:{addr:04X}" not in by_address
        ],
        "all_observations_within_bounded_original_window": True,
        "cpu_stack_hypothesis_only": True,
        "interpretation": (
            "Addresses lie in the conventional 65816 stack page, but the exact "
            "guest original store and subsequent read/consumer semantics are "
            "NOT established merely by an opcode-scoped pre/post byte change. "
            "SP-before/after, opcode and push-width/address consistency provide discriminators, NOT instruction attribution. No native "
            "instruction/phase comparison was performed."
        ),
        "complete_event_release_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--original-report", type=Path, required=True)
    ap.add_argument("--instrumented-report", type=Path, required=True)
    ap.add_argument("--opcode-log", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    provenance = verify_replay(args.original_report, args.instrumented_report)
    scope = parse_trace(args.opcode_log.read_text(encoding="utf-8"),
                        provenance["source_result_frame"])
    scope["provenance"] = provenance
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(scope, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_result_frame": provenance["source_result_frame"],
        "opcode_scopes": scope["event_count"],
        "address_counts": scope["address_counts"],
        "complete_event_release_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
