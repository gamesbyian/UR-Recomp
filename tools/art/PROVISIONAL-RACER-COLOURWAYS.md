# ART-4K P1/P2 provisional colourway pair

**Status: experimental colourway derivation only. No source-model likeness, original 3D material, camera, sprite-to-rig pose or shipping approval.** This tool builds downstream of the **single draft #2832 canonical OpenSCAD rig**, source-registered first-family raster colour census (#2965), real material identity audit (#2967) and the **single Pages model viewer** (#2938/#2957). No new model, viewer, publishing route or native presenter.

## Motivation and source facts

The authenticated original first-family sprites distinguish P1 **red** (mean 54 descriptive red-indicator pixels per unique silhouette, 0 blue) from P2 **blue** (mean 67 blue-indicator pixels, 0 red). The shared five-pose GLB has 16 material meshes in one constant palette; fork_and_frame__material_0 is blue RGB (28,89,222). The original 1994 model's material identities and scene lighting cannot be inferred from source pixels, so the first P1 red (211,43,47) is an **explicit provisional 2026 artist proposal**, not a recovered source albedo. P2 stays byte-identical.

## Run (no new 3D compute)

First export all five named poses with the **existing #2832 exporter**, retaining successful source-hash-bound attempts/current pointers as required by tools/art/model-review/stage_pages.py.

Run from repository root:

    python3 tools/art/build_racer_colourways.py --exports /path/to/five-pose-exports --out /path/to/derived-review-assets --source-commit FULL_EXACT_40_CHARACTER_MODEL_COMMIT

The tool validates all five source exports, the exact common source SCAD SHA, the five-part 16-material source receipt and all original per-vertex material RGBA bytes. P1 edits only COLOR_0 bytes for the primary fork/frame slot and corresponding glTF accessor min/max metadata; P2 is the byte-exact source GLB. A digest signs all other binary bytes and every unchanged glTF structural field, including positions, indices, normals, scene hierarchy and transforms. There is no rerender, remesh, rig fork or model inference.

On Linux, atomic renameat2(RENAME_NOREPLACE) publishes the complete directory without replacing an existing empty destination; Windows os.rename rejects existing destinations. Other platforms fail closed if atomic no-replace directory publication is unavailable. The supplied 40-character source commit is explicitly an unverified operator claim (source_commit_verified: false). Only the common SCAD SHA and actual GLB/receipt digests are verified. Do not use the commit claim as independent producer attestation.

A new immutable art4k-colourways-<id> directory contains 10 named GLBs (five original P2, five experimental P1), colourways.json, source model commit/SCAD SHA, input/output SHA-256s and per-pose geometry invariance fingerprints. Every approval/mapping/camera/holdout claim is false. An interrupted batch is not published under its final name. A future changed base material must have a deliberately versioned mapping, never a guessed recolour.

The pair is **not automatically inserted into the website**. The Pages reviewer can later add an independent experimental-model colourway control, separate from original-source P1/P2 sprite-frame scrubber and the five blockout poses, after qualifying the actual GLBs. A palette match cannot prove authentic pose pairing or override the owner's current character-likeness veto.

## Validation

Run: python3 -m unittest tests.unit.test_build_racer_colourways

The tests are Python-standard-library-only synthetic glTF 2.0 cases, including five-pose batch, invalid/aliased material accessors, corrupted binary, mixed model identities and immutable outputs. These are mechanical checks, not original art certification. Remaining acceptance requires testing the **actual** five original GLBs, a browser comparison at 32/64px and correct source 7:6 pixel aspect, and explicit owner likeness review after camera/geometry/pose fidelity work.

Source authorities: [original colour census](ORIGINAL-RACER-COLOURWAY-SOURCE.md), [16-material audit](EXPERIMENTAL-GLB-MATERIAL-IDENTITY.md), [inverse-graphics plan](../../docs/HD-RACER-INVERSE-GRAPHICS-PLAN.md), [character brief](../../docs/HD-RACER-CHARACTER-RECONSTRUCTION.md), [issue #2969](https://github.com/gamesbyian/UR-Recomp/issues/2969).
