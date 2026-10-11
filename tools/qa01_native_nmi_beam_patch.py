#!/usr/bin/env python3
"""Add exact source-native NMI writer beam metadata to disposable Baldosa.

Apply only after qa01_native_switcher_stack_gate.py to the pinned
snesrecomp/runner/src/cpu_state.c. The existing opt-in WRAM logger owns
capture, frame bounds, event cap and file output. No guest operation changes.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import qa01_native_switcher_stack_gate as gate

STAMP = "UR_QA01_NATIVE_NMI_WRITER_BEAM_V1"
MARKER = "    fputc('\\n', g_wlog_addr_fp);\n    if (g_wlog_halt_off >= 0) {"


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("native NMI beam observer already installed")
    if gate.STAMP not in source:
        raise ValueError("install existing native frame-range logger gate first")
    if source.count(MARKER) != 1:
        raise ValueError("pinned native WRAM log terminator absent or ambiguous")
    extra = """    /* UR_QA01_NATIVE_NMI_WRITER_BEAM_V1: already address+frame gated.
     * Framework beam position is a MODELED snapshot, not proof the CPU
     * reached the same instruction/hardware phase as source Snes9x. */
    if (g_wlog_addr_state && g_snes && addr == 0x01DDu &&
        width == 2 && g_last_recomp_func &&
        strcmp(g_last_recomp_func, "I_NMI_M1X1") == 0) {
        fprintf(g_wlog_addr_fp,
                " QAbeam_v=%u QAbeam_h=%u QAbeam_master=%llu"
                " QAcpu_master=%llu",
                (unsigned)g_snes->vPos, (unsigned)g_snes->hPos,
                (unsigned long long)g_snes->beamMasterLast,
                (unsigned long long)g_cpu.master_cycles);
    }
"""
    return source.replace(MARKER, extra + MARKER, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    target = args.source.resolve()
    if target.name != "cpu_state.c" or "snesrecomp" not in target.parts:
        raise ValueError("only disposable snesrecomp/runner/src/cpu_state.c")
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
