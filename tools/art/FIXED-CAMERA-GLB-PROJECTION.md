# ART-4K fixed-camera GLB silhouette exporter

**Opt-in offline source-registration experiment, no approved art.** This tool reads the already-created **five-part articulated GLB** of draft [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832). It does not create a competing mesh or a native runtime renderer. It computes a transparent black-and-alpha **256×256** raster that is suitable for the fixed-coordinate alpha calibration scorer in \`tools/art/score_racer_candidate.py\` (PR #2933 until integrated).

The first provisional camera is \`analysis/data/racer-inverse-side-provisional-1205.json\`, with the **original registered P1 frame1205 lowest-alpha source anchor [67,76]** and a **guessed** 9.5 vertical logical pixels per 2026 model unit. The camera is an **unfitted hypothesis**, not independent evidence of the original 1994 3D camera. World +X is screen-right, world +Z screen-up, original source physical pixel aspect is 7:6. The result will naturally disagree with the source wherever the old OpenSCAD model is wrong. Preserve those disagreements.

On a workstation with \`numpy\`, \`trimesh\` and \`Pillow\` available:

```sh
# Obtain a verified GLB from the existing draft #2832 exporter.
python3 tools/art/render_racer_glb_projection.py \
  --glb /private/ur-art4k/attempts/<id>/articulated_unicycle.glb \
  --glb-sha256 '<actual-64-hex-GLB-file-sha>' \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --out /private/ur-art4k/registered-p1-1205.png \
  --receipt /private/ur-art4k/registered-p1-1205-receipt.json

# The receipt's candidate_png_sha256 becomes the scorer's required hash:
python3 tools/art/score_racer_candidate.py \
  --player p1 --frame 1205 --density 4 \
  --candidate /private/ur-art4k/registered-p1-1205.png \
  --candidate-sha256 '<receipt-candidate_png_sha256>' \
  --out /private/ur-art4k/registered-p1-1205-score.json

python3 -m unittest tests.unit.test_render_racer_glb_projection
```

**No per-pose auto-alignment:** source coordinates are derived directly from the manifest anchor and world scale. The same camera manifest must be used for all poses in one comparable family. Every world triangle is projected (including parent/child GLB transforms), filled into a hard silhouette mask and projected to four times each logical source coordinate; its screen-X model scale is reduced by 6/7 to honor original physical pixel aspect. No colour, shading, alpha trim, hidden asset generation or depth-dependent art paint is modeled. Source model GPU/renderer geometry is not inferred here. The rasterizer rejects an incomplete five-part hierarchy, altered GLB SHA, invalid camera basis, malformed camera source-attestation, nonfinite vertices, invisible models **and any clipped geometry** instead of auto-fitting/cropping. The PNG contains only binary alpha with transparent/black RGB. Offscreen use is limited to this research tool and is not included in normal game builds.

**Evidence distinction:** the camera manifest is marked \`provisional\`; \`source-calibrated\` is only accepted with a 64-hex source calibration receipt. Neither field is proof of likeness, and the tool's receipt carries explicit false original-model/owner/shipping claims. A render output PNG is atomically replaced after it has been fully encoded; the caller must use this invocation's generated SHA and receipt, never assume an older output means a failed render was successful. For a multi-asset production scheduler, retain immutable GLB/export receipts per #2832 and promote candidate-specific images and scores only after both hashes validate.

**Validation performed for the prototype:** local OpenSCAD 2021.01/Trimesh offline dependency availability was checked; the projected-mesh algorithm produced a valid 256x256 alpha mask from a synthetic five-part GLB, and a synthetic 20,480-triangle mesh required roughly 0.8 s on one test machine. **That is not a verified run of the real #2832 model or a source-fitted animation**. The focused source-code unit checks use synthetic meshes and are skipped when optional offline dependencies are unavailable in ordinary CI. A real art benchmark and exact camera calibration remain the next milestone.
