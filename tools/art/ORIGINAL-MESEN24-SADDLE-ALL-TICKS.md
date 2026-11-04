# Original Mesen24 complete two-player timeline: saddle-only 2026 3D control

This is a **temporal generalization check** for [#3121](https://github.com/gamesbyian/UR-Recomp/pull/3121)'s unusually promising, independently articulated **2026 saddle-only +15°** GLB result. The same authenticated current #2832 GLB, source-original Mesen PPU and frozen 7:6 camera must be reused. It does **not** recover the lost 1994 physical 3D model, source camera, actual saddle hinge degrees, painted 4bpp material semantics or owner art approval.

## Why the 8 selected sprites are insufficient

The previously executed real-GLB comparison used **four previously examined original sprites per player** near original orientation index 57–61. Under the source-index→2026 axle-rotation hypothesis, unchanged saddle pose scored **0.52846054 blue / 0.55107352 red** pooled alpha IoU; the same GLB with **constant +15° local saddle mount pitch** improved both **0.56812169 / 0.58201058**, with upper y0–14 gains **0.28798186→0.41523342 blue** and **0.33251834→0.43556701 red**, while lower bands remained stable. A constant −15° lost. The original 2D source rotation still scores **0.83754513 / 0.82731214**, so the 2026 proposal is substantially incomplete.

Two concerns remain: the initial eight original sprite observations were selected for known events, and repeating nearly identical source shapes through time can artificially amplify a small silhouette improvement. Also, a fixed 3D pose may fit individual source frames without explaining *actual chronological source alpha motion*.

## Frozen larger authentic source and model control

Use exactly the existing unskipped original Mesen source archive **ticks 1601–1624** for **both** OAM-local racers (48 original 64×64 index/alpha sprites). Use the exact SHA-pinned #3104 source-ROM 24-phase×64-orientation ID/plane report for **each of the 48** PPU frames, rather than rediscovering or loosely matching poses. The existing decoder in `score_original_mesen24_fixed_pivot_glb.py::read_original_roles` now has an optional `all_original_ticks=True` path with **identical frame/OAM/CGRAM/VRAM/ROM-hash validation**; it does not duplicate original graphics decoding.

At every authentic original tick, compare precisely four globally fixed projections:

1. Real original tick1601 alpha **2D rigidly rotated** by the exact source orientation-index difference under the previous even-index source pivot (31.515625,19.578125). This is the acknowledged stronger *2D original-art null*.
2. Existing **2026** five-parent authentic GLB, source orientation-index absolute wheel-axle-root hypothesis, **neutral saddle (0°)**.
3. Identical 2026 GLB under **+15° saddle-parent-only local Y** pitch.
4. Identical GLB under **−15° saddle-parent-only local Y** pitch.

The `temporary_saddle_pitch` already authored/tested on #3121 guarantees the saddle's *real existing GLB mount remains in place*, other four parents and all sixteen material child meshes are unchanged, and the scene graph restores exactly before another root pose. All three 2026 controls use the *same* original source angle, neutral crank and frame pitch, one frozen camera, original SNES 7:6 aspect, and the **same tick1601 lower-alpha registration per player**. No model angle, saddle pitch, camera, source anchor, geometry, palette or source tick is selected based on score. Cache duplicate model pose renders by (original orientation index, saddle pitch) to avoid redundant 2026 real-GLB computation.

Report per original tick each candidate's full 64px silhouette TP/FP/FN/IoU and fixed upper/middle/lower original source image-band errors; then report **three deliberately distinct** 24-frame summaries for each player:

- *Chronological pooled IoU*: every true original Mesen frame has its actual temporal vote, for compatibility with the earlier eight-frame comparison.
- *Unique original binary source silhouette equal-vote mean IoU*: group all 24 original frames by **exact SHA of their 64px original source alpha**. Each distinct original shape has exactly **one** vote, regardless of how many times it appears, with any different model predictions for repeats averaged **within** the group. This rejects artificial sample-size inflation from duplicates.
- *True chronological alpha-change support*: compare all **23 actual consecutive original PPU edges**, using XOR of authentic adjacent source masks and XOR of adjacent projected model masks. Score TP/FP/FN/IoU for *changed locations*, not just each standalone sprite's shape. A constant saddle angle is not allowed to take credit for source phase animation it never predicts.

The source selection is a full short **retrospective original temporal sequence**, **not** a novel 1994 3D perspective or a prospective blind holdout. Real 2026 part labels and saddle pivot are only current authoring geometry. A positive result in 8 selected frames may reverse or weaken in the full 48-image sequence; **the experiment must publish its negative result if so**. Even if +15° remains favourable, owner-visible visual likeness and a genuinely independent original perspective/source family are required before proposing a new default. No desktop machine, additional 1994 emulator run, new OpenSCAD/GLB export, new workflow, server or alternate model is involved.

## Reproduction and provenance

```sh
python3 -m unittest tests.unit.test_score_original_mesen24_full_saddle
python3 -m tools.art.score_original_mesen24_full_saddle \
  --source-zip /exact/sha-verified/original-mesen-consecutive-1601-1624.zip \
  --pose-report /exact/sha-verified/original-mesen24-ROM-pose-IDs.json \
  --axis-report /exact/sha-verified/original-ROM-24phase-64angle-axis.json \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --verified-exports /current/successful/model-exports \
  --out /new/original-Mesen24-saddle-only-all-frames.json
```

The existing Windows Visual Atlas real-model job already downloads/verifies the original source ZIP and two source receipts, exports and validates one authentic 2026 GLB, runs the original two-player source scorer and Chromium. This stacked branch adds **one source-score step**, retaining the report with the same real model artifact. The standalone unit tests validate fixed experimental arms, authentic timeline completeness, exact source alpha shape grouping, temporal edge comparison and exclusive no-overwrite output. **Only actual GHA execution at the final changed head qualifies original ROM/GLB results.**

Dependency order: existing exact #2832 2026 source model → #3101/#3115 mechanical controls → #3116/#3117/#3118 authentic source comparisons → #3119 neutral 2026 part census → #3120 source-registered real parent attribution → #3121 independent authored saddle pitch → this source-timeline generalization. Keep original ROM evidence, current 2026 model hypothesis, and owner-approved art completely distinct. Independent source/geometry reviewer required before merge.
