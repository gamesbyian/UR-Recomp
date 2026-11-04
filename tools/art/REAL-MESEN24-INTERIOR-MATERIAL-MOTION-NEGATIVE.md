# ART-4K: original source interior motion versus a moving real 2026 material-ID raster

**Experimental bounded negative, 2026-11-03 local.** The 2026 authored GLB remains a five-parent, sixteen-material, visually unapproved reconstruction candidate. This study asks whether its *changing visible material mesh boundaries* spatially cover actual source-original **opaque-to-opaque SNES 4bpp index changes**. It never maps original palette indices to specific 2026 material IDs or identifies a historical 1994 3D rig, camera or angular velocity.

## Frozen input and predeclared scope

Reuse the **original consecutive no-skip Mesen source** already merged by [#3103](https://github.com/gamesbyian/UR-Recomp/pull/3103), ZIP SHA-256 `28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`, ROM/authentic OAM/VRAM/CGRAM verified by the existing source auditor. Source is the **held OAM-local** 64×64 4bpp sprite, OAM96 blue and OAM97 red, not the separately proven completed-screen reflection. The source 24 ticks have already been examined and cannot become a prospective blind holdout.

The **single authentic existing 2026 upright GLB** is SHA-256 `efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5`, with sixteen real material mesh children under the same five articulated parents. Frozen provisional **7:6** orthographic camera SHA-256 `1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028`. Two-DOF coupled rig is the existing experimental [#3101](https://github.com/gamesbyian/UR-Recomp/pull/3101) controller; in this experiment the frame pitch is always **0°** and only the wheel/crank drives **+24° per authentic original tick** (an illustration, not an inferred original rate). Candidate local material meshes/colours are **never modified**. Source/model registration is the single transparent lower-alpha-span anchor from tick1601, separately fixed per player.

Before scoring, the [canonical draft #2832](https://github.com/gamesbyian/UR-Recomp/pull/2832) recorded **three exact source edge pairs**: original blue upper event **1602→1603**, original red upper event **1605→1606**, and ordinary **1609→1610**. Each pair is compared against *both* original players, yielding six transparent source/model comparisons. No frame was selected by candidate IoU, no per-frame flipping/translation/camera/phase/shape or source palette-to-2026 part assignment.

The independent source 4bpp decoder measures **interior index change** where both before and after original source pixels remain opaque. An independent new source-fixed CPU depth renderer assigns the *front-most of sixteen authentic GLB material node IDs* at each of the six moving poses. It refuses equal-depth ambiguous material owners. A separate all-geometry silhouette renderer matched the material-ID alpha mask **pixel-for-pixel at 256×256 on all six dynamic poses**. At neutral, reducing the material labels to their five parent IDs matched the **previously merged independent `glb_parent_part_id_raster.py` exactly at all 256×256 pixels**. The reduced parent labels are then separately scored as a conservative coarse baseline. This explicitly avoids inferring 3D original parts from 2D palette colours.

For any candidate source pixel, predict a model material change only when the frontmost **2026 material node label changes and both model frames remain opaque**. Spatially intersect this binary model-change map with original SNES source 4bpp interior-change pixels. Also test four fixed ±8-logical-pixel candidate spatial translations without wrap. These are coarse sensitivity controls, **not statistically independent nulls** (their coverage may clip).

## Actual real-model result

| Original source and edge | Original opaque-to-opaque 4bpp changed pixels | Candidate visible 2026 material-ID changed pixels | Correct change locations | Source recall | Change IoU |
|---|---:|---:|---:|---:|---:|
| Blue, 1602→1603 (its upper event) | **176** | 9 | 5 | 2.84% | 0.02778 |
| Blue, 1605→1606 | 24 | 16 | 3 | 12.50% | 0.08108 |
| Blue, 1609→1610 | 33 | 12 | 2 | 6.06% | 0.04651 |
| Red, 1602→1603 | 26 | 9 | 3 | 11.54% | 0.09375 |
| Red, 1605→1606 (its upper event) | **192** | 16 | 9 | 4.69% | 0.04523 |
| Red, 1609→1610 | 31 | 12 | 3 | 9.68% | 0.07500 |

**The decisive gap:** even after a physically coherent fixed-rate model wheel rotation, the 2026 visible material labels change at **only 9–16 candidate pixels per adjacent selected pair**, whereas the original source changes up to **176/192 opaque interior index pixels** at the independently executed player event edges. The fixed 2026 material mask captures only 5/176 and 9/192 of the event-local source index-change locations. The one frozen source-alpha registration beats all four ±8-pixel null displacements on raw change-support IoU for all six comparisons, but none of these results independently calibrates the camera or label correspondences.

Collapsing the sixteen material labels to **five parent labels** reduces predicted changed model pixels to **7 / 8 / 6** on the respective three edges. It captures fewer original change locations: blue **3 / 2 / 2**, red **2 / 4 / 2**. This confirms that coarse parent-ID motion loses a little internal signal, while the full material segmentation still leaves the vast majority of original 4bpp motion unexplained.

**Limitations:** A visible 2026 material-ID swap can exaggerate visible colour changes if two material IDs happen to share RGB; conversely changing lighting, textures, details within one material, game-original source redraws and temporally varying original 4bpp index values are not represented by the present candidate material-ID model. The original source 4bpp labels may be reused on multiple independent anatomical components. This is a *location-only* comparison across already-inspected frames, with no inferred material semantics, original camera or historical 3D wheel cadence. The source events were deliberately selected as discriminators, not blind generalization.

## Decision and efficient follow-up

**Stop the arbitrary rigid wheel-speed/frame-pitch/geometry search.** The current 2026 material/part representation does not produce enough correctly located internal moving detail under the tested fixed camera and direct drive. Wheel rotational symmetry, insufficient authored paint/spoke differentiation, missing localized articulation, source registration and original sprite drawing/occlusion remain candidate causes. No single cause is uniquely identified.

Use the **existing source index-region descriptors**, real-model part-ID renderer and current one GLB to investigate which **source image-space regions** contribute the 176/192 event-local index changes and whether any camera-stable, source-independent paint/material hypotheses could recover such changes. Require explicit original image-vs-model label ambiguity/null controls and a new genuine prospective holdout **before** declaring any recovered material correspondence. The owner has not approved visual likeness; no ART shipping asset or Windows release gate is advanced.

## Reproduce

Use the same original Mesen 24-tick archive and original actual GLB, plus optional offline NumPy/Trimesh/Pillow; no ROM execution, OpenSCAD rebuild, new workflow or additional source corpus is required:

```sh
python3 -m unittest tests.unit.test_art4k_mesen24_visible_material_motion_receipt
python3 -m tools.art.evaluate_original_mesen24_visible_material_motion \
  analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip \
  /verified/artifact/upright-efdc8425f252b4a0.glb \
  analysis/data/racer-inverse-side-provisional-1205.json \
  /new/output/material-index-motion-control.json
```

Authentic 2026 model SHA and original source ZIP/camera hashes are all fail-closed. The source auditor verifies all original PPU member hashes; only the six exact authored model poses are rendered. **The output publisher uses the repository's existing atomic no-replace helper**, and the source-index vs model label output is canonical LF UTF-8 JSON. The complete numerical receipt is `analysis/data/racer-original-mesen24-visible-material-motion-20261103.json`, SHA-256 **`11e3956e433aca67673b397e66e7925578d6adc77223b29c29c12fff1a9d3541`**. The real HP run completed and five fast, ROM/GLB-free standard-library tests passed on SHA identity, model-to-parent mapping, arithmetic totals, all six true edge roles, null controls, and syntax/no-replace guards. This model study is experimental and requires independent source review before integration.
