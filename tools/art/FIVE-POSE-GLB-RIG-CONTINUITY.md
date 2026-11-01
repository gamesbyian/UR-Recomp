# Five-pose GLB rig continuity and animation capability audit

**2026-11-01 evidence status:** Source-verified inspection of the *actual* viewer [Actions artifact #13063969312](https://github.com/gamesbyian/UR-Recomp/actions/runs/41259476190/artifacts/13063969312) from model source commit `d061cddcdbac9b2b5ac137d0d721b63f92dc3ec1` (the existing unapproved ART-4K model PR #2832). This is a geometry/rig-engineering audit, with no original-1994 source pose mapping, owner likeness approval or shipping art claim.

## Measured inventory

Every GLB (`upright`, `pedal`, `wheelie`, `stunt`, `bank`) has **22 glTF scene nodes, five named part parents, 16 material-separated meshes, zero glTF animation channels and zero glTF skins**. All model GLB file digests were verified against the merged Pages viewer's manifest, and the independent original P1/P2 source-raster rail was verified before analysis. The five model files are authored static pose studies; switching between them in the viewer works but is not playback of one internally animated GLB.

Of the **16 local mesh buffers**, **nine have byte-identical local vertices and face indices across all five poses**: both tire materials, four rim/hub materials (`0,1,3,4`), and three fork/frame materials (`1,2,3`). Seven local component buffers vary with pose: rim/hub material `2`, fork/frame material `0`, all three pedal materials and both saddle materials. Most varying buffers preserve triangle counts, although **`pedals__material_0` changes triangle count across poses**: `upright=1320`, `pedal=1280`, `wheelie=1296`, `stunt=1288`, `bank=1312`. This has the signature of pose-dependent triangulation/CSG, which needs examination before implementing shared-vertex continuous animation; it does not alone prove any visible defect.

**Important:** changed local bytes can represent legitimate source-authored articulated joint rotation baked into a static pose. Byte-identical component geometry supports shared rigid-part continuity, but does not prove true mechanical linkage, 1994 source geometry, continuous animation or correct rig pivots. The exporter may legitimately produce fresh triangles while preserving geometric shape, and the correct future architecture depends on deciding which components should be rigid animated nodes versus intentionally deformable saddle/other meshes.

## Reproduce without creating another website or GLB

```sh
# First safely extract the real five-GLB viewer artifact into a private folder.
# Keep manifest.json, sprites.json, sprites/* and assets/* unchanged.
python3 tools/art/audit_five_pose_rig_continuity.py \
  --model-review-dir /private/real-model-site/model-review \
  --out /private/rig-continuity-evidence.json

python3 -m unittest tests.unit.test_audit_five_pose_rig_continuity
```

The tool uses the **existing** `audit_real_viewer_glbs.inspect_viewer` to validate the published model and all retained original PNG hashes first, then reads each real GLB's JSON animation/skin counts and compares source-local geometry/triangle buffers under explicit part/material identities. SHA and error diagnostics are written only as a private report, with the normal no-replace publication helper. NumPy and Trimesh are optional offline dependencies; synthetic source/contract checks remain ROM-free in ordinary CI.

## Actionable contract for the existing model and viewer owners

Rig/model owner **draft #2832**: preserve the nine shared rigid source-mesh components when parameterizing true animation. Decide whether to express pedal/crank/spoke phase as parent-node rotations and saddle lean/stretch as explicit child transforms/morph channels. Investigate why pedal material 0 varies from 1280 to 1320 triangles as phase changes, and whether the required continuous model needs fixed topology or controlled replacement meshes. Test the animated source model with the original SHA-verified temporal witness from [#2953](https://github.com/gamesbyian/UR-Recomp/pull/2953) and the existing five-GLB camera/silhouette diagnostics. Do not infer authentic 1994 sprite-to-model pose mapping from a 2D best-score ranking.

Viewer owner **merged #2938**: the existing website's pose buttons remain correctly labelled experimental separate GLBs, not GLB-embedded animation. Once the rig exports a genuine pose-timeline/animation asset, update the *same* viewer with playback only after the source-built rig and browser/atlas tests validate the new asset. The source-verified measurement sidecar in merged #2950 remains a separate optional research overlay; no new website or default multi-minute CI workflow is required.

**Release/art gate:** this audit observes the 2026 procedural blockout's internal consistency only. It does not establish original character identity, source 3D geometry, source-camera/rig motion correspondence, human owner likeness approval or usable gameplay art.
