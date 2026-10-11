# Racer character likeness: reference-bound projected landmark study

**Status: reproducible offline measurement protocol, not validated original
reference measurements, completed character reconstruction, new art or release
approval.** Owner visual veto and review rubric live in
[HD-RACER-CHARACTER-RECONSTRUCTION.md](HD-RACER-CHARACTER-RECONSTRUCTION.md).

## Why this exists

The existing 4× procedural rider can match a 32-pixel pose footprint while
missing the personality and 3D mass of the original pre-rendered character.
Before rebuilding a model/rig, measure the **projected** saddle width and
height, wheel outline, crown/fork spread and crank/pedal offset against
**individually authenticated** original imagery. Keep a named viewpoint and
pose for every single numeric measurement. A book-cover wheel foreshortened
toward the camera is not a canonically short wheel in the original model.

Run the stdlib-only offline validator:

```sh
python3 tools/art/measure_unicycle_reference.py /private/uniracer-review/landmarks.json \
  --out /private/uniracer-review/projected-measures.json
python3 -m unittest tests.unit.test_measure_unicycle_reference
```

No emulator, Blender, network, GPU, AI weights, new CI or shipping asset
dependency is required. It reuses `tools/art/validate_upscale_trials.py` for
exact PNG SHA-256 provenance and safe local manifest file paths. **Keep original
scans and screenshots in a private working directory.** The report emits
measurement ratios, image hashes, source URLs and annotated point coordinates
but never embeds/redistributes copyrighted source pixels.

## Manifest contract

Top-level `schema` must be `UR-RACER-LIKENESS-LANDMARKS/1`; `views`
is a nonempty array of unique IDs. Every view requires:

- `image: {path, sha256}`, where path is relative to the manifest and hash
  identifies the **exact unaltered local PNG** being annotated. Re-extract
  landmarks if the source scan, crop or image content changes.
- `source: {url, kind, creator_or_credit, region_or_version,
  capture_context, rights_notes}`. URL is HTTPS; `kind` is
  `original-title`, `original-gameplay`, `official-packaging`,
  `period-promotional`, or `artist-blockout`. Name the specific
  title/intro frame, OAM/PPU frame, physical box/front scan or promotional
  asset, not just a game title. An artist-blockout input is **a proposal**.
- `view: {angle, pose, pixel_aspect, crop_and_rescale_history}`.
  Angles are `side`, `front`, `three-quarter` or `unknown`.
  Pixel aspect `square` applies to undistorted scans/renderings;
  `snes_7_6` applies to raw logical SNES source pixel coordinates.
  Never mark an unknown crop/perspective as a neutral orthographic view.
- `annotator` and `landmarks`: `wheel_left`, `wheel_right`,
  `wheel_top`, `wheel_bottom`, `saddle_left`, `saddle_right`,
  `saddle_top`, `saddle_bottom` are **required two-element [x,y] pixel
  coordinates**, each inside the real PNG. Mark extremes of the same
  coherent silhouette, not approximate material highlights or tire shine.
  Optional matched pairs `crown_left/right`, `fork_left/right` and points
  `axle`, `pedal_center` add other ratios. When a feature is hidden,
  omit its point(s) and give a reason in `unmeasurable`, e.g.
  `{"fork":"obscured by wheel"}`, `{"pedal":"behind fork"}`. All four
  optional feature families must be either marked or explained.

The schema is deliberately point-based rather than inventing pose-to-3D
fitting. Wheel **vertical diameter** is the normalizer for every measured
ratio. Horizontal distances are corrected by the **declared** pixel aspect,
and positive Y is image-down. All values are projected 2D image ratios and
may be invalid for cross-view comparison without fitting a camera.
A measured wheel ellipse could be due to view angle or lens distortion,
not a different physical wheel.

## Sources and comparison policy

The authentic visual-identity plan already links the Nintendo Life developer
interview, region-specific box/manual gallery and original title captures.
The DMA Design archival press-material listing at
https://hiddenpalace.org/Assets/DMA_Design_Miscellaneous_Press_Material
**lists Uniracers/Unirally among represented games** and is already in
`reference/catalog.yml`; the actual unicycle renders, quality, image origin,
reuse rights and relation to the original CG files **remain uninspected**.
Do not mark the archive as verified Martin Good model evidence merely because
Uniracers is in the listing.

The North American and European cover images can reproduce the **same key
illustration** with alternate regional lettering/crops. Such variants do
not count as independent proof of repeated original-model proportions.
Record a `region_or_version` and `crop_and_rescale_history` for each.
Nor does 2010 retrospective article artwork automatically prove its images
were rendered by the original 1994 in-game CG artist. Developer testimony
and physical-art inspection answer different questions.

First measurement campaign should use (a) one actual original cover image,
(b) a genuinely independent large-scale title/menu/promo depiction if
authentic, (c) two adjacent native-source PPU gameplay frames from one
motion family, and (d) the old 4× baseline as an **artist-blockout** control.
Where source geometry is not measurable, report absence instead of filling
it with plausible-looking values. Contact sheet must retain image copyright,
origin, version, perspective and exact hash. Compare like-for-like
silhouettes at real split-screen and normal gameplay size, not only at
400% zoom.

**Shipping disposition:** This script always reports
`three_dimensional_character_proportions_proven=false`,
`current_character_likeness_approved=false` and
`shipping_art_approved=false`, even when every numeric landmark fits.
Human review after a coherent multiview canonical rig and game-scale
two-pose sequence remains mandatory. Historic
`analysis/data/racer-hd-art-approval*.json` hashes are preserved as
prior technical evidence; they do not override the current art veto.
