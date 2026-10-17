#!/usr/bin/env python3
"""RF041: original executed SMP debt vs native queue/SPC phase at exact Zoo F6.

Read-only, source-pinned experiment staged after RF034, RF037 and RF039.
It never advances SPC, reads a port again, changes queue targets or writes
memory. Clock axes and sampled instruction boundaries remain independent.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf034_spc_opcode_boundary_observer as rf034
import qa01_rf037_sound_transaction_window as rf037
import qa01_rf039_target_receiver_observer as rf039

MARK = "UR_QA01_RF041_SMP_DEBT"
FLAG = "UR_QA01_RF041_SMP_DEBT"
O_APU = Path("apu/apu.cpp")
O_SPC = Path("apu/bapu/smp/core.cpp")
N_APU = Path("snesrecomp/runner/src/snes/apu.c")

ORIGINAL_CPU_SLOT = "    S9xAPUExecute();\n    SNES::cpu.port_write(port & 3, byte);\n"
ORIGINAL_CPU_REPLACEMENT = r"""    /* UR_QA01_RF041_SMP_DEBT: original source clock/debt before sync. */
    const bool rf041_target = (port & 3) == 2 && byte == 0x24 &&
        getenv("UR_QA01_RF041_SMP_DEBT") &&
        (unsigned)::CPU.V_Counter == 116u && (int)::CPU.Cycles >= 400 &&
        (int)::CPU.Cycles <= 500 &&
        rf033_before_age >= 103919400ull && rf033_before_age <= 103919500ull;
    if (rf041_target)
        fprintf(stderr,
            "QA01RF041ORIGCPU phase=before-sync age=%llu v=%u h=%d debt=%d pc=%04X op=%02X cycle=%u port=2 value=24\n",
            (unsigned long long)rf033_before_age,
            (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
            (int)rf034_debt_before, rf034_pc_before,
            rf034_opcode_before, rf034_opcycle_before);
    S9xAPUExecute();
    if (rf041_target)
        fprintf(stderr,
            "QA01RF041ORIGCPU phase=after-sync-before-publish age=%llu v=%u h=%d debt=%d pc=%04X op=%02X cycle=%u port=2 value=24\n",
            (unsigned long long)SNES::ur_qa01_rf030_spc_age,
            (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
            (int)SNES::smp.clock, (unsigned)SNES::smp.regs.pc,
            (unsigned)SNES::smp.opcode_number,
            (unsigned)SNES::smp.opcode_cycle);
    SNES::cpu.port_write(port & 3, byte);
    if (rf041_target)
        fprintf(stderr,
            "QA01RF041ORIGCPU phase=after-publish age=%llu v=%u h=%d debt=%d pc=%04X op=%02X cycle=%u port=2 value=24\n",
            (unsigned long long)SNES::ur_qa01_rf030_spc_age,
            (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
            (int)SNES::smp.clock, (unsigned)SNES::smp.regs.pc,
            (unsigned)SNES::smp.opcode_number,
            (unsigned)SNES::smp.opcode_cycle);
"""
# RF037 upstream instruments the CPU writer *inside* RF034's block.
# Match only the immutable adjacent execute/write boundary, preserving the
# already-inserted RF037 writer observer after the write without touching it.
# RF034's prior snapshot names remain in the surrounding S9xAPUWritePort scope.
ORIGINAL_CPU_BEFORE = ORIGINAL_CPU_SLOT
ORIGINAL_CPU_AFTER = ORIGINAL_CPU_REPLACEMENT

ORIGINAL_SPC_BEFORE = rf037.ORIGINAL_SPC_EXTRA.replace(
    rf039.ORIG_NEEDLE, rf039.ORIG_SUBSTITUTE, 1)
ORIGINAL_SPC_SLOT = "    return observed;\n  }\n"
ORIGINAL_SPC_INSERT = r"""    /* UR_QA01_RF041_SMP_DEBT: real F6 read already performed once. */
    if (addr == 0xf6 && getenv("UR_QA01_RF041_SMP_DEBT") &&
        ur_qa01_rf030_spc_age >= 103919445ull &&
        ur_qa01_rf030_spc_age <= 103919470ull) {
      static unsigned rf041_source_f6_count;
      if (rf041_source_f6_count++ < 64u)
        fprintf(stderr,
            "QA01RF041ORIGF6 age=%llu v=%u h=%d debt=%d pc=%04X opcode=%02X cycle=%u port=2 val=%02X\n",
            (unsigned long long)ur_qa01_rf030_spc_age,
            (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
            (int)clock, (unsigned)regs.pc,
            (unsigned)opcode_number, (unsigned)opcode_cycle,
            (unsigned)observed);
      else if (rf041_source_f6_count == 65u)
        fprintf(stderr, "QA01RF041ORIGF6_TRUNCATED\n");
    }
"""
assert ORIGINAL_SPC_BEFORE.count(ORIGINAL_SPC_SLOT) == 1
ORIGINAL_SPC_AFTER = ORIGINAL_SPC_BEFORE.replace(
    ORIGINAL_SPC_SLOT, ORIGINAL_SPC_INSERT + ORIGINAL_SPC_SLOT, 1)

NATIVE_BEFORE = rf037.NATIVE_APU_HELPER.replace(
    rf039.NATIVE_NEEDLE, rf039.NATIVE_SUBSTITUTE, 1)
NATIVE_SLOT = "  else if (count == 16001u)\n    fprintf(stderr, \"QA01RF037NATIVEBUS_TRUNCATED frame=%d\\n\", f);\n"
NATIVE_INSERT = r"""  /* UR_QA01_RF041_SMP_DEBT: exact native SPC queue/read clock state. */
  if (f == 6091 && port == 2 && getenv("UR_QA01_RF041_SMP_DEBT") &&
      apu->portClock >= 103919420ull &&
      apu->portClock <= 103919450ull) {
    static unsigned rf041_rows;
    if (rf041_rows++ < 128u)
      fprintf(stderr,
          "QA01RF041NATIVE kind=%s frame=%d age=%llu target=%llu left=%u pc=%04X port=2 val=%02X q=%u\n",
          kind, f, (unsigned long long)apu->portClock,
          (unsigned long long)target, (unsigned)apu->cpuCyclesLeft,
          (unsigned)apu->spc->pc, (unsigned)value,
          (unsigned)(apu->portQTail - apu->portQHead));
    else if (rf041_rows == 129u)
      fprintf(stderr, "QA01RF041NATIVE_TRUNCATED frame=6091\n");
  }
"""
assert NATIVE_BEFORE.count(NATIVE_SLOT) == 1
NATIVE_AFTER = NATIVE_BEFORE.replace(
    NATIVE_SLOT, NATIVE_SLOT + NATIVE_INSERT, 1)

def splice(source: str, before: str, after: str, label: str) -> str:
    if MARK in source:
        if source.count(after) != 1:
            raise ValueError("RF041 partial/tampered " + label)
        return source
    if source.count(before) != 1:
        raise ValueError("RF041 missing/duplicated pinned stage " + label)
    return source.replace(before, after, 1)

def original_cpu(source: str) -> str:
    return splice(source, ORIGINAL_CPU_BEFORE, ORIGINAL_CPU_AFTER,
                  "Snes9x original CPU/SPC publication")

def original_spc(source: str) -> str:
    return splice(source, ORIGINAL_SPC_BEFORE, ORIGINAL_SPC_AFTER,
                  "Snes9x executed SMP F6 read")

def native_spc(source: str) -> str:
    return splice(source, NATIVE_BEFORE, NATIVE_AFTER,
                  "native queue apply and executed F6 read")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("side", choices=("original", "native"))
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    root = a.root.resolve()
    tasks = ((O_APU, original_cpu), (O_SPC, original_spc)) if a.side == "original" else (
        (N_APU, native_spc),)
    staged = []
    for rel, operation in tasks:
        path = root / rel
        if not path.is_file():
            p.error("missing pinned source " + str(path))
        before = path.read_text(encoding="utf8")
        staged.append((path, before, operation(before)))
    for path, before, after in staged:
        if before != after:
            path.write_text(after, encoding="utf8")
        print("RF041", path, "already staged" if before == after else "read-only witness staged")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
