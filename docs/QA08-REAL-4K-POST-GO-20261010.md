# QA-08: real SDL 3840×2160 output during post-GO racing

**Status: accepted bounded Original-mode native 4K visual QA.** Merged #1221,
AOT run `38085717011`, artifact `11682517633` (original unmodified
source/density/full SDL PAM captures and exact-pixel reports). All exact-head
CI workflows passed. **This does not accept 342-wide authored Remastered
racers, physical hardware scan-out or integrated Windows beta.**

## The visible product question

Merged #1191 and earlier wide captures prove native *physical* 4K SDL
output for a centred fixed-width Original frame and a 342-column
pre-GO screenshot (frame 1856). Merged #1211 proves genuine split-screen
widescreen Original racing **after GO** at frame 2208. These must also
be seen together at the **real** 3840×2160 drawable. A 1368×896
fourfold texture or a synthetic resampling of a screenshot cannot prove
this, and neither does a physics/guest checksum.

## Reuse with no extra guest run

\`tools/baldosa_sdl_physical_4k_capture_spike.py\` already instruments
the pinned disposable SDL2 host *immediately before SDL_RenderPresent*
with genuine \`SDL_RenderReadPixels\` on the complete drawable. This
candidate adds an opt-in **second frame/file pair** to the same callback:
the existing 1856 reference is preserved unchanged, while an independent
post-GO physical capture at **2208** uses the exact same 2,473-frame
scripted 2P guest process, 4x nearest Original compositor, world
materializer, 7:6 PAR and real 3840×2160 software SDL display.

The existing fixed-width 256×224 Original source guest process also
retains a third exact read-only 1× source image at frame 2208 (alongside
400 and 1856), using the existing source capture callback. The strict
`check_baldosa_original_center_parity.py` compares **every one of the
57,344 RGBA stock-centre pixels** against the post-GO 342-column frame
and reports top/bottom HUD and rider differences honestly. That closes
the countdown-only source-centre QA gap if the candidate passes, without
adding a third execution of the source game.

The pre-existing independently executed native 342×224 1x source
capture at 2208 comes from merged #1211. This branch extends the
*already required* separate 1368×896 4x source route with one bounded
read-only late PAM at the same guest frame. The strict pre-existing
\`check_baldosa_wide_density_parity.py\` must accept the extra matching
pair without dropping any of the original early six. The real 4K
output route continues to execute **once** (not twice); only its
in-memory SDL readback is repeated once when the extra frame occurs.

Exactly matching opt-in frame+file controls suppress the incidental
turbo/FPS OSD for either diagnostic capture only, leaving title-native
HUD untouched. Malformed, absent and out-of-range controls remain
inert; the normal renderer and all guest/PPU/ROM/input/SRAM activity
are unchanged.

## Actual independently captured post-GO result

Native guest frame **2208** occurred after the scripted 2P GO checkpoint
at 1989. The original source was independently captured as **342×224**,
the native renderer's fourfold Original density as **1368×896**, and
the completed SDL2 framebuffer readback as **3840×2160**. The real
SDL output full-frame pixel comparison passed for all **8,294,400**
output pixels against the independently authenticated source plus SDL2
16.16 nearest-sampling mapping. The same AOT process retained the
accepted frame-1856 4K pre-GO witness and fixed 256-wide, side-matted
frame-400 Original witness.

Independent fixed-Original guest versus widened-Original guest at frame
**2208** also demonstrated **0/57,344** changed centre RGBA pixels:
**0** top-band P1/HUD differences and **0** bottom-band P2/HUD differences.
All full guest CRC sequences remained **2,473/2,473 identical** across
their respective source/control runs, without editing guest state.

Accepted read-only SHA256 witnesses:

| Source | SHA256 |
| --- | --- |
| Native logical 342×224 PPU, 2208 | `f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a` |
| Independent fixed 256×224 centre, 2208 | `6ecff0530c94a41419628866aebf7073f4cb80870cdfb149cb758f47b86abe1c` |
| Native Original 1368×896 density, 2208 | `776963ddc3c50f8824a0b026251aee5ae05296a841a135c1ff55eff119cec108` |
| Actual 3840×2160 SDL drawable, 2208 | `29f6ef1f9b5965d32818228182922e337a0570433b5929c89e285af2969a0fac` |

The recovered widened centre SHA equals the independent fixed source
SHA exactly. The drawable hash represents **real renderer output**, not
a generated upscale. Full image source/CRC provenance is in
`ws342_physical_4k_frame2208.json` and
`ws342_original_center_parity_2208.json` in the native artifact.

The actual image shows P1/P2 riders, original green/blue course strips,
a running race time/HUD and the full horizontal world without cropping
the split views. It still has the deliberately nearest-composed Original
raster and visibly cannot substitute for approved HD Remastered art.

## Exact oracle and limits

Run \`tools/check_baldosa_physical_4k_capture.py\` for both 1856 and
2208, requiring same-frame provenance, every 4×4 logical source block,
the pinned SDL2 16.16 nearest-sampling output mapping, 3840×2160 true
drawable pixels and correct 7:6/512:513 aspect behavior. A single
wrong physical RGBA byte is a negative, regardless of screenshots'
perceptual similarity. Each report retains independent raw source,
density and actual SDL output SHA256s.

Successful acceptance establishes **bounded post-GO physical
4K Original split-race pixels**, but not authored 342-wide HD riders,
Remastered gameplay, uninterrupted high-resolution art, hardware
display timings, all-course fidelity or a release-ready beta.

A real 4K post-GO screenshot can be shared with the media showcase
only with the exact pixel provenance. Keep ordinary release acceptance
independent from the diagnostic source readback.
