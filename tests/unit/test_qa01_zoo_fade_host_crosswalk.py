"""Source-tick pinned Zoo result fade, distinct from strict completed-event credit."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_zoo_fade_host_crosswalk as m


class ExecutedZooFade(unittest.TestCase):
    def source(self):
        result = {}
        for side, entry in (("original", m.ORIGINAL_ENTRY),
                            ("native", m.NATIVE_ENTRY)):
            first = 5166 if side == "original" else 5164
            result[side] = {}
            for f in set(m.BLANK_SAMPLE) | set(m.FADE_SAMPLE):
                if f <= 5033:
                    b = 0x0F
                elif f <= 5035:
                    b = 0x80
                elif f < first:
                    b = 0x80
                else:
                    b = min(0x0E, 2 * (f - first + 1))
                result[side][f] = {
                    "guest_relative_frame": f,
                    "actual_host_frame": entry + f,
                    "ppu_inidisp": b,
                }
        return result

    def test_sourced_7_fade_brightness_values_align_absolute_hosts_only(self):
        r = self.source()
        a = m.summarize(r["original"], r["native"])
        self.assertEqual(a["first_result_fade_scene_relative"],
                         {"original": 5166, "native": 5164})
        self.assertEqual(a["first_result_fade_absolute_host"],
                         {"original": 6770, "native": 6770})
        self.assertEqual(
            [x["original_actual_host"] for x in
             a["seven_executed_source_native_brightness_steps"]],
            [6770, 6771, 6772, 6773, 6774, 6775, 6776])
        self.assertTrue(a["each_result_fade_brightness_absolute_host_exact_match"])
        self.assertEqual(
            a["source_native_forced_blank_first_absolute_host"],
            {"original": 6638, "native": 6640})
        self.assertFalse(a["native_same_pc_or_CPU_beam_phase_not_proven"] is False)
        self.assertEqual(a["complete_original_native_usa_events_accepted"], 0)
        self.assertEqual(a["total_usa_events"], 45)

    def test_source_original_replay_fade_interval_cannot_be_waived(self):
        for side, f, replacement in (
            ("original", 5166, 0x80),
            ("native", 5164, 0x80),
            ("native", 5169, 8),
            ("original", 5172, 0x80),
        ):
            with self.subTest(side=side, frame=f):
                r = self.source()
                r[side][f]["ppu_inidisp"] = replacement
                with self.assertRaisesRegex(ValueError, "fade"):
                    m.summarize(r["original"], r["native"])

    def test_original_return_blank_phase_and_exact_anchors_required(self):
        for side in ("original", "native"):
            r = self.source()
            r[side][5034]["ppu_inidisp"] = 0x0F
            with self.assertRaisesRegex(ValueError, "forced-blank onset"):
                m.summarize(r["original"], r["native"])
            r = self.source()
            r[side][5033]["ppu_inidisp"] = 0x80
            with self.assertRaisesRegex(ValueError, "pre-blank"):
                m.summarize(r["original"], r["native"])
            r = self.source()
            r[side][5034]["actual_host_frame"] += 1
            with self.assertRaisesRegex(ValueError, "forced-blank.*offset"):
                m.summarize(r["original"], r["native"])

    def test_missing_samples_and_skewed_fade_host_rejected(self):
        r = self.source()
        r["original"].pop(5168)
        with self.assertRaisesRegex(ValueError, "missing"):
            m.summarize(r["original"], r["native"])
        r = self.source()
        r["native"][5166]["actual_host_frame"] += 1
        with self.assertRaisesRegex(ValueError, "absolute host drifted"):
            m.summarize(r["original"], r["native"])

    def test_real_emulator_receipts_must_attest_separate_scene_entries(self):
        samples = [(f, f"boundary-{f:05d}")
                   for f in sorted(set(m.BLANK_SAMPLE) | set(m.FADE_SAMPLE))]
        for side, entry in (("original", m.ORIGINAL_ENTRY),
                            ("native", m.NATIVE_ENTRY)):
            suffix = ("fb=256x224 RGB565 sram=8192 ppuw=4"
                      if side == "original" else "ok")
            source = (f"script f={entry} dump scene-entered {suffix}\n"
                      + "".join(f"script f={entry+f} dump {tag} {suffix}\n"
                                for f, tag in samples))
            checked, actual = m.receipts(source, side)
            self.assertEqual(checked, entry)
            self.assertEqual(len(actual), len(samples))
            self.assertEqual(actual[5166], entry + 5166)
            with self.assertRaisesRegex(ValueError, "actual dump frame"):
                m.receipts(source.replace(
                    f"script f={entry+5166} dump boundary-05166",
                    f"script f={entry+5167} dump boundary-05166"), side)
            with self.assertRaisesRegex(ValueError, "missing or duplicate"):
                m.receipts(source.replace(
                    f"script f={entry+5166} dump boundary-05166 {suffix}\n",
                    ""), side)
            with self.assertRaisesRegex(ValueError, "malformed"):
                m.receipts(source.replace(
                    f"boundary-05166 {suffix}", "boundary-05166 invalid"), side)

    def test_arbitrary_zip_never_impersonates_source_execution(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "fake.zip"
            p.write_bytes(b"fake independent original/native witness")
            with self.assertRaisesRegex(ValueError, "exactly the pinned"):
                m.analyze(p)


    def test_executed_source_return_pc_is_inside_menu_init_not_finish_logic(self):
        # The original runtime executed 80:A09A; the archived source owns
        # its instructions. Historical code semantics != a new CPU trace.
        ledger = json.loads((ROOT / "analysis/data/"
                             "zoo-original-native-return-ppu-fade-host-20261014.json")
                            .read_text(encoding="utf-8"))
        self.assertEqual(ledger["observed_real_workflow"], 38511451553)
        pc = ledger["actual_original_source_return_pc"]
        self.assertTrue(pc["executed_real_original"])
        self.assertEqual(pc["cpu_pc"], "80:A09A")
        self.assertEqual(pc["icpu_frame"], 6636)
        self.assertEqual(pc["v_counter"], 248)
        self.assertFalse(pc["direct_gameplay_finish_instruction_proven"])
        self.assertEqual(ledger["first_persistent_ppu_blank"]
                         ["original_absolute_host"], 6638)
        self.assertFalse(ledger["interpretation"]
                         ["source_gameplay_finish_instruction_identified"])
        self.assertEqual(ledger["interpretation"]["approved_usa_events"], 0)
        symbols = (ROOT / "reference/imported/reverse-engineering/"
                   "baldosa-uniracers-recomp/decomp/symbols.txt").read_text(
                       encoding="utf-8")
        self.assertIn("80A08B Menu_InitVideo", symbols)
        self.assertIn("80A087 Menu_InitVideoLong", symbols)
        bank = (ROOT / "reference/imported/reverse-engineering/nitrodon/"
                "bank 80.txt").read_text(encoding="utf-8")
        prelude = (
            "80/A08B: A9 80        LDA #$80",
            "80/A08D: 8D 00 21     STA $2100",
            "80/A090: AF 42 07 77  LDA $770742",
            "80/A094: 29 FD        AND #$FD",
            "80/A096: 8F 42 07 77  STA $770742",
            "80/A09A: A9 03        LDA #$03",
            "80/A09C: 8D 85 01     STA $0185",
        )
        at = [bank.index(op) for op in prelude]
        self.assertEqual(at, sorted(at))
        self.assertIn("80/A0C5: 8D 00 42     STA $4200", bank)
        self.assertIn("80A15B Sys_InitVars", symbols)



if __name__ == "__main__":
    unittest.main()
