# Display and Presentation Policy

Last updated: 2026-10-03

This document owns the product-level relationship between the SNES logical raster, pixel aspect, overscan, logical view width, host output geometry, filtering, and presentation refresh.

The policy exists to prevent several historically entangled concepts from collapsing into a single "16:9" or "resolution" switch.

## Status

The architectural policy is accepted for implementation.

Exact numeric transforms and final user-facing labels remain subject to validation against retained Uniracers reference captures and the project's deterministic rendering fixtures. Validation may tune constants or naming; it must not collapse the separate policy axes defined here.

## Core rule

Treat these as independent coordinates:

1. **Guest logical raster** — authoritative SNES presentation coordinates and guest-owned animation/state timing.
2. **Display geometry / pixel aspect** — how one guest logical pixel is mapped horizontally and vertically for presentation.
3. **Logical view** — how much game world is intentionally exposed, such as Original, 16:9, ultrawide, or Adaptive.
4. **Overscan / safe area** — which logical rows or margins are intentionally shown or cropped.
5. **Graphics representation** — Original, Remastered, or Reimagined presentation assets.
6. **Filtering / display treatment** — nearest/raw, optional CRT/NTSC reconstruction, and later curated scalers.
7. **Output resolution** — host framebuffer/window/display resolution.
8. **Presentation cadence** — host refresh/FPS policy, independent of authoritative simulation cadence.

No one setting may silently redefine another.

In particular:

- **16:9 is a view/composition policy, not a source pixel-aspect policy.**
- changing output resolution must not change logical camera extent;
- changing pixel aspect must not change simulation, object activation, collision, course semantics, or animation-state selection;
- changing presentation FPS must not change simulation cadence, timers, AI, RNG, stunt windows, replay timing, or records;
- Widescreen must expose additional logical world rather than stretch a 4:3 image.

## Product presets

### Authentic 4:3

Purpose: historical/reference presentation.

- use the original logical raster and guest-authored timing;
- map the source using the historically appropriate SNES/NTSC horizontal pixel-aspect correction rather than pretending the source raster itself is square 4:3;
- preserve the original logical view;
- use the project's validated authentic overscan policy;
- retain Original graphics;
- optional CRT/NTSC display treatment may be layered on top without changing guest geometry or state.

The current community reference point is SNESRecomp's 4:3 CRT policy using 7:6 horizontal pixel correction. UR-Recomp must validate the exact transform against its own retained reference evidence before treating any numeric constant as title-final.

### Raw Pixels

Purpose: literal source/reference/debug presentation.

- one guest logical pixel maps to a square host pixel before integer scaling;
- no historical horizontal pixel-aspect correction;
- preserve the original logical view by default;
- show source geometry without implying that this was the intended CRT display shape;
- remain available for asset provenance, regression screenshots, renderer debugging, and users who prefer literal square pixels.

For the ordinary 256x224 active raster this is the familiar approximately 8:7 source shape, subject to the chosen overscan policy.

### Modern square-pixel presentation

Purpose: Remastered and Reimagined graphics at modern output resolutions.

- host presentation geometry uses square output pixels;
- replacement assets are registered against semantic/game geometry, not CRT pixel shape;
- the logical view is selected independently;
- Original artwork may still be composited into the same host coordinate system through an explicit source-to-host transform.

This keeps CRT-era display reconstruction from leaking into the geometry contract for new 4K assets.

## Logical view policy

The initial user-facing view choices should be modeled as:

- **Original** — stock logical horizontal view;
- **16:9** — true additional horizontal game-world exposure derived from the active display-geometry policy;
- **Adaptive** — later, if scene and renderer evidence supports safely growing or clamping the logical viewport to the available host window;
- additional ultrawide fixed views may be admitted later if the renderer/materializer and scene policies support them without exposing broken staging.

Do not hard-code a single "16:9 source width" into gameplay or presentation logic. Derive left/right logical margins from:

