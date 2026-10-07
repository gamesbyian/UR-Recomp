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
            '      - ".github/workflows/windows-native-smoke.yml"',
            '      - "native/product/**"',
            '      - "native/presentation/**"',
            '      - "native/title/**"',
        ):
            self.assertIn(path, self.text)

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

    def test_assembled_package_lifecycle_stays_in_windows_final_main_gate(self) -> None:
        self.assertIn("Assemble and verify portable Windows package", self.text)
        self.assertIn("tools/assemble_windows_package.py verify-archive", self.text)
        self.assertIn("tools/assemble_windows_package.py verify-archive-checksum", self.text)
        self.assertIn("Clean-package boot and per-user state anchoring", self.text)
        self.assertIn("WINDOWS_PACKAGE_STARTUP_DIAGNOSTICS ok", self.text)


if __name__ == "__main__":
    unittest.main()
