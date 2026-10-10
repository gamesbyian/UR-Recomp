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

## Real native rear-99 execution: accepted bounded observation

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

The dedicated AOT native run **38081157287** (artifact **11679874808**),
merged through #1204, completed successfully. The full 2,473-frame
stock/rear-source/rear-removed guest CRC streams are identical.
Independent native reports establish:

- Slot-99 emitted Original PPU pixels: **319**. Rear-only deletion
  changed **162** final-colour pixels, all **top** band, **0** outside
  the rear source and **0** in the bottom viewport.
- Slot-98/front source **321**, source union **483**, source overlap
  **157**. Front deletion changed **307** pixels, rear deletion
  **162**, paired deletion **483**, with **0** nonlocal violations.
- Exactly **14** identical-RGB front/rear overlap pixels are unchanged
  by either single deletion yet change after both deletions. This is
  direct pair-level redundant-colour causality.
- Native stock PPU raster SHA256:
  `0e956fac212cb7413a32ee2a0de318540e58cfd5f2b7610472c2573ab6719dd9`.
  Independently removed rear raster SHA256:
  `a98bed9a8041161e06e3bfb4dde43411f533cdf7c5a7f87e365e557e18267813`.
  Rear emitted source SHA256:
  `658b214071df7637abc308a0222e37cb15753b72c4ef42cf4c084311c031ec8f`.

The full report names are
`baldosa-evidence/ws342_rear99_removal_1856.json` and
`baldosa-evidence/ws342_six_plane_causal_1856.json`.
This confirms **bounded original final-colour influence**, including
real rear visibility. It still does **not** prove unique ownership
of the 14 same-colour overlap pixels, BG/window ordering, automatic
HD replacement safety or a player-ready 4K Remastered presentation.
No guest graphics or source priority in production was altered.
