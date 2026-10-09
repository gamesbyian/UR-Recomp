# Widescreen Feature Architecture

**Baldosa integration, 2026-10-09:** Merged #1078 and #1082 preserve guest geometry and produce native, course-derived +24 and +43 logical world pixels per side, respectively. The 342×224 view uses calibrated +48-pixel backing to cover fine scroll phase and has been witnessed in both 2P split views without changing guest CRCs. Merged #1045 conservatively protects original source-visible P1/P2 OBJ. PR #1092 connects this *existing* widened source field to the existing stable integer-density compositor and tests exact 1368×896 host-presentation pixels at 4×. Its runtime QA is a component gate until exact native CI completes. This is still not a demonstrated physical 3840×2160 Windows drawable, 4K-capable product window integration, authored HD racer replacement in widened frames, or independent PPU/HUD/foreground layer parity. The first-party world provider, original sprite capture guards and approved artwork remain the only authorities; do not create another renderer.

The canonical end-to-end project strategy is `docs/PROJECT-PLAN.md`. This document owns the **Widescreen** feature specifically: implementation notes for expanding the logical horizontal view beyond the original 4:3 presentation.

## Principle

Increase presentation width while keeping original simulation semantics.

Original 4:3 remains the canonical regression mode. With the Widescreen feature disabled, defined deterministic routes must remain equivalent to the stock native/reference path.

## Baldosa wide host presentation boundary

The title-owned course materializer `native/title/uniracers_ws_margins.c` reads real bank-$7F course cells, calibrates against native per-band PPU VRAM and HDMA scroll, and serves additional tiles through the framework's world-shadow hooks. It does not modify guest camera, WRAM, VRAM, collision or course execution. A failed calibration must shrink back to a stock 256×224 field. The host samples at 342×224 only for an independently recognized live-race scene; the bounded Baldosa experiment still uses its 1800..2450 route window, which is **not** a shipping game-state classifier. Agent 2's guest-state evidence should drive the eventual production scene decision, using the existing `observe_widescreen_scene` contract.

The same native compositor must receive every fixed and wide field. Its internal density is 1×–4× *separately from* logical world extent and the final output/window size. With current source-OBJ limitations, the widened 342×224 field retains every Original stock rider and is fully nearest-composed at any accepted density. **Do not arm Racer HD RemoveFromGame for 342-wide geometry until isolated source-visible per-slot 2P ownership and final draw coordinates are proved.** Merged authored 256×224 4× graphics continue to work in supported fixed scenes. This conservative fallback is preferable to fabricating missing or overpainted riders.

The original source display is 7:6 PAR, and discrete 342-wide source geometry uses 512/513 horizontal fit to target exact 16:9. The pure output-layout authority is `native/product/widescreen_output_composition.*`; **neither 342×224 nor 1368×896 is the physical 3840×2160 drawable**. Agent 1 owns final host window/display application and the actual pixel-aspect/output evidence. Preserve source-present-frame identity, host pitch, band ownership, original RGB/OBJ comparisons and guest CRCs when giving it captures.

## Systems to map before widening

- logical camera and its PPU scroll relationship;
- background/tilemap streaming;
- authored world/course boundaries;
- sprite/OAM construction and screen-X rejection;
- object activation, spawning and culling;
- graphics/stage streaming triggers;
- HUD/frontend anchoring;
- two-player viewport split;
- active-display OAM behavior.

## Framework doctrine to reuse

The pinned SNESRecomp framework's `docs/WIDESCREEN_PATTERNS.md` is the transferable checklist. For Uniracers, verify each applicable invariant with title-specific evidence rather than copying another game's addresses.

In particular:

- use actual rendered PPU scroll phase;
- populate newly visible margins before their first display;
- classify layers as world-anchored, periodic, bounded or HUD;
- prove gameplay/liveness gates;
- widen culling and OAM emission together;
- handle negative/left-margin sprite coordinates;
- do not widen progression/controller triggers merely because ordinary objects should become visible earlier;
- keep subsystem-specific kill switches;
- preserve bit-identical 4:3 behavior where the comparison contract requires it.

## Uniracers-specific seam: split-screen sprite ripping

Authentic mode must preserve the original raster/OAM behavior. Current evidence gives a concrete target in Vs. mode:

- active-display/HBlank OAMDATA writes on scanlines 0 and 112;
- values `0xA5` and `0x5A`;
- effective high-OAM byte `$18`;
- sprites 96-99;
- original ROM hook neighborhoods around offsets `0x01534C` and `0x015714`.

The HD Presentation compositor may render equivalent logical per-viewport sprite state without relying on the physical SNES trick for final pixels, but only after the authentic path is understood and remains available for validation.

## Non-goals

Do not:

- widen physics or collision bounds simply because more world is visible;
- alter race timing, RNG or AI as a side effect of presentation;
- activate progression records early;
- infer collision from replacement artwork;
- stretch a 4:3 framebuffer and call it the Widescreen feature;
- replace the whole renderer before stock world/camera/sprite boundaries are mapped.

## First Widescreen feature gate

Before implementation, establish:

1. a deterministic playable stock route;
2. an independent reference capture through `snesref`;
3. verified player/camera/object state anchors;
4. a permanent 4:3 regression gate.

Then widen backgrounds first, followed by culling/OAM, ordinary spawning, and graphics staging, matching the framework's proven dependency order.
