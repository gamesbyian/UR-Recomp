"""ROM-free fail-closed tests of six-artifact integrated native Win32 auditor.

Plausible test fixture PE files are deliberately SYNTHETIC; no unit fixture
is evidence of actual host-rendered gameplay, artist approval or hardware.
"""
from __future__ import annotations

from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import qa_modern_visual_actions_batch as qa


class IntegratedWindowsBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = "a"*40
        self.pe_zip = self.root / "real-in-test-only.zip"
        self.artifacts = {
            name:self.root / f"{name}.zip" for name in qa.EXPECTED
        }
        for file in self.artifacts.values():
            with zipfile.ZipFile(file,"w") as z:
                z.writestr("test-fixture",b"SYNTHETIC")
        native=bytearray(70000)
        native[:2]=b"MZ"
        struct.pack_into("<I",native,0x3c,0x80)
        native[0x80:0x84]=b"PE\0\0"
        struct.pack_into("<H",native,0x84,0x8664)
        struct.pack_into("<H",native,0x98,0x20b)
        with zipfile.ZipFile(self.pe_zip,"w") as z:
            z.writestr(qa.EXE_NAME,native)
        self.pe_sha,_=qa.native_exe_sha(self.pe_zip)

    def fake_verify(self,archive,expected_source_sha,expected_exe_sha):
        self.assertEqual(expected_source_sha,self.source)
        self.assertEqual(expected_exe_sha,self.pe_sha)
        role=next(k for k,v in self.artifacts.items() if v==archive)
        return {"captures":[{
            "id":name,"native_semantic_route":route,
            "verified_native_title_source":(
                {"title_source_stage":"title"} if role=="title" else None)}
            for name,route in qa.EXPECTED[role].items()]}

    def test_direct_script_help_from_clean_checkout(self):
        script = Path(__file__).resolve().parents[2] / "tools" / (
            "qa_modern_visual_actions_batch.py")
        r = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=script.parents[1], capture_output=True, text=True,
            timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("--native-executable",r.stdout)
        self.assertIn("--wide-destinations",r.stdout)

    def test_all_21_exact_route_receipts_same_source_and_pe(self):
        with patch.object(qa.capture,"verify",side_effect=self.fake_verify):
            report=qa.verify(self.artifacts,self.pe_zip,self.source,self.pe_sha)
        self.assertEqual(report["verified_exact_sdl_png_p7_native_route_cases"],21)
        self.assertEqual(report["title_source_FNV_witnesses"],5)
        self.assertTrue(report["complete_transport_and_source_provenance"])
        self.assertFalse(report["human_visual_approved"])
        self.assertFalse(report["hardware_approved"])
        self.assertEqual(report["release_gate_credit"],0)

    def test_missing_artifact_role_rejected_before_trusting_some_results(self):
        subset={k:v for k,v in self.artifacts.items() if k!="title"}
        with self.assertRaisesRegex(qa.BundleError,"six original"):
            qa.verify(subset,self.pe_zip,self.source)

    def test_capture_zip_reuse_refused_even_with_good_receipts(self):
        files=dict(self.artifacts)
        files["title"]=files["root"]
        with self.assertRaisesRegex(qa.BundleError,"paths cannot be reused"):
            qa.verify(files,self.pe_zip,self.source)

    def test_wrong_source_epoch_rejected_without_claiming_completion(self):
        with self.assertRaisesRegex(qa.BundleError,"40-character source"):
            qa.verify(self.artifacts,self.pe_zip,"old")

    def test_wrong_executable_digest_rejected_before_accepting_captures(self):
        with self.assertRaisesRegex(qa.BundleError,"required SHA256"):
            qa.verify(self.artifacts,self.pe_zip,self.source,"f"*64)

    def test_missing_native_PE_or_wrong_architecture_rejected(self):
        self.pe_zip.unlink()
        with self.assertRaisesRegex(qa.BundleError,"absent or redirected"):
            qa.verify(self.artifacts,self.pe_zip,self.source)
        native=bytearray(70000)
        native[:2]=b"MZ"
        struct.pack_into("<I",native,0x3c,0x80)
        native[0x80:0x84]=b"PE\0\0"
        struct.pack_into("<H",native,0x84,0x14c)
        struct.pack_into("<H",native,0x98,0x10b)
        with zipfile.ZipFile(self.pe_zip,"w") as z:
            z.writestr(qa.EXE_NAME,native)
        with self.assertRaisesRegex(qa.BundleError,"not Windows AMD64"):
            qa.verify(self.artifacts,self.pe_zip,self.source)

    def test_duplicate_or_absent_title_case_cannot_be_hidden_by_20_other_cases(self):
        def missing_title(archive,expected_source_sha,expected_exe_sha):
            data=self.fake_verify(archive,expected_source_sha,expected_exe_sha)
            if archive==self.artifacts["title"]:
                data["captures"].pop()
            return data
        with patch.object(qa.capture,"verify",side_effect=missing_title):
            with self.assertRaisesRegex(qa.BundleError,"missing/duplicate/extra"):
                qa.verify(self.artifacts,self.pe_zip,self.source)

    def test_route_label_forgery_rejected_even_when_case_name_matches(self):
        def wrong_route(archive,expected_source_sha,expected_exe_sha):
            data=self.fake_verify(archive,expected_source_sha,expected_exe_sha)
            if archive==self.artifacts["play"]:
                data["captures"][0]["native_semantic_route"]="root-quit"
            return data
        with patch.object(qa.capture,"verify",side_effect=wrong_route):
            with self.assertRaisesRegex(qa.BundleError,"wrong route"):
                qa.verify(self.artifacts,self.pe_zip,self.source)

    def test_new_unrelated_root_case_cannot_pad_expected_title_coverage(self):
        def extra_root(archive,expected_source_sha,expected_exe_sha):
            data=self.fake_verify(archive,expected_source_sha,expected_exe_sha)
            if archive==self.artifacts["root"]:
                data["captures"].append({
                    "id":"ur-modern-win32-random-root",
                    "native_semantic_route":"root-quit"})
            return data
        with patch.object(qa.capture,"verify",side_effect=extra_root):
            with self.assertRaisesRegex(qa.BundleError,"missing/duplicate/extra"):
                qa.verify(self.artifacts,self.pe_zip,self.source)


if __name__=="__main__":
    unittest.main()
