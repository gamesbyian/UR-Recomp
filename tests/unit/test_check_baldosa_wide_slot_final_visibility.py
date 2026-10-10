"""All-pixel regression for native one-slot removal counterfactual."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_wide_slot_final_visibility import (
    assess, HEADER, WIDTH, HEIGHT,
)


class WideFinalSlotVisibilityTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        root = Path(self.td.name)
        self.stock = root / "stock/ur-baldosa-ws342-001856.pam"
        self.removed = root / "removed/ur-baldosa-ws342-001856.pam"
        self.source = root / "source/ur-baldosa-ws342-obj-slot98-frame001856.pam"
        self.stock_crc = root / "stock_crc"
        self.source_crc = root / "source_crc"
        self.removed_crc = root / "removed_crc"
        self.log = root / "removal_log"
        for x in (self.stock, self.removed, self.source):
            x.parent.mkdir(parents=True, exist_ok=True)
        self.stock_crc.write_text("abcd1234\nabcd5678\n")
        self.source_crc.write_text("abcd1234\nabcd5678\n")
        self.removed_crc.write_text("abcd1234\nabcd5678\n")
        self.log.write_text(
            "UR_RACER_HD_WIDE_REMOVE_SLOT frame=1856 slot=98 "
            "status=armed guest_unchanged=1\n")
        self.original = bytearray(bytes((30, 40, 50, 255)) * WIDTH * HEIGHT)
        self.alpha = bytearray(WIDTH * HEIGHT * 4)
        self.counterfactual = bytearray(self.original)
        self.set_pixel(11, 40)
        self.set_pixel(331, 130)
        self.write()

    def set_pixel(self, x, y):
        at = (y * WIDTH + x) * 4
        self.alpha[at:at + 4] = bytes((200, 120, 80, 255))
        self.counterfactual[at:at + 4] = bytes((3, 4, 5, 255))

    def write(self):
        self.stock.write_bytes(HEADER + self.original)
        self.removed.write_bytes(HEADER + self.counterfactual)
        self.source.write_bytes(HEADER + self.alpha)

    def proof(self):
        return assess(self.stock, self.source, self.removed,
                      self.stock_crc, self.source_crc, self.removed_crc,
                      self.log, slot=98, frame=1856)

    def test_final_visible_pixels_are_derived_from_original_composite(self):
        p = self.proof()
        self.assertEqual(p["status"], "passed")
        self.assertEqual(p["native_ppu_final_contributed_pixels"], 2)
        self.assertEqual(p["source_emitted_alpha_pixels"], 2)
        self.assertEqual(p["native_ppu_changed_outside_emitted_source_alpha"], 0)
        self.assertEqual(p["visible_pixels_top"], 1)
        self.assertEqual(p["visible_pixels_bottom"], 1)
        self.assertEqual(p["visible_pixels_left_margin"], 1)
        self.assertEqual(p["visible_pixels_right_margin"], 1)

    def test_source_alpha_is_not_equivalent_to_final_visibility(self):
        at = (40 * WIDTH + 11) * 4
        self.counterfactual[at:at + 4] = self.original[at:at + 4]
        self.write()
        p = self.proof()
        self.assertEqual(p["status"], "passed")
        self.assertEqual(p["source_emitted_alpha_pixels"], 2)
        self.assertEqual(p["native_ppu_final_contributed_pixels"], 1)
        self.assertEqual(p["visible_pixels_top"], 0)
        self.assertEqual(p["visible_pixels_bottom"], 1)

    def test_outside_source_change_cannot_be_attributed_to_this_slot(self):
        at = (63 * WIDTH + 85) * 4
        self.counterfactual[at:at + 4] = bytes((1, 2, 3, 255))
        self.write()
        p = self.proof()
        self.assertEqual(p["status"], "unproven")
        self.assertEqual(p["native_ppu_changed_outside_emitted_source_alpha"], 1)

    def test_invisible_slot_is_not_awarded_hd_admission(self):
        self.counterfactual[:] = self.original
        self.write()
        self.assertEqual(self.proof()["status"], "unproven")

    def test_source_guest_crc_and_diagnostic_authority_are_required(self):
        self.removed_crc.write_text("abcd1234\nxyz\n")
        self.assertEqual(self.proof()["status"], "unproven")
        self.removed_crc.write_text("abcd1234\nabcd5678\n")
        self.log.write_text("UR_RACER_HD_WIDE_REMOVE_SLOT frame=1856 slot=97 "
                            "status=armed guest_unchanged=1\n")
        self.assertEqual(self.proof()["status"], "unproven")

    def test_wrong_frame_and_bad_raster_fail(self):
        with self.assertRaises(ValueError):
            assess(self.stock, self.source, self.removed,
                   self.stock_crc, self.source_crc, self.removed_crc,
                   self.log, slot=98, frame=1872)
        self.source.write_bytes(HEADER + self.alpha[:-4])
        with self.assertRaises(ValueError):
            self.proof()


if __name__ == "__main__":
    unittest.main()
