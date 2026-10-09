"""Pinned framework ancestry catalog sanity and OAM patch provenance."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
DELTA = ROOT / "analysis/data/baldosa-framework-delta-20261009.json"
PATCH = ROOT / "analysis/patches/baldosa-oam-address-pin.patch"
SRC = ROOT / "reference/imported/reverse-engineering/baldosa-uniracers-recomp/src/main.c"


class FrameworkDeltaAuditTest(unittest.TestCase):
    def test_exact_ancestry(self):
        j = json.loads(DELTA.read_text(encoding="utf-8"))
        self.assertEqual(j["from_ur_recomp_pinned"], "cd5875cbdaf19f5e324272b1f8051d671fce9215")
        self.assertEqual(j["to_baldosa_pinned"], "075fbe4c8e0d97b0013be541795c39cb644a9709")
        self.assertEqual((j["ahead_by"], j["behind_by"], j["total_commits"]), (86, 0, 86))
        self.assertEqual(len(j["commits"]), 86)
        self.assertEqual(len(j["files"]), 121)
        self.assertEqual(len(set(x["sha"] for x in j["commits"])), 86)
        self.assertEqual(len(set(x["path"] for x in j["files"])), 121)
        self.assertIn("runner/src/snes/dma.c", {x["path"] for x in j["files"]})

    def test_patch_not_live_code(self):
        text = PATCH.read_text(encoding="utf-8")
        self.assertIn("diff --git a/runner/src/snes/dma.c b/runner/src/snes/dma.c", text)
        self.assertIn("g_hdma_oamdata_at_10c", text)
        self.assertIn("hdma_pin_oam_address", text)
        self.assertIn("g_hdma_oamdata_at_10c = true;", SRC.read_text(encoding="utf-8"))
        self.assertNotIn("src/gen/", str(PATCH))


if __name__ == "__main__":
    unittest.main()
