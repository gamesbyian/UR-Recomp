#!/usr/bin/env python3
"""RF094: opt-in genuine SPC DSP-write and F7 continuation observer.

Run only on disposable, already RF092/RF093-staged original/native sources.
The actual DSP F3 write is observed *after* its existing hardware call; no
new guest I/O, dispatch, audio state, timestamps or emulation cycles. Existing
F4-F7 port logs are extended by two Bowl-entry-relative host frames.
This instrumentation is diagnostic, not an audio equivalence or event verdict.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ORIGINAL_SMP = Path("apu/bapu/smp/smp.cpp")
ORIGINAL_MEMORY = Path("apu/bapu/smp/memory.cpp")
NATIVE_APU = Path("snesrecomp/runner/src/snes/apu.c")
ORIGINAL_STAMP = "UR_QA01_RF094_ORIGINAL_DSP_FOLLOWTHROUGH"
NATIVE_STAMP = "UR_QA01_RF094_NATIVE_DSP_FOLLOWTHROUGH"
ORIGINAL_STAGE = "UR_QA01_RF092_ORIGINAL_SPC_EDGES"
NATIVE_STAGE = "UR_QA01_RF093_NATIVE_SPC_EDGES"
ORIGINAL_FRAME_OLD = "frame >= 6445u && frame <= 6449u"
NATIVE_FRAME_OLD = "snes_frame_counter >= 6447 && snes_frame_counter <= 6451"
ORIGINAL_WRITE = "    dsp.write(status.dsp_addr, data);\n"
NATIVE_WRITE = "      if(apu->dspAdr < 0x80) dsp_write(apu->dsp, apu->dspAdr, val);\n"
SMP_SINGLETON = '#include "algorithms.cpp"\n'
NATIVE_ENTRY = "static const uint8_t bootRom[0x40] = {"

ORIGINAL_HELPER = r'''
/* UR_QA01_RF094_ORIGINAL_DSP_FOLLOWTHROUGH
 * Post-write DSP register evidence, not an audio sample/PCM observation.
 * RF092's already-ticking original SMP counter is the ONLY clock here. */
static unsigned rf094_original_rows;
static void rf094_original_dsp_write(unsigned reg, unsigned value) {
  const char *flag = std::getenv("UR_QA01_RF094_SPC_DSP");
  if (!flag || flag[0] != '1' || flag[1] != '\0') return;
  const unsigned frame = ::rf083_original_frame();
  if (frame < 6445u || frame > 6451u || reg >= 0x80u) return;
  if (++rf094_original_rows > 16384u) {
    if (rf094_original_rows == 16385u)
      std::fprintf(stderr, "QA01RF094ORIG_TRUNCATED\n");
    return;
  }
  std::fprintf(stderr,
    "QA01RF094ORIG seq=%u frame=%u reg=%02X val=%02X "
    "spc_ticks=%llu spc_next_pc=%04X clock=original_spc\n",
    rf094_original_rows, frame, reg & 0xffu, value & 0xffu,
    rf092_spc_ticks, (unsigned)smp.regs.pc);
}
'''
NATIVE_HELPER = r'''
/* UR_QA01_RF094_NATIVE_DSP_FOLLOWTHROUGH
 * Actual post-dsp_write, native SPC-relative clock. The existing SPC bus
 * presently models an opcode's first-cycle access, not precise final-cycle
 * timing; never subtract from the original SPC clock. */
static unsigned ur_rf094_native_rows;
static void ur_rf094_native_dsp_write(Apu *apu, unsigned reg, unsigned value) {
  const char *flag = getenv("UR_QA01_RF094_SPC_DSP");
  if (!flag || flag[0] != '1' || flag[1] != '\0') return;
  if (snes_frame_counter < 6447 || snes_frame_counter > 6453 ||
      reg >= 0x80u) return;
  if (++ur_rf094_native_rows > 16384u) {
    if (ur_rf094_native_rows == 16385u)
      fprintf(stderr, "QA01RF094NATIVE_TRUNCATED\n");
    return;
  }
  fprintf(stderr,
    "QA01RF094NATIVE seq=%u frame=%d reg=%02X val=%02X "
    "spc_ticks=%llu spc_next_pc=%04X clock=native_spc\n",
    ur_rf094_native_rows, snes_frame_counter, reg & 0xffu, value & 0xffu,
    (unsigned long long)apu->portClock, (unsigned)apu->spc->pc);
}
'''

def replace_one(source: str, before: str, after: str, name: str) -> str:
    if source.count(before) != 1:
        raise ValueError("RF094 staged source drift: " + name)
    return source.replace(before, after, 1)


def patch_original(smp: str, memory: str) -> tuple[str, str]:
    if (ORIGINAL_STAGE not in smp or ORIGINAL_STAMP in smp or
            "rf094_original_dsp_write" in smp + memory):
        raise ValueError("RF094 requires pristine RF092-staged original SMP")
    if "rf092_spc_ticks" not in smp or "rf083_original_frame" not in smp:
        raise ValueError("RF094 original clock/frame authority missing")
    smp = replace_one(smp, ORIGINAL_FRAME_OLD,
                      "frame >= 6445u && frame <= 6451u", "original F7 window")
    smp = replace_one(smp, SMP_SINGLETON,
                      ORIGINAL_HELPER + SMP_SINGLETON, "pre-include helper after RF092 ticks")
    memory = replace_one(
        memory, ORIGINAL_WRITE,
        ORIGINAL_WRITE + "    rf094_original_dsp_write(status.dsp_addr, data);\n",
        "original post-DSP write")
    # Don't modify the reject-invalid-address or the real DSP write itself.
    if (memory.count("dsp.write(status.dsp_addr, data);") != 1 or
            memory.count("if(status.dsp_addr & 0x80) break;") != 1):
        raise ValueError("RF094 original DSP write branch drift")
    return smp, memory


def patch_native(source: str) -> str:
    if (NATIVE_STAGE not in source or NATIVE_STAMP in source or
            "ur_rf094_native_dsp_write" in source):
        raise ValueError("RF094 requires pristine RF093-staged native APU")
    source = replace_one(source, NATIVE_FRAME_OLD,
                         "snes_frame_counter >= 6447 && snes_frame_counter <= 6453",
                         "native F7 window")
    source = replace_one(source, NATIVE_ENTRY,
                         NATIVE_HELPER + "\n" + NATIVE_ENTRY, "native helper")
    source = replace_one(
        source, NATIVE_WRITE,
        "      if(apu->dspAdr < 0x80) {\n"
        "        dsp_write(apu->dsp, apu->dspAdr, val);\n"
        "        ur_rf094_native_dsp_write(apu, apu->dspAdr, val);\n"
        "      }\n",
        "native post-DSP write")
    if source.count("dsp_write(apu->dsp, apu->dspAdr, val);") != 1:
        raise ValueError("RF094 native DSP write population changed")
    return source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path,
                        help="Already RF092-staged original Snes9x root")
    parser.add_argument("--native", type=Path,
                        help="Already RF093-staged disposable Baldosa root")
    args = parser.parse_args()
    if bool(args.original) == bool(args.native):
        parser.error("choose exactly one of --original and --native")
    if args.original:
        paths = [args.original / ORIGINAL_SMP, args.original / ORIGINAL_MEMORY]
        if any(not p.is_file() or p.is_symlink() for p in paths):
            parser.error("original staged SMP sources missing or symlinked")
        output = patch_original(*(p.read_text(encoding="utf-8") for p in paths))
        for p, s in zip(paths, output):
            p.write_text(s, encoding="utf-8")
    else:
        path = args.native / NATIVE_APU
        if not path.is_file() or path.is_symlink():
            parser.error("native staged APU source missing or symlinked")
        path.write_text(patch_native(path.read_text(encoding="utf-8")),
                        encoding="utf-8")
    print("RF094 opt-in post-DSP and two-frame SPC port continuation staged")

if __name__ == "__main__":
    main()
