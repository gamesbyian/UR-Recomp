# Rendering, camera and OAM

## The unusual split-screen mechanism

Uniracers intentionally changes sprite-related state during active display.

This is supported independently by developer testimony and multiple emulator investigations.

Mike Dailly described the technique as a SNES application of C64-style **sprite ripping** and said Nintendo R&D had to verify the behavior.

Modern emulator evidence makes the mechanism concrete:

- jgenesis reports OAMDATA writes on scanlines 0 and 112;
- values are `0xA5` and `0x5A`;
- both are expected to target high-OAM byte `$18`;
- that byte affects sprites 96 through 99;
- top and bottom screen halves alternately move sprite pairs on/off screen.

Snes9x's title-specific workaround forces OAM word address `0x10C`.

MAME describes the equivalent byte offset as `0x0218`.

These are two representations of the same effective location.

## What this means architecturally

The split-screen racer presentation is not simply "draw two normal scenes."

At least part of the original visual result depends on raster-time mutation of OAM-related state.

Therefore:

- authentic 4:3 mode must preserve or accurately model the original effect;
- two-player and Vs. modes deserve dedicated validation;
- a later host compositor may render equivalent logical sprites without needing to reproduce the trick in final presentation, but game state must remain authoritative.

## Other historical rendering seams

Older Snes9x history shows Uniracers also exposed unrelated emulator correctness problems:

- LoROM SRAM mapping;
- XOR/window-area logic;
- color addition / empty-subscreen behavior;
- active-display OAM behavior.

These should be separate tests. A visual failure in Uniracers should not automatically be blamed on the famous OAM quirk.

## Recovered multiplayer camera-to-render bridge

Recent structural recovery turns the split-screen camera path into a concrete chain rather than a generic widescreen risk.

The game maintains two camera positions and velocity pairs:

- camera 1: `$0419/$041D`, velocity `$04F5/$04F9`;
- camera 2: `$041B/$041F`, velocity `$04F7/$04FB`.

Bank 81's recovered camera-control island updates camera 1 every active race pass and conditionally updates camera 2 when `$0DDB != 0`. The same island converts camera position into coarse/fine map-window indices and feeds `81:ADB6`, `81:B27F` and `81:B375`, which derive track-data windows from `$7F000F` into working buffers. This is evidence that camera state participates in world/course sampling, not only PPU scroll.

The per-camera raw window-update state is now exposed by the paired-player summarizer: `$0505/$0507` are the movement-derived edge values, `$052B/$052D` are their associated update spans, and `$0509/$050B` retain the fine/index component. The code sets inactive edges to `$FFFF` and zero span, while active camera motion drives additional strip fetches through `B27F/B375`. Treat these names as structural/raw until runtime evidence further narrows whether they represent rendering-only streaming, collision/object activation, or a shared world-window primitive.

Bank 82 then computes per-racer, per-screen coordinates in `$1501..$150E` from racer positions relative to camera 1/2. Off-screen branches substitute sentinel coordinates and update visibility bits in `$1599`. Routine `82:D2D8..` subsequently writes `$1501..$1510` directly to OAMDATA.

For later widescreen work, keep these layers distinct:

1. camera simulation/follow state;
2. camera-derived course/window sampling;
3. racer screen-space projection and culling;
4. OAM emission and the active-display split-screen seam.

Expanding only the final render rectangle would therefore be insufficient and could expose objects or course sectors outside the original simulation/activation window.

## Camera and future Widescreen feature

The project should recover and distinguish:

- world/camera state;
- PPU scroll state actually rendered;
- object culling bounds;
- sprite/OAM emission bounds;
- stage/stream activation boundaries;
- HUD/UI layers.

SNESRecomp's existing Widescreen patterns warn that widening only one of those layers is insufficient. In particular, culling and OAM emission form separate gates.

The permanent rule is:

**4:3 authentic behavior is the regression oracle. Widescreen extends presentation without silently changing simulation or progression.**

See `docs/WIDESCREEN.md` for implementation-specific rules.
