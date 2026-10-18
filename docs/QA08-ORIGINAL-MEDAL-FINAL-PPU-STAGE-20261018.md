# QA08 original 2014 Snes9x result: actual final main pixel source

**18 October 2026. Read-only original renderer evidence; no cross-emulator parity claimed.**

## Immutable execution identity

- Original game: retail USA ROM SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`; pinned original Snes9x source `1bcc369e89f08243e0a462882fb1f3e42e51de3a`, compiled through already pinned source route. Exact 2014 original controller script `tests/input/qa08-original-medal-source-2014.script` SHA256 `bddfb15fedbaba3fcb0e95e628f11e1506fd210d93f4be67c6e9855c705dd3db`; it reached `script f=5484 quit`.
- Original-only diagnostic implementation is isolated on [#1836](https://github.com/gamesbyian/UR-Recomp/pull/1836), tested on exact head `7b20100d211870b54c4262fa06ab90031525392b`; real pinned-original execution [run 39164293633](https://github.com/gamesbyian/UR-Recomp/actions/runs/39164293633) **passed**. Tooling/hygiene checks remain independent.
- Immutable GitHub artifact **12150037795** SHA256 `8387c413d42cf8d2da2a61ba3ec67e8375394f938171dc4d73a3e4ba567920e4`. Members: `qa08-original-medal/original-layer-stages.log` SHA256 `1a1150df39acdab30302830ae26d8fab8b2611949235c316f1eca8429776c21e`; `qa08-original-medal/active-tile-candidates.log` SHA256 `6406cd6ef186f1d01cc7c6936bc834552f265c9472448b8a2fa3b60e6d2ba6d2`; original combined log SHA256 `066436c1e6c0a7f0924353104110898b882095c88eecf17163433ed4bfe2eeee`.
- **252 real original DrawOBJS tile-call records** and **360 original main-screen renderer-stage records**. Each of 18 selected original frame labels `4028..4036` and `4172..4180` emitted 14 tile candidates (two real paint passes) and 20 stage observations (5 pixels × OBJ, BG0, BG1, FINAL). PPU screen mode 3 on these fields. Native emulator guest/input/callback equivalence is explicitly unproved.

## Original 2014 Snes9x final visible main-screen owners

Each entry below uses the **same original raster pass** and genuine source destination depth before and after the normal OBJ/BG painters. All five final values repeat at original frames 4032 and 4176.

| Original pixel (x,y) | Actual original sprite candidate | After original OBJ | After BG0 / BG1 / backdrop | Final source owner |
| --- | --- | --- | --- | --- |
| 207,91 | OBJ slot112 tile `15a0`, call **did not paint** | depth 00, RGB565 `71c9` | depth 27, RGB565 `738e` | **BG0** |
| 205,115 | OBJ slot113 tile `19a2`, depth write | depth 28, RGB565 `8183` | unchanged | **OBJ113** |
| 205,139 | OBJ slot114 tile `1da4`, depth write | depth 28, RGB565 `71c9` | unchanged | **OBJ114** |
| 225,96 | OBJ slot97 tile `15de`, depth write; later slot99 was rejected at same pixel | depth 28, RGB565 `83cd` | unchanged | **OBJ97** |
| 225,120 | OBJ slot96 tile `15de`, depth write; later slot98 was rejected at same pixel | depth 28, RGB565 `83cd` | unchanged | **OBJ96** |

`RenderScreen` actually invokes original `DrawOBJS(D+4)` **before** Mode 3 BG0 and BG1, and `DrawBackdrop()` last. Original depth 28 (hex) on the four OBJ pixels survives each later source-painter stage; depth 27 (hex) on the BG0 control is written after OBJ and survives BG1/backdrop. This is a stronger, final-layer **original main-depth ownership** proof than a sprite tile-call log or an OAM rectangle. It does **not** prove equality of resulting final RGB against an independently registered original callback/P7 image, nor source 2014 CPU-versus-native event clocks, OAM producer latching or physical LCD pixels; sub-screen and any later host blending/output transforms are outside its scope.

## Native 4bpp reconciliation and explicit identity stop

Merged [#1835](https://github.com/gamesbyian/UR-Recomp/pull/1835) independently replays a **different authentic native RF017 Windows source route** and establishes 19/19 effective native OBJ pixels from their actual last 4bpp/OAM/VRAM/priority sprite writer, with six BG controls. On its own native guest fields 4032 and 4176, (205,115), (205,139), (225,96), (225,120) are OBJ and (207,91) is a BG control. The four *slot numbers* and their native low tile IDs (`a2`, `a4`, `de`, `de`) are consistent with original isolated tile painters (`19a2`, `1da4`, `15de`, `15de`, containing original Snes9x display-mode/palette bits). This **limited corroboration is anatomical/ownership only**. It cannot establish same-render-field source pixel parity or independently validate the native 4bpp winner from the original movie: **the scripts are different**.

In particular the older 263-frame true original Snes9x P7 source archive **12075111053** uses source input script SHA256 `a6c8815482b742d90dca61645f876c15918f5d9985a027eef107ac4fdc515264`, not this probe's `bddfb15f...`. The native Windows #1835 route uses imported Baldosa `race_2p.txt`, with actual native full-guest CRC SHA `b735b018...`. No same-numbered original/native source frame or OAM packet may be equated on these different routes without a recorded **consumed-mask sequence and original callback/guest display registration**. Earlier original postrun-OAM versus native host -2 field relation is independent evidence, not a general translation applicable to this source-painter study.

**Decision:** For these original source labels, the suspected medal-region pixels are primarily winning sprite-painter pixels with real BG negative control; no invented BG overwrite is needed. The already-known fixed 296-pixel native/source RGB5 medal mismatch and real native gray phases remain **unresolved** against their own exact original script/reference, and no native correction is justified from this separate movie. The cheapest next source discriminator is to run this already-tested **read-only** painter+layer probe against the **same exact original 2014 movie** as the authenticated 263-frame source archive, preserving original callback/presentation identifiers and paired native *consumed inputs*. Do not change CPU clocks, sprite IDs, PPU tile indices, output LUT, frame labels or 342×224 geometry to force agreement.

## Production boundaries

- Clean Windows firstline/V0 [#1780](https://github.com/gamesbyian/UR-Recomp/pull/1780): **HOLD** pending final exact integrated candidate and independent source raster and Modern acceptance; its source code is not changed by this evidence.
- True operand brightness [#1807](https://github.com/gamesbyian/UR-Recomp/pull/1807): **EXPERIMENT**, separate and unmerged; source guest4016 forced-blank still divergent.
- Coherent HD-racer rig [#1826](https://github.com/gamesbyian/UR-Recomp/pull/1826): **art experiment, owner likeness approval absent**.
- Release QA ledger: untouched. No QA-08, UHD physical product or original/native complete USA event gate claimed.

The temporary source-instrumentation PR #1836 is to be **closed unmerged** after transferring this self-contained, source-hash-bound finding. Original source and native game binaries are never modified in shipping source.
