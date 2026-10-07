import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "check_racer_presentation_trace.py"

spec = importlib.util.spec_from_file_location("trace_validator", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


GOOD = """\
UR_RACER_PRESENTATION_TRACE frame=1205 p1_primary=057E p2_primary=0543 p1_companion=0000
UR_RACER_HD_DRAW PASS frame=1205 semantic=057E viewport=top slot=98 x=1
UR_RACER_HD_DRAW PASS frame=1205 semantic=0543 viewport=top slot=99 x=2
UR_RACER_HD_DRAW PASS frame=1205 semantic=057E viewport=bottom slot=97 x=3
UR_RACER_HD_DRAW PASS frame=1205 semantic=0543 viewport=bottom slot=96 x=4
"""


class RacerPresentationTraceValidatorTests(unittest.TestCase):
    def test_complete_draw_maps_to_trace_primaries(self):
        report = module.analyze(GOOD)
        self.assertEqual(report["complete_draw_frames"], [1205])
        self.assertEqual(report["validated_complete_frames"], [1205])
        self.assertEqual(report["errors"], [])

    def test_semantic_mismatch_is_reported_without_frame_policy(self):
        bad = GOOD.replace(
            "semantic=0543 viewport=bottom slot=96",
            "semantic=0542 viewport=bottom slot=96",
        )
        report = module.analyze(bad)
        self.assertEqual(report["complete_draw_frames"], [1205])
        self.assertEqual(report["validated_complete_frames"], [])
        self.assertTrue(
            any("bottom slot 96 semantic 0542" in error
                for error in report["errors"])
        )

    def test_duplicate_slot_is_rejected(self):
        duplicate = GOOD + (
            "UR_RACER_HD_DRAW PASS frame=1205 semantic=057E "
            "viewport=top slot=98\n"
        )
        report = module.analyze(duplicate)
        self.assertTrue(any("duplicate draw" in e for e in report["errors"]))

    def test_cli_writes_machine_readable_shadow_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            log = root / "racer.log"
            out = root / "report.json"
            log.write_text(GOOD, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    str(log),
                    "--json-out",
                    str(out),
                    "--min-complete-frames",
                    "1",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("RACER_PRESENTATION_TRACE PASS", result.stdout)
            self.assertIn('"ok": true', out.read_text(encoding="utf-8"))

    def test_cli_fails_if_no_complete_transition_is_observed(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = pathlib.Path(tmp) / "racer.log"
            log.write_text(
                "UR_RACER_PRESENTATION_TRACE frame=1 "
                "p1_primary=0541 p2_primary=0540\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(TOOL), str(log)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("complete draw frames 0", result.stderr)


if __name__ == "__main__":
    unittest.main()
