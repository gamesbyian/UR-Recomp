# Authenticated original racer 2D temporal cadence and frame placement

**Purpose:** make the original 1994 ROM-composed first-family frame sequence usable as a *time-indexed* calibration target without promoting an invented 3D pose or a camera solution. The source owner remains [the original pixel-corpus auditor](build_racer_source_pixel_corpus.py); this adds time structure rather than copying its source-art files.

`tools/art/audit_original_racer_cadence.py` reuses the actual first-family `P1/P2 guest frames 1205..1220` retained 64×64 PNGs and original sprite representation registry. It checks the exact USA ROM identity claimed by the independently verified retained manifests, independently decodes every source PNG, verifies its binary silhouette and RGBA SHA, and recalculates each source's registered contact as the **midpoint of the lowest occupied alpha row**. That semantic contact is **not a physically proven wheel-to-ground collision coordinate**.

## What the report actually measures

The JSON emits each exact original frame and source identity in temporal order, groups contiguous equal binary silhouettes into source-shape *holds*, and describes each of the 15 frame-to-frame edges per player in two ways. Raw XOR and alpha IoU measure the actual original 64×64 pixels. Contact-aligned XOR and IoU first translate each independently registered mask to the same P1:1205 witness location, thereby separating original 2D placement from residual alpha-shape change. The same 7:6 source pixel-aspect context applies to all frames. **The alignment uses an original-source coordinate only and never searches for a shift that maximizes IoU.** Any unsupported half-pixel parity or pixel clipping fails closed; no resample, crop or guessed registration is accepted.

The report also counts which guest-frame boundaries have changes in P1, P2, both or neither, without claiming coupled 3D animation. Original frame time is an index from the recorded guest-frame window. The tool does not assert real milliseconds or SNES exact subframe cadence, does not assign any original frame to the 2026 OpenSCAD `upright/pedal/wheelie/stunt/bank` pose labels, and does not produce an independently verified novel camera, 3D body motion, owner likeness or shipping-art approval.

## Run

```sh
# From repository root, no original ROM or 3D model dependencies required.
python3 tools/art/audit_original_racer_cadence.py

# For one immutable receipt use an unused filename in an existing directory.
python3 tools/art/audit_original_racer_cadence.py \
  --out /private/ur-art-corpus/source-temporal-cadence-20261101.json

python3 -m unittest tests.unit.test_audit_original_racer_cadence
```

The existing immutable no-replace report helper prevents overwriting a foreign destination. The report contains **hashes and numeric 2D measurements only**, no copied original PNG, ROM, GLB or other binary artwork. ROM-free synthetic tests cover repeated holds, returning-to-old shapes, palette-only changes, 2D source shifts, forged alpha/registry identity and missing or duplicate source frames. A positive integration test recomputes the complete first-family authentic evidence from the actual already-retained original PNG files.

## How to use this for the rig

Use the source **hold boundaries and 2D placement deltas** to choose which temporal transitions deserve actual calibrated 3D reconstruction. The measured source-frame occupancy variation can guide validation of crank/fork/saddle/wheel silhouette acting only after a defensible correspondence between original sprite family and model rig phase is obtained. Neither coincident 2D shape changes nor disjoint alpha masks prove novel 1994 source camera, orientation or 3D articulation. Keep original motion evidence independent of the [unpaired GLB pose similarity matrix](REAL-GLB-POSE-SIMILARITY-MATRIX.md), the [private source-family split freezer](FROZEN-SOURCE-FAMILY-SPLITS.md), the [canonical draft rig #2832](https://github.com/gamesbyian/UR-Recomp/pull/2832), and the existing [single 3D review website](model-review/README.md).
