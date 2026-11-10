# Rainbow 3D-key-art wordmark: front-face vector tracing

**Status: working research/art asset, not approved canonical promo artwork.** This folder does not alter `assets/promo/canonical/`.

The source is the 1536 × 1139 user-provided raster shared 2026-11-07. Its original source format and camera/perspective parameters are unknown. The source image itself is not embedded in these SVGs or stored here.

- `uniracers-front-faces-source.svg`: source-aligned Bézier tracing of the nine *visible foremost coloured planes*, in the raster's original pixel coordinate system.
- `uniracers-front-faces-rectified.svg`: separately editable, projectively adjusted version of the same nine paths.
- `uniracers-front-faces-comparison.svg`: visual review of source and corrected geometry on dark background.
- `uniracers-front-faces-registration.svg`: thin green outlines in 1536 × 1139 source registration for overlay on the supplied image.

The traced shapes are **U N I R A C E R S**; the two Rs are `R1` and `R2`. Shapes are individually editable, with transparent internal counters in R1, A and R2. The first tracing is a careful manual interpretation of foreground boundaries, not an automatically proven pixel-perfect extraction, original production vector, or a font match. The solid per-letter fills approximate the dominant face colour; gradients, gloss, extrusion, sidewalls and black drop shadows are intentionally omitted. This particular reference does not show a separate spiral, TM or asterisk.

## Perspective correction

The original SVG is deliberately left untouched. The corrected version transforms each Bézier anchor and control point by a weak projective mapping:

```text
p = (1 - 1/1.05) / (317 - 48)
q = 1 / (1 - p * (317 - y))
x_corrected = 763 + (x - 763) * q
y_corrected = 317 + (y - 317) * q
```

At the reference top line `y=48`, that recovers about 5% of apparent shrinkage; the baseline `y=317` remains fixed. The S descends below the baseline intentionally. Transforming control points is an approximation of the projectively warped cubic curves; it remains clean, editable, and suitable for modest corrections.

**Limitations:** The true 3D tilt, lens, and original 2D glyph geometry cannot be uniquely recovered from this single rendered image. The corrected version is a conservative proposal for owner visual comparison, not a claim of canonical typographic approval. Further manual edge adjustments are expected wherever source pixels are ambiguous.

## Verification

All SVGs use SVG vector paths without embedded bitmap data; the source and corrected files each contain nine paths with stable glyph IDs. The source tracing was visually checked as a registered overlay on the supplied raster, and the files were parsed and rasterized locally. No release or visual-art approval gate is changed by this commit.
