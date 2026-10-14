# QA-08: original 65816 opcode source context for genuine channel5 HDMA writers

## Independently accepted original and native evidence

A genuine original USA Snes9x two-player run 38510398955 captured
**18 instruction-PC-bracketed WRAM byte changes** at original frame1781,
all within $82:D5D8..$82:D655. The original source addresses
$7E:2085/2088/208B/208E/2091/2094 supply CGADSUB=04 in genuine
native AOT run 38514112274, while $7E:2086/2089/208C/208F/2092/2095
supply actual COLDATA in prior native AOT 38504531564.
Both native studies retain full Original guest CRCs and 26 real BG3/OBJ
compositor source samples. Adjacent +1 WRAM values earlier mistaken
for mode1 SETINI transfers are **not** accepted source bytes.

Original Snes9x PC change records do not automatically reveal the
instruction's opcode, CPU dynamic operand length, addressing mode or
call context. Source provenance must not be replaced by a guessed
relationship to older $A59E graphics preparation research.

## Read-only original opcode experiment

tools/instrument_snesref_qa08_hdma_opcode_context.py patches a
**disposable** original Snes9x libretro cpuexec.cpp at the exact real
opcode-dispatch anchor. It reads original Op already fetched and the
four direct CPU.PCBase ROM bytes before the guest executes an
unchanged opcode; it does not call mapped bus reads, change guest
ROM/WRAM/PPU, or alter dispatcher semantics. Length is read directly
from the executing Snes9x ICPU.S9xOpLengths[Op] table: the trailing
4-byte preview is not assumed to belong to the current instruction.

The observer is **disabled by default** and requires precisely
UR_QA08_ORIGINAL_HDMA_OPCODE_FRAME=1781. It records only actual bank82
CPU program counters D5C0..D66F in original frame1781, with an
explicit overflow marker if more than 512 source instructions occur.

One dedicated QA-08 original opcode workflow runs **one** pinned
original USA 2P script to frame2473 using the same immutable input
route, stripping only the native-host-only turbo directive. It
requires original second-camera $0DDB=1, in-race $0313=1,
original route end state and original ROM verification. The strict
tools/check_qa08_original_hdma_opcode_context.py decoder requires
all **18** independently witnessed original writer PCs, authentic
Snes9x source-mapped ROM opcode bytes, correct program order and
actual CPU execution-mode instruction lengths. Adversarial synthetic
tests reject absent writer PCs, mismatched original opcodes, wrong
frame, wrong bank, source drift or overflow.

The original source artifact retains full executed opcode trace
and SHA256-bound ROM/core/script/WRAM receipts, but **never uploads
ROM, SRAM or WRAM**. Reproduction:

    python3 tools/check_qa08_original_hdma_opcode_context.py \
      --log /path/to/qa08-original-opcode.log \
      --original-writer-census analysis/data/qa08-original-snes9x-2p-channel5-eighteen-writer-PCs.json \
      --out /tmp/qa08-original-writer-opcode-context.json

**Proposed original opcode study, not yet accepted at new exact head.**
The native COLDATA/CGADSUB register sources are already accepted,
but physical SNES HBlank timing, full same-input original/native
frame parity, game-code call graph and HD character art approval
remain separate gates. No original graphics renderer,
modern-product, oracle/gameplay, independent release QA, original
256x224 with 7:6 pixel aspect, 342-wide real world, or exact 4x
Original fallback code is changed by this research diagnostic.
