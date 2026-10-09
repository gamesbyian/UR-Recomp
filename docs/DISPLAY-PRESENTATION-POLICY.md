> **2026-10-09 implementation note:** Keep **logical world width, 1×–4× internal source density, 7:6 original PAR, graphics representation and actual output resolution** independent. Merged #1082/#1092 prove calibrated 342×224 logical split-world at 1368×896 density-4 Original presentation with exact repeated 4×4 blocks and unchanged 2,473-frame guest CRCs (native CI `38004162535`). That native buffer is not the physical 3840×2160 drawable. The existing 7:6 PAR plus 512/513 horizontal fit remain final-host geometry policy. Source-visible wide authored OBJ, HUD/foreground parity, real Windows 4K output and complete-event QA remain separate decisions. Current owners: [WORK-QUEUE.md](WORK-QUEUE.md).

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

SNESRecomp's 7:6 horizontal correction remains useful community precedent, and UR-Recomp now has title-specific evidence for the same horizontal display family. Eleven in-game screenshots printed in the official USA manual measure near 4:3 rather than raw 8:7; even a conservative ±5-pixel-per-edge measurement envelope admits 4:3 for every sample and excludes 8:7 for every sample. For a 256-wide source, that supports a 7:6 horizontal pixel correction. The title-final logical Authentic transform is therefore full 256×224 at 7:6 PAR. Any optional simulation of period-TV edge loss belongs to display treatment, not destructive logical-raster cropping.

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

## Modern overlay composition and sampling

Modern product UI uses a host-owned composition contract rather than screen-specific coordinates leaking into guest geometry. `native/product/modern_overlay_composition.*` keeps logical placement, integer presentation density, reserved stock-content bands, and final output projection separate. Callers own the reserved bands for the scene they already understand; the generic resolver only anchors inside the resulting usable rectangle and fails closed when the requested minimum cannot fit.

This is intentionally independent of Widescreen scene classification. A 256x224 fixed scene and a 342x224 widened scene use the same overlay policy with different logical surface widths. High-DPI output likewise does not change logical anchors: density multiplies the complete logical overlay geometry, then final window scaling happens after composition.

The deterministic source-sampling policy is represented by `native/product/presentation_sampling_policy.hpp`:

- Original pixel art uses nearest-neighbour for integer presentation transforms;
- Remastered and Reimagined rasters are sampled at their declared native density rather than being round-tripped through the guest surface;
- Modern primitives and glyphs rasterize directly at presentation density.

This policy does not silently select a CRT/NTSC treatment. Final-window filtering remains a separate post-composition display-treatment axis, but the current Windows x64 Modern product now binds that axis explicitly to nearest through SNESRecomp's live renderer seam. That is deliberate for the current mixed-source compositor: one completed frame may contain nearest-expanded Original pixels, native-density Remastered raster content, and Modern primitives/glyphs, so whole-frame linear filtering would blur sources whose sampling contract is already resolved. Authentic execution leaves the framework/config-owned final-window filter untouched. A future CRT/NTSC reconstruction or curated scaler must therefore arrive as an explicit treatment policy rather than by changing source-sampling semantics. `native/product/display_treatment_policy.hpp` now owns that explicit product axis without claiming a renderer backend: `Clean`, `CRT/NTSC`, and `Curated Scaler` are distinct requested treatments, with capability-aware resolution that fails unavailable post-process choices closed to Clean. An unavailable treatment never enables linear filtering, changes per-source sampling, alters view/aspect/overscan, changes graphics representation, or touches guest cadence/state. Clean is the only universally available treatment until a concrete backend registers support. The live timing HUD, non-modal Recent / Quick Practice / Tour hints and all current host-owned Modern modals preserve logical size at supported integer presentation densities.

### Resize/high-DPI acceptance

The composition contract is regression-tested over common Windows desktop/window sizes and arbitrary odd-sized drawables, across fixed and widened logical views and 1x–4x internal presentation density. Window resizing may change the resolved output viewport and final projected rectangle, but it must not change the logical overlay rectangle. Any constrained logical layout must remain inside caller-declared safe bands, compact only to its declared minimum, then disappear rather than overlap protected content.

### Stable fixed-scene density

