# QA-08 real Windows original raster correction and current blockers (2026-10-15)

**Scope:** independent actual original-USA Snes9x reference against the source-sized **real playable Windows** `UniracersSNESRecomp.exe`. This is a graphics-source acceptance receipt, not an accepted release ledger gate, completed guest event, 4× remaster approval, physical display validation or 216-high cropped approximation.

## Positive real product correction: V0 HDMA before the first visible pixel

Compiled Windows graphics branch: draft [#1641](https://github.com/gamesbyian/UR-Recomp/pull/1641), head `b55c3d64d318ff27381a36fce3ac329f9637a320`. [Native Windows CI 38810338859](https://github.com/gamesbyian/UR-Recomp/actions/runs/38810338859) passed its Windows build, 11 existing player journeys and four-frame 2P source control. The exact executable SHA-256 is `362746e641a03476e5230598fc91ddf2a91e218f5cf3d6fb4166c7033f8020cb`. Two source producers then emitted 261 full-size 1P and 263 full-size 2P real post-PPU images. [Independent archive-only CI 38812998990](https://github.com/gamesbyian/UR-Recomp/actions/runs/38812998990) adjudicated both against the original Snes9x references and the immediately preceding Windows build, with no fresh emulator execution.

| Measured exact original/native source property | Before V0 fix | After V0 fix |
| --- | ---: | ---: |
| 1P 256×224 RGB5 exact | 162 / 261 | **162 / 261** |
| 1P wrong source pixels | 19,153 | **19,153** |
| 1P native P7 frame bytes changed | | **0 / 261** |
| 2P 256×224 RGB5 exact | 190 / 263 | **203 / 263** |
| 2P wrong source pixels | 786,347 | **385,373** |
| 2P improved frames | | **15** (3648–3872 step16) |
| Previously exact 2P source frames regressed | | **0** |
| 2P erroneous RGB5 pixels removed | | **400,974** |

Each of those 15 2P frames has the same underlying original scene geometry and background palette; **13 become completely pixel-exact**, two retain only one wrong pixel. Native **5,447-frame 1P and 5,484-frame 2P guest CRC transcripts are unchanged**. The original Snes9x `$2100` HDMA V0/V111/V113 brightness `07/00/07` at source frame 3683 is now reproduced by the compiled Win32 PPU at the correct upper/split/lower lines. Source-backed live channel-7 table `$7E:2064–206B = 6f07020060070000` and CGRAM checksum `e79794a9` also agree. The actual defect was registered CPU vblank `INIDISP=0F` being replayed *after* V0 HDMA 07 and overwriting the first-line brightness. The correction moves register/HDMAEN line0 replay **before** `dma_initHdma` and `dma_primeHdmaFirstLine` in only the disposable pinned Uniracers Windows title. Pixel aspect policy, original 256×224, split-screen geometry, guest code, clock and Modern paths are untouched.

Machine/producer receipt: `analysis/data/qa08-compiled-Windows-v0-before-HDMA-corrected-20261015.json`; archived image SHA files and all per-frame 1P/2P comparisons are in the independent Actions artifact.

## Negative CGRAM completed-field experiment, deliberately not promoted

The results checkerboard remains a separate, source-proven phase discrepancy. At original Snes9x result frame 5184, CGRAM FNV1a is `e8cdbe60`; the native display has `898ece20`, even though both use brightness 14 and CGADSUB 7F. Similar checkerboard mismatches repeat every 112 frames. Native results around 4016 also show a source-visible blackout transition discrepancy; small OBJ selection-arrow/medal colour differences persist in otherwise aligned frames.

The pinned PPU raster journal excludes CGRAM port writes `$2121/$2122`. A separate source-pinned, title-only field-completed CGRAM snapshot and restore experiment was tested as [draft #1666](https://github.com/gamesbyian/UR-Recomp/pull/1666) on top of the accepted V0 branch. The experiment captured 256 palette words at the V225 field boundary, showed that completed-field palette during scanout, then restored every live guest CGRAM word, pointer, buffer and write-twice latch. Actual Windows [CI 38813922158](https://github.com/gamesbyian/UR-Recomp/actions/runs/38813922158) compiled that code (`applied=1`), passed the existing player journeys, and produced authentic 261-frame 1P and 263-frame 2P raster archives. **Every single one of 524 original-sized Windows source frame hashes remained byte-identical to the previous V0 build.** Every source pixel comparison and all 1P/2P guest CRCs likewise remained unchanged. The result-CGRAM checksum at 5184 was still `898ece20`. Thus this particular snapshot hypothesis is **falsified for the observed scenes**. It was not merged into #1641 and #1666 was closed.

Negative machine receipt: `analysis/data/qa08-cgram-completed-field-negative-source-result-20261015.json`.

A naive global remapping of the four checkerboard gray values `123,132,140,165` has also been rejected: in an otherwise nearly exact frame 4032 it introduces around **24,500 new incorrect pixels**, and on frames 4064/5184 it reduces only roughly 8,000 errors while leaving ~16,500. A palette-slot/raster-phase diagnosis is required; visible pixel recolouring is not acceptable.

## Bounded next discriminator, ownership boundaries

A source-qualified, read-only original/native **CGRAM data-port write chronology** around neighboring result guest frames 5183–5184 is now required. The original Snes9x register dump at 5184 has **zero $2121/$2122 writes in that frame**; knowing the adjacent preceding write frame and native matched beam/CPU phase would distinguish stale/advanced palette state from raster arithmetic. Coordinate that boundary with the gameplay/original verifier and CPU/APU agent. **Do not edit their timing, instruction emitter, persistence, Modern business logic, or alter controller scripts to force image parity.** Without that source witness, no source-backed second renderer correction can be claimed.

Graphics release blockers persist: 1P menus/selection sprites (19,153 sparse-pixel errors), 2P results/checkerboard/blackout (385,373), independent complete 1P/2P event and camera phase, actual Windows physical 4× Original/appropriate Upscaled fallback/widescreen extra-world geometry and 7:6 PAR, HD racer likeness/proportions with human signoff, and physical controller/audio/display acceptance. QA-08/10 and release ledger remain **unadmitted**. Both #1641 and research #1649 should remain draft until their appropriate authority has reviewed them. No new autonomous emulator farm is needed merely to increase capture volume.
