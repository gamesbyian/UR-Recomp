#!/usr/bin/env python3
"""Synthetic-only negative tests for independent native Win32 Records admission."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_native_1p_records_evidence as qa
import verify_baldosa_romless_candidate_qa as wrapperqa
import assemble_baldosa_windows_candidate as package
from tests.unit.test_verify_baldosa_romless_candidate_qa import IndependentBaldosaZipQaTests


def sample():
    report = {
        "scope": "native-windows-modern-real-guest-1p-product-integration",
        "first_process_source_result_published": True,
        "newly_persisted_urrun_count": 1,
        "new_run_sha256": "a" * 64,
        "second_native_game_process_reopened_exact_new_record": True,
        "second_process_reloaded_previous_native_sram": True,
        "original_native_strict_event_pass": False,
        "physical_controller_hardware_tested": False,
        "release_gate_credit": 0,
    }
    played = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
        "root=saves/profile-native-ci-rider\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-rider "
        "bytes=8192 fnv=1234abcd\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p profile=native-ci-rider "
        "course=course:01 input_frames=1200 inputs=3 "
        "path=C:\\CI\\runs\\native-ci-rider\\run-0000000000000001-0000.urrun\n"
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p "
        "race_host=900 result_host=2100 finish_ticks60=1700 "
        "input_frames=1200 input_runs=3 published=1\n"
    )
    fresh = (
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-rider bytes=8192 fnv=1234abcd\n"
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
        "root=saves/profile-native-ci-rider\n"
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=1 unavailable=0\n"
    )
    return report, played, fresh


class HostedNativeWindowsRecordsQA(unittest.TestCase):
    def check(self, report, played, fresh):
        return qa.audit_hosted_native_1p_records(
            json.dumps(report).encode(), played.encode(), fresh.encode(),
        )

    def test_consistent_saved_run_claim_stays_hosted_not_release_certified(self):
        report, played, fresh = sample()
        record = self.check(report, played, fresh)
        self.assertTrue(record["hosted_native_1p_result_to_fresh_records_logs_consistent"])
        self.assertFalse(record["hosted_saved_urrun_bytes_independently_reopened"])
        self.assertFalse(record["hosted_original_emulator_parity_accepted"])
        self.assertFalse(record["hosted_physical_hardware_accepted"])
        self.assertEqual(record["hosted_1p_result_ticks60"], 1700)
        self.assertEqual(record["hosted_1p_captured_named_run_basename"],
                         "run-0000000000000001-0000.urrun")
        self.assertEqual(record["hosted_new_1p_run_sha256_producer_reported"], "a" * 64)
        self.assertEqual(record["hosted_native_1p_played_log_sha256"],
                         hashlib.sha256(played.encode()).hexdigest())

    def test_existing_candidate_qa_consumes_only_complete_new_win32_evidence_group(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inner, revision, digest = IndependentBaldosaZipQaTests().make(root)
            bound = wrapperqa.audit(inner, revision, digest)
            with zipfile.ZipFile(inner) as zip_in:
                manifest = json.loads(zip_in.read(package.PREFIX + package.MANIFEST))
            exe_sha = next(x["sha256"] for x in manifest["immutable_files"]
                           if x["path"] == package.EXE)
            smoke = {
                "classification": "windows_native_pause_and_named_profile_smoke_only",
                "exe_sha256": exe_sha, "course_complete_credit": 0,
                "physical_gamepad_hardware_tested": False,
                "native_named_readonly_records": {
                    "actual_native_2p_match_published": False,
                },
            }
            for seat, field in ((1, "modern_root_race_entry_p1"),
                                (2, "modern_root_race_entry_p2")):
                smoke[field] = {
                    "players": seat, "native_root_handoff_observed": True,
                    "original_race_nmi_barrier_passed": True,
                    "original_go_ticker_barrier_passed": True,
                    "complete_event_outcome_claimed": False,
                    "actual_guest_frames": 100,
                }
            launcher = {
                "archive_sha256": digest,
                "real_extracted_launcher_accepted": True,
                "published_zip_unchanged": True,
                "rom_not_in_archive": True,
                "canonical_8192_byte_save_outside_package": True,
            }
            archived = root / "hosted-win32.zip"
            report, played, fresh = sample()
            old_log = lambda seat: (
                f"SDL reports 0 joystick(s)\n"
                f"audio=dummy\n"
                f"UR_BALDOSA_MODERN_ROOT stock_entered players={seat} menu=3c\n"
                "script f=100 quit\n"
            )
            def emit(*, include_new=True, include_fresh=True, result=report):
                with zipfile.ZipFile(archived, "w") as outfile:
                    outfile.writestr(wrapperqa.RUNTIME_REPORT, json.dumps(smoke))
                    outfile.writestr(wrapperqa.RUNTIME_LAUNCHER, json.dumps(launcher))
                    outfile.writestr(wrapperqa.RUNTIME_ONE, old_log(1))
                    outfile.writestr(wrapperqa.RUNTIME_TWO, old_log(2))
                    if include_new:
                        outfile.writestr(wrapperqa.RUNTIME_NEW_ONE, json.dumps(result))
                        outfile.writestr(wrapperqa.RUNTIME_NEW_PLAYED, played)
                        if include_fresh:
                            outfile.writestr(wrapperqa.RUNTIME_NEW_FRESH, fresh)
            emit()
            admitted = wrapperqa.check_runtime_actions_wrapper(
                archived, wrapperqa.audit(inner, revision, digest),
            )
            self.assertEqual(admitted["outcome"], "inconclusive")
            self.assertTrue(admitted["metrics"][
                "hosted_native_1p_result_to_fresh_records_logs_consistent"])
            self.assertFalse(admitted["metrics"]["hosted_saved_urrun_bytes_independently_reopened"])
            self.assertTrue(admitted["metrics"]["finished_native_event_or_new_match_observed"])
            self.assertFalse(admitted["metrics"]["strict_original_native_complete_event_accepted"])
            self.assertFalse(admitted["metrics"]["new_native_two_player_match_published"])
            self.assertIn(
                "hosted-native-1p-result-and-fresh-game-records-logs-consistent",
                [x["name"] for x in admitted["assertions"]],
            )

            emit(include_new=False)
            legacy = wrapperqa.check_runtime_actions_wrapper(
                archived, wrapperqa.audit(inner, revision, digest),
            )
            self.assertFalse(legacy["metrics"][
                "hosted_native_1p_result_to_fresh_records_logs_consistent"])
            self.assertFalse(legacy["metrics"]["finished_native_event_or_new_match_observed"])
            emit(include_fresh=False)
            with self.assertRaisesRegex(ValueError, "evidence group incomplete"):
                wrapperqa.check_runtime_actions_wrapper(
                    archived, wrapperqa.audit(inner, revision, digest),
                )
            forged = {**report, "release_gate_credit": 1}
            emit(result=forged)
            with self.assertRaisesRegex(ValueError, "contradictory admission claims"):
                wrapperqa.check_runtime_actions_wrapper(
                    archived, wrapperqa.audit(inner, revision, digest),
                )

    def test_metadata_cannot_forge_real_source_or_release_credit(self):
        report, played, fresh = sample()
        for field, value in (
            ("first_process_source_result_published", False),
            ("newly_persisted_urrun_count", 0),
            ("newly_persisted_urrun_count", True),
            ("new_run_sha256", "not-sha"),
            ("second_native_game_process_reopened_exact_new_record", False),
            ("second_process_reloaded_previous_native_sram", False),
            ("original_native_strict_event_pass", True),
            ("physical_controller_hardware_tested", True),
            ("release_gate_credit", True),
            ("release_gate_credit", 1),
        ):
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(report)
                changed[field] = value
                with self.assertRaises(ValueError):
                    self.check(changed, played, fresh)

    def test_bad_gameplay_log_cannot_claim_settled_run(self):
        report, played, fresh = sample()
        for damaged in (
            played.replace("published=1", "published=0"),
            played.replace("input_runs=3", "input_runs=2"),
            played.replace("input_frames=1200 inputs=3",
                           "input_frames=1300 inputs=3"),
            played.replace("result_host=2100", "result_host=800"),
            played.replace("result_host=2100", "result_host=2101"),
            played.replace("runs\\\\native-ci-rider", "runs\\\\wrong-profile"),
            played.replace("run-0000000000000001-0000.urrun", "stale.urrun"),
            played.replace("path=C:\\\\CI", "path=relative"),
            played.replace("PROFILE APPLIED", "PROFILE DECLINED"),
            played.replace("PROFILE BOOT_SRAM", "PROFILE WRONG_SRAM"),
            played.replace("finish_ticks60=1700", "finish_ticks60=0"),
            played.replace("course=course:01", "course=course:02"),
            played.replace("CAPTURED=1", "CAPTURED=0"),
            played + played,
            played + "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1\n",
            played.replace("UR_BALDOSA_NATIVE_RUN CAPTURED=1", "BAD") +
                "UR_BALDOSA_NATIVE_RUN NOT_SAVED=1\n",
        ):
            with self.subTest(damaged=damaged[-150:]):
                with self.assertRaises(ValueError):
                    self.check(report, damaged, fresh)

    def test_real_windows_crlf_logs_have_canonical_named_capture(self):
        report, played, fresh = sample()
        win_played = played.replace("\n", "\r\n")
        win_fresh = fresh.replace("\n", "\r\n")
        admitted = self.check(report, win_played, win_fresh)
        self.assertTrue(admitted["hosted_native_1p_result_to_fresh_records_logs_consistent"])
        self.assertEqual(admitted["hosted_1p_captured_named_run_basename"],
                         "run-0000000000000001-0000.urrun")

    def test_fresh_native_game_cannot_be_dummy_record_or_writer(self):
        report, played, fresh = sample()
        for damaged in (
            fresh.replace("validated=1", "validated=0"),
            fresh.replace("unavailable=0", "unavailable=1"),
            fresh.replace("profile=native-ci-rider bytes", "profile=anonymous bytes"),
            fresh.replace("PROFILE APPLIED", "PROFILE DECLINED"),
            fresh + fresh,
            fresh + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
            fresh + "UR_BALDOSA_NATIVE_RESULT observed=1\n",
        ):
            with self.subTest(damaged=damaged[-160:]):
                with self.assertRaises(ValueError):
                    self.check(report, played, damaged)


if __name__ == "__main__":
    unittest.main()
