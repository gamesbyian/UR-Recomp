# QA-08: independently observed original Snes9x $2100 brightness-HDMA source

**Accepted original source replay, run 38546562780 (artifact 11884792090).** The existing
[finished source-pixel reference](QA08-ORIGINAL-NATIVE-2P-RGB5-SPLIT-BAND-PIXEL-20261014.md)
matches **56,832/57,344 original/native RGB pixels** after source
RGB565 green6→native green5 normalization. The 512 different pixels
are exactly full-width rows111 and113, accounting for a single-row
split-band offset. Actual original `go.ppuw.tsv` has two genuine
`$2100 INIDISP` HDMA writes: `00` at V111 and `0F` at V113.

**Important:** `$2100=00` sets **PPU brightness 0**; the
hardware forced-blank flag is bit7 and is **clear**.
`$2100=0F` restores brightness to 15. The original
source `ppu.cpp::S9xSetPPU` handles brightness and forced bit
as distinct state. Do not conflate *black output* with bit7 forced blank.

The new supplemental source observer
`tools/instrument_snesref_qa08_original_hdma_ppu.py`
reuses the exact existing original Snes9x read-only
`UR_QA08_ORIGINAL_HDMA_PPU_WINDOW=source-go-t480` arm,
restricting itself to the same twelve original frame
windows and requiring an actual `CPU.InHDMA` on the
original Snes9x source `case 0x2100`. It is called
**after** the actual PPU brightness/blanking handler.
It separately records original frame, V-counter, cycles,
actual HDMA channel/mode/directness, table bank/address,
BBUS byte and **PPU.Brightness + PPU.ForcedBlanking after
the write**. Any source channel is permitted; neither
original nor native $2100 channel ownership is guessed.
It neither writes memory nor changes original instructions,
controller inputs, PPU or display scheduling.

The strict checker
`tools/check_qa08_original_inidisp_brightness.py`
requires source original ROM/input/final 2P WRAM/55 opcode/
18 source-writer receipt, ordered live original HDMA
observations, correct separate brightness low nibble and
bit7 semantics, and a real original GO V111/V113
source transition that agrees with *independent*
`go.ppuw.tsv` events in the same already-accepted archive.
No synthetic test source values or emulator frame tags
are promoted as actual. The accepted run report is
`qa08-original-brightness-hdma.json` in the **existing**
single original 2P AOT workflow and archive, with zero
new runner factories.

When this original source is accepted, compare to the
separately pending native true `$2100` after-BBUS
INIDISP observation. The discrepancy is not enough to
authorize a global native line offset or shipping UI/HD
asset change until the real source PPU row relationship
is proved. Original 256×224, 7:6 PAR, 4× fallback and
authentic wide-world materialization remain unchanged.


## Accepted observed source result

The real original Snes9x run captured **24 actual channel-7 direct-mode-0
INIDISP events** across the eight sampled frames. Original GO
frame 1989 has source `7E:2065` → `0F` at V0,
`7E:2067` → `00` at V111 and `7E:2069` → `0F` at V113,
with live brightness **15, 0, 15** and **forced-blank bit clear**
at each write. Its separately instrumented source PPUW journal agrees.
The native original-source-frame guest2208 test independently confirms
channel7, mode0, direct, and those same WRAM source bytes, with write-log
tags 0/2/113/115. Both exact-head source runs passed their gates.
The unresolved component is the relationship of logged transfer tags to
the final displayed row at the one-line-shifted 2P black seam.
See the [paired source SHA handoff](../analysis/data/qa08-original-native-2p-brightness-split-channel7-handoff-20261014.json).
