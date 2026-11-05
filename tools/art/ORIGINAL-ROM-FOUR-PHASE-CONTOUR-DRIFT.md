# Original-ROM geometry evidence: cross-phase 2D contour conservation

## Executed, frozen original-ROM result (2026-11-05)

Real original 2,097,152-byte USA ROM and SHA-locked original 24×64 source axis report were executed by the existing full unit suite in [GitHub Actions run #41990764973](https://github.com/gamesbyian/UR-Recomp/actions/runs/41990764973). This is the original source's **four** previously frozen phase indices 0/6/12/18, each independently derived from all 64 raw 4bpp ROM orientations; it is **not** a claim about every one of the 24 phases or a new blind holdout. The source report was generated once by its existing authentic-ROM unit; the new analysis reused it without a second decode.

Across all four original phases, after excluding source pixels sampled from outside the original 64px canvas:

- **3,008** image-space pixels have adequate original orientation coverage in *all four* phase views.
- Original source majority-opaque 2D silhouette has **291** pixels common to all four and **304** pixels present in at least one. Consequently only **13** common-valid 2D silhouette positions vary across these four phases.
- The stronger, ≥90%-opaque **2D core common to all four** contains **164** pixels.
- The 13 varying source pixels are distributed **upper y0–14: 0; middle y15–26: 1; lower y27–63: 12**. The common silhouette contributes upper **51**, middle **95**, lower **145** pixels.

| Original ROM phase pair | Common-valid 2D contour IoU | Exact 4bpp paint recall on shared opaque source |
|---|---:|---:|
| 0 → 6 | 0.97029703 | 0.91836735 |
| 0 → 12 | 0.97333333 | 0.91095890 |
| 0 → 18 | 0.98000000 | 0.89795918 |
| 6 → 12 | 0.97674419 | 0.93197279 |
| 6 → 18 | 0.97682119 | 0.91864407 |
| 12 → 18 | 0.97333333 | 0.91780822 |

These are **2D source-space** alpha and indexed-paint statistics, measured after an explicit *hypothetical* source-index inverse screen rotation. The fact that original source paint indices change more than original alpha at these phases may include animation or shading; it does not recover 1994 3D materials.

**Consequence for the single 2026 GLB:** a large phase-dependent vertical stretch/saddle displacement is **not identified** by these particular original source views, especially in the upper y0–14 region. This is consistent with the separately witnessed real 1602→1603 and 1605→1606 upper events having been orientation-dominant rather than phase-dominant. Treat the 2026 model's existing wheel/rim/pedal movement as a distinct lower-region temporal hypothesis, and test upper shape/visibility under *shared* source-orientation/camera constraints before varying authored upper geometry per phase. All earlier real-GLB silhouette and 23-edge scores still matter; no source phase index is a calibrated physical 3D rotation, stretch, bone or original 1994 mesh. Preserve the owner art-likeness veto.

The authentic numerical counts and six alpha IoUs are now **frozen as assertions in the existing original source-ROM test**, so subsequent refactors cannot silently change the evidence.


This is a source-only geometric constraint for the **single** draft 2026 GLB, not an original 1994 3D mesh or camera reconstruction. The authenticated original USA ROM contains a 24-phase × 64-orientation 4bpp pre-rendered sprite table. The previous full source audit (merged #3123) already inverse-rotates 64 original orientations at **four frozen phases: 0, 6, 12, 18**, using a single even-orientation 2D pivot and a separate valid-canvas mask to distinguish cropped pixels from true transparent pixels.

The new `tools/art/analyze_original_rom_four_phase_contour_drift.py` accepts **only** that SHA-authenticated existing four-phase consensus report. It reconstructs each phase's majority-opaque, ≥90%-opaque core, exact original 4bpp plurality and accepted pixel coverage from the saved per-pixel 64-view observations. It checks that derived core, 2D silhouette and 4bpp indexed-paint hashes match the source report exactly. A pixel must have at least **32 source-valid orientations** at a phase to become either opaque or transparent evidence for that phase.

Across all **six** frozen unordered phase pairs, compare consensus silhouettes only on the intersection of their actually valid source pixels. Report 2D alpha TP/FP/FN and IoU, exact 4bpp agreement among jointly opaque consensus pixels, and fixed source-image y0..14/y15..26/y27..63 counts. Also report how much 2D image-space contour is always opaque, ever opaque, phase-variable, or near-invariant core **across all four** phases, after requiring all four to have valid source samples. Do not choose pairs after observing results or assume they represent 1994 physical wheel-pedal angles. Per-band and whole-source pixel counts must exactly conserve, and cropped/unknown cells cannot be converted to fake transparent backgrounds.

**How this informs 3D modelling:** the always-opaque core is a plausible *2D projected* invariant reference for testing a common 2026 rig silhouette, whereas phase-varying source pixels identify where an animated model must have independent geometry/visibility, rather than achieving an apparently good static fit through a per-sprite translation. The original silhouette may still change because of hand-authored drawing, material masking, true 3D parallax, original source shape deformation, or imperfect 2D rotation assumptions. None can be uniquely resolved from this measurement.

Reproduction is independent of OpenSCAD, the current optional GLB libraries and new Mesen captures:

```sh
python3 -m unittest tests.unit.test_analyze_original_rom_four_phase_contour_drift
python3 -m tools.art.analyze_original_rom_four_phase_contour_drift \
  --original-consensus-report /previous/exact-source-derotated-consensus.json \
  --out /new/four-phase-2d-contour-drift.json
```

The existing authentic original-ROM consensus unit test also emits this score from the **same** decoded source grid, with no second ROM decode and no new Actions workflow. Once exact source metrics are observed, freeze the output counts in the original test/decision handoff, rather than fitting new 2026 geometry to a source slice as a new blind holdout.

This is a bounded prerequisite before any further trial of original frame length, saddle width or camera angle, and must preserve the existing real 2026 GLB six-objective Pareto and genuine 23-edge source-motion comparisons as independent diagnostics. Original 1994 physical 3D joints, mesh, camera, owner likeness and Windows ART release approval remain **false**.
