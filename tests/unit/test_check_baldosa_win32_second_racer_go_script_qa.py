#!/usr/bin/env python3
"""Synthetic negative testing for original guest GO wait receipts only."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_baldosa_win32_second_racer_go_script_qa as qa
from tests.unit.test_check_baldosa_win32_second_racer_go_qa import example


def synthetic():
    report, first, second, third = example()
    guest_prefix = (
        "SDL reports 0 joystick(s)\n"
        "SDL init ok: video=windows audio=dummy\n"
        "script f=0 turbo on\n"
        "script f=248 until 00053 ok after 248 frames\n"
    )
    guest_end = (
        "script f=2002 until 00053 ok after 6 frames\n"
        "script f=2353 until 00E1F ok after 351 frames\n"
        "script f=2353 dump go ok\n"
        "script f=2353 quit\n"
    )
    return (json.dumps(report).encode(), first.encode(), second.encode(),
            (guest_prefix + third + guest_end).encode(),
            qa.SOURCE.read_bytes())


class IndependentGuestGOLogAudit(unittest.TestCase):
    def audit(self, raw):
        return qa.audit_guest_script(*raw)

    def test_current_source_and_bounded_guest_script_admit_no_completed_event(self):
        observed = self.audit(synthetic())
        self.assertTrue(observed["hosted_native_guest_source_script_wait_receipts_consistent"])
        self.assertEqual(observed["hosted_guest_go_script_nmi_frame"], 2002)
        self.assertEqual(observed["hosted_guest_go_script_ticker_frame"], 2353)
        for field in (
            "guest_go_register_bytes_independently_archived",
            "original_emulator_GO_parity_independently_accepted",
            "source_settled_scored_2p_result",
            "player_created_pair_fresh_records_reopened",
            "actual_physical_controller_or_audio_accepted",
        ):
            self.assertFalse(observed[field])
        self.assertEqual(observed["release_gate_credit"], 0)

    def test_win32_real_crlf_is_permitted(self):
        parts = list(synthetic())
        for i in (1, 2, 3):
            parts[i] = parts[i].replace(b"\n", b"\r\n")
        self.assertTrue(self.audit(parts)[
            "hosted_native_guest_source_script_wait_receipts_consistent"])

    def test_guest_markers_cannot_be_faked_reordered_or_conflated(self):
        original = synthetic()
        third = original[3].decode()
        samples = (
            third.replace("script f=248 until 00053 ok after 248 frames\n", ""),
            third.replace("script f=2002 until 00053 ok after 6 frames\n", ""),
            third.replace("script f=2353 until 00E1F ok after 351 frames\n", ""),
            third.replace("script f=2353 dump go ok\n", ""),
            third.replace("script f=2353 quit\n", ""),
            third.replace("script f=2353 dump go ok", "script f=2354 dump go ok"),
            third.replace("script f=2353 until 00E1F", "script f=2001 until 00E1F"),
            third.replace("script f=2002 until 00053", "script f=247 until 00053"),
            third.replace("script f=2353 until 00E1F ok after 351 frames",
                          "DEBUG: script f=2353 until 00E1F ok after 351 frames"),
            third + "echo script f=2353 dump go ok\n",
            third + "script f=2353 dump go ok\n",
            third.replace("SDL reports 0 joystick(s)", "SDL reports 2 joystick(s)"),
            third.replace("audio=dummy", "audio=real"),
            third.replace("stock_entered players=2 menu=3d",
                          "stock_entered players=2 menu=3c"),
            third.replace("script f=248 until 00053 ok after 248 frames\n",
                          "script f=248 until 00053 ok after 0 frames\n"),
        )
        for value in samples:
            with self.subTest(case=value[-95:]):
                parts = list(original)
                parts[3] = value.encode()
                with self.assertRaises(ValueError):
                    self.audit(parts)

    def test_source_script_cannot_silently_change_the_guest_barriers(self):
        original = synthetic()
        for frm, to in (
            (b'"until16 0053 == F60C"', b'"until16 0053 == F60D"'),
            (b'"until16 0053 == 8610"', b'"until16 0053 == 8611"'),
            (b'"until 0E1F != 00"', b'"until 0E1F == 00"'),
            (b'"dump go"', b'"dump guest"'),
        ):
            parts = list(original)
            self.assertIn(frm, parts[4])
            parts[4] = parts[4].replace(frm, to)
            with self.subTest(token=frm):
                with self.assertRaises(ValueError):
                    self.audit(parts)

    def test_bounded_named_evidence_zip_members(self):
        group = synthetic()
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "runtime.zip"
            with zipfile.ZipFile(archive, "w") as z:
                for name, data in zip(qa.FILES, group[:4]):
                    z.writestr(qa.PREFIX + name, data)
            self.assertEqual(qa.read_bounded_runtime(archive), group[:4])
            with zipfile.ZipFile(archive, "a") as z:
                z.writestr(qa.PREFIX + qa.FILES[-1], group[3])
            with self.assertRaisesRegex(ValueError, "duplicated"):
                qa.read_bounded_runtime(archive)


if __name__ == "__main__":
    unittest.main()
