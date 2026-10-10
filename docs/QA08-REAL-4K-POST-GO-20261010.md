# QA-08: real SDL 3840×2160 output during post-GO racing

**Status:** implementation candidate, not accepted. No source-capture report exists
from this branch until its exact native AOT job succeeds.

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

## Exact oracle and limits

Run \`tools/check_baldosa_physical_4k_capture.py\` for both 1856 and
2208, requiring same-frame provenance, every 4×4 logical source block,
the pinned SDL2 16.16 nearest-sampling output mapping, 3840×2160 true
drawable pixels and correct 7:6/512:513 aspect behavior. A single
wrong physical RGBA byte is a negative, regardless of screenshots'
perceptual similarity. Each report retains independent raw source,
density and actual SDL output SHA256s.

Successful native acceptance would establish **bounded post-GO physical
4K Original split-race pixels**, not authored 342-wide HD riders,
Remastered gameplay, uninterrupted high-resolution art, hardware
display timings, all-course fidelity or a release-ready beta.

A real 4K post-GO screenshot can be shared with the media showcase
only with the exact pixel provenance. Keep ordinary release acceptance
independent from the diagnostic source readback.
