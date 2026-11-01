# One-command evidence packet for the current ART-4K GLB export

**Offline research helper.** This consolidates existing source extraction and fixed-camera tools. It does not generate a new unicycle, prove its original 1994 pose, or update gameplay, rendering, graphics/owner acceptance or the release ledger.

Prerequisite: the **existing draft #2832** \`tools/art/export_articulated_unicycle.py\` generated an *unapproved* five-part GLB in a directory containing \`articulated_blockout_current.json\`, \`articulated_blockout_last_attempt.json\` and the immutable \`attempts/<id>/\` files. Its SCAD source must match the export's recorded SHA. The offline image stage requires optional NumPy, Trimesh and Pillow.

```sh
# Run in a checkout with #2832's exporter and source available:
python3 tools/art/export_articulated_unicycle.py \
  tools/art/candidates/unicycle_shared_rig.scad /private/ur-art4k \
  --rig-pose upright

# No manual GLB filename/hash/receipt selection: this command reads and
# verifies the actual successful current pointer and then performs the
# complete original-source projection and scoring.
python3 tools/art/run_racer_inverse_packet.py \
  --export-dir /private/ur-art4k \
  --source-scad tools/art/candidates/unicycle_shared_rig.scad \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --player p1 --frame 1205 \
  --out-dir /private/ur-first-source-score
```

**Guards:** the exporter last attempt must be \`succeeded\` and its ID must equal the immutable current pointer. Interrupted/failed newer exports are **not silently replaced with older successful assets**. Check exact source-SCAD SHA, GLB SHA, receipt SHA, source pose, immutable file paths, report schema, model/approval=false fields, model parent structure, original source-registered frame ID, pixel-aspect, camera witness and exact original source alpha anchor. The renderer rejects cropped silhouettes and the scorer independently revalidates source-original PNG pixel SHA. The source camera must remain \`provisional\` until actual camera-calibration evidence is validated in code.

The output is a unique \`attempts/<id>/candidate-4x.png\` and \`attempts/<id>/packet.json\` pair. The packet records original source representation, all input/GLB/SCAD/camera SHA, alpha projected silhouette score, model pose and explicit **no art approval** flags. Immutable files are published together, followed by an atomic \`racer_inverse_current.json\` pointer; \`racer_inverse_last_attempt.json\` records success, failure or interruption. Previous successful results are retained but not counted as freshly executed when the newest attempt fails. Keep this directory private because candidate/source visuals can be subject to separate rights and review constraints.

The camera example is intentionally **not fitted** to original 1994 animation and the existing default OpenSCAD \`upright\` source pose is only a 2026 blockout interpretation. The original-image frame must not be used as a final held-out test after tuning against it. The [retained pilot receipt](../../analysis/data/racer-inverse-first-source-pilot-20261031.json) used a *locally reassembled* five-part GLB, so **the next independently valuable test is this pipeline on the actual #2832 material-separated GLB**, comparing its silhouette and source transforms to that pilot. Do not promote a better single-frame IoU to a shipping art claim or an original-mesh recovery.

**CI policy:** the default repository unit suite executes only stdlib source/receipt/corruption controls; the synthetic full GLB publication tests are skipped if the optional offline dependencies are absent. A full original-raster render and source-1994 likeness qualification are not currently claimed.
