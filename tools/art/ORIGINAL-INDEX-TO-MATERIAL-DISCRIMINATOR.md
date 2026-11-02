# ART-4K: source-index to GLB-material attribution discriminator

Status: **experimental research plan, not a recovered 1994 part mapping**. Builds on merged #3056 (reversible viewer material hypotheses) and #3057 (authenticated original 4bpp census).

## Fixed evidence and testable question

The 59 authenticated source representations collapse to 41 RGBA images, 35 silhouettes, and 35 original palette-index planes. All six colour-variant silhouette pairs retain exactly the same index plane. The frozen census and source hashes live in `analysis/data/racer-original-4bpp-index-census-summary-20261102.json`. No inference below treats repeated representations as independent observations.

**Question:** can one or more stable 4bpp index-region assignments be associated with independently identified 2026 GLB mesh materials across source poses, without using the 2026 mesh to relabel the original evidence circularly?

## Mechanical experiment

1. Load the authenticated original 4bpp source producer, preserving index-zero visited/untouched distinction and every tied wheel-centre hypothesis. Validate ROM, historical registry, PNG manifest and full-report SHA before any inference.
2. For each of 35 unique index planes, create one binary mask for each index 1..15, plus transparent visited-zero and untouched masks. Retain source pose IDs and colourway membership. Export **numerical descriptors only**: area, centroid, covariance/principal axis, bounding box, 4-connected components, perimeter, radial distribution relative to *each* tied wheel-centre hypothesis, and adjacency graph to other index masks.
3. Normalize source poses using independent silhouette geometry. Do not align based on the GLB material colours or a guessed wheel-part label. Quantify descriptor stability across pose families and the six index-identical colour variants.
4. Render each of the five existing GLB parts as a distinct *ID mask* in every available pose, using a fixed projection, transparent background, disabled lighting, nearest-neighbour rasterization, and independently frozen camera parameters. Never infer material IDs from WebGL RGB pixels. Keep the original GLB geometry/material bytes immutable.
5. Generate candidate assignments between index masks (or connected subregions, because one index can cover several physical parts) and GLB ID masks. Evaluate exhaustive small assignments or deterministic beam search with fixed seed, explicit split/merge penalties and no per-pose manual tuning.
6. Score each candidate across held-out **pose families**, not random pixels or repeated colourways. Report silhouette IoU, boundary F-score, centroid displacement, temporal consistency, index-to-part ambiguity, and margin over a permutation/null baseline. Report wheel-centre uncertainty as an interval across tied centres.
7. For the six palette variants, run an index-stability negative control: changing the colourway must not change index-plane identity, source index descriptors or fitted part assignment. Independently vary the viewer's three reversible material-colour hypotheses and verify that *geometry-ID masks remain bit-identical*.
8. Produce a sortable ambiguity table: index, candidate part, supporting poses, contradictory poses, score interval, null baseline, and explicit `unresolved` outcome. Never force one-to-one labels. Distinguish index-plane evidence from the semantic 1994 OAM/OBJ part identity, which remains unverified.
9. Before claiming source anatomical attribution, require an **independent** original OAM/OBJ/palette-trace witness at known frame/pose, and check the recovered mapping on held-out original frames. Before claiming a recovered camera or animation chronology, require separate PPU timing/pose-sequence evidence.

## Admission gates

- Authenticated source hashes and 59/41/35/35 counts are exact.
- No GLB geometry changes, default material changes, or publication/deployment side effects.
- Source and GLB masks are stored in separate namespaces with explicit provenance; no self-confirming matching labels.
- A held-out family with insufficient correspondence yields `unresolved`, not a guessed label.
- Synthetic controls cover index reuse across two parts, multiple indices within one part, palette-only recolouring, tied wheel centres, missing pose, and nonblack transparent palette zero.
- Publish only a bounded numerical summary and reproducible command, never a claim of approved likeness.
- No Windows build or release QA gate is altered by this research.

## Next implementation slice

Implement a ROM-free descriptor/assignment module with synthetic fixtures first, then source-authenticated 35-plane descriptor production and GLB ID-mask generation. Keep the two producers separate so that their independent provenance can be inspected before matching. Reuse existing viewer and pose exporters rather than creating another renderer.
