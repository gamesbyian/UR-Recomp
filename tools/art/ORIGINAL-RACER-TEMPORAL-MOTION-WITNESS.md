# Original racer first-family temporal motion witness

**Scope:** Source-authenticated 2D animation evidence from the existing **P1/P2 guest frames 1205–1220**. This is a direct next input to the inverse-graphics execution plan's A1/A3 motion-calibration lanes and the existing 3D rig, not a new rig, pose classifier, viewer or source pose mapping.

The new `tools/art/build_original_racer_temporal_witness.py` uses the merged lossless original PNG decoder and source corpus auditor. It revalidates every one of the 32 retained 64×64 original sprite-frame PNGs against the independently retained ROM-composition image SHA and representation ID, then independently checks the original source registry's visible bottom-alpha midpoint. It never downloads or exports a new ROM, source image or GLB.

```sh
python3 tools/art/build_original_racer_temporal_witness.py \
  --out /private/ur-art4k-original-temporal-1205-1220.json
python3 -m unittest tests.unit.test_build_original_racer_temporal_witness
```

The output is no-overwrite UTF-8 JSON (schema `UR-RACER-ORIGINAL-2D-TEMPORAL-MOTION-WITNESS/1`) containing **32 original player/frame observations, 30 consecutive player-specific transitions**, exact source image/mask hashes, repeated-hold runs for both RGBA and binary silhouette, frame-aligned alpha bounds, centroid coordinates, and second central moments with original 7:6 physical pixel aspect. It also gives the actual image silhouette overlap, differing binary source pixels, projected centroid displacements, and visible bottom-alpha displacement across adjacent guest frames. The retained source rail contains **21 unchanged binary-mask transitions** and **nine changing ones** (P1: six changes; P2: three), verified from the original PNG alpha bytes. The source's lowest visible alpha row remains at `y2=76` over this first-family interval, while horizontal midpoint registration changes; these are 2D sprite facts rather than physics or 3D joint motion. These measurements help distinguish a held sprite from a changing source image and bound how a future coherent animated 3D rig should appear in projection.

**Important limits:** A source alpha centroid is a 2D statistical descriptor, **not** a recognized wheel/saddle pivot or a 3D bone coordinate. The visible lowest-alpha midpoint is **not** the physical road contact or physics collider. Covariance is a 2D shape moment, not a recovered 3D orientation. A repeated RGBA frame does not prove the guest physics did not move, and a changing raster does not establish a distinct 3D camera or authenticated model pose. The first-family input has no independent held-out 3D camera and no approved 1994 character likeness. All approval/pose-map/ground-contact flags are explicitly false.

**Handoff to rig #2832:** use these exact original sequence frame and SHA identities alongside source-registered camera and multi-pose measurements from merged #2948. Test that a shared articulated rig and a single continuous motion parameterization can account for the verified temporal shape changes **without assigning per-frame unrelated geometry or fitting the held-out original family**. A candidate may reuse the source's known hold cadence, but cannot claim an authentic source-rig pose mapping until model rendering and visual evidence independently qualify. The first-family is a training and sanity-check witness, not generalization proof.

**Handoff to viewer #2938:** the existing Pages viewer alone owns WebGL, pose playback, original sprite scrubber and optional research overlays. This tool is an offline, metadata-only producer with no UI or Pages write. Any later visible temporal diagnostics should be read-only, SHA-bound, labelled *original 2D animation evidence*, and kept independent from the five provisional 3D blockout pose names. The optional measurement overlay is separately tracked in [issue #2952](https://github.com/gamesbyian/UR-Recomp/issues/2952).

**CI and rights:** ROM-free unit tests, no copyrighted original image bytes or ROM added to repository, no heavy GLB/GPU dependency, no native/gameplay/acceptance state changed. `--out` refuses any existing path using the repository's no-replace report helper.
