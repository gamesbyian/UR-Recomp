# QA-08: source-PC provenance for original colour-HDMA table writers

**Status: bounded original-emulator research harness, not a same-input original/native writer acceptance.**

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
