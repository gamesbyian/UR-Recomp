# Original 24-tick racer sprites: exact 2D review rail

The existing Pages **model-review** viewer already has an independently scrubbed original sprite rail alongside the *unapproved* five-parent GLB. This standalone export provides a higher-information **optional** source rail from the authentic 24 consecutive Mesen ticks 1601..1624, separately for both players. It does **not** change that viewer or deploy Pages in this PR.

`tools/art/export_original_mesen24_review_rail.py` requires the exact SHA-locked original USA ROM, retained original no-skip 24-tick Mesen archive and #3104's independently verified **48 uniquely matched** ROM frame-identity JSON. It checks actual source OAM/VRAM/CGRAM sprites against the original ROM's own 30-tile packed frame representation again, then exports **48 true 64×64 RGBA PNGs** with the *actual Mesen-selected CGRAM colours*, plus `source-poses.json` recording player, original bridge tick, original ROM frame ID, phase 0..23, orientation 0..63 and index/colour/PNG SHA-256. Index zero remains transparent. PNG encoder is deterministic and tested by independent zlib/CRC decoding; no image AI or invented 3D pose enters the export.

Run after #3104 is incorporated:

```sh
python3 -m unittest tests.unit.test_export_original_mesen24_review_rail
python3 -m tools.art.export_original_mesen24_review_rail \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --source-zip analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip \
  --pose-ids analysis/data/racer-original-mesen24-exact-ROM-pose-IDs-20261103.json \
  --out-dir /new/path/original-source-review-rail
```

The output directory must not exist. It is staged atomically only after all 48 source and ROM match checks succeed; existing review exports cannot be silently overwritten. Neither `manifest.json` nor `sprites.json` from the preexisting model viewer is changed. The exporter itself must pass exact-head CI before being treated as qualified.

## Deliberate next integration, not implicit approval

A viewer follow-up can incorporate this new manifest **as a second opt-in source-only timeline**, leaving the existing 1205..1220 stock rail and all five GLB selectors unchanged. Show original 1994 **frame ID, phase and orientation as integers**, and the explicit unknown camera/degree/rig mapping in the UI. Preserve 7:6 display pixel aspect, mobile 44px controls, and pixelated image scaling. A source-frame selection must **never silently select a 2026 GLB pose or modify material/geometry**. Set no owner-likeness flag. Include browser smoke checks for source/tick switching, independent GLB pose/camera state and missing/corrupt PNG manifest fallbacks before making this part of the current atlas publish.

The next model-fitting discriminator is to compare isolated wheel/crank versus fork/saddle GLB transforms with exact *phase-only* and *orientation-only* source-ROM sprite changes under a fixed projection, after controlling for authored 2D-only sprite changes. Neither original 1994 geometry nor calibrated 3D degrees is recovered here.
