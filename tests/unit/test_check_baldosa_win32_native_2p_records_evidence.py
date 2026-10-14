#!/usr/bin/env python3
"""Synthetic ROM-free contract tests; no invented native 2P event acceptance."""
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

import assemble_baldosa_windows_candidate as package
import check_baldosa_win32_native_2p_records_evidence as qa
import verify_baldosa_romless_candidate_qa as wrapperqa
from tests.unit.test_verify_baldosa_romless_candidate_qa import IndependentBaldosaZipQaTests


def observed():
    report = {
        "scope": "actual-source-2p-baldosa-modern-records-integration",
        "p1_profile": "native-ci-rider",
        "p2_profile": "native-ci-second",
        "played_guest_2p_result_published": True,
        "canonical_match_artifact_sha256": {
            "run-123.urrun": "a" * 64,
            "run-123.urrun.urmatch": "b" * 64,
        },
        "new_native_process_reopened_paired_2p_records": True,
        "p2_named_profile_sram_preserved": True,
        "source_result": {
            "source_result_host": 4377,
            "source_input_frames": 2231,
            "p1_hundredths": 2761,
            "p2_hundredths": 2757,
            "winner": 2,
        },
        "original_native_strict_event_pass": False,
        "physical_gamepads_tested": False,
        "release_gate_credit": 0,
    }
    played = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
        "root=saves/profile-native-ci-rider\n"
        "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2\n"
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1\n"
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n"
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1 profile1=native-ci-rider "
        "profile2=native-ci-second course=course:01 frames=2231 path=C:\\CI\\multiplayer-runs\\run-123.urrun\n"
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p race_host=2146 "
        "result_host=4377 riders=0,2 hundredths=2761,2757 winner=2 "
        "input_frames=2231 input_runs=5 published=1\n"
    )
    fresh = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider "
        "root=saves/profile-native-ci-rider\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-rider "
        "bytes=8192 fnv=abcd1234\n"
        "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected "
        "validated=0 unavailable=0\n"
        "UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=1 "
        "unavailable=0 selected=1\n"
        "UR_BALDOSA_MODERN_ROOT records_page=2p\n"
        "UR_BALDOSA_MODERN_ROOT records_last_2p=LAST 01 LOSS 00:27.61 "
        "source=historical_paired_archive\n"
        "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
        "UR_BALDOSA_MODERN_ROOT records_closed=1\n"
    )
    return report, played, fresh


