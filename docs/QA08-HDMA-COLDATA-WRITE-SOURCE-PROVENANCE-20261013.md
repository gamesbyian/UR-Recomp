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
