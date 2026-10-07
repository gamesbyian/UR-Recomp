# Controller Prompt Policy

Status: semantic prompt substrate implemented; physical-brand glyph selection deferred.

## Authority

SNESRecomp's configured `GamepadMap` is the sole authority that turns a physical controller button into a P1 SNES semantic control. The title-owned `system_gamepad_control` seam receives the already-resolved control index in this stable order:

`Up, Down, Left, Right, Select, Start, A, B, X, Y, L, R`.

Modern product UI may present that semantic result. It must not infer a physical Xbox, PlayStation, Nintendo, Steam Input, SDL, or vendor-specific button legend from the controller name or raw SDL button number.

A user can remap GamepadMap. Therefore device brand plus physical button index is not sufficient evidence for a truthful on-screen glyph.

## Implemented semantic prompts

`native/product/modern_controller_prompt.hpp` provides ASCII-safe prompts for the authoritative semantic controls:

- directions: `[UP]`, `[DOWN]`, `[LEFT]`, `[RIGHT]`;
- system controls: `[SELECT]`, `[START]`;
- face/shoulder semantics: `[A]`, `[B]`, `[X]`, `[Y]`, `[L]`, `[R]`.

These are semantic SNES prompts, not claims about the label printed on the player's physical controller.

Unknown or out-of-range semantic input fails closed to `[?]`.

## Future physical glyphs

A future controller-family glyph layer is allowed only after the framework exposes a trustworthy presentation-safe reverse mapping from the active semantic control to the currently bound physical input for that seat.

That later layer should keep three things independent:

1. semantic action ownership;
2. active physical binding;
3. artwork/glyph family.

Do not derive physical glyphs from a controller brand string, opaque source ID, SDL button ordinal, or a hard-coded Xbox-style assumption.

Until that reverse-map seam exists, semantic prompts are the truthful player-facing fallback.
