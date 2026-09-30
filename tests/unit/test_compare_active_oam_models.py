from __future__ import annotations

import unittest

from tools.compare_active_oam_models import (
    ares_active_high_target,
    compare,
    jgenesis_active_high_target,
    mame_active_target,
    snes9x_uniracers_first_high_byte,
)


class ActiveOamModelTests(unittest.TestCase):
    def test_uniracers_sprite_96_converges_on_0218(self) -> None:
        report = compare(96)
        self.assertTrue(report["all_converge"])
        self.assertEqual(set(report["targets"].values()), {"0x218"})

    def test_one_variable_change_separates_fixed_and_dynamic_models(self) -> None:
        report = compare(64)
        self.assertFalse(report["all_converge"])
        self.assertEqual(report["targets"]["snes9x_uniracers"], "0x218")
        self.assertEqual(report["targets"]["mame"], "0x218")
        self.assertEqual(report["targets"]["ares"], "0x210")
        self.assertEqual(report["targets"]["jgenesis"], "0x210")

    def test_pinned_source_formulas(self) -> None:
        self.assertEqual(snes9x_uniracers_first_high_byte(), 0x218)
        self.assertEqual(mame_active_target(), 0x218)
        self.assertEqual(ares_active_high_target(127), 0x21F)
        self.assertEqual(jgenesis_active_high_target(0), 0x200)

    def test_sprite_index_range_is_checked(self) -> None:
        with self.assertRaises(ValueError):
            ares_active_high_target(128)
        with self.assertRaises(ValueError):
            jgenesis_active_high_target(-1)


if __name__ == "__main__":
    unittest.main()
