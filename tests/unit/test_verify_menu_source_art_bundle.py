"""Synthetic, no-ROM adversarial check of source menu PNG admission."""
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract_menu_visual_language as mvl  # noqa: E402
import verify_menu_source_art_bundle as verify  # noqa: E402


def pixel(img, width, x, y, rgba=(248, 240, 64, 255)):
    i = (y * width + x) * 4
    img[i:i + 4] = bytes(rgba)


def sample_art_files(directory):
    paths = {}
    for key, (width, height) in verify.EXPECTED.items():
        pixels = bytearray(width * height * 4)
        if key == "detail":
            pixel(pixels, width, 0, 0)  # first '0' cell
            pixel(pixels, width, 35 * 8, 0)  # O alias of first 0 cell
            pixel(pixels, width, 38 * 8, 0)  # '('
            pixel(pixels, width, 43 * 8 + 7, 0)  # ')' mirrored
        elif key == "cursor":
            for n in range(16):
                pixel(pixels, width, n * 39, 0)
        else:
            pixel(pixels, width, 0, 0)
        path = directory / (key + ".png")
        mvl.write_png(path, width, height, bytes(pixels))
        paths[key] = path
    return paths


def receipt_for(paths):
    return {
        "schema_version": 1,
        # Synthetic, explicitly non-original source digests prove only the
        # manifest's required shape. They must not grant ROM provenance.
        "source_fixture": mvl.SCRIPT,
        "source_main_tag": "mvl-idle-000",
        "source_detail_tag": "mvl-track-00",
        "source_ppu_sha256": {
            kind: hashlib.sha256(("synthetic-only:" + kind).encode()).hexdigest()
            for kind in verify.SOURCE_PPU_FIELDS
        },
        "reference_only": True,
        "asset_distribution_approved": False,
        "native_render_and_visual_acceptance": False,
        "asset_png_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in paths.items()
        },
        "output_dimensions": {
            name: list(dims) for name, dims in verify.EXPECTED.items()
        },
    }


