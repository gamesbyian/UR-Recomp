#!/usr/bin/env python3
"""Only synthetic, ROM-free codec fixtures. No real Windows run bytes exist here."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_native_ci_pair_bytes_qa as consumer
from verify_windows_tournament_acceptance_receipt import fnv_hex
from tests.unit.test_check_baldosa_win32_native_2p_records_evidence import observed


RUN = "run-123.urrun"


def encode(lines):
    body = ("\n".join(lines) + "\n").encode("ascii")
    return body + ("checksum " + fnv_hex(body) + "\n").encode("ascii")


def fake_pair(
    *,
    frame_count=2231, mode="race-2p", course="course:01",
    win="p2", p1_result=2761, p2_result=2757, p2_name="MARTIN",
    p2_rider=2, first_start=0,
):
    inputs = [
        f"input {first_start} 300 10 40",
        "input 300 30 10 40",
        "input 330 900 10 40",
        "input 1230 30 10 40",
        "input 1260 971 10 40",
    ]
    run = encode([
        "URRUN 1", "game uniracers-usa",
        "rom_sha256 " + consumer.USA_ROM_SHA256,
        "build_compat " + consumer.BALDOSA_COMPAT,
        "course " + course, "mode " + mode,
        "elapsed_ticks60 1654", f"frame_count {frame_count}",
        "terminal_digest -", *inputs, "END",
    ])
    checksum = run.decode("ascii").splitlines()[-1][9:]
    match = encode([
        "UR-MULTIPLAYER-MATCH/1",
        "run_checksum " + checksum,
        "course course:01", "outcome " + win,
        f"p1_result {p1_result}", f"p2_result {p2_result}",
        "p1_profile " + b"native-ci-rider".hex(),
        "p1_name " + b"MIKE".hex(), "p1_rider 0",
        "p2_profile " + b"native-ci-second".hex(),
        "p2_name " + p2_name.encode("ascii").hex(),
        f"p2_rider {p2_rider}",
    ])
    return run, match


class IndependentRawNativeCIPairQA(unittest.TestCase):
    def review(self, *, run=None, match=None, reported=None, report_overrides=None):
        report, played, fresh = observed()
        real_run, real_match = fake_pair()
        if run is None:
            run = real_run
        if match is None:
            match = real_match
        report = copy.deepcopy(report)
        report["canonical_match_artifact_sha256"] = reported or {
            RUN: hashlib.sha256(run).hexdigest(),
            RUN + ".urmatch": hashlib.sha256(match).hexdigest(),
        }
        if report_overrides:
            report.update(report_overrides)
        return consumer.audit_raw_native_ci_two_player_pair(
            json.dumps(report).encode(), played.encode(), fresh.encode(),
            run_name=RUN, raw_run=run, raw_match=match,
        )

    def test_synthetic_ci_bytes_pass_only_narrow_byte_consistency(self):
        x = self.review()
        self.assertTrue(x["saved_run_and_match_bytes_independently_decoded"])
        self.assertEqual(x["source_input_frames"], 2231)
        self.assertEqual(x["source_input_runs"], 5)
        self.assertEqual(x["run_name"], RUN)
        self.assertFalse(x["strict_original_emulator_event_parity_verified"])
        self.assertFalse(x["physical_windows_hardware_verified"])
        self.assertEqual(x["release_gate_credit"], 0)
        self.assertEqual(x["outcome"], "inconclusive_for_release")

    def test_tampered_or_missing_bytes_cannot_be_admitted_with_old_report_hash(self):
        raw_run, raw_match = fake_pair()
        pinned = {
            RUN: hashlib.sha256(raw_run).hexdigest(),
            RUN + ".urmatch": hashlib.sha256(raw_match).hexdigest(),
        }
        for change_run, change_match in (
            (raw_run + b"x", raw_match),
            (raw_run, raw_match + b"x"),
            (b"", raw_match),
            (raw_run, b""),
        ):
            with self.subTest(lengths=(len(change_run), len(change_match))):
                with self.assertRaises(ValueError):
                    self.review(run=change_run, match=change_match,
                                reported=pinned)

    def test_valid_rechecksummed_wrong_source_or_pair_still_fails(self):
        for kwargs in (
            {"frame_count": 2230},
            {"mode": "race-1p"},
            {"course": "course:02"},
            {"win": "p1"},
            {"p1_result": 2757},
            {"p2_result": 2761},
            {"p2_name": "ANDREW"},
            {"p2_rider": 1},
            {"first_start": 1},
        ):
            with self.subTest(case=kwargs):
                run, match = fake_pair(**kwargs)
                with self.assertRaises(ValueError):
                    self.review(run=run, match=match)

    def test_v1_noncanonical_text_and_internal_checksum_rejected(self):
        run, match = fake_pair()
        for changed in (
            run.replace(b"\n", b"\r\n"),
            run[:-1],
            run.replace(b"input 300", b"input 0300"),
            run.replace(b"END\n", b"END\njunk\n"),
            run.replace(b"input 300 30", b"input 200 30"),
        ):
            with self.subTest(bad=changed[-60:]):
                with self.assertRaises(ValueError):
                    self.review(run=changed, match=match)
        with self.assertRaises(ValueError):
            self.review(run=run, match=match.replace(b"\n", b"\r\n"))


if __name__ == "__main__":
    unittest.main()
