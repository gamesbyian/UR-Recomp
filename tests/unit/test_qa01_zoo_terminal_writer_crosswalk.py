"""Synthetic Zoo terminal opcode/helper scopes; zero original/native course credit."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_zoo_terminal_writer_crosswalk as c


class ZooTerminalWriterCrosswalk(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.original = root / "source"
        self.native = root / "native"
        self.original.mkdir()
        self.native.mkdir()
        self.source_host = self.logs(1604)
        self.native_host = self.logs(1606)
        for side, directory in (("original", self.original), ("native", self.native)):
            for i, frame in enumerate(c.FRAMES):
                raw = bytearray(131072)
                raw[0x0313] = c.EXPECTED[side][i]
                raw[0x009F] = c.EXPECTED_MENU[side][i]
                raw[0x00CE] = 1
                (directory / f"boundary-{frame:05d}.wram.bin").write_bytes(raw)
        self.source_trace = (
            "ZOOPCWRITE f=6766 v=225 pc=83E073 addr=0313 old=01 new=00\n"
            "ZOOPCWRITE f=6767 v=224 pc=83E3FE addr=0313 old=00 new=3D\n"
            "ZOOPCWRITE f=6766 v=224 pc=839A1E addr=009F old=16 new=BC\n")
        self.native_trace = (
            "f6766 00:0313=0000 w2 candidate_zero via=cpu_write16\n"
            "f6767 00:0313=003D w2 candidate_result via=cpu_write16\n"
            "f6767 00:009F=00BC w2 candidate_menu via=cpu_write16\n")

    def logs(self, entry: int) -> str:
        return "script f=" + str(entry) + " dump scene-entered ok\n" + "".join(
            f"script f={entry+frame} dump boundary-{frame:05d} ok\n"
            for frame in c.FRAMES)

    def run_crosswalk(self, *, original=None, native=None,
                      source_host=None, native_host=None):
        return c.analyze(
            self.source_trace if original is None else original,
            self.native_trace if native is None else native,
            self.source_host if source_host is None else source_host,
            self.native_host if native_host is None else native_host,
            self.original, self.native)

    def test_existing_zoo_producer_watches_0313_and_preserves_original_cpu_pc(self):
        flow = (ROOT / ".github/workflows/baldosa-2014-zoo-scene.yml").read_text()
        self.assertIn('SNESRECOMP_WLOG_ADDR="008B:0313:', flow)
        self.assertIn("instrument_snesref_zoo_menu_writes.py", flow)
        self.assertIn("qa01_zoo_terminal_writer_crosswalk.py", flow)
        self.assertIn("original-pc.log", flow)
        self.assertIn("native-menu-writes.log", flow)
        self.assertIn("zoo-terminal-writer-crosswalk.json", flow)
        source = (ROOT / "tools/instrument_snesref_zoo_menu_writes.py").read_text()
        self.assertIn("CONTROLS = (0x009F, 0x00CE, 0x0313)", source)

    def test_real_original_snesref_dump_receipt_not_native_ok(self):
        # Original snesref from executed CI 38499115188 writes an informational
        # full-dump descriptor, not the native framework's 'ok' marker.
        original = self.source_host.replace(
            "scene-entered ok",
            "scene-entered fb=256x224 RGB565 sram=8192 ppuw=4")
        for frame, count in ((5160, 677), (5161, 645), (5162, 3190), (5163, 33)):
            original = original.replace(
                f"boundary-{frame:05d} ok",
                f"boundary-{frame:05d} fb=256x224 RGB565 sram=8192 ppuw={count}")
        report = self.run_crosswalk(source_host=original)
        self.assertEqual(report["original_verified_dump_host_ticks"][5162], 6766)
        self.assertEqual(report["release_complete_event_credit"], 0)
        invalid = original.replace("RGB565", "RGB???")
        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
            self.run_crosswalk(source_host=invalid)

    def test_real_frame_labels_keep_original_native_clocks_separate(self):
        result = self.run_crosswalk()
        self.assertEqual(result["original_host_scene_entry"], 1604)
        self.assertEqual(result["native_host_scene_entry"], 1606)
        self.assertEqual(result["entry_host_offset_native_minus_original"], 2)
        self.assertEqual(result["original_verified_dump_host_ticks"][5162], 6766)
        self.assertEqual(result["native_verified_dump_host_ticks"][5162], 6768)
        self.assertEqual(len(result["raw_state_transitions_and_trace_candidates"]), 4)
        self.assertEqual(
            [(t["engine"], t["observed_raw_0313"]) for t in
             result["raw_state_transitions_and_trace_candidates"]],
            [("original", [1, 0]), ("original", [0, 61]),
             ("native", [1, 0]), ("native", [0, 61])])
        self.assertTrue(all(t["any_exact_value_candidate"] for t in
                            result["raw_state_transitions_and_trace_candidates"]))
        self.assertEqual(result["original_cpu_0313_opcode_scope_rows"][0]["guest_pc"],
                         "83:E073")
        self.assertTrue(result["cpu_opcode_scope_not_proven_direct_store"])
        self.assertEqual(result["release_complete_event_credit"], 0)
        self.assertFalse(result["strict_guest_relative_result_boundary_equal"])

    def test_missing_native_writer_is_a_negative_not_rewritten_history(self):
        result = self.run_crosswalk(native="f6766 00:009F=16 w1 unrelated\n")
        self.assertEqual(result["native_cpu_helper_0313_write_rows"], [])
        self.assertEqual(result["release_complete_event_credit"], 0)
        self.assertEqual([x["any_exact_value_candidate"] for x in
                          result["raw_state_transitions_and_trace_candidates"]],
                         [True, True, False, False])
        result = self.run_crosswalk(original="ZOOPCWRITE f=6766 v=225 "
                                    "pc=839A1E addr=009F old=16 new=BC\n")
        self.assertEqual(result["original_cpu_0313_opcode_scope_rows"], [])

    def test_duplicate_mistimed_source_labels_fail_before_writer_claim(self):
        for altered in (
            self.source_host.replace("script f=6766 dump boundary-05162",
                                     "script f=6767 dump boundary-05162"),
            self.source_host.replace("script f=6766 dump boundary-05162", ""),
            self.source_host + "script f=6766 dump boundary-05162 ok\n",
            self.source_host.replace("dump scene-entered ok",
                                     "dump something-else ok"),
        ):
            with self.subTest(altered=altered[-90:]), self.assertRaises(ValueError):
                self.run_crosswalk(source_host=altered)
        with self.assertRaises(ValueError):
            self.run_crosswalk(native_host=self.native_host.replace(
                "script f=6768 dump boundary-05162",
                "script f=6767 dump boundary-05162"))

    def test_mutated_genuine_wram_and_wrong_course_fail_closed(self):
        frame = self.original / "boundary-05162.wram.bin"
        original = frame.read_bytes()
        frame.write_bytes(original[:-1])
        with self.assertRaisesRegex(ValueError, "128-KiB"):
            self.run_crosswalk()
        frame.write_bytes(original)
        bad = bytearray(original)
        bad[0x0313] = 1
        frame.write_bytes(bad)
        with self.assertRaisesRegex(ValueError, "phase drifted"):
            self.run_crosswalk()
        frame.write_bytes(original)
        bad = bytearray(original)
        bad[0x00CE] = 0
        frame.write_bytes(bad)
        with self.assertRaisesRegex(ValueError, "no longer on original Zoo"):
            self.run_crosswalk()


if __name__ == "__main__":
    unittest.main()
