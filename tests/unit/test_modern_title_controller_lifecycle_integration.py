#!/usr/bin/env python3
"""Source contracts for coexisting Modern title and native SDL controller journeys.

This guards the *draft integration source*, not physical hardware or a Windows
release gate. Exact-head Windows acceptance remains necessary after rebase.
"""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[2] /
          "tools/baldosa_native_modern_root.cpp").read_text(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "tools"))
from run_baldosa_keyboard_pad_join_acceptance import verify_owner_disconnect
HOST_PATCH = (ROOT / "tools/baldosa_sdl_controller_lifecycle_spike.py").read_text(encoding="utf-8")
WINDOWS_WORKFLOW = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text(encoding="utf-8")
ATTRACT_PROBE = (ROOT / "tools/probe_baldosa_modern_title_attract_win32.py").read_text(encoding="utf-8")
BOOTSTRAP_SCRIPT = (ROOT / "tests/input/baldosa-modern-title-first-profile-bootstrap.script").read_text(encoding="utf-8")


def require_lifecycle(source: str) -> None:
    for token in (
        "snesrecomp_desktop_product_seat_source(int seat)",
        "snesrecomp_desktop_product_seat_move(int from, int to)",
        "bool join_p2_owner_present()",
        "if (!join_p2_owner_present()) return false;",
        "join_watch_seat_owners();",
        "join_return_moved_pad();",
        "promote_lone_seat2_pad();",
        "g_join_p1_by_keyboard = true;",
        "g_join_moved_source = snesrecomp_desktop_product_seat_source(1);",
        "join_pad_moved from=1 to=2",
        "join_seat_left seat=2 confirmation_cleared=1",
        "lone_pad_promoted from=2 to=1",
    ):
        if token not in source:
            raise AssertionError("lost merged-main controller behavior: " + token)


def require_native_host_linkage(patch: str, workflow: str) -> None:
    # A C++ declaration without the pinned Baldosa SDL host definition links
    # unsuccessfully even when every source-only root test passes.
    for symbol in (
        "long long snesrecomp_desktop_product_seat_source(int seat) {",
        "int snesrecomp_desktop_product_seat_move(int from, int to) {",
    ):
        if symbol not in patch:
            raise AssertionError("native host definition missing: " + symbol)
    stage = 'python tools/baldosa_sdl_controller_lifecycle_spike.py --game baldosa --ur-root "$GITHUB_WORKSPACE"'
    if workflow.count(stage) != 2:
        raise AssertionError("host patch must be staged and idempotence-checked before native link")
    if workflow.index(stage) > workflow.index("cmake --build baldosa/build-ur-win --target UniracersSNESRecomp"):
        raise AssertionError("controller host patch stages too late")
    if "python tests/unit/test_baldosa_sdl_controller_lifecycle_spike.py" not in workflow:
        raise AssertionError("host patch source regression guard missing")


