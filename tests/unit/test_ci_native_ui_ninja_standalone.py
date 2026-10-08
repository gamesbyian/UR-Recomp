"""The standalone Native UI builder can use the canonical Ninja generator."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class NativeUiNinjaBuildExperimentTest(unittest.TestCase):
    def test_two_core_generator_is_shared_with_canonical(self):
        native = (ROOT / ".github/workflows/native-ui-evidence.yml").read_text()
        canonical = (ROOT / ".github/workflows/modern-native-heavy-router.yml").read_text()
        self.assertIn('cmake -S "$ROOT" -B "$ROOT/build" -G Ninja', canonical)
        standalone = native.split("      - name: Scaffold, generate and build", 1)[1].split(
            "      - name: Package native UI candidate", 1
        )[0]
        self.assertIn('cmake -S "$ROOT" -B "$ROOT/build" -G Ninja', standalone)
        self.assertIn('cmake --build "$ROOT/build" -j2', standalone)
        self.assertIn('test -x "$ROOT/build/UniracersSNESRecomp"', standalone)
        self.assertIn('ninja --version', native.split(
            "      - name: Install desktop build dependencies", 1
        )[1].split("      - name: Verify canonical ROM", 1)[0])

    def test_canonical_bridge_does_not_regenerate(self):
        native = (ROOT / ".github/workflows/native-ui-evidence.yml").read_text()
        bridge = native.split(
            "      - name: Bridge canonical candidate into Native UI artifact contract", 1
        )[1].split("      - name: Upload bridged native UI candidate", 1)[0]
        self.assertIn('inputs.canonical_candidate == true', bridge)
        self.assertNotIn('cmake --build', bridge)
        self.assertIn("native-ui-build.tar.gz", bridge)


if __name__ == "__main__":
    unittest.main()
