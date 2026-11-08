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


## Focused spiral and `i` correction (2026-11-08)

The owner specifically requested more attention to the spiral and the `i` after the previous localized `a`/`e` work. This iteration edits **only those two closed yellow-face contour paths**, with all other glyphs and the TM/asterisk left unchanged.

- **`i`**: refitted its cap, left stem and bottom oval against the cleaner box reproduction, reducing a subtly swollen lower stem and improving consistency of the long sides. The candidate uses **13 periodic cubic segments** and has a sampled adjacent-join curvature jump below **0.00003 inverse source pixels**.
- **Spiral**: preserved the overall spiral turn while rebalancing the inner tongue and rounded lower terminal against the clean source. Uses **20 periodic cubic segments** with sampled maximum adjacent-join curvature jump below **0.00039 inverse source pixels**. The contour stays a single continuous shape with no fill holes or self-intersections.
- **Outline**: shared paths rendered as black 10 px round stroke translated (+2,+2) under the yellow face. There are no independent manually traced border paths.

The yellow-only source-mask overlap (IoU) against the clean cover illustration `1000022738.png` changes from **94.97% to 97.39%** for the `i` and from **88.76% to 90.24%** for the spiral. Agreement with alternate reference `1000022735.png` changes from **83.45% to 83.37%** for the `i` and **61.30% to 60.68%** for the spiral. The alternate-reference tradeoffs remain visible and documented. Source images may be modern restoration/redraws, so none of these numbers prove true 1994 vector fidelity.

The candidate was rendered in context on a charcoal preview and separately compared beside previous SVG and clean cover, at the same crop and scale. Both updated glyphs were sampled to valid, positively oriented, closed, non-self-intersecting polygons. This is an artistic review candidate, not an owner-approved final logo and not a release gate.


## Follow-up: broad-curve cleanup of `u`, `i`, second `r`, and outer `n` leg (2026-11-08)

In response to owner review of lingering *waviness*, this pass edits only the requested four contours. It deliberately freezes the first `r`, `a`, `c`, `e`, `s`, spiral, TM/asterisk, and the single-source black-border offset, avoiding another global smoothing pass.

- `u`: replace 19 periodic cubic spans with **18**, regularizing long descending/returning edges rather than blurring both rounded ends.
- `i`: replace 13 with **11** continuous spans and simplify its long stem while protecting its cap, lower oval, and original slope.
- Second `r`: retain **18** spans while smoothing its sidewalls and the transition into the long stem. The upper pinch/terminal remains.
- `n`: leave the shoulder, opening, left side, and inner right leg in their existing positions. Replace **three** short outer-right-leg spans with **two** broad cubic spans (23→22 total). The new segment is tangent-aligned with its neighbors, with join curvature constrained and maximal old-to-new contour displacement under **0.65 source pixels**.

The rounded black backing remains derived from the **exact same glyph paths** as the yellow faces, with the already accepted **10 px stroke** and **(+2,+2) px offset**. The other six face paths are unchanged.

### Checks and tradeoffs

The intended modest scale of revision is confirmed by maximum nearest-contour displacements: `u` 2.11 px; `i` 1.65 px; second `r` 2.23 px; `n` 0.64 px. All ten paths remain valid closed polygons after dense sampling, with no detected self-intersection or endpoint gaps. Maximum sampled adjacent curvature jumps for the four changed contours are all below **0.0004 inverse source pixels**.

Against the clean cover reference `1000022738.png`, yellow-face IoU is:

| Shape | Prior | Revision |
|---|---:|---:|
| `u` | 95.75% | **97.26%** |
| `i` | **97.39%** | 97.05% |
| second `r` | 95.07% | **96.72%** |
| `n` | 94.85% | **94.89%** |

The small measured `i` decline is accepted provisionally in exchange for simplifying two Bézier segments and improving the subjective long-stem flow. Agreement against alternate reference A also declines slightly for the `i` and second `r`, so this does **not** claim universal fidelity improvement. Clean box-art raster measurements are evidence for review, not the 1994 editable vector master or owner artistic signoff.

The owner should compare the large-source crop to the exact revised SVG at ordinary viewing scale and 3× magnification before art acceptance. No ROM, gameplay, HD racer, Windows package, release QA gate or 3D geometry is affected.


## 2026-11-08: reconstruct the `u` and `n` as designed curves, not raster-bound fits

**Owner correction:** Earlier passes put too much importance on pixel-mask Intersection-over-Union (IoU) with cover scans, even while the owner identified lumpy, wavering letter edges. The intended finish is a smooth, coherent *vector design*, so for this revision **raster overlap is not the objective function, approval metric, or selection criterion**. The earlier IoU tables remain historical diagnostic evidence only.

