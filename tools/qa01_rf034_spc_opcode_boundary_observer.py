#!/usr/bin/env python3
"""RF034 source-only SPC instruction boundary observer at actual CPU port writes.

Stage into disposable exact Snes9x/Baldosa checkouts after merged RF030/032/033.
Never alter clock debt, SPC cycle count, queue target, op run order or inputs.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf033_original_native_master_clock as rf033
import qa01_rf032_native_port_target_observer as rf032

MARK = "UR_QA01_RF034_SPC_OPCODE_BOUNDARY"
ORIG = rf033.ORIG
NATIVE = rf032.APU

ORIGINAL_BEFORE = """    const uint64_t rf033_before_age = SNES::ur_qa01_rf030_spc_age;
    S9xAPUExecute();
    SNES::cpu.port_write(port & 3, byte);"""
ORIGINAL_AFTER = r"""    const uint64_t rf033_before_age = SNES::ur_qa01_rf030_spc_age;
    /* UR_QA01_RF034_SPC_OPCODE_BOUNDARY: read-only original SMP debt. */
    const int32 rf034_debt_before = SNES::smp.clock;
    const unsigned rf034_pc_before = SNES::smp.regs.pc;
    const unsigned rf034_opcode_before = SNES::smp.opcode_number;
    const unsigned rf034_opcycle_before = SNES::smp.opcode_cycle;
    S9xAPUExecute();
    SNES::cpu.port_write(port & 3, byte);
    if ((port & 3) == 0 && byte == 0xcc &&
        getenv("UR_QA01_RF034_SPC_OPCODE_BOUNDARY") &&
        SNES::ur_qa01_rf030_spc_age >= 103322420ull &&
        SNES::ur_qa01_rf030_spc_age <= 103323100ull) {
        fprintf(stderr,
          "QA01RF034ORIG before=%llu after=%llu debtbefore=%d debtafter=%d pcbefore=%04X pcafter=%04X opbefore=%02X opafter=%02X cycbefore=%u cycafter=%u value=CC\n",
          (unsigned long long)rf033_before_age,
          (unsigned long long)SNES::ur_qa01_rf030_spc_age,
          (int)rf034_debt_before, (int)SNES::smp.clock,
          rf034_pc_before, (unsigned)SNES::smp.regs.pc,
          rf034_opcode_before, (unsigned)SNES::smp.opcode_number,
          rf034_opcycle_before, (unsigned)SNES::smp.opcode_cycle);
    }"""

NATIVE_BEFORE = rf032.APU_APPLY_NEW
NATIVE_AFTER = r"""  ur_qa01_rf032_port(apu, "apply", w->port, w->val, 0, w->target_cycle);
  /* UR_QA01_RF034_SPC_OPCODE_BOUNDARY: actual native queue-consumer
   * SPC opcode state, before the existing unchanged port store. */
  if (w->port == 0 && w->val == 0xcc &&
      getenv("UR_QA01_RF034_SPC_OPCODE_BOUNDARY") &&
      apu->portClock >= 103322420ull && apu->portClock <= 103323100ull) {
    fprintf(stderr,
      "QA01RF034NATIVE age=%llu target=%llu pc=%04X left=%u qhead=%u qtail=%u value=CC\n",
      (unsigned long long)apu->portClock,
      (unsigned long long)w->target_cycle,
      (unsigned)apu->spc->pc, (unsigned)apu->cpuCyclesLeft,
      (unsigned)apu->portQHead, (unsigned)apu->portQTail);
  }
  apu_writePortNow(apu, w->port, w->val);"""

def _pin(source: str, previous: str, before: str, after: str, name: str) -> str:
    if MARK in source:
        if source.count(after)!=1:
            raise ValueError(f"partial/tampered RF034 {name}")
        return source
    if previous not in source or source.count(before)!=1:
        raise ValueError(f"RF034 unknown {name} exact prior source stage")
    return source.replace(before,after,1)

def patch_original(source: str)->str:
    return _pin(source,rf033.MARK,ORIGINAL_BEFORE,ORIGINAL_AFTER,"Snes9x original apu.cpp")

def patch_native(source: str)->str:
    return _pin(source,rf032.MARK,NATIVE_BEFORE,NATIVE_AFTER,"Baldosa native apu.c")

def main()->int:
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("side",choices=("original","native"))
    cli.add_argument("--root",type=Path,required=True)
    a=cli.parse_args()
    path=a.root.resolve()/(ORIG if a.side=="original" else NATIVE)
    if not path.is_file():
        cli.error(f"missing pinned {path}")
    before=path.read_text(encoding="utf8")
    after=(patch_original if a.side=="original" else patch_native)(before)
    if before!=after:
        path.write_text(after,encoding="utf8")
    print(f"RF034 {a.side}: {'already' if before==after else 'bounded SPC instruction source observer staged'} {path}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
