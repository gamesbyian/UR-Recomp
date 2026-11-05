# ART-4K: model-projection mirroring versus authentic upper red screen source

**Source-bound 2D sensitivity test, not recovery of the 1994 camera.** All original sprites were independently observed executing the authentic USA ROM under pinned MesenCE. Merged #3088 authenticates 40 original source 4bpp sprites to their completed original 2D framebuffer, including the original red player's **horizontal screen reflection** despite held OAM H-flip=false. Merged #3091 found the apparent 3D model pose ranking shifts dramatically when scoring red in the correct displayed orientation, yet it compared both blue and screen-reflected red to the **same** 2026 fixed-camera experimental projection. This experiment freezes an additional coordinate-system counterfactual before adding more 3D hinge angles.

## Two fixed, competing projection interpretations

1. `shared_model_projection`: blue and reflected screen-red are scored against the **same** five experimental 2026 GLB projected paint axes, measured previously under the *one provisional 7:6 side camera*. This is the earlier comparison premise.
2. `red_model_projection_reflected`: blue remains unchanged; the **five experimental model projected axes are mirrored for red as an entire arm**, with no per-frame decision or per-source parameter tuning. This tests whether the missing 2D red directional coverage is partly an inconsistent screen/model handedness convention. It is a mathematical 2D projection candidate only, not an authenticated 1994 opposite physical camera, material depth order, articulated rig or original red 3D skeleton.

All original observed red masks/colour pixels are mirrored to their **actual completed-screen 2D orientation** in **both** arms. No alternate source 1994 OAM phase is invented. Both arms use the same frozen original player-colour heuristic (from `tools/art/audit_original_racer_colourway.py`), top/bottom three nonempty colour rows, 7:6 physical pixel aspect, true ROM-derived CGRAM RGB and the five immutable real 2026 GLB painted-axis numbers from source run #41290041584 (`upright/pedal=+6.944131°`, `wheelie=+33.869252°`, `stunt=−43.167160°`, `bank=+9.272860°`). The original screen P6/PPU provenance is re-authenticated before the comparison; no ROM emulator replay or GLB render is necessary.

## Independently reconstructed original-source result (40 actual 2D observations)

| Frozen arm | Blue source angles gap >10° | Red source angles gap >10° | Combined >10° | Mean nearest projected 2D angle gap |
| --- | ---: | ---: | ---: | ---: |
| Shared model image orientation | 13/20 | 15/20 | **28/40** | **13.514623°** |
| Reflect model projection for red | 13/20 | 5/20 | **18/40** | **10.325687°** |

Both arms still have 40 original sprites, use the same source placements and colours, and leave all GLB meshes, camera files and original sprites unchanged. A fixed model projection reflection changes the red coverage assessment by ten source frames. That is a **37.5% decrease in mean red nearest-axis error** (13.622743° to 7.244871°), with blue unchanged. Unexplained blue intermediate 2D axes remain. The 2D closest-axis metric does not classify the genuine original animation pose; it ignores full silhouettes, material occlusion and varying source camera.

**Consequences:** An apparent excess of original missing intermediate negative 3D hinge angles under a single side model projection is partly a *projection handedness* confound. Before changing canonical #2832 GLB source, systematically test both plausible projected model orientations on the same authentic source 2D silhouette and chroma geometry, keeping the provisional camera and original source anchor registration frozen. A full-silhouette source comparison could further distinguish the candidates, but simply maximizing a 2D IoU after per-frame reflection would be circular. Original 3D camera, actual opposite side visibility, source painted-material segmentation, 1994 skeleton and owner likeness remain unknown.

## Reproduction and acceptance

The source-only module `tools.art.audit_original_mesen_live_camera_axis_sensitivity` verifies the original source ZIP, every original PPU/P6 source screenshot registration, the old real five-GLB numeric axis report and all 40 source pixel-colour chroma measurements. Its `--verify-committed` compares an immutable compact numeric receipt, while the fresh detailed output includes actual 40 original tick/player angles and per-arm gaps.

```sh
python3 -m unittest -v tests.unit.test_audit_original_mesen_live_camera_axis_sensitivity

python3 -m tools.art.audit_original_mesen_live_camera_axis_sensitivity \
  --source-zip /private/original-13217381754.zip \
  --verify-committed analysis/data/racer-original-mesen-live40-camera-axis-sensitivity-20261103.json \
  --out /private/new/live40-2026-camera-orientation-sensitivity.json
```

Actual original Mesen source run #41605614082, ZIP artifact #13217381754 SHA256 `709fbc2a1cd94b888d8ae0d43894c42c5d455bd968f6bc11f26e710f44e2788f`, original USA ROM SHA `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`, source MesenCE revision `a60e79feb4d6dcced5922d636f9211837d01e381`. Historical five-real-GLB projected axis summary in `analysis/data/racer-original-vs-glb-painted-axis-coverage-20261101.json`. Source-only tests and hygiene appropriate; no new heavyweight PPU/Windows/GLB workflow.

**Negative gates:** no 3D geometry changed, no 1994 camera/pose/material inferred, no original motion state labelled, no fit/withheld roles reclassified, no artistic owner approval and no Windows release QA credit. This study does not create another Pages viewer, model, colour-map selector or permanent CI job.