Only the `u` and `n` path data change in the canonical `uniracers-box-wordmark-traced.svg`. This is a deliberate silhouette redraw, not another global blur/spline fit over the printed pixels.

### Construction

- **`u`:** rebuild both rounded cap transitions, long descending sides, inner horseshoe and outer bowl as a small set of intentionally shaped cubic arcs. Reduce from **18** cubic spans to **12**. Remove the meandering sequence of curvature changes along long edges, while retaining the letter's slant, width and general personality.
- **`n`:** reconstruct the two vertical legs, rounded bottoms, small top notch and broad shoulder as continuous designed sweeps. Reduce from **22** cubic spans to **16**. The notch is intentional; the ripples previously visible along the stems are not.
- Align adjacent cubic tangents, then regularize handle lengths to reduce abrupt curvature discontinuities, **without asking the curves to pass through every source-raster contour fluctuation**. The final candidate uses a moderate geometric-regularization weight selected by enlarged contour inspection.
- Preserve the other **eight** paths byte-for-byte, plus the existing shared-source black border with 10 px round stroke and (+2,+2) displacement, color palette, TM and asterisk.

### Validation and limitations

Both redrawn polygons remain closed, valid and non-self-intersecting on dense numerical sampling. The maximum sampled adjacent-tangent directional discrepancies are under **0.006 degrees**. Compared with the last master, the `u` face area changes about **−2.4%** and the `n` about **+2.5%**; this is the acceptable cost of removing raster-driven geometry rather than a pixel-error score.

The curves are tangent-continuous (geometric G1) at the Bézier joins but are **not claimed to be exactly curvature-continuous C2**: maximum sampled curvature jumps are about 0.0063 in source-pixel inverse units at the most tightly curved joins. The broad strokes and joins were inspected in a magnified before/after render and in the full wordmark. This is a new owner-review candidate rather than original 1994 control points or final art signoff.

**Future review criterion:** judge the quality of long arcs, consistency of stem widths, intentional terminal shapes and absence of unwanted inflections at multiple render scales. Do not reintroduce pixel-fitting merely to increase IoU. Release/gameplay QA gates remain unchanged.


## 2026-11-08: targeted `u` scoop, `a` curls, and black-outline balance

The owner noted three remaining artistic problems: the **right side of the `u` inner scoop**, unintended shape changes in the **`a`**, and patches of **inconsistent black outline weight**. This pass addresses only those, prioritizing smooth intentional curves rather than raster-mask overlap.

**Geometry changes**
- **`u`**: adjust the inner right wall and the lower-turn cubic handles together so the scoop flows continuously into its rising left edge, without the prior bulge/flat-bottom transition. Retain the 12-span designed `u` established by #3272. Only a localized portion of its contour changes.
- **`a`**: reshape the upper curl's inner side (removing an unnecessary sideways reversal) and the lower hooked return (removing the flat shelf). Refit neighboring cubic handles jointly for continuous tangent direction and nearly continuous geometric curvature. Keep 25 spans and preserve the overall `a` envelope.
- **All eight other source contours**, including `n`, `i`, spiral, both `r`s, `c`, `e`, and `s`, are unchanged byte-for-byte. The TM and asterisk also remain unchanged.

**Border construction**: the previous single 10 px black rounded stroke displaced (+2,+2) created very thin portions opposite the shadow direction and exaggerated weight on other sides. Replace it with two reusable, **path-derived** black layers beneath the yellow faces: (1) 8 px rounded stroke translated (+1.4,+1.4), then (2) a *uniform* 4.2 px centered black keyline. Both reference the very same glyph source paths, so no separate traced black silhouette or font text is introduced. The diagonal offset remains intentional but the keyline establishes a consistent minimum black edge, including around tight inside turns.

**Quality verification**
- Both changed glyphs use **closed, valid, non-self-intersecting** contours sampled at 100 points per cubic span. All ten existing glyphs likewise remain valid.
- Maximum adjacent cubic tangent-direction mismatch is approximately **0.086°** across the `u` and **0.016°** across the `a`. The optimized `a`'s targeted join-curvature discontinuity is below **0.0006 inverse source pixels**.
- CairoSVG successfully rendered the entire asset against neutral and transparent backgrounds. Enlarged side-by-side checks compared each corrected character with the previous SVG and the clean packaging reference.
- **No raster-overlap score was used to decide or qualify this change**; the criterion is coherent broad-curve shape and reasonable outline consistency.

The previous master is preserved in Git history. This remains a candidate for owner art review, not a recovered original editable vector file, owner sign-off, or any release/QA acceptance.
