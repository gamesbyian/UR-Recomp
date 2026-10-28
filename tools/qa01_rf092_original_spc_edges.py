#!/usr/bin/env python3
"""RF092: disposable, read-only original SPC port-consumption/ready observer.

Patch the pinned Snes9x Bapu SMP implementation, never the checked-in core.
Count actual SMP tick units since reset, not CPU master cycles. A CPU->SPC
receipt is an executed SMP MMIO read of $F4-$F7; an SPC->CPU ready
publication is an executed SMP MMIO write. Neither is inferred from a
CPU-side $2140 read, nor are the two clock domains assumed aligned.
"""
import argparse
from pathlib import Path

SMP = Path("apu/bapu/smp/smp.cpp")
CORE = Path("apu/bapu/smp/core.cpp")
MEMORY = Path("apu/bapu/smp/memory.cpp")
STAMP = "UR_QA01_RF092_ORIGINAL_SPC_EDGES"
SMP_HEADER = ('#ifdef DEBUGGER\n'
              '#include "../../../snes9x.h"\n'
              '#include "../../../debug.h"\n')
SMP_SINGLETON = "SMP smp;\n"
SMP_RESET = "void SMP::reset() {\n"
CORE_SINGLE = "  clock++;\n  dsp.clock++;\n"
CORE_MULTI = "  clock += clocks;\n  dsp.clock += clocks;\n"
MEMORY_READ = ("""  case 0xf4:
  case 0xf5:
  case 0xf6:
  case 0xf7:
    return cpu.port_read(addr);""")
MEMORY_WRITE = ("""  case 0xf4:
  case 0xf5:
  case 0xf6:
  case 0xf7:
    port_write(addr, data);
    break;""")
HELPER = r'''
/* UR_QA01_RF092_ORIGINAL_SPC_EDGES
 * The counter advances ONLY with the existing SMP tick methods and resets
 * with the actual SMP. This is an original-SPC-relative clock, not a SNES
 * CPU master-cycle stamp. regs.pc is the next SPC PC, not a fetched opcode
 * identity. Logging never performs an extra MMIO read or write. */
static unsigned long long rf092_spc_ticks;
static unsigned rf092_rows;
static void rf092_spc_port(const char *kind, unsigned addr, unsigned value) {
  const char *flag = std::getenv("UR_QA01_RF092_ORIGINAL_SPC");
  if (!flag || flag[0] != '1' || flag[1] != '\0') return;
  const unsigned frame = (unsigned)ICPU.Frame;
  if (frame < 6054u || frame > 6059u ||
      addr < 0xf4u || addr > 0xf7u) return;
  if (++rf092_rows > 16384u) {
    if (rf092_rows == 16385u)
      std::fprintf(stderr, "QA01RF092SPC_TRUNCATED\n");
    return;
  }
  std::fprintf(stderr,
    "QA01RF092SPC seq=%u frame=%u kind=%s addr=%04X val=%02X"
    " spc_ticks=%llu spc_next_pc=%04X clock=original_spc\n",
    rf092_rows, frame, kind, addr, value & 0xffu,
    rf092_spc_ticks, (unsigned)smp.regs.pc);
}
'''

def patch(smp: str, core: str, memory: str) -> tuple[str, str, str]:
    """Fail closed on source drift, partial staging or ambiguous callsites."""
    if any(STAMP in s or "rf092_spc_port" in s or "rf092_spc_ticks" in s
           for s in (smp, core, memory)):
        raise ValueError("RF092 already or partly staged")
    required = ((smp, SMP_HEADER), (smp, SMP_SINGLETON),
                (smp, SMP_RESET), (core, CORE_SINGLE),
                (core, CORE_MULTI), (memory, MEMORY_READ),
                (memory, MEMORY_WRITE))
    if any(source.count(anchor) != 1 for source, anchor in required):
        raise ValueError("RF092 pinned original SMP source drift")
    # The include is already used under DEBUGGER in the pinned SMP. Make
    # it unconditional so ICPU.Frame is available in normal libretro builds.
    smp = smp.replace(
        SMP_HEADER,
        '#include "../../../snes9x.h"\n'
        '#include <cstdio>\n#include <cstdlib>\n'
        '#ifdef DEBUGGER\n#include "../../../debug.h"\n', 1)
    smp = smp.replace(SMP_SINGLETON, SMP_SINGLETON + HELPER, 1)
    smp = smp.replace(SMP_RESET, SMP_RESET +
                      "  rf092_spc_ticks = 0;\n  rf092_rows = 0;\n", 1)
    core = core.replace(CORE_SINGLE, CORE_SINGLE +
                        "  ++rf092_spc_ticks;\n", 1)
    core = core.replace(CORE_MULTI, CORE_MULTI +
                        "  rf092_spc_ticks += clocks;\n", 1)
    memory = memory.replace(
        MEMORY_READ,
        MEMORY_READ.replace(
            "    return cpu.port_read(addr);",
            "    {\n"
            "      const unsigned value = cpu.port_read(addr);\n"
            '      rf092_spc_port("CPU_TO_SPC_READ", addr, value);\n'
            "      return value;\n"
            "    }"), 1)
    memory = memory.replace(
        MEMORY_WRITE,
        MEMORY_WRITE.replace(
            "    port_write(addr, data);\n",
            "    port_write(addr, data);\n"
            '    rf092_spc_port("SPC_TO_CPU_WRITE", addr, data);\n'), 1)
    if (smp.count(STAMP) != 1 or
        core.count("++rf092_spc_ticks;") != 1 or
        core.count("rf092_spc_ticks += clocks;") != 1 or
        memory.count("cpu.port_read(addr)") != 1 or
        memory.count("rf092_spc_port(") != 2 or
        memory.count("port_write(addr, data);") != 1):
        raise AssertionError("RF092 must preserve one genuine MMIO read/write")
    return smp, core, memory

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    paths = [args.root / path for path in (SMP, CORE, MEMORY)]
    if any(not path.is_file() or path.is_symlink() for path in paths):
        parser.error("missing authentic non-symlink disposable Snes9x SMP sources")
    edited = patch(*(path.read_text(encoding="utf-8") for path in paths))
    for path, content in zip(paths, edited):
        path.write_text(content, encoding="utf-8")
    print("RF092 original SPC executed input receipt/output ready staged")

if __name__ == "__main__":
    main()
