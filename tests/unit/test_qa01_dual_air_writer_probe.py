"""Read-only 2P seed-50036056 dual-air CPU-writer probe: provenance regressions."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import instrument_snesref_2p_air_writes as core
import qa01_dual_air_writer_probe as m
import qa01_dual_air_paired as paired


class AirWriterProbe(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source-fresh"

    def test_dense_script_has_exact_24_host_ticks_without_extra_simulation(self):
        manifest = m.prepare(self.root)
        self.assertEqual(manifest["source_original_rom_sha256"], paired.ROM_SHA)
        self.assertTrue(manifest["source_input_frames_retained_exact"])
        self.assertFalse(manifest["strict_complete_event_accepted"])
        self.assertEqual(manifest["release_gate_credit"], 0)
        self.assertEqual(len(manifest["checkpoints"]), 24)
        self.assertEqual([(f, t) for f, t in manifest["checkpoints"]
                          if 2576 <= f <= 2584],
                         [(f, m.tag(f)) for f in range(2576, 2585)])
        self.assertEqual(
            manifest["checkpoints"][0], (1620, paired.BASE))
        text = (self.root / "dense.script").read_text()
        self.assertIn("wait 116\ndump qa01-air-2576\n", text)
        self.assertIn("wait 1\ndump endurance-2580\n", text)
        self.assertIn("wait 1\ndump qa01-air-2584\n", text)
        self.assertIn("wait 116\ndump endurance-2700\n", text)
        self.assertEqual(text.count("dump endurance-2580"), 1)
        original = (self.root / "case.script").read_text()
        self.assertIn("wait 119\ndump qa01-neighbor-2579", original)
        self.assertEqual(
            paired.digest((self.root / "case.input").read_text()),
            manifest["source_original_input_sha256"])
        # The observed P1 anomaly is during neutral *held* masks:
        # P2 140 ends at 2578; the next event begins only at 2590.
        controller = (self.root / "case.input").read_text()
        self.assertIn("2548:31:000:140\n", controller)
        self.assertIn("2590:18:000:180\n", controller)
        self.assertFalse(any(
            2579 <= int(line.split(":", 1)[0]) <= 2589
            for line in controller.splitlines()
            if line and not line.startswith("#")))
        with self.assertRaisesRegex(ValueError, "overwrite"):
            m.prepare(self.root)

    def test_new_script_must_preserve_original_2p_observer_schedule(self):
        original = paired.paired_script(paired.guest.base_source()[1])
        with self.assertRaisesRegex(ValueError, "drifted"):
            m.dense_script(original.replace("wait 119\ndump qa01-neighbor-2579",
                                            "wait 118\ndump qa01-neighbor-2579"))
        result = m.dense_script(original)
        self.assertEqual(len(m.DENSE), 9)
        self.assertEqual(len(m.EXTRA), 6)
        self.assertEqual(result.count("dump qa01-air-"), 6)

    def test_side_specific_actual_host_receipts_reject_bad_clock_and_grammar(self):
        tags = [(f, m.tag(f)) for f in m.DENSE]
        org = "".join(f"script f={f} dump {tag} "
                      "fb=256x224 RGB565 sram=8192 ppuw=99\n"
                      for f, tag in tags)
        nat = "".join(f"script f={f} dump {tag} ok\n"
                      for f, tag in tags)
        self.assertEqual(m.valid_logs(org, "original", tags)["count"], 9)
        self.assertEqual(m.valid_logs(nat, "native", tags)["count"], 9)
        with self.assertRaisesRegex(ValueError, "invalid real emulator receipt"):
            m.valid_logs(org.replace("fb=256x224 RGB565 sram=8192 ppuw=99",
                                     "ok"), "original", tags)
        with self.assertRaisesRegex(ValueError, "invalid real emulator receipt"):
            m.valid_logs(nat.replace("endurance-2580 ok",
                                     "endurance-2580 partial"), "native", tags)
        with self.assertRaisesRegex(ValueError, "missing/duplicate/mistimed"):
            m.valid_logs(org.replace("script f=2580 dump", "script f=2581 dump"),
                         "original", tags)
        with self.assertRaisesRegex(ValueError, "missing/duplicate/mistimed"):
            m.valid_logs(nat + "script f=2580 dump endurance-2580 ok\n",
                         "native", tags)

    def test_genuine_full_wram_dimensions_and_all_racer_slots(self):
        self.root.mkdir(parents=True)
        path = self.root / "frame.wram.bin"
        raw = bytearray(131072)
        raw[0x0313] = 1
        for addr, word in ((0x0545, 1), (0x0547, 2),
                           (0x0415, 858), (0x0417, 862),
                           (0x04BB, 19), (0x04BD, 38)):
            raw[addr:addr + 2] = word.to_bytes(2, "little")
        path.write_bytes(raw)
        result = m.sample(2580, path)
        self.assertEqual([result[k] for k in (
            "p1_raw_air", "p2_raw_air", "p1_y", "p2_y",
            "p1_y_velocity", "p2_y_velocity")],
            [1, 2, 858, 862, 19, 38])
        self.assertEqual(result["active_race_byte"], 1)
        path.write_bytes(raw[:-1])
        with self.assertRaisesRegex(ValueError, "128-KiB"):
            m.sample(2580, path)

    def test_original_cpu_patch_is_read_only_and_cpu_dispatch_exactly_once(self):
        src = "begin\n" + core.MARKER + "\nend\n"
        patched = core.patch(src)
        self.assertEqual(patched.count("Registers.PCw++;"), 1)
        self.assertEqual(patched.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertIn("QA01AIRPC f=%u v=%u pc=%06X addr=%04X", patched)
        self.assertIn("Memory.RAM[ur_qa_air_addr[ur_i]]", patched)
        self.assertIn("0x818E26", patched)
        self.assertIn("0x818F7A", patched)
        self.assertIn("0x04BB", patched)
        self.assertIn("0x0415", patched)
        self.assertIn("2574", patched)
        self.assertIn("2586", patched)
        with self.assertRaisesRegex(ValueError, "already installed"):
            core.patch(patched)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            core.patch("not original dispatch")


    def test_original_opcode_scope_retains_scratch_and_high_bytes_fail_closed(self):
        # These are source-CPU receipts, not host-frame snapshots or proof
        # that either original/native air flag means physical airborne motion.
        candidate = (
            "QA01AIRPC f=2579 v=250 pc=818E26 addr=0545 old=00 new=00 candidate=1\n")
        scratch = (
            "QA01AIRPC f=2580 v=001 pc=819E2A addr=0F29 old=02 new=03 candidate=0\n")
        lower = (
            "QA01AIRPC f=2580 v=002 pc=818E26 addr=0545 old=00 new=01 candidate=1\n")
        upper = (
            "QA01AIRPC f=2580 v=003 pc=819E2B addr=0546 old=00 new=02 candidate=0\n")
        rows = m.source_opcode_chronology(candidate + scratch + lower + upper)
        self.assertEqual([x["address"] for x in rows],
                         ["7E:0545", "7E:0F29", "7E:0545", "7E:0546"])
        self.assertEqual([x["changed"] for x in rows],
                         [False, True, True, True])
        self.assertEqual([x["frame"] for x in rows],
                         [2579, 2580, 2580, 2580])
        self.assertEqual(len(m.SOURCE_CAPTURED_BYTES), 18)
        self.assertIn(0x0F29, m.SOURCE_SHARED_WORKING_BYTES)
        for changed, failure in (
            (candidate.replace("f=2579", "f=2587"), "frame gate"),
            (candidate.replace("v=250", "v=777"), "vertical counter"),
            (candidate.replace("addr=0545", "addr=0550"), "address outside"),
            (candidate.replace("candidate=1", "candidate=0"), "candidate PC"),
            (candidate.replace("pc=818E26", "pc=818E27"), "candidate PC"),
            (scratch.replace("new=03", "new=02"), "nonmutating"),
            (scratch.replace("old=02", "old=XX"), "malformed"),
        ):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError, failure):
                    m.source_opcode_chronology(changed)
        with self.assertRaisesRegex(ValueError, "gate/order"):
            m.source_opcode_chronology(scratch + candidate)
        with self.assertRaisesRegex(ValueError, "missing or malformed"):
            m.source_opcode_chronology("original source logger absent\n")


if __name__ == "__main__":
    unittest.main()
