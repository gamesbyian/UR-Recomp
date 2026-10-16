#!/usr/bin/env python3
"""Charge the 65816 interrupt-entry sequence in Baldosa's beam driver (RF-028).

On hardware, taking NMI or IRQ costs a full bus sequence before the
handler's first instruction (bsnes ``CPU::interrupt``): a dummy read at the
interrupted PC, one internal cycle, the stack pushes (PB in native mode, PCH,
PCL, P) and the two vector reads. On the SlowROM USA Uniracers with the
stack in WRAM that is 8 + 6 + 4 x 8 + 2 x 8 = 62 master clocks in native
mode. The pinned Baldosa framework (``baldosa/snesrecomp@075fbe4``) pushes the
frame with unpaced ``cpu_write8`` and reads the vector untimed, so every
handler starts ~62 clocks early against the beam.

Measured on Switcher Race B (RF-027): Snes9x enters the NMI handler
``00:8588`` at V225 H82, native 18 clocks after V=225. Every race field then
runs ~150 clocks early relative to the beam. Carried into the post-race
loader, that offset makes native reach the ``80:FAC9`` VBlank wait before
V=225 and end the event one frame early.

This stages, into a DISPOSABLE pinned Baldosa checkout, the charge in
``beam_frame_driver.c::run_interrupt`` just before the frame push: the
region speed of the interrupted PC, 6 internal, one region-speed write per
pushed byte at the live stack pointer, and the two vector reads in bank 0
(vector ``$FFE0`` page). Handlers, the push itself and the beam are otherwise
unchanged. Idempotent; refuses any other framework revision.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_INTERRUPT_ENTRY_COST"
DRIVER = Path("snesrecomp/runner/src/beam_frame_driver.c")

PINNED = """   * already starts where the real CPU would take it. */
  cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);
  interp_bridge_set_master_deadline(deadline);
"""

CORRECTED = """   * already starts where the real CPU would take it. */
  {
    /* """ + MARK + """ (RF-028): hardware enters the handler through a bus
     * sequence (bsnes CPU::interrupt): dummy read at PC, one internal cycle,
     * push PB (native only), PCH, PCL, P, then read the two vector bytes. */
    uint64_t entry = cpu_region_speed(s_resume_pc) + 6u;
    uint16_t sp = g_cpu.S;
    for (int i = g_cpu.emulation ? 3 : 4; i > 0; i--, sp--)
      entry += cpu_region_speed((uint32_t)sp);
    entry += 2u * cpu_region_speed(0x00FFE0u);
    g_cpu.master_cycles += entry;
  }
  cpu_push_interrupt_frame_at(&g_cpu, s_resume_pc);
  interp_bridge_set_master_deadline(deadline);
"""


def patch(source: str) -> str:
    if MARK in source:
        if source.count(CORRECTED) != 1:
            raise ValueError("interrupt-entry marker present but driver altered")
        return source
    if source.count(PINNED) != 1 or "static void run_interrupt(uint32_t vector, uint64_t deadline) {" not in source:
        raise ValueError("pinned Baldosa beam driver not recognized; "
                         "do not splice against an unknown framework revision")
    return source.replace(PINNED, CORRECTED, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", required=True, type=Path,
                    help="disposable gamesbyian/uniracers-recomp checkout")
    args = ap.parse_args()
    path = args.game.resolve() / DRIVER
    before = path.read_text(encoding="utf-8")
    after = patch(before)
    if after == before:
        print(f"interrupt-entry cost already staged: {path}")
    else:
        path.write_text(after, encoding="utf-8")
        print(f"staged interrupt-entry cost: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
