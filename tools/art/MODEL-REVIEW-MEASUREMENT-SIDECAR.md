# Source-verified measurement sidecar for the existing 3D viewer

**Ownership:** The existing [model-review Pages site](model-review/README.md), merged as [#2938](https://github.com/gamesbyian/UR-Recomp/pull/2938), exclusively owns the HTML, interaction, original-sprite rail and Pages deployment. This document introduces a compatible **offline JSON producer** and an optional handoff format. It neither changes the website nor publishes anything automatically.

The producer `prepare_model_review_measurement_sidecar.py` reuses the **merged real five-pose comparison runner** from [#2948](https://github.com/gamesbyian/UR-Recomp/pull/2948). It recomputes the full 5×10 comparison from **actual five GLBs and all 32 independently authenticated original source sprite references**, using source-registered 2D anchors. It does **not** accept previously saved, self-asserted metrics as authoritative.

```sh
# The model-review directory comes from the actual, independently verified
# five-GLB Pages staging artifact, not a default no-model placeholder.
python3 tools/art/prepare_model_review_measurement_sidecar.py \
  --model-review-dir /private/ur-viewer-stage/model-review \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --out /private/ur-viewer-evidence/model-measurements-v1.json

python3 -m unittest tests.unit.test_prepare_model_review_measurement_sidecar
```

The output is an immutable, **no-overwrite** UTF-8 JSON file with schema `UR-RACER-MODEL-REVIEW-MEASUREMENT-SIDECAR/1`. It records the exact SHA-256 of the staged viewer manifest and sprite rail, source-model commit and SCAD digest, all five actual GLB file digests, exact original USA ROM and source registry digests, camera-manifest digest and provisional camera status, 32 original frame IDs grouped into 10 distinct source binary silhouette identities, explicitly separate from the **five** experimental model poses, source-registered 2D anchor offsets, and five 2D similarity scores per unique source shape. There are no original PNG, ROM, GLB, derived image bytes or on-page URLs in this sidecar.

**Every rank is labelled exploratory and unpaired.** The source sprites have **no authenticated mapping** to the experimental `upright`, `pedal`, `wheelie`, `stunt`, and `bank` model poses. The original 1994 3D camera, truly independent pose-family holdout, owner character likeness and shipping art remain unverified. The producer refuses input marked as owner-approved, camera-calibrated, pose-authenticated, or other unsupported success. It also rejects inconsistent score winners, duplicated player/frame observations, impossible source-to-registered-anchor offsets, wrong GLB count, forged missing source SHA and inconsistent equal-shape-weighted means.

**Viewer-agent integration contract:** only after the viewer agent independently validates that the sidecar's `viewer_manifest_sha256` and `viewer_sprite_rail_sha256` match the exact assets it is serving should the site offer this as a *separate, opt-in research overlay*. A missing, stale or partially updated sidecar should simply leave the viewer's current GLB and sprite interfaces working, with no measurement shown. It must not display a GLB pose name as the corresponding 1994 original sprite pose, claim that numerical IoU establishes artistic likeness, or modify the standard atlas publishing workflow without separate review. Use an unambiguous label such as **Unpaired experimental silhouette similarity, provisional camera** and show source player/frame and digest provenance on demand.

**Reproducibility:** the sidecar is generated only by rescoring the actual staged GLBs through the established projection/scorer; an off-site observer cannot trust a JSON score merely because it has a SHA-256. The sidecar captures the local source evidence identity, which lets the viewer reject stale measurements after any model/source change. No default CI job builds heavyweight GLBs or computes this matrix; optional offline dependencies NumPy, Trimesh and Pillow are required only for an explicitly invoked measurement run. ROM-free schema and spoofed-input tests run in ordinary tooling CI.

**Next:** the viewer owner may add a small optional read-only comparison panel consuming this versioned file after separate QA. Source-to-rig camera and pose calibration and genuine withheld-family validation remain separate higher-order work. No new website, new rig, or runtime 3D engine is authorized by this tool.
