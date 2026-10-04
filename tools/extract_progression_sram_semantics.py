#!/usr/bin/env python3
"""Verify the decoded progression/stat SRAM semantics against the canonical ROM.

Decision served: modern save UX (tour resume, Player Scores, VS tally) must read
and write the stock battery fields with their stock meaning
(analysis/frontend-modernization-policy.json, ``unfinished-tour-session-loss``).

Each claim is pinned to the exact instruction bytes it was decoded from
(Nitrodon bank 80/83 listings, cross-checked against the USA retail ROM), so a
wrong ROM or a misread routine fails loudly instead of drifting silently.
Runtime corroboration lives in tools/probe_tour_progress_persistence.py
(tour flags) and R-2026-10-03-UI-19 (rider 0 stats). ``--vs-sram`` checks a battery
dump taken after the VS route ``tests/input/two-player-p1-win.input`` (dual-controller
snesref, ``wait 38200`` then ``press a 2`` / ``wait 130`` / dump), where P1 finishes
and the idle P2 times out.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"

# (bank, address, hex bytes, what the bytes establish)
SIGNATURES = {
    "stats_offset_is_rider_times_8": (0x80, 0xC776, "c220af48077729ff000a0a0a8f3e0777af49077729ff000a0a0a8f400777",
        "0x073E = 8 * P1 rider (0x0748), 0x0740 = 8 * P2 rider (0x0749)"),
    "played_is_offset_0": (0x80, 0xCA63, "af3e0777aabf3002771a9f30027760", "INC 0x0230 + offset"),
    "won_is_offset_2_and_bumps_vs_tally": (0x80, 0xCA72, "af3e0777aabf3202771a9f320277afa910771a8fa9107760",
        "INC 0x0232 + offset, then INC 0x10A9 (P1 side; P2 uses 0x10AB at 80:CAB4)"),
    "failed_is_offset_4": (0x80, 0xCA8A, "af3e0777aabf3402771a9f34027760",
        "INC 0x0234 + offset; called when the loser's time/best lap is >= 60000 (80:C7EF, 80:C8D7)"),
    "player_scores_reads_16_riders": (0x83, 0x97DA, "a20000a00f00bf300277cd3f0190038d3f0138ff320277",
        "X=0, Y=15 loop over 0x0230,X; LOST = PLAYED - WON (SBC 0x0232,X), not stored"),
    "player_scores_stride_8": (0x83, 0x985B, "8a18690800aa883003", "X += 8 per rider"),
    "tour_flag_set_and_row_sum": (0x83, 0x87F5,
        "22c89e83a9019f751077a90022d59e83a00400187f751077e88810f7c905b00622f49083286b",
        "0x1075 + $CE = 1, sum 0x1075 + 5*$D0 .. +4, >= 5 -> medal award at 83:881B"),
    "tour_award_clears_row": (0x83, 0x895B, "08e220a90022d59e83a004009f751077e88810f82860",
        "zero 0x1075 + 5*$D0 .. +4"),
    "rider_confirm_wipes_all_tour_flags": (0x80, 0xBBC1, "a900a03100bb9f7510778810f8",
        "zero 0x1075 .. 0x10A6 (50 bytes) on 1P rider confirm"),
    "tour_confirm_snapshots_medal": (0x80, 0xE6B7, "22b49e83bf9c06778fd11077",
        "0x10D1 = medal cell (16*$D0 + rider) when the tour is confirmed"),
    "vs_entry_resets_tally_and_sets_mode": (0x80, 0xBD05, "c220a900008fa910778fab1077a902008fad1077",
        "0x10A9 = 0x10AB = 0, 0x10AD = 2 on VS entry (1P tour entry writes 0x10AD = 1 at 80:BBD6)"),
}

LAYOUT = {
    "rider_stats": {"base": "0x0230", "stride": 8, "count": 16, "index": "rider 0..15",
                    "fields": {"+0": "PLAYED", "+2": "WON", "+4": "FAILED (did not finish: time or best lap >= 60000)",
                               "+6": "SCORE (cumulative stunt points)"},
                    "derived": "LOST = PLAYED - WON; screen percentages are count*100/PLAYED",
                    "counted": "P1 always; P2 only when its rider index (0x0749) < 16, so CPU opponents are not counted"},
    "tour_flags": {"base": "0x1075", "size": 50, "index": "5*tour_row + track",
                   "set": "qualifying 1P result", "cleared": "row on medal award; all on rider confirm"},
    "tour_medal_snapshot": {"offset": "0x10D1", "meaning": "medal cell at tour confirm; drives the run label and the keep-row test on leaving TRACK_SELECT"},
    "play_mode": {"offset": "0x10AD", "values": {"0": "none / exited", "1": "1P tour", "2": "VS"}},
    "vs_tally": {"offsets": ["0x10A9", "0x10AB"], "meaning": "P1 / P2 win counts, zeroed on VS entry and shown on VS track select; 0x10A9 also counts 1P wins harmlessly"},
}


def lorom(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


def analyze(rom: bytes) -> dict:
    checks, evidence = {}, {}
    for name, (bank, addr, hexbytes, meaning) in SIGNATURES.items():
        want = bytes.fromhex(hexbytes)
        start = lorom(bank, addr)
        checks[name] = rom[start:start + len(want)] == want
        evidence[name] = {"at": f"{bank:02X}:{addr:04X}", "meaning": meaning}
    return {
        "schema_version": 1,
        "purpose": "Stock meaning of progression and rider-stat battery fields for modern save UX.",
        "rom": "reference/roms/retail/Uniracers_USA.sfc",
        "layout": LAYOUT,
        "evidence": evidence,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def word(sram: bytes, offset: int) -> int:
    return sram[offset] | sram[offset + 1] << 8


def rider_stats(sram: bytes, rider: int) -> list[int]:
    return [word(sram, 0x0230 + 8 * rider + 2 * i) for i in range(4)]


def vs_runtime(sram: bytes) -> dict:
    p1, p2 = sram[0x0748], sram[0x0749]
    return {
        "vs_p1_winner_counts_played_and_won": rider_stats(sram, p1) == [1, 1, 0, 0],
        "vs_p2_timeout_counts_played_and_failed": word(sram, 0x061A) == 60000 and rider_stats(sram, p2) == [1, 0, 1, 0],
        "vs_tally_and_mode": (word(sram, 0x10A9), word(sram, 0x10AB), sram[0x10AD]) == (1, 0, 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rom", type=Path, default=ROM)
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/progression-sram-semantics.json")
    ap.add_argument("--vs-sram", type=Path, help="battery dump after the two-player-p1-win VS route (clean save)")
    args = ap.parse_args()
    report = analyze(args.rom.read_bytes())
    if args.vs_sram:
        runtime = vs_runtime(args.vs_sram.read_bytes())
        report["runtime_checks"] = runtime
        report["checks"].update(runtime)
        report["all_checks_pass"] = all(report["checks"].values())
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report["checks"], indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
