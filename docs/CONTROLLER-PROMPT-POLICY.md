# Controller Prompt Policy

Status: semantic prompt substrate implemented; positional physical-button labels from the live GamepadMap implemented; host surfaces share one physical A-confirm/B-back convention; physical-brand artwork deferred.

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

Onboarding's gameplay bindings, the Controls Clear/Reset hints and the frontend Options `PAD <SNES X> CONTROLS` hint use these live labels, because those actions are SNES controls. Host shortcuts that test a fixed physical `kGamepadBtn_*` position (Quick Practice `PAD X`, results `PAD X`, profile `PAD X`/`PAD Y`) keep fixed labels because they are not routed through GamepadMap.

## Host confirm/back convention

Every host-owned surface confirms with the physical south button (`A`) and goes back with east (`B`): the pause family, Records/Local Runs, profiles, Welcome/help, local-multiplayer join, and also the Quick Practice picker, Tour Progress, the Tour action surface, results navigation, frontend Options and Controls. This is the platform convention PC ports apply to their own menus (Steam/Xbox: south confirms), and it is independent of `[GamepadMap]`: a game remap changes what the stock game sees, not how the port's own menus navigate. Start still backs out where it did; the stock title's own screens keep the game's mapping.

Before this, the picker, Tour surfaces, results navigation, frontend Options and Controls resolved confirm/back through the SNES A/B semantics. Under the default positional map (SNES A = east, SNES B = south) that made the same physical button confirm in Pause and back out in the picker, and Controls read `B/ENTER SET  A/ESC BACK`. These surfaces now intercept physical A/B in `ur_uniracers_modern_system_gamepad_button` and ignore semantic SNES A/B, so a remap cannot add a hidden second confirm. Their hints name the fixed buttons (`PAD A`, `PAD B`). `UR_MAIN_MENU_PAD_ACCEPTANCE` now takes a comma-separated virtual-pad sequence from settled main (`a`, `b`, `x`, `y`, `r`, `start`); `x,a` (picker → `UR_PRACTICE STARTED`) and `x,b` (picker → `UR_PRACTICE_PICKER CANCELLED`) exercise this convention through real SDL input under a `--script` wait.

Nintendo-layout controllers (confirm on east) are a known follow-up: honoring them needs the framework to expose SDL3's per-device button labels, which the pinned host does not yet do.

## Future brand artwork

Brand-specific artwork (Xbox/PlayStation/Nintendo legends) remains deferred. If added, keep three things independent:

1. semantic action ownership;
2. active physical binding (the reverse map above);
3. artwork/glyph family.

Do not derive physical glyphs from a controller brand string, opaque source ID or SDL button ordinal alone.
