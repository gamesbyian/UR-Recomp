"""Baldosa experiment evidence must never inflate our course acceptance."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("baldosa_spike", ROOT / "tools/baldosa_core_spike_report.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class BaldosaSpikeReportTest(unittest.TestCase):
    def test_unobserved_routes_not_passed(self):
        with tempfile.TemporaryDirectory() as td:
            x = mod.summarize(Path(td))
            self.assertEqual(len(x["routes"]), 3)
            self.assertTrue(all(r["exit_code"] is None for r in x["routes"]))
            self.assertTrue(all(not r["ran_and_exited_cleanly"] for r in x["routes"]))
            self.assertTrue(all(r["complete_event_qa_credit"] == 0 for r in x["routes"]))

    def test_exit_zero_not_terminal_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "race_1p.exit").write_text("0\n")
            sub = root / "race_1p"
            (sub / "dump").mkdir(parents=True)
            (sub / "log.txt").write_text("script complete\n")
            (sub / "dump" / "end.wram.bin").write_bytes(b"WRAM")
            (sub / "dump" / "end.oam.bin").write_bytes(b"OAM")
            (sub / "fd").mkdir()
            (sub / "fd" / "crc.txt").write_text("0x00000001\n0x00000002\n")
            x = mod.summarize(root)["routes"][0]
            self.assertTrue(x["ran_and_exited_cleanly"])
            self.assertEqual(x["wram_checkpoints"], ["end.wram.bin"])
            self.assertEqual(x["oam_checkpoints"], ["end.oam.bin"])
            self.assertEqual(x["recorded_frame_crc_count"], 2)
            self.assertEqual(x["last_frame_crc"], "0x00000002")
            self.assertFalse(x["original_native_terminal_result_admitted"])
            self.assertEqual(x["complete_event_qa_credit"], 0)

    @staticmethod
    def _zoo_frame(path: Path, *, lap: int, checkpoint: int, gate: int,
                   contact: int = 0x2304, track: int = 1,
                   in_race: int = 1, handler: int = 0x8610):
        image = bytearray(0x20000)
        image[0x0313] = in_race
        image[0x00CE] = track
        for offset, value in ((0x0053, handler), (0x0411, 9200),
                              (0x0415, 1489), (0x0E95, contact),
                              (0x1199, checkpoint), (0x119D, gate),
                              (0x0EF1, lap)):
            image[offset:offset + 2] = value.to_bytes(2, "little")
        path.write_bytes(image)

    def test_progression_snapshots_are_observations_not_event_results(self):
        with tempfile.TemporaryDirectory() as td:
            dump = Path(td)
            frames = [
                ("go", 4, 0, 0),
                ("after_first_left", 3, 1, 1),
                ("before_long_left", 3, 2, 1),
                ("after_drive", 3, 2, 1),
            ]
            for name, lap, checkpoint, gate in frames:
                self._zoo_frame(dump / f"{name}.wram.bin",
                                lap=lap, checkpoint=checkpoint, gate=gate)
            result = mod.zoom_zoo_progression(dump)
            self.assertTrue(result["complete_samples"])
            self.assertTrue(result["after_drive_active_zoo"])
            self.assertEqual(result["sampled_active_zoo_count"], 4)
            self.assertEqual(len(result["sampled_progress_changes"]), 2)
            self.assertEqual(
                result["sampled_progress_changes"][0]["changes"]["p1_laps_remaining"],
                [4, 3])
            self.assertFalse(result["after_drive_terminal_menu_gate_f60c"])
            self.assertFalse(result["independent_original_emulator_comparison"])
            self.assertFalse(result["original_native_terminal_result_admitted"])

    def test_missing_or_wrong_sized_zoo_snapshots_never_admitted(self):
        with tempfile.TemporaryDirectory() as td:
            dump = Path(td)
            evidence = mod.zoom_zoo_progression(dump)
            self.assertFalse(evidence["complete_samples"])
            self.assertEqual(evidence["missing"], list(mod.ZOO_SAMPLES))
            for name in mod.ZOO_SAMPLES:
                (dump / f"{name}.wram.bin").write_bytes(b"not WRAM")
            with self.assertRaisesRegex(ValueError, "128 KiB WRAM"):
                mod.zoom_zoo_progression(dump)

    def test_premature_exit_cannot_qualify_as_active_zoo(self):
        with tempfile.TemporaryDirectory() as td:
            dump = Path(td)
            for name in mod.ZOO_SAMPLES:
                self._zoo_frame(dump / f"{name}.wram.bin",
                                lap=4, checkpoint=0, gate=0,
                                track=0, in_race=0, handler=0xF60C)
            result = mod.zoom_zoo_progression(dump)
            self.assertTrue(result["complete_samples"])
            self.assertEqual(result["sampled_active_zoo_count"], 0)
            self.assertTrue(result["after_drive_terminal_menu_gate_f60c"])
            self.assertFalse(result["original_native_terminal_result_admitted"])



if __name__ == "__main__":
    unittest.main()
