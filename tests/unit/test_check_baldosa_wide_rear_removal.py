"""Exact rear-only PPU deletion observation, including legitimate zero delta."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.check_baldosa_wide_rear_removal import assess_rear
from tools.check_baldosa_wide_slot_final_visibility import HEADER, WIDTH, HEIGHT


class RearOnlyNativeRemovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.stock = root / "stock/ur-baldosa-ws342-001856.pam"
        self.src = root / "rear/ur-baldosa-ws342-obj-slot99-frame001856.pam"
        self.removed = root / "deleted/ur-baldosa-ws342-001856.pam"
        self.crcs = [root / f"crc{i}" for i in range(3)]
        self.log = root / "log.txt"
        for x in (self.stock, self.src, self.removed):
            x.parent.mkdir(parents=True, exist_ok=True)
        for c in self.crcs:
            c.write_text("frame000\nframe001\n")
        self.log.write_text(
            "UR_RACER_HD_WIDE_REMOVE_SLOT frame=1856 slot=99 "
            "status=armed guest_unchanged=1\n")
        self.base = bytearray(bytes((5, 7, 9, 0)) * (WIDTH * HEIGHT))
        self.source = bytearray(WIDTH * HEIGHT * 4)
        self.deletion = bytearray(self.base)
        at = (20 * WIDTH + 45) * 4
        self.source[at:at+4] = bytes((100, 110, 120, 255))
        self.base[at:at+4] = bytes((100, 110, 120, 0))
        self.deletion[at:at+4] = bytes((100, 110, 120, 0))
        self.save()

    def save(self):
        for f, v in ((self.stock, self.base),
                     (self.src, self.source), (self.removed, self.deletion)):
            f.write_bytes(HEADER + v)

    def result(self):
        return assess_rear(self.stock, self.src, self.removed, *self.crcs,
                           self.log, rear_slot=99, frame=1856)

    def test_no_delta_is_observable_but_never_release_authority(self):
        r = self.result()
        self.assertEqual(r["status"], "observed-no-rear-color-change")
        self.assertEqual(r["rear_source_emitted_pixels"], 1)
        self.assertEqual(r["rear_deletion_changed_pixels"], 0)
        self.assertFalse(r["winner_identity_proven"])
        self.assertFalse(r["release_hd_admission"])

    def test_real_rear_pixel_change_counted_in_correct_half(self):
        at = (20 * WIDTH + 45) * 4
        self.deletion[at:at+4] = bytes((5, 7, 9, 0))
        self.save()
        r = self.result()
        self.assertEqual(r["status"], "observed-rear-color-change")
        self.assertEqual(r["rear_deletion_changed_pixels"], 1)
        self.assertEqual(r["rear_deletion_changed_top"], 1)
        self.assertEqual(r["rear_deletion_changed_bottom"], 0)

    def test_foreign_pixels_crc_and_arming_fail_closed(self):
        at = (134 * WIDTH + 240) * 4
        self.deletion[at:at+4] = bytes((99, 20, 30, 0))
        self.save()
        self.assertEqual(self.result()["status"], "unproven")
        self.deletion[at:at+4] = self.base[at:at+4]
        self.save()
        self.crcs[2].write_text("altered\n")
        self.assertEqual(self.result()["status"], "unproven")
        self.crcs[2].write_text("frame000\nframe001\n")
        self.log.write_text("no native PPU marker\n")
        self.assertEqual(self.result()["status"], "unproven")

    def test_bad_slot_frame_or_raster_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "only rear OAM"):
            assess_rear(self.stock, self.src, self.removed, *self.crcs,
                        self.log, rear_slot=98, frame=1856)
        with self.assertRaisesRegex(ValueError, "guest frame names"):
            assess_rear(self.stock, self.src, self.removed, *self.crcs,
                        self.log, rear_slot=99, frame=1872)
        self.src.write_bytes(HEADER + self.source[:-4])
        with self.assertRaisesRegex(ValueError, "342x224"):
            self.result()

    def test_direct_cli_has_no_package_path_dependency(self):
        root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, str(root / "tools/check_baldosa_wide_rear_removal.py"),
             "--help"], cwd=root, env=env,
            capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--rear-slot", result.stdout)


if __name__ == "__main__":
    unittest.main()
