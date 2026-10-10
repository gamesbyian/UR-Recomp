# QA-08: rear-only native Original PPU counterfactual

The existing pinned native 342×224 source and front-only/paired-removal
experiments cover real 2P OAM slots 96–99. They cannot completely
disambiguate a same-colour overlap: removing the front may leave
exactly the same rear colour, and removing both can prove only a
**pair-level** contribution.

The next independent native run should use the already-implemented
single-slot, one-frame PPU diagnostic to remove ONLY rear slot **99**
at guest frame **1856** (and subsequently slot 97 / frame 1872).
It must capture the unmodified stock, independently read-only slot
source, and rear-removed final native PPU raster with complete guest
CRC equality and unique PPU removal marker.

`tools/check_baldosa_wide_rear_removal.py` is the paired experiment's
companion oracle. It requires three separately observed complete guest
CRC streams and compares every full native 342×224 RGBA pixel.
Changes outside the rear slot's emitted-alpha footprint or invalid
frame/slot identity fail closed. Unlike the *front* change-positive
assessor, **zero final-colour changes are a legitimate observational
result** for a rear sprite that might be hidden or same-colour-overlaid.

That zero-change result **never proves full occlusion, a particular
winner, that replacing the slot is safe, or authored HD admission**.
Reports always set `winner_identity_proven=false` and
`release_hd_admission=false`. Direct CLI invocation without
`PYTHONPATH` has a regression test, after the earlier paired-script
import failure.

This tool adds no native route or graphics-mode option. It is ready
for a separately authorized guest-frame witness once the currently
running paired 98/99 experiment is accepted.

## Real native rear-99 execution candidate

The same existing pinned Baldosa AOT job now runs the actual original
2P guest route independently with **only OAM slot 99** removed by the
one-frame native PPU counterfactual at guest frame **1856**. It checks
the complete stock/rear-source/rear-removed guest CRC streams, a unique
native slot-99 deletion marker, exact stock and source PPU rasters, and
every affected pixel in the final native 342×224 image. The result,
native log and full image are retained in the existing CI artifact.

A zero-change result would be **valid evidence that deleting the rear
changed no output colours in this exact frame**, rather than grounds
for claiming all rear pixels are occluded or safe for authored HD
replacement. A nonzero final change must remain entirely inside the
authentic slot-99 emitted source footprint. Either outcome must be
correlated with independently verified front-only and paired
deletions before inferring relative priority.

The native run is not yet accepted, and no guest graphics or source
priority in production is altered by this experiment.
