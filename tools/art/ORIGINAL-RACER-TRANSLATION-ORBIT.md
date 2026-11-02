# ART-4K: retrospective original-ROM translation-orbit control

Complements merged #3022's target-anchor translation baseline. The 35 masks are revalidated against the authentic USA ROM-composed raster corpus. The **109 adjacency edges, 19 changes and 90 holds belong to an authored reference registry**, not independently witnessed original-emulator cadence. See merged #3025 and draft #3026.

For each same-player same-window authored adjacent pair, optimize a fixed finite grid of integer translations (default ±2 logical pixels, no alpha clipping), minimizing XOR between the shifted previous mask and the *actual next mask*. Preserve all equal minimum shifts, a deterministic least-motion tie break and the margin to the next distinct residual. Compare the optimal shift with #3022's *target-derived* visible-alpha anchor shift. A zero residual means a rigid integer shift can explain that pair under the stated constraints. A positive residual cannot be eliminated by any eligible such shift, but does not by itself prove a 3D mesh deformation; rotation, occlusion, bake/view and sprite shape changes remain possibilities.

**This is an optimistic retrospective oracle**, because the target mask itself chooses the shift. It does not predict motion or establish true source translation, a wheel contact point, original 1994 animation timing, camera, pose mapping, likeness or shipping art. A rig fit must never optimize a novel-frame score using an oracle displacement selected from that held-out frame.

ROM-free core tests:
    python3 -m unittest tests.unit.test_audit_original_racer_translation_orbit

Source-authenticated execution via the existing original-ROM corpus producer:
    python3 tools/art/audit_original_racer_translation_orbit.py --corpus /private/source-corpus.json --radius 2 --out /private/new/original-translation-orbit.json

This standalone source-only diagnostic reuses the established corpus validator, authored window walker, and write-once report. It does not add a rig/viewer, change native presentation or create an expensive default workflow. Before interpreting totals, run it once on the real source corpus; the six ROM-free unit controls prove only the bounded algorithm. Inspect in particular the two changing-mask authored edges with fixed visible alpha anchor. Source-matched pose work should use the existing #2832 five-part rig with a fixed shared camera. Authentic cadence remains gated on actual emulator-captured PPU/OAM evidence.

## Actual source-authenticated run, November 2, 2026

The existing ROM-authenticated research workflow [run #41396846120](https://github.com/gamesbyian/UR-Recomp/actions/runs/41396846120) executed the new control successfully and saved the report in artifact #13118714968. Source report member SHA-256: 000c2b3f03600e86d468dc3fca7283a7ba8e49488e19de4e31b6214df4db2ada. Compact run identity and measured counts: analysis/data/racer-art4k-original-translation-orbit-20261102.json. The original full report remains in the workflow artifact, not duplicated here.

Across 19 changed authored-registry source mask edges, best no-clipping ±2px translation removes 338 of 1,631 original changed-pixel XOR positions by shape alignment, leaving **1,293 residual pixels** (79.277% of unshifted XOR). **All 19** changing pairs independently select exactly the same integer shift as the earlier target-visible-alpha-anchor method. There are **no tied optima** among any of 109 examined registry edges, and the second-best distinct residual on a changing pair is at least 12 pixels worse. All 19 changing pairs retain a nonzero shape residual; two have zero best displacement and still change. This **confirms** the previous target-anchor alignment was already the optimal integer shift within this bounded search; it does not discover a better source motion map.

These conclusions concern exact original ROM pixels in the **authored sequence registry**. They do not certify the original game's executed 1994 frame chronology, PPU/OAM sprite ownership, genuine 3D rotation/deformation, camera or character likeness. The next geometry experiment should use the existing #2832 rig on the remaining shape residual with a locked common camera, not multiply 2D source translations or treat this retrospective oracle as a predictive fit.

## Raster-region residual, deduplicated by actual source-mask identity

The first two successful authenticated-ROM runs established that 19 changing authored-registry edges represent **14 distinct directed (before SHA, after SHA) binary-mask transitions**. New per-pair and aggregated reporting now partitions the exact target-minus-shifted-source XOR by fixed *source raster* Y bands, with both occupied union pixels and mismatch counts. A band with zero occupancy has `null` mismatch fraction rather than invented success. The summary counts each unique directed pair once before region aggregation, avoiding inflated independent sample sizes from repeated authored windows. This is not a physical-part annotation or 1994 PPU timing claim.

Prior independently decoded source-artifact analysis of the 14 distinct directed transitions found upper Y=0..15: 663/1544 union pixels mismatched (42.94%), middle Y=16..31: 236/2370 (9.96%), lower occupied Y=32..39: 23/1088 (2.11%). Y=40..63 is empty and therefore cannot supply a meaningful zero-error score. The newly automated report should reproduce these exact fractions against canonical ROM data. This is stronger than counting 926/1293 repeated edge residual pixels in the first band, which is affected by source occupancy and registry repetitions.
