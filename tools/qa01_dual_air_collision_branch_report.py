#!/usr/bin/env python3
"""QA-01: classify *actual original CPU* two-player contact-branch scopes.

Only the independently executed original Snes9x event trace can establish
instruction reaches, branch destinations and source scratch. Native helper
scope and host frame clocks are deliberately not claimed equivalent.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import instrument_snesref_2p_collision_gate as original

SCHEMA = "UR-QA01-ORIGINAL-2P-COLLISION-BRANCH-BOUNDARY/1"
LINE = re.compile(
    r"^QA01COLLBR pre_f=(\d+) post_f=(\d+) pre_v=(\d+) post_v=(\d+) "
    r"pc=([0-9A-F]{6}) next=([0-9A-F]{6}) "
    r"contact=([0-9A-F]{2})/([0-9A-F]{2}) "
    r"state=([0-9A-F]{4})/([0-9A-F]{4}) "
    r"seat=([0-9A-F]{4})/([0-9A-F]{4}) "
    r"y=([0-9A-F]{4})/([0-9A-F]{4}) "
    r"vy=([0-9A-F]{4})/([0-9A-F]{4})$")
BRANCHES = {
    0x81925A: {0x81925C: "fallthrough_on_negative", 0x81926E: "taken_on_nonnegative"},
    0x819266: {0x819268: "fallthrough_to_store", 0x81926B: "taken_skip_store"},
}
MAX_LOG = 15_000_000
MAX_SCOPE = 5000


def classify(log: str) -> dict:
    if len(log) > MAX_LOG:
        raise ValueError("original CPU trace exceeds budget")
    stamped = [line for line in log.splitlines() if line.startswith("QA01COLLBR")]
    if not stamped:
        raise ValueError("no bounded actual original collision opcode witnesses")
    if len(stamped) > MAX_SCOPE:
        raise ValueError("original collision opcode count exceeds receipt budget")
    frames = []
    prior = (2574, 0)
    for line in stamped:
        m = LINE.fullmatch(line)
        if not m:
            raise ValueError("malformed original source opcode branch receipt")
        f, post_f, v, post_v = map(int, m.group(1, 2, 3, 4))
        pc, nxt = (int(m.group(5), 16), int(m.group(6), 16))
        if (not 2574 <= f <= 2586 or not f <= post_f <= 2587
                or not 0 <= v <= 511 or not 0 <= post_v <= 511
                or (f, v) < prior):
            raise ValueError("original source CPU frame/scanline chronology invalid")
        if pc not in original.PCS or nxt < 0x810000 or nxt > 0x81FFFF:
            raise ValueError("original source opcode outside bounded source PC family")
        if pc in BRANCHES and nxt not in BRANCHES[pc]:
            raise ValueError("impossible original 65816 BPL next-PC")
        a = [int(m.group(i), 16) for i in range(7, 17)]
        contact_in, contact_out, state_in, state_out, seat_in, seat_out, y_in, y_out, vy_in, vy_out = a
        if (seat_in not in (0, 2) or seat_out != seat_in
                or pc == 0x81925A and contact_out != contact_in
                or pc in BRANCHES and state_out != state_in):
            raise ValueError("original collision branch scratch/seat changed during branch")
        # On the archived sequential 9253 SEP / 9255 8-bit LDA / 9258
        # REP / 925A BPL path, REP changes M but preserves the N flag set
        # by LDA. The BPL target must respect the sign of that source byte.
        if pc == 0x81925A and nxt != (
                0x81925C if contact_in & 0x80 else 0x81926E):
            raise ValueError("original collision sign and BPL destination disagree")
        # The opcode sets its own flags, but a BPL instruction itself cannot
        # mutate A or WRAM; do not infer N from a post-REP status byte.
        frames.append({
            "source_cpu_pre_frame": f,
            "source_cpu_post_frame": post_f,
            "source_vcounter_pre": v,
            "source_vcounter_post": post_v,
            "pc": f"{pc>>16:02X}:{pc&0xFFFF:04X}",
            "next_pc": f"{nxt>>16:02X}:{nxt&0xFFFF:04X}",
            "seat": seat_in,
            "contact_02c0_before_after": [contact_in, contact_out],
            "scratch_state_0f29_before_after": [state_in, state_out],
            "scratch_y_00a7_before_after": [y_in, y_out],
            "scratch_vy_0fa1_before_after": [vy_in, vy_out],
            "branch_result": BRANCHES[pc][nxt] if pc in BRANCHES else None,
        })
        prior = (f, v)
    branch = [x for x in frames if x["branch_result"]]
    counts = Counter((x["seat"], x["pc"], x["branch_result"]) for x in branch)
    return {
        "schema": SCHEMA,
        "original_cpu_scopes": frames,
        "branch_decisions_by_seat": [
            {"seat": seat, "source_pc": pc, "decision": decision, "count": count}
            for (seat, pc, decision), count in sorted(counts.items())
        ],
        "observed_bpl_seats": sorted({x["seat"] for x in branch}),
        "preserved_original_cpu_pre_post_frame_and_scanline": True,
        "native_helper_PC_or_beam_alignment_proven": False,
        "full_original_native_gameplay_causality_proven": False,
        "strict_complete_usa_release_credit": 0,
        "interpretation": (
            "Source Snes9x actual PC and next PC can reveal original BPL "
            "decision at 81:925A or 81:9266. No original/native clock "
            "or pre-P1 native contact equality follows without an independent "
            "native branch/scratch observer."),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-log", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    report = classify(args.original_log.read_text(encoding="utf-8", errors="replace"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "original_cpu_scopes": len(report["original_cpu_scopes"]),
        "actual_bpl_seats": report["observed_bpl_seats"],
        "release_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
