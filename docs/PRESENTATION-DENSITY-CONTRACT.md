# Presentation Density Contract

Status: bounded Windows x64 implementation contract

## Why this exists

`SEMANTIC-SUFFICIENCY.md` records an intentional asymmetry in the current product: Internal Render Scale is acceptance-backed at 2x for Racer HD, while widened world composition and logical-coordinate Modern overlays remain at 1x until their renderers own the required transforms. `WORK-QUEUE.md` consequently keeps high-density overlay composition and deterministic sampling/filter policy open under Presentation polish.

This document turns that gap into a finite implementation/acceptance target. It does not authorize guest geometry, timing, simulation, or state changes.

## Ownership

High-density presentation is host-owned. The authoritative guest remains 256x224 at its normal cadence; Widescreen may expose the already-approved wider logical view, but density is a separate presentation axis.

The compositor owns three coordinate spaces explicitly:

1. **Guest logical space**: stock 256x224 coordinates and title-owned widened logical coordinates. Gameplay observation, OAM placement, course/world projection, timing and overlay anchors are expressed here.
2. **Presentation surface space**: logical coordinates multiplied by the active integer internal render scale where a renderer declares density support.
3. **Output/window space**: the final window/fullscreen target after display-mode, output-resolution and aspect policy. Scaling into this space must not feed back into guest or presentation state.

A feature that has not declared presentation-surface support remains on the existing 1x path. Do not silently multiply only part of its geometry.

## First shipping slice

The first high-density composition slice should cover host-owned Modern overlays that already use logical anchors and contain no simulation authority: pause/options/controls, run-data/timing overlays, Records/Local Runs, profile/progression continuation prompts and Quick Practice/onboarding surfaces.

Racer HD already owns its independent density transform and is the control case. Widescreen world margins remain on their current path until the world compositor owns the same explicit transform; this slice must not couple overlay density to logical view width.

For an integer render scale `S`:

- every overlay vertex/rect anchor `(x,y)` maps to `(S*x,S*y)` in presentation-surface space;
- clip/scissor rectangles use the same transform;
- integer source-pixel assets use nearest-neighbour sampling unless the asset explicitly declares a higher-density source;
- text/glyph rasterization may use a density-aware source, but baseline, advance and logical bounds remain anchored in logical space;
- hit/navigation semantics remain model-driven and independent of rendered pixel density;
- output/window scaling happens after overlay composition.

No overlay may infer `S` from output resolution. Internal Render Scale is the only density authority.

## Fail-closed rules

- Authentic mode remains on the established authentic presentation path and acquires no Modern overlay authority.
- Unsupported or invalid render-scale values fall back through the existing settings policy rather than creating fractional transforms.
- A renderer that cannot prove all of its anchors, clipping and asset sampling are density-aware stays at 1x.
- Presentation density must not write WRAM/SRAM, alter controller input, advance timers, change replay/ghost selection, or affect completed-run/PB persistence.
- View width and density remain independent. 4:3 at 2x and Widescreen at 1x are both valid states.

## Deterministic acceptance matrix

Use one fixed scripted scene for each representative overlay class and compare logical layout plus guest state at 1x and 2x. At minimum:

| Surface | 1x | 2x | Required invariant |
| --- | --- | --- | --- |
| Pause/Options | capture | capture | same selected row, same logical bounds |
| Controls/rebind | capture | capture | same binding model/capture state |
| Live timing/run data | capture | capture | same authoritative time/delta values |
| Records/Local Runs | capture | capture | same course/run selection |
| Resume/Restart Tour | capture | capture | same continuation policy/state |
| Quick Practice/Help | capture | capture | same route/selection |

For every row, require:

1. guest WRAM/SRAM and promoted semantic state equality at the same guest frame;
2. identical host model/selection state before rasterization;
3. 2x overlay geometry equal to the exact integer transform of the 1x logical geometry;
4. no clipping introduced by the density transform at representative 4:3 and Widescreen logical widths;
5. fresh-process persistence of the selected Internal Render Scale through the existing settings authority;
6. Authentic capture unchanged by the Modern density setting.

A screenshot-only visual comparison is insufficient: retain machine-readable logical bounds/clip rectangles alongside representative PNG evidence so failures distinguish layout-transform bugs from font/asset raster differences.

## Implemented composition seam

The reusable composition seam lives in `native/product/modern_overlay_composition.*`. It resolves a Modern overlay in three explicit spaces without learning title-specific HUD pixels:

- a caller-owned logical surface plus reserved edge bands;
- an exact integer-density presentation rectangle;
- a deterministic projection into the already-resolved output viewport.

The resolver anchors against the usable logical region, clamps only when the caller supplies a smaller-but-usable minimum, and otherwise fails closed when reserved stock content plus margins leave insufficient space. Density never changes logical placement. The same logical rectangle therefore produces exact 1x/2x/3x/4x presentation transforms while final window/output projection remains independent.

The first shipping consumers are the live run-timing HUD and the non-modal Recent, Quick Practice and Tour hint/banner surfaces. They use the canonical presentation-scale authority, verify it against the actual presentation surface, resolve logical anchors through the shared contract, and scale glyph rasterization with panel geometry. Their logical footprints therefore stay stable instead of shrinking at 2x-4x. Interactive/modal product surfaces that still use direct physical-pixel coordinates remain on the existing fail-safe 1x path; removing that guard is permitted only surface-by-surface after migration to this contract.

Deterministic model coverage includes stock 256x224, widened 342x224, 1x/2x/3x/4x density, caller-reserved HUD bands, constrained-width compaction, minimum-size fail-closed behavior, and output-viewport projection. Native visual acceptance should remain bounded to representative migrated surfaces rather than turning every overlay into a screenshot oracle.

## Sampling policy

Default policy is deterministic and deliberately boring:

- Original pixel art: nearest-neighbour when scaled by an integer presentation transform;
- Remastered/Reimagined assets: sample at their declared native density; do not downsample then re-upscale through the guest surface;
- Modern vector/glyph/UI primitives: rasterize directly at presentation density when supported;
- final presentation-surface to output-window scaling follows display geometry policy and must not change the internal logical layout.

Any later CRT/NTSC filter is a post-composition display treatment and cannot become the coordinate or density authority.

## Stop condition

This queue item is closed when the representative Modern overlays above have one shared explicit logical-to-presentation transform, deterministic 1x/2x acceptance with retained machine-readable geometry, and Authentic/guest-state invariants. Do not broaden the work into arbitrary fractional supersampling, shader redesign, CRT simulation, or Widescreen world-renderer refactoring.
