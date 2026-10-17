"""Read-only pinned current PPU finish output sample guard tests."""
import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tools"))
from tools import qa08_rF017_finish_operand_patch as p
from tools import qa08_rF017_finish_operand_witness as w
class Probe(unittest.TestCase):
    def test_pinned_exact_PPU_source_and_idempotence(self):
        raw=(p.HEADER+p.ENTRY+p.MAIN+p.WINDOW+
             p.MATH_END+p.SUB+p.BEFORE_END)
        staged=p.patch(raw)
        self.assertEqual(staged,p.patch(staged))
        self.assertIn("pre_main=%d,%d,%d",staged)
        self.assertIn("snes_frame_counter == 3680",staged)
        # Full guest original PPU renders ~314M raster pixels; the observer
        # must not run getenv on ordinary coordinates.
        self.assertLess(staged.index('snes_frame_counter == 3680'),
                        staged.index('getenv("UR_QA08_RF017_FINISH_OPERAND_TRACE")'))
        for bad in (raw.replace(p.MAIN,""),staged.replace(p.MARK,"WRONG"),
                    staged.replace("post_math=%d,%d,%d","bogus"),raw+raw):
            with self.subTest(preview=bad[:45]),self.assertRaises(ValueError):
                p.patch(bad)
    def test_source_missing_and_wrong_guest_rejected(self):
        with self.assertRaisesRegex(ValueError,"complete"):
            w.inspect("",[])
        with self.assertRaisesRegex(ValueError,"source changed"):
            w.inspect("",["0xdeadbeef"]*5484)
if __name__=="__main__":unittest.main()
