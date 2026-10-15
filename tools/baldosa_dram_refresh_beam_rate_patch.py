#!/usr/bin/env python3
"""Charge Baldosa's DRAM refresh once per 1364-clock beam line (RF-015).

The pinned Baldosa framework (``baldosa/snesrecomp@075fbe4``, still unchanged
upstream at ``ec8a3e7``) taxes 40 master clocks per 1364 clocks of CPU
*execution* in ``runner/src/common_cpu_infra.c::snes_refresh_charge``: after
adding the tax it moves the watermark past the stall, so the stall never counts
toward the next line. Hardware refreshes once per 1364-clock scanline with the
stall inside that line, so the pinned runtime gives a CPU-bound guest ~1.14
extra master clocks per line (0.086%).

On the original USA ROM that surplus is decisive for the CPU-driven result
screen upload ``82:B1D8``: Snes9x and bsnes reach the post-load two-edge wait
``80:FAC9`` at V=230 and wait a whole extra field; the pinned runtime arrives
at V=224, passes both edges in the same field and ends the raw ``0x84`` result
phase after 33 frames instead of 34 (RF-015).

This stages the one-line correction into a DISPOSABLE pinned Baldosa
checkout: keep the watermark before the stall so the next delta counts it.
The per-instruction cost model, park/exempt path, teleport guard and rollback
accessors are untouched. Idempotent; refuses any other framework revision.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_DRAM_REFRESH_BEAM_RATE"
RELATIVE = Path("snesrecomp/runner/src/common_cpu_infra.c")

PINNED = """  if (lines) {
    s_refresh_phase -= lines * 1364u;
    g_cpu.master_cycles += 40u * lines;
  }
  g_refresh_charged_upto = g_cpu.master_cycles;
}
"""

CORRECTED = """  if (lines) {
    s_refresh_phase -= lines * 1364u;
    g_cpu.master_cycles += 40u * lines;
  }
  /* """ + MARK + """: the stall is beam time too. Hardware
   * refreshes once per 1364-clock scanline with the 40 clocks inside it;
   * moving the watermark past the stall charged once per 1364 clocks of
   * execution (1404 of beam time). Keep the watermark before the stall so
   * the next delta counts it toward the next line. */
  g_refresh_charged_upto = m;
}
"""

# The function head the correction depends on: ``m`` is the entry clock.
HEAD = """void snes_refresh_charge(void) {
  uint64_t m = g_cpu.master_cycles;
"""


def patch(source: str) -> str:
    if MARK in source:
        if source.count(CORRECTED) != 1:
            raise ValueError("refresh beam-rate marker present but correction altered")
        return source
    if source.count(HEAD) != 1 or source.count(PINNED) != 1:
        raise ValueError("pinned Baldosa DRAM refresh charge not recognized; "
                         "do not splice against an unknown framework revision")
    if source.index(HEAD) > source.index(PINNED):
        raise ValueError("refresh charge body is not inside snes_refresh_charge")
    return source.replace(PINNED, CORRECTED, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", required=True, type=Path,
                    help="disposable gamesbyian/uniracers-recomp checkout")
    args = ap.parse_args()
    path = args.game.resolve() / RELATIVE
    before = path.read_text(encoding="utf-8")
    after = patch(before)
    if after == before:
        print(f"already staged: {path}")
    else:
        path.write_text(after, encoding="utf-8")
        print(f"staged DRAM refresh beam-rate correction: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
