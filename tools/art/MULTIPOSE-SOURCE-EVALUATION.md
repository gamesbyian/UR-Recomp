# Source-shape-weighted multi-pose evaluation

**Stage:** first-family offline diagnostics only; no genuine independent 3D viewpoint, model fit, final art or withheld-family validation has been certified. This tool extends [source-registered inverse graphics](../../docs/HD-RACER-INVERSE-GRAPHICS-SPEC.md) and existing \`build_racer_pose_equivalence.py\` semantics. It does not replace gameplay pose registration, historical native HD acceptance or the artist review gate.

The first available 1994 raster study contains **32 P1/P2 observations, 14 retained PNG filenames, and 10 distinct decoded RGBA source hashes**. Training all 32 frame slots with equal weight would overvalue the seven-frame and ten-frame repeated holds. The new diagnostic computes per-frame source-vs-model alpha scores using the existing [fixed-source scorer](REGISTERED-SILHOUETTE-CALIBRATION.md) and aggregates each **exact original 64×64 binary source mask** to one unit of weight. It also groups palettes that use exactly the same original source silhouette. A source shape that appears on both calibration/fit and diagnostic splits is **rejected**, regardless of its frame number, file name, palette identity or candidate art. This prevents a trivial duplicated hold being described as an unseen result.

To run after producing **per-frame independent** [immutable evidence packets](RACER-INVERSE-PACKET-RUNBOOK.md) for the existing ART-4K SCAD model:

```sh
cat > /private/ur-art4k-suite/manifest.json <<'JSON'
{
  "schema": "UR-RACER-MULTIPOSE-SCORE-SUITE/1",
  "packets": [
    {
      "role": "fit",
      "packet_path": "one/packet.json",
      "packet_sha256": "<exact SHA256 of one/packet.json>",
      "candidate_path": "one/candidate-4x.png",
      "candidate_png_sha256": "<exact SHA256 of candidate>"
    },
    {
      "role": "diagnostic",
      "packet_path": "two/packet.json",
      "packet_sha256": "<exact SHA256 of two/packet.json>",
      "candidate_path": "two/candidate-4x.png",
      "candidate_png_sha256": "<exact SHA256 of candidate>"
    }
  ]
}
JSON

python3 tools/art/aggregate_racer_pose_scores.py \
  /private/ur-art4k-suite/manifest.json \
  --out /private/ur-art4k-suite/multipose-score.json
```

The example is a *template*: use actual independently generated packets from \`run_racer_inverse_packet.py\` and genuine source alpha shapes with **different** binary SHA across roles. Do not use frame1205 in fit and its visually identical 1206 as a diagnostic. File paths must remain beneath the manifest root, reference exact submitted SHA, and never overwrite source files. Each packet is SHA-verified, must carry the correct unapproved ART-4K schema and source representation, its candidate PNG hash must match the projection packet and the source scorer's result must be reproducible against unchanged original PNGs. All frames in a suite must descend from the same immutable **shared OpenSCAD source SHA**; separate GLB hashes are allowed for genuinely different rig poses and phase/export attempts.

The report contains original binary source hash groups, membership by player/frame, arithmetic mean within each shape family, then **equal-shape-weighted mean** IoU and physical-pixel Chamfer per role. It reports candidate-mask diversity within one identical-source family: a reason to examine static pose/cadence inconsistency, not independent evidence of new characters. Different camera manifests may be present because source OAM anchors change; the tool **does not certify a single physically calibrated camera**, and you must inspect source-camera consistency separately before attributing cross-pose fit to geometry.

The \`diagnostic\` role deliberately does **not** mean genuinely unseen 3D camera or independent animation family; all currently retained original P1/P2 pixels derive from a short same-family 16-frame window. For an authentic withheld-family result, first import and SHA-authenticate an independent source capture (e.g. verified 1230–1239 or 1244–1252 rasters) with the actual source extractor, extend the corpus with a separate declared lineage, then **freeze** the split before fitting. The evaluator currently **rejects frames outside 1205–1220** rather than silently treating other native PPU layers or screenshot crops as equivalent inputs.

Normal GHA tests remain ROM-free/stdlib. The optional real multi-pose GLB export/render occurs off CI, using existing #2832/OpenSCAD, unlicensed original/retained raster rules and immutable SHA receipts.
