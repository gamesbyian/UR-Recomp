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

## Implemented bounded tools and evidence (November 2, 2026)

This PR now contains executable, independent source index topology (`tools/art/index_region_descriptors.py`), depth-tested, scene-parent-labelled 2026 GLB ID rendering (`tools/art/glb_parent_part_id_raster.py`), conservative held-out 2D correspondence scoring (`tools/art/score_index_glb_parts.py`), and a real-ROM corpus adapter (`tools/art/audit_original_index_regions.py`), each with dedicated synthetic adversarial tests.

**Real original source:** [run #41550316932](https://github.com/gamesbyian/UR-Recomp/actions/runs/41550316932) completed the canonical USA ROM + exact historical registry + frozen 41-PNG source re-execution with the NEW region adapter. It verified 59 representations, 41 RGBA, 35 binary silhouettes and exactly 35 index planes. [Artifact #13190178539](https://github.com/gamesbyian/UR-Recomp/actions/runs/41550316932/artifacts/13190178539) contains the actual 35-plane numerical topology JSON, SHA-256 `7c00ccbb1e7e2ebc50fa51702d22305dd77c070a5ae03e7f8ef8edfe05febdc3`, expiring November 10, 2026. The same index-region summaries were independently reproduced offline from archived source PNGs and checked against all 41 actual ROM-producer index-plane and tile-written-mask SHA values. Region 7 illustrates why a palette index cannot be called one physical part: 486 source pixels across 35 unique planes form 285 separate 4-neighbour components, 353 pixels inside the source 2D wheel-disc hypotheses.

**Actual experimental model:** an offline run of the prototype GLB parent-labelled renderer against the original published five-pose artifact #13063969312 produced nonempty source-centre ID masks for upright, pedal, wheelie, stunt and bank. A second, independent silhouette renderer matched each full 256×256 depth-assembled ID-mask silhouette with **zero XOR pixels** (4,358 / 4,316 / 4,346 / 4,301 / 4,371 pixels in pose order). Hashes for each source GLB and the corresponding 64/256px ID planes are in `analysis/data/racer-source-index-and-model-part-evidence-20261102.json`; these 2026 GLBs are procedural and remain *unpaired* to independently witnessed 1994 poses.

**Commands:** use `python3 -m tools.art.audit_original_index_regions --rom ... --registry HISTORIC_REGISTRY --source-zip FROZEN_CORPUS.zip --out NEW_NUMERICAL_REPORT.json` for authenticated source evidence; use `python3 -m tools.art.glb_parent_part_id_raster --glb HASHED_POSE.glb --glb-sha256 SHA --camera analysis/data/racer-inverse-side-provisional-1205.json --out NEW_ID_RECEIPT.json` for independently projected GLB parts. The scorer `propose_index_part_correspondence` in `tools/art/score_index_glb_parts.py` accepts only pairings with an explicit alignment witness, holds out entire original pose families, rejects duplicated colourways, tests a fixed spatial-shift negative control, and may return `unresolved`. **No real original-to-GLB pose pairing is admitted at this milestone.**

The one-off original-source workflow steps used to produce the receipt were restored to the original opt-in workflow after completion. No new recurring CI or platform path, no default geometry/material changes, no 1994 OAM/OBJ/PPU part truth, and no art/release gate credit.
