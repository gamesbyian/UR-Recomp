# QA-08: later moving 2P Original native visual review

**Status:** candidate, no accepted native run at this branch. Built to expose
real racing imagery after the six already-approved early 342-wide captures,
not to certify gameplay, HUD alignment, split-screen, or authored widescreen HD.

## Why this observation is needed

The existing bounded native 2P 342×224 capture corpus at frames
1808/1824/1840/1856/1872/1888 proves moving source pixels and split-world
margin materialization, but the actual images include prominent original
start/countdown graphics. Those are useful Original source-validation
frames and insufficient by themselves for an honest visual assessment of
sustained racing quality. A post-early capture is necessary.

## Capture and guard contract

Reuses the **same** existing independent, 2,473-guest-frame
`race_2p_split_ur_ws342` invocation and source-world materializer. One
new diagnostic option `UR_BALDOSA_WS342_LATE_CAPTURE_AFTER=2200`
witnesses the first actual native presentation callback at or after
that threshold, between guest frames 2200 and 2450. Only one additional
PAM is captured per process; the first six and all stock/4× control
witnesses are preserved. When the option is absent or malformed,
no extra image is created. There is no guest WRAM/VRAM, SRAM, camera,
input, race-state or result change.

`tools/check_baldosa_late_original_world.py` requires a unique, exact
native late-present log marker, full RGBA PAM at the reported guest frame,
complete independent 2,473-frame guest CRC equality, all four active
split-world margins with nontrivial actual native pixel content, and a
changed full PPU raster compared with the last early native capture.
It retains SHA256s, raw source frame and changed pixel count. Synthetic
unit inputs only exercise negative controls.

A threshold alone cannot certify that a particular gameplay phase has
begun, that a rider animation is correct, or that the direction arrow
should be gone. **Human review of the retained actual native frame**
must classify start/countdown/actual riding and any HUD/track/racer
defects before beta-readiness credit is considered.

## Next visual QA

After accepting this bounded native run, compare early and later 1P,
ordinary-2P and VS screenshots at 1×, 4× and physical 3840×2160 as
appropriate. Audit P1/P2 silhouette/occlusion, HUD alignment, road
extension and camera continuity, and contrast authored high-resolution
coverage against Original fallback. Do not desaturate, invent or redraw
sprites to conceal provenance gaps. No guest gameplay change.
