#!/usr/bin/env python3
"""ROM-free negative campaign for genuine played 0/1 native paired Records."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_created_pair_records_qa as qa
from tests.unit.test_check_baldosa_win32_second_racer_go_qa import example

RUN = "run-0001791957063228-0000.urrun"
ROOT_LINE = (
    "[Launcher] Config/saves anchored to "
    "'D:\\a\\_temp\\New Player-Created Named Racers'.\n"
)
PRELUDE = (
    "[Gamepad] SDL reports 0 joystick(s). enable_gamepad=[1,1]\n"
    "[host +0.030s] SDL init ok: video=windows audio=dummy\n"
)


def fixture():
    _, first, second, third = example()
    first = ROOT_LINE + PRELUDE + first
    second = ROOT_LINE + PRELUDE + second
    # The GO script's first $0053 title condition is BEFORE menu=3d.
    third = ROOT_LINE + PRELUDE + "script f=0 turbo on\n" + third
    third = third.replace(
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1\n",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1\n"
        "UR_BALDOSA_MODERN_ROOT synthetic_join_edge seat=1\n")
    third = third.replace(
        "UR_BALDOSA_MODERN_ROOT stock_requested players=2\n",
        "UR_BALDOSA_MODERN_ROOT stock_requested players=2\n"
        "UR_BALDOSA_MODERN_ROOT synthetic_join_edge seat=2\n")
    third = third.replace(
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n",
        "script f=248 until 00053 ok after 248 frames\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n")
    third += (
        "script f=2002 until 00053 ok after 6 frames\n"
        "script f=2352 until 00E1F ok after 350 frames\n"
        "script f=2352 dump go ok\n"
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1 profile1=mike "
        "profile2=andrew course=course:01 frames=2231 "
        "path=D:\\a\\_temp\\New Player-Created Named Racers\\multiplayer-runs\\"
        + RUN + "\n"
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p "
        "race_host=2146 result_host=4377 riders=0,1 "
        "hundredths=2761,2757 winner=2 input_frames=2231 "
        "input_runs=5 published=1\n"
    )
    # The authoritative native application opens the Records 1P page first,
    # then 2P, then back to 1P with an exact player-relative WIN/LOSS clock.
    def view(profile, result, time):
        return (
            ROOT_LINE + PRELUDE +
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=" + profile +
            " root=saves/profile-" + profile + "\n"
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=" + profile +
            " bytes=8192 fnv=85c4e6d1\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT selected=3\n"
            "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
            "UR_BALDOSA_MODERN_ROOT records_opened=1 "
            "profile=selected validated=0 unavailable=0\n"
            "UR_BALDOSA_MODERN_ROOT matches_readonly=1 "
            "paired=1 unavailable=0 selected=1\n"
            "UR_BALDOSA_MODERN_ROOT records_page=2p\n"
            "UR_BALDOSA_MODERN_ROOT records_last_2p=LAST 01 " + result +
            " " + time + " source=historical_paired_archive\n"
            "UR_BALDOSA_MODERN_ROOT records_page=1p\n"
            "UR_BALDOSA_MODERN_ROOT records_closed=1\n"
        )
    report = {
        "scope": "two-native-controller-created-profiles-played-source-2p-and-both-records",
        "actual_frontend_created_profiles": ["mike", "andrew"],
        "observed_stock_riders": [0, 1],
        "observed_source_guest_result": {
            "source_result_host": 4377,
            "source_input_frames": 2231,
            "p1_hundredths": 2761, "p2_hundredths": 2757, "winner": 2,
        },
        "canonical_one_pair_sha256": {
            RUN: "a" * 64, RUN + ".urmatch": "b" * 64,
        },
        "fresh_native_records_for_each": True,
        "p2_existing_profile_select_via_fixture_not_player_UI": True,
        "native_existing_p1_profile_selector_UI_proved": False,
        "physical_pad_hardware_accepted": False,
        "original_native_strict_event_accepted": False,
        "release_gate_credit": 0,
    }
    return report, first, second, third, view("mike", "LOSS", "00:27.61"), view(
        "andrew", "WIN", "00:27.57")


class IndependentCreatedPairRecords(unittest.TestCase):
    def check(self, payload):
        report, *logs = payload
        return qa.audit(json.dumps(report).encode(), *(x.encode() for x in logs))

    def test_genuine_source_log_contract_admits_only_hosted_product_consistency(self):
        report = self.check(fixture())
        self.assertEqual(report["source_rider_pair"], [0, 1])
        self.assertEqual(report["scored_source_winner"], 2)
        self.assertEqual(report["scored_source_hundredths"], [2761, 2757])
        self.assertTrue(report["fresh_mike_and_andrew_records_display_source_consistent"])
        self.assertFalse(report["archived_run_and_match_bytes_independently_verified"])
        self.assertFalse(report["per_user_catalog_and_SRAM_bytes_independently_verified"])
        self.assertFalse(report["real_physical_2p_controllers_or_audio_verified"])
        self.assertEqual(report["release_gate_credit"], 0)
        self.assertEqual(report["original_USA_course_release_credit"], 0)

    def test_real_windows_crlf_and_no_source_viewer_result(self):
        group = fixture()
        result = self.check([group[0], *(x.replace("\n", "\r\n") for x in group[1:])])
        self.assertEqual(result["scored_source_winner"], 2)

    def test_report_must_remain_fixture_selected_not_a_shipped_existing_profile_UI(self):
        group = fixture()
        for field, value in (
            ("scope", "native-release-accepted"),
            ("actual_frontend_created_profiles", ["native-ci-rider", "native-ci-second"]),
            ("observed_stock_riders", [0, 2]),
            ("fresh_native_records_for_each", False),
            ("p2_existing_profile_select_via_fixture_not_player_UI", False),
            ("native_existing_p1_profile_selector_UI_proved", True),
            ("physical_pad_hardware_accepted", True),
            ("original_native_strict_event_accepted", True),
            ("release_gate_credit", 1),
            ("release_gate_credit", True),
            ("canonical_one_pair_sha256", {RUN: "a" * 64}),
            ("canonical_one_pair_sha256", {RUN: "bad", RUN + ".urmatch": "b" * 64}),
        ):
            candidate = copy.deepcopy(group)
            candidate[0][field] = value
            with self.subTest(field=field, value=str(value)[:25]):
                with self.assertRaises(ValueError):
                    self.check(candidate)

    def test_source_result_wrong_rider_winner_and_published_receipts_fail(self):
        source = fixture()
        race = source[3]
        changes = (
            ("riders=0,1", "riders=0,2"),
            ("profile2=andrew", "profile2=native-ci-second"),
            ("profile1=mike", "profile1=native-ci-rider"),
            ("frames=2231", "frames=2230"),
            ("input_frames=2231", "input_frames=2230"),
            ("winner=2", "winner=1"),
            ("published=1", "published=0"),
            ("result_host=4377", "result_host=2000"),
            ("course=course:01", "course=course:02"),
            ("run-0001791957063228-0000.urrun", "../run-0001791957063228-0000.urrun"),
            ("script f=2352 until 00E1F ok after 350 frames", "script f=37963 until 00053 timed out after 36000 frames"),
            ("script f=2002 until 00053 ok after 6 frames", ""),
            ("join_confirmed seat=2", "join_confirmed seat=1"),
            ("synthetic_join_edge seat=2", "synthetic_join_edge seat=1"),
        )
        for old, new in changes:
            with self.subTest(old=old, new=new):
                edited = copy.deepcopy(source)
                self.assertIn(old, race)
                edited[3] = race.replace(old, new)
                with self.assertRaises(ValueError):
                    self.check(edited)

    def test_wrong_or_forged_player_relative_records_are_not_accepted(self):
        group = fixture()
        for profile_ix, mutations in (
            (4, (
                ("LOSS 00:27.61", "WIN 00:27.61"),
                ("LOSS 00:27.61", "LOSS 00:27.57"),
                ("profile=mike", "profile=andrew"),
                ("records_page=2p\n", "records_page=1p\n"),
                ("matches_readonly=1", "matches_readonly=0"),
            )),
            (5, (
                ("WIN 00:27.57", "LOSS 00:27.57"),
                ("WIN 00:27.57", "WIN 00:27.61"),
                ("profile=andrew", "profile=mike"),
                ("records_page=2p\n", ""),
                ("paired=1 unavailable=0", "paired=0 unavailable=1"),
            )),
        ):
            for before, after in mutations:
                with self.subTest(view=profile_ix, before=before):
                    bad = copy.deepcopy(group)
                    bad[profile_ix] = bad[profile_ix].replace(before, after)
                    with self.assertRaises(ValueError):
                        self.check(bad)

    def test_source_members_are_bounded_and_entire_new_pair_group_required(self):
        group = fixture()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "runtime.zip"
            with zipfile.ZipFile(path, "w") as archive:
                for name, datum in zip(qa.FILES, [json.dumps(group[0]), *group[1:]]):
                    archive.writestr(qa.PREFIX + name, datum)
            raw = qa.read_source_evidence_zip(path)
            self.assertEqual(len(raw), 6)
            self.assertEqual(qa.audit(*raw)["release_gate_credit"], 0)
            with zipfile.ZipFile(path, "w") as archive:
                for name, datum in zip(qa.FILES[:-1], [json.dumps(group[0]), *group[1:-1]]):
                    archive.writestr(qa.PREFIX + name, datum)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                qa.read_source_evidence_zip(path)


if __name__ == "__main__":
    unittest.main()
