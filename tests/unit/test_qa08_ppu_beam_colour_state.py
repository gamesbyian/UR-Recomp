"""Synthetic beam-order regression; these are not new original/native PPU passes."""
from __future__ import annotations

import unittest

from tools.qa08_ppu_beam_colour_state import beam_key, decode_field


def entry(line, register, value):
    return {"l": line, "r": f"0x{register:04X}", "v": f"0x{value:02X}"}


def visible_at(record, line):
    for span in record["visible_line_tag_intervals_after_same_line_final_write"]:
        if span["first_visible_line_tag"] <= line <= span["last_visible_line_tag"]:
            return span
    raise AssertionError(line)


class BeamOrderColourStateTest(unittest.TestCase):
    def test_real_native_field_wrap_and_vblank_before_visible(self):
        self.assertEqual([beam_key(t) for t in (225, 226, 261, 0, 1, 223, 224)],
                         [0, 1, 36, 37, 38, 260, 261])
        record = decode_field({"cgadsub": "0x13"}, [
            entry(230, 0x2131, 0x10),
            entry(230, 0x2130, 0x02),
            entry(0, 0x2132, 0x2D),
            entry(43, 0x2132, 0x4F),
            entry(45, 0x2131, 0x00),
        ])
        first = visible_at(record, 0)
        self.assertEqual(first["cgadsub"], "0x10")
        self.assertEqual(first["cgwsel"], "0x02")
        self.assertEqual(first["fixed_R5_G5_B5"], [13, None, None])
        self.assertIsNone(first["fixed_rgb15"])
        self.assertEqual(visible_at(record, 42)["fixed_R5_G5_B5"], [13, None, None])
        self.assertEqual(visible_at(record, 43)["fixed_R5_G5_B5"], [13, 15, None])
        self.assertEqual(visible_at(record, 44)["cgadsub"], "0x10")
        self.assertEqual(visible_at(record, 45)["cgadsub"], "0x00")
        self.assertEqual(len(record["completed_visible_line_tags"]), 224)
        self.assertEqual(record["visible_line_tag_intervals_after_same_line_final_write"][0]["first_visible_line_tag"], 0)
        self.assertEqual(record["visible_line_tag_intervals_after_same_line_final_write"][-1]["last_visible_line_tag"], 223)
        self.assertFalse(record["source_colour_math_operand_per_pixel_proven"])

    def test_rgb_component_writes_enable_independently_and_same_line_order(self):
        record = decode_field({"cgadsub": "0x13"}, [
            entry(0, 0x2132, 0xA5),
            entry(0, 0x2132, 0x4A),
            entry(0, 0x2132, 0x8B),
            entry(3, 0x2132, 0x0F),
            entry(10, 0x2132, 0xFF),
        ])
        first = visible_at(record, 0)
        self.assertEqual(first["fixed_R5_G5_B5"], [5, 10, 11])
        self.assertEqual(first["fixed_rgb15"], "0x2D45")
        self.assertEqual(visible_at(record, 4)["fixed_R5_G5_B5"], [5, 10, 11])
        self.assertEqual(visible_at(record, 10)["fixed_rgb15"], "0x7FFF")
        self.assertEqual([e["journal_index"] for e in record["colour_writes_in_original_beam_order"]],
                         list(range(5)))

    def test_unobserved_baselines_stay_unknown_after_no_write(self):
        record = decode_field({"cgadsub": "0x03"}, [])
        first = visible_at(record, 0)
        self.assertEqual(first["cgadsub"], "0x03")
        self.assertIsNone(first["cgwsel"])
        self.assertEqual(first["fixed_R5_G5_B5"], [None, None, None])
        self.assertFalse(record["baseline_cgwsel_known"])
        self.assertFalse(record["baseline_fixed_colour_known"])

    def test_out_of_beam_order_crossing_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            decode_field({"cgadsub": "0x01"}, [entry(1, 0x2131, 0x10),
                                                  entry(225, 0x2131, 0x11)])
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            decode_field({"cgadsub": "0x01"}, [entry(3, 0x2131, 0x10),
                                                  entry(2, 0x2131, 0x11)])
        with self.assertRaisesRegex(ValueError, "invalid native beam"):
            decode_field({"cgadsub": "0x01"}, [entry(262, 0x2131, 0x10)])

    def test_bool_tags_and_invalid_formats_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid native beam"):
            decode_field({"cgadsub": "0x01"}, [{"l": True, "r": "0x2131", "v": "0x10"}])
        for bad in ({"l": 0, "r": "0x2131", "v": "0xGG"},
                    {"l": 0, "r": "0x420B", "v": "0x20"},
                    {"l": 0, "r": "0x2131", "v": 16}):
            with self.assertRaisesRegex(ValueError, "invalid"):
                decode_field({"cgadsub": "0x00"}, [bad])
        with self.assertRaisesRegex(ValueError, "baseline"):
            decode_field({"cgadsub": "13"}, [])
        with self.assertRaisesRegex(ValueError, "overlong"):
            decode_field({"cgadsub": "0x00"}, [entry(0, 0x2131, 0)] * 4097)

    def test_completed_field_baseline_does_not_claim_live_HDMA_operand(self):
        report = decode_field({"cgadsub": "0x04", "cgwsel": "0x02",
                               "fixed15": "0x0260"}, [])
        state = visible_at(report, 50)
        self.assertEqual(state["fixed_rgb15"], "0x0260")
        self.assertEqual(report["state_interval_scope"],
                         "recorded raster journal writes only")
        self.assertFalse(report["render_time_hdma_ppu_writes_recorded_by_this_journal"])
        self.assertFalse(report["field_baseline_fixed_RGB_is_effective_per_scanline"])
        self.assertFalse(report["render_time_live_fixed_RGB_sampled"])
        self.assertFalse(report["source_colour_math_operand_per_pixel_proven"])

    def test_saved_native_baselines_override_unknowns(self):
        report = decode_field({"cgadsub": "0x13", "cgwsel": "0x02",
                               "fixed15": "0x296D"},
                              [entry(225, 0x2132, 0x4A)])
        first = visible_at(report, 0)
        self.assertTrue(report["baseline_cgwsel_known"])
        self.assertTrue(report["baseline_fixed_colour_known"])
        self.assertEqual(first["cgwsel"], "0x02")
        self.assertEqual(first["fixed_R5_G5_B5"], [13, 10, 10])
        self.assertEqual(first["fixed_rgb15"], "0x294D")

    def test_invalid_claimed_native_baselines_rejected(self):
        for key, value in (("cgwsel", "0xG1"), ("cgwsel", 1),
                           ("fixed15", "0x8000"), ("fixed15", "0xG002"),
                           ("fixed15", 0)):
            with self.assertRaisesRegex(ValueError, "baseline"):
                decode_field({"cgadsub": "0x00", key: value}, [])

    def test_host_final_registers_are_not_invented_as_field_baselines(self):
        record = decode_field({"cgadsub": "0x10"}, [entry(225, 0x2131, 0x01)])
        self.assertIsNone(visible_at(record, 1)["cgwsel"])
        self.assertIsNone(visible_at(record, 1)["fixed_rgb15"])
        self.assertEqual(visible_at(record, 1)["cgadsub"], "0x01")


if __name__ == "__main__":
    unittest.main()
