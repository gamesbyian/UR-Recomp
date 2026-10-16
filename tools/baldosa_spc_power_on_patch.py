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

This stages, into a DISPOSABLE pinned Baldosa checkout, the anchor in
``apu_reset``: establish the guest/APU correspondence at reset, so the
per-frame boundary sync steps the SPC from the first frame. ``--anchor`` is
the guest SPC cycle at which APU cycle 0 falls (default 2,446):

- With the RF-016 frame clock alone, whose one-field WAI minimum inflates SPC
  time during boot, 2,446 (37 lines from the V=225 guest origin to the V=0
  power-on position, plus reset latency) reproduces the reference's
  586,459-cycle SPC age at the first handshake exactly.
- With the RF-023 frame-clock correction (``baldosa_spc_frame_clock_patch.py``)
  that inflation is gone: anchor 0 reproduces the reference SPC age to 14
  cycles at the boot handshake and at every later SPC reset, while 2,446
  leaves the SPC 2,460 cycles younger. On that base 2,446 is the empirical
  candidate (it keeps the attract and Dragster matches, which anchor 0 loses);
  see RF-025 in docs/RF023-025-SPC-FRAME-CLOCK-20261016.md.
- With RF-026 (``baldosa_spc_bus_cycle_patch.py``) also staged, anchor 0 keeps
  every witness (docs/RF026-SPC-BUS-CYCLE-20261016.md): use ``--anchor 0``.

Idempotent; refuses any other framework revision.
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

DEFAULT_ANCHOR = 2446

CORRECTED_TEMPLATE = """  apu->cpuCyclesLeft = 7;
  apu->portClock = 0;
  apu_clearPortQueue(apu);
  /* """ + MARK + """: the SPC700 runs from power-on. Anchor the guest/APU
   * correspondence now instead of at the first CPU port write, so the frame
   * boundary sync steps the SPC (IPL ROM, then whatever is uploaded) from the
   * first frame as hardware does. Guest time starts at the field boundary
   * (V=225); APU cycle 0 falls at guest SPC cycle ANCHOR (see
   * tools/baldosa_spc_power_on_patch.py for the measured choice). */
  apu->portTimeValid = true;
  apu->portGuestAnchor = ANCHOR;
  apu->portLastGuest = ANCHOR;
}
"""


def corrected(anchor: int = DEFAULT_ANCHOR) -> str:
    if not 0 <= anchor < 1 << 20:
        raise ValueError("anchor out of range")
    return CORRECTED_TEMPLATE.replace("ANCHOR", str(anchor))


CORRECTED = corrected()


def patch(source: str, anchor: int = DEFAULT_ANCHOR) -> str:
    want = corrected(anchor)
    if MARK in source:
        if source.count(want) != 1:
            raise ValueError("SPC power-on marker present but correction altered")
        return source
    if source.count(PINNED) != 1 or "void apu_reset(Apu* apu) {" not in source:
        raise ValueError("pinned Baldosa apu_reset not recognized; "
                         "do not splice against an unknown framework revision")
    if source.index("void apu_reset(Apu* apu) {") > source.index(PINNED):
        raise ValueError("anchor is not inside apu_reset")
    return source.replace(PINNED, want, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", required=True, type=Path,
                    help="disposable gamesbyian/uniracers-recomp checkout")
    ap.add_argument("--anchor", type=int, default=DEFAULT_ANCHOR,
                    help="guest SPC cycle of APU cycle 0 (default %(default)s)")
    args = ap.parse_args()
    path = args.game.resolve() / RELATIVE
    before = path.read_text(encoding="utf-8")
    after = patch(before, args.anchor)
    if after == before:
        print(f"SPC power-on anchor already staged: {path}")
    else:
        path.write_text(after, encoding="utf-8")
        print(f"staged SPC power-on anchor: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
