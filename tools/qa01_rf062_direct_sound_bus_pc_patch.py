#!/usr/bin/env python3
"""RF062: preserve Baldosa paced-bus accounting, then bind real Read to PC.

Research-only disposable pinned native sources. The v2 emitter first counts
the ORIGINAL decoded IR data access as a paced guest bus byte. Only AFTER
that accounting, a source-stamped 82:82F0 Read callsite is replaced with the
single-bus-read observer. A naive replacement before _pace_bus_lines would
double-charge the guest CPU master clock and is explicitly forbidden.
"""
from __future__ import annotations

import argparse
from pathlib import Path

GEN = Path("snesrecomp/recompiler/v2/codegen.py")
EMITTER = Path("snesrecomp/recompiler/v2/emit_function.py")
CPU = Path("snesrecomp/runner/src/cpu_state.c")
HEADER = Path("snesrecomp/runner/src/cpu_state.h")
STAMP = "UR_QA01_RF062_DIRECT_CPU_BUS_GUEST_PC"
SITE = "UR_QA01_RF062_DIRECT_PC_8282F0"

READ_SITE = ("def _emit_read(op: Read) -> List[str]:\n"
             "    bank, addr = _segref_addr_expr(op.seg)\n")
READ_SITE_RF018 = (
    "def _emit_read(op: Read) -> List[str]:\n"
    "    prelude, bank, addr = _segref_hoisted(op.seg)\n"
)
READ_PATCH_RF018 = """    # UR_QA01_RF062_DIRECT_CPU_BUS_GUEST_PC: RF018 hoists the
    # [dp],Y pointer exactly once. Keep its prelude and account any
    # actual paced guest reads before substituting this single operand.
    if _CURRENT_SOURCE_PC24 == 0x8282F0 and op.width == 1:
        return prelude + [f"{widths.ctype(op.width)} {_v(op.out)} = "
                          f"{widths.read_fn(op.width)}(cpu, {bank}, {addr}); /* UR_QA01_RF062_DIRECT_PC_8282F0 */"]
"""
READ_PATCH = """    # UR_QA01_RF062_DIRECT_CPU_BUS_GUEST_PC: source decoded opcode PC.
    # Mark but DO NOT replace this real cpu_read8 call before pacing pass.
    if _CURRENT_SOURCE_PC24 == 0x8282F0 and op.width == 1:
        return [f"{widths.ctype(op.width)} {_v(op.out)} = "
                f"{widths.read_fn(op.width)}(cpu, {bank}, {addr}); /* UR_QA01_RF062_DIRECT_PC_8282F0 */"]
"""
PACE_SITE = (
    '        data_bytes += sum(1 if m.group(1) == "8" else 2 for m in _PACED_RE.finditer(ln))\n'
    '        out.append(ln)\n')
