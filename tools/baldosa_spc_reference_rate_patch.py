#!/usr/bin/env python3
"""Clock Baldosa's SPC700 at the reference rate against the CPU (RF-016).

The pinned Baldosa framework (``baldosa/snesrecomp@075fbe4``) converts CPU
master clocks to SPC700 cycles at a fixed 17088 per 357368-clock field
(``runner/src/apu_frame_clock.h``): 534 DSP samples x 32 per field, i.e. the
32040 Hz output rate at exactly 60 fields per second. The NTSC field is
357368 / (236.25 MHz / 11) = 1/60.0988 s, so the SPC700 runs 0.165% fast
relative to the CPU. Snes9x (``APU_NUMERATOR_NTSC / APU_DENOMINATOR_NTSC`` =
15664 / 328125 SPC cycles per master clock) and bsnes (32040 x 768 Hz / 24)
both use 1,025,280 SPC cycles per second, which is 17059.99 per field.

This stages, into a DISPOSABLE pinned Baldosa checkout, a guest timeline kept
in master clocks and converted at exactly 15664 / 328125:

- ``apu_frame_clock.h``: the extended-timing clock (the desktop host's path)
  advances a master-clock timeline; a host iteration still spans at least one
  field (357368 clocks), and ``last_duration`` stays in SPC cycles.
- ``common_rtl.c``: the fixed-frame path converts ``frame * 357368 + within``
  the same way, and ``RtlLastFramePeriods`` measures the iteration in fields
  of master clocks, so a normal frame is still exactly 1.0 for host pacing.

The DSP, the audio servo (which already absorbs +/-0.5%), port semantics and
the CPU are untouched. Idempotent; refuses any other framework revision.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

MARK = "UR_BALDOSA_SPC_REFERENCE_RATE"
HEADER = Path("snesrecomp/runner/src/apu_frame_clock.h")
RTL = Path("snesrecomp/runner/src/common_rtl.c")
PINNED_HEADER_SHA256 = "7f0a999a97690632299d6c89fbd4e2d141bfc328f42a37a5e94243702754157e"

CORRECTED_HEADER = """#pragma once
#include <stdint.h>

/* """ + MARK + """ (RF-016): the SPC700 runs at the reference rate
 * against the CPU, 1,025,280 Hz (32040 Hz x 32) over 236.25/11 MHz, which is
 * exactly 15664 / 328125 SPC cycles per master clock (Snes9x's NTSC ratio and
 * bsnes's 32040 x 768 Hz / 24). The old fixed 17088 per 357368-clock field
 * assumed exactly 60 fields per second and ran the SPC 0.165% fast. The guest
 * timeline is kept in master clocks so the conversion never accumulates
 * rounding error. */
#define RTL_MASTER_CYCLES_PER_FRAME 357368ull
#define RTL_APU_CYCLES_PER_FRAME 17088ull /* nominal; host buffer sizing only */
#define RTL_APU_RATE_NUM 15664ull
#define RTL_APU_RATE_DEN 328125ull

static inline uint64_t rtl_apu_cycles_of_master(uint64_t master) {
  return (master / RTL_APU_RATE_DEN) * RTL_APU_RATE_NUM +
         (master % RTL_APU_RATE_DEN) * RTL_APU_RATE_NUM / RTL_APU_RATE_DEN;
}

/* A host iteration can include an NMI-disabled loader spanning many hardware
 * frames. Keep its elapsed time when beginning the following iteration. */
typedef struct RtlApuFrameClock {
  uint64_t start_master, start_guest, next_guest, last_duration;
  uint64_t start_timeline, next_timeline, last_master_duration;
} RtlApuFrameClock;

static inline void rtl_apu_clock_begin(RtlApuFrameClock *clock, uint64_t master) {
  clock->start_master = master;
  clock->start_timeline = clock->next_timeline;
  clock->start_guest = rtl_apu_cycles_of_master(clock->start_timeline);
}

