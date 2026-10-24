"""QA-02 C04: never publish the selector before target framework SRAM.

The independent-process host persistence test kills at both durable file
boundaries. This companion source guard binds the correct order to the
actual Modern profile activation producer instead of another mock router.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ProfileSwitchSramRecoveryContract(unittest.TestCase):
    def test_selector_is_last_authoritative_publication(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        activation = host.split("bool activate_profile_id(", 1)[1].split(
            "\n}\n\nbool create_profile_from_editor", 1
        )[0]
        self.assertIn("const auto previous_product = g_product_state;", activation)
        self.assertIn("std::memcpy(previous_sram.data(), g_sram", activation)
        self.assertIn("if (!g_sram ||", activation)
        self.assertIn("if (!persist_live_profile_snapshot()) return false;", activation)
        self.assertIn("g_product_state = product;", activation)
        self.assertIn("apply_profile_save_root();", activation)
        self.assertIn("if (!g_profile_state ||", activation)
        self.assertIn("restore_stock_sram_from_profile(", activation)
        self.assertIn("if (!RtlTryWriteSram())", activation)
        self.assertIn("if (!persist_product_state(product))", activation)
        self.assertIn("UR_PROFILE_SELECT TARGET_SRAM_WRITE_FAILED", activation)
        self.assertIn("UR_PROFILE_SELECT SELECTOR_COMMIT_FAILED", activation)
        self.assertIn("UR_PROFILE_SELECT RESTORED_PRECOMMIT", activation)
        self.assertIn("UR_PROFILE_SELECT RESTORE_SRAM_WRITE_FAILED", activation)
        self.assertNotIn("persist_product_state(previous_product)", activation)
        # The target's framework SRAM is durable *before* the global CAS,
        # while any rejection restores only in-memory state and prior SRAM.
        switch = activation.index("g_product_state = product;")
        load = activation.index("restore_stock_sram_from_profile(")
        target_write = activation.index("if (!RtlTryWriteSram())")
        selector_commit = activation.index("if (!persist_product_state(product))")
        applied = activation.index('product_diagnostic("UR_PROFILE_SELECT APPLIED")')
        self.assertLess(switch, load)
        self.assertLess(load, target_write)
        self.assertLess(target_write, selector_commit)
        self.assertLess(selector_commit, applied)

        # A live competing process's selector CAS winner is never rolled
        # back using a stale expectation from our failed local attempt.
        rollback = activation.split("const auto restore_previous = [&]() {", 1)[1].split(
            "\n    };", 1
        )[0]
        self.assertIn("g_product_state = previous_product;", rollback)
        self.assertIn("std::memcpy(g_sram, previous_sram", rollback)
        self.assertIn("RtlTryWriteSram()", rollback)
        self.assertNotIn("persist_product_state(", rollback)

    def test_reloaded_target_format_is_checked_before_guest_sram_write(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        activation = host.split("bool activate_profile_id(", 1)[1].split(
            "\n}\n\nbool create_profile_from_editor", 1
        )[0]
        # The first check happens before the source profile is persisted.
        # apply_profile_save_root() subsequently reloads the target from disk,
        # so the bytes that will actually reach the guest need their own guard.
        switched = activation.split("g_product_state = product;", 1)[1]
        reloaded = switched.index("apply_profile_save_root();")
        guarded = switched.index(
            "UR_PROFILE_SELECT TARGET_RELOADED_UNFORMATTED_SNAPSHOT"
        )
        restored = switched.index("restore_stock_sram_from_profile(")
        self.assertLess(reloaded, guarded)
        self.assertLess(guarded, restored)
        guard_start = switched.index(
            "if (!ur::product::stock_sram_format_signature_present("
        )
        guard_body = switched[guard_start:restored]
        self.assertIn("g_profile_state->stock_sram->data()", guard_body)
        self.assertIn("g_profile_state->stock_sram->size()", guard_body)
        self.assertIn(
            "UR_PROFILE_SELECT TARGET_RELOADED_UNFORMATTED_SNAPSHOT", guard_body
        )
        self.assertIn("return restore_previous();", guard_body)

    def test_reloaded_target_is_bound_to_live_save_root_and_identity(self):
        host = (ROOT / "native/product/uniracers_modern_host.cpp").read_text(
            encoding="utf-8"
        )
        activation = host.split("bool activate_profile_id(", 1)[1].split(
            "\n}\n\nbool create_profile_from_editor", 1
        )[0]
        switched = activation.split("g_product_state = product;", 1)[1]
        reload = switched.index("apply_profile_save_root();")
        binding = switched.index("const bool target_reload_bound =")
        refusal = switched.index("UR_PROFILE_SELECT TARGET_RELOAD_UNAVAILABLE")
        guest_copy = switched.index("restore_stock_sram_from_profile(")
        self.assertLess(reload, binding)
        self.assertLess(binding, refusal)
        self.assertLess(refusal, guest_copy)
        condition = switched[binding:refusal]
        self.assertIn("g_profile_state_writable", condition)
        self.assertIn("g_profile_state->profile_id == profile_id", condition)
        self.assertIn("g_profile_state_path ==", condition)
        self.assertIn('std::string(applied_save_root) + "/host-profile.txt"', condition)
        self.assertIn("return restore_previous();", switched[refusal:guest_copy])


if __name__ == "__main__":
    unittest.main()
