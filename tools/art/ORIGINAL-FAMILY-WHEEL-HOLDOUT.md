# ART-4K authenticated additional-family wheel geometry holdout

**Purpose:** evaluate the already-frozen 2026 experimental wheel-width hypotheses against genuine original sprite families never used to choose them. This is source-registered 2D silhouette research, NOT proof of the original 1994 camera/mesh/pose or owner approval.

## Frozen comparison

Merged #2971 reports original first-family (1205–1220) source silhouette mean IoU **0.57255469** for the actual experimental upright GLB. Scaling *only the wheel and rim world X coordinates* by **1.10** increased first-family mean IoU to **0.59883507**. Both P1 and P2 contributed to selecting that factor, so neither player was withheld. This new test fixes both factors **1.00 / 1.10** before inspecting any new source family.

The source is the existing #2942/#2968 canonical USA ROM compositor, not a second image extraction algorithm. The exporter checks the exact original USA ROM SHA. The evaluator independently rechecks every 64x64 source PNG against the immutable corpus receipt, including decoded RGBA, alpha and shape SHA. It traces shared binary masks across source windows, moving any window connected to first-family masks into the fit group. Only other connected components of **previously unused exact binary silhouettes** form the novel original 2D holdout.

The only evaluated model is the same five-part, 16-material, unapproved 2026 upright GLB from Actions run 41259476190 with SHA-256 efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5. Camera remains the prior fixed provisional 9.5-logical-pixels/unit side projection, original 7:6 PAR and source visible lowest-alpha contact. Differences in source contact position are applied as **exact half-logical-pixel deltas on the 4x mask**, never arbitrary score-optimizing recentering or zoom. The one original model is not altered or exported.

## Reproduce

On any authoring host with Python 3.11, NumPy, Trimesh, Pillow, a copy of the exact original USA ROM and an externally staged real upright GLB, run the already-established original corpus export and:

    python3 tools/art/evaluate_original_racer_wheel_holdout.py --corpus /private/corpus/source-corpus.json --glb /verified/upright.glb --camera analysis/data/racer-inverse-side-provisional-1205.json --out /private/new/holdout.json

A new narrow **explicit workflow or PR-change-triggered** Ubuntu hosted GHA runner in .github/workflows/art4k-original-family-holdout.yml performs the source ROM size/SHA preflight, source export, exact historic model artifact recovery, frozen evaluation and uploads **the numeric JSON receipt only**. It has a 20-minute cap and no periodic schedule; no gameplay build or repeated whole-rig export. Missing ROM, expired artifact or source mismatch are named failures, never accepted scores.

The report proves no 1994 camera identity, 3D shape, original pose to 2026 GLB mapping or owner likeness; all approval flags false. A positive holdout delta would make the bounded 10% width hypothesis worth *independent art review*, not automatic implementation in draft #2832. A negative holdout delta falsifies this one-family wheel hypothesis under the fixed camera. Do not optimize on the held-out set then call it withheld again. The sole existing model viewer remains #2938/#2957.
