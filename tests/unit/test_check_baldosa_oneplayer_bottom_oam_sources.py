"""Original native PPU bottom slots96/97 require separate source, not a guessed HD rider."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_oneplayer_bottom_oam_sources import (
    observed_rgb, assess,
)


class OnePlayerBottomOriginalSourcesTests(unittest.TestCase):
    def test_isolated_native_alpha_is_not_authoritative_final_layer_ownership(self):
        orig = bytearray(bytes((43, 66, 88, 0)) * (342 * 224))
        slot = bytearray(bytes((0, 0, 0, 0)) * (342 * 224))
        first = (118 * 342 + 116) * 4
        second = (119 * 342 + 117) * 4
        slot[first:first + 4] = bytes((43, 66, 88, 255))
        slot[second:second + 4] = bytes((245, 20, 60, 255))
        pixels = observed_rgb(bytes(orig), bytes(slot))
        self.assertEqual(pixels["isolated_source_opaque"], 2)
        self.assertEqual(pixels["source_rgb_equal_final_original"], 1)
        self.assertEqual(pixels["source_rgb_different_final_original"], 1)
        self.assertFalse(pixels["final_ppu_owner_proven"])
        slot[:] = bytes(len(slot))
        self.assertEqual(observed_rgb(bytes(orig), bytes(slot))["isolated_source_opaque"], 0)
        with self.assertRaisesRegex(ValueError, "dimensions"):
            observed_rgb(bytes(orig[:-4]), bytes(slot))

    def test_wrong_original_guest_identity_and_frames_fail_before_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stock, one, four = (root / p for p in ("base.crc", "one.crc", "four.crc"))
            stock.write_bytes(b"00000000\n" * 5447)
            one.write_bytes(stock.read_bytes())
            four.write_bytes(stock.read_bytes()[:-9])
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(stock, one, four, root, root,
                       root / "slot96.pam", root / "slot97.pam",
                       root / "one.log", root / "four.log")
            four.write_bytes(stock.read_bytes())
            with self.assertRaisesRegex(ValueError, "only guest2208"):
                assess(stock, one, four, root, root,
                       root / "slot96.pam", root / "slot97.pam",
                       root / "one.log", root / "four.log", frame=2224)
            with self.assertRaisesRegex(ValueError, "source guest-frame"):
                assess(stock, one, four, root, root,
                       root / "slot96.pam", root / "slot97.pam",
                       root / "one.log", root / "four.log")

    def test_native_workflow_single_1x_4x_guest_runs_not_new_one(self):
        root = Path(__file__).resolve().parents[2]
        wf = (root / ".github/workflows/baldosa-core-spike.yml").read_text()
        first = wf.index('UR_RACER_HD_WIDE_SOURCE_SLOT=96')
        second = wf.index('UR_RACER_HD_WIDE_SOURCE_SLOT=97', first)
        self.assertLess(first, second)
        self.assertIn('UR_RACER_HD_WIDE_SOURCE_FRAME=2208', wf[first:second])
        self.assertIn('UR_BALDOSA_WS342_LIVE=1', wf)
        self.assertIn('tools/check_baldosa_oneplayer_bottom_oam_sources.py', wf)
        self.assertIn('ws342_live_1p_bottom_slot96_97_source.json', wf)
        self.assertIn('unset UR_RACER_HD_WIDE_SOURCE_SLOT', wf[first:second])
        self.assertNotIn('UR_RACER_HD_WIDE_REMOVE_DIAGNOSTIC=counterfactual',
                         wf[first:second])
        self.assertIn('race_1p_ur_ws342_live"', wf[first:second])
        self.assertIn('race_1p_ur_ws342_live_4x"', wf[second:])


if __name__ == "__main__":
    unittest.main()
