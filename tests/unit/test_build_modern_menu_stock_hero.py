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

    def test_registered_long_source_windows_emit_exact_cpp_lengths(self):
        self.assertEqual(hero.CLIP_WINDOWS, {
            "root-entry-reaction": (1213, 1220),
            "settle-and-recover": (1230, 1239),
            "long-hold-recovery": (1244, 1252),
        })
        for clip_id, (start, stop) in hero.CLIP_WINDOWS.items():
            with self.subTest(clip_id=clip_id):
                frames = [[0xff050500 + n] * hero.WIDTH * hero.HEIGHT
                          for n in range(stop - start + 1)]
                rows = [
                    {"original_guest_frame": start + n,
                     "semantic_frame_id": "0x0541",
                     "argb_fnv1a64": f"{hero.source_digest(frame):016x}"}
                    for n, frame in enumerate(frames)
                ]
                header = hero.cpp_header(rows, frames)
                count = len(rows)
                self.assertIn(
                    f"std::array<std::uint32_t, {4096 * count}> kOriginalArgb",
                    header)
                self.assertIn(
                    f"std::array<ModernMenuStockHeroFrame, {count}> kFrames",
                    header)
                self.assertIn(f"original guest frame {stop}", header)
                self.assertIn("kFrames.data(), kFrames.size(), true", header)
                self.assertEqual(header.count("original guest frame"), count)
                metrics = hero.original_temporal_evidence(rows, frames)
                self.assertEqual(metrics["frame_count"], count)
                self.assertEqual(metrics["first_registered_guest_frame"], start)
                self.assertEqual(metrics["last_registered_guest_frame"], stop)
                self.assertEqual(len(metrics["consecutive_registered_edges"]),
                                 count - 1)
                seam = metrics["counterfactual_last_to_first_edge"]
                self.assertEqual(seam["from_registered_guest_frame"], stop)
                self.assertEqual(seam["to_registered_guest_frame"], start)
                self.assertFalse(seam["is_observed_chronological_edge"])
                self.assertFalse(metrics["loop_certified"])
                self.assertFalse(
                    metrics["source_guest_timing_independently_certified"])
                bad = copy.deepcopy(rows)
                bad[-1]["original_guest_frame"] = start
                with self.assertRaisesRegex(ValueError, "registered window"):
                    hero.cpp_header(bad, frames)
        with self.assertRaisesRegex(ValueError, "incomplete source"):
            hero.cpp_header(rows, frames[:-1])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "unregistered original"):
                hero.build(root / "unavailable.rom", root / "x.hpp",
                           root / "x.json", clip_id="invented-id")

    def test_generated_registered_long_clip_compiles_into_real_native_compositor(self):
        """No private ROM required: synthetic pixels, real generated header ABI."""
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        for clip_id in ("long-hold-recovery", "settle-and-recover"):
            with self.subTest(clip_id=clip_id), tempfile.TemporaryDirectory() as tmp:
                start, stop = hero.CLIP_WINDOWS[clip_id]
                count = stop - start + 1
                rows, frames = [], []
                for i in range(count):
                    pixels = [0xff050500 + i] * hero.WIDTH * hero.HEIGHT
                    frames.append(pixels)
                    rows.append({
                        "original_guest_frame": start + i,
                        "semantic_frame_id": "0x0541",
                        "argb_fnv1a64": f"{hero.source_digest(pixels):016x}",
                    })
                out = Path(tmp)
                (out / "original.generated.hpp").write_text(
                    hero.cpp_header(rows, frames), encoding="utf-8")
                (out / "main.cpp").write_text(
                    '#include "original.generated.hpp"\n'
                    '#include <algorithm>\n'
                    '#include <cassert>\n'
                    '#include <cstdint>\n'
                    '#include <vector>\n'
                    'int main() {\n'
                    ' using namespace ur::product;\n'
                    ' using namespace ur::product::modern_menu_source_hero;\n'
                    f' assert(kClip.frame_count == {count});\n'
                    ' assert(modern_menu_stock_hero_sequence_eligible(kClip));\n'
                    ' for (int width : {256, 342}) {\n'
                    '  std::vector<std::uint32_t> dst(width * 224, 0xff101010u);\n'
                    '  ModernMenuMotionState state{};\n'
                    f'  for (int tick = 0; tick < {count + 3}; ++tick) {{\n'
                    '   auto pose = advance_modern_menu_motion(state,\n'
                    f'      {{static_cast<std::uint64_t>(tick), 0, true, false, {count}}});\n'
                    f'   const int expected = tick < {count} ? tick : {count - 1};\n'
                    '   assert(pose.hero_frame_ordinal == expected);\n'
                    '   pose.hero_bob_px = 0; pose.hero_lean_px = 0;\n'
                    '   std::fill(dst.begin(), dst.end(), 0xff101010u);\n'
                    '   assert(paint_modern_menu_stock_hero(\n'
                    '      dst.data(), width, 224, {0, 0, width, 224},\n'
                    '      {60, 20, 2}, kClip, pose) == ModernMenuStockHeroDraw::Drawn);\n'
                    '   assert(dst[84 * width + 124] ==\n'
                    '      (0xff050500u + static_cast<std::uint32_t>(expected)));\n'
                    '   assert(dst[0] == 0xff101010u);\n'
                    '  }\n'
                    ' }\n'
                    ' return 0;\n'
                    '}\n',
                    encoding="utf-8")
                exe = out / "native-long-clip"
                build = subprocess.run(
                    [compiler, "-std=c++17", "-O0", "-Wall", "-Wextra",
                     "-Werror", "-pedantic", "-I", str(out),
                     "-I", str(ROOT / "native/product"),
                     str(out / "main.cpp"), "-o", str(exe)],
                    text=True, capture_output=True, check=False)
                self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
                run = subprocess.run(
                    [str(exe)], text=True, capture_output=True, check=False)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_private_original_asset_paths_never_escape_into_tracked_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            external = Path(tmp)
            fake_rom = external / "missing-rom.sfc"
            allowed = ROOT / "native/product/modern_menu_stock_hero_original.generated.hpp"
            # Exact ignored native header is allowed; the canonical ROM
            # validation remains a separate fail-closed producer gate.
            hero.require_private_artifact_paths(
                allowed, external / "receipt.json", external / "plates")
            for header, manifest, plates in (
                (ROOT / "native/product/private-new-art.hpp",
                 external / "receipt.json", None),
                (external / "hero.hpp",
                 ROOT / "analysis/private-hero-manifest.json", None),
                (external / "hero.hpp", external / "receipt.json",
                 ROOT / "analysis/private-hero-plates"),
                (ROOT, external / "receipt.json", None),
            ):
                with self.subTest(header=header, manifest=manifest, plates=plates):
                    with self.assertRaisesRegex(ValueError, "tracked source"):
                        hero.require_private_artifact_paths(
                            header, manifest, plates)
            with self.assertRaisesRegex(ValueError, "tracked source"):
                hero.build(fake_rom, external / "hero.hpp",
                           ROOT / "analysis/accident.json")
            self.assertFalse((ROOT / "analysis/accident.json").exists())
            self.assertFalse((external / "hero.hpp").exists())

    def test_direct_cli_lists_registered_source_clips(self):
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run(
                [sys.executable, str(Path(hero.__file__).resolve()), "--help"],
                cwd=cwd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            for clip_id in hero.CLIP_WINDOWS:
                self.assertIn(clip_id, result.stdout)

    def test_private_original_reaction_header_when_canonical_rom_exists(self):
        if not hero.ROM.is_file():
            self.skipTest("canonical private ROM unavailable")
        for clip_id, (start, stop) in hero.CLIP_WINDOWS.items():
            if clip_id == hero.DEFAULT_CLIP:
                continue
            with self.subTest(clip_id=clip_id), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                report = hero.build(
                    hero.ROM, root / "source.generated.hpp",
                    root / "manifest.json", root / "source-plates",
                    clip_id=clip_id)
                self.assertEqual(report["original_motion_window"], [start, stop])
                self.assertEqual(len(report["frames"]), stop - start + 1)
                self.assertEqual(
                    len(list((root / "source-plates").glob("original-stock-*.png"))),
                    stop - start + 1)
                self.assertFalse(report["source_clip_loop_certified"])
                self.assertFalse(report["source_guest_timing_independently_certified"])
                self.assertFalse(report["human_visual_approval"])
                metrics = report["temporal_original_raster_metrics"]
                self.assertEqual(metrics["frame_count"], stop - start + 1)
                self.assertFalse(metrics["counterfactual_last_to_first_edge"][
                    "is_observed_chronological_edge"])
                self.assertFalse(metrics["loop_certified"])
                self.assertIn(
                    f"std::array<ModernMenuStockHeroFrame, {stop - start + 1}>",
                    (root / "source.generated.hpp").read_text())

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
            self.assertEqual(
                result["temporal_original_raster_metrics"]["frame_count"], 8)
            self.assertFalse(
                result["temporal_original_raster_metrics"]["loop_certified"])
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
