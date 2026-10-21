"""Synthetic cross-platform earned-run filename admission, not native QA."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from export_baldosa_earned_1p_run import SOURCE_SCOPE, export


class PortableDeviceNames(unittest.TestCase):
    def run_case(self, name, reject):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journey = root / "journey"
            runs = journey / "Brand New Player With Spaces" / "runs" / "mike"
            runs.mkdir(parents=True)
            payload = b"synthetic exported source"
            (runs / name).write_bytes(payload)
            report = {
                "scope": SOURCE_SCOPE,
                "first_game_created_first_named_racer": True,
                "second_game_loaded_named_sram_and_finished_real_source_race": True,
                "third_game_reopened_exact_earned_run_read_only": True,
                "active_selector_and_catalog_preserved": True,
                "anonymous_sram_preserved": True,
                "physical_gamepad_verified": False,
                "strict_original_native_event_pass": False,
                "release_gate_credit": 0,
                "one_canonical_run_sha256": hashlib.sha256(payload).hexdigest(),
            }
            (journey / "report.json").write_text(json.dumps(report))
            if reject:
                with self.assertRaisesRegex(ValueError, "Nonportable source-earned run filename"):
                    export(journey, root / "out")
                self.assertFalse((root / "out").exists())
            else:
                manifest = export(journey, root / "out")
                self.assertEqual(manifest["source_run_filename"], name)

    @unittest.skipIf(sys.platform.startswith("win"), "Win32 refuses device filenames at creation")
    def test_windows_device_stems_rejected_on_linux(self):
        for name in ("CON.urrun", "com1.urrun", "LPT².urrun", "COM¹.urrun", "NUL.urrun"):
            with self.subTest(name=name):
                self.run_case(name, True)

    def test_regular_filename_still_exports(self):
        self.run_case("normal.urrun", False)


if __name__ == "__main__":
    unittest.main()
