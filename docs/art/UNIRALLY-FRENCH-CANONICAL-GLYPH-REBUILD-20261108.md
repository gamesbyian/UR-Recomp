# French parody title, rebuilt from the canonical Uniracers alphabet

**Artwork:** [`assets/branding/unirally-french-wordmark.svg`](../../assets/branding/unirally-french-wordmark.svg)  
**Title:** `l'inéluctable esseulement de la roue unique.`  
**Status:** Original owner-directed French arthouse parody, visual review candidate. Not a historical French release name.  
**Date:** 2026-11-08.

## Purpose and design

The owner preferred a much funnier French wordmark that obviously **recycles the established Uniracers/Unirally hand-drawn glyphs**, rather than looking like a completely separate decorative typeface. All lettering is lowercase, with the apostrophe, acute accent, word spacing and terminal full stop preserved.

The phrase is broken into three centered lines for visual balance:

> l'inéluctable  
> esseulement  
> de la roue unique.

This grouping emphasizes the absurd melodramatic title while remaining readable at ordinary viewing sizes.

## Shape provenance

All reusable letterforms are the **exact original approved vector `d` data**, not stylistic redraws or font substitutions:

- `u n i r a`: the six-glyph normalization master shared by both English wordmarks.
- `c e s`: the owner-approved Uniracers wordmark's exclusive characters.
- `l`: the owner-approved first `l` in the PAL Unirally wordmark.
- **30 of 37 visible letters**, including the `e` in `é`, reuse these precise canonical contours.
- The two dots above `i` use the separately supplied shared original box-art **spiral silhouette**, with the established lighter border styling.
- Six **new** lowercase letter designs were needed: `b d m o q t`. The title uses seven occurrences of those new designs because `t` appears twice. New shapes were drawn as filled cubic Bézier outlines to harmonize with the originals' rounded termini, uneven but deliberate strokes, single-story `a`, and hand-lettered curvature.
- The apostrophe, acute accent and final period are new small editable vector shapes. They are not font-glyph placeholders.

The artwork uses only local SVG `<path>` definitions and `<use>` instances, with **translation and uniform scale** for every appearance. No distortion of the canonical contours, no external images, no fonts and no embedded raster. Each reused glyph can be identified by its `shape-` definition. The canonical shared masters are *copied into the stand-alone SVG* so the file renders directly in GitHub without cross-file references.

## Colour, borders and validation

Exactly matches the English logo palette and border recipe:
- Yellow faces: `#ffea00`.
- Main black: `#090409`, with 8-unit offset stroke at (+2,+2) and centered 2.4-unit keyline.
- Spirals: original 5-unit offset black stroke at (+1.25,+1.25), centered 1.5-unit keyline.

The previous French vector (based on an unrelated decorative typeface) remains available in Git history, but this new artwork is the canonical French parody at the same repository path.

Run `python3 tools/verify_french_wordmark_glyphs.py` to verify that all imported `d` strings match the current English masters, both spirals match the current source, all placements are uniformly scaled, the title contains the exact lower-case phrase and all stroke values remain normalized.

A human should compare the finished graphic at normal viewing size against the game's two English box-art logos, not optimize against scan noise. Final artistic acceptance still belongs to the owner. No gameplay, release or QA gates are changed.
