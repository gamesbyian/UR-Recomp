"""H22 source namespace and export isolation regression."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from export_baldosa_earned_1p_run import export, SOURCE_SCOPE

def fixture(root, name="journey"):
    journey=root/name
    runs=journey/"Brand New Player With Spaces"/"runs"/"mike"
    runs.mkdir(parents=True)
    payload=b"realistic synthetic source bytes"
    (runs/"earned.urrun").write_bytes(payload)
    report=dict(scope=SOURCE_SCOPE, first_game_created_first_named_racer=True,
        second_game_loaded_named_sram_and_finished_real_source_race=True,
        third_game_reopened_exact_earned_run_read_only=True,
        active_selector_and_catalog_preserved=True, anonymous_sram_preserved=True,
        physical_gamepad_verified=False,strict_original_native_event_pass=False,
        release_gate_credit=0,one_canonical_run_sha256=hashlib.sha256(payload).hexdigest())
    (journey/"report.json").write_text(json.dumps(report))
    return journey,runs

class H22ExportBoundaries(unittest.TestCase):
    def test_output_must_be_outside_journey(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            journey,_=fixture(root)
            for out in (journey,journey/"new-export",journey/"nested"/"new"):
                with self.subTest(out=str(out)),self.assertRaisesRegex(ValueError,"outside source"):
                    export(journey,out)

    def test_case_insensitive_run_namespace_collision(self):
        if sys.platform.startswith("win"):
            self.skipTest("Win32 does not allow case-distinct files")
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            journey,runs=fixture(root)
            (runs/"shadow.URRUN").write_bytes(b"not original")
            with self.assertRaisesRegex(ValueError,"exactly one"):
                export(journey,root/"out")

    def test_device_root_refused_before_export(self):
        if sys.platform.startswith("win"):
            self.skipTest("Win32 device name unavailable on filesystem")
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ("CON","NUL","LPT¹","COM4"):
                with self.subTest(name=name):
                    journey,_=fixture(root,name)
                    with self.assertRaisesRegex(ValueError,"Nonportable source journey"):
                        export(journey,root/("out-"+name))

    def test_normal_source_remains_exportable(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            journey,_=fixture(root)
            manifest=export(journey,root/"out")
            self.assertEqual(manifest["source_run_filename"],"earned.urrun")
            self.assertTrue((root/"out"/"earned.urrun").exists())

if __name__=="__main__":
    unittest.main()
