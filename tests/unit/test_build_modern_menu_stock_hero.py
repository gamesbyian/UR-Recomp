#!/usr/bin/env python3
"""Exact ROM-linked Original P1 racer clip export and fail-closed proof."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_modern_menu_stock_hero as hero


class StockHeroOriginalExtractionTest(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(hero.MANIFEST.read_text(encoding="utf-8"))
        self.source = json.loads(hero.SOURCE.read_text(encoding="utf-8"))

    def test_refuses_wrong_rom_and_unqualified_sequence(self):
        with self.assertRaisesRegex(ValueError, "canonical USA retail ROM"):
            hero.verified_clip(b"not the retail ROM", self.registry, self.source)
        with self.assertRaisesRegex(ValueError, "canonical USA retail ROM"):
            hero.verified_clip(bytes(2_097_152), self.registry, self.source)
        # Dependency injected only to reject the source-registration preflight:
        # no test fakes that noncanonical raster data is source-verified.
        if not hero.ROM.is_file():
            self.skipTest("canonical private ROM unavailable")
        rom = hero.ROM.read_bytes()
        bad = copy.deepcopy(self.registry)
        bad["motion_review_sequence"]["frames"] = bad["motion_review_sequence"]["frames"][:-1]
        with self.assertRaisesRegex(ValueError, "missing, duplicate"):
            hero.verified_clip(rom, bad, self.source)
        bad = copy.deepcopy(self.registry)
        original = bad["motion_review_sequence"]["frames"]
        original[-2]["frame"] = original[-1]["frame"]
        with self.assertRaisesRegex(ValueError, "missing, duplicate"):
            hero.verified_clip(rom, bad, self.source)
        bad = copy.deepcopy(self.registry)
        target = next(item for item in bad["entries"]
                      if item["representation_id"] ==
                      next(x for x in original if x["frame"] == 1213)["p1_representation_id"])
        target["palette_asset_id"] = "0x07"
        with self.assertRaisesRegex(ValueError, "unknown original P1"):
            hero.verified_clip(rom, bad, self.source)

    def test_private_source_outputs_are_new_and_checksum_preserving(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            header = root / "native-build" / "original.generated.hpp"
            manifest = root / "provenance" / "source.json"
            plate_dir = root / "source-plates"
            plates = [("original-stock-1213.png", b"original-synthetic-png"),
                      ("original-stock-1214.png", b"next-source-raster")]
            hero.publish_private_source_artifacts(
                b"source-qualified-cpp", b"source-qualified-json",
                plates, header, manifest, plate_dir)
            self.assertEqual(header.read_bytes(), b"source-qualified-cpp")
            self.assertEqual(manifest.read_bytes(), b"source-qualified-json")
            self.assertEqual(
                (plate_dir / "original-stock-1213.png").read_bytes(),
                b"original-synthetic-png")
            self.assertEqual(len(list(plate_dir.glob("*.png"))), 2)
            with self.assertRaisesRegex(ValueError, "refuse overwrite"):
                hero.publish_private_source_artifacts(
                    b"forged", b"forged", plates, header, manifest, plate_dir)
            self.assertEqual(header.read_bytes(), b"source-qualified-cpp")
            self.assertEqual(manifest.read_bytes(), b"source-qualified-json")
            self.assertEqual(list(root.glob("**/.original*staging*")), [])

    def test_refuse_symlink_collision_and_ambiguous_destinations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            h, m, plates = root / "hero.hpp", root / "receipt.json", root / "plates"
            with self.assertRaisesRegex(ValueError, "distinct destinations"):
                hero.publish_private_source_artifacts(
                    b"h", b"m", [], h, h, None)
            with self.assertRaisesRegex(ValueError, "inside new plates"):
                hero.publish_private_source_artifacts(
                    b"h", b"m", [], plates / "hero.hpp", m, plates)
            h.symlink_to(root / "missing-real-file")
            with self.assertRaisesRegex(ValueError, "refuse overwrite"):
                hero.publish_private_source_artifacts(
                    b"h", b"m", [], h, m, None)
            h.unlink()
            plates.symlink_to(root / "missing-art-folder", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "refuse overwrite"):
                hero.publish_private_source_artifacts(
                    b"h", b"m", [("original-stock-1213.png", b"fake")],
                    h, m, plates)
            plates.unlink()
            self.assertEqual(list(root.iterdir()), [])

    def test_reject_duplicate_and_path_escape_review_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            header, manifest, folder = (
                root / "head.hpp", root / "receipt.json", root / "frames")
            invalid = [
                [("original-stock-1213.png", b"one"),
                 ("original-stock-1213.png", b"two")],
                [("../original-stock-1213.png", b"escape")],
                [("original-stock-1213.png/../x.png", b"escape")],
                [("other-1213.png", b"unregistered")],
            ]
            for plates in invalid:
                with self.subTest(plates=plates), self.assertRaises(ValueError):
                    hero.publish_private_source_artifacts(
                        b"h", b"m", plates, header, manifest, folder)
                self.assertEqual(list(root.iterdir()), [])

    def test_fail_partial_publish_restores_absence_and_retry_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            header, manifest, folder = (
                root / "head.hpp", root / "receipt.json", root / "frames")
            plates = [("original-stock-1213.png", b"raster")]
            real_link = hero.os.link
            call_count = 0
            def fail_second_file(source, target):
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise OSError("simulated second publication fault")
                return real_link(source, target)
            with patch.object(hero.os, "link", side_effect=fail_second_file):
                with self.assertRaisesRegex(OSError, "simulated second"):
                    hero.publish_private_source_artifacts(
                        b"h", b"m", plates, header, manifest, folder)
            self.assertFalse(header.exists())
            self.assertFalse(manifest.exists())
            self.assertFalse(folder.exists())
            self.assertEqual(list(root.glob("**/.original*staging*")), [])
            hero.publish_private_source_artifacts(
                b"h", b"m", plates, header, manifest, folder)
            self.assertEqual(header.read_bytes(), b"h")
            self.assertEqual(manifest.read_bytes(), b"m")
            self.assertEqual((folder / plates[0][0]).read_bytes(), b"raster")

    def test_plate_publication_fault_removes_created_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            header, manifest, folder = (
                root / "hero.hpp", root / "receipt.json", root / "plates")
            plates = [("original-stock-1213.png", b"source-only-test")]
            genuine_link = hero.os.link
            calls = 0
            def interrupted_plate_link(source, target):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("simulated plate-publication failure")
                return genuine_link(source, target)
            with patch.object(hero.os, "link", side_effect=interrupted_plate_link):
                with self.assertRaisesRegex(OSError, "plate-publication"):
                    hero.publish_private_source_artifacts(
                        b"header", b"manifest", plates, header, manifest, folder)
            self.assertEqual(list(root.iterdir()), [])
            hero.publish_private_source_artifacts(
                b"header", b"manifest", plates, header, manifest, folder)
            self.assertEqual((folder / plates[0][0]).read_bytes(), plates[0][1])

    def test_concurrent_directory_claim_never_overwrites_user_art(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            header, manifest, folder = (
                root / "hero.hpp", root / "receipt.json", root / "plates")
            genuine_link = hero.os.link
            calls = 0
            def conflicting_creator(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    folder.mkdir()
                    (folder / "keep.txt").write_text("must survive", encoding="utf-8")
                return genuine_link(source, target)
            with patch.object(hero.os, "link", side_effect=conflicting_creator):
                with self.assertRaises(FileExistsError):
                    hero.publish_private_source_artifacts(
                        b"header", b"manifest",
                        [("original-stock-1213.png", b"clip")],
                        header, manifest, folder)
            self.assertFalse(header.exists())
            self.assertFalse(manifest.exists())
            self.assertEqual((folder / "keep.txt").read_text(), "must survive")
            self.assertEqual(list(folder.iterdir()), [folder / "keep.txt"])
            self.assertEqual(list(root.glob(".original-*")), [])

    def test_late_plate_failure_keeps_other_writers_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            h, m, folder = root / "hero.hpp", root / "manifest.json", root / "plates"
            plates = [("original-stock-1213.png", b"ours-a"),
                      ("original-stock-1214.png", b"ours-b")]
            real_link = hero.os.link
            calls = 0

            def late_failure(source, target):
                nonlocal calls
                calls += 1
                if calls == 4:  # after mkdir and first plate link
                    (folder / "other-writer.txt").write_bytes(b"preserve user evidence")
                    raise OSError("synthetic late plate publication fault")
                return real_link(source, target)

            with patch.object(hero.os, "link", side_effect=late_failure):
                with self.assertRaisesRegex(OSError, "late plate publication"):
                    hero.publish_private_source_artifacts(
                        b"header", b"receipt", plates, h, m, folder)
            self.assertFalse(h.exists())
            self.assertFalse(m.exists())
            self.assertEqual(sorted(p.name for p in folder.iterdir()),
                             ["other-writer.txt"])
            self.assertEqual((folder / "other-writer.txt").read_bytes(),
                             b"preserve user evidence")
            self.assertEqual(list(root.glob(".original-*")), [])

    def test_rollback_does_not_delete_replaced_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            h, m, folder = root / "hero.hpp", root / "manifest.json", root / "plates"
            real_link = hero.os.link
            calls = 0

            def replacement_then_failure(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    h.unlink()
                    h.write_bytes(b"a different writer owns this name")
                    raise OSError("synthetic manifest publication fault")
                return real_link(source, target)

            with patch.object(hero.os, "link", side_effect=replacement_then_failure):
                with self.assertRaisesRegex(OSError, "manifest publication"):
                    hero.publish_private_source_artifacts(
                        b"header", b"receipt", [], h, m, None)
            self.assertEqual(h.read_bytes(), b"a different writer owns this name")
            self.assertFalse(m.exists())
            self.assertFalse(folder.exists())
            self.assertEqual(list(root.glob(".original-*")), [])

    def test_original_raster_and_compiled_cpp_asset(self):
        if not hero.ROM.is_file():
            self.skipTest("canonical private ROM unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            header = out / "modern_menu_stock_hero_original.generated.hpp"
            manifest = out / "source-hero-manifest.json"
            pngs = out / "source-plates"
            result = hero.build(hero.ROM, header, manifest, pngs)
            self.assertEqual(len(list(pngs.glob("original-stock-*.png"))), 8)
            for row in result["frames"]:
                image = pngs / f"original-stock-{row['original_guest_frame']:04d}.png"
                raster = image.read_bytes()
                self.assertEqual(raster[:8], bytes.fromhex("89504e470d0a1a0a"))
                self.assertEqual(int.from_bytes(raster[16:20], "big"), 64)
                self.assertEqual(int.from_bytes(raster[20:24], "big"), 64)
                self.assertTrue(len(row["review_png_sha256"]) == 64)
            self.assertEqual(result["original_rom_sha256"],
                             self.source["rom_sha256"])
            self.assertEqual(len(result["frames"]), 8)
            self.assertEqual([x["original_guest_frame"] for x in result["frames"]],
                             list(range(1213, 1221)))
            self.assertEqual(result["sequence_contract"],
                             "one-shot original guest 60Hz P1 frames; never loop as if original idle")
            self.assertTrue(all(int(x["opaque_pixels"]) > 100
                                for x in result["frames"]))
            self.assertEqual(result, json.loads(manifest.read_text()))
            self.assertIn("constexpr ModernMenuStockHeroSequence kClip",
                          header.read_text())
            compiler = shutil.which("g++") or shutil.which("clang++")
            if not compiler:
                return
            source = out / "verify.cpp"
            source.write_text(
                '#include "modern_menu_stock_hero_original.generated.hpp"\n'
                '#include <cassert>\n'
                'int main() {\n'
                ' using namespace ur::product;\n'
                ' using namespace ur::product::modern_menu_source_hero;\n'
                ' assert(modern_menu_stock_hero_sequence_eligible(kClip));\n'
                ' assert(kFrames[0].semantic_frame_id == 0x057E);\n'
                ' assert(kFrames[7].semantic_frame_id == 0x0541);\n'
                ' return 0;\n'
                '}\n', encoding="utf-8")
            exe = out / "source-hero-native"
            compile_result = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(out), "-I",
                 str(ROOT / "native/product"), str(source), "-o", str(exe)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(compile_result.returncode, 0,
                             compile_result.stdout + compile_result.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 check=False)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)


if __name__ == "__main__":
    unittest.main()
