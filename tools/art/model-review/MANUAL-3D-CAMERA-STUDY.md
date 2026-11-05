# Three-dimensional model viewing from original manual-inspired angles

Existing source-authored five-parent/16-material Pages reviewer only.
The new optional Print fork (official 1994 manual p14) and Print hub
(manual p15) controls rotate the unchanged *2026 unapproved GLB camera*.
They DO NOT reproduce or recover the original historical 3D artist's
camera, focal length, part geometry, materials or render lighting.

Print fork approaches a near-frontal upper fork/crown view with a small
elevation. Print hub views the wheel/hub/crank and saddle underside from
a three-quarter lower-than-wheel-axis orbit. Both directions are manually
chosen inspection presets rather than landmark-calibrated camera fits.
Their positioning is independent of the original-game 24-tick raster rail,
root physics, source OAM state and model pose. Camera reset is available;
all original five canonical camera presets remain supported.

Reference source: already retained printed 1994 USA manual page figures,
with SHA-bound offline crop pipeline introduced in #3166. Any claim of a
source-consistent 3D physical model requires independently annotated
crop landmarks, an appropriate full 3D model and separate owner visual
review. The viewport should remain useful even when printed figures
cannot be automatically displayed or source crop extraction is absent.

The predeclared direction vectors are embedded in the small
manual_view_directions.mjs helper and validated in Node. Full existing
browser smoke checks verify 44px touch targets and original source
reference data never changes when these camera views are selected.
No original ROM, game presentation, asset exporter, new GLB or Windows
release acceptance is changed.
