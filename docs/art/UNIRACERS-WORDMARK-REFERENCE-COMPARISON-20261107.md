# Uniracers box wordmark: dual-reference reconstruction (2026-11-07)

## Purpose and current asset

The working vector asset [`assets/branding/uniracers-box-wordmark-traced.svg`](../../assets/branding/uniracers-box-wordmark-traced.svg) has been rebuilt from **two separate, recent high-contrast artwork references**, replacing the prior independent raster-traced Bézier contours that retained wobble, bulges, and awkward inflections. This is a **candidate reconstruction for owner art review**, not a recovered 1994 vector master or release/art approval.

Both independently reconstructed sources are preserved, with an editable SVG for each:

- [Reference A](../../assets/branding/reference-traces/uniracers-wordmark-ref-a-20261107.svg): user-supplied `1000022735.png`, SHA-256 `4e5dfa9f880a88d6aeea03dcd707e85f9b53200f0c8c59f6ff2d2c60bffea603`.
- [Reference B](../../assets/branding/reference-traces/uniracers-wordmark-ref-b-20261107.svg): user-supplied `1000022738.png`, SHA-256 `ac79167f4cf5ea683309e91bfbe9f1f6cae472829185b91c252c65103d70095d`.
- Geometric registration anchor: earlier packaging image `1000022665.png`, SHA-256 `e682c9a83fefc833b63543bc105c4e5ec61bc7ab2547f54f987da935e9d63769`.

The two uploaded reference illustrations are independent renderings but **not** independent historical master art or proof of artist intent. Source image files were used for analysis, not embedded in the SVGs.

## Method

1. Isolate the yellow foreground separately in each 1536-wide reference. Identify the nine letter faces and detached spiral as ten components; exclude multicolored tubing, promotional art and print noise.
2. Bring each image into the earlier box-art coordinates using a lightweight affine registration of corresponding component centroids. Reference A approximates x scale **1.01006**, y scale **0.99446**; B approximates x scale **1.00018**, y scale **0.99501**. Residuals stay near 2 source pixels or less.
3. Fit each contour independently as a **closed periodic cubic B-spline**. Convert knot spans to true cubic Bézier paths, maintaining continuity of position, slope and curvature at joins rather than using visibly segmented line tracing.
4. Form a third working master from the average **signed-distance fields** of the aligned foreground masks, then fit that contour to a new smooth set of closed cubic curves. Do not average unregistered control points or automatically choose one scan wholesale.
5. Render the face *and* dark border from precisely the **same ten vector contours**. The backing uses a rounded 10 px stroke translated (+2,+2) source pixels; the foreground face covers it. The small TM and six-spoke asterisk remain from the earlier curated trace.

The original distinct letter proportions, loop shapes, narrow interior cuts, spiral direction, and letter order are maintained. No typeface substitution, creative redesign, raster embed or auto-generated 3D extrusion is involved.

## Measured comparison

The area Intersection-over-Union (IoU) below compares yellow faces only after rasterizing both SVGs onto the same 1536×1152 source-pixel canvas. Because the reference scans are not the original vector artwork, these numbers quantify *agreement between candidate interpretations*, **not** historical fidelity, and should not outweigh direct visual review.

| Comparison | Yellow-face IoU |
|---|---:|
| Independent A vs B | 94.27% |
| A vs new consensus | 96.18% |
| B vs new consensus | 96.86% |
| Previous master vs A | 92.33% |
| Previous master vs B | 93.41% |
| Previous master vs new consensus | 93.52% |

Per-glyph **A–B agreement** after independent fitting:

| Element | IoU | Review note |
|---|---:|---|
| u | 94.8% | Terminal roll and left/right widths |
| n | 94.0% | Shoulder transition and inner opening |
| Spiral | **79.6%** | Largest uncertainty; whorl thickness and turn differ between references |
| i | 94.6% | Slender stem and rounded ends |
| First r | 95.7% | Preserve deliberately pinched top notch |
| a | 94.2% | Preserve the distinctive inner curl and acute return |
| c | 95.6% | Open mouth and terminal form |
| e | 95.3% | Inner spiral-to-open-bowl transition |
| Second r | 94.9% | Top cleft and trailing stem |
| s | **91.4%** | Lower bend and upper inside terminal remain worthy of visual review |

