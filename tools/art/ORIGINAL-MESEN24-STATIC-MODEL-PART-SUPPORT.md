# ART-4K: fixed model-part footprint versus authentic source interior changes

**Purpose, 2026-11-03 local:** use the one existing unapproved 2026 racer GLB and the original 1994 game's authenticated 24 consecutive no-skip Mesen source OBJ observations to determine *where source-index changes fall relative to the static projected 2026 visible parts*. This is an offline orientation/coverage discriminator, **not a physical part identification or recovered animation**. Do not promote the experimental GLB into shipping art.

## Frozen, independent evidence classes

- Original: the exact source PPU archive from merged [#3103](https://github.com/gamesbyian/UR-Recomp/pull/3103), authentic bridge ticks **1601–1624**, ZIP SHA-256 `28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`, source OAM slot **96 blue / 97 red**, source-held local 4bpp orientation. Its independent pinned original-source auditor is run *before* computing any model overlap. Red completed-screen orientation is a separate authenticated observation and is **not** applied to these OAM-local source planes.
- Model: exactly the original 2026 experimental **upright** five-parent, 16-material GLB SHA-256 `efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5`, previously authenticated from retained real viewer artifact #13063969312. One existing provisional orthographic **7:6** camera SHA-256 `1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028`. No new GLB, camera, geometry, model pose or palette recolouring.
- Reuse the existing merged `tools/art/glb_parent_part_id_raster.py` to depth-rasterize each original GLB material mesh into one of its **five actual 2026 parent labels**. Validate all 16 material parents and the rigid scene transform; independently compare the entire 256×256 model ID-mask footprint against the existing source-fixed whole-GLB silhouette raster. **Zero differing 256-pixel raster samples** were found. Labels at logical 64px centres use the existing `[2::4,2::4]` sampling lattice.
- Register **once per racer**, using only the tick-1601 visible lowest-alpha-span midpoint in source-local half-pixel coordinates. The model part-ID raster and its original geometry are thereafter static for all 23 genuine source transitions. No per-frame free translation, flip, camera, size, part association, or individual target source mask is optimized.

The source-only 4bpp change census distinguishes (a) **alpha boundary XOR**, when a pixel switches between transparent index 0 and nonzero, from (b) **interior-index change**, when the original 4bpp index changes but both pixels remain opaque. Part IDs are 2026 *visible model labels at a pixel*, not claims that original SNES palette indices belonged to those physical components.

## Bounded result from the actual original source

| Authentic 23-edge source index changes | Blue source OAM96 | Red source OAM97 |
|---|---:|---:|
| Source interior-index changed-pixel instances | 717 | 834 |
| Model-visible part footprint contains source changes | **433 (60.39%)** | **514 (61.63%)** |
| Original changes outside the static model footprint | **284 (39.61%)** | **320 (38.37%)** |
| Inside 2026 tire projection | 120 | 139 |
| Inside 2026 rim/hub projection | 140 | 189 |
| Inside 2026 pedals projection | 95 | 111 |
| Inside 2026 fork/frame projection | 64 | 75 |
| Inside 2026 saddle projection | 14 | 0 |
| Source tick-1601 vs model static alpha-mask IoU | 0.54641910 | 0.43424318 |

The **355 blue / 439 red** interior source changes that spatially land on *candidate* tire/rim/pedal pixels are about 49.5% and 52.6% of all original interior changes respectively. This counts *instances across 23 edges*, **not independent pixel samples, source-to-2026 part correspondences, explained changing model paint, or model dynamic index agreement**. No source palette index was assigned to a model material or part in this experiment.

Four coarse fixed position controls (±8 logical pixels in horizontal or vertical direction), **predeclared before scoring**, provide a basic registration sanity check:

| Unfitted static candidate placement | Blue source interior coverage | Red source interior coverage |
|---|---:|---:|
| Actual tick-1601 source-alpha anchored | **60.39%** | **61.63%** |
| Offset +8 horizontal | 44.35% | 26.38% |
| Offset −8 horizontal | 27.89% | 47.12% |
| Offset +8 vertical | 49.79% | 56.47% |
| Offset −8 vertical | 37.38% | 32.49% |

The actual source-alpha anchor beats these four *coarse* alternatives, but the red +8 vertical control approaches it. These nulls are **not statistical null models**: they are sparse hand-chosen source-space offsets, and zero-filled displaced model footprints can be clipped at the 64px border, changing coverage area. They establish neither a uniquely calibrated original camera nor independent part identity.

**The mechanical inference is limited but useful:** the provisional 2026 static shape covers about three fifths of observed original internal colour-index changes, with many remaining outside it even before evaluating temporal motion or assigning materials. Geometry discrepancy, original source pose changes, projection/registration, painted surface and occlusion can all cause this. It would be unjustified to tune model geometry or infer original wheel material ownership simply to maximize static coverage.

## Next discriminating comparison

The source's 4bpp index plane changes at **1,377 blue** and **1,493 red** pixel instances across 23 genuine edges. Original silhouette-only temporal rig controls in [#3101](https://github.com/gamesbyian/UR-Recomp/pull/3101) leave **717 blue** and **834 red** opaque-shared interior changes outside their scored objective. The current fixed-ID study establishes a source-to-*candidate-part-region* baseline, but **cannot** tell if parts actually move at the right pixels.

Reuse `glb_parent_part_id_raster.py`, `score_index_glb_parts.py`, existing source-index descriptors, the single coupled rig and one camera. A useful next bounded discriminator is *changed material/part boundaries across a finite, predeclared pair of GLB poses*, with unpaired/shifted source index controls and no fitted colour/part mapping. A model part-ID may remain constant inside a rotating rim; therefore **part ID changes alone will also miss internal material/spoke detail**. Do not call this remaining motion recovered until the appropriate material-ID/paint visibility controls exist. Stop with `unresolved` if source index to 2026 material correspondence is not independently identifiable.

## Reproduce without source ROM or GLB regeneration

From the repository root, using the retained source archive and real viewer GLB and the **optional** NumPy/Trimesh/Pillow packages:

```sh
python3 -m unittest tests.unit.test_art4k_mesen24_static_model_part_coverage
python3 -m tools.art.audit_original_mesen24_static_model_part_visibility \
  analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip \
  /exact/sha-pinned/upright-efdc8425f252b4a0.glb \
  analysis/data/racer-inverse-side-provisional-1205.json \
  /new/experiment-static-model-part-coverage.json
```

The exact numeric HP report is `analysis/data/racer-original-mesen24-static-model-part-coverage-20261103.json`, SHA-256 **`4fec59233ee550bf435bfd802f58ace160edeccae582adf3fe2e3008ece8d97f`**. The offline tool verifies the original Mesen evidence using the existing authoritative archive validator; checks actual GLB, camera and scene identities; independently proves 256px ID-mask/silhouette equality; and writes through the existing exclusive no-overwrite publisher. Four standard-library unit tests assert exact source/model/camera/report hashes, per-part exhaustive partition arithmetic, fixed offset identities and refusal to imply a historical 1994 3D part identification. The actual HP real-GLB run passed; the repeat run's canonical numerical report matched the first run byte-for-byte.

No new original ROM replay, viewer, 3D art, original part mapping, owner approval, Windows build or release gate is claimed.
