"""Fail-closed source Zoo real guest return-PC/PPU transition observer tests."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_zoo_return_bracket as r
import baldosa_2014_zoo_scene_route as route
import instrument_snesref_zoo_menu_writes as source


class ZooReturnBracket(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.dirs = {side: root / side for side in ("original", "native")}
        self.logs = {side: root / (side + ".log")
                     for side in ("original", "native")}
        self.source_pc = root / "source-pc.log"
        for side, folder in self.dirs.items():
            folder.mkdir()
            entry = 1604 if side == "original" else 1606
            reset_at = 5028 if side == "original" else 5027
            lines = ["script f=" + str(entry) + " dump scene-entered " +
                     ("fb=256x224 RGB565 sram=8192 ppuw=4"
                      if side == "original" else "ok")]
            for f in (5000, *r.FRAME_WINDOW, 5100):
                w = bytearray(131072)
                w[0x1199] = w[0x119D] = 1
                (folder / f"boundary-{f:05d}.wram.bin").write_bytes(w)
                ppu = 128 if f >= reset_at else 15
                regs = ({"snesref_dbg_version": 1,
                         "fillram": {"2100": f"{ppu:02X}"}}
                        if side == "original" else {"inidisp": ppu})
                (folder / f"boundary-{f:05d}.regs.json").write_text(
                    json.dumps(regs) + "\n", encoding="utf-8")
                lines.append(f"script f={entry+f} dump boundary-{f:05d} " +
                             ("fb=256x224 RGB565 sram=8192 ppuw=5"
                              if side == "original" else "ok"))
            self.logs[side].write_text("\n".join(lines) + "\n",
                                       encoding="utf-8")
        self.source_pc.write_text(
            "ZOOPCRETURN f=6630 v=225 pc=83C8DD\n"
            "ZOOPCRETURN f=6631 v=003 pc=80A09A\n"
            "ZOOPPUWRITE f=6631 v=004 pc=80A08B old=0F new=80\n",
            encoding="utf-8")

    def run_probe(self):
        return r.analyze(self.dirs["original"], self.dirs["native"],
                         self.logs["original"], self.logs["native"],
                         self.source_pc)

    def test_dense_25_frame_return_ppu_crosswalk_not_course_completion(self):
        out = self.run_probe()
        self.assertEqual(len(out["source_original_native_guest_frames"]["original"]), 51)
        self.assertEqual(out["independent_guest_entry_host"],
                         {"original": 1604, "native": 1606})
        self.assertEqual(out["forced_blank_observation"]["original"][
            "first_forced_blank_dense_sample"], 5028)
        self.assertEqual(out["forced_blank_observation"]["native"][
            "first_forced_blank_dense_sample"], 5027)
        self.assertEqual(out["native_minus_original_first_blank_absolute_host"], 1)
        self.assertEqual([x["usa_source_pc_observed_executing"] for x in
                          out["source_original_pc_executed_receipts"]],
                         ["83:C8DD", "80:A09A"])
        self.assertFalse(out["first_source_original_guest_finish_instruction_identified"])
        self.assertTrue(out["this_is_ppu_return_presentation_not_gameplay_finish"])
        self.assertEqual(out["source_original_first_executing_cpu_pc_setting_forced_blank"]["usa_source_pc_observed_executing"], "80:A08B")
        self.assertTrue(out["source_original_first_executing_cpu_pc_setting_forced_blank"]["newly_entered_forced_blank"])
        self.assertEqual(out["complete_event_qa_credit"], 0)

    def test_missing_candidate_pc_is_not_missing_native_source_execution(self):
        self.source_pc.write_text("no source PC candidate executed\n")
        out = self.run_probe()
        self.assertEqual(out["source_original_pc_executed_receipts"], [])
        self.assertEqual(out["complete_event_qa_credit"], 0)

    def test_genuine_receipts_must_come_from_right_engines_at_right_ticks(self):
        original = self.logs["original"].read_text()
        self.logs["original"].write_text(original.replace(
            "script f=6661 dump boundary-05057",
            "script f=6662 dump boundary-05057"))
        with self.assertRaisesRegex(ValueError, "mistimed"):
            self.run_probe()
        self.logs["original"].write_text(original)
        self.logs["native"].write_text(
            self.logs["native"].read_text().replace(
                "boundary-05056 ok", "boundary-05056 partial"))
        with self.assertRaisesRegex(ValueError, "unqualified real host"):
            self.run_probe()

    def test_raw_ppu_and_guest_course_counter_tamper_fail_closed(self):
        p = self.dirs["native"] / "boundary-05056.regs.json"
        orig = p.read_text()
        p.write_text('{"inidisp": "80"}\n')
        with self.assertRaisesRegex(ValueError, "INIDISP"):
            self.run_probe()
        p.write_text(orig)
        w = self.dirs["original"] / "boundary-05056.wram.bin"
        orig_bytes = w.read_bytes()
        w.write_bytes(orig_bytes[:64])
        with self.assertRaisesRegex(ValueError, "128-KiB"):
            self.run_probe()
        w.write_bytes(orig_bytes)
        bad = bytearray(orig_bytes)
        bad[0x1199] = 0
        w.write_bytes(bad)
        with self.assertRaisesRegex(ValueError, "finished-course counters"):
            self.run_probe()

    def test_false_ppu_register_writer_never_becomes_source_pc(self):
        self.source_pc.write_text(
            "ZOOPPUWRITE f=6600 v=4 pc=80A08B old=0F new=80\n")
        with self.assertRaisesRegex(ValueError, "outside bounded return"):
            self.run_probe()
        self.source_pc.write_text(
            "ZOOPPUWRITE f=6632 v=4 pc=80A08B old=80 new=80\n")
        with self.assertRaisesRegex(ValueError, "not a change"):
            self.run_probe()

    def test_false_historical_rom_pc_is_not_accepted_as_executed_original(self):
        self.source_pc.write_text("ZOOPCRETURN f=6660 v=3 pc=123456\n")
        with self.assertRaisesRegex(ValueError, "source PC out"):
            self.run_probe()
        self.source_pc.write_text("ZOOPCRETURN f=6600 v=3 pc=80A09A\n")
        with self.assertRaisesRegex(ValueError, "outside qualified"):
            self.run_probe()

    def test_original_source_return_trace_uses_independent_pc_gate(self):
        self.assertEqual(len(route.RETURN_BRACKET_FRAMES), 49)
        self.assertEqual(route.RETURN_BRACKET_FRAMES[0], 5001)
        self.assertEqual(route.RETURN_BRACKET_FRAMES[-1], 5049)
        self.assertEqual(len(route.BOUNDARY_FRAMES), len(set(route.BOUNDARY_FRAMES)))
        self.assertEqual(tuple(route.BOUNDARY_FRAMES), tuple(sorted(route.BOUNDARY_FRAMES)))
        c = source.patch(source.MARKER)
        self.assertIn("UR_QA_ZOO_RETURN_FIRST", c)
        self.assertIn("UR_QA_ZOO_RETURN_LAST", c)
        self.assertIn("ZOOPCRETURN f=%u v=%u pc=%06X", c)
        self.assertIn("ZOOPPUWRITE f=%u v=%u pc=%06X", c)
        self.assertIn("UR_QA_ZOO_TRACE_FIRST", c)
        self.assertEqual(c.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        with self.assertRaisesRegex(ValueError, "already installed"):
            source.patch(c)


if __name__ == "__main__":
    unittest.main()
