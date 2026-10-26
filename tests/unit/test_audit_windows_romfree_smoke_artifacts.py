"""Synthetic-byte tests; never package or fetch a real ROM/private ZIP."""
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from tools import audit_windows_romfree_smoke_artifacts as m

SOURCE = "a" * 40
PRIVATE = "b" * 64

def sha(x):
    return hashlib.sha256(x).hexdigest()

def fixture(path, *, stamp=0, rom=False, corrupt=False, source=SOURCE, state=False):
    exe = bytearray(512)
    exe[:2] = b"MZ"
    struct.pack_into("<I", exe, 0x3c, 0x80)
    exe[0x80:0x84] = b"PE\x00\x00"
    struct.pack_into("<H", exe, 0x84, 0x8664)
    struct.pack_into("<I", exe, 0x88, stamp)
    struct.pack_into("<H", exe, 0x98, 0x20b)
    pe = bytes(exe)
    manifest = json.dumps({"source_revision": source, "files": [
        {"path": "UniracersSNESRecomp.exe", "size": len(pe),
         "sha256": sha(pe)}]}).encode()
    receipt = {
        "schema": "ur-windows-smoke-romfree-pe-binding/1",
        "source_commit": source,
        "original_portable_zip_sha256": PRIVATE,
        "original_manifest_sha256": sha(manifest),
        "executable_sha256": sha(pe) if not corrupt else "c"*64,
        "executable_bytes": len(pe), "release_gate_credit": 0,
        "physical_windows_accepted": False, "original_zip_uploaded": False,
        "rom_or_player_data_uploaded": False,
    }
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as z:
        z.writestr(m.EXE, pe)
        z.writestr(m.BINDING, json.dumps(receipt))
        z.writestr(m.MANIFEST, manifest)
        z.writestr(m.SIDECAR, PRIVATE + "  UR-Recomp-Windows-x64.zip\n")
        if rom:
            z.writestr("private/Uniracers_USA.sfc", b"NEVER ACCEPT")
        if state:
            z.writestr("boot-dumps/boot.sram.bin", bytes(8192))
    return pe

class WindowsRomfreeAuditTests(unittest.TestCase):
    def test_two_synthetic_builds_timestamp_and_privacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp)/"a.zip"
            b = Path(tmp)/"b.zip"
            fixture(a, stamp=1, state=True)
            fixture(b, stamp=2)
            report = m.compare([a,b], expected_source=SOURCE, expected_zip=PRIVATE)
            self.assertEqual(report["release_gate_credit"], 0)
            self.assertEqual(report["pairwise"][0]["different_byte_count"], 1)
            self.assertTrue(report["pairwise"][0]["only_coff_timestamp_bytes_differ"])
            self.assertFalse(report["all_exe_sha256_identical"])
            self.assertTrue(report["all_private_zip_sha256_claims_identical"])
            self.assertTrue(report["upload_privacy_review_required"])
            self.assertTrue(report["source_matches_expected"])

    def test_wrong_content_and_rom_members_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            for variant in ("rom", "corrupt"):
                with self.subTest(variant=variant):
                    p = Path(tmp)/(variant + ".zip")
                    fixture(p, rom=variant=="rom", corrupt=variant=="corrupt")
                    with self.assertRaises(ValueError):
                        m.audit(p)

    def test_corrupted_unrelated_diagnostic_member_fails_whole_archive_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "screenshot-diagnostic.zip"
            fixture(path)
            marker = b"UNIQUE_DIAGNOSTIC_PAYLOAD_DO_NOT_PRINT"
            with ZipFile(path, "a") as archive:
                archive.writestr("screenshots/diagnostic.txt", marker,
                                 compress_type=ZIP_STORED)
            # The four source-binding files remain valid, but another
            # archive member is corrupt. Auditing only named members would
            # have incorrectly accepted this ZIP.
            raw = path.read_bytes()
            self.assertEqual(raw.count(marker), 1)
            path.write_bytes(raw.replace(marker, b"X" + marker[1:]))
            with self.assertRaisesRegex(ValueError, "CRC"):
                m.audit(path)

    def test_source_is_claim_not_authenticated(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"a.zip"
            fixture(p)
            report=m.compare([p], expected_source="c"*40)
            self.assertIs(report["source_matches_expected"], False)
            self.assertIn("producer-supplied", " ".join(report["limits"]))
            self.assertIsNone(m.compare([p])["source_matches_expected"])

    def test_bad_expected_source_and_wrong_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"a.zip"
            fixture(p)
            with self.assertRaises(ValueError):
                m.compare([p], expected_source="main")
            with self.assertRaises(ValueError):
                m.compare([p], expected_zip="wrong")

    def test_rejects_duplicate_alias_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"a.zip"
            fixture(p)
            with ZipFile(p, "a") as z:
                z.writestr(m.EXE.upper(), b"alias")
            with self.assertRaisesRegex(ValueError, "alias"):
                m.audit(p)

    def test_rejects_hidden_zip_prefix_using_shared_transport_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"a.zip"
            fixture(p)
            original = p.read_bytes()
            # zipfile can often read a self-extracting prefix by adjusting
            # central offsets; the repository's canonical transport reader
            # must reject unindexed bytes before auditing published receipts.
            p.write_bytes(b"NOT_A_CANONICAL_ZIP" + original)
            with self.assertRaisesRegex(ValueError, "noncanonical transport"):
                m.audit(p)

    def test_rejects_more_than_eight_for_bounded_work(self):
        with self.assertRaisesRegex(ValueError, "eight"):
            m.compare([Path("missing.zip")] * 9)


if __name__ == "__main__":
    unittest.main()
