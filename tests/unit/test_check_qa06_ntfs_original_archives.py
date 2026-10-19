"""Adversarial synthetic archive tests. Never asserts a real Windows execution."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_qa06_ntfs_original_archives as qa

SOURCE = "a" * 40
CMD = "b" * 64


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def typed(raw: bytes, generation: int) -> bytes:
    return (f"UR-HOST-PROFILE/5\nprofile=synthetic\ngeneration={generation}\n"
            f"stock_sram={raw.hex()}\ntour_resume=\n").encode("ascii")


def scenario(root: Path):
    baseline_raw = bytes(8192)
    changed_raw = b"X" + baseline_raw[1:]
    old = {"raw": baseline_raw, "typed": typed(baseline_raw, 1),
           "catalog": b"catalog", "selector": b"selector"}
    postraw = {**old, "raw": changed_raw}
    recovered = {**postraw, "typed": typed(changed_raw, 2)}
    pre_bytes, post_bytes = {}, {}
    for stage in ("before", "actual-full", "cold1", "cold2"):
        for key, value in old.items():
            pre_bytes[f"{stage}.{key}.bin"] = value
    for stage, files in (("before", old), ("postraw", postraw),
                         ("denied", postraw), ("recovered", recovered),
                         ("cold2", recovered)):
        for key, value in files.items():
            post_bytes[f"{stage}.{key}.bin"] = value
    post_bytes["intent.postraw.bin"] = b"original intent"
    post_bytes["intent.recovery-receipt.bin"] = b"original intent"

    def manifest(files):
        return {key: {"bytes": len(value), "sha256": sha(value)}
                for key, value in files.items()}

    pre = {
        "result.json": {
            "exact_before_full_two_cold_binary_members": manifest(pre_bytes),
            "original_cmd_sha256": CMD,
            "actual_native_cmd_exit8_during_original_guest_save": True},
        "real-ntfs-substrate.json": {
            "tested_commit": SOURCE, "actual_ephemeral_ntfs_vhdx": True,
            "fresh_process_os_error": 112},
        "full-process.json": {
            "original_full_ntfs_cmd_sha256": CMD, "native_cmd_exit": 8,
            "real_ntfs_pre_intent_durable_allocation_refused": True},
        "candidate.json": {"cmd_sha256": CMD},
    }
    post = {
        "result.json": {
            "actual_source_bytes": manifest(post_bytes),
            "original_cmd_sha256": CMD,
            "two_fresh_original_Windows_cold_boots": True,
            "recovery_intent_reconciled_once": True},
        "full-postraw-result.json": {
            "native_exit": 8,
            "full_volume": {"first_process_real_ntfs_full": True,
                            "second_process_win32_error": 112}},
        "filler-exhaustion.json": {
            "guest_postraw_typed_failure_proven": False,
            "events": [{"python_errno": 28}]},
        "cold-1-original-CMD.log": "BOOT_SRAM RECOVERY_RECONCILED",
        "cold-2-original-CMD.log": "BOOT_SRAM",
    }

    def archive(path, fields, files):
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for key, value in fields.items():
                z.writestr(key, json.dumps(value) if isinstance(value, dict) else value)
            for key, value in files.items():
                z.writestr("source-bytes/" + key, value)
        return sha(path.read_bytes())

    pre_path, post_path = root / "pre.zip", root / "post.zip"
    return (pre_path, post_path, archive(pre_path, pre, pre_bytes),
            archive(post_path, post, post_bytes), pre, post,
            pre_bytes, post_bytes, archive)


class IndependentRealNTFSArchiveConsumerTests(unittest.TestCase):
    def test_synthetic_positive_and_adversarial_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            pre_path, post_path, pre_sha, post_sha, pre, post, pre_bytes, post_bytes, write = (
                scenario(Path(directory)))

            def pins(pre_hash, post_hash):
                return dict(pre_sha=pre_hash, post_sha=post_hash,
                            source_sha=SOURCE, cmd_sha=CMD)

            report = qa.inspect(pre_path, post_path, **pins(pre_sha, post_sha))
            self.assertEqual(report["raw_changed_positions"], 1)
            self.assertEqual(report["post_raw_exact_original_bytes"], 22)
            self.assertEqual(report["release_gate_credit"], 0)
            self.assertFalse(report["windows_original_process_executed_here"])

            with self.assertRaisesRegex(ValueError, "wrapper hash"):
                qa.inspect(pre_path, post_path, **pins("0" * 64, post_sha))

            damaged = copy.deepcopy(post)
            damaged["full-postraw-result.json"]["full_volume"]["second_process_win32_error"] = 0
            mutated_hash = write(post_path, damaged, post_bytes)
            with self.assertRaisesRegex(ValueError, "full volume"):
                qa.inspect(pre_path, post_path, **pins(pre_sha, mutated_hash))

            damaged = copy.deepcopy(post)
            mutated_files = copy.deepcopy(post_bytes)
            mutated_files["cold2.raw.bin"] = bytes(8192)
            damaged["result.json"]["actual_source_bytes"]["cold2.raw.bin"] = {
                "bytes": 8192, "sha256": sha(mutated_files["cold2.raw.bin"])}
            mutated_hash = write(post_path, damaged, mutated_files)
            with self.assertRaisesRegex(ValueError, "second cold restart"):
                qa.inspect(pre_path, post_path, **pins(pre_sha, mutated_hash))

            damaged = copy.deepcopy(post)
            damaged["result.json"]["original_cmd_sha256"] = "f" * 64
            mutated_hash = write(post_path, damaged, post_bytes)
            with self.assertRaisesRegex(ValueError, "binding conflict"):
                qa.inspect(pre_path, post_path, **pins(pre_sha, mutated_hash))

            post_sha = write(post_path, post, post_bytes)
            damaged = copy.deepcopy(pre)
            damaged["real-ntfs-substrate.json"]["tested_commit"] = "f" * 40
            mutated_hash = write(pre_path, damaged, pre_bytes)
            with self.assertRaisesRegex(ValueError, "binding conflict"):
                qa.inspect(pre_path, post_path, **pins(mutated_hash, post_sha))


if __name__ == "__main__":
    unittest.main()
