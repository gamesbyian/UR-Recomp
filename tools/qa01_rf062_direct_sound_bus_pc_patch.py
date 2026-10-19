#!/usr/bin/env python3
"""RF062: read-only native 65816 executed guest-PC bound to real ROM helper.

Disposable pinned Baldosa v2 sources, never production code. Unlike RF055's
mode-dependent speculative marker, the ORIGINAL decoded 82:82F0 Read IR emits
a wrapper around the SINGLE existing cpu_read8_paced call in every generated
M/X variant. It logs only actual returned ROM bytes, never maps/peeks ROM or
assigns a stale interpreter PC. Build must prove the live M1X0 body contains
the wrapper before an authentic replay can qualify a sound consumer.
"""
from __future__ import annotations

import argparse
from pathlib import Path

GEN = Path("snesrecomp/recompiler/v2/codegen.py")
CPU = Path("snesrecomp/runner/src/cpu_state.c")
HEADER = Path("snesrecomp/runner/src/cpu_state.h")
STAMP = "UR_QA01_RF062_DIRECT_CPU_BUS_GUEST_PC"
READ_SITE = ("def _emit_read(op: Read) -> List[str]:\n"
             "    bank, addr = _segref_addr_expr(op.seg)\n")
READ_PATCH = """    # UR_QA01_RF062_DIRECT_CPU_BUS_GUEST_PC: this is the actual
    # decoder-supplied source opcode PC, not function scope/interp hint.
    if (_CURRENT_SOURCE_PC24 == 0x8282F0 and op.width == 1 and
            widths.read_fn(op.width) == "cpu_read8_paced"):
        return [f"{widths.ctype(op.width)} {_v(op.out)} = "
                f"ur_rf062_cpu_read8_pc(cpu, {bank}, {addr}, 0x8282F0u);"]
"""
CPU_SITE = "uint8_t cpu_read8_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {\n"
HEADER_SITE = "uint8  cpu_read8_paced (CpuState *cpu, uint8 bank, uint16 addr);\n"
PROTOTYPE = "uint8 ur_rf062_cpu_read8_pc(CpuState *cpu, uint8 bank, uint16 addr, uint32 pc);\n"
HELPER = r"""/* UR_QA01_RF062_DIRECT_CPU_BUS_GUEST_PC
 * Actual decoded 82:82F0 operand Read IR callsite, in *all* M/X variants.
 * The one original CPU bus call and its pace remain authoritative. Never
 * supply a value from a ROM pointer, probe a second bus read or modify CPU
 * master/SPC clocks. Independent recorder ordinal, not an RF054 join key.
 */
uint8 ur_rf062_cpu_read8_pc(CpuState *cpu, uint8 bank, uint16 addr, uint32 pc) {
    uint8 value = cpu_read8_paced(cpu, bank, addr);
    extern int snes_frame_counter;
    if (getenv("UR_QA01_RF062_SOUND_DIRECT_PC") &&
        snes_frame_counter == 6124 && pc == 0x8282F0u &&
        bank == 0x11u && addr >= 0xC770u && addr <= 0xC779u) {
        static unsigned seq;
        if (++seq <= 8192u)
            fprintf(stderr,
                "QA01RF062NATIVE seq=%u f=%d executedPC=%06X"
                " master=%llu addr=%02X%04X value=%02X A=%04X"
                " Y=%04X D=%04X dp63=%02X dp64=%02X dp65=%02X\n",
                seq, snes_frame_counter, (unsigned)pc,
                (unsigned long long)cpu->master_cycles,
                (unsigned)bank, (unsigned)addr, (unsigned)value,
                (unsigned)cpu->A, (unsigned)cpu->Y, (unsigned)cpu->D,
                (unsigned)cpu->ram[0x63], (unsigned)cpu->ram[0x64],
                (unsigned)cpu->ram[0x65]);
        else if (seq == 8193u)
            fprintf(stderr, "QA01RF062NATIVE_TRUNCATED\n");
    }
    return value;
}
"""

def replace_one(src: str, old: str, new: str, label: str) -> str:
    if src.count(old) != 1:
        raise ValueError("RF062 exact pinned " + label + " source drift")
    return src.replace(old, new, 1)


def patch(gen: str, cpu: str, header: str) -> tuple[str, str, str]:
    if any(STAMP in text for text in (gen, cpu, header)):
        raise ValueError("RF062 already/partially staged")
    if "_CURRENT_SOURCE_PC24" not in gen or "widths.read_fn(op.width)" not in gen:
        raise ValueError("RF062 decoded per-Read source opcode attribution missing")
    if "cpu_read8_paced(cpu, bank, addr)" not in cpu:
        raise ValueError("RF062 real paced native CPU reader missing")
    gen = replace_one(gen, READ_SITE, READ_SITE + READ_PATCH,
                      "v2 codegen source Read IR")
    cpu = replace_one(cpu, CPU_SITE, HELPER + CPU_SITE, "actual paced CPU helper")
    header = replace_one(header, HEADER_SITE, HEADER_SITE + PROTOTYPE,
                         "actual paced CPU declaration")
    if cpu.count("uint8 value = cpu_read8_paced(cpu, bank, addr);") != 1 or \
       gen.count("ur_rf062_cpu_read8_pc(cpu,") != 1:
        raise AssertionError("RF062 duplicated read or executable guest PC shim")
    return gen, cpu, header


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    a = p.parse_args()
    paths = [a.root.resolve() / x for x in (GEN, CPU, HEADER)]
    if not all(x.is_file() for x in paths):
        p.error("missing pinned Baldosa v2 generator/native runtime")
    original = [x.read_text(encoding="utf8") for x in paths]
    updated = patch(*original)
    for path, content in zip(paths, updated):
        path.write_text(content, encoding="utf8")
    print("RF062 direct executed guest-PC wrapper staged; rebuild generated M1X0 source")


if __name__ == "__main__":
    main()
