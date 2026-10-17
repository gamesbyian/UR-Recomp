#!/usr/bin/env python3
"""RF037 disposable original/native sound transaction observer.

Stage strictly after source-pinned RF030..035 observers. It only prints
actual CPU sound instructions, pointer reads and CPU/SPC port events.
No clock, CPU/APU state, queue target, input or ROM mutation.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf035_sound_consumer_observer as rf035
import qa01_rf034_spc_opcode_boundary_observer as rf034
import qa01_ipl_echo_trace_patch as rf030

MARK = "UR_QA01_RF037_SOUND_BUS"
ORIGINAL = (
    (Path("cpuexec.cpp"), "cpu"),
    (Path("apu/apu.cpp"), "apu"),
    (Path("apu/bapu/smp/core.cpp"), "spc"),
)
NATIVE = (
    (Path("snesrecomp/runner/src/cpu_state.c"), "cpu"),
    (Path("snesrecomp/runner/src/snes/apu.c"), "apu"),
)

OPCODE_AFTER = r"""            /* UR_QA01_RF037_SOUND_BUS: unchanged post-opcode state. */
            if (ur_rf035_sound && getenv("UR_QA01_RF037_SOUND_BUS") &&
                (unsigned)ICPU.Frame >= 6070u && (unsigned)ICPU.Frame <= 6080u) {
                static unsigned last_frame = 0xffffffffu, count;
                unsigned f = (unsigned)ICPU.Frame;
                if (last_frame != f) { last_frame = f; count = 0; }
                if (count++ < 5000u)
                    fprintf(stderr, "QA01RF037ORIGOP frame=%u v=%u h=%d pc=%02X:%04X op=%02X a0=%04X a1=%04X y=%04X dp63=%02X dp64=%02X dp65=%02X dp69=%02X\n",
                            f, (unsigned)CPU.V_Counter, (int)CPU.Cycles,
                            ur_rf035_bank, ur_rf035_pc, ur_rf035_op,
                            ur_rf035_a0, (unsigned)Registers.A.W, ur_rf035_y0,
                            ur_rf035_dp63, ur_rf035_dp64, ur_rf035_dp65,
                            ur_rf035_dp69);
                else if (count == 5001u)
                    fprintf(stderr, "QA01RF037ORIGOP_TRUNCATED frame=%u\n", f);
            }
"""
ORIGINAL_APU_WRITE = "    SNES::cpu.port_write(port & 3, byte);\n"
ORIGINAL_APU_EXTRA = r"""    /* UR_QA01_RF037_SOUND_BUS: original CPU 2142/2143 publication. */
    if ((port & 3) >= 2 && getenv("UR_QA01_RF037_SOUND_BUS")) {
        uint64_t age = SNES::ur_qa01_rf030_spc_age;
        if ((age >= 103310000ull && age <= 103355000ull) ||
            (age >= 103390000ull && age <= 103450000ull))
            fprintf(stderr, "QA01RF037ORIGCPU age=%llu v=%u h=%d port=%u val=%02X\n",
                    (unsigned long long)age, (unsigned)::CPU.V_Counter,
                    (int)::CPU.Cycles, (unsigned)(port & 3), (unsigned)byte);
    }
