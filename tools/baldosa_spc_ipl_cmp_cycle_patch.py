#!/usr/bin/env python3
"""Research-only RF-029: sample the SPC IPL ready compare's $F4 bus read on cycle 4.

RF-026 executes every SPC opcode as one transaction on its last base cycle.
The 5-cycle IPL instruction at FF:FFCF is CMP $F4,#$CC (78 CC F4):
Snes9x's cycle-stepped SMP takes opcode/operand/DP-address fetches on
cycles 1/2/3, reads the port on cycle 4, and takes the idle cycle on 5.
A queued CPU $2140 write arriving between cycles 4 and 5 can otherwise make
the native CPU see an echo one whole poll earlier, with a full-frame WRAM
sound-upload boundary flicker at Zoo +5040/+5045.

This deliberately narrow falsification patch caches the $F4 read on cycle 4
and consumes it at cycle 5 *only when the IPL ROM is visible, the SPC PC is
0xFFCF and DP page 0*. It retains cycle totals, other opcodes, timer/DSP
stepping and the recorded CPU inputs. It requires RF-026 already staged and
rejects unrecognized source. It is NOT a production SPC model or a waiver
for any original/native discrepancy. The final hardware-correct fix would
derive all relevant SPC opcode bus accesses from a per-cycle model.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_SPC_IPL_CMP_CYCLE"
APU = Path("snesrecomp/runner/src/snes/apu.c")
SPC = Path("snesrecomp/runner/src/snes/spc.c")

# The pad lives inside Apu's existing saveload-ed state. RF-026 uses
# pad[0]/pad[1] for the base-cycle countdown; use pad[2] as one cached
# read and pad[3] as its one-shot validity. No struct/ABI modification.
RESET_OLD = """  apu->cpuCyclesLeft = 7;
  apu->portClock = 0;
"""
RESET_NEW = """  apu->cpuCyclesLeft = 7;
  memset(apu->pad, 0, sizeof(apu->pad)); /* """ + MARK + """ */
  apu->portClock = 0;
"""
APU_OLD = """    if (--apu->pad[0] == 0) {
#if SNESRECOMP_SPC_DIAGNOSTICS
"""
APU_NEW = """    /* """ + MARK + """: RF-026's countdown is 2 before SPC cycle 4
     * of a five-cycle instruction. Read the IPL CMP $F4,#$CC port here,
     * after the port queue is drained, rather than on the idle fifth cycle.
     * This preserves one and only one port read per compare. */
    if (apu->pad[0] == 2 && apu->pad[1] == 5 &&
        apu->romReadable && apu->spc->pc == 0xffcf && !apu->spc->p) {
      apu->pad[2] = apu_cpuRead(apu, 0xf4);
      apu->pad[3] = 1;
    }
    if (--apu->pad[0] == 0) {
#if SNESRECOMP_SPC_DIAGNOSTICS
"""
SPC_OLD = """static uint8_t spc_read(Spc* spc, uint16_t adr) {
  return apu_cpuRead(spc->apu, adr);
}
"""
SPC_NEW = """static uint8_t spc_read(Spc* spc, uint16_t adr) {
  /* """ + MARK + """: spc_adrDpImm has now advanced IPL PC to FFD2.
   * Return its cycle-4 port sample once; do not read/trace $F4 again
   * on the otherwise unchanged cycle-5 comparison. */
  if (adr == 0xf4 && spc->apu->pad[3] &&
      spc->apu->romReadable && spc->pc == 0xffd2) {
    spc->apu->pad[3] = 0;
    return spc->apu->pad[2];
  }
  return apu_cpuRead(spc->apu, adr);
}
"""


def replace_exact(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    if source.count(old) != 1:
        raise ValueError(f"pinned RF-026 {label} not recognized; refuse unknown guest")
    return source.replace(old, new, 1)


def patch_apu(source: str) -> str:
    if "UR_BALDOSA_SPC_BUS_CYCLE" not in source:
        raise ValueError("RF-029 requires RF-026 SPC bus-cycle stage first")
    if MARK in source and (RESET_NEW not in source or APU_NEW not in source):
        raise ValueError("RF-029 APU marker present but implementation altered")
    source = replace_exact(source, RESET_OLD, RESET_NEW, "apu_reset")
    source = replace_exact(source, APU_OLD, APU_NEW, "apu_cycle")
    if source.count(MARK) != 2:
        raise ValueError("RF-029 APU stage incomplete")
    return source


def patch_spc(source: str) -> str:
    if "UR_BALDOSA_SPC_BUS_CYCLE" not in source:
        raise ValueError("RF-029 requires RF-026 SPC peekCycles first")
    if MARK in source and SPC_NEW not in source:
        raise ValueError("RF-029 SPC marker present but implementation altered")
    result = replace_exact(source, SPC_OLD, SPC_NEW, "spc_read")
    if result.count(MARK) != 1:
        raise ValueError("RF-029 SPC stage incomplete")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game", type=Path, required=True,
                    help="disposable game checkout with pinned RF-026 staged")
    args = ap.parse_args()
    game = args.game.resolve()
    changed = 0
    for rel, apply in ((APU, patch_apu), (SPC, patch_spc)):
        path = game / rel
        old = path.read_text(encoding="utf-8")
        new = apply(old)
        if new != old:
            path.write_text(new, encoding="utf-8")
            changed += 1
    print(f"RF-029 research-only IPL CMP cycle-4 port read: {changed} files changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
