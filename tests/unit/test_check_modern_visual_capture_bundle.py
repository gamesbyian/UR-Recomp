"""Adversarial ROM-free tests for independent native visual evidence admission."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

SOURCE = Path(__file__).resolve().parents[2] / "tools/check_modern_visual_capture_bundle.py"
spec = importlib.util.spec_from_file_location("visual_capture_qa", SOURCE)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


def png(width=4, height=3, *, raw=None, compressed=None):
    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload +
                struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    pixels = (b"".join(b"\x00" + b"\xff\x21\x42\xff" * width for _ in range(height))
              if raw is None else raw)
    return (qa.PNG_SIG + chunk(b"IHDR", header) +
            chunk(b"IDAT", compressed if compressed is not None else zlib.compress(pixels)) + chunk(b"IEND", b""))


def sha(data):
    return hashlib.sha256(data).hexdigest()


class IndependentVisualBundleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = b"native PE simulated test fixture, not a release executable"
        self.root.joinpath("native.exe").write_bytes(self.binary)
        self.root.joinpath("capture.png").write_bytes(png())
        self.log = b"UR_BALDOSA_MODERN_ROOT opened=1\nsemantic pad P1 accepted\n"
        self.root.joinpath("route.log").write_bytes(self.log)
        self.row = {
            "id": "root", "screen": "root", "mode": "modern",
            "aspect": "4:3", "pixels": [4, 3], "input": "pad-p1",
            "state": "normal", "review_target": "semantic P1 cursor"
        }
        self.matrix = {"schema_version": 1, "cases": [self.row]}
        self.entry = {
            "case_id": "root", "screen": "root", "mode": "modern",
            "input": "pad-p1", "state": "normal",
            "source_sha": "a" * 40,
            "exe_sha256": sha(self.binary),
            "driver": "native-semantic-pad",
            "png": "capture.png", "png_sha256": sha(png()),
            "route_log": "route.log", "route_log_sha256": sha(self.log),
            "route_markers": ["UR_BALDOSA_MODERN_ROOT opened=1"]
        }
        self.bundle = {
            "schema_version": 1,
            "source_sha": "a" * 40,
            "exe_sha256": sha(self.binary),
            "executable": "native.exe",
            "capture_runtime": "native-sdl-final-output",
            "captures": [self.entry],
        }

    def run_audit(self):
        return qa.audit(self.matrix, self.bundle, self.root)

    def test_complete_structural_receipt_not_visual_signoff(self):
        result = self.run_audit()
        self.assertTrue(result["structurally_complete"])
        self.assertEqual(result["checked_structural"], ["root"])
        self.assertFalse(result["visual_approved"])
        self.assertFalse(result["hardware_approved"])
        self.assertFalse(result["authentic_isolation_approved"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_partial_bundle_never_reports_complete(self):
        self.bundle["captures"] = []
        self.assertEqual(self.run_audit()["missing_capture_cases"], ["root"])
        self.assertFalse(self.run_audit()["structurally_complete"])

    def test_png_crc_mutation_rejected_even_with_matching_file_sha(self):
        altered = bytearray(png())
        altered[19] ^= 4
        self.root.joinpath("capture.png").write_bytes(altered)
        self.entry["png_sha256"] = sha(altered)
        with self.assertRaisesRegex(qa.CaptureError, "CRC"):
            self.run_audit()

    def test_crc_valid_but_broken_compressed_raster_rejected(self):
        forged = png(compressed=b"bogus-compressed-data")
        self.root.joinpath("capture.png").write_bytes(forged)
        self.entry["png_sha256"] = sha(forged)
        with self.assertRaisesRegex(qa.CaptureError, "PNG image data"):
            self.run_audit()

    def test_crc_valid_but_invalid_filter_and_truncated_raster_rejected(self):
        scanline = b"\x00" + b"\x22\x33\x44\xff" * 4
        for raw, expected in [
            (b"\x05" + scanline[1:] + scanline * 2, "scanline filter"),
            (scanline, "invalid/truncated PNG image raster"),
        ]:
            with self.subTest(expected=expected):
                forged = png(raw=raw)
                self.root.joinpath("capture.png").write_bytes(forged)
                self.entry["png_sha256"] = sha(forged)
                with self.assertRaisesRegex(qa.CaptureError, expected):
                    self.run_audit()

    def test_wrong_dimensions_rejected(self):
        other = png(8, 6)
        self.root.joinpath("capture.png").write_bytes(other)
        self.entry["png_sha256"] = sha(other)
        with self.assertRaisesRegex(qa.CaptureError, "output size"):
            self.run_audit()

    def test_wrong_mode_and_input_owner_rejected(self):
        self.entry["mode"] = "authentic"
        with self.assertRaisesRegex(qa.CaptureError, "mismatched mode"):
            self.run_audit()
        self.entry["mode"] = "modern"
        self.entry["driver"] = "native-keyboard"
        with self.assertRaisesRegex(qa.CaptureError, "wrong native input"):
            self.run_audit()

    def test_undeclared_source_or_binary_mismatch_rejected(self):
        self.entry["source_sha"] = "f" * 40
        with self.assertRaisesRegex(qa.CaptureError, "source/executable changed"):
            self.run_audit()
        self.entry["source_sha"] = "a" * 40
        self.bundle["exe_sha256"] = "c" * 64
        with self.assertRaisesRegex(qa.CaptureError, "SHA256 mismatch"):
            self.run_audit()

    def test_duplicate_and_unknown_cases_rejected(self):
        self.bundle["captures"].append(copy.deepcopy(self.entry))
        with self.assertRaisesRegex(qa.CaptureError, "duplicate capture"):
            self.run_audit()
        self.bundle["captures"][1]["case_id"] = "fabricated-screen"
        with self.assertRaisesRegex(qa.CaptureError, "unknown"):
            self.run_audit()

    def test_path_traversal_and_symlink_rejected(self):
        self.entry["png"] = "../capture.png"
        with self.assertRaisesRegex(qa.CaptureError, "traversal"):
            self.run_audit()
        self.entry["png"] = "alias.png"
        self.root.joinpath("alias.png").symlink_to(self.root / "capture.png")
        with self.assertRaisesRegex(qa.CaptureError, "symlink"):
            self.run_audit()

    def test_log_missing_required_actual_marker_rejected(self):
        self.entry["route_markers"] = ["UR_BALDOSA_MODERN_ROOT records_earned"]
        with self.assertRaisesRegex(qa.CaptureError, "route marker"):
            self.run_audit()

    def test_fake_png_and_trailing_chunk_rejected(self):
        fake = png() + b"opaque-extra"
        self.root.joinpath("capture.png").write_bytes(fake)
        self.entry["png_sha256"] = sha(fake)
        with self.assertRaisesRegex(qa.CaptureError, "trailing PNG"):
            self.run_audit()

    def test_matrix_duplicate_or_invalid_aspect_rejected(self):
        self.matrix["cases"].append(copy.deepcopy(self.row))
        with self.assertRaisesRegex(qa.CaptureError, "duplicate matrix"):
            self.run_audit()
        self.matrix["cases"].pop()
        self.row["aspect"] = "16:9"
        with self.assertRaisesRegex(qa.CaptureError, "aspect/pixel"):
            self.run_audit()

    def test_bundle_receipt_does_not_accept_synthetic_or_mock_runtime(self):
        self.bundle["capture_runtime"] = "mock"
        with self.assertRaisesRegex(qa.CaptureError, "not native"):
            self.run_audit()

    def test_canonical_live_matrix_parses_and_covers_expected_families(self):
        data = json.loads(qa.MATRIX.read_text(encoding="utf-8"))
        entries = qa.read_matrix(data)
        self.assertGreaterEqual(len(entries), 20)
        self.assertIn("records-earned-2p", entries)
        self.assertIn("title-reduced-motion", entries)
        self.assertIn("authentic-title-stock", entries)
        self.assertIn("root-wide-4k-virtual", entries)
        self.assertIn("focus-loss-modal", entries)


if __name__ == "__main__":
    unittest.main()
