#!/usr/bin/env python3
"""RF037 follow-up: source-pinned upstream port-writer coverage audit.

Read-only, disposable research guest instrumentation; requires prior RF037.
One origin frame window, one native host window. No additional SPC running,
reads, writes, scheduling, clock phase, input changes, or sampling exceptions.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf037_sound_transaction_window as rf037

MARK = "UR_QA01_RF037_UPSTREAM_WRITER"
ORIG_APU = Path("apu/apu.cpp")
NATIVE_RTL = Path("snesrecomp/runner/src/common_rtl.c")
NATIVE_CPU = Path("snesrecomp/runner/src/cpu_state.c")

# The first source probe's original CPU-port age band observed IPL only,
# although original opcode execution continues at ICPU.Frame 6072..6080.
# Keep source SPC-age, but qualify capture on *actual original CPU frame*.
OLD_ORIG = rf037.ORIGINAL_APU_EXTRA
NEW_ORIG = r"""    /* UR_QA01_RF037_UPSTREAM_WRITER: original 2142/2143, full frame. */
    if ((port & 3) >= 2 && getenv("UR_QA01_RF037_SOUND_BUS")) {
        const uint64_t ur_age = SNES::ur_qa01_rf030_spc_age;
        if (ur_age >= 103300000ull && ur_age <= 104200000ull) {
            /* apu.cpp cannot legally access cpuexec.cpp's ICPU singleton.
             * Partition by observed native-independent SPC age instead. */
            const unsigned ur_bucket = (unsigned)((ur_age - 103300000ull) / 16000ull);
            static unsigned ur_last_bucket = 0xffffffffu, ur_rows;
            if (ur_last_bucket != ur_bucket) { ur_last_bucket = ur_bucket; ur_rows = 0; }
            if (ur_rows++ < 8000u)
                fprintf(stderr,
                  "QA01RF037ORIGCPU2 bucket=%u age=%llu v=%u h=%d port=%u val=%02X\n",
                  ur_bucket, (unsigned long long)ur_age,
                  (unsigned)::CPU.V_Counter, (int)::CPU.Cycles,
                  (unsigned)(port & 3), (unsigned)byte);
            else if (ur_rows == 8001u)
                fprintf(stderr, "QA01RF037ORIGCPU2_TRUNCATED bucket=%u\n", ur_bucket);
        }
    }
"""
RTL_HEADER = "void WriteReg(uint16 reg, uint8 value) {\n"
RTL_PORT_BRANCH = "  } else if (reg >= 0x2140 && reg < 0x2180) {\n"
RTL_APU_HEADER = "void RtlApuWrite(uint16 adr, uint8 val) {\n"
RTL_ACCEPTED = "  if (rtl_apu_port_observers_filter(adr, val)) return;\n"
RTL_HELPER = r"""/* UR_QA01_RF037_UPSTREAM_WRITER: actual native CPU register dispatch. */
static void ur_rf037_upstream(const char *kind, uint16 reg, uint8 value) {
  extern int snes_frame_counter;
  extern const char *g_last_recomp_func;
  int frame = snes_frame_counter;
  if (!getenv("UR_QA01_RF037_SOUND_BUS") || reg < 0x2142 ||
      reg > 0x2143 || frame < 6055 || frame > 6064) return;
  static int last_frame = -1;
  static unsigned count;
  if (last_frame != frame) { last_frame = frame; count = 0; }
  if (count++ < 12000u)
    fprintf(stderr,
      "QA01RF037NATIVEUP kind=%s frame=%d master=%llu reg=%04X val=%02X scope=%s\n",
      kind, frame, (unsigned long long)g_cpu.master_cycles,
      (unsigned)reg, (unsigned)value,
      g_last_recomp_func ? g_last_recomp_func : "?");
  else if (count == 12001u)
    fprintf(stderr, "QA01RF037NATIVEUP_TRUNCATED frame=%d\n", frame);
}

