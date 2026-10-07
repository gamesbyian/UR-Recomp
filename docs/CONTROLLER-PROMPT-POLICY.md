# Controller Prompt Policy

Status: semantic prompt substrate implemented; positional physical-button labels from the live GamepadMap implemented; physical-brand artwork deferred.

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

## Physical-button labels from the live GamepadMap

The framework's own lookup, `FindCmdForGamepadButton(button, 0)`, is the reverse-map seam this policy waited for. `native/product/modern_pad_glyphs.hpp` (`modern_pad_glyph_for_control`) walks the positional `kGamepadBtn` order and returns the first physical button whose unmodified binding produces a given SNES control, or `NONE` when nothing is bound. The host wraps it as `live_gamepad_binding_label`, so a remapped `[GamepadMap]` changes the hint on the next draw.

Labels are positional (`A` = south, `B` = east, `X` = west, `Y` = north, plus `LB`/`RB`/`LT`/`RT`/`BACK`/`START`/`L3`/`R3`/D-pad), matching the names `[GamepadMap]` itself uses. They name the button position, not a vendor legend.

Onboarding, Controls instructions and the tour restart confirm use these live labels. Host shortcuts that test a fixed physical `kGamepadBtn_*` position (Quick Practice `PAD X`, results `PAD X`, profile `PAD X`/`PAD Y`, cancel `PAD B`) keep fixed labels because they are not routed through GamepadMap.

## Future brand artwork

Brand-specific artwork (Xbox/PlayStation/Nintendo legends) remains deferred. If added, keep three things independent:

1. semantic action ownership;
2. active physical binding (the reverse map above);
3. artwork/glyph family.

Do not derive physical glyphs from a controller brand string, opaque source ID or SDL button ordinal alone.
