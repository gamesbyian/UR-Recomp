"""2014 Zoo paired scene observations are deliberately below release admission."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "zoo_report", ROOT / "tools/baldosa_2014_zoo_scene_report.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class Baldosa2014ZooSceneReportTest(unittest.TestCase):
    @staticmethod
    def frame(path: Path, *, track: int = 1, flag: int = 1,
              menu: int = 0, x: int = 9200):
        w = bytearray(0x20000)
        w[0x00CE], w[0x0313], w[0x009F] = track, flag, menu
        w[0x0411:0x0413] = x.to_bytes(2, "little")
        path.write_bytes(w)

    def test_stable_menu_is_only_candidate_never_course_credit(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for label in ("original", "native"):
                d = base / label
                d.mkdir()
                self.frame(d / "scene-entered.wram.bin")
                self.frame(d / "result-onset-candidate.wram.bin", menu=0xBC, flag=0x3D)
                self.frame(d / "result-stable-candidate.wram.bin", menu=0xBC, flag=0x3D)
            r = mod.analyze(base / "original", base / "native", {"schema_version": 1})
            self.assertTrue(r["paired_result_state_candidate"])
            self.assertEqual(r["complete_event_qa_credit"], 0)
            self.assertEqual(r["observed_named_fields_compared"], 33)
            self.assertIsNone(r["first_semantic_difference"])

    def test_hallucinated_terminal_or_partial_source_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for label in ("original", "native"):
                d = base / label
                d.mkdir()
                for name in mod.SAMPLES:
                    self.frame(d / f"{name}.wram.bin")
            self.frame(base / "native/result-stable-candidate.wram.bin", x=1000)
            r = mod.analyze(base / "original", base / "native", {})
            self.assertFalse(r["paired_result_state_candidate"])
            self.assertFalse(r["original_reached_stable_circuit_result_state"])
            self.assertFalse(r["baldosa_reached_stable_circuit_result_state"])
            self.assertEqual(r["first_semantic_difference"]["field"], "p1_world_xy")

    def test_missing_corrupt_and_wrong_course_fail(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "original").mkdir()
            (base / "native").mkdir()
            for label in ("original", "native"):
                for name in mod.SAMPLES:
                    self.frame(base / label / f"{name}.wram.bin",
                               track=0 if label == "native" else 1)
            r = mod.analyze(base / "original", base / "native", {})
            self.assertFalse(r["original_and_baldosa_entered_zoo"])
            (base / "native/result-stable-candidate.wram.bin").write_bytes(b"bad")
            with self.assertRaisesRegex(ValueError, "128 KiB"):
                mod.analyze(base / "original", base / "native", {})


if __name__ == "__main__":
    unittest.main()
