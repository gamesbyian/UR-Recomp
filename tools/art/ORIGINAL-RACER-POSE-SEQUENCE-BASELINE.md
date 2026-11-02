# ART-4K: source-frame-aware discrete pose-label baseline

**Scope:** This is an offline, reversible research diagnostic using the **one** unapproved five-part 2026 rig and **one** existing Pages viewer. It does not recover the original 1994 mesh, 3D camera, original animation identity or finished artwork. Do not award ART/QA/release credit from these metrics.

## Evidence and safe path

1. Use the existing `art4k-original-family-holdout.yml` canonical USA-ROM producer and its `source-corpus.json` and `stock/source-*.png`, not model-generated synthetic sprites. The existing `freeze_racer_source_family_splits.validate_corpus` reopens and checks all authentic original 64×64 PNGs, RGBA hashes, binary alpha hashes and player/representation identities.
2. Use a **real** five-GLB original-source pose matrix generated under a single provisional, documented 7:6 camera. `build_real_viewer_pose_matrix.py` already generates an exploratory matrix for 10 first-family masks; it does **not** cover the remaining 25 masks. Missing scores must cause failure rather than selecting a substituted pose, skipped observation or guessed camera. Real GLB identities and the unchanged camera manifest must be retained with the report. The model report is evidence supplied by its producer, not proof of original animation identity.
3. Run `prepare_original_racer_pose_sequence.py` with explicit actual original source windows and (preferably) the already frozen connected-window split:

```sh
python3 tools/art/prepare_original_racer_pose_sequence.py \
  --corpus /private/original/source-corpus.json \
  --pose-matrix /private/reports/real-five-pose-matrix.json \
  --window first-1205-1220 \
  --change-penalty 0.03 \
  --out /private/new/pose-sequence.json
```

Optional `--frozen-split /private/frozen-original-source-split.json` preserves fit/diagnostic/withheld_candidate labels, checks the exact corpus SHA and independently rejects a binary silhouette shared across different roles. Without this file, all windows are explicitly `unfrozen_diagnostic`, never held out by assumption. The output uses the existing write-once reporter, so reruns cannot silently overwrite earlier evidence.

4. For manually constructed **ROM-free** cost fixtures, `fit_original_racer_pose_sequence.py input.json --output result.json` requires `poses`, `frames` with `window`, `player` (`p1`/`p2`), integer `guest_frame` and one nonnegative finite cost per pose, plus optional `change_penalty` or complete `transition_penalties`. Minimize `1-IoU + transition cost`. Different window/player tracks and **missing guest-frame integers are always independent sequences**. Never smooth across an unobserved frame, mix P1/P2, guess labels from the bank-dominates-all baseline, re-optimize the camera per frame, or hide constant-pose degeneracy. The output preserves independent greedy selections, sequence selections, emission vs transition contributions and the count of gratuitous label flips.

## Next original-source experiment

Produce one *complete* 35-mask × five existing material-separated pose-GLB matrix, using the **already running original-ROM workflow and its restored, SHA-checked five-pose viewer artifact**, with original visible-bottom-alpha registration at exact 4×. Reuse `originals_from_corpus`, `render_mask`, `translated_4x_source_mask` and `score` from current art tools; do not build a second renderer. Then join it to the existing 91-frame / 27-window / 109-edge original 2D temporal witness. Report source hold and silhouette-change transitions separately, with chronological adjacency and frozen connected-window/shape split. The originally reported 35 × five-pose exploratory comparisons are *unpaired*; this adapter must never invent missing per-mask data.

Compare penalty zero (independent baseline) and one **predeclared** regularization value. Report constant-pose collapse, fraction of actually adjacent source frames, transitions by family, and both normalized source-mask and frame-weighted metrics. Independent original-family holdout is only meaningful when the geometry/camera/penalty were not selected by looking at that family. The already inspected 19 additional masks cannot be retroactively treated as untouched geometry holdouts.

This tool is subordinate to the governing `docs/HD-RACER-INVERSE-GRAPHICS-SPEC.md`, draft rig #2832, and existing Pages viewer. Art/likeness approval remains a separate human decision.
