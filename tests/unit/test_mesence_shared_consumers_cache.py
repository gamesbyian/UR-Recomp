"""Keep all pinned MesenCE consumers on one source-bound main cache.

Source tests alone cannot substitute for real original ROM replay; dormant
manual workflows remain opt-in and preserve their own semantic assertions.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / ".github/workflows"
PATHS = (
    "art4k-live-original-mesen-ppu-raw.yml",
    "mesence-two-player-reference.yml",
    "racer-composition-mesen.yml",
)
PINNED = "a60e79feb4d6dcced5922d636f9211837d01e381"


class MesenceSharedConsumersTests(unittest.TestCase):
    def test_all_three_reuse_identical_source_hash_key_and_verified_build(self):
        sources = [(W / name).read_text(encoding="utf-8") for name in PATHS]
        import re
        keys = [re.findall(r"(?m)^          key: (mesence-linux-x64-v3-.*)$", source)
                for source in sources]
        for name, source, found in zip(PATHS, sources, keys):
            with self.subTest(workflow=name):
                self.assertEqual(len(found), 2)
                self.assertEqual(found[0], found[1])
                self.assertIn("MESENCE_REVISION: " + PINNED, source)
                self.assertIn("MESENCE_INPUT_PATCH_REV: v2", source)
                self.assertIn("    runs-on: ubuntu-22.04", source)
                self.assertIn('make -C "$RUNNER_TEMP/MesenCE" -j2 -O LTO=true STATICLINK=true SYSTEM_LIBEVDEV=false', source)
                self.assertIn("actions/cache/restore@v4", source)
                self.assertIn("actions/cache/save@v4", source)
                self.assertIn("tools/art/mesence_cache_receipt.py verify", source)
                self.assertIn("mesence-lua-input-subport.patch", source)
                self.assertIn("      - name: Verify canonical ROM", source)
                self.assertNotIn("      push:\n", source)
                self.assertLess(source.index("- name: Save verified pinned MesenCE build"),
                                source.index("MesenCE PPU RAM frames" if "art4k" in name else
                                             "Replay ordinary 2P fixture" if "two-player" in name else
                                             "Capture one exact composition invocation"))
        self.assertEqual(len(set(keys[0] + keys[1] + keys[2])), 1)

    def test_sibling_consumers_stay_manual_only(self):
        for name in PATHS[1:]:
            source = (W / name).read_text(encoding="utf-8")
            self.assertIn("  workflow_dispatch:", source)
            self.assertNotIn("  pull_request:", source)
            self.assertNotIn("  push:", source)
            self.assertIn("third_party/src/mesen-for-ai", source)
            self.assertIn("reference/roms/retail/Uniracers_USA.sfc", source)


if __name__ == "__main__":
    unittest.main()
