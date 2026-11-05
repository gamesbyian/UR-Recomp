# ART-4K: real continuous ride cycle against authentic original ROM motion

## Evidence class and exact inputs

The **one** experimental five-part OpenSCAD rig in draft #2832 now has five independently source-verified, five-parent/16-material real ride-cycle GLBs at **2026 authored normalized times 0.0, 0.25, 0.5, 0.75 and 1.0**, generated via child #3019's existing shared exporter, on actual CI [run #41383635894](https://github.com/gamesbyian/UR-Recomp/actions/runs/41383635894). They are not the 1994 source animation, and their normalized time does not map to any original gameplay frame.

This experimental research tool is built on merged #3013 authentic original 35-mask×five-pose source classification and merged #3017 pixel-motion diagnostic. Both demonstrated why static unpaired silhouette IoU is inadequate for reconstructing animation: 109 genuine original P1/P2 frame edges include 19 silhouette changes, 90 holds and 1,631 changed alpha pixel locations; only **33/1,631 (2.02%)** changed source pixels coincide with source-placed fixed-camera *pose-only* changes in the earlier static-label model. A translated source visible-bottom anchor accounted for much of a larger 29.18% nominal placed-model recall.

The producer `tools/art/study_original_racer_continuous_ride_motion.py`:
- Reads all authentic 64×64 source PNGs and rechecks their original canonical ROM/source hash, source player identity, source-specific visible-alpha anchor, 27 temporal windows, 144 player/frame observations and 109 genuine per-player adjacent edges.
- Requires **exactly five** predeclared times and the independently verified source-owned authoring SHA `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`; pins the **exact five actual GLB SHA hashes** of #3019 and checks all exporter-current/successful immutable attempt, independent 5-parent/16-material receipt and real loaded GLB scene structure. No second model/rig/viewer/rendering engine.
- Renders each candidate once under the **same frozen provisional 7:6 first-family camera** and compares each of four predeclared 2026 phase transitions (0→.25, .25→.5, .5→.75, .75→1) **independently against all 109 authenticated original source frame edges**.
- For each original edge, measures 64px binary XOR original-source changes versus real model **pose-only** projected changes at one unchanged original source anchor. Reports the separately placed-model diagnostic using both original source anchors, with source-hold false-positive counts (90 intact original holds), changed-pixel recall and precision.
- Reports endpoint closure as a descriptive count of different pixels between actual 4× render of ride@0 and ride@1. No closure is invented by copying pixels or mirroring assets.

**Critical limitation:** Every phase interval is applied counterfactually to every source edge, without choosing a time correspondence. This tests *motion vocabulary/expressivity*, not an actual reconstructed source animation. A large recall cannot be promoted to registered motion or likeness; a large false-motion count on original holds is meaningful negative evidence. Do not rank or optimize the phase/timing/geometry using the same 35 inspected source masks and claim them as untouched validation. This particular frozen preliminary experiment has no true original 3D camera calibration or new held-out 1994 frames.

## Reproduction

The existing original-ROM research workflow restores the five immutable artifacts from #3019's previously verified source-export job via `actions/download-artifact@v4`, pins every GLB file SHA, and runs:

```bash
python tools/art/study_original_racer_continuous_ride_motion.py \
  --corpus /private/source-corpus.json \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --ride-sample 0.0 /private/art4k-real-continuous-ride-0.0 \
  --ride-sample 0.25 /private/art4k-real-continuous-ride-0.25 \
  --ride-sample 0.5 /private/art4k-real-continuous-ride-0.5 \
  --ride-sample 0.75 /private/art4k-real-continuous-ride-0.75 \
  --ride-sample 1.0 /private/art4k-real-continuous-ride-1.0 \
  --out /private/new/actual-original-ride-motion.json
```

ROM-free receipt/census/negative tests run with `python -m unittest tests.unit.test_study_original_racer_continuous_ride_motion`. The actual original sprite and GLB job is path-filtered in the existing, bounded source workflow, not a new schedule, server or mainline asset. Output publishes once; all original/2026-model, camera, time, experimental player colour, likeness and shipping flags remain unapproved.

### Next decision after actual numeric evidence

A genuine source-registered articulated trajectory requires original frame-to-phase hypotheses chosen **only from frozen fit source families**, a strictly held-out connected original family (including shared binary masks), and physically interpretable time/phase, saddle/fork/pedal motion. Score real temporal **changed-pixel overlap** and false motion across unchanged source frames, and include the two original moving edges with fixed visible anchor as diagnostic cases. The current 2026 procedural source art remains rejected as shipping likeness. Keep exactly one rig (#2832) and one Pages viewer.
