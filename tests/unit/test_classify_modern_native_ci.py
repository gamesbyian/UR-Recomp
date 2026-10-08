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
    "shared": ROOT / ".github/ci/modern-native-shared-paths.txt",
    "onboarding": ROOT / ".github/ci/modern-native-onboarding-paths.txt",
    "ui": ROOT / ".github/ci/modern-native-ui-paths.txt",
}
MIGRATED = {
    "shared": WORKFLOWS / "modern-shared-native-acceptance.yml",
    "ui": WORKFLOWS / "native-ui-evidence.yml",
}
ROUTER = ".github/workflows/modern-native-heavy-router.yml"


def workflow_pr_paths(path: Path) -> tuple[str, ...]:
    text = path.read_text()
    start = text.index("  pull_request:")
    end = text.index("\nconcurrency:", start)
    block = text[start:end]
    return tuple(re.findall(r'^\s+- "([^"]+)"\s*$', block, re.MULTILINE))


class ModernNativeCiClassifierTests(unittest.TestCase):
    def test_onboarding_manifest_still_matches_standalone_pull_request_filter(self):
        self.assertEqual(
            classifier.load_patterns(MANIFESTS["onboarding"]),
            workflow_pr_paths(
                WORKFLOWS / "modern-onboarding-practice-acceptance.yml"
            ),
        )

    def test_migrated_suites_are_reusable_and_router_owned(self):
        for suite, workflow in MIGRATED.items():
            with self.subTest(suite=suite):
                text = workflow.read_text()
                self.assertIn("  workflow_call:", text)
                self.assertNotIn("  pull_request:", text)
                self.assertIn(
                    ROUTER,
                    classifier.load_patterns(MANIFESTS[suite]),
                )

    def test_router_change_selects_migrated_suites_only(self):
        self.assertEqual(
            classifier.classify_paths([ROUTER]),
            {"shared": True, "onboarding": False, "ui": True},
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
