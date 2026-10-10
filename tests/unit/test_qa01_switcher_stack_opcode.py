"""Fail-closed source-only original 65816 stack-page probe contracts."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import instrument_snesref_qa01_switcher_stack as instrument
import report_qa01_switcher_stack_trace as report


def fixture_log():
    return (
        "QASTACKBEGIN f=17014 v=230 pc=80D32A sp=01F3\n"
        "QASTACKWRITE f=17015 v=230 pc=80D32A op=48 sp0=01DD "
        "sp1=01DC addr=01DD old=00 new=8F\n"
        "QASTACKWRITE f=17016 v=231 pc=83988A op=8D sp0=01DD "
        "sp1=01DD addr=01E6 old=08 new=09\n"
    )


class SwitcherOpcodeStackTests(unittest.TestCase):
    def test_disposable_patch_is_single_instrumented_opcode_call(self):
        old = "prefix\n" + instrument.MARKER + "\nsuffix"
        changed = instrument.patch(old)
        self.assertIn(instrument.STAMP, changed)
        self.assertEqual(changed.count("(*Opcodes[Op].S9xOpcode)();"), 1)
        self.assertEqual(changed.count("Registers.PCw++;"), 1)
        self.assertEqual(changed.count("QASTACKWRITE"), 1)
        self.assertEqual(changed.count("QASTACKBEGIN"), 1)
        self.assertIn("UR_QA_STACK_FIRST", changed)
        self.assertIn("UR_QA_STACK_LAST", changed)
        for addr in instrument.TARGETS:
            self.assertIn(f"0x{addr:04X}", changed)
        with self.assertRaisesRegex(ValueError, "already installed"):
            instrument.patch(changed)
        with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
            instrument.patch("none")
        with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
            instrument.patch(instrument.MARKER * 2)

    def test_exact_two_original_cpu_opcode_scopes_remain_nonadmission(self):
        d = report.parse_trace(fixture_log(), 17030)
        self.assertEqual(d["schema"], report.SCHEMA)
        self.assertEqual(d["event_count"], 2)
        self.assertEqual(d["observed_cpu_gate"]["pc"], "80:D32A")
        self.assertEqual(d["observed_cpu_gate"]["sp"], "01F3")
        self.assertEqual(d["opcode_scope_events"][0]["sp_after"], "01DC")
        self.assertTrue(d["opcode_scope_events"][0]["push_opcode_candidate"])
        self.assertTrue(d["opcode_scope_events"][0]["stack_pointer_address_compatible"])
        self.assertFalse(d["opcode_scope_events"][1]["push_opcode_candidate"])
        self.assertFalse(d["opcode_scope_events"][1]["stack_pointer_address_compatible"])
        self.assertIn("7E:01F1", d["untouched_targets"])
        self.assertEqual(d["complete_event_release_credit"], 0)
        self.assertTrue(d["cpu_stack_hypothesis_only"])

    def test_push_opcode_alone_does_not_prove_address_was_stack_written(self):
        self.assertTrue(report.stack_push_compatible(0x48, 0x01DD, 0x01DC, 0x01DD))
        self.assertFalse(report.stack_push_compatible(0x48, 0x01DE, 0x01DD, 0x01DD))
        self.assertTrue(report.stack_push_compatible(0xF4, 0x01E7, 0x01E5, 0x01E6))
        self.assertFalse(report.stack_push_compatible(0xF4, 0x01E7, 0x01E5, 0x01E4))
        self.assertFalse(report.stack_push_compatible(0x8D, 0x01DD, 0x01DC, 0x01DD))
        inconsistent = fixture_log().replace("op=48 sp0=01DD sp1=01DC",
                                              "op=48 sp0=01DE sp1=01DD")
        event = report.parse_trace(inconsistent, 17030)["opcode_scope_events"][0]
        self.assertTrue(event["push_opcode_candidate"])
        self.assertFalse(event["stack_pointer_address_compatible"])

    def test_zero_target_changes_is_valid_negative_if_gate_executed(self):
        d = report.parse_trace(fixture_log().split("QASTACKWRITE")[0], 17030)
        self.assertEqual(d["event_count"], 0)
        self.assertEqual(len(d["untouched_targets"]), 8)
        self.assertEqual(d["complete_event_release_credit"], 0)

    def test_forged_missing_out_of_window_and_overlarge_traces_reject(self):
        log = fixture_log()
        for damaged in (
            "",
            log.replace("QASTACKBEGIN", "WRONG"),
            log.replace("f=17014", "f=16900", 1),
            log.replace("addr=01DD", "addr=0199"),
            log.replace("old=00 new=8F", "old=8F new=8F"),
            log.replace("f=17015", "f=17099", 1),
            log.replace("v=230", "v=300", 1),
        ):
            with self.subTest(damaged=damaged[:40]):
                with self.assertRaises(ValueError):
                    report.parse_trace(damaged, 17030)
        with self.assertRaisesRegex(ValueError, "cap"):
            report.parse_trace(fixture_log() + fixture_log().splitlines()[1].join(["\n"]*(report.LIMIT+2)), 17030)

    def test_replay_validates_source_identity_and_exact_original_wram(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "original", root / "patched"
            for folder, core in ((a, "sha-pristine"), (b, "sha-instrumented")):
                samples = folder / "source-switcher" / "source"
                samples.mkdir(parents=True)
                (samples / "source-race-entered.wram.bin").write_bytes(bytes(131072))
                (samples / "source-horizon.wram.bin").write_bytes(bytes(131072))
                witness = {
                    "schema": "UR-QA01-ORIGINAL-SWITCHER-SOURCE-QUALIFICATION/1",
                    "status": "source_event_and_entry_verified",
                    "release_complete_event_credit": 0,
                    "original_source_horizon_frames": 22000,
                    "rom_sha256": "same-rom",
                    "archived_movie_sha256": "same-movie",
                    "source_sram_sha256": "same-sram",
                    "original_core_sha256": core,
                    "source_result": {"original_entry_frame": 12327,
                                      "original_result_frame": 17030},
                    "source_event_diagnostic": {"proven_horizon": 22000},
                }
                (folder / "report.json").write_text(json.dumps(witness))
            outcome = report.verify_replay(a / "report.json", b / "report.json")
            self.assertEqual(outcome["source_result_frame"], 17030)
            self.assertEqual(len(outcome["unchanged_original_wram_sha256"]), 2)
            altered = b / "source-switcher" / "source" / "source-horizon.wram.bin"
            data = bytearray(altered.read_bytes())
            data[0x01DD] = 1
            altered.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "changed source WRAM"):
                report.verify_replay(a / "report.json", b / "report.json")


if __name__ == "__main__":
    unittest.main()