def require_shared_native_acceptance(workflow: str) -> None:
    # A successful Win32 link is not a controller/title journey. Demand
    # real native invocations from the SAME compiled executable and receipts.
    start = "      - name: Qualify draft controller 15-19 and title 24-28 on one Win32 PE"
    end = "      - name: Retain draft title/controller exact-PE receipts"
    if workflow.count(start) != 1 or workflow.count(end) != 1:
        raise AssertionError("missing or duplicated same-PE native acceptance step")
    step = workflow.split(start, 1)[1].split(end, 1)[0]
    for token in (
        "agent2/title-controller-lifecycle-20261023",
        "integration/modern-title-final-sdl-current-main-20261021",
        "run_baldosa_controller_lifecycle_acceptance.py",
        "run_baldosa_keyboard_pad_join_acceptance.py",
        "for confirm in gamepad keyboard start held; do",
        "capture_baldosa_modern_title_win32.py",
        "probe_baldosa_modern_title_attract_win32.py",
        "--preview-wake --timeout 140",
        "for wake in keyboard p2; do",
        '--preview-wake --wake-route "$wake" $aspect --timeout 140',
        '--preview-wake --recovery --timeout 140',
        '--preview-wake --recovery --named-play --timeout 140',
        '--bootstrap-script "$GITHUB_WORKSPACE/tests/input/baldosa-modern-title-first-profile-bootstrap.script"',
        "'source_main_recovery':",
        "'named_play_after_attract':",
        "receipt.get('real_guest_main_recovery_verified') is not True",
        "receipt.get('named_source_play_verified') is not True",
        "'original_main_stable' if name == 'named_play_after_attract'",
        "'wake_keyboard_4by3':",
        "'wake_p2':",
        "receipt.get('native_wake_route') != wake_route",
        "hashlib.sha256(exe.read_bytes()).hexdigest()",
        "if receipt.get(key) != expected:",
        "SAME_PE_NATIVE_TITLE_CONTROLLER_ACCEPTANCE_OK",
    ):
        if token not in step:
            raise AssertionError("native acceptance coverage missing: " + token)
    if not (ROOT / "tools/run_baldosa_keyboard_pad_join_acceptance.py").is_file():
        raise AssertionError("actual native 15-19 acceptance runner missing")
    if step.count('--exe "$EXE"') != 7:
        raise AssertionError("controller/title runs must all use one exact Windows PE")


def require_named_failure_diagnostics(workflow: str, probe: str) -> None:
    for token in (
        "ur-title-original-attract-named-play/native-attract.log",
        "ur-title-original-attract-recovery/native-attract.log",
    ):
        if token not in workflow:
            raise AssertionError("native original-game failure log not retained: " + token)
    for token in ("observed_source_phases=", "inspect retained native-attract.log",
                  "matches={count}"):
        if token not in probe:
            raise AssertionError("native source-stage failure diagnostics missing: " + token)


