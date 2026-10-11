"""ROM-free, independently pinned provisional Baldosa consumer archive QA."""
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import assemble_baldosa_windows_candidate as producer
import verify_baldosa_romless_candidate_qa as qa
from tests.unit.test_assemble_baldosa_windows_candidate import fake_x64_pe


def resigned(path, modify):
    with zipfile.ZipFile(path) as source:
        originals = [(item, source.read(item.filename)) for item in source.infolist()]
    with zipfile.ZipFile(path, "w") as dest:
        for entry, data in originals:
            dest.writestr(entry, modify(entry.filename, data))


class IndependentBaldosaZipQaTests(unittest.TestCase):
    def make(self, root):
        exe = root / producer.EXE
        fake_x64_pe(exe)
        zip_path = root / "provisional.zip"
        source = "a" * 40
        digest = producer.create_candidate(exe, zip_path, source)
        return zip_path, source, digest

    def test_real_candidate_historical_receipt_is_romfree_inconclusive(self):
        from evidence_contract import validate_envelope
        evidence = ROOT / "analysis/evidence/baldosa-romless-windows-38118756830-consistency.json"
        report = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(validate_envelope(report), [])
        self.assertEqual(report["outcome"], "inconclusive")
        self.assertEqual(report["subject"]["backend"], "baldosa-aot-provisional")
        self.assertEqual(report["subject"]["candidate_merge_commit"],
                         "8f7767444157b49a02b4b502cae01f300e57cda8")
        self.assertEqual(report["subject"]["producing_pr_head"],
                         "d20cd31ef86131dd12e611f41956e0106703eddf")
        self.assertEqual(report["provenance"]["checkout_merge_second_parent"],
                         report["subject"]["producing_pr_head"])
        self.assertFalse(report["metrics"]["rom_bundled"])
        self.assertFalse(report["metrics"]["integrated_fresh_process_1p_2p_records_verified"])
        self.assertFalse(report["metrics"]["physical_windows_controller_audio_display_verified"])

    def test_native_runtime_archive_matches_provisional_executable_only(self):
        from evidence_contract import validate_envelope
        path = ROOT / "analysis/evidence/baldosa-windows-38118756830-runtime-correlation.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_envelope(report), [])
        self.assertEqual(report["outcome"], "inconclusive")
        self.assertEqual(report["subject"]["backend"], "baldosa-aot-provisional")
        self.assertEqual(report["subject"]["win32_executable_sha256"],
                         "29982231bd85dacdb5058c65ccc87deec4e1641603e95dd5d6fb9a37c0c8a439")
        self.assertEqual(report["subject"]["inner_candidate_zip_sha256"],
                         "5bb9f872fd0e97b5f99fc50d41bb7ee9a04ab00752e7745dbb6bbc5d7f593a78")
        self.assertEqual(report["metrics"]["guest_course_complete_credit"], 0)
        self.assertEqual(report["metrics"]["source_settled_native_2p_result_publications"], 0)
        self.assertFalse(report["metrics"]["physical_controller_coverage"])
        self.assertFalse(report["metrics"]["fresh_process_native_1p_2p_results_records_verified"])

    def test_canonical_unexecuted_candidate_is_only_inconclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            result = qa.audit(archive, source, digest)
            self.assertEqual(result["outcome"], "inconclusive")
            self.assertEqual(result["subject"]["backend"], "baldosa-aot-provisional")
            self.assertFalse(result["metrics"]["integrated_native_1p_2p_journey_verified"])
            self.assertFalse(result["metrics"]["physical_windows_verified"])

    def test_pins_are_full_and_mismatches_reject_before_zip_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            for badsource, baddigest in (("main", digest), ("A" * 40, digest),
                                          (source, "0" * 64), (source, "xx")):
                with self.subTest(source=badsource, digest=baddigest):
                    with self.assertRaisesRegex(ValueError, "nominated"):
                        qa.audit(archive, badsource, baddigest)
            with self.assertRaisesRegex(ValueError, "source mismatched"):
                qa.audit(archive, "b" * 40, digest)

    def test_forced_recomputed_digest_cannot_hide_mutated_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            def change(name, value):
                if name.endswith(producer.LAUNCHER):
                    return value.replace(b"setlocal DisableDelayedExpansion",
                                         b"setlocal EnableDelayedExpansion")
                return value
            resigned(archive, change)
            revised = qa.file_digest(archive)
            with self.assertRaisesRegex(ValueError, "digest or size mismatch"):
                qa.audit(archive, source, revised)

    def test_resigned_and_manifest_rehashed_wrong_launcher_still_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            original = {}
            with zipfile.ZipFile(archive) as z:
                original = {name: z.read(name) for name in z.namelist()}
            mutated = producer.launcher().replace(
                b"setlocal DisableDelayedExpansion",
                b"setlocal EnableDelayedExpansion")
            manifest = json.loads(original[producer.PREFIX + producer.MANIFEST])
            for entry in manifest["immutable_files"]:
                if entry["path"] == producer.LAUNCHER:
                    entry["bytes"] = len(mutated)
                    entry["sha256"] = hashlib.sha256(mutated).hexdigest()
            new_manifest = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
            def change(name, data):
                if name.endswith(producer.MANIFEST):
                    return new_manifest
                if name.endswith(producer.LAUNCHER):
                    return mutated
                return data
            resigned(archive, change)
            with self.assertRaisesRegex(ValueError, "canonical source policy"):
                qa.audit(archive, source, qa.file_digest(archive))

    def test_extra_or_duplicate_archive_member_refused_even_with_new_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            with zipfile.ZipFile(archive, "a") as z:
                z.writestr(producer.PREFIX + "Uniracers_USA.sfc", b"do not ship")
            with self.assertRaisesRegex(ValueError, "extra, missing"):
                qa.audit(archive, source, qa.file_digest(archive))
            archive.unlink()
            archive, source, digest = self.make(Path(tmp))
            with zipfile.ZipFile(archive, "a") as z:
                z.writestr(producer.PREFIX + producer.EXE, b"duplicate")
            with self.assertRaisesRegex(ValueError, "extra, missing"):
                qa.audit(archive, source, qa.file_digest(archive))

    def test_symlinked_archive_and_noncandidate_zip_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, source, digest = self.make(root)
            linked = root / "aliased.zip"
            try:
                linked.symlink_to(archive)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "symlink"):
                qa.audit(linked, source, digest)


if __name__ == "__main__":
    unittest.main()
