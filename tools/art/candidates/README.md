# Shared-rig high-detail racer blockout (NOT APPROVED)

This is **one coherent unicycle model**, with five pose configurations, introduced for reconstruction review without touching the production 4× presenter or the shipping Windows guest. OpenSCAD is an optional *offline art authoring tool*; this source is not compiled or interpreted in a game build. No binary reference image, protected source ROM or model weights are in this branch.

**Visual provenance, not proof of 3D ground truth:** Original Uniracers title frame 400, an authentic 256×224 original PPU source snapshot in independently pinned native AOT artifact **11863045863** (archive SHA256 `6fb7e9ad5ce53e02f0dda0896f520e2a667f5798c58f8d65b5541ed2d53a5431`), and unchanged 2P gameplay frames 1856 and 2208 from the same archive. The title reference contains two overlapping unicycles under a genuine dark title-fade; for visual inspection only, a brighter 3.5× *display preview* was used, explicitly **never** as source pixel evidence. The previous procedural 4× rider from `baldosa-hd-captures-4x/ur-baldosa-frame-001856.pam` serves as the owner's rejected technical baseline. The title-source proportion estimates are tentative because this is a composite, angled title scene. The exact current 7:6 stock gameplay PAR and all output-geometry policies remain independent.

**Rig interpretation:** Each pose derives from one shared tire, wheel, spokes/hub, fork, pedal assembly and a curved saddle. Wheel/tire and rounded mass are intentionally treated as consistent 3D geometry; the five prototypes differ only by rig rotation, pedal crank phase and saddle lean. The saddle uses connected loft sections to represent the broad raised tail, dipped center and curled nose seen in the high-detail title, instead of unrelated per-pose 2D polygon drawings. Color and proportions are early design parameters, **not source-measured final values**. Do not treat OpenSCAD's default camera, test lighting or visible silhouette at 480px as a source-exact camera calibration.

## Reproducible fixed-camera artwork review

The authentic P7 source columns are resampled for display at original **7:6 horizontal PAR** using nearest-neighbour; authored HD rig columns remain modern square-pixel. Neither transform affects archived source hashes, and neither claims physical 4K acceptance.

The first rough render used OpenSCAD `--viewall --autocenter` separately for
each pose. This is **not** adequate for a multi-pose shape comparison: it can
change the camera fit and make character geometry appear more consistent than
it is. The review tool now locks *two* named orthographic cameras across
**all five transforms**. It also produces literal 64px and 32px thumbnails,
rather than judging the result solely at a large rendering size.

Install optional **OpenSCAD 2021.01+** and Python **Pillow** locally, then run:

```sh
# Source-only review without copyrighted reference material:
python tools/art/render_shared_unicycle_review.py \
  --out /tmp/ur-five-pose

# For the genuine independent original/stock/old-art comparison, supply
# already downloaded GitHub artifact 11863045863 (original ZIP SHA256
# 6fb7e9ad5ce53e02f0dda0896f520e2a667f5798c58f8d65b5541ed2d53a5431).
python tools/art/render_shared_unicycle_review.py \
  --authentic-source-zip /secure/local/baldosa-native-spike-evidence.zip \
  --out /tmp/ur-five-pose-with-authentic-reference

# Under headless Linux, append --xvfb (runs OpenSCAD via xvfb-run -a).
```

Each output directory must be absent or empty: stale test frames cannot be
silently admitted. Both fixed-camera sets and the contact sheet are hashed
into `review-receipt.json`, alongside model source identity and explicit
**negative** Original RGB5/source-likeness/shipping/QA claims. Inputs are
authenticated against the full original AOT SHA and three distinct P7
member hashes before any display-only title-frame brightness change; the
3.5× brightness enhancement is **only for the title fade preview**. This
is not a PPU comparison nor a scheme for inferring a camera from raster
pixels.

The initial arbitrary-ground-pivot stunt transform dropped the wheel
partly outside the fixed-camera view. It now rotates the **same whole
unicycle around a 3D character-centre pivot** at z=1.80 for review; do
not infer this artist pivot matches any authentic physics/stunt location.
Next acceptance work is still reference-landmark annotation and pose-to-
stock contact registration, followed by real source-visible live 1P/2P
capture and owner aesthetic review. In particular a 32px thumbnail is
only an *evaluation*, never a source-matched 32px animation frame.

## Continuous pose coherence and clipping review (18 October)

The same canonical `shared_rig` now supports two further **non-shipping,
normalized-time** animation states, `ride` (two full crank rotations) and
`stunt_cycle` (one eased 360° midair rotation around a provisional
character-centre pivot). Static `upright/pedal/wheelie/stunt/bank` choices
remain intact. The geometry, palette and rider identity are exactly the
same object; only the transforms vary. This is a *kinematic blockout*, not
reverse-engineered original stunt timing, track contact, wheel physics or
SNES-derived animation.

Use the new fail-closed authoring tool to inspect the entire temporal
trajectory, rather than five hand-picked attractive stills:

```sh
# Needs OpenSCAD and Pillow. On headless Linux add --xvfb.
python tools/art/render_shared_unicycle_motion.py \
  --model tools/art/candidates/unicycle_shared_rig.scad \
  --out /tmp/ur-single-rig-motion --xvfb

# Manual mid-cycle pose: one shared rig at exactly t=0.375.
openscad -o /tmp/ur-stunt-mid.png --imgsize=320,320 \
  --projection=o --colorscheme=Tomorrow \
  --camera=0,0,1.6,90,0,0,12.5 \
  -D 'rig_pose="stunt_cycle"' -D 'rig_time=0.375' \
  tools/art/candidates/unicycle_shared_rig.scad
```

The tool uses **one unchanged side-view camera** for all 18 samples (nine
ride + nine stunt) and enforces **pixel-identical first/last rendered frames for each cycle**, then writes `continuous-motion-review-receipt.json`
with per-image SHA-256, silhouette bounding boxes, rig identity and
explicit negative approval/Original-source claims. It aborts if any
silhouette reaches within four pixels of a window edge, if a frame is
missing/blank or if stale output is present. The initially used
static-study camera distance of 11 **really cropped** the interpolated
stunt at normalized `t=0.125`; moving the **entire motion study** to
distance 12.5 restored a minimum visible edge margin of 18px at the
sampled times without per-pose zoom. The study's camera is only a
review instrument, not an original-game camera assumption. A separate
17-step-per-mode local preview confirmed 34/34 uncropped frames, including
start/end restoration at both motion endpoints. The review source lives
under `tools/art` and never modifies the game, saves, upstream renderer
or acceptance ledger. Actual artist sign-off remains blocked as below.

**Review is presently BLOCKED.** Before baking any 256×256 candidate into the existing `native/presentation/racer_hd_presenter.hpp` or enabling new 1P/2P substitution, obtain source-hashed original-title/period-art landmark annotations, review a consistent **side and three-quarter** model across adjacent authentic poses, retarget pivot/contact/7:6 source registration, compare at real race and split-screen scale, and obtain **new explicit owner visual approval**. Earlier `shipping_art_approved` technical hashes do not authorize this candidate. Never promise parity from the five static previews. The finished media and 4K display acceptance are distinct gates, left to the independent QA owner.

**No runtime or shipping changes in this branch:** authentic Original and the existing fail-closed Remastered fallback remain exactly as before. This blockout should be rejected, changed or deleted if detailed reference comparisons show a proportion or personality mismatch. It is a reviewable single-rig input for an actual artist, not an automatic replacement for approved work.