With Remastered Racer HD enabled, Internal Render Scale is resolved from the persisted product setting for the whole supported fixed scene, not from whether a particular racer pose has HD art. Authored replacement frames use the Racer HD compositor; stock fallback frames use exact nearest-neighbour integer expansion of the guest raster at the same density. This keeps output dimensions and pixel sampling deterministic across replacement/fallback transitions.

Widened world composition now preserves the configured 1x–4x presentation density without changing the accepted 342×224 logical view, +48 backing/materializer coverage, +43 visible world extent, 7:6 Original PAR or final viewport policy. SNESRecomp allocates the presentation buffer from logical width/height multiplied by density; if the Racer-HD replacement presenter declines the widened frame, the generic nearest-density compositor expands the entire completed widened field, including host-owned margins, exactly. Regional-title replacement likewise preserves its logical retail crop at 1x–4x by nearest-composing the canonical guest title at the selected density, painting the proven Europe crop in logical coordinates expanded by that same integer scale, verifying the density-aware crop digest, and restoring the canonical composed frame on any failure. Current Modern presentation therefore has no global 1x density holdout.

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

## Canonical review harness

PR #302 / native smoke run `37142393303` closes the review-tooling prerequisite. `tools/build_display_geometry_review.py` consumes canonical 256×224 framebuffer BMPs from the ordinary 1P route and emits self-contained JSON/HTML review evidence. The current matrix in `analysis/display-geometry-candidates.json` retains raw-square and centered-216 alternatives as diagnostics, while full-height 7:6 is now the accepted Authentic logical geometry.

The same run proves the canonical `main-menu-ready`, `now-playing-ready`, and `race-entered` captures are 256×224 and that the review can be generated inside the normal native workflow. Artifact `uniracers-native-frame` id `11281695308` retains the generated review and source captures. The outstanding question is therefore which transform is best supported by Uniracers-specific visual/reference evidence, not whether the project can reproduce and compare the candidates.

## Title-specific transform closure

The logical Authentic transform is now closed for implementation. The evidence chain is:

1. official-manual screenshot geometry supports the 4:3 display family and excludes raw 8:7 within the retained uncertainty envelope;
2. for the 256-wide source, that establishes 7:6 horizontal correction;
3. canonical framebuffer evidence proves centered 216-line cropping discards rendered information in representative frontend, transition, and race scenes;
4. therefore Authentic logical geometry preserves all 224 authored rows;
5. period-TV edge loss, when desired, is optional display treatment layered after logical composition rather than a different guest/view geometry;
6. Raw Pixels remains an independent reference mode.

The unresolved work is therefore measurement and title-specific validation, not a need to invent the architecture.

## Accepted Authentic binding

Native Widescreen run `37146519813` closes the host-owned provider through **+72 logical source pixels per side** while preserving the accepted ownership split: margin 0 is untouched stock, column +1 is the accepted guest +8 lane, and every deeper column is host presentation state sourced from the live course tables.

The title-specific logical binding is now accepted for implementation:

- source raster: 256×224, full height;
- horizontal pixel aspect: 7:6;
- resulting stock display aspect: exactly 4:3;
- logical overscan crop: none; preserve all 224 authored rows;
- derived exact 16:9 per-side logical margin: 128/3 source pixels;
- materializer strip margin: +48 per side at the established 8-pixel granularity;
- provider: the accepted live-course-runtime host materializer.

The horizontal part of this candidate is now evidence-backed. `analysis/display-reference-geometry.json` records eleven printed in-game screenshot frames from the official USA manual (pages 17, 19, 21, 23 and 25). Their measured mean aspect is about 1.329 and median about 1.342. With ±5 pixels of uncertainty on every measured edge, all eleven intervals still contain 4:3 and none contain raw 8:7. Because 256×224 requires 7:6 horizontal correction to land at 4:3 when all 224 rows are active, this is title-specific support for 7:6-style Authentic PAR rather than merely emulator convention.

Vertical logical presentation is now closed by a preservation rule grounded in title evidence. `analysis/display-active-height-evidence.json` reuses the retained canonical `main-menu-ready`, `now-playing-ready`, and `race-entered` 256×224 framebuffers from run `37142393303` / artifact `11281695308`. A centered 216-line crop removes distinct rendered information in all three scenes: 791/2048 cropped pixels on the menu frame, 40/2048 on the transition frame, and 645/2048 on the race frame differ from the nearest retained boundary row, 1476/6144 in aggregate. Because no stronger title-specific evidence requires throwing those authored rows away, Authentic logical geometry preserves all 224 rows. This does not claim every period CRT exposed every row; optional CRT/NTSC treatment may mask edges after logical composition without redefining the game view.

