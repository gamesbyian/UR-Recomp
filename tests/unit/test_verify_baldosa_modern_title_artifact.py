"""ROM-free adverse archive proof: exact bytes, not Windows newline assumptions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from tools.probe_baldosa_modern_title_attract_win32 import persist_exact_native_log
from tools.verify_baldosa_modern_title_artifact import audit_title_archive


class ExactRetainedTitleEvidenceTests(unittest.TestCase):
    def make_bundle(self, root: Path, *, crlf: bool = False, drop_root: bool = False,
                    preview: bool = True, named: bool = False,
                    drop_bootstrap: bool = False) -> Path:
        archive = root / "evidence.zip"
        folder = "modern-title-native-attract-recovery-pr2043"
        log = b"real native guest source\nwake consumed\n"
        bytes_retained = log.replace(b"\n", b"\r\n") if crlf else log
        images = []
        entries = {folder + "/native-attract.log": bytes_retained}
        boot = b"real native P1 racer created through X/A\n"
        if named and not drop_bootstrap:
            entries[folder + "/native-profile-bootstrap.log"] = boot
        if preview:
            for stage, width in (("original-demo", 256), ("restored-title", 342),
                                 ("root", 342)):
                photo = b"P6\n%d 224\n255\n" % width + bytes([17]) * (width * 224 * 3)
                name = "native-" + stage + ".ppm"
                if stage != "root" or not drop_root:
                    entries[folder + "/presented/" + name] = photo
                images.append({
                    "stage": stage, "guest_frame": {"original-demo": 1584,
                    "restored-title": 1616, "root": 1696}[stage],
                    "width": width, "height": 224,
                    "sha256": hashlib.sha256(photo).hexdigest(),
                    "file": name,
                })
        receipt = {
            "schema_version": 1,
            "candidate_executable_sha256": "a" * 64,
            "log_sha256": hashlib.sha256(log).hexdigest(),
            "native_stock_demo_and_wake_presentations": images,
            "scripted_host_preview_only": preview, "drawable_aspect": "wide",
            "real_guest_main_recovery_verified": preview,
            "named_source_play_verified": named,
            "genuine_native_profile_bootstrap_sha256": (
                hashlib.sha256(boot).hexdigest() if named else None),
            "final_sdl_capture": False, "release_gate_credit": 0,
        }
        entries[folder + "/native-attract-receipt.json"] = (
            json.dumps(receipt) + "\n").encode()
        with ZipFile(archive, "w") as dest:
            for name, data in entries.items():
                dest.writestr(name, data)
        return archive

    def test_exact_utf8_log_write_is_independent_of_windows_text_newlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "native-attract.log"
            for content in ("original\nwake\n", "original\r\nwake\n"):
                digest = persist_exact_native_log(path, content)
                self.assertEqual(path.read_bytes(), content.encode("utf-8"))
                self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_complete_preview_is_independently_auditable(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = audit_title_archive(self.make_bundle(Path(tmp)))
            self.assertEqual(result["scenario_count"], 1)
            self.assertEqual(result["native_presented_images_verified"], 3)
            self.assertFalse(result["final_sdl_capture_approved"])
            self.assertEqual(result["release_gate_credit"], 0)

    def test_source_only_case_has_no_photographs(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = audit_title_archive(self.make_bundle(Path(tmp), preview=False))
            self.assertEqual(result["native_presented_images_verified"], 0)

    def test_named_profile_must_keep_actual_first_process_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                audit_title_archive(self.make_bundle(root, named=True))[
                    "native_presented_images_verified"], 3)
            with self.assertRaisesRegex(ValueError, "profile-bootstrap bytes"):
                audit_title_archive(self.make_bundle(root, named=True,
                                                     drop_bootstrap=True))

    def test_rejects_old_windows_crlf_sha_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "byte SHA256 mismatch"):
                audit_title_archive(self.make_bundle(Path(tmp), crlf=True))

    def test_rejects_missing_recovery_stage_from_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "evidence absent"):
                audit_title_archive(self.make_bundle(Path(tmp), drop_root=True))


if __name__ == "__main__":
    unittest.main()
