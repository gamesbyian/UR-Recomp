# One global 4bpp index relabelling control after authentic original 2D rotation

**Research question:** the original-ROM full-sprite 2D rotation null on #3114 explains ~66.5% of source silhouette pixels across four original animation phases and 32 odd orientations, but matches only 9,806 / 41,141 = **23.84%** of all authentic source opaque 4bpp index locations. Before attributing the mismatch to unseen original 3D materials/lighting, test whether merely **relabeling source palette indices** after rotation explains more of those pixels. This is a deliberately inexpensive 2D-only shading/encoding null. A 4bpp index is *not* recovered 1994 3D material, surface normal, physical lighting or an RGB value; CGRAM palette choices and original hand-authored sprite shading remain separate.

## Frozen method

Reuse the same exact USA ROM SHA `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`, #3104's original source 24×64 axis SHA `23aa563c094471a3d7f1b5dcb12489cc1b5ca45b1240aee06fde3934a932bbd0`, and #3114's original **full-sprite** 2D rotation. Render source-authored original ROM source 64×64 4bpp index planes at exactly the same **four phase slices 0,6,12,18**. Rotate each phase's source-orientation-zero indexed sprite in raw source pixel coordinates, around the same one shared centre fitted from original *even* source region bounding boxes, with index-angle hypothesis `2πa/64`.

Fit one **global** index mapping on original *even* orientation samples **2,4,...,62** across all four phases, excluding the identically copied angle-zero reference. Collect only paired foreground/foreground pixels into one 16×16 index confusion table. Original zero index remains transparent/unchanged; never turn background into colour or alter alpha. Compare three *predeclared* original 2D models on the **32 odd** orientation indices 1,3,...,63 across all four phases (128 previously inspected source images):

- Identity index mapping: the already executed #3114 baseline (9,806 exact source indices, 41,141 original opaque pixels).
- One global many-to-one majority-index relabel. High flexibility but only 15 fixed source colour substitutions shared across all phases/angles, not 128 image-specific paint jobs.
- One globally **bijective** (one-to-one) index permutation optimized by exact 15-index subset dynamic programming, preserving 0 transparency and the number of distinguishable palette-index labels.

All three use **identical source rotation, 7:6 source/display aspect treatment, original alpha support, target masks, and one reference pose per phase**. Output the actual mapping, train confusion, observed opaque pair counts, overall exact 4bpp index matches, recall over **all original opaque source pixels**, and conditional match rate within alpha overlap. Expose each phase's mean test recall. Do not choose the best mapping per image or claim independence: every source sprite was previously inspected, so this is an internal split, **not a prospective blind holdout**.

If the shared remaps yield little gain, the large original source-paint mismatch requires more than a fixed source palette permutation: view-dependent shading/occlusion/detail, sprite redraw or incorrect source 2D model remain. If gain is material, preserve it as a *cheap source 2D appearance control* that an actual 2026 five-parent GLB material/lighting proposal must surpass with meaningful unseen viewpoint or motion predictions. Neither outcome proves the source 1994 3D artist's material names or the original camera.

## Executed genuine ROM result

The source-only original USA ROM test completed successfully at exact implementation head `87844f8e0c16351dbff0e2b4e0599df829af3581`, [Actions run #41826651132](https://github.com/gamesbyian/UR-Recomp/actions/runs/41826651132), unit job `126562967879`. All source inputs were SHA-verified; the index-only comparison covers **128 original ROM-authored images**, four fixed phases × 32 odd orientation indices, and shares a global mapping fitted using only even orientation indices 2–62.

| Single globally applied indexed-colour rule | Exact source 4bpp index matches | Recall of 41,141 opaque source pixels | Exact fraction within 32,793 alpha-overlap pixels |
|---|---:|---:|---:|
| Unchanged palette indices, rigid 2D rotation | **9,806** | **23.835104%** | 29.902723% |
| One optimal bijective 4bpp-index permutation | **9,887** | **24.031988%** | 30.149727% |
| One more flexible many-to-one 4bpp relabelling | **10,976** | **26.678982%** | 33.470558% |

The best one-to-one remap improves recall by only **0.196884 percentage points** over the original rigid-rotation index baseline. Even the more expressive many-to-one mapping adds just **2.843878 points**, and collapses original palette-index distinctions in ways a physically faithful material system may not permit. Both use the **same** 32,793 geometrically overlapping predicted/source opaque pixels and do not improve silhouette or uncover source depth. The majority of source-painted index structure remains unexplained by global index relabelling.

**Decision:** do not spend model-reconstruction effort fitting a single global 4bpp palette conversion as a substitute for geometry/view-dependent 3D structure. Preserve the source original pixel-index correspondence and test source-relative shape, occlusion and localized apparent motion. Lighting, CGRAM interpretation, sprite redrawing and 3D surface/material hypotheses remain possible but unverified. The follow-up numerical regression asserts the exact three real-ROM count/recall results, and requires its own final-head CI before integration; the implementation run above predates the assertion.

## Reproduce

```sh
python3 -m unittest tests.unit.test_analyze_original_rom_palette_rotation_null
python3 -m tools.art.analyze_original_rom_palette_rotation_null \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --original-axis-report analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json \
  --out /new/original-source-2d-global-4bpp-index-null.json
```

The existing exclusive/no-overwrite report publisher and original ROM/source SHA checks are reused. No new emulator, 2026 GLB export, network fetch, PR validation workflow or authoring branch. Actual numerical source results must come from exact-head CI, not an assumed success. This diagnostic is stacked on #3104, #3113 and #3114; independent scientific review remains required.
