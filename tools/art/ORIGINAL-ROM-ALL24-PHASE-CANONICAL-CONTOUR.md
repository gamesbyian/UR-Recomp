# Complete 24-phase original ROM contour stability: source-only reconstruction constraint

The previous verified 4-phase study #3151 found that original 64-orientation inverse-rotated 2D consensus silhouettes at phase indices 0,6,12,18 differ at only **13 common-valid pixels** (upper0/middle1/lower12) over 3,008 adequately sampled source-canvas positions. That cannot establish a claim about the *other twenty* original phases. This experiment resolves the outstanding source uncertainty before proposing another 2026 GLB parameter.

## Source and measurement protocol

Reuse the **single original SHA-256 verified USA ROM**, previously authenticated 24×64 table, original 64px 30-tile packed 4bpp renderer, original SHA-pinned source phase/orientation evidence, and one frozen 2D inverse-rotation pivot **(31.515625,19.578125)** learned from the even source orientation bounding-box evidence. The existing source-only consensus function computes per-phase majority alpha and 90%-opaque core over **all 64 original orientation indices**, using a separately inverse-sampled valid canvas so cropped corners are not counted as transparent pixels. No original physical 3D joint, camera angle or pedal speed is inferred from these indices.

Run against all **24 original ROM presentation phases**, without extrapolating from only 0,6,12,18. On the intersection of adequately viewed original pixels across all 24, report always/ever majority-opaque 2D silhouette, invariant near-opaque core and 2D phase-variable pixel support. Partition source alpha changes into the frozen upper y0..14/middle y15..26/lower y27..63 source image bands with exact conservation. Independently report each of the **24 cyclic adjacent source phase-index pairs**, alpha TP/FP/FN and source 4bpp index-paint recall. Source *index neighbors* are **not chronological consecutive Mesen PPU frames**. The original game may advance indices by 2,3,4,5 or another timing law. Preserve the previous 4-phase golden: **291 always, 304 ever, 164 core, 13 phase-variable**.

## Compute-aware qualification

The source-only Python analyzer has one explicit rom/axis/out CLI, reuses the existing source renderer, produces a compact report of counts/hashes and refuses to overwrite a previous output. A fast synthetic unit suite checks 24-phase conservation, paint-versus-alpha separation, invalid input and false original-3D claims. One initial, bounded actual 2MiB/1,536-frame source-ROM qualification in the existing tooling suite records the real numerical result. After that, its heavy genuine-ROM unit can be retired from recurring CI while preserving exact pinned metrics, run ID and CLI reproduction. No new emulator capture, 3D asset, Windows model renderer, source viewer, workflow file or OpenSCAD export.

Run using the existing module at tools/art/analyze_original_rom_all24_phase_contour.py with the original ROM, the source-axis JSON in analysis/data, and a new output JSON path.

## Interpretation and decision

If the full original 24-phase alpha contour stays strongly invariant in the upper region, the most discriminating **3D modelling work** is recovering the *shared upper source geometry* and screen orientation/occlusion under one provisional camera, rather than adding speculative phase-dependent saddle/stretch motion. If untested phases reveal substantial upper variability, preserve source phase identities and 2D coverage, then design one falsifiable two-player model comparison rather than fitting every source tick. The full original 24×64 table has already been inspected; it cannot become prospective holdout.

Original 1994 mesh, artist materials, physical wheel/saddle joints and camera are **not** recovered. Preserve one canonical experimental five-parent/16-material 2026 GLB (#2832), the genuine two-player six-objective Pareto comparisons (#3150), and owner likeness/Windows ART release veto.
