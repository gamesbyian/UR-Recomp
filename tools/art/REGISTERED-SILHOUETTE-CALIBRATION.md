# ART-4K candidate registration score: offline technical metric

**Status:** diagnostic-only, unapproved art. This is the fixed-coordinate scorer for the [inverse-graphics plan](../../docs/HD-RACER-INVERSE-GRAPHICS-PLAN.md) A2/A4. It consumes retained source-verified 64×64 original player rasters from the October 10 showcase and independently generated 64×64 or **256×256** candidate PNGs. It is not a Blender/OpenSCAD exporter, a new runtime HD presenter or a source-1994 3D reconstruction.

From repo root:

```sh
python3 tools/art/build_racer_source_pixel_corpus.py --out /tmp/source-racer-corpus.json
# First render the existing unapproved PR #2832 model into a FIXED registered
# 256x256 transparent canvas, without pose-specific auto-cropping/centering.
python3 tools/art/score_racer_candidate.py \
  --player p1 --frame 1205 \
  --candidate /tmp/registered-p1-1205.png \
  --candidate-sha256 "$(sha256sum /tmp/registered-p1-1205.png | cut -d' ' -f1)" \
  --density 4 --out /tmp/p1-1205-score.json
python3 -m unittest tests.unit.test_racer_source_pixel_corpus tests.unit.test_score_racer_candidate
```

**Input contract:** candidate PNG must be lossless non-interlaced RGBA8 and precisely **64×64** for \`--density 1\` or **256×256** for \`--density 4\`. The source is authenticated against the existing per-frame PNG pixel SHA in \`inputs-p1.json\` / \`inputs-p2.json\`, and the relevant registered frame/player in \`analysis/data/racer-hd-replacement-prototype.json\`. The candidate requires an exact *file SHA*, so a replaced PNG cannot silently keep a successful evaluation. These 16 source frames are the **first-family review window only**; the different 2P native-PPU original-sources at frame2208 must be introduced through their own native evidence validator, not sent to this tool with the wrong raster size.

**Registration contract:** no translating, scaling, cropping or silhouette normalizing is done. At 4×, evaluate exactly one alpha sample at \`(4*x+2, 4*y+2)\` in each source-logical pixel, matching the existing art review’s 4× logical-pixel-centre convention. Alpha is binary for scoring; any nonzero alpha counts as occupied. Transparent or malformed candidates fail closed. The original logical raster has physical horizontal pixel aspect **7:6**, used by the symmetric mean Chamfer boundary distance. Original source silhouette IoU is computed on exact logical-grid pixels, not physically warped artwork. The lowest visible alpha-row midpoint is reported in fixed-point source pixels; it is **not a verified physical wheel-ground/collision-contact point**.

**Report:** exact source and candidate PNG SHA, source decoded RGBA SHA, selected player/frame/representation, 64px mask intersection/union/IoU/XOR, 7:6 boundary Chamfer distance, source and candidate occupancy, alpha bounds, lowest occupied row/span and offset, and explicit \`false\` source-3D/model/owner-likeness/shipping claims. A source image compared with itself can achieve perfect metrics and must be marked as a trivial identical-original control. This score alone does not certify the original character identity or animation.

**Next use:** produce a real source-coordinate model-render adapter for the existing #2832 five-parent GLB rig, with one fixed declared camera family and parameter receipt, then evaluate multiple named poses and **pre-declared independent** holdout families rather than optimizing a single 1205 silhouette. Ensure the runner checks candidate model/pose/camera source digests and unchanged guest placement. Do not invent a new GLB rig or runtime animation system. Source colour, physical materials, presentation foreground/occlusion and human character likeness require their separate established gates. Heavy rendering is opt-in, not a per-push CI dependency.
