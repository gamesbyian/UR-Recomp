#!/usr/bin/env python3
"""Charge HDMA's per-line CPU stall in Baldosa's beam frame driver (RF-019).

Hardware pauses the 65816 for HDMA in every visible line's H-blank: ~18
master clocks of overhead when any channel is live, 8 per live channel, 8 per
byte transferred and, when a channel reloads its line counter, 8 more (+16
for an indirect address); V=0 initialization pays 18 plus 8 (+16) per
channel. The pinned Baldosa framework (``baldosa/snesrecomp@075fbe4``) runs
HDMA only in the post-field render walk (``beam_frame_driver.c::
snes_beam_frame_driver_draw_ppu_frame``) and charges the CPU nothing for it.
``dma_hdmaMasterEstimate`` survives in ``dma.c`` but nothing calls it, and
it would charge every channel a transfer on every line.

On the original USA ROM the attract demo race runs six HDMA channels
(HDMAEN=$BE) whose split-screen tables transfer only at a few lines: Snes9x
stalls 66 clocks (18 + 6 x 8) in every visible H-blank, which the pinned
runtime omits, so CPU-bound frames run ~4% fast and the post-race wait at
82:D4E9 is reached one field early at host 2347.

This stages, into a DISPOSABLE pinned Baldosa checkout:

- ``common_cpu_infra.c``: a cost-only HDMA walk. At V=0 it reads the live
  HDMAEN shadow and channel registers, walks each active table (ROM/WRAM
  reads only; register space is never touched) and records the stall for
  initialization and each of lines 0-223. The existing per-block/per-opcode
  refresh hook charges each stall when CPU time passes that line's H-blank
  (H=1104); parked time passes them without a charge, as for refresh.
- ``beam_frame_driver.c``: each field arms the walk from its V=225 start.

Guest-visible HDMA (the render walk) is untouched. Idempotent; refuses any
other framework revision.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_HDMA_CPU_STALL"
INFRA = Path("snesrecomp/runner/src/common_cpu_infra.c")
DRIVER = Path("snesrecomp/runner/src/beam_frame_driver.c")

PINNED_INFRA = """void snes_refresh_exempt(void) { g_refresh_charged_upto = g_cpu.master_cycles; }
void snes_refresh_charge(void) {
  uint64_t m = g_cpu.master_cycles;
"""

HDMA_MODULE = """/* """ + MARK + """ (RF-019): HDMA's per-line CPU stall.
 * Hardware pauses the CPU in each visible line's H-blank for HDMA: 18 clocks
 * when any channel is live, 8 per live channel, 8 per byte moved and, on a
 * line-counter reload, 8 more (+16 for an indirect address). The render walk
 * performs the guest-visible HDMA after the field and charges nothing, so
 * this cost-only walk (ROM/WRAM table reads, never register space) prices
 * each line at V=0 and the per-block hook charges it as CPU time passes. */
#define UR_HDMA_LINE 1364u
#define UR_HDMA_VBLANK_LINES 37u   /* V=225..261 precede V=0 */
#define UR_HDMA_INIT_H 12u
#define UR_HDMA_RUN_H 1104u
#define UR_HDMA_LINES 224
static const uint8_t ur_hdma_len[8] = {1, 2, 2, 4, 4, 4, 2, 4};
static uint64_t s_ur_hdma_field;      /* master clock of this field's V=225 */
static int s_ur_hdma_event = UR_HDMA_LINES;  /* -1 init, 0..223 lines */
static uint16_t s_ur_hdma_cost[UR_HDMA_LINES];
static uint16_t s_ur_hdma_init_cost;

static uint8_t ur_hdma_table_byte(uint8_t bank, uint16_t adr) {
  if (!(bank & 0x40) && adr >= 0x2000 && adr < 0x6000) return 0;
  return snes_read(g_snes, ((uint32_t)bank << 16) | adr);
}

static void ur_hdma_walk(void) {
  extern uint8 g_snesrecomp_last_hdmaen;
  uint8_t en = g_snesrecomp_last_hdmaen;
  uint16_t table[8], ind[8];
  uint8_t rep[8];
  bool live[8], transfer[8];
  uint32_t init = 0;
  for (int i = 0; i < 8; i++) {
    const DmaChannel *c = &g_snes->dma->channel[i];
    live[i] = (en >> i) & 1;
    if (!live[i]) continue;
    init += 8u;
    table[i] = c->aAdr;
    rep[i] = ur_hdma_table_byte(c->aBank, table[i]++);
    if (rep[i] == 0) { live[i] = false; continue; }
    if (c->indirect) {
      ind[i] = ur_hdma_table_byte(c->aBank, table[i]++);
      ind[i] |= (uint16_t)(ur_hdma_table_byte(c->aBank, table[i]++) << 8);
      init += 16u;
    }
    transfer[i] = true;
  }
  s_ur_hdma_init_cost = (uint16_t)(en ? 18u + init : 0u);
  for (int line = 0; line < UR_HDMA_LINES; line++) {
    uint32_t cost = 0;
    bool any = false;
    for (int i = 0; i < 8; i++) {
      if (!live[i]) continue;
      const DmaChannel *c = &g_snes->dma->channel[i];
      uint32_t len = ur_hdma_len[c->mode & 7];
      any = true;
      cost += 8u;
      if (transfer[i]) {
        cost += 8u * len;
        if (c->indirect) ind[i] = (uint16_t)(ind[i] + len);
        else table[i] = (uint16_t)(table[i] + len);
      }
      rep[i]--;
      transfer[i] = (rep[i] & 0x80) != 0;
      if ((rep[i] & 0x7f) == 0) {
        rep[i] = ur_hdma_table_byte(c->aBank, table[i]++);
        cost += 8u;
        if (rep[i] == 0) { live[i] = false; continue; }
        if (c->indirect) {
          ind[i] = ur_hdma_table_byte(c->aBank, table[i]++);
          ind[i] |= (uint16_t)(ur_hdma_table_byte(c->aBank, table[i]++) << 8);
          cost += 16u;
        }
        transfer[i] = true;
      }
    }
    s_ur_hdma_cost[line] = (uint16_t)(any ? 18u + cost : 0u);
  }
}

static uint64_t ur_hdma_event_at(int event) {
  uint64_t v0 = s_ur_hdma_field + (uint64_t)UR_HDMA_VBLANK_LINES * UR_HDMA_LINE;
  return event < 0 ? v0 + UR_HDMA_INIT_H
                   : v0 + (uint64_t)event * UR_HDMA_LINE + UR_HDMA_RUN_H;
}

/* Pass every due HDMA slot; charge its stall unless the time was parked. */
static void ur_hdma_pass(bool charge) {
  while (s_ur_hdma_event < UR_HDMA_LINES &&
         g_cpu.master_cycles >= ur_hdma_event_at(s_ur_hdma_event)) {
    uint32_t cost;
    if (s_ur_hdma_event < 0) {
      ur_hdma_walk();
      cost = s_ur_hdma_init_cost;
    } else {
      cost = s_ur_hdma_cost[s_ur_hdma_event];
    }
    if (charge) g_cpu.master_cycles += cost;
    s_ur_hdma_event++;
  }
}

void ur_hdma_stall_field_begin(uint64_t field_start_master) {
  s_ur_hdma_field = field_start_master;
  s_ur_hdma_event = -1;
}

"""

CORRECTED_INFRA = HDMA_MODULE + """void snes_refresh_exempt(void) {
  ur_hdma_pass(false);  /* """ + MARK + """: parked time displaces no work */
  g_refresh_charged_upto = g_cpu.master_cycles;
}
void snes_refresh_charge(void) {
  ur_hdma_pass(true);  /* """ + MARK + """ */
  uint64_t m = g_cpu.master_cycles;
"""

PINNED_DRIVER = """    frame_end = g_snes->beamMasterLast +
                (to_vblank ? to_vblank : BFD_MASTER_CYCLES_PER_FIELD);
  }
"""

CORRECTED_DRIVER = PINNED_DRIVER + """  {
    /* """ + MARK + """: arm this field's HDMA stall walk at its V=225. */
    extern void ur_hdma_stall_field_begin(uint64_t field_start_master);
    ur_hdma_stall_field_begin(frame_end - BFD_MASTER_CYCLES_PER_FIELD);
  }
"""


def _patch(source: str, pinned: str, corrected: str, what: str) -> str:
    if MARK in source:
        if source.count(corrected) != 1:
            raise ValueError(f"HDMA stall marker present but {what} altered")
        return source
    if source.count(pinned) != 1:
        raise ValueError(f"pinned Baldosa {what} not recognized; "
                         "do not splice against an unknown framework revision")
    return source.replace(pinned, corrected, 1)


def patch_infra(source: str) -> str:
    if MARK not in source and "#include \"snes/dma.h\"" not in source:
        source = source.replace('#include "snes/snes.h"\n',
                                '#include "snes/snes.h"\n#include "snes/dma.h"\n', 1)
    return _patch(source, PINNED_INFRA, CORRECTED_INFRA, "refresh hook")


def patch_driver(source: str) -> str:
    return _patch(source, PINNED_DRIVER, CORRECTED_DRIVER, "beam frame driver")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", required=True, type=Path,
                    help="disposable gamesbyian/uniracers-recomp checkout")
    args = ap.parse_args()
    game = args.game.resolve()
    changed = False
    for rel, fn in ((INFRA, patch_infra), (DRIVER, patch_driver)):
        path = game / rel
        before = path.read_text(encoding="utf-8")
        after = fn(before)
        if after != before:
            path.write_text(after, encoding="utf-8")
            changed = True
    print(("staged HDMA CPU-stall charge in " if changed
           else "HDMA CPU-stall charge already staged in ") + str(game))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
