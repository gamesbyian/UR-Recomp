#!/usr/bin/env python3
"""Make Baldosa's SPC timeline track the hardware beam exactly (RF-023, RF-024).

RF-023 (dominant): ``rtl_apu_clock_finish`` clamps every host iteration to at
least one 357,368-clock field ("WAI still advances a hardware frame"). Native
CPU iterations overshoot the field boundary by a varying amount, so the next
iteration is often shorter than a field and gets clamped up, while the CPU
clock is not: the SPC timeline gains ~35 master clocks per field on the CPU
(measured +38,530 over 1,098 attract fields), ~0.01% fast, ~6,700 SPC cycles
over 4,000 fields. The beam driver already advances parked/WAI time
explicitly (``advance_parked``), so the clamp is removed: the SPC timeline
follows the CPU master clock exactly.

RF-024: the NTSC short scanline, below.

Hardware NTSC fields alternate 357,368 and 357,364 master clocks: on every
other non-interlaced field scanline 240 is 1,360 clocks instead of 1,364
(bsnes ``PPUcounter::tickScanline``). The pinned Baldosa beam always uses
1,364-clock lines, so every native field is 357,368 clocks, 2 more than the
hardware average. The CPU is frame-locked, so this does not move CPU work
inside a field; but the SPC700 runs on the master clock, so its timeline
gains 2 master clocks per field against the CPU's fields: ~380 SPC cycles over
the ~4,000 fields between two sound-driver restarts. The driver's timer phase
relative to the CPU then decides SPC-reset handshakes one timer tick apart
(RF-020: 2P seed 50048000, 1P Dragster).

This stages, into a DISPOSABLE pinned Baldosa checkout that already carries
the RF-016 reference-rate header, both corrections, confined to the APU frame
clock: on alternate fields the SPC timeline pauses for 4 master clocks
at the end of scanline 240 (it never runs backwards), and the RF-023 one-field
minimum is removed. A host iteration spanning many fields (an
NMI-disabled loader) pays one pause per odd field it crosses. The beam, CPU,
DMA/HDMA and IRQ timing are untouched. Idempotent; requires RF-016 staged.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_SPC_FRAME_CLOCK"
RF016_MARK = "UR_BALDOSA_SPC_REFERENCE_RATE"
HEADER = Path("snesrecomp/runner/src/apu_frame_clock.h")

PINNED_STRUCT = """typedef struct RtlApuFrameClock {
  uint64_t start_master, start_guest, next_guest, last_duration;
  uint64_t start_timeline, next_timeline, last_master_duration;
} RtlApuFrameClock;
"""

CORRECTED_STRUCT = """typedef struct RtlApuFrameClock {
  uint64_t start_master, start_guest, next_guest, last_duration;
  uint64_t start_timeline, next_timeline, last_master_duration;
  uint64_t field_parity; /* """ + MARK + """: parity of the field at start */
} RtlApuFrameClock;

/* """ + MARK + """ (RF-024): NTSC hardware shortens scanline 240 to
 * 1,360 clocks on every other non-interlaced field, so fields alternate
 * 357,368 and 357,364 master clocks. The beam here keeps 1,364-clock lines;
 * the SPC timeline instead pauses 4 clocks at the end of line 240 on odd
 * fields, so the SPC sees the hardware field lengths against the CPU's
 * frame-locked fields. Offsets are from the field start at V=225. */
#define RTL_SHORT_LINE_END ((241ull - 225ull) * 1364ull - 4ull)

static inline uint64_t rtl_apu_short_line_pause(uint64_t parity, uint64_t within) {
  uint64_t paused = 0;
  for (uint64_t k = 0;; k++) {
    uint64_t at = k * RTL_MASTER_CYCLES_PER_FRAME + RTL_SHORT_LINE_END;
    if (within <= at) break;
    if ((parity + k) & 1) {
      uint64_t d = within - at;
      paused += d < 4 ? d : 4;
    }
  }
  return paused;
}
"""

PINNED_TIMELINE = """  uint64_t within = master >= clock->start_master ? master - clock->start_master : 0;
  return clock->start_timeline + within;
}
"""

CORRECTED_TIMELINE = """  uint64_t within = master >= clock->start_master ? master - clock->start_master : 0;
  return clock->start_timeline + within -
         rtl_apu_short_line_pause(clock->field_parity, within);
}
"""

PINNED_FINISH = """  uint64_t end = rtl_apu_clock_timeline(clock, master);
  uint64_t minimum = clock->start_timeline + RTL_MASTER_CYCLES_PER_FRAME;
  if (end < minimum) end = minimum;  /* WAI still advances a hardware frame. */
"""

CORRECTED_FINISH = """  /* """ + MARK + """: the SPC follows the CPU master clock exactly; no
   * one-field minimum (RF-023: it inflated SPC time on every short iteration).
   * Remove the short-line pauses the iteration crossed (RF-024). */
  uint64_t within = master >= clock->start_master ? master - clock->start_master : 0;
  uint64_t end = clock->start_timeline + within -
                 rtl_apu_short_line_pause(clock->field_parity, within);
  clock->field_parity += (within + RTL_MASTER_CYCLES_PER_FRAME / 2) /
                         RTL_MASTER_CYCLES_PER_FRAME;
"""


def patch(source: str) -> str:
    if MARK in source:
        if any(source.count(x) != 1 for x in (CORRECTED_STRUCT, CORRECTED_TIMELINE, CORRECTED_FINISH)):
            raise ValueError("short-scanline marker present but header altered")
        return source
    if RF016_MARK not in source:
        raise ValueError("stage tools/baldosa_spc_reference_rate_patch.py (RF-016) first")
    for pinned in (PINNED_STRUCT, PINNED_TIMELINE, PINNED_FINISH):
        if source.count(pinned) != 1:
            raise ValueError("RF-016 APU frame clock not recognized")
    source = source.replace(PINNED_STRUCT, CORRECTED_STRUCT, 1)
    source = source.replace(PINNED_TIMELINE, CORRECTED_TIMELINE, 1)
    return source.replace(PINNED_FINISH, CORRECTED_FINISH, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", required=True, type=Path,
                    help="disposable gamesbyian/uniracers-recomp checkout")
    args = ap.parse_args()
    path = args.game.resolve() / HEADER
    before = path.read_text(encoding="utf-8")
    after = patch(before)
    if after == before:
        print(f"SPC frame-clock correction already staged: {path}")
    else:
        path.write_text(after, encoding="utf-8")
        print(f"staged SPC frame-clock correction: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
