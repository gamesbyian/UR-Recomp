# Original source phase → current 2026 GLB wheel motion: fixed counterfactual

This is an **experimental addition** stacked on #3124, not replacement art or a recovered 1994 skeleton. It reuses its authenticated original MesenCE 1601–1624 two-player PPU source, SHA-locked ROM phase/orientation indices, exact original 64×64 masks, canonical current-success five-parent/16-material 2026 GLB, frozen provisional 7:6 camera and one original tick1601 registration per player. The original source has already been inspected, so these 48 images are **exploratory**, not prospective holdout.

The earlier authentic 48-frame saddle-only test reported improved static IoU at +15° but reduced already-small 23-edge change overlap. Historical #3101 fixed drive +24°/tick, tested against a different base camera/pose convention, achieved ~0.16 source change support in a bounded control. A fair direct control must keep **the same** current source-verified GLB, original first-frame anchor, source-index root-angle convention, and +15° saddle; neither #3101 nor #3124 alone provides that comparison.

## Predeclared current experiment

- Baseline: the four existing #3124 arms (original source rigid 2D rotation, fixed axle-root neutral / saddle +15° / saddle −15°) are unchanged and still checked **exactly** against the prior executed real-GLB receipt.
- New A: fixed +15° authored saddle; rotate actual source GLB tire, rim and pedals together by **15° per delta in the original ROM phase index**, relative to that player's tick1601 0..23 phase (wrap 24). Original drawing phase may not equal physical crank angle.
- New B: identical +15° saddle but rotate those same parts by the earlier **24° per chronological tick** control, relative to tick1601 (wrap 360). Neither rate is optimized to this source corpus.
- Same absolute source ROM orientation-index root, real authored axle pivot and current source 2026 mesh under both controls. No per-frame translation, scale, reflection, role-specific speed choice, mesh replacement, camera fitting, saddle-angle selection or hidden shape optimization.
- Report pooled alpha IoU over 24 original images, equal-vote distinct-source-shape IoU, and **real 23 consecutive Mesen source change-edge** IoU for blue and red independently. Keep upper/middle/lower source y-band residuals and per-tick source phase/orientation provenance. If full source shape rises but edges do not, report the negative.

The existing Windows Visual Atlas PR validation already exports, verifies and renders the **actual** OpenSCAD-authored GLB and checks the original source ZIP; editing the existing scorer automatically triggers that gate. No additional emulator, model exporter, dataset, viewer or Actions workflow is justified.

**Stopping rule:** Only a simultaneous, meaningful motion-edge improvement in both independently named original players, without wiping out baseline shape correspondence or breaking real GLB pivot/material contracts, warrants further mechanical phase calibration. If neither fixed A nor B generalizes to the two observed roles, stop phase-angle sweeps and investigate locally missing source change clusters, authored wheel spoke/material visibility, and source registration/occlusion. Keep owner likeness approval, original 3D parameter recovery, prospective holdout and Windows ART/release acceptance **false**.