- target view aspect;
- active display-geometry/pixel-aspect policy;
- active logical height/overscan policy;
- renderer/materializer capacity;
- scene-specific policy.

Widescreen materialization remains expressed in logical source-pixel margins. The existing +8, +16, +24 and later capacity work is therefore valid regardless of the eventual user-facing aspect preset.

## Scene policy

Not every scene should widen identically.

Use the existing Widescreen scene classes:

- `world-expand`;
- `fixed-4:3`;
- `fixed-center`;
- `edge-anchored-ui`;
- `mixed`;
- `special-scripted`.

Racing should normally use genuine world expansion once its presentation contracts are closed. Menus, scripted reveals, transitions, result compositions, and other special scenes may remain fixed or use bespoke composition where widening would expose unfinished/offstage content.

HUD and UI anchoring are host-composition concerns and must not be inferred from the world-view width.

## Overscan policy

Overscan is independent of both display aspect and logical view.

The product should retain at least:

- a validated authentic/reference overscan policy;
- a full/raw logical-raster reference option where useful for diagnostics and preservation.

Do not crop gameplay-critical information merely to hit an integer multiple of 1080p or 4K. Integer-scaling convenience is subordinate to title evidence.

## Presentation cadence

The authoritative simulation remains fixed to original game cadence.

Higher-refresh presentation may use:

- repeated host frames;
- host-side frame pacing;
- presentation-only interpolation if later proven visually worthwhile and semantically safe.

It may not mutate guest timing or make presentation refresh part of authoritative state.

## Community precedent

This policy deliberately incorporates lessons already exercised by the recomp and SNES-emulation communities rather than treating UR-Recomp as a blank-slate renderer.

### SNESRecomp

Upstream SNESRecomp separates **Display Aspect** from **View**. Its shared desktop policy exposes 4:3 CRT with SNES horizontal pixel correction, 8:7 square-pixel presentation, and wider/adaptive logical views independently.

Reference:
https://github.com/RetroPortingToolKit/snesrecomp/blob/main/README.md

Transferable lesson: pixel shape and world exposure are different controls.

### bsnes-hd

bsnes-hd independently controls widescreen extension, pixel-aspect correction, overscan, sprite policy, window policy, and layer behavior. Its required 16:9 extension changes when pixel-aspect and overscan choices change.

Reference:
https://github.com/DerKoun/bsnes-hd/blob/master/README.md

Transferable lesson: a fixed "16:9 = N extra columns" rule is structurally wrong unless the display-geometry and overscan assumptions are pinned first.

### Mega Man X SNESRecomp

The community Mega Man X recomp exposes fixed/adaptive view independently from display aspect, keeps native screens constrained where appropriate, and preserves original camera/collision/encounter behavior while widening presentation.

Reference:
https://github.com/mstan/MegaManXSNESRecomp

Transferable lesson: widened world presentation should preserve gameplay timing and allow fixed presentation for non-world scenes.

### Zelda64Recomp

Zelda64Recomp demonstrates arbitrary presentation aspect and high-refresh rendering while keeping gameplay timing unchanged, and separately controls HUD positioning. Its documented cutscene edge quirks also demonstrate why blindly widening every scene is unsafe.

Reference:
https://github.com/Zelda64Recomp/Zelda64Recomp

Transferable lesson: presentation refresh, world aspect, HUD composition, and special-scene policy need separate ownership.

## Validation required before declaring title-final constants

Before closing the remaining Widescreen viewport/PAR/overscan queue item:

1. capture one or more retained stock Uniracers reference scenes under raw-square and historically corrected display transforms;
2. compare recognizable geometry, UI proportions, circles/curves, racer proportions, and known emulator/reference output;
3. pin the exact authentic overscan behavior;
4. record the selected transform and tolerance in deterministic fixtures;
5. derive the first 16:9 logical-margin target from that policy rather than entering a magic source width;
6. retain Raw Pixels as an independent reference mode even after Authentic 4:3 is validated.

The unresolved work is therefore measurement and title-specific validation, not a need to invent the architecture.
