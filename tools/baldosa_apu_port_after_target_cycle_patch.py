#!/usr/bin/env python3
"""RF-031 isolated A/B: apply queued CPU port write after target SPC cycle.

The exact Snes9x `S9xAPUWritePort` executes the SPC through CPU.Cycles
and only THEN updates the CPU->SPC port latch. Pinned Baldosa drains due
writes BEFORE advancing SPC cycle, and currently accepts target == portClock.
A CPU CC port write therefore becomes visible to the native IPL CMP one
SPC read-loop iteration early at a knife-edge of the handshake.

Hypothesis to FALSIFY on exact original-native USA Zoo, not a shipping fix:
defer equal-target queued writes until AFTER that SPC cycle by changing only
the queue-drain condition > to >=. Strictly preserve all staging counters,
controllers, clocks, queue events and paired full SRAM/WRAM report.

This may affect every CPU port write, so negative regressions are expected
and must remain visible. No original/reference or product changes.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_RF031_APU_CPU_PORT_AFTER_SPC_TARGET_CYCLE"
REL = Path("snesrecomp/runner/src/snes/apu.c")
OLD = """    if (w->target_cycle > apu->portClock)
      break;
    apu_applyPortWrite(apu, w);"""
NEW = """    /* UR_RF031_APU_CPU_PORT_AFTER_SPC_TARGET_CYCLE: RF-031 disposable
     * source-timing discriminator. On original Snes9x, CPU writes update
     * the latch after S9xAPUExecute has finished the equal clock's SPC
     * instruction microcycles. A queued write targeting this portClock
     * must therefore not reach the SPC before its equal-target cycle. */
    if (w->target_cycle >= apu->portClock)
      break;
    apu_applyPortWrite(apu, w);"""


def patch(src: str) -> str:
    if MARK in src:
        if src.count(NEW) != 1:
            raise ValueError("RF-031 marker exists but queue stage modified")
        return src
    if "uint64_t target = apu->portTargetAnchor +" not in src or \
       "void apu_cycle(Apu* apu)" not in src or \
       src.count(OLD) != 1:
        raise ValueError("reject unknown pinned Baldosa CPU->SPC queue implementation")
    return src.replace(OLD, NEW, 1)


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--game", required=True, type=Path)
    args = cli.parse_args()
    path = args.game.resolve() / REL
    old = path.read_text(encoding="utf8")
    new = patch(old)
    if old != new:
        path.write_text(new, encoding="utf8")
    print(f"RF-031 queue boundary: {'staged' if old != new else 'already staged'} in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
