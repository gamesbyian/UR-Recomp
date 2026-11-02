# ART-4K experimental axle-centred fork/saddle hinge

**Experimental 2026 blockout, not approved original Uniracers art.** Reuse one source-owned five-part, sixteen-material GLB rig (#2832). This add-on reads the historical exact 2026 upright model GLB from the existing artifact run #41259476190, checks SHA-256 efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5, and changes **only the existing parent transforms** of fork/frame and saddle around the real tire axle. Tire, rim, hub and pedals remain unchanged. It adds no geometry, forked canonical SCAD source, viewer or runtime renderer. No new 1994 source animation timing is assumed.

## Command

Install optional offline Python packages numpy and trimesh in the experiment environment. Obtain the original GLB using existing authenticated model-review artifact #13063969312 from run #41259476190. Never replace an original or prior candidate.

    python3 tools/art/experimental_frame_hinge.py \
      --source-glb /private/upright-efdc8425f252b4a0.glb \
      --frame-pitch-degrees 3 \
      --out-glb /private/new/hinge-plus3.glb \
      --receipt /private/new/hinge-plus3.json

Accept the derived GLB only with its successfully published write-once receipt. The tool checks exact source input SHA, finite restricted angle ±8°, five source parent and sixteen material child identities, source wheel/rim/crank pivot consistency, preserved untransformed source vertex/face buffers after actual GLB round-trip, exact unchanged wheel/rim/pedal transforms, and no overwrites. A zero-degree transform retains original geometry; it can produce a different export hash due to reserialization.

## Independent fixed-camera original-ROM diagnostic (2026-11-02)

Derived real source-locked GLBs using trimesh 4.11.1 / numpy 2.3.5:
- +3°: SHA-256 fd08d6f277d78f55d7b7ca3823f808587543f3f3e64c3d077ffd284b39af8172, 640012 bytes.
- −3°: SHA-256 385bf80875960cfd4c105ecb8a0d3466406ab370f12e66cec237ad081e5ffb8e, 640012 bytes.

Original mask source: authenticated canonical USA ROM-corpus artifact #13118909409 from run #41396846120, source-corpus manifest SHA-256 e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e. Exact original 64×64 PNG and binary-mask SHA-256 identities were checked again. Split membership comes from actual prior fixed "wheel-holdout.json" report, artifact #13120351488: first connected 16 masks and disconnected additional 19 masks (the single initial 1205–1220 window by itself has only ten distinct masks). The original fixed provisional 7:6 side camera at analysis/data/racer-inverse-side-provisional-1205.json and the existing fourfold triangle rasterization and source-alpha placement conventions were reproduced. Baseline full-model mean IoU **0.46002071** exactly reproduces the published source experiment.

| Diagnostic source family | Unchanged GLB | +3° parent hinge | −3° parent hinge |
|---|---:|---:|---:|
| First connected 16 | 0.55276425 | 0.54748542 | 0.55159519 |
| Other 19 binary-SHA-disjoint | 0.38192089 | 0.38421620 | 0.38285225 |
| All 35 unique source silhouettes | 0.46002071 | 0.45885356 | 0.45999188 |

+3° improved per-source mask IoU on **19 of 19 disconnected additional 2D masks**, but **worsened the fit on the connected first 16**. It is therefore useful as a *possible adjustable joint* hypothesis, **not** a reason to turn the model permanently or describe a character-likeness improvement. The fixed-camera logical 64px projected GLB alpha changes for +3° occupy 34 pixels, 32 in Y=0..15 and 2 in Y=16..31; none in Y≥32. For −3°: 38, distributed 31 / 7 / 0 / 0. These are model pixel differences, not source pixel changes.

Source masks, and the authored registry's timing/hold schedule, remain separate evidence classes. No live original-emulator PPU/OAM chronology, source-registered 3D joint/camera/physical contact, unseen pose holdout, likeness or release acceptance. Any fitting should jointly compare source shape and rigid translation with frozen camera, and require actual temporal capture before timing claims. In the canonical rig (#2832), wheel/spoke synchronization is a separate known mechanical issue: applying a fix only in the SCAD whole-scene composition would leave independent GLB exporter tire/rim nodes unrotated. Coordinate that work there, not in this optional parent-transform study.

## Validation

    python3 -m unittest tests.unit.test_art4k_experimental_frame_hinge

Pure-Python matrix and invalid-angle tests need only stdlib. Four scene/asset tests use optional numpy/trimesh and skip if unavailable. Local real-GLB export of both ±3° samples passed all five-source-parent and sixteen-source-material checks, and their bytes match the previously generated candidate hashes. Hosted PR checks and independent source review still required; no candidate GLB is committed to the repository or substituted for shipping artwork.
