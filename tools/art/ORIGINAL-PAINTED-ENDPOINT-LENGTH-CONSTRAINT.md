# Original 2D painted endpoints versus 2026 GLB blue-frame length

**Experimental ART-4K geometric constraint, not source 3D joint recovery.** Reuses the existing five-parent/16-material unapproved 2026 GLB, its order-independent material-depth rasterizer from merged #3047, the existing original-ROM painted-colour source SHA, the one fixed provisional 7:6 side camera and the source family split. No new model, game renderer, or Pages viewer is created.

The real original 64×64 P1 red/P2 blue painted-colour feature has independently authenticated 2D top and bottom three-row centroids. Their signed vector, corrected for the SNES horizontal 7:6 pixel aspect, has an **absolute physical-pixel length**. The model's depth-visible blue material has the same mathematical 2D descriptor. The difference and ratio are invariant to **translation** because both endpoints move together. Unlike previous whole-silhouette comparisons, this experiment does not choose a source target alignment, best-overlap shift, wheel-contact pixel, camera zoom or silhouette IoU to measure length.

## Actual original-source and real-GLB pilot, fixed camera

The previously inspected 35 distinct original binary silhouette masks each contribute one vote, averaging their original authenticated RGB-variant lengths within the mask. The source 2D painted-axis angle determines the closest 2026 model hinge among 19 candidate positions in 5° steps, using only the already merged blue-frame projected angle. The resulting source-painted/model-painted length ratios under the provisional +world-Y view:

| Metric | All 35 | First connected 16 | Additional SHA-disjoint 19 |
|---|---:|---:|---:|
| Mean original/model painted-axis length | **0.91236878** | 0.88630568 | 0.93431666 |
| Median | 0.92210646 | 0.88103079 | 0.92770264 |
| Per-mask range | 0.81755506–0.98766169 | 0.81755506–0.98766169 | 0.90839786–0.98766169 |

The authenticated original colour-axis lengths lie roughly **13.86–16.02** physical logical pixels, versus **15.66–17.57** for the selected model blue-painted visible-axis lengths. The apparent model painted feature is systematically longer under this uncalibrated camera, but the observation does **not** justify shortening the fork by ~9%. Original high-chroma paint may terminate inside the original physical structure, include pixels from more than one part, or be affected by a source-camera scale error. The 2026 blue frame is a deliberately hypothetical material, not recovered 1994 anatomy. All 35 source families and 19 hinge candidates have been inspected retrospectively. No held-out 3D-view generalization.

The code retains every source RGB-variant endpoint length and the per-binary-mask mean and min/max variant ratios. It independently calculates both +Y and −Y material-depth views and uses the same finite physically scaled endpoint metric. It requires exact historical 2026 GLB SHA efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5, source painted report SHA 78f420423c62e61bcb5c4271c61dc8dab17b786f693c2895cd0e3054d1d06bc8 and camera SHA 1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028. The optional source family split SHA is aa86e13348875a768351d926a2daa913c3428732e92c2f38f135bbeadf53398c. The original 1994 emulator PPU chronology, camera, geometry and owner likeness remain unverified.

Reproduce with the real experimental GLB from model-review run #41259476190 and the original authenticated painted-axis report from run #41398486394. NumPy/Trimesh/Pillow are optional offline rendering dependencies; pure physical-vector unit tests run under normal Python:

    python3 -m unittest tests.unit.test_audit_original_racer_painted_frame_length
    python3 tools/art/audit_original_racer_painted_frame_length.py \
      --glb /private/upright-efdc8425f252b4a0.glb \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --source-chroma /private/source-chroma-axes.json \
      --source-family /private/wheel-holdout.json \
      --out /private/new/original-paint-versus-model-length.json

This emits a write-once numeric report with the established source-integrity publisher. Do not mutate the canonical source rig, hardcode a length-scaled fork or promote shipping art based on the descriptive ratio alone.
