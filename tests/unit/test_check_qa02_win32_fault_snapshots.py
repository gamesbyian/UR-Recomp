"""Synthetic fail-closed tests for original and journaled QA-02 ZIP receipt reader.

Generated SRAM here is a codec test only, NEVER evidence of a Windows game.
"""
from __future__ import annotations
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from check_qa02_win32_fault_snapshots import inspect  # noqa: E402

SOURCE = "1" * 40
EXE = "2" * 64
LOG = ("UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1\n"
       "UR_BALDOSA_NATIVE_PROFILE QA_CRASH_AFTER_RAW_WRITE exit=86 typed_checkpoint=0\n")


def typed(raw: bytes, generation: int) -> bytes:
    return ("UR-HOST-PROFILE/5\nprofile=example\ngeneration=" + str(generation) +
            "\nstock_sram=" + raw.hex() + "\n").encode()


def make_members(mode: str) -> dict[str, bytes]:
    before_raw = bytes(8192)
    changed_raw = b"\x01" + before_raw[1:]
    old = {"raw-sram": before_raw, "typed-profile": typed(before_raw, 1),
           "selector": b"selector", "roster": b"roster"}
    crash = {**old, "raw-sram": changed_raw}
    after = crash if mode == "historic" else {**crash, "typed-profile": typed(changed_raw, 2)}
    stages = {"before": old, "after": after}
    if mode != "historic":
        stages["crash"] = crash
    files = {}
    receipt = {}
    for name in old:
        fields = {}
        for stage, values in stages.items():
            binary = values[name]
            files[f"{name}.{stage}.bin"] = binary
            fields[stage + "_bytes"] = len(binary)
            fields[stage + "_sha256"] = hashlib.sha256(binary).hexdigest()
        fields["changed_byte_count"] = sum(a != b for a, b in zip(old[name], after[name]))
        if mode != "historic":
            fields["crash_changed_byte_count"] = sum(
                a != b for a, b in zip(old[name], crash[name]))
        receipt[name] = fields
    if mode == "journaled":
        old_typed = old["typed-profile"]
        new_typed = after["typed-profile"]
        intent = (b"UR-BALDOSA-NATIVE-SRAM-INTENT/1\n" +
                  str(len(old_typed)).encode() + b"\n" +
                  str(len(new_typed)).encode() + b"\n" +
                  old_typed + new_typed)
        files["intent.crash.bin"] = intent
        files["intent.recovered-receipt.bin"] = intent
        files["second-cold-recovery-boot.log"] = (
            b"UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=example\n")
        intent_receipt = {
            "crash_sha256": hashlib.sha256(intent).hexdigest(),
            "receipt_sha256": hashlib.sha256(intent).hexdigest(),
            "bytes": len(intent),
            "byte_identical": True,
            "pending_retired": True,
        }
        files["intent-receipt.json"] = json.dumps(intent_receipt).encode()
    files["file-receipt.json"] = json.dumps(receipt).encode()
    files["crash.log"] = LOG.encode()
    if mode == "historic":
        files["cold-refusal.log"] = b"selected_profile_sram_not_initialized\n"
        files["qa02-exact-owner-receipt.json"] = json.dumps({
            "schema": "qa02-nominated-owner-real-win32-crash-byte-receipt/1",
            "tested_source": SOURCE, "original_candidate_exe_sha256": EXE,
            "native_process_result": {"forced_process_exit_code": 86}}).encode()
    elif mode == "unjournaled":
        files["cold-refusal.log"] = b"selected_profile_sram_not_initialized\n"
    else:
        files["cold-recovery.log"] = (
            b"RECOVERY_RECONCILED exact_staged_guest_sram=1 no_records=1\n"
            b"UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=example\n")
    return files


