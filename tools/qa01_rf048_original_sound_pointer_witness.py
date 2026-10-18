#!/usr/bin/env python3
"""RF048 read-only original Snes9x LDA [$63],Y actual source-side sound consumer.

Installs after the already source-qualified RF035 logger and keeps the original
opcode dispatch untouched. It observes direct-page-register D, *raw mirrored
WRAM candidate* pointer bytes, Y and post-execution A at the actual opcode.
The raw pointer is not independently a bus read, so a non-WRAM DP bank is
reported as unmapped and never promoted as a proven effective address.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import qa01_rf035_sound_consumer_observer as rf035

MARK = "UR_QA01_RF048_ORIG_SOUND_POINTER"
ORIGINAL = Path("cpuexec.cpp")

AFTER = r"""
            /* UR_QA01_RF048_ORIG_SOUND_POINTER: one original opcode, no new bus call. */
            if (ur_rf035_sound && ur_rf035_pc == 0x82F0u &&
                getenv("UR_QA01_RF048_ORIG_SOUND_POINTER")) {
                const unsigned rf048_frame = (unsigned)ICPU.Frame;
                const unsigned rf048_d = (unsigned)Registers.D.W;
                const unsigned rf048_dp = (rf048_d + 0x63u) & 0xffffu;
                const int rf048_mirror = rf048_dp <= 0x1ffdu;
                const unsigned rf048_lo = rf048_mirror ?
                    (unsigned)Memory.RAM[rf048_dp] : 0u;
                const unsigned rf048_hi = rf048_mirror ?
                    (unsigned)Memory.RAM[rf048_dp+1u] : 0u;
                const unsigned rf048_bank = rf048_mirror ?
                    (unsigned)Memory.RAM[rf048_dp+2u] : 0u;
                const unsigned rf048_base = rf048_lo | (rf048_hi << 8) |
                                           (rf048_bank << 16);
                const unsigned rf048_y = (unsigned)Registers.Y.W;
                const unsigned rf048_effective = (rf048_base + rf048_y) & 0xffffffu;
                static unsigned rf048_total = 0u;
                static unsigned rf048_logged = 0u;
                static unsigned rf048_frame_count = 0u;
                static unsigned rf048_last_frame = 0xffffffffu;
                const int rf048_target = rf048_mirror &&
                     (((rf048_lo | (rf048_hi << 8)) >= 0xC770u &&
                       (rf048_lo | (rf048_hi << 8)) <= 0xC779u) ||
                      ((rf048_lo | (rf048_hi << 8)) >= 0xD0B0u &&
                       (rf048_lo | (rf048_hi << 8)) <= 0xD0B9u));
                /* The original uploader STZs base $63/$64, then increments
                 * Y. A raw zero base does not make the LDA target zero. */
                const unsigned rf048_indexed_low = rf048_effective & 0xffffu;
                const int rf048_indexed_target = rf048_mirror &&
                    ((rf048_indexed_low >= 0xC770u &&
                      rf048_indexed_low <= 0xC779u) ||
                     (rf048_indexed_low >= 0xD0B0u &&
                      rf048_indexed_low <= 0xD0B9u));
                if (rf048_last_frame != rf048_frame) {
                    if (rf048_last_frame != 0xffffffffu)
                        fprintf(stderr,
                           "QA01RF048ORIGCOUNT frame=%u actual_lda=%u\n",
                           rf048_last_frame, rf048_frame_count);
                    rf048_last_frame = rf048_frame;
                    rf048_frame_count = 0;
                }
                ++rf048_frame_count;
                ++rf048_total;
                if (rf048_frame >= 6060u && rf048_frame <= 6100u &&
                    (rf048_target || rf048_indexed_target || rf048_frame_count <= 4u)) {
                    if (rf048_logged++ < 4096u)
                        fprintf(stderr,
                          "QA01RF048ORIGPTR count=%u frame=%u v=%u h=%d dp_base=%04X dp_slot=%04X mirror=%u raw_ptr=%06X y=%04X effective_candidate=%06X a0=%04X a1=%04X target=%u indexed_target=%u\n",
                          rf048_total, rf048_frame, (unsigned)CPU.V_Counter,
                          (int)CPU.Cycles, rf048_d, rf048_dp,
                          (unsigned)rf048_mirror, rf048_base, rf048_y,
                          rf048_effective, ur_rf035_a0,
                          (unsigned)Registers.A.W, (unsigned)rf048_target,
                          (unsigned)rf048_indexed_target);
                    else if (rf048_logged == 4097u)
                        fprintf(stderr, "QA01RF048ORIGPTR_TRUNCATED\n");
                }
            }
"""

def patch_original(src: str) -> str:
    if MARK in src:
        if src.count(AFTER) != 1:
            raise ValueError("RF048 partial original pointer observer")
        return src
    if src.count(rf035.ORIG_AFTER) != 1 or src.count("(*Opcodes[Op].S9xOpcode)();") != 1:
        raise ValueError("RF048 requires intact RF035 original opcode observer")
    out = src.replace(rf035.ORIG_AFTER, rf035.ORIG_AFTER + AFTER, 1)
    if out.count("(*Opcodes[Op].S9xOpcode)();") != 1:
        raise AssertionError("RF048 must never duplicate actual original opcode dispatch")
    return out

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    args = p.parse_args()
    path = args.root.resolve() / ORIGINAL
    if not path.is_file():
        p.error("RF048 requires actual original Snes9x cpu source")
    original = path.read_text(encoding="utf8")
    patched = patch_original(original)
    if patched != original:
        path.write_text(patched, encoding="utf8")
    print("RF048 source pointer observer: " + ("already staged" if patched == original else "staged"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
