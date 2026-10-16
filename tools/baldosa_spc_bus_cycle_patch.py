#!/usr/bin/env python3
"""Perform each SPC700 opcode's bus accesses at its last cycle (RF-026).

The pinned Baldosa framework (``baldosa/snesrecomp@075fbe4``) uses a
LakeSnes-derived SPC700: ``apu_cycle`` executes a whole opcode on its FIRST
cycle and then idles for the rest of its cycle count. Every port read, port
echo write, timer read and ``$F1`` timer enable therefore lands 1-7 SPC cycles
before the bus cycle on which hardware (and both cycle-stepped references,
Snes9x's bapu SMP and bsnes) performs it. In CPU/SPC handshakes, where each
side polls for the other's write, that moves the moment each side sees the
other's value:

- over the 4,450-byte boot IPL upload native ran 1,824 master clocks fast,
  with exchanges shorter than any the reference makes (632-684 clocks);
- the sound driver's timer restarts landed up to ~300 SPC cycles off their
  reference positions relative to SPC age, so the driver's timer-2 phase at
  later SPC resets depended on an arbitrary power-on anchor (RF-025).

This stages, into a DISPOSABLE pinned Baldosa checkout:

- ``spc.c``: ``spc_peekCycles`` returns the base cycle count of the opcode at
  PC (the existing table), reading only program memory;
- ``apu.c``: ``apu_cycle`` waits out that count first and executes the opcode
  on its LAST cycle, so its reads see CPU port writes and timer ticks up to
  that cycle and its writes become visible from it. Extra cycles an opcode
  reports beyond its base count (taken branches) follow it as idle cycles.
  The countdown lives in the Apu's reserved ``pad`` bytes (no layout change).

Approximation: every access of an opcode is placed on its last cycle; on
hardware a multi-cycle read-modify-write reads one or two cycles earlier.
DSP, timer stepping and the CPU side are untouched. Idempotent; refuses any
other framework revision.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_SPC_BUS_CYCLE"
APU = Path("snesrecomp/runner/src/snes/apu.c")
SPC = Path("snesrecomp/runner/src/snes/spc.c")
SPC_H = Path("snesrecomp/runner/src/snes/spc.h")

PINNED_APU = """  apu_drainPortQueue(apu);
  if(apu->cpuCyclesLeft == 0) {
    /* Sample PC right BEFORE running the opcode — so PC reflects the
     * instruction we're about to execute, not the post-opcode PC. */
#if SNESRECOMP_SPC_DIAGNOSTICS
    g_spc_pc_histogram[apu->spc->pc]++;
    if (apu->spc->pc > g_spc_pc_max_seen) g_spc_pc_max_seen = apu->spc->pc;
#endif
    apu->cpuCyclesLeft = spc_runOpcode(apu->spc);
  }
  apu->cpuCyclesLeft--;
"""

CORRECTED_APU = """  apu_drainPortQueue(apu);
  if(apu->cpuCyclesLeft == 0) {
    /* """ + MARK + """ (RF-026): hardware performs an opcode's bus
     * accesses on its later cycles, not its first. Wait out the opcode's
     * base cycle count (pad[0] counts down, pad[1] holds it) and execute it
     * on its last cycle, so port/timer reads see everything up to that cycle
     * and its port writes appear from it; extra (branch) cycles follow. */
    if (apu->pad[0] == 0) {
      apu->pad[1] = (uint8_t)spc_peekCycles(apu->spc);
      apu->pad[0] = apu->pad[1];
    }
    if (--apu->pad[0] == 0) {
#if SNESRECOMP_SPC_DIAGNOSTICS
      g_spc_pc_histogram[apu->spc->pc]++;
      if (apu->spc->pc > g_spc_pc_max_seen) g_spc_pc_max_seen = apu->spc->pc;
#endif
      apu->cpuCyclesLeft = (uint8_t)(spc_runOpcode(apu->spc) - apu->pad[1] + 1);
    } else {
      apu->cpuCyclesLeft = 1;
    }
  }
  apu->cpuCyclesLeft--;
"""

PINNED_SPC = "int spc_runOpcode(Spc* spc) {\n"
CORRECTED_SPC = ("/* " + MARK + ": base cycles of the opcode at PC (program memory read). */\n"
                 "int spc_peekCycles(Spc* spc) {\n"
                 "  return spc->stopped ? 1 : cyclesPerOpcode[spc_read(spc, spc->pc)];\n"
                 "}\n\n" + PINNED_SPC)

PINNED_SPC_H = "int spc_runOpcode(Spc* spc);\n"
CORRECTED_SPC_H = PINNED_SPC_H + "int spc_peekCycles(Spc* spc); /* " + MARK + " */\n"


def _patch(source: str, pinned: str, corrected: str, what: str) -> str:
    if MARK in source:
        if source.count(corrected) != 1:
            raise ValueError(f"SPC bus-cycle marker present but {what} altered")
        return source
    if source.count(pinned) != 1:
        raise ValueError(f"pinned Baldosa {what} not recognized; "
                         "do not splice against an unknown framework revision")
    return source.replace(pinned, corrected, 1)


def patch_apu(source: str) -> str:
    return _patch(source, PINNED_APU, CORRECTED_APU, "apu_cycle")


def patch_spc(source: str) -> str:
    if MARK not in source and "static const int cyclesPerOpcode[256]" not in source:
        raise ValueError("pinned Baldosa spc.c cycle table not recognized")
    return _patch(source, PINNED_SPC, CORRECTED_SPC, "spc_runOpcode")


def patch_spc_h(source: str) -> str:
    return _patch(source, PINNED_SPC_H, CORRECTED_SPC_H, "spc.h")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", required=True, type=Path,
                    help="disposable gamesbyian/uniracers-recomp checkout")
    args = ap.parse_args()
    game = args.game.resolve()
    changed = False
    for rel, fn in ((APU, patch_apu), (SPC, patch_spc), (SPC_H, patch_spc_h)):
        path = game / rel
        before = path.read_text(encoding="utf-8")
        after = fn(before)
        if after != before:
            path.write_text(after, encoding="utf-8")
            changed = True
    print(("staged SPC bus-cycle execution in " if changed
           else "SPC bus-cycle execution already staged in ") + str(game))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
