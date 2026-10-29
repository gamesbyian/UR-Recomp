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
    "onboarding": WORKFLOWS / "modern-onboarding-practice-acceptance.yml",
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

    def test_router_change_selects_all_migrated_suites(self):
        self.assertEqual(
            classifier.classify_paths([ROUTER]),
            {"shared": True, "onboarding": True, "ui": True},
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

    def test_shared_negative_assertion_helper_selects_actual_onboarding_consumer(self):
        helper = "tests/native/assert_absent_grep.sh"
        self.assertEqual(
            classifier.classify_paths([helper]),
            {"shared": False, "onboarding": True, "ui": False},
        )
        self.assertEqual(
            classifier.load_patterns(MANIFESTS["onboarding"]).count(helper), 1
        )
        source = MIGRATED["onboarding"].read_text()
        self.assertIn('bash "$GITHUB_WORKSPACE/tests/native/$script"', source)
        self.assertIn('run_modern_next_event_acceptance.sh', source)

    def test_concrete_host_change_matches_overlapping_globs(self):
        result = classifier.classify_paths(
            ["native/product/uniracers_modern_host.cpp"]
        )
        self.assertTrue(result["shared"])
        self.assertTrue(result["onboarding"])
        self.assertTrue(result["ui"])

    def test_router_trigger_is_exact_manifest_union(self):
        # GitHub should not schedule a classify-only runner for unrelated
        # tools, references or research. Keep the event prefilter and the
        # authoritative per-suite classifier in sync.
        selected = set()
        for manifest in MANIFESTS.values():
            selected.update(classifier.load_patterns(manifest))
        self.assertEqual(set(workflow_pr_paths(WORKFLOWS / "modern-native-heavy-router.yml")), selected)
        self.assertFalse(any(pattern in selected for pattern in (
            "tools/**", "tests/**", "native/**", "analysis/**", "reference/**",
        )))

    def test_suite_manifest_change_is_tested_and_classifier_change_selects_all(self):
        for suite in MANIFESTS:
            path = f".github/ci/modern-native-{suite}-paths.txt"
            matched = classifier.classify_paths([path])
            self.assertTrue(matched[suite], path)
        self.assertEqual(classifier.classify_paths(
            ["tools/classify_modern_native_ci.py"]
        ), {"shared": True, "onboarding": True, "ui": True})

    def test_router_uses_same_merge_base_comparison_as_pr_paths(self):
        router = (WORKFLOWS / "modern-native-heavy-router.yml").read_text()
        self.assertIn(
            "${{ github.event.pull_request.base.sha }}...${{ github.event.pull_request.head.sha }}",
            router,
        )
        self.assertIn("native router triggered without an owning suite", router)

    def test_pairwise_selection_shares_canonical_build(self):
        router = (WORKFLOWS / "modern-native-heavy-router.yml").read_text()
        self.assertIn("outputs.shared == 'true' && needs.classify.outputs.onboarding == 'true'", router)
        self.assertIn("outputs.shared == 'true' && needs.classify.outputs.ui == 'true'", router)
        self.assertIn("outputs.onboarding == 'true' && needs.classify.outputs.ui == 'true'", router)

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
