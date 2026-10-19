"""QA08 three-real-archive medal pose onset: source-only ROM-free guards."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import qa08_verify_true_original_medal_boundary as witness


def synthetic(first=4032):
    table = {}
    for i, (x, y) in enumerate(witness.POINTS):
        before = (0x28, 0x71c9, 112, 0x15a2 + i)
        after = (0x27, 0x738e, None, None) if i == 0 else (0x28, 0x83cd, 96 + i, 0x15de)
        later = (0x28, 0x8183, 112, 0x15ae + i)
        for frame in range(first-3, first):
            table[frame,x,y] = before
        for frame in range(first, first+3):
            table[frame,x,y] = after
        table[first+3,x,y] = later
    return table


class OriginalMedalSourceTransition(unittest.TestCase):
    def test_three_field_plateaus_and_exact_flip(self):
        rows = witness.true_source_boundary(synthetic(), 4032)
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r["source_internal_previous"] == 4031 for r in rows))
        self.assertTrue(all(r["source_internal_first_new_pose"] == 4032 for r in rows))
        self.assertTrue(all(r["source_internal_first_next_pose"] == 4035 for r in rows))
        self.assertEqual(rows[0]["after_actual_winner_slot"], None)

    def test_reject_absent_pose_change(self):
        table=synthetic()
        p=witness.POINTS[1]
        for frame in range(4032, 4036):
            table[frame,*p]=table[4031,*p]
        with self.assertRaisesRegex(ValueError,"pose onset"):
            witness.true_source_boundary(table,4032)

    def test_reject_forged_frame_or_unstable_plateau(self):
        table=synthetic()
        del table[4032,*witness.POINTS[0]]
        with self.assertRaisesRegex(ValueError,"missing original field"):
            witness.true_source_boundary(table,4032)
        table=synthetic()
        table[4030,*witness.POINTS[0]]=(0,0,None,None)
        with self.assertRaisesRegex(ValueError,"stability"):
            witness.true_source_boundary(table,4032)

    def test_reject_source_sha_without_emulator_run(self):
        with patch.object(Path,"read_bytes",return_value=b"forged"):
            with self.assertRaisesRegex(ValueError,"identity"):
                witness.verify(Path("wrong.zip"),Path("painter.zip"),Path("native.zip"))

    def test_no_bootstrapped_video_or_native_frame_shift(self):
        self.assertEqual(witness.SOURCE_FRAMES,(4032,4176))
        self.assertEqual(witness.SOURCE_FRAMES[1]-witness.SOURCE_FRAMES[0],144)
        self.assertEqual(witness.ORIGINAL_NESTED_SHA,
            "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e")
        self.assertEqual(witness.POINTS,witness.owners.POINTS)
        source=(ROOT/"tools/qa08_verify_true_original_medal_boundary.py").read_text()
        for literal in (
            '"source_original_native_consumed_input_and_beam_proven": False',
            '"global_frame_shift_permitted": False',
            '"release_acceptance": False',
            'callbacks.verify(source_path, painter)',
            'owners.verify(painter, native_4bpp)',
        ):
            self.assertIn(literal,source)
        self.assertNotIn("PpuSetOverlayOamRange",source)

if __name__=="__main__":
    unittest.main()
