# Existing 2026 GLB: depth-visible wheel paint allocation (no geometry edits)

**2026-11-05. Research-only counterfactual, not original 1994 3D recovery or owner-approved character art.**

The source-morphology analysis [#3055](https://github.com/gamesbyian/UR-Recomp/pull/3055) showed that the original ROM's high-chroma paint overlaps the wheel/rim more than the current model's **blue fork material**. A new exact executed Mesen24 reference (see [#3159](https://github.com/gamesbyian/UR-Recomp/pull/3159)) gives source-only fractions **0.58260667–0.61296669 blue** (19 exact binary silhouette votes) and **0.58674359–0.59078737 red** (23 votes), without selecting favourable tied 2D ring centres. This extension asks a narrower question: *how much of the visible 2026 material distribution mismatch can be explained by changing paint assignment without touching its 3D geometry?*

## Frozen model and renderer

Re-use the one original unapproved five-parent/16-material source GLB from the latest successful [Pages real-model export #42049555726](https://github.com/gamesbyian/UR-Recomp/actions/runs/42049555726), artifact **#13433963866**:

- Exact source SCAD SHA `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`, candidate upright GLB SHA `d2a2beee85f63fa074f1fa7294c5cd7522f376f9d4b02354e97c0702dda3fa7f` and source authoring branch revision `975920cafc87af120649cd6db2b81e740f4363f9`.
- Unchanged provisional 7:6 source side-camera SHA `1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028` from `analysis/data/racer-inverse-side-provisional-1205.json`. Project actual 2026 tire axle into this 64px raster, not any original source-derived optimized alignment.
- Re-use the *existing* `material_triangles` and `rasterize_depth` full 16-material frontmost z-buffer, not a second renderer; exclude exactly tied frontmost different-material pixels. Report **both** +world-Y and −world-Y source-unverified provisional viewing directions; do not choose the more source-like side.
- Use only the currently *already implemented* research-review Pages paint hypotheses: unchanged original blue `fork_and_frame__material_0`; `area` adds `rim_and_hub__material_1` and `pedals__material_1`; `disc` adds `rim_and_hub__material_2` and `pedals__material_1`; `discPlus` adds `rim_and_hub__material_2`, `pedals__material_0` and `pedals__material_1`. These are **material-label counterfactuals**, never replacements of actual mesh, source GLB material bytes or approved palette.

## Actual source-model offline first measurement

Independent offline projection of exactly the published GLB, its unchanged camera, material names and all 28,860 original model triangles. The wheel axle projects to **(33.5,28.5) logical 64px coordinates** under the provisional side view. All **267** projected whole-model pixels have a definite frontmost material on either side; no distinct-material top-depth ties. Only the counted original-painted labels differ:

| Existing Pages preview mode | Painted material pixels visible, +Y / −Y | Inside unchanged seven-pixel wheel disc | Painted fraction inside, +Y / −Y |
|---|---:|---:|---:|
| Original fork blue | 39 / 39 | 9 / 9 | **0.23076923 / 0.23076923** |
| Add rim shadow and crank (`area`) | 57 / 57 | 27 / 27 | **0.47368421 / 0.47368421** |
| Add rim face and crank (`disc`) | 65 / 67 | 35 / 37 | **0.53846154 / 0.55223881** |
| Add rim face and both cranks (`discPlus`) | 67 / 69 | 37 / 39 | **0.55223881 / 0.56521739** |

These were independently measured by a local NumPy full-z-buffer implementation using the **same frozen triangle projection, material IDs, camera and tie convention** as the repository's previously validated rasterizer. The newly committed producer must reproduce them using the existing canonical rasterizer before the numbers are promoted to a final audited model receipt.

The earlier 35-source original paint study compared different source poses and a selected model hinge and found a **0.29678519** material fraction. The present original-upright model's **0.23076923** therefore must *not* replace that historical score or be conflated with its pose selection. Likewise the new original Mesen24 source fractions and this provisional 2026 model view are **unpaired**, so no source-avatar match metric can be calculated by direct subtraction. The descriptive consistency supports pursuing material allocation before mesh-inflation, not accepting one 1994 physical part hypothesis.

## Reproduction and next decision

```sh
python3 -m unittest tests.unit.test_audit_review_glb_paint_allocation
python3 -m tools.art.audit_review_glb_paint_allocation \
  --model-artifact-zip /private/ur-experimental-model-review-actual-glbs.zip \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --out /private/new/real-model-material-policy-receipt.json
```

The producer fails closed on source model/camera/model-asset SHA mismatches and keeps all four existing viewer modes, actual material names, two depth directions, top-depth ties and one axle/rim. It writes only a no-overwrite **numeric** report. No added CI runner, camera fit, source-ROM re-extraction, game asset, GLB export or compiled model.

**Next bounded physical/character question:** An independently sourced high-detail wheel/hub/crank rendering or original animation with known 3D surface ownership could adjudicate where the original source paint belongs. Without it, test colour-corrected reversible *2026* viewer candidates, not new unverified anatomy; keep the owner's procedural likeness veto and ART/Windows release gates false.
