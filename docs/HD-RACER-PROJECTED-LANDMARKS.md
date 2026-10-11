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


## Source-grounded 1P silhouette identity observation (original PPU)

As a complementary **pixel-exact sprite observation**, use
`tools/export_native_racer_obj_source_reference.py` to obtain lossless
source silhouettes and original alpha row/column profiles, then compare the
two independently isolated PPU planes with:

```sh
python3 tools/art/compare_native_1p_silhouettes.py \
  --source98 path/to/baldosa-ws342-live-1p-slot98/ur-baldosa-ws342-obj-slot98-frame002208.pam \
  --source99 path/to/baldosa-ws342-live-1p-slot99/ur-baldosa-ws342-obj-slot99-frame002208.pam \
  --validated-report path/to/baldosa-evidence/ws342_live_1p_top_slot98_99_source.json \
  --out path/to/source-alpha-comparison.json
```

The recovered genuine five-process native AOT evidence
[`38097914195`](https://github.com/gamesbyian/UR-Recomp/actions/runs/38097914195),
artifact `11686843233`, produces the committed numerical digest
[`qa08-live-1p-source-alpha-alignment-2208.json`](../analysis/data/qa08-live-1p-source-alpha-alignment-2208.json).
It proves a narrowly useful thing for character reconstruction: in one
original one-player post-GO source image, the two 98/99 PPU alpha silhouettes
have **16 consecutive identical nonempty raster rows, y128 through143,
after an explicit left-edge X translation**. Their upper-source rows do not
share this exact profile, and their original whole-source bounding boxes
differ: slot98 `[101,121,132,143]` (285 pixels) versus slot99
`[36,120,71,143]` (293 pixels). This is excellent repeatable control
for preserving the source's shared lower silhouette geometry when
rebuilding a canonical articulated model. It **does not** identify that
lower area anatomically as a specific mesh, establish the 1994 3D geometry
or prove either source pixel owns the final PPU output. Distinct RGB values
and possible palette identity changes do not affect the binary alpha
comparison.

The 16-row measurement is genuine ROM-era sprite-image geometry, not a
validated wheel diameter or saddle width/height. Do not mix its bbox
normalization with manually marked artist/packaging landmarks as though
the cameras and perspectives match. Both original source planes and their
native validation logs remain in the referenced external artifact; the
committed JSON retains only numeric measurements and hashes, no proprietary
ROM-derived sprite image bytes. The experiment **does not** approve the
old procedural character, any new 4× geometry or Widescreen replacement.


## Native cross-pose 2P racer palette census

Separately recovered **authentic original PPU** 2P source slot98/99 at
native guest frames1856,1872,1888 (accepted AOT
[`38115756178`](https://github.com/gamesbyian/UR-Recomp/actions/runs/38115756178),
artifact `11693865103`) offers a small invariant for future **single-rig
with colour-variant** reconstruction. Every source alpha pixel's
original RGB was counted and validated against the independent native
source hashes. Six RGB colours recur in **both** racer source palettes
over **all three** different poses: `101008,181818,313131,4A4A4A,737373,A5A5A5`.
Each racer also retains eight pose-stable, mutually exclusive colour
variants, a warm red/rust group on slot98 and a green group on slot99.
A ninth shared light colour `F7EFEF` appears in the first two poses
and disappears from both at frame1888; the two racer palettes therefore
have 15 unique colours in each first two frames and 14 at1888.

The complete source SHA/racer-colour evidence is preserved in
[`analysis/data/qa08-original-2p-racer-cross-pose-palette-1856-1888.json`](../analysis/data/qa08-original-2p-racer-cross-pose-palette-1856-1888.json).
The material resemblance suggests a **constraint for later variant
testing**, not an established per-wheel/per-saddle material assignment:
sprite colours alone cannot identify the actual 3D mesh/rig part, all
original PPU priority layers, lighting math or a safe replacement
palette. The owner-disapproved procedural HD shapes stay vetoed.
Preserve the original palette families as a reviewer reference, not a
new default shader or shipping art authority.


## Six real moving 2P source envelopes: constant bottom scanline

The same already retained native 2P source artifact, with independent
slot98/99 PPU source planes at moving guest1856,1872,1888, yields a
useful **projected bottom-of-silhouette registration constraint**:
both source riders end precisely at **absolute original top-raster
y=78** in all six captures, and their separately verified copies in
split lower OAM slots97/96 end at **y=191**, exactly +113 rows below.
During the three frames their original source silhouettes change
markedly, across **18–23 source pixels width, 35–37 pixels height**,
and 319–330 opaque source pixels, while their upper silhouette begins
at y42–44. The project can use this sampled invariant to *test*
proposed image registration and vertical pose anchoring instead of
assuming a rigid top-edge/middle-of-bbox offset.

The source-hash-anchored six-frame numeric measurement is in
[`analysis/data/qa08-original-2p-three-pose-projected-source-envelope.json`](../analysis/data/qa08-original-2p-three-pose-projected-source-envelope.json).
**The lowest visible sprite pixel is not automatically the physics
ground-contact point, wheel hub, collision pivot or original 3D
model origin.** Confirm actual guest/world collision anchors
separately before assigning that name to raster y78/191. Likewise,
the exact repeated OAM-viewport shift is screen-source copying, not
a claim about 3D camera geometry. Observe the established **7:6
pixel-aspect correction** when comparing these raw source-pixel
envelopes against any artist or Blender render. No artistic approval
is granted by the geometric measurement.


## Real 2P alpha-shape changes across those same three source frames

Bounding-box dimensions alone hide important animation differences.
Re-examining the six independently authenticated PPU source RGBA
planes as **binary alpha**, first translate each source bbox's
leftmost opaque X to `x=0` while retaining its **original Y**,
including the sampled fixed bottom row `y=78`.
This is an explicit source-space registration, not 3D retargeting.
The resulting original source-mask Jaccard intersections/unions are:

| Moving native source | 1856→1872 | 1872→1888 | 1856→1888 |
| --- | ---: | ---: | ---: |
| Original upper OAM slot98 | 186/460 = **0.404** | 252/397 = **0.635** | 222/423 = **0.525** |
| Original upper OAM slot99 | 208/441 = **0.472** | 288/364 = **0.791** | 183/458 = **0.400** |

Even with the same projected bottom boundary, genuine rider pose
silhouettes are not merely translated copies across time.
A proposed rig-generated replacement pose sequence should be able
to preserve comparable expressive source-space shape variation at
normal gameplay viewing sizes, not just hold an immobile detailed
unicycle above an animated colour field. These numbers are an
**archaeological comparison reference**, not a target optimization
loss, hard-coded playback transform, automatically approved 3D pose
or proof of wheel-contact geometry. They are distinct from the
**exact +113 Y split-viewport duplication within each frame**.

Numerators, denominators, explicit bbox-left registration and
all original slot/frame SHA identities are preserved in
[`analysis/data/qa08-original-2p-three-pose-anchored-alpha-jaccard.json`](../analysis/data/qa08-original-2p-three-pose-anchored-alpha-jaccard.json).
No copyrighted sprite imagery is included. Original character
likeness still requires a separate explicit artistic review.


## Native 2P moving camera/screen-source registration is phase-dependent

For any eventual **single 3D character rig** with original-derived
2P projections, distinguish *pose identity* from *viewport
screen-space transformation*. The exact native original source
captures at guest1856,1872,1888 each contain
**byte-matching upper/lower RGBA silhouettes** for rider pairs
slot98→97 and slot99→96 at source raster shift
`(dx=0,dy=+113)`. At authenticated **post-GO
guest2208**, both rider pairs remain exact source-RGBA copies
(317+313 occupied pixels, **zero alpha/colour disagreement**),
but the registered transform is **`(dx=-13,dy=+112)`**.
That is a genuine difference in the original's sampled
source viewport placement, not a reason to distort the model,
re-author the lower rider pose or use a global static offset.

The post-GO source AOT [38120828291](https://github.com/gamesbyian/UR-Recomp/actions/runs/38120828291)
(artifact `11695173178`) independently checked four OAM
slots, seven identical whole Original PPU captures and guest
CRC parity, using unmodified ROM gameplay; cross-phase
per-source pixel and original-stock SHA counts are retained
in [`analysis/data/qa08-original-2p-source-registration-phase-matrix-1856-2208.json`](../analysis/data/qa08-original-2p-source-registration-phase-matrix-1856-2208.json)
on graphics [PR #1342](https://github.com/gamesbyian/UR-Recomp/pull/1342).
This evidence is currently **sampled across two phase regions
only**. It does not establish the exact transition frame,
WRAM camera instruction, generalized source pose transform,
real 3D model origin, ground contact or replacement HD
paint coordinates. Actual HD capture/animation must receive
appropriate authentic dynamic screen projection and PPU
foreground ordering; neither a hard-coded +113Y nor a
hard-coded −13X is a sufficient multi-frame solution.
The current owner-vetoed procedural 4× character remains
unapproved.


## Real post-GO original racer palette stability

The accepted 2P source-only AOT at guest2208 establishes that
the original sprite colour families persist after the countdown,
even though the source silhouette, OAM position and two-viewport
translation change. Independently verifying the **actual occupied
original PPU source RGBA** shows both racers have 15 distinct
source colours at guest1856,1872 and **2208**, with 14 at1888
when the same light `F7EFEF` shade is absent in both.
No previously unseen RGB value appears at2208, versus the
authenticated earlier source palette union.

Across **all four** sampled 2P source poses, the six shared
neutral colours remain `101008,181818,313131,4A4A4A,737373,A5A5A5`.
Each rider also retains its own eight-colour variant palette:
a rust/red ramp for OAM slot98 and green ramp for slot99;
the ninth variable shared light shade `F7EFEF` is present
at1856,1872 and2208 and absent at1888. This makes the
original palette-family relationship a **well-sampled
material-variant reference** for future author experiments,
not a requirement to copy each RGB value literally as a
physically based 3D material.

The complete native source SHA/palette census is in
[`analysis/data/qa08-original-2p-racer-palette-four-poses-through2208.json`](../analysis/data/qa08-original-2p-racer-palette-four-poses-through2208.json)
using exact successful AOT [38120828291](https://github.com/gamesbyian/UR-Recomp/actions/runs/38120828291),
artifact `11695173178`. Palette invariance cannot recover
which raster pixels correspond to tire, saddle, fork, hub,
lighting or original model mesh; source RGB is also earlier
than final BG/window priority. No currently rejected
procedural Remastered art receives renewed approval.
