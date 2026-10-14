"""QA-01 exact-source differentiation of legacy Modern and Baldosa Windows."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_framework_lineage as m


class FrameworkLineage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {
            "toolchain": m.TOOLCHAIN.read_text(encoding="utf-8"),
            "entry": m.TOOL_ENTRY.read_text(encoding="utf-8"),
            "windows": m.WINDOWS.read_text(encoding="utf-8"),
            "router": m.ROUTER.read_text(encoding="utf-8"),
            "shared": m.SHARED.read_text(encoding="utf-8"),
            "baldosa": m.BALDOSA.read_text(encoding="utf-8"),
        }

    def run_contract(self, **overrides):
        parts = dict(self.data, **overrides)
        return m.lineage(parts["toolchain"], parts["entry"],
                         parts["windows"], parts["router"],
                         parts["shared"], parts["baldosa"])

    def test_distinct_executables_and_definitive_nonadmission(self):
        report = self.run_contract()
        self.assertEqual(report["schema"], m.SCHEMA)
        self.assertEqual(report["legacy_framework"], m.LEGACY)
        self.assertEqual(report["baldosa_framework"], m.NEWER)
        self.assertEqual(report["baldosa_game"], m.GAME)
        for path in ("default_shared_modern_framework",
                     "router_canonical_modern_framework",
                     "windows_portable_smoke_framework"):
            self.assertEqual(report[path], m.LEGACY)
        self.assertEqual(report["baldosa_independent_windows_title_framework"],
                         m.NEWER)
        self.assertTrue(
            report["borrowed_canonical_candidate_requires_upstream_artifact_identity"])
        for key in (
            "the_two_windows_builds_are_the_same_executable",
            "downloaded_windows_zip_exact_binary_identity_proven_here",
            "baldosa_reference_match_proves_windows_portable_attract_parity",
            "runtime_original_native_cpu_beam_parity_proven",
        ):
            self.assertIs(report[key], False, key)
        self.assertEqual(report["strict_usa_complete_event_credit"], 0)

    def test_no_silent_legacy_revision_or_manifest_substitution(self):
        for key in ("entry", "toolchain"):
            with self.subTest(source=key):
                self.assertIn(m.LEGACY, self.data[key])
                bad = self.data[key].replace(m.LEGACY, "a" * 40)
                with self.assertRaisesRegex(ValueError, "revision drifted"):
                    self.run_contract(**{key: bad})
        entry = json.loads(self.data["entry"])
        entry["url"] = "https://github.com/example/unrelated-recompiler.git"
        with self.assertRaisesRegex(ValueError, "origin drifted"):
            self.run_contract(entry=json.dumps(entry))
        root = json.loads(self.data["toolchain"])
        root["tools"] = [t for t in root["tools"]
                         if t.get("id") != "snesrecomp"]
        with self.assertRaisesRegex(ValueError, "one snesrecomp"):
            self.run_contract(toolchain=json.dumps(root))

    def test_windows_and_modern_default_build_steps_required(self):
        substitutions = (
            ("windows",
             "python tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only",
             "echo used another framework"),
            ("windows", '-DSNESRECOMP_ROOT="$FRAMEWORK"',
             '-DSNESRECOMP_ROOT="$DIFFERENT"'),
            ("router",
             "python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only",
             "echo staged a different framework"),
            ("router", "modern-native-canonical-candidate",
             "unrelated-canonical-candidate"),
            ("shared",
             "python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only",
             "echo another framework"),
            ("shared", "inputs.canonical_candidate != true",
             "inputs.canonical_candidate == true"),
            ("shared", "modern-native-canonical-candidate",
             "unknown-unqualified-zip"),
        )
        for key, needle, wrong in substitutions:
            with self.subTest(workflow=key, needle=needle):
                self.assertIn(needle, self.data[key])
                with self.assertRaisesRegex(ValueError, "identity"):
                    self.run_contract(**{key: self.data[key].replace(needle, wrong)})

    def test_upstream_baldosa_checkout_and_actual_gitlink_required(self):
        cases = (
            (m.GAME, "b" * 40),
            (m.NEWER, "c" * 40),
            ("repository: gamesbyian/uniracers-recomp",
             "repository: unrelated/example"),
            ("cmake -S baldosa", "cmake -S another-title"),
        )
        for old, new in cases:
            with self.subTest(modified=old):
                self.assertIn(old, self.data["baldosa"])
                with self.assertRaisesRegex(ValueError, "identity"):
                    self.run_contract(baldosa=self.data["baldosa"].replace(old, new))


if __name__ == "__main__":
    unittest.main()
