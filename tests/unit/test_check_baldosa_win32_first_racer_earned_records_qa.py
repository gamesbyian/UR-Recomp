#!/usr/bin/env python3
"""ROM-free fail-closed tests for proposed real Win32 three-guest evidence."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_first_racer_earned_records_qa as qa
from tests.unit.test_check_baldosa_win32_first_racer_evidence import fixture

RUN_PATH = r"C:\CI\User With Spaces\runs\mike\run-0001791946349567-0000.urrun"


def sample():
    created_report, first, _ = fixture()
    report = {
        "scope": "actual-native-windows-first-racer-to-earned-one-player-records",
        "first_game_created_first_named_racer": True,
        "second_game_loaded_named_sram_and_finished_real_source_race": True,
        "one_canonical_run_sha256": "a" * 64,
        "third_game_reopened_exact_earned_run_read_only": True,
        "active_selector_and_catalog_preserved": True,
        "anonymous_sram_preserved": True,
        "physical_gamepad_verified": False,
        "strict_original_native_event_pass": False,
        "release_gate_credit": 0,
    }
    second = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=d4dc382b\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p profile=mike "
        "course=course:01 input_frames=2253 inputs=5 path=" + RUN_PATH + "\n"
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p "
        "race_host=1911 result_host=4164 finish_ticks60=1679 "
        "input_frames=2253 input_runs=5 published=1\n"
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=committed\n"
    )
    third = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=37cc13a8\n"
        "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=1 unavailable=0\n"
        "UR_BALDOSA_MODERN_ROOT records_page=2p\n"
        "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
        "UR_BALDOSA_MODERN_ROOT records_closed=1\n"
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=mike status=committed\n"
    )
    return report, first, second, third


class FirstRacerEarnedSourceRecordsQA(unittest.TestCase):
    def check(self, report, created, played, records):
        return qa.audit_hosted_first_racer_earned_1p(
            json.dumps(report).encode(), created.encode(),
            played.encode(), records.encode(),
        )

    def test_valid_hosted_three_games_are_not_release_acceptance(self):
        d = self.check(*sample())
        self.assertTrue(d["hosted_first_racer_earned_1p_three_game_logs_consistent"])
        self.assertEqual(d["hosted_played_1p_finish_ticks60"], 1679)
        self.assertEqual(d["hosted_played_1p_input_frames"], 2253)
        self.assertEqual(d["hosted_played_guest_boot_fnv_observed"], "d4dc382b")
        self.assertEqual(d["hosted_fresh_records_guest_boot_fnv_observed"], "37cc13a8")
        self.assertFalse(d["hosted_saved_urrun_bytes_independently_decoded"])
        self.assertFalse(d["hosted_packaged_cmd_auto_relaunch_verified"])
        self.assertFalse(d["hosted_physical_controller_verified"])
        self.assertFalse(d["strict_original_native_complete_event_accepted"])
        self.assertEqual(d["release_gate_credit"], 0)

    def test_real_windows_crlf_with_one_valid_1p_tab_revisit(self):
        report, created, played, records = sample()
        d = self.check(
            report, created.replace("\n", "\r\n"),
            played.replace("\n", "\r\n"), records.replace("\n", "\r\n"),
        )
        self.assertEqual(d["hosted_played_1p_finish_ticks60"], 1679)

    def test_json_does_not_mint_invented_release_credit(self):
        report, created, played, records = sample()
        for k, v in (
            ("scope", "another source"),
            ("first_game_created_first_named_racer", False),
            ("second_game_loaded_named_sram_and_finished_real_source_race", 1),
            ("third_game_reopened_exact_earned_run_read_only", False),
            ("active_selector_and_catalog_preserved", False),
            ("anonymous_sram_preserved", False),
            ("physical_gamepad_verified", True),
            ("strict_original_native_event_pass", True),
            ("release_gate_credit", 1),
            ("release_gate_credit", True),
            ("one_canonical_run_sha256", "forged"),
        ):
            with self.subTest(k=k, v=v):
                damaged = copy.deepcopy(report)
                damaged[k] = v
                with self.assertRaises(ValueError):
                    self.check(damaged, created, played, records)

    def test_played_guest_source_capture_not_just_stock_entry(self):
        report, created, played, records = sample()
        for damaged in (
            played.replace("profile=mike", "profile=native-ci-rider"),
            played.replace("published=1", "published=0"),
            played.replace("result_host=4164", "result_host=4165"),
            played.replace("finish_ticks60=1679", "finish_ticks60=0"),
            played.replace("input_runs=5", "input_runs=4"),
            played.replace("inputs=5", "inputs=6"),
            played.replace("input_frames=2253", "input_frames=2252"),
            played.replace("course=course:01", "course=course:02"),
            played.replace("runs\\mike", "runs\\other"),
            played.replace("run-0001791946349567-0000.urrun", "other.urrun"),
            played.replace("CHECKPOINT profile=mike status=committed", "CHECKPOINT missing"),
            played.replace("CAPTURED=1", "CAPTURED=0"),
            played + played,
            played + "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1\n",
            played + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
        ):
            with self.subTest(damaged=damaged[-110:]):
                with self.assertRaises(ValueError):
                    self.check(report, created, damaged, records)

    def test_unrelated_or_false_third_game_records_not_accepted(self):
        report, created, played, records = sample()
        for damaged in (
            records.replace("profile=mike", "profile=other"),
            records.replace("validated=1", "validated=0"),
            records.replace("unavailable=0", "unavailable=1"),
            records.replace("bytes=8192", "bytes=1024"),
            records.replace("CHECKPOINT profile=mike status=committed", "CHECKPOINT missing"),
            records + records,
            records + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
            records + "UR_BALDOSA_NATIVE_RESULT observed=1\n",
            records + "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n",
        ):
            with self.subTest(damaged=damaged[-110:]):
                with self.assertRaises(ValueError):
                    self.check(report, created, played, damaged)

    def test_first_guest_did_not_earn_result_or_hot_swap(self):
        report, created, played, records = sample()
        for bad in (
            created.replace("activation=next_process", "activation=live"),
            created + created,
            created + "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike\n",
            created + "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n",
            created + "UR_BALDOSA_NATIVE_RESULT observed=1\n",
        ):
            with self.subTest(bad=bad[-110:]):
                with self.assertRaises(ValueError):
                    self.check(report, bad, played, records)


if __name__ == "__main__":
    unittest.main()
