"""QA-08 previous-results-frame observer preserves true original input."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_original_results_port_chronology as trial
import qa08_original_twoplayer_ppu_register_trace as original

ROUTE=ROOT/"reference/imported/reverse-engineering/baldosa-uniracers-recomp/tests/routes/race_2p.txt"


class ResultsPortChronologyTest(unittest.TestCase):
    def test_preserves_all_input_and_historical_register_dumps(self):
        raw=ROUTE.read_bytes()
        old=original.build_script(raw)
        new=trial.build_script(raw)
        self.assertEqual(new.replace(trial.SPLIT,trial.ANCHOR),old)
        self.assertEqual(new.count(b"dump qa08_"),4)
        self.assertEqual(new.count(b"press right+p2:right 1499\n"),1)
        self.assertEqual(new.count(b"press right+p2:right 1\n"),1)
        self.assertEqual(trial.DUMPS["qa08_results_previous"],5183)
        self.assertEqual(trial.DUMPS["qa08_results_cgram"],5184)
        for tag in original.DUMPS:
            self.assertEqual(new.count(b"dump "+tag.encode()+b"\n"),1)

    def test_rejects_altered_routes(self):
        raw=ROUTE.read_bytes()
        for changed in (
            raw.replace(b"right+p2:right 1500",b"right+p2:right 1499"),
            raw.replace(b"right+p2:right 1500",b"right+p2:left 1500"),
            raw.replace(b"turbo on\n",b""),
            raw+b"dump untrusted\n",
        ):
            with self.subTest(last=changed[-35:]):
                with self.assertRaises(ValueError):
                    trial.build_script(changed)

    def test_cgram_exact_size_and_fnv(self):
        self.assertEqual(trial.cgram_fnv(bytes(512)),"4d7705c5")
        for value in (b"",bytes(511),bytes(513)):
            with self.assertRaises(ValueError):
                trial.cgram_fnv(value)

    def test_fails_closed_on_original_frame_corruption(self):
        source=(ROOT/"tools/qa08_original_results_port_chronology.py").read_text()
        self.assertIn("original_unchanged_BGRX_sha256",source)
        self.assertIn("native_guest_phase_certified",source)
        self.assertNotIn("forcepoke(",source)
        self.assertNotIn("patch_guest",source)


if __name__=="__main__":
    unittest.main()
