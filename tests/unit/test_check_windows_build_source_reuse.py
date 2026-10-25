"""Exact Windows candidate-only producer must preserve original build commands."""
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_windows_build_source_reuse as gate


class WindowsBuildParityTests(unittest.TestCase):
    def test_all_five_real_build_bodies_are_exactly_retained(self):
        gate.audit(gate.SOURCE.read_text(encoding="utf-8"),
                   gate.REUSE.read_text(encoding="utf-8"))

    def test_any_changed_original_compiler_command_fails(self):
        src = gate.SOURCE.read_text(encoding="utf-8")
        altered = src.replace("cmake --build baldosa/build-ur-win --target UniracersSNESRecomp -j 3",
                              "cmake --build baldosa/build-ur-win --target UniracersSNESRecomp -j 8", 1)
        self.assertNotEqual(src, altered)
        with self.assertRaisesRegex(ValueError, "silently diverged"):
            gate.audit(altered, gate.REUSE.read_text(encoding="utf-8"))

    def test_duplicated_pinned_step_fails(self):
        src = gate.SOURCE.read_text(encoding="utf-8")
        src += "\n      - name: Verify immutable native source pins\n        run: |\n          true\n"
        with self.assertRaisesRegex(ValueError, "missing/duplicate"):
            gate.audit(src, gate.REUSE.read_text(encoding="utf-8"))

    def test_modified_candidate_export_cannot_pass(self):
        src = gate.REUSE.read_text(encoding="utf-8")
        src = src.replace("name: qa-baldosa-native-export", "name: different-artifact")
        with self.assertRaisesRegex(ValueError, "candidate export"):
            gate.audit(gate.SOURCE.read_text(encoding="utf-8"), src)


if __name__ == "__main__":
    unittest.main()
