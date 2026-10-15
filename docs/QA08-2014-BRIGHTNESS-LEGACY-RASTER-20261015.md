# QA-08 original 2014 Snes9x brightness: active legacy PPU closure (2026-10-15)

**Status: title-scoped Windows candidate, NOT an accepted graphics or release gate.**

The original/reference Snes9x build pinned by `tools/toolchain-entries/snes9x-libretro.json`, revision `1bcc369e89f08243e0a462882fb1f3e42e51de3a`, stores an explicit `mul_brightness[16][32]` table in `globals.cpp`. Inspection of all 512 literal entries found **zero** deviations from:

```
scaled_SNESC5 = (channel5 * brightness + 7) / 15;
screen8 = (scaled_SNESC5 << 3) | (scaled_SNESC5 >> 2);
```

This is *not* the previously compiled 8-bit-first `((channel5 << 3)|(channel5 >> 2))*brightness/15` when the register is neither full bright nor zero. For instance, 5-bit 17 at register 14 yields **132** original versus **130** under the previous algorithm; 5-bit 9 at register 7 yields the source-defined result using rounding in 5-bit.

## Independently reproduced failed-first-patch boundary

Historical source pin **#1641 at `c8c01ead7fab5ead34a2f6504ace57ebdf6c605f`** compiled a preliminary 5-bit correction in `snesrecomp/runner/src/snes/ppu.c` only. Actual Win32 [run 38705798457](https://github.com/gamesbyian/UR-Recomp/actions/runs/38705798457) passed the real Windows executable build, complete 11-journey batch, and captured 261 scene source P7 images. However its actual source-sized raster **did not change**: independent comparison of native artifacts **11958061951** (before; full ZIP SHA `44becef0c15a30761c22180df47f8b7efe3957f95e6d18f295c11615e73fb78c`) and **11958940630** (after lookup-only; SHA `03b62fd8b657375a83c4d61865c252956e7de718c4624d50240f56e7bc2713f2`) found **0 changed pixels in every frame**, with identical full **5,447-frame guest CRC SHA** `45d7675858ebf3e3a051a58d2af104b6d2d9a66e7700da8248ad571713662c41`. Against independently executed original reference artifact **11956993823** (ZIP SHA `1b2fb01338380dc7e4d093ccbb0a5778bd04388945ee0bc7eb5b910d4de3ca59`), **149 of 261 frames remain exact; 112 diverge, 5,667,072 RGB5 wrong source pixels total**.

The pinned PPU dispatcher at `runner/src/snes/ppu.c:841-850` chooses `PpuDrawWholeLine` **only** when `kPpuRenderFlags_NewRenderer` is set. Otherwise it calls **`ppu_draw_whole_line_legacy`**, whose actual `ppu_render_pixel` in `runner/src/snes/ppu_legacy.c` still directly applied brightness to **8-bit expanded** B/G/R after resolving original PPU layer order and math. This separate active renderer path precisely explains the no-op, without assuming a guest timing error or falsifying the source evidence.

Offline *diagnostic* direct LUT reversal on genuine old Windows pixels suggests 14/15 brightness in menus/results, while countdown guest1536 behaves at 7/15. At original 1P guest1280 source-mismatches go **50,962→254** under an assumed display-colour remap; at guest1536 **55,696→0**; guest3776 **50,834→0**; guest4000 **52,302→159**. This is not a compiled PPU receipt, since reconstructing the prebrightness 5-bit colour from an already-expanded final 8-bit pixel can be ambiguous in rare sprite/colour-math contexts. Do **not** promote these counterfactuals as release test results.

## Corrected active implementation and safety

The updated `tools/baldosa_uniracers_brightness_pixel_lut_patch.py` now checks and stages **both** `ppu.c` (new renderer, preserved) and `ppu_legacy.c` (the actually running Original display), with all revisions and exact source assignment windows pinned. Both transformations are validated before writing either staged file. No cross-title SNESRecomp core file is committed or modified, only the disposable Windows `gamesbyian/uniracers-recomp` source checkout at exact title SHA `10b864b9d14a7b7416dd909eb7b054c88faef101` and core SHA `075fbe4c8e0d97b0013be541795c39cb644a9709`. The three legacy output channels now quantize their native 5-bit B/G/R using the original 512-entry rule *before* expanding to 8-bit, preserving the same PPU colour math, window, sprites, alpha and 256×224 output. Existing HDMA-first-line source correction remains independent.

The source-guarded unit tests cover both code paths, exact 2014 values and all 512 mathematical entries, idempotence, rejected partial/foreign source and preflight no-writes on failed source checks. A corrected Win32 binary and **same 261 whole-frame independent original Snes9x** comparison are required before reporting any new exactness. The first sign of a new raster error is a blocker, not a licence to mask pixels or shift frames.

**Remaining gates:** continuous moving 1P/2P event source and phase, finish/results and return, OAM/window effective raster, 342-wide authentic widescreen world margins (not a 216-high crop), 4× Original and upscaled fallback, original-style controller-first options seam, actual physical Windows capture, and artistically approved official racer identity/proportions. Release ledger remains untouched.
