# Presentation Density Contract

Status: implemented Windows x64 contract; maintenance/reference

## Why this exists

`SEMANTIC-SUFFICIENCY.md` now records the closed result of this work: Internal Render Scale is stable across authored Racer HD, stock fallback, evidence-backed widened world composition, regional-title replacement and every current host-owned Modern overlay/modal surface. No current Modern presentation surface requires a global 1x density clamp.

This document is retained as the implementation/maintenance contract for that closure. It does not authorize guest geometry, timing, simulation, or state changes.

## Ownership

High-density presentation is host-owned. The authoritative guest remains 256x224 at its normal cadence; Widescreen may expose the already-approved wider logical view, but density is a separate presentation axis.

The compositor owns three coordinate spaces explicitly:

1. **Guest logical space**: stock 256x224 coordinates and title-owned widened logical coordinates. Gameplay observation, OAM placement, course/world projection, timing and overlay anchors are expressed here.
2. **Presentation surface space**: logical coordinates multiplied by the active integer internal render scale where a renderer declares density support.
3. **Output/window space**: the final window/fullscreen target after display-mode, output-resolution and aspect policy. Scaling into this space must not feed back into guest or presentation state.

A future feature that has not declared presentation-surface support must fail closed rather than partially applying density. Current shipping Modern presentation consumers have completed that migration; do not reintroduce per-surface 1x clamps as an accidental fallback.

## Implemented shipping slice

Host-owned Modern overlays using logical anchors now share the same composition contract across pause/options/controls, run-data/timing overlays, Records/Local Runs, profile/progression continuation prompts, Quick Practice/onboarding surfaces and the remaining modal families.

Racer HD remains the authored-density control case. Evidence-backed widened world fields now use the same configured density through the generic nearest-density fallback when Racer HD declines the widened frame, without coupling density to logical view width. Regional-title replacement likewise owns an explicit integer-density transform over the canonical title frame.

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
- A new renderer that cannot prove all of its anchors, clipping and asset sampling are density-aware must fail closed and may not silently reinterpret a high-density surface. Existing shipping Modern renderers have completed this proof.
- Presentation density must not write WRAM/SRAM, alter controller input, advance timers, change replay/ghost selection, or affect completed-run/PB persistence.
- View width and density remain independent. Original and 16:9 views may each use any accepted 1x-4x Internal Render Scale; changing density never changes logical world extent.

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

The initial shipping consumers were the live run-timing HUD and the non-modal Recent, Quick Practice and Tour hint/banner surfaces. The same contract now covers the complete current host-owned modal/non-modal Modern UI family. Consumers use the canonical presentation-scale authority, verify it against the actual presentation surface, resolve logical anchors through the shared contract, and scale glyph rasterization with panel geometry. Their logical footprints therefore remain stable through 1x-4x, with no remaining direct-coordinate modal 1x guard.

Deterministic model coverage includes stock 256x224, widened 342x224, 1x/2x/3x/4x density, caller-reserved HUD bands, constrained-width compaction, minimum-size fail-closed behavior, and output-viewport projection. Native visual acceptance should remain bounded to representative migrated surfaces rather than turning every overlay into a screenshot oracle.

## Resize acceptance matrix

The deterministic contract is exercised across common Windows drawable sizes (640×480, 800×600, 1024×768, 1280×720, 1366×768, 1600×900, 1920×1080, 2560×1440 and 3840×2160) plus deliberately awkward 853×479, 1277×719, 1001×733 and 311×197 windows. The matrix covers fixed 256×224 and widened 342×224 logical surfaces, Original and Remastered output composition, and presentation densities 1x through 4x.

Acceptance requires logical overlay rectangles to remain invariant as drawable size changes, integer density to affect only the presentation rectangle, output projection to remain fully inside the already-resolved viewport, and constrained logical space to compact only down to the caller-owned minimum before failing closed. Letterboxing and pillarboxing therefore move/scale only the output projection; they cannot change title-space anchors.

## Stable fallback density

Internal Render Scale is now a fixed-scene presentation property rather than a signal that appears only on frames with an authored Racer HD replacement. When Remastered Racer HD is enabled, the host resolves the configured 1x-4x density from product state for every supported fixed scene. The Racer HD compositor still gets first refusal; if the current frame has no authored replacement, the host composes the untouched logical guest raster with exact nearest-neighbour integer expansion at the same density.

This removes density flicker across replacement/fallback pose transitions and gives Original fallback pixels an explicit deterministic sampling path. Widened world composition now preserves the configured density across the complete 342x224 logical field, including host-materialized margins. Regional title replacement also preserves the configured density by nearest-composing the canonical title frame, painting the verified Europe crop at the same integer scale, validating its logical-pixel digest, and restoring the canonical composed frame on failure.

## Sampling policy

Default policy is deterministic and deliberately boring:

- Original pixel art: nearest-neighbour when scaled by an integer presentation transform;
- Remastered/Reimagined assets: sample at their declared native density; do not downsample then re-upscale through the guest surface;
- Modern vector/glyph/UI primitives: rasterize directly at presentation density when supported;
- final presentation-surface to output-window scaling follows display geometry policy and must not change the internal logical layout.

Any later CRT/NTSC filter is a post-composition display treatment and cannot become the coordinate or density authority.

## Stop condition

This queue item is closed. Current Modern overlays share one explicit logical-to-presentation transform; widened world and regional-title presenters preserve the same integer density; deterministic coverage spans 1x-4x and representative resize/high-DPI surfaces; Authentic and guest-state authority remain unchanged. Future work must not reopen this contract merely to add readable-text reflow, fractional supersampling, shader redesign or CRT/NTSC display treatment.
