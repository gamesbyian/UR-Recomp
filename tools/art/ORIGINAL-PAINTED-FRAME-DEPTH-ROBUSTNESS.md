# Original sprite painted-axis robustness under actual 2026 GLB material depth

Research-only post hoc continuation of the merged source-registered fitting work in #3035, #3038 and #3039, applied to the **same** historical five-parent, sixteen-material GLB. No second model, camera-calibration attempt, renderer replacement, original ROM images, deployed Pages control, or gameplay change.

## Why this matters

The earlier original-2D source-colour-guided rig selector measured the full 2026 GLB blue frame material's unoccluded projected alpha. Its own per-angle receipt showed approximately 36–43% projected blue pixels overlapping other materials. That overlap was deliberately **not called occlusion**, because it did not establish the front/back depth order.

The new offline source-pinned diagnostic rasterizes triangles at the SAME source 64x64 pixel-centre positions, using the existing provisional 7:6 camera and explicit orthographic **world-Y depth** interpolation. It computes three painted blue-frame axes at each unchanged 5-degree frame hinge from -45 to +45 degrees: unoccluded blue material, depth-visible blue as viewed from +world-Y, and depth-visible blue from -world-Y. The depth buffer reports overlapping triangles, rejects non-finite/cropped meshes, never culls a back-facing material as transparent, and conservatively marks coplanar *different materials* as ambiguous. Any later nearer triangle resolves that ambiguity. No source sprite is used as the z-depth oracle.

Original-ROM 2D chroma SHA and 2026 model GLB / provisional camera SHAs are verified independently, and each of the 35 source sprite axes selects a hypothetical 3D frame angle using **2D painted-axis distance only**. No source/3D silhouette intersection-over-union is used to select a pose, camera direction, registration, or material.

## Initial independent real-GLB depth observations

Offline NumPy/Trimesh test against the historical upright GLB SHA efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5 and original ROM 2D painted-axis report SHA 78f420423c62e61bcb5c4271c61dc8dab17b786f693c2895cd0e3054d1d06bc8, same provisional camera:

- Exactly **2 of 35** candidate 2026 hinge selections differ between the blue-material unoccluded 2D axis and the depth-aware +Y view. Exactly **2 of 35** also differ under the -Y view.
- The two opposite world-Y viewing directions select identical discrete 5-degree hinge candidates for **all 35 source masks**, despite not proving which orientation was the 1994 original.
- The two source masks whose chosen 2026 frame hinges shift are SHA prefixes 1a1180d6963d... (from -35° to -30°) and 6d7a2658f3ef... (from +35° to +40°), under BOTH candidate view directions.
- Depth-visible blue material counts span **33–44 pixels** at the 64x64 sample grid across the frozen 19 hinge poses. Relative to unoccluded blue, **1–5 pixels** are hidden by other 2026 materials depending on angle under +Y. The two camera directions' painted-axis measurements differ by at most ≈0.524° on the sampled model poses, and the maximum unoccluded-to-depth-axis difference for +Y is ≈1.695°.

These numbers describe the source-authored 2026 *model blue material* and a fixed provisional side camera; they do **not** establish correct original sprite part segmentation. The original 2D player-colour centroid could represent multiple 1994 materials/overlays rather than one 2026 fork. One source sprite family remains distinct in observed 2D paint orientation. The selected candidate angle is a 2026 rig research parameter, not an original 3D joint reconstruction. Existing inherited original source corpus/shape inspection makes this in-sample, not an independent held-out generalization.

## Reproduction

Use the historical exact original upright GLB from real model-review run #41259476190, the existing frozen camera `analysis/data/racer-inverse-side-provisional-1205.json`, and the independently authenticated original 2D painted-axis JSON from original source run #41398486394. Optional NumPy/Trimesh/Pillow are required for rendering; no new CI workflow is required. The default dependency-free unit suite skips NumPy-only raster cases when unavailable.

    python3 tools/art/audit_original_racer_painted_frame_depth.py \
      --glb /private/upright-efdc8425f252b4a0.glb \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --source-chroma /private/source-chroma-axes.json \
      --out /private/new/depth-visible-blue-frame.json

A successful output is a write-once numeric receipt using the existing repository publisher. The next genuinely independent discriminator needs authenticated live emulator PPU/OAM capture and source-colour part attribution. This diagnostic does not make #2832 shipping-ready, recover the original 1994 camera, identify original 3D joints or approve character likeness.


## Independent RGB variants of the same source binary silhouette

The original ROM corpus has 35 unique 2D binary masks but **six** have more than one independently authenticated original RGB variant. The previous per-mask colour-axis reducer reports their equal-variant mean angle. That mean is useful for a one-vote-per-binary-mask census but can hide genuine uncertainty in the *painted* anatomy. Under the new actual-depth +Y model:
- Three of the six multi-colour masks select differing **5-degree 2026 hinge** candidates across their original colour variants.
- The affected mask SHA prefixes are 29116a986243, 312bf146d502 and 385cffd21b4e. Their pairwise candidate sets are respectively +5°/+10°, +20°/+25° and +5°/+10° under the existing original-to-model angle sign.
- Each exact source colour variant is now separately reported by source player, original RGBA SHA, original 2D painted axis and candidate angle for all three projected blue-material visibility methods. Summary counts retain one **binary mask vote**, while reporting multiple allowable 2026 frame poses rather than silently assigning the average-derived angle as physically unique.

These differences can stem from original sprite colour segmentation, player-specific paint area, palette shading or structural remapping. They do **not** prove that 1994 geometry differs between colour variants of the same binary silhouette, or that a 5° shift measures an actual historical joint. Do not turn source colour-variant ambiguity into fictitious independent 3D pose coverage or additional statistical masks.


### Depth-tie publication-order negative control

An independent post-publication review found that a simple incremental nearest-triangle z-buffer could produce different outcomes when three differently labelled materials had depths A=0, B=0.75×10⁻⁶, C=1.5×10⁻⁶ source-world units. Even though B and C are within the declared 10⁻⁶ tie threshold, processing A→B→C could clear the earlier ambiguity on arrival of C. This is unacceptable because serialized triangle order must not influence a source/material visibility receipt.

The current guard now computes a separate **maximum depth for every material** at each source pixel, then resolves the highest visible material and all material ties only after every triangle has contributed. This is order-independent, conservatively preserves B/C ambiguity, and still allows a strictly nearer material to win. The six permutations of the adversarial three-triangle fixture are an explicit regression control. Same-material repeated triangles do not create false cross-material ambiguity. The tie rule is a numerical uncertainty convention, not a claim about exact source-game anti-aliasing or multi-layer sprite compositing.
