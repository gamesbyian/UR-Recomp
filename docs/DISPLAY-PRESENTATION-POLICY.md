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
6. **Filtering / display treatment** — nearest/raw, optional CRT/NTSC reconstruction, and later curated scalers. DKC2-style Reconstruct/xBR/ScaleFX candidate results belong here as final-composite hypotheses, not as replacement Racer-HD art. The bounded comparison is in [HD-UPSCALING-EXPERIMENT-PLAN.md](HD-UPSCALING-EXPERIMENT-PLAN.md); current product filtering remains the existing validated path until separately accepted.
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

## Desktop display modes and monitor changes

The Display setting has three meanings, and every desktop host must keep them distinct: **Windowed**; **Borderless** (fullscreen at the desktop mode, no mode switch); **Fullscreen** (exclusive, with a concrete display mode). SDL3 has no separate "fullscreen desktop" flag. A fullscreen SDL3 window is borderless unless the host first gives it a mode with `SDL_SetWindowFullscreenMode`. The pinned Baldosa host and Modern Options seam never did, so on the SDL3 Windows product Fullscreen was silently Borderless and switching between the two did nothing.

`tools/baldosa_sdl_display_lifecycle_spike.py` closes this with decisions from `native/product/display_window_lifecycle_policy.h`:

- **Fullscreen mode before every transition.** Before each fullscreen transition (Options, the in-game launcher, Alt+Enter, and window creation), Fullscreen gets SDL's closest exclusive mode to the window's display desktop mode, and Windowed/Borderless clear it. Output Resolution is not a Baldosa Options row yet, so "Native" is the only resolution.
- **No exclusive mode means a refusal.** A display offering no such mode makes Options report a refusal, which the Options seam already rolls back.
- **Alt+Enter stays borderless.** Alt+Enter moves between windowed and borderless only, so it clears any mode left from an earlier Fullscreen.
- **Alt+Enter is never a menu key.** The product key hook runs before the framework's command lookup and sees no modifiers, so a visible Modern root took Alt+Enter's Return as CONFIRM and started a 1P game while the window stayed windowed. A key that maps to the framework's fullscreen command now always reaches the framework.
- **Display events are reconciled, never consumed.** They are handled in all host event pumps:
  - an exclusive window that lands on another display, or whose display's desktop mode changes, is re-moded for that display;
  - a windowed window whose title strip no longer shows at least 32 px on any display's usable area (for example after its monitor was removed) is centred on the primary display, shrunk to fit if necessary;
  - after a DPI change, a default-sized window that no longer fits is re-clamped through the framework's own window-scale rule.
  - the in-game launcher's own event loop drains display events too, so the same reconcile runs when it returns (`reason=launcher_returned`), for a monitor removed or rescaled while it was open.

**In-game launcher without usable OpenGL.** The launcher asks SDL for a 3.3 core context. Where Windows has no real GL driver (remote desktop, VMs, GPU-less machines), it returns the GDI 1.1 context instead of failing. ImGui's GL3 loader then failed, its result was ignored, and the first draw crashed the whole game through the launcher hotkey (#2272). The display seam now checks the context's own `GL_VERSION` and refuses anything below 3 (`[launcher] UR_LAUNCHER_GL unusable version=…`). The launcher returns UNAVAILABLE, which the host already treats as "resume the game". `tools/run_baldosa_launcher_gl_fallback_acceptance.py` opens the real in-game launcher twice. The first launch uses a test override that forces version 1.1, which must be refused. The second uses the machine's own GL and must not crash. Locally, without the check, the forced launch is not refused.

Presentation pacing still follows the active display's refresh through the host's existing 250 ms re-check.

**After a GPU device reset the game keeps drawing.** When the Direct3D 11 device is lost (a driver update, a GPU timeout, or a monitor switch on a hybrid-GPU laptop), SDL3 frees every texture's GPU data, recovers the device and sends `SDL_EVENT_RENDER_DEVICE_RESET`. The host kept locking its old frame texture, which then fails every frame ("Texture is not currently available"), so the window stayed black for the rest of the run. The display seam now flags the reset (`UR_DISPLAY render_device_reset`), and the next draw rebuilds the frame texture through the host's existing recreate path (`texture_recreated=WxH`). An unrecoverable loss is logged as `render_device_lost`. `tools/run_baldosa_render_reset_acceptance.py` delivers the event in a real launch and requires one rebuild, no failed lock and a running game; without the flag it fails. The game frame is the host's only SDL texture: the framework's FPS readout (`snes_osd.c`) is composited into the frame here, and its separate SDL draw path is never called. Hosted CI cannot remove a real GPU device, so a real device loss is physical check D17.

**A panel slower than the game never slows the game.** The Baldosa host presents once per simulated frame and drops simulation it falls behind on. With VSync on, a panel slower than the SNES's ~60.1 Hz therefore set the game's own speed. A model of the host clock gives 50.000 simulated fps on a 50 Hz panel (83%), against 59.95 on a 59.94 Hz panel and 60.017 on a 60 Hz panel: the usual sync-to-video. Where `ur_display_vsync_cannot_carry` says the panel is more than 1% slower than the guest, the swap interval is now 0, so presents do not wait and the clock paces the game. Windowed play composites normally; exclusive fullscreen may tear. The decision is logged as `UR_DISPLAY vsync panel_hz=… guest_hz=… wait=no|setting` and re-applied when the window changes display or goes fullscreen. An unknown refresh keeps the setting. `tools/run_baldosa_slow_panel_vsync_acceptance.py` checks the renderer's applied interval with a forced 50 Hz and a forced 60 Hz panel, then on the machine's own panel. Locally, without the decision, the 50 Hz launch keeps vsync 1. The pinned 2P route's WRAM CRCs are unchanged. Game speed on a real 50 Hz panel is physical check D16.

