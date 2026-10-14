# QA-08: independent original Snes9x live channel-5 PPU colour transfer

**New original source experiment, status pending exact-source execution.**
The pinned original USA 2P palette-table writer and selector branches are
already authenticated: original executed 65816 frame1781, upper selector0,
lower selector2, six descriptors in WRAM `$7E:2084..2095`, and two original
four-byte ROM lookups. Separately, Baldosa native executed channel5/mode1
register writes and original PPU compositor RGB at native guest2208 have
been measured. The missing original *render-time register transfer* is a
distinct, independently falsifiable step, rather than another CPU journal.

## Pinned original Snes9x dataflow

The original emulator implementation
`snes9xgit/snes9x@1bcc369e89f08243e0a462882fb1f3e42e51de3a`
puts actual channel5 data transfer in `dma.cpp::S9xDoHDMA` and receives
the actual B-bus writes in `ppu.cpp::S9xSetPPU`.
The former marks `CPU.InHDMA`, sets
`CPU.CurrentDMAorHDMAChannel`, reads the direct table at current
`DMA[5].Address` and calls `S9xSetPPU` in mode1 twice with
B-bus offsets 0/1; **only after** those writes does it advance the
DMA table address. Snes9x's PPU implementation of `$2132`
conditionally updates `PPU.FixedColourRed/Green/Blue` using
the byte's component-enable bits.

`tools/instrument_snesref_qa08_original_hdma_ppu.py` patches only
a disposable copy of that original Snes9x `ppu.cpp`.
The injected read-only observer activates only for the exact env
`UR_QA08_ORIGINAL_HDMA_PPU_WINDOW=1781-1783`, requires real
`CPU.InHDMA` and channel5, and fires *after* the underlying
`$2131` or `$2132` PPU write, never in place of it. It captures
actual original CPU frame/V/cycles, source table pointer and
bank, HDMA mode/indirect/config, original WRAM byte, actual BBUS value,
CGADSUB, CGWSEL, and the **live after-transfer RGB15 fixed colour**.
128 actual writes is the explicit bound, with an overflow failure
marker. The regular emulator and guest input logic remain unchanged.

The probe deliberately **does not require observed source bytes to
equal native results**: a changed byte can be an informative original
register discrepancy, not permission to doctor the original trace.
`tools/check_qa08_original_hdma_ppu.py` preserves any disagreement
against the accepted original writer table and byte readback, but
requires genuine paired channel-5/mode1/direct original register
events, six source descriptors, and the pinned original-USA ROM,
controller script, exact 18-writer, frame1781 and full t480-WRAM
source witnesses. The checker refuses duplicate evidence JSON keys,
missing/odd PPU register pairs, invalid beam/config, different
input/ROM/WRAM receipts or observer overflow. The ordinal and
original CPU beam are kept to detect real chronology deviations.

## Execution and acceptance

Extend the existing one-process original
[writer/selector workflow](../.github/workflows/qa08-original-hdma-writer-opcodes.yml).
Its source compilation and exact original 2P route are already tested.
The existing route still requires `$0DDB=1`, `$0313=1`, 55 executed
original CPU opcodes, all 18 original WRAM writer PCs and the original
ROM/core/input/final WRAM fingerprints. After those receipts, the new
validator writes `qa08-original-live-hdma-ppu.json`, retaining that
report in the existing original-source evidence archive. The
dependency-free negative tests exercise source-patch drift, ungated
execution, incorrect channel/mode/address, forged register and
out-of-order beam, missing BBUS companion, overflow and false frame
parity. No separate runner, asset output, emulator route or network
download is needed.

**What this can prove:** actual *original Snes9x* live channel-5
register transfer bytes, PPU readback and emulator scanline tags
in the genuine original USA 2P route. It can measure discrepancies
relative to the already accepted native register byte sequence, but
the route clocks are not yet paired.

**What this cannot prove:** original/native same-input exact
physical frame pairing, finished original Snes9x RGB pixel equivalence,
the proprietary Snes9x Uniracers OAM hardware-accuracy hack,
physical SNES scanline timing, universal P1/P2 sprite occlusion,
Widescreen/HD feature quality or approval of rejected
procedural racer artwork. Continue the source-attested same-state/
same-pixel comparison before promoting Windows release graphics.
Keep canonical 256x224 at 7:6 PAR, genuine widened world and 4x
Original fallback unchanged.
