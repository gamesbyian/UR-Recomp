#!/usr/bin/env python3
"""ROM-free adversarial tests. Source logs are synthetic, not Win32 witnesses."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_cmd_first_racer_evidence as qa
import verify_baldosa_romless_candidate_qa as wrapperqa
from tests.unit.test_verify_baldosa_romless_candidate_qa import IndependentBaldosaZipQaTests


def trace():
    return (
        "UR-BALDOSA-FIRST-RACER: Restarting with newly created racer.\n"
        "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process\n"
        "UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset=0 id=mike activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process\n"
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike bytes=8192 fnv=d4dc382b\n"
    )


class NativeFirstRacerCMDReview(unittest.TestCase):
    def test_positive_synthetic_cmd_stages_never_grant_physical_credit(self):
        source = trace()
        for text in (source, source.replace("\n", "\r\n")):
            with self.subTest(line_ending=text.count("\r")):
                result = qa.audit_win32_cmd_first_racer_source(text.encode())
                self.assertTrue(result[
                    "hosted_cmd_two_native_roots_one_first_racer_restart_log_consistent"])
                self.assertEqual(result["hosted_cmd_second_native_guest_sram_fnv32_observed"],
                                 "d4dc382b")
                self.assertEqual(result["hosted_cmd_raw_log_sha256"],
                                 hashlib.sha256(text.encode()).hexdigest())
                self.assertFalse(result["hosted_actual_zero_cli_arguments_independently_observed"])
                self.assertFalse(result["hosted_immutable_zip_still_separately_verified"])
                self.assertFalse(result["hosted_physical_gamepad_verified"])
                self.assertFalse(result["strict_original_native_complete_event_accepted"])
                self.assertEqual(result["release_gate_credit"], 0)

    def test_exact_real_windows_receipt_is_report_only_not_raw_log_proof(self):
        receipt = (ROOT / "analysis/evidence" /
                   "baldosa-win32-38504990847-noargs-cmd-first-racer-review.json")
        data = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(data["workflow_run_id"], 38504990847)
        self.assertEqual(data["candidate"]["inner_romless_zip_sha256"],
                         "608ac9224280bd0a1da7434fe2457e4c93df29140e6382d32d53bcfc5a15a469")
        self.assertTrue(data["runtime"]["report_flags"][
            "no_argument_first_racer_cmd_one_shot_restart_accepted"])
        self.assertFalse(data["runtime"]["actual_cmd_first_racer_raw_log_uploaded"])
        self.assertFalse(data["runtime"]["actual_cmd_source_relaunch_independently_recomputed"])
        self.assertFalse(data["candidate"]["approved_release_candidate"])
        self.assertEqual(data["release_scope"]["release_gate_credit"], 0)

    def test_missing_duplicated_reordered_or_forged_native_stages_fail(self):
        source = trace()
        for broken in (
            source.replace("DEFAULT no_host_state=1", "DEFAULT no_host_state=0"),
            source.replace("preset=0", "preset=1"),
            source.replace("first_racer_created=1", "first_racer_created=0"),
            source.replace("profile=mike", "profile=other"),
            source.replace("bytes=8192", "bytes=4096"),
            source.replace("fnv=d4dc382b", "fnv=invalid"),
            source.replace("Restarting with newly created racer.", "Skipping restart."),
            source + "UR-BALDOSA-FIRST-RACER: Restarting with newly created racer.\n",
            source + "UR_BALDOSA_MODERN_ROOT opened=1\n",
            source.replace("UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike\n", ""),
            source.replace(
                "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process\n",
                ""
            ),
            source + "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n",
            source + "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p\n",
            source + "UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p\n",
            source + "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n",
            source + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
        ):
            with self.subTest(broken=broken[-90:]):
                with self.assertRaises(ValueError):
                    qa.audit_win32_cmd_first_racer_source(broken.encode())
        with self.assertRaises(ValueError):
            qa.audit_win32_cmd_first_racer_source(b"")
        with self.assertRaises(ValueError):
            qa.audit_win32_cmd_first_racer_source(source.encode() + b"x" * (2*1024*1024))

    def test_zip_guest_bound_report_only_vs_raw_source_lineage(self):
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
                "no_argument_first_racer_cmd_one_shot_restart_accepted": True,
                "fresh_named_game_after_actual_cmd_restart": True,
            }
            target = root / "win32-evidence.zip"
            def write(*, report=launcher, raw=None):
                with zipfile.ZipFile(target, "w") as z:
                    z.writestr(wrapperqa.RUNTIME_REPORT, json.dumps(stock))
                    z.writestr(wrapperqa.RUNTIME_LAUNCHER, json.dumps(report))
                    for players, name in ((1, wrapperqa.RUNTIME_ONE),
                                          (2, wrapperqa.RUNTIME_TWO)):
                        z.writestr(name, "SDL reports 0 joystick(s)\n"
                                   "SDL init ok: audio=dummy\n"
                                   f"UR_BALDOSA_MODERN_ROOT stock_entered players={players} menu=3c\n"
                                   "script f=100 quit\n")
                    if raw is not None:
                        z.writestr(wrapperqa.RUNTIME_NOARGS_FIRST_RACER_LOG, raw)

            write()
            observed = wrapperqa.check_runtime_actions_wrapper(
                target, wrapperqa.audit(inner, revision, digest))
            self.assertTrue(observed["metrics"][
                "hosted_cmd_noargs_first_racer_restart_producer_reported_only"])
            self.assertFalse(observed["metrics"][
                "hosted_cmd_two_native_roots_one_first_racer_restart_log_consistent"])
            self.assertFalse(observed["metrics"]["hosted_cmd_log_independently_recomputed"])
            self.assertFalse(observed["metrics"]["physical_gamepad_hardware_verified"])

            write(raw=trace())
            checked = wrapperqa.check_runtime_actions_wrapper(
                target, wrapperqa.audit(inner, revision, digest))
            self.assertEqual(checked["outcome"], "inconclusive")
            self.assertTrue(checked["metrics"][
                "hosted_cmd_two_native_roots_one_first_racer_restart_log_consistent"])
            self.assertTrue(checked["metrics"][
                "hosted_cmd_noargs_first_racer_restart_producer_reported"])
            self.assertFalse(checked["metrics"][
                "hosted_cmd_noargs_first_racer_restart_producer_reported_only"])
            self.assertFalse(checked["metrics"]["strict_original_native_complete_event_accepted"])
            self.assertIn(
                "hosted-cmd-noargs-first-racer-two-native-roots-source-log-consistent",
                [a["name"] for a in checked["assertions"]],
            )
            for wrong in (
                trace().replace("preset=0", "preset=1"),
                trace() + trace(),
                trace().replace("BOOT_SRAM profile=mike", "BOOT_SRAM profile=other"),
            ):
                with self.subTest(wrong=wrong[-70:]):
                    write(raw=wrong)
                    with self.assertRaises(ValueError):
                        wrapperqa.check_runtime_actions_wrapper(
                            target, wrapperqa.audit(inner, revision, digest))
            for field in (
                "no_argument_first_racer_cmd_one_shot_restart_accepted",
                "fresh_named_game_after_actual_cmd_restart",
            ):
                for value in (None, False, 1):
                    with self.subTest(field=field, value=value):
                        bad = copy.deepcopy(launcher)
                        if value is None:
                            del bad[field]
                        else:
                            bad[field] = value
                        write(report=bad)
                        with self.assertRaises(ValueError):
                            wrapperqa.check_runtime_actions_wrapper(
                                target, wrapperqa.audit(inner, revision, digest))
            old = {k:v for k,v in launcher.items() if k not in (
                "no_argument_first_racer_cmd_one_shot_restart_accepted",
                "fresh_named_game_after_actual_cmd_restart",
            )}
            write(report=old)
            historic = wrapperqa.check_runtime_actions_wrapper(
                target, wrapperqa.audit(inner, revision, digest))
            self.assertFalse(historic["metrics"][
                "hosted_cmd_noargs_first_racer_restart_producer_reported_only"])
            self.assertFalse(historic["metrics"][
                "hosted_cmd_two_native_roots_one_first_racer_restart_log_consistent"])
            write(report=old, raw=trace())
            with self.assertRaisesRegex(ValueError, "unbound to a positive producer report"):
                wrapperqa.check_runtime_actions_wrapper(
                    target, wrapperqa.audit(inner, revision, digest))


if __name__ == "__main__":
    unittest.main()
