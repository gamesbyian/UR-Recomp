#!/usr/bin/env python3
"""Guard native shared Modern menu tokens against the canonical USA PPU capture.

This checks evidence-to-code parity, not visual/art approval or original asset
distribution. The C++ pixel tests separately exercise the actual painters.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "analysis/generated/menu-visual-language.json"
NATIVE = ROOT / "native/product/modern_menu_visual_grammar.hpp"


def native_array(header: str, name: str) -> tuple[int, ...]:
    """Read one literal constexpr array without interpreting C++ expressions."""
    start = header.find(name + "{{")
    if start < 0:
        raise ValueError(f"missing native source-token array: {name}")
    start += len(name) + 2
    end = header.find("}}", start)
    if end < 0:
        raise ValueError(f"unterminated native source-token array: {name}")
    values = header[start:end].strip().split(",")
    result = []
    for item in values:
        number = item.strip().removesuffix("u").removesuffix("U")
        if number:
            if not re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+)", number):
                raise ValueError(f"nonliteral {name} entry: {number!r}")
            result.append(int(number, 0))
    return tuple(result)


def rgb_to_argb(rgb: list[int]) -> int:
    if len(rgb) != 3 or any(not isinstance(c, int) or not 0 <= c <= 255
                           for c in rgb):
        raise ValueError("invalid measured source RGB triplet")
    r, g, b = rgb
    return 0xFF000000 | (r << 16) | (g << 8) | b


def native_scalar(header: str, name: str) -> int:
    match = re.search(r"\b" + re.escape(name) +
                      r"\s*=\s*(0x[0-9A-Fa-f]+|[0-9]+)u?\s*;", header)
    if match is None:
        raise ValueError(f"missing literal native source-token scalar: {name}")
    return int(match.group(1), 0)


class ModernMenuOriginalSourceTokensTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.header = NATIVE.read_text(encoding="utf-8")

    def test_palette_stops_are_exact_observed_usa_cgram(self):
        source = self.source
        self.assertEqual(source["schema_version"], 1)
        self.assertTrue(source["all_checks_pass"])
        palette = source["typography"]["palette_bgr555_as_rgb"]
        self.assertEqual(
            native_array(self.header, "kModernMenuYellowRamp"),
            tuple(rgb_to_argb(palette[i]) for i in (3, 4, 5, 6, 7)),
        )
        self.assertEqual(
            native_array(self.header, "kModernMenuGreyRamp"),
            tuple(rgb_to_argb(palette[i]) for i in (0, 12, 11, 10, 9)),
        )
        self.assertEqual(
            native_scalar(self.header, "kModernMenuCursorLight"),
            rgb_to_argb(source["cursor"]["arrow_palette_rgb"][15]),
        )
        self.assertEqual(
            native_scalar(self.header, "kModernMenuCursorDark"),
            rgb_to_argb(source["cursor"]["arrow_palette_rgb"][1]),
        )
        self.assertEqual(
            native_scalar(self.header, "kModernMenuSourceCursorShadow"),
            rgb_to_argb(source["cursor"]["shadow_palette_rgb"]),
        )
        self.assertEqual(native_scalar(self.header, "kModernMenuCursorShadowOffset"),
                         source["cursor"]["shadow_offset_px"][0])
        self.assertEqual(source["cursor"]["shadow_offset_px"], [7, 7])

    def test_motion_tables_are_exact_observed_usa_frames(self):
        source = self.source
        self.assertEqual(
            native_array(self.header, "kModernMenuSpinTile"),
            tuple(source["cursor"]["spin_cycle_tiles"]),
        )
        self.assertEqual(
            native_array(self.header, "kModernMenuSlidePixels"),
            tuple(source["transition_main_to_options"]["enter_hofs"]),
        )
        self.assertEqual(
            native_array(self.header, "kModernMenuObservedRowMoveY"),
            tuple(source["cursor"]["move_y_per_frame"]),
        )
        self.assertEqual(native_scalar(self.header, "kModernMenuSpinPeriod"),
                         source["cursor"]["spin_period_frames"])
        self.assertEqual(native_scalar(self.header, "kModernMenuSlideFrameCount"),
                         source["transition_main_to_options"]["enter_frames"])
        self.assertEqual(source["cursor"]["spin_frames_per_tile"], [2])
        self.assertEqual(source["cursor"]["move_settle_frames"], 12)
        self.assertIn("menu_frame / 2u", self.header)

    def test_menu_contexts_retain_source_only_variants(self):
        source = self.source
        screens = source["setup_strip"]["screens"]
        self.assertEqual(screens["rider"]["arrow_palette_highlight_rgb"],
                         [136, 200, 240])
        self.assertEqual(screens["tour"]["arrow_palette_highlight_rgb"],
                         [240, 160, 136])
        self.assertEqual(screens["track"]["arrow_palette_highlight_rgb"],
                         [240, 160, 136])
        self.assertIn("case ModernMenuSourceCursor::Rider: return 0xFF88C8F0u;",
                      self.header)
        self.assertIn("case ModernMenuSourceCursor::Track: return 0xFFF0A088u;",
                      self.header)
        self.assertEqual(screens["rider"]["big_font_rows"][0]["word_gaps_px"],
                         [8, 8])
        self.assertEqual(screens["tour"]["big_font_rows"][0]["word_gaps_px"],
                         [16])
        self.assertEqual(screens["track"]["big_font_rows"][0]["word_gaps_px"],
                         [16])
        self.assertIn("ModernMenuSourceCursor::Rider ? 8 : 16", self.header)

    def test_guard_detects_mutated_source_or_native_tokens(self):
        header = self.header
        source_yellow = self.source["typography"]["palette_bgr555_as_rgb"][3]
        first = rgb_to_argb(source_yellow)
        self.assertEqual(native_array(header, "kModernMenuYellowRamp")[0], first)
        altered = header.replace("0xFFF8F800u", "0xFFF8F801u", 1)
        self.assertNotEqual(native_array(altered, "kModernMenuYellowRamp")[0],
                            first)
        with self.assertRaisesRegex(ValueError, "nonliteral"):
            native_array(header.replace("0xFFF8F800u", "some_dynamic_colour", 1),
                         "kModernMenuYellowRamp")
        with self.assertRaisesRegex(ValueError, "missing"):
            native_scalar(header, "kImaginaryModernMenuSourceToken")


if __name__ == "__main__":
    unittest.main()