class SourceArtBundleVerifierTest(unittest.TestCase):
    def test_valid_synthetic_four_source_sheets_and_failure_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = sample_art_files(Path(temp))
            receipt = receipt_for(paths)
            result = verify.verify_source_art_bundle(receipt, paths)
            self.assertTrue(result["source_bundle_verified"])
            self.assertTrue(result["reference_only"])
            self.assertFalse(result["distribution_approved"])
            self.assertFalse(result["final_native_capture_approved"])
            self.assertEqual(set(result["assets"]), set(verify.EXPECTED))
            self.assertEqual(result["assets"]["bg1"]["pixels"], 256 * 224)

    def test_hash_geometry_and_rights_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = sample_art_files(Path(temp))
            receipt = receipt_for(paths)
            bad = json.loads(json.dumps(receipt))
            bad["asset_distribution_approved"] = True
            with self.assertRaisesRegex(ValueError, "rights"):
                verify.verify_source_art_bundle(bad, paths)
            bad = json.loads(json.dumps(receipt))
            bad["output_dimensions"]["cursor"] = [623, 39]
            with self.assertRaisesRegex(ValueError, "dimensions"):
                verify.verify_source_art_bundle(bad, paths)
            data = paths["cursor"].read_bytes()
            paths["cursor"].write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
            with self.assertRaisesRegex(ValueError, "hash"):
                verify.verify_source_art_bundle(receipt, paths)

    def test_missing_or_forged_capture_receipt_must_fail_before_png_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = sample_art_files(Path(temp))
            receipt = receipt_for(paths)
            # Historical compatibility tests admitted all four PNGs even
            # when the entire source VRAM/CGRAM identity was absent.
            for missing in ("source_fixture", "source_main_tag",
                            "source_detail_tag", "source_ppu_sha256"):
                with self.subTest(missing=missing):
                    bad = json.loads(json.dumps(receipt))
                    del bad[missing]
                    with self.assertRaisesRegex(
                            ValueError, "source capture|source PPU"):
                        verify.verify_source_art_bundle(bad, paths)
            for tag, key in (("mvl-idle-002", "source_main_tag"),
                             ("unrelated.script", "source_fixture"),
                             ("mvl-track-evil", "source_detail_tag"),
                             (None, "source_detail_tag")):
                with self.subTest(tag=tag):
                    bad = json.loads(json.dumps(receipt))
                    bad[key] = tag
                    with self.assertRaisesRegex(ValueError, "source capture"):
                        verify.verify_source_art_bundle(bad, paths)
            for changed in ("main_vram", "main_cgram",
                            "detail_vram", "detail_cgram"):
                with self.subTest(ppu_digest=changed):
                    bad = json.loads(json.dumps(receipt))
                    bad["source_ppu_sha256"][changed] = "not-a-sha256"
                    with self.assertRaisesRegex(ValueError, "source PPU"):
                        verify.verify_source_art_bundle(bad, paths)
                    bad = json.loads(json.dumps(receipt))
                    del bad["source_ppu_sha256"][changed]
                    with self.assertRaisesRegex(ValueError, "source PPU"):
                        verify.verify_source_art_bundle(bad, paths)
            bad = json.loads(json.dumps(receipt))
            bad["source_ppu_sha256"]["main_vram"] = "A" * 64
            with self.assertRaisesRegex(ValueError, "source PPU"):
                verify.verify_source_art_bundle(bad, paths)
            bad = json.loads(json.dumps(receipt))
            bad["source_ppu_sha256"]["unexpected"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "source PPU"):
                verify.verify_source_art_bundle(bad, paths)
            # Complete source fields remain a claim, not permission to ship.
            good = verify.verify_source_art_bundle(receipt, paths)
            self.assertTrue(good["source_bundle_verified"])
            self.assertFalse(good["distribution_approved"])
            self.assertFalse(good["final_native_capture_approved"])

    def test_bad_png_crc_filter_and_trailing_bytes_refused_even_with_matching_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = sample_art_files(Path(temp))
            base = paths["heading"].read_bytes()
            for mutation in (base + b"x", base[:-1], b"bogus" + base[5:]):
                paths["heading"].write_bytes(mutation)
                receipt = receipt_for(paths)  # forged matching hash is not sufficient
                with self.assertRaises(ValueError):
                    verify.verify_source_art_bundle(receipt, paths)

            # Construct a valid-checksum PNG but an unsupported filter (1).
            rgba = bytearray(640 * 16 * 4)
            pixel(rgba, 640, 0, 0)
            import zlib
            index = base.index(b"IDAT")
            chunk_length = struct.unpack(">I", base[index - 4:index])[0]
            raw = bytearray(zlib.decompress(base[index + 4:index + 4 + chunk_length]))
            raw[0] = 1
            path = paths["heading"]
            mvl.write_png(path, 640, 16, bytes(rgba))
            # Rewrite first scanline byte while preserving valid PNG checksums.
            blob = bytearray(path.read_bytes())
            pos = blob.index(b"IDAT")
            compressed2 = zlib.compress(bytes(raw))
            def crc_chunk(kind, payload):
                return (struct.pack(">I", len(payload)) + kind + payload +
                        struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))
            hdr = blob[8:pos - 4]
            tail = blob[pos + 4 + chunk_length + 4:]
            path.write_bytes(blob[:8] + hdr + crc_chunk(b"IDAT", compressed2) + tail)
            with self.assertRaisesRegex(ValueError, "filter"):
                verify.verify_source_art_bundle(receipt_for(paths), paths)

    def test_small_glyph_reuse_and_cursor_phase_integrity(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = sample_art_files(Path(temp))
            small = bytearray(360 * 16 * 4)
            pixel(small, 360, 0, 0)
            pixel(small, 360, 35 * 8 + 1, 0)
            pixel(small, 360, 38 * 8, 0)
            pixel(small, 360, 43 * 8 + 7, 0)
            mvl.write_png(paths["detail"], 360, 16, bytes(small))
            with self.assertRaisesRegex(ValueError, "duplicated"):
                verify.verify_source_art_bundle(receipt_for(paths), paths)
            paths = sample_art_files(Path(temp))
            cursor = bytearray(624 * 39 * 4)
            for n in range(15):
                pixel(cursor, 624, n * 39, 0)
            mvl.write_png(paths["cursor"], 624, 39, bytes(cursor))
            with self.assertRaisesRegex(ValueError, "phase 15"):
                verify.verify_source_art_bundle(receipt_for(paths), paths)


if __name__ == "__main__":
    unittest.main()
