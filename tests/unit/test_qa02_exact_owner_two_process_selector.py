#!/usr/bin/env python3
"""Pure byte oracle for exact nominated Win32 stale-selector test; not gameplay."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_exact_owner_two_process_selector as qa
from baldosa_windows_native_pause_route import capture_native_selector_conflict_files
from verify_retained_owner_playtest import SOURCE_COMMIT, CANDIDATE_SHA256, EXE_SHA256


def fake_typed(profile: str, raw: bytes) -> bytes:
    return (
        "UR-HOST-PROFILE/5\n"
        f"profile={profile}\ngeneration=1\nstock_sram={raw.hex()}\n"
        "tour_resume=\nghost_target=off\n"
    ).encode("ascii")


class ExactOwnerSelectorConflictTests(unittest.TestCase):
    def test_same_original_nominated_owner_hashes_and_no_gate_promotion(self):
        self.assertEqual(SOURCE_COMMIT, "11501a15dea38fa912335cfc63103ce3a7208001")
        self.assertEqual(CANDIDATE_SHA256,
                         "5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7")
        self.assertEqual(EXE_SHA256,
                         "0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9")
        w = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text("utf-8")
        self.assertIn("qa/qa02-exact-owner-two-process-conflict-20261016", w)
        self.assertIn("12016101293", w)
        self.assertIn("tools/qa02_exact_owner_two_process_selector.py", w)

    def test_profile_decodes_real_8192_byte_stock_sram(self):
        raw = bytes(range(256)) * 32
        generation, decoded = qa.decode_host_profile_stock_sram(
            fake_typed("native-ci-rider", raw))
        self.assertEqual(generation, 1)
        self.assertEqual(decoded, raw)
        with self.assertRaisesRegex(ValueError, "8192 SRAM"):
            qa.decode_host_profile_stock_sram(fake_typed("native-ci-rider", b"short"))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            qa.decode_host_profile_stock_sram(
                fake_typed("native-ci-rider", raw) + b"generation=2\n")

    def test_full_six_file_three_stage_disposition(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "root"
            evidence = Path(temp) / "evidence"
            root.mkdir()
            a = bytes(range(256)) * 32
            b = a[:-1] + bytes([a[-1] ^ 0x5a])
            files = {
                "selector": root / "host-state-v1.txt",
                "catalog": root / "profiles-v1.txt",
                "first_raw": root / "saves/profile-native-ci-rider/save.srm",
                "first_typed": root / "saves/profile-native-ci-rider/host-profile.txt",
                "second_raw": root / "saves/profile-native-ci-second/save.srm",
                "second_typed": root / "saves/profile-native-ci-second/host-profile.txt",
            }
            for path in files.values():
                path.parent.mkdir(parents=True, exist_ok=True)
            files["selector"].write_bytes(b"selected=A")
            files["catalog"].write_bytes(b"catalog=A")
            files["first_raw"].write_bytes(a)
            files["first_typed"].write_bytes(fake_typed("native-ci-rider", a))
            first = capture_native_selector_conflict_files(root, evidence, "before_A")
            self.assertFalse(first["second_raw"]["present"])
            files["selector"].write_bytes(b"selected=B")
            files["catalog"].write_bytes(b"catalog=A,B")
            files["second_raw"].write_bytes(b)
            files["second_typed"].write_bytes(fake_typed("native-ci-second", b))
            capture_native_selector_conflict_files(root, evidence, "after_B_before_A")
            capture_native_selector_conflict_files(root, evidence, "after_A")
            got = qa.audit_stage_files(evidence)
            self.assertEqual(got["profiles"]["first"]["raw_size"], 8192)
            self.assertEqual(got["profiles"]["second"]["raw_size"], 8192)
            self.assertTrue(got["profiles_have_distinct_raw_sram"])
            capture_native_selector_conflict_files(root, evidence, "after_cold_B")
            self.assertEqual(qa.snapshot_bytes(evidence, "after_cold_B")["selector"],
                             b"selected=B")

            # A stale actual game publishing over B after writer B
            # must be recognized even if both profile types still decode.
            files["selector"].write_bytes(b"selected=A")
            capture_native_selector_conflict_files(root, evidence, "after_A")
            with self.assertRaisesRegex(ValueError, "Stale game A modified"):
                qa.audit_stage_files(evidence)

    def test_missing_or_corrupt_byte_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp)
            with self.assertRaises(FileNotFoundError):
                qa.snapshot_bytes(evidence, "before_A")
            with self.assertRaisesRegex(ValueError, "Unrecognized"):
                capture_native_selector_conflict_files(evidence, evidence, "not_a_stage")


if __name__ == "__main__":
    unittest.main()
