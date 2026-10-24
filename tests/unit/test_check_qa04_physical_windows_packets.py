"""Synthetic *structural* private Windows QA-04 packets; never actual hardware."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_qa04_physical_windows_packets as qa

SOURCE = "a" * 40
ZIP = "b" * 64
PE = "c" * 64
KINDS = tuple(sorted(qa.REQUIRED_PHYSICAL))


def make_packet(root: Path, key: str, *, environment: str = "physical",
                clean: bool = False) -> Path:
    place = root / key
    place.mkdir()
    physical = environment == "physical"
    attachments = []
    for kind in KINDS:
        value = ("synthetic-" + kind + "-" + key).encode("ascii")
        f = place / (kind + ".txt")
        f.write_bytes(value)
        attachments.append({
            "path": f.name, "sha256": hashlib.sha256(value).hexdigest(),
            "bytes": len(value), "kind": kind,
        })
    receipt = {
        "schema": "ur-windows-physical-witness/1",
        "layer": "L5",
        "source_commit": SOURCE,
        "artifact_sha256": ZIP,
        "tested_executable_sha256": PE,
        "zip_sha256_before_launch": ZIP,
        "zip_sha256_after_launch": ZIP,
        "pe_sha256_before_launch": PE,
        "pe_sha256_after_launch": PE,
        "package_unchanged_after_launch": True,
        "independent_review_completed": False,
        "operator_notes": "Synthetic fixture: not a real machine or operator",
        "hardware": {
            "setup_id": key,
            "environment": environment,
            "clean_environment": clean,
            "windows_version": "Windows 11 " + key,
            "gpu": "GPU " + key,
            "display": "screen " + key,
            "controller": "pair of pads " + key,
            "audio": "audio endpoint " + key,
            "physical_controller_observed": physical,
            "audible_output_observed": physical,
            "visible_display_observed": physical,
        },
        "attachments": attachments,
    }
    p = place / "witness.json"
    p.write_text(json.dumps(receipt), encoding="utf-8")
    return p


def change(path: Path, callback) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    callback(raw)
    path.write_text(json.dumps(raw), encoding="utf-8")


class WindowsPhysicalWitnessPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.paths = [make_packet(root, "pc1", clean=True),
                      make_packet(root, "pc2"),
                      make_packet(root, "pc3")]

    def review(self, paths=None) -> dict:
        return qa.audit(paths if paths is not None else self.paths,
                        source_sha=SOURCE, portable_zip_sha=ZIP,
                        executable_sha=PE)

    def test_synthetic_three_physical_and_one_clean_vm_two_physical(self):
        report = self.review()
        self.assertTrue(report["structural_three_setup_coverage"])
        self.assertEqual(report["release_gate_credit"], 0)
        self.assertFalse(report["independent_hardware_observation_certified_by_tool"])
        self.assertEqual(len(report["setups"]), 3)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = [make_packet(root, "pc1"),
                     make_packet(root, "pc2"),
                     make_packet(root, "vm3", environment="isolated-clean-vm",
                                 clean=True)]
            self.assertTrue(self.review(paths)["structural_three_setup_coverage"])

    def test_refuses_same_setup_and_two_clean_vms(self):
        with self.assertRaisesRegex(ValueError, "three separate packet"):
            self.review(self.paths[:2] + [self.paths[1]])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = [make_packet(root, "pc1"),
                     make_packet(root, "vm2", environment="isolated-clean-vm", clean=True),
                     make_packet(root, "vm3", environment="isolated-clean-vm", clean=True)]
            with self.assertRaisesRegex(ValueError, "not three dissimilar"):
                self.review(paths)

    def test_rejects_stale_zip_pe_or_tampered_attachments(self):
        for field, value in (("source_commit", "d" * 40),
                             ("artifact_sha256", "d" * 64),
                             ("tested_executable_sha256", "d" * 64),
                             ("zip_sha256_after_launch", "d" * 64),
                             ("package_unchanged_after_launch", False)):
            with self.subTest(field=field):
                old = self.paths[0].read_text(encoding="utf-8")
                try:
                    change(self.paths[0], lambda x: x.__setitem__(field, value))
                    with self.assertRaisesRegex(ValueError, "candidate|package"):
                        self.review()
                finally:
                    self.paths[0].write_text(old, encoding="utf-8")
        attachment = self.paths[1].parent / "audio-output.txt"
        attachment.write_bytes(b"tampered instead")
        with self.assertRaisesRegex(ValueError, "source bytes changed"):
            self.review()

    def test_refuses_synthetic_unobserved_devices_and_duplicate_machine_claim(self):
        original = self.paths[0].read_text(encoding="utf-8")
        try:
            change(self.paths[0], lambda x:
                   x["hardware"].__setitem__("physical_controller_observed", False))
            with self.assertRaisesRegex(ValueError, "has not observed"):
                self.review()
        finally:
            self.paths[0].write_text(original, encoding="utf-8")
        original2 = self.paths[1].read_text(encoding="utf-8")
        try:
            def same_machine(x):
                other = json.loads(self.paths[0].read_text(encoding="utf-8"))
                for field in ("gpu", "display", "controller"):
                    x["hardware"][field] = other["hardware"][field]
            change(self.paths[1], same_machine)
            with self.assertRaisesRegex(ValueError, "not three dissimilar"):
                self.review()
        finally:
            self.paths[1].write_text(original2, encoding="utf-8")

    def test_refuses_missing_screenshots_traversal_and_symlink(self):
        for poison in ({"kind": "audio-output"},
                       {"path": "../stolen.txt"},
                       {"path": "/var/tmp/stolen.txt"},
                       {"path": "evidence\\alternate.txt"}):
            with self.subTest(poison=poison):
                old = self.paths[2].read_text(encoding="utf-8")
                try:
                    def rewrite(x):
                        target = x["attachments"][0]
                        target.update(poison)
                        if poison.get("kind") == "audio-output":
                            x["attachments"] = [v for v in x["attachments"]
                                                if v["kind"] != "visible-display"]
                    change(self.paths[2], rewrite)
                    with self.assertRaises(ValueError):
                        self.review()
                finally:
                    self.paths[2].write_text(old, encoding="utf-8")
        f = self.paths[2].parent / "startup-log.txt"
        f.unlink()
        try:
            f.symlink_to(self.paths[0].parent / "startup-log.txt")
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaisesRegex(ValueError, "symlinked"):
            self.review()

    def test_rejects_copied_genuine_attachment_between_claimed_machines(self):
        # A compromised reporter can rewrite the SHA and file length. The
        # two supposedly independent setups must still not recycle evidence.
        source = self.paths[0].parent / "controller-p1.txt"
        target = self.paths[1].parent / "controller-p1.txt"
        data = source.read_bytes()
        target.write_bytes(data)
        def bind_copied_evidence(x):
            item = next(a for a in x["attachments"]
                        if a["kind"] == "controller-p1")
            item["sha256"] = hashlib.sha256(data).hexdigest()
            item["bytes"] = len(data)
        change(self.paths[1], bind_copied_evidence)
        with self.assertRaisesRegex(ValueError, "reused across independent"):
            self.review()

    def test_refuses_ambiguous_json_and_extra_private_machine_identifiers(self):
        old = self.paths[0].read_text(encoding="utf-8")
        try:
            # Python's normal JSON parser would silently take the last value.
            self.paths[0].write_text(
                old[:-1] + ', "source_commit": "' + SOURCE + '"}',
                encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                self.review()
        finally:
            self.paths[0].write_text(old, encoding="utf-8")
        try:
            change(self.paths[0], lambda x:
                   x["hardware"].__setitem__("device_serial", "private-serial"))
            with self.assertRaisesRegex(ValueError, "privacy-bounded"):
                self.review()
        finally:
            self.paths[0].write_text(old, encoding="utf-8")

    def test_refuses_claimed_two_pad_observation_without_p2_original(self):
        old = self.paths[0].read_text(encoding="utf-8")
        try:
            change(self.paths[0], lambda x:
                   x.__setitem__("attachments", [
                       a for a in x["attachments"] if a["kind"] != "controller-p2"
                   ]))
            with self.assertRaisesRegex(ValueError, "missing independent observations"):
                self.review()
        finally:
            self.paths[0].write_text(old, encoding="utf-8")

    def test_vm_must_be_clean_and_cannot_self_claim_physical_devices(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = [make_packet(root, "pc1"),
                     make_packet(root, "pc2"),
                     make_packet(root, "vm3", environment="isolated-clean-vm",
                                 clean=False)]
            with self.assertRaisesRegex(ValueError, "VM must be a clean installation"):
                self.review(paths)


    def test_refuses_hardlinked_receipt_before_parsing(self):
        """Reject receipt inode aliases even when contents appear valid."""
        receipt = self.paths[0]
        alias = receipt.with_name("witness-hardlink-alias.json")
        try:
            os.link(receipt, alias)
        except (OSError, NotImplementedError):
            self.skipTest("hardlink creation unavailable")
        try:
            with self.assertRaisesRegex(ValueError, "hardlinked receipt JSON"):
                qa.inspect_packet(receipt, commit=SOURCE, zip_sha=ZIP, pe_sha=PE)
            receipt.write_text("not-json", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hardlinked receipt JSON"):
                qa.inspect_packet(receipt, commit=SOURCE, zip_sha=ZIP, pe_sha=PE)
        finally:
            alias.unlink()

    def test_refuses_manufactured_release_claim_and_self_review(self):
        for key, val in (("release_gate_credit", 1),
                         ("physical_hardware_verified", True),
                         ("independent_review_completed", True)):
            with self.subTest(key=key):
                old = self.paths[0].read_text(encoding="utf-8")
                try:
                    change(self.paths[0], lambda x: x.__setitem__(key, val))
                    with self.assertRaisesRegex(ValueError, "self-admit|signoff"):
                        self.review()
                finally:
                    self.paths[0].write_text(old, encoding="utf-8")


class AttachmentReadBindingTests(unittest.TestCase):
    """The hashed attachment must be the object the path still names afterwards."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.packets = [make_packet(self.root, "pc1", clean=True),
                        make_packet(self.root, "pc2"),
                        make_packet(self.root, "pc3")]

    def review(self) -> dict:
        return qa.audit(self.packets, source_sha=SOURCE, portable_zip_sha=ZIP,
                        executable_sha=PE)

    def swap_after_open(self, swap) -> None:
        real_open = qa.os.open
        state = {"done": False}

        def hook(path, *args, **kwargs):
            fd = real_open(path, *args, **kwargs)
            if not state["done"] and Path(path).name == "startup-log.txt":
                state["done"] = True
                swap(Path(path))
            return fd

        with mock.patch.object(qa.os, "open", hook):
            self.review()

    def test_unmodified_packets_still_pass(self):
        self.assertTrue(self.review()["structural_three_setup_coverage"])

    def test_leaf_replaced_after_open_is_refused(self):
        def swap(path: Path) -> None:
            other = path.with_name("replacement.txt")
            other.write_bytes(path.read_bytes())
            os.replace(other, path)

        # The opened inode is unlinked (nlink 0) or the path identity differs.
        with self.assertRaisesRegex(ValueError, "changed"):
            self.swap_after_open(swap)

    def test_packet_directory_swapped_after_open_is_refused(self):
        def swap(path: Path) -> None:
            place = path.parent
            os.rename(place, place.with_name(place.name + "-moved"))
            place.mkdir()

        with self.assertRaisesRegex(ValueError, "changed while being read"):
            self.swap_after_open(swap)

    def test_growth_beyond_declared_size_is_refused(self):
        real_open = qa.os.open

        def hook(path, *args, **kwargs):
            if Path(path).name == "startup-log.txt":
                with open(path, "ab") as stream:
                    stream.write(b"x")
            return real_open(path, *args, **kwargs)

        with mock.patch.object(qa.os, "open", hook):
            with self.assertRaisesRegex(ValueError, "changed or oversized"):
                self.review()

    def test_leaf_symlink_is_not_followed(self):
        target = self.packets[1].parent / "startup-log.txt"
        leaf = self.packets[0].parent / "startup-log.txt"
        leaf.unlink()
        try:
            leaf.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(ValueError):
            self.review()


if __name__ == "__main__":
    unittest.main()
