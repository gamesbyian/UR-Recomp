#!/usr/bin/env python3
"""RF049: complete source-window bank-qualified original sound operand census.

Installed ONLY into a pinned disposable Snes9x guest after RF035 and RF048.
Counts every real executed bank82 LDA [$63],Y in the source window,
qualifying exact 24-bit address with D, raw DP pointer and Y. Prints a final
source-window census after frame 6150, target LDA rows and the immediately
following real CPU STA opcode completions. Never performs extra emulated bus
reads/writes, moves clocks, or changes generated gameplay / live Windows.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import qa01_rf048_original_sound_pointer_witness as rf048

MARK = "UR_QA01_RF049_SOUND_OPERAND"
ORIGINAL = Path("cpuexec.cpp")
AFTER = r"""
            /* UR_QA01_RF049_SOUND_OPERAND: true opcode, no synthetic bus read. */
            if (getenv("UR_QA01_RF049_SOUND_OPERAND")) {
                static unsigned long long rf049_lda_total;
                static unsigned long long rf049_banks[4];
                static unsigned rf049_min[4] = {65535u,65535u,65535u,65535u};
                static unsigned rf049_max[4];
                static unsigned rf049_other_bank, rf049_unmapped;
                static unsigned rf049_lowword_C774, rf049_lowword_D0B4;
                static unsigned rf049_exact_13C774, rf049_exact_13D0B4;
                static unsigned rf049_target_logged, rf049_target_overflow;
                static unsigned rf049_pending, rf049_pending_at;
                static unsigned rf049_unclosed;
                static unsigned rf049_first_frame = 0xffffffffu;
                static unsigned rf049_last_frame, rf049_completed;
                if (!rf049_completed && (unsigned)ICPU.Frame > 6150u) {
                    if (rf049_pending) ++rf049_unclosed;
                    fprintf(stderr,
                       "QA01RF049FINAL first=%u last=%u total=%llu bank10=%llu bank11=%llu bank12=%llu bank13=%llu min10=%04X max10=%04X min11=%04X max11=%04X min12=%04X max12=%04X min13=%04X max13=%04X other=%u unmapped=%u lowC774=%u lowD0B4=%u exact13C774=%u exact13D0B4=%u target_logged=%u target_overflow=%u unclosed=%u\n",
                       rf049_first_frame,rf049_last_frame,rf049_lda_total,
                       rf049_banks[0],rf049_banks[1],rf049_banks[2],rf049_banks[3],
                       rf049_min[0],rf049_max[0],rf049_min[1],rf049_max[1],
                       rf049_min[2],rf049_max[2],rf049_min[3],rf049_max[3],
                       rf049_other_bank,rf049_unmapped,rf049_lowword_C774,
                       rf049_lowword_D0B4,rf049_exact_13C774,
                       rf049_exact_13D0B4,rf049_target_logged,
                       rf049_target_overflow,rf049_unclosed);
                    rf049_completed = 1u;
                }
                if (ur_rf035_sound && !rf049_completed) {
                    if (ur_rf035_pc == 0x82F0u) {
                        const unsigned rf049_frame = (unsigned)ICPU.Frame;
                        const unsigned rf049_d = (unsigned)Registers.D.W;
                        const unsigned rf049_dp = (rf049_d + 0x63u) & 0xffffu;
                        if (rf049_first_frame == 0xffffffffu)
                            rf049_first_frame = rf049_frame;
                        rf049_last_frame = rf049_frame;
                        ++rf049_lda_total;
                        if (rf049_pending) {
                            ++rf049_unclosed;
                            rf049_pending = 0u;
                        }
                        if (rf049_dp > 0x1ffdu) ++rf049_unmapped;
                        else {
                            const unsigned rf049_pointer =
                               (unsigned)Memory.RAM[rf049_dp] |
                               ((unsigned)Memory.RAM[rf049_dp+1u] << 8) |
                               ((unsigned)Memory.RAM[rf049_dp+2u] << 16);
                            const unsigned rf049_y = ur_rf035_y0;
                            const unsigned rf049_ea = (rf049_pointer + rf049_y) & 0xffffffu;
                            const unsigned rf049_bank = rf049_ea >> 16;
                            const unsigned rf049_low = rf049_ea & 0xffffu;
                            if (rf049_bank>=0x10u && rf049_bank<=0x13u) {
                                const unsigned j = rf049_bank - 0x10u;
                                ++rf049_banks[j];
                                if (rf049_low < rf049_min[j]) rf049_min[j] = rf049_low;
                                if (rf049_low > rf049_max[j]) rf049_max[j] = rf049_low;
                            } else ++rf049_other_bank;
                            if (rf049_low == 0xC774u) ++rf049_lowword_C774;
                            if (rf049_low == 0xD0B4u) ++rf049_lowword_D0B4;
                            if (rf049_ea == 0x13C774u) ++rf049_exact_13C774;
                            if (rf049_ea == 0x13D0B4u) ++rf049_exact_13D0B4;
                            const int rf049_target =
                                (rf049_bank==0x13u &&
                                 ((rf049_low>=0xC770u && rf049_low<=0xC779u) ||
                                  (rf049_low>=0xD0B0u && rf049_low<=0xD0B9u))) ||
                                (rf049_low==0xC774u || rf049_low==0xD0B4u);
                            if (rf049_target) {
                                if (rf049_target_logged < 128u) {
                                    ++rf049_target_logged;
                                    fprintf(stderr,
                                       "QA01RF049LDA ordinal=%llu frame=%u v=%u h=%d pc=%02X:%04X d=%04X ptr=%06X y=%04X ea=%06X a0=%04X a1=%04X\n",
                                       rf049_lda_total,rf049_frame,(unsigned)CPU.V_Counter,
                                       (int)CPU.Cycles,ur_rf035_bank,ur_rf035_pc,
                                       rf049_d,rf049_pointer,rf049_y,rf049_ea,
                                       ur_rf035_a0,(unsigned)Registers.A.W);
                                    rf049_pending=1u;
                                    rf049_pending_at=rf049_target_logged;
                                } else ++rf049_target_overflow;
                            }
                        }
                    } else if (rf049_pending &&
                               (ur_rf035_pc==0x82F2u || ur_rf035_pc==0x82F6u)) {
                        const unsigned expected = rf049_pending==1u ? 0x82F2u : 0x82F6u;
                        if (ur_rf035_pc!=expected) {
                            ++rf049_unclosed;
                            rf049_pending=0u;
                        } else {
                            fprintf(stderr,
                               "QA01RF049STA target=%u frame=%u v=%u h=%d pc=%02X:%04X op=%02X a0=%04X a1=%04X\n",
                               rf049_pending_at,(unsigned)ICPU.Frame,
                               (unsigned)CPU.V_Counter,(int)CPU.Cycles,
                               ur_rf035_bank,ur_rf035_pc,ur_rf035_op,
                               ur_rf035_a0,(unsigned)Registers.A.W);
                            rf049_pending=rf049_pending==1u?2u:0u;
                        }
                    }
                }
            }
"""

def patch_original(source: str) -> str:
    if MARK in source:
        if source.count(AFTER) != 1:
            raise ValueError("RF049 original observer partially modified")
        return source
    if source.count(rf048.AFTER) != 1 or source.count("(*Opcodes[Op].S9xOpcode)();") != 1:
        raise ValueError("RF049 requires intact original RF048 source observer")
    result = source.replace(rf048.AFTER, rf048.AFTER + AFTER, 1)
    if result.count("(*Opcodes[Op].S9xOpcode)();") != 1:
        raise AssertionError("RF049 duplicated original 65816 opcode execution")
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    path = args.root.resolve() / ORIGINAL
    if not path.is_file():
        parser.error("missing original Snes9x cpuexec.cpp")
    original = path.read_text(encoding="utf8")
    patched = patch_original(original)
    if patched != original:
        path.write_text(patched, encoding="utf8")
    print("RF049 original sound census: " +
          ("unchanged" if patched == original else "staged"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
