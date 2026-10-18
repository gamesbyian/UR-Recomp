# Shared-rig high-detail racer blockout (NOT APPROVED)

This is **one coherent unicycle model**, with five pose configurations, introduced for reconstruction review without touching the production 4× presenter or the shipping Windows guest. OpenSCAD is an optional *offline art authoring tool*; this source is not compiled or interpreted in a game build. No binary reference image, protected source ROM or model weights are in this branch.

**Visual provenance, not proof of 3D ground truth:** Original Uniracers title frame 400, an authentic 256×224 original PPU source snapshot in independently pinned native AOT artifact **11863045863** (archive SHA256 `6fb7e9ad5ce53e02f0dda0896f520e2a667f5798c58f8d65b5541ed2d53a5431`), and unchanged 2P gameplay frames 1856 and 2208 from the same archive. The title reference contains two overlapping unicycles under a genuine dark title-fade; for visual inspection only, a brighter 3.5× *display preview* was used, explicitly **never** as source pixel evidence. The previous procedural 4× rider from `baldosa-hd-captures-4x/ur-baldosa-frame-001856.pam` serves as the owner's rejected technical baseline. The title-source proportion estimates are tentative because this is a composite, angled title scene. The exact current 7:6 stock gameplay PAR and all output-geometry policies remain independent.

**Rig interpretation:** Each pose derives from one shared tire, wheel, spokes/hub, fork, pedal assembly and a curved saddle. Wheel/tire and rounded mass are intentionally treated as consistent 3D geometry; the five prototypes differ only by rig rotation, pedal crank phase and saddle lean. The saddle uses connected loft sections to represent the broad raised tail, dipped center and curled nose seen in the high-detail title, instead of unrelated per-pose 2D polygon drawings. Color and proportions are early design parameters, **not source-measured final values**. Do not treat OpenSCAD's default camera, test lighting or visible silhouette at 480px as a source-exact camera calibration.

For a quick unapproved pose render with OpenSCAD 2021.01 or later:

```sh
openscad -o /tmp/ur-racer-side.png --imgsize=480,480 \
  --projection=o --viewall --autocenter --colorscheme=Tomorrow \
  -D 'rig_pose="upright"' tools/art/candidates/unicycle_shared_rig.scad

for pose in upright pedal wheelie stunt bank; do
  openscad -o "/tmp/ur-racer-${pose}.png" --imgsize=480,480 \
    --projection=o --viewall --autocenter --colorscheme=Tomorrow \
    -D "rig_pose=\"$pose\"" tools/art/candidates/unicycle_shared_rig.scad
done
```

**Review is presently BLOCKED.** Before baking any 256×256 candidate into the existing `native/presentation/racer_hd_presenter.hpp` or enabling new 1P/2P substitution, obtain source-hashed original-title/period-art landmark annotations, review a consistent **side and three-quarter** model across adjacent authentic poses, retarget pivot/contact/7:6 source registration, compare at real race and split-screen scale, and obtain **new explicit owner visual approval**. Earlier `shipping_art_approved` technical hashes do not authorize this candidate. Never promise parity from the five static previews. The finished media and 4K display acceptance are distinct gates, left to the independent QA owner.

**No runtime or shipping changes in this branch:** authentic Original and the existing fail-closed Remastered fallback remain exactly as before. This blockout should be rejected, changed or deleted if detailed reference comparisons show a proportion or personality mismatch. It is a reviewable single-rig input for an actual artist, not an automatic replacement for approved work.
