"""Reference result preceding-frame dump must not alter the input stream."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_original_results_port_chronology as trial
import qa08_original_twoplayer_ppu_register_trace as original
import qa08_snesref_results_previous_patch as stage

ROUTE=ROOT/"reference/imported/reverse-engineering/baldosa-uniracers-recomp/tests/routes/race_2p.txt"

class ResultsPortChronologyTest(unittest.TestCase):
    def test_original_controller_script_bitwise_identical_to_accepted_prior_three_dumps(self):
        raw=ROUTE.read_bytes()
        self.assertEqual(trial.build_script(raw), original.build_script(raw))
        self.assertEqual(trial.build_script(raw).count(b"dump qa08_"),3)
        self.assertNotIn(b"dump qa08_results_previous",trial.build_script(raw))
        self.assertEqual(trial.DUMPS["qa08_results_previous"],5183)
        self.assertEqual(trial.DUMPS["qa08_results_cgram"],5184)

    def test_invalid_original_script_rejected(self):
        raw=ROUTE.read_bytes()
        for changed in (raw.replace(b"right+p2:right 1500",b"right+p2:right 1499"),
                        raw.replace(b"right+p2:right 1500",b"right+p2:left 1500"),
                        raw.replace(b"turbo on\n",b""),raw+b"dump arbitrary\n"):
            with self.subTest(last=changed[-35:]):
                with self.assertRaises(ValueError):
                    trial.build_script(changed)

    def test_readonly_host_patch_is_exact_idempotent_and_rejects_tamper(self):
        frame="static void do_dump(const char* tag) {}\n"+stage.BEFORE+"int trailing;\n"
        once=stage.patch_source(frame)
        self.assertIn(stage.MARK,once)
        self.assertEqual(stage.patch_source(once),once)
        self.assertEqual(once.count("do_dump(\"qa08_results_previous\")"),1)
        self.assertIn("getenv",once)
        with self.assertRaises(ValueError):
            stage.patch_source(once.replace("5183","5184"))
        with self.assertRaises(ValueError):
            stage.patch_source(frame.replace("g_frame++;","g_frame += 2;"))

    def test_cgram_exact_size_and_fnv(self):
        self.assertEqual(trial.cgram_fnv(bytes(512)),"4d7705c5")
        for value in (bytes(0),bytes(511),bytes(513)):
            with self.assertRaises(ValueError):
                trial.cgram_fnv(value)

    def test_fails_closed_on_original_raster_corruption(self):
        src=(ROOT/"tools/qa08_original_results_port_chronology.py").read_text()
        self.assertIn("original_unchanged_BGRX_sha256",src)
        self.assertIn("native_guest_phase_certified",src)
        self.assertNotIn("forcepoke(",src)

if __name__=="__main__":
    unittest.main()
