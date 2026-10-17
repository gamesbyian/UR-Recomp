"""Opt-in original Snes9x 4015..4017 blackout readback cannot alter input."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_snesref_results_previous_patch as previous
import qa08_snesref_original_blackout_host_patch as blackout

class OriginalBlackoutHostTest(unittest.TestCase):
    def test_readonly_after_core_frame_and_idempotence(self):
        source=(previous.BEFORE+"\n"+previous.HISTORY_CODE+
                "\n"+previous.HISTORY_MARK+"\n")
        # The existing original patch already replaces the main frame hook
        # and inserts the read-only debug journal before do_dump.
        original=source.replace(previous.BEFORE,previous.AFTER)
        changed=blackout.patch_source(original)
        self.assertEqual(blackout.patch_source(changed),changed)
        self.assertIn('getenv("UR_QA08_ORIGINAL_BLACKOUT")',changed)
        self.assertIn('do_dump("qa08_blackout_4015")',changed)
        self.assertIn('do_dump("qa08_blackout_4016")',changed)
        self.assertIn('do_dump("qa08_blackout_4017")',changed)
        self.assertIn("qa08_original_blackout_inidisp_history();",changed)
        self.assertEqual(changed.replace(blackout.WRITE_HISTORY,
                                        blackout.DUMP_ANCHOR)
                                .replace(blackout.HOOK_AFTER,previous.AFTER),
                         original)
    def test_strict_rejects_foreign_and_tampered_host(self):
        with self.assertRaises(ValueError):
            blackout.patch_source(previous.AFTER)
        source=(previous.AFTER+"\n"+previous.HISTORY_CODE+"\n")
        correct=blackout.patch_source(source)
        for bad in (
            correct.replace("g_frame==4036","g_frame==0"),
            correct.replace('g_frame==4016','g_frame==9999'),
        ):
            with self.subTest(bad=bad[-40:]):
                with self.assertRaises(ValueError):
                    blackout.patch_source(bad)

if __name__=="__main__":
    unittest.main()