Shape validations run locally: all **30 closed glyph contours** in the two independent candidates and consensus sampled as valid, non-self-intersecting polygons; SVG/XML parses; all three SVGs render; open components and relative placement remain stable. The consensus master uses **147 cubic Bézier spans** over ten contours. More spans do not mean rougher paths here: all are constructed from joined periodic splines with continuous derivatives. The independent fits use 154 and 151.

## Review priorities and limits

Inspect the *spiral first*, because it is materially less consistent across source references than the nine letters. Then compare the `s` bottom and upper-hook transitions, followed by the `a` return, the `u` inner bend, and the first `r` notch. These are deliberate high-curvature features that a global smoothing filter can erase. The earlier default path remains available through Git history if any detail must be reinstated. Do not infer owner approval, release readiness or 1994-authored vector control points from smoothness, topology checks, IoU, or a successful Git merge.

## Follow-up: localized spiral and final `s` curvature review (2026-11-08 UTC)

This is a **small, reversible artistic refinement**, based on the original packaging crop and the two independent high-contrast references above. The previously accepted A/B consensus for the other **eight** paths remains byte-for-byte unchanged.

- **Spiral:** retained the existing consensus outer sweep and adjusted only control points around the inner yellow tongue, replacing its nearly vertical-looking inward drop with a gentler rounded turn. The neighboring cubic handles were constrained to preserve the entering and departing tangent directions. The spiral remains a simple closed shape with 14 cubic spans.
- **Final `s`:** used the independently fitted Reference B path in place of the averaged path, as its upper terminal and lower inside bend look smoother in the original artwork comparisons. This uses 15 rather than 14 cubic spans.
- The border still comes from one shared path group rendered twice, using the **10 px rounded stroke** behind the face translated **(+2,+2)**. The TM and six-spoke asterisk are untouched.

### Independent checks and tradeoffs

All ten paths were sampled at 80 points per cubic span and verified to form valid, non-self-intersecting, exactly closed shapes. The largest join-direction discrepancy in the resulting SVG was **0.0356 degrees**, with the spiral itself below **0.019 degrees**. These are tangent-direction tests, not absolute claims about the original artist's control points.

Yellow-face IoU for the two changed glyphs, measured against registered reference masks and the older printed packaging crop:

| Glyph | SVG | Reference A | Reference B | Printed original |
|---|---|---:|---:|---:|
| Spiral | Previous | 78.67% | 84.42% | 76.08% |
| Spiral | **Revised** | **79.32%** | 84.06% | 75.55% |
| `s` | Previous | 93.64% | 92.67% | 93.33% |
| `s` | **Revised** | 92.77% | **93.91%** | **94.05%** |

The numbers show tradeoffs, **not a universal improvement**. The spiral's printed-original raster overlap decreases slightly while the inner tongue becomes visually rounder; the `s` is closer to Reference B and the printed original but slightly farther from Reference A. Do not optimize a noisy raster-IoU score at the cost of smooth intended geometry.

Original references A and B remain available unchanged in `assets/branding/reference-traces/`, and earlier consensus is recoverable from Git history. This refinement is still a **candidate for human likeness review**, with no new original-master provenance, owner sign-off, Windows release acceptance or QA-gate claim.


## Follow-up: curvature-adaptive cover-art refit (2026-11-08)

**Owner feedback:** although the prior SVG passed C2-join tests, several contours looked visually wonky compared with the cleaner box-art illustration. Tangent continuity alone is insufficient: the actual radii, terminal proportions, inflection locations and relative widths must be correct.

### What changed

The foreground contours were re-estimated directly from supplied high-contrast `1000022738.png`, verified against independent `1000022735.png` and earlier `1000022665.png` art. The revised master takes **nine letter paths** from a curvature-adaptively filtered, periodic cubic reconstruction. The **previous manually reviewed spiral is deliberately preserved** because reference-to-reference spiral disagreement remains substantially higher than letter disagreement.

The contour refit applies roughly 2 source pixels of Gaussian filtering around intentional tight turns and up to 6 pixels along gentle, low-curvature stretches; a smoothly varying curvature weight controls the transition. A regularized periodic cubic fit then removes pixel-level wiggles without forcing tight notches and broad body curves through the same smoothing filter. In trial runs, applying indiscriminate stronger regularization to entire letters visibly blunted the first `r`, `a` and `e` features and reduced raster agreement. **The final SVG has more Bézier spans (173 across ten components), not fewer**, because a low control-point count alone is neither a smoothness guarantee nor a fidelity objective. Those spans have matched tangents, and visible high-frequency contour noise is reduced.

