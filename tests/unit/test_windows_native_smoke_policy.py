from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "windows-native-smoke.yml"
HOST = ROOT / "native" / "product" / "uniracers_modern_host.cpp"


class WindowsNativeSmokePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_shipping_runtime_surfaces_retrigger_final_main_package_acceptance(self) -> None:
        for path in (
            '      - "tools/verify_rom.py"',
            '      - "tools/check_result_screen_time.py"',
            '      - "tests/input/ui-race-result-route.script"',
            '      - "tests/unit/test_assemble_windows_package.py"',
            '      - "reference/roms/retail/Uniracers_USA.sfc"',
            '      - "native/product/**"',
            '      - "native/presentation/**"',
            '      - "native/title/**"',
        ):
            self.assertIn(path, self.text)
        self.assertNotIn(
            '      - ".github/workflows/windows-native-smoke.yml"',
            self.text,
        )

    def test_push_path_entries_are_structurally_indented(self) -> None:
        paths_start = self.text.index("    paths:\n") + len("    paths:\n")
        paths_end = self.text.index("\n\nconcurrency:", paths_start)
        entries = [
            line
            for line in self.text[paths_start:paths_end].splitlines()
            if line.strip()
        ]
        self.assertTrue(entries)
        for line in entries:
            self.assertTrue(
                line.startswith('      - "'),
                f"malformed push.paths entry: {line!r}",
            )

    def test_multiplayer_acceptance_quit_helper_is_declared_before_use(self) -> None:
        host = HOST.read_text(encoding="utf-8")
        declaration = host.index("bool request_desktop_quit();")
        acceptance = host.index(
            'if (std::getenv("UR_MULTIPLAYER_MATCH_ACCEPTANCE"))'
        )
        definition = host.index("bool request_desktop_quit() {")
        self.assertLess(declaration, acceptance)
        self.assertLess(acceptance, definition)

    def test_portable_artifact_upload_requires_success(self) -> None:
        upload = self.text.index("- name: Upload portable Windows package")
        snippet = self.text[upload : upload + 180]
        self.assertIn("if: success()", snippet)
        self.assertNotIn("if: always()", snippet)

    def test_portable_build_uses_static_msvc_runtime_and_verifies_imports(self) -> None:
        self.assertIn(
            "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
            self.text,
        )
        self.assertIn("dumpbin /dependents", self.text)
        self.assertIn("windows-runtime-dependencies.log", self.text)
        self.assertIn("MSVCP[0-9_]*|VCRUNTIME[0-9_]*", self.text)
        self.assertIn(
            "Portable executable unexpectedly depends on the Visual C++ Redistributable.",
            self.text,
        )

    def test_package_refresh_covers_current_run_stores(self) -> None:
        self.assertIn(
            '$PACKAGE_USER_DATA/runs/default/package-refresh-marker.urrun',
            self.text,
        )
        self.assertIn(
            '$PACKAGE_USER_DATA/multiplayer-runs/package-refresh-marker.urrun',
            self.text,
        )
        self.assertIn(
            '$PACKAGE_USER_DATA/multiplayer-runs/package-refresh-marker.urmatch',
            self.text,
        )
        self.assertIn(
            'test "$MULTIPLAYER_RUN_BEFORE" = "$MULTIPLAYER_RUN_AFTER"',
            self.text,
        )
        self.assertIn(
            'test "$MULTIPLAYER_MATCH_BEFORE" = "$MULTIPLAYER_MATCH_AFTER"',
            self.text,
        )

    def test_package_refresh_rechecks_durable_state_after_replacement_boot(self) -> None:
        for marker in (
            'test "$MODERN_BEFORE" = "$(sha256sum "$PACKAGE_USER_DATA/host-state-v1.txt"',
            'test "$PROFILE_CATALOG_BEFORE" = "$(sha256sum "$PACKAGE_USER_DATA/profiles-v1.txt"',
            'test "$PROFILE_BEFORE" = "$(sha256sum "$PACKAGE_USER_DATA/saves/profile-default/host-profile.txt"',
            'test "$RUN_BEFORE" = "$(sha256sum "$PACKAGE_USER_DATA/runs/default/package-refresh-marker.urrun"',
            'test "$MULTIPLAYER_RUN_BEFORE" = "$(sha256sum "$PACKAGE_USER_DATA/multiplayer-runs/package-refresh-marker.urrun"',
            'test "$MULTIPLAYER_MATCH_BEFORE" = "$(sha256sum "$PACKAGE_USER_DATA/multiplayer-runs/package-refresh-marker.urmatch"',
        ):
            self.assertIn(marker, self.text)

    def test_startup_diagnostics_enforce_current_log_line_bound(self) -> None:
        self.assertIn("assert_bounded_startup_log()", self.text)
        self.assertIn('cat "$log"', self.text)
        self.assertIn('test "$(wc -l < "$log")" -le 11', self.text)
        for name in (
            "BROKEN_ROM_LOG",
            "BROKEN_DATA_LOG",
            "EMPTY_MODS_LOG",
            "INVALID_LOG",
            "VIDEO_LOG",
            "AUDIO_LOG",
        ):
            self.assertIn(
                'assert_bounded_startup_log "$' + name + '"',
                self.text,
            )

    def test_assembled_package_lifecycle_stays_in_windows_final_main_gate(self) -> None:
        self.assertIn("Assemble and verify portable Windows package", self.text)
        self.assertIn("tools/assemble_windows_package.py verify-archive", self.text)
        self.assertIn(
            "tools/assemble_windows_package.py verify-archive-checksum",
            self.text,
        )
        self.assertIn("Clean-package boot and per-user state anchoring", self.text)
        self.assertIn(
            'python tools/verify_rom.py "$PACKAGE/Uniracers_USA.sfc"',
            self.text,
        )
        self.assertIn(
            'python tools/verify_rom.py "$TEST_PACKAGE/Uniracers_USA.sfc"',
            self.text,
        )
        self.assertIn("WINDOWS_PACKAGE_STARTUP_DIAGNOSTICS ok", self.text)


if __name__ == "__main__":
    unittest.main()
