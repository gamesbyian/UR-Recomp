# Source original 24×64 sprite-manifold phase-region orbit

**Purpose:** A retrospective, source-only diagnostic from the 1,536 already authenticated original-ROM 4bpp frames recovered on #3104. No emulator or GLB rebuild, camera fit, physical wheel degrees or shipping-art approval.

The exact #3104 24-phase×64-orientation counterfactual report contains the **64 bounding boxes** of pixels whose index changes when original phase varies across its 24 values **at fixed orientation**. The centre of that phase-sensitive bounding box travels with the broader orientation, providing a simple independent 2D test of whether the local changing wheel-region footprint follows a coherent orbit. This is a box-centre measurement, not original wheel-hub ground truth; changes in the shape of the variable pixel set can shift the box even when a physical part does not translate.

With angle index `a=0..63`, use the fixed prespecified first-harmonic basis `cos(2πa/64), sin(2πa/64)` for source-pixel x and y box centres, with means and coefficients computed by the orthogonal 64-point discrete Fourier sums. No centre-per-angle adjustment, image registration, GLB fitting or higher-harmonic optimization. Compare with the constant-centre null and report coordinate-space RMSE and R². The estimated original source-pixel fit from the verified report is:

| Quantity | x | y |
|---|---:|---:|
| Mean box centre | 31.515625 | 19.5859375 |
| Cosine coefficient | +0.01605 | +10.31435 |
| Sine coefficient | −9.71759 | +0.00914 |
| First-harmonic amplitude | 9.71761 | 10.31435 |
| RMSE versus observed box centres | 0.42690 source px | 0.44946 source px |
| Maximum absolute coordinate residual | 0.8633 source px | 1.5285 source px |

These coefficients indicate a **near-quadrature, approximately circular movement of the phase-sensitive source region in raw 64×64 coordinates**. The original 7:6 display pixel aspect makes the horizontal harmonic amplitude ~11.34 in corrected display-coordinate units, versus ~10.31 vertically. Therefore do not describe the physically displayed path as a proven circle, the original angle index as measured physical degrees, the image transform as a recovered 3D camera, or the phase-sensitive region as a certified real wheel axle. Source-only pixel rasterization may explain the same observation.

**Reproduction:** `tools/art/analyze_original_rom_phase_orbit.py` verifies source report SHA-256 `23aa563c094471a3d7f1b5dcb12489cc1b5ca45b1240aee06fde3934a932bbd0` and writes a fresh exclusive report. No ROM needed after the report has been qualified:

```sh
python3 -m unittest tests.unit.test_analyze_original_rom_phase_orbit
python3 -m tools.art.analyze_original_rom_phase_orbit \
  --original-axis-report analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json \
  --out /new/phase-region-orbit-harmonic.json
```

**Next 3D discriminator:** Under one frozen source 7:6 projection and unchanged GLB geometry, measure the projected motion of each *candidate 2026 wheel/crank part-ID region* under a single rigid screen-plane orientation control and a mechanically coupled frame/saddle control. Compare its movement support, angular sign, path centre and radius in original screen coordinates to the **entire original source-index/alpha change masks**, not just the same bounding boxes used to propose the hypothesis. Include a source-only rigid 2D rotation/deformation control, and do not optimize per-angle translations or permit an unconstrained camera per sprite. A good fit indicates a useful 3D replacement construction; it still cannot uniquely recover the 1994 artist's source mesh.

## Provisional 2026 model-pivot backprojection (new diagnostic)

The previously authored **2026 experimental** OpenSCAD character in draft #2832 uses `shared_rig` with the wheel axle at world Z=**1.00**, and `continuous_rig` with an in-air spin pivot at world Z=**1.80**. Those are 2026 art-construction choices, never recovered 1994 pivots. The retained original 2026 SCAD identifier is SHA-256 `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`.

With the **one previously fixed, provisional, unfitted 2026 side camera**, SHA-256 `1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028`, original 7:6 pixel aspect and 9.5 vertical logical pixels/model unit, the measured **original 2D phase-region orbit mean** `(31.515625, 19.5859375)` backprojects to lateral model-world X about **−0.24370**, vertical Z about **1.93832**, with **all camera-depth positions unconstrained**. It is a *line* in three-dimensional space, not a recovered joint or source-model coordinate. This uses raw source-local sprite coordinates; the original sprite/model registration, display orientation and shared physical camera remain hypothetical.

Under that same frozen projection, the historical 2026 spin pivot `(0,0,1.8)` projects to original-source pixels `(33.5,20.9)`, **2.662** display-corrected source-pixel units from the orbit mean. The wheel axle `(0,0,1.0)` projects to `(33.5,28.5)`, **9.210** display-corrected units away. These are only **two prior authored candidate pivots**, not a free optimization or blind test. The fact that the historically hand-chosen mid-body pivot is closer is suggestive for a **2026 rig control to test**, but can arise from the source artist already eyeballing original art. It cannot authenticate the 1994 camera, a physical centre of rotation, wheel contact, or model likeness.

The source-locked numerical tool is `tools/art/compare_source_orbit_to_candidate_pivots.py`, and its regression `tests/unit/test_compare_source_orbit_to_candidate_pivots.py` explicitly checks the **unidentifiable depth dimension** alongside both numerical residuals. No actual historical GLB was modified or auto-aligned. Reproduce offline, without a new ROM/emulator/GLB run:

```sh
python3 -m unittest tests.unit.test_compare_source_orbit_to_candidate_pivots
python3 -m tools.art.compare_source_orbit_to_candidate_pivots \
  --original-axis-report analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --out /new/source-orbit-two-2026-pivots.json
```

**Next 3D discriminator:** test the already-authorized single 2026 GLB under a *globally fixed* root/pivot transform derived from the same camera hypothesis, with both 2026 authored pivots held fixed in advance. Compare entire original alpha/index change masks and original frame-specific orientation, including the stronger original-ROM 2D null from #3114. Do not optimise a pivot or scale per frame or silently treat 64 source orientation values as 64 calibrated physical rotation increments.
