# QA-08: source-PC provenance for original colour-HDMA table writers

**Status: executed original Snes9x two-player source write census accepted, with original/native full same-input/physical verification still open.**

## Established original-native facts

Accepted pinned USA 2P native [run 38504531564](https://github.com/gamesbyian/UR-Recomp/actions/runs/38504531564) and artifact **11867072862** prove full 2,473 guest CRC equality and all 26 BG3-main/OBJ-subscreen source intersections. Seven real $2132 writes originate from **channel 5, HDMA mode 1, direct bank $7E**:

| WRAM A-bus address | BBUS COLDATA byte | Native log tag | Live fixed RGB15 |
|---|---|---|---|
| $7E:2086 | 2F, red15 (primed and again at tag2) | 0,2 | 026F |
| $7E:2089 | 40, green0 | 3 | 000F |
| $7E:208C | 80, blue0 | 4 | 000F |
| $7E:208F | 20, red0 | 113 | 0000 |
| $7E:2092 | 53, green19 | 114 | 0260 |
| $7E:2095 | 80, blue0 | 115 | 0260 |

Real compositor source values: **upper output row50 fixed RGB15 000F**, **lower row162 fixed RGB15 0260**. The pinned beam driver draws PPU line N to output row N−1, then runs HDMA. PPU line N sets its write-log tag to N+1; thus a regular during-render log tag L (2..224) affects the following output row **L−1**, not output row L. The first-line prime precedes this loop. This emulator-source crosswalk is not a physical SNES timing measurement.

## New bounded original 65816 writer witness

tools/instrument_snesref_qa08_hdmacolour_table_writers.py instruments the original Snes9x reference's opcode dispatcher, using the source anchor already proven by the existing camera DMA trace tool. It snapshots only original WRAM **$7E:2084..2097**, executes the **unaltered original guest instruction**, then reports each changed byte with original emulator frame, scanline, executed 65816 PC, address, before and after.

The observer is **off by default**. BOTH UR_QA08_ORIGINAL_WRITER_FRAME_FIRST and UR_QA08_ORIGINAL_WRITER_FRAME_LAST must be supplied and form a window of at most **256 emulator frames**. An event cap of 4,096 emits explicit overflow instead of hiding lost instructions. The instrumented source goes only into a disposable original-emulator checkout. No guest RAM, ROM, PPU, emulator model or replay event is edited.

Example setup with a genuine correlated original Snes9x input route, NOT an invented mapping from Baldosa guest2208 to Snes9x ICPU.Frame:

~~~sh
python3 tools/instrument_snesref_qa08_hdmacolour_table_writers.py /path/to/disposable/snes9x/cpuexec.cpp
# Supply both ORIGINAL WRITER FRAME env variables after correlating the original route
~~~

tools/analyze_snesref_qa08_hdmacolour_table_writers.py then consumes that actual original emulator log together with the accepted native ws342_hdma_coldata_source_2208.json. It refuses changed native channel identity, incomplete records, duplicate-byte nonchanges or missing provenance. It groups executed original PC candidates, and checks which last observed WRAM writes agree byte-for-byte with the **six independently accepted native source addresses**.

~~~sh
python3 tools/analyze_snesref_qa08_hdmacolour_table_writers.py --log /path/to/original-emulator.log --native-source /path/to/ws342_hdma_coldata_source_2208.json --out /tmp/qa08-original-hdma-writer-candidates.json
~~~

Even six agreeing last-byte values do not establish that the original emulator used an identically aligned native input/field or that a specific ROM PC necessarily built the game's table. The existing $A59E per-frame graphics/HDMA-table preparation is one possible writer because it handles neighbouring BG scroll $7E:2046..2063; **this is a candidate, not a proven writer of $7E:2086..2095**. The next authoritative gate is the original game instruction trace on a fixed independently aligned USA two-player route.

**Scope:** Original graphics QA-08 only. No gameplay/oracle, Modern, independent release QA, source-art promotion, widened-world pixels, 256×224/7:6 original geometry or 4× Original fallback changes. No new original-emulator campaign was run by this tooling PR.


## Complete executed original WRAM producer census, not static inference

The opt-in original Snes9x source experiment was executed on real USA
two-player input script in [run 38510398955](https://github.com/gamesbyian/UR-Recomp/actions/runs/38510398955),
artifact **11869807231**. The exact original script was verified against
its pinned Baldosa import and stripped **only** the non-guest host turbo
directive. Its 10 independent deterministic original Snesref processes
replayed the **same 2P script to frame2473**, each observing one
non-overlapping 256-frame interval. This covered **all original emulator
frames 0–2559** and all ten processes completed with byte-identical
end-of-route WRAM SHA256
`9350bcb02f3cbf490678c5276245ec2c7fe36b9078bfab9e912d86c5cbc93bf6`.
The original guest second camera `0DDB=01` and race `0313=01` are
confirmed by the original replay itself, not synthetic flags.

There were **exactly 18 observed byte changes** in the
`$7E:2084..2097` channel5 HDMA table neighbourhood, **all at
original emulator frame1781**. Every changed byte was previously
`00` under the explicitly deterministic original WRAM fill.
Each row below is the **real executed original 65816 instruction PC**
bracket whose execution changed the indicated guest WRAM byte:

| Executed original USA PC | Original WRAM byte | Actual change |
| --- | --- | --- |
| $82:D5D8 | $7E:2086 | 00→2F |
| $82:D5E0 | $7E:2089 | 00→40 |
| $82:D5E8 | $7E:208C | 00→80 |
| $82:D5F0 | $7E:2085 | 00→04 |
| $82:D5F4 | $7E:2088 | 00→04 |
| $82:D5F8 | $7E:208B | 00→04 |
| $82:D5FE | $7E:2084 | 00→01 |
| $82:D602 | $7E:2087 | 00→01 |
| $82:D608 | $7E:208A | 00→6D |
| $82:D625 | $7E:208F | 00→20 |
| $82:D62D | $7E:2092 | 00→53 |
| $82:D635 | $7E:2095 | 00→80 |
| $82:D63D | $7E:208E | 00→04 |
| $82:D641 | $7E:2091 | 00→04 |
| $82:D645 | $7E:2094 | 00→04 |
| $82:D64B | $7E:208D | 00→01 |
| $82:D64F | $7E:2090 | 00→01 |
| $82:D655 | $7E:2093 | 00→6D |

All **six** actual COLDATA source bytes independently measured in the
native pinned AOT match the original WRAM writer observations
*exactly*. Five **additional** adjacent source bytes, independently
changed by original opcodes, are consistent with the mode1
companion SETINI address predictions. Original run frame1781 is
**not assumed to equal** Baldosa native guest2208. The
PC-bracketed original WRAM changes do not alone establish a
hardware write instruction mnemonic/disassembly or original/native
same-input per-frame parity.

**Archive provenance:** ZIP SHA256
`646dc27a6a549e0450a326536359a8f3e1e332863529dd62a3cf474427cd1841`,
original executed-guest report `qa08-executed-original-writers.json`
SHA256
`fb2a5e80dfa0738009bdab22eaa43f7f8948b60b083b335d770d61cb60990c26`,
route receipt SHA256
`d27b2b4b9e94c07d1f5a36c41dd454731e1bfcd7d82c6c948c986d6320b07c7c`.
The full original core SHA, script SHA and all 18 source
PC/WRAM bytes are preserved without any ROM or copyrighted raster
in `analysis/data/qa08-original-snes9x-2p-channel5-eighteen-writer-PCs.json`.

Next meaningful executable source question: establish the original
producer's *call context* and actual instruction opcode types around
the compact `$82:D5D8..$82:D655` source block. The accepted
native 2P source already identified channel5 and COLDATA; a
separate, narrow real-native $2133 SETINI pair witness in
[#1491](https://github.com/gamesbyian/UR-Recomp/pull/1491)
must remain a **distinct** gate. Physical SNES HBlank
subscanline timing, full original/native same-input run parity,
and any HD racer artwork approval remain unproven.
