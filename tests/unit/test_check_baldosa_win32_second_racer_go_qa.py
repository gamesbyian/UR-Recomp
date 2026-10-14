#!/usr/bin/env python3
"""ROM-free source contract regression. Synthetic logs never prove native GO."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_baldosa_win32_second_racer_go_qa as qa
import verify_baldosa_romless_candidate_qa as wrapperqa
from tests.unit.test_verify_baldosa_romless_candidate_qa import IndependentBaldosaZipQaTests
from tests.unit.test_check_baldosa_win32_first_racer_evidence import fixture


def example():
    _, first, _ = fixture()
    report = {
        "scope": "native-real-first-p1-created-p2-then-both-seats-stock-go",
        "P1_source_profile": "mike",
        "P2_source_profile": "andrew",
        "original_p1_selector_unchanged": True,
        "P2_canonical_raw_bytes": 8192,
        "P2_source_rider": 1,
        "third_native_process_two_named_seats_confirmed": True,
        "actual_stock_two_player_go": True,
        "completed_two_player_result": False,
        "reopened_paired_records": False,
        "strict_original_native_event_pass": False,
        "physical_gamepad_acceptance": False,
        "release_gate_credit": 0,
    }
    second = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=63568e07\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_MODERN_ROOT second_racer_opened=1 preset=1 activation=next_process\n"
        "UR_BALDOSA_NATIVE_SECOND_RACER status=0 preset=1 id=andrew activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT second_racer_created=1 activation=next_process\n"
    )
    third = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=63568e07\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared\n"
        "UR_BALDOSA_MODERN_ROOT selected=2\n"
        "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2\n"
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1\n"
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2\n"
        "UR_BALDOSA_MODERN_ROOT stock_requested players=2\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n"
    )
    return report, first, second, third


class IndependentSecondRacerGO(unittest.TestCase):
    def check(self, report, first, second, third):
        return qa.audit_win32_second_created_racer_go(
            json.dumps(report).encode(),
            first.encode(), second.encode(), third.encode(),
        )

    def test_three_synthetic_native_games_never_count_as_a_finished_event(self):
        observed = self.check(*example())
        self.assertTrue(observed[
            "hosted_new_mike_and_andrew_to_two_seat_stock_entry_logs_consistent"])
        self.assertEqual(observed["hosted_named_p1_during_p2_creation_boot_fnv_observed"],
                         "63568e07")
        for key in (
            "hosted_p2_catalog_and_sram_bytes_independently_rehashed",
            "hosted_original_guest_stock_two_player_go_barrier_independently_observed",
            "hosted_actual_two_player_settled_result",
            "hosted_earned_2p_match_reopened_in_fresh_records",
            "hosted_physical_two_pad_accepted",
            "strict_original_native_complete_event_accepted",
        ):
            self.assertFalse(observed[key])
        self.assertEqual(observed["release_gate_credit"], 0)
        self.assertEqual(observed["outcome"], "inconclusive_for_release")

    def test_real_win32_crlf_and_different_checkpoint_fnv_are_allowed(self):
        report, first, second, third = example()
        third = third.replace("fnv=63568e07", "fnv=85c4e6d1")
        accepted = self.check(
            report, first.replace("\n", "\r\n"),
            second.replace("\n", "\r\n"), third.replace("\n", "\r\n"),
        )
        self.assertEqual(accepted["hosted_fresh_two_seat_game_p1_boot_fnv_observed"],
                         "85c4e6d1")

    def test_producer_report_must_not_claim_result_or_hardware(self):
        report, first, second, third = example()
        for key, value in (
            ("scope", "source-race-complete"),
            ("P1_source_profile", "andrew"),
            ("P2_source_profile", "mike"),
            ("original_p1_selector_unchanged", False),
            ("P2_canonical_raw_bytes", 8191),
            ("P2_canonical_raw_bytes", True),
            ("P2_source_rider", 0),
            ("P2_source_rider", True),
            ("third_native_process_two_named_seats_confirmed", False),
            ("actual_stock_two_player_go", False),
            ("completed_two_player_result", True),
            ("reopened_paired_records", True),
            ("strict_original_native_event_pass", True),
            ("physical_gamepad_acceptance", True),
            ("release_gate_credit", 1),
            ("release_gate_credit", True),
        ):
            with self.subTest(field=key, value=value):
                bad = copy.deepcopy(report)
                bad[key] = value
                with self.assertRaises(ValueError):
                    self.check(bad, first, second, third)

    def test_a_p2_creation_cannot_hot_swap_race_or_claim_duplicate(self):
        report, first, second, third = example()
        for altered in (
            second.replace("id=andrew", "id=martin"),
            second.replace("preset=1", "preset=2"),
            second.replace("status=0", "status=1"),
            second.replace("bytes=8192", "bytes=8191"),
            second.replace("fnv=63568e07", "fnv=nope"),
            second.replace("activation=next_process", "activation=now"),
            second.replace("profile=mike", "profile=andrew"),
            second + second,
            second + "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew\n",
            second + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
            second + "UR_BALDOSA_NATIVE_RESULT observed=1\n",
            second + "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n",
        ):
            with self.subTest(tail=altered[-80:]):
                with self.assertRaises(ValueError):
                    self.check(report, first, altered, third)

    def test_third_game_requires_both_seat_confirmations_and_only_stock_entry(self):
        report, first, second, third = example()
        for altered in (
            third.replace("join_confirmed seat=2", "join_confirmed seat=1"),
            third.replace("join_opened=1", "join_opened=0"),
            third.replace("join_confirmed seat=2\n", ""),
            third.replace("stock_requested players=2", "stock_requested players=1"),
            third.replace("stock_entered players=2", "stock_entered players=1"),
            third.replace("menu=3d", "menu=3c"),
            third.replace("profile=mike", "profile=andrew"),
            third.replace("bytes=8192", "bytes=8191"),
            third.replace("selected=2", "selected=3"),
            third + third,
            third + "UR_BALDOSA_MODERN_ROOT unbound_2p_consented=1\n",
            third + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
            third + "UR_BALDOSA_NATIVE_RESULT observed=1\n",
        ):
            with self.subTest(tail=altered[-80:]):
                with self.assertRaises(ValueError):
                    self.check(report, first, second, altered)

    def test_source_receipts_must_be_complete_unquoted_individual_lines(self):
        report, first, second, third = example()
        # A grep hit or source-generated report echo is not a native event.
        mutations = (
            (first.replace(
                "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process",
                "DEBUG: UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process"),
             second, third),
            (first, second.replace(
                "UR_BALDOSA_NATIVE_SECOND_RACER status=0 preset=1 id=andrew activation=next_process",
                "UR_BALDOSA_NATIVE_SECOND_RACER status=0 preset=1 id=andrew activation=next_process other=1"),
             third),
            (first, second, third.replace(
                "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
                "echo 'UR_BALDOSA_MODERN_ROOT join_confirmed seat=2'")),
            (first, second, third.replace(
                "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
                "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d extra=untrusted")),
        )
        for logs in mutations:
            with self.subTest(source=repr(logs)[-160:]):
                with self.assertRaises(ValueError):
                    self.check(report, *logs)

    def test_shadow_lines_are_rejected_even_when_real_source_marker_exists(self):
        report, first, second, third = example()
        for index, marker in (
            (0, "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike activation=next_process"),
            (1, "UR_BALDOSA_MODERN_ROOT second_racer_created=1 activation=next_process"),
            (2, "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2"),
        ):
            logs = [first, second, third]
            logs[index] += "not-an-event: " + marker + "\\n"
            with self.subTest(guest=index):
                with self.assertRaises(ValueError):
                    self.check(report, *logs)

    def test_runtime_artifact_four_all_or_none_never_adds_finished_event(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inner, revision, digest = IndependentBaldosaZipQaTests().make(root)
            candidate = wrapperqa.audit(inner, revision, digest)
            stock = {
                "classification": "windows_native_pause_and_named_profile_smoke_only",
                "exe_sha256": candidate["metrics"]["executable_payload_sha256"],
                "course_complete_credit": 0,
                "physical_gamepad_hardware_tested": False,
                "native_named_readonly_records": {
                    "actual_native_2p_match_published": False,
                },
            }
            for players, name in ((1, "modern_root_race_entry_p1"),
                                  (2, "modern_root_race_entry_p2")):
                stock[name] = {
                    "players": players,
                    "native_root_handoff_observed": True,
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
            report, first, second, third = example()
            group = wrapperqa.RUNTIME_SECOND_CREATED_RACER_GROUP
            archive = root / "runtime.zip"

            def emit(present=(), altered_third=None):
                texts = (json.dumps(report), first, second,
                         third if altered_third is None else altered_third)
                with zipfile.ZipFile(archive, "w") as zipfile_out:
                    zipfile_out.writestr(wrapperqa.RUNTIME_REPORT, json.dumps(stock))
                    zipfile_out.writestr(wrapperqa.RUNTIME_LAUNCHER, json.dumps(launcher))
                    for players, name in ((1, wrapperqa.RUNTIME_ONE),
                                          (2, wrapperqa.RUNTIME_TWO)):
                        zipfile_out.writestr(
                            name, "SDL reports 0 joystick(s)\n"
                            "SDL init ok: audio=dummy\n"
                            f"UR_BALDOSA_MODERN_ROOT stock_entered players={players} menu=3c\n"
                            "script f=100 quit\n")
                    for i in present:
                        zipfile_out.writestr(group[i], texts[i])

            emit()
            empty = wrapperqa.check_runtime_actions_wrapper(
                archive, wrapperqa.audit(inner, revision, digest))
            self.assertFalse(empty["metrics"][
                "hosted_new_mike_and_andrew_to_two_seat_stock_entry_logs_consistent"])
            for present in ((1, 2, 3), (0,), (0, 1, 3)):
                emit(present)
                with self.subTest(partial=present):
                    with self.assertRaisesRegex(ValueError, "second-racer source evidence group incomplete"):
                        wrapperqa.check_runtime_actions_wrapper(
                            archive, wrapperqa.audit(inner, revision, digest))
            emit((0, 1, 2, 3))
            accepted = wrapperqa.check_runtime_actions_wrapper(
                archive, wrapperqa.audit(inner, revision, digest))
            self.assertTrue(accepted["metrics"][
                "hosted_new_mike_and_andrew_to_two_seat_stock_entry_logs_consistent"])
            self.assertFalse(accepted["metrics"]["finished_native_event_or_new_match_observed"])
            self.assertFalse(accepted["metrics"]["new_native_two_player_match_published"])
            self.assertEqual(accepted["outcome"], "inconclusive")
            emit((0, 1, 2, 3), third.replace("join_confirmed seat=2", "join_confirmed seat=1"))
            with self.assertRaises(ValueError):
                wrapperqa.check_runtime_actions_wrapper(
                    archive, wrapperqa.audit(inner, revision, digest))


if __name__ == "__main__":
    unittest.main()
