# QA-08: original native HDMA COLDATA write-source provenance

**Strict original-native source evidence accepted in pinned AOT run 38504531564, source witness published below.**

The accepted genuine native two-player source PPU experiment #1433 discovered **two distinct live fixed-colour operands**: at source coordinate (133,50), `fixed15=0x000F` (red15); at (133,162), `fixed15=0x0260` (green19). Both pixels have BG3 red13 main and OBJ subscreen. Source journal base `fixed15=0x0260` does **not** capture rendering-phase HDMA, so it is not enough to identify the address/channel that writes red15 above.

Unlike extrapolating from two colours, the pinned native SNESRecomp [DMA engine](https://github.com/baldosa/snesrecomp/blob/075fbe4c/runner/src/snes/dma.c) already knows the **actual** A-bus source address/bank, HDMA channel, mode, direct/indirect table cursor and target BBUS register at the instant it executes each write. Its `dma_doHdma()` invokes `dma_transferByte()`, marks the write as `kPpuWlogHdma`, and writes BBUS register 0x32 for `$2132 COLDATA`. Read these values there rather than reconstructing speculative ROM table addresses.

## Safe source probe

`tools/qa08_patch_hdma_coldata_source.py` is a fail-closed text patch to **only the disposable pinned Baldosa `runner/src/snes/dma.c` checkout**. The opt-in `UR_QA08_HDMA_COLDATA_FRAME=2208` logs actual `$2132` **HDMA-origin** bytes only, after their ordinary PPU register write. It reports SNES framebuffer/PPU journal frame/tag, actual DMA channel, byte value/RGB selectors, source `bank:address`, HDMA mode, table pointer, whether indirect, and the PPU's live 15-bit fixed-colour register *after the byte*. Missing opt-in is silent; more than 2,048 bytes emits an explicit overflow failure marker.

`tools/qa08_analyze_hdma_coldata_source.py` refuses to analyze a supposed native log unless the independent exact original-native two-pixel report still verifies guest frame2208, 2,473 guest CRCs, true BG3/OBJ composition, and live fixed15 both rows. It fails closed on absent/malformed/overflowing source records, wrong SNES BBUS address, unexpected frame/channel/mode, and preserves the entire actual ordered byte stream plus source bank/cursor in machine-readable JSON.

**Important boundary:** Even a complete source-byte stream does not automatically establish that an observed channel caused the specific PPU pixel at y50 or y162. The pinned emulator performs HBlank HDMA after each line, and `ppu_wlog_position` has its own frame/line tagging. Actual source byte order and register states, independent beam-to-row alignment, and original PPU compositor values must be reconciled before attributing a channel/table to a physical displayed scanline. No full real SNES timing claim or global colour fix is permitted.

## Exact native acceptance in this graphics PR (no new runner factory)

This PR wires the read-only DMA source patch into **the same existing
pinned original/native Baldosa AOT job** after the accepted PPU colour,
two-point and 26-pixel source reporters and before the original compiled
2P route. It arms `UR_QA08_HDMA_COLDATA_FRAME=2208` for the existing
unmodified stock Original guest run **only**, then unsets it before
the separately bound OBJ-removal and other source processes. The native
job still requires full Original 342x224 SHA/2,473 guest CRC equality
and the independent two- and 26-pixel PPU provenance reports; the new
`qa08_analyze_hdma_coldata_source.py` runs **after** those gates and
writes `ws342_hdma_coldata_source_2208.json` into the normal
evidence artifact. No additional game/emulator process is executed.

A real native failure to observe HDMA COLDATA bytes, an unparseable
source address/channel, overflow, or a contradictory previously accepted
PPU colour state is a genuine **red acceptance**. The exact-head native job **passed**, and its source-address/channel byte stream is independently preserved below. The original guest table-population instruction has **not** yet been observed.

## Historical pre-acceptance research plan (completed for the native channel/source bytes)

After current 26-pixel #1453 native proof completes, apply the DMA patch immediately before compiling the same existing pinned native 2P executable, and enable its env only for the already-required unmodified stock 2P guest2208 route. The original SHA256 and full guest CRC gates must remain unchanged. Run the offline reader on that original native log and the already-produced `ws342_native_main_sub_pixel_2208.json`, saving its report in the existing native evidence artifact. There is **no need to run an independent long GHA research campaign** or to inject memory/graphics writes. Avoid editing active jobs while they run. This preparatory code **does not yet establish any observed source channel or RAM address**.

Still excluded: gameplay/oracle, Modern/frontend/persistence, independent release QA certification, original physical SNES hardware acceptance and all owner-vetoed procedural HD character art.

## Accepted source chain: channel 5, six distinct WRAM bytes, seven real transfers

The exact-head [native AOT run 38504531564](https://github.com/gamesbyian/UR-Recomp/actions/runs/38504531564), merged as [#1461](https://github.com/gamesbyian/UR-Recomp/pull/1461), **passed** the original USA 2P complete guest CRC comparison (2,473 entries), strict 342x224 Original renderer SHA, both 2-point PPU main/sub compositor witnesses, all **26 native BG3/text plus OBJ source pixel** witnesses, and independently re-run original front OBJ98 and OBJ96 removal counterfactuals. It recorded `QA08_NATIVE_HDMA_COLDATA_SOURCE_BYTES_ACCEPTED count=7` in the actual pinned source run.

The original native evidence archive is artifact **11867072862**. Downloaded ZIP SHA256 `2716fc6a21b7ac75a05b9ce26d270b7bf0c1e575e75e74e550665b2a899e5302`; the *actual* generated native report `baldosa-evidence/ws342_hdma_coldata_source_2208.json` SHA256 `659ee309b9f79cc1bd2ae1b8d56eaa8f8e8634b49b049ef4421d2f1f066ad51d`. A smaller derivative, retaining the native evidence hashes and literal source write chronology, is in `analysis/data/qa08-original-native-channel5-hdma-coldata-source-handoff.json`.

**All seven actual $2132 COLDATA writes came from HDMA channel 5, mode 1, direct (not indirect), A-bus bank $7E**:

| Write order | Actual A-bus source | $2132 byte / channel | Native write-log tag | Actual live fixed RGB15 after write |
| ---: | --- | --- | ---: | --- |
| 0 | $7E:2086 | 2F red15 | 0, first-line priming | 026F |
| 1 | $7E:2086 | 2F red15 | 2 | 026F |
| 2 | $7E:2089 | 40 green0 | 3 | 000F |
| 3 | $7E:208C | 80 blue0 | 4 | 000F |
| 4 | $7E:208F | 20 red0 | 113 | 0000 |
| 5 | $7E:2092 | 53 green19 | 114 | 0260 |
| 6 | $7E:2095 | 80 blue0 | 115 | 0260 |

The real native beam source explicitly draws `ppu_runLine(line)` at framebuffer row `line-1`, followed by `dma_doHdma()`, with the PPU write-log cursor tagged `line+1`. Therefore a normal in-frame HDMA tag **L=2..224** represents a write *after* framebuffer row **L-2** and *before* framebuffer row **L-1**. The first-line prime is separate. This aligns the observed colour changes with the source-confirmed upper row50 live `000F` and lower row162 live `0260`. It establishes native source timing and register effects, **not independently verified physical SNES subscanline timing**.

**Unclosed:** the executed **original 65816 guest PC(s)** that populate those six source bytes in WRAM; proof of original instruction producer requires the original Snes9x reference trace on a fixed aligned 2P route, not just nearby disassembly or equal memory values. The candidate routine `$A59E` is known to prepare neighbouring scroll HDMA tables, but is **not asserted** to be channel5's table writer. A bounded original-opcode writer probe is prepared in [#1473](https://github.com/gamesbyian/UR-Recomp/pull/1473).

No gameplay/oracle, Modern, independent QA certification, native graphics output, true widened world, original 7:6 PAR and 4× fallback, or artist-rejected HD racer is changed by this diagnostic ledger.


## Unmeasured paired writes: HDMA mode 1 also targets $2133 SETINI

A source-backed consequence of the accepted channel-5 trace deserves its
**own unresolved evidence gate**. In pinned `baldosa/snesrecomp@075fbe4c`
`runner/src/snes/dma.c`, HDMA mode 1 has
`transferLength[1] = 2` and
`bAdrOffsets[1] = {0,1,0,1}`. The actual native PPU trace
independently recorded channel 5 as mode 1, direct, starting at
B-bus register `0x32`, with six distinct COLDATA source addresses.
`dma_doHdma` reads successive direct bytes from
`ch->tableAdr++` during its two-byte transfer. The **next**
source address therefore targets **$2133**, rather than another $2132:

| Real channel5 first source | Measured write to $2132 COLDATA | Source of paired write to $2133 SETINI | Paired byte **actually measured?** |
| --- | --- | --- | --- |
| $7E:2086 | 2F (twice) | $7E:2087 | **No** |
| $7E:2089 | 40 | $7E:208A | **No** |
| $7E:208C | 80 | $7E:208D | **No** |
| $7E:208F | 20 | $7E:2090 | **No** |
| $7E:2092 | 53 | $7E:2093 | **No** |
| $7E:2095 | 80 | $7E:2096 | **No** |

The original pinned PPU's `ppu_write` path **does handle**
`case SETINI & 0xff` by assigning `ppu->setini = val`.
Thus it would be incorrect to assume a mode-1 HDMA pair writes
only fixed colours. However, none of the six paired **actual SETINI
data bytes**, their actual values at the two original screenshot
rows, or any original physical console effects has yet been
captured by the `bAdr == 0x32`-filtered native tracer.
The table above is a precise **source-derived address/target
prediction**, not six additional empirically observed writes.

Next narrowly scoped QA-08 test: extend the existing opt-in
read-only channel5 native byte probe to record **$2133** as well as
$2132 at the same guest2208 field. Read real `bAdr=0x33`
value, A-bus address, channel/mode/tag and live `ppu->setini`
after write, then correlate its bounds with the accepted
two-viewport PPU samples. Reuse the *existing stock 2P process*,
all 2,473 guest CRC entries and original full-raster SHA; do not
launch a separate cumulative factory. A relevant unexpected
SETINI effect is an investigated native fidelity issue, not
permission to alter Original pixels speculatively.

The candidate original Snes9x full guest writer trace in
[#1481](https://github.com/gamesbyian/UR-Recomp/pull/1481)
may also recover actual table bytes from original WRAM, but its
executed opcode/source result and original/native input alignment
have **not** yet been accepted. This additional paired-register
requirement preserves the physical hardware gap and the procedural
HD character art veto.


### Original-emulator producer bytes observed; native SETINI transfers still unmeasured

Independent real original Snes9x USA two-player execution
[run 38510398955](https://github.com/gamesbyian/UR-Recomp/actions/runs/38510398955),
artifact **11869807231**, ZIP SHA256
646dc27a6a549e0450a326536359a8f3e1e332863529dd62a3cf474427cd1841,
spanned ten deterministic 256-frame opcode-bracket windows covering
original emulator frames **0–2559**. Its 18 WRAM byte changes all
occurred at **original frame 1781**, and all ten unmodified
controller-route replays produced byte-identical end-of-route
WRAM SHA256
9350bcb02f3cbf490678c5276245ec2c7fe36b9078bfab9e912d86c5cbc93bf6.
The original executed-writer source JSON SHA256 is
fb2a5e80dfa0738009bdab22eaa43f7f8948b60b083b335d770d61cb60990c26.

The genuine original emulator independently recorded **five**
of the six source-predicted companion byte values from executed
65816 opcode brackets:

| Paired source WRAM byte | Actual executed original PC changing byte | New original WRAM byte | Actual native $2133 write observed? |
| --- | --- | --- | --- |
| $7E:2087 | $82:D602 | **01** | **No** |
| $7E:208A | $82:D608 | **6D** | **No** |
| $7E:208D | $82:D64B | **01** | **No** |
| $7E:2090 | $82:D64F | **01** | **No** |
| $7E:2093 | $82:D655 | **6D** | **No** |
| $7E:2096 | No changed-byte opcode recorded across frames 0–2559 | **Not independently sampled as a byte value** | **No** |

The same original source report found all **six** independently
native-accepted $2132 COLDATA bytes, with genuine executed
original PC brackets at $82:D5D8, D5E0, D5E8, D625, D62D, D635.
These values are original **table-write provenance**, not yet
a strict same-input original/native writer comparison.
The earlier native tracer had bAdr==0x32 filtering and so did not
observe even one actual $2133 SETINI source transfer. Original
opcode bytes matching source-predicted companion addresses cannot
substitute for a native transfer witness or physical SNES timing
measurement. Do not interpret an unchanged original byte at
$7E:2096 as an independently observed $2133 hardware zero.

This original producer observation comes from
[PR #1481](https://github.com/gamesbyian/UR-Recomp/pull/1481).
The remaining original-native **graphics** gate is to capture
real channel-5 bAdr=0x33 and post-write PPU setini values during
the same pinned native guest2208 field and compare against
the original-emulator byte producer candidate set.
