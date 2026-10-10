# QA-08: later moving 2P Original native visual review

**Status: accepted bounded native post-GO Original-world observation.** Merged
#1211; native AOT run `38083974528`, artifact `11681865494` includes
`ws342_late_original_world.json` and the unmodified source PAM frame 2208.
It does not certify all-scene gameplay/HUD parity, source visibility for HD,
or authored widescreen Remastered presentation.

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

## Actual frame 2208 visual and data finding

The independent native run reached its scripted **GO** checkpoint at guest
frame **1989** and saved genuine 342×224 split-screen racing source pixels
at host-presented guest frame **2208**. This is 219 guest frames later, with
both riders, a green/blue live track, a running **0:03:6** HUD and no large
countdown overlay in the actual retained image. Compared against original
frame 1888, **53,360/76,608** logical output pixels changed; all four
new-world bands were nontrivial (top left **973**, top right **758**, bottom
left **1,842**, bottom right **2,883** detected margin differences). The
late native RGBA SHA256 is
`f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a`.
Full independent guest CRC parity remains **2,473/2,473**. The frame is
still **Original fallback at logical 342×224**, not evidence that authored
racer art appears on a 4K physical display. This distinction matters for
recruitment footage, beta decisions and new Remastered pose priorities.

## Next visual QA

After accepting this bounded native run, compare early and later 1P,
ordinary-2P and VS screenshots at 1×, 4× and physical 3840×2160 as
appropriate. Audit P1/P2 silhouette/occlusion, HUD alignment, road
extension and camera continuity, and contrast authored high-resolution
coverage against Original fallback. Do not desaturate, invent or redraw
sprites to conceal provenance gaps. No guest gameplay change.