PACE_PATCH = """        data_bytes += sum(1 if m.group(1) == "8" else 2 for m in _PACED_RE.finditer(ln))
        # UR_QA01_RF062_DIRECT_CPU_BUS_GUEST_PC: account the real guest
        # data byte FIRST, then instrument only its returned value.
        if "UR_QA01_RF062_DIRECT_PC_8282F0" in ln:
            if not ln.count("cpu_read8_paced("):
                raise ValueError("RF062 82:82F0 guest Read did not use paced bus")
            ln = ln.replace("cpu_read8_paced(", "ur_rf062_read8_pc_8282f0(", 1)
        out.append(ln)
"""
CPU_SITE = "uint8_t cpu_read8_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {\n"
HEADER_SITE = "uint8  cpu_read8_paced (CpuState *cpu, uint8 bank, uint16 addr);\n"
PROTOTYPE = "uint8 ur_rf062_read8_pc_8282f0(CpuState *cpu, uint8 bank, uint16 addr);\n"
HELPER = r"""/* UR_QA01_RF062_DIRECT_CPU_BUS_GUEST_PC
 * Replaces ONLY the original 82:82F0 IR read AFTER the ordinary paced
 * emitter counted that guest bus byte for static clock subtraction.
 * Never read a pointer/ROM byte speculatively or add an SPC/CPU tick.
 */
uint8 ur_rf062_read8_pc_8282f0(CpuState *cpu, uint8 bank, uint16 addr) {
    uint8 value = cpu_read8_paced(cpu, bank, addr);
    extern int snes_frame_counter;
    if (getenv("UR_QA01_RF062_SOUND_DIRECT_PC") &&
        snes_frame_counter == 6124 &&
        bank == 0x11u && addr >= 0xC770u && addr <= 0xC779u) {
        static unsigned seq;
        if (++seq <= 8192u)
            fprintf(stderr,
                "QA01RF062NATIVE seq=%u f=%d executedPC=8282F0"
                " master=%llu addr=%02X%04X value=%02X A=%04X"
                " Y=%04X D=%04X dp63=%02X dp64=%02X dp65=%02X\n",
                seq, snes_frame_counter,
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


def patch(gen: str, emitter: str, cpu: str, header: str) -> tuple[str, str, str, str]:
    if any(STAMP in text for text in (gen, emitter, cpu, header)):
        raise ValueError("RF062 already/partially staged")
    if "_CURRENT_SOURCE_PC24" not in gen or "widths.read_fn(op.width)" not in gen or \
       "_pace_bus_lines" not in emitter or "_PACED_RE" not in emitter:
        raise ValueError("RF062 original per-Read or paced-byte attribution missing")
    if CPU_SITE not in cpu or "return cpu_read8(cpu, bank, addr);" not in cpu:
        raise ValueError("RF062 real paced native CPU reader missing")
    # RF018's pointer-once correction is legitimately staged before this
    # observer in the genuine Zoo workflow. Never revert to the pre-RF018
    # emitter, drop the hoisted pointer prelude or accept an unknown shape.
    bare = gen.count(READ_SITE)
    corrected = gen.count(READ_SITE_RF018)
    if bare + corrected != 1:
        raise ValueError("RF062 exact pinned or RF018-corrected Read IR source drift")
    if corrected:
        if "UR_BALDOSA_DP_INDIRECT_LONG_POINTER_ONCE" not in gen or (
                gen.count("return prelude + [f") != 1):
            raise ValueError("RF062 RF018 pointer-once producer incomplete")
        gen = replace_one(gen, READ_SITE_RF018,
                          READ_SITE_RF018 + READ_PATCH_RF018,
                          "RF018 pointer-once Read IR")
    else:
        if "UR_BALDOSA_DP_INDIRECT_LONG_POINTER_ONCE" in gen:
            raise ValueError("RF062 RF018 marker without corrected Read IR")
        gen = replace_one(gen, READ_SITE, READ_SITE + READ_PATCH,
                          "v2 decoded source Read IR")
    emitter = replace_one(emitter, PACE_SITE, PACE_PATCH,
                          "v2 paced guest byte accounting")
    cpu = replace_one(cpu, CPU_SITE, HELPER + CPU_SITE, "actual paced CPU helper")
    header = replace_one(header, HEADER_SITE, HEADER_SITE + PROTOTYPE,
                         "actual paced CPU declaration")
    if cpu.count("uint8 value = cpu_read8_paced(cpu, bank, addr);") != 1 or \
       emitter.count('ln.replace("cpu_read8_paced(", "ur_rf062_read8_pc_8282f0(", 1)') != 1:
        raise AssertionError("RF062 duplicated guest bus read or clock accounting stage")
    return gen, emitter, cpu, header


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    a = p.parse_args()
    paths = [a.root.resolve() / x for x in (GEN, EMITTER, CPU, HEADER)]
    if not all(x.is_file() for x in paths):
        p.error("missing pinned native v2 codegen/runtime")
    previous = [x.read_text(encoding="utf8") for x in paths]
    changed = patch(*previous)
    for target, new in zip(paths, changed):
        target.write_text(new, encoding="utf8")
    print("RF062 staged AFTER paced-byte accounting: exact CPU guest bus call unchanged")


if __name__ == "__main__":
    main()
