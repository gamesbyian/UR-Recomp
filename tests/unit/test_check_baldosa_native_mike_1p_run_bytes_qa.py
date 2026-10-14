#!/usr/bin/env python3
"""Only synthetic ROM-free raw .urrun fixtures, never retained real Windows save bytes."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_baldosa_native_mike_1p_run_bytes_qa as qa
from check_baldosa_native_ci_pair_bytes_qa import BALDOSA_COMPAT, USA_ROM_SHA256
from verify_windows_tournament_acceptance_receipt import fnv_hex
from tests.unit.test_check_baldosa_win32_first_racer_earned_records_qa import sample

RUN_NAME = "run-0001791946349567-0000.urrun"


def encode(rows):
    payload = ("\n".join(rows) + "\n").encode("ascii")
    return payload + f"checksum {fnv_hex(payload)}\n".encode("ascii")


def fake_run(*, mode="race-1p", ticks=1679, frames=2253,
             course="course:01", rom=USA_ROM_SHA256,
             compat=BALDOSA_COMPAT, terminal="-", rows=None, splits=None):
    if rows is None:
        rows = [
            "input 0 100 10 0",
            "input 150 400 20 0",
            "input 550 300 40 0",
            "input 900 200 20 0",
            "input 1200 1053 10 0",
        ]
    if splits is None:
        splits = [f"split finish {ticks}"]
    return encode([
        "URRUN 1", "game uniracers-usa",
        "rom_sha256 " + rom,
        "build_compat " + compat,
        "course " + course,
        "mode " + mode,
        f"elapsed_ticks60 {ticks}", f"frame_count {frames}",
        "terminal_digest " + terminal,
        *splits, *rows, "END",
    ])


class MikeOnePlayerRawRunQA(unittest.TestCase):
    def review(self, *, raw_run=None, reported_sha=None, run_name=RUN_NAME,
               played=None, report=None, created=None, fresh=None):
        actual_report, actual_created, actual_played, actual_fresh = sample()
        raw_run = fake_run() if raw_run is None else raw_run
        actual_report = copy.deepcopy(report or actual_report)
        actual_report["one_canonical_run_sha256"] = (
            reported_sha if reported_sha is not None
            else hashlib.sha256(raw_run).hexdigest()
        )
        return qa.inspect_earned_mike_1p_run_bytes(
            json.dumps(actual_report).encode(),
            (created or actual_created).encode(),
            (played or actual_played).encode(),
            (fresh or actual_fresh).encode(),
            run_name=run_name, raw_run=raw_run,
        )

    def test_matching_synthetic_ci_file_only_proves_codec_and_source_consistency(self):
        out = self.review()
        self.assertTrue(out["saved_run_v1_codec_decoded"])
        self.assertEqual(out["native_source_frame_count_matched"], 2253)
        self.assertEqual(out["native_source_result_ticks60_matched"], 1679)
        self.assertEqual(out["native_source_resolved_input_runs_matched"], 5)
        self.assertEqual(out["saved_run_basename"], RUN_NAME)
        self.assertEqual(out["run_split_count_parsed_not_original_verified"], 1)
        self.assertEqual(out["release_gate_credit"], 0)
        self.assertFalse(out["original_emulator_event_parity_accepted"])
        self.assertFalse(out["physical_controller_audio_display_verified"])
        self.assertFalse(out["approved_merged_main_release_candidate"])
        self.assertEqual(out["outcome"], "inconclusive_for_release")

    def test_exact_native_finish_split_is_not_an_arbitrary_annotation(self):
        # Actual assemble_baldosa_native_run_record() always inserts ONE
        # source finish split at elapsed_ticks60 for a timed 1P Race.
        accepted = self.review()
        self.assertEqual(accepted["run_split_count_parsed_not_original_verified"], 1)
        for splits in (
            [],
            ["split finish 1678"],
            ["split gate:finish 1679"],
            ["split finish 1679", "split extra 1679"],
            ["split finish 1679", "split finish 1679"],
            ["split finish 1700"],
        ):
            with self.subTest(splits=splits):
                with self.assertRaises(ValueError):
                    self.review(raw_run=fake_run(splits=splits))

    def test_stale_or_missing_bytes_never_pass_with_old_producer_hash(self):
        original = fake_run()
        pinned = hashlib.sha256(original).hexdigest()
        for changed in (original + b"x", original[:-1], b"",
                        original.replace(b"\n", b"\r\n"),
                        original.replace(b"input 900 200", b"input 901 200")):
            with self.subTest(changed=changed[-60:]):
                with self.assertRaises(ValueError):
                    self.review(raw_run=changed, reported_sha=pinned)
        with self.assertRaises(ValueError):
            self.review(run_name="other.urrun")

    def test_self_consistent_sha_and_fnv_still_cannot_forge_source_result(self):
        for variant in (
            {"mode": "race-2p"}, {"ticks": 1600},
            {"frames": 2252}, {"course": "course:02"},
            {"rom": "0" * 64}, {"compat": "other-engine-v1"},
            {"terminal": "0" * 64},
            {"rows": ["input 0 100 10 0"]},
            {"rows": ["input 0 100 10 0"] * 5},
            {"rows": [
                "input 0 100 10 0", "input 150 400 20 0",
                "input 550 300 40 0", "input 900 200 20 0",
                "input 1200 1053 10 1",
            ]},
            {"rows": [
                "input 0 100 10 0", "input 50 400 20 0",
                "input 550 300 40 0", "input 900 200 20 0",
                "input 1200 1053 10 0",
            ]},
            {"rows": [
                "input 0 100 10 0", "input 100 400 10 0",
                "input 550 300 40 0", "input 900 200 20 0",
                "input 1200 1053 10 0",
            ]},
            {"rows": [
                "input 0 100 10 0", "input 150 400 20 0",
                "input 550 300 40 0", "input 900 200 20 0",
                "input 1200 1054 10 0",
            ]},
            {"rows": [
                "split 1p:gateA 1000", "split 1p:gateB 900",
                "input 0 100 10 0", "input 150 400 20 0",
                "input 550 300 40 0", "input 900 200 20 0",
                "input 1200 1053 10 0",
            ]},
            {"rows": [
                "input 0 100 10 0", "split 1p:gateA 900",
                "input 150 400 20 0", "input 550 300 40 0",
                "input 900 200 20 0", "input 1200 1053 10 0",
            ]},
            {"rows": [
                "input 0 100 10 0", "input 150 400 20 0",
                "input 550 300 40 0", "input 900 200 20 0",
                "input 1200 1053 10 0", "NOTSOURCE",
            ]},
        ):
            with self.subTest(variant=variant):
                with self.assertRaises(ValueError):
                    self.review(raw_run=fake_run(**variant))

    def test_corrupted_claimed_guest_result_and_profile_cannot_pass(self):
        report, created, played, fresh = sample()
        for bad in (
            played.replace("published=1", "published=0"),
            played.replace("result_host=4164", "result_host=4165"),
            played.replace("inputs=5", "inputs=4"),
            played.replace("profile=mike", "profile=andrew"),
            played.replace("course=course:01", "course=course:02"),
        ):
            with self.subTest(bad=bad[-80:]):
                with self.assertRaises(ValueError):
                    self.review(played=bad)

    def test_read_bounded_refuses_symlink_and_absent_or_zero_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            missing = root / "missing.urrun"
            with self.assertRaises(ValueError):
                qa.read_bounded(missing, 4096)
            zero = root / "empty.urrun"
            zero.write_bytes(b"")
            with self.assertRaises(ValueError):
                qa.read_bounded(zero, 4096)
            real = root / RUN_NAME
            real.write_bytes(fake_run())
            link = root / "link.urrun"
            try:
                link.symlink_to(real)
            except (OSError, NotImplementedError):
                return
            with self.assertRaises(ValueError):
                qa.read_bounded(link, 4096)


if __name__ == "__main__":
    unittest.main()
