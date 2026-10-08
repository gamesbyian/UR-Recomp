from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/classify_modern_native_ci.py"
SPEC = spec_from_file_location("classify_modern_native_ci", MODULE_PATH)
assert SPEC and SPEC.loader
classifier = module_from_spec(SPEC)
SPEC.loader.exec_module(classifier)

WORKFLOWS = ROOT / ".github/workflows"
MANIFESTS = {
    "shared": (
        WORKFLOWS / "modern-shared-native-acceptance.yml",
        ROOT / ".github/ci/modern-native-shared-paths.txt",
    ),
    "onboarding": (
        WORKFLOWS / "modern-onboarding-practice-acceptance.yml",
        ROOT / ".github/ci/modern-native-onboarding-paths.txt",
    ),
    "ui": (
        WORKFLOWS / "native-ui-evidence.yml",
        ROOT / ".github/ci/modern-native-ui-paths.txt",
    ),
}


def workflow_pr_paths(path: Path) -> tuple[str, ...]:
    text = path.read_text()
    start = text.index("  pull_request:")
    end = text.index("\nconcurrency:", start)
    block = text[start:end]
    return tuple(re.findall(r'^\s+- "([^"]+)"\s*$', block, re.MULTILINE))


class ModernNativeCiClassifierTests(unittest.TestCase):
    def test_manifests_match_current_pull_request_filters(self):
        for suite, (workflow, manifest) in MANIFESTS.items():
            with self.subTest(suite=suite):
                self.assertEqual(
                    classifier.load_patterns(manifest),
                    workflow_pr_paths(workflow),
                )

    def test_common_toolchain_change_selects_all_heavy_suites(self):
        self.assertEqual(
            classifier.classify_paths(["tools/patch_modern_product_host.py"]),
            {"shared": True, "onboarding": True, "ui": True},
        )

    def test_suite_specific_paths_remain_selective(self):
        self.assertEqual(
            classifier.classify_paths(
                ["native/product/completed_run_ghost_policy.hpp"]
            ),
            {"shared": True, "onboarding": False, "ui": False},
        )
        self.assertEqual(
            classifier.classify_paths(
                ["tests/native/run_modern_vibration_acceptance.sh"]
            ),
            {"shared": False, "onboarding": True, "ui": False},
        )
        self.assertEqual(
            classifier.classify_paths(["tests/input/ui-race-result-route.script"]),
            {"shared": False, "onboarding": False, "ui": True},
        )

    def test_concrete_host_change_matches_overlapping_globs(self):
        result = classifier.classify_paths(
            ["native/product/uniracers_modern_host.cpp"]
        )
        self.assertTrue(result["shared"])
        self.assertTrue(result["onboarding"])
        self.assertTrue(result["ui"])

    def test_unrelated_docs_do_not_select_heavy_suites(self):
        self.assertEqual(
            classifier.classify_paths(["docs/WORK-QUEUE.md"]),
            {"shared": False, "onboarding": False, "ui": False},
        )

    def test_single_star_does_not_cross_directory_boundary(self):
        self.assertTrue(
            classifier.path_matches(
                "native/product/local_multiplayer_setup.cpp",
                "native/product/local_multiplayer_*.cpp",
            )
        )
        self.assertFalse(
            classifier.path_matches(
                "native/product/sub/local_multiplayer_setup.cpp",
                "native/product/local_multiplayer_*.cpp",
            )
        )

    def test_double_star_matches_nested_paths(self):
        self.assertTrue(
            classifier.path_matches(
                "third_party/cargo/snesrecomp-analyzer/src/lib.rs",
                "third_party/cargo/snesrecomp-analyzer/**",
            )
        )


if __name__ == "__main__":
    unittest.main()