The accepted runtime selector carries this transform through both sides of the presentation contract without coupling it to product UI. On the preparation side, `URRECOMP_WS_VIEW=authentic-16x9` resolves to the next complete provider strip boundary, **+48 source pixels per side**. On the host-view side, exact 16:9 requires 128/3 = 42⅔ source pixels per side, so the nearest symmetric integer logical viewport is **+43 per side**, or **342×224**. At 7:6 PAR that discrete source viewport is 57:32 (1.78125), about +0.195% wider than exact 16:9; final output scaling absorbs that sub-pixel quantization without exposing the unused five prepared pixels at either edge. `authentic-16x9-candidate` remains a compatibility alias, explicit `URRECOMP_WS_MARGIN` remains a diagnostic override, and unknown/unset selectors fail closed to stock margin 0.

The distinction is architectural: **provider margin is backing coverage, not automatically visible camera extent**. The +48 materializer prepares more data than the +43 host viewport exposes. With full 224 and 7:6 now fixed as the logical Authentic transform, +43 visible / +48 backing is the accepted 16:9 geometry contract.

The product layer now represents final 16:9 composition explicitly in `native/product/widescreen_output_composition.*`. The contract carries logical view extent, display pixel aspect, target output aspect, final horizontal fit, centering, and world-exposure intent as separate fields. Original presentation therefore keeps 7:6 PAR and the 512/513 widened correction, while Remastered presentation uses square-pixel host geometry without inheriting CRT-era PAR. Representation is a completed-frame property: the current mixed compositor still uses Original output geometry when Remastered racer sprites are present because the background, HUD and widened margins remain stock/Original. A future square-pixel geometry switch requires a full-frame Remastered presenter, not merely one replacement layer. Output resolution remains a separate presenter concern. Scene recognition remains a separate title-host responsibility. The product contract provides a fail-closed classifier for the verified 1P/ordinary-2P/VS selection states, and the live title host now consumes it through `prepare_frame` and `compute_viewport`. Under the accepted 16:9 selector, evidence-backed active 1P/2P races request the 342×224 logical view and fill the largest 16:9 output rectangle; fixed scenes preserve 256×224 and are centered inside that same 16:9 canvas. The framework's dynamic native-wide callback is enabled only for a live `world-expand` scene, so fixed scenes and selector-off runs retain the stock PPU raster path rather than merely requesting a 256-wide viewport through the widened renderer. The ordinary generated product now installs the accepted materializer automatically before build. Output resolution remains independent. Persisted Modern Options now exposes Original / 16:9 View selection. 1P, ordinary 2P and VS races all widen; their margins are presented host-side from the live course model, one calibrated origin per viewport (R-2026-10-04-UI-29/30), and native smoke gates centre-pixel and WRAM parity against the Original view.

## Policy-derived logical margin

`tools/widescreen_probe.py derive-margin` now derives the required symmetric logical margin from four independent inputs:

- target display aspect;
- active logical height after the selected overscan policy;
- source/display pixel aspect;
- materializer strip granularity.

The calculation uses exact rational arithmetic and reports both the exact per-side logical margin and the first strip-granular margin that can cover it. It also compares that requirement with the currently validated materializer capacity recorded in `analysis/widescreen-policy.yml` (+72 pixels per side at 8-pixel granularity).

The accepted full-height 7:6 row and retained diagnostic alternatives are:

| Active logical height | Pixel aspect | Exact per-side margin | First 8-pixel materializer margin | Fits validated +72? |
| ---: | ---: | ---: | ---: | --- |
| 224 | 7:6 | 128/3 ≈ 42.67 px | +48 | yes |
| 216 | 7:6 | 256/7 ≈ 36.57 px | +40 | yes |
| 224 | 1:1 | 640/9 ≈ 71.11 px | +72 | yes |
| 216 | 1:1 | 64 px | +64 | yes |

These rows show why pixel aspect and overscan remain separate from logical view width. The accepted +72 provider covers every retained diagnostic candidate. Full-height 7:6 is the title-final logical Authentic transform; its 16:9 view exposes +43 per side while the provider remains rounded to +48.

