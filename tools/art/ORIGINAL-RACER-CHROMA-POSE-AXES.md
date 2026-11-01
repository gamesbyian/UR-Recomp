# ART-4K original projected painted-axis pose constraints

**Status: source-authenticated 2D diagnostic, NOT reconstructed 1994 3D geometry, camera, pose pivot or owner likeness.**

The original USA ROM corpus has 91 source-frame observations, 59 registered representation IDs, 41 distinct RGBA PNGs and 35 unique binary masks across 27 registered source windows. The repository's existing strict original P1 red / P2 blue chroma classifier can describe image-space leaning directions without pretending any experimental five-pose GLB is a registered source animation state.

The new source auditor tools/art/audit_original_racer_chroma_axes.py reuses the exact existing classify_source_chroma red/blue RGB rule. It first independently authenticates the complete original-ROM corpus, rehashes actual PNG file bytes, decoded RGBA and each binary alpha mask at use time, then computes the centroids of the *top three and bottom three occupied player-colour raster rows*. Their bottom-minus-top horizontal distance is corrected by the original **7:6 SNES pixel aspect**. The resulting signed angle is measured from the 2D *image vertical*, positive for chromatic pixels extending rightward toward the bottom. Source endpoint centroids, occupied rows, colour-pixel counts and all input representation SHA identities remain explicit. This intentionally does not segment a source 3D fork, wheel pivot or original skeletal joint.

On the same already validated 41-source-PNG archive that generated the 35-shape atlas, an independent local colour-pixel calculation measured projected image-axis angles from approximately **-29.19° to +43.12°**. This includes near-vertical, negative and positive image-space slope states, but the majority of the newer red source images are very near-duplicate. A distinct original binary alpha mask is not automatically a distinct 3D pose or camera. Multiple player/palette variants sharing one exact alpha shape are recorded separately and the source mask still receives one aggregate vote.

## Reproduce without adding another build system

    python3 tools/art/audit_original_racer_chroma_axes.py --corpus /path/to/verified/source-corpus.json --out /new/immutable/source-chroma-axes.json
    python3 -m unittest tests.unit.test_audit_original_racer_chroma_axes

The existing optional ART-4K original-ROM holdout Actions workflow reuses the same original-source composition and validates this extra diagnostic in the same CPU job. A JSON numeric report is uploaded alongside the frozen 1.00× / 1.10× wheel-ablation and near-duplicate results, with no new recurring job and no GLB modification.

## Geometry implications

Future real pose work should pair registered original time sequences with these source-derived coloured-axis descriptors and separate dark wheel/saddle landmark tracks, then test a frozen projected-rig animation hypothesis against different source families. Do not equate a 2D colour-mask line with a physical unicycle fork, the true original wheel lean angle, 3D camera orientation or a source-authenticated mapping to the 2026 upright/pedal/wheelie/stunt/bank GLBs. The single draft #2832 rig and the single existing Pages model viewer remain source authorities. All original camera/pose/owner/shipping approvals stay false.

## Compare against the five real 2026 experimental GLBs (still unpaired)

The companion tools/art/compare_original_chroma_axes_to_glb_poses.py opens the **exact** previously verified five-pose SHA-bound GLBs from real model viewer Actions run #41259476190 (source commit d061cddcdbac9b2b5ac137d0d721b63f92dc3ec1), without rerunning the OpenSCAD rig or altering a vertex. It isolates the one painted fork/frame material mesh in each GLB, bakes its original part/world transforms, projects it using the **frozen provisional** side camera and exact 7:6 aspect at 4×, then samples the same logical 64×64 coloured-mask descriptor. It fails when any source original ROM, original colour-axis report, GLB SHA, source scene node or camera SHA changes.

    python3 tools/art/compare_original_chroma_axes_to_glb_poses.py --corpus /source/source-corpus.json --source-axes /reports/source-chroma-axes.json --model-review-dir /verified/real-model-site/model-review --camera analysis/data/racer-inverse-side-provisional-1205.json --out /new/source-glb-axis-coverage.json

The numeric comparison reports each of the five experimental image-projected painted axes, the range and gap from all 35 original exact binary source masks. The distance to the nearest *experimental* axis is a **coverage descriptor only**; do not interpret it as a source-to-GLB pose matcher or pose-classification confidence. No 1994 image is labelled with an experimental pose. It does not determine the original 3D camera, true source fork lean, part hierarchy or a sufficient animation system.

The existing opt-in original-ROM GHA workflow emits this second numeric report in its same bounded research job, alongside the source-only axis, frozen wheel and near-duplicate evidence. Future geometry proposals should target gaps in source pose **directional diversity**, not just improving already correlated near-duplicate silhouettes.
