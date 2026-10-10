"""Bounded QA-01 native writer chronology is independent from original CPU PC."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_zoo_native_write_chronology as native


class NativeMenuChronologyTest(unittest.TestCase):
    def fixtures(self, root):
        original = root / "original"
        baldosa = root / "native"
        original.mkdir()
        baldosa.mkdir()
        for frame in range(5155, 5159):
            for directory, is_native in ((original, False), (baldosa, True)):
                wram = bytearray(0x20000)
                if frame >= (5157 if is_native else 5158):
                    wram[0x9F] = 0x16
                    wram[0xCE] = 1
                else:
                    wram[0x9F] = 0x84
                (directory / f"boundary-{frame:05d}.wram.bin").write_bytes(wram)
        host = "".join(
            f"script f={1606+f} dump boundary-{f:05d} ok\n"
            for f in range(5155, 5159)
        )
        return original, baldosa, host

    def test_records_native_writer_in_own_host_pre_run_frame(self):
        with tempfile.TemporaryDirectory() as d:
            orig, bald, host = self.fixtures(Path(d))
            writes = ("f6762   00:009F=16 w1 interposed_menu_update via=cpu_write8\n"
                      "f6762   00:00CE=01 w1 native_track_update via=cpu_write8\n"
                      "f6762   7E:008B=0001 w2 includedbutnotmenu\n"
                      "f6758   00:009F=84 w1 before_window\n")
            result = native.analyze(writes, host, bald, orig, native_scene_entry_frame=1606)
            self.assertEqual(result["native_scene_entry_host_frame"], 1606)
            self.assertEqual(result["native_boundary_cpu_store_trace_status"],
                             "partial_candidate_writers")
            self.assertEqual(len(result["native_menu_and_track_value_writes_near_boundary"]), 2)
            self.assertEqual(result["native_script_dump_host_frames"]["5157"], 6763)
            self.assertEqual(result["complete_event_qa_credit"], 0)

    def test_two_byte_write_ending_on_menu_position_is_not_ignored(self):
        rows, counts = native.parse_writes(
            "f6762 7E:009E=16AB w2 scope\n"
            "f6762 80:00CD=01BB w2 another_scope\n"
            "f6762 00:009F=0016 w2 scope3",
            entry_frame=1606)
        self.assertEqual([(r["guest_address"], r["guest_value"])
                          for r in rows], [
                              ("7E:009F", "16"),
                              ("7E:00CE", "01"),
                              ("7E:009F", "16"),
                          ])
        self.assertEqual(counts["native_log_target_guest_writes"], 3)

    def test_missing_native_writer_is_negative_not_false_course_pass(self):
        with tempfile.TemporaryDirectory() as d:
            orig, bald, host = self.fixtures(Path(d))
            result = native.analyze("f6762 00:008B=01 w1 another_scope", host, bald, orig,
                                    native_scene_entry_frame=1606)
            self.assertEqual(result["native_boundary_cpu_store_trace_status"],
                             "no_target_cpu_helper_write_observed")
            self.assertEqual(result["complete_event_qa_credit"], 0)

    def test_wrong_scene_entry_or_dump_boundary_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            orig, bald, host = self.fixtures(Path(d))
            with self.assertRaisesRegex(ValueError, "native scene-entry"):
                native.parse_writes("", entry_frame=0)
            with self.assertRaisesRegex(ValueError, "script frames disagree"):
                native.analyze("", host, bald, orig, native_scene_entry_frame=1604)
            with self.assertRaisesRegex(ValueError, "missing native exact boundary"):
                native.analyze("", host.replace("boundary-05157", "boundary-04999"),
                               bald, orig, native_scene_entry_frame=1606)
            p = bald / "boundary-05157.wram.bin"
            p.write_bytes(p.read_bytes()[:-1])
            with self.assertRaisesRegex(ValueError, "128KiB"):
                native.analyze("", host, bald, orig, native_scene_entry_frame=1606)


if __name__ == "__main__":
    unittest.main()
