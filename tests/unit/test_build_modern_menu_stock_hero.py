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
                      original[0]["p1_representation_id"])
        target["palette_asset_id"] = "0x07"
        with self.assertRaisesRegex(ValueError, "unknown original P1"):
            hero.verified_clip(rom, bad, self.source)

    def test_original_raster_and_compiled_cpp_asset(self):
        if not hero.ROM.is_file():
            self.skipTest("canonical private ROM unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            header = out / "modern_menu_stock_hero_original.generated.hpp"
            manifest = out / "source-hero-manifest.json"
            result = hero.build(hero.ROM, header, manifest)
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
