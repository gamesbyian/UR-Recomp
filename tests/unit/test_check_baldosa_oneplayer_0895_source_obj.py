"""Real native 1P semantic0895 OBJ-source witness must not claim BG priority or HD."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_oneplayer_0895_source_obj import (
    alpha_vs_final, assess,
)


class NativeOnePlayer0895SourceTests(unittest.TestCase):
    def test_source_plane_alpha_vs_full_ppu_final_is_observational(self):
        orig = bytearray(bytes((120, 25, 60, 0)) * (342 * 224))
        src = bytearray(bytes((0, 0, 0, 0)) * (342 * 224))
        first = (115 * 342 + 100) * 4
        second = (115 * 342 + 101) * 4
        src[first:first+4] = bytes((120, 25, 60, 255))
        src[second:second+4] = bytes((200, 99, 30, 255))
        report = alpha_vs_final(bytes(orig), bytes(src))
        self.assertEqual(report["source_opaque_pixels"], 2)
        self.assertEqual(report["source_opaque_rgb_matches_final_raster"], 1)
        self.assertEqual(report["source_opaque_rgb_differs_from_final_raster"], 1)
        self.assertEqual(report["source_alpha_empty_pixels"], 342 * 224 - 2)
        self.assertFalse(report["final_owner_or_priority_proven"])
        with self.assertRaisesRegex(ValueError, "dimensions"):
            alpha_vs_final(bytes(orig[:-4]), bytes(src))

    def test_identity_and_crc_cannot_be_bypassed_by_fake_alphas(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            control, trial = root / "stock.crc", root / "4x.crc"
            control.write_bytes(b"DEADBEEF\n" * 5447)
            trial.write_bytes(b"DEADBEEF\n" * 5446)
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(control, trial, root, root,
                       root / "source.pam", root / "native.log")
            with self.assertRaisesRegex(ValueError, "only the authenticated"):
                assess(control, trial, root, root,
                       root / "source.pam", root / "native.log",
                       guest_frame=1856)
            with self.assertRaisesRegex(ValueError, "only the authenticated"):
                assess(control, trial, root, root,
                       root / "source.pam", root / "native.log", slot=98)

    def test_workflow_uses_existing_native_one_player_fourfold_guest_only(self):
        root = Path(__file__).resolve().parents[2]
        script = (root / ".github/workflows/baldosa-core-spike.yml").read_text()
        self.assertIn("UR_RACER_HD_WIDE_SOURCE_SLOT=97", script)
        self.assertIn("UR_RACER_HD_WIDE_SOURCE_FRAME=2208", script)
        self.assertIn("UR_BALDOSA_WS342_LIVE=1", script)
        self.assertIn("tools/check_baldosa_oneplayer_0895_source_obj.py", script)
        self.assertIn("unset UR_RACER_HD_WIDE_SOURCE_SLOT UR_RACER_HD_WIDE_SOURCE_FRAME", script)
        self.assertIn("ws342_live_1p_0895_source_obj.json", script)
        self.assertIn('race_1p_ur_ws342_live_4x"', script)
        # Do not change the shared guest route, invent a new session or
        # allow the separate destructive counterfactual OAM mode.
        self.assertNotIn("UR_RACER_HD_WIDE_REMOVE_DIAGNOSTIC=counterfactual",
                         script.split("UR_RACER_HD_WIDE_SOURCE_SLOT=97")[1]
                               .split("tools/check_baldosa_oneplayer_0895_source_obj.py")[0])


if __name__ == "__main__":
    unittest.main()
