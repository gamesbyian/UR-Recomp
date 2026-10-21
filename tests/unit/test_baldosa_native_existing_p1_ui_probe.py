#!/usr/bin/env python3
"""No-result native UI and next-boot profile switch contract regressions."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from baldosa_native_existing_p1_ui_probe import require_switch


def valid_switch(current: str = "mike", next_id: str = "andrew") -> str:
    return (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={current} "
        f"root=saves/profile-{current}\n"
        "UR_BALDOSA_MODERN_ROOT opened=1\n"
        "UR_BALDOSA_MODERN_ROOT existing_p1_opened=1 "
        f"from={current} to={next_id} activation=next_process\n"
        f"UR_BALDOSA_NATIVE_P1_SWITCH status=0 from={current} "
        f"to={next_id} activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT existing_p1_queued=1 "
        "activation=next_process\n"
        "UR_BALDOSA_MODERN_ROOT existing_p1_stale_race_blocked=1\n"
        f"UR_BALDOSA_NATIVE_PROFILE NEXT_BOOT_COMMITTED from={current} "
        f"to={next_id} original_raw_typed_saved=1\n"
    )


class ExistingP1ControllerSwitchTest(unittest.TestCase):
    def test_source_order_and_duplicate_switch_refusal(self):
        require_switch(valid_switch(), "mike", "andrew")
        require_switch(valid_switch("andrew", "mike"), "andrew", "mike")
        for invalid in (
            valid_switch().replace("status=0", "status=4"),
            valid_switch().replace("from=mike to=andrew", "from=mike to=mike"),
            valid_switch().replace("existing_p1_opened=1",
                                   "existing_p1_opened=0"),
            valid_switch().replace("existing_p1_queued=1",
                                   "existing_p1_queued=0"),
            valid_switch().replace("profile=mike", "profile=andrew"),
            valid_switch() + valid_switch(),
            valid_switch() + "UR_BALDOSA_NATIVE_RUN CAPTURED=1\n",
            valid_switch() + "UR_BALDOSA_NATIVE_MATCH CAPTURED=1\n",
            valid_switch() + "UR_BALDOSA_MODERN_ROOT stock_entered players=1\n",
            valid_switch() + "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew\n",            valid_switch().replace("NEXT_BOOT_COMMITTED", "NEXT_BOOT_COMMIT_FAILED"),
            valid_switch() + "UR-BALDOSA-SAVE-FAILED: no save\n",

        ):
            with self.subTest(reason=invalid[-80:]), self.assertRaises(ValueError):
                require_switch(invalid, "mike", "andrew")

    def test_ui_path_uses_existing_product_authority_and_sticky_reboot(self):
        root = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text()
        adapter = (ROOT / "tools/baldosa_modern_profile_activation.cpp").read_text()
        presenter = (ROOT / "native/product/modern_root_overlay_presenter.hpp"
                     ).read_text()
        for token in (
            "ur_baldosa_modern_select_existing_p1_next_boot(",
            "g_named_profile_stale = true;",
            "g_existing_switch_saved = true;",
            "existing_p1_opened=1",
            "existing_p1_queued=1",
            'std::strcmp(opt, "6") == 0',
            "view.existing_profile_switch_saved = g_existing_switch_saved;",
        ):
            self.assertIn(token, root)
        self.assertIn("select_baldosa_existing_profile_for_next_boot", adapter)
        original = (ROOT / "tools/baldosa_native_existing_p1_ui_probe.py").read_text()
        self.assertIn("UR_BALDOSA_QA_POSTSAVE_NEXT_BOOT_GATE", original)
        self.assertIn("--select-existing-next-boot", original)
        self.assertIn("proc.returncode != 9", original)
        self.assertIn("original_raw_typed_checkpoint_before_external_selector", original)
        self.assertIn('snapshot("before")', original)
        self.assertIn('snapshot("after-source-save")', original)
        self.assertIn('snapshot("after-external-selector")', original)
        self.assertIn('snapshot("after-original-refusal")', original)
        self.assertIn("len(receipts) != 24", original)
        self.assertIn("UR-BALDOSA-SWITCH-FAILED", original)
        self.assertIn("SWITCH ACTIVE P1", presenter)
        self.assertIn("A SWITCH  B CANCEL", presenter)
        self.assertIn("RESTART TO SWITCH RACER", presenter)
        self.assertNotIn("NO LIVE RACER CHANGE", presenter)
        self.assertNotIn("RtlWriteSram(", root)
        self.assertNotIn("RtlRunFrame(", root)


if __name__ == "__main__":
    unittest.main()