The framework's window-size keys (Ctrl+Up/Down when bound, and Ctrl+mouse-wheel) used to change only the live scale. `config.ini` kept the old `WindowScale`, so the chosen size was forgotten on relaunch. An explicit size step now records `WindowScale`, written by the host's existing exit-time config write. A re-clamp after a display or DPI change is not a player choice and is never persisted. Local check: a real Ctrl+wheel step then a normal quit persisted `WindowScale = 1` and relaunched at 320×240; main relaunched at 640×480.

**The default window size follows the display's DPI.** Windows makes the host per-monitor DPI aware, and SDL3 window sizes are in pixels. The framework's fixed default scale, 2 (640×480), was therefore a small window on a 150% or 200% panel. When nobody chose a size (`WindowScale = 0`, with no `WindowWidth`/`WindowHeight`), the display seam asks `ur_display_default_window_scale` before the window is created:
- the primary display's content scale times 2, rounded, and never below 2;
- capped at the framework's maximum;
- stepped down until the window uses at most 90% of the display's usable width and height.

It logs `UR_DISPLAY default_window_scale content_scale=… usable=WxH scale=N`. An explicit `WindowScale`, an explicit size, a saved placement and later display or DPI changes keep their existing rules. Two framework paths used to turn the unset default into a fixed number:
- the in-game launcher seeded an unset scale as a literal 2 and committed it;
- the config writer saved an unset scale as `WindowScale = 3`, so the first config write resized the next launch.

The launcher now opens on the live scale and leaves `WindowScale` unset unless the player changes it, and the writer keeps 0.

`tools/run_baldosa_default_window_scale_acceptance.py` checks this in real launches:
- a forced content scale of 1.0 opens at 2×;
- a forced 2.0 opens at the policy's scale for the usable area the game logged;
- an explicit `WindowScale = 1` is kept;
- a launcher round trip keeps the default unset.

Locally on a 3840×2160 X11 display, 2.0 gave scale 4 (1280×960); on 1024×768 it was clamped to 2. Without the decision, the runner fails; without the writer fix, the launcher round trip writes `WindowScale = 3` and fails. The pinned 2P route's WRAM CRCs are unchanged. A real high-DPI panel is physical check D18.

**Window placement.** The pinned host always reopened centred on the primary display, so a player who keeps the game on a second monitor had to move it back every launch. At a clean exit the host now writes `window-placement.txt` next to the active `config.ini`. The file records:
- the window's display, by name and bounds;
- for a window that is not fullscreen, minimized or maximized, its windowed position;
- whether a windowed game was maximized (`maximized=1`). The windowed position from before keeps its place in the file, so un-maximizing later returns there.

At the next launch, after the renderer has the window (an OpenGL renderer can recreate it), the saved display is found by `ur_display_placement_match`:
- an exact name and bounds match wins;
- otherwise a uniquely named display wins, for a monitor that was rearranged;
- otherwise the saved display is treated as missing.

What happens next:
- a missing display logs `saved_display_missing`, and the window stays where SDL put it;
- a fullscreen window on another display is moved there and re-moded;
- a windowed window returns to its saved spot only when the 32 px reachability rule still holds, and is otherwise centred on that display;
- a window saved maximized is then maximized there, on the saved display.

`tools/run_baldosa_window_placement_acceptance.py` runs five real launches:
1. move the window, then quit;
2. relaunch, which must reopen at the same spot on the same display, not maximized;
3. maximize, then quit; the file must keep the moved spot and record `maximized=1`;
4. relaunch, which must reopen maximized on the same display;
5. relaunch with the saved display renamed to one that is not connected, which must log the fallback and must not reuse the old spot or the maximized state.

Local X11 run: positive pass. Without the restore call the runner fails, and without the maximize step it fails `relaunch did not restore the maximized state`. Before the restore was moved after renderer creation, it landed at the right spot and was then displaced by window recreation; the runner caught that. Moving between real monitors needs more than one display and is a physical check.

`tools/run_baldosa_display_lifecycle_acceptance.py` drives these transitions on the real Win32 window through the product Options seam and the Alt+Enter command, and checks the window's actual flags and mode after each step. Off-screen rescue is recorded as `not_exercised` when the desktop refuses to move a window off-screen. Local negative controls fail as expected:
- without the mode decision, `borderless_to_exclusive` and `windowed_to_exclusive` fail;
- without the Alt+Enter clear, `hotkey_enters_borderless` fails.
- without the key routing, a visible Modern root takes Alt+Enter as CONFIRM (`stock_requested players=1`), and both hotkey steps fail. The acceptance runs with the Modern root visible and the runner rejects any `stock_requested`.

The pinned 2P route's per-frame WRAM CRCs are unchanged. A hosted runner has one display, so multi-monitor hot-plug, physical DPI changes and real mode-switch hardware remain unaccepted.

**Window-key persistence:** Modern restores the persisted `HostSettings` display mode at boot. An Alt+Enter or launcher change is now adopted into that existing store when the live display changes (`baldosa_options_adopt_live_display`, see [MODERN-PRODUCT-LAYER](MODERN-PRODUCT-LAYER.md)), so it survives the next launch. A missing store keeps `config.ini` authoritative.

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

