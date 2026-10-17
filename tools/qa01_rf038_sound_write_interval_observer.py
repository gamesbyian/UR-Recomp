#!/usr/bin/env python3
"""RF038 disposable original opcode / native AOT paced-access probe.

Single exact USA Zoo 156-master-clock interval at original source CPU frame
6073, V116 and native host6091. Stage after RF037 in separately pinned
original/native research checkouts. Emits read-only evidence. Never changes
clock charges, I/O bus calls, real guest state, timing, input or source ROM.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf035_sound_consumer_observer as rf035
import qa01_rf037_sound_transaction_window as rf037
import qa01_rf037_upstream_writer_observer as upstream

MARK = "UR_QA01_RF038_SOUND_WRITE_INTERVAL"
ORIGINAL = Path("cpuexec.cpp")
NATIVE = Path("snesrecomp/runner/src/cpu_state.c")
OLD_DISPATCH = rf035.ORIG_DISPATCH
ORIG_DISPATCH = r"""            /* UR_QA01_RF038_SOUND_WRITE_INTERVAL: exact real opcode boundary. */
            const int rf038_active =
                getenv("UR_QA01_RF038_INTERVAL") &&
                (unsigned)ICPU.Frame == 6073u &&
                (unsigned)CPU.V_Counter == 116u &&
                (int)CPU.Cycles >= 300 && (int)CPU.Cycles <= 1050;
            const unsigned rf038_pb = rf038_active ? (unsigned)Registers.PB : 0u;
            const unsigned rf038_pc = rf038_active ? (unsigned)Registers.PCw : 0u;
            const unsigned rf038_op = rf038_active ? (unsigned)Op : 0u;
            const int rf038_h = rf038_active ? (int)CPU.Cycles : 0;
""" + OLD_DISPATCH + r"""
            if (rf038_active) {
                static unsigned rf038_rows;
                if (rf038_rows++ < 512u)
                    fprintf(stderr,
                       "QA01RF038ORIGOP frame=%u v=116 pre_h=%d post_v=%u post_h=%d pc=%02X:%04X opcode=%02X nextpc=%02X:%04X a=%04X x=%04X y=%04X s=%04X\n",
                       (unsigned)ICPU.Frame, rf038_h,
                       (unsigned)CPU.V_Counter, (int)CPU.Cycles,
                       rf038_pb, rf038_pc, rf038_op,
                       (unsigned)Registers.PB, (unsigned)Registers.PCw,
                       (unsigned)Registers.A.W, (unsigned)Registers.X.W,
                       (unsigned)Registers.Y.W, (unsigned)Registers.S.W);
                else if (rf038_rows == 513u)
                    fprintf(stderr, "QA01RF038ORIGOP_TRUNCATED frame=6073 v=116\n");
            }
"""
HEADERS = (
    ("uint8_t cpu_read8_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {", "read8"),
    ("uint16_t cpu_read16_paced(CpuState *cpu, uint8_t bank, uint16_t addr) {", "read16"),
    ("void cpu_write8_paced(CpuState *cpu, uint8_t bank, uint16_t addr, uint8_t v) {", "write8"),
    ("void cpu_write16_paced(CpuState *cpu, uint8_t bank, uint16_t addr, uint16_t v) {", "write16"),
)
NATIVE_HELPER = r"""/* UR_QA01_RF038_SOUND_WRITE_INTERVAL: live source-paced bus charge. */
static void ur_rf038_paced(CpuState *cpu, const char *kind,
                           uint8 bank, uint16 addr, uint32_t charge) {
    extern int snes_frame_counter;
    extern const char *g_last_recomp_func;
    if (!getenv("UR_QA01_RF038_INTERVAL") ||
        snes_frame_counter != 6091 ||
        cpu->master_cycles < 2176886750ull ||
        cpu->master_cycles > 2176887550ull) return;
    static unsigned count;
    if (count++ < 256u)
        fprintf(stderr,
            "QA01RF038NATIVEPACE frame=%d master=%llu op=%s bank=%02X addr=%04X charge=%u scope=%s\n",
            snes_frame_counter, (unsigned long long)cpu->master_cycles,
            kind, (unsigned)bank, (unsigned)addr, (unsigned)charge,
            g_last_recomp_func ? g_last_recomp_func : "?");
    else if (count == 257u)
        fprintf(stderr, "QA01RF038NATIVEPACE_TRUNCATED frame=6091\n");
}

"""
CHARGE = "    cpu->master_cycles += _sp;\n"


def patch_original(src: str) -> str:
    if MARK in src:
        if src.count(ORIG_DISPATCH) != 1:
            raise ValueError("partial RF038 original opcode probe")
        return src
    if rf037.OPCODE_AFTER not in src or src.count(OLD_DISPATCH) != 1:
        raise ValueError("requires RF037 staged real original opcode dispatch")
    out = src.replace(OLD_DISPATCH, ORIG_DISPATCH, 1)
    if out.count("(*Opcodes[Op].S9xOpcode)();") != src.count(
            "(*Opcodes[Op].S9xOpcode)();"):
        raise AssertionError("original CPU dispatch altered")
    return out


def patch_native(src: str) -> str:
    if MARK in src:
        if (src.count(NATIVE_HELPER) != 1 or
                any(src.count(f'ur_rf038_paced(cpu, "{k}", bank, addr, _sp);') != 1
                    for _, k in HEADERS)):
            raise ValueError("partial RF038 native paced probe")
        return src
    if upstream.MARK not in src:
        raise ValueError("requires RF037 upstream native source staging")
    if any(src.count(header) != 1 for header, _ in HEADERS):
        raise ValueError("unknown exact pinned native paced source")
    # Only four authoritative paced bus transfer helpers. Preserve the
    # exact original charge and exactly one existing underlying bus call.
    for header, kind in HEADERS:
        start = src.index(header)
        charge_at = src.find(CHARGE, start)
        if charge_at < 0 or charge_at - start > 700:
            raise ValueError("unknown exact paced charge in "+kind)
        src = (src[:charge_at] + CHARGE +
               f'    ur_rf038_paced(cpu, "{kind}", bank, addr, _sp);\n' +
               src[charge_at + len(CHARGE):])
    first = HEADERS[0][0]
    return src.replace(first, NATIVE_HELPER + first, 1)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("side", choices=("original", "native"))
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    file = a.root.resolve() / (ORIGINAL if a.side == "original" else NATIVE)
    if not file.is_file():
        p.error("missing pinned original/native source: "+str(file))
    old = file.read_text(encoding="utf8")
    new = (patch_original if a.side == "original" else patch_native)(old)
    if new != old:
        file.write_text(new, encoding="utf8")
    print("RF038 " + a.side + ": " + ("already staged" if new == old else "read-only interval probe staged"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
