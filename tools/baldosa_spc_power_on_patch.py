#!/usr/bin/env python3
"""Run Baldosa's SPC700 from power-on instead of from the first port write (RF-021).

The pinned Baldosa framework (``baldosa/snesrecomp@075fbe4``) anchors guest
time to APU time lazily: ``apu_schedulePortWrite`` sets ``portTimeValid`` on
the CPU's first APU-port write, and until then ``apu_runToGuestCycle``
returns without stepping the SPC. Hardware runs the SPC700 from power-on, so
its IPL ROM has long finished clearing zero page and is waiting with
``$BBAA`` on ports 0/1 when the game first talks to it.

On the original USA ROM the first SPC reset (host 35, ``82:8082``) is
answered after 10,004 master clocks on Snes9x (its SPC has run 586,459
cycles); the pinned runtime's SPC has run 6 cycles, so the IPL is still
clearing zero page and the answer takes 50,528. With the SPC anchored at
power-on the latency is 10,004 = 10,004, and the later SPC-reset handshakes
that depend on the sound driver's timer phase move much closer to the
references (RF-020 class).

This stages, into a DISPOSABLE pinned Baldosa checkout, one line in
``apu_reset``: establish the guest/APU correspondence at reset (guest cycle 0
= APU cycle 0) so the per-frame boundary sync steps the SPC from the first
frame. Idempotent; refuses any other framework revision.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_SPC_POWER_ON"
RELATIVE = Path("snesrecomp/runner/src/snes/apu.c")

PINNED = """  apu->cpuCyclesLeft = 7;
  apu->portClock = 0;
  apu_clearPortQueue(apu);
}
"""

CORRECTED = """  apu->cpuCyclesLeft = 7;
  apu->portClock = 0;
  apu_clearPortQueue(apu);
  /* """ + MARK + """: the SPC700 runs from power-on. Anchor guest cycle 0
   * to APU cycle 0 now instead of at the first CPU port write, so the frame
   * boundary sync steps the SPC (IPL ROM, then whatever is uploaded) from the
   * first frame as hardware does. */
  apu->portTimeValid = true;
}
"""


def patch(source: str) -> str:
    if MARK in source:
        if source.count(CORRECTED) != 1:
            raise ValueError("SPC power-on marker present but correction altered")
        return source
    if source.count(PINNED) != 1 or "void apu_reset(Apu* apu) {" not in source:
        raise ValueError("pinned Baldosa apu_reset not recognized; "
                         "do not splice against an unknown framework revision")
    if source.index("void apu_reset(Apu* apu) {") > source.index(PINNED):
        raise ValueError("anchor is not inside apu_reset")
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
        print(f"SPC power-on anchor already staged: {path}")
    else:
        path.write_text(after, encoding="utf-8")
        print(f"staged SPC power-on anchor: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
