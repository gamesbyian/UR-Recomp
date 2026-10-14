# QA-08: original native HDMA COLDATA write-source provenance

**Prepared diagnostic only, native validation still required.**

The accepted genuine native two-player source PPU experiment #1433 discovered **two distinct live fixed-colour operands**: at source coordinate (133,50), `fixed15=0x000F` (red15); at (133,162), `fixed15=0x0260` (green19). Both pixels have BG3 red13 main and OBJ subscreen. Source journal base `fixed15=0x0260` does **not** capture rendering-phase HDMA, so it is not enough to identify the address/channel that writes red15 above.

Unlike extrapolating from two colours, the pinned native SNESRecomp [DMA engine](https://github.com/baldosa/snesrecomp/blob/075fbe4c/runner/src/snes/dma.c) already knows the **actual** A-bus source address/bank, HDMA channel, mode, direct/indirect table cursor and target BBUS register at the instant it executes each write. Its `dma_doHdma()` invokes `dma_transferByte()`, marks the write as `kPpuWlogHdma`, and writes BBUS register 0x32 for `$2132 COLDATA`. Read these values there rather than reconstructing speculative ROM table addresses.

## Safe source probe

`tools/qa08_patch_hdma_coldata_source.py` is a fail-closed text patch to **only the disposable pinned Baldosa `runner/src/snes/dma.c` checkout**. The opt-in `UR_QA08_HDMA_COLDATA_FRAME=2208` logs actual `$2132` **HDMA-origin** bytes only, after their ordinary PPU register write. It reports SNES framebuffer/PPU journal frame/tag, actual DMA channel, byte value/RGB selectors, source `bank:address`, HDMA mode, table pointer, whether indirect, and the PPU's live 15-bit fixed-colour register *after the byte*. Missing opt-in is silent; more than 2,048 bytes emits an explicit overflow failure marker.

`tools/qa08_analyze_hdma_coldata_source.py` refuses to analyze a supposed native log unless the independent exact original-native two-pixel report still verifies guest frame2208, 2,473 guest CRCs, true BG3/OBJ composition, and live fixed15 both rows. It fails closed on absent/malformed/overflowing source records, wrong SNES BBUS address, unexpected frame/channel/mode, and preserves the entire actual ordered byte stream plus source bank/cursor in machine-readable JSON.

**Important boundary:** Even a complete source-byte stream does not automatically establish that an observed channel caused the specific PPU pixel at y50 or y162. The pinned emulator performs HBlank HDMA after each line, and `ppu_wlog_position` has its own frame/line tagging. Actual source byte order and register states, independent beam-to-row alignment, and original PPU compositor values must be reconciled before attributing a channel/table to a physical displayed scanline. No full real SNES timing claim or global colour fix is permitted.

## Proposed later native acceptance without a factory

After current 26-pixel #1453 native proof completes, apply the DMA patch immediately before compiling the same existing pinned native 2P executable, and enable its env only for the already-required unmodified stock 2P guest2208 route. The original SHA256 and full guest CRC gates must remain unchanged. Run the offline reader on that original native log and the already-produced `ws342_native_main_sub_pixel_2208.json`, saving its report in the existing native evidence artifact. There is **no need to run an independent long GHA research campaign** or to inject memory/graphics writes. Avoid editing active jobs while they run. This preparatory code **does not yet establish any observed source channel or RAM address**.

Still excluded: gameplay/oracle, Modern/frontend/persistence, independent release QA certification, original physical SNES hardware acceptance and all owner-vetoed procedural HD character art.