def pack(root: Path, files: dict[str, bytes]) -> tuple[Path, str]:
    path = root / "synthetic.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class SnapshotByteConsumerTest(unittest.TestCase):
    def test_synthetic_original_refusal_and_journaled_reconciliation(self):
        with tempfile.TemporaryDirectory() as d:
            for mode in ("historic", "unjournaled", "journaled"):
                path, sha = pack(Path(d), make_members(mode))
                report = inspect(path, sha, mode, source=SOURCE, exe=EXE)
                self.assertEqual(report["changed_guest_raw_bytes"], 1)
                self.assertEqual(report["release_gate_credit"], 0)

    def test_three_stage_unjournaled_rejects_silent_promotion(self):
        with tempfile.TemporaryDirectory() as d:
            members = make_members("unjournaled")
            path, sha = pack(Path(d), members)
            report = inspect(path, sha, "unjournaled")
            self.assertFalse(report["reconciled_typed"])
            members["typed-profile.after.bin"] = typed(b"\x01" + bytes(8191), 2)
            path, sha = pack(Path(d), members)
            with self.assertRaisesRegex(ValueError, "declared SHA/length mismatch"):
                inspect(path, sha, "unjournaled")

    def test_digest_mismatch_and_false_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path, sha = pack(Path(d), make_members("journaled"))
            with self.assertRaisesRegex(ValueError, "actual archive ZIP differs"):
                inspect(path, "0" * 64, "journaled")
            members = make_members("journaled")
            members["raw-sram.crash.bin"] = bytes(8192)
            path, sha = pack(Path(d), members)
            with self.assertRaisesRegex(ValueError, "declared SHA/length mismatch"):
                inspect(path, sha, "journaled")

    def test_falsified_typed_checkpoint_and_private_rom_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            members = make_members("journaled")
            members["typed-profile.after.bin"] = members["typed-profile.before.bin"]
            path, sha = pack(Path(d), members)
            with self.assertRaisesRegex(ValueError, "declared SHA/length mismatch"):
                inspect(path, sha, "journaled")
            members = make_members("journaled")
            members["Uniracers_USA.sfc"] = b"not a real ROM"
            path, sha = pack(Path(d), members)
            with self.assertRaisesRegex(ValueError, "unrecognized, missing or duplicated"):
                inspect(path, sha, "journaled")

    def test_forged_intent_or_changed_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            members = make_members("journaled")
            modified = bytearray(members["intent.crash.bin"])
            modified[-1] ^= 1
            members["intent.crash.bin"] = bytes(modified)
            path, sha = pack(Path(d), members)
            with self.assertRaisesRegex(ValueError, "crash intent and recovered"):
                inspect(path, sha, "journaled")
            members = make_members("journaled")
            members["intent.crash.bin"] = b"garbage"
            members["intent.recovered-receipt.bin"] = b"garbage"
            receipt = json.loads(members["intent-receipt.json"])
            receipt["crash_sha256"] = hashlib.sha256(b"garbage").hexdigest()
            receipt["receipt_sha256"] = hashlib.sha256(b"garbage").hexdigest()
            receipt["bytes"] = len(b"garbage")
            members["intent-receipt.json"] = json.dumps(receipt).encode()
            path, sha = pack(Path(d), members)
            with self.assertRaisesRegex(ValueError, "invalid durable prewrite-intent"):
                inspect(path, sha, "journaled")

    def test_second_cold_or_missing_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            members = make_members("journaled")
            members["second-cold-recovery-boot.log"] = (
                b"UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED\n"
                b"UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM\n")
            path, sha = pack(Path(d), members)
            with self.assertRaisesRegex(ValueError, "second cold guest"):
                inspect(path, sha, "journaled")
            members = make_members("journaled")
            del members["intent.recovered-receipt.bin"]
            path, sha = pack(Path(d), members)
            with self.assertRaisesRegex(ValueError, "unrecognized, missing"):
                inspect(path, sha, "journaled")

    def test_source_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path, sha = pack(Path(d), make_members("historic"))
            with self.assertRaisesRegex(ValueError, "source/PE report differs"):
                inspect(path, sha, "historic", source="3" * 40, exe=EXE)


if __name__ == "__main__":
    unittest.main()
