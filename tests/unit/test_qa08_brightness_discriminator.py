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

if __name__ == "__main__":
    unittest.main()
