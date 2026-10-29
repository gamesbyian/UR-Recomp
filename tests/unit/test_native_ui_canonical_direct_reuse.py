"""Guard source-identical Modern UI fan-out against needless artifact repacks.

Canonical routing may skip only the redundant bridge/build job. All six
capture shards, original native host hooks and aggregate gates remain required.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-ui-evidence.yml"
ROUTER = ROOT / ".github/workflows/modern-native-heavy-router.yml"


class NativeUiCanonicalReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.router = ROUTER.read_text(encoding="utf-8")
        cls.build, remainder = cls.source.split("\n  build:\n", 1)[1].split("\n  capture:\n", 1)
        cls.capture, cls.aggregate = remainder.split("\n  aggregate:\n", 1)

    def test_router_still_builds_and_uploads_exact_canonical_candidate(self):
        self.assertIn("name: modern-native-canonical-candidate", self.router)
        self.assertIn("tar -czf \"$RUNNER_TEMP/modern-native-canonical.tar.gz\"", self.router)
        self.assertIn("canonical_candidate: ${{ needs.build.result == 'success' }}", self.router)
        self.assertIn("uses: ./.github/workflows/native-ui-evidence.yml", self.router)

    def test_canonical_path_skips_only_redundant_bridge(self):
        self.assertIn("inputs.canonical_candidate != true &&", self.build)
        self.assertNotIn("modern-native-canonical-artifact", self.build)
        self.assertNotIn("Upload bridged native UI candidate", self.build)
        self.assertIn("needs: build", self.capture)
        self.assertIn("always() &&", self.capture)
        self.assertIn("needs.build.result == 'skipped'", self.capture)
        self.assertIn("github.event.pull_request.draft == false", self.capture)
        self.assertIn("name: modern-native-canonical-candidate", self.capture)
        self.assertIn("modern-native-canonical.tar.gz", self.capture)
        self.assertIn('mv "$RUNNER_TEMP/modern-native-canonical" "$RUNNER_TEMP/ur-recomp-build"', self.capture)
        self.assertIn('test ! -e "$RUNNER_TEMP/ur-recomp-build"', self.capture)

    def test_canonical_restore_preserves_all_prior_source_hooks(self):
        for required in (
            "ur_uniracers_product_after_run_frame",
            "ur_uniracers_product_system_key_down",
            "ur_uniracers_product_system_gamepad_button",
            "ur_uniracers_product_system_overlay",
            "uniracers_modern_host.cpp",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.capture)

    def test_standalone_path_still_builds_and_uses_old_candidate(self):
        self.assertIn("- name: Scaffold, generate and build", self.build)
        self.assertIn("- name: Upload native UI candidate", self.build)
        self.assertIn("name: native-ui-build-candidate", self.build)
        self.assertIn("name: native-ui-build-candidate", self.capture)
        self.assertIn("inputs.canonical_candidate != true", self.capture)
        self.assertIn("native-ui-build.tar.gz", self.capture)

    def test_authentic_inertness_refuses_forbidden_markers(self):
        # A bare negated grep under errexit would silently continue even when
        # the marker was present; explicit if + exit must own the failure.
        self.assertNotIn("! grep -q", self.capture)
        self.assertIn('if grep -q "$marker" "$AUTH_LOG"; then', self.capture)
        self.assertIn("exit 1", self.capture)
        for marker in (
            "UR_HOST_STATE LOADED",
            "UR_DISPLAY_MODE APPLIED",
            "UR_VSYNC APPLIED",
            "UR_PRESENTATION_FPS APPLIED",
            "UR_OUTPUT_RESOLUTION",
            "UR_WIDESCREEN",
        ):
            with self.subTest(marker=marker):
                self.assertIn('"' + marker + '"', self.capture)

    def test_reset_dump_names_read_without_shell_word_splitting(self):
        self.assertIn('test -f "$script"', self.aggregate)
        self.assertIn('while IFS= read -r tag; do', self.aggregate)
        self.assertIn('done < <(awk', self.aggregate)
        self.assertIn('exit "$missing"', self.aggregate)

    def test_all_six_capture_shards_and_aggregate_still_required(self):
        self.assertIn("shard: [core, navigation, results-a, results-b, records, profiles]", self.capture)
        self.assertIn("if: ${{ always() && needs.capture.result == 'success'", self.aggregate)
        self.assertIn("needs.build.result == 'skipped'", self.aggregate)
        self.assertIn("needs.build.result == 'success'", self.aggregate)
        self.assertIn("- name: Download capture shards", self.aggregate)
        self.assertIn("- name: Build UI atlas report", self.aggregate)


if __name__ == "__main__":
    unittest.main()
