# Widescreen Architecture

The canonical end-to-end remaster strategy is `docs/WIDESCREEN-HD-REMASTER-PLAN.md`. This document owns focused Uniracers widescreen implementation notes as they are discovered.

## Principle

Increase presentation width while keeping original simulation semantics.

Original 4:3 remains the canonical regression mode. With widescreen disabled, defined deterministic routes must remain equivalent to the stock native/reference path.

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

The final HD compositor may render equivalent logical per-viewport sprite state without relying on the physical SNES trick for final pixels, but only after the authentic path is understood and remains available for validation.

## Non-goals

Do not:

- widen physics or collision bounds simply because more world is visible;
- alter race timing, RNG or AI as a side effect of presentation;
- activate progression records early;
- infer collision from replacement artwork;
- stretch a 4:3 framebuffer and call it widescreen;
- replace the whole renderer before stock world/camera/sprite boundaries are mapped.

## First widescreen gate

Before implementation, establish:

1. a deterministic playable stock route;
2. an independent reference capture through `snesref`;
3. verified player/camera/object state anchors;
4. a permanent 4:3 regression gate.

Then widen backgrounds first, followed by culling/OAM, ordinary spawning, and graphics staging, matching the framework's proven dependency order.
