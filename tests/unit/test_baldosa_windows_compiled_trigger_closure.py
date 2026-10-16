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
# When the Modern owner lands genuine native Options, both the disposable
# Baldosa host patch and its app-level settings interface directly affect
# the compiled PE. Neither file exists on main until that PR is accepted;
# requiring them unconditionally would make baseline CI fail prematurely.
# Treat the pair atomically as soon as the product feature appears.

# These translation units are linked into the actual Windows candidate, or
# its source-bound profile fixture. Extract their literal first-party header
# dependencies from source instead of maintaining only a manually copied list.
# This is intentionally narrow, not a blanket native/** PR trigger.
DIRECT_BRIDGE_SOURCES = {
    "tools/baldosa_native_modern_root.cpp",
    "tools/baldosa_modern_profile_activation.cpp",
    "tools/baldosa_modern_profile_native_fixture.cpp",
    "tools/baldosa_native_pause_lifecycle.cpp",
    "tools/baldosa_native_product_execution.cpp",
    "tools/baldosa_guest_snapshot_probe.cpp",
}
FIRST_PARTY_INCLUDE_ROOTS = (
    "native/product", "native/presentation", "native/title", "tools",
)


def direct_first_party_bridge_headers(source_files: set[str] | None = None) -> set[str]:
    observed: set[str] = set()
    # Source files are derived from the exact existing CMake appendices, not
    # copied from a hand-maintained translation-unit list. Preserve selected
    # fixture/source-only bridges as additional direct inputs.
    for source in sorted(DIRECT_BRIDGE_SOURCES | (source_files or set())):
        src = ROOT / source
        if not src.is_file():
            raise AssertionError("Compiled bridge source is missing: " + source)
        for include in re.findall(
            r'^\s*#include\s+"([^"]+)"', src.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        ):
            # Framework headers ("desktop/config.h", etc.) live under the
            # immutable Baldosa checkout, not in our first-party source root.
            for root in FIRST_PARTY_INCLUDE_ROOTS:
                candidate = ROOT / root / include
                if candidate.is_file():
                    observed.add(candidate.relative_to(ROOT).as_posix())
    return observed



# These are observed, compiled first-party header roots from the existing
# CMake staged bridge. Follow quoted first-party includes to guard nested
# source contracts without a blanket native/** Windows PR trigger. External
# pinned Baldosa framework headers remain outside this mutable-UR graph.
TRANSITIVE_WINDOWS_HEADER_ROOTS = {
    "native/product/run_record_capture_policy.hpp",
    "native/product/modern_root_overlay_presenter.hpp",
    "native/product/quick_practice_available_selection.hpp",
    "native/product/quick_practice_selection_view.hpp",
    "native/product/host_product_state.hpp",
    "native/product/host_profile_state.hpp",
}


def transitive_first_party_bridge_headers() -> set[str]:
    pending = list(TRANSITIVE_WINDOWS_HEADER_ROOTS)
    seen: set[str] = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        if len(seen) > 256:
            raise AssertionError("Unbounded first-party header closure")
        source = ROOT / path
        if not source.is_file():
            raise AssertionError("Missing compiled first-party header: " + path)
        for include in re.findall(
            r'^\s*#include\s+"([^"]+)"', source.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        ):
            if include.startswith("/") or ".." in Path(include).parts:
                raise AssertionError("Unexpected first-party relative include: " + include)
            for root in (source.parent, *(ROOT / d for d in FIRST_PARTY_INCLUDE_ROOTS)):
                candidate = root / include
                if candidate.is_file():
                    rel = candidate.relative_to(ROOT).as_posix()
                    if rel not in seen:
                        pending.append(rel)
    return seen - TRANSITIVE_WINDOWS_HEADER_ROOTS


OPTIONAL_NATIVE_OPTIONS_INPUTS = {
    "tools/baldosa_modern_options_spike.py",
    "native/product/baldosa_native_options.hpp",
}


