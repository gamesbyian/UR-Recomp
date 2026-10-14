#!/usr/bin/env python3
"""ROM-free parser and source-boundary checks for native Dragster Practice.

These sample strings are NOT actual guest results or physical pad evidence.
Only the Win32 job executes the pinned native 65816 source course.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from baldosa_native_practice_probe import require_native_practice_source


class NativePracticeProbeTests(unittest.TestCase):
    def test_requires_source_course_and_real_p1_root_edges(self):
        good = (
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1\n"
            "UR_BALDOSA_MODERN_ROOT opened=1\n"
            "UR_BALDOSA_MODERN_ROOT practice_gamepad=DOWN\n"
            "UR_BALDOSA_MODERN_ROOT practice_opened=1 available=1 "
            "course=0 source_menu_required=1\n"
            "UR_BALDOSA_MODERN_ROOT practice_gamepad=A\n"
            "UR_BALDOSA_MODERN_ROOT practice_requested=1 course=0 "
            "name=DRAGSTER source_route=stock\n"
            "UR_BALDOSA_MODERN_ROOT practice_gamepad=A\n"
            "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=0 "
            "original_course=1 race=1 source_identity=verified\n"
        )
        require_native_practice_source(good)
        bad = (
            good.replace("original_course=1", "original_course=2"),
            good.replace("course=0 name=DRAGSTER", "course=1 name=ZOOM ZOO"),
            good.replace("practice_gamepad=DOWN", "practice_gamepad=UP"),
            good.replace("practice_gamepad=A", "practice_gamepad=B", 1),
            good.replace("practice_entered=1", "practice_entered=0"),
            good.replace("race=1", "race=0"),
            good.replace("source_identity=verified", "source_identity=guessed"),
            good.replace("practice_opened=1", "practice_opened=0"),
            good.replace("available=1", "available=45"),
            good.replace("source_route=stock", "source_route=host"),
            good + good,
            good + "UR_BALDOSA_MODERN_ROOT practice_rejected=timeout\n",
            good + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
        )
        for text in bad:
            with self.subTest(value=text[-100:]), self.assertRaises(ValueError):
                require_native_practice_source(text)

    def test_reuses_product_route_without_original_guest_writes(self):
        source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        shared = (ROOT / "native/product/quick_practice_launch.hpp").read_text()
        overlay = (ROOT / "native/product/modern_root_overlay_presenter.hpp").read_text()
        for token in (
            "advance_quick_practice_launch(",
            "ur_uniracers_identify_course(",
            "ur_baldosa_product_queue_stock_menu_input(mask)",
            "quick_practice_launch_owns_player_input",
            "source_identity=verified",
            "kNativePracticeAvailable{1u}",
        ):
            self.assertIn(token, source)
        # The native root is available before original MAIN settles; the
        # shared router, not the scratch-SRAM preflight, owns waiting for it.
        self.assertIn("QuickPracticeLaunchStage::AwaitMain", shared)
        self.assertIn("g_ram[0x0313] == 1u || !g_visible || g_stock_target != -1", source)
        self.assertNotIn("g_ram[0x0313] == 1u || g_ram[0x009f] != 0xd7u", source)
        self.assertIn("AwaitNowPlaying", shared)
        self.assertIn("AwaitRace", shared)
        self.assertIn("view.practice_picker_open", source)
        self.assertIn("if (view.practice_picker_open || view.practice_launch_pending)", overlay)
        self.assertNotIn("RtlWriteSram(", source)

        # Regression gate: first-party Practice is a scratch SRAM session,
        # never a normal named career or a real earned run. This source check
        # alone does not replace the two genuine Windows process byte audit.
        activation = (ROOT / "tools/baldosa_modern_profile_activation.cpp").read_text()
        for token in (
            "begin_practice_session()",
            "restore_practice_session()",
            'RtlSetSaveRoot(requested_root.c_str());',
            'const std::string requested_root = "practice-session";',
            "g_practice_sram_snapshot.assign(",
            "std::memcpy(g_sram, g_practice_sram_snapshot.data(),",
            "practice_sram_restored=1",
            "ur_baldosa_modern_root_practice_active(void)",
            "ur_baldosa_modern_root_restore_practice_on_shutdown(void)",
            "!g_practice_session_active",
        ):
            self.assertIn(token, source)
        self.assertIn("ur_baldosa_modern_root_practice_active() ||", activation)
        before_save = activation.index(
            'extern "C" int ur_baldosa_modern_profile_before_native_save(void)')
        restore = activation.index(
            "ur_baldosa_modern_root_restore_practice_on_shutdown()", before_save)
        save_guard = activation.index(
            'if (!activated() || g_verified_native_profile_id.empty()) return 1;',
            before_save)
        self.assertLess(before_save, restore)
        self.assertLess(restore, save_guard)
        probe = (ROOT / "tools/baldosa_native_practice_probe.py").read_text()
        for token in (
            '"Named P1 Practice SRAM Integrity"',
            '"practice-session"',
            '"saves/profile-mike/save.srm"',
            '"saves/profile-mike/host-profile.txt"',
            '"host-state-v1.txt"',
            '"profiles-v1.txt"',
            "p.read_bytes() != before",
            "Named Practice minted an earned completed run",
            "run_game_hard_killed(",
            "proc.kill()",
            "killed_live = True",
            "record_boundary(",
            "ordinary_idle_boot_2_control",
            "Idle baseline boot entered play: ",
            "Post-kill witness boot entered play: ",
            "verify_boot_sram(retried, original_srm",
            "after_ordinary_reboot",
            "after_practice_after_kill",
            "kill-receipt.json",
            "killed_while_alive",
            "no longer live at the kill",
            "reported a clean exit",
            "Hard-killed Practice altered named data: ",
            "verify_boot_sram(rebooted,",
            "Practice after hard kill failed: ",
        ):
            self.assertIn(token, probe)

    def test_workflow_retains_practice_logs_in_separate_artifact(self):
        wf = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertIn("name: baldosa-win32-native-practice-lifecycle", wf)
        for token in ("named_p1_practice_hard_killed/log.txt",
                      "named_p1_practice_hard_killed/kill-receipt.json",
                      "named_p1_boot_after_practice_kill/log.txt",
                      "named_p1_practice_after_kill/log.txt",
                      "boundary-receipts.json"):
            self.assertIn("native_source_practice_dragster/" + token, wf)
        pause = wf.index("name: baldosa-win32-native-pause-evidence")
        pause_end = wf.index("Retain bounded pre-Records raw pair")
        self.assertNotIn("native_source_practice_dragster", wf[pause:pause_end])


if __name__ == "__main__":
    unittest.main()
