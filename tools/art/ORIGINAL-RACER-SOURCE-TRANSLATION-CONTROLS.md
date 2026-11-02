# ART-4K authentic original source translation-only diagnostic

This source-authenticated 2D control deliberately uses the **next original 1994 frame's own lowest visible-alpha midpoint** to shift the previous original frame. Consequently its movement estimate is *post-hoc and nonpredictive*: it measures how much changing 64×64 alpha could be described by translation under a source-known anchor, not original 3D motion, camera or the character's wheel contact point.

It belongs alongside merged [#3017](https://github.com/gamesbyian/UR-Recomp/pull/3017)'s real five-GLB pose-only changed-pixel benchmark and [#3020](https://github.com/gamesbyian/UR-Recomp/pull/3020)'s real source-owned ride phase-grid experiment. No new rig, viewer, renderer, scheduled lane, model parameter, sprite or replacement art.

## Exact current authentic original-ROM data

The source has 35 P1/P2 contiguous tracks and 109 actually adjacent per-player guest-frame edges. Only **9 tracks** exhibit any original binary silhouette change: 19 moving edges and 90 exact sprite holds. Original changed-pixel XOR count over all adjacent edges: **1,631**. When the source visibly shifts, every observed source-alpha anchor displacement is exactly one whole logical pixel horizontally: **ten +1px, seven −1px**; the other **two genuine silhouette-change edges** have zero anchor movement (P1 1219→1220 and P1 1305→1306).

By moving the **previous original binary mask** by that measured integer translation, with no morphological manipulation or 3D model:
- Predicted source changed pixel positions: **1,776**.
- Coinciding with the actual next frame's XOR positions: **1,057**.
- Source changed-pixel recall: **64.806867%**, precision **59.515766%**.
- **The translated previous source shape still differs from the next original shape at 1,293 pixel positions.** The 1,057 motion-XOR overlaps are *not* the same as a shape match. Retain both metrics.
- No false predicted motion on the 90 source-held edges, because their measured original anchor is identical.

This retrospective use of the **actual next source frame** is explicitly unsuitable as a predictive model acceptance criterion, nor does its 64.8% source-XOR overlap prove a 3D camera translation rather than different baked source artwork/animation. It is a necessary explanatory baseline for separating source appearance translation from real shape changes.

## Reproduction and trust boundary

```sh
python -m unittest tests.unit.test_audit_original_racer_translation_only_control
python tools/art/audit_original_racer_translation_only_control.py \
  --corpus /private/authenticated/source-corpus.json \
  --out /private/new/original-source-translation-shape-control.json
```

The existing original-ROM source workflow re-composes the canonical USA ROM, reopens and verifies all original source PNG bytes/identities/alpha hashes, recomputes 35 authenticated source binary shapes, and runs this extra source-only step without adding another expensive model render. The script refuses to interpolate half-pixel anchors, silently crop translated occupied pixels, or invent motion links across missing guest frames. It asserts the exact 109/19/90, 1,631/1,776/1,057/1,293 and 10+/7−/2 stationary source controls, and publishes a write-once numeric JSON report. Original source assets are retained only in the workflow's existing short-lived artifact, not added to git.

## Next decision

Future **genuine** source-registered articulated pose fitting should measure **new** model-generated shape change at the old source anchor, then assess model-driven rigid translation/world/camera separately, with both authentic 2D source frames as references. Use the two original moving edges with stationary anchors as particularly useful articulation/contact diagnostics. Preserve the 90 source hold controls and collect longer diverse original-ROM PPU motion sequences: only 9/35 current tracks contain positive motion evidence.

Every original-model camera, actual joint angle, 1994 guest-frame↔2026 rig-time mapping, owner likeness, release and ART acceptance remains unverified.
