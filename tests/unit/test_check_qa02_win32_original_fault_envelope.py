"""Fail-closed synthetic tests for source-original 39-member Win32 fault archive.

Inputs are synthetic SRAM and fabricated logs only; no guest/ROM or release
approval is claimed. The actual pinned Windows 39-member archive is independently
hashed and analyzed by the real QA evidence receipt.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "unit"))
sys.path.insert(0, str(ROOT / "tools"))
from check_qa02_win32_original_fault_envelope import (  # noqa: E402
    EXTRA, NEG, POS, audit,
)
from test_check_qa02_win32_fault_snapshots import make_members  # noqa: E402


def original_members() -> dict[str, bytes]:
    members = {NEG + name: value
               for name, value in make_members("unjournaled").items()}
    members.update({POS + name: value
                    for name, value in make_members("journaled").items()})
    supplement = {
        "native_post_raw_pre_typed_crash/explicit-recovery-native-command.log":
            b"UR_BALDOSA_RECOVERY_CHOICE choice=raw completed=1\n",
        "native_post_raw_pre_typed_crash/explicit-recovery-fresh-boot.log":
            b"UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=example\n",
        "native_recovery_healthy_alternate/damaged-source-refusal.log":
            b"selected_profile_sram_not_initialized\n",
        "native_recovery_healthy_alternate/explicit-healthy-selection.log":
            b"UR_BALDOSA_RECOVERY_CHOICE choice=healthy completed=1\n",
        "native_recovery_healthy_alternate/fresh-healthy-guest.log":
            b"UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=other\n",
    }
    assert set(supplement) == EXTRA
    members.update(supplement)
    return members


def write_zip(root: Path, members: dict[str, bytes]) -> tuple[Path, str]:
    path = root / "source-original.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(members.items()):
            z.writestr(name, data)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class OriginalWin32FaultEnvelopeTest(unittest.TestCase):
    def test_two_exact_cases_and_supplemental_source_logs(self):
        with tempfile.TemporaryDirectory() as d:
            path, sha = write_zip(Path(d), original_members())
            result = audit(path, sha)
            self.assertEqual(result["source_original_GitHub_Actions_ZIP_SHA256"], sha)
            self.assertEqual(result["source_original_member_count"], 39)
            self.assertEqual(result["supplemental_win32_logs_checked"], 5)
            self.assertEqual(set(result["cases"]), {"unjournaled", "journaled"})
            self.assertTrue(result["same_original_guest_raw_bytes_both_modes"])
            self.assertEqual(result["release_gate_credit"], 0)

    def test_reject_mutation_and_extra_rom_even_with_updated_outer_sha(self):
        with tempfile.TemporaryDirectory() as d:
            members = original_members()
            path, sha = write_zip(Path(d), members)
            with self.assertRaisesRegex(ValueError, "original Actions ZIP SHA256 mismatch"):
                audit(path, "0" * 64)
            members["Uniracers_USA.sfc"] = b"not a game ROM"
            path, sha = write_zip(Path(d), members)
            with self.assertRaisesRegex(ValueError, "whole-artifact|unexpected|duplicate"):
                audit(path, sha)

    def test_reject_forged_intent_with_valid_repacked_outer_hash(self):
        with tempfile.TemporaryDirectory() as d:
            members = original_members()
            members[POS + "intent.recovered-receipt.bin"] = b"fake"
            path, sha = write_zip(Path(d), members)
            with self.assertRaisesRegex(ValueError, "crash intent and recovered"):
                audit(path, sha)

    def test_reject_wrong_legacy_choice_with_valid_repacked_outer_hash(self):
        with tempfile.TemporaryDirectory() as d:
            members = original_members()
            members["native_post_raw_pre_typed_crash/explicit-recovery-native-command.log"] = (
                b"UR_BALDOSA_RECOVERY_CHOICE choice=typed completed=1\n")
            path, sha = write_zip(Path(d), members)
            with self.assertRaisesRegex(ValueError, "explicit legacy raw selection missing"):
                audit(path, sha)

    def test_reject_cross_mode_real_guest_raw_difference(self):
        with tempfile.TemporaryDirectory() as d:
            members = original_members()
            # Each case's own SHA receipt is recomputed, so the aggregate
            # auditor must catch cross-mode guest byte substitution itself.
            stage = POS + "raw-sram.crash.bin"
            data = bytearray(members[stage])
            data[600] ^= 0x40
            members[stage] = bytes(data)
            receipt_path = POS + "file-receipt.json"
            receipt = json.loads(members[receipt_path].decode())
            receipt["raw-sram"]["crash_sha256"] = hashlib.sha256(data).hexdigest()
            receipt["raw-sram"]["crash_changed_byte_count"] += 1
            members[receipt_path] = json.dumps(receipt).encode()
            path, sha = write_zip(Path(d), members)
            with self.assertRaises(ValueError):
                audit(path, sha)


if __name__ == "__main__":
    unittest.main()