class HostedNativeWindowsTwoPlayerRecordsQA(unittest.TestCase):
    def check(self, report, played, fresh):
        return qa.audit_hosted_native_2p_records(
            json.dumps(report).encode(), played.encode(), fresh.encode(),
        )

    def test_consistent_hosted_pair_never_claims_source_original_or_real_pads(self):
        report, played, fresh = observed()
        result = self.check(report, played, fresh)
        self.assertTrue(result["hosted_native_2p_result_to_fresh_records_logs_consistent"])
        self.assertEqual(result["hosted_native_2p_source_riders"], [0, 2])
        self.assertEqual(result["hosted_native_2p_source_times_hundredths"], [2761, 2757])
        self.assertEqual(result["hosted_native_2p_source_winner"], 2)
        self.assertEqual(result["hosted_native_2p_saved_run_capture_basename"], "run-123.urrun")
        self.assertEqual(result["hosted_native_2p_player1_records_display_verified"],
                         "LAST 01 LOSS 00:27.61 source=historical_paired_archive")
        self.assertFalse(result["hosted_saved_2p_pair_bytes_independently_reopened"])
        self.assertFalse(result["hosted_original_emulator_2p_parity_accepted"])
        self.assertFalse(result["hosted_physical_gamepads_verified"])
        self.assertEqual(result["hosted_native_2p_played_log_sha256"],
                         hashlib.sha256(played.encode()).hexdigest())

    def test_refuse_unsupported_publication_and_false_winner(self):
        report, played, fresh = observed()
        for damaged in (
            played.replace("published=1", "published=0"),
            played.replace("riders=0,2", "riders=0,1"),
            played.replace("hundredths=2761,2757", "hundredths=2757,2761"),
            played.replace("winner=2", "winner=1"),
            played.replace("result_host=4377", "result_host=2000"),
            played.replace("input_frames=2231", "input_frames=9999"),
            played.replace("CAPTURED=1", "NOT_SAVED=1"),
            played.replace("frames=2231 path=", "frames=2230 path="),
            played.replace("run-123.urrun", "different-run.urrun"),
            played.replace("multiplayer-runs", "unrelated-runs"),
            played.replace("course=course:01", "course=course:02"),
            played.replace("join_confirmed seat=2", "join_rejected seat=2"),
            played + played,
            played + "UR_BALDOSA_NATIVE_MATCH SAVE_PENDING=1\n",
            played.replace(
                "UR_BALDOSA_NATIVE_MATCH CAPTURED=1", "BROKEN_WRITER"
            ),
        ):
            with self.subTest(damaged=damaged[-130:]):
                with self.assertRaises(ValueError):
                    self.check(report, damaged, fresh)

    def test_fresh_records_display_tracks_p1_win_and_draw_source_semantics(self):
        report, played, fresh = observed()
        for case, expected_outcome, expected_time, times, winner in (
            ("p1_win", "WIN", "00:27.57", "2757,2761", 1),
            ("draw", "DRAW", "00:27.61", "2761,2761", 0),
            ("p1_dnf", "LOSS", "DNF", "60000,2757", 2),
        ):
            with self.subTest(case=case):
                updated = copy.deepcopy(report)
                t1, t2 = (int(v) for v in times.split(","))
                updated["source_result"].update(
                    p1_hundredths=t1, p2_hundredths=t2, winner=winner,
                )
                source = played.replace(
                    "hundredths=2761,2757 winner=2",
                    f"hundredths={times} winner={winner}",
                )
                display = fresh.replace(
                    "LOSS 00:27.61", f"{expected_outcome} {expected_time}",
                )
                self.check(updated, source, display)
                with self.assertRaises(ValueError):
                    self.check(updated, source, fresh)

    def test_refuse_fake_match_report_or_candidate_release_promotion(self):
        report, played, fresh = observed()
        mutations = (
            ("p1_profile", "another-rider"),
            ("p2_profile", "another-rider"),
            ("played_guest_2p_result_published", False),
            ("new_native_process_reopened_paired_2p_records", False),
            ("p2_named_profile_sram_preserved", False),
            ("release_gate_credit", 1),
            ("release_gate_credit", False),
            ("original_native_strict_event_pass", True),
            ("physical_gamepads_tested", True),
            ("canonical_match_artifact_sha256", {"run-123.urrun": "a" * 64}),
            ("canonical_match_artifact_sha256", {
                "run-123.urrun": "a" * 64,
                "run-123.urrun.urmatch": "bad-hash",
            }),
            ("source_result", {
                **report["source_result"], "source_result_host": True,
            }),
            ("source_result", {
                **report["source_result"], "winner": 1,
            }),
        )
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                changed = copy.deepcopy(report)
                changed[key] = value
                with self.assertRaises(ValueError):
                    self.check(changed, played, fresh)

    def test_refuse_fake_second_game_records_or_duplicated_pair(self):
        report, played, fresh = observed()
        for damaged in (
            fresh.replace("paired=1", "paired=0"),
            fresh.replace("selected=1", "selected=0"),
            fresh.replace("records_page=2p", "records_page=1p"),
            fresh.replace("records_last_2p=", "records_hidden="),
            fresh.replace("LOSS 00:27.61", "WIN 00:27.57"),
            fresh.replace("LOSS 00:27.61", "LOSS 00:27.57"),
            fresh.replace("LOSS 00:27.61", "DRAW 00:27.61"),
            fresh.replace("LAST 01", "LAST 02"),
            fresh.replace("00:27.61", "00:27.60"),
            fresh.replace("source=historical_paired_archive", "source=synthetic"),
            fresh.replace("BOOT_SRAM profile=native-ci-rider", "BOOT_SRAM profile=anonymous"),
            fresh + fresh,
            fresh + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
        ):
            with self.subTest(damaged=damaged[-130:]):
                with self.assertRaises(ValueError):
                    self.check(report, played, damaged)

    def test_independent_candidate_consumer_admits_all_or_none_win32_2p_group(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            inner, source, sha = IndependentBaldosaZipQaTests().make(root)
            with zipfile.ZipFile(inner) as archive:
                manifest = json.loads(
                    archive.read(package.PREFIX + package.MANIFEST)
                )
            executable = next(
                entry["sha256"] for entry in manifest["immutable_files"]
                if entry["path"] == package.EXE
            )
            base_report = {
                "classification": "windows_native_pause_and_named_profile_smoke_only",
                "exe_sha256": executable,
                "course_complete_credit": 0,
                "physical_gamepad_hardware_tested": False,
                "native_named_readonly_records": {
                    "actual_native_2p_match_published": False
                },
            }
            for players, field in (
                (1, "modern_root_race_entry_p1"),
                (2, "modern_root_race_entry_p2"),
            ):
                base_report[field] = {
                    "players": players,
                    "native_root_handoff_observed": True,
                    "original_race_nmi_barrier_passed": True,
                    "original_go_ticker_barrier_passed": True,
                    "complete_event_outcome_claimed": False,
                    "actual_guest_frames": 100,
                }
            launcher = {
                "archive_sha256": sha,
                "real_extracted_launcher_accepted": True,
                "published_zip_unchanged": True,
                "rom_not_in_archive": True,
                "canonical_8192_byte_save_outside_package": True,
            }
            raw, played, fresh = observed()
            runtime = root / "win32-runtime.zip"

            def package_logs(*, newer=True, partial=False, mutated=None):
                with zipfile.ZipFile(runtime, "w") as archive:
                    archive.writestr(wrapperqa.RUNTIME_REPORT, json.dumps(base_report))
                    archive.writestr(wrapperqa.RUNTIME_LAUNCHER, json.dumps(launcher))
                    for seats, path in ((1, wrapperqa.RUNTIME_ONE),
                                        (2, wrapperqa.RUNTIME_TWO)):
                        archive.writestr(path, (
                            "SDL reports 0 joystick(s)\n"
                            "audio=dummy\n"
                            f"UR_BALDOSA_MODERN_ROOT stock_entered players={seats} menu=3c\n"
                            "script f=100 quit\n"
                        ))
                    if newer:
                        archive.writestr(wrapperqa.RUNTIME_NEW_TWO, json.dumps(mutated or raw))
                        archive.writestr(wrapperqa.RUNTIME_NEW_TWO_PLAYED, played)
                        if not partial:
                            archive.writestr(wrapperqa.RUNTIME_NEW_TWO_FRESH, fresh)

            package_logs()
            observed_report = wrapperqa.check_runtime_actions_wrapper(
                runtime, wrapperqa.audit(inner, source, sha),
            )
            self.assertEqual(observed_report["outcome"], "inconclusive")
            self.assertTrue(observed_report["metrics"]["new_native_two_player_match_published"])
            self.assertFalse(observed_report["metrics"]["strict_original_native_complete_event_accepted"])
            self.assertFalse(observed_report["metrics"]["hosted_saved_2p_pair_bytes_independently_reopened"])
            self.assertIn(
                "hosted-source-2p-atomic-pair-and-fresh-game-records-logs-consistent",
                [a["name"] for a in observed_report["assertions"]],
            )
            package_logs(newer=False)
            original = wrapperqa.check_runtime_actions_wrapper(
                runtime, wrapperqa.audit(inner, source, sha),
            )
            self.assertFalse(original["metrics"]["new_native_two_player_match_published"])
            package_logs(partial=True)
            with self.assertRaisesRegex(ValueError, "2P paired result-to-Records evidence group incomplete"):
                wrapperqa.check_runtime_actions_wrapper(
                    runtime, wrapperqa.audit(inner, source, sha),
                )
            falsified = {**raw, "release_gate_credit": 1}
            package_logs(mutated=falsified)
            with self.assertRaisesRegex(ValueError, "hosted-only product evidence"):
                wrapperqa.check_runtime_actions_wrapper(
                    runtime, wrapperqa.audit(inner, source, sha),
                )


if __name__ == "__main__":
    unittest.main()
