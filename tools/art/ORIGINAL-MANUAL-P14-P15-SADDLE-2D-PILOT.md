# Two visually estimated original 1994 printed-saddle silhouette examples

This file reports the first *actual source-figure pixel coordinates* from the authenticated and visually inspected 1994 official USA manual rather than a proposed 2026 3D mesh. The source is the tracked PDF Git object `a52da4f94a75e3e76fd61a759cb8e0c3a4fbc5d3`, PDF SHA256 `50d5d02a3f8f04b9a38a1dac7ff05fd96f5583fbdf1d0afc201bbaea454e2235`. Actual source crops were first rendered, RGB replay-validated, and retained in successful [GHA run #42125657977](https://github.com/gamesbyian/UR-Recomp/actions/runs/42125657977). Original printed image bytes are not copied into Git.

The numerical annotations in `analysis/data/racer-original-manual-saddle-estimates-20261105.json` are **approximate GPT-6 visual readings from those exact rendered PNGs**, not independently reviewed artist landmark picks. Uncertainty explicitly allows blurred shading, boundary ambiguity and antialiasing, and the two perspectives are **not calibrated as the same production 3D camera, lens, pose, scale or mesh**.

| Printed figure | View | Saddle 2D image-plane width | 2D height | Visual-coordinate uncertainty |
|---|---|---:|---:|---:|
| p14 `p14-twist-fork-front` | Near-frontal | 154 px | 66 px | ±8 px per marked point |
| p15 `p15-mega-underside` | Low oblique/underside | 318 px | 273 px | ±14 px per marked point |

The measured apparent 2D width-to-height changes from **~2.33 to ~1.16** across these independently published print compositions. The source art therefore strongly cautions against matching a single flat saddle silhouette by physically stretching one 3D plane. **These numbers do not prove the original 1994 saddle's 3D dimensions, model consistency, perspective, surface topology or camera.** The original PNGs have very different full-figure scales, and one view includes severe shading/overlap.

Only the saddle outline group has all four estimated landmarks. For the wheel, hub, crown, fork, clamp, and crank, parts may be visible but individual complete bounding groups are occluded, cropped or overlapping, so every other source part is explicitly marked `unmeasurable`, not filled with imagined coordinates. There is no complete visible wheel in these two views; normalisation to true wheel diameter is **null**. The source image aspect is **square PDF scan pixels**, not SNES source 7:6 pixels.

## Qualification boundary

The existing PR-scoped/on-demand GitHub Actions manual-source workflow now does the entire source trace: run the strict exact-PDF/PNG crop rendering and RGB replay from #3166/#3170, apply these exact printed-pixel estimates to the retained original source manual, emit the authenticated numerical report `p14-p15-saddle-observations-2d.json` into the temporary artifact, and verify all 3D-camera/model/owner likeness/shipping gates remain false. The pure stdlib tests preserve the exact source crop hash, original 2D coordinates and explicit observational uncertainty; optional PyMuPDF/Pillow test exercises the real on-disk source PDF, not only a mocked image.

This is an **in-sample, visually estimated observational pilot**, not independent artist signoff or a blinded source reconstruction benchmark. Its main value is to establish a reliable path from genuinely observed, perspective-tagged **2D original print geometry** toward a single source-owned **3D saddle mesh** hypothesis, instead of applying unrestricted changes to the unapproved 2026 GLB based on screenshots. The current original game source frames, five-parent/16-material 2026 draft #2832, mainline Pages inspector, and all Windows/ART acceptance gates are unchanged.
