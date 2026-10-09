# QA-08: foreground depth and Original OBJ isolation witness

Status: **diagnostic candidate finder**, not a certified SNES BG/OBJ priority
compositor or a player-facing Remastered completion claim.

## The raster limitation

The Remastered presenter currently paints HD racers over an already
flattened Original framebuffer. The existing 4× pixel-confinement witness
proves the area *outside* actual racer bounding boxes is unchanged at
guest frame 1220. It says nothing about foreground BG tiles, other OBJ,
SNES window masks or subscreen/color-math pixels that should appear
**in front** of a racer *inside* those rectangles. The pinned
SNESRecomp `docs/HOST_OVERLAY_EXTRACTION.md` calls for a priority-aware
composition seam before host-placed graphics can preserve those depths.

## First native experiment: empty direct OBJ capture

Native workflow `37875602021`, artifact `11591573934` attempted
a single frame-1220 export of `g_obj_overlay` (PAM/P7) using the pinned
PPU's optional source-plane interface. The producer printed
`status=captured`, but byte inspection proved **all 57,344 alpha
pixels are zero**. Meanwhile the same native log recorded four valid
HD racer placements at frame 1220 (top OAM slots 98/99 at X=104,Y=40;
bottom 97/96 at X=104,Y=153) and full-pair render admission.

Therefore an all-transparent PAM is **not a valid Original sprite
reference**, and the attempted foreground comparison correctly failed.
It cannot establish either correct compositing or absence of sprite
occlusion. The export function now labels an all-empty plane
`status=empty` with `opaque_pixels=0` rather than claiming success.
The optional exporter remains for future PPU-layer debugging but is no
longer the acceptance witness.

## Independent stock OBJ-only raster

The pinned SNESRecomp also provides a non-mutating display debug mask:
`SNESRECOMP_LAYER_MASK=0x10` retains OBJ while masking BG1–BG4.
Run the **identical original two-player script, ROM and input** in a
fourth process with this setting, capturing its original 256×224 P6
screen at guest/present frame 1220. Original-A and Original-B controls
still run unchanged, and the normal HD process still renders its 4×
1024×896 screenshot at frame 1220.

The acceptance step now invokes:

```sh
python3 tools/check_racer_hd_foreground_occlusion.py \
  --original racer-original-a-1220.ppm \
  --original-control racer-original-b-1220.ppm \
  --hd racer-hd-1220.ppm \
  --obj-only-ppm racer-original-obj-only-1220.ppm \
  --native-log racer-hd.log --frame 1220 \
  --json-out racer-hd-foreground-1220.json
```

This gives a **conservative nonblack lower bound** on visible OBJ-only
pixels, not a fully alpha-correct PPU plane. Black may be either an
actual black OBJ pixel or the masked-out backdrop, so it is excluded.
The tool refuses a completely empty OBJ-only witness rather than
manufacturing a zero-overpaint success. It uses the four live OAM
placements, 256-line Y wrapping, 112-line split, full 1×–4× output
pixels and exact independent Original controls.

For nonblack OBJ pixels inside those OAM footprints, it counts:

- OBJ-only color matching Original display color, optionally changed by
  HD as expected for a replacement;
- OBJ-only color **different** from Original, an ambiguity that might
  reflect foreground BG, other OBJ, PPU window or color math;
- such ambiguous pixels **overpainted by HD**, yielding candidates for
  exact original-renderer depth investigation.

These candidates are not automatically confirmed priority defects.
Color math, palette setup and different host-present timing can also
produce mismatches; always align actual guest composition and account
for capture phase before making a causal claim.

## Direct native stock-removal test

A separate opt-in `UR_RACER_HD_CAPTURE_ONLY=1` host run arms exactly
the normal full-pair PPU `RemoveFromGame` path but returns the captured
stock framebuffer **without painting HD pixels**. This reveals whether
the PPU actually removed original racer pixels, rather than merely
allowing HD artwork to overpaint a still-present Original sprite.
`tools/check_racer_hd_pixel_confinement.py` compares that 4× screen
with two independently reproduced Original captures at frame 1220,
using the actual four racer OAM footprints. Acceptance requires
nonzero changed pixels in **both** original racer viewports, exactly
zero differences outside their combined bounding boxes, and an
authoritative 8-word guest composition match across all five routes
(Original A, Original B, HD, stock OBJ-only, and capture-only).

The capture-only option is diagnostic and inert unless explicitly
enabled. A failure here would identify an authentic mixed-resolution
raster fault requiring a renderer/PPU extraction fix, not permission
to expand art coverage or weaken the geometry guard.

## Acceptance and next engineering decision

The existing native graphics job now retains the OBJ-only PPM/log and
candidate JSON beside the two Original controls, HD frame and OAM
confinement evidence. It requires a nonempty layer witness and
structurally valid counts, **not zero ambiguous or suspect pixels**.
A successful 1220 static check is only the beginning; prioritize
motion where racers cross scenery, overlap each other, wrap around Y=255,
cross scanline 112 and move with the camera, in ordinary 2P, 1P, VS,
4:3 and 16:9.

Before accepting QA-08 L4, identify the source of any candidate through
original PPU main/subscreen and per-layer priority evidence, correct
the actual raster compositor and verify same-frame native Original/HD
pixel ordering across moving scenes. No debug capture here changes guest
physics, ROM state, input, frontend, persistence or ordinary player
graphics.
