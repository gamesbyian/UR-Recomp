"""Adversarial checks for source-original three-racer archive verifier.

Synthetic files only: no emulator, real Windows device or ROM.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_qa02_win32_three_profile_original import (  # noqa: E402
    verify, PREFIX, SNAP, LABELS, STAGES, BLOB_NAMES
)


def members():
    originals = [bytes((i * 19 + j) % 256 for j in range(8192)) for i in (1, 2, 3)]
    before = {
        "a-raw": originals[0], "a-typed": b"A" * 8300,
        "b-raw": originals[1], "b-typed": b"B" * 8300,
        "c-raw": originals[2], "selector": b"active=native-ci-rider\n",
        "roster": b"native-ci-rider\nnative-ci-second\nnative-ci-third\n",
    }
    damaged = before.copy()
    raw = bytearray(before["a-raw"])
    raw[0x711] ^= 0x35
    damaged["a-raw"] = bytes(raw)
    after = damaged.copy()
    after["selector"] = b"active=native-ci-second\n"
    stages = {"before": before, "damaged": damaged, "after": after, "second-cold": after}
    result = {SNAP + f"{p}.{stage}.bin": states[p]
              for stage, states in stages.items() for p in LABELS}
    result[SNAP + "c-typed.original-then-absent.bin"] = b"C" * 8300
    messages = {
        "damaged-a-refusal.log":
            "UR_BALDOSA_NATIVE_PROFILE REJECTED reason=selected_profile_sram_not_initialized",
        "invalid-c-selection.log":
            "UR_BALDOSA_RECOVERY_CHOICE choice=healthy status=1",
        "explicit-b-selection.log":
            "UR_BALDOSA_RECOVERY_CHOICE choice=healthy next_profile=native-ci-second completed=1",
        "healthy-b-cold-1.log":
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-second",
        "healthy-b-cold-2.log":
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-second",
    }
    result.update({PREFIX + k: v.encode() for k, v in messages.items()})
    result[SNAP + "file-receipt.json"] = json.dumps({
        k: {"sha256": hashlib.sha256(result[SNAP + k]).hexdigest(),
            "bytes": len(result[SNAP + k])}
        for k in BLOB_NAMES
    }).encode()
    return result


def pack(root, entries):
    path = root / "original.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        for name, data in sorted(entries.items()):
            z.writestr(name, data)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class ThreeProfileIndependentTest(unittest.TestCase):
    def test_positive_fixture_is_still_zero_release_gates(self):
        with tempfile.TemporaryDirectory() as d:
            path, sha = pack(Path(d), members())
            verdict = verify(path, sha)
            self.assertEqual(verdict["canonical_binary_objects_verified"], 29)
            self.assertEqual(verdict["source_logs_checked"], 5)
            self.assertEqual(verdict["complete_QA02_release_gate_credit"], 0)
            self.assertFalse(verdict["real_NTFS_partial_write_or_power_loss_verified"])

    def test_original_actions_hash_is_mandatory(self):
        with tempfile.TemporaryDirectory() as d:
            path, sha = pack(Path(d), members())
            with self.assertRaisesRegex(ValueError, "original Actions ZIP hash"):
                verify(path, "0" * 64)

    def test_unrelated_c_corruption_even_with_forged_consistent_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            entries = members()
            name = "c-raw.after.bin"
            raw = SNAP + name
            entries[raw] = b"?" + entries[raw][1:]
            receipt = json.loads(entries[SNAP + "file-receipt.json"])
            receipt[name]["sha256"] = hashlib.sha256(entries[raw]).hexdigest()
            entries[SNAP + "file-receipt.json"] = json.dumps(receipt).encode()
            path, sha = pack(Path(d), entries)
            with self.assertRaisesRegex(ValueError, "unrelated canonical file changed"):
                verify(path, sha)

    def test_selector_churn_after_receipt_rehash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            entries = members()
            key = SNAP + "selector.after.bin"
            entries[key] = entries[SNAP + "selector.before.bin"]
            receipt = json.loads(entries[SNAP + "file-receipt.json"])
            receipt["selector.after.bin"]["sha256"] = hashlib.sha256(entries[key]).hexdigest()
            receipt["selector.after.bin"]["bytes"] = len(entries[key])
            entries[SNAP + "file-receipt.json"] = json.dumps(receipt).encode()
            path, sha = pack(Path(d), entries)
            with self.assertRaisesRegex(ValueError, "selector update missing"):
                verify(path, sha)

    def test_missing_exported_c_and_extra_rom_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            entries = members()
            del entries[SNAP + "c-typed.original-then-absent.bin"]
            path, sha = pack(Path(d), entries)
            with self.assertRaisesRegex(ValueError, "missing three-profile evidence"):
                verify(path, sha)
            entries = members()
            entries["Uniracers.sfc"] = b"ROM forbidden"
            path, sha = pack(Path(d), entries)
            with self.assertRaisesRegex(ValueError, "ROM-containing"):
                verify(path, sha)

    def test_duplicate_archive_entry_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "original.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(path, "w") as z:
                    for name, data in members().items():
                        z.writestr(name, data)
                    z.writestr(SNAP + "a-raw.before.bin", b"bad")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "duplicate ZIP entry"):
                verify(path, sha)


if __name__ == "__main__":
    unittest.main()
