# Local 2026 spoke support: projected pixel-scale experiment

This work follows unapproved research-only [#3172](https://github.com/gamesbyian/UR-Recomp/pull/3172) on the single authored five-parent / sixteen-material **2026** Uniracers blockout. Its exact upright GLB SHA is `d83a39b805107eb309d3f56db8d5aeb77f435038170005fd5d15c0c45ed4c94a`. The original 1994 USA ROM, printed manual source pixel planes and original gameplay 3D geometry are **not** inputs.

The one 2.0-width source mesh experiment widens only `rim_and_hub__material_2`, eight original spoke solids, while preserving Y depth and polar wheel radius. The new counterfactual can be physically fuller in 2026 model units yet **invisible** at SNES source resolution if sampled from an unfavourable viewpoint. It therefore needs a deliberate preliminary *model-only* screen-pixel visibility test before spending original-source CI time.

`python3 -m tools.art.audit_source_spoke_blade_screen_support --glb /private/upright-d83a39b805107eb3.glb --out /private/spoke-visibility-64px.json` renders **only the isolated spoke material** as an unoccluded triangle-union 2D mask at 64×64, 128×128 and 256×256. The illustrative 2026 model-centred `[−1.05,+1.05]` X/Z cropping window and camera yaw **0°, 30°, 60°, 90°** are frozen. A yaw 0 views the wheel face; 90 is edge-on, with no attempt to reproduce original game PPU semantics or true print p15 camera. No other original 2026 part is substituted, coloured, moved or fitted.

Independently exercised direct exact-source real GLB triangle projection with Pillow/NumPy/Trimesh on the unchanged and fixed bladed support:

| Unoccluded 2026 source spoke material at 64px | Original narrow rods | One wider proposed support | New pixels | Removed pixels |
| --- | ---: | ---: | ---: | ---: |
| Source-model face-on yaw 0° | 431 | 509 | **78** | 0 |
| Source-model oblique yaw 30° | 415 | 478 | **63** | 0 |
| Source-model oblique yaw 60° | 332 | 393 | **61** | 0 |
| Source-model edge-on yaw 90° | 134 | 134 | **0** | 0 |

These are projected **model-support pixels** within the unoccluded 2026 spoke mesh, **not** original 1994 source alpha fit, appearance on a fully composited unicycle, depth-visible material colours, a sprite-scale fidelity score, render antialiasing or rig animation score. The shape has a testably relevant wheel-face effect and appropriately vanishes from edge-on view when the original Y thickness is unchanged. A later source-registered full-scene camera/printed p15 crop with actual first-party landmark pixel coordinates must judge whether these supports are visible and historically faithful after hub/tire/fork occlusion.

The scorer fails closed on any different GLB source SHA, unbounded angle/grid and invalid triangles; it emits only source-model 2D pixel counts, with every 1994 camera, mesh/material part identity and owner art/Windows release approval **false**. Keep on the **unapproved** #3124 experiment branch; do not merge the widened spokes into game art, invent the original printed spoke count, or undertake additional arbitrary radial width sweeps without new independent source evidence. This probe does not replace the canonical original Mesen24 six-objective GLB scorer.
