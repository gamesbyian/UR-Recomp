"""The QA01 compile-cache pilot must not change original/native evidence contracts."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/qa01-event-campaign.yml"


class QA01NativeCompileCacheContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_opt_in_dispatch_and_binary_identity_are_unchanged(self):
        text = self.workflow
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("repository: gamesbyian/uniracers-recomp", text)
        self.assertIn("ref: 10b864b9d14a7b7416dd909eb7b054c88faef101", text)
        self.assertIn("test \"$(git -C baldosa/snesrecomp rev-parse HEAD)\" = 075fbe4c8e0d97b0013be541795c39cb644a9709", text)
        self.assertIn("python3 tools/verify_rom.py reference/roms/retail/Uniracers_USA.sfc", text)
        self.assertIn("sha256sum snesref native snes9x_libretro.so > SHA256SUMS", text)
        self.assertIn("(cd \"$RUNNER_TEMP/qa01-binaries\" && sha256sum -c SHA256SUMS)", text)
        self.assertIn('(cd "$RUNNER_TEMP/qa01-binaries" && sha256sum -c SHA256SUMS)', text)

    def test_ccache_is_only_a_native_cmake_compiler_launcher(self):
        text = self.workflow
        self.assertIn("cmake ccache libsdl2-dev", text)
        self.assertIn("-DCMAKE_C_COMPILER_LAUNCHER=ccache", text)
        self.assertIn("-DCMAKE_CXX_COMPILER_LAUNCHER=ccache", text)
        self.assertIn("CCACHE_COMPILERCHECK=content", text)
        self.assertIn("ccache --max-size=256M", text)
        self.assertNotIn("CCACHE_SLOPPINESS=", text)
        self.assertEqual(text.count("ccache --show-stats"), 1)
        # The original reference emulator and pinned executable are compiled
        # *before* the launcher is selected. No cache provides finished binaries.
        self.assertLess(text.index("python3 tools/bootstrap_toolchain.py --offline"),
                        text.index("export CCACHE_DIR="))
        self.assertLess(text.index('cmake --build "$RUNNER_TEMP/qa01-snesref"'),
                        text.index("export CCACHE_DIR="))
        self.assertLess(text.index("export CCACHE_DIR="),
                        text.index("cmake -S baldosa -B baldosa/build"))

    def test_cache_save_is_optional_and_cannot_replace_rehash(self):
        text = self.workflow
        self.assertIn("uses: actions/cache/restore@v4", text)
        self.assertIn("uses: actions/cache/save@v4", text)
        self.assertEqual(text.count("continue-on-error: true"), 2)
        self.assertRegex(text, r"(?s)name: Save reusable QA01 native compile cache.*?if: success\(\)")
        self.assertLess(text.index("Save reusable QA01 native compile cache"),
                        text.index("Upload one immutable candidate for all case shards"))
        self.assertIn('sha256sum -c SHA256SUMS', text)
        self.assertIn("name: qa01-campaign-reference-and-native-binaries", text)
        self.assertIn("Run and classify source-qualified", text)

    def test_cross_run_key_includes_patch_sources_and_attempt(self):
        text = self.workflow
        keys = re.findall(r"^\s+key: (ur-qa01-ccache-.*)$", text, re.MULTILINE)
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0], keys[1])
        self.assertIn("baldosa10b864b9", keys[0])
        self.assertIn("hashFiles(", keys[0])
        self.assertIn("github.run_id", keys[0])
        self.assertIn("github.run_attempt", keys[0])
        self.assertIn("restore-keys: |", text)
        self.assertNotIn("github.sha", keys[0])
        self.assertNotIn("inputs.", keys[0])


if __name__ == "__main__":
    unittest.main()