"""
ORIGINAL_SPC_READ = "  if((addr & 0xfff0) == 0x00f0) return mmio_read(addr);\n"
ORIGINAL_SPC_EXTRA = r"""  /* UR_QA01_RF037_SOUND_BUS: source SPC F6/F7 read, exactly once. */
  if ((addr == 0xf6 || addr == 0xf7) &&
      getenv("UR_QA01_RF037_SOUND_BUS") &&
      ((ur_qa01_rf030_spc_age >= 103310000ull &&
        ur_qa01_rf030_spc_age <= 103355000ull) ||
       (ur_qa01_rf030_spc_age >= 103390000ull &&
        ur_qa01_rf030_spc_age <= 103450000ull))) {
    uint8 observed = mmio_read(addr);
    fprintf(stderr, "QA01RF037ORIGSPC age=%llu v=%u h=%d pc=%04X port=%u val=%02X\n",
            (unsigned long long)ur_qa01_rf030_spc_age,
            (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
            (unsigned)regs.pc, (unsigned)(addr - 0xf4), (unsigned)observed);
    return observed;
  }
"""
NATIVE_PTR_HELPER = r"""/* UR_QA01_RF037_SOUND_BUS: exact native pointer consumer, read only. */
static void ur_qa01_rf037_ptr(CpuState *cpu, uint8 bank, uint16 addr,
                             uint16 value, unsigned width) {
    extern int snes_frame_counter;
    extern const char *g_last_recomp_func;
    int f = snes_frame_counter;
    if (!getenv("UR_QA01_RF037_SOUND_BUS") || f < 6055 || f > 6064)
        return;
    unsigned end = (unsigned)addr + width;
    if (!(((unsigned)addr <= 0x63u && 0x63u < end) ||
          ((unsigned)addr <= 0x64u && 0x64u < end) ||
          ((unsigned)addr <= 0x65u && 0x65u < end) ||
          ((unsigned)addr <= 0x69u && 0x69u < end)))
        return;
    static int last_frame = -1;
    static unsigned count;
    if (last_frame != f) { last_frame = f; count = 0; }
    if (count++ < 8000u)
        fprintf(stderr, "QA01RF037NATIVEPTR frame=%d bank=%02X addr=%04X width=%u val=%04X A=%04X scope=%s\n",
                f, (unsigned)bank, (unsigned)addr, width,
                (unsigned)value, (unsigned)cpu->A,
                g_last_recomp_func ? g_last_recomp_func : "?");
    else if (count == 8001u)
        fprintf(stderr, "QA01RF037NATIVEPTR_TRUNCATED frame=%d\n", f);
}

"""
NATIVE_PTR_BYTE = "    ur_qa01_rf035_read(cpu, bank, addr, value, 1);\n"
NATIVE_PTR_WORD = (
    "        ur_qa01_rf035_read(cpu, bank, addr,\n"
    "                            (uint16)lo | ((uint16)hi << 8), 2);\n"
)
NATIVE_APU_HELPER = r"""/* UR_QA01_RF037_SOUND_BUS: actual queue / publish / SPC reads. */
static void ur_qa01_rf037_port(Apu *apu, const char *kind, uint8_t port,
                              uint8_t value, uint64_t target) {
  extern int snes_frame_counter;
  int f = snes_frame_counter;
  if (!getenv("UR_QA01_RF037_SOUND_BUS") || port < 2 ||
      f < 6055 || f > 6064) return;
  static int last_frame = -1;
  static unsigned count;
  if (last_frame != f) { last_frame = f; count = 0; }
  if (count++ < 16000u)
    fprintf(stderr, "QA01RF037NATIVEBUS kind=%s frame=%d age=%llu target=%llu pc=%04X port=%u val=%02X q=%u\n",
            kind, f, (unsigned long long)apu->portClock,
            (unsigned long long)target, (unsigned)apu->spc->pc,
            (unsigned)port, (unsigned)value,
            (unsigned)(apu->portQTail - apu->portQHead));
  else if (count == 16001u)
    fprintf(stderr, "QA01RF037NATIVEBUS_TRUNCATED frame=%d\n", f);
}

"""
NATIVE_APU_HEADER = "void apu_writePortNow(Apu* apu, uint8_t port, uint8_t val) {"
NATIVE_APU_SCHEDULE = "  apu->portLastTarget = target;\n"
NATIVE_APU_APPLY = "  apu_writePortNow(apu, w->port, w->val);"
NATIVE_APU_READ = '      if (adr == 0xf4) ur_qa01_rf030_native(apu, "read", v);'

def splice(src: str, marker: str, replacements: tuple[tuple[str, str], ...],
           description: str) -> str:
    if marker in src:
        if not all(src.count(new) == 1 for _, new in replacements):
            raise ValueError("RF037 tampered "+description)
        return src
    for before, after in replacements:
        if src.count(before) != 1:
            raise ValueError("RF037 unknown source "+description)
        src = src.replace(before, after, 1)
    return src

def original_cpu(src: str) -> str:
    if rf035.MARK not in src: raise ValueError("requires RF035 original")
    return splice(src, "QA01RF037ORIGOP",
                  ((rf035.ORIG_AFTER, rf035.ORIG_AFTER+OPCODE_AFTER),),
                  "original opcode")

def original_apu(src: str) -> str:
    if rf034.MARK not in src: raise ValueError("requires RF034 original")
    return splice(src, "QA01RF037ORIGCPU",
                  ((ORIGINAL_APU_WRITE, ORIGINAL_APU_WRITE+ORIGINAL_APU_EXTRA),),
                  "original CPU bus")

def original_spc(src: str) -> str:
    if rf030.MARK not in src: raise ValueError("requires RF030 original")
    return splice(src, "QA01RF037ORIGSPC",
                  ((ORIGINAL_SPC_READ, ORIGINAL_SPC_EXTRA+ORIGINAL_SPC_READ),),
                  "original SPC recipient")

def native_cpu(src: str) -> str:
    if rf035.MARK not in src: raise ValueError("requires RF035 native")
    return splice(src, "QA01RF037NATIVEPTR", (
        (rf035.NATIVE_HELPER, rf035.NATIVE_HELPER+NATIVE_PTR_HELPER),
        (NATIVE_PTR_BYTE, NATIVE_PTR_BYTE +
         "    ur_qa01_rf037_ptr(cpu, bank, addr, value, 1);\n"),
        (NATIVE_PTR_WORD, NATIVE_PTR_WORD +
         "        ur_qa01_rf037_ptr(cpu, bank, addr,\n"
         "                            (uint16)lo | ((uint16)hi << 8), 2);\n"),
    ), "native pointer")

def native_apu(src: str) -> str:
    if rf034.MARK not in src: raise ValueError("requires RF034 native")
    return splice(src, "QA01RF037NATIVEBUS", (
        (NATIVE_APU_HEADER, NATIVE_APU_HELPER+NATIVE_APU_HEADER),
        (NATIVE_APU_SCHEDULE, NATIVE_APU_SCHEDULE +
         '  ur_qa01_rf037_port(apu, "schedule", (uint8_t)(port & 3), val, target);\n'),
        (NATIVE_APU_APPLY,
         '  ur_qa01_rf037_port(apu, "apply", w->port, w->val, w->target_cycle);\n'+
         NATIVE_APU_APPLY),
        (NATIVE_APU_READ, NATIVE_APU_READ+
         '\n      ur_qa01_rf037_port(apu, "spc-read", (uint8_t)(adr - 0xf4), v, apu->portClock);'),
    ), "native CPU/SPC bus")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("side", choices=("original", "native"))
    p.add_argument("--root", type=Path, required=True)
    args = p.parse_args()
    root = args.root.resolve()
    tasks = ((ORIGINAL[0][0], original_cpu),
             (ORIGINAL[1][0], original_apu),
             (ORIGINAL[2][0], original_spc)) if args.side == "original" else (
             (NATIVE[0][0], native_cpu), (NATIVE[1][0], native_apu))
    updates = []
    for rel, func in tasks:
        path = root / rel
        if not path.is_file(): p.error("missing pinned source "+str(path))
        before = path.read_text(encoding="utf8")
        updates.append((path, before, func(before)))
    for path, before, after in updates:
        if before != after: path.write_text(after, encoding="utf8")
        print("RF037 "+str(path)+": "+("unchanged" if before==after else "observer staged"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
