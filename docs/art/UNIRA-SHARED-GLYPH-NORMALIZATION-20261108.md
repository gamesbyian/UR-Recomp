# Canonical `unira` and spiral shapes in the two box-art logos

**Date:** 2026-11-08  
**Status:** Vector normalization implemented; owner has final visual acceptance authority.  
**Affects:** Art assets only. No gameplay or release gate.

## Contract

The Uniracers and Unirally box designs are taken to have used the **same six intended shapes** for the first five letters `u n i r a` and the separate spiral above the `i`. Differences from scanning, printing and restoration must not cause two distinct letter geometries to persist in the repository.

- Shared master: [`assets/branding/shared/unira-shared-glyph-master.svg`](../../assets/branding/shared/unira-shared-glyph-master.svg)
- Uniracers: [`assets/branding/uniracers-box-wordmark-traced.svg`](../../assets/branding/uniracers-box-wordmark-traced.svg)
- Unirally: [`assets/branding/unirally-box-wordmark-traced.svg`](../../assets/branding/unirally-box-wordmark-traced.svg)

The six canonical paths (`shared-u`, `shared-n`, `shared-i`, `shared-r`, `shared-a`, `shared-spiral`) have **identical `d` strings in all three SVG files**. Each wordmark embeds its own identical copy of the definition so viewers can render it without external SVG references. Glyph placements use SVG `<use>` with **translation and one uniform scale only** (no nonuniform stretch, rotation or independent retracing).

The five letter contours are taken from the owner-selected Uniracers interior source, which the owner identified as satisfactory in its actual letter shapes. The spiral is the separately owner-provided single closed path from `assets/research/uniracers-box-art-i-spiral-interior.svg` (branch `art/uniracers-boxart-spiral-interior-20261108`, when available), as pasted directly into this conversation. Its original-coordinate `d` string is retained exactly. Source artwork attribution: the spiral trace identifies packaging PNG SHA-256 `d714d8a78e1df7460e088f91c0a73f31cd28e845b75a2db9c07713b755f054ec`.

## Preserved differences between the wordmarks

| Shared or unique element | Uniracers presentation | Unirally presentation |
|---|---|---|
| `u n i r a` | Canonical geometry, original large-cover arrangement | The **same** geometry uniformly rescaled and moved to PAL cover positions |
| Spiral over `i` | Exact newly provided canonical spiral, scaled to its former dot location | The **same** exact spiral, scaled to PAL dot location |
| Remaining letters | Original owner-approved `c e r s` | Original owner-provided `l l y` |
| Border | Letter bodies: yellow `#ffea00`; black `#090409` 8-unit stroke offset (+2,+2), plus centered 2.4-unit black keyline. Spiral uses **5-unit offset stroke at (+1.25,+1.25) and centered 1.5-unit keyline** | Identical |
| Trademark | Original separate small `TM*` vector treatment retained | No trademark added in this glyph-normalization change |

The baseline shared letter positions and heights are retained approximately from each existing canonical SVG. To ensure undistorted glyph shapes, width is an outcome of **uniform height-matched scaling**, rather than a forced fit to the former scan-derived width. This can shift a few horizontal pixels; that is preferable to introducing an artificial second geometry. The original per-wordmark non-shared shapes and composition remain independent.

## Regression guard and validation

Run `python3 tools/verify_shared_wordmark_glyphs.py`.

The standard-library-only guard checks:

1. Exactly matching six path-data strings in the master and both wordmarks.
2. Every shared glyph is an actual SVG `<use>` of the matching shared definition, with **translation plus positive uniform scale**.
3. The displaced black outline, centered keyline and yellow face each use the same group of letter contours and have matching colour/stroke settings.
4. The supplied spiral's starting coordinates remain present.

After editing **any** of the six glyph contours, update the library **and both self-contained SVGs together**, run the guard, and inspect both logo renders at 1× and magnified scale. Do not independently smooth the shared `unira` letters in one wordmark or reintroduce raster-specific divergence.

**Limit:** This guarantees source-vector identity of the shared shapes, not proof of the original 1994 control points or automatic visual signoff. Human-scale likeness against both original boxes remains the objective. Prior art research and divergent independent traces remain recoverable from Git history.


## 2026-11-08: lighter spiral border (presentation-only change)

Owner review identified the spiral as having **disproportionately heavy black edging** compared with the letter bodies. The fine spiral whorl is much narrower than a full letter stem, so treating both with the same 8-unit stroked underlay crowds the spiral's inner curl.

The correction applies **identically to Uniracers and Unirally**, preserving the exact `shared-spiral` `d` string and all five shared letter source paths. The spiral's own wordmark instance (`i-spiral-dot` or `i-spiral`) now lives in a separate `spiral-contours` group in `<defs>`, but still uses `href="#shared-spiral"` and its unchanged uniform-scale placement transform.

- Letter bodies: unchanged 8-unit black rounded stroke at (+2,+2), unchanged centered 2.4-unit keyline, yellow face `#ffea00`.
- Spiral: black rounded stroke reduced to **5 units**, offset (+1.25,+1.25); centered black keyline reduced to **1.5 units**; same yellow `#ffea00` face.
- Black remains `#090409`, and all three spiral layers are composed from the same shared spiral master path, without any independently traced outer/inner shape.
- Dedicated shared-spiral regression tests now verify separate compositing, exact styling equality between wordmarks, and no drift of the six canonical source paths.

This is a **visual-weight correction**, not a change to the canonical geometry. Rendered variants at 8/6/5/4.4 black-stroke units were compared at enlarged scale, with 5 units selected to retain a clearly readable offset edge without swallowing the inner yellow turn. Final owner judgment of border aesthetics remains appropriate. No gameplay/release qualification effect.
