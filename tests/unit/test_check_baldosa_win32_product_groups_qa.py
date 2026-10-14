#!/usr/bin/env python3
"""Adversarial ROM-free exact source group allowlist contracts.

These are synthetic parser tests; they do not substitute for raw real native
Windows artifacts, saved run/match bytes, a physical pad or an original oracle.
"""
from __future__ import annotations
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_product_groups_qa as extra
from verify_baldosa_romless_candidate_qa import RUNTIME_ALLOWED_MEMBERS
from tests.unit.test_check_baldosa_win32_six_ui_created_pair_records_qa import six
from tests.unit.test_check_baldosa_win32_existing_profile_selector_qa import (
    fixture as selector_fixture,
)


def andrew():
    report = {
        "before_reboot_sha256": {
            "save.srm": "a" * 64, "host-profile.txt": "b" * 64,
            "profiles-v1.txt": "c" * 64, "host-state-v1.txt": "d" * 64,
        },
        "existing_stock_sram_root": "saves/profile-andrew",
        "first_native_guest_creation": True,
        "fresh_native_guest_named_profile_applied": True,
        "independent_original_native_event_pass": False,
        "newly_selected_stock_preset_index": 1,
        "physical_pad_acceptance": False,
        "release_gate_credit": 0,
        "scope": "first-anonymous-modern-root-stock-racer-next-process-boot",
        "stock_rider_boot_verified": True,
    }
    common = (
        "[Gamepad] SDL reports 0 joystick(s)\n"
        "SDL init ok: video=windows audio=dummy\n"
    )
    first = common + (
        "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT first_racer_preset=1\n"
        "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=1 id=andrew activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process\n"
    )
    second = common + (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew root=saves/profile-andrew\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=andrew bytes=8192 fnv=999f4aae\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
    )
    return [json.dumps(report), first, second]


def group_members():
    created = six()
    selected = selector_fixture()
    return {
        **dict(zip(extra.SIX_CREATED, [json.dumps(created[0]), *created[1:]])),
        **dict(zip(extra.SELECTOR, [json.dumps(selected[0]), *selected[1:]])),
        **dict(zip(extra.ANDREW, andrew())),
    }


def check(members):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, contents in members.items():
            archive.writestr(name, contents)
    buffer.seek(0)
    with zipfile.ZipFile(buffer) as archive:
        return extra.audit_extra_hosted_groups(archive)


class ActualGroupAdmissionGuards(unittest.TestCase):
    def test_synthetic_complete_six_plus_selector_plus_andrew_are_only_hosted_source(self):
        metrics = check(group_members())
        self.assertTrue(metrics[
            "hosted_real_six_native_process_ui_created_pair_and_both_records_log_consistent"])
        self.assertTrue(metrics[
            "hosted_real_existing_p1_switch_both_directions_log_consistent"])
        self.assertTrue(metrics[
            "hosted_first_anonymous_nondefault_andrew_source_boot_log_consistent"])
        self.assertFalse(metrics[
            "hosted_user_created_pair_run_match_bytes_rehashed"])
        self.assertFalse(metrics["hosted_product_group_physical_joysticks_accepted"])
        self.assertFalse(metrics["hosted_product_group_original_event_parity_accepted"])
        self.assertEqual(metrics["hosted_product_group_release_gate_credit"], 0)
        self.assertEqual(metrics["hosted_created_pair_source_riders"], [0, 2])

    def test_all_real_members_are_explicitly_allowed_but_private_files_are_not(self):
        self.assertLessEqual(extra.ALLOWED_MEMBERS, RUNTIME_ALLOWED_MEMBERS)
        self.assertNotIn("UR Baldosa Win32 Pause Route/private/save.srm",
                         RUNTIME_ALLOWED_MEMBERS)
        self.assertNotIn("UR Baldosa Win32 Pause Route/native_player_created_2p_records/save.srm",
                         RUNTIME_ALLOWED_MEMBERS)

    def test_incomplete_corrupt_and_false_claim_groups_are_rejected(self):
        members = group_members()
        for name in (
            extra.SIX_CREATED[0], extra.SIX_CREATED[2],
            extra.SIX_CREATED[5], extra.SIX_CREATED[6],
            extra.SELECTOR[0], extra.SELECTOR[-1],
            extra.ANDREW[0], extra.ANDREW[2],
        ):
            data = dict(members)
            del data[name]
            with self.subTest(missing=name), self.assertRaises(ValueError):
                check(data)
        changes = (
            (extra.SIX_CREATED[0], '"release_gate_credit": 0',
             '"release_gate_credit": 1'),
            (extra.SIX_CREATED[3], "profile2=martin", "profile2=andrew"),
            (extra.SELECTOR[3], "existing_p1_saved=1",
             "existing_p1_saved=0"),
            (extra.ANDREW[0], '"stock_rider_boot_verified": true',
             '"stock_rider_boot_verified": false'),
            (extra.ANDREW[-1], "profile=andrew bytes=8192",
             "profile=mike bytes=8192"),
        )
        for name, old, new in changes:
            data = dict(members)
            self.assertIn(old, data[name])
            data[name] = data[name].replace(old, new)
            with self.subTest(forged=name), self.assertRaises(ValueError):
                check(data)

    def test_reported_5_process_fixture_source_is_not_six_real_ui(self):
        members = group_members()
        from tests.unit.test_check_baldosa_win32_created_pair_records_qa import fixture
        case = fixture()
        raw = [json.dumps(case[0]), *case[1:]]
        for name in extra.SIX_CREATED:
            members.pop(name, None)
        members.update(dict(zip(extra.FIVE_CREATED, raw)))
        metrics = check(members)
        self.assertTrue(metrics[
            "hosted_real_five_native_process_backend_selected_pair_log_consistent"])
        self.assertFalse(metrics[
            "hosted_real_six_native_process_ui_created_pair_and_both_records_log_consistent"])


if __name__ == "__main__":
    unittest.main()
