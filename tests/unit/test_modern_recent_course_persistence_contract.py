import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"
HARNESS = ROOT / "tests" / "native" / "run_modern_recent_course_persistence_acceptance.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "modern-onboarding-practice-acceptance.yml"
ONBOARDING_PATHS = ROOT / ".github" / "ci" / "modern-native-onboarding-paths.txt"


def _body(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    return source[start:source.index(end_marker, start)]


class ModernRecentCoursePersistenceContractTests(unittest.TestCase):
    def test_persist_is_metadata_only(self):
        source = HOST.read_text(encoding="utf-8")
        body = _body(
            source,
            "void persist_recent_course_for_active_profile(std::uint8_t track_id) {",
            "void observe_recent_course_identity() {",
        )
        self.assertIn("auto candidate = *g_profile_state;", body)
        self.assertIn("candidate.recent_track = track_id;", body)
        self.assertIn("g_profile_state_writable", body)
        self.assertIn("g_profile_state->profile_id != active_profile_key()", body)
        # Never captures live/Practice SRAM, writes cartridge SRAM or bumps
        # the autosave generation.
        for forbidden in (
            "capture_stock_sram_for_profile",
            "RtlTryWriteSram",
            "g_sram",
            "autosave_generation =",
            "++",
        ):
            self.assertNotIn(forbidden, body)

    def test_only_named_profiles_persist(self):
        source = HOST.read_text(encoding="utf-8")
        body = _body(
            source,
            "void observe_recent_course_identity() {",
            "ur::product::FastNavigationContext fast_navigation_context() {",
        )
        guard = body.index("if (!profile_key.empty()) {")
        persist = body.index("persist_recent_course_for_active_profile(track_id);")
        self.assertLess(guard, persist)

    def test_restore_is_scoped_to_loaded_profile(self):
        source = HOST.read_text(encoding="utf-8")
        body = _body(source, "void apply_profile_save_root() {", "UR_PROFILE_SAVE_ROOT APPLIED")
        self.assertIn("g_recent_course_track_id = *g_profile_state->recent_track;", body)
        self.assertIn("g_recent_course_profile_key = g_profile_state->profile_id;", body)

    def test_native_acceptance_is_wired(self):
        subprocess.run(["bash", "-n", str(HARNESS)], cwd=ROOT, check=True)
        harness = HARNESS.read_text(encoding="utf-8")
        for marker in (
            "RECENT_PERSISTED track=0 generation=1",
            "RECENT_RESTORED track=4",
            "UR_PROFILE_STATE MALFORMED_READ_ONLY",
            "UR_HOST_STATE AUTHENTIC_INERT",
        ):
            self.assertIn(marker, harness)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        paths = ONBOARDING_PATHS.read_text(encoding="utf-8")
        self.assertIn("run_modern_recent_course_persistence_acceptance.sh", workflow)
        self.assertIn("tests/input/modern-recent-course-persist.script", paths)
        self.assertIn("tests/input/modern-recent-course-restore.script", paths)


if __name__ == "__main__":
    unittest.main()
