# ART-4K 2026 fork/crown localized volume experiment vs original Mesen24

**Preregistered 2026 model-only controlled 3D reconstruction, not recovered 1994 production geometry or approved character art.**

## Why test this distinct parameter?

Earlier 2026 model changes affected the saddle's X span, center cup, mounted height, or entire upper-frame Z stretch. None tested the **cross-section of the upper fork/crown** independently of overall head height. The printed 1994 Nintendo/DMA manual reference inventory [official p. 14, p. 15, p. 16](../../docs/HD-RACER-MANUAL-MULTIVIEW-REFERENCE-20261105.md) shows rounded/voluminous fork, axle/hub and stem assemblies from near-front and near-wheel oblique views. These printed 2D images **do not supply a calibrated 3D width, production mesh or exact camera**. Consequently the signed shape controls below are symmetrical, frozen in advance and can be rejected even if an isolated pixel metric rises.

Keep the **same source-owned 2026 five-parent, sixteen-material GLB** exported from draft #2832, same historical SCAD authoring SHA and same source-authenticated USA original ROM 2 × 24 no-frame-skip Mesen PPU image sequence, same first-tick anchor and provisional 7:6 camera. Never replace the original authoring SCAD, GLB or existing Pages default.

## Geometry: one localized symmetric crown cross-section, two frozen signs

The source **2026** OpenSCAD fork centerline around the upper yoke and stem is
`(z,x)=(.83,-.10)→(1.39,-.17)→(2.09,-.25)`, in *GLB mesh local* authored units, with the fork's median transverse Y = 0. This source line is used for **both** racer colours and every original tick, not fitted to pixels or guessed original anatomy.

Use `CROWN_CENTER_Z=1.42`, `CROWN_HALF_BAND=.56`, so the intervention is identically zero outside `0.86<z<1.98`. For each original fork child mesh (all four material groups, not only blue):
```
u = abs((z - 1.42)/0.56)
w = (1 - u*u)**2 if u < 1 else 0
f = 1 + (signed_scale - 1)*w
x' = centerline_x(z) + f * (x - centerline_x(z))
y' = f*y
z' = z
```
Only predeclared `signed_scale = 0.90 or 1.10` are accepted, crossed with each **same historical mechanical world-level-saddle wheel law**: source ROM phase × 15° or chronological fixed +24°/tick. Thus only **four new 2026 geometry arms**, both roles equally. The Z origin, fork end junctions and saddle mount/pivot remain untouched, as do real wheel/rim/tire/crank node and mesh geometry, all source vertex RGBA, triangle face indices and parent world transforms. Material colour seams are transformed by exactly the same function in their source-owned shared coordinates. All original fork geometry arrays are restored **exactly** when projection finishes or throws.

## Evidence and no overfitting

The same existing `score_original_mesen24_full_saddle.py` source producer evaluates the four new profiles on the **same all-48 original PPU masks** and all **23 actual consecutive source change edges per racer**. Preserve historical 24 geometry/model arms and both source roles' previous metrics **exactly**; the original 2D source rigid-rotation null remains separate from new real GLB geometry. Record separately each original player's 24-frame pooled static alpha IoU, one-vote-per-unique-original-binary-shape static IoU, real 23-edge change IoU, and the *actual original source upper-event* y0:14 TP/FP/FN and projected 2026 fork-versus-saddle contribution. Use canonical mainline six-objective source Pareto and match each new crown arm only to its **same-wheel-drive** world-level-saddle control before inferring anything about local mesh contribution.

**Decision rule:** If crown expansion improves static alpha but worsens true source motion, or helps one racer while harming the other, report **mixed** and do not promote a globally 'winning' model or physical 1994 thickness. Equally, a positive pixel match cannot determine where original red/blue surface paint or 1994 rim/hub fork ownership lay. Do not pick per-player geometry from these retrospective reference frames; official manual print views still need exact crop SHA, perspective-tagged 2D landmarks and separate visual review. Stop after these frozen two signed values unless independent original evidence identifies another physically meaningful contour.

## Verification

- `python3 -m unittest tests.unit.test_experimental_fork_crown_volume tests.unit.test_score_original_mesen24_full_saddle`
- Existing exact-head full tooling and hygiene, and existing real Linux OpenSCAD/GLB/Chromium Visual Atlas PR pipeline with original 48 Mesen source PPU frames and original per-part motion. No new GHA workflow or another ROM recording.
- Tests must demonstrate all 4 actual fork source materials manipulated in memory, single source authoring centerline, fixed upper-band edges, zero change to wheel/hub and saddle mount, unchanged colours and face lists, and **exact rollback even after exception**.
- Keep draft #2832 and source parent #3124 **unapproved**. No Windows game/default material/art switch, original 1994 renderer/camera/mesh/joint recovered assertion, independent artist acceptance, or ART/release ledger credit.

If new expansion/contraction is underdetermined by authentic source images, report a negative result. That is a useful end condition, not a pretext for endless localized parameter sweeps.
