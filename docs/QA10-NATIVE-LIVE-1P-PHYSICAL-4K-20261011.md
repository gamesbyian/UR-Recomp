# QA-10: live original 1P, genuine physical 3840×2160 output

**Status: pending exact-head native AOT.** This is a bounded,
independent native physical-output witness, not approval for HD art,
release, alternate output GPUs, a general live display settings claim,
or the existing 2P screenshot's reuse as 1P evidence.

## Previously accepted and missing proof

The graphics AOT already establishes **different independent
native 1P USA guest runs** for the genuine 342×224 *live wider-world*
Original frame at guest2208 and its full 1368×896 nearest-neighbour
4× density copy, with matching complete guest CRC and seven or more
unaltered Original screenshot samples. The tested source contains
real live 1P top racer OBJ and wide margins; it must not be
substituted with the distinct 2P same-frame raster.

A separate accepted **2P** test at guest1856 and2208 proved actual
*physical* 3840×2160 SDL2 `SDL_RenderReadPixels` output, independently
certifying source→4× density→physical Original 7:6-PAR 16:9
pixel mapping, with fixed-point 16.16 SDL nearest sampling. The
fixed 256×224 Original has another centered, matte-padded
physical 4K acceptance. However, neither 2P nor centered mode
proves the physical **live 1P wider-world** rendering.

## One source-faithful native experiment

The existing `.github/workflows/baldosa-core-spike.yml`
reuses the **same already compiled Baldosa guest and existing
3840×2160 Xvfb display**. It launches exactly *one* additional
normal `race_1p.txt` deterministic guest route, with the
standard Original `UR_BALDOSA_WS342_LIVE=1`, widened 342-wide
game source, `UR_BALDOSA_HD_DENSITY=4` and the existing
opt-in diagnostic readback selector for guest2208.

The already installed disposable, bounded physical-readback adapter
captures the entire actual 3840×2160 **SDL drawable** from
`SDL_RenderReadPixels` **after 4× texture composition and
before `SDL_RenderPresent`**. A 1368×896 source texture is not
accepted as a substitute for a 3840×2160 capture.

Pass conditions, all fail-closed:

- A real diagnostic log matching original guest2208 and output
  **3840×2160**, with `status=saved`; a complete RGBA PAM file.
- **Every** native guest CRC entry matching the untouched USA
  stock **1P** guest route, not merely a successful exit.
- Independent 1× source and 4× screen comparisons from this
  newly executed physical host process versus the **earlier
  independent accepted 1P route**, with at least **three** full
  same-guest Original pixel-frame matches.
- Exact same-frame `342×224` original capture and independent
  `1368×896` 4× density capture already accepted in the 1P
  workflow. All 8,294,400 physical output RGBA pixels are
  checked against the original source via the pinned SDL2
  16.16 nearest resampling and 7:6 PAR viewport mapping.
  A single wrong physical pixel or alpha fails, including
  edges, split-like seam locations, margins and matte.
- The adapter remains absent from all production host code;
  its controls are cleared before the next guest route,
  leaving subsequent fixed Original and 2P acceptance intact.

**No imported image data or AOT binary** is checked into Git.
The compact report
`baldosa-evidence/ws342_live_1p_physical_4k_frame2208.json`
records native source/density/physical SHA, dimensions,
viewport geometry and documented limitations. The independent
screen-density agreement report and native guest log remain
in the **existing** AOT artifact.

## Reproduction and regression boundary

The existing standard-library-only strict oracle is reused
rather than creating a second scaling algorithm:

```sh
python3 tools/check_baldosa_physical_4k_capture.py \
  --source native/baldosa-ws342-live-1p/ur-baldosa-ws342-002208.pam \
  --density-4x native/baldosa-ws342-live-1p-4x/ur-baldosa-ws342-002208.pam \
  --physical-4k native/ur-baldosa-output-live-1p-002208.pam \
  --frame 2208 --out native/ws342_live_1p_physical_4k_frame2208.json
python3 -m unittest tests.unit.test_baldosa_1p_physical_4k_native_scope
```

The physical image is a **temporary CI diagnostic**; the report
retains its SHA and exact-pixel acceptance without shipping
or reproducing a copyrighted gameplay screenshot. That is
a sensible size limit: a full 3840×2160 RGBA frame is ~33 MB
before an archive, and retaining its validated digest and
native full-guest provenance avoids turning CI artifacts
into a ROM-art distribution.

Even a green exact-head run only proves that **this** real
1P guest frame has faithful Original SDL2 physical output in the
pinned software-renderer environment. It does not prove all
modes/games/screens, that physical consumer GPUs match the SDL
software backend, arbitrary 4K display reconfiguration in the
Windows Modern host, approved 3D unicycle likeness, general
OAM/BG/window HD occlusion or QA release certification.
Preserve the authentic Original fallback and the separate
independent release ledger.
