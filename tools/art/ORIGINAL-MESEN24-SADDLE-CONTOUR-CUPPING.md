# ART-4K: 2026 saddle contour cupping vs genuine original Mesen24

**Status: experimental 3D geometry proposal, not original 1994 model recovery or approved character art.**

## A single new geometric question

The previous `0.90 / 1.10` saddle experiment uniformly scaled the **entire** authored 2026 saddle along its local longitudinal X axis. That leaves the specific **curvature of the central seat bowl** unresolved. The existing source model already has a multi-section saddle with elevated rear/front and a lowered central section. This experiment isolates whether the shape of that center cup, rather than overall saddle length, contributes to its poor upper-source fit.

Keep the **one** authentic, SHA-authenticated five-parent/sixteen-material 2026 GLB, its existing source SCAD SHA, original 48-frame (two racers × 24 genuine adjacent Mesen ticks) PPU evidence, frozen 7:6 provisional camera, original source ROM phase/orientation reports and fixed first-tick source alpha anchor. Do not create a replacement rig or adjust the camera per player. This is an explicitly provisional hypothetical sculpture, **not** an inference of the original 1994 artist's mesh.

## Preregistered source-local sculpt

Only two signed center-cup offsets, **−0.08 and +0.08 2026 model units**, may be compared. Negative deepens the central concavity, positive softens it. Both are independently compared under the two already frozen wheel laws, source ROM phase×15° and +24° per actual chronological tick, on **both** racers, with the same existing +15° saddle control held in world orientation.

For each of the **two original saddle material meshes**, use one **joint** original saddle X/Z bounding box. Define `x_n=(x−midX)/halfWidth` and `z_n=(z−bottomZ)/height`, then:

```
W_x = (1 - clamp(x_n, -1, 1)^2)^2
u   = clamp((z_n - 0.20)/0.80, 0, 1)
W_z = u^2 (3 - 2u)
z'  = z + signed_offset * W_x * W_z
x'  = x,  y' = y
```

The source saddle's **outermost fore/aft tips** have `W_x=0`; the **bottom 20% of all-saddle source Z** has `W_z=0`, and the existing mount, parent matrix, fork, wheel, crank, material RGBA and triangle-face topology remain untouched. Using common bounds for both saddle paints prevents artificial seams at coincident source vertices. The original vertex buffers are restored **exactly even when rendering raises an exception**; no GLB or SCAD file is written. This is a shape-only counterfactual of the present 2026 model.

## Exact evidence and stopping criteria

The existing `score_original_mesen24_full_saddle.py` now adds four fixed, separately named arms, leaving all previously published original 2D and existing real-GLB controls intact. Same current real original ROM 48-image chronology, per-player 19/23 SHA-distinct original binary shapes, upper/middle/lower projected source bands, 23 real source XOR-alpha motion edges, and source upper-event real five-parent GLB OR/unique-part accounting. No per-role/frame selected degree, contour or image-space fit.

Compare each new contour only with the existing **world-level saddle** arm under the *same wheel law*, using the canonical six-objective source Pareto analyzer (#3150) and the matched-control delta extension (#3154 once qualified). Judge static pooled alpha, equal-vote original distinct-shape alpha, 23-edge real temporal alpha and upper-band event TP/FP/FN separately. Require all existing arms' metrics to match their prior measured source run, preserving actual provenance and original 1994 nonapproval flags.

A larger static IoU with worse real change-edge evidence is a **mixed** result. Different 'winners' for blue and red do not establish a common historical saddle. An apparent success on retrospectively inspected original frames cannot be treated as a prospective blind source-family holdout. Report the numeric negative if neither signed sculpt offers a robust same-control gain. Do not promote a new default asset or ART/Windows gate on source silhouette alone.

**Qualification:** stdlib pure-geometry and optional real Trimesh rollback tests, exact-head full tooling/hygiene, same existing Windows Visual Atlas real OpenSCAD/GLB/Chromium source job (without a new emulator/re-export workflow), independent source/geometry review, and **separate owner visual likeness approval** before any shipping art change.