BRIDGE_HEADERS = {
    "native/product/baldosa_execution_backend.hpp",
    "native/product/baldosa_modern_session_binding.hpp",
    "native/product/modern_host_input_release_latch.hpp",
    "native/product/modern_root_menu.hpp",
    "native/product/modern_root_overlay_presenter.hpp",
    "native/product/modern_root_physical_edges.hpp",
    "native/product/baldosa_native_run_save_feedback.hpp",
    "native/product/baldosa_native_two_seat_join.hpp",
    "native/product/quick_practice_route.hpp",
    "native/product/quick_practice_input_mask.hpp",
    "native/product/quick_practice_launch.hpp",
    "native/product/quick_practice_available_selection.hpp",
    "native/product/quick_practice_selection_view.hpp",
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
    options_present = {
        path for path in OPTIONAL_NATIVE_OPTIONS_INPUTS if (ROOT / path).is_file()
    }
    if options_present and options_present != OPTIONAL_NATIVE_OPTIONS_INPUTS:
        raise AssertionError("Native Options host patch/header are an incomplete pair")
    return (sources | paired_headers | STAGING_SCRIPTS | BRIDGE_HEADERS
            | options_present | direct_first_party_bridge_headers(sources)
            | transitive_first_party_bridge_headers())


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

    def test_native_options_feature_addition_invalidates_windows_candidate(self):
        # Absent on baseline main; the moment Modern ships the Options host
        # seam, both implementation-bearing inputs must trigger real Win32 CI.
        options_present = {
            path for path in OPTIONAL_NATIVE_OPTIONS_INPUTS
            if (ROOT / path).is_file()
        }
        self.assertIn(options_present, (set(), OPTIONAL_NATIVE_OPTIONS_INPUTS))
        self.assertEqual(
            missing_triggers(options_present, pr_paths()), [])
        self.assertEqual(
            options_present.issubset(staged_project_sources()), True)

    def test_direct_bridge_headers_invalidate_real_windows_candidate(self):
        observed = direct_first_party_bridge_headers()
        key_inputs = {
            "native/title/uniracers_practice_tour_unlock.hpp",
            "native/product/baldosa_native_profile_sram_checkpoint.hpp",
            "native/product/baldosa_native_profile_path_guard.hpp",
            "native/product/baldosa_native_existing_profile_next_boot.hpp",
            "native/product/baldosa_physical_pause_input.hpp",
            "native/product/baldosa_native_run_publish_retry.hpp",
            "native/product/baldosa_native_match_publish_retry.hpp",
        }
        self.assertTrue(key_inputs.issubset(observed))
        compiled = staged_project_sources()
        shared_storage_headers = {
            "native/product/local_tournament_atomic_replace.hpp",
            "native/product/local_tournament_launch_path_lock.hpp",
            "native/product/run_record_capture_policy.hpp",
        }
        self.assertTrue(shared_storage_headers.issubset(compiled))
        self.assertEqual(missing_triggers(compiled, pr_paths()), [])
        self.assertEqual(missing_triggers(observed, pr_paths()), [])
        # A regression that drops a critical path must fail even though the
        # .cpp it feeds is unchanged and remains otherwise in the PR filter.
        stripped = [p for p in pr_paths()
                    if p != "native/product/baldosa_native_profile_sram_checkpoint.hpp"]
        self.assertIn(
            "native/product/baldosa_native_profile_sram_checkpoint.hpp",
            missing_triggers(observed, stripped),
        )

    def test_nested_compiled_presentation_practice_and_profile_headers_trigger_windows(self):
        inputs = staged_project_sources()
        self.assertTrue(TRANSITIVE_WINDOWS_HEADER_ROOTS.issubset(inputs))
        nested = transitive_first_party_bridge_headers()
        required = {
            "native/product/widescreen_output_composition.hpp",
            "native/product/modern_stock_menu_palette.hpp",
            "native/product/modern_overlay_composition.hpp",
            "native/product/modern_overlay_text_fit.hpp",
            "native/product/modern_text_layout.hpp",
            "native/product/modern_text_catalog.hpp",
            "native/product/quick_practice_selection.hpp",
            "native/product/quick_practice_picker.hpp",
            "native/product/quick_practice_catalog.hpp",
            "native/product/quick_practice_availability.hpp",
            "native/product/regional_presentation.hpp",
            "native/product/completed_run_ghost_target.hpp",
        }
        self.assertTrue(required.issubset(nested))
        self.assertEqual(missing_triggers(nested, pr_paths()), [])
        omitted = [p for p in pr_paths()
                   if p != "native/product/widescreen_output_composition.hpp"]
        self.assertIn(
            "native/product/widescreen_output_composition.hpp",
            missing_triggers(nested, omitted),
        )

    def test_missing_executable_input_is_detected_not_silently_dropped(self):
        inputs = staged_project_sources()
        filtered = [p for p in pr_paths()
                    if p not in ("native/product/session_control.cpp",
                                 "native/product/session_control.*")]
        self.assertIn("native/product/session_control.cpp",
                      missing_triggers(inputs, filtered))


if __name__ == "__main__":
    unittest.main()
