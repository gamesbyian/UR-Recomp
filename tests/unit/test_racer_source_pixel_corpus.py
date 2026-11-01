"""Synthetic corruption controls and authentic retained-raster corpus checks."""
from __future__ import annotations

import json
import shutil
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.art.racer_source_pixels import decode_rgba_png, alpha_metrics
from tools.art.build_racer_source_pixel_corpus import build, STRIP, REGISTRY, _stock_path


def chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(
        ">I", zlib.crc32(kind + payload) & 0xffffffff
    )


def png_fixture(width=3, height=5, invalid_filter=False):
    """Create each of PNG's five filter types from known nontrivial pixels."""
    rows, expected, prior = [], bytearray(), bytes(width * 4)
    for y in range(height):
        raw = bytes(((x * 19 + y * 31 + 55) % 256 for x in range(width * 4)))
        filter_type = (y % 5) if not invalid_filter else 5
        filtered = bytearray()
        for i, value in enumerate(raw):
            left = raw[i-4] if i >= 4 else 0
            up = prior[i]
            upper_left = prior[i-4] if i >= 4 else 0
            if filter_type == 1:
                prediction = left
            elif filter_type == 2:
                prediction = up
            elif filter_type == 3:
                prediction = (left + up) // 2
            elif filter_type == 4:
                p = left + up - upper_left
                a, b, c = abs(p-left), abs(p-up), abs(p-upper_left)
                prediction = left if a <= b and a <= c else up if b <= c else upper_left
            else:
                prediction = 0
            filtered.append((value-prediction) & 255)
        rows.append(bytes([filter_type]) + filtered)
        expected.extend(raw)
        prior = raw
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) +
            chunk(b"IDAT", zlib.compress(b"".join(rows))) +
            chunk(b"IEND", b"")), bytes(expected)


class SourcePixelPngTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "fixture.png"

    def test_all_five_filters_decode_bit_for_bit(self):
        data, rgba = png_fixture()
        self.path.write_bytes(data)
        w, h, decoded, digest = decode_rgba_png(self.path)
        self.assertEqual((w, h, decoded), (3, 5, rgba))
        self.assertEqual(len(digest), 64)

    def test_png_crc_corruption_fails_closed(self):
        data, _ = png_fixture()
        changed = bytearray(data)
        changed[45] ^= 1
        self.path.write_bytes(changed)
        with self.assertRaisesRegex(ValueError, "CRC"):
            decode_rgba_png(self.path)

    def test_unsupported_filter_fails_closed(self):
        data, _ = png_fixture(invalid_filter=True)
        self.path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "filter"):
            decode_rgba_png(self.path)

    def test_trailing_png_bytes_rejected(self):
        data, _ = png_fixture()
        self.path.write_bytes(data + b"EXTRA")
        with self.assertRaisesRegex(ValueError, "trailing"):
            decode_rgba_png(self.path)

    def test_alpha_length_rejected(self):
        with self.assertRaisesRegex(ValueError, "raster"):
            alpha_metrics(bytes(7), 2, 2)

    def test_path_traversal_and_wrong_player_rejected(self):
        base = Path(self.tmp.name)
        for path in ("../stock/p1-00.png", "/etc/passwd", "stock/p2-00.png", "stock/../../secret.png"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "path"):
                _stock_path(base, path, "p1")


class OriginalReviewCorpusTests(unittest.TestCase):
    def test_retained_source_pixels_agree_with_exact_manifest_sha(self):
        report = build()
        self.assertTrue(report["decoded_png_rgba_sha_verified_against_review_manifest"])
        self.assertEqual(report["frame_observation_count"], 32)
        self.assertEqual(report["distinct_png_file_count"], 14)
        self.assertLess(report["distinct_rgba_pixel_groups"], 14)
        self.assertLessEqual(report["distinct_binary_silhouette_groups"], 14)
        self.assertFalse(report["source_rom_reextracted_in_this_run"])
        self.assertFalse(report["distinct_source_pose_family_holdout_verified"])
        self.assertFalse(report["shipping_art_approved"])

    def test_aliases_and_true_temporal_holds_are_not_new_poses(self):
        report = build()
        obs = {(x["player"], x["guest_frame"]): x for x in report["observations"]}
        self.assertEqual(obs["p1", 1217]["source_rgba_sha256"],
                         obs["p1", 1218]["source_rgba_sha256"])
        self.assertEqual(obs["p2", 1205]["source_rgba_sha256"],
                         obs["p2", 1207]["source_rgba_sha256"])
        edges = {(x["player"], x["to_frame"]): x for x in report["transitions"]}
        self.assertEqual(edges["p1", 1206]["source_rgba_changed_pixels"], 0)
        self.assertGreater(edges["p1", 1219]["source_rgba_changed_pixels"], 0)

    def test_tampered_manifest_pixel_hash_rejected(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            shutil.copytree(STRIP / "stock", root / "stock")
            for player in ("p1", "p2"):
                obj = json.loads((STRIP / ("inputs-" + player + ".json")).read_text())
                if player == "p1":
                    obj["frames"][0]["stock_rgba_sha256"] = "0" * 64
                (root / ("inputs-" + player + ".json")).write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, "disagree"):
                build(root, REGISTRY)

    def test_modified_original_file_rejected(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            shutil.copytree(STRIP / "stock", root / "stock")
            for player in ("p1", "p2"):
                shutil.copyfile(STRIP / ("inputs-" + player + ".json"),
                                root / ("inputs-" + player + ".json"))
            path = root / "stock/p1-00.png"
            raw = bytearray(path.read_bytes())
            raw[45] ^= 1
            path.write_bytes(raw)
            with self.assertRaises((ValueError, zlib.error)):
                build(root, REGISTRY)


if __name__ == "__main__":
    unittest.main()
