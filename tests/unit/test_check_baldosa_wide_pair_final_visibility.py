"""Exact same-frame native PPU adjacent racer source removal contract."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_wide_pair_final_visibility import assess_pair
from tools.check_baldosa_wide_slot_final_visibility import (
    HEADER, WIDTH, HEIGHT,
)


class PairVisibilityTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.stock = root / "stock/ur-baldosa-ws342-001856.pam"
        self.front = root / "src/ur-baldosa-ws342-obj-slot98-frame001856.pam"
        self.rear = root / "src/ur-baldosa-ws342-obj-slot99-frame001856.pam"
        self.removed = root / "pair/ur-baldosa-ws342-001856.pam"
        self.logs = root / "pair.log"
        self.crcs = [root / f"crc-{i}" for i in range(4)]
        for x in (self.stock, self.front, self.rear, self.removed):
            x.parent.mkdir(parents=True, exist_ok=True)
        for x in self.crcs:
            x.write_text("frame-zero\nframe-one\n")
        self.logs.write_text(
            "UR_RACER_HD_WIDE_REMOVE_PAIR frame=1856 slots=98-99 "
            "status=armed guest_unchanged=1\n")
        self.base = bytearray(bytes((12, 13, 14, 0)) * (WIDTH * HEIGHT))
        self.front_pixels = bytearray(WIDTH * HEIGHT * 4)
        self.rear_pixels = bytearray(WIDTH * HEIGHT * 4)
        self.pair_pixels = bytearray(self.base)
        self.set_pixel(11, 40, True, True)
        self.set_pixel(331, 130, True, False)
        self.save()

    def set_pixel(self, x, y, front, rear):
        at = (y * WIDTH + x) * 4
        if front:
            self.front_pixels[at:at+4] = bytes((10, 30, 50, 255))
        if rear:
            self.rear_pixels[at:at+4] = bytes((10, 30, 50, 255))
        self.pair_pixels[at:at+4] = bytes((80, 81, 82, 0))

    def save(self):
        for path, data in ((self.stock, self.base),
                           (self.front, self.front_pixels),
                           (self.rear, self.rear_pixels),
                           (self.removed, self.pair_pixels)):
            path.write_bytes(HEADER + data)

    def result(self):
        return assess_pair(
            self.stock, self.front, self.rear, self.removed,
            *self.crcs, self.logs, first_slot=98, frame=1856)

    def test_positive_real_ppu_pair_effect_confined_to_source_union(self):
        out = self.result()
        self.assertEqual(out["status"], "passed")
        self.assertEqual(out["source_alpha_union_pixels"], 2)
        self.assertEqual(out["source_alpha_pair_overlap_pixels"], 1)
        self.assertEqual(out["final_changed_pixels"], 2)
        self.assertEqual(out["changed_outside_source_union"], 0)
        self.assertEqual(out["final_changed_top"], 1)
        self.assertEqual(out["final_changed_bottom"], 1)
        self.assertFalse(out["release_hd_admission"])

    def test_unexplained_changes_fail_closed(self):
        at = (70 * WIDTH + 80) * 4
        self.pair_pixels[at:at + 4] = bytes((200, 10, 20, 0))
        self.save()
        out = self.result()
        self.assertEqual(out["status"], "unproven")
        self.assertEqual(out["changed_outside_source_union"], 1)

    def test_missing_authorization_or_guest_divergence_fails(self):
        self.logs.write_text("not armed\n")
        self.assertEqual(self.result()["status"], "unproven")
        self.logs.write_text(
            "UR_RACER_HD_WIDE_REMOVE_PAIR frame=1856 slots=98-99 "
            "status=armed guest_unchanged=1\n")
        self.crcs[-1].write_text("different\n")
        self.assertEqual(self.result()["status"], "unproven")

    def test_invalid_slot_frame_and_raster_rejected(self):
        with self.assertRaisesRegex(ValueError, "pair must be exactly"):
            assess_pair(self.stock, self.front, self.rear, self.removed,
                        *self.crcs, self.logs, first_slot=97, frame=1856)
        with self.assertRaisesRegex(ValueError, "frame or slot names differ"):
            assess_pair(self.stock, self.front, self.rear, self.removed,
                        *self.crcs, self.logs, first_slot=98, frame=1872)
        self.rear.write_bytes(HEADER + self.rear_pixels[:-4])
        with self.assertRaisesRegex(ValueError, "342x224"):
            self.result()


if __name__ == "__main__":
    unittest.main()
