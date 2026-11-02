# ART-4K original-wheel disk vs 2026 blue material

**Experimental evidence only. No original 3D anatomy, 1994 camera or shipping likeness approval.**

This continuation of the original-source paint work tests a narrower hypothesis than “the fork needs to be twice as thick.” The 2D original P1 red / P2 blue high-chroma region visibly overlaps the wheel/hub, while the unapproved 2026 model's BLUE material is associated primarily with the fork/frame. Their 2D centroids and painted area therefore cannot be treated as corresponding anatomical landmarks without further evidence.

## Measurement and anti-oracle rules

The actual source is the retained ROM-authenticated 41-RGBA/35-binary-silhouette/59-reference PNG corpus, read from the exact original artifact ZIP. The existing original wheel-ring detector first validates the original ROM source manifest and every PNG/decoded RGB/alpha/binary mask digest; the new tool separately computes the high-chroma pixels with the **integer-safe** original per-player classifier and independently re-verifies each PNG/RGBA/colour source pairing. It retains **all tied seven-pixel grey wheel-ring centres**, rather than choosing the one that makes a model fit.

Define a region relative to that 2D original ring centre: (1) all painted pixel centres inside a radius-seven wheel disk, (2) painted pixels at or below the wheel's topmost point, (3) painted pixels at or below the axle row. For the original source, each authentic red/blue RGB variant gives an interval over all its ring-centre ties. These variant intervals are averaged **within one binary silhouette**, and the resulting 35 binary silhouettes each have exactly one vote.

For the 2026 model, load the *exact historical unapproved five-part/16-material GLB bytes* under the frozen provisional 7:6 source-raster camera; the existing two-sided depth renderer classifies genuinely visible BLUE material under the +world-Y or -world-Y hypothesis. Use the already-authored 2026 frame-hinge grid and original source 2D colour-axis angle to choose the model hinge, with no target-silhouette fit or frame order. The source wheel-disk's **same seven-logical-pixel radius** is applied around the projected model axle. This is a matched 2D region test, not an inference that the 1994 model had any particular physical wheel radius.

## Actual original-ROM and real GLB preliminary result

Offline exact historical original 41-image source/2026-GLB pilot, one vote per distinct 35 binary masks, original wheel centre ambiguity fully retained:

| Relative to an original-equivalent 7px wheel disk | Original, worst to best tied-centre mean | Experimental 2026 blue material |
|---|---:|---:|
| Painted fraction inside full 7px wheel disk | **0.5910–0.5956** | **0.2968** |
| Painted fraction at/below wheel top | **0.7706–0.7728** | **0.3431** |

The source ring-interior fraction is greater than the model's BLUE disk fraction for **35/35 original silhouettes**, even at the smallest source candidate. First16 mask source disk 0.6037–0.6113 versus model 0.3008; additional19 0.5803–0.5823 versus model 0.2934. The source wheel-top band also exceeds the model in 35/35. A source-colored pixel inside the disc is NOT proof the original wheel itself is painted; it may be a spoke, pedal, fork, hub, another object projected over the wheel, or simply the model-facing camera/material hypothesis being incorrect.

Crucially, the original palette/paint mask may cover more than the modern model's single BLUE material. The earlier retroactive source/model centroid mismatch (average 5.82–5.90 physical screen pixels) and corrected source/model minor-axis spread excess (1.92×) are consistent with this more specific *part-correspondence* concern. **Do not translate the wheel, inflate fork thickness, reinterpret original 3D geometry, or approve shipping art on this basis.** The true old-game camera and timing remain unverified.

## Reproduction

Use the original SHA-pinned source corpus ZIP from run #41396846120, historical upright 2026 GLB SHA efdc8425..., original painted 2D axis receipt SHA 78f42042..., frozen camera SHA 1261016b..., and optional SHA-disjoint original family split aa86e133.... Source pixel payloads remain in private inputs; output is a numeric JSON ledger only.

    python3 -m unittest tests.unit.test_audit_original_racer_paint_wheel_disc
    python3 tools/art/audit_original_racer_paint_wheel_disc.py \
      --corpus-zip /private/source/original-rom-verified-source.zip \
      --glb /private/model/historical-upright.glb \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --source-chroma /private/source-chroma-axes.json \
      --family-split /private/source-family.json \
      --view-y 1 \
      --out /private/new/wheel-disk-material-comparison.json

Pillow, NumPy and Trimesh are optional for the actual source/GLB evaluation; ROM-free synthetic region/uncertainty tests use standard Python only. The existing no-replace publisher rejects overwriting evidence. No new GLB, viewer, recurring workflow or Windows game change.


## Above-wheel-only centroid falsification test

The same script now also emits a paired whole-colour vs strictly-above-wheel-top centroid test. It keeps the original rim centre candidate and the original 7:6 horizontal screen-pixel convention for both measurements. A pixel at y >= wheel_y-7 is explicitly excluded from the above-rim subset. The original source part of each distinct RGB variant and each tied wheel-centre candidate is retained in the report, and the model uses the exact posed existing GLB axle and frontmost BLUE material. The model centre is **not** moved by optimizing silhouette overlap or colour overlap.

The historical real original 41-RGBA/35-binary-source-mask pilot gives these **mean 2D physical-pixel centroid-vector distance intervals**, carrying all tied original wheel centres without selecting a favourable candidate:

| Equal vote per source binary mask | Whole original paint vs model BLUE | Paint strictly above wheel rim vs model BLUE strictly above rim |
| --- | ---: | ---: |
| All 35 | 5.82338840–5.89797063 | **2.80567018–2.86254340** |
| First16 | 6.10315691–6.22937399 | 3.45011560–3.56819340 |
| Additional19 | 5.58779387–5.61889411 | 2.26297931–2.26831182 |

This is an independent conditional segmentation experiment: removing coloured pixels near/inside the ring cuts the *centroid disagreement magnitude* nearly in half in the 35-source aggregate. Above-wheel centroid mismatch remains, especially in the first16 family, and source-camera, original palette anatomy, sprite pose and 1994 joint geometry are all unproven. A lower centroid discrepancy is NOT evidence that the excluded pixels are actually a coloured wheel; other components can overlap this region in 2D. The check specifically cautions against widening the fork, globally translating the wheel, or assigning every red/blue source pixel to one model BLUE material based on an in-sample fit.

A complete full-binary-mask/variant/ring-tie numeric initial above-wheel receipt is retained with SHA256 9adfcd235fc807bb7477dc5f4aeb528f71cdfab88066faa99c809e979543abcb. Its source-weighted summary is descriptive, not original-1994 animation or camera approval. The now-executable producer emits fresh source-verified 2D/GLB numbers and includes ROM-free controls for exact centroid cutoffs, tied centres, and invalid empty subsets.
