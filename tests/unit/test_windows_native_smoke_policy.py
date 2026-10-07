from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "windows-native-smoke.yml"


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

    def test_assembled_package_lifecycle_stays_in_windows_final_main_gate(self) -> None:
        self.assertIn("Assemble and verify portable Windows package", self.text)
        self.assertIn("tools/assemble_windows_package.py verify-archive", self.text)
        self.assertIn("tools/assemble_windows_package.py verify-archive-checksum", self.text)
        self.assertIn("Clean-package boot and per-user state anchoring", self.text)
        self.assertIn("WINDOWS_PACKAGE_STARTUP_DIAGNOSTICS ok", self.text)


if __name__ == "__main__":
    unittest.main()
