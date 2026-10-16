#!/usr/bin/env python3
"""Fail-closed QA-only raw/typed and two-profile crash-blast-radius oracles."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa02_original_two_profile_crash_blast as qa
from verify_retained_owner_playtest import SOURCE_COMMIT, CANDIDATE_SHA256, EXE_SHA256


def typed(raw: bytes, profile: str) -> bytes:
    return (
        f"UR-HOST-PROFILE/5\nprofile={profile}\ngeneration=1\n"
        f"stock_sram={raw.hex()}\n"
    ).encode("ascii")


def states():
    raw_a = bytes(range(256)) * 32
    raw_b = raw_a[:-1] + bytes([raw_a[-1] ^ 0x5a])
    original = {
        "selector": b"selected:B", "catalog": b"A|B",
        "A_raw": raw_a, "A_typed": typed(raw_a, "native-ci-rider"),
        "B_raw": raw_b, "B_typed": typed(raw_b, "native-ci-second"),
    }
    after = dict(original, B_raw=raw_b[:-10] + bytes(x ^ 1 for x in raw_b[-10:]))
    return original, after


class TwoProfileCrashBlastRadiusTests(unittest.TestCase):
    def test_candidate_pinning_and_no_release_promotion(self):
        self.assertEqual(SOURCE_COMMIT, "11501a15dea38fa912335cfc63103ce3a7208001")
        self.assertEqual(CANDIDATE_SHA256,
                         "5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7")
        self.assertEqual(EXE_SHA256,
                         "0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9")
        source = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertIn("qa/qa02-original-two-profile-crash-blast-20261016", source)
        self.assertIn("qa02_original_two_profile_crash_blast.py", source)
        self.assertIn("12016101293", source)
        self.assertIn("release_gate_credit", (ROOT / "tools/qa02_original_two_profile_crash_blast.py").read_text())

    def test_crash_must_change_only_B_raw_and_keep_valid_A(self):
        before, after = states()
        audit = qa.adjudicate_crash(before, after)
        self.assertEqual(audit["B_raw_changed_count"], 10)
        self.assertTrue(audit["healthy_A_raw_typed_and_global_data_unchanged"])
        self.assertNotEqual(audit["old_and_new_B_raw_sha256"][0],
                            audit["old_and_new_B_raw_sha256"][1])
        with self.assertRaisesRegex(ValueError, "did not write newly"):
            qa.adjudicate_crash(before, before)
        for key in ("A_raw", "A_typed", "B_typed", "selector", "catalog"):
            changed = dict(after, **{key: b"corrupted"})
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "changed last-good"):
                qa.adjudicate_crash(before, changed)
        corrupt_initial = dict(before, A_typed=typed(bytes(8192), "native-ci-rider"))
        with self.assertRaisesRegex(ValueError, "originally valid"):
            qa.adjudicate_crash(corrupt_initial, after)
        no_B = {k: v for k, v in after.items() if k != "B_typed"}
        with self.assertRaisesRegex(ValueError, "incomplete six-file"):
            qa.adjudicate_crash(before, no_B)

    def test_byte_capture_contains_full_six_files_and_rejects_redirect(self):
        before, _ = states()
        with tempfile.TemporaryDirectory() as td:
            root, output = Path(td) / "root", Path(td) / "artifact"
            root.mkdir()
            for name, rel in qa.FILES.items():
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(before[name])
            capture = qa.capture(root, output, "healthy_before_B_crash")
            self.assertEqual(capture, before)
            report = json.loads((output / "healthy_before_B_crash.json").read_text())
            self.assertEqual(set(report), set(qa.FILES))
            for name in qa.FILES:
                self.assertEqual((output / f"healthy_before_B_crash.{name}.bin").read_bytes(),
                                 before[name])
                self.assertEqual(report[name]["sha256"], qa.digest(before[name]))
            with self.assertRaisesRegex(ValueError, "invalid independent"):
                qa.capture(root, output, "made-up")
            (root / qa.FILES["B_raw"]).write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "8192 bytes"):
                qa.capture(root, output, "after_B_crash")


if __name__ == "__main__":
    unittest.main()