class ModernTitleControllerReconciliation(unittest.TestCase):
    def test_named_bootstrap_uses_proven_first_profile_environment(self):
        self.assertIn('boot_env["UR_BALDOSA_MODERN_PROFILE_SELECT"] = "1"', ATTRACT_PROBE)
        self.assertIn('boot_env["UR_BALDOSA_MODERN_INPUT"] = "1"', ATTRACT_PROBE)
        self.assertNotIn('boot_env["UR_BALDOSA_MODERN_PROFILE_SELECT"] = "0"', ATTRACT_PROBE)
        self.assertIn("wait 900", BOOTSTRAP_SCRIPT)
        self.assertIn("native-profile-bootstrap.log", WINDOWS_WORKFLOW)
        self.assertIn("inspect retained native-profile-bootstrap.log", ATTRACT_PROBE)
    
    def test_failed_named_play_retains_real_guest_timeline(self):
        # Preserve the actual guest log after successful bootstrap; otherwise
        # the first failing source-stage expectation cannot be adjudicated.
        require_named_failure_diagnostics(WINDOWS_WORKFLOW, ATTRACT_PROBE)
        for token in (
            "ur-title-original-attract-named-play/native-attract.log",
            "ur-title-original-attract-recovery/native-attract.log",
        ):
            with self.subTest(path=token), self.assertRaises(AssertionError):
                require_named_failure_diagnostics(WINDOWS_WORKFLOW.replace(token, ""), ATTRACT_PROBE)
        for token in ("observed_source_phases=", "inspect retained native-attract.log",
                      "matches={count}"):
            with self.subTest(token=token), self.assertRaises(AssertionError):
                require_named_failure_diagnostics(WINDOWS_WORKFLOW, ATTRACT_PROBE.replace(token, ""))


    def test_same_executable_native_acceptance_is_invoked(self):
        require_shared_native_acceptance(WINDOWS_WORKFLOW)

    def test_same_executable_negative_controls(self):
        for token in (
            "run_baldosa_keyboard_pad_join_acceptance.py",
            "for confirm in gamepad keyboard start held; do",
            "--preview-wake --timeout 140",
            "for wake in keyboard p2; do",
            "'wake_p2':",
            "'source_main_recovery':",
            "'named_play_after_attract':",
            "receipt.get('real_guest_main_recovery_verified') is not True",
            "receipt.get('named_source_play_verified') is not True",
            "'original_main_stable' if name == 'named_play_after_attract'",
            "receipt.get('native_wake_route') != wake_route",
            "if receipt.get(key) != expected:",
        ):
            with self.subTest(token=token), self.assertRaises(AssertionError):
                require_shared_native_acceptance(WINDOWS_WORKFLOW.replace(token, ""))

    def test_owner_leaves_requires_actual_host_p2_unplug(self):
        # run_game joins captured stdout + newline + captured stderr, so
        # host SDL seat lines precede all root lines even when the real
        # detach occurred between root confirmations. Never infer causal
        # cross-stream order from their offsets in this combined string.
        p1 = ("[Gamepad] UR_CONTROLLER_SEAT assign instance=101 seat=0 "
              "reason=empty player_index=-1 key=0000000000000001")
        p2 = ("[Gamepad] UR_CONTROLLER_SEAT assign instance=202 seat=1 "
              "reason=empty player_index=-1 key=0000000000000002")
        opened = "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2"
        confirmed = "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2"
        vacate = ("[Gamepad] UR_CONTROLLER_SEAT vacate instance=202 "
                  "seat=1 key=0000000000000002")
        cleared = ("UR_BALDOSA_MODERN_ROOT join_seat_left seat=2 "
                   "confirmation_cleared=1")
        p1_confirm = "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1"
        host = [p1, p2, vacate]
        root = [opened, confirmed, cleared, p1_confirm]
        expected = host + root
        verify_owner_disconnect("\n".join(expected) + "\n")
        invalid = {
            "no SDL unplug": [p1, p2] + root,
            "wrong instance": [p1, p2,
                               vacate.replace("instance=202", "instance=999")] + root,
            "wrong seat": [p1, p2, vacate.replace("seat=1", "seat=0")] + root,
            "vacate before assignment": [vacate, p1, p2] + root,
            "P1 also unplugged": host +
                                 [vacate.replace("instance=202", "instance=101")
                                        .replace("seat=1", "seat=0")] + root,
            "duplicate unplug": host + [vacate] + root,
            "duplicate pad identity": [p1, p2.replace("instance=202", "instance=101"),
                                       vacate] + root,
            "spurious stock admission": expected +
                                        ["UR_BALDOSA_MODERN_ROOT stock_requested players=2"],
            "unexpected seat move": expected +
                                    ["[Gamepad] UR_CONTROLLER_SEAT move instance=101 from=0 to=1"],
            "missing root withdrawal": host + [opened, confirmed, p1_confirm],
            "root withdrawal before confirmation": host +
                    [opened, cleared, confirmed, p1_confirm],
        }
        for label, witness in invalid.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                verify_owner_disconnect("\n".join(witness) + "\n")

    def test_owner_disconnect_native_causal_source_guard(self):
        # The root may report withdrawal only after it has observed that
        # the confirmed P2 SDL instance no longer owns seat 2.
        for token in (
            "g_join_p2_source = snesrecomp_desktop_product_seat_source(1);",
            "snesrecomp_desktop_product_seat_source(1) == g_join_p2_source;",
            "if (!g_two_seat_join.open() || !g_two_seat_join.confirmed(1) ||\n        join_p2_owner_present()) return;",
            "g_two_seat_join.clear(1);",
        ):
            self.assertIn(token, SOURCE)

    def test_failed_p2_disconnect_retains_source_evidence(self):
        self.assertIn("inspect retained p2_owner_leaves/log.txt",
                      (ROOT / "tools/run_baldosa_keyboard_pad_join_acceptance.py").read_text(encoding="utf-8"))
        self.assertIn("ur-title-controller-join/p2_owner_leaves/log.txt",
                      WINDOWS_WORKFLOW)

    def test_native_host_definitions_are_staged_before_link(self):
        require_native_host_linkage(HOST_PATCH, WINDOWS_WORKFLOW)

    def test_host_linkage_negative_controls(self):
        for token in (
            "long long snesrecomp_desktop_product_seat_source(int seat) {",
            "int snesrecomp_desktop_product_seat_move(int from, int to) {",
        ):
            with self.subTest(symbol=token), self.assertRaises(AssertionError):
                require_native_host_linkage(HOST_PATCH.replace(token, ""), WINDOWS_WORKFLOW)
        stage = 'python tools/baldosa_sdl_controller_lifecycle_spike.py --game baldosa --ur-root "$GITHUB_WORKSPACE"'
        with self.assertRaises(AssertionError):
            require_native_host_linkage(HOST_PATCH, WINDOWS_WORKFLOW.replace(stage, ""))

    def test_merged_controller_lifecycle_is_present(self):
        require_lifecycle(SOURCE)

    def test_negative_removal_controls(self):
        for token in ("if (!join_p2_owner_present()) return false;",
                      "g_join_p1_by_keyboard = true;",
                      "join_watch_seat_owners();"):
            with self.subTest(token=token), self.assertRaises(AssertionError):
                require_lifecycle(SOURCE.replace(token, ""))

    def test_title_and_controller_smoke_ids_do_not_collide(self):
        title = SOURCE.split('const char* fixture = std::getenv("UR_BALDOSA_MODERN_ROOT_KEY_SMOKE");', 1)[1]
        title = title.split("g_title_logged = false;", 1)[0]
        for mode in range(15, 20):
            self.assertIn('std::strcmp(opt, "' + str(mode) + '")', SOURCE)
            self.assertNotIn('std::strcmp(fixture, "' + str(mode) + '")', title)
        for mode in range(24, 29):
            self.assertIn('std::strcmp(opt, "' + str(mode) + '")', SOURCE)
            self.assertIn('std::strcmp(fixture, "' + str(mode) + '")', title)
        self.assertIn("SDL_AttachVirtualJoystick(&desc)", SOURCE)

    def test_title_confirm_and_original_attract_wake_remain(self):
        self.assertIn("confirm_modern_native_title();", SOURCE)
        self.assertIn("wake_original_stock_attract();", SOURCE)
        self.assertIn("g_original_attract_p2_release_button", SOURCE)

    def test_current_main_presentation_contracts_survive_title_integration(self):
        # These are merged main behaviors, not title-only visual approval.
        self.assertIn('#include "modern_reduced_motion_preference.hpp"', SOURCE)
        self.assertIn("ur::product::modern_reduced_motion_preference(", SOURCE)
        self.assertIn('std::getenv("UR_REDUCED_MOTION"));', SOURCE)
        self.assertIn("height, g_run_save_feedback,\n            width)", SOURCE)
        self.assertIn("ur::product::modern_menu_source_hero::kClip.frame_count", SOURCE)
        self.assertIn("ur::product::kModernMenuStockHeroMaxCycle", SOURCE)
        self.assertIn("root_focus_visible, reduced_motion, hero_source_frames}", SOURCE)

    def test_p2_reentry_is_gated_by_observed_stock_main(self):
        start = SOURCE.index("// During stock gameplay P2 remains P2.")
        end = SOURCE.index("if (player != 0) return 0;", start)
        body = SOURCE[start:end]
        self.assertIn("snesrecomp_desktop_product_seat_source(0) != -1", body)
        self.assertIn("snesrecomp_desktop_product_seat_source(1) == -1", body)
        self.assertIn("reopen_on_observed_stock_main()", body)


if __name__ == "__main__":
    unittest.main()
