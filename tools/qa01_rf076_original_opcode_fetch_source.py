#!/usr/bin/env python3
"""RF076 original Snes9x true opcode-fetch and NMI-entry source witness.

Only opt-in, disposable 2014 original Snes9x. The observed opcode byte is
already fetched by the real CPU fast/slow dispatch path, before PC increment.
No additional guest memory access, emulated instruction or clock mutation.
The original source sequence is not the native RF047 event sequence.
"""
from __future__ import annotations
import argparse
from pathlib import Path

SOURCE = Path('cpuexec.cpp')
STAMP = 'UR_QA01_RF076_ORIGINAL_FETCH_PC'
NMI = '                S9xOpcode_NMI();'  # Real RF044/RF063 staged call, spaces
NMI_WAKE = '\t\t\t\tTimings.NMITriggerPos = 0xffff;\n\t\t\t\tif (CPU.WaitingForInterrupt)'
FETCH = '\t\t\tRegisters.PCw++;\n\t\t\t(*Opcodes[Op].S9xOpcode)();'
HEADER = 'static inline void S9xReschedule (void);\n'
TARGETS = (0xD4EE, 0xD4F0, 0xD4F2, 0xD4F4, 0xD4F5)
HOOK = r'''/* UR_QA01_RF076_ORIGINAL_FETCH_PC: this is the true, already fetched
 * opcode and its pre-increment PC in S9xMainLoop, never a later PC context.
 * The NMI marker is before the original emulator's genuine interrupt push.
 * Reporter does not call S9xGetByte, mutate PC/SP, or change CPU cycles. */
static void ur_rf076_original_fetched_opcode(const char *stage, uint8 opcode) {
    static unsigned long long seq;
    static unsigned count;
    if (!getenv("UR_QA01_RF076_ORIGINAL_FETCH_PC") ||
        (unsigned)ICPU.Frame < 1017u || (unsigned)ICPU.Frame > 1025u)
        return;
    const unsigned pc = ((unsigned)Registers.PB << 16) | Registers.PCw;
    if (stage[0] == 'f' &&
        (pc != 0x82D4EEu && pc != 0x82D4F0u &&
         pc != 0x82D4F2u && pc != 0x82D4F4u &&
         pc != 0x82D4F5u))
        return;
    if (count++ >= 131072u) {
        if (count == 131073u)
            fprintf(stderr, "QA01RF076ORIGPC_TRUNCATED\n");
        return;
    }
    fprintf(stderr,
        "QA01RF076ORIGPC seq=%llu stage=%s f=%u"
        " actualFetchedPC=%06X fetchedOpcode=%02X S=%04X"
        " v=%u h=%d wai=%u\n",
        ++seq, stage, (unsigned)ICPU.Frame, pc,
        (unsigned)opcode, (unsigned)Registers.S.W,
        (unsigned)CPU.V_Counter, (int)CPU.Cycles,
        (unsigned)CPU.WaitingForInterrupt);
}

'''


def patch(source: str) -> str:
    if STAMP in source:
        raise ValueError('RF076 original fetched opcode hook already staged')
    # RF044 replaces the original tab-indented call with a source-qualified
    # instrumentation block. RF063 then augments that exact real call with
    # its post-push WRAM checkpoint. Never match a stray textual NMI call.
    if ('UR_QA01_RF044_STACK_BUS' not in source or
        'UR_QA01_RF063_SOURCE_BUS_CHECKPOINT_SEQUENCE' not in source or
        'rf044_nmi' not in source or
        'QA01RF063ORIGCHECKPOINT' not in source):
        raise ValueError('RF076 requires actual RF044/RF063 staged original NMI')
    if source.count(HEADER) != 1 or source.count(NMI) != 1 or \
       source.count(FETCH) != 1 or source.count(NMI_WAKE) != 1:
        raise ValueError('RF076 pinned source S9xMainLoop opcode/NMI structural drift')
    # Require the original fast-direct and slow-bus fetched operand *before*
    # creating an observer that might otherwise log a fabricated opcode.
    if source.count('Op = CPU.PCBase[Registers.PCw];') != 1 or \
       source.count('Op = S9xGetByte(Registers.PBPC);') != 1:
        raise ValueError('RF076 original fast/slow opcode fetch sources changed')
    result = source.replace(HEADER, HEADER + '\n' + HOOK, 1)
    result = result.replace(NMI_WAKE,
                            '\t\t\t\tTimings.NMITriggerPos = 0xffff;\n'
                            '\t\t\t\tur_rf076_original_fetched_opcode("nmi_pending", 0);\n'
                            '\t\t\t\tif (CPU.WaitingForInterrupt)',1)
    result = result.replace(NMI,
                            '                ur_rf076_original_fetched_opcode("nmi_before", 0);\n'
                            + NMI, 1)
    result = result.replace(FETCH,
                            '\t\t\tur_rf076_original_fetched_opcode("fetch", Op);\n'
                            + FETCH, 1)
    if result.count('ur_rf076_original_fetched_opcode(') != 4:
        raise AssertionError('RF076 native/original source hook insertion count changed')
    # No new original source guest bus/CPU side effects in the transformed call.
    for needle in ('Op = S9xGetByte(Registers.PBPC);',
                   'Op = CPU.PCBase[Registers.PCw];',
                   'S9xOpcode_NMI();', 'Registers.PCw++;',
                   '(*Opcodes[Op].S9xOpcode)();'):
        if result.count(needle) != source.count(needle):
            raise AssertionError('RF076 original instruction/fetch call changed')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    file = args.root.resolve() / SOURCE
    if not file.is_file():
        parser.error('pinned original cpuexec.cpp missing')
    before = file.read_text(encoding='utf8')
    file.write_text(patch(before), encoding='utf8')
    print('RF076 true fetched original opcode/NMI source staging complete (no guest execution proof)')


if __name__ == '__main__':
    main()
