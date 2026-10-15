"""Guard the actual UR source files staged into the Baldosa Windows candidate.

This is a PR-trigger invalidation contract, NOT an acceptance substitute.
Use the established pinned staging adapters as the source list so that a
new linked C++ unit cannot silently bypass genuine Win32 journey coverage.
"""
from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path
import re
import unittest
from unittest import mock

from tools import baldosa_guest_adapter_spike as guest
from tools import baldosa_product_execution_spike as execution
from tools import baldosa_product_pause_spike as pause
from tools import baldosa_modern_profile_activation_spike as profile

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/baldosa-windows-native-bridge.yml"
STAGING_SCRIPTS = {
    "tools/baldosa_guest_adapter_spike.py",
    "tools/baldosa_product_execution_spike.py",
    "tools/baldosa_product_pause_spike.py",
    "tools/baldosa_modern_user_data_spike.py",
    "tools/baldosa_modern_profile_activation_spike.py",
}
# These non-sibling bridge headers control game input and native title routing.
# Normal .cpp sibling .hpp/.h files are discovered automatically below.
BRIDGE_HEADERS = {
    "native/product/baldosa_execution_backend.hpp",
    "native/product/baldosa_modern_session_binding.hpp",
    "native/product/modern_host_input_release_latch.hpp",
    "native/product/modern_root_menu.hpp",
    "native/product/modern_root_overlay_presenter.hpp",
    "native/product/modern_root_physical_edges.hpp",
}


def pr_paths() -> list[str]:
    text = WORKFLOW.read_text(encoding="utf-8")
    pr = text.split("  pull_request:\n", 1)[1].split("  workflow_dispatch:\n", 1)[0]
    return re.findall(r'^      - "([^"]+)"$', pr, flags=re.MULTILINE)


def staged_project_sources() -> set[str]:
    # Build the very CMake appendices applied by the shipping Windows job,
    # rather than maintaining another copy of two dynamic source lists.
    # Only suppress filesystem existence checks while constructing a synthetic
    # *planning* CMake string; validate every resolved real repo path below.
    with mock.patch.object(Path, "is_file", return_value=True):
        cmake = "\n".join((
            guest.patch_cmake(
                "snesrecomp_target_desktop_host(UniracersSNESRecomp)", ROOT),
            execution.patch_cmake(execution.OBSERVER, ROOT),
            pause.patch_game_cmake(pause.REQUIRED, ROOT),
            profile.patch_cmake(profile.NATIVE_MARK, ROOT),
        ))
    pattern = re.compile(
        re.escape(ROOT.as_posix()) +
        r"/((?:tools|native/(?:product|presentation|title))/"
        r"[A-Za-z0-9_.-]+\.cpp)"
    )
    sources = set(pattern.findall(cmake))
    if len(sources) < 35:
        raise AssertionError("Native CMake staging source population shrank unexpectedly")
    for path in sources:
        if not (ROOT / path).is_file():
            raise AssertionError("Staged source is missing: " + path)
    # A change to a directly paired declaration changes these translation
    # units even if the .cpp remains byte-identical.
    paired_headers = {
        str((Path(path).with_suffix(ext)).as_posix())
        for path in sources
        for ext in (".hpp", ".h")
        if (ROOT / Path(path).with_suffix(ext)).is_file()
    }
    for path in STAGING_SCRIPTS | BRIDGE_HEADERS:
        if not (ROOT / path).is_file():
            raise AssertionError("Pinned project staging/header input missing: " + path)
    return sources | paired_headers | STAGING_SCRIPTS | BRIDGE_HEADERS


def missing_triggers(inputs: set[str], filters: list[str]) -> list[str]:
    return sorted(path for path in inputs
                  if not any(fnmatchcase(path, item) for item in filters))


class BaldosaWindowsCompiledTriggerClosureTest(unittest.TestCase):
    def test_every_direct_staged_source_header_and_script_triggers_windows(self):
        inputs = staged_project_sources()
        self.assertIn("native/product/session_control.cpp", inputs)
        self.assertIn("native/presentation/racer_guest_snapshot.cpp", inputs)
        self.assertIn("tools/baldosa_native_modern_root.cpp", inputs)
        self.assertGreaterEqual(len(inputs), 45)
        self.assertEqual(missing_triggers(inputs, pr_paths()), [])

    def test_exact_scope_no_blanket_product_or_coordination_trigger(self):
        filters = pr_paths()
        for forbidden in ("native/product/**", "native/presentation/**",
                          "native/title/**", "tools/**",
                          "docs/WORK-QUEUE.md", "docs/**"):
            self.assertNotIn(forbidden, filters)
        self.assertIn(".github/workflows/baldosa-windows-native-bridge.yml", filters)

    def test_missing_executable_input_is_detected_not_silently_dropped(self):
        inputs = staged_project_sources()
        filtered = [p for p in pr_paths()
                    if p not in ("native/product/session_control.cpp",
                                 "native/product/session_control.*")]
        self.assertIn("native/product/session_control.cpp",
                      missing_triggers(inputs, filtered))


if __name__ == "__main__":
    unittest.main()
