"""ROM-free synthetic H27 P7/PNG/log/receipt bundle admission tests."""
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests/unit"))
from qa06_h27_sdl_receipt_bundle import audit_receipt_bundle, _paths
from test_qa06_sdl_source_grid_audit import source_grid, surface


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))


def to_png(p7: bytes, width: int, height: int) -> bytes:
    header = p7.index(b"ENDHDR\n") + len(b"ENDHDR\n")
    raw = p7[header:]
    row = width * 4
    scan = b"".join(b"\x00" + raw[y * row:(y + 1) * row] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" +
            png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height,
                                             8, 6, 0, 0, 0)) +
            png_chunk(b"IDAT", zlib.compress(scan)) +
            png_chunk(b"IEND", b""))


def repack(files: dict[str, bytes]) -> bytes:
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as z:
        for name, value in files.items():
            z.writestr(name, value)
    return data.getvalue()


def fixture() -> dict[str, bytes]:
    result = {}
    with tempfile.TemporaryDirectory() as td:
        source = source_grid()
        for w, h in ((1024, 768), (1280, 720)):
            root = Path(td)
            path = root / f"{w}x{h}.pam"
            surface(path, w, h, source)
            p7 = path.read_bytes()
            png = to_png(p7, w, h)
            log = (f"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 "
                   f"guest_frame=40 output={w}x{h} "
                   "source=SDL_RenderReadPixels backend=sdl3\n").encode()
            receipt = {
                "actual_sdl_renderer_output": [w, h],
                "execution_mode": "modern", "SDL_driver": "windows",
                "native_process_exit": 0, "observed_in_draw": 40,
                "source_sha": "a" * 40, "exe_sha256": "b" * 64,
                "source_bound_by_independent_rebuild": False,
                "visual_approved": False, "hardware_approved": False,
                "release_gate_credit": 0,
                "p7_sha256": hashlib.sha256(p7).hexdigest(),
                "png_sha256": hashlib.sha256(png).hexdigest(),
                "native_process_log_sha256": hashlib.sha256(log).hexdigest(),
            }
            paths = _paths(w, h)
            result[paths["p7"]] = p7
            result[paths["png"]] = png
            result[paths["log"]] = log
            result[paths["receipt"]] = json.dumps(receipt).encode()
    return result


class ReceiptBoundH27(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = fixture()

    def check(self, files):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "h27.zip"
            path.write_bytes(repack(files))
            return audit_receipt_bundle(path)

    def change_receipt(self, files, w, h, key, value):
        paths = _paths(w, h)
        receipt = json.loads(files[paths["receipt"]])
        receipt[key] = value
        files[paths["receipt"]] = json.dumps(receipt).encode()

    def test_matching_source_and_qualified_receipts_do_not_award_acceptance(self):
        result = self.check(self.files)
        self.assertTrue(result["compact_wide_grid_identical"])
        self.assertEqual(result["checked_surfaces"], ["1024x768", "1280x720"])
        for key in ("source_bound_by_independent_rebuild",
                    "actual_native_execution_independently_proven",
                    "physical_device_approved", "visual_approved"):
            self.assertIs(result[key], False)
        self.assertEqual(result["release_gate_credit"], 0)

    def test_claimed_digest_or_hardware_approval_refused(self):
        files = self.files.copy()
        self.change_receipt(files, 1024, 768, "png_sha256", "0" * 64)
        with self.assertRaisesRegex(ValueError, "png digest"):
            self.check(files)
        files = self.files.copy()
        self.change_receipt(files, 1280, 720, "hardware_approved", True)
        with self.assertRaisesRegex(ValueError, "preapproved"):
            self.check(files)

    def test_recomputed_fake_capture_marker_refused(self):
        files = self.files.copy()
        paths = _paths(1280, 720)
        files[paths["log"]] = b"FAKE_" + files[paths["log"]]
        self.change_receipt(files, 1280, 720, "native_process_log_sha256",
                            hashlib.sha256(files[paths["log"]]).hexdigest())
        with self.assertRaisesRegex(ValueError, "spoofed"):
            self.check(files)

    def test_rehashed_png_with_changed_pixels_refused(self):
        files = self.files.copy()
        paths = _paths(1024, 768)
        src = bytearray(files[paths["p7"]])
        src[-1] ^= 1
        files[paths["png"]] = to_png(bytes(src), 1024, 768)
        self.change_receipt(files, 1024, 768, "png_sha256",
                            hashlib.sha256(files[paths["png"]]).hexdigest())
        with self.assertRaisesRegex(ValueError, "PNG disagree"):
            self.check(files)

    def test_same_source_epoch_required(self):
        files = self.files.copy()
        self.change_receipt(files, 1280, 720, "source_sha", "c" * 40)
        with self.assertRaisesRegex(ValueError, "source identity"):
            self.check(files)

    def test_extra_member_not_admitted(self):
        files = self.files.copy()
        files["unexpected/member.bin"] = b"not original source"
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.check(files)


if __name__ == "__main__":
    unittest.main()
