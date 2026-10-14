#!/usr/bin/env python3
"""ROM-free adversarial first-racer CI report/log tests. Not hardware QA."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_first_racer_evidence as qa
import verify_baldosa_romless_candidate_qa as wrapperqa
from tests.unit.test_verify_baldosa_romless_candidate_qa import IndependentBaldosaZipQaTests


def fixture():
    report = {
        "scope": "first-anonymous-modern-root-stock-racer-next-process-boot",
        "first_native_guest_creation": True,
        "fresh_native_guest_named_profile_applied": True,
        "existing_stock_sram_root": "saves/profile-mike",
        "before_reboot_sha256": {
            "save.srm": "a" * 64,
            "host-profile.txt": "b" * 64,
            "profiles-v1.txt": "c" * 64,
            "host-state-v1.txt": "d" * 64,
        },
        "physical_pad_acceptance": False,
        "independent_original_native_event_pass": False,
        "release_gate_credit": 0,
    }
    first = (
        "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process\n"
        "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike "
        "activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process\n"
    )
    fresh = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 "
        "fnv=ab01cd23\n"
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
    )
    return report, first, fresh


class IndependentWin32FirstRacerQA(unittest.TestCase):
    def audit(self, report, first, fresh):
        return qa.audit_hosted_win32_first_racer(
            json.dumps(report).encode(), first.encode(), fresh.encode(),
        )

    def test_scripted_controller_semantic_creation_stays_nonrelease(self):
        report, first, fresh = fixture()
        result = self.audit(report, first, fresh)
        self.assertTrue(result[
            "hosted_first_racer_anonymous_creation_to_fresh_named_boot_consistent"])
        self.assertEqual(result["hosted_fresh_boot_sram_fnv32_observed"], "ab01cd23")
        self.assertEqual(result["hosted_first_racer_preset_index"], 0)
        for field in (
            "hosted_created_profile_bytes_independently_rehashed",
            "hosted_one_shot_packaged_launcher_restart_verified",
            "hosted_earned_result_or_fresh_records_verified",
            "hosted_physical_controller_verified",
            "strict_original_native_complete_event_accepted",
        ):
            self.assertFalse(result[field])
        self.assertEqual(result["release_gate_credit"], 0)
        self.assertEqual(result["outcome"], "inconclusive_for_release")

    def test_win32_crlf_and_ordinary_extra_diagnostics(self):
        report, first, fresh = fixture()
        both = self.audit(
            report, "SDL reports 0 joystick(s)\r\n" + first.replace("\n", "\r\n"),
            "SDL init ok: audio=dummy\r\n" + fresh.replace("\n", "\r\n"),
        )
        self.assertTrue(both[
            "hosted_first_racer_anonymous_creation_to_fresh_named_boot_consistent"])

    def test_exact_windows_zip_consumer_binds_first_racer_triad_to_same_exe(self):
        # This is a ROM-free synthetic cross-component contract; the real
        # observed source artifact is independently pinned in the repo's
        # dated Win32 run 38501679761 evidence receipt.
        with tempfile.TemporaryDirectory() as temp:
            inner, revision, digest = IndependentBaldosaZipQaTests().make(Path(temp))
            candidate = wrapperqa.audit(inner, revision, digest)
            exe_sha = candidate["metrics"]["executable_payload_sha256"]
            stock = {
                "classification": "windows_native_pause_and_named_profile_smoke_only",
                "exe_sha256": exe_sha, "course_complete_credit": 0,
                "physical_gamepad_hardware_tested": False,
                "native_named_readonly_records": {
                    "actual_native_2p_match_published": False,
                },
            }
            for players, field in ((1, "modern_root_race_entry_p1"),
                                   (2, "modern_root_race_entry_p2")):
                stock[field] = {
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
            report, first, fresh = fixture()
            archive = Path(temp) / "win32-evidence.zip"
            group = wrapperqa.RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS[0]

            def emit(*, changed_report=report, changed_fresh=fresh):
                with zipfile.ZipFile(archive, "w") as z:
                    z.writestr(wrapperqa.RUNTIME_REPORT, json.dumps(stock))
                    z.writestr(wrapperqa.RUNTIME_LAUNCHER, json.dumps(launcher))
                    for players, member in ((1, wrapperqa.RUNTIME_ONE),
                                            (2, wrapperqa.RUNTIME_TWO)):
                        z.writestr(
                            member,
                            "SDL reports 0 joystick(s)\n"
                            "SDL init ok: video=windows audio=dummy\n"
                            f"UR_BALDOSA_MODERN_ROOT stock_entered players={players} menu=3c\n"
                            "script f=100 quit\n",
                        )
                    z.writestr(group[0], json.dumps(changed_report))
                    z.writestr(group[1], first)
                    z.writestr(group[2], changed_fresh)

            emit()
            readback = wrapperqa.check_runtime_actions_wrapper(
                archive, wrapperqa.audit(inner, revision, digest),
                expected_wrapper_sha=wrapperqa.file_digest(archive),
            )
            self.assertEqual(readback["outcome"], "inconclusive")
            self.assertTrue(readback["metrics"][
                "hosted_first_racer_anonymous_creation_to_fresh_named_boot_consistent"])
            self.assertFalse(readback["metrics"][
                "hosted_created_profile_bytes_independently_rehashed"])
            self.assertFalse(readback["metrics"][
                "hosted_one_shot_packaged_launcher_restart_verified"])
            self.assertFalse(readback["metrics"][
                "finished_native_event_or_new_match_observed"])
            self.assertIn(
                "hosted-first-racer-creation-to-fresh-named-guest-logs-consistent",
                [x["name"] for x in readback["assertions"]],
            )

            emit(changed_report={**report, "physical_pad_acceptance": True})
            with self.assertRaisesRegex(ValueError, "unsupported release or save claims"):
                wrapperqa.check_runtime_actions_wrapper(
                    archive, wrapperqa.audit(inner, revision, digest),
                )
            emit(changed_fresh=fresh.replace("profile=mike", "profile=andrew"))
            with self.assertRaisesRegex(ValueError, "second named guest"):
                wrapperqa.check_runtime_actions_wrapper(
                    archive, wrapperqa.audit(inner, revision, digest),
                )

    def test_no_producer_json_can_award_release_or_physical_credit(self):
        report, first, fresh = fixture()
        for field, value in (
            ("scope", "first-racer-passed"),
            ("first_native_guest_creation", False),
            ("fresh_native_guest_named_profile_applied", 1),
            ("existing_stock_sram_root", "../private"),
            ("physical_pad_acceptance", True),
            ("independent_original_native_event_pass", True),
            ("release_gate_credit", True),
            ("release_gate_credit", 1),
            ("before_reboot_sha256", {}),
            ("before_reboot_sha256", {"save.srm": "a" * 64}),
            ("before_reboot_sha256", {
                **report["before_reboot_sha256"],
                "save.srm": "not-a-hash",
            }),
        ):
            with self.subTest(field=field, value=value):
                damaged = copy.deepcopy(report)
                damaged[field] = value
                with self.assertRaises(ValueError):
                    self.audit(damaged, first, fresh)

    def test_first_process_not_allowed_to_boot_selected_racer_or_race(self):
        report, first, fresh = fixture()
        for damaged in (
            first.replace("status=0", "status=1"),
            first.replace("preset=0", "preset=1"),
            first.replace("activation=next_process", "activation=live"),
            first + first,
            first.replace("first_racer_opened=1", "first_racer_opened=0"),
            first.replace(
                "UR_BALDOSA_MODERN_ROOT opened=1\n",
                "",
            ),
            first + "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike\n",
            first + "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike\n",
            first + "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n",
            first + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
            first + "UR_BALDOSA_NATIVE_RESULT observed=1\n",
        ):
            with self.subTest(damaged=damaged[-100:]):
                with self.assertRaises(ValueError):
                    self.audit(report, damaged, fresh)

    def test_second_process_must_boot_mike_not_create_another_profile(self):
        report, first, fresh = fixture()
        for damaged in (
            fresh.replace("profile=mike", "profile=andrew"),
            fresh.replace("profile-mike", "profile-other"),
            fresh.replace("bytes=8192", "bytes=100"),
            fresh.replace("fnv=ab01cd23", "fnv=garbled"),
            fresh.replace("players=1", "players=2"),
            fresh.replace("menu=3c", "menu=3d"),
            fresh + fresh,
            fresh.replace("BOOT_SRAM", "BOOT_BAD"),
            fresh + "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n",
            fresh + "UR_BALDOSA_MODERN_ROOT first_racer_created=1\n",
            fresh + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
            fresh + "UR_BALDOSA_NATIVE_RESULT observed=1\n",
        ):
            with self.subTest(damaged=damaged[-120:]):
                with self.assertRaises(ValueError):
                    self.audit(report, first, damaged)


if __name__ == "__main__":
    unittest.main()
