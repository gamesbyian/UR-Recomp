"""Fail-closed native 1P later-source provenance and route identity."""
import tempfile
from pathlib import Path
import unittest

from tools.check_baldosa_late_1p_original import read_log


class LateOnePlayerSourceTests(unittest.TestCase):
    def test_exact_guest_mode_script_density_and_capture_frame(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "native.log"
            base = (
                "UR_BALDOSA_WS342_LIVE_MODE frame=550 mode=1 "
                "guest_race=3C frontend=3C\n"
                "script f=1720 until 00E1F ok after 351 frames\n"
                "UR_BALDOSA_WS342_LATE_PRESENT frame=2208 saved=1 "
                "logical=342x224 density=1 source=native-original-ppu\n"
                "script f=5447 dump end ok\n"
            )
            log.write_text(base)
            self.assertEqual(read_log(log, 1, 2200, 5447), 2208)
            with self.assertRaisesRegex(ValueError, "density-specific"):
                read_log(log, 4, 2200, 5447)
            with self.assertRaisesRegex(ValueError, "terminal"):
                read_log(log, 1, 2200, 5446)
            log.write_text(base.replace("frontend=3C", "frontend=3D"))
            with self.assertRaisesRegex(ValueError, "scene"):
                read_log(log, 1, 2200, 5447)
            log.write_text(base.replace("frame=2208 saved=1", "frame=2488 saved=1"))
            with self.assertRaisesRegex(ValueError, "window"):
                read_log(log, 1, 2200, 5447)
            log.write_text(base.replace(
                "script f=1720 until 00E1F ok after 351 frames\n", ""))
            with self.assertRaisesRegex(ValueError, "milestone"):
                read_log(log, 1, 2200, 5447)
            repeated = (
                "UR_BALDOSA_WS342_LATE_PRESENT frame=2224 saved=1 "
                "logical=342x224 density=1 source=native-original-ppu\n"
            )
            log.write_text(base + repeated)
            with self.assertRaisesRegex(ValueError, "density-specific"):
                read_log(log, 1, 2200, 5447)


if __name__ == "__main__":
    unittest.main()