The black border still uses the **exact same vector source** as the yellow faces, translated (+2,+2) with a 10 px rounded stroke. The small `TM*` now has its **own black outline** as in the supplied clean packaging illustration; the T/M and six-spoke star remain editable vector shapes. No raster is embedded.

### Bounded checks

Masks were rasterized at 1536 × 1152 in a shared registered coordinate system. Yellow-face overlap (IoU) was:

| Reference | Before | After |
|---|---:|---:|
| Alternate cover A | 92.93% | **93.02%** |
| Clean cover B | 92.97% | **94.21%** |
| Earlier printed packaging | 92.38% | **92.92%** |

The after values use the full proposed SVG, with the preserved spiral and outlined TM. The measured improvements are modest and **do not constitute owner artistic acceptance** or a recovery of 1994 master vectors. Raster IoU cannot distinguish intended vector geometry from coincidentally matching printing/antialiasing artifacts. All ten sampled closed letter/spiral contours were topologically valid with no self-intersections; cubic join tangents deviated by at most **0.037°** in local validation. XML parsing and CairoSVG rendered both transparent and composited previews.

**Next artistic review:** scrutinize the `a` lower return, the first `r` upper pinch and the `e` inner terminal at high magnification, alongside the earlier spiral uncertainty. Further edits should be localized and backed by cross-reference visual comparisons, avoiding another global blur/fit cycle. Release, 3D character likeness and historical-original-geometry acceptance remain unchanged.


## Follow-up: constrained a/e/spiral curvature revision (2026-11-08 UTC)

The user continued to identify rounded edges that were technically continuous but still aesthetically lumpy compared with supplied clean box art. This pass edits only **three** source paths in the existing canonical wordmark SVG, leaving `u`, `n`, `i`, both `r`s, `c`, `s`, the diagonal stroke construction and outlined `TM*` unchanged.

- **a:** source-aware contour relaxation on the lower return and upper inner bend, retaining the hooked terminal. 26 to **25** continuously joined cubic segments.
- **e:** refit of the inner curl and bowl with a stronger broad-curve smoothness prior. **15** cubic segments before and after.
- **spiral:** round-trip to a periodic cubic spline, replacing the earlier localized hand-edit's curvature breaks with a continuous-curvature path. **14 to 18** cubic segments. More segments are needed to preserve the tight inner turn without angular jumps; this does not imply adding visual waviness.
- All three paths are closed, valid, non-self-intersecting polygons when sampled at 100 points per cubic span. All ten original letters and spiral remain present; the backing outline continues to reuse these same yellow-face paths with a 10-pixel rounded stroke displaced (+2,+2).

### Source comparisons

For the clean reference `1000022738.png`, yellow-only Intersection-over-Union using connected-component segmentation in source-pixel coordinates:

| Glyph | Prior SVG | Revised SVG |
|---|---:|---:|
| a | 93.57% | **95.14%** |
| e | 94.20% | **96.24%** |
| Spiral | 85.47% | **88.76%** |

The spiral also improves overlap against the earlier `1000022665.png` source (78.69% to **81.83%**), although it drops modestly against alternate reference A `1000022735.png` (62.05% to **61.30%**). This is a recorded source tradeoff, not suppressed disagreement. The two cover-image reproductions diverge particularly strongly in the tiny spiral, and direct visual review remains the art authority.

Unlike the earlier spiral path, whose sampled join-curvature discontinuity reached roughly 0.164 inverse source pixels, the revised spiral's maximum sampled absolute curvature jump is below **0.0007** inverse source pixels. The `a` and `e` remain similarly smooth at their joins (below 0.0004). The curvature units are defined by the input SVG's original-pixel coordinates, so they should not be compared to 3D rig curvature.

**Validation limits:** These checks confirm source/reference alignment, polygon topology, SVG renderability and differential geometry, but do not prove that the printed 1994 contours are exactly recovered. The clean cover reference may also contain its own redraw or restoration errors. Do not count this as owner art acceptance or any gameplay/release QA gate.
