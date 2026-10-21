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
    # #2165 is merged on main: on a combined title/destination source head
    # the global BG1 checker must remain anchored to the framebuffer, rather
    # than silently phase-resetting when a differently sized root is drawn.
    "fixed_bg1_grammar_available": (
        "native/product/modern_menu_visual_grammar.hpp",
        r"\bbool\s+fixed_bg1_grid\s*=\s*false",
    ),
    "native_root_fixed_bg1_opt_in": (
        "native/product/modern_root_overlay_presenter.hpp",
        r"\bmodern_menu_paint_checker_backdrop\s*\(\s*paint\s*,\s*pixels\s*,"
        r"\s*stride\s*,\s*surface_height\s*,\s*x\s*,\s*y\s*,"
        r"\s*rect\.width\s*,\s*rect\.height\s*,\s*scale\s*,\s*true\s*\)",
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
    "fixed_bg1_grammar_available", "native_root_fixed_bg1_opt_in",
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
        r"paint_modern_menu_selection_motion\s*\([\s\S]{0,420}?\);", text)
    if motion_draw is None:
        motion_draw = re.search(
            r"paint_modern_menu_selection_motion\s*\([\s\S]{0,600}?\);", text)
    conflicts = []
    if (motion_draw and
            re.search(r"HostOverlayRect\s*\{\s*\(width\s*-\s*240\)\s*/\s*2\s*,"
                      r"\s*10\s*,\s*240\s*,\s*204\s*\}", motion_draw.group())):
        conflicts.append("motion_uses_240px_root_under_342px_child_canvas")
    # Later animation branches use `root_rect` in the paint call but keep
    # its DECLARATION fixed at 240. That is not a fix on the 342-wide
    # destination canvas: source-wide title + child + motion must share
    # the same 320-wide root geometry, not merely a same-named variable.
    integrated_wide = all(checked[k]["present"] for k in (
        "native_host_chooses_wide_logical_source",
        "native_destinations_drawn", "native_motion_painted"))
    if integrated_wide and motion_draw is not None:
        has_fixed_root = bool(re.search(
            r"\b(?:const\s+)?HostOverlayRect\s+root_rect\s*\{\s*"
            r"(?:8\s*,\s*10\s*,\s*240\s*,\s*204|"
            r"\(width\s*-\s*240\)\s*/\s*2\s*,\s*10\s*,\s*240\s*,\s*204)"
            r"\s*\}", text))
        has_wide_root = bool(re.search(
            r"\bpanel_w\s*=\s*width\s*==\s*342\s*\?\s*320\s*:\s*240"
            r"\s*;", text)) and bool(re.search(
            r"HostOverlayRect\s+root_rect\s*\{\s*"
            r"\(width\s*-\s*panel_w\)\s*/\s*2\s*,\s*10\s*,"
            r"\s*panel_w\s*,\s*204\s*\}", text))
        if has_fixed_root and not has_wide_root:
            conflicts.append("motion_and_destination_share_fixed_240px_root_on_wide_canvas")

    # Merged #2113 fixed a *measured real SDL* bug: the blue motion ink
    # previously repainted identical blue on the already-blue selected-band
    # stripe, so four native output frames were pixel-identical despite
    # advancing source motion ticks. A stale rehearsal merge can reintroduce
    # that invisible overlay while all four integration callsites still exist.
    # Demand a dark source-band undertrack BEFORE the constant-blue accent.
    # This is a cheap source reject only; genuine final-SDL pixel-motion
    # capture and reduced-motion comparison remain independently mandatory.
    motion_header = root / "native/product/modern_menu_motion.hpp"
    motion_source = (
        motion_header.read_text(encoding="utf-8")
        if motion_header.is_file() and not motion_header.is_symlink() else ""
    )
    if all(checked[key]["present"] for key in (
            "motion_model_available", "native_motion_painted",
            "source_grammar_available")):
        motion_painter = re.search(
            r"\bpaint_modern_menu_selection_motion\s*\([\s\S]{0,7000}?\n\}",
            motion_source)
        painter_source = motion_painter.group(0) if motion_painter else ""
        fill = re.search(
            r"\bkStockFocusBandFill\s*=\s*0xE0283058u\b",
            painter_source)
        erase = re.search(
            r"paint\.fill_rect\s*\([^;]{0,240}?\bkStockFocusBandFill\s*\)",
            painter_source)
        blue = re.search(
            r"paint\.fill_rect\s*\([^;]{0,240}?\bpalette\.cursor_blue\s*\)",
            painter_source)
        if not (fill and erase and blue and erase.start() < blue.start()):
            conflicts.append("motion_blue_on_blue_undertrack_can_be_invisible")

    # Merged #2119 repaired a source-only success-receipt bug: if a child
    # destination refuses painting, the native host must not silently keep
    # the shell and claim the child appeared. In-progress integration #2053
    # predates this protection, and a conflicting host merge can regress it
    # while all header/callsite presence checks still look green.
    child_predicate = text.find("modern_native_destination_is_open(view)")
    child_guard = text.find("if (drawn && !child_ok)")
    child_receipt = text.find("modern_native_destination_stage(view)")
    child_result = text.find("const bool child_ok")
    if checked["native_destinations_drawn"]["present"]:
        guarded = (
            0 <= child_predicate < child_result < child_guard < child_receipt
            and "render_modern_native_destination(" in
                text[child_result:child_guard]
            and all(token in text[child_guard:child_receipt] for token in (
                "g_last_native_destination_stage.clear();",
                "paint_refused=1", "return 0;"))
        )
        if not guarded:
            conflicts.append("destination_child_refusal_can_claim_success")
    # An independently reproduced title-owner regression (PR #2043,
    # source 5a3b3b4) used a truncated USA SHA256 literal and refused the
    # canonical ROM before the new final-SDL probe launched. This cheap
    # integration guard is conditional on the optional capture producer
    # being present; it never weakens the ROM identity preflight.
    title_capture_tool = root / "tools/capture_modern_title_entry_sdl_win32.py"
    if title_capture_tool.is_symlink():
        conflicts.append("title_sdl_capture_tool_redirected")
    elif title_capture_tool.is_file():
        title_capture_source = title_capture_tool.read_text(encoding="utf-8")
        literal = re.search(
            r'^\\s*USA\\s*=\\s*"([0-9a-f]+)"\\s*$',
            title_capture_source, re.MULTILINE)
        if literal and literal.group(1) != (
                "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"):
            conflicts.append("title_sdl_capture_incomplete_canonical_rom_digest")

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
