#!/usr/bin/env python3
"""RF033 read-only original CPU/APU clock conversion vs native AOT writer.

Stage ONLY after merged RF030's original Snes9x CPU/SPC observer and merged
RF032's native queued target/poll observers in disposable reference checkouts.
No 65816 bus delay, controller movement, SPC opcode/timing or product code.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_ipl_echo_trace_patch as rf030

MARK = "UR_QA01_RF033_MASTER_APU_CLOCK"
ORIG = Path("apu/apu.cpp")
NATIVE = Path("snesrecomp/runner/src/common_rtl.c")

ORIGINAL_OLD = rf030.CPU_WRITE_NEW
# preserve all existing RF030 event records exactly, inserting only pre/post
# clock details around the original S9xAPUExecute() / CPU latch transaction.
ORIGINAL_NEW = ORIGINAL_OLD.replace(
    "    S9xAPUExecute();\n    SNES::cpu.port_write(port & 3, byte);",
    r"""    /* UR_QA01_RF033_MASTER_APU_CLOCK: original S9x CPU->APU ratio evidence. */
    const int32 rf033_cpu_h_before = ::CPU.Cycles;
    const int32 rf033_reference_time = spc::reference_time;
    const uint32 rf033_remainder = spc::remainder;
    const uint32 rf033_numerator = spc::ratio_numerator;
    const uint32 rf033_denominator = spc::ratio_denominator;
    const int rf033_expected_ticks = S9xAPUGetClock(::CPU.Cycles);
    const uint64_t rf033_before_age = SNES::ur_qa01_rf030_spc_age;
    S9xAPUExecute();
    SNES::cpu.port_write(port & 3, byte);
    if ((port & 3) == 0 && byte == 0xcc &&
        getenv("UR_QA01_RF033_MASTER_APU_CLOCK") &&
        SNES::ur_qa01_rf030_spc_age >= 103322420ull &&
        SNES::ur_qa01_rf030_spc_age <= 103323100ull) {
        fprintf(stderr,
          "QA01RF033ORIG before=%llu after=%llu h=%d v=%u ref=%d rem=%u num=%u den=%u predicted=%d value=%02X\n",
          (unsigned long long)rf033_before_age,
          (unsigned long long)SNES::ur_qa01_rf030_spc_age,
          (int)rf033_cpu_h_before, (unsigned)::CPU.V_Counter,
          (int)rf033_reference_time, (unsigned)rf033_remainder,
          (unsigned)rf033_numerator, (unsigned)rf033_denominator,
          rf033_expected_ticks, (unsigned)byte);
    }""",
    1)

NATIVE_OLD = """    uint64_t guest_cycle = rtl_apu_guest_cycle();
    while (!apu_schedulePortWrite(g_snes->apu, port, val, guest_cycle))
      apu_cycle(g_snes->apu);"""
NATIVE_NEW = r"""    uint64_t guest_cycle = rtl_apu_guest_cycle();
    /* UR_QA01_RF033_MASTER_APU_CLOCK: actual AOT CPU writer clock, read-only. */
    if (port == 0 && val == 0xcc && getenv("UR_QA01_RF033_MASTER_APU_CLOCK") &&
        g_snes->apu->portClock >= 103322420ull &&
        g_snes->apu->portClock <= 103323100ull) {
      static unsigned rf033_writer_count;
      if (rf033_writer_count++ < 128) {
        fprintf(stderr,
          "QA01RF033NATIVE age=%llu guest=%llu master=%llu frame=%llu framestart=%llu extended=%u valid=%u value=%02X pc=%04X\n",
          (unsigned long long)g_snes->apu->portClock,
          (unsigned long long)guest_cycle,
          (unsigned long long)g_cpu.master_cycles,
          (unsigned long long)snes_frame_counter,
          (unsigned long long)g_apu_frame_start_master,
          (unsigned)g_extended_frame_timing,
          (unsigned)g_apu_frame_time_valid, (unsigned)val,
          (unsigned)g_snes->apu->spc->pc);
      } else if (rf033_writer_count == 129) {
        fprintf(stderr, "QA01RF033NATIVE_TRUNCATED\n");
      }
    }
    while (!apu_schedulePortWrite(g_snes->apu, port, val, guest_cycle))
      apu_cycle(g_snes->apu);"""

def _patch(source: str, before: str, after: str, side: str) -> str:
    if MARK in source:
        if source.count(after) != 1:
            raise ValueError(f"partial/tampered RF033 {side}")
        return source
    if source.count(before) != 1:
        raise ValueError(f"unrecognized exact pinned {side}; source stage not present")
    return source.replace(before, after, 1)

def patch_original(source: str) -> str:
    if "UR_QA01_RF030_IPL_ECHO" not in source:
        raise ValueError("original RF030 read-only source stage is mandatory")
    return _patch(source, ORIGINAL_OLD, ORIGINAL_NEW, "Snes9x apu.cpp")

def patch_native(source: str) -> str:
    if "static uint64_t rtl_apu_guest_cycle(void)" not in source:
        raise ValueError("pinned native guest APU clock mapping absent")
    return _patch(source, NATIVE_OLD, NATIVE_NEW, "Baldosa common_rtl.c")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("side", choices=("original", "native"))
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    path = a.root.resolve() / (ORIG if a.side == "original" else NATIVE)
    if not path.is_file():
        p.error(f"missing exact pinned {path}")
    before = path.read_text(encoding="utf8")
    after = (patch_original if a.side == "original" else patch_native)(before)
    if before != after:
        path.write_text(after, encoding="utf8")
    print(f"RF033 {a.side}: {'already' if before == after else 'read-only clock probe staged'} {path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
