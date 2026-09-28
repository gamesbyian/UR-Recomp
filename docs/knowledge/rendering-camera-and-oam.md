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