"""
CPU_BYTE_HEADER = "void cpu_write8(CpuState *cpu, uint8 bank, uint16 addr, uint8 v) {\n"
CPU_WORD_HEADER = "void cpu_write16(CpuState *cpu, uint8 bank, uint16 addr, uint16 v) {\n"
CPU_BYTE_EXTRA = r"""    /* UR_QA01_RF037_UPSTREAM_WRITER: before authoritative CPU bus. */
    {
        extern int snes_frame_counter;
        extern const char *g_last_recomp_func;
        int f = snes_frame_counter;
        if (getenv("UR_QA01_RF037_SOUND_BUS") &&
            (addr == 0x2142u || addr == 0x2143u) && f >= 6055 && f <= 6064) {
            static int last_frame = -1;
            static unsigned count;
            if (last_frame != f) { last_frame = f; count = 0; }
            if (count++ < 12000u)
                fprintf(stderr,
                  "QA01RF037NATIVECPU kind=byte frame=%d master=%llu bank=%02X reg=%04X val=%02X scope=%s\n",
                  f, (unsigned long long)cpu->master_cycles,
                  (unsigned)bank, (unsigned)addr, (unsigned)v,
                  g_last_recomp_func ? g_last_recomp_func : "?");
            else if (count == 12001u)
                fprintf(stderr, "QA01RF037NATIVECPU_TRUNCATED frame=%d\n", f);
        }
    }
"""
CPU_WORD_EXTRA = CPU_BYTE_EXTRA.replace(
    "kind=byte", "kind=word").replace(
    'val=%02X', 'val=%04X').replace(
    '(addr == 0x2142u || addr == 0x2143u)', '(addr == 0x2142u || addr == 0x2143u)'
).replace('reg=%04X val=%04X scope=', 'reg=%04X val=%04X scope=')

def _one(src: str, pre: str, replacement: str, marker: str, label: str) -> str:
    if marker in src:
        if src.count(replacement) != 1:
            raise ValueError("RF037 partial/tampered "+label)
        return src
    if src.count(pre) != 1:
        raise ValueError("RF037 unknown exact "+label)
    return src.replace(pre, replacement, 1)

def original(src: str) -> str:
    if "QA01RF037ORIGCPU" not in src:
        raise ValueError("requires RF037 original port stage")
    return _one(src, OLD_ORIG, NEW_ORIG, MARK, "original CPU port")

def native_rtl(src: str) -> str:
    # The helper executes at the existing register API boundaries, before
    # mod filtering. No second call to the interceptors or to RtlApuWrite.
    if MARK in src:
        if (src.count(RTL_HELPER) != 1 or
            src.count('ur_rf037_upstream("write-reg", reg, value);') != 1 or
            src.count('ur_rf037_upstream("rtl-apu-enter", adr, val);') != 1):
            raise ValueError("RF037 partial native register writer stage")
        return src
    for anchor in (RTL_HEADER, RTL_PORT_BRANCH, RTL_APU_HEADER, RTL_ACCEPTED):
        if src.count(anchor) != 1:
            raise ValueError("RF037 unknown native common RTL source")
    src=src.replace(RTL_HEADER, RTL_HELPER+RTL_HEADER, 1)
    src=src.replace(RTL_PORT_BRANCH, RTL_PORT_BRANCH+
                    '    ur_rf037_upstream("write-reg", reg, value);\n', 1)
    src=src.replace(RTL_APU_HEADER, RTL_APU_HEADER+
                    '  ur_rf037_upstream("rtl-apu-enter", adr, val);\n', 1)
    src=src.replace(RTL_ACCEPTED, RTL_ACCEPTED+
                    '  ur_rf037_upstream("rtl-apu-after-filter", adr, val);\n', 1)
    return src

def native_cpu(src: str) -> str:
    if "QA01RF037NATIVEPTR" not in src:
        raise ValueError("requires RF037 native CPU pointer stage")
    if MARK in src:
        if src.count(CPU_BYTE_EXTRA) != 1 or src.count(CPU_WORD_EXTRA) != 1:
            raise ValueError("RF037 partial native CPU writer stage")
        return src
    if src.count(CPU_BYTE_HEADER) != 1 or src.count(CPU_WORD_HEADER) != 1:
        raise ValueError("RF037 unknown native CPU byte/word source")
    src=src.replace(CPU_BYTE_HEADER, CPU_BYTE_HEADER+CPU_BYTE_EXTRA, 1)
    src=src.replace(CPU_WORD_HEADER, CPU_WORD_HEADER+CPU_WORD_EXTRA, 1)
    return src

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("side", choices=("original","native"))
    p.add_argument("--root", type=Path, required=True)
    a=p.parse_args()
    tasks=((ORIG_APU,original),) if a.side=="original" else (
           (NATIVE_RTL,native_rtl),(NATIVE_CPU,native_cpu))
    root=a.root.resolve(); changes=[]
    for relative, fn in tasks:
        path=root/relative
        if not path.is_file(): p.error("missing exact "+str(path))
        before=path.read_text(encoding="utf8")
        changes.append((path,before,fn(before)))
    for path,before,after in changes:
        if after != before: path.write_text(after, encoding="utf8")
        print("RF037 upstream "+str(path)+": "+("unchanged" if before==after else "staged"))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
