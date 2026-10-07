# Reduced Flashing Presentation Backend

Status: deterministic presentation backend implemented; live host integration and user-facing setting remain pending.

## Purpose

Some SNES effects rely on alternate-frame visibility to suggest translucency or intensity. On a modern display, duplicated or torn presents can make that flicker harsher or less stable than intended.

The project now has a host-independent presentation backend in:

- `native/product/reduced_flashing_frame_blend.hpp`
- `native/product/reduced_flashing_frame_blend.cpp`

It averages each presented pixel byte with the previous **unblended guest frame** using the same floor-mean arithmetic used by the recomp community's shared frame-blend implementation.

## Authority boundary

This is presentation only.

The backend cannot:

- alter guest cadence;
- suppress or invent guest frames;
- write WRAM/SRAM;
- change input;
- affect timers, RNG, physics, collisions, records or replay;
- change logical view, pixel aspect, graphics representation, source sampling or display treatment policy.

It receives already-rendered 32-bit presentation frames and mutates only those output bytes.

## Reference lifetime

The retained reference is the previous **unblended** guest frame.

A new guest frame:

1. blends against the retained reference if one exists;
2. is retained in its original unblended form for the next frame.

A repeated/intermediate host present may use the holding path:

- blend against the same retained guest-frame reference;
- do not advance that reference.

This matters when host presentation refresh is higher than guest simulation cadence. The visual pairing remains consecutive guest frames rather than consecutive host presents.

## Reset/failure policy

The backend resets automatically when presentation geometry changes.

Callers must also reset across discontinuities where the preceding image is not a meaningful temporal predecessor, including reset/reboot, save-state jumps, replay seeks or equivalent hard cuts.

Invalid dimensions, null buffers, insufficient pitch and allocation failure fail closed to an unmodified frame.

The first new guest frame after reset or resize is captured and presented unchanged. A holding present with no retained reference is also unchanged.

## Current integration boundary

The shipped no-recomp-ui product currently does not wire this backend into the live presentation loop. That remains a thin integration task once the central host surface is free.

Do not expose a Reduced Flashing toggle until:

- the live host can distinguish new guest frames from repeated/intermediate presents;
- resets/cuts clear the retained reference;
- deterministic acceptance proves guest/simulation evidence is identical with the setting on and off.

The existing framework `FrameBlend` config spelling is precedent, not a second product authority. When integration occurs, use one setting path and one backend.
