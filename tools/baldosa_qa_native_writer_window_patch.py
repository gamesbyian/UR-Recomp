#!/usr/bin/env python3
"""Add a QA-only host-frame gate to Baldosa's pinned WRAM writer logger.

Applied ONLY to the disposable framework copy in the Zoo CI workflow.
The source game logic, host-frame execution and CPU bus writes are unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = """static void wlog_addr_note_via(uint8 bank, uint16 addr, uint16 v, int width,
                               const char *via) {
    if (addr < g_wlog_addr_lo || addr > g_wlog_addr_hi) return;
    if (g_wlog_addr_n++ >= g_wlog_addr_cap) return;
    extern int snes_frame_counter;"""

STAMP = "UR-QA01-ZOO-FRAME-BOUNDED-WRAM-WRITER"

REPLACEMENT = """static void wlog_addr_note_via(uint8 bank, uint16 addr, uint16 v, int width,
                               const char *via) {
    /* UR-QA01-ZOO-FRAME-BOUNDED-WRAM-WRITER:
     * Observe the source-native WRAM writer only within a validated host-frame
     * window; never consume logger capacity on ordinary boot/gameplay writes.
     * This filter does not alter memory values or execution order. */
    extern int snes_frame_counter;
    static int ur_qa_zoo_initialized = 0;
    static long ur_qa_zoo_first = -1;
    static long ur_qa_zoo_last = -1;
    if (!ur_qa_zoo_initialized) {
        const char *first = getenv("UR_QA_ZOO_NATIVE_WRITE_FIRST");
        const char *last = getenv("UR_QA_ZOO_NATIVE_WRITE_LAST");
        char *end1 = NULL, *end2 = NULL;
        if (first && last) {
            ur_qa_zoo_first = strtol(first, &end1, 10);
            ur_qa_zoo_last = strtol(last, &end2, 10);
            if (!end1 || *end1 || !end2 || *end2 ||
                ur_qa_zoo_first < 1 || ur_qa_zoo_last < ur_qa_zoo_first)
                ur_qa_zoo_first = ur_qa_zoo_last = -1;
        }
        ur_qa_zoo_initialized = 1;
    }
    if (ur_qa_zoo_first < 0 || snes_frame_counter < ur_qa_zoo_first ||
        snes_frame_counter > ur_qa_zoo_last) return;
    if (addr < g_wlog_addr_lo || addr > g_wlog_addr_hi) return;
    if (g_wlog_addr_n++ >= g_wlog_addr_cap) return;"""


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError("QA frame gate already installed in this disposable copy")
    if source.count(MARKER) != 1:
        raise ValueError("pinned Baldosa cpu_state.c WRAM writer marker changed")
    return source.replace(MARKER, REPLACEMENT, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--framework-cpu-state", required=True, type=Path)
    args = ap.parse_args()
    source = args.framework_cpu_state.read_text(encoding="utf-8")
    args.framework_cpu_state.write_text(patch(source), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
