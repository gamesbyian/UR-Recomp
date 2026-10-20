#!/usr/bin/env python3
"""Read-only Modern combined-native-frontend hook inventory.

Use on the *combined* post-merge checkout. A green individual component PR
cannot establish that the single actual Baldosa native Windows host consumes
all four producers. This inventory is intentionally source-level, so its only
positive verdict is "eligible_for_native_acceptance_run". It never awards
screen pixels, guest parity, physical devices, artistic quality or release.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


REQUIREMENTS = {
    "title_renderer_available": (
        "native/product/modern_title_presenter.hpp",
        r"\brender_modern_title\s*\(",
    ),
    "source_grammar_available": (
        "native/product/modern_menu_visual_grammar.hpp",
        r"\bmodern_menu_paint_focus_band\s*\(",
    ),
    "destination_renderer_available": (
        "native/product/modern_native_destination_presenter.hpp",
        r"\brender_modern_native_destination\s*\(",
    ),
    "motion_model_available": (
        "native/product/modern_menu_motion.hpp",
        r"\badvance_modern_menu_motion\s*\(",
    ),
    "native_title_drawn": (
        "tools/baldosa_native_modern_root.cpp",
        r"\bur::product::render_modern_title\s*\(",
    ),
    "native_destinations_drawn": (
        "tools/baldosa_native_modern_root.cpp",
        r"\bur::product::render_modern_native_destination\s*\(",
    ),
    "native_motion_updated": (
        "tools/baldosa_native_modern_root.cpp",
        r"\bur::product::advance_modern_menu_motion\s*\(",
    ),
    "native_motion_painted": (
        "tools/baldosa_native_modern_root.cpp",
        r"\bur::product::paint_modern_menu_selection_motion\s*\(",
    ),
    "native_title_controller_confirm": (
        "tools/baldosa_native_modern_root.cpp",
        r"modern_title_confirm\s*\(",
    ),
    "native_title_state_handoff": (
        "tools/baldosa_native_modern_root.cpp",
        r"modern_title_active\s*\(",
    ),
    "native_host_chooses_wide_logical_source": (
        "tools/baldosa_native_modern_root.cpp",
        r"\*logical_width\s*=\s*(?:342\s*;|ur::product::modern_title_logical_width\s*\()",
    ),
    "native_wide_canvas_supported": (
        "tools/baldosa_native_modern_root.cpp",
        r"width\s*(!=|==)\s*342",
    ),
    "native_p1_edges_owned": (
        "tools/baldosa_native_modern_root.cpp",
        r"g_navigation_edges\.p1_gamepad\s*\(",
    ),
    "native_keyboard_edges_owned": (
        "tools/baldosa_native_modern_root.cpp",
        r"g_navigation_edges\.keyboard\s*\(",
    ),
    "authentic_mode_can_disable_root": (
        "tools/baldosa_native_modern_root.cpp",
        r"std::strcmp\s*\(\s*mode\s*,\s*\"authentic\"\s*\)",
    ),
    "reduced_motion_policy_requested": (
        "tools/baldosa_native_modern_root.cpp",
        r"UR_REDUCED_MOTION",
    ),
    "modern_host_widescreen_hook_staged": (
        "tools/baldosa_modern_profile_activation_spike.py",
        r"native_widescreen",
    ),
    "modern_host_prepare_frame_hook_staged": (
        "tools/baldosa_modern_profile_activation_spike.py",
        r"prepare_frame",
    ),
}

# Avoid a misleading green check for four headers + no actual game callback.
REQUIRED_NATIVE = (
    "native_title_drawn", "native_destinations_drawn", "native_motion_updated",
    "native_motion_painted", "native_title_controller_confirm",
    "native_host_chooses_wide_logical_source", "native_p1_edges_owned",
    "native_keyboard_edges_owned", "authentic_mode_can_disable_root",
)


def inventory(root: Path) -> dict:
    checked = {}
    for key, (path, pattern) in REQUIREMENTS.items():
        file = root / path
        if file.is_symlink() or not file.is_file():
            checked[key] = {"present": False, "path": path, "reason": "missing or redirected"}
            continue
        body = file.read_text(encoding="utf-8")
        matched = bool(re.search(pattern, body))
        checked[key] = {"present": matched, "path": path,
                        "reason": "source marker present" if matched else "source marker absent"}
    # Old or partly overwritten owner PR merges are unready even when
    # individually tested headers happen to coexist in the repository.
    missing = [key for key, row in checked.items() if not row["present"]]
    native_missing = [key for key in REQUIRED_NATIVE if not checked[key]["present"]]
    # This is an ACTUAL integration defect in isolated #2042: its dynamic
    # motion ornament assumes a centered 240px root even on the 342px
    # canvas where #2040's root and child occupy the same 320px rectangle.
    # A merge containing every "callsite" is still wrong if that literal
    # survives inside the painter call. Do not bless marker-only integration.
    root_source = root / "tools/baldosa_native_modern_root.cpp"
    text = (root_source.read_text(encoding="utf-8")
            if root_source.is_file() and not root_source.is_symlink() else "")
    motion_draw = re.search(
        r"paint_modern_menu_selection_motion\\s*\\([\\s\\S]{0,420}?\\);", text)
    if motion_draw is None:
        motion_draw = re.search(
            r"paint_modern_menu_selection_motion\\s*\\([\\s\\S]{0,600}?\\);", text)
    conflicts = []
    if (motion_draw and
            re.search(r"HostOverlayRect\\s*\\{\\s*\\(width\\s*-\\s*240\\)\\s*/\\s*2\\s*,"
                      r"\\s*10\\s*,\\s*240\\s*,\\s*204\\s*\\}", motion_draw.group())):
        conflicts.append("motion_uses_240px_root_under_342px_child_canvas")
    return {
        "schema_version": 1,
        "checked": checked,
        "missing": missing,
        "missing_native_integration_hooks": native_missing,
        "known_host_geometry_conflicts": conflicts,
        "eligible_for_native_acceptance_run": not missing and not conflicts,
        "native_executed": False,
        "screenshots_captured": 0,
        "human_visual_approved": False,
        "authentic_isolation_approved": False,
        "release_gate_credit": 0,
        "scope": "source-callsite and module-presence inventory only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--strict", action="store_true",
                        help="Fail if any required native hook is absent")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = inventory(args.root)
        if args.out:
            args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 2 if args.strict and (result["missing"] or
                                   result["known_host_geometry_conflicts"]) else 0
    except (OSError, ValueError, UnicodeError) as exc:
        print("MODERN_VISUAL_INTEGRATION_INCONCLUSIVE:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
