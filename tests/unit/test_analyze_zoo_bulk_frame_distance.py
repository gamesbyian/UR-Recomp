"""Full WRAM/VRAM/CGRAM Zoo time-neighbor diagnostic is not course acceptance."""
import io
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import analyze_zoo_bulk_frame_distance as fit


class BulkGuestDistanceTest(unittest.TestCase):
    def make_artifact(self, *, corrupt=False, missing_native=False):
        stream = io.BytesIO()
        zero = {k: bytes(n) for k, n in fit.FIELDS.items()}
        prep = {k: bytearray(n) for k, n in fit.FIELDS.items()}
        prep["wram"][0x9F] = 0x84
        restored = {k: bytearray(n) for k, n in fit.FIELDS.items()}
        restored["wram"][0x9F] = 0x16
        restored["wram"][0xCE] = 1
        with ZipFile(stream, "w", ZIP_DEFLATED) as z:
            for frame, fields in ((5155, zero), (5156, prep), (5157, restored)):
                for k, data in fields.items():
                    z.writestr(f"original-boundary/boundary-{frame:05d}.{k}.bin", data)
            if not missing_native:
                for k, data in restored.items():
                    z.writestr(f"native-boundary/dump/boundary-05156.{k}.bin",
                               data[:-1] if corrupt and k == "wram" else data)
        stream.seek(0)
        return stream

    def test_paired_exact_adjacent_memory_is_observation_not_instruction_time(self):
        with ZipFile(self.make_artifact()) as archive:
            report = fit.compare(archive, 5156, 5156, 1)
        self.assertEqual(report["rows"][0]["native_relative_frame"], 5156)
        best = report["rows"][0]["nearest_original_candidate"]
        self.assertEqual(best["original_relative_frame"], 5157)
        self.assertEqual(best["bytes_different"],
                         {"wram": 0, "vram": 0, "cgram": 0})
        self.assertEqual(report["rows"][0]["same_relative_frame"][
                         "bytes_different"]["wram"], 2)
        self.assertEqual(report["admission"]["release_usa_complete_courses_credited"], 0)
        self.assertEqual(report["admission"]["causal_claim"], "none")

    def test_exact_source_artifact_hashes_never_relabel_other_runs(self):
        old = fit.provenance(
            "f6a0ef06a856f16bfde3206cdcc86b752e831a9594a489484934d6c5388ef993",
            require_known=True)
        recent = fit.provenance(
            "d5ec65c672736fa45f01214134db8598baa840f106729bd2c04ffb8949f1d039",
            require_known=True)
        self.assertEqual((old["source_ci_run"], old["source_artifact_id"]),
                         (38018081196, 11656564258))
        self.assertEqual((recent["source_ci_run"], recent["source_artifact_id"]),
                         (38500427634, 11866136501))
        self.assertTrue(old["original_native_source_execution_identity_verified"])
        self.assertTrue(recent["original_native_source_execution_identity_verified"])
        self.assertEqual(recent["release_complete_event_qa_credit"], 0)

    def test_unknown_zip_cannot_inherit_original_native_execution_identity(self):
        import hashlib
        unverified_zip = self.make_artifact().getvalue()
        digest = hashlib.sha256(unverified_zip).hexdigest()
        self.assertNotIn(digest, fit.KNOWN_ARTIFACTS)
        obj = fit.provenance(digest)
        self.assertFalse(obj["original_native_source_execution_identity_verified"])
        self.assertIsNone(obj["source_ci_run"])
        self.assertIsNone(obj["source_artifact_id"])
        self.assertEqual(obj["artifact_zip_sha256"], digest)
        self.assertEqual(obj["release_complete_event_qa_credit"], 0)
        with self.assertRaisesRegex(ValueError, "unknown original/native source"):
            fit.provenance(digest, require_known=True)
        for invalid in ("unknown", digest.upper(), digest[:-1], digest + "0"):
            with self.subTest(invalid=invalid[:15]),self.assertRaisesRegex(
                    ValueError, "invalid complete artifact"):
                fit.provenance(invalid)

    def test_missing_or_corrupt_guest_dump_rejected(self):
        with ZipFile(self.make_artifact(corrupt=True)) as archive:
            with self.assertRaisesRegex(ValueError, "expected"):
                fit.compare(archive, 5156, 5156, 1)
        with ZipFile(self.make_artifact(missing_native=True)) as archive:
            with self.assertRaisesRegex(ValueError, "native missing"):
                fit.compare(archive, 5156, 5156, 1)
        with self.assertRaisesRegex(ValueError, "only original"):
            fit.compare(None, 5154, 5155)
        with self.assertRaisesRegex(ValueError, "only original"):
            fit.compare(None, 5155, 5156, 4)


if __name__ == "__main__":
    unittest.main()
