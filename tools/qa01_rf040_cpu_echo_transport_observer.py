#!/usr/bin/env python3
"""RF040: read-only source CPU $2142 poll + SPC port2 echo witnesses.

Stage into the same disposable RF030/032/034... research guests as RF039.
Observe after true port reads and actual SPC F6 writes. Never duplicate I/O
calls, alter schedule/clock/debt, modify ROM/input, or touch Windows product.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_ipl_echo_trace_patch as rf030
import qa01_rf032_native_port_target_observer as rf032

MARK = "UR_QA01_RF040_ZOO_CPU_ECHO"
FLAG = "UR_QA01_RF040_ZOO_CPU_ECHO"
O_APU = Path("apu/apu.cpp")
O_SPC = Path("apu/bapu/smp/core.cpp")
N_SNES = Path("snesrecomp/runner/src/snes/snes.c")
N_APU = Path("snesrecomp/runner/src/snes/apu.c")

CPU_ORIG_OLD = rf030.CPU_READ_NEW
CPU_ORIG_APPEND = r"""    /* UR_QA01_RF040_ZOO_CPU_ECHO: returned CPU $2142 value. */
    if ((port & 3) == 2 && getenv("UR_QA01_RF040_ZOO_CPU_ECHO") &&
        (unsigned)::CPU.V_Counter == 116u &&
        (unsigned)::CPU.Cycles >= 440u && (unsigned)::CPU.Cycles <= 880u &&
        SNES::ur_qa01_rf030_spc_age >= 103919410ull &&
        SNES::ur_qa01_rf030_spc_age <= 103919510ull) {
        static unsigned rf040_cpu_reads = 0;
        if (rf040_cpu_reads++ < 128u)
            fprintf(stderr, "QA01RF040ORIGCPU v=%u h=%d age=%llu port=2 value=%02X\n",
                    (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
                    (unsigned long long)SNES::ur_qa01_rf030_spc_age,
                    (unsigned)observed);
        else if (rf040_cpu_reads == 129u)
            fprintf(stderr, "QA01RF040ORIGCPU_TRUNCATED\n");
    }
"""
CPU_ORIG_ANCHOR = "    return observed;\n}"
SPC_ORIG_OLD = rf030.WRITE_NEW
SPC_ORIG_APPEND = r"""  /* UR_QA01_RF040_ZOO_CPU_ECHO: actual output-port2 publication. */
  if (addr == 0xf6 && getenv("UR_QA01_RF040_ZOO_CPU_ECHO") &&
      ur_qa01_rf030_spc_age >= 103919410ull &&
      ur_qa01_rf030_spc_age <= 103919550ull) {
    static unsigned rf040_echo_rows = 0;
    if (rf040_echo_rows++ < 128u)
      fprintf(stderr, "QA01RF040ORIGSPCECHO age=%llu pc=%04X port=2 value=%02X\n",
              (unsigned long long)ur_qa01_rf030_spc_age,
              (unsigned)regs.pc, (unsigned)data);
    else if (rf040_echo_rows == 129u)
      fprintf(stderr, "QA01RF040ORIGSPCECHO_TRUNCATED\n");
  }
"""
SPC_ORIG_ANCHOR = "  apuram[addr] = data;  //all writes go to RAM, even MMIO writes\n}"

CPU_NATIVE_OLD = rf032.SNES_READ_NEW
CPU_NATIVE_APPEND = r"""    /* UR_QA01_RF040_ZOO_CPU_ECHO: true post-sync, post-filter CPU value. */
    {
      extern int snes_frame_counter;
      if ((adr & 3) == 2 && snes_frame_counter == 6091 &&
          getenv("UR_QA01_RF040_ZOO_CPU_ECHO") &&
          snes->apu->portClock >= 103919280ull &&
          snes->apu->portClock <= 103919480ull) {
        static unsigned rf040_cpu_reads = 0;
        if (rf040_cpu_reads++ < 128u)
          fprintf(stderr, "QA01RF040NATIVECPU frame=6091 age=%llu pc=%04X port=2 raw=%02X returned=%02X\n",
                  (unsigned long long)snes->apu->portClock,
                  (unsigned)snes->apu->spc->pc,
                  (unsigned)raw_apu_value, (unsigned)v);
        else if (rf040_cpu_reads == 129u)
          fprintf(stderr, "QA01RF040NATIVECPU_TRUNCATED\n");
      }
    }
"""
CPU_NATIVE_ANCHOR = "    RtlApuUnlock();"

SPC_NATIVE_OLD = rf030.NATIVE_ECHO_NEW
SPC_NATIVE_APPEND = r"""      /* UR_QA01_RF040_ZOO_CPU_ECHO: actual output-port2 echo store. */
      if (adr == 0xf6 && getenv("UR_QA01_RF040_ZOO_CPU_ECHO") &&
          apu->portClock >= 103919280ull &&
          apu->portClock <= 103919550ull) {
        extern int snes_frame_counter;
        if (snes_frame_counter == 6091) {
          static unsigned rf040_echo_rows = 0;
          if (rf040_echo_rows++ < 128u)
            fprintf(stderr, "QA01RF040NATIVESPCECHO frame=6091 age=%llu pc=%04X port=2 value=%02X\n",
                    (unsigned long long)apu->portClock,
                    (unsigned)apu->spc->pc, (unsigned)val);
          else if (rf040_echo_rows == 129u)
            fprintf(stderr, "QA01RF040NATIVESPCECHO_TRUNCATED\n");
        }
      }
"""
SPC_NATIVE_ANCHOR = "      if (adr == 0xf4) ur_qa01_rf030_native(apu, \"echo\", val);"


def _patch(text: str, anchor: str, before: str, insert: str, slot: str,
           label: str) -> str:
    if before.count(slot) != 1:
        raise ValueError("RF040 upstream " + label + " contract changed")
    after = before.replace(slot, insert + slot, 1)
    if MARK in text:
        if text.count(after) != 1:
            raise ValueError("RF040 partial/tampered " + label)
        return text
    if text.count(anchor) != 1:
        raise ValueError("RF040 needs staged RF030/RF032 " + label)
    return text.replace(anchor, after, 1)


def original_apu(s: str) -> str:
    return _patch(s, CPU_ORIG_OLD, CPU_ORIG_OLD, CPU_ORIG_APPEND,
                  CPU_ORIG_ANCHOR, "original CPU returned read")


def original_spc(s: str) -> str:
    return _patch(s, SPC_ORIG_OLD, SPC_ORIG_OLD, SPC_ORIG_APPEND,
                  SPC_ORIG_ANCHOR, "original SPC output publication")


def native_snes(s: str) -> str:
    return _patch(s, CPU_NATIVE_OLD, CPU_NATIVE_OLD, CPU_NATIVE_APPEND,
                  CPU_NATIVE_ANCHOR, "native returned CPU read")


def native_apu(s: str) -> str:
    return _patch(s, SPC_NATIVE_OLD, SPC_NATIVE_OLD, SPC_NATIVE_APPEND,
                  SPC_NATIVE_ANCHOR, "native SPC output publication")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("side", choices=("original", "native"))
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    root = a.root.resolve()
    pairs = ((O_APU, original_apu), (O_SPC, original_spc)) if a.side == "original" else (
        (N_SNES, native_snes), (N_APU, native_apu))
    pending = []
    for relative, fn in pairs:
        path = root / relative
        if not path.is_file():
            p.error("missing pinned source " + str(path))
        original = path.read_text(encoding="utf8")
        pending.append((path, original, fn(original)))
    for path, before, after in pending:
        if before != after:
            path.write_text(after, encoding="utf8")
        print("RF040", path, "already staged" if before == after else "read-only echo staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
