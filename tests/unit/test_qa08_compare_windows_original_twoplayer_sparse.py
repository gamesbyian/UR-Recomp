"""Full original/Windows two-pad source comparator must fail closed."""
from pathlib import Path
import sys
import tempfile
import unittest
import json

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_compare_windows_original_twoplayer_sparse as two


class TwoPlayerStrictSourceComparatorTest(unittest.TestCase):
    def test_only_genuine_256x224_same_frame_registration(self):
        self.assertEqual((two.FIRST,two.LAST,two.STEP),(1280,5472,16))
        self.assertEqual(two.NUM,263)
        self.assertEqual((two.W,two.H),(256,224))
        c=(ROOT/"tools/qa08_compare_windows_original_twoplayer_sparse.py").read_text()
        self.assertIn("callback=guest-1",c)
        self.assertIn("compare(ref,p7[len(HEADER):])",c)
        self.assertNotIn("resize(",c)
        self.assertNotIn("nearest(",c)
        self.assertNotIn("crop(",c)

    def test_unqualified_source_rejected_before_pixel_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            o=root/"original";o.mkdir()
            w=root/"windows";w.mkdir()
            (o/"qa08-original-2p-fullroute.json").write_text(json.dumps({
                "schema":"fabricated"}))
            (w/"qa08-windows-2p-fullroute.json").write_text("{}")
            route=root/"race_2p.txt"
            route.write_text("turbo on\nquit\n")
            (o/"original.script").write_text("quit\n")
            with self.assertRaisesRegex(ValueError,"original Snes9x"):
                two.inspect(o,w,route)


if __name__=="__main__":
    unittest.main()
