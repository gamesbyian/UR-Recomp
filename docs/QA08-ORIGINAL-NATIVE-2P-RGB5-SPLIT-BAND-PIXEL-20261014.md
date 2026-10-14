# QA-08: exact original/native 2P RGB5 pixel parity except the split seam

**Independent real original Snes9x and Baldosa native source results, 2026-10-14.**
The source hashes, scripts and exact framebuffer bytes are retained in
[`analysis/data/qa08-original-native-2p-split-seam-rgb5-pixel-parity-20261014.json`](../analysis/data/qa08-original-native-2p-split-seam-rgb5-pixel-parity-20261014.json).

The original Snes9x [run 38543766102](https://github.com/gamesbyian/UR-Recomp/actions/runs/38543766102),
artifact **11884155561**, genuinely captured 37 complete **256×224**
raster video buffers, one per original emulator callback frame 2188–2224.
Original frames have unchanged 2P script SHA
`94eaa5ffb487d9b227e34965c1d2ee09efe3dac06ade595f7dad05315dfc5221`,
the USA ROM SHA, actual 55 decoded instruction bytes, 18 executed
source table writers, two observed racer LUT indices, 96 authentic
original live HDMA colour-register events and final original WRAM
checksum. Exact full source archive ZIP SHA-256:
`6e5d488230c11d3dfcd144b6a7cbc8c25d7acfcb4f95b776a85071dd3487f5e3`.
The individual callback frame2207 source file has SHA-256:
`e76c6010b3fb339ecbdae2fec985a00019345723cdff122d9bbc78d71481c8aa`.

Compare the independent genuine Baldosa
[native 2P run 38504531564](https://github.com/gamesbyian/UR-Recomp/actions/runs/38504531564),
artifact **11867072862**, using **only** its original-source-size
256×224 `baldosa-fixed-source/ur-baldosa-original-source-002208.pam`.
P7 full source SHA-256:
`a946c9ebb54775639b8fd87a6861af0408cceed4896e58be05908c4a4491c67f`.
This is *not* a 342×224 wide-world screenshot and has no substituted
`+43` horizontal crop.

## First real original/native pixel finding

Snes9x reports `RGB565` for the original framebuffer; its
`snesref::maybe_dump_frame` expands **6-bit green** as
`G8=(G6<<2)|(G6>>4)`, while red/blue are expanded from
5-bit channels. Baldosa native's source PPU expands all
**5-bit SNES channels** to 8-bit with
`(c5<<3)|(c5>>2)`. The different 8-bit green values
(e.g., original **166**, native **165**) are thus an expected
**source video-output format difference**, rather than necessarily a
game colour error. The strictly source-backed normalization
per original pixel is `G6 = original_G8 >> 2`,
`G5 = G6 >> 1`, then the native 5-bit expansion. Red
and blue source values are left untouched.

After this *one* justified channel-depth conversion, comparing
all 37 real original callbacks against native guest2208 yields one
unambiguous best frame: **original Snes9x callback 2207**
(its **one-based retro_run frame2208**).

| Observation | Source count |
| --- | ---: |
| Original/native equal 24-bit RGB pixels | **56,832 / 57,344 (99.1071%)** |
| Pixels different after format normalization | **512** |
| Different at original output row111 | **256/256** |
| Different at original output row113 | **256/256** |
| Pixels different on *all other rows* | **0** |
| Second-best of other 36 authentic original frames | **34,613** matches |

The actual original image renders **black split rows111 and112**.
The actual native image renders **black split rows112 and113**.
Every other RGB pixel, including both racer silhouettes and the
foreground/background scene, is identical at these unscaled original
256×224 coordinates after the documented format conversion.
The image comparison therefore isolates the source display band
at the two-row split to a one-row output-Y displacement.

Crucially, the independent original Snes9x `go.ppuw.tsv`
shows **real HDMA writes** `$2100 INIDISP=$00` at original V111 and
`$2100=$0F` at V113. That is concrete source timing explaining the
*original emulator's* 2-line forced-black interval. Native
`$2100` channel register-write timing and its final row mapping
must now be captured independently before altering
`snes_beam_frame_driver_draw_ppu_frame` or the compositor.

## Reproducible strict offline source acceptance

`tools/qa08_accept_original_native_split_seam.py` consumes **only the
two exact run-artifact ZIPs**. It re-verifies their exact whole-file SHA,
original live opcode/ROM/route/WRAM/37-frame receipt, original GO
video `RGB565` pixel format, native exact P7 image SHA,
each of 37 original frame SHA-256 values, source RGB565 bit expansion,
unique candidate nearest match, every output RGB pixel and the
original `$2100 INIDISP` transfer witnesses. A forged/changed source
fails closed rather than being silently re-registered.

```sh
python3 -m unittest tests.unit.test_qa08_accept_original_native_split_seam
python3 tools/qa08_accept_original_native_split_seam.py \
  --original-zip /path/to/qa08-original-window-accepted.zip \
  --native-zip /path/to/qa08-native-colour-2208.zip \
  --out /tmp/qa08-original-native-split-rgb5.json
```

**Acceptance boundary:** this is extremely strong original/native
*finished framebuffer* agreement at a single source-dimension
frame pair after explicit pixel-format equivalence. It does not
yet independently establish identical full 2P WRAM/controller
simulation history, physical SNES HBlank/OAM accuracy, every other
frame, native split $2100 source-clock attribution, or 342-wide
world presentation parity. Do not simply move all native PPU lines
or alter HDMA timing across other games based on one seam.
Preserve 256×224, 7:6 display PAR, 4× Original fallback and
real wider-world architecture; current procedural HD art remains
aesthetically vetoed.

**Next source experiment:** observe native `$2100` HDMA at the
source scanline-112 boundary, with actual table source, live PPU
`INIDISP`, render row and exact original 2P guest2208 source
frame SHA. Then apply a minimal guarded source fix only if
same input/PPU owner evidence demonstrates causality and rerun
the exact real original/native per-pixel oracle.
