#!/usr/bin/env python3
"""Admission tests for three-process first-user -> real 1P -> Records chain.

The logs here are synthetic and NEVER confer original/native gameplay credit.
The actual Windows executable and source-run artifact are mandatory in CI.
"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_native_first_racer_real_run_probe as chain
from baldosa_native_1p_records_probe import (
    native_records_reopened,
    source_finish_script,
    source_result_published,
)


def genuine_log(profile: str = "mike") -> str:
    return (
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c\n"
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p "
        f"profile={profile} course=course:01 "
        "input_frames=2253 inputs=5 path=run.urrun\n"
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p "
        "race_host=1910 result_host=4163 finish_ticks60=1679 "
        "input_frames=2253 input_runs=5 published=1\n"
    )


def records_log(profile: str = "mike") -> str:
    return (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile} "
        f"root=saves/profile-{profile}\n"
        "UR_BALDOSA_MODERN_ROOT records_opened=1 "
        "profile=selected validated=1 unavailable=0\n"
    )


class FirstRacerPlayedRecordAcceptance(unittest.TestCase):
    def test_reuses_real_source_drive_and_profile_bound_admission(self):
        self.assertIn("until16 0053 == 8610", source_finish_script())
        self.assertIn("until 0E1F != 00", source_finish_script())
        self.assertIn("press right 1200", source_finish_script())
        source_result_published(genuine_log(), profile="mike")
        source_result_published(genuine_log("native-ci-rider"))
        for broken in (
            genuine_log("native-ci-rider"),
            genuine_log().replace("published=1", "published=0"),
            genuine_log().replace("result_host=4163", "result_host=1200"),
            genuine_log().replace("finish_ticks60=1679", "finish_ticks60=0"),
            genuine_log().replace("course=course:01", "course=course:02"),
            genuine_log().replace("CAPTURED=1", "CAPTURED=0"),
            genuine_log() + genuine_log(),
            genuine_log() + "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1\n",
        ):
            with self.subTest(broken=broken[-120:]):
                with self.assertRaises(ValueError):
                    source_result_published(broken, profile="mike")

    def test_records_require_same_new_player_and_earned_run(self):
        native_records_reopened(records_log(), profile="mike")
        native_records_reopened(records_log("native-ci-rider"))
        for broken in (
            records_log("native-ci-rider"),
            records_log().replace("validated=1", "validated=0"),
            records_log().replace("unavailable=0", "unavailable=1"),
            records_log() + records_log(),
            records_log() + "UR_BALDOSA_NATIVE_RESULT observed=1\n",
            records_log() + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
        ):
            with self.subTest(broken=broken[-120:]):
                with self.assertRaises(ValueError):
                    native_records_reopened(broken, profile="mike")

    def test_real_first_racer_boot_fingerprint_accepts_exact_mike_only(self):
        from baldosa_windows_native_pause_route import (
            fnv32, verify_named_profile_boot_bytes,
        )
        raw = bytes(range(256)) * 32
        log = (
            "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
            "root=saves/profile-mike\n"
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=mike "
            f"bytes=8192 fnv={fnv32(raw)}\n"
        )
        self.assertEqual(
            verify_named_profile_boot_bytes(log, raw, profile_id="mike")["bytes"],
            8192)
        for bad in (
            log.replace(fnv32(raw), "12345678"),
            log.replace("profile=mike ", "profile=other ", 1),
            log + log,
            log.replace("bytes=8192", "bytes=8191"),
        ):
            with self.subTest(bad=bad[-100:]):
                with self.assertRaises(ValueError):
                    verify_named_profile_boot_bytes(bad, raw, profile_id="mike")
        with self.assertRaises(ValueError):
            verify_named_profile_boot_bytes(log, raw, profile_id="unsupported")

    def test_archive_admission_refuses_empty_duplicates_or_redirects(self):
        with tempfile.TemporaryDirectory() as temp:
            user = Path(temp)
            root = user / "runs" / "mike"
            root.mkdir(parents=True)
            with self.assertRaises(ValueError):
                chain.assert_exact_one_named_run(user, "mike")
            record = root / "played.urrun"
            record.write_bytes(b"native original controlled result")
            path, digest = chain.assert_exact_one_named_run(user, "mike")
            self.assertEqual(path, record)
            self.assertEqual(len(digest), 64)
            (root / "duplicate.urrun").write_bytes(b"extra")
            with self.assertRaises(ValueError):
                chain.assert_exact_one_named_run(user, "mike")
            (root / "duplicate.urrun").unlink()
            record.write_bytes(b"")
            with self.assertRaises(ValueError):
                chain.assert_exact_one_named_run(user, "mike")
            record.unlink()
            record.write_bytes(b"safe")
            if hasattr(Path, "symlink_to"):
                redirect = user / "redirection"
                try:
                    redirect.write_bytes(b"redirected run")
                    record.unlink()
                    record.symlink_to(redirect)
                except (OSError, NotImplementedError):
                    pass
                else:
                    with self.assertRaises(ValueError):
                        chain.assert_exact_one_named_run(user, "mike")

    def test_three_separate_games_are_strict_real_processes_not_repackaged_fixture(self):
        body = (ROOT / "tools/baldosa_native_first_racer_real_run_probe.py"
                ).read_text(encoding="utf-8")
        for part in (
            'output / "new_user_creates_first_racer"',
            'output / "fresh_named_player_completes_race"',
            'output / "new_game_reopens_earned_records"',
            "source_finish_script()",
            "source_result_published(race, profile=P1)",
            "native_records_reopened(fresh, profile=P1)",
            "verify_native_profile_checkpoint(fixture, user, P1, race, timeout)",
            "assert_exact_one_named_run(user, P1)",
            '"release_gate_credit": 0',
        ):
            self.assertIn(part, body)
        self.assertNotIn("RtlWriteSram(", body)
        self.assertNotIn("source_result_published(genuine_log", body)


if __name__ == "__main__":
    unittest.main()
