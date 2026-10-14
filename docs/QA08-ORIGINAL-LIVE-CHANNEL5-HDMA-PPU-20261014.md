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
`UR_QA08_ORIGINAL_HDMA_PPU_WINDOW=source-go-t480`, requires real
`CPU.InHDMA` and channel5, and fires *after* the underlying
`$2131` or `$2132` PPU write, never in place of it. It captures
actual original CPU frame/V/cycles, source table pointer and
bank, HDMA mode/indirect/config, original WRAM byte, actual BBUS value,
CGADSUB, CGWSEL, and the **live after-transfer RGB15 fixed colour**.
512 actual writes is the explicit bound, with an overflow failure
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

## First authentic negative and bounded follow-up

The first exact-head original Snes9x run
[38521340789](https://github.com/gamesbyian/UR-Recomp/actions/runs/38521340789)
**failed the new live-PPU presence gate** while still passing the
independently required 55 executed opcode, two original selector,
18 source writer, original script and final WRAM checks. The emitted
archive had **zero** `UR_QA08_ORIGINAL_HDMA_PPU` records within
original frames **1781–1783**. This cannot be upgraded to evidence
that the original game never uses HDMA: the probed original range
includes palette-table construction, before the actual GO script
checkpoint at original frame1989. No core/source error occurred during
instrumentation or compilation.

The next narrowly discriminating real replay retains the same pinned
original process and observes only **four explicit three-frame
windows**: 1781–1783, 1988–1990 (around source GO=1989),
2231–2233 (around scripted t240=2232), and 2471–2473
(around t480=2473). Each has a separately reportable actual
original frame and beam tag; the 512-record overflow guard now
covers these 12 frames without emitting all ~2500 original game
frames. In the same existing artifact, preserve original `go` and
`t480` source `*.ppuw.tsv`, `*.info.json`, and exact
256x224 `*.fb.bgrx` outputs already captured by `snesref`.
These are **original Snes9x PPU and RGB source** outputs, not
independently aligned against Baldosa's native frame2208
or its 342-pixel-wide presentation. A real mismatch is evidence
to investigate, not a reason to force expected channel5 native values.


## Authenticated original runtime result (2026-10-14)

**Original Snes9x run [38521827670](https://github.com/gamesbyian/UR-Recomp/actions/runs/38521827670) succeeded.**
Source artifact **11873899132**, downloaded ZIP SHA-256
`17380f2e8d5c7d2f43eac5bd98cf5661d9fb1c3900cd7cafb1b9479784ada234`.
The actual generated original live PPU report SHA-256 is
`cb48890b00c9247a20cf5ec0aeec44bd06fec709120c86a36c5b9ad5b8b39ef9`.
The instrumented original Snes9x core SHA-256 is
`77e5a54bf91acec539eeb6475c7910d5ad546172624c6d70fd9e1dea545f6986`.
The genuine 2P script and original t480 WRAM SHA match the earlier
authenticated 18-writer and two-selector results **byte-for-byte**.

The original's live PPU observer measured **96 real channel5/direct/mode1
register writes, 48 adjacent $2131/$2132 pairs**, across eight original
Snes9x frames **1988, 1989, 1990, 2231, 2232, 2233, 2471, 2472**.
**All 96** original HDMA BBUS bytes agree with the independently read
live original WRAM source and all 96 match the originally executed
18-writer table bytes. The unproductive early window 1781–1783 is
a true negative observation, explained by the source instrumentation
not yet observing those live transfers there. It is **not** proof
of globally absent original HDMA.

| True original emulator V | Original $2131 + $2132 source | Live original RGB15 after transfer |
| --- | --- | --- |
| 0 | `7E:2085/2086` → `04/2F` | `026F` |
| 1 | `7E:2088/2089` → `04/40` | `000F` |
| 2 | `7E:208B/208C` → `04/80` | `000F` |
| 111 | `7E:208E/208F` → `04/20` | `0000` |
| 112 | `7E:2091/2092` → `04/53` | `0260` |
| 113 | `7E:2094/2095` → `04/80` | `0260` |

The original `snesref` independent per-register PPUW journal at **GO
frame1989** reproduces all six live-register pairs at the same V tags,
including two horizontal PPU writes separated by **two reported SNES
dot units** within each pair. The normal journal also includes CPU
`$2130` writes that cannot be inferred from the channel5-only observer.
The two source observers have different logging owners within the same
emulator, so agreement is a **same-core instrumentation crosscheck**,
not independence between emulators or proof of original hardware.

The separately accepted **native** channel5 writes retained a
before-first-line prime and tags 2,3,4,113,114,115. The original
captures above report tags 0,1,2,111,112,113. The *written values
and final fixed-colour states match*, while source event tags and
priming presentation differ. The exact cause of those tag offsets
remains a renderer/beam-phase alignment question; **do not patch
either core or declare final original/native source-image parity**.

The pinned archived source manifest
[`analysis/data/qa08-original-snes9x-2p-hdma-live-pixel-source-handoff-20261014.json`](../analysis/data/qa08-original-snes9x-2p-hdma-live-pixel-source-handoff-20261014.json)
contains both source report hashes and exact original
`go`/`t480` framebuffer, `ppuw.tsv` and metadata SHA-256.
`tools/qa08_original_snesref_raster_source.py` verifies the
256x224 original BGRX and per-frame PPUW transport; new
`tools/qa08_crosscheck_original_live_ppuw.py` verifies original
GO PPUW register and byte order against the genuine live PPU report.
The original framebuffer outputs do **not** yet carry an
input/frame-aligned native 256x224 pixel oracle.
