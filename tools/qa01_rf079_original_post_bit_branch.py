#!/usr/bin/env python3
"""RF079: original 2014 real BIT operand / BPL destination observer.

Stage AFTER RF076 real opcode-fetch source witness and before original rebuild.
Post-dispatch ICPU._Negative is the real BIT(Work8) operand in M=1, set by
the already executed opcode. No emulated bus read, CPU tick or PC mutation.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import qa01_rf076_original_opcode_fetch_source as rf076

SOURCE=Path('cpuexec.cpp')
STAMP='UR_QA01_RF079_ORIGINAL_AFTER_BIT_BPL'
OLD=('\t\t\tRegisters.PCw++;\n'
     '\t\t\t(*Opcodes[Op].S9xOpcode)();')
HELPER=r'''/* UR_QA01_RF079_ORIGINAL_AFTER_BIT_BPL: original post-opcode
 * source-local raw operand and actual branch landing, not a guessed future
 * PC or another S9xGetByte. Scope to two actual NMI host labels only. */
static unsigned long long ur_rf079_original_seq;
static unsigned ur_rf079_original_rows;
static inline void ur_rf079_original_post_op(unsigned pre_pc, uint8 opcode) {
    if (!getenv("UR_QA01_RF079_ORIGINAL_BIT_BPL") ||
        ((unsigned)ICPU.Frame != 1017u && (unsigned)ICPU.Frame != 1018u) ||
        (pre_pc != 0x82D4EEu && pre_pc != 0x82D4F0u))
        return;
    if (ur_rf079_original_rows++ >= 32768u) {
        if (ur_rf079_original_rows == 32769u)
            fprintf(stderr,"QA01RF079ORIG_TRUNCATED\n");
        return;
    }
    const unsigned after=((unsigned)Registers.PB << 16) | Registers.PCw;
    const unsigned neg=(unsigned)ICPU._Negative;
    fprintf(stderr,
        "QA01RF079ORIG seq=%llu f=%u before=%06X opcode=%02X"
        " after=%06X D=%04X M=%u Nbyte=%02X N=%u"
        " V=%u H=%d phase=after_real_guest_opcode\n",
        ++ur_rf079_original_seq,(unsigned)ICPU.Frame,pre_pc,
        (unsigned)opcode,after,(unsigned)Registers.D.W,
        (unsigned)(CheckMemory()!=0),neg,(unsigned)((neg & 0x80u)!=0),
        (unsigned)CPU.V_Counter,(int)CPU.Cycles);
}
'''

def patch(src:str)->str:
    if STAMP in src:
        raise ValueError('RF079 original observer already/partially staged')
    if rf076.STAMP not in src or src.count(rf076.HOOK)!=1:
        raise ValueError('RF079 requires exact RF076 staged original fetch')
    if src.count(OLD)!=1 or src.count(rf076.HEADER)!=1:
        raise ValueError('RF079 original exact guest opcode dispatch drift')
    before={token:src.count(token) for token in
            ('S9xGetByte(', 'S9xGetWord(', 'S9xSetByte(', 'S9xSetWord(',
             'Registers.PCw++;', '(*Opcodes[Op].S9xOpcode)();',
             'S9xOpcode_NMI();')}
    repl=('\t\t\tconst unsigned ur_rf079_prepc='
          '((unsigned)Registers.PB<<16)|Registers.PCw;\n'
          + OLD +
          '\n\t\t\tur_rf079_original_post_op(ur_rf079_prepc,Op);')
    result=src.replace(rf076.HEADER,rf076.HEADER+HELPER,1).replace(OLD,repl,1)
    if any(result.count(token)!=count for token,count in before.items()):
        raise AssertionError('RF079 changed original guest opcode/bus population')
    if result.count('ur_rf079_original_post_op(')!=2 or result.count(STAMP)!=1:
        raise AssertionError('RF079 source observer injection missing/duplicated')
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    args=ap.parse_args()
    file=args.root.resolve()/SOURCE
    if not file.is_file():
        ap.error('pinned 2014 original CPU source not found')
    file.write_text(patch(file.read_text(encoding='utf-8')),encoding='utf-8')
    print('RF079 real original BIT/BPL post-op source staged; guest bus/timing untouched')

if __name__=='__main__':main()
