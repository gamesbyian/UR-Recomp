#!/usr/bin/env python3
"""Only negative contract testing: simulated UI receipts never certify hardware."""
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
from tests.unit.test_check_baldosa_win32_created_pair_records_qa import fixture


def six():
    report, first, second, played, mike_records, martin_records = fixture()
    report = copy.deepcopy(report)
    report.update({
        "scope": "two-native-ui-created-players-played-source-2p-and-both-ui-selected-records",
        "p2_existing_profile_select_via_fixture_not_player_UI": False,
        "native_existing_p1_profile_selector_UI_proved": True,
        "anonymous_first_boot_sram_present": False,
        "anonymous_bootstrap_bytes_unchanged_by_all_named_games": True,
    })
    common_root = first.split("\n")[0] + "\n"
    source_ui = (
        common_root +
        "[Gamepad] SDL reports 0 joystick(s). enable_gamepad=[1,1]\n"
        "[host +0.050s] SDL init ok: video=windows audio=dummy\n"
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "script f=0 turbo on\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=85c4e6d1\n"
        "UR_BALDOSA_MODERN_ROOT existing_p1_opened=1 from=mike to=martin activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT synthetic_p1_switch_gamepad=2\n"
        "UR_BALDOSA_NATIVE_P1_SWITCH status=0 from=mike to=martin activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT existing_p1_saved=1 activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT synthetic_p1_switch_gamepad=0\n"
        "UR_BALDOSA_MODERN_ROOT existing_p1_closed=1\n"
        "UR_BALDOSA_MODERN_ROOT synthetic_p1_switch_gamepad=1\n"
        "UR_BALDOSA_MODERN_ROOT synthetic_p1_switch_gamepad=0\n"
        "UR_BALDOSA_MODERN_ROOT existing_p1_stale_race_blocked=1\n"
        "script f=900 quit\n"
        "UR_BALDOSA_NATIVE_PROFILE PREFLIGHT_REJECTED status=3\n"
        "UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed\n"
    )
    return [report, first, second, played, mike_records, source_ui, martin_records]


class IndependentUiSelectedRecords(unittest.TestCase):
    def read(self, sample):
        return qa.audit(json.dumps(sample[0]).encode(), *(s.encode() for s in sample[1:]))

    def test_six_source_logs_are_ui_semantic_only_and_never_release_credit(self):
        report = self.read(six())
        self.assertEqual(report["source_rider_pair"], [0, 2])
        self.assertTrue(report["martin_selection_via_real_native_ui_controller_semantics"])
        self.assertFalse(report["martin_selection_via_backend_fixture_not_shipping_UI"])
        self.assertEqual(report["scored_source_winner"], 2)
        self.assertTrue(report["fresh_mike_and_martin_records_display_source_consistent"])
        self.assertFalse(report["archived_run_and_match_bytes_independently_verified"])
        self.assertFalse(report["real_physical_2p_controllers_or_audio_verified"])
        self.assertEqual(report["release_gate_credit"], 0)
        self.assertEqual(len(report["native_process_log_sha256"]), 6)

    def test_missing_real_ui_process_or_false_backend_selection_cannot_pass(self):
        data = six()
        five = data[:5] + data[6:]
        with self.assertRaises(ValueError):
            self.read(five)
        for key,value in (
            ("scope", "two-native-controller-created-profiles-played-source-2p-and-both-records"),
            ("p2_existing_profile_select_via_fixture_not_player_UI", True),
            ("native_existing_p1_profile_selector_UI_proved", False),
            ("anonymous_bootstrap_bytes_unchanged_by_all_named_games", False),
            ("physical_pad_hardware_accepted", True),
            ("release_gate_credit", 1),
            ("release_gate_credit", True),
        ):
            broken = copy.deepcopy(data)
            broken[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.read(broken)

    def test_ui_handoff_and_stale_guest_barrier_are_required(self):
        data = six()
        ui = data[5]
        for old,new in (
            ("profile=mike root=saves/profile-mike", "profile=martin root=saves/profile-martin"),
            ("profile=mike bytes=8192", "profile=martin bytes=8192"),
            ("existing_p1_opened=1 from=mike to=martin", "existing_p1_opened=1 from=mike to=andrew"),
            ("status=0 from=mike to=martin", "status=1 from=mike to=martin"),
            ("existing_p1_saved=1", "existing_p1_saved=0"),
            ("existing_p1_stale_race_blocked=1", "existing_p1_stale_race_blocked=0"),
            ("synthetic_p1_switch_gamepad=1\n", ""),
            ("PREFLIGHT_REJECTED status=3", "PREFLIGHT_REJECTED status=0"),
        ):
            with self.subTest(old=old):
                bad = list(data)
                self.assertIn(old, ui)
                bad[5] = ui.replace(old,new)
                with self.assertRaises(ValueError):
                    self.read(bad)
        bad = list(data)
        bad[5] = ui + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n"
        with self.assertRaises(ValueError):
            self.read(bad)

    def test_six_process_artifact_group_requires_exact_named_new_selector_log(self):
        data = six()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"native-evidence.zip"
            with zipfile.ZipFile(p, "w") as z:
                for name,item in zip(qa.UI_FILES, [json.dumps(data[0]),*data[1:]]):
                    z.writestr(qa.PREFIX+name,item)
            raw = qa.read_source_evidence_zip(p, require_ui=True)
            self.assertEqual(len(raw),7)
            self.assertTrue(qa.audit(*raw)["martin_selection_via_real_native_ui_controller_semantics"])
            with self.assertRaises(ValueError):
                qa.audit(*qa.read_source_evidence_zip(p))
            with zipfile.ZipFile(p, "w") as z:
                for name,item in zip(qa.UI_FILES[:-1], [json.dumps(data[0]),*data[1:-1]]):
                    z.writestr(qa.PREFIX+name,item)
            with self.assertRaises(ValueError):
                qa.read_source_evidence_zip(p, require_ui=True)


if __name__ == "__main__":
    unittest.main()
