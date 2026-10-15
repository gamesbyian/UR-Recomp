# QA-08 source-certified 2P finish and results PPU register trace (2026-10-15)

**Actual original Snes9x register witness, not a Windows correction or a CPU-phase acceptance.**

The full-route original 2P source was previously captured from pinned 2014
Snes9x as **263 full-size 256×224 BGRX callbacks**, all ending at original
script frame **5484**. That source has been independently compared against
the corrected playable Windows executable: **190/263 exact**, **73
divergent**, **786,347 incorrect RGB5 pixels**, with the large divergences
concentrated in the finish fade and results-screen checkerboard animation.
The reference images were not discarded or replaced with screenshots.

The original harness already provides a patched `snesref_debug` register
export and exact `$2100–$2133` per-frame PPU write journal. Rather than
guess native brightness from screenshots or alter the original guest, I
introduced **only three additional zero-frame `dump` instructions** at
natural input-script command boundaries. The analyser proves that removing
those three commands returns exactly the stock original script minus its
`turbo on` acceleration directive, byte for byte. It re-executed all
**263 original frame callback captures and verified that every raw image
SHA-256 equals the untouched prior original source**. The original input
sequence, CPU execution, PPU imagery and frame count were therefore not
perturbed by the diagnostic observations.

Original PPU source: [run 38791934542](https://github.com/gamesbyian/UR-Recomp/actions/runs/38791934542), artifact `12000438001`,
whole ZIP SHA256
`d5e08ad76137c86125f64d52b6d0dc689352375ab536f4c430238f3bc6d6908e`.
The read-only source script SHA256 is
`bddfb15fedbaba3fcb0e95e628f11e1506fd210d93f4be67c6e9855c705dd3db`.
Diagnostic original `snes9x_libretro.so` binary SHA256 is
`11cd574e85e003986ad4633b47ce126f8c1867d54912e18c7aa6b84e074f3975`.
It is **not bitwise identical** to the earlier original-source compiled
binary, but exact 263/263 source-image replay establishes the narrow
reproducibility requirement of this register experiment. This does not
resolve independent toolchain binary reproducibility.

| True original scene | Snes9x frame | `$2100` V0 / V111 / V113 HDMA | Final brightness | `$2131` | CGRAM 512-byte FNV1a |
| --- | ---: | --- | ---: | --- | --- |
| Before finish | 3622 | 0F / 00 / 0F | 15 | 04 | `fe405bb5` |
| Finish fading | 3683 | **07 / 00 / 07** | **7** | 04 | `e79794a9` |
| Results | 5184 | No `$2100` writes in sampled frame | 14 | 7F | `e8cdbe60` |

Both the pre-finish and fading scenes also contain CPU `$2100=80`
forced-blank writes during V225 and restoration to `0F` near V242–243.
The early visible line's effective brightness is then independently
replaced by HDMA at V0. This establishes the original dual-camera
**three-band source behaviour**, including a true zero-brightness split
line and two equal upper/lower bands. It is consistent with the earlier
source-qualified brightness-seam correction and says exactly what the
native PPU register stream must accomplish.

The results screen instead uses mode 3, colour-math `7F`, brightness
`0E` and animated grayscale background. A checkerboard image mismatch
repeats at native frames 4064, 4176, …, 5408 (112-frame cycle), while
other nearby frame samples are source-exact apart from a small OBJ
colour difference. The registered source images and pixel-mask analysis
do not support shifting/cropping the whole image to repair it.

## Independent comparator handoff and gate

A separate graphics-owned **opt-in read-only native Windows PPU probe** is
now staged on draft PR #1641. It logs the active legacy PPU's INIDISP
brightness/forced-blank, CGADSUB, CGWSEL, fixed colour, and full CGRAM
FNV1a at the same bounded finish and results intervals. It does **not**
write guest code, DMA buffers, OAM, registers, Modern state or render
pixels, and is disabled in ordinary player sessions.

Once the Windows PPU probe completes, require:

1. **Same 263/263 native RGBA P7 source hashes** as the previously accepted
   full-route Windows capture, and unchanged native 5484-frame CRC receipt;
   otherwise the observer experiment is invalid.
2. Compare original and Windows register states at source-qualified
   frame boundaries and effective scanlines, taking account of source
   `retro_run` callback/guest numbering and HDMA V-counter semantics.
3. If native `$2100` is wrong at the finish, pass an exact register/beam
   timing witness to the owning CPU/guest/HDMA lane before altering
   timing or guest state. If registers are equal but source pixels
   differ, localize the raster/compositor error in this graphics lane.
4. For the result checkerboard, establish whether CGRAM and native
   scrolling/tile register state really match before changing colours
   or inventing an animation-phase fix.

Machine-readable register provenance:
`analysis/data/qa08-2p-original-INIDISP-HDMA-colormath-trace-20261015.json`.
The archive includes actual `*.regs.json`, `*.ppuw.tsv`,
`*.cgram.bin`, `*.oam.bin` and `*.info.json` files, not only a prose
interpretation. The original SNES logical frame is **256×224** with
authentic 7:6 display pixel aspect; no 216-line crop, HD racer replacement
or source-masked acceptance is permitted. The 4× Remastered
character likeness is still artistically unapproved, and **no release
ledger gate has been admitted by this experiment**.
