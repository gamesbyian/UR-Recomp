"""ROM-free proof that cinematic position witnesses read unmodified guest bytes."""
import importlib.util
import struct
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "tools/showcase/audit_dynamic_native_2p.py"
SPEC = importlib.util.spec_from_file_location("dynamic_2p_source_audit", PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

class GenuineTwoPlayerPositionWitnessTest(unittest.TestCase):
    def make_blob(self, x1=1000, x2=500, y1=80, y2=220):
        b = bytearray(0x20000)
        for offset, value in ((0x0411, x1), (0x0413, x2),
                              (0x0415, y1), (0x0417, y2)):
            struct.pack_into("<H", b, offset, value)
        return bytes(b)

    def test_actual_7e_source_coordinate_offsets(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "real-guest.wram.bin"
            path.write_bytes(self.make_blob())
            result = m.read_world_snapshot(path)
            self.assertEqual(result["p1_world_x_u16"], 1000)
            self.assertEqual(result["p2_world_x_u16"], 500)
            self.assertEqual(result["raw_abs_x_difference"], 500)
            self.assertEqual(result["raw_abs_y_difference"], 140)
            self.assertIn("not_course_arc_distance", result["distance_status"])

    def test_scene_snapshots_match_exact_guest_frames_and_bytes(self):
        with tempfile.TemporaryDirectory() as dirname:
            work = Path(dirname)
            name = "looper-p1-leads"
            for suffix in ("control", "recorded"):
                folder = work / f"{name}-{suffix}"
                (folder / "dump").mkdir(parents=True)
                (folder / "log.txt").write_text("".join(
                    f"script f={2100 + i*200} dump cinematic-{tag} ok\n"
                    for i, tag in enumerate(("lead", "middle", "late"))))
                for tag in ("lead", "middle", "late"):
                    (folder / "dump" / f"cinematic-{tag}.wram.bin").write_bytes(
                        self.make_blob())
            checks = m.read_guest_dump_witnesses(work, name)
            self.assertEqual(len(checks), 3)
            self.assertEqual([x["guest_frame"] for x in checks],
                             [2100, 2300, 2500])
            self.assertTrue(all(x["raw_abs_x_difference"] == 500 for x in checks))
            path = work / f"{name}-recorded/dump/cinematic-middle.wram.bin"
            corrupt = bytearray(path.read_bytes())
            corrupt[0x0413] ^= 1
            path.write_bytes(corrupt)
            with self.assertRaises(ValueError):
                m.read_guest_dump_witnesses(work, name)

    def test_missing_and_duplicated_go_witnesses_fail(self):
        with tempfile.TemporaryDirectory() as dirname:
            work = Path(dirname)
            name = "jumps-p2-leads"
            for suffix in ("control", "recorded"):
                folder = work / f"{name}-{suffix}"
                (folder / "dump").mkdir(parents=True)
                (folder / "log.txt").write_text(
                    "script f=2100 dump cinematic-lead ok\n")
                (folder / "dump/cinematic-lead.wram.bin").write_bytes(self.make_blob())
            with self.assertRaises(ValueError):
                m.read_guest_dump_witnesses(work, name)

    def test_truncated_guest_wram_rejected(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "bad.wram.bin"
            path.write_bytes(b"\0" * 4096)
            with self.assertRaises(ValueError):
                m.read_world_snapshot(path)

if __name__ == "__main__":
    unittest.main()
