# ART-4K: original 2D pose-reference exemplars, with no invented 3D labels

**Status:** experimental research-only original-source pose review. This is a deterministic selection of distinct *2D* silhouettes from the already-authenticated 20-tick, two-racer Mesen archive (40 live OBJ planes), not an inferred 1994 source mesh, skeletal joint pose, camera calibration, or approved replacement artwork. The canonical editable 2026 experimental rig remains [draft #2832](https://github.com/gamesbyian/UR-Recomp/pull/2832); the existing Pages model reviewer and all five GLB pose studies are unchanged.

## Exact evidence and why another selector was needed

The [authenticated 20-tick original source capture #3088](https://github.com/gamesbyian/UR-Recomp/pull/3088) proves **12,937/12,937** 2D source pixels correspond to the completed original screenshots under original RGB or the declared 5-bit red+13/clamp overlay. Red is horizontally reflected in the original completed upper viewport relative to held OAM. [The source-only 40-vs-five-real-GLB study #3091](https://github.com/gamesbyian/UR-Recomp/pull/3091) found that simply swapping held-original red alpha to **player-visible mirrored red** changed the five-pose unpaired winner counts from **29 bank / 7 upright** to **18 bank / 17 upright**, with an unresolved tie. Those rankings cannot assign genuine 1994 animation pose identities.

[Original tile ancestry #3094](https://github.com/gamesbyian/UR-Recomp/pull/3094), independently recreated from **five SHA-pinned original ZIP archives**, found 38 novel authentic 4bpp index planes beyond the frozen original 16-fit/19-withheld corpus, divided into 11 transitive nonblank-8×8-tile-content groups. Nine new sprites in three whole groups (sizes 4,4,1) share **no** original tile with the historical corpus. All historic fit/withheld/strict-six roles are protected. Distinct underlying tiles do **not** independently certify distinct camera angles, articulated poses or facial personality.

## One source-faithful selection algorithm

Run `tools/art/select_original_mesen_live_pose_exemplars.py` on the unchanged real-source archive. It **first** reruns the authentic 40/40 PPU+completed-screen SHA and pixel correspondence auditor. It then re-decodes the true SNES 4bpp OBJ alpha, uses the frozen 11-group source-tile partition and independently recomputes the tile-connected components. For visual silhouette distance only, it reflects red horizontally as observed on the completed upper screen and leaves blue unreflected.

Within each group the tool chooses the **medoid**, the sprite with highest mean binary-mask IoU to the other members. For groups with at least four sprites, it also chooses the source sprite with the **lowest IoU to that medoid**, an intentionally contrasting view. Ties use earliest actual original Mesen tick then blue before red, with no random seed, score-driven flip or camera search. Groups of one to three receive one exemplar, preserving a 15-image selection across the 11 content groups.

**Output (November 3):** 15 selected original source observations:

`blue@1601, blue@1607, red@1631, blue@1648, blue@1700, red@1700, red@1768, blue@1809, blue@1899, red@1899, red@1952, blue@2072, blue@2283, red@2283, blue@2445`.

The 15 screen-oriented exemplars have mean pairwise binary silhouette IoU **0.41781196**, minimum **0.09493671**. Those are 2D appearance diagnostics, not 3D novelty or automatically verified anatomy.

The interesting contrast is among the original-content-independent groups:

| Exact source identities | Group count | Mean player-visible alpha IoU | Interpretation |
| --- | ---: | ---: | --- |
| Blue ticks 1648,1671,1700,2011 | 4 | **0.94434076** | Distinct original tiles but very similar projected shape |
| Red ticks 1671,1700,1731; blue tick 2283 | 4 | **0.54068146** | Much broader source-2D shape variation, without proven 3D angle identity |
| Blue tick 2445 | 1 | N/A | Single novel source reference; no within-group pose diversity to infer |

All **nine** content-independent observations remain unassigned to fit/holdout. Their historical experimental five-GLB score comparisons have already been inspected, so these are valuable **reference-only** stress cases, not fresh prospective blind test data. Similarly, 29 novel planes connected to historical fit tiles remain **unclassified**; this tool never promotes them to fitting or changes any frozen original roles. Red 1601 remains historical withheld; blue 1952 remains historical fit.

## Reproducibility and next 3D decision

The compact frozen original-2D selection receipt is `analysis/data/racer-original-live40-screen-review-exemplars-20261103.json`. It contains the full 11 component identities, medoids, contrasts, IoUs, group status and explicit negative 3D/approval flags. The standalone CLI also reconstructs and SHA-checks all **40** individual source index/alpha planes, screen-facing alpha bounding boxes and original completed-screen coordinates in an optional full fresh JSON output; this avoids storing redundant ROM-derived image blobs in the public repository.

```bash
python3 -m unittest -v tests.unit.test_select_original_mesen_live_pose_exemplars

python3 -m tools.art.select_original_mesen_live_pose_exemplars \
  --source-zip /private/original-13217381754.zip \
  --registration analysis/data/racer-original-mesen-twenty-live-2d-screen-registrations-20261103.json \
  --novelty analysis/data/racer-original-live40-historical-tile-content-novelty-20261103.json \
  --verify-committed analysis/data/racer-original-live40-screen-review-exemplars-20261103.json \
  --contact-sheet /private/new/original-15-pose-reference.png \
  --out /private/new/source-review-exemplars.json
```

**Optional original-colour review sheet:** the `--contact-sheet` argument renders the 15 exact source **OAM+VRAM+CGRAM** 64×64 RGBA sprites onto a neutral checkerboard at nearest-neighbour scale. Red is reflected *only* because the independently authenticated completed screen shows it that way; its CGRAM RGB bytes are untouched, and HUD red-overlay pixels are not fabricated. The generator verifies original index and alpha SHA for each selected sprite, refuses an existing output path, and prints the PNG SHA. Pillow is required only when rendering the optional sheet. This sheet is a local/private review artifact; the PR does not redistribute 40 raw original sprites or another published Pages app. Original full-screen P6/source SHA audit and compact receipt verification always run before the sheet is created.

Authentic original source: [Actions run #41605614082](https://github.com/gamesbyian/UR-Recomp/actions/runs/41605614082), artifact #13217381754, ZIP SHA `709fbc2a1cd94b888d8ae0d43894c42c5d455bd968f6bc11f26e710f44e2788f`. The actual original USA ROM, original replay, MesenCE revision and per-source framebuffer SHA identities remain pinned in #3088. This command **does not execute the emulator**, rebuild GLBs, mutate the Pages site, reassign assets, adjust the provisional camera, or alter native graphics.

**Next stage:** use these 2D reference identities for *human-labelled* correspondences between wheel/saddle/fork, original screen anchor, and the one existing experimental GLB rig. Require multiple original viewpoints and an independently frozen camera/pose hypothesis before changing the geometry. Treat the previously used 16/19/strict-six original split and the 4/4/1 source-content disjoint groups as protected review evidence; any truly blind evaluation needs a future precommitted original source sample **not already inspected by five-GLB score**. Avoid repeating a large Mesen replay merely to re-show these authenticated pixels.

**Nonclaims:** no original 3D model, source skeleton, 1994 camera, original articulated pose identity, original PPU per-scanline winner or owner artistic likeness recovered or accepted. No gameplay/runtime or Windows release gates modified.
