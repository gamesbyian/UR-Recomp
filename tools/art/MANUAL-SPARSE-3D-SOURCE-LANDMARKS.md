# Genuine sparse 2D character landmarks from official 1994 printed views

The original 1994 Nintendo/DMA USA booklet contains near-frontal, oblique and underside unicycle illustrations, but parts are frequently hidden behind the printed track, other geometry, type or the page boundary. The existing complete-wheel-and-saddle landmark contract works for unoccluded gameplay silhouettes. It cannot truthfully describe a print crop where only the fork crown is visible. **Never fill occluded anatomy with invented coordinates.**

`tools/art/audit_manual_sparse_landmarks.py` implements a separate **strictly 2D, per-part sparse landmark contract** for exactly the four crop views from `extract_manual_3d_reference_views.py` (#3166), without weakening the original full-silhouette contract. It allows recording a visible crown/fork/clamp without a visible whole wheel, and only computes ratios against the printed wheel's *projected vertical diameter when the entire wheel has actually been annotated*. Otherwise those ratios are JSON `null`, not fake zeros or physical 3D dimensions.

Example private workflow:

```sh
python3 tools/art/extract_manual_3d_reference_views.py \
  --pdf reference/imported/manuals/Uniracers-USA-manual.pdf \
  --out-dir /private/ur-manual-crops
# Review the four actual images and annotate one or more original figures.
python3 tools/art/audit_manual_sparse_landmarks.py \
  /private/ur-manual-crops/observations.json \
  --crop-dir /private/ur-manual-crops \
  --source-pdf reference/imported/manuals/Uniracers-USA-manual.pdf \
  --out /private/ur-manual-crops/observations-measured.json
```

The annotations file uses `UR-ART4K-OFFICIAL-MANUAL-SPARSE-2D/1`, the **actual PDF SHA256** from `source-crops.json`, and one or more records with a unique `reference_id`, nonzero positive `pixel_uncertainty`, genuine `annotator`, nonempty `perspective_and_occlusion_notes`, `visible_points` and `unmeasurable` reasons. For every group, supply all its points or supply a specific occlusion explanation:

- `wheel`, `hub`, `saddle`: left/right/top/bottom point pairs on the **same printed** 2D object.
- `crown`, `fork`: left/right points.
- `clamp`: top/bottom points.
- `crank`: crank root and visible pedal-end center.

A record for printed page-14 `p14-twist-fork-front` can contain **only the crown** if the whole wheel is concealed, with every other group explained in `unmeasurable`. This is valid evidence about **one projected 2D width**, but cannot supply a ratio to a hidden wheel or establish physical 3D separation. A different page-15 `p15-mega-underside` view may have a complete visible tire with the crank pedal cropped; annotate the tire and omit the pedal group with a reason rather than inferring its invisible endpoint. All coordinates are pixel X/Y **within the actual source crop**. Pixel aspect is **square print image**, never the original SNES 7:6 raster correction. Perspective foreshortening/lighting and uncertainty still require careful human interpretation.

Provenance is deliberately stronger than a self-hashed crop: this tool independently authenticates the entire original Git-tracked source PDF blob; validates the complete four-image crop receipt, fixed page numbers, crop rectangles, true image sizes and each recorded PNG SHA-256; and then **rerenders the source PDF at the same 144 DPI and compares every decoded RGB crop pixel**. Rewriting a PNG *and its claimed SHA* is rejected. Pillow and PyMuPDF are required for this source-pixel replay, and missing dependencies must fail rather than silently weakening verification. The CLI never embeds source pixels in a report, overwrites a prior measurement or writes to game assets.

Current status: **measurement infrastructure only.** No real retained-manual figure pixels have yet been measured in this pipeline, no coherent physical 1994 source mesh or original 3D camera has been recovered, and the printed illustrations may have different compositing, cropping and/or geometry from original game sprites. The one five-parent/16-material 2026 GLB remains an experimental viewer/model, and owner likeness plus shipping/Windows ART approval remain ungranted. Do not use unmeasured picture proportions as a reason to promote the widened 2026 crown or create a second rig.
