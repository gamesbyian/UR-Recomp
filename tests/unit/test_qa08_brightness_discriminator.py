"""ROM-free empirical brightness fit checks, not hardware colour proof."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa08_brightness_discriminator as model

class BrightnessDiscriminator(unittest.TestCase):
    def test_rgb5_expansion_and_brightness(self):
        for value in range(32):
            expanded = (value << 3) | (value >> 2)
            self.assertEqual(model.scale_channel(value, 14), expanded * 14 // 15)
        self.assertEqual(model.scale_channel(0, 0), 0)
        self.assertEqual(model.scale_channel(31, 15), 255)

    def test_invalid_channel_and_brightness_refused(self):
        for channel, brightness in ((-1,14),(32,14),(0,-1),(0,16),(False,14),(4,False)):
            with self.subTest(channel=channel, brightness=brightness), self.assertRaises(ValueError):
                model.scale_channel(channel, brightness)

    def test_selected_word_model_is_not_gate_credit(self):
        for word in ("4210","4631","4a52","56b5"):
            self.assertEqual(len(model.expected_rgb(word,14)), 3)

    def test_rgb555_high_bit_is_not_an_observed_colour(self):
        # SNES RGB555 uses fifteen colour bits; bit 15 is noncanonical.
        for word in ("8000", "ffff", "c210"):
            with self.subTest(word=word), self.assertRaisesRegex(
                    ValueError, "RGB555 high bit"):
                model.expected_rgb(word, 14)
        self.assertEqual(len(model.expected_rgb("7fff", 14)), 3)

    def test_source_fields_reject_retagged_high_bit_palette_words(self):
        fields = {"frame": "5176", "x": "53", "logical_y": "41",
                  "ppu_line": "52", "index": "00", "inidisp": "0e",
                  "cgadsub": "00", "cgwsel": "00"}
        colour_fields = ("selected_rgb555", "cgram_index_word",
                         "cgram6c", "cgram6d", "cgram6e", "cgram6f")
        for key in colour_fields:
            fields[key] = "4210"
        model._canonical_observation(fields, "UR_QA08_LATE_PPU_SOURCE")
        for key in colour_fields:
            with self.subTest(key=key):
                bad = dict(fields, **{key: "c210"})
                with self.assertRaisesRegex(ValueError, "noncanonical RGB555"):
                    model._canonical_observation(bad, "UR_QA08_LATE_PPU_SOURCE")

if __name__ == "__main__":
    unittest.main()
