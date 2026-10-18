#!/usr/bin/env python3
"""RF055: read-only generated v2 instruction-site trace for real 82:82F0.

Patch only the disposable pinned Baldosa SNESRecomp code generator.
The trace is injected at the decoded instruction boundary before its IR,
never inserts guest bus calls, changes clock charges or alters instructions.
"""
from __future__ import annotations
import argparse
from pathlib import Path

MARK = 'UR_QA01_RF055_EXECUTED_8282F0_OPCODE'
TARGET = Path('snesrecomp/recompiler/v2/emit_function.py')
ANCHOR = '            for op in ir_ops:\n'
SITE = '''            # UR_QA01_RF055_EXECUTED_8282F0_OPCODE: source-stamped dynamic
            # instruction site, distinct from enclosing AOT function label.
            if (bank == 0x82 and getattr(di_insn, 'addr', None) == 0x8282F0):
                if (di_insn.mnem != 'LDA' or di_insn.opcode != 0xB7
                        or di_insn.operand != 0x63):
                    raise ValueError('RF055 decoded original 82:82F0 changed')
                lines.extend([
                    '{ extern int snes_frame_counter;',
                    '  if (getenv("UR_QA01_RF055_NATIVE_OPCODE_PC") && snes_frame_counter == 6124) {',
                    '    static unsigned rf055_count;',
                    '    if (++rf055_count <= 2048u) {',
                    '      fprintf(stderr, "QA01RF055NATIVEPC seq=%u frame=%d pc=8282F0 opcode=B7 operand=63 master=%llu A=%04X Y=%04X PB=%02X DB=%02X D=%04X ptr63=%02X ptr64=%02X ptr65=%02X scope=%s\\n",',
                    '        rf055_count, snes_frame_counter, (unsigned long long)cpu->master_cycles,',
                    '        (unsigned)cpu->A, (unsigned)cpu->Y, (unsigned)cpu->PB,',
                    '        (unsigned)cpu->DB, (unsigned)cpu->D,',
                    '        (unsigned)cpu->ram[0x63], (unsigned)cpu->ram[0x64],',
                    '        (unsigned)cpu->ram[0x65],',
                    '        g_last_recomp_func ? g_last_recomp_func : "?");',
                    '    } else if (rf055_count == 2049u) {',
                    '      fprintf(stderr, "QA01RF055NATIVEPC_TRUNCATED\\n");',
                    '    }',
                    '  }',
                    '}',
                ])
'''
def patch(src: str) -> str:
    if MARK in src:
        if src.count(SITE) != 1 or src.count(ANCHOR) != 1:
            raise ValueError('partial/tampered RF055 emitter')
        return src
    if src.count(ANCHOR) != 1 or "getattr(di_insn, 'addr', None)" not in src:
        raise ValueError('not the pinned v2 per-insn lowering loop')
    return src.replace(ANCHOR, SITE+ANCHOR, 1)

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', required=True, type=Path)
    a=p.parse_args()
    target=a.game/TARGET
    src=target.read_text(encoding='utf8')
    out=patch(src)
    if out != src: target.write_text(out,encoding='utf8')
    print('RF055 staged exactly one generated instruction-site observer', target)
if __name__ == '__main__': main()
