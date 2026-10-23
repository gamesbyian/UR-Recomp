#!/usr/bin/env python3
"""Pin SDL controller smoke IDs against title-integration collisions.

Modes 15-19 are an executable Windows controller acceptance contract. A
future title merge may add new smoke modes but must not silently repurpose
these IDs and leave the native controller runner testing title gestures.
This is source-structure coverage, not a substitute for exact-head Win32 QA.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(encoding="utf-8")
RUNNER = (ROOT / "tools/run_baldosa_keyboard_pad_join_acceptance.py").read_text(
    encoding="utf-8"
)


def block(source: str, anchor: str) -> str:
    """Return one balanced C++ branch, rather than matching later branches."""
    start = source.index(anchor)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise ValueError(f"unclosed smoke branch: {anchor}")


def two_pad_contract(source: str) -> None:
    """Reject a one-pad or keyboard-confirming substitute for mode 19."""
    required = (
        'if (std::strcmp(opt, "19") == 0) {',
        'if (frame == 50u || frame == 52u)',
        'const int i = frame == 50u ? 0 : 1;',
        'SDL_AttachVirtualJoystick(&desc)',
        'if (frame == 60u || frame == 62u || frame == 64u)',
        'event.key.key = frame == 64u ? SDLK_RETURN : SDLK_DOWN;',
        'if (frame == 68u || frame == 69u ||',
        'frame == 72u || frame == 73u)',
        'const int i = frame >= 72u ? 1 : 0;',
        'const bool down = frame == 68u || frame == 72u;',
        'SDL_SetJoystickVirtualButton(',
        'pads[i], SDL_GAMEPAD_BUTTON_SOUTH, down',
    )
    for token in required:
        if token not in source:
            raise ValueError(f"mode 19 lost required independent-pad input: {token}")
    for forbidden in ('ur_baldosa_modern_root_gamepad(', 'join_confirm(',
                      'g_ram[', 'UR_BALDOSA_MODERN_TITLE'):
        if forbidden in source:
            raise ValueError(f"mode 19 bypasses controller event pump: {forbidden}")


class ControllerSmokeNamespaceTests(unittest.TestCase):
    def test_controller_modes_15_through_19_keep_their_own_branches(self):
        section = SOURCE.split(
            'extern "C" void ur_baldosa_modern_root_after_run_frame(', 1
        )[1]
        shared = block(section, 'if (std::strcmp(opt, "15") == 0 ||')
        for token in ('std::strcmp(opt, "16") == 0',
                      'std::strcmp(opt, "17") == 0',
                      'SDL_AttachVirtualJoystick(&desc)',
                      'SDL_SetJoystickVirtualButton(',
                      'SDL_DetachVirtualJoystick(ids[1])',
                      'const bool owner_leaves', 'const bool cancel'):
            self.assertIn(token, shared)
        lone = block(section, 'if (std::strcmp(opt, "18") == 0) {')
        for token in ('SDL_AttachVirtualJoystick(&desc)',
                      'SDL_DetachVirtualJoystick(ids[0])',
                      'SDL_SetJoystickVirtualButton('):
            self.assertIn(token, lone)
        two_pad = block(section, 'if (std::strcmp(opt, "19") == 0) {')
        two_pad_contract(two_pad)
        # The title can allocate disjoint modes. It cannot steal these five.
        for candidate in (shared, lone, two_pad):
            self.assertNotIn('UR_BALDOSA_MODERN_TITLE', candidate)

    def test_runner_still_calls_each_distinct_controller_mode(self):
        for output, mode in (
            ('keyboard_plus_pad', '15'), ('p2_owner_leaves', '16'),
            ('join_cancelled', '17'), ('lone_p2_pad', '18'),
            ('two_virtual_pads', '19'),
        ):
            with self.subTest(mode=mode):
                self.assertIn(f'out / "{output}", "{mode}"', RUNNER)

    def test_two_pad_source_contract_rejects_false_positive_mutations(self):
        section = SOURCE.split(
            'extern "C" void ur_baldosa_modern_root_after_run_frame(', 1
        )[1]
        original = block(section, 'if (std::strcmp(opt, "19") == 0) {')
        two_pad_contract(original)
        for old, new in (
            ('const int i = frame >= 72u ? 1 : 0;',
             'const int i = 0;'),
            ('const bool down = frame == 68u || frame == 72u;',
             'const bool down = frame == 68u;'),
            ('event.key.key = frame == 64u ? SDLK_RETURN : SDLK_DOWN;',
             'event.key.key = SDLK_RETURN;'),
            ('pads[i], SDL_GAMEPAD_BUTTON_SOUTH, down',
             'pads[0], SDL_GAMEPAD_BUTTON_SOUTH, down'),
        ):
            with self.subTest(mutation=old):
                self.assertIn(old, original)
                with self.assertRaisesRegex(ValueError, 'mode 19'):
                    two_pad_contract(original.replace(old, new, 1))


if __name__ == "__main__":
    unittest.main()