static inline uint64_t rtl_apu_clock_timeline(const RtlApuFrameClock *clock,
                                              uint64_t master) {
  /* RESET may initialize CPU state inside the first host iteration. */
  uint64_t within = master >= clock->start_master ? master - clock->start_master : 0;
  return clock->start_timeline + within;
}

static inline uint64_t rtl_apu_clock_now(const RtlApuFrameClock *clock,
                                        uint64_t master) {
  return rtl_apu_cycles_of_master(rtl_apu_clock_timeline(clock, master));
}

static inline uint64_t rtl_apu_clock_finish(RtlApuFrameClock *clock,
                                           uint64_t master) {
  uint64_t end = rtl_apu_clock_timeline(clock, master);
  uint64_t minimum = clock->start_timeline + RTL_MASTER_CYCLES_PER_FRAME;
  if (end < minimum) end = minimum;  /* WAI still advances a hardware frame. */
  clock->last_master_duration = end - clock->start_timeline;
  clock->next_timeline = end;
  clock->next_guest = rtl_apu_cycles_of_master(end);
  clock->last_duration = clock->next_guest - clock->start_guest;
  /* Leave the current origin intact: raster IRQs can still touch APU ports
   * between the completed game iteration and the next clock_begin. */
  return clock->next_guest;
}
"""

RTL_EDITS = (
    ("""  return g_extended_frame_timing && g_apu_frame_clock.last_duration
      ? (double)g_apu_frame_clock.last_duration / RTL_APU_CYCLES_PER_FRAME : 1.0;
""",
     """  /* """ + MARK + """: periods are fields of master clocks. */
  return g_extended_frame_timing && g_apu_frame_clock.last_master_duration
      ? (double)g_apu_frame_clock.last_master_duration / RTL_MASTER_CYCLES_PER_FRAME
      : 1.0;
"""),
    ("""  return (uint64_t)snes_frame_counter * RTL_APU_CYCLES_PER_FRAME +
         within * RTL_APU_CYCLES_PER_FRAME /
             RTL_MASTER_CYCLES_PER_FRAME;
""",
     """  /* """ + MARK + """ */
  return rtl_apu_cycles_of_master(
      (uint64_t)snes_frame_counter * RTL_MASTER_CYCLES_PER_FRAME + within);
"""),
    ("""      : (uint64_t)snes_frame_counter * RTL_APU_CYCLES_PER_FRAME;
""",
     """      : rtl_apu_cycles_of_master(  /* """ + MARK + """ */
            (uint64_t)snes_frame_counter * RTL_MASTER_CYCLES_PER_FRAME);
"""),
)


def patch_header(source: str) -> str:
    if MARK in source:
        if source != CORRECTED_HEADER:
            raise ValueError("SPC reference-rate marker present but header altered")
        return source
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != PINNED_HEADER_SHA256:
        raise ValueError("pinned Baldosa apu_frame_clock.h not recognized; "
                         "do not splice against an unknown framework revision")
    return CORRECTED_HEADER


def patch_rtl(source: str) -> str:
    if MARK in source:
        if any(source.count(new) != 1 for _, new in RTL_EDITS):
            raise ValueError("SPC reference-rate marker present but common_rtl.c altered")
        return source
    for old, new in RTL_EDITS:
        if source.count(old) != 1:
            raise ValueError("pinned Baldosa SPC frame clock use not recognized; "
                             "do not splice against an unknown framework revision")
        source = source.replace(old, new, 1)
    return source


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", required=True, type=Path,
                    help="disposable gamesbyian/uniracers-recomp checkout")
    args = ap.parse_args()
    game = args.game.resolve()
    changed = False
    for rel, fn in ((HEADER, patch_header), (RTL, patch_rtl)):
        path = game / rel
        before = path.read_text(encoding="utf-8")
        after = fn(before)
        if after != before:
            path.write_text(after, encoding="utf-8")
            changed = True
    print(("staged SPC reference-rate correction in " if changed
           else "SPC reference-rate correction already staged in ") + str(game))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
