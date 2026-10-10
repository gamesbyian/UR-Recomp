#!/usr/bin/env python3
"""Patch a DISPOSABLE, pinned Baldosa cpu_state.c WRAM logging hook.

Restrict the already existing SNESRECOMP_WLOG_ADDR hook to a small native
host-frame interval before it increments its event cap. No game-state
mutation, frame scheduling change, guest opcode edit, or production patch.
Never apply to the project's checked-in or installed framework source.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = "    if (addr < g_wlog_addr_lo || addr > g_wlog_addr_hi) return;\n"
STAMP = "UR_QA01_NATIVE_STACK_FRAME_GATE"


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("QA-01 native stack gate is already installed")
    if source.count(MARKER) != 1:
        raise ValueError("pinned Baldosa WRAM hook range-marker absent or ambiguous")
    addition = r"""    /* UR_QA01_NATIVE_STACK_FRAME_GATE: disposable read-only WRAM log. */
    static int ur_qa_stack_gate_init = 0;
    static long ur_qa_stack_first = 0x7fffffffL;
    static long ur_qa_stack_last = -1L;
    if (!ur_qa_stack_gate_init) {
        const char *first = getenv("UR_QA_NATIVE_STACK_FIRST");
        const char *last = getenv("UR_QA_NATIVE_STACK_LAST");
        if (first && first[0] && last && last[0]) {
            char *end_first = NULL, *end_last = NULL;
            long a = strtol(first, &end_first, 10);
            long b = strtol(last, &end_last, 10);
            if (end_first && *end_first == 0 && end_last &&
                *end_last == 0 && a >= 0 && b >= a && b - a <= 64) {
                ur_qa_stack_first = a;
                ur_qa_stack_last = b;
            }
        }
        ur_qa_stack_gate_init = 1;
    }
    extern int snes_frame_counter;
    if ((long)snes_frame_counter < ur_qa_stack_first ||
        (long)snes_frame_counter > ur_qa_stack_last)
        return;
"""
    return source.replace(MARKER, MARKER + addition, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", type=Path, help="disposable baldosa/snesrecomp/runner/src/cpu_state.c")
    args = ap.parse_args()
    target = args.source.resolve()
    if target.name != "cpu_state.c" or "snesrecomp" not in target.parts:
        raise ValueError("require a disposable snesrecomp/.../cpu_state.c path")
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
