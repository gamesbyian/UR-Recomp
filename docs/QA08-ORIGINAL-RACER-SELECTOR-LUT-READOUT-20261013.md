# QA-08: executed original racer selector and ROM LUT readout

**New experiment, original output pending exact-head CI.** Do not mistake
synthetic selector fixtures or this source patch for a witnessed result.

## Why this discriminator matters

The executed original frame1781 55-opcode capture in [#1503](https://github.com/gamesbyian/UR-Recomp/pull/1503)
proves original program bank `$82` loads its first racer selector
from `$77:0748`, multiplies it by four, and reads four adjacent bytes
from the original USA ROM at `$82:D52A + 4*selector`. The observed
branch tests `$77:0750 & $08`; on the original captured 2P route it
is **not taken**. A second selector comes from `$77:0749` and follows
the same ROM LUT. All 18 source stores and six HDMA descriptor triples
are independently proven, but the original *numeric selector values*
and exact indexed ROM entry addresses have not yet been captured.

## One source-safe original execution

Rather than add another emulator or workflow, the existing
`tools/instrument_snesref_qa08_hdma_opcode_context.py` now makes
**four additional read-only CPU-state observations** inside its
original already-armed, bounded bank82 frame1781 instruction probe:

| Actually executed PC | Original context captured |
| --- | --- |
| `82:D5D1` | First `LDA $77:0748` completed; actual accumulator selector |
| `82:D5D4` | Two `ASL` and `TAX` completed; actual X plus four direct ROM source bytes |
| `82:D61E` | Fall-through `LDA $77:0749` completed; lower-selector accumulator |
| `82:D621` | Second two-`ASL`/`TAX`; actual X plus same table's four source bytes |

The lookup reads the existing `CPU.PCBase` mapping for the current
program bank, **not** a side-effecting SNES bus read or a new guest
instruction. The source probe refuses a null PC mapping or an out-of-
bounds index. It remains off unless the exact original opcode
instrumentation is armed for frame1781. No ROM, WRAM, DMA, PPU,
controller stream, CPU register or command path is modified.

The extended **existing** manual/original-on-PR workflow runs the
same single pinned USA 2P original replay to frame2473 and retains
the new `qa08-original-racer-LUT.json` source report alongside
the already required original instruction/ROM/core/script/WRAM
fingerprints. It performs no second original process and does not
upload copyrighted ROM bytes beyond four-source-byte lookup values.

## Strict readout

`tools/check_qa08_original_racer_lut.py` first checks original
ROM SHA `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`,
the exact original two-player input script and end-WRAM SHA,
the unchanged complete 55 fetched original instructions and 18
independently witnessed WRAM stores, original frame1781, and live 2P
flags `$0DDB=1`, `$0313=1`. It then requires exactly the four
ordered actual CPU observations, exact relevant original PCs and
consistent selector-index `X=4*selector` before admitting
the two source values against the six previously accepted direct HDMA
source triplets. The resulting original selector values must emerge
from actual source observation. Tests using arbitrary selectors
(e.g., 2 and 4) prove the checker contract **only**, never historical
values.

This closes a narrow source archaeology gap if and only if the
exact-head original workflow passes, without promoting any
**original/native same-input frame parity, live original/native
matched RGB, CPU journal as live HDMA, physical SNES HBlank timing,
untaken alternate branch, uncaptured other racer entries, new
HD character resemblance or gameplay/Windows acceptance**.

The full source-to-HDMA-to-native-pixel chain remains governed by
[the executed 65816 source table authority](QA08-ORIGINAL-2P-CHANNEL5-EXECUTED-65816-LOOKUP-TABLE-20261013.md),
[real native register/pixel evidence](QA08-HDMA-COLDATA-WRITE-SOURCE-PROVENANCE-20261013.md)
and the separately current release ledger.